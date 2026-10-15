#!/usr/bin/env python3
"""Freeze completed prospective preparation before one admission sample."""
from pathlib import Path
import datetime as dt
import hashlib
import json


def identity(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    root = Path(__file__).resolve().parent
    desktop = root.parents[1]
    required = ['PROTOCOL.md', 'run-plan.json', 'RUBRIC.md', 'EVALUATION.md', 'check_real_model_export.py', 'test_real_model_export.py', 'review-helper-reuse-01.json', 'preparation-reuse-01.json', 'admit_once.py', 'freeze_episode.py', 'owned_model.py', 'test_owned_model.py', 'software-selection.json', 'helper-source-continuity-01.json', 'RUNTIME-REVIEW.md', 'runtime-review-01.json', 'HELPER-REVIEW.md', 'owned-helper-tests-02.json', 'journal_quality.py', 'test_journal_quality.py']
    files = [identity(root / name) for name in required]
    files.extend(identity(path) for path in sorted((root / "runtime-sources-01").rglob("*")) if path.is_file())
    reused = json.loads((root / "preparation-reuse-01.json").read_text())["files"]
    for item in reused:
        now = identity(Path(item["path"]))
        if now["sha256"] != item["sha256"]:
            raise ValueError("Reused preparation identity changed")
        files.append(now)
    previous = json.loads((root.parent / "2026-10-14-v6-writing-episode01/evaluation-freeze-01.json").read_text())
    for item in previous["files"]:
        now = identity(Path(item["path"]))
        if now["sha256"] != item["sha256"]:
            raise ValueError("Episode01 frozen input changed")
        files.append(now)
    fixtures = desktop / "crates/reservoir-core/tests/fixtures/sustained-prompts"
    files.extend(identity(fixtures / name) for name in ("v6-observation-10.txt", "v6-memory-20.txt", "v6-provenance.json"))
    receipt = {"schema": "reservoir-prospective-episode-freeze-v1",
               "frozenAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "episodeId": "v6-writing-0.18.0-episode02", "status": "prospective-before-admission",
               "plannedOpportunities": 12, "newModelCallsAtFreeze": 0,
               "newSessionCreatedAtFreeze": False, "files": files,
               "checkerQualificationReusedFrom": str(root.parent / "2026-10-14-v6-writing-episode01/checker-qualification-02.json"),
               "limits": ["Prior app/helper tests are reused, not rerun claims.",
                          "No automatic accuracy, creative-quality or full-context verdict.",
                          "Later execution/results append without replacing this freeze."]}
    with (root / "evaluation-freeze-01.json").open("x") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"frozen": True, "files": len(files)}))


if __name__ == "__main__":
    main()
