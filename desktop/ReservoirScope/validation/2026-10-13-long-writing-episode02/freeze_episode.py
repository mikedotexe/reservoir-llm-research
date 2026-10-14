#!/usr/bin/env python3
"""Bind this episode's completed preparation before the one admission sample."""
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
    required = ["PROTOCOL.md", "run-plan.json", "RUBRIC.md", "EVALUATION.md",
                "check_real_model_export.py", "test_real_model_export.py",
                "checker-tests-01.json", "PRE-RUN-REVIEW.md", "cleanup-result.json", "cleanup-protected-before.json",
                "admit_once.py", "freeze_episode.py", "reclaim_incremental.py", "owned_model.py", "test_owned_model.py",
                "helper-continuity-01.json", "package-provenance-01.json"]
    files = [identity(root / name) for name in required]
    files.extend(identity(desktop / "scripts" / name) for name in ("journal_quality.py", "test_journal_quality.py"))
    fixtures = desktop / "crates/reservoir-core/tests/fixtures/sustained-prompts"
    files.extend(identity(fixtures / name) for name in ("v4-observation-10.txt", "v4-memory-20.txt", "v4-provenance.json"))
    checker = json.loads((root / "checker-tests-01.json").read_text())
    receipt = {"schema": "reservoir-prospective-episode-freeze-v1",
               "frozenAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "episodeId": "long-writing-0.16.0-episode02", "status": "prospective-before-admission",
               "plannedOpportunities": 12, "newModelCallsAtFreeze": 0,
               "newSessionCreatedAtFreeze": False, "files": files,
               "checkerQualification": checker,
               "limits": ["Prior app/helper/evaluator checks are reused, not rerun claims.",
                          "No automatic accuracy, creative-quality or full-context verdict.",
                          "Later execution/results append without replacing this freeze."]}
    with (root / "evaluation-freeze-01.json").open("x") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"frozen": True, "files": len(files)}))


if __name__ == "__main__":
    main()
