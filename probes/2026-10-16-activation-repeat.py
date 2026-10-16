#!/usr/bin/env python3
"""Compare two retained completed trace sequences and resource evidence, read-only.

Standard library only: no model imports, inference, resource commands, or prose
interpretation. Journal strings are compared exactly and hashed, never printed.
Usage: python3 -B probes/2026-10-16-activation-repeat.py OLD_PILOT NEW_COMPARISON
       --output NEW_PUBLIC_SUMMARY.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path


class EvidenceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return sha(path.read_bytes())


def canonical_sha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def read(path):
    require(path.is_file() and not path.is_symlink(), f"Missing ordinary evidence file: {path.name}")
    return json.loads(path.read_bytes())


def inventory(root):
    files = {str(p.relative_to(root)): file_sha(p) for p in sorted(root.rglob("*")) if p.is_file()}
    return {"fileCount": len(files), "relativePathAndContentSha256": canonical_sha(files)}


def first_difference(a, b):
    return next((i for i, (x, y) in enumerate(zip(a, b)) if x != y),
                min(len(a), len(b)) if len(a) != len(b) else None)


def numeric_difference(a, b):
    require(len(a) == len(b) and all(math.isfinite(x) for x in a + b), "Invalid comparable activation/projection")
    return max((abs(x-y) for x, y in zip(a, b)), default=0)


def differing_paths(a, b, path=""):
    """Report structural locations only, never journal or prompt values."""
    if type(a) is not type(b):
        return [path]
    if isinstance(a, dict):
        return [p for key in sorted(a.keys() | b.keys())
                for p in ([path+"."+key] if key not in a or key not in b
                          else differing_paths(a[key], b[key], path+"."+key))]
    if isinstance(a, list):
        if len(a) != len(b):
            return [path+".length"]
        return [p for i, (x,y) in enumerate(zip(a,b)) for p in differing_paths(x,y,path+f"[{i}]")]
    return [] if a == b else [path]


def sequence(root):
    sessions = [p for p in (root / "condition-1").iterdir() if (p / "latest.json").is_file()]
    require(len(sessions) == 1, "Expected exactly one condition-1 session")
    session = sessions[0]
    manifest = read(session / "latest.json")
    require(manifest["status"] == "completed" and manifest["config"]["arm"] == "decaying_trace", "Expected completed trace condition")
    require(file_sha(session / "latest.json") == file_sha(session / f'manifest-{manifest["revision"]:06d}.json'), "Latest immutable manifest differs")
    record_path = session / manifest["recordFile"]
    require(file_sha(record_path) == manifest["recordSha256"], "Record hash differs from manifest")
    record = read(record_path)
    wire = []
    for request_path in session.glob("worker-protocol-*-request.json"):
        prefix = request_path.name.removesuffix("-request.json")
        request, response = read(request_path), read(session / f"{prefix}-response.json")
        require(response["type"] == "result" and request["id"] == response["id"]
                and request["command"] == response["command"], "Wire request/response identity differs")
        wire.append((int(prefix.rsplit("-", 1)[1]), request, response))
    wire.sort(key=lambda item: item[0])
    require(len({r["id"] for _, r, _ in wire}) == len(wire), "Duplicate wire request ID")
    require(wire and wire[0][1]["command"] == "initialize", "First worker request was not initialization")
    calibration = read(root / "calibration.json")
    require(wire[0][1]["existingCalibration"] == wire[0][2]["result"]["calibration"] == calibration
            == read(session / "calibration.json"), "Calibration identity differs")
    operations, pending = [], None
    for event in record["events"]:
        kind = event["kind"]
        if kind == "requestStarted":
            require(pending is None, "Overlapping ledger requests")
            pending = event["request"]
        elif kind in ("quietReceived", "journalReceived"):
            require(pending and pending["id"] == event["request_id"], "Ledger response/request ID differs")
            operation = "quiet_capture" if kind == "quietReceived" else "generate_journal"
            require(pending["kind"] == operation, "Ledger operation differs")
            request_path = session / f'{pending["id"]}-request.json'
            response_path = session / f'{pending["id"]}-response.json'
            request, response = read(request_path), read(response_path)
            require(file_sha(response_path) == event["evidence_sha256"], "Response hash differs from event")
            require(request["text" if operation == "quiet_capture" else "prompt"] == pending["prompt"], "Ledger prompt differs")
            _, wire_request, wire_response = wire[len(operations)+1]
            require(wire_request["command"] == operation, "Wire operation order differs")
            require({k:v for k,v in wire_request.items() if k not in ("id", "command")} == request,
                    "Wire payload differs from the matching ledger request")
            require(wire_response["result"] == response, "Wire result differs from matching retained response")
            require(response["projection"] == event["projection"], "Ledger projection differs")
            if operation == "quiet_capture":
                require(response["sampledTokenIds"] == response["generatedTokenIds"] == []
                        and response["receipt"]["sampledTokenCount"] == 0, "Quiet capture sampled tokens")
            else:
                require(response["complete"] and response["stopReason"] == "eos"
                        and response["text"] == event["text"], "Journal completeness/text differs")
                require(request["steeringState"] == pending["steeringState"] == response["receipt"]["steeringState"], "Steering state differs")
            operations.append({"operation": operation, "requestId": pending["id"], "workerRequestId": wire_request["id"],
                               "request": request, "response": response,
                               "requestFileSha256": file_sha(request_path), "responseFileSha256": file_sha(response_path)})
            pending = None
    require(pending is None and len(wire) == len(operations)+1, "Incomplete or extra wire operation")
    journals = record["state"]["journals"]
    require(len(operations) == 18 and len(journals) == 6, "Expected twelve captures and six complete journals")
    for journal in journals:
        require(journal["saved"] and journal["firstAppliedStep"] is not None, "Journal not saved/applied")
        require(file_sha(session / f'{journal["id"]}.txt') == journal["sha256"] == sha(journal["text"].encode()), "Saved journal bytes differ")
    return {"manifest": manifest, "record": record, "operations": operations, "calibration": calibration,
            "source": {"directory": root.name, "sessionId": manifest["sessionId"],
                       "resultSha256": file_sha(root / "result.json"), "frozenPlanSha256": file_sha(root / "frozen-plan.json"),
                       "calibrationFileSha256": file_sha(root / "calibration.json"),
                       "manifestFileSha256": file_sha(session / "latest.json"), "recordFileSha256": file_sha(record_path)}}


def resource_summary(root):
    outcome, frozen = read(root / "result.json"), read(root / "frozen-plan.json")
    preparation = frozen["pilot"]["resourcePreparation"]
    preparations = []
    for i, retained in enumerate(outcome["resourcePreparations"], 1):
        path = root / f"condition-{i}-resource-preparation.json"
        summary = read(path)
        require(summary == retained and summary["preparation"] == preparation, "Preparation summary differs")
        samples_path = root / summary["samplesFile"]
        rows = [json.loads(line) for line in samples_path.read_text().splitlines()]
        streak = 0
        samples = []
        for n, row in enumerate(rows, 1):
            resource = row["resource"]
            commands = resource["commands"]
            require(commands[0]["command"] == ["/usr/sbin/sysctl", "-n", "kern.memorystatus_vm_pressure_level"]
                    and commands[1]["command"] == ["/usr/bin/memory_pressure", "-Q"], "Unexpected resource command")
            pressure = free = None
            if commands[0].get("returnCode") == 0:
                try: pressure = int(commands[0]["stdout"].strip())
                except ValueError: pass
            if commands[1].get("returnCode") == 0:
                for line in commands[1]["stdout"].splitlines():
                    if line.startswith("System-wide memory free percentage: "):
                        try: free = int(line.split(":",1)[1].strip().removesuffix("%"))
                        except ValueError: pass
                        if free is not None and not 0 <= free <= 100: free = None
                        break
            require((pressure, free) == (resource["pressure"], resource["freePercent"]), "Parsed resource result differs")
            healthy = pressure == preparation["requiredPressureLevel"] and free is not None and free >= preparation["minimumFreePercent"]
            streak = streak+1 if healthy else 0
            require(row["sample"] == n and row["healthy"] == healthy and row["consecutiveHealthySamples"] == streak, "Resource streak differs")
            samples.append({k:row[k] for k in ("sample", "sampledAtUtc", "completedAtUtc", "elapsedSeconds", "healthy", "consecutiveHealthySamples")} | {"pressure": pressure, "freePercent": free})
        require(len(rows) == summary["sampleCount"] and streak == summary["consecutiveHealthySamples"], "Preparation count differs")
        ready = streak >= preparation["consecutiveHealthySamples"] and rows[-1]["elapsedSeconds"] <= preparation["maximumSeconds"]
        require(summary["ready"] == ready, "Preparation readiness differs")
        dispatched = any(x["arm"] == summary["arm"] for x in outcome["arms"])
        if not ready:
            require(not dispatched and not (root / f"condition-{i}").exists()
                    and not (root / f"condition-{i}.json").exists(), "Unready condition was dispatched")
        preparations.append({"condition": i, "arm": summary["arm"], "ready": ready, "cliDispatched": dispatched,
                             "sampleCount": len(rows), "healthySamples": sum(x["healthy"] for x in samples),
                             "elapsedSeconds": summary["elapsedSeconds"], "reason": summary["reason"],
                             "samples": samples, "summaryFileSha256": file_sha(path), "samplesFileSha256": file_sha(samples_path)})
    releases = []
    for i, arm in enumerate(outcome["arms"], 1):
        path = root / arm["workerReleaseObservationFile"]
        observation = read(path)
        config = read(root / f"condition-{i}.json")
        require(observation["pythonPath"] == config["pythonPath"] and observation["workerPath"] == config["workerPath"], "Release observation command differs")
        releases.append({"condition": i, "arm": arm["arm"], "fileSha256": file_sha(path),
                         **{k:observation[k] for k in ("observedAtUtc", "returnCode", "matchingProcesses", "status", "scope", "limitation")}})
    require(outcome["status"] == "held" and len(outcome["arms"]) == 1 and not (root / "condition-3").exists(), "Unexpected comparison scope")
    return {"status": outcome["status"], "error": outcome["error"], "automaticRetries": outcome["automaticRetries"],
            "conditionsDispatched": len(outcome["arms"]), "preparations": preparations,
            "workerReleaseObservations": releases, "remainingRecurrentCondition": "not_started_after_preparation_timeout"}


def analyze(old, new):
    before = [inventory(old), inventory(new)]
    a, b = sequence(old), sequence(new)
    plans = [read(p / "frozen-plan.json") for p in (old,new)]
    protocol_fields = ("seed", "temperature", "stepsBetweenObservations", "journalEveryObservations",
                       "outputTokens", "requestDeadlineSeconds", "arms", "observations")
    pairs = []
    for i, (x,y) in enumerate(zip(a["operations"], b["operations"]), 1):
        require(x["operation"] == y["operation"], "Paired operation kinds differ")
        u, v = x["response"], y["response"]
        row = {"operationNumber": i, "operation": x["operation"],
               "oldRequestId": x["requestId"], "newRequestId": y["requestId"],
               "oldWorkerRequestId": x["workerRequestId"], "newWorkerRequestId": y["workerRequestId"],
               "requestPayloadEqual": x["request"] == y["request"],
               "promptTokens": [len(u["promptTokenIds"]), len(v["promptTokenIds"])],
               "generatedContentTokens": [len(u["generatedTokenIds"]), len(v["generatedTokenIds"])],
               "firstDifferingPromptTokenIndex": first_difference(u["promptTokenIds"], v["promptTokenIds"]),
               "firstDifferingGeneratedTokenIndex": first_difference(u["generatedTokenIds"], v["generatedTokenIds"]),
               "activationMaxAbsoluteDifference": numeric_difference(u["activation"], v["activation"]),
               "projectionMaxAbsoluteDifference": numeric_difference(u["projection"], v["projection"]),
               "fullResponseEqual": u == v,
               "differingResponsePaths": differing_paths(u, v),
               "responseFileSha256": [x["responseFileSha256"], y["responseFileSha256"]]}
        for field in ("promptTokenIds", "generatedTokenIds", "sampledTokenIds", "activation", "projection", "norms"):
            row[field+"Equal"] = u[field] == v[field]
            row[field+"Sha256"] = [canonical_sha(u[field]), canonical_sha(v[field])]
        if x["operation"] == "generate_journal":
            row.update({"textEqual": u["text"] == v["text"], "textSha256": [sha(u["text"].encode()), sha(v["text"].encode())],
                        "firstDifferingTextCharacterIndex": first_difference(u["text"], v["text"])})
        pairs.append(row)
    numerical = lambda state: {k:state[k] for k in ("step", "observationIndex", "reservoir", "trace", "pendingRequest", "failed")}
    numeric_states = [numerical(x["record"]["state"]) for x in (a,b)]
    states = [x["record"]["state"] for x in (a,b)]
    journal_pairs = [p for p in pairs if p["operation"] == "generate_journal"]
    quiet_pairs = [p for p in pairs if p["operation"] == "quiet_capture"]
    result = {"schema": "activation-repeat-and-resource-summary/1", "scope": "Exploratory same-arm repeat; no cross-arm contrast",
              "sources": [a["source"], b["source"]], "analysisSourceSha256": file_sha(Path(__file__)),
              "frozenApparatus": {"binarySha256": [p["binarySha256"] for p in plans],
                                  "modelManifestSha256": [p["modelManifest"]["sha256"] for p in plans],
                                  "binaryIdentityEqual": plans[0]["binarySha256"] == plans[1]["binarySha256"],
                                  "modelWorkerRuntimeManifestEqual": plans[0]["modelManifest"] == plans[1]["modelManifest"],
                                  "computationalProtocolFieldsCompared": list(protocol_fields),
                                  "computationalProtocolEqual": all(plans[0]["pilot"][k] == plans[1]["pilot"][k] for k in protocol_fields)},
              "calibrationEqual": a["calibration"] == b["calibration"],
              "counts": {"pairedOperations": len(pairs), "pairedQuietCaptures": len(quiet_pairs), "pairedJournals": len(journal_pairs),
                         "equalJournalTexts": sum(x["textEqual"] for x in journal_pairs),
                         "equalPromptTokenArrays": sum(x["promptTokenIdsEqual"] for x in pairs),
                         "equalGeneratedTokenArrays": sum(x["generatedTokenIdsEqual"] for x in pairs),
                         "equalActivationVectors": sum(x["activationEqual"] for x in pairs),
                         "equalProjectionVectors": sum(x["projectionEqual"] for x in pairs),
                         "pairedActivationCoordinates": len(pairs)*2560, "pairedProjectionCoordinates": len(pairs)*32,
                         "promptTokensPerSequence": [sum(p["promptTokens"][i] for p in pairs) for i in (0,1)],
                         "generatedContentTokensPerSequence": [sum(p["generatedContentTokens"][i] for p in pairs) for i in (0,1)],
                         "quietInputTokensPerSequence": [sum(p["promptTokens"][i] for p in quiet_pairs) for i in (0,1)],
                         "journalPromptTokensPerSequence": [sum(p["promptTokens"][i] for p in journal_pairs) for i in (0,1)],
                         "sampledJournalTokensIncludingEOSPerSequence": [sum(len(op["response"]["sampledTokenIds"]) for op in seq["operations"] if op["operation"] == "generate_journal") for seq in (a,b)],
                         "quietSampledTokensPerSequence": [sum(len(op["response"]["sampledTokenIds"]) for op in seq["operations"] if op["operation"] == "quiet_capture") for seq in (a,b)]},
              "pairs": pairs,
              "numericalAndLedgerEquality": {"specificationEqual": a["record"]["specification"] == b["record"]["specification"],
                  "completeRecordEqual": a["record"] == b["record"], "eventsEqual": a["record"]["events"] == b["record"]["events"],
                  "differingRecordPaths": differing_paths(a["record"], b["record"]),
                  "completeStateEqual": states[0] == states[1], "numericalStateEqual": numeric_states[0] == numeric_states[1],
                  "numericalStateSha256": [canonical_sha(s) for s in numeric_states], "finalSteps": [s["step"] for s in states]},
              "newResourceEvidence": resource_summary(new), "modelCalls": 0, "resourceCommandsExecuted": 0,
              "limitations": ["Same seed, matched apparatus and reused observations: this is not an independent replication or a cross-arm causal contrast.",
                              "Exact text/token identity does not establish meaning, continuity, benefit, agency, or experience.",
                              "Activation and norm comparisons use retained worker evidence, not a new measurement.",
                              "A command-identity absence observation does not independently prove ownership or reaping of a recorded worker PID."]}
    after = [inventory(old), inventory(new)]
    require(before == after, "An experimental directory changed during analysis")
    result["sourceInventories"] = before
    result["experimentalFilesUnchanged"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    old, new = args.old.resolve(strict=True), args.new.resolve(strict=True)
    result = analyze(old, new)
    payload = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n"
    if args.output:
        output = args.output.resolve()
        require(not any(output.is_relative_to(p) for p in (old,new)), "Output must be outside both experimental directories")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x") as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        print(json.dumps({"output": str(output), "sha256": sha(payload.encode()), "counts": result["counts"],
                          "numericalAndLedgerEquality": result["numericalAndLedgerEquality"]}))
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
