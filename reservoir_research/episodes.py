"""Keyword-free, two-being reconstruction from the research cache only.

Point observations use [since, until). Declared intervals overlap when their start
is before until and their end is at or after since: an end exactly at since counts
as a boundary event. Explicit action identities may supply separately labeled
out-of-window context. Neither proximity nor parent IDs establish feedback use.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from bisect import insort
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .explore import _digest, _fenced, _index_snapshot, _snapshot

BEINGS = ("astrid", "minime")
SCHEMA_VERSION = 1
EXCERPT_CHARACTERS = 1800


def _json(value):
    try:
        parsed = json.loads(value or "{}", parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except (TypeError, ValueError, RecursionError):
        return {"unparsed": value}


def _stamp(value, milliseconds=False):
    if value is None or isinstance(value, bool):
        return None
    try:
        if isinstance(value, str) and not re.fullmatch(r"[-+]?\d+(\.\d+)?", value):
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return None  # Never guess a timezone for source timing fields.
            value = parsed.timestamp()
        else:
            value = float(value) / (1000 if milliseconds else 1)
        if not math.isfinite(value):
            return None
        datetime.fromtimestamp(value, timezone.utc)
        return value
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def _iso(value, zone=timezone.utc):
    return datetime.fromtimestamp(value, zone).isoformat() if value is not None else None


def _timing(row, record_type):
    start, end = _stamp(row.get("occurred_at")), None
    basis = "journal record writing/filename time; not an action execution time"
    if record_type == "observation":
        end = _stamp(row.get("ended_at"))
        record = _json(row.get("record_json"))
        basis = record.get("time_semantics") or ("declared action start/end" if row.get("kind") == "action" else "declared observation timestamp")
    elif record_type == "generation":
        source = _json(row.get("metadata_json")).get("source_record", {})
        source = source if isinstance(source, dict) else {}
        basis = "generation record creation time; execution start not inferred"
        explicit_start = None
        for field in ("started_at_unix_ms", "started_at", "start_time"):
            explicit_start = _stamp(source.get(field), field.endswith("_ms"))
            if explicit_start is not None:
                start, basis = explicit_start, "explicit generation start/end"
                break
        for field in ("ended_at_unix_ms", "completed_at_unix_ms", "finished_at_unix_ms", "ended_at", "completed_at", "finished_at"):
            end = _stamp(source.get(field), field.endswith("_ms"))
            if end is not None:
                break
        duration = source.get("duration_ms")
        if end is None and explicit_start is not None and isinstance(duration, (int, float)) and not isinstance(duration, bool) and math.isfinite(duration) and duration >= 0:
            end = _stamp(explicit_start + duration / 1000)
            basis += "; end derived from declared duration_ms"
        if end is not None and explicit_start is None:
            basis = "generation creation-to-recorded-end interval; execution start unknown"
    warning = "declared end precedes start; treated as a start-time point" if start is not None and end is not None and end < start else None
    return start, end, basis, warning


def _inside(start, end, since, until):
    if start is None:
        return end is not None and since <= end < until
    if end is not None and end >= start:
        return start < until and end >= since
    return since <= start < until


def _wrap(row, record_type, zone, since, until, context=False):
    start, end, basis, warning = _timing(row, record_type)
    texts = {key: hashlib.sha256(row[key].encode()).hexdigest() for key in
             ("raw_text", "body_text", "prompt_text", "response_text", "record_json") if isinstance(row.get(key), str)}
    return {"record_type": record_type, "kind": row.get("kind", record_type), "being": row["being"],
            "id": row["id"], "start_at": start, "end_at": end,
            "start_utc": _iso(start), "end_utc": _iso(end),
            "start_local": _iso(start, zone), "end_local": _iso(end, zone),
            "time_basis": basis, "timing_warning": warning,
            "selection": "same_explicit_action_id_outside_window" if context else "in_window_or_overlapping",
            "starts_before_window": start is not None and start < since,
            "ends_after_window": end is not None and end >= until,
            "cached_field_sha256": texts, "data": row}


def _order(record):
    stamp = record["start_at"] if record["start_at"] is not None else record["end_at"]
    return (stamp is None, stamp or 0, record["being"], record["record_type"], record["kind"], record["id"])


def _metrics(row):
    record = _json(row.get("record_json"))
    metrics = record.get("metrics", {})
    if not isinstance(metrics, dict):
        return
    units = metrics.get("units", record.get("units", {}))
    for name, item in metrics.items():
        if name in {"session_id", "engine_t_ms", "timestamp", "tick", "ticks", "sample_id"}:
            continue  # Identifiers and clocks remain in raw evidence, not physical summaries.
        details = item if isinstance(item, dict) else {}
        value = details.get("value") if details else item
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
            continue
        unit = details.get("unit", units.get(name, metrics.get("unit", record.get("unit"))) if isinstance(units, dict) else units)
        identity = (row["being"], str(details.get("subsystem", metrics.get("subsystem", record.get("subsystem", record.get("system", "unknown"))))),
                    str(details.get("handle", metrics.get("handle", record.get("handle", "unknown")))),
                    str(details.get("producer", metrics.get("producer", record.get("producer", "unknown")))), str(name), str(unit or "unknown"),
                    str(row.get("source_path") or "unknown"))
        note = details.get("measurement_note", metrics.get("measurement_note", record.get("measurement_note")))
        yield identity, value, str(note) if note is not None else None


def _retain(buckets, key, record, limit):
    bucket = buckets[key]
    insort(bucket, record, key=_order)
    if len(bucket) > limit:
        bucket.pop()


def _declared_provenance(conn, row):
    fields = _json(row.get("metadata_json")).get("header_fields", [])
    declarations = [{"name": item["name"], "value": item.get("value")} for item in fields
                    if isinstance(item, dict) and str(item.get("name", "")).lower() in
                    {"provenance", "authorship", "source-id", "mode-role", "parent-ids"}]
    result = {"header_declarations": declarations, "declared_source_links": []}
    for declaration in declarations:
        value = declaration["value"]
        if declaration["name"].lower() != "source-id" or not isinstance(value, str) or not value.startswith("minime_journal:"):
            continue
        canonical = value.removeprefix("minime_journal:")
        targets = list(conn.execute("SELECT id,canonical_name,raw_sha256,source_path FROM catalog WHERE being='minime' AND canonical_name=? ORDER BY id", (canonical,)))
        result["declared_source_links"].append({"source_id": value, "match_basis": "exact declared minime_journal canonical name",
            "matching_cached_records": len(targets), "target": dict(targets[0]) if len(targets) == 1 else None,
            "interpretation": "Declared-source link only; not an independent LLM generation or verified exposure."})
    return result


def _imports(conn, names):
    if "evidence_imports" not in names:
        return []
    columns = [r[1] for r in conn.execute("PRAGMA table_info(evidence_imports)") if r[1] != "bundle_json"]
    result = []
    for row in conn.execute("SELECT " + ",".join(columns) + " FROM evidence_imports ORDER BY id"):
        item = dict(row)
        for field in ("capture_json", "coverage_json"):
            if field in item:
                parsed = _json(item.pop(field))
                item[field.removesuffix("_json")] = parsed["value"] if set(parsed) == {"value"} else parsed
        result.append(item)
    return result


def collect_episode(conn, since: float, until: float, timezone_name: str = "UTC", limit: int = 1000) -> dict:
    """Collect both beings without keyword selection, from one cached snapshot.

    The cap applies per being/kind to retained rows. Telemetry summaries and action
    counts use all matched observation rows, explicitly distinct from retained JSON.
    Additional same-action context has its own per-being/kind cap and is excluded
    from window counts. No source files are opened and no cache rows are changed.
    """
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or _stamp(v) is None for v in (since, until)) or since >= until:
        raise ValueError("Provide a finite since < until UTC epoch window.")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer per being/kind.")
    try:
        zone = ZoneInfo(timezone_name)
    except (TypeError, ValueError, ZoneInfoNotFoundError) as exc:
        raise ValueError("timezone_name must identify an available IANA timezone.") from exc
    with _snapshot(conn):
        return _collect(conn, float(since), float(until), timezone_name, zone, limit)


def _collect(conn, since, until, timezone_name, zone, limit):
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
    if "catalog" not in names:
        raise ValueError("The index has no journal catalog.")
    retained, denominators, actions, metrics = defaultdict(list), {}, {}, {}
    anonymous_actions = Counter()
    table_map = {"journal": "catalog", "generation": "generations", "observation": "observations"}
    for record_type, table in table_map.items():
        kinds = ["action", "telemetry"] if record_type == "observation" else [record_type]
        if table in names and record_type == "observation":
            kinds = sorted(set(kinds) | {r[0] for r in conn.execute("SELECT DISTINCT kind FROM observations")})
        for being in BEINGS:
            for kind in kinds:
                denominators[(being, record_type, kind)] = {"being": being, "record_type": record_type, "kind": kind,
                    "source_table": table, "table_available": table in names, "total_indexed": 0 if table in names else None,
                    "matching_in_window": 0 if table in names else None, "undated_before_time_filter": 0 if table in names else None,
                    "retained": 0, "omitted_by_cap": 0}
        if table not in names:
            continue
        where, parameters = "being IN ('astrid','minime')", []
        if record_type != "generation":
            kind_column = "kind" if record_type == "observation" else "'journal'"
            undated = "occurred_at IS NULL AND ended_at IS NULL" if record_type == "observation" else "occurred_at IS NULL"
            for group in conn.execute(f"SELECT being,{kind_column} AS kind,count(*) AS total,sum({undated}) AS undated FROM {table} WHERE {where} GROUP BY being,{kind_column}"):
                denominator = denominators[(group["being"], record_type, group["kind"])]
                denominator["total_indexed"], denominator["undated_before_time_filter"] = group["total"], group["undated"]
            if record_type == "journal":
                where += " AND occurred_at>=? AND occurred_at<?"
                parameters = [since, until]
            else:
                # Match _inside exactly, including an interval ending at since,
                # end-only timestamps, and invalid reversed intervals as points.
                where += " AND ((occurred_at IS NULL AND ended_at>=? AND ended_at<?) OR (occurred_at<? AND ((ended_at>=occurred_at AND ended_at>=?) OR ((ended_at IS NULL OR ended_at<occurred_at) AND occurred_at>=?))))"
                parameters = [since, until, until, since, since]
        # Only generation intervals still need a metadata scan: the cache has no
        # normalized start/end columns for these heterogeneous historical formats.
        for raw in conn.execute(f"SELECT * FROM {table} WHERE {where} ORDER BY occurred_at IS NULL,occurred_at,id", parameters):
            row = dict(raw)
            kind = row.get("kind", record_type)
            denominator = denominators[(row["being"], record_type, kind)]
            start, end, _, _ = _timing(row, record_type)
            if record_type == "generation":
                denominator["total_indexed"] += 1
                if start is None and end is None:
                    denominator["undated_before_time_filter"] += 1
            if not _inside(start, end, since, until):
                continue
            denominator["matching_in_window"] += 1
            _retain(retained, (row["being"], record_type, kind), _wrap(row, record_type, zone, since, until), limit)
            denominator["retained"] = min(limit, denominator["matching_in_window"])
            denominator["omitted_by_cap"] = max(0, denominator["matching_in_window"] - limit)
            if record_type == "observation" and kind == "action" and row.get("action_id") is None:
                anonymous_actions[row["being"]] += 1
            if record_type == "observation" and kind == "action" and row.get("action_id") is not None:
                key = (row["being"], str(row["action_id"]))
                action = actions.setdefault(key, {"being": key[0], "action_id": key[1], "matched_observation_ids": [], "lifecycle": []})
                action["matched_observation_ids"].append(row["id"])
                action["lifecycle"].append({key: row.get(key) for key in ("id", "occurred_at", "ended_at", "raw_next", "effective_action", "route", "status", "outcome_summary", "parent_action_id", "thread_id", "job_id", "source_path", "source_sha256")})
            if record_type == "observation" and kind == "telemetry":
                for identity, value, note in _metrics(row):
                    point = {"value": value, "at": start if start is not None else end, "observation_id": row["id"]}
                    group = metrics.setdefault(identity, {"count": 0, "first": point, "last": point, "min": point, "max": point, "measurement_notes": []})
                    group["count"] += 1
                    if note is not None and note not in group["measurement_notes"]:
                        group["measurement_notes"].append(note)
                    if (point["at"], point["observation_id"]) < (group["first"]["at"], group["first"]["observation_id"]):
                        group["first"] = point
                    if (point["at"], point["observation_id"]) > (group["last"]["at"], group["last"]["observation_id"]):
                        group["last"] = point
                    if value < group["min"]["value"]:
                        group["min"] = point
                    if value > group["max"]["value"]:
                        group["max"] = point
    records = sorted((r for bucket in retained.values() for r in bucket), key=_order)
    for record in records:
        if record["record_type"] == "journal":
            record["declared_provenance"] = _declared_provenance(conn, record["data"])
    context_buckets, context_counts = defaultdict(list), Counter()
    if actions:
        for being in BEINGS:
            ids = sorted(key[1] for key in actions if key[0] == being)
            for offset in range(0, len(ids), 400):
                chunk = ids[offset:offset + 400]
                sql = "SELECT * FROM observations WHERE being=? AND action_id IN (" + ",".join("?" for _ in chunk) + ") ORDER BY occurred_at IS NULL,occurred_at,id"
                for raw in conn.execute(sql, [being, *chunk]):
                    row = dict(raw)
                    if _inside(*_timing(row, "observation")[:2], since, until):
                        continue
                    key = (being, row["kind"])
                    context_counts[key] += 1
                    _retain(context_buckets, key, _wrap(row, "observation", zone, since, until, context=True), limit)
    context = sorted((r for bucket in context_buckets.values() for r in bucket), key=_order)
    for action in actions.values():
        action["lifecycle"].sort(key=lambda r: (_stamp(r["occurred_at"]) is None, _stamp(r["occurred_at"]) or _stamp(r["ended_at"]) or 0, r["id"]))
    metric_summaries = [{**dict(zip(("being", "subsystem", "handle", "producer", "metric", "unit", "source_path"), identity)), **group}
                        for identity, group in sorted(metrics.items())]
    denominators = sorted(denominators.values(), key=lambda d: (d["being"], d["record_type"], d["kind"]))
    action_counts = [{"being": being, "matching_action_records": next(d["matching_in_window"] for d in denominators if d["being"] == being and d["kind"] == "action"),
                      "observed_distinct_action_ids": sum(k[0] == being for k in actions) if "observations" in names else None,
                      "records_without_action_id": anonymous_actions[being] if "observations" in names else None}
                     for being in BEINGS]
    leads = _review_leads(records, context, list(actions.values()))
    gaps = [{"being": d["being"], "kind": d["kind"], "note": "Evidence table unavailable; live activity is unknown." if not d["table_available"] else
             "No matching cached records; this does not establish zero live activity.", "matching_in_window": d["matching_in_window"]}
            for d in denominators if not d["matching_in_window"]]
    result = {"schema_version": SCHEMA_VERSION, "method": "cached_two_being_episode_v1",
              "window": {"since": since, "until": until, "since_utc": _iso(since), "until_utc": _iso(until),
                         "timezone": timezone_name, "since_local": _iso(since, zone), "until_local": _iso(until, zone)},
              "parameters": {"limit_per_being_kind": limit, "excerpt_characters": EXCERPT_CHARACTERS,
                             "retention_order": "declared start, otherwise end; then being, record_type, kind, id"},
              "denominators": denominators, "records": records, "identity_context": context,
              "identity_context_counts": [{"being": k[0], "kind": k[1], "matching": n, "retained": min(n, limit), "omitted_by_cap": max(0, n-limit)} for k, n in sorted(context_counts.items())],
              "summary_scope": "Telemetry and action summaries use all matched cached observations, including rows omitted by raw-record caps. Identity context is excluded from window counts.",
              "actions": sorted(actions.values(), key=lambda a: (a["being"], a["action_id"])), "action_counts": action_counts,
              "telemetry": metric_summaries, "review_leads": leads, "gaps": gaps,
              "index_snapshot": _index_snapshot(conn), "evidence_imports": _imports(conn, names),
              "returned": len(records), "truncated": any(d["omitted_by_cap"] for d in denominators),
              "notes": ["Journal being identifies the owning archive, not necessarily authorship. Mirror and operational records retain their lane/content kind.",
                        "Journal and observation raw-row queries are time-bounded; generation metadata is scanned because historical intervals lack normalized columns.",
                        "Original source hashes are retained assertions from the cache/import; cached field hashes are computed here. Source bytes are not re-read or re-verified.",
                        "Point times use [since,until). A declared interval ending exactly at since is included as a boundary event.",
                        "Action IDs group lifecycle evidence only. Handled is not assumed successful; parent IDs do not establish feedback exposure.",
                        "Out-of-window records are included only by matching an explicit being/action_id, and are labeled separately.",
                        "A timestamped sequence is not a causal join. Source availability, unrecorded events, and completeness remain bounded by capture/index coverage.",
                        "Review leads are invitations to inspect evidence, not automatically diagnosed bugs."]}
    result["content_fingerprint"] = _digest({"records": records, "identity_context": context})
    result["result_sha256"] = _digest(result)
    return result


def _review_leads(records, context, actions):
    leads, seen = [], set()
    candidates = [(r["being"], r["id"], r["data"]) for r in [*records, *context] if r["kind"] != "telemetry"]
    candidates += [(a["being"], row["id"], row) for a in actions for row in a["lifecycle"]]
    for being, record_id, data in candidates:
        matched = [key for key in ("status", "route", "outcome_summary") if re.search(r"block|unwired|fail|timeout|timed.out|error", str(data.get(key) or ""), re.I)]
        if matched and (being, record_id) not in seen:
            seen.add((being, record_id))
            leads.append({"being": being, "record_id": record_id, "fields": {key: data[key] for key in matched}, "interpretation": "Review lead, not an automatic bug finding."})
    return sorted(leads, key=lambda r: (r["being"], r["record_id"]))


def _cell(value):
    if value is None:
        return "unknown"
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").replace("`", "\\`").replace("<", "&lt;").replace(">", "&gt;")


def _short(value, limit=170):
    text = " ".join(str(value or "").split())
    return text[:limit] + ("…" if len(text) > limit else "")


def _reference(record_id, kind, being):
    """Label long IDs without throwing away their distinguishing portion."""
    if len(record_id) <= 24:
        return record_id
    token = hashlib.sha256(f"{being}\0{kind}\0{record_id}".encode()).hexdigest()[:12]
    return f"{kind}:{token}"


def _detail(record):
    row = record["data"]
    if record["record_type"] == "journal":
        return f"{row.get('lane') or 'unknown lane'} / {row.get('content_kind') or 'unknown kind'}: {_short(row.get('body_text'), 130)}; requested {_short(row.get('next_raw'), 90) or 'NEXT unknown'}"
    if record["record_type"] == "generation":
        return f"{row.get('lane') or 'unknown lane'}; recorded status {row.get('status') or 'unknown'}; backend {row.get('backend') or 'unknown'}"
    return f"{_short(row.get('raw_next'), 80) or 'request unknown'} → effective {row.get('effective_action') or 'unknown'}; route {row.get('route') or 'unknown'}; status {row.get('status') or 'unknown'}; {_short(row.get('outcome_summary'), 100)}"


def _markdown(result):
    sections = ["# Around-time evidence report\n", "## Overview\n\n" +
                f"Window: {_cell(result['window']['since_local'])} to {_cell(result['window']['until_local'])} ({_cell(result['window']['timezone'])}).\n\n" +
                "Both archives are included without keyword selection. Counts below are records, not inferred authored writings, successful actions, or independent events.\n\n" + result["summary_scope"] + "\n",
                "| Being | Evidence kind | Indexed | Matched window | Retained | Capped | Undated, excluded |\n|---|---|---:|---:|---:|---:|---:|\n" +
                "\n".join("| " + " | ".join(_cell(d[k]) for k in ("being", "kind", "total_indexed", "matching_in_window", "retained", "omitted_by_cap", "undated_before_time_filter")) + " |" for d in result["denominators"]) + "\n"]
    sections.append("### Recorded action overview\n\nStatus labels are source observations. Multiple statuses can describe one action; none is translated into success.\n")
    for count in result["action_counts"]:
        statuses = Counter(str(row.get("status") or "unknown") for a in result["actions"] if a["being"] == count["being"] for row in a["lifecycle"])
        sections.append(f"- {_cell(count['being'])}: {_cell(count['matching_action_records'])} action records, {_cell(count['observed_distinct_action_ids'])} distinct action IDs, {_cell(count['records_without_action_id'])} records without IDs. Status observations with explicit action IDs: " + (_cell(", ".join(f"{status}: {n}" for status, n in sorted(statuses.items()))) or "none cached") + ".\n")
    sections.append("### Named telemetry overview\n\nAll matched numeric samples. First and last follow recorded sample time; full times, source identities, and measurement qualifications are below. Clocks and session IDs remain in raw evidence.\n\n" +
                    "| Being · metric | Producer / subsystem | Unit | Samples | First | Last | Min | Max |\n|---|---|---|---:|---:|---:|---:|---:|\n" +
                    "\n".join("| " + " | ".join(_cell(v) for v in (m["being"] + " · " + m["metric"], m["producer"] + " / " + m["subsystem"], m["unit"], m["count"], *(format(m[k]["value"], ".6g") for k in ("first", "last", "min", "max")))) + " |" for m in result["telemetry"]) + "\n")
    timeline = sorted([r for r in [*result["records"], *result["identity_context"]] if r["kind"] != "telemetry"], key=_order)
    sections.append("## Recorded sequence\n\nRetained records in timestamp order; dense telemetry appears in named summaries below. Proximity does not establish a causal link.\n\n" +
                    "Short references are stable type-labelled hashes for long IDs; the detail sections pair them with full IDs, which JSON preserves. Journal times describe recorded writing, generation times retain their creation/start meanings, and action times are declared start/end.\n\n" +
                    "| Time local | Archive / kind | Short reference | Recorded detail | Scope |\n|---|---|---|---|---|\n" +
                    "\n".join("| " + " | ".join(_cell(v) for v in (r["start_local"] or r["end_local"], r["being"] + " / " + r["kind"], _reference(r["id"], r["kind"], r["being"]), _detail(r), "same-ID outside window" if r["selection"] != "in_window_or_overlapping" else "overlap" if r["starts_before_window"] else "window")) + " |" for r in timeline) + "\n")
    for being in BEINGS:
        sections.append(f"## {being.capitalize()} · recorded journal material\n")
        journals = [r for r in result["records"] if r["record_type"] == "journal" and r["being"] == being]
        if not journals:
            sections.append("No matching journal records in this cache/window; activity outside this evidence is unknown.\n")
        for r in journals:
            row = r["data"]
            label = "Recorded mirror material; authorship is not inferred." if row.get("lane") == "mirror" else "Journal archive ownership does not alone establish text authorship."
            sections.append(f"### {_cell(r['start_local'])} · {_cell(row.get('lane'))} · {_cell(row.get('content_kind'))}\n\n" + label + "\n\n" +
                            _fenced(json.dumps({"reference": _reference(r["id"], r["kind"], r["being"]), **{k: row.get(k) for k in ("id", "source_path", "raw_sha256", "body_sha256", "backend", "prompt_available", "next_raw", "next_verb")}}, ensure_ascii=False, indent=2), "json"))
            if r["declared_provenance"]["header_declarations"]:
                sections.append("Declared provenance and authorship (source assertions):\n\n" + _fenced(json.dumps(r["declared_provenance"], ensure_ascii=False, indent=2), "json"))
            body = row.get("body_text") or row.get("raw_text") or ""
            sections.append(_fenced(body[:EXCERPT_CHARACTERS]) + ("Excerpt capped; complete cached body/raw text is in episode.json.\n" if len(body) > EXCERPT_CHARACTERS else ""))
    sections.append("## Action lifecycle evidence\n\nIDs group records without treating handled as success. Requested NEXT text is distinct from routing, execution, and results.\n")
    for count in result["action_counts"]:
        sections.append(f"- {_cell(count['being'])}: {_cell(count['matching_action_records'])} matched action records; {_cell(count['observed_distinct_action_ids'])} distinct observed action IDs; {_cell(count['records_without_action_id'])} records without an action ID.\n")
    for action in result["actions"]:
        sections.append(f"### {_cell(action['being'])} · action {_cell(action['action_id'])}\n\n" +
                        "| Observation ID | Declared start UTC | Declared end UTC | Request | Effective | Route | Status | Outcome |\n|---|---|---|---|---|---|---|---|\n" +
                        "\n".join("| " + " | ".join(_cell(v) for v in (row["id"], _iso(_stamp(row["occurred_at"])), _iso(_stamp(row["ended_at"])), row["raw_next"], row["effective_action"], row["route"], row["status"], row["outcome_summary"])) + " |" for row in action["lifecycle"]) + "\n")
        sections.append(_fenced(json.dumps([{"reference": _reference(row["id"], "action", action["being"]), **{key: row.get(key) for key in ("id", "parent_action_id", "thread_id", "job_id", "source_path", "source_sha256")}} for row in action["lifecycle"]], ensure_ascii=False, indent=2), "json"))
    for record in result["records"]:
        if record["record_type"] == "observation" and record["kind"] == "action" and record["data"].get("action_id") is None:
            sections.append(f"### {_cell(record['being'])} · action identity unknown · {_cell(record['id'])}\n\n" +
                            _fenced(json.dumps({"reference": _reference(record["id"], record["kind"], record["being"]), "cached_record": record["data"]}, ensure_ascii=False, indent=2), "json"))
    sections.append("## Generation records and identity context\n\nCreation, execution start, and completion times retain their recorded meanings. Context outside the window is labeled and excluded from window totals.\n")
    for r in sorted([r for r in result["records"] if r["record_type"] == "generation"] + result["identity_context"], key=_order):
        row = r["data"]
        sections.append(_fenced(json.dumps({"reference": _reference(r["id"], r["kind"], r["being"]), "being": r["being"], "id": r["id"], "selection": r["selection"], "start_utc": r["start_utc"], "end_utc": r["end_utc"], "time_basis": r["time_basis"],
                            **{key: row.get(key) for key in ("action_id", "job_id", "parent_action_id", "lane", "backend", "prompt_available", "raw_next", "effective_action", "status", "route", "outcome_summary", "source_path", "source_sha256")},
                            "recorded_generation_metadata": _json(row.get("metadata_json")) if r["record_type"] == "generation" else None}, ensure_ascii=False, indent=2), "json"))
    sections.append("## Named telemetry summaries\n\nAll matched numeric samples, not just retained rows. Missing telemetry is unknown, not a zero reading. Metric ownership and units remain explicit.\n")
    for metric in result["telemetry"]:
        sections.append(f"### {_cell(metric['being'])} · {_cell(metric['metric'])}\n\n" +
                        _fenced(json.dumps({**metric, **{key: {**metric[key], "utc": _iso(metric[key]["at"])} for key in ("first", "last", "min", "max")}}, ensure_ascii=False, indent=2), "json"))
    sections.append("## Evidence coverage and gaps\n\n" + _fenced(json.dumps({"gaps": result["gaps"], "evidence_imports": result["evidence_imports"], "index_snapshot": result["index_snapshot"], "identity_context_counts": result["identity_context_counts"]}, ensure_ascii=False, indent=2), "json") + "\n".join("- " + note for note in result["notes"]) + "\n")
    sections.append("## Review leads\n\nThese flags support inspection; they are not automatic bug findings.\n\n" + _fenced(json.dumps(result["review_leads"], ensure_ascii=False, indent=2), "json"))
    return "\n".join(sections)


def export_episode(result, out_dir) -> dict:
    """Export a frozen result to a fresh private directory; caller guards roots."""
    if result.get("schema_version") != SCHEMA_VERSION or _digest({k: v for k, v in result.items() if k != "result_sha256"}) != result.get("result_sha256"):
        raise ValueError("Episode integrity check failed.")
    if _digest({"records": result["records"], "identity_context": result["identity_context"]}) != result["content_fingerprint"]:
        raise ValueError("Episode content fingerprint failed.")
    payloads = (("episode.json", json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n"), ("episode.md", _markdown(result)))
    out_dir, created = Path(out_dir), []
    out_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    try:
        for name, text in payloads:
            path = out_dir / name
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            created.append(path)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(text)
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        try:
            out_dir.rmdir()
        except OSError:
            pass
        raise
    return {"json": str(out_dir / "episode.json"), "markdown": str(out_dir / "episode.md"),
            "records": result["returned"], "result_sha256": result["result_sha256"]}
