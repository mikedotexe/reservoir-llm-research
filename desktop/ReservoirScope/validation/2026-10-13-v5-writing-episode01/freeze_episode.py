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
    required = ["PROTOCOL.md", "run-plan.json", "RUBRIC.md", "EVALUATION.md",
                "check_real_model_export.py", "test_real_model_export.py",
                "checker-tests-01.json", "checker-freeze-01.json", "PRE-RUN-REVIEW.md",
                "admit_once.py", "freeze_episode.py", "owned_model.py", "test_owned_model.py",
                "helper-continuity-01.json", "package-provenance-01.json",
                "journal_quality.py", "test_journal_quality.py", "quality-helper-tests-01.json"]
    files = [identity(root / name) for name in required]
    fixtures = desktop / "crates/reservoir-core/tests/fixtures/sustained-prompts"
    files.extend(identity(fixtures / name) for name in ("v5-observation-10.txt", "v5-memory-20.txt", "v5-provenance.json"))
    receipt = {"schema": "reservoir-prospective-episode-freeze-v1",
               "frozenAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "episodeId": "v5-writing-0.17.0-episode01", "status": "prospective-before-admission",
               "plannedOpportunities": 12, "newModelCallsAtFreeze": 0,
               "newSessionCreatedAtFreeze": False, "files": files,
               "checkerQualification": json.loads((root / "checker-tests-01.json").read_text()),
               "limits": ["Prior app/helper tests are reused, not rerun claims.",
                          "No automatic accuracy, creative-quality or full-context verdict.",
                          "Later execution/results append without replacing this freeze."]}
    with (root / "evaluation-freeze-01.json").open("x") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"frozen": True, "files": len(files)}))


if __name__ == "__main__":
    main()
