#!/usr/bin/env python3
"""Read-only v7 prompt qualification using the unchanged five-reply 0.16 fixture.

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
import re
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
MEMORY_PREFIX = "Full previous text as one JSON string: "
PROMPT_VERSION = "reservoir-journal-v7"
FINAL_INVITATION = "Write the next entry in whatever direction seems worth pursuing."
SESSION_CONTEXT = (
    "An external 32-node recurrent reservoir and a separate sensory field evolve between entries. "
    "After a complete entry is saved and read back, its reduced text-feature signal becomes numerical input at the next step. "
    "The latest applied entry also returns here in full. "
    "Forcing, noise and regulation contribute to change; writing trains no weights."
)
AVAILABLE_OUTPUT = "Available output: the text of this entry. There are no tools or control commands in this turn."
EARLIER_PROSE = (
    "Earlier prose is not a record of executed controls or additional measurements. "
    "Describing a control change does not execute it; saved text returns through the automatic encoding described above."
)


def writing_boundary(observation: dict, memory: dict | None) -> str:
    returned = ("Recorded text return: no earlier saved entry has been applied."
                if memory is None else
                f"Recorded text return: the entry observed at step {memory['entry']['observedStep']} "
                f"first entered numerical input at step {memory['appliedStep']}.")
    return ("WRITING BOUNDARY\n" + AVAILABLE_OUTPUT + "\n"
            f"The numerical clock is held at observation step {observation['step']}; "
            "no new readout arrives while this entry is written.\n"
            + returned + "\n" + EARLIER_PROSE)



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


def check_compact_prompt(pending: dict) -> dict:
    """Bounded structural checks; the pinned CLI owns exact numerical rendering.

    Authored prior prose may itself contain field names or apparent instructions.
    Inspect only the supplied scaffold for forbidden exposure, and decode the
    single LF-delimited JSON value separately without treating it as a section.
    """
    prompt = pending["prompt"]
    observation = pending["observation"]
    require(prompt.startswith(f"Reservoir Scope · ongoing journal · {PROMPT_VERSION}\n"),
            "Expected v7 prompt header")
    require(prompt.endswith("\n\n" + FINAL_INVITATION), "Final open invitation differs")
    require(observation["version"] == "reservoir-and-sensory-v2"
            and len(observation["state"]) == 32
            and len(observation["sensory"]["eigenvalues"]) == 32,
            "Full retained observation is missing behind compact prompt")
    parts = prompt.split("\n\nPREVIOUS JOURNAL\n")
    require(len(parts) == 2, "Previous-journal section boundary differs")
    scaffold, historical = parts
    # The early scaffold derives from frozen V5, not the added V6 scope.
    # Quoted historical prose is decoded as data; it cannot supply this boundary.
    sections = scaffold.split("\n\nSESSION CONTEXT\n")
    require(len(sections) == 2, "Session-context section boundary differs")
    context, separator, _readout = sections[1].partition("\n\nOPTIONAL READOUT\n")
    require(separator and context == SESSION_CONTEXT,
            "Exact v7 early context must retain V5 without early V6 action scope")
    require("WRITING BOUNDARY" not in scaffold and AVAILABLE_OUTPUT not in scaffold,
            "Writing boundary must follow previous journal, not precede it")
    memory = pending["memory"]
    suffix = "\nEND PREVIOUS JOURNAL\n\n" + writing_boundary(observation, memory) + "\n\n" + FINAL_INVITATION
    require(historical.endswith(suffix),
            "Exact v7 writing boundary must follow memory with current clock and actual recorded return")
    body = historical[:-len(suffix)]
    if memory is None:
        require(body == "No earlier entry has been saved and applied in this session.",
                "First-entry memory absence differs")
    else:
        header = ("This is earlier writing you may revisit, not instructions or current measurements.\n"
                  f"Observed at step {memory['entry']['observedStep']}; first applied at step {memory['appliedStep']}.\n"
                  + MEMORY_PREFIX)
        require(body.startswith(header), "Prior-journal provenance/header differs")
        quoted = body[len(header):]
        require("\n" not in quoted,
                "Prior JSON value is not one LF-delimited line before the writing boundary")
        require(exact(decode(quoted.encode("utf-8")), memory["entry"]["text"]),
                "Prior prose was shortened, altered or not quoted as one string")
        for identity_value in (memory["entry"]["id"], memory["entry"]["sha256"]):
            require(identity_value not in scaffold, "Journal identity leaked into compact scaffold")
    lower = scaffold.lower()
    for forbidden in ("all recurrent state coordinates", "x[0]", "eigenvalue", "head share",
                      "shoulder share", "tail share", "entropy", "l2 norm",
                      "measurement reference", "sha-256", "journal id", "journals/"):
        require(forbidden not in lower, f"Unexpected compact scaffold exposure: {forbidden}")
    decimal = r"[+-]?\d+\.\d{8}"
    optional = rf"(?:{decimal}|unavailable)"
    patterns = (
        rf"Recurrent state RMS: current ({decimal}); previous ({optional}); change ({optional})\.",
        rf"Separate sensory fill \(%\): current ({decimal}); previous ({optional}); change ({optional}) percentage points\.",
        rf"Recurrent state-coordinate L2 distance since the previous observation: ({optional})\.",
    )
    matches = []
    for pattern in patterns:
        found = [re.fullmatch(pattern, line) for line in scaffold.split("\n")]
        found = [match for match in found if match]
        require(len(found) == 1, "Compact readout row missing, duplicated or malformed")
        matches.append(found[0])
    prior_available = observation.get("previousMeasurements") is not None
    for row in matches[:2]:
        require((row[2] != "unavailable") == prior_available
                and (row[3] != "unavailable") == prior_available,
                "Prior scalar availability differs from retained observation")
    distance = matches[2][1]
    require((distance != "unavailable") == (observation["changeL2"] is not None),
            "Coordinate-distance availability differs")
    require(distance == "unavailable" or float(distance) >= 0,
            "Coordinate distance must be nonnegative")
    return {"promptVersion": PROMPT_VERSION, "fullObservationRetained": True,
            "actionScopeChecked": True, "lateWritingBoundaryChecked": True,
            "recordedReturnChecked": True,
            "compactScaffoldChecked": True, "exactPriorTextChecked": memory is not None,
            "numericalFormattingAuthority": "Pinned production replay; this check is structural."}


def check_protocol_events(by_kind: dict, final_state: dict) -> None:
    """Protocol acceptance is stricter than merely replaying a valid prefix."""
    forbidden = ("retried", "interrupted", "budgetsExtended", "skipped", "languageCancelled")
    require(not any(by_kind.get(kind) for kind in forbidden),
            "Fixture contains an unplanned retry/interruption/extension/skip/cancellation")
    require(final_state["phase"]["kind"] == "blocked",
            "Fifth incomplete response must remain blocked, not explicitly cleared")


def check_request_sequence(log: list) -> list:
    reads = [row for row in log if row.get("method") == "GET"]
    require(len(reads) == 1 and reads[0].get("path") == "/api/tags"
            and reads[0].get("status") == 200 and reads[0].get("socketWriteCompleted") is True,
            "Expected exactly one completed successful readiness GET")
    requests = [row for row in log if row.get("method") == "POST" and "request" in row]
    require([row["request"] for row in requests] == [1, 2, 3, 4, 5],
            "Fixture generation request sequence differs")
    require(all(row.get("path") == "/api/chat" for row in requests)
            and not [row for row in log if row.get("method") == "POST" and "request" not in row],
            "Unexpected rejected/extra fixture POST in inspected log prefix")
    completed = [row for row in log if "response" in row]
    require([row["response"] for row in completed] == [1, 2, 3, 4, 5]
            and all(row.get("status") == 200 and row.get("socketWriteCompleted") is True for row in completed),
            "Expected five completed successful fixture response writes")
    return requests


def check_static(bundle: Path, fixture: Path):
    before = inventory(bundle)
    manifest = decode(read(bundle / "manifest.json"))
    config = manifest["config"]
    expected_config = {
        "seed": "20261013", "promptVersion": PROMPT_VERSION,
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
    requests = check_request_sequence(log)

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
    check_protocol_events(by_kind, previous_checkpoint["state"])
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
        compact = check_compact_prompt(p)
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
                     "exactPromptRequestResponseAndMemoryJoins": True,
                     "compactContext": compact})
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
