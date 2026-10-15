#!/usr/bin/env python3
"""Run prepared pure Python helper tests after root authorization; no real provider.

The temporary fixtures are synthetic and production-verifier subprocesses are
mocked. This wrapper invokes only the Python unit suite and preserves an exclusive
log/receipt with exact before/after helper and v8 golden identities.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1]

def digest(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def sources():
    paths = [HERE / n for n in ("run_helper_checks.py", "check_fixture_export.py", "test_check_fixture_export.py",
             "owned_provider.py", "test_owned_provider.py", "check_reanchored_tamper.py", "test_reanchored_tamper.py")]
    paths += [DESKTOP / "crates/reservoir-core/tests/fixtures/sustained-prompts" / n
              for n in ("v8-observation-10.txt", "v8-memory-20.txt", "v8-provenance.json")]
    return [digest(p) for p in paths]

def main():
    before = sources()
    command = [sys.executable, "-B", "-m", "unittest", "-v", "test_check_fixture_export", "test_owned_provider", "test_reanchored_tamper"]
    report = {"schema": "reservoir-reading-measurement-helper-tests-v1", "startedAtUtc": datetime.now(timezone.utc).isoformat(),
              "scope": "Pure temporary-file and mocked-verifier helper tests only. No provider, app, native verifier, model or Being calls.",
              "sourceBefore": before, "command": command}
    with (HERE / "synthetic-harness-tests-01.json").open("x") as receipt:
        began = time.monotonic()
        with (HERE / "synthetic-harness-tests-01.log").open("x") as log:
            result = subprocess.run(command, cwd=HERE, stdout=log, stderr=subprocess.STDOUT)
        raw = (HERE / "synthetic-harness-tests-01.log").read_text()
        count = re.search(r"Ran (\d+) tests?", raw)
        after = sources()
        report.update(endedAtUtc=datetime.now(timezone.utc).isoformat(), elapsedSeconds=time.monotonic()-began,
                      exitCode=result.returncode, testCount=int(count.group(1)) if count else None,
                      log=digest(HERE / "synthetic-harness-tests-01.log"), sourceAfter=after,
                      sourceUnchanged=before == after, status="passed" if result.returncode == 0 and before == after else "failed")
        json.dump(report, receipt, indent=2); receipt.write("\n"); receipt.flush(); os.fsync(receipt.fileno())
    print(json.dumps({"status": report["status"], "testCount": report["testCount"], "sourceUnchanged": report["sourceUnchanged"]}))
    return 0 if report["status"] == "passed" else 1

if __name__ == "__main__":
    raise SystemExit(main())
