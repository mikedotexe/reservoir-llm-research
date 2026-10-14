#!/usr/bin/env python3
"""Replay preserved owned exports with an explicitly pinned new production CLI.

No service, GUI, restore or numerical continuation command is issued. Historical
bundle bytes must match their earlier retained inventories before and after.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess


def require(condition, message):
    if not condition:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def identity(path, limit=64 * 1024 * 1024):
    require(stat.S_ISREG(path.lstat().st_mode), f"Not an ordinary input: {path}")
    require(path.stat().st_size <= limit, f"Input exceeds bound: {path}")
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def inventory(root):
    require(stat.S_ISDIR(root.lstat().st_mode), f"Not an ordinary bundle: {root}")
    require(root == root.resolve(), f"Bundle has redirected ancestors: {root}")
    files, total, count = {}, 0, 0
    pending = [root]
    while pending:
        directory = pending.pop()
        for member in sorted(directory.iterdir()):
            count += 1
            require(count <= 1100, "Historical bundle exceeds entry bound")
            mode = member.lstat().st_mode
            if stat.S_ISDIR(mode):
                require(len(member.relative_to(root).parts) <= 4, "Unexpected nested bundle")
                pending.append(member)
            else:
                item = identity(member, 4 * 1024 * 1024)
                total += item["bytes"]
                require(total <= 64 * 1024 * 1024, "Historical bundle exceeds byte bound")
                files[str(member.relative_to(root))] = {k: item[k] for k in ("bytes", "sha256")}
    return dict(sorted(files.items()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", required=True, type=Path)
    parser.add_argument("--expected-cli-sha256", required=True)
    parser.add_argument("--cases", type=Path, default=Path(__file__).with_name("historical-replay-cases-01.json"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.cli, args.cases, args.output = (path.absolute() for path in (args.cli, args.cases, args.output))
    require(re.fullmatch(r"[0-9a-f]{64}", args.expected_cli_sha256), "Exact expected executable SHA-256 required")
    case_identity = identity(args.cases)
    selection = json.loads(args.cases.read_bytes())
    require(len(selection["cases"]) == 6, "Expected fixed six-case selection")
    for case in selection["cases"]:
        require(not args.output.is_relative_to(Path(case["bundle"])), "Output cannot modify an inspected bundle")
    receipt = {"schema": "reservoir-historical-production-replay-v1", "startedAtUtc": utc(),
               "script": identity(Path(__file__).absolute()), "selection": case_identity,
               "status": "running", "cases": [], "scope": "Explicit headless verification only; no service, UI, restore or continuation.",
               "v2HistoricalExportCoverage": selection["v2HistoricalExportCoverage"]}
    # Reserve the receipt before the first executable call. A partial or failed
    # run remains visible and cannot be silently overwritten by a second run.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
        try:
            executable = identity(args.cli)
            require(executable["sha256"] == args.expected_cli_sha256, "Pinned executable hash differs")
            receipt["executable"] = executable
            for case in selection["cases"]:
                bundle = Path(case["bundle"])
                require(identity(Path(case["basisReceipt"]["path"])) == case["basisReceipt"], "Historical basis receipt changed")
                before = inventory(bundle)
                require(before == case["expectedInventory"], f"Historical bytes changed: {case['name']}")
                manifest = json.loads((bundle / "manifest.json").read_bytes())
                require(manifest["config"].get("promptVersion", "reservoir-journal-v1") == case["promptVersion"], "Historical version differs")
                require(identity(args.cli) == executable, "Pinned executable changed before case")
                command = [str(args.cli), "--verify-sustained", str(bundle)]
                row = {"name": case["name"], "bundle": str(bundle), "promptVersion": case["promptVersion"],
                       "startedAtUtc": utc(), "command": command, "inventoryBefore": before}
                receipt["cases"].append(row)
                result = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
                row.update({"endedAtUtc": utc(), "exitCode": result.returncode,
                            "stdout": result.stdout, "stderr": result.stderr})
                after = inventory(bundle)
                row["inventoryAfter"] = after
                row["originalUnchanged"] = before == after
                require(row["originalUnchanged"], "Historical bundle changed during replay")
                require(result.returncode == 0, "Historical production replay failed")
                parsed = json.loads(result.stdout)
                row["parsedResult"] = parsed
                require(parsed.get("status") == "passed" and parsed.get("modelsContacted") is False, "Expected model-free verification pass")
                report = parsed["report"]
                require(report["step"] == case["step"] and report["journalCount"] == case["journalCount"], "Historical retained cursor/count differs")
                require(report["manifestSha256"] == before["manifest.json"]["sha256"], "Replay did not bind the selected manifest")
            require(identity(args.cli) == executable, "Pinned executable changed during qualification")
            require(identity(args.cases) == case_identity, "Case selection changed")
            for case in selection["cases"]:
                require(inventory(Path(case["bundle"])) == case["expectedInventory"], "A historical input changed after its case")
            receipt["executableUnchanged"] = True
            receipt["allOriginalsUnchanged"] = True
            receipt["status"] = "passed"
        except Exception as error:
            receipt["status"] = "failed"
            receipt["error"] = f"{type(error).__name__}: {error}"
        receipt["endedAtUtc"] = utc()
        stream.seek(0)
        stream.truncate()
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({"status": receipt["status"], "receipt": identity(args.output)}))
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
