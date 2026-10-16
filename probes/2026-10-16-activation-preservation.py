#!/usr/bin/env python3
"""Read-only byte preservation and frozen-source checks; no model/runtime imports.

Only --output is written, with exclusive creation outside either experiment.
Journal contents are hashed as bytes, never decoded or interpreted. This checks
identities and preservation, not numerical replay, model behavior, or process state.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Missing or nonordinary file: {path}")
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def read(path):
    digest(path)
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def relative_path(value):
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise ValueError(f"Invalid manifest-relative path: {value}")
    return path


def inspect(args):
    prior, comparison = args.prior.resolve(strict=True), args.comparison.resolve(strict=True)
    output = args.output.absolute()
    if output.is_relative_to(prior) or output.is_relative_to(comparison):
        raise ValueError("Preservation output must be outside both experiments")
    result = {"schema": "activation-preservation-check/1", "observedAtUtc": datetime.now(timezone.utc).isoformat(),
              "modelCalls": 0, "proseDecoded": False, "experimentFilesModified": False,
              "scriptSha256": digest(Path(__file__)), "priorPilot": str(prior),
              "comparison": str(comparison), "checks": [], "priorFiles": []}

    def check(name, actual, expected):
        result["checks"].append({"name": name, "actual": actual, "expected": expected,
                                  "matches": actual == expected})

    try:
        inventory = read(args.inventory)
        result["priorInventorySha256"] = digest(args.inventory)
        expected = {entry["path"]: entry for entry in inventory}
        check("uniquePriorInventoryPaths", len(expected), len(inventory))
        actual_paths = sorted(str(path.relative_to(prior)) for path in prior.rglob("*")
                              if path.is_file() or path.is_symlink())
        check("exactPriorFileSet", actual_paths, sorted(expected))
        for name, entry in sorted(expected.items()):
            path = prior / relative_path(name)
            actual_hash = digest(path)
            size = path.stat().st_size
            result["priorFiles"].append({"path": name, "bytes": size, "sha256": actual_hash,
                                          "matches": actual_hash == entry["sha256"] and size == entry["bytes"]})
        check("allPriorFilesUnchanged", all(row["matches"] for row in result["priorFiles"]), True)
        result["priorFileCount"] = len(result["priorFiles"])
        result["priorByteCount"] = sum(row["bytes"] for row in result["priorFiles"])

        frozen_path = comparison / "frozen-plan.json"
        frozen = read(frozen_path)
        result["frozenPlanSha256"] = digest(frozen_path)
        app = args.root.resolve(strict=True) / "desktop/ReservoirScope"
        manifest = frozen["modelManifest"]
        check("modelManifestSemanticHash", canonical({k: v for k, v in manifest.items() if k != "sha256"}), manifest["sha256"])
        sources = manifest["workerSources"]
        actual_sources = sorted(path.name for path in (app / "activation_worker").glob("*.py"))
        check("exactWorkerSourceSet", actual_sources, sorted(row["path"] for row in sources))
        for entry in sources:
            check(f"worker/{entry['path']}", digest(app / "activation_worker" / relative_path(entry["path"])), entry["sha256"])
        check("dependencyLock", digest(app / "activation-requirements.lock"), frozen["lockSha256"])
        check("runnerSource", digest(Path(frozen["runnerPath"])), frozen["runnerSha256"])
        check("protocolSource", digest(Path(frozen["protocolPath"])), frozen["protocolSha256"])
        check("frozenBinary", digest(Path(frozen["binary"])), frozen["binarySha256"])
        qualification = Path(frozen["qualificationDirectory"])
        report = read(qualification / "result.json")
        check("qualificationResult", digest(qualification / "result.json"), frozen["qualificationResultSha256"])
        check("qualificationCalibrationFile", digest(qualification / "calibration.json"), report["calibrationFileSha256"])
        check("qualificationCalibrationIdentity", report["calibrationSha256"], frozen["calibrationSha256"])
        for name, path in (("comparison", comparison / "calibration.json"),
                           ("qualification", qualification / "calibration.json")):
            calibration = read(path)
            check(f"{name}CalibrationContentHash", canonical({k: v for k, v in calibration.items() if k != "sha256"}), frozen["calibrationSha256"])
            check(f"{name}CalibrationDeclaredHash", calibration["sha256"], frozen["calibrationSha256"])
            check(f"{name}CalibrationModel", calibration["modelManifestSha256"], manifest["sha256"])
            for key, filename in (("projectionSha256", "projection-q.npy"), ("textsSha256", "calibration-texts.json")):
                check(f"{name}/{filename}", digest(app / "activation_worker/fixtures" / filename), calibration[key])
        result["scope"] = "Exact previous-pilot file set and bytes; current worker Python sources, dependency lock, projection/text fixtures, calibration content, runner, protocol, qualification result and frozen binary. No model asset rehash or loaded-runtime claim."
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["status"] = "passed" if not result.get("error") and all(row["matches"] for row in result["checks"]) else "failed"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return result, digest(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    result, output_hash = inspect(parser.parse_args())
    print(json.dumps({"status": result["status"], "priorFiles": result.get("priorFileCount"),
                      "checks": len(result["checks"]), "outputSha256": output_hash,
                      "modelCalls": 0}))
    raise SystemExit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
