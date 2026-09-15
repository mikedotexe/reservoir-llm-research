"""Read-only discovery over cached catalog text; no access to live source files.

Question candidates are surface-language heuristics, not claims of introspection.
Search uses a safely quoted FTS5 phrase; recurrence uses case-sensitive literal text.
Time filters accept epoch seconds or ISO dates/timestamps (naive values mean UTC),
with an inclusive start and exclusive end.
"""

from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def _time(value):
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            value = parsed.replace(tzinfo=timezone.utc).timestamp() if parsed.tzinfo is None else parsed.timestamp()
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Time boundaries must be finite.")
    return value


def _filters(being=None, since=None, until=None):
    since, until = _time(since), _time(until)
    if since is not None and until is not None and since >= until:
        raise ValueError("since must precede until.")
    parts, values = [], []
    for field, op, value in (("being", "=", being), ("occurred_at", ">=", since), ("occurred_at", "<", until)):
        if value is not None:
            parts.append(f"c.{field} {op} ?")
            values.append(value)
    return (" AND " + " AND ".join(parts) if parts else ""), values, {"being": being, "since": since, "until": until}


@contextmanager
def _snapshot(conn):
    # A nested savepoint preserves a caller's transaction and a consistent read view.
    conn.execute("SAVEPOINT explore_read")
    try:
        yield
    finally:
        conn.execute("RELEASE explore_read")


def candidate_questions(body_text: str) -> list[dict]:
    """Return exact character spans outside Markdown fences, in source order.

    Explicit candidates end in '?' and can span wrapped lines; implicit candidates
    are whole lines containing uncertainty markers. Overlapping explicit/implicit
    candidates are deduplicated. Rhetorical questions and false positives remain.
    """
    result, offset, fence, paragraph, paragraph_start = [], 0, None, [], 0
    implicit = re.compile(r"\b(?:I\s+wonder\b|wondering\b|whether\b|I\s+don['’]t\s+understand\b)", re.I)

    def flush():
        text = "".join(paragraph)
        spans = [(m.start(), m.end(), "explicit_question") for m in re.finditer(r"[^.!?]+\?", text)]
        line_start = 0
        for part in paragraph:
            line_end = line_start + len(part)
            if implicit.search(part) and not any(a < line_end and b > line_start for a, b, _ in spans):
                spans.append((line_start, line_end, "implicit_question"))
            line_start = line_end
        for start, end, kind in sorted(spans):
            while start < end and text[start].isspace():
                start += 1
            while end > start and text[end - 1].isspace():
                end -= 1
            result.append({"kind": kind, "text": text[start:end],
                           "start_offset": paragraph_start + start, "end_offset": paragraph_start + end})
        paragraph.clear()

    for line in body_text.splitlines(keepends=True):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            flush()
            token = marker.group(1)
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1] and not line[marker.end():].strip():
                fence = None
        elif fence is None:
            if not line.strip():
                flush()
            else:
                if not paragraph:
                    paragraph_start = offset
                paragraph.append(line)
        offset += len(line)
    flush()
    return result


def search(conn, query, being=None, since=None, until=None, limit=20) -> list[dict]:
    """Search cached body text as one FTS5 phrase, never as raw query syntax.

    Tokenization is SQLite FTS5's: punctuation/case are not exact-text matching.
    Use recurrence() when literal punctuation, spacing, and case matter.
    """
    if limit < 0:
        raise ValueError("limit must be nonnegative.")
    if not query.strip() or limit == 0:
        return []
    filters, values, _ = _filters(being, since, until)
    phrase = '"' + query.replace('"', '""') + '"'
    sql = ("SELECT c.*, bm25(entry_fts) AS rank FROM entry_fts JOIN catalog c "
           "ON c.id = entry_fts.entry_id WHERE entry_fts MATCH ?" + filters +
           " ORDER BY rank, c.occurred_at IS NULL, c.occurred_at, c.id LIMIT ?")
    return [dict(row) for row in conn.execute(sql, [phrase, *values, limit])]


def recurrence(conn, phrase, being=None, since=None, until=None) -> dict:
    """Count case-sensitive literal, non-overlapping occurrences chronologically.

    Identical body hashes are identified independently of phrase recurrence. Neither
    phrase matches nor identical bodies establish semantic continuity or causation.
    """
    if not phrase or not phrase.strip():
        raise ValueError("phrase must contain non-whitespace text.")
    filters, values, scope = _filters(being, since, until)
    sql = ("SELECT c.id, c.being, c.lane, c.occurred_at, c.body_sha256, c.source_path, "
           "(length(c.body_text)-length(replace(c.body_text, ?, '')))/length(?) AS occurrences "
           "FROM catalog c WHERE instr(c.body_text, ?) > 0" + filters +
           " ORDER BY c.occurred_at IS NULL, c.occurred_at, c.id")
    rows = [dict(r) for r in conn.execute(sql, [phrase, phrase, phrase, *values])]
    seen, groups = {}, {name: defaultdict(list) for name in ("being", "lane", "month")}
    for row in rows:
        key = row["body_sha256"] or ("unknown", row["id"])
        row["duplicate_of"] = seen.get(key)
        seen.setdefault(key, row["id"])
        month = datetime.fromtimestamp(row["occurred_at"], timezone.utc).strftime("%Y-%m") if row["occurred_at"] is not None else "unknown"
        for name, group in (("being", row["being"]), ("lane", (row["being"], row["lane"])), ("month", month)):
            groups[name][group].append(row)
    counts = lambda batch: {"entries": len(batch), "occurrences": sum(r["occurrences"] for r in batch),
                           "distinct_bodies": len({r["body_sha256"] or ("unknown", r["id"]) for r in batch})}
    return {"phrase": phrase, "method": "case_sensitive_literal_nonoverlapping", "filters": scope,
            **counts(rows), "duplicate_entries": len(rows) - len(seen),
            "unknown_body_hashes": sum(not r["body_sha256"] for r in rows),
            "by_being": [{"being": k, **counts(v)} for k, v in sorted(groups["being"].items(), key=lambda p: str(p[0]))],
            "by_lane": [{"being": k[0], "lane": k[1], **counts(v)} for k, v in sorted(groups["lane"].items(), key=lambda p: str(p[0]))],
            "by_month": [{"month": k, **counts(v)} for k, v in sorted(groups["month"].items())],
            "matches": rows,
            "interpretation": "Exact textual matches only; duplicates are not independent observations. No semantic or causal claim."}


def _record(row):
    fields = ("id", "being", "lane", "occurred_at", "content_kind", "body_sha256", "raw_sha256",
              "source_path", "canonical_name", "mike_flag", "backend", "prompt_available", "contract", "time_source")
    result = {key: row[key] for key in fields}
    result["cached_text_sha256"] = _digest({key: row[key] for key in ("body_text", "raw_text")})
    return result


def _index_snapshot(conn):
    schema = [tuple(r) for r in conn.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name")]
    names = {row[1] for row in schema if row[0] == "table"}
    sources = [dict(r) for r in conn.execute("SELECT * FROM sources ORDER BY id")] if "sources" in names else []
    runs = []
    if "runs" in names:
        # Incremental scans accumulate coverage. Last-seen runs alone lose the
        # original import scope when an unchanged path is observed in a later scan.
        for row in conn.execute("SELECT * FROM runs ORDER BY id"):
            run = dict(row)
            for field in ("options_json", "summary_json"):
                if field in run:
                    try:
                        run[field.removesuffix("_json")] = json.loads(run[field] or "null")
                    except (TypeError, ValueError):
                        run[field.removesuffix("_json")] = {"unparsed": run[field]}
                    del run[field]
            runs.append(run)
    return {"user_version": conn.execute("PRAGMA user_version").fetchone()[0],
            "schema_version": conn.execute("PRAGMA schema_version").fetchone()[0],
            "schema_sha256": _digest(schema), "sqlite_version": sqlite3.sqlite_version,
            "catalog_entries": conn.execute("SELECT count(*) FROM catalog").fetchone()[0],
            "registered_sources": sources, "applicable_or_latest_runs": runs,
            "run_history_note": "All recorded runs retained to describe accumulated incremental coverage, including partial/failed runs.",
            "source_availability": "Cached index records only; source availability was not rechecked. Run options and summaries bound index coverage."}


def _fingerprint(records):
    return _digest([{key: record[key] for key in ("id", "body_sha256", "raw_sha256", "cached_text_sha256")}
                    for record in sorted(records, key=lambda r: r["id"])])


def sample(conn, per_being=4, since=None, until=None, seed="0", context=2, curated_ids=None) -> dict:
    """Choose S-001 ordered-list midpoints: floor((i + 0.5) * N / k).

    Sort by time, source path, then ID; k=min(per_being,N). Seed is a recorded label,
    not randomness. Curated selections are excluded from ordinary eligibility and
    may fall outside its filters. Context uses adjacent dated, nonempty prose,
    may cross the time filter, and is deduplicated with overlaps recorded.
    """
    if not isinstance(per_being, int) or not isinstance(context, int) or per_being < 0 or context < 0:
        raise ValueError("per_being and context must be nonnegative integers.")
    filters, values, scope = _filters(since=since, until=until)
    curated = list(dict.fromkeys(curated_ids or []))
    with _snapshot(conn):
        return _sample(conn, per_being, filters, values, scope, str(seed), context, curated)


def _sample(conn, count, filters, values, scope, seed, context, curated):
    selected, missing = [], []
    for entry_id in curated:
        row = conn.execute("SELECT * FROM catalog WHERE id=?", (entry_id,)).fetchone()
        if row is None:
            missing.append(entry_id)
        else:
            selected.append({**_record(row), "selection": "curated"})
    base = " FROM catalog c WHERE c.content_kind='prose' AND length(trim(c.body_text)) > 0"
    undated = {r[0]: r[1] for r in conn.execute("SELECT c.being,count(*)" + base + " AND c.occurred_at IS NULL GROUP BY c.being")}
    omission = (" AND c.id NOT IN (" + ",".join("?" for _ in curated) + ")") if curated else ""
    eligible = base + " AND c.occurred_at IS NOT NULL" + filters + omission
    params = [*values, *curated]
    groups = list(conn.execute("SELECT c.being,count(*)" + eligible + " GROUP BY c.being ORDER BY c.being", params))
    before = {r[0]: r[1] for r in conn.execute("SELECT c.being,count(*)" + base + " AND c.occurred_at IS NOT NULL" + filters + " GROUP BY c.being", values)}
    after = {r[0]: r[1] for r in groups}
    beings = [r[0] for r in conn.execute("SELECT DISTINCT being FROM catalog ORDER BY being")]
    denominators = [{"being": b, "dated_prose_before_curated_exclusion": before.get(b, 0),
                     "eligible_dated_prose": after.get(b, 0), "ordinary_selected": min(count, after.get(b, 0)),
                     "curated_dated_prose_excluded": before.get(b, 0) - after.get(b, 0)} for b in beings]
    for being, n in groups:
        k = min(count, n)
        for ordinal in range(k):
            position = ((2 * ordinal + 1) * n) // (2 * k)
            row = conn.execute("SELECT c.*" + eligible + " AND c.being IS ? ORDER BY c.occurred_at,COALESCE(c.source_path,''),c.id LIMIT 1 OFFSET ?", [*params, being, position]).fetchone()
            selected.append({**_record(row), "selection": "ordered_midpoint", "position": position,
                             "eligible_list_count": n})
    neighbors = {}
    for entry in selected:
        entry["context_ids"] = []
        if entry["occurred_at"] is None:
            entry["context_note"] = "Undated entry: chronological context unavailable."
            continue
        around, available = [], {"before": 0, "after": 0}
        for sign, operator, order in ((-1, "<", "DESC"), (1, ">", "ASC")):
            sql = ("SELECT * FROM catalog WHERE being IS ? AND content_kind='prose' AND length(trim(body_text))>0 "
                   "AND (occurred_at,COALESCE(source_path,''),id) " + operator + " (?,?,?) "
                   "ORDER BY occurred_at " + order + ",COALESCE(source_path,'') " + order + ",id " + order + " LIMIT ?")
            rows = conn.execute(sql, (entry["being"], entry["occurred_at"], entry["source_path"] or "", entry["id"], context))
            for distance, row in enumerate(rows, 1):
                ref = neighbors.setdefault(row["id"], {**_record(row), "uses": []})
                ref["uses"].append({"selected_id": entry["id"], "position": sign * distance})
                around.append((sign * distance, row["id"]))
                available["before" if sign < 0 else "after"] += 1
        entry["context_ids"] = [entry_id for _, entry_id in sorted(around)]
        entry["context_coverage"] = {"requested_each_side": context, **available,
                                     "missing_before": context - available["before"], "missing_after": context - available["after"]}
    selected_ids = {r["id"] for r in selected}
    context_entries = sorted(neighbors.values(), key=lambda r: (str(r["being"]), r["occurred_at"], r["source_path"] or "", r["id"]))
    records = {r["id"]: r for r in [*selected, *context_entries]}
    manifest = {"schema_version": 1, "method": "deterministic_ordered_midpoints_v1", "filters": scope,
                "ordering": ["occurred_at", "source_path", "id"], "position_formula": "floor((i + 0.5) * N / min(per_being, N))",
                "parameters": {"per_being": count, "seed": seed, "context": context, "curated_ids": curated},
                "eligibility": {"by_being": denominators, "total_eligible_dated_prose": sum(r[1] for r in groups),
                                "undated_prose_by_being_before_time_filters": undated,
                                "curated_excluded_from_ordinary": curated},
                "selected": selected, "context_entries": context_entries, "missing_curated_ids": missing,
                "overlap": {"context_ids_used_by_multiple_selections": [r["id"] for r in context_entries if len(r["uses"]) > 1],
                            "selected_ids_also_in_context": sorted(selected_ids & neighbors.keys())},
                "index_snapshot": _index_snapshot(conn), "content_fingerprint": _fingerprint(records.values()),
                "notes": ["Ordinary selection includes entries without question candidates.",
                          "Time filters are inclusive at since and exclusive at until; context may cross them.",
                          "Order-statistic midpoints follow S-001; seed is a recorded label only, not randomness.",
                          "Context uses all indexed, dated, nonempty prose lanes. Missing neighbors may reflect incomplete indexing.",
                          "Temporal sampling is descriptive, not a probability sample. Entries and overlapping contexts are dependent."]}
    manifest["manifest_sha256"] = _digest(manifest)
    return manifest


def _fenced(text, language=""):
    fence = "`" * max(3, 1 + max((len(run) for run in re.findall(r"`+", text)), default=0))
    return fence + language + "\n" + text + ("" if text.endswith("\n") else "\n") + fence + "\n"


def export_pack(conn, manifest, out_dir: Path) -> dict:
    """Export a frozen selection from cached text; reject changed selected material.

    The caller must enforce its permitted output roots. No source paths are opened.
    This function creates manifest.json and reading-pack.md, without inferred claims.
    Either pre-existing output causes refusal, preserving reader notes on re-export.
    """
    if not isinstance(manifest, dict) or manifest.get('schema_version') != 1:
        raise ValueError('Expected a version 1 research manifest object.')
    if not all(isinstance(manifest.get(k), list) for k in ('selected', 'context_entries')) or not isinstance(manifest.get('index_snapshot'), dict):
        raise ValueError('Manifest is missing its selection or index snapshot.')
    unsigned = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    if _digest(unsigned) != manifest.get("manifest_sha256"):
        raise ValueError("Manifest integrity check failed.")
    references = {}
    for record in [*manifest["selected"], *manifest["context_entries"]]:
        references.setdefault(record["id"], {}).update(record)
    with _snapshot(conn):
        current = _index_snapshot(conn)
        if any(current[k] != manifest["index_snapshot"][k] for k in ("user_version", "schema_sha256")):
            raise ValueError("Index schema changed since selection; create a new manifest.")
        rows = {}
        for entry_id, ref in references.items():
            row = conn.execute("SELECT * FROM catalog WHERE id=?", (entry_id,)).fetchone()
            if row is None or _record(row) != {k: ref[k] for k in _record(row)}:
                raise ValueError(f"Indexed entry changed or disappeared since selection: {entry_id}")
            rows[entry_id] = dict(row)
        if _fingerprint(_record(r) for r in rows.values()) != manifest["content_fingerprint"]:
            raise ValueError("Selected content fingerprint changed.")
    sections = ["# Reading pack\n\nCached source material for close reading. Candidate status, meaning, and interpretation remain for the reader.\n",
                "## Selection record\n\n" + _fenced(json.dumps({k: manifest[k] for k in ("method", "filters", "parameters", "eligibility", "overlap", "index_snapshot", "manifest_sha256")}, ensure_ascii=False, sort_keys=True, indent=2), "json")]
    selected = {r["id"]: r for r in manifest["selected"]}
    for ordinal, (entry_id, ref) in enumerate(references.items(), 1):
        role = selected[entry_id]["selection"] if entry_id in selected else "context"
        sections.append(f"## Entry {ordinal} · {role}\n\n" + _fenced(json.dumps(ref, ensure_ascii=False, sort_keys=True, indent=2), "json"))
        raw = rows[entry_id]["raw_text"]
        label = "Cached raw source, verbatim" if raw is not None else "Cached body only; raw source unavailable"
        sections.append(f"### {label}\n\n" + _fenced(raw if raw is not None else (rows[entry_id]["body_text"] or "")))
        sections.append("### Reader notes\n\n- Observation or question in the Being's wording: [unfilled]\n- Our interpretation: [unfilled]\n- Another plausible reading: [unfilled]\n- Missing context or next evidence: [unfilled]\n")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    manifest_path, pack_path = out_dir / "manifest.json", out_dir / "reading-pack.md"
    if manifest_path.exists() or pack_path.exists():
        raise FileExistsError("Pack output already exists; choose a fresh directory to preserve reader notes.")
    for path, text in ((manifest_path, json.dumps(manifest, sort_keys=True, ensure_ascii=False, indent=2) + "\n"),
                       (pack_path, "\n".join(sections))):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
    return {"manifest": str(manifest_path), "reading_pack": str(pack_path),
            "entries": len(references), "manifest_sha256": manifest["manifest_sha256"]}
