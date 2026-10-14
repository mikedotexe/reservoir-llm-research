"""Offline exploration conformance receipt: Swift fixtures -> Rust, Rust -> Swift.

Executables are explicit; no provider/live sources are accessed. Retained fixture
inputs and local source files are hashed. Generated records and mutations stay in
an owned temporary directory. Missing tools or a timeout are incomplete, not passed.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
    return {"command": [str(value) for value in command], "exitCode": result.returncode,
            "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rust-runner", required=True, type=Path)
    parser.add_argument("--rust-emitter", required=True, type=Path)
    parser.add_argument("--swift-runner", required=True, type=Path)
    args = parser.parse_args()
    crate = Path(__file__).resolve().parents[2]
    repo = crate.parents[3]
    fixtures = crate / "tests/fixtures/exploration"
    receipt = {
        "schema": "reservoir-core-exploration-oracles-v1",
        "createdAtUTC": datetime.now(timezone.utc).isoformat(),
        "scope": "Bounded essentials-exploration-v1 numerical/control verification and verified resume; not full M1 or sustained sessions",
        "platform": platform.platform(), "modelsContacted": False, "liveSourcesRead": False,
        "outcome": "incomplete", "cases": [],
    }
    try:
        rust, emitter, swift = [value.resolve() for value in (args.rust_runner, args.rust_emitter, args.swift_runner)]
        receipt["executables"] = {name: {"path": str(path), "sha256": sha(path)}
                                  for name, path in (("rustVerifier", rust), ("rustEmitter", emitter), ("swiftVerifier", swift))}
        sources = [repo / "essentials" / name for name in (
            "reservoir/ReservoirExploration.swift", "reservoir/Reservoir.swift", "stages/EssentialsSession.swift", "spectral_bridge/SensoryField.swift")]
        sources += [crate / "src/exploration.rs", crate / "src/math.rs", crate / "src/stage.rs", crate / "src/lib.rs",
                    crate / "tests/support/emit_exploration_vectors.swift", crate / "examples/emit_exploration_records.rs"]
        receipt["sources"] = [{"path": str(path.relative_to(repo)), "sha256": sha(path)} for path in sources]
        okay = True
        for fixture in sorted(fixtures.glob("*.json")):
            record = json.loads(fixture.read_text())
            commands = [invoke([swift, "verify", fixture]), invoke([rust, "verify", fixture, "--json"])]
            passed = all(command["exitCode"] == 0 for command in commands)
            receipt["cases"].append({"kind": "retainedSwiftFixture", "path": str(fixture.relative_to(repo)),
                                     "sha256": sha(fixture), "steps": len(record["frames"]),
                                     "seedDecimal": str(record["seed"]), "checks": commands,
                                     "outcome": "passed" if passed else "failed"})
            okay &= passed
        with tempfile.TemporaryDirectory(prefix="reservoir-exploration-oracles-") as directory:
            root = Path(directory)
            generated = invoke([emitter, root])
            receipt["rustGeneration"] = generated
            if generated["exitCode"] != 0:
                receipt["outcome"] = "failed"
            else:
                for path in sorted(root.glob("*.json")):
                    record = json.loads(path.read_text())
                    commands = [invoke([swift, "verify", path]), invoke([rust, "verify", path, "--json"])]
                    passed = all(command["exitCode"] == 0 for command in commands)
                    receipt["cases"].append({"kind": "rustGenerated", "name": path.name, "sha256": sha(path),
                                             "steps": len(record["frames"]), "seedDecimal": str(record["seed"]),
                                             "checks": commands, "outcome": "passed" if passed else "failed"})
                    okay &= passed
                source = json.loads((fixtures / "control-transitions-u64-max.json").read_text())
                for name in ("missing-control", "state", "weight", "retention", "noise", "field-presence", "basis", "negative-eigenvalue", "final-covariance-asymmetry"):
                    changed = deepcopy(source)
                    if name == "missing-control": del changed["frames"][0]["controls"]["leak"]
                    elif name == "state": changed["frames"][0]["state"][0] += 0.1
                    elif name == "weight": changed["model"]["inputWeights"][0] += 0.1
                    elif name == "retention": changed["frames"][1]["controls"]["retention"] = 0.9
                    elif name == "noise": changed["frames"][9]["noise"][0] += 0.1
                    elif name == "field-presence": changed["frames"][1].pop("spectral")
                    elif name == "basis": changed["frames"][1]["spectral"]["eigenvectors"][0] += 0.1
                    elif name == "negative-eigenvalue": changed["frames"][1]["spectral"]["eigenvalues"][31] = -1e-15
                    elif name == "final-covariance-asymmetry": changed["frames"][-1]["spectral"]["covariance"][1] += 1e-8
                    path = root / f"mutated-{name}.json"
                    path.write_text(json.dumps(changed), encoding="utf-8")
                    commands = [invoke([swift, "verify", path]), invoke([rust, "verify", path, "--json"])]
                    passed = all(command["exitCode"] == 1 for command in commands)
                    receipt["cases"].append({"kind": "negativeMutation", "name": name, "sha256": sha(path),
                                             "checks": commands, "outcome": "passed" if passed else "failed"})
                    okay &= passed
                receipt["outcome"] = "passed" if okay else "failed"
    except (OSError, subprocess.TimeoutExpired, ValueError) as error:
        receipt["diagnostic"] = str(error)
    print(json.dumps(receipt, indent=2))
    return {"passed": 0, "failed": 1, "incomplete": 2}[receipt["outcome"]]


if __name__ == "__main__":
    raise SystemExit(main())
