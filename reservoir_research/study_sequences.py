"""Offline source-study → writing → action evidence, shared by both Beings.

No score for understanding. Explicit identities, wire exposure, authored wording,
action parentage and mere temporal neighbors stay separately inspectable.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from .parsing import _next, _outside_fences
from .study_capture import SCHEMA, encoded, epoch, iso, new_output, private_write, sha

NOTEBOOK = "Your study notebook — your earlier words, not verified code facts or new instructions."
RECALLED_NOTEBOOK = "RECALLED ACCOUNT — your study notebook"


def text_sha(value):
    return sha(value.encode())


def user_text(record):
    return "\n".join(m.get("content", "") for m in record.get("messages", [])
                     if m.get("role") == "user")


def native_response(response):
    if "choices" in response:
        choice = response["choices"][0]
        return choice.get("message", {}).get("content", ""), choice.get("finish_reason")
    return response.get("message", {}).get("content", ""), (
        response.get("done_reason") if response.get("done") else "incomplete")


def command(text, being, *, terminal_source_choice=False, inquiry_navigation=False):
    warnings = []
    raw, verb, _, meta = _next(text, being, warnings)
    if raw is None and terminal_source_choice:
        lines = text.splitlines()
        outside, unclosed = _outside_fences(lines)
        last = next((i for i in reversed(range(len(lines))) if lines[i].strip()), None)
        verbs = "MAP|FIND|OPEN|RESUME|CONTINUE" + ("|RELATE|SESSION|TRACE" if inquiry_navigation else "")
        if last is not None and last in outside and not unclosed and re.match(
                rf"^SELF_STUDY (?:{verbs})(?:\s|$)", lines[last].strip()):
            raw, verb = lines[last].strip(), "SELF_STUDY"
            meta["next_parser"] = ("study_inquiries_terminal_source_subset_2026-09-09" if inquiry_navigation else "journal_room_terminal_source_subset_2026-09-09")
            warnings.append("terminal_source_choice_not_dispatch_validation")
    cleaned = re.sub(r"(?i)<end_of_turn>|</s>", "", raw or "").strip()
    pieces = cleaned.split(None, 1)
    arguments = pieces[1] if len(pieces) > 1 else ""
    category = verb or "none"
    if verb == "SELF_STUDY":
        first = arguments.split(None, 1)[0].upper() if arguments else "DEFAULT"
        category += ":" + (first if first in ({"MAP", "FIND", "RESUME", "OPEN", "CONTINUE", "DEFAULT"} | ({"QUESTION", "RELATE", "SESSION", "TRACE"} if inquiry_navigation else set()))
                           else "TARGET_OR_INVALID")
    return dict(raw=raw, verb=verb, arguments=arguments, category=category,
                comparison_key=" ".join(filter(None, (verb, arguments))).strip(),
                warnings=warnings, parser=meta["next_parser"],
                authority="research subset; not dispatch validation")


def authored_fields(text):
    lines = text.splitlines()
    outside, _ = _outside_fences(lines)
    result = {"STUDY_NOTE": [], "STUDY_QUESTION": []}
    offset = 0
    for i, line in enumerate(text.splitlines(keepends=True)):
        if i in outside:
            for name in result:
                found = re.fullmatch(r"\s*" + name + r":\s*(.*)", line.rstrip("\r\n"))
                if found:
                    result[name].append(dict(text=found[1], start=offset, end=offset+len(line.rstrip("\r\n"))))
        offset += len(line)
    return result


def notebook_exposure(text):
    start = max(text.rfind("\n\n" + heading) for heading in (NOTEBOOK, RECALLED_NOTEBOOK))
    if start < 0:
        return dict(status="absent")
    body_start = text.find("\n", start + 2) + 1
    end = text.find("\nEnd of study notebook.", body_start)
    if not body_start or end < 0:
        return dict(status="malformed", start=start)
    try:
        value = json.loads(text[body_start:end])
        if not isinstance(value, dict) or set(value) not in (
                {"note", "question", "previous"}, {"note", "question", "previous", "recent"}):
            raise ValueError("Notebook shape")
        recent = value.get("recent", [])
        if not isinstance(recent, list) or any(not isinstance(entry, dict) for entry in recent):
            raise ValueError("Recent notebook shape")
        for entry in [value["note"], value["question"], value["previous"], *recent]:
            if entry is not None and (not isinstance(entry, dict) or
                    not all(isinstance(entry.get(k), str) for k in ("origin", "response_sha256", "text"))):
                raise ValueError("Notebook entry shape")
            if entry is not None and (
                    ("complete" in entry and type(entry["complete"]) is not bool) or
                    ("prose_bytes" in entry and (type(entry["prose_bytes"]) is not int or entry["prose_bytes"] < 0))):
                raise ValueError("Notebook completeness shape")
    except (ValueError, TypeError):
        return dict(status="malformed", start=start, end=end)
    return dict(status="included_in_submitted_user_text", start=start, end=end,
                sha256=text_sha(text[start:end]), fields=value)


def writing_match(response, row):
    """Allow only known whole runtime separator lines; preserve original spans."""
    if not response:
        return None
    raw = row["text"]
    start = raw.find(response)
    if start >= 0:
        spans, relation = [[start, start+len(response)]], "exact response containment"
    else:
        lines = raw.splitlines(keepends=True)
        outside, _ = _outside_fences(raw.splitlines())
        kept, positions, offset = [], [], 0
        for i, line in enumerate(lines):
            if not (i in outside and line.strip() in {"--- ACTION TAIL ---", "--- GENERATED JOURNAL ---"}):
                kept.append(line)
                positions.extend(range(offset, offset+len(line)))
            offset += len(line)
        start = "".join(kept).find(response)
        if start < 0:
            return None
        spans = []
        for index in positions[start:start+len(response)]:
            if spans and spans[-1][1] == index:
                spans[-1][1] += 1
            else:
                spans.append([index, index+1])
        relation = "exact response after removing known runtime separator lines; original spans preserved"
    return dict(path=row["path"], sha256=row["sha256"], source_spans=spans,
                response_sha256=text_sha(response), relation=relation,
                curated=Path(row["path"]).name.startswith("!"))


def kind_of(text):
    if re.search(r"^SOURCE ", text, re.M):
        return "source"
    if re.search(r"^Shared system map", text, re.M):
        return "map"
    if re.search(r"^Literal source search:", text, re.M):
        return "search"
    if re.search(r"^End of ", text, re.M):
        return "eof"
    return "other"


def merge_ranges(ranges):
    merged = []
    for start, end in sorted(ranges):
        if not 0 <= start <= end:
            raise ValueError("Invalid byte range")
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    return merged


def range_bytes(ranges):
    return sum(end-start for start, end in merge_ranges(ranges))


def source_progress(deliveries, lo, hi):
    """Union by Being/file/revision; retained earlier receipts establish baseline."""
    ranges, output = defaultdict(list), []
    expanded = [dict(row, page=page) for row in deliveries
                for page in (row.get("session_pages") or [row.get("page")])]
    for row in sorted(expanded, key=lambda r: (r["completed"], r["path"])):
        page = row.get("page")
        if not page or not row["verified"] or row["completed"] >= hi:
            continue
        key = (row["being"], page["source"], page["revision"]["sha256"])
        before = range_bytes(ranges[key])
        start, end = page["start"]["byte"], page["end"]["byte"]
        if end > page["revision"]["bytes"]:
            raise ValueError("Page exceeds file size")
        ranges[key] = merge_ranges([*ranges[key], [start, end]])
        after = range_bytes(ranges[key])
        if row["completed"] >= lo:
            output.append(dict(path=row["path"], being=row["being"], source=page["source"],
                revision=page["revision"]["sha256"], start=start, end=end,
                delivered_bytes=end-start, new_bytes=after-before,
                repeated_bytes=end-start-(after-before), union_bytes_after=after,
                file_bytes=page["revision"]["bytes"],
                full_revision_delivered=after == page["revision"]["bytes"],
                basis="all retained earlier verified receipts; not comprehension"))
    return output


def release_eras(records, profile="continuity"):
    profiles = {
        "continuity": ("source-study-continuity-validation", "self-study-continuity-live-20260908", "provider-observation-live-20260908"),
        "follow-through": ("self-study-follow-through-validation", "self-study-follow-through-20260908", "self-study-continuity-live-20260908"),
        "evidence-views": ("study-evidence-validation", "study-evidence-20260908", "self-study-follow-through-20260908"),
        "journal-room": ("journal-room-validation", "journal-room-20260909", "study-evidence-20260908"),
        "study-inquiries": ("study-inquiries-validation", "study-inquiries-20260909", "journal-room-20260909"),
        "study-context": ("study-context-validation", "study-context-20260909", "study-inquiries-20260909"),
        "study-choice": ("study-choice-validation", "study-choice-20260909", "study-context-20260909"),
    }
    if profile not in profiles:
        raise ValueError("Unknown release profile")
    rollout_dir, stage_dir, previous_dir = profiles[profile]
    bypath = {r["path"]: r for r in records}
    rollout = next(r for r in records if r["path"].endswith(rollout_dir + "/live-rollout.json"))
    value = json.loads(rollout["text"])
    manifest = next(r for r in records if r["path"].endswith(stage_dir + "/bridge-stage-01/manifest.json"))
    if manifest["sha256"] != value["manifest_sha256"]:
        raise ValueError("Release manifest hash mismatch")
    activation = json.loads(bypath[value["bridge"]["activation_receipt"]]["text"])
    reload = json.loads(bypath[value["minime"]["receipt"]]["text"].splitlines()[-1])
    if (activation.get("status") != "activated_verified" or reload.get("outcome") != "success"
            or activation["new_process"]["pid"] != value["bridge"]["new_pid"]
            or reload["new_pid"] != value["minime"]["new_pid"]
            or activation["manifest_sha256"] != value["manifest_sha256"]
            or activation["new_process"]["started_at"] != value["bridge"]["started_at"]
            or reload["new_started_at"] != value["minime"]["started_at"]):
        raise ValueError("Release activation identity mismatch")
    result = {}
    for being, key, hashkey in (("astrid", "activation_receipt", "activation_receipt_sha256"),
                                ("minime", "receipt", "receipt_sha256")):
        info = value["bridge" if being == "astrid" else "minime"]
        receipt = bypath[info[key]]
        if receipt["sha256"] != info[hashkey]:
            raise ValueError("Activation receipt hash mismatch")
        result[being] = dict(boundary=datetime.strptime(info["started_at"], "%a %b %d %H:%M:%S %Y")
                            .replace(tzinfo=ZoneInfo("America/Los_Angeles")).timestamp(),
                            old_pid=info["old_pid"], new_pid=info["new_pid"],
                            commit=value[being+"_commit"], receipt_sha256=receipt["sha256"],
                            manifest_sha256=manifest["sha256"])
    old = next(r for r in records if r["path"].endswith(previous_dir + "/bridge-stage-01/manifest.json"))
    if old["sha256"] != activation["old_identity"]["manifest_sha256"]:
        raise ValueError("Prior release manifest mismatch")
    result["astrid"]["old_manifest_sha256"] = old["sha256"]
    return result


def era_for(being, start, completed, pid, eras, release=None):
    e = eras[being]
    if start < e["boundary"] <= completed:
        return "transition"
    if (being == "minime" and start < e["boundary"] and
            completed >= eras["astrid"]["boundary"]):
        return "transition_shared_helper"
    label = "before" if completed < e["boundary"] else "after"
    if pid != e["old_pid" if label == "before" else "new_pid"]:
        return label + "_unverified"
    if being == "astrid":
        expected = e["old_manifest_sha256" if label == "before" else "manifest_sha256"]
        if not release or release.get("manifest_sha256") != expected:
            return label + "_unverified"
    return label


def verify_records(packet):
    if packet["schema"] != SCHEMA:
        raise ValueError("Unsupported capture schema")
    paths = set()
    for row in packet["records"]:
        raw = row["text"].encode()
        if sha(raw) != row["sha256"] or len(raw) != row["bytes"]:
            raise ValueError("Capture content hash/length mismatch: " + row["path"])
        if row["path"] in paths:
            raise ValueError("Duplicate capture path")
        paths.add(row["path"])
        if row["kind"] == "generation":
            gen = json.loads(row["text"])
            if gen.get("response_text") is not None and text_sha(gen["response_text"]) != gen.get("response_sha256"):
                raise ValueError("Generation response hash mismatch")


def receipt_records(records):
    result = []
    # Prefer the shared reader receipt when two stores retain the same wire.
    seen = set()
    def priority(r):
        if r["kind"] == "navigation" and json.loads(r["text"]).get("output", {}).get("session_pages"):
            return -1
        return int(r["kind"] == "accepted_delivery")
    for r in sorted(records, key=priority):
        if r["kind"] not in {"delivery", "navigation", "accepted_delivery"}:
            continue
        d = json.loads(r["text"])
        accepted = r["kind"] == "accepted_delivery"
        wire = d["attempt"] if accepted else d
        if accepted and wire.get("admission", {}).get("kind") != "source_study":
            continue
        key = (r["being"], text_sha(wire["request_json"]), text_sha(wire["response_json"]))
        if key in seen:
            continue
        seen.add(key)
        request, response = json.loads(wire["request_json"]), json.loads(wire["response_json"])
        text, finish = native_response(response)
        clock = response.get("created")
        if clock is None and response.get("created_at"):
            clock = epoch(response["created_at"])
        page = d.get("page")
        offer = d.get("output") or {}
        pages = offer.get("session_pages", [])
        supplied = offer.get("text", page["text"] if page else "")
        errors = []
        if d.get("session_id"):
            errors.append("session page has no captured whole-session offer; completeness unknown")
        if pages and (not 2 <= len(pages) <= 3 or any(p.get("text", "") not in supplied for p in pages)):
            errors.append("session offer does not contain every selected page")
        if accepted:
            admission = wire["admission"]
            message = request["messages"][admission["message_index"]]
            raw = message["content"].encode()[admission["content_start_byte"]:admission["content_end_byte"]]
            supplied = raw.decode()
            if (message["role"] != "user" or sha(raw) != admission["admitted_text_sha256"]
                    or len(raw) != admission["offered_bytes"]
                    or admission["admitted_end_byte"] - admission["source_start_byte"] != len(raw)):
                errors.append("protected admission mismatch")
            if d["accepted_completion"].strip() != text.strip():
                errors.append("accepted/provider text differs; cleanup requires separate review")
            text = d["accepted_completion"]
        expected_schema = ("accepted_prompt_delivery_v1" if accepted else
                           "source_study_delivery_v1" if page else "source_study_navigation_delivery_v1")
        if d.get("schema") != expected_schema:
            errors.append("unsupported receipt schema")
        if Path(r["path"]).stem != r["sha256"]:
            errors.append("artifact filename hash mismatch")
        rid = wire["admission"]["content_id"] if accepted else page["id"] if page else d.get("output", {}).get("navigation_id")
        if not accepted and Path(r["path"]).parent.name != rid:
            errors.append("receipt identity mismatch")
        if not supplied or not any(m.get("role") == "user" and supplied in m.get("content", "")
                                   for m in request.get("messages", [])):
            errors.append("whole supplied page/navigation absent")
        if finish != "stop" or not text.strip() or response.get("error"):
            errors.append("not a normal nonempty completion")
        if clock is None:
            errors.append("missing provider clock")
        result.append(dict(path=r["path"], being=r["being"], receipt_id=rid,
            kind=r["kind"], request=request, response=response, text=text,
            request_sha256=text_sha(wire["request_json"]), response_sha256=text_sha(wire["response_json"]),
            response_text_sha256=text_sha(text), native_finish=finish, page=page,
            user_text=user_text(request), completed=clock or 0,
            clock_basis="provider response clock until joined to local attempt",
            verified=not errors, errors=errors, artifact_sha256=r["sha256"]))
        if pages:
            result[-1]["session_pages"] = pages
        for key in ("question_id", "input_kind"):
            if key in offer:
                result[-1][key] = offer[key]
    return result


def matching_generations(receipt, generations):
    matches = []
    request = receipt["request"]
    systems = [text_sha(m.get("content", "")) for m in request.get("messages", []) if m.get("role") == "system"]
    for row, gen in generations:
        if row["being"] != receipt["being"] or gen.get("response_text") != receipt["text"]:
            continue
        if user_text(gen) != receipt["user_text"] or gen.get("model") != request.get("model"):
            continue
        if [m.get("content_sha256", text_sha(m.get("content", ""))) for m in gen.get("messages", [])
                if m.get("role") == "system"] != systems:
            continue
        matches.append((row, gen))
    return matches


def followthrough(study, actions, studies, hi, horizon=1800):
    start, end = study["completed"], min(hi, study["completed"] + horizon)
    owner = study.get("action_id")
    nearby = [a for a in actions if a["being"] == study["being"] and start <= a["started"] < end]
    children = [a for a in nearby if owner and a.get("parent_action_id") == owner]
    requested = study["next"]["comparison_key"]
    def view(a):
        return {**a, "matches_requested": bool(requested and
            command("NEXT: " + (a.get("raw_next") or ""), a["being"])["comparison_key"] == requested)}
    later = sorted([s for s in studies if s["being"] == study["being"] and
                    s["id"] != study["id"] and start < s["started"] < end], key=lambda s: s["started"])
    transition = None
    current_page = study.get("page") or (study.get("session_pages") or [None])[-1]
    next_page = (later[0].get("page") or (later[0].get("session_pages") or [None])[0]) if later else None
    if current_page and next_page:
        a, b = current_page, next_page
        same = a["source"] == b["source"] and a["revision"] == b["revision"]
        transition = dict(same_source_revision=same,
            contiguous_bytes=bool(same and a["end"]["byte"] == b["start"]["byte"]),
            next_start_byte=b["start"]["byte"], source=b["source"],
            relation="next observed study; does not establish originating NEXT")
    return dict(horizon_seconds=horizon, observed_seconds=max(0, end-start),
        right_censored=hi < start+horizon,
        explicit_parent_actions=[view(a) for a in children],
        temporal_neighbors=[view(a) for a in nearby[:3]],
        temporal_action_count=len(nearby),
        next_study_id=later[0]["id"] if later else None,
        next_source_transition=transition,
        relation="parent IDs establish action ancestry, not which journal supplied the choice; neighbors establish order only")


def build_report(packet):
    verify_records(packet)
    rs = packet["records"]
    lo, hi = epoch(packet["selection"]["since"]), epoch(packet["selection"]["until_exclusive"])
    eras = release_eras(rs, packet["selection"].get("release_profile", "continuity"))
    gens = [(r, json.loads(r["text"])) for r in rs if r["kind"] == "generation"]
    events = [(r, json.loads(r["text"])) for r in rs if r["kind"] == "provider_event"]
    jobs = {(r["being"], json.loads(r["text"])["job_id"]): (r, json.loads(r["text"]))
            for r in rs if r["kind"] == "job_job.json"}
    receipts = receipt_records(rs)
    linked, studies, issues = set(), [], []

    def make(row, being, start, completed, pid, status, text, supplied, **extra):
        completed_after_cutoff = completed >= hi
        if completed_after_cutoff:
            text, supplied, status = "", "", "no_completion_by_cutoff"
            extra["receipt_verified"] = False
        study = dict(id=f"{being}:{row}", being=being, started=start, completed=completed,
                     started_utc=iso(start), completed_utc=iso(completed), pid=pid,
                     status=status, text=text, response_sha256=text_sha(text), user_text=supplied,
                     next=command(text, being), authored=authored_fields(text),
                     notebook=notebook_exposure(supplied), kind=kind_of(supplied), **extra)
        study["completed_after_cutoff"] = completed_after_cutoff
        # Avoid counting a recalled notebook's wording as current navigation.
        current = supplied[:study["notebook"].get("start", len(supplied))]
        study["navigation"] = dict(explicit_no_matches="No matches for the exact literal query" in current,
            progress_lines=[line for line in current.splitlines() if any(mark in line for mark in (
                "Partial delivery", "Complete delivery", "Deliberate reread", "Not delivered", "Current source:"))])
        study["era"] = era_for(being, start, completed, pid, eras, study.get("release"))
        if packet["selection"].get("release_profile") in {"journal-room", "study-inquiries", "study-context", "study-choice"} and study["era"] == "after":
            study["next"] = command(text, being, terminal_source_choice=True,
                inquiry_navigation=packet["selection"].get("release_profile") in {"study-inquiries", "study-context", "study-choice"})
        if study.get("session_pages"):
            study["kind"] = "source_session"
        elif study.get("input_kind") in {"questions", "relationships", "runtime_trace"}:
            study["kind"] = study["input_kind"]
        studies.append(study)
        return study

    for rec in receipts:
        matches = matching_generations(rec, gens)
        outcomes = [(r, e) for r, e in events if r["being"] == rec["being"] and
                    e.get("stage") == "provider_outcome" and
                    e.get("request_sha256") == rec["request_sha256"] and
                    e.get("http_body_sha256") == rec["response_sha256"]]
        if len(matches) > 1 or len(outcomes) > 1:
            issues.append(dict(receipt=rec["path"], issue="ambiguous exact join",
                               generations=[g["generation_id"] for _, g in matches],
                               attempts=[e["attempt_id"] for _, e in outcomes]))
        if len(matches) == 1:
            row, gen = matches[0]
            linked.add(row["path"])
            end = gen["created_at_unix_ms"] / 1000
            start = int(gen["generation_id"].split("-")[0]) / 1000
            rec["completed"] = end
            rec["clock_basis"] = "exact generation request/response/system/model join"
            if lo <= start < hi:
                make(gen["generation_id"], rec["being"], start, end, gen.get("pid"), gen["status"],
                     gen.get("response_text", ""), rec["user_text"], receipt=rec["path"],
                     source_record=row["path"], action_id=gen.get("action_id"), job_id=gen.get("job_id"),
                     model=gen.get("model"), backend=gen.get("backend"),
                     runtime_next=gen.get("next_action_parsed"), native_finish=rec["native_finish"],
                     receipt_verified=rec["verified"], page=rec["page"],
                     **{k:rec[k] for k in ("session_pages", "question_id", "input_kind") if k in rec})
        elif len(outcomes) == 1:
            row, event = outcomes[0]
            start = event["created_at_unix_ms"] / 1000
            end = start + event["elapsed_ms"] / 1000
            rec["completed"] = end
            rec["clock_basis"] = "exact provider request/body hash join"
            if lo <= start < hi:
                make(event["attempt_id"], rec["being"], start, end, event.get("pid"),
                     "ok" if rec["verified"] else "unverified", rec["text"], rec["user_text"],
                     receipt=rec["path"], source_record=row["path"], action_id=None, job_id=None,
                     model=event.get("reported_model"), backend=event.get("provider"),
                     native_finish=rec["native_finish"], receipt_verified=rec["verified"],
                     release=event.get("release_before"), page=rec["page"],
                     **{k:rec[k] for k in ("session_pages", "question_id", "input_kind") if k in rec})
        elif lo <= rec["completed"] < hi:
            issues.append(dict(receipt=rec["path"], issue="receipt has no unique local attempt join",
                               provider_time=iso(rec["completed"])))

    for row, gen in gens:
        if row["path"] in linked or gen.get("lane") != "self_study":
            continue
        end = gen["created_at_unix_ms"] / 1000
        start = int(gen["generation_id"].split("-")[0]) / 1000
        if lo <= start < hi:
            make(gen["generation_id"], row["being"], start, end, gen.get("pid"), gen["status"],
                 gen.get("response_text") or "", user_text(gen), receipt=None,
                 source_record=row["path"], action_id=gen.get("action_id"), job_id=gen.get("job_id"),
                 model=gen.get("model"), backend=gen.get("backend"), runtime_next=gen.get("next_action_parsed"),
                 native_finish=None, receipt_verified=False)

    # Provider attempts retain Astrid failures even when no accepted receipt or journal exists.
    for row, event in events:
        if event.get("stage") != "dispatch_started" or event.get("label") != "self_study":
            continue
        start = event["created_at_unix_ms"] / 1000
        sid = "astrid:" + event["attempt_id"]
        if not lo <= start < hi or any(s["id"] == sid for s in studies):
            continue
        terminal = [e for _, e in events if e.get("attempt_id") == event["attempt_id"] and e.get("stage") == "provider_outcome"]
        t = terminal[0] if len(terminal) == 1 else {}
        end = start + t.get("elapsed_ms", 0) / 1000
        make(event["attempt_id"], "astrid", start, end, event.get("pid"),
             t.get("outcome", "no_terminal_receipt"), "", "", receipt=None, source_record=row["path"],
             action_id=None, job_id=None, model=t.get("reported_model"), backend=event.get("provider"),
             native_finish=None, receipt_verified=False, release=event.get("release_before"))

    studies.sort(key=lambda s: (s["started"], s["id"]))
    actions = []
    for row in rs:
        if row["kind"] != "action":
            continue
        db = json.loads(row["text"])
        a = json.loads(db["payload"])
        start = epoch(a["started_at"]) if a.get("started_at") else float(db["timestamp"])
        actions.append(dict(being=row["being"], path=row["path"], action_id=db["action_id"],
            started=start, started_utc=iso(start), ended_at=a.get("ended_at"),
            parent_action_id=a.get("parent_action_id"), raw_next=a.get("raw_next"),
            canonical_action=a.get("canonical_action"), effective_action=a.get("effective_action"),
            route=db["route"], status=db["status"], source=a.get("source"),
            suggested_next=a.get("suggested_next"), llm_job_id=a.get("llm_job_id"),
            outcome_summary=a.get("outcome_summary"), artifacts=a.get("artifacts", []),
            terminal_after_cutoff=bool(a.get("ended_at") and epoch(a["ended_at"]) >= hi)))
    actions.sort(key=lambda a: a["started"])
    writing = [r for r in rs if r["kind"] in {"journal", "introspections"}]
    bywire = defaultdict(list)
    for rec in receipts:
        bywire[(rec["being"], rec["response_sha256"])].append(rec)
    for study in studies:
        study["writing"] = []
        if study["text"]:
            for row in writing:
                if row["being"] == study["being"] and (match := writing_match(study["text"], row)):
                    study["writing"].append(match)
        study["followthrough"] = followthrough(study, actions, studies, hi)
        study["notebook"]["origin_receipts"] = {}
        fields = study["notebook"].get("fields", {})
        entries = [(field, entry) for field, entry in fields.items() if field != "recent"]
        entries += [(f"recent[{i}]", entry) for i, entry in enumerate(fields.get("recent", []))]
        for field, entry in entries:
            if entry:
                study["notebook"]["origin_receipts"][field] = [dict(path=r["path"],
                    before_this_attempt=r["completed"] <= study["started"], verified=r["verified"])
                    for r in bywire[(study["being"], entry["response_sha256"])]]
        study["job_status"] = jobs.get((study["being"], study.get("job_id")), ({}, {}))[1].get("status")
        owner = [a for a in actions if a["being"] == study["being"] and a["action_id"] == study.get("action_id")]
        study["producing_action"] = owner[0] if len(owner) == 1 else None
        study["prompt_suggestions"] = [line for line in study["user_text"].splitlines()
            if re.search(r"(?:Suggested|Proposed|Conveyor|Current) NEXT:", line)]

    selected, summary = [], {}
    for being in ("astrid", "minime"):
        summary[being] = {}
        for label in sorted({s["era"] for s in studies if s["being"] == being}):
            rows = [s for s in studies if s["being"] == being and s["era"] == label]
            summary[being][label] = dict(attempts=len(rows),
                statuses=dict(Counter(s["status"] for s in rows)),
                kinds=dict(Counter(s["kind"] for s in rows)),
                models=dict(Counter(s.get("model") or "unknown" for s in rows)),
                verified_receipts=sum(s["receipt_verified"] for s in rows),
                writing_matches=sum(bool(s["writing"]) for s in rows),
                notebook_included=sum(s["notebook"]["status"] == "included_in_submitted_user_text" for s in rows),
                note_authored=sum(bool(s["authored"]["STUDY_NOTE"]) for s in rows),
                question_authored=sum(bool(s["authored"]["STUDY_QUESTION"]) for s in rows),
                explicit_no_matches=sum(s["navigation"]["explicit_no_matches"] for s in rows),
                progress_maps=sum(s["kind"] == "map" and bool(s["navigation"]["progress_lines"]) for s in rows),
                requested=dict(Counter(s["next"]["category"] for s in rows)),
                right_censored=sum(s["followthrough"]["right_censored"] for s in rows))
        for label in ("before", "after"):
            rows = [s for s in studies if s["being"] == being and s["era"] == label and
                    s["status"] == "ok" and s["text"] and s["completed"] < hi]
            chosen = rows[-3:] if label == "before" else rows[:3]
            selected.append(dict(being=being, era=label, requested=3, available=len(rows),
                                 ids=[s["id"] for s in chosen], shortfall=max(0, 3-len(chosen))))
    study_jobs = [dict(being=b, job_id=j["job_id"], status=j.get("status"), path=r["path"],
                       action_id=j.get("action_id"), action_text=j.get("action_text"),
                       error=j.get("error"), summary=j.get("summary"),
                       started_at=j.get("started_at"), finished_at=j.get("finished_at"),
                       worker_pid=j.get("worker_pid"),
                       period="before" if r["filename_time"] < eras[b]["boundary"] else "after",
                       has_generation=any(s.get("job_id") == j["job_id"] and s["being"] == b for s in studies))
                  for (b, _), (r, j) in jobs.items() if "self-study" in j["job_id"] and
                  lo <= r["filename_time"] < hi]
    reading_actions = []
    for a in actions:
        requested = command("NEXT: " + (a.get("raw_next") or ""), a["being"])
        if lo <= a["started"] < hi and requested["verb"] in {"SELF_STUDY", "READ_MORE", "INTROSPECT"}:
            reading_actions.append({**a, "requested_category": requested["category"],
                "period": "before" if a["started"] < eras[a["being"]]["boundary"] else "after"})
    reading_requests = []
    for row, gen in gens:
        response = gen.get("response_text") or ""
        request = command(response, row["being"])
        completed = gen["created_at_unix_ms"] / 1000
        if not lo <= completed < hi or request["verb"] not in {"SELF_STUDY", "READ_MORE", "INTROSPECT"}:
            continue
        candidates = [a["action_id"] for a in reading_actions if a["being"] == row["being"] and
            completed <= a["started"] < min(hi, completed+1800) and
            command("NEXT: " + (a["raw_next"] or ""), a["being"])["comparison_key"] == request["comparison_key"]]
        links = [match for w in writing if w["being"] == row["being"]
                 and (match := writing_match(response, w))]
        reading_requests.append(dict(generation_id=gen["generation_id"], being=row["being"],
            lane=gen.get("lane"), pid=gen.get("pid"), completed_utc=iso(completed),
            period="before" if completed < eras[row["being"]]["boundary"] else "after",
            source_record=row["path"], response_sha256=text_sha(response), response_text=response,
            request=request, runtime_next=gen.get("next_action_parsed"), writing=links,
            matching_later_action_candidates=candidates,
            relation="exact request wording and temporal order; no originating generation ID on action",
            prompt_reading_lines=[line for line in user_text(gen).splitlines()
                                  if "SELF_STUDY" in line or "INTROSPECT" in line or "READ_MORE" in line]))
    return dict(schema="study_sequence_report_v1", selection=packet["selection"],
        release_eras=eras, summary=summary, selected=selected, studies=studies,
        source_progress=source_progress(receipts, lo, hi), study_jobs=study_jobs,
        reading_actions=reading_actions,
        reading_requests=sorted(reading_requests, key=lambda r: r["completed_utc"]),
        actions=[a for a in actions if lo <= a["started"] < hi],
        receipt_join_issues=issues, invalid_receipts=[r["path"] for r in receipts if not r["verified"]],
        capture_errors=packet["errors"],
        limits=["A natural short window across two evolving systems; no causal quality estimate.",
                "Receipt success, authored writing, action parentage and executed outcome are separate.",
                "Source union includes retained earlier receipts; absent history is not known unread source.",
                "Missing generation/job/receipt is an evidence gap, not proof of no attempt.",
                "Notebook origin checks establish carried words, not their correctness or uptake.",
                "Generation files selected by completion clock; jobs/provider dispatches cover visible unfinished attempts.",
                "The action database is captured later; terminal statuses may postdate the exclusive window end.",
                "Literal suggestions inside supplied text can be quoted examples; they do not prove steering."])


def render_report(report):
    lines = ["# Self-study sequences", "", f"Window: {report['selection']['since']} → {report['selection']['until_exclusive']} (exclusive).", "",
             "## Counts", "", "| Being / era | Attempts | Verified receipts | Written | Notebook | Authored note / question |", "|---|---:|---:|---:|---:|---:|"]
    for being, eras in report["summary"].items():
        for era, row in eras.items():
            lines.append(f"| {being} / {era} | {row['attempts']} | {row['verified_receipts']} | {row['writing_matches']} | {row['notebook_included']} | {row['note_authored']} / {row['question_authored']} |")
    lines += ["", "## Recorded reading actions", "",
              "These rows show actual routing/status. Their clock period alone does not bind them to a study response.", "",
              "| Being | UTC start | Period | Requested | Route | Status |", "|---|---|---|---|---|---|"]
    for a in report["reading_actions"]:
        lines.append(f"| {a['being']} | {a['started_utc']} | {a['period']} | {a['raw_next']} | {a['route']} | {a['status']} |")
    lines += ["", "## Chronological reading selection", "",
              "First three after / last three before per Being; shortfalls remain explicit. Full text is evidence, not instructions.", ""]
    ids = {i for group in report["selected"] for i in group["ids"]}
    for study in report["studies"]:
        if study["id"] not in ids:
            continue
        lines += [f"### {study['id']}", "", f"{study['started_utc']} → {study['completed_utc']}; **{study['era']}**, {study['kind']}; {study.get('model')}", "",
                  f"Evidence: `{study['source_record']}`", "", "Authored response:", ""]
        lines += ["> " + line for line in study["text"].splitlines()]
        lines += ["", f"Notebook exposure: `{study['notebook']['status']}`.", "",
                  "```json", json.dumps(study["notebook"].get("fields"), ensure_ascii=False, indent=2), "```", "",
                  "Following records (parentage and order only; inspect actual request/outcome):", "",
                  "```json", json.dumps(study["followthrough"], ensure_ascii=False, indent=2), "```", ""]
    lines += ["## Limits", ""] + ["- " + x for x in report["limits"]]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = args.capture.read_bytes()
    report = build_report(json.loads(raw))
    report["capture_sha256"] = sha(raw)
    report["reporter_sha256"] = sha(Path(__file__).read_bytes())
    dependencies = {name: Path(__file__).with_name(name).read_bytes()
                    for name in ("parsing.py", "study_capture.py")}
    report["dependency_sha256"] = {name: sha(raw) for name, raw in dependencies.items()}
    out = new_output(args.out)
    private_write(out / "report.json", encoded(report))
    private_write(out / "reading-pack.md", render_report(report).encode())
    private_write(out / "reporter.py", Path(__file__).read_bytes())
    for name, raw in dependencies.items():
        private_write(out / name, raw)
    print(json.dumps({k: report[k] for k in ("summary", "selected", "receipt_join_issues", "invalid_receipts", "capture_errors")}, indent=2))


if __name__ == "__main__":
    main()
