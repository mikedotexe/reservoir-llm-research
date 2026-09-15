#!/usr/bin/env python3
"""Read-only, bounded Git-message census for S-006; standard library only.

Snapshots HEAD before scanning (no fetch, index refresh, runtime imports or live
commands). A literal report/file reference is a candidate link, not causation.
Outputs only beneath this research repo. Does not read journal contents.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REF = re.compile(r"\bintrospection_[A-Za-z0-9_]+_\d{10}\b|!?\b(?:self_study|astrid|reply|moment|pressure|daydream|aspiration|lend_aperture_held)_[A-Za-z0-9_.:-]+\.txt\b")


def git(repo, *args):
    return subprocess.check_output(
        ["git", "--no-optional-locks", "-C", str(repo), *args],
        timeout=600,
    )


def summarize(rows):
    result = {}
    for being in sorted({r["repository"] for r in rows}):
        subset = [r for r in rows if r["repository"] == being]
        refs = [r for r in subset if r["references"]]
        archives = [r for r in subset if "Steward-Archive:" in r["message"]]
        result[being] = {
            "commits": len(subset), "literal_reference_commits": len(refs),
            "unique_literal_references": len({x for r in refs for x in r["references"]}),
            "flywheel_mention_commits": sum("flywheel" in r["message"].lower() for r in subset),
            "archive_marker_commits": len(archives),
            "archive_label_line_commits": sum(bool(re.search(r"(?m)^Steward-Archive: introspection-flywheel-v1\s*$", r["message"])) for r in subset),
            "earliest_archive_committer_time": min((r["committed_at"] for r in archives), default=None),
            "archive_unique_reports": len({x for r in archives for x in r["references"]}),
            "committer_months": dict(sorted(Counter(r["committed_at"][:7] for r in subset).items())),
            "reference_committer_months": dict(sorted(Counter(r["committed_at"][:7] for r in refs).items())),
            "earliest_observed_reference_commit": min(refs, key=lambda r:r["committed_at"])["sha"] if refs else None,
        }
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", type=Path, default=ROOT.parent)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--replay", type=Path, help="Recompute counts from retained history.json")
    p.add_argument("--since", default="2026-05-01T00:00:00Z")
    p.add_argument("--until", default="2026-09-08T03:15:00Z")
    p.add_argument("--limit", type=int, default=2000)
    p.add_argument("--all-refs", action="store_true", help="Pin local branch and remote-tracking tips, without fetching")
    a = p.parse_args()
    out = a.out.resolve()
    if not out.is_relative_to(ROOT / "research" / "outputs"):
        p.error("Output must be within research/outputs")
    if out.exists():
        p.error("Choose a new output directory")
    if not 1 <= a.limit <= 5000:
        p.error("Limit must be 1–5000")
    out.mkdir(parents=True, mode=0o700)
    if a.replay:
        data = json.loads(a.replay.read_text())
    else:
        data = {"captured_at": datetime.now(timezone.utc).isoformat(),
                "since": a.since, "until": a.until, "limit_per_repo": a.limit,
                "scope": "committer-time Git traversal on pinned tips; merges included; no remote refresh",
                "sources": {}, "commits": []}
        for being in ("astrid", "minime"):
            repo = a.base / being
            head = git(repo, "rev-parse", "HEAD").decode().strip()
            refs = {}
            if a.all_refs:
                for line in git(repo, "for-each-ref", "--format=%(objectname) %(refname)", "refs/heads", "refs/remotes").decode().splitlines():
                    sha, name = line.split(" ", 1)
                    refs[name] = sha
            tips = sorted({head, *refs.values()})
            args = ["log", *tips, f"--since={a.since}", f"--until={a.until}",
                    f"-n{a.limit}", "--format=%H%x00%aI%x00%cI%x00%P%x00%B%x00%x1e"]
            raw = git(repo, *args)
            (out / f"{being}-git-log.bin").write_bytes(raw)
            rows = []
            for record in raw.decode("utf-8").split("\x1e"):
                record = record.lstrip("\n")
                if not record:
                    continue
                sha, authored, committed, parents, message, remainder = record.split("\x00", 5)
                assert not remainder.strip()
                rows.append({"repository": being, "sha": sha, "authored_at": authored,
                             "committed_at": committed, "parents": parents.split(),
                             "message": message, "references": sorted(set(REF.findall(message)))})
            data["commits"].extend(rows)
            data["sources"][being] = {"path": str(repo.resolve()), "head": head,
                "raw_sha256": hashlib.sha256(raw).hexdigest(), "command": args, "refs": refs,
                "cap_reached": len(rows) == a.limit}
            print(json.dumps({"captured": being, "commits": len(rows), "head": head}), flush=True)
    (out / "history.json").write_text(json.dumps(data, indent=2) + "\n")
    summary = summarize(data["commits"])
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    candidates = [r for r in data["commits"] if r["references"]]
    (out / "candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
    for file in out.iterdir():
        file.chmod(0o600)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
