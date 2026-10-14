#!/usr/bin/env python3
"""Verify explicitly supplied fresh records with independent Swift and Rust CLIs.

No generation, model calls, historical-path reads or native-source edits occur here.
Both verifiers replay each original and a temporary changed-weight negative control.
The receipt preserves failures and refuses an existing output path.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
DESKTOP = ROOT / "desktop/ReservoirScope"


def identity(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def execute(binary: Path, record: Path, rust: bool) -> dict:
    command = [str(binary.resolve()), "verify", str(record.resolve())]
    if rust:
        command.append("--json")
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        return {"command": command, "exitCode": result.returncode,
                "stdout": result.stdout[:16384], "stderr": result.stderr[:16384]}
    except subprocess.TimeoutExpired:
        return {"command": command, "exitCode": None, "error": "120-second deadline exceeded"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--swift", type=Path, required=True)
    parser.add_argument("--rust", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("records", nargs="+", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Receipt exists; choose a new output path.")
    inputs = [args.swift, args.rust, *args.records]
    for path in inputs:
        if path.is_symlink() or not path.is_file():
            raise SystemExit(f"Expected an explicit regular file: {path}")
    before = [identity(path) for path in inputs]
    checks = []
    with tempfile.TemporaryDirectory(prefix="scope-fresh-negative-") as temporary:
        for index, path in enumerate(args.records):
            data = path.read_bytes()
            record = json.loads(data)
            family = record.get("format", record.get("recipeVersion"))
            original = {"swift": execute(args.swift, path, False),
                        "rust": execute(args.rust, path, True)}
            model = record.get("model")
            if model is None:
                model = record["right"]["model"]
            model["inputWeights"][0] += 0.125
            mutated = Path(temporary) / f"changed-seeded-weight-{index}.json"
            mutated.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            negative = {"swift": execute(args.swift, mutated, False),
                        "rust": execute(args.rust, mutated, True)}
            row = {"record": identity(path), "family": family,
                   "original": original, "negativeChangedSeededWeight": negative,
                   "originalBytesUnchanged": path.read_bytes() == data}
            row["passed"] = (row["originalBytesUnchanged"]
                             and all(x["exitCode"] == 0 for x in original.values())
                             and all(x["exitCode"] == 1 for x in negative.values()))
            checks.append(row)
    stable = before == [identity(path) for path in inputs]
    native_sources = sorted((ROOT / "essentials").glob("*/*.swift"))
    rust_sources = sorted((DESKTOP / "crates/reservoir-core/src").glob("*.rs"))
    receipt = {"schema": "reservoir-scope.fresh-record-conformance.v1",
               "executedAtUtc": datetime.now(timezone.utc).isoformat(),
               "purpose": "Independent replay of explicitly supplied fresh records and changed-weight controls",
               "inputsStable": stable, "executables": before[:2],
               "sources": [identity(p) for p in [Path(__file__).resolve(), *native_sources, *rust_sources]],
               "modelsContacted": False, "historicalPathsRead": False,
               "checks": checks, "passed": stable and all(c["passed"] for c in checks),
               "limits": "CLI numerical/text compatibility only. Save receipts in portable records do not authenticate storage. Native dialogs, pending-save lifecycle, packaged behavior and human acceptance require separate checks."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"passed": receipt["passed"], "records": len(checks),
                      "negativeControls": len(checks), "receipt": str(args.output)}))
    if not receipt["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
