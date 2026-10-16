"""Newline-delimited JSON service. Stdout is protocol only; no listening socket."""
from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import contextlib
import importlib.metadata
import json
import platform
import queue
import re
import sys
import threading
from pathlib import Path

from activation_worker import MODEL_ID, MODEL_REVISION, PROTOCOL_VERSION
from activation_worker.engine import Engine, WorkerError
from activation_worker.math_core import canonical_hash, sha256_file

MAX_LINE_BYTES = 8 * 1024 * 1024
REQUEST_FIELDS = {
    "inspect": {"modelPath"},
    "initialize": {"modelPath", "existingCalibration"},
    "quiet_capture": {"text"},
    "generate_journal": {"prompt", "steeringState", "gain", "arm", "maxTokens", "seed", "temperature"},
    "cancel": {"targetId"},
    "shutdown": set(),
}


def parse_request(line: str) -> dict:
    if len(line.encode("utf-8")) > MAX_LINE_BYTES:
        raise WorkerError("invalid_request", "request exceeds the 8 MiB line limit")
    def reject_constant(value):
        raise ValueError(f"nonfinite JSON constant: {value}")
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    try:
        request = json.loads(line, parse_constant=reject_constant, object_pairs_hook=unique_pairs)
    except (ValueError, TypeError) as exc:
        raise WorkerError("invalid_json", str(exc)) from exc
    if not isinstance(request, dict):
        raise WorkerError("invalid_request", "request must be a JSON object")
    valid_id = isinstance(request.get("id"), str) and bool(re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", request["id"]))
    try:
        if not valid_id:
            raise WorkerError("invalid_request", "id must contain 1..128 ASCII letters, digits, _, ., :, or -")
        command = request.get("command")
        if not isinstance(command, str) or command not in REQUEST_FIELDS:
            raise WorkerError("unknown_command", "unsupported command")
        unexpected = set(request) - REQUEST_FIELDS[command] - {"id", "command"}
        if unexpected:
            raise WorkerError("invalid_request", "unexpected fields: " + ", ".join(sorted(unexpected)))
        if command == "cancel" and (not isinstance(request.get("targetId"), str) or not request["targetId"]):
            raise WorkerError("invalid_request", "cancel requires targetId")
        if "modelPath" in request and not isinstance(request["modelPath"], str):
            raise WorkerError("invalid_request", "modelPath must be a string")
    except WorkerError as exc:
        exc.request_identity = {"id": request.get("id") if valid_id else None,
                                "command": request.get("command") if isinstance(request.get("command"), str) else None}
        raise
    return request


class Server:
    def __init__(self, engine=None, input_stream=None, output_stream=None):
        self.engine = engine or Engine()
        self.input = input_stream or sys.stdin
        self.output = output_stream or sys.stdout
        self.jobs = queue.Queue()
        self.events = {}
        self.seen = set()
        self.lock = threading.Lock()
        self.output_lock = threading.Lock()
        versions = {}
        for package in ("mlx", "mlx-lm", "numpy", "transformers", "huggingface-hub"):
            try:
                versions[package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                versions[package] = None
        sources = [{"path": path.name, "sha256": sha256_file(path)}
                   for path in sorted(Path(__file__).parent.glob("*.py"))]
        self.worker_identity = {"modelId": MODEL_ID, "revision": MODEL_REVISION,
                                "pythonVersion": platform.python_version(),
                                "runtimeVersions": versions, "workerSourcesSha256": canonical_hash(sources)}

    def emit(self, payload):
        manifest = getattr(self.engine, "manifest", None)
        payload["protocolVersion"] = PROTOCOL_VERSION
        payload["workerIdentity"] = {**self.worker_identity,
                                     "modelManifestSha256": manifest.get("sha256") if manifest else None}
        encoded = json.dumps(payload, separators=(",", ":"), allow_nan=False)
        with self.output_lock:
            self.output.write(encoded + "\n")
            self.output.flush()

    def result(self, request, result):
        self.emit({"id": request["id"], "command": request["command"], "type": "result", "result": result})

    def error(self, request, exc):
        self.emit({"id": request.get("id"), "command": request.get("command"), "type": "error",
                   "error": {"code": getattr(exc, "code", "operation_failed"), "message": str(exc)}})

    def _read(self):
        try:
            for line in self.input:
                if not line.strip():
                    continue
                request = {}
                try:
                    request = parse_request(line)
                    with self.lock:
                        if request["id"] in self.seen:
                            raise WorkerError("duplicate_id", "request id has already been used in this worker")
                        self.seen.add(request["id"])
                    command = request["command"]
                    if command == "cancel":
                        with self.lock:
                            target = self.events.get(request["targetId"])
                            if target is not None:
                                target.set()
                        self.result(request, {"targetId": request["targetId"], "cancellationRequested": target is not None})
                    elif command == "shutdown":
                        with self.lock:
                            for event in self.events.values():
                                event.set()
                        self.jobs.put((request, None))
                        break
                    else:
                        event = threading.Event()
                        with self.lock:
                            self.events[request["id"]] = event
                        self.jobs.put((request, event))
                except Exception as exc:
                    self.error(request or getattr(exc, "request_identity", {}), exc)
        finally:
            self.jobs.put((None, None))

    def run(self):
        # Reading/cancellation never enters MLX; all inference stays on this thread.
        reader = threading.Thread(target=self._read, name="activation-jsonl-reader", daemon=True)
        reader.start()
        while True:
            request, event = self.jobs.get()
            if request is None:
                break
            if request["command"] == "shutdown":
                self.result(request, {"shutdown": True})
                break
            try:
                # Third-party progress messages are not allowed onto the wire.
                with contextlib.redirect_stdout(sys.stderr):
                    result = self.engine.dispatch(request, event)
                self.result(request, result)
            except Exception as exc:
                self.error(request, exc)
            finally:
                with self.lock:
                    self.events.pop(request["id"], None)


def main():
    Server().run()


if __name__ == "__main__":
    main()
