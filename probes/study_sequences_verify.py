"""Offline reproducibility, exact journal spans and complete-source checks for S-008."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reservoir_research.study_capture import REPO, encoded, private_write, sha
from reservoir_research.study_sequences import build_report, receipt_records


def verify(capture, report_path):
    raw = capture.read_bytes()
    packet, saved = json.loads(raw), json.loads(report_path.read_bytes())
    rebuilt = build_report(packet)
    assert all(saved[key] == value for key, value in rebuilt.items()), "Report replay differs"
    assert saved["capture_sha256"] == sha(raw)
    assert sha((report_path.parent / "reporter.py").read_bytes()) == saved["reporter_sha256"]
    for name, digest in saved["dependency_sha256"].items():
        assert sha((report_path.parent / name).read_bytes()) == digest
    assert sha((capture.parent / "protocol.md").read_bytes()) == packet["protocol_sha256"]
    assert sha((capture.parent / "collector.py").read_bytes()) == packet["collector_sha256"]
    assert sha((capture.parent / "parsing.py").read_bytes()) == packet["parser_sha256"]
    originals = {r["path"]: r["text"] for r in packet["records"]}
    spans = 0
    for row in saved["studies"] + saved["reading_requests"]:
        text = row.get("text", row.get("response_text"))
        for link in row["writing"]:
            reconstructed = "".join(originals[link["path"]][a:b] for a,b in link["source_spans"])
            assert reconstructed == text
            assert sha(reconstructed.encode()) == link["response_sha256"]
            spans += 1
    revisions = defaultdict(list)
    for receipt in receipt_records(packet["records"]):
        page = receipt["page"]
        if receipt["verified"] and page:
            revisions[(receipt["being"], page["source"], page["revision"]["sha256"])].append(page)
    sources = []
    for (being, source, digest), pages in revisions.items():
        size = pages[0]["revision"]["bytes"]
        assert 0 <= size <= 64*1024*1024
        data, covered = bytearray(size), bytearray(size)
        for page in pages:
            start, end = page["start"]["byte"], page["end"]["byte"]
            rendered = "".join(m[1] + "\n" for line in page["text"].splitlines()
                               if (m := re.fullmatch(r"\s*\d+ \| (.*)", line))).encode()
            assert len(rendered) in (end-start, end-start+1)
            fragment = rendered[:end-start]
            for index, byte in enumerate(fragment, start):
                assert not covered[index] or data[index] == byte, "Overlapping source bytes disagree"
                data[index], covered[index] = byte, 1
        full = all(covered)
        if full:
            assert sha(bytes(data)) == digest, "Reconstructed source revision differs"
        sources.append(dict(being=being, source=source, revision=digest, receipts=len(pages),
                            unique_bytes=sum(covered), file_bytes=size, full_file_hash_verified=full))
    counts = Counter((a["being"], a["period"], a["requested_category"], a["route"], a["status"])
                     for a in saved["reading_actions"])
    return dict(verified=True, capture_sha256=sha(raw), report_sha256=sha(report_path.read_bytes()),
        captured_records=len(packet["records"]), exact_writing_links_verified=spans,
        source_reconstructions=sources,
        reading_action_counts=[dict(being=k[0], period=k[1], requested=k[2], route=k[3], status=k[4], n=v)
                               for k,v in sorted(counts.items())],
        post_reading_requests=len([x for x in saved["reading_requests"] if x["period"] == "after"]),
        post_reading_request_journal_matches=sum(bool(x["writing"]) for x in saved["reading_requests"] if x["period"] == "after"),
        read_more_actions=sum(a["requested_category"] == "READ_MORE" for a in saved["reading_actions"]),
        study_jobs=len(saved["study_jobs"]), completed_studies_after=sum(s["era"] == "after" and s["status"] == "ok" for s in saved["studies"]),
        capture_errors=len(saved["capture_errors"]), invalid_receipts=len(saved["invalid_receipts"]),
        ambiguous_or_missing_receipt_joins=len(saved["receipt_join_issues"]))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("capture", type=Path)
    p.add_argument("report", type=Path)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if not args.out.resolve().is_relative_to(REPO / "research/outputs"):
        raise ValueError("Research output required")
    result = verify(args.capture, args.report)
    private_write(args.out, encoded(result))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
