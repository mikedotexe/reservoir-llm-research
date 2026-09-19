"""Derived daily S-007 denominators from an independently verified maintained report.

No collection, ledger writes, sample-specific claims, or quality scoring.
"""
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path


def build(packet, report_path):
    packet, report_path = Path(packet), Path(report_path)
    report_raw = report_path.read_bytes()
    r = json.loads(report_raw)
    rows = r["studies"]
    if len(rows) != r["generation_count"] or len({x["id"] for x in rows}) != len(rows):
        raise ValueError("Generation denominator differs")
    source = [x for x in rows if x["actual_route"] == "source_study"]
    private = [x for x in rows if x["actual_route"] == "extended_writing"]
    pages = [p for x in source for p in x["pages"]]
    counted = lambda values: dict(sorted(Counter(values).items()))
    at = lambda x: datetime.fromisoformat(x.replace("Z", "+00:00"))
    selected = [next(x for x in rows if x["id"] == i) for i in r["close_reading_ids"]]
    return {
        "schema": "s007-daily-descriptive-account-v1",
        "status": "derived; acceptance requires independent report verification",
        "report_sha256": hashlib.sha256(report_raw).hexdigest(),
        "capture_sha256": r["capture_sha256"],
        "supplement_sha256": r["supplement_sha256"],
        "counts": {
            "generations": len(rows),
            "routes": counted(x["actual_route"] for x in rows),
            "source_study_completed": sum(x["status"] == "ok" for x in source),
            "source_study_other_status": counted(x["status"] for x in source if x["status"] != "ok"),
            "private_writing_generations": len(private),
            "source_receipts_verified": sum(x["receipt_verified"] for x in source),
            "source_full_journal_matches": sum(bool(x["writing"]) for x in source),
            "source_page_opportunities": len(pages),
            "source_page_opportunities_by_repository": counted(p["source"].split("/")[0] for p in pages),
            "source_revisions": len(r["sources"]),
            "fully_reconstructed_revisions": sum(x["full_file_hash_verified"] for x in r["sources"]),
            "notebooks_supplied": sum(x["notebook"].get("status") == "included_in_submitted_user_text" for x in source),
            "statuses": counted(x["status"] for x in rows),
            "kinds": counted(x["kind"] for x in rows),
            "cap_hits": sum(bool(x["cap_hit"]) for x in rows),
            "filename_jobs": r["jobs_queued"],
            "expanded_linked_jobs": r["expanded_linked_jobs"],
        },
        "sources": r["sources"],
        "process_eras": r["eras"],
        "jobs_without_window_generation": r["jobs_without_window_generation"],
        "source_rows_without_full_journal_match": [
            {k:x[k] for k in ("id", "completed", "record_sha256", "response_sha256", "job_id", "linked_artifacts", "journal_status")}
            for x in source if not x["writing"]
        ],
        "minime_owned_page": next(
            ({"id":x["id"], "page":p} for x in source for p in x["pages"]
             if p["source"].split("/")[0] == "minime"), None),
        "selected": [
            {**{k:x[k] for k in ("id", "completed", "started_utc", "actual_route", "pages", "record_sha256", "response_sha256", "next_action")},
             "began_before_window": at(x["started_utc"]) < at(r["selection"]["since"])}
            for x in selected
        ],
        "limits": [
            "Distinct denominators: generations, routes, jobs, receipt delivery, journal matches, pages, revisions.",
            "Filename capture boundaries differ from completion-window selection.",
            "Source ownership is literal repository identity, not study author identity.",
            "Counts do not establish factual correctness, understanding, correction or causal improvement.",
            "No later outcome selection or prose-quality search is performed here.",
        ],
    }

