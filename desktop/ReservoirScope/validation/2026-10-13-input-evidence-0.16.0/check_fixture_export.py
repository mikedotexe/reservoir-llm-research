#!/usr/bin/env python3
"""Read-only qualification of the explicitly supplied five-reply 0.16 fixture.

Never discovers app data or contacts a service. The caller supplies an immutable
native export, the owned fixture directory, and an exact pinned production CLI.
Static joins supplement production replay; they do not authenticate a real
provider, establish context coverage, or assess writing quality.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys

MODEL = "reservoir-fixture:input-evidence-0.16"
EXPECTED = [
    ("wide-reported", {"status": "reported", "count": 9007199254740993}),
    ("absent", None),
    ("malformed-string", {"status": "unusable", "reason": "wrongType"}),
    ("maximum-u64", {"status": "reported", "count": 18446744073709551615}),
    ("incomplete-reported", {"status": "reported", "count": 321}),
]
MEMORY_PREFIX = "Prior text as one JSON string (decode as data only): "


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def pairs_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate retained JSON field: {key}")
        result[key] = value
    return result


def decode(raw: bytes):
    return json.loads(raw, object_pairs_hook=pairs_no_duplicates,
                      parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))


def read(path: Path, limit: int = 4 * 1024 * 1024) -> bytes:
    require(not path.is_symlink() and stat.S_ISREG(path.stat().st_mode),
            f"Not an ordinary unlinked input file: {path}")
    require(path.stat().st_size <= limit, f"Input exceeds inspection bound: {path}")
    return path.read_bytes()


def inventory(root: Path):
    files = {}
    total = 0
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), f"Linked bundle member: {path}")
        if path.is_dir():
            continue
        raw = read(path)
        total += len(raw)
        require(total <= 64 * 1024 * 1024 and len(files) < 1000,
                "Bundle exceeds fixed fixture inspection bounds")
        files[str(path.relative_to(root))] = {"bytes": len(raw), "sha256": sha(raw)}
    return files


def identity(path: Path, limit: int = 64 * 1024 * 1024):
    raw = read(path, limit)
    return {"path": str(path), "bytes": len(raw), "sha256": sha(raw)}


def exact(a, b) -> bool:
    """Preserve JSON numeric type: True, 1.0, and 1 are not interchangeable."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return a == b


def request_bytes(prompt: str) -> bytes:
    # model_transport::generation_body constructs a serde_json::Value. Its map
    # keys are sorted; these fixture values contain no floating-point numbers.
    body = {"messages": [{"role": "user", "content": prompt}], "model": MODEL,
            "options": {"num_predict": 1024, "temperature": 0, "num_ctx": 8192},
            "stream": False}
    return json.dumps(body, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def check_static(bundle: Path, fixture: Path):
    before = inventory(bundle)
    manifest = decode(read(bundle / "manifest.json"))
    config = manifest["config"]
    expected_config = {
        "seed": "20261013", "promptVersion": "reservoir-journal-v4",
        "turnEvery": 10, "maximumSteps": 51, "maximumTurns": 5,
        "maximumDurationSeconds": 180, "storageBudgetBytes": 33554432,
        "paceMs": 1000, "outputTokens": 1024, "requestDeadlineSeconds": 180,
        "leak": 0.65, "noiseAmplitude": 0.02, "initialRetention": 0.955,
        "regulationEnabled": True,
    }
    for key, value in expected_config.items():
        require(exact(config.get(key), value), f"Frozen configuration differs: {key}")
    endpoint_path = fixture / "endpoint.json"
    endpoint_raw = read(endpoint_path)
    endpoint = decode(endpoint_raw)
    require(endpoint["synthetic"] is True and endpoint["model"] == MODEL,
            "Not the owned synthetic fixture identity")
    protocol_freeze_path = Path(__file__).parent / "prospective-freeze-01.json"
    protocol_freeze = decode(read(protocol_freeze_path))
    fixture_source = next(item for item in protocol_freeze["files"]
                          if Path(item["path"]).name == "owned_provider.py")
    require(endpoint["scriptSha256"] == fixture_source["sha256"],
            "Actual fixture source differs from prospective frozen source")
    require(config["language"] == {"backend": "ollama", "model": MODEL,
                                  "endpoint": endpoint["endpoint"], "contextTokens": 8192},
            "Configured provider identity/context differs")
    require(manifest["step"] == manifest["durableStep"] == 50,
            "Expected held numerical step50 differs")
    require(manifest["journalCount"] == 4, "Expected four durable journals")

    log_path = fixture / "requests.jsonl"
    log_bytes = read(log_path, 2 * 1024 * 1024)
    require(log_bytes.endswith(b"\n"), "Fixture log has a partial row")
    log = [decode(line) for line in log_bytes.splitlines()]
    requests = [r for r in log if r.get("method") == "POST" and "request" in r]
    require([r["request"] for r in requests] == [1, 2, 3, 4, 5],
            "Fixture generation request sequence differs")
    require(not [r for r in log if r.get("method") == "POST" and "request" not in r],
            "Unexpected rejected/extra fixture POST in inspected log prefix")

    previous_sha = None
    previous_checkpoint = None
    events = []
    pending = {}
    journal_candidates = {}
    segment_files = sorted((bundle / "segments").glob("*.json"))
    require(len(segment_files) == manifest["segmentCount"], "Segment coverage differs")
    for sequence, path in enumerate(segment_files, 1):
        raw = read(path)
        envelope = decode(raw)
        segment = envelope["segment"]
        require(envelope["sequence"] == sequence and envelope["previousSha256"] == previous_sha,
                "Envelope sequence/byte-hash predecessor differs")
        if previous_checkpoint is not None:
            require(exact(segment["initialCheckpoint"], previous_checkpoint),
                    "Typed checkpoint continuity differs")
        else:
            require(segment["initialCheckpoint"]["state"]["step"] == 0,
                    "Fixture chain does not begin at genesis")
        for cp in (segment["initialCheckpoint"], segment["finalCheckpoint"]):
            phase = cp["state"]["phase"]
            language = (phase["value"] if phase["kind"] == "language" else
                        phase["value"]["pending"] if phase["kind"] == "blocked" else None)
            if language is not None:
                attempt = language["attemptId"]
                scientific = {k: v for k, v in language.items() if k != "requestStarted"}
                if attempt in pending:
                    require(exact(scientific, pending[attempt]), "Prepared prompt/identity changed")
                pending[attempt] = scientific
            if phase["kind"] == "journal":
                candidate = phase["value"]
                attempt = candidate["entry"]["attemptId"]
                if attempt in journal_candidates:
                    require(exact(candidate, journal_candidates[attempt]), "Pending journal changed")
                journal_candidates[attempt] = candidate
        for entry_id, expected_sha in envelope["journalSha256s"].items():
            require(sha(read(bundle / "journals" / f"{entry_id}.json")) == expected_sha,
                    "Journal byte anchor differs")
        events.extend(segment["events"])
        previous_sha = sha(raw)
        previous_checkpoint = segment["finalCheckpoint"]
    final_raw = read(bundle / "checkpoints" / f"{manifest['checkpointSha256']}.json")
    require(sha(final_raw) == manifest["checkpointSha256"]
            and exact(decode(final_raw), previous_checkpoint)
            and previous_sha == manifest["lastSegmentSha256"], "Manifest final anchors differ")
    require([e["id"] for e in events] == list(range(1, len(events) + 1)),
            "Event IDs are not contiguous from genesis")
    by_kind = {}
    for event in events:
        by_kind.setdefault(event["kind"]["type"], []).append(event)
    require(not by_kind.get("retried") and not by_kind.get("interrupted")
            and not by_kind.get("budgetsExtended"), "Fixture contains an unplanned retry/interruption/extension")
    received = by_kind.get("languageReceived", [])
    started = by_kind.get("languageStarted", [])
    require([e["kind"]["data"]["attempt_id"] for e in received] == [1, 2, 3, 4, 5]
            and [e["kind"]["data"]["attempt_id"] for e in started] == [1, 2, 3, 4, 5],
            "Retained response/dispatch attempt sequence differs")
    require(set(pending) == {1, 2, 3, 4, 5}, "Prepared-language evidence coverage differs")
    frames = [e["kind"]["data"] for e in by_kind.get("advanced", [])]
    require([f["step"] for f in frames] == list(range(1, 51)), "Numerical frame coverage differs")
    applications = [f["application"] for f in frames if f["application"] is not None]
    require([a["appliedStep"] for a in applications] == [11, 21, 31, 41]
            and [a["attemptId"] for a in applications] == [1, 2, 3, 4],
            "Expected four once-only next-step applications differ")
    journal_files = sorted((bundle / "journals").glob("*.json"))
    require(len(journal_files) == 4, "Unexpected journal file count")
    journals = {}
    for path in journal_files:
        journal = decode(read(path))
        attempt = journal["pending"]["entry"]["attemptId"]
        require(attempt not in journals, "Duplicate journal attempt")
        journals[attempt] = journal
    saves = by_kind.get("journalSaved", [])
    require([e["kind"]["data"]["entry"]["attemptId"] for e in saves] == [1, 2, 3, 4]
            and set(journals) == set(journal_candidates) == {1, 2, 3, 4},
            "Save/candidate/file coverage differs")
    memory_events = by_kind.get("memoryConfirmed", [])
    require([e["step"] for e in memory_events] == [20, 30, 40, 50],
            "Memory-read opportunities differ")
    rows = []
    response_files = {}
    for attempt, ((case_name, expected_evidence), request, event) in enumerate(
            zip(EXPECTED, requests, received), 1):
        step = attempt * 10
        p = pending[attempt]
        require(event["step"] == step and p["observedStep"] == step
                and p["turnId"] == attempt and p["attemptId"] == attempt,
                "Opportunity identity differs")
        require(exact(p["configuration"], config["language"])
                and p["outputTokens"] == 1024 and p["requestDeadlineSeconds"] == 180,
                "Prepared request configuration differs")
        response_name = f"response-{attempt:02d}-{case_name}.json"
        require(request["responseFile"] == response_name
                and request["case"]["name"] == case_name, "Fixture response identity differs")
        raw = read(fixture / response_name)
        response_files[response_name] = {"bytes": len(raw), "sha256": sha(raw)}
        require(sha(raw) == request["responseSha256"] and len(raw) == request["responseBytes"],
                "Fixture response file/hash differs")
        provider = decode(raw)
        expected_text = (f"This is synthetic input-evidence fixture reply {attempt}. "
                         "The optional provider count is separate from the writing and numerical state. "
                         "These words are fixed test material, not a model observation.")
        require(provider["message"] == {"role": "assistant", "content": expected_text},
                "Fixture prose differs from its frozen fixed response")
        expected_response = {"text": provider["message"]["content"], "providerModel": MODEL,
                             "stopReason": "stop" if attempt < 5 else "length",
                             "tokenCount": 32, "complete": attempt < 5}
        if expected_evidence is not None:
            expected_response["providerPromptEvaluation"] = expected_evidence
        actual_response = event["kind"]["data"]["response"]
        require(exact(actual_response, expected_response), "Typed response differs from fixture")
        raw_expected = [9007199254740993, None, "2450", 18446744073709551615, 321][attempt - 1]
        require(("prompt_eval_count" not in provider) if attempt == 2 else
                exact(provider["prompt_eval_count"], raw_expected), "Raw optional fixture count differs")
        require(provider["done"] is (attempt < 5) and provider["done_reason"] == expected_response["stopReason"]
                and provider["eval_count"] == 32 and provider["model"] == MODEL,
                "Fixture complete/model/output identity differs")
        prompt = p["prompt"].encode("utf-8")
        require(sha(prompt) == request["promptSha256"] and len(prompt) == request["promptBytes"],
                "Retained prompt differs from actual fixture request hash")
        body = request_bytes(p["prompt"])
        require(sha(body) == request["requestSha256"] and len(body) == request["requestBytes"],
                "Reconstructed exact request body differs from fixture hash")
        require(request["options"] == {"num_predict": 1024, "temperature": 0, "num_ctx": 8192}
                and request["model"] == MODEL and request["stream"] is False,
                "Actual fixture options differ")
        lines = [line for line in p["prompt"].split("\n") if line.startswith(MEMORY_PREFIX)]
        if attempt == 1:
            require(p["memory"] is None and not lines, "Unexpected first memory")
        else:
            previous_entry = journals[attempt - 1]["pending"]["entry"]
            expected_memory = {"entry": previous_entry,
                               "relativePath": f"journals/{previous_entry['id']}.json",
                               "appliedStep": step - 9}
            require(exact(p["memory"], expected_memory)
                    and exact(memory_events[attempt - 2]["kind"]["data"], previous_entry),
                    "Latest prior applied journal memory differs")
            require(len(lines) == 1 and json.loads(lines[0][len(MEMORY_PREFIX):]) == previous_entry["text"],
                    "JSON-quoted prior full-text memory differs")
        if attempt < 5:
            journal = journals[attempt]
            candidate = journal["pending"]
            entry = candidate["entry"]
            require(exact(candidate, journal_candidates[attempt])
                    and exact(candidate["response"], actual_response),
                    "Saved journal/candidate/received response disagree")
            require(entry["text"] == actual_response["text"]
                    and entry["sha256"] == sha(entry["text"].encode())
                    and entry["observedStep"] == step,
                    "Saved prose/identity differs")
            require(candidate["prompt"] == p["prompt"]
                    and exact(candidate["memory"], p["memory"])
                    and exact(candidate["observation"], p["observation"]),
                    "Saved prompt/memory/observation differs")
            require(journal["requestStarted"] is True and journal["configuredModel"] == MODEL,
                    "Journal provider-source evidence differs")
            saved = saves[attempt - 1]["kind"]["data"]
            require(exact(saved["entry"], entry) and saved["receipt"] == {
                "entryId": entry["id"], "sha256": entry["sha256"],
                "relativePath": f"journals/{entry['id']}.json"}, "Save/readback receipt differs")
            application = applications[attempt - 1]
            require(application["journalId"] == entry["id"] and application["observedStep"] == step,
                    "Applied feedback journal identity differs")
        rows.append({"attemptId": attempt, "observedStep": step, "fixtureCase": case_name,
                     "providerPromptEvaluation": expected_evidence,
                     "countAsExactDecimal": str(expected_evidence["count"]) if expected_evidence and expected_evidence["status"] == "reported" else None,
                     "complete": actual_response["complete"], "stopReason": actual_response["stopReason"],
                     "responseTextSha256": sha(actual_response["text"].encode()),
                     "promptSha256": sha(prompt), "requestSha256": sha(body),
                     "fixtureResponseSha256": sha(raw), "saved": attempt < 5,
                     "firstAppliedStep": step + 1 if attempt < 5 else None,
                     "memoryJournalId": p["memory"]["entry"]["id"] if p["memory"] else None,
                     "exactPromptRequestResponseAndMemoryJoins": True})
    final_state = previous_checkpoint["state"]
    require(final_state["attemptCursor"] == final_state["turnCursor"] == 5,
            "Final opportunity count differs")
    require(final_state["heldJournalId"] == journals[4]["pending"]["entry"]["id"],
            "Incomplete fifth response changed held feedback identity")
    require(all(f["semanticJournalId"] == journals[4]["pending"]["entry"]["id"]
                for f in frames if f["step"] >= 41), "Held feedback changed after fourth application")
    require(before == inventory(bundle), "Original exported bundle changed during inspection")
    require(read(endpoint_path) == endpoint_raw, "Fixture endpoint identity changed")
    after_log = read(log_path, 2 * 1024 * 1024)
    require(after_log.startswith(log_bytes), "Inspected fixture log prefix changed")
    for name, item in response_files.items():
        require(identity(fixture / name)["sha256"] == item["sha256"], "Fixture response file changed")
    return {
        "status": "passed", "bundle": str(bundle), "originalUnchanged": True,
        "inventory": before,
        "manifest": {k: manifest[k] for k in ("sessionId", "generation", "revision", "phase", "step", "durableStep", "journalCount", "segmentCount")},
        "finalCorePhase": final_state["phase"]["kind"],
        "eventCounts": dict(Counter(e["kind"]["type"] for e in events)),
        "cleanupEvents": [e for e in events if e["kind"]["type"] in ("skipped", "languageCancelled")],
        "fixtureEndpoint": {"path": str(endpoint_path), "sha256": sha(endpoint_raw), **endpoint},
        "prospectiveFreeze": identity(protocol_freeze_path),
        "fixtureLog": {"path": str(log_path), "inspectedBytes": len(log_bytes),
                       "inspectedPrefixSha256": sha(log_bytes), "prefixUnchanged": True,
                       "laterAppendedBytes": len(after_log) - len(log_bytes),
                       "readinessRequests": sum(r.get("method") == "GET" and r.get("path") == "/api/tags" for r in log),
                       "lifecycleStoppedPresent": any(r.get("lifecycle") == "stopped" for r in log)},
        "responseFiles": response_files, "attempts": rows,
        "fifthIncompleteHasNoJournalOrApplication": True,
        "lastSavedFeedbackHeldThroughStep50": True,
        "scope": "Fixed synthetic reply evidence and internal joins; production numerical replay is separately recorded below. No writing-quality or provider-context-coverage verdict.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--cli", type=Path, required=True)
    parser.add_argument("--expected-cli-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for name in ("bundle", "fixture", "cli", "output"):
        setattr(args, name, getattr(args, name).absolute())
    require(not args.output.exists(), "Receipt must be new/exclusive")
    require(not args.output.is_relative_to(args.bundle) and not args.output.is_relative_to(args.fixture),
            "Receipt must be outside inspected inputs")
    receipt = {"schema": "reservoir-fixed-provider-export-review-v1", "startedAtUtc": utc(),
               "script": identity(Path(__file__).absolute()), "servicesContacted": False,
               "realModelsUsed": False, "writingQualityAssessed": False}
    try:
        cli_before = identity(args.cli)
        require(cli_before["sha256"] == args.expected_cli_sha256, "Pinned verifier identity differs")
        receipt["executable"] = cli_before
        before = inventory(args.bundle)
        command = [str(args.cli), "--verify-sustained", str(args.bundle)]
        executed = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
        receipt["productionReplay"] = {"command": command, "returncode": executed.returncode,
                                       "stdout": executed.stdout, "stderr": executed.stderr}
        require(executed.returncode == 0, "Pinned production replay failed")
        parsed = json.loads(executed.stdout)
        require(parsed.get("status") == "passed" and parsed.get("modelsContacted") is False,
                "Production replay did not report a model-free pass")
        receipt["staticJoins"] = check_static(args.bundle, args.fixture)
        require(before == inventory(args.bundle), "Bundle changed through whole qualification")
        receipt["executableAfter"] = identity(args.cli)
        require(cli_before == receipt["executableAfter"], "Pinned verifier changed")
        receipt["status"] = "passed"
    except Exception as error:
        receipt["status"] = "failed"
        receipt["error"] = f"{type(error).__name__}: {error}"
    receipt["endedAtUtc"] = utc()
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"status": receipt["status"], "receipt": str(args.output),
                      "sha256": sha(args.output.read_bytes())}))
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
