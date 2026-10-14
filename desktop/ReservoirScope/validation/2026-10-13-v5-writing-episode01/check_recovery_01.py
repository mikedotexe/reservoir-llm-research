#!/usr/bin/env python3
"""After explicit handoff, verify and compare two immutable v5 episode exports.

Preparation does not execute this script. Its only child command is the supplied
pinned offline --verify-sustained path. No app store, process, UI or service probe;
no new model call, main-checker rerun or modification of original evidence.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess


EXPECTED_EXE = "7d46719838495b7a9ba57eea69ac9c940bb81f2fdc47cd12b761d97bb472d081"
EXPECTED_SESSION = "sustained-1791942995555-1"
EXPECTED_ENDPOINT = "http://127.0.0.1:60782"
U64_MAX = 18446744073709551615


def require(condition, message):
    if not condition:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ordinary_parents(path):
    require(path.is_absolute(), "Input path must be absolute")
    for parent in path.parents:
        require(stat.S_ISDIR(parent.lstat().st_mode), f"Linked/nonordinary ancestor: {parent}")


def metadata(path):
    value = path.lstat()
    require(stat.S_ISREG(value.st_mode), f"Not an ordinary file: {path}")
    return {"device": value.st_dev, "inode": value.st_ino, "bytes": value.st_size,
            "modifiedNs": value.st_mtime_ns, "changedNs": value.st_ctime_ns}


def read(path, limit=32 * 1024 * 1024):
    ordinary_parents(path)
    before = metadata(path)
    require(before["bytes"] <= limit, f"Input exceeds bound: {path}")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
        opened = os.fstat(stream.fileno())
        require((opened.st_dev, opened.st_ino) == (before["device"], before["inode"]),
                "Input identity changed at open")
        raw = stream.read(limit + 1)
    require(len(raw) <= limit and before == metadata(path), f"File changed during read: {path}")
    return raw


def identity(path):
    raw = read(path)
    return {"path": str(path), "bytes": len(raw), "sha256": sha(raw)}


def inventory(folder):
    ordinary_parents(folder)
    require(stat.S_ISDIR(folder.lstat().st_mode), "Export root is not an ordinary directory")
    result, total = {}, 0
    for path in sorted(folder.rglob("*")):
        mode = path.lstat().st_mode
        require(stat.S_ISREG(mode) or stat.S_ISDIR(mode), f"Linked/nonordinary export member: {path}")
        if stat.S_ISDIR(mode):
            continue
        item = identity(path)
        total += item["bytes"]
        require(total <= 64 * 1024 * 1024 and len(result) < 1000,
                "Bounded episode export inspection limit exceeded")
        result[str(path.relative_to(folder))] = {k: item[k] for k in ("bytes", "sha256")}
    require("manifest.json" in result, "No export manifest")
    return result


def pairs_unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON member: {key}")
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=pairs_unique,
                      parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))


def exact(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(exact(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return left == right


def decimal(value):
    require(type(value) is str and re.fullmatch(r"(?:0|[1-9][0-9]*)", value) is not None,
            "Generation/revision must be a canonical decimal string")
    parsed = int(value)
    require(0 < parsed <= U64_MAX, "Generation/revision outside positive u64")
    return parsed


def changed_manifest(old, new):
    require(old.keys() == new.keys(), "Manifest members changed")
    changes = [{"field": key, "original": old[key], "recovered": new[key]}
               for key in sorted(old) if not exact(old[key], new[key])]
    fields = {row["field"] for row in changes}
    require(fields in ({"generation", "revision"}, {"generation", "phase", "revision"}),
            "Manifest differs outside the explicit restore metadata")
    require(decimal(new["generation"]) == decimal(old["generation"]) + 1,
            "Expected one generation increment on this restore")
    require(decimal(new["revision"]) == decimal(old["revision"]) + 1,
            "Expected one revision increment on this restore")
    require(new["phase"] == "paused", "Recovered wrapper is not paused")
    return changes


def bounded_int(value, name):
    require(type(value) is int and 0 <= value <= U64_MAX, f"Invalid {name}")
    return value


def separate_outcomes(manifest, state, continuity):
    """Integrity, twelve-entry completion and resource limits are distinct."""
    require(continuity["plannedOpportunities"] == 12
            and len(continuity["slots"]) == 12
            and continuity["outcome"] in ("complete", "partial", "unstarted"),
            "Original twelve-slot qualification is missing")
    for flag, total in continuity["totals"].items():
        require(type(total) is int
                and total == sum(slot.get(flag) is True for slot in continuity["slots"]),
                f"Original slot count differs: {flag}")
    cfg = manifest["config"]
    step = bounded_int(manifest["step"], "step")
    attempt = bounded_int(state["attemptCursor"], "attempt count")
    elapsed = bounded_int(manifest["elapsedMillis"], "active elapsed milliseconds")
    step_limit = bounded_int(cfg["maximumSteps"], "step limit")
    attempt_limit = bounded_int(cfg["maximumTurns"], "attempt limit")
    duration_limit = bounded_int(cfg["maximumDurationSeconds"], "duration limit")
    require(step == state["step"] == manifest["durableStep"], "Live/durable checkpoint steps differ")
    return {
        "originalContinuityOutcome": continuity["outcome"],
        "fullTwelveEntryContinuityWitnessed": continuity["fullTwelveEntryContinuityWitnessed"],
        "slotTotals": continuity["totals"], "slots": continuity["slots"],
        "step": step, "attemptCount": attempt, "journalCount": manifest["journalCount"],
        "elapsedMillis": elapsed, "finalCorePhase": state["phase"]["kind"],
        "configuredStepLimitReached": step >= step_limit,
        "configuredAttemptLimitReached": attempt >= attempt_limit,
        "configuredActiveDurationLimitReached": elapsed >= duration_limit * 1000,
        "originalWrapperPhase": manifest["phase"],
        "limit": "A configured limit can be reached while the writing outcome remains partial. Paused wrapper does not turn blocked/prepared core evidence into ready/applied evidence. Storage headroom, current controls, provider processing and prose quality are not inferred here.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--recovered", type=Path, required=True)
    parser.add_argument("--original-receipt", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for name in ("original", "recovered", "original_receipt", "executable", "output"):
        setattr(args, name, getattr(args, name).absolute())
    require(not args.output.exists(), "Output must be new/exclusive; preserve earlier outcomes")
    require(args.output.parent == Path(__file__).absolute().parent,
            "Write only a new receipt in this episode directory")
    require(args.original != args.recovered, "Exports must be distinct")
    require(not any(args.output.is_relative_to(p) for p in (args.original, args.recovered)),
            "Output cannot be inside an inspected bundle")
    result = {
        "schema": "reservoir-v5-episode-recovery-audit-v1", "startedAtUtc": utc(),
        "script": identity(Path(__file__).absolute()), "status": "failed",
        "modelOrProviderCalls": False, "uiOrProcessInspection": False,
        "mainCheckerRerun": False,
        "scope": "Pinned offline verification and immutable file comparison after explicit handoff; native quit/relaunch/Restore actions must be qualified separately.",
    }
    original_before = recovered_before = original_receipt_raw = None
    try:
        original_receipt_raw = read(args.original_receipt)
        qualification = decode(original_receipt_raw)
        require(qualification["status"] == "passed" and qualification["originalUnchanged"] is True,
                "Original export qualification did not pass")
        require(qualification["bundle"] == str(args.original), "Original receipt targets another bundle")
        require(qualification["expectedPromptVersion"] == "reservoir-journal-v5"
                and qualification["pinnedExecutable"]["sha256"] == EXPECTED_EXE,
                "Original prompt/version verifier identity differs")
        result["originalQualification"] = identity(args.original_receipt)
        original_before = inventory(args.original)
        recovered_before = inventory(args.recovered)
        require(exact(original_before, qualification["inventoryBefore"]),
                "Original differs from its qualified inventory")
        require(original_before.keys() == recovered_before.keys(), "Recovered file set differs")
        changed = [{"path": path, "original": original_before[path], "recovered": recovered_before[path]}
                   for path in sorted(original_before) if original_before[path] != recovered_before[path]]
        require([row["path"] for row in changed] == ["manifest.json"],
                "Recovery changed retained history or checkpoint bytes")
        old = decode(read(args.original / "manifest.json"))
        new = decode(read(args.recovered / "manifest.json"))
        require(old["sessionId"] == new["sessionId"] == EXPECTED_SESSION,
                "Export is not the explicitly handed-off episode")
        require(old["config"]["promptVersion"] == "reservoir-journal-v5"
                and old["config"]["language"]["endpoint"] == EXPECTED_ENDPOINT,
                "Version or declared owned endpoint differs")
        differences = changed_manifest(old, new)
        checkpoint_hash = old["checkpointSha256"]
        require(re.fullmatch(r"[0-9a-f]{64}", checkpoint_hash) is not None,
                "Invalid checkpoint identity")
        checkpoint_raw = read(args.original / "checkpoints" / f"{checkpoint_hash}.json")
        require(sha(checkpoint_raw) == checkpoint_hash, "Checkpoint file hash differs")
        checkpoint = decode(checkpoint_raw)
        require(exact(checkpoint["state"]["phase"], qualification["evidence"]["finalCorePhase"]),
                "Original core outcome differs from qualification")
        result["outcomePreservation"] = separate_outcomes(
            old, checkpoint["state"], qualification["evidence"]["continuity"])
        result["outcomePreservation"]["recoveredWrapperPhase"] = new["phase"]
        result["exportComparison"] = {
            "original": str(args.original), "recovered": str(args.recovered),
            "originalInventory": original_before, "recoveredInventory": recovered_before,
            "fileCountEach": len(original_before), "identicalNonManifestFiles": len(original_before) - 1,
            "changedFiles": changed, "manifestChanges": differences,
            "checkpointBytesIdentical": True, "noNewRetainedEventsOrApplications": True,
        }
        exe_before = identity(args.executable)
        require(exe_before["sha256"] == EXPECTED_EXE, "Pinned 0.17 executable identity differs")
        result["executableBefore"] = exe_before
        command = [str(args.executable), "--verify-sustained", str(args.recovered)]
        started = utc()
        run = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
        result["recoveredReplay"] = {
            "command": command, "startedAtUtc": started, "endedAtUtc": utc(),
            "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr,
        }
        require(run.returncode == 0, "Recovered production replay failed")
        replay = decode(run.stdout.encode())
        require(replay["status"] == "passed" and replay["modelsContacted"] is False,
                "Recovered replay did not report model-free success")
        report = replay["report"]
        require(report["sessionId"] == EXPECTED_SESSION
                and report["step"] == new["step"]
                and report["journalCount"] == new["journalCount"]
                and report["segmentCount"] == new["segmentCount"]
                and report["manifestSha256"] == recovered_before["manifest.json"]["sha256"]
                and report["checkpointSha256"] == checkpoint_hash,
                "Replay report does not bind the inspected recovered bundle")
        result["executableAfter"] = identity(args.executable)
        require(exact(result["executableAfter"], exe_before), "Pinned executable changed")
        result["status"] = "passed"
    except Exception as error:
        result["error"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        try:
            if original_before is not None:
                result["originalUnchanged"] = exact(inventory(args.original), original_before)
                require(result["originalUnchanged"], "Original export changed during audit")
            if recovered_before is not None:
                result["recoveredUnchanged"] = exact(inventory(args.recovered), recovered_before)
                require(result["recoveredUnchanged"], "Recovered export changed during audit")
            if original_receipt_raw is not None:
                result["originalQualificationUnchanged"] = read(args.original_receipt) == original_receipt_raw
                require(result["originalQualificationUnchanged"], "Original qualification changed")
        except Exception as error:
            result["status"] = "failed"
            result["preservationError"] = {"type": type(error).__name__, "message": str(error)}
    result["endedAtUtc"] = utc()
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"status": result["status"], "receipt": str(args.output),
                      "sha256": sha(read(args.output)), "error": result.get("error")}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
