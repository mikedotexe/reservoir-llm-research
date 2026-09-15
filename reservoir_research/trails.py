"""Bounded literal leads across cached journal originals and generation records.

These are textual candidates, never reconstructed execution or learning stages.
Source paths and identifiers are retained as evidence and are never opened.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path

from .explore import _digest, _fenced, _index_snapshot, _snapshot
from .segments import split_channels

SCHEMA_VERSION = 1
MAX_SPANS_PER_RECORD = 40
CONTEXT_CHARACTERS = 160
_FIELDS = {"journal": ("raw_text",),
           "generation": ("prompt_text", "response_text", "metadata_json")}
_CAVEATS = [
    "Literal lead matches are not causal links or proof of execution, delivery, learning, or change.",
    "Journal raw_text includes headers and action requests removed from cleaned search; its text is cached and decoded.",
    "Generation metadata_json is serialized record metadata, not necessarily model-visible language.",
    "Window bounds are inclusive at since and exclusive at until; undated records are counted separately and excluded.",
    "Channel labels describe textual marker boundaries; reply targets are literal tokens, not verified thread identities.",
    "Coverage is limited to the index snapshot; source files, source freshness, and missing intervening events were not checked.",
]


def _validate(terms, being, since, until, limit):
    if not isinstance(terms, list) or not terms or any(not isinstance(t, str) or not t.strip() for t in terms):
        raise ValueError("Provide a nonempty list of nonblank literal terms.")
    if not isinstance(being, str) or being.casefold() not in {"astrid", "minime"}:
        raise ValueError("being must be astrid or minime.")
    for value in (since, until):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("An explicit finite since/until date window is required.")
        try:
            datetime.fromtimestamp(value, timezone.utc)
        except (ValueError, OverflowError, OSError) as exc:
            raise ValueError("Date window is outside the supported calendar range.") from exc
    if since >= until:
        raise ValueError("since must precede until.")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer.")
    return list(dict.fromkeys(terms)), being.casefold(), float(since), float(until)


def _matches(row, kind, terms):
    candidates, counts, field_hashes = [], [], {}
    for field_order, field in enumerate(_FIELDS[kind]):
        text = row[field]
        if text is None:
            field_hashes[field] = None
            continue
        field_hashes[field] = hashlib.sha256(text.encode()).hexdigest()
        for term_order, term in enumerate(terms):
            count = text.count(term)
            if not count:
                continue
            counts.append({"field": field, "term": term, "occurrences": count})
            start = 0
            for _ in range(min(count, MAX_SPANS_PER_RECORD)):
                start = text.find(term, start)
                end = start + len(term)
                candidates.append((field_order, start, term_order, end, term))
                start = end
    spans = []
    segments = split_channels(row["raw_text"]) if kind == "journal" else []
    for field_order, start, _, end, term in sorted(candidates)[:MAX_SPANS_PER_RECORD]:
        field = _FIELDS[kind][field_order]
        text = row[field]
        left, right = max(0, start - CONTEXT_CHARACTERS), min(len(text), end + CONTEXT_CHARACTERS)
        channels = [s for s in segments if s["start_offset"] <= start and end <= s["end_offset"]]
        spans.append({"field": field, "term": term, "start_offset": start, "end_offset": end,
                      "text": text[start:end], "context_start_offset": left,
                      "context_end_offset": right, "context_text": text[left:right],
                      "channel": channels[0]["channel"] if len(channels) == 1 else None,
                      "reply_target": channels[0]["reply_target"] if len(channels) == 1 else None})
    total = sum(item["occurrences"] for item in counts)
    return {"field_sha256": field_hashes, "match_counts": counts, "match_occurrences": total,
            "matched_spans": spans, "returned_spans": len(spans), "spans_truncated": total > len(spans)}


def collect_trail(conn, terms: list[str], being: str, since: float, until: float, limit: int = 100) -> dict:
    """Read a consistent cached snapshot, searching case-sensitive literal text.

Record limits apply after merging both kinds chronologically. Within each field,
occurrences are nonoverlapping per term; different terms may overlap. Span offsets
count Python string characters. No selected field's text is normalized for search.
"""
    terms, being, since, until = _validate(terms, being, since, until, limit)
    with _snapshot(conn):
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
        if "catalog" not in names:
            raise ValueError("The index has no journal catalog.")
        denominators, matches, total_matching, missing = [], [], 0, []
        for kind, table in (("journal", "catalog"), ("generation", "generations")):
            if table not in names:
                missing.append(kind)
                denominators.append({"kind": kind, "being": being, "available": False,
                                     "total_indexed": None, "dated_in_window": None,
                                     "undated_before_time_filter": None, "undated_matching_excluded": None})
                continue
            terms_sql = " OR ".join(f"instr(COALESCE({field}, ''), ?) > 0"
                                    for field in _FIELDS[kind] for _ in terms)
            term_values = terms * len(_FIELDS[kind])
            values = (being, since, until)
            denominator = conn.execute(f'''SELECT COUNT(*) AS total_indexed,
                COALESCE(SUM(occurred_at>=? AND occurred_at<?),0) AS dated_in_window,
                COALESCE(SUM(occurred_at IS NULL),0) AS undated_before_time_filter
                FROM {table} WHERE being=?''', (since, until, being)).fetchone()
            undated = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE being=? AND occurred_at IS NULL AND ({terms_sql})",
                                   (being, *term_values)).fetchone()[0]
            denominators.append({"kind": kind, "being": being, "available": True,
                                 **dict(denominator), "undated_matching_excluded": undated})
            where = f"being=? AND occurred_at>=? AND occurred_at<? AND ({terms_sql})"
            count = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", (*values, *term_values)).fetchone()[0]
            total_matching += count
            columns = ("id,being,occurred_at,lane,source_path,raw_text,raw_sha256,next_raw,backend,prompt_available"
                       if kind == "journal" else
                       "id,being,occurred_at,lane,source_path,source_sha256,prompt_text,response_text,metadata_json,backend,prompt_available")
            rows = conn.execute(f"SELECT {columns} FROM {table} WHERE {where} ORDER BY occurred_at,id LIMIT ?",
                                (*values, *term_values, limit))
            matches.extend((kind, dict(row)) for row in rows)
        ordered = sorted(matches, key=lambda item: (item[1]["occurred_at"], item[0], item[1]["id"]))[:limit]
        records = []
        for kind, row in ordered:
            record = {key: row[key] for key in ("id", "being", "occurred_at", "lane", "source_path", "backend", "prompt_available")}
            record.update(kind=kind, time_utc=datetime.fromtimestamp(row["occurred_at"], timezone.utc).isoformat(),
                          raw_sha256=row.get("raw_sha256"), source_sha256=row.get("source_sha256"),
                          next_raw=row.get("next_raw"), **_matches(row, kind, terms))
            records.append(record)
        result = {"schema_version": SCHEMA_VERSION, "method": "cached_case_sensitive_literal_trail_v1",
                  "filters": {"being": being, "since": since, "until": until}, "terms": terms,
                  "parameters": {"limit": limit, "max_spans_per_record": MAX_SPANS_PER_RECORD,
                                 "context_characters_each_side": CONTEXT_CHARACTERS},
                  "ordering": ["occurred_at", "kind", "id"],
                  "denominators": denominators, "missing_kinds": missing,
                  "total_matching": total_matching, "returned": len(records),
                  "truncated": total_matching > len(records), "records": records,
                  "index_snapshot": _index_snapshot(conn), "content_fingerprint": _digest(records),
                  "caveats": _CAVEATS.copy()}
        result["result_sha256"] = _digest(result)
        return result


def export_trail(result: dict, out_dir: Path) -> dict:
    """Write deterministic JSON and Markdown to a new private directory.

The caller must protect output roots. Export uses only the frozen result, does
not consult the index or sources, and refuses any existing destination directory.
"""
    if not isinstance(result, dict) or result.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Expected a version 1 source-trail result.")
    if _digest({key: value for key, value in result.items() if key != "result_sha256"}) != result.get("result_sha256"):
        raise ValueError("Source-trail integrity check failed.")
    if _digest(result.get("records")) != result.get("content_fingerprint"):
        raise ValueError("Source-trail content fingerprint failed.")
    sections = ["# Cached source trail\n\nLiteral leads for further reading. Sequence alone does not establish cause.\n",
                "## Scope\n\n" + _fenced(json.dumps({key: result[key] for key in (
                    "filters", "terms", "parameters", "denominators", "missing_kinds",
                    "total_matching", "returned", "truncated", "content_fingerprint", "result_sha256")},
                    ensure_ascii=False, sort_keys=True, indent=2), "json"),
                "## Unknowns and limits\n\n" + "\n".join("- " + caveat for caveat in result["caveats"]) + "\n"]
    for number, record in enumerate(result["records"], 1):
        sections.append(f"## {number}. {record['kind']} · {record['time_utc']}\n\n" +
                        _fenced(json.dumps({key: value for key, value in record.items() if key != "matched_spans"},
                                          ensure_ascii=False, sort_keys=True, indent=2), "json"))
        for span in record["matched_spans"]:
            sections.append(f"### {span['field']} · match characters {span['start_offset']}–{span['end_offset']}\n\n"
                            f"Exact cached context: characters {span['context_start_offset']}–{span['context_end_offset']}.\n\n" +
                            _fenced(span["context_text"]))
    json_text = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    markdown = "\n".join(sections)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    created = []
    try:
        for name, text in (("trail.json", json_text), ("trail.md", markdown)):
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
    return {"json": str(out_dir / "trail.json"), "markdown": str(out_dir / "trail.md"),
            "records": result["returned"], "result_sha256": result["result_sha256"]}
