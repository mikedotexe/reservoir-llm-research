"""Protocol-independent operations, with an injectable backend for unit tests."""
from __future__ import annotations

import time
from threading import Event

import numpy as np

from . import (DEADLINE_SECONDS, GAIN, HIDDEN_DIM, MAX_TOKENS, MODEL_ID,
               MODEL_REVISION, PROTOCOL_VERSION, STATE_DIM, TAP_BLOCK_INDEX)
from .backend import MLXBackend
from .manifest import inspect_model
from .math_core import (array_hash, calibration_texts, canonical_hash, finite_array,
                        load_projection, make_calibration, project,
                        steering_direction, validate_calibration)


class WorkerError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def checked_text(value, field="text") -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 262144:
        raise WorkerError("invalid_request", f"{field} must be nonempty text, at most 262144 characters")
    return value


class Engine:
    def __init__(self, backend_factory=MLXBackend, inspector=inspect_model, clock=time.monotonic):
        self.backend_factory, self.inspector, self.clock = backend_factory, inspector, clock
        self.backend = None
        self.manifest = None
        self.calibration = None
        self.model_path = None
        self.q = load_projection()

    def inspect(self, request: dict) -> dict:
        result = {"protocolVersion": PROTOCOL_VERSION, "modelId": MODEL_ID,
                  "revision": MODEL_REVISION, "hiddenDim": HIDDEN_DIM,
                  "stateDim": STATE_DIM, "tapBlockIndex": TAP_BLOCK_INDEX,
                  "initialized": self.backend is not None and self.calibration is not None,
                  "loadedModelPath": self.model_path}
        if request.get("modelPath"):
            result.update(self.inspector(request["modelPath"]))
        return result

    def initialize(self, request: dict, cancel: Event) -> dict:
        if self.backend is not None:
            raise WorkerError("already_initialized", "start a new owned worker to initialize another session")
        path = checked_text(request.get("modelPath"), "modelPath")
        inspected = self.inspector(path)
        manifest = inspected["manifest"]
        saved = request.get("existingCalibration")
        if saved is not None:
            validate_calibration(saved, manifest["sha256"])
        if cancel.is_set():
            raise WorkerError("cancelled", "initialization was cancelled before model load")
        self.backend = self.backend_factory(inspected["modelPath"])
        self.manifest, self.model_path = manifest, inspected["modelPath"]
        observations = []
        try:
            if saved is None:
                captures = []
                for index, text in enumerate(calibration_texts()):
                    if cancel.is_set():
                        raise WorkerError("cancelled", "calibration was cancelled")
                    capture = self._capture(text, cancel)
                    captures.append(capture["activation"])
                    observations.append({"index": index, "text": text, **capture})
                self.calibration = make_calibration(captures, manifest["sha256"])
            else:
                self.calibration = saved
        except Exception:
            self.backend.release_cache()
            self.backend = None
            self.calibration = None
            raise
        return {"manifest": manifest, "modelPath": self.model_path,
                "calibration": self.calibration,
                "calibrationSource": "restored" if saved is not None else "captured",
                "calibrationObservations": observations,
                "eosTokenIds": sorted(self.backend.eos_ids),
                "specialTokenIds": sorted(self.backend.special_ids)}

    def _require_initialized(self):
        if self.backend is None or self.calibration is None:
            raise WorkerError("not_initialized", "initialize the worker before capturing or writing")

    def _capture(self, text: str, cancel: Event) -> dict:
        backend = self.backend
        ids = backend.encode_raw(checked_text(text))
        if not ids or len(ids) > 512:
            raise WorkerError("token_limit", "quiet observations must encode to 1..512 tokens; no truncation is performed")
        if ids[-1] in backend.special_ids:
            raise WorkerError("non_content_boundary", "quiet observation ends with a special token")
        start = self.clock()
        try:
            if cancel.is_set():
                raise WorkerError("cancelled", "quiet capture was cancelled")
            # A full raw prefill, no chat template and no call to sample.
            backend.begin(ids, np.zeros(HIDDEN_DIM), 0.0, seed=0, temperature=0.0)
            if cancel.is_set():
                raise WorkerError("cancelled", "quiet capture was cancelled")
            if self.clock() - start >= DEADLINE_SECONDS:
                raise WorkerError("deadline", "quiet capture exceeded its deadline")
            activation = finite_array(backend.last_activation, (HIDDEN_DIM,), "captured activation")
            norms = self._norms(backend)
            receipt = {"captureBoundary": "last-raw-content-token-after-block-18-before-steering",
                       "capturedTokenId": ids[-1], "capturedPosition": len(ids) - 1,
                       "processedTokenCount": len(backend.processed_ids),
                       "sampleCount": 0, "sampledTokenCount": 0, "freshCache": True, "cacheDiscarded": True,
                       "thinking": False, "chatTemplateApplied": False,
                       "activationSha256": array_hash(activation),
                       "modelManifestSha256": self.manifest["sha256"],
                       "elapsedSeconds": self.clock() - start}
            return {"activation": activation.tolist(), "promptTokenIds": ids,
                    "generatedTokenIds": [], "sampledTokenIds": [],
                    "norms": norms, "receipt": receipt}
        finally:
            backend.release_cache()

    def quiet_capture(self, request: dict, cancel: Event) -> dict:
        self._require_initialized()
        result = self._capture(request.get("text"), cancel)
        return self._attach_projection(result)

    def _attach_projection(self, result: dict) -> dict:
        projected = project(result["activation"], self.calibration)
        result["projection"] = projected.tolist()
        result["receipt"]["projectionSha256"] = array_hash(projected)
        result["receipt"]["calibrationSha256"] = self.calibration["sha256"]
        return result

    @staticmethod
    def _norms(backend) -> dict:
        rows = list(backend.norm_rows)
        ratios = [x["actualDeltaRatio"] for x in rows]
        return {"perPosition": rows, "positionCount": len(rows),
                "residualDtype": getattr(backend, "residual_dtype", "fake-float32"),
                "maxActualDeltaRatio": max(ratios, default=0.0),
                "minActualDeltaRatio": min(ratios, default=0.0),
                "final": rows[-1] if rows else None}

    def generate_journal(self, request: dict, cancel: Event) -> dict:
        self._require_initialized()
        prompt = checked_text(request.get("prompt"), "prompt")
        gain = request.get("gain", GAIN)
        if isinstance(gain, bool) or gain not in (0, GAIN):
            raise WorkerError("invalid_request", "gain must be exactly 0 or 0.01")
        state = finite_array(request.get("steeringState"), (STATE_DIM,), "steeringState")
        direction = steering_direction(state, self.q)
        max_tokens = request.get("maxTokens", MAX_TOKENS)
        if type(max_tokens) is not int or not 1 <= max_tokens <= MAX_TOKENS:
            raise WorkerError("invalid_request", "maxTokens must be an integer in 1..1024")
        seed = request.get("seed", 0)
        if type(seed) is not int or not 0 <= seed < 2**32:
            raise WorkerError("invalid_request", "seed must be an unsigned 32-bit integer")
        temperature = request.get("temperature", 0.7)
        if isinstance(temperature, bool) or not isinstance(temperature, (float, int)) or not 0 <= temperature <= 2:
            raise WorkerError("invalid_request", "temperature must be finite in [0, 2]")
        arm = request.get("arm", "reservoir")
        if not isinstance(arm, str) or not arm or len(arm) > 80:
            raise WorkerError("invalid_request", "arm must be a short nonempty string")
        backend = self.backend
        ids = backend.encode_journal(prompt)
        if not ids or len(ids) > 8192:
            raise WorkerError("token_limit", "journal prompt must encode to 1..8192 tokens; no truncation is performed")
        start = self.clock()
        generated, sampled = [], []
        stop_reason, stop_token, error = "max_tokens", None, None
        activation = None
        backend.norm_rows, backend.processed_ids = [], []

        def interrupted():
            if cancel.is_set():
                return "cancelled"
            if self.clock() - start >= DEADLINE_SECONDS:
                return "deadline"
            return None

        try:
            stopping = interrupted()
            if stopping:
                stop_reason = stopping
            else:
                logits = backend.begin(ids, direction, float(gain), seed, float(temperature))
                for _ in range(max_tokens):
                    stopping = interrupted()
                    if stopping:
                        stop_reason = stopping
                        break
                    token = backend.sample(logits)
                    sampled.append(token)
                    if token in backend.eos_ids:
                        stop_reason, stop_token = "eos", token
                        break
                    if token in backend.special_ids:
                        stop_reason, stop_token = "non_eos_special_token", token
                        break
                    generated.append(token)
                    # Process each accepted content token once, including the last one.
                    # No sampler lookahead and no second replay to obtain its state.
                    logits = backend.advance(token)
                    activation = finite_array(backend.last_activation, (HIDDEN_DIM,), "captured activation").copy()
                stopping = interrupted()
                if stopping:
                    stop_reason = stopping
        except Exception as exc:
            stop_reason, error = "worker_error", f"{type(exc).__name__}: {exc}"
        finally:
            norms = self._norms(backend)
            processed = list(backend.processed_ids)
            backend.release_cache()
        try:
            text = backend.decode(generated)
        except Exception as exc:
            text = ""
            stop_reason = "worker_error"
            error = f"decode {type(exc).__name__}: {exc}"
        complete = stop_reason == "eos" and bool(text.strip()) and activation is not None
        if stop_reason == "eos" and not complete:
            stop_reason = "empty_eos"
        receipt = {
            "captureBoundary": "last-generated-content-token-after-block-18-before-steering" if complete else None,
            "capturedTokenId": generated[-1] if complete else None,
            "capturedPosition": len(ids) + len(generated) - 1 if complete else None,
            "promptTokenCount": len(ids), "generatedTokenCount": len(generated),
            "processedTokenCount": len(processed), "processedTokenIdsSha256": canonical_hash(processed),
            "sampleCount": len(sampled), "stopTokenId": stop_token,
            "freshCache": True, "cacheDiscarded": True, "thinking": False,
            "chatTemplateApplied": True, "templateSha256": canonical_hash(ids),
            "captureReplayed": False, "feedbackEligible": complete,
            "steeringHeld": True, "steeringState": state.tolist(),
            "steeringStateSha256": array_hash(state), "requestedGain": gain,
            "effectiveSteering": bool(gain and np.any(direction)),
            "seed": seed, "temperature": temperature, "maxTokens": max_tokens,
            "deadlineSeconds": DEADLINE_SECONDS, "elapsedSeconds": self.clock() - start,
            "arm": arm, "modelManifestSha256": self.manifest["sha256"],
            "calibrationSha256": self.calibration["sha256"],
            "activationSha256": array_hash(activation) if complete else None,
        }
        result = {"text": text, "complete": complete, "stopReason": stop_reason,
                  "promptTokenIds": ids, "generatedTokenIds": generated,
                  "sampledTokenIds": sampled, "stopTokenId": stop_token,
                  "activation": activation.tolist() if complete else None,
                  "projection": None, "norms": norms, "receipt": receipt}
        if error:
            result["error"] = error
        return self._attach_projection(result) if complete else result

    def dispatch(self, request: dict, cancel: Event) -> dict:
        command = request["command"]
        if command == "inspect":
            return self.inspect(request)
        if command == "initialize":
            return self.initialize(request, cancel)
        if command == "quiet_capture":
            return self.quiet_capture(request, cancel)
        if command == "generate_journal":
            return self.generate_journal(request, cancel)
        raise WorkerError("unknown_command", f"unsupported command: {command}")
