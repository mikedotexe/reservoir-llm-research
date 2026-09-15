#!/usr/bin/env python3
"""Verify retained S-006 evidence and scanner outputs without live-source access."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/outputs/2026-09-07-flywheel"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    evidence = BASE / "evidence-final"
    manifest = json.loads((evidence / "manifest.json").read_text())
    for row in manifest["sources"]:
        p = evidence / row["file"]
        assert sha(p) == row["sha256"]
        assert p.stat().st_size == row["bytes"]
    assert manifest["all_quoted_substrings_match"]
    history = BASE / "all-refs"
    h = json.loads((history / "history.json").read_text())
    replay = json.loads((BASE / "history-replay/history.json").read_text())
    assert h == replay
    for name, source in h["sources"].items():
        assert sha(history / f"{name}-git-log.bin") == source["raw_sha256"]
    marker = BASE / "marker-observed"
    r = json.loads((marker / "result.json").read_text())
    for label in ("before", "after"):
        receipt = r["source_receipts"][label]
        assert sha(marker / f"{label}-full.rs") == receipt["full_sha256"]
        assert sha(marker / f"{label}-constants.rs") == receipt["constant_file_sha256"]
        assert sha(marker / f"{label}-scanner") == receipt["binary_sha256"]
        source = (marker / f"{label}-full.rs").read_text()
        span = "".join(source.splitlines(keepends=True)[receipt["scanner_start_line"]-1:receipt["scanner_end_line"]])
        assert hashlib.sha256(span.encode()).hexdigest() == receipt["scanner_span_sha256"]
        assert span in (marker / f"{label}-harness.rs").read_text()
        rows = []
        for line in (marker / f"{label}-output.tsv").read_text().splitlines():
            i, count, hex_value = line.split("\t")
            rows.append({"id":r["cases"][int(i)]["id"],"matches":int(count),"output":bytes.fromhex(hex_value).decode()})
        assert rows == r["results"][label]
    original = (evidence / "016.txt").read_text()
    binding = re.search(r"(?m)^Source SHA-256: ([0-9a-f]{64})$", original)[1]
    assert binding == r["source_receipts"]["before"]["full_sha256"]
    changed = [i for i,(b,a) in enumerate(zip(r["results"]["before"],r["results"]["after"])) if b["output"] != a["output"]]
    assert changed == list(range(9))
    assert all(row["output"] == c["expected_after"] for row,c in zip(r["results"]["after"],r["cases"]))
    result = {"status":"passed","retained_files_verified":len(manifest["sources"]),
              "original_report_to_parent_source_hash":"matched",
              "history_replay":"identical","scanner_source_spans":"exact",
              "executed_binary_hashes":"matched retained bytes",
              "changed_case_indices":changed,"control_cases_unchanged":8,
              "limits":"Does not revalidate historical test/deployment claims or independently replay generation exposure"}
    output = BASE / "verification.json"
    output.write_text(json.dumps(result,indent=2)+"\n")
    output.chmod(0o600)
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
