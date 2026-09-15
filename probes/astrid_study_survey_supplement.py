"""Read-only, bounded method supplement for the frozen 2026-09-15 survey.

Reads provider observer events by filename dispatch clock and indexed SQLite
actions, then joins immutable accepted-delivery wire hashes. Writes only the
new survey supplement. Never operates a reader, provider, or live state handle.
"""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "research/outputs/2026-09-15-astrid-study-survey"
OUT = PACKET / "supplement"
LIVE = Path("/Users/v/other/astrid/capsules/spectral-bridge/workspace")
LOW_MS = 1789465283000  # 2026-09-15T09:41:23Z; first selected journal minus 600s
HIGH_MS = 1789489841000  # frozen inclusive cutoff: 2026-09-15T16:30:41Z
TARGETS = (59, 60, 71, 74, 90)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("xb") as stream:
        os.chmod(path, 0o600)
        stream.write(raw)


def retain(path, kind, records):
    before = path.stat(follow_symlinks=False)
    if path.is_symlink() or not path.is_file() or before.st_size > 12 * 1024 * 1024:
        raise ValueError(f"Unsafe/oversize input: {path}")
    raw = path.read_bytes()
    after = path.stat(follow_symlinks=False)
    if (before.st_ino, before.st_mtime_ns, before.st_size) != (after.st_ino, after.st_mtime_ns, after.st_size):
        raise ValueError(f"Input changed while read: {path}")
    digest = sha(raw)
    destination = OUT / "raw" / kind / (digest + path.suffix)
    if not destination.exists():
        write(destination, raw)
    record = dict(source=str(path), retained=str(destination.relative_to(PACKET)),
                  kind=kind, sha256=digest, bytes=len(raw), mtime_ns=before.st_mtime_ns)
    records.append(record)
    return raw, record


def query(conn, sql, params, cap):
    plan = [list(row) for row in conn.execute("EXPLAIN QUERY PLAN " + sql, params)]
    if not any("SEARCH " in row[3] for row in plan):
        raise ValueError("Nonindexed data query refused")
    started = time.monotonic()
    conn.set_progress_handler(lambda: int(time.monotonic() - started > 5), 1000)
    try:
        rows = [dict(row) for row in conn.execute(sql, params).fetchmany(cap + 1)]
    finally:
        conn.set_progress_handler(None, 0)
    return dict(sql=sql, parameters=params, query_plan=plan, row_limit=cap,
                truncated=len(rows) > cap, rows=rows[:cap])


def capture():
    OUT.mkdir(mode=0o700, exist_ok=False)
    records, errors, observers = [], [], []
    started = datetime.now(timezone.utc).isoformat()
    directory = LIVE / "provider_observations/20260908-live-01/events"
    visited = candidates = 0
    scan_start = time.monotonic()
    for item in os.scandir(directory):
        visited += 1
        if visited > 100000 or time.monotonic() - scan_start > 30:
            raise ValueError("Provider event inventory resource ceiling")
        match = re.fullmatch(r"provider-(\d+)-(\d+)-(\d+)-(dispatch|outcome)\.json", item.name)
        if not match or not LOW_MS <= int(match[1]) <= HIGH_MS:
            continue
        candidates += 1
        path = Path(item.path)
        # Stable read before filtering label. Only study records are retained.
        before = path.stat(follow_symlinks=False)
        if path.is_symlink() or before.st_size > 1024 * 1024:
            raise ValueError("Unsafe/oversize observer metadata")
        raw = path.read_bytes()
        after = path.stat(follow_symlinks=False)
        if (before.st_ino, before.st_mtime_ns, before.st_size) != (after.st_ino, after.st_mtime_ns, after.st_size):
            raise ValueError("Observer changed while read")
        data = json.loads(raw)
        if data.get("label") != "self_study":
            continue
        retained, rec = retain(path, "provider_observer", records)
        assert raw == retained
        observers.append(dict(record=rec, data=data, filename_dispatch_ms=int(match[1]), filename_stage=match[4]))
    conn = sqlite3.connect((LIVE / "bridge.db").as_uri() + "?mode=ro", uri=True, timeout=3)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("BEGIN")
        actions = query(conn,
            "SELECT * FROM action_events WHERE action_id>=? AND action_id<? ORDER BY action_id LIMIT ?",
            [f"act_astrid_{LOW_MS}", f"act_astrid_{HIGH_MS + 1}", 3001], 3000)
        topics = query(conn,
            "SELECT topic,direction,COUNT(*) AS records FROM bridge_messages WHERE timestamp>=? AND timestamp<=? GROUP BY topic,direction ORDER BY topic,direction",
            [LOW_MS / 1000, HIGH_MS / 1000], 500)
    finally:
        conn.close()
    write(OUT / "actions.json", encode(actions))
    write(OUT / "topics.json", encode(topics))
    sequence = json.loads((PACKET / "linked-sequence.json").read_bytes())
    inventory = json.loads((PACKET / "journal-inventory.json").read_bytes())
    if isinstance(inventory, dict):
        inventory = inventory.get("entries", inventory.get("journals", []))
    targeted = []
    for ordinal in TARGETS:
        current, prior = sequence[ordinal - 1], sequence[ordinal - 2]
        for entry in inventory:
            if prior["epoch"] <= entry["epoch"] <= current["epoch"] and entry["mode"] != "self_study":
                _, rec = retain(Path(entry["path"]), "targeted_intervening_journal", records)
                targeted.append(dict(ordinal=ordinal, prior_journal=prior["name"], current_journal=current["name"], entry=entry, record=rec))
    result = dict(schema="astrid_study_survey_supplement_capture_v1", captured_utc=started,
        scope=dict(dispatch_start_ms=LOW_MS, dispatch_end_ms_inclusive=HIGH_MS,
                   observer_label="self_study", atomically_frozen=False,
                   actions="all verbs, indexed action-id dispatch clock", targeted_ordinals=list(TARGETS)),
        observer_scan=dict(directory=str(directory), visited=visited, filename_candidates=candidates,
                           retained_events=len(observers), complete=True),
        records=records, targeted_intervening_journals=targeted, errors=errors,
        probe_sha256=sha(Path(__file__).read_bytes()))
    write(OUT / "capture-index.json", encode(result))
    return result


def analyze(capture_index):
    accepted = []
    base = json.loads((PACKET / "capture-index.json").read_bytes())
    sequence = json.loads((PACKET / "linked-sequence.json").read_bytes())
    for item in base["files"]:
        if item["kind"] != "provider":
            continue
        data = json.loads((PACKET / item["retained"]).read_bytes())
        attempt = data["attempt"]
        response = json.loads(attempt["response_json"])
        choice = (response.get("choices") or [{}])[0]
        accepted.append(dict(retained=item["retained"], request_sha256=sha(attempt["request_json"].encode()),
            response_sha256=sha(attempt["response_json"].encode()),
            accepted_completion_sha256=sha(data["accepted_completion"].encode()),
            finish_reason=choice.get("finish_reason", response.get("done_reason")),
            usage=response.get("usage"), mtime_ns=item["mtime_ns"]))
    attempts = {}
    for rec in capture_index["records"]:
        if rec["kind"] != "provider_observer":
            continue
        data = json.loads((PACKET / rec["retained"]).read_bytes())
        item = attempts.setdefault(data["attempt_id"], dict(attempt_id=data["attempt_id"]))
        key = "dispatch" if data["stage"] == "dispatch_started" else "outcome"
        item[key] = dict(record=rec, data=data)
    for item in attempts.values():
        outcome = item.get("outcome")
        dispatch = item.get("dispatch")
        data = (outcome or dispatch)["data"]
        start = data["created_at_unix_ms"]
        end = start + data["elapsed_ms"] if outcome and isinstance(data.get("elapsed_ms"), (int, float)) else None
        matches = [row for row in accepted if row["request_sha256"] == data.get("request_sha256")
                   and row["response_sha256"] == data.get("http_body_sha256")]
        ordinals = [row["ordinal"] for row in sequence if any(match["retained"] in row.get("providers", []) for match in matches)]
        item.update(start_ms=start, approximate_end_ms=end,
            completed_by_cutoff=end is not None and end <= HIGH_MS,
            outcome_published_by_cutoff=bool(outcome and outcome["record"]["mtime_ns"] <= HIGH_MS * 1000000),
            accepted_wire_matches=matches, selected_journal_ordinals=ordinals,
            status=data.get("outcome") if outcome else "outcome_record_missing",
            provider=data.get("provider"), pid=data.get("pid"))
    values = sorted(attempts.values(), key=lambda x: (x["start_ms"], x["attempt_id"]))
    summary = dict(physical_attempts=len(values),
        dispatch_records=sum("dispatch" in x for x in values),
        outcome_records=sum("outcome" in x for x in values),
        outcomes=dict(Counter(x["status"] for x in values)),
        completed_by_cutoff=sum(x["completed_by_cutoff"] for x in values),
        published_by_cutoff=sum(x["outcome_published_by_cutoff"] for x in values),
        attempts_with_exact_accepted_wire=sum(bool(x["accepted_wire_matches"]) for x in values),
        attempts_joined_to_selected_journals=sum(bool(x["selected_journal_ordinals"]) for x in values),
        selected_journal_ordinals_joined=sorted({o for x in values for o in x["selected_journal_ordinals"]}),
        accepted_artifacts=len(accepted), providers=dict(Counter(x["provider"] for x in values)))
    report = dict(schema="astrid_study_survey_attempt_frame_v1", summary=summary, attempts=values,
        limitations=["Physical provider attempts are not all study opportunities: preparation can fail before dispatch.",
          "Dispatch receipt proves client send entry, not server acceptance.",
          "Approximate end uses dispatch wall clock plus monotonic elapsed time; event created_at stays dispatch time.",
          "Returned provider output is not equivalent to verified study delivery; use accepted wire join.",
          "Missing observer outcomes or missing records are not counted as completed; persistence coverage is not guaranteed by a directory census.",
          "Accepted delivery joins require exact serialized request AND HTTP response hashes; journal identity remains timestamp-assisted."])
    write(OUT / "provider-attempt-frame.json", encode(report))
    print(json.dumps(summary))


def summarize_retained():
    """Derive chronology from captured rows; never reread the live database."""
    capture_index = json.loads((OUT / "capture-index.json").read_bytes())
    actions = json.loads((OUT / "actions.json").read_bytes())
    sequence = json.loads((PACKET / "linked-sequence.json").read_bytes())
    parsed_actions = []
    for row in actions["rows"]:
        payload = json.loads(row["payload"])
        parsed_actions.append(dict(action_id=row["action_id"], timestamp=row["timestamp"],
            canonical_action=row["canonical_action"], status=row["status"], route=row["route"],
            raw_next=payload.get("raw_next"), parent_action_id=payload.get("parent_action_id"),
            source=payload.get("source"), outcome_summary=payload.get("outcome_summary"),
            row_sha256=sha(encode(row)), row_hash_basis="sorted, indented UTF-8 JSON with trailing newline"))
    traces = []
    for ordinal in TARGETS:
        prior, current = sequence[ordinal - 2], sequence[ordinal - 1]
        # One second before/after journal filename clocks accommodates fractional
        # action timestamps; retained originals expose every comparison boundary.
        candidates = [row for row in parsed_actions
                      if prior["epoch"] - 1 <= row["timestamp"] <= current["epoch"] + 1]
        journals = []
        for row in capture_index["targeted_intervening_journals"]:
            if row["ordinal"] != ordinal:
                continue
            text = (PACKET / row["record"]["retained"]).read_text()
            next_lines = [line for line in text.splitlines() if line.startswith("NEXT:")]
            journals.append(dict(name=row["entry"]["name"], epoch=row["entry"]["epoch"],
                retained=row["record"]["retained"], sha256=row["record"]["sha256"],
                literal_next_lines=next_lines,
                action_candidates=[x["action_id"] for x in candidates
                    if 0 <= x["timestamp"] - row["entry"]["epoch"] <= 5
                    and any(line.removeprefix("NEXT:").strip() == x["raw_next"] for line in next_lines)]))
        traces.append(dict(ordinal=ordinal, prior_journal=prior["name"],
            prior_literal_next_lines=prior.get("next_lines"), current_journal=current["name"],
            current_input_kind=current.get("input_kind"), action_events=candidates,
            intervening_journals=sorted(journals, key=lambda x: x["epoch"])))
    selected_choices = []
    for row in sequence:
        candidates = [x for x in parsed_actions
            if 0 <= x["timestamp"] - row["epoch"] <= 5
            and x["raw_next"] in row.get("next_lines", [])]
        selected_choices.append(dict(ordinal=row["ordinal"], candidates=[x["action_id"] for x in candidates],
            association="exact selected NEXT string plus action timestamp within five seconds of journal filename; temporal association, not durable generation ID"))
    report = dict(schema="astrid_study_survey_action_traces_v1", truncated=actions["truncated"],
        action_count=len(parsed_actions), action_statuses=dict(Counter(x["status"] for x in parsed_actions)),
        action_routes=dict(Counter(x["route"] for x in parsed_actions)),
        targets=traces, selected_journal_choice_associations=selected_choices,
        interpretation="All five inspected apparent mismatches include an explicit later REPLACE command with a handled action event that names the superseded pending choice. They are not evidence of a silently lost pending request.",
        limitations=["Handled means queued or identical pending retry, not prepared or delivered.",
            "Blocked conflicting choices preserve pending requests; they are not provider failures.",
            "Literal NEXT extraction alone is not the released parser; actual raw_next/canonical_action/outcome are retained action evidence.",
            "Study journals omit intervening dialogue decisions; selected-study adjacency is not decision adjacency.",
            "Action rows are the observed SQLite state in one read transaction, not an append-only history of every former row status."],
        derivation_probe_sha256=sha(Path(__file__).read_bytes()))
    write(OUT / "action-traces.json", encode(report))
    write(OUT / "derivation-probe.py", Path(__file__).read_bytes())
    return report


def verify():
    capture_index = json.loads((OUT / "capture-index.json").read_bytes())
    for row in capture_index["records"]:
        raw = (PACKET / row["retained"]).read_bytes()
        assert len(raw) == row["bytes"] and sha(raw) == row["sha256"]
    assert sha((OUT / "capture-probe.py").read_bytes()) == capture_index["probe_sha256"]
    attempts = json.loads((OUT / "provider-attempt-frame.json").read_bytes())["attempts"]
    assert len({row["attempt_id"] for row in attempts}) == len(attempts)
    assert all(LOW_MS <= row["start_ms"] <= HIGH_MS for row in attempts)
    joined = [ordinal for row in attempts for ordinal in row["selected_journal_ordinals"]]
    assert sorted(joined) == list(range(1, 101))
    assert all(len(row["accepted_wire_matches"]) <= 1 for row in attempts)
    assert not json.loads((OUT / "actions.json").read_bytes())["truncated"]
    traces = json.loads((OUT / "action-traces.json").read_bytes())
    assert sha((OUT / "derivation-probe.py").read_bytes()) == traces["derivation_probe_sha256"]
    for row in traces["targets"]:
        assert any(event["raw_next"].startswith("SELF_STUDY REPLACE ")
                   and event["status"] == "handled"
                   and "Explicitly superseded:" in event["outcome_summary"]
                   for event in row["action_events"])
    return dict(retained_files_verified=len(capture_index["records"]),
        physical_attempts_verified=len(attempts), selected_journals_joined_once=len(joined),
        explicit_replacement_traces_verified=len(traces["targets"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summarize-retained", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify()))
    elif args.summarize_retained:
        print(json.dumps({"target_traces": len(summarize_retained()["targets"])}))
    else:
        captured = capture()
        write(OUT / "capture-probe.py", Path(__file__).read_bytes())
        analyze(captured)
        summarize_retained()
