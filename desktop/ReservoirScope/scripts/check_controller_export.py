#!/usr/bin/env python3
"""Independently replay explicit complete controller exports and prefix evidence.

Reads only supplied files, verifier executables and this checkout's source files.
Writes a new receipt and temporary one-ULP projection controls. No canonical record,
app store, provenance path, model service or live system is written or followed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import math
from pathlib import Path
import platform
import subprocess
import tempfile

from check_fresh_conformance import DESKTOP, ROOT, identity

SUPPORT = DESKTOP / "crates/reservoir-core/tests/support/check_regulation_oracles.py"
CURSORS = [0, 300, 301, 450, 599, 600, 450, 301, 300, 900]


def invoke(command: list[Path | str]) -> dict:
    command = [str(value) for value in command]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        return {"command": command, "exitCode": result.returncode,
                "stdout": result.stdout[:262144], "stderr": result.stderr[:16384]}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"command": command, "exitCode": None, "error": str(error)}


def rust_report_matches(result: dict, accepted: bool) -> bool:
    try:
        report = json.loads(result.get("stdout", ""))
    except (ValueError, TypeError):
        return False
    if not isinstance(report, dict):
        return False
    if accepted:
        return (result["exitCode"] == 0 and report.get("status") == "passed"
                and report.get("checkedSteps") == 1200
                and report.get("checkedTurns") == 0
                and report.get("modelsContacted") is False)
    return result["exitCode"] == 1 and report.get("status") == "failed"


def prefix_matches(left: dict, right: dict, equal_windows) -> bool:
    if left["exitCode"] != 0 or right["exitCode"] != 0:
        return False
    try:
        a, b = json.loads(left["stdout"]), json.loads(right["stdout"])
        # Equality alone would let two empty or truncated helper outputs pass.
        return ([row["cursor"] for row in a] == CURSORS
                and [row["cursor"] for row in b] == CURSORS
                and equal_windows(a, b))
    except (ValueError, TypeError, KeyError, AttributeError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("swift", "swift-window", "rust", "rust-helper", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("records", nargs="+", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("Receipt exists; select a new output path.")
    executables = [args.swift, args.swift_window, args.rust, args.rust_helper]
    supplied = [*executables, *args.records]
    for path in supplied:
        if path.is_symlink() or not path.is_file():
            parser.error(f"Expected an explicit regular file: {path}")
    receipt = {
        "schema": "reservoir-scope.controller-export-conformance.v1",
        "executedAtUtc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "outcome": "incomplete", "passed": False,
        "modelsContacted": False, "historicalPathsRead": False,
        "scope": "Complete essentials-regulation-v1 exports: 600 paired/1200 arm observations, zero language turns, one exact-projection negative control per input, and native versus Rust prefix/rewind evidence",
        "countConvention": "The unchanged Swift CLI prints 600 paired controller steps; RegulationExample.verify returns checkedSteps=frames.count*2 and checkedTurns=0. Rust's JSON report must explicitly return 1200 and 0.",
        "limits": "Numerical and prefix compatibility only. This check does not authenticate app storage, UI actions, crash recovery, platform support or scientific benefit. A one-ULP projection rejection is one bounded mutation, not exhaustive corruption coverage.",
        "checks": [],
    }
    tracked: list[Path] = []
    before: list[dict] = []
    try:
        sources = [Path(__file__).resolve(), Path(__file__).with_name("check_fresh_conformance.py"),
                   SUPPORT, SUPPORT.with_name("regulation_window_oracle.swift"),
                   DESKTOP / "crates/reservoir-core/examples/emit_regulation_record.rs",
                   DESKTOP / "crates/reservoir-core/examples/regulation_session_fixtures.rs",
                   ROOT / "native/ReservoirScope/Sources/ReservoirScope/GuidedLessons.swift",
                   *sorted((ROOT / "essentials").glob("*/*.swift")),
                   *sorted((DESKTOP / "crates/reservoir-core/src").glob("*.rs"))]
        tracked = [*supplied, *sources]
        before = [identity(path) for path in tracked]
        receipt["executables"] = dict(zip(
            ("swiftVerifier", "nativePrefixOracle", "rustVerifier", "rustPrefixHelper"), before[:4]))
        receipt["inputs"] = before[4:len(supplied)]
        receipt["sources"] = before[len(supplied):]
        spec = importlib.util.spec_from_file_location("controller_window_comparison", SUPPORT)
        if spec is None or spec.loader is None:
            raise ValueError("Cannot load the existing bounded prefix comparison")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        swift, window, rust, helper = (path.resolve() for path in executables)
        incomplete = False
        with tempfile.TemporaryDirectory(prefix="scope-controller-export-controls-") as temporary:
            for index, path in enumerate(args.records):
                data = path.read_bytes()
                record = json.loads(data)
                if not isinstance(record, dict) or record.get("format") != "essentials-regulation-v1":
                    raise ValueError(f"Expected an explicit controller record: {path}")
                original = {"swift": invoke([swift, "verify", path.resolve()]),
                            "rust": invoke([rust, "verify", path.resolve(), "--json"])}
                original_passed = (
                    original["swift"]["exitCode"] == 0
                    and original["swift"].get("stdout", "").startswith("Verified 600 paired controller steps,")
                    and rust_report_matches(original["rust"], True))
                old_weight = record["projectionWeights"][0]
                if not isinstance(old_weight, (int, float)) or not math.isfinite(old_weight):
                    raise ValueError("Projection mutation requires a finite original weight")
                new_weight = math.nextafter(old_weight, math.inf)
                record["projectionWeights"][0] = new_weight
                control = Path(temporary) / f"{index}-projection-one-ulp.json"
                control.write_text(json.dumps(record, ensure_ascii=False, allow_nan=False,
                                               separators=(",", ":")), encoding="utf-8")
                negative = {"swift": invoke([swift, "verify", control]),
                            "rust": invoke([rust, "verify", control, "--json"])}
                negative_passed = negative["swift"]["exitCode"] == 1 and rust_report_matches(negative["rust"], False)
                prefix = {"swift": invoke([window, path.resolve()]),
                          "rust": invoke([helper, "windows", path.resolve()])}
                prefix_passed = prefix_matches(prefix["swift"], prefix["rust"], module.equal_windows)
                unchanged = path.read_bytes() == data
                incomplete |= any(result["exitCode"] is None for group in (original, negative, prefix) for result in group.values())
                row = {"input": before[4 + index], "original": original,
                       "originalAcceptedByBoth": original_passed,
                       "negativeControl": {"mutation": "projection-one-ulp", "index": 0,
                                           "beforeHex": float(old_weight).hex(), "afterHex": new_weight.hex(),
                                           "input": identity(control), "checks": negative,
                                           "rejectedByBoth": negative_passed},
                       "prefixEvidence": {"cursorSequence": CURSORS, "checks": prefix,
                                          "matchesNative": prefix_passed},
                       "originalBytesUnchanged": unchanged,
                       "passed": original_passed and negative_passed and prefix_passed and unchanged}
                receipt["checks"].append(row)
                print(f"{path.name}: {'passed' if row['passed'] else 'not passed'}", flush=True)
        receipt["outcome"] = "incomplete" if incomplete else (
            "passed" if all(row["passed"] for row in receipt["checks"]) else "failed")
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        receipt["diagnostic"] = str(error)
    finally:
        try:
            after = [identity(path) for path in tracked]
            receipt["inputsExecutablesAndSourcesStable"] = bool(before) and before == after
            if not receipt["inputsExecutablesAndSourcesStable"]:
                receipt["outcome"] = "failed"
        except OSError as error:
            receipt["inputsExecutablesAndSourcesStable"] = False
            receipt["stabilityDiagnostic"] = str(error)
            receipt["outcome"] = "incomplete"
    receipt["passed"] = receipt["outcome"] == "passed"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"outcome": receipt["outcome"], "records": len(receipt["checks"]),
                      "receipt": str(args.output)}))
    return {"passed": 0, "failed": 1, "incomplete": 2}[receipt["outcome"]]


if __name__ == "__main__":
    raise SystemExit(main())
