#!/usr/bin/env python3
"""Freeze explicitly selected S-006 sources; read-only toward sibling repos.

Standard library only. Fixed allowlist, bounded stable reads, no runtime imports,
database access, journal recursion, service calls, or source-directed commands.
Output includes full selected text privately; controller receipt is projected
through an allowlist, excluding lease/token fields. Dates/counts are reproducible.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
REPORTS = {
    "unicode": ("introspection_astrid_llm_1786076073", "3d810535c0226111cfdebe598de62ce4b7ed236387566fe471cf71454289bfa2"),
    "pressure": ("introspection_minime_regulator_1785629184", "f7c527e1d63e95686b979018e16d0f60694b6c841d9eb1534402eb73e497ffcf"),
    "correspondence": ("introspection_minime_autonomous_agent_1785375952", "1717fa920adab84a6b266b60cc49e4f142027016c7eb34a9adb90cbf62d05637"),
    "codec": ("introspection_astrid_codec_1788784520", None),
}
COMMITS = {"unicode": ("astrid", "6344ba25e9d3"), "pressure": ("minime", "fa0fbf1e16df"),
           "correspondence": ("minime", "7ad16072c9ef"), "codec": ("astrid", "44ea2f4903")}
PACKET = "docs/steward-notes/claude-heartbeat_1788791389_codec_projection_fixed_legacy_basis_attribution/"
FILES = [
    "scripts/flywheel_loop_prompt.txt", "scripts/flywheel_loop_run.sh", "scripts/flywheel_round_child.sh",
    "scripts/steward_control/executor.py", "scripts/self_study_effectiveness.py",
    "docs/steward-notes/AI_BEINGS_FEEDBACK_TO_CHANGE_LEDGER.md",
    "docs/steward-notes/2026-09-07-marker-annotation-preservation.md",
    "docs/steward-notes/2026-09-07-marker-preservation-live-rollout.md",
    "capsules/spectral-bridge/workspace/journal/self_study_1788800559.txt",
    "capsules/spectral-bridge/workspace/journal/!self_study_1788815877.txt",
] + [PACKET+n for n in ["RUN_REPORT.md", "read_manifest.json", "source_receipts.json",
                        "test_results.json", "verification_receipt.json", "unprocessed_selected.json"]]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", type=Path, default=ROOT.parent)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    out = a.out.resolve()
    if not out.is_relative_to(ROOT / "research" / "outputs") or out.exists():
        p.error("Choose a new directory beneath research/outputs")
    out.mkdir(parents=True, mode=0o700)
    records = []
    def retain(raw, source, kind):
        file = out / f"{len(records):03d}.txt"
        file.write_bytes(raw)
        file.chmod(0o600)
        row = {"file":file.name,"source":source,"kind":kind,"bytes":len(raw),
               "sha256":hashlib.sha256(raw).hexdigest()}
        records.append(row)
        return row
    def read(relative):
        path = a.base / "astrid" / relative
        before = path.stat()
        if not path.is_file() or path.is_symlink() or before.st_size > 4*1024*1024:
            raise ValueError(f"Not a bounded regular source: {path}")
        raw = path.read_bytes()
        after = path.stat()
        if (before.st_size,before.st_mtime_ns) != (after.st_size,after.st_mtime_ns):
            raise ValueError(f"Source changed while reading: {path}")
        return raw
    def git(being,*args):
        return subprocess.check_output(["git","--no-optional-locks","-C",str(a.base/being),*args],timeout=90)
    for rel in FILES:
        retain(read(rel), f"astrid/{rel}", "working_file")
    reports = {}
    for case,(name,expected) in REPORTS.items():
        rel = "capsules/spectral-bridge/workspace/introspections/"+name+".txt"
        raw = read(rel)
        receipt = retain(raw,"astrid/"+rel,"original_report")
        if expected:
            assert receipt["sha256"] == expected, case
        text = raw.decode()
        ts = int(re.search(r"(?m)^Timestamp: (\d+)$",text)[1])
        reports[case] = {"id":name,"sha256":receipt["sha256"],"header":text.splitlines()[0],
            "timestamp":ts,"utc":datetime.fromtimestamp(ts,timezone.utc).isoformat(),
            "pacific":datetime.fromtimestamp(ts,ZoneInfo("America/Los_Angeles")).isoformat()}
        being,short = COMMITS[case]
        sha = git(being,"rev-parse",short).decode().strip()
        msg = git(being,"show","-s","--format=%B",sha)
        retain(msg,f"{being}@{sha}","commit_message")
        # Some archives put their Source metadata inside the blockquote. That
        # is a citation, not a claim that the being authored the citation line.
        quotes = [q for q in re.findall(r"(?m)^> (.+)$",msg.decode()) if not q.startswith("Source:")]
        reports[case]["commit_sha"] = sha
        reports[case]["quote_checks"] = [{"quote":q,"exact_substring":q in text} for q in quotes]
        retain(git(being,"show","--format=","--no-ext-diff",sha),f"{being}@{sha}","commit_diff")
        retain(git(being,"diff-tree","--no-commit-id","--name-only","-r",sha),f"{being}@{sha}","changed_paths")
    for name in ["RUN_REPORT.md","claims/llm_1786076073.json","read_manifest.json","test_results.json","deployment_alignment.json"]:
        rel = "docs/steward-notes/codex_1786077892_llm_unicode_delimiters_round/"+name
        retain(git("astrid","show",COMMITS["unicode"][1]+":"+rel),f"astrid@{COMMITS['unicode'][1]}:{rel}","historical_packet")
    rel = "capsules/spectral-bridge/workspace/diagnostics/steward_control_v1/runs/run_1788786399252113000_c8bd381221.json"
    raw = read(rel)
    d = json.loads(raw)
    receipt = {k:d.get(k) for k in ["schema","run_id","actor","adapter_kind","started_at","finished_at","status","outcome","exit_code","requested_outcome"]}
    receipt["source_bytes_sha256"] = hashlib.sha256(raw).hexdigest()
    receipt["projection_note"] = "Allowlisted fields only; lease/token fields omitted"
    receipt["elapsed_minutes"] = (datetime.fromisoformat(d["finished_at"])-datetime.fromisoformat(d["started_at"])).total_seconds()/60
    retain((json.dumps(receipt,indent=2)+"\n").encode(),"astrid/"+rel,"projected_controller_receipt")
    result = {"captured_at":datetime.now(timezone.utc).isoformat(),"sources":records,"cases":reports,
              "codec_run":receipt,"all_quoted_substrings_match":all(q["exact_substring"] for r in reports.values() for q in r["quote_checks"])}
    assert result["all_quoted_substrings_match"]
    (out/"manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    (out/"manifest.json").chmod(0o600)
    print(json.dumps({"captured_files":len(records),"cases":reports,"codec_run":receipt},indent=2))


if __name__ == "__main__":
    main()
