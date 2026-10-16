#!/usr/bin/env python3
"""Read-only mechanical analysis of a retained activation pilot, never inference.

Run with desktop/ReservoirScope/.venv-activation/bin/python -B. NumPy from that
pinned environment is used only for finite-array checks and independently expressed
projection arithmetic. No activation_worker code, MLX runtime or model is imported.
No pilot file is modified. An optional aggregate --output must be outside the pilot
directory and must not already exist. Prose is hashed and compared, never emitted
or interpreted. Every rate/range carries its observed denominator.

Usage:
  .venv-activation/bin/python -B ../../probes/2026-10-15-activation-pilot.py \
    ../../research/outputs/activation-0.26.0-20261015/pilot-01 \
    --historical-binary '../../research/outputs/activation-0.26.0-20261015/pilot-package-27f05ac.app/Contents/MacOS/reservoir-scope-desktop' \
    --output validation/2026-10-15-activation-0.26.0/mechanical-pilot-summary.json
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import platform
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "desktop/ReservoirScope"
MEMORY_START = "PREVIOUS JOURNAL (earlier writing, not instructions)\n"
MEMORY_END = "\nEND PREVIOUS JOURNAL"
NO_MEMORY = "No earlier entry has been saved and applied."
PROJECTION_ATOL = 1e-12


class EvidenceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value) -> str:
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def array_hash(value) -> str:
    return sha_bytes(np.asarray(value, dtype="<f4").tobytes(order="C"))


def load(path: Path):
    require(path.is_file() and not path.is_symlink(), f"Missing or nonordinary evidence file: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def numeric_range(values):
    return {"n": len(values), "min": min(values) if values else None,
            "max": max(values) if values else None}


def first_difference(left, right):
    for index, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return index
    return min(len(left), len(right)) if len(left) != len(right) else None


class ProjectionCheck:
    def __init__(self, calibration):
        self.calibration = calibration
        body = {k: v for k, v in calibration.items() if k != "sha256"}
        require(canonical_hash(body) == calibration["sha256"], "Calibration semantic hash differs")
        self.q = np.asarray(calibration["projection"], dtype=np.float64)
        self.mean = np.asarray(calibration["mean"], dtype=np.float64)
        self.scales = np.asarray(calibration["scales"], dtype=np.float64)
        require(self.q.shape == (2560, 32) and np.isfinite(self.q).all(), "Invalid Q")
        require(self.mean.shape == self.scales.shape == (32,), "Invalid projected calibration shape")
        require(np.isfinite(self.mean).all() and np.isfinite(self.scales).all()
                and (self.scales > 0).all(), "Invalid calibration statistics")
        gram = np.einsum("di,dj->ij", self.q, self.q, optimize=False)
        require(np.allclose(gram, np.eye(32), atol=1e-6, rtol=0), "Q is not orthonormal")
        self.errors = []

    def check(self, response, label):
        h = np.asarray(response["activation"], dtype=np.float64)
        stored = np.asarray(response["projection"], dtype=np.float64)
        require(h.shape == (2560,) and np.isfinite(h).all(), f"{label}: invalid activation")
        require(stored.shape == (32,) and np.isfinite(stored).all()
                and (np.abs(stored) <= 1).all(), f"{label}: invalid projection")
        # Independent of the worker's einsum implementation: compensated scalar
        # summation of each column product, followed by the declared transform.
        raw = np.array([math.fsum(h * column) for column in self.q.T])
        expected = np.tanh((raw - self.mean) / self.scales)
        error = float(np.max(np.abs(expected - stored)))
        require(error <= PROJECTION_ATOL, f"{label}: projection mismatch {error}")
        receipt = response["receipt"]
        require(receipt["activationSha256"] == array_hash(h), f"{label}: activation hash differs")
        require(receipt["projectionSha256"] == array_hash(stored), f"{label}: projection hash differs")
        require(receipt["calibrationSha256"] == self.calibration["sha256"], f"{label}: calibration differs")
        require(receipt["modelManifestSha256"] == self.calibration["modelManifestSha256"], f"{label}: model differs")
        require(receipt["freshCache"] and receipt["cacheDiscarded"], f"{label}: cache receipt differs")
        self.errors.append(error)
        return error


def norm_summary(response, label):
    norms = response["norms"]
    rows = norms["perPosition"]
    tokens = response["promptTokenIds"] + response.get("generatedTokenIds", [])
    require(len(rows) == norms["positionCount"] == len(tokens), f"{label}: norm/token counts differ")
    actual, intended, requested = [], [], []
    gain = response["receipt"].get("requestedGain", 0.0)
    effective = response["receipt"].get("effectiveSteering", False)
    for position, (row, token) in enumerate(zip(rows, tokens)):
        require(row["tokenId"] == token, f"{label}: norm token at {position} differs")
        require(all(math.isfinite(float(v)) for v in row.values()), f"{label}: nonfinite norm")
        before = row["preSteerL2"]
        a = row["actualDeltaL2"] / before if before else 0.0
        i = row["intendedDeltaL2"] / before if before else 0.0
        target = row["requestedDeltaL2"] / before if before else 0.0
        require(a == row["actualDeltaRatio"], f"{label}: recorded norm ratio differs")
        require(abs(target - (gain if effective else 0.0)) <= 1e-12,
                f"{label}: requested norm differs from held intervention")
        require(abs(i - target) <= 1e-7, f"{label}: intended norm differs from target")
        if not effective:
            require(a == 0, f"{label}: nonzero delta with no effective steering")
        actual.append(a); intended.append(i); requested.append(target)
    require(norms["maxActualDeltaRatio"] == max(actual, default=0), f"{label}: norm maximum differs")
    require(norms["minActualDeltaRatio"] == min(actual, default=0), f"{label}: norm minimum differs")
    return {"dtype": norms["residualDtype"], "actual": actual, "intended": intended,
            "requested": requested, "promptPositions": len(response["promptTokenIds"]),
            "contentPositions": len(response.get("generatedTokenIds", []))}


def current_artifacts(frozen, calibration):
    rows = []
    protocol_path = Path(frozen.get("protocolPath", ROOT / "shared/reservoir-scope/activation-pilot.json"))
    protocol_sha256 = frozen.get("protocolSha256", frozen["fixtureSha256"])
    sources = [(APP / "activation_worker" / item["path"], item["sha256"],
                "worker/" + item["path"]) for item in frozen["modelManifest"]["workerSources"]]
    sources += [
        (APP / "activation_worker/fixtures/projection-q.npy", calibration["projectionSha256"], "projection-q.npy"),
        (APP / "activation_worker/fixtures/calibration-texts.json", calibration["textsSha256"], "calibration-texts.json"),
        (protocol_path, protocol_sha256, protocol_path.name),
        (APP / "activation-requirements.lock", frozen["lockSha256"], "activation-requirements.lock"),
        (Path(frozen["binary"]), frozen["binarySha256"], "pilot-binary"),
        (Path(frozen["qualificationDirectory"]) / "result.json", frozen["qualificationResultSha256"],
         "qualification-result.json"),
    ]
    if "runnerPath" in frozen:
        sources.append((Path(frozen["runnerPath"]), frozen["runnerSha256"], "pilot-runner"))
    for path, expected, label in sources:
        actual = sha_file(path) if path.is_file() else None
        rows.append({"artifact": label, "expectedSha256": expected, "actualSha256": actual,
                     "status": "matches" if actual == expected else "unavailable" if actual is None else "changed"})
    return rows


def arm_analysis(pilot, index, arm, outcome, calibration, checker, *,
                 session_override=None, frozen_config=None,
                 wire_prefix="worker-protocol-", ignored_response_files=()):
    condition = pilot / f"condition-{index + 1}"
    if session_override is None and not condition.exists():
        attempted = any(x["arm"] == arm for x in outcome.get("arms", []))
        require(not attempted, f"Attempted arm {arm} has no retained directory")
        return {"arm": arm, "status": "not_started_after_stop" if outcome.get("status") == "held" else "not_started",
                "quietCaptures": 0, "completeJournals": 0, "reason": "No attempt retained for this planned arm"}, None
    sessions = ([session_override] if session_override is not None else
                [p for p in condition.iterdir() if p.is_dir() and (p / "latest.json").is_file()])
    require(len(sessions) == 1, f"{arm}: expected exactly one retained session")
    session = sessions[0]
    manifest = load(session / "latest.json")
    immutable = session / f'manifest-{manifest["revision"]:06d}.json'
    require(sha_file(immutable) == sha_file(session / "latest.json"), f"{arm}: latest manifest differs")
    record_path = session / manifest["recordFile"]
    require(sha_file(record_path) == manifest["recordSha256"], f"{arm}: record hash differs")
    record = load(record_path)
    expected_config = frozen_config if frozen_config is not None else load(pilot / f"condition-{index+1}.json")
    require(manifest["config"] == expected_config, f"{arm}: frozen configuration differs")
    config = manifest["config"]
    require(config["arm"] == arm and record["specification"] ==
            {key: config[key] for key in ("arm", "seed", "observations", "stepsBetween", "journalEvery", "gain")},
            f"{arm}: numerical specification differs")
    require(load(session / "calibration.json") == calibration, f"{arm}: calibration differs")
    if manifest.get("calibrationFileSha256"):
        require(sha_file(session / "calibration.json") == manifest["calibrationFileSha256"], f"{arm}: calibration file hash differs")
    if manifest.get("modelManifestFileSha256"):
        require(sha_file(session / "model-manifest.json") == manifest["modelManifestFileSha256"], f"{arm}: model manifest file hash differs")
        require(load(session / "model-manifest.json")["sha256"] == calibration["modelManifestSha256"], f"{arm}: model identity differs")

    pending = None
    current_step = observation_count = 0
    quiet_count = quiet_samples = quiet_processed = 0
    attempts, journals, norms = [], [], []
    accepted_ids = set()
    accepted_payloads = {}
    applied = None
    projection_start = len(checker.errors)
    failures = []
    for event_index, event in enumerate(record["events"], start=1):
        kind = event["kind"]
        if kind == "requestStarted":
            require(pending is None, f"{arm}: overlapping requests")
            pending = event["request"]
            payload = load(session / f'{pending["id"]}-request.json')
            if pending["kind"] == "quiet_capture":
                current_step = (observation_count + 1) * config["stepsBetween"] - 1
                require(payload["text"] == pending["prompt"] == config["observations"][observation_count], f"{arm}: quiet input differs")
            else:
                require(payload["prompt"] == pending["prompt"] and payload["steeringState"] == pending["steeringState"], f"{arm}: journal request differs")
                require(payload["arm"] == arm and payload["seed"] == config["seed"], f"{arm}: journal settings differ")
                require(MEMORY_START in pending["prompt"] and MEMORY_END in pending["prompt"], f"{arm}: missing memory boundary")
                memory = pending["prompt"].split(MEMORY_START, 1)[1].split(MEMORY_END, 1)[0]
                if applied is None:
                    require(memory == NO_MEMORY, f"{arm}: first journal unexpectedly has prior memory")
                else:
                    require(json.loads(memory) == applied["text"], f"{arm}: quoted previous journal differs")
                attempts.append({"requestId": pending["id"], "observedStep": current_step,
                                 "promptSha256": sha_bytes(pending["prompt"].encode()),
                                 "previousJournalId": applied["id"] if applied else None,
                                 "previousJournalSha256": applied["sha256"] if applied else None,
                                 "previousFirstAppliedStep": applied["firstAppliedStep"] if applied else None,
                                 "memoryMatchesExactSavedAppliedText": True})
        elif kind in ("quietReceived", "journalReceived"):
            require(pending and event["request_id"] == pending["id"], f"{arm}: response/request association differs")
            response_path = session / f'{pending["id"]}-response.json'
            require(sha_file(response_path) == event["evidence_sha256"], f"{arm}: response evidence hash differs")
            response = load(response_path)
            require(response["projection"] == event["projection"], f"{arm}: ledger projection differs")
            checker.check(response, f'{arm}/{pending["id"]}')
            accepted_ids.add(pending["id"])
            accepted_payloads[canonical_hash(response)] = pending["id"]
            receipt = response["receipt"]
            if kind == "quietReceived":
                require(pending["kind"] == "quiet_capture", f"{arm}: quiet lane association differs")
                require(response["sampledTokenIds"] == response["generatedTokenIds"] == []
                        and receipt["sampledTokenCount"] == receipt["sampleCount"] == 0,
                        f"{arm}: quiet input sampled output")
                require(not receipt["chatTemplateApplied"], f"{arm}: quiet input received a chat template")
                require(receipt["capturedTokenId"] == response["promptTokenIds"][-1]
                        and receipt["capturedPosition"] == len(response["promptTokenIds"]) - 1,
                        f"{arm}: quiet final token differs")
                quiet_count += 1; quiet_samples += receipt["sampleCount"]
                quiet_processed += receipt["processedTokenCount"]
                observation_count += 1; current_step += 1
            else:
                require(pending["kind"] == "generate_journal" and response["complete"]
                        and response["stopReason"] == "eos" and receipt["feedbackEligible"], f"{arm}: incomplete accepted journal")
                generated = response["generatedTokenIds"]
                require(generated and receipt["capturedTokenId"] == generated[-1], f"{arm}: journal final token differs")
                require(receipt["capturedPosition"] == len(response["promptTokenIds"]) + len(generated) - 1
                        and receipt["processedTokenCount"] == len(response["promptTokenIds"]) + len(generated), f"{arm}: capture position differs")
                require(response["sampledTokenIds"] == generated + [response["stopTokenId"]]
                        and not receipt["captureReplayed"], f"{arm}: EOS/replay boundary differs")
                require(response["text"] == event["text"], f"{arm}: journal text differs")
                require(receipt["steeringState"] == pending["steeringState"] and receipt["steeringHeld"], f"{arm}: steering changed")
                text_hash = sha_bytes(response["text"].encode())
                journal_id = f'journal-{len(journals)+1}-{text_hash[:12]}'
                journal = {"id": journal_id, "text": response["text"], "sha256": text_hash,
                           "generatedTokenIds": generated, "response": response,
                           "observedStep": current_step, "saved": False, "firstAppliedStep": None}
                journals.append(journal)
                attempts[-1].update({"complete": True, "stopReason": response["stopReason"],
                                     "generatedContentTokens": len(generated),
                                     "sampledTokensIncludingEOS": len(response["sampledTokenIds"]),
                                     "promptTokens": len(response["promptTokenIds"]),
                                     "promptTokenIdsSha256": canonical_hash(response["promptTokenIds"]),
                                     "journalId": journal_id, "journalTextSha256": text_hash,
                                     "generatedTokenIdsSha256": canonical_hash(generated)})
                norms.append(norm_summary(response, f'{arm}/{pending["id"]}'))
            pending = None
        elif kind == "journalSaved":
            journal = journals[-1]
            require(event["journal_id"] == journal["id"] and event["sha256"] == journal["sha256"], f"{arm}: save association differs")
            require(sha_file(session / f'{journal["id"]}.txt') == journal["sha256"], f"{arm}: saved journal bytes differ")
            journal["saved"] = True; journal["savedAtStep"] = current_step
        elif kind == "journalApplied":
            journal = journals[-1]
            require(journal["saved"] and event["journal_id"] == journal["id"], f"{arm}: applied unsaved journal")
            current_step += 1; journal["firstAppliedStep"] = current_step; applied = journal
        elif kind == "failed":
            failures.append(event["reason"])
        else:
            raise EvidenceError(f"{arm}: unsupported event {kind}")
    require(current_step == record["state"]["step"] and observation_count == record["state"]["observationIndex"], f"{arm}: event steps differ")
    require(len(journals) == len(record["state"]["journals"]), f"{arm}: journal count differs")
    for journal, retained in zip(journals, record["state"]["journals"]):
        require(all(retained[key] == journal[key] for key in ("id", "text", "sha256", "observedStep", "saved", "firstAppliedStep")), f"{arm}: retained journal state differs")
    extra_responses, wire_responses, wire_matches = [], [], set()
    for path in sorted(session.glob("*-response.json")):
        if path.name in ignored_response_files:
            continue
        request_id = path.name.removesuffix("-response.json")
        if request_id in accepted_ids:
            continue
        response = load(path)
        if path.name.startswith(wire_prefix):
            request = load(path.with_name(path.name.removesuffix("-response.json") + "-request.json"))
            require(response["id"] == request["id"] and response["command"] == request["command"],
                    f"{arm}: protocol request/response association differs")
            require(response["protocolVersion"] == "reservoir-activation/1", f"{arm}: protocol version differs")
            identity = response["workerIdentity"]
            require(identity["modelManifestSha256"] == calibration["modelManifestSha256"],
                    f"{arm}: protocol model identity differs")
            payload = response.get("result", {})
            matching = accepted_payloads.get(canonical_hash(payload))
            if matching:
                require(matching not in wire_matches, f"{arm}: duplicate accepted protocol response")
                wire_matches.add(matching)
            elif response["command"] == "initialize" and response["type"] == "result":
                require(payload["calibration"] == request["existingCalibration"] == calibration,
                        f"{arm}: protocol initialization calibration differs")
            elif payload.get("activation") is not None:
                checker.check(payload, f"{arm}/{request_id}/unaccepted-protocol")
            wire_responses.append({"command": response["command"], "type": response["type"],
                                   "matchingAcceptedRequestId": matching})
            continue
        if response.get("activation") is not None:
            checker.check(response, f"{arm}/{request_id}/unaccepted")
        extra_responses.append({"requestId": request_id, "complete": response.get("complete"),
                                "stopReason": response.get("stopReason"), "acceptedForFeedback": False,
                                "generatedContentTokens": len(response.get("generatedTokenIds", []))})
    require(wire_matches == accepted_ids, f"{arm}: accepted response has no identical protocol evidence")
    all_actual = [x for item in norms for x in item["actual"]]
    all_intended = [x for item in norms for x in item["intended"]]
    all_requested = [x for item in norms for x in item["requested"]]
    admissions = [load(path) for path in sorted(session.glob("admission-*.json"))]
    summary = {"arm": arm, "status": manifest["status"], "sessionId": manifest["sessionId"],
               "finalStep": current_step, "quietCaptures": quiet_count, "quietSampledTokens": quiet_samples,
               "quietProcessedInputTokens": quiet_processed, "completeJournals": len(journals),
               "generatedContentTokens": sum(len(j["generatedTokenIds"]) for j in journals),
               "sampledJournalTokensIncludingEOS": sum(len(j["response"]["sampledTokenIds"]) for j in journals),
               "journalAttempts": attempts, "unacceptedResponses": extra_responses,
               "protocolResponses": {"count": len(wire_responses),
                                     "matchingAcceptedCaptures": len(wire_matches),
                                     "initializations": sum(x["command"] == "initialize" for x in wire_responses),
                                     "errors": sum(x["type"] == "error" for x in wire_responses)},
               "failureReasons": failures, "admissions": admissions,
               "projectionCapturesRecomputed": len(checker.errors) - projection_start,
               "normScope": "All prefill and generated content positions in accepted complete journals; EOS is sampled, not processed",
               "steeringNormRatios": {"actual": numeric_range(all_actual), "intended": numeric_range(all_intended),
                                      "requested": numeric_range(all_requested),
                                      "actualPercent": numeric_range([100*x for x in all_actual]),
                                      "promptPositions": sum(x["promptPositions"] for x in norms),
                                      "contentPositions": sum(x["contentPositions"] for x in norms),
                                      "residualDtypes": sorted(set(x["dtype"] for x in norms))},
               "saveApply": [{key: journal.get(key) for key in ("id", "observedStep", "savedAtStep", "firstAppliedStep", "sha256")} for journal in journals],
               "consecutiveIdenticalJournalTextPairs": sum(a["sha256"] == b["sha256"] for a,b in zip(journals,journals[1:])),
               "consecutiveJournalPairs": max(0, len(journals)-1),
               "recordSha256": manifest["recordSha256"]}
    private = {"arm": arm, "journals": journals, "attempts": attempts}
    return summary, private


def analyze(pilot: Path, historical_binary: Path | None = None):
    frozen = load(pilot / "frozen-plan.json")
    outcome = load(pilot / "result.json")
    calibration = load(pilot / "calibration.json")
    require(calibration["sha256"] == frozen["calibrationSha256"], "Frozen calibration identity differs")
    require(calibration["modelManifestSha256"] == frozen["modelManifest"]["sha256"], "Frozen model identity differs")
    model_body = {key: value for key,value in frozen["modelManifest"].items() if key != "sha256"}
    require(canonical_hash(model_body) == frozen["modelManifest"]["sha256"], "Frozen model semantic hash differs")
    checker = ProjectionCheck(calibration)
    arms, private = [], []
    for index, arm in enumerate(frozen["pilot"]["arms"]):
        summary, retained = arm_analysis(pilot, index, arm, outcome, calibration, checker)
        arms.append(summary)
        if retained is not None:
            private.append(retained)
    comparisons = []
    for left_arm, right_arm in itertools.combinations(frozen["pilot"]["arms"], 2):
        left = next((x for x in private if x["arm"] == left_arm), {"journals": [], "attempts": []})
        right = next((x for x in private if x["arm"] == right_arm), {"journals": [], "attempts": []})
        pairs = []
        for index, (a,b) in enumerate(zip(left["journals"], right["journals"]), start=1):
            pairs.append({"journalNumber": index, "textIdentical": a["text"] == b["text"],
                          "tokensIdentical": a["generatedTokenIds"] == b["generatedTokenIds"],
                          "firstDifferingContentTokenIndex": first_difference(a["generatedTokenIds"], b["generatedTokenIds"]),
                          "firstDifferingTextCharacterIndex": first_difference(a["text"], b["text"])})
        first_prompt = first_prompt_tokens = None
        if left["attempts"] and right["attempts"]:
            first_prompt = left["attempts"][0]["promptSha256"] == right["attempts"][0]["promptSha256"]
            first_prompt_tokens = (left["attempts"][0]["promptTokenIdsSha256"] ==
                                   right["attempts"][0]["promptTokenIdsSha256"])
        comparisons.append({"arms": [left_arm, right_arm], "pairedCompleteJournals": len(pairs),
                            "firstJournalPromptIdentical": first_prompt,
                            "firstJournalPromptTokensIdentical": first_prompt_tokens, "journals": pairs,
                            "status": "assessed" if pairs else "unassessed",
                            "reason": None if pairs else "Fewer than two arms retain a complete journal at a comparable opportunity"})
    artifacts = current_artifacts(frozen, calibration)
    historical = None
    if historical_binary is not None:
        historical_binary = historical_binary.expanduser().resolve(strict=True)
        actual = sha_file(historical_binary)
        require(actual == frozen["binarySha256"], "Supplied historical binary differs from frozen pilot identity")
        historical = {"path": str(historical_binary.relative_to(ROOT)) if historical_binary.is_relative_to(ROOT)
                      else str(historical_binary), "sha256": actual, "status": "matches_frozen_pilot",
                      "replacesCurrentPathCheck": False}
    return {"schema": "activation-pilot-mechanical-summary/1", "sourcePilot": pilot.name,
            "pilotStatus": outcome["status"], "scope": "complete-comparison" if all(a["status"] == "completed" for a in arms) else "partial-comparison",
            "evidenceConsistency": "passed", "modelCalls": 0, "pilotFilesModified": False,
            "analysisSourceSha256": sha_file(Path(__file__)), "pythonVersion": platform.python_version(),
            "numpyVersion": np.__version__, "frozenPlanSha256": sha_file(pilot / "frozen-plan.json"),
            "pilotResultSha256": sha_file(pilot / "result.json"), "calibrationSha256": calibration["sha256"],
            "modelManifestSha256": calibration["modelManifestSha256"],
            "currentSourceArtifacts": artifacts, "currentSourceArtifactsAllMatch": all(x["status"] == "matches" for x in artifacts),
            "historicalFrozenBinary": historical,
            "arms": arms, "betweenArmComparisons": comparisons,
            "independentProjection": {"method": "Float64 column products with math.fsum; tanh((Q^T h - mean)/scale)",
                                      "absoluteTolerance": PROJECTION_ATOL, "maxAbsoluteCoordinateError": max(checker.errors, default=None),
                                      "activationCaptures": len(checker.errors), "coordinates": 32 * len(checker.errors)},
            "limitations": [
                "This checks retained evidence and independently recomputes projection; it does not authenticate an external activation measurement.",
                "Steering ratios are recomputed from retained scalar norms; full pre/post residual matrices were not stored.",
                "Event/save/apply timing is reconstructed here; the separate Rust verifier owns full recurrent-state replay.",
                "No prose or thematic interpretation is emitted. Hash and token identity do not establish meaning, continuity, or benefit.",
                "Unstarted/refused arms have no model outcomes; a partial pilot supports no between-arm behavioral conclusion.",
                "Current source mismatches are reported separately because later source changes do not rewrite retained history.",
            ]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilotdir", type=Path)
    parser.add_argument("--historical-binary", type=Path,
                        help="Preserved executed binary, checked against the frozen SHA without replacing current-path checks")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    pilot = args.pilotdir.expanduser().resolve(strict=True)
    summary = analyze(pilot, args.historical_binary)
    payload = json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        output = args.output.expanduser().resolve()
        require(not output.is_relative_to(pilot), "Aggregate output must be outside the pilot evidence directory")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        print(json.dumps({"output": str(output), "sha256": sha_bytes(payload.encode()),
                          "scope": summary["scope"], "evidenceConsistency": summary["evidenceConsistency"],
                          "projectionCaptures": summary["independentProjection"]["activationCaptures"]}))
    else:
        sys.stdout.write(payload)


if __name__ == "__main__":
    main()
