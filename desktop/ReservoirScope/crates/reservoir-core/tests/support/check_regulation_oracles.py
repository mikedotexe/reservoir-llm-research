"""Offline controller conformance against freshly built Swift and native prefix evidence.

Only tracked synthetic fixtures and locally generated temporary records are read.
No model calls, live sources, embedded paths or writable application stores are used.
Missing tools/timeouts are incomplete, not successful qualification.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(command):
    command = [str(v) for v in command]
    result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=60)
    return {"command": command, "exitCode": result.returncode,
            "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def equal_windows(a, b):
    if len(a) != len(b):
        return False
    for left, right in zip(a, b):
        if left["cursor"] != right["cursor"]:
            return False
        x, y = left["evidence"], right["evidence"]
        if x is None or y is None:
            if x != y:
                return False
            continue
        if x.keys() != y.keys():
            return False
        for key in x:
            if key.endswith("MeanAbsoluteError"):
                if not math.isclose(x[key], y[key], abs_tol=1e-12, rel_tol=1e-12):
                    return False
            elif x[key] != y[key]:
                return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("swift-runner", "swift-window-oracle", "rust-runner", "rust-helper", "receipt"):
        parser.add_argument("--" + key, required=True, type=Path)
    args = parser.parse_args()
    crate = Path(__file__).resolve().parents[2]
    repo = crate.parents[3]
    fixture = repo / "essentials/examples/portable/example-regulation-controller.json"
    receipt = {"schema": "reservoir-core-regulation-oracles-v1", "createdAtUTC": datetime.now(timezone.utc).isoformat(),
               "scope": "Fixed essentials-regulation-v1 numerical replay, 600 paired field observations and native cursor-prefix target-error evidence; not sustained regulation or live-system evidence",
               "platform": platform.platform(), "modelsContacted": False, "liveSourcesRead": False,
               "outcome": "incomplete", "cases": []}
    try:
        swift, window, rust, helper = [p.resolve() for p in (args.swift_runner, args.swift_window_oracle, args.rust_runner, args.rust_helper)]
        receipt["executables"] = {name: {"path": str(path), "sha256": sha(path)} for name, path in
                                  (("swiftVerifier", swift), ("nativePrefixOracle", window), ("rustVerifier", rust), ("rustHelper", helper))}
        sources = [repo / "essentials" / name for name in (
            "regulation/RegulationExample.swift", "regulation/Regulation.swift", "spectral_bridge/SensoryField.swift", "actions/ActionVerification.swift", "runner/Main.swift")]
        sources += [repo / "native/ReservoirScope/Sources/ReservoirScope/GuidedLessons.swift", crate / "src/regulation.rs", crate / "src/math.rs", crate / "src/stage.rs", crate / "src/lib.rs", Path(__file__), crate / "tests/support/regulation_window_oracle.swift", crate / "examples/emit_regulation_record.rs"]
        receipt["sources"] = [{"path": str(p.relative_to(repo)), "sha256": sha(p)} for p in sources]
        receipt["fixture"] = {"path": str(fixture.relative_to(repo)), "sha256": sha(fixture), "bytes": fixture.stat().st_size}
        okay = True

        def check(name, path, accepted):
            nonlocal okay
            commands = [invoke([swift, "verify", path]), invoke([rust, "verify", path, "--json"])]
            rust_report = json.loads(commands[1]["stdout"])
            passed = all(c["exitCode"] == (0 if accepted else 1) for c in commands)
            passed &= rust_report.get("status") == ("passed" if accepted else "failed")
            if accepted:
                passed &= rust_report.get("checkedSteps") == 1200 and rust_report.get("checkedTurns") == 0 and not rust_report.get("modelsContacted")
            receipt["cases"].append({"name": name, "expected": "accepted" if accepted else "rejected", "sha256": sha(path), "checks": commands, "outcome": "passed" if passed else "failed"})
            okay &= passed
            print(f'{name}: {"passed" if passed else "failed"}', flush=True)

        check("retained-swift-controller", fixture, True)
        with tempfile.TemporaryDirectory(prefix="reservoir-regulation-oracles-") as directory:
            root = Path(directory)
            generated = root / "rust-generated.json"
            receipt["rustGeneration"] = invoke([helper, "generate", generated])
            if receipt["rustGeneration"]["exitCode"] != 0:
                raise ValueError("Rust controller generation failed")
            check("rust-generated-controller", generated, True)
            source = json.loads(fixture.read_text())
            for name in ("defaults-and-inert-path", "null-specification-fields", "clock-within-tolerance", "spectral-within-native-tolerance", "projection-one-ulp", "changed-common-input", "clock-outside-tolerance", "next-retention-outside-tolerance", "same-step-retention", "control-integral", "basis-corruption", "wrong-summary", "partial-record", "wrong-qualified-seed"):
                changed = deepcopy(source)
                accepted = name in ("defaults-and-inert-path", "null-specification-fields", "clock-within-tolerance", "spectral-within-native-tolerance")
                if name == "defaults-and-inert-path":
                    changed["specification"] = {}
                    changed["untrustedHistoricalPath"] = r"C:\missing\other-app\journal\never-open.json"
                elif name == "null-specification-fields":
                    changed["specification"] = {k: None for k in changed["specification"]}
                elif name == "clock-within-tolerance": changed["frames"][0]["time"] += 5e-9
                elif name == "spectral-within-native-tolerance": changed["frames"][0]["baseline"]["spectral"]["fieldVector"][0] += 5e-8
                elif name == "projection-one-ulp": changed["projectionWeights"][0] = math.nextafter(changed["projectionWeights"][0], math.inf)
                elif name == "changed-common-input": changed["frames"][0]["input"][0] += 0.001
                elif name == "clock-outside-tolerance": changed["frames"][0]["time"] += 5e-8
                elif name == "next-retention-outside-tolerance": changed["frames"][0]["regulated"]["control"]["appliedRetention"] += 5e-8
                elif name == "same-step-retention": changed["frames"][0]["regulated"]["retentionUsed"] = changed["frames"][0]["regulated"]["control"]["appliedRetention"]
                elif name == "control-integral": changed["frames"][0]["regulated"]["control"]["integral"] += 0.01
                elif name == "basis-corruption": changed["frames"][0]["regulated"]["spectral"]["eigenvectors"][0] += 0.01
                elif name == "wrong-summary": changed["summary"]["regulatedMeanAbsoluteError"] += 0.01
                elif name == "partial-record": changed["frames"].pop()
                elif name == "wrong-qualified-seed": changed["specification"]["inputSeed"] = 18446744073709551615
                path = root / "mutation.json"
                path.write_text(json.dumps(changed, ensure_ascii=False, allow_nan=False, separators=(",", ":")), encoding="utf-8")
                check(name, path, accepted)
                del changed
            for name, path in (("retained-prefix-and-rewind", fixture), ("rust-generated-prefix-and-rewind", generated)):
                commands = [invoke([window, path]), invoke([helper, "windows", path])]
                passed = all(c["exitCode"] == 0 for c in commands)
                passed &= equal_windows(json.loads(commands[0]["stdout"]), json.loads(commands[1]["stdout"]))
                receipt["cases"].append({"name": name, "cursorSequence": [0,300,301,450,599,600,450,301,300,900], "checks": commands, "outcome": "passed" if passed else "failed"})
                okay &= passed
                print(f'{name}: {"passed" if passed else "failed"}', flush=True)
        receipt["outcome"] = "passed" if okay else "failed"
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError) as error:
        receipt["diagnostic"] = str(error)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"outcome": receipt["outcome"], "cases": len(receipt["cases"]), "receipt": str(args.receipt)}))
    return {"passed": 0, "failed": 1, "incomplete": 2}[receipt["outcome"]]

if __name__ == "__main__":
    raise SystemExit(main())
