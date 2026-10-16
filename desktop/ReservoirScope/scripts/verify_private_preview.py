#!/usr/bin/env python3
"""Verify one private package's frozen inputs; never launch or modify it."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import plistlib

APP = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def verify(package):
    resources = package / "Contents/Resources"
    info = plistlib.loads((package / "Contents/Info.plist").read_bytes())
    if info["CFBundleShortVersionString"] != "0.27.0":
        raise ValueError("Private preview version differs")
    identities = {}

    def same(relative, source):
        target = resources / relative
        if target.is_symlink() or digest(target) != digest(source):
            raise ValueError(f"Packaged input differs: {relative}")
        identities[relative] = {"bytes": target.stat().st_size, "sha256": digest(target)}

    bundle = resources / "activation_setup_bundle"
    manifest = json.loads((bundle / "setup-manifest.json").read_bytes())
    for relative in ("setup-manifest.json", "activation-wheels.lock", "wheels.json", "model-files.json"):
        same(f"activation_setup_bundle/{relative}", APP / "activation_setup_bundle" / relative)
    for key, path_key, hash_key in (("python", "archivePath", "archiveSha256"), ("uv", "path", "sha256")):
        asset = manifest[key]
        relative = f"activation_setup_bundle/{asset[path_key]}"
        same(relative, APP / relative)
        if identities[relative]["sha256"] != asset[hash_key]:
            raise ValueError(f"Frozen {key} artifact identity differs")
    for locked in manifest["locks"].values():
        if digest(bundle / locked["path"]) != locked["sha256"]:
            raise ValueError("Packaged setup lock differs")
    for directory in ("activation_worker", "activation_setup"):
        for source in sorted((APP / directory).glob("*.py")):
            same(f"{directory}/{source.name}", source)
    for source in sorted((APP / "activation_worker/fixtures").iterdir()):
        if source.is_file():
            same(f"activation_worker/fixtures/{source.name}", source)
    same("activation-requirements.lock", APP / "activation-requirements.lock")
    same("examples/activation-preview-v1.json", APP / "preview-assets/activation-preview-v1.json")
    for source in sorted((APP / "activation_setup_bundle/licenses").rglob("*")):
        if source.is_file():
            relative = source.relative_to(APP).as_posix()
            same(relative, source)
    forbidden = [p.relative_to(resources).as_posix() for p in resources.rglob("*")
                 if p.name in {"__pycache__", ".DS_Store", "uv.tar.gz"} or p.suffix in {".pyc", ".pyo"}]
    if forbidden:
        raise ValueError(f"Unintended package inputs: {forbidden}")
    return {"schema": "activation-private-package-inputs-v1", "passed": True,
            "version": info["CFBundleShortVersionString"], "runtimeId": manifest["runtimeId"],
            "inputs": identities}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.app.resolve(strict=True))
    with args.output.open("x") as output:
        json.dump(report, output, indent=2, sort_keys=True)
        output.write("\n")
    print(json.dumps({"passed": True, "verifiedInputs": len(report["inputs"])}))
