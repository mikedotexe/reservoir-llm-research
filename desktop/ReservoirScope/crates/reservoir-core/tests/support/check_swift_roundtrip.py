"""Independent offline Rust -> Swift stage check. No models or live sources.

Both executable paths are explicit. Missing tools are incomplete, never passing.
All generated files live in an owned temporary directory and are removed after
the receipt is constructed. Redirect stdout to retain the qualification receipt.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rust-runner", type=Path, required=True)
    parser.add_argument("--swift-runner", type=Path, required=True)
    args = parser.parse_args()
    receipt = {
        "schema": "reservoir-core-swift-roundtrip-v1",
        "createdAtUTC": datetime.now(timezone.utc).isoformat(),
        "scope": "Rust-generated essentials-v1 stages verified by explicit Swift runner",
        "platform": platform.platform(),
        "modelsContacted": False,
        "liveSourcesRead": False,
        "outcome": "incomplete",
        "cases": [],
    }
    try:
        rust, swift = args.rust_runner.resolve(), args.swift_runner.resolve()
        receipt["executables"] = {
            label: {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for label, path in (("rust", rust), ("swift", swift))
        }
        with tempfile.TemporaryDirectory(prefix="reservoir-core-roundtrip-") as directory:
            root = Path(directory)
            for stage in range(1, 5):
                recipe = {"stage": stage, "seed": 18446744073709551615, "steps": 61,
                          "turnEvery": 15, "noiseAmplitude": 0.01}
                config, run = root / f"stage-{stage}.recipe.json", root / f"stage-{stage}.json"
                config.write_text(json.dumps(recipe), encoding="utf-8")
                generated = subprocess.run([str(rust), "run", "--config", str(config), "--output", str(run)],
                                           capture_output=True, text=True, timeout=60, check=False)
                case = {"stage": stage, "seedDecimal": str(recipe["seed"]),
                        "steps": recipe["steps"], "rustExitCode": generated.returncode}
                receipt["cases"].append(case)
                if generated.returncode:
                    case["diagnostic"] = generated.stderr
                    receipt["outcome"] = "failed"
                    break
                case["recordSha256"] = hashlib.sha256(run.read_bytes()).hexdigest()
                verified = subprocess.run([str(swift), "verify", str(run)], capture_output=True,
                                          text=True, timeout=60, check=False)
                case.update(swiftExitCode=verified.returncode, swiftOutput=verified.stdout.strip(),
                            diagnostic=verified.stderr.strip())
                if verified.returncode:
                    receipt["outcome"] = "failed"
                    break
            else:
                receipt["outcome"] = "passed"
    except (OSError, subprocess.TimeoutExpired) as error:
        receipt["diagnostic"] = str(error)
    print(json.dumps(receipt, indent=2))
    return {"passed": 0, "failed": 1, "incomplete": 2}[receipt["outcome"]]


if __name__ == "__main__":
    raise SystemExit(main())
