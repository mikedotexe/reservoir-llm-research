#!/usr/bin/env python3
"""Stage verified M0 resources in the Tauri build directory, never canonical inputs."""
import argparse
import json
from pathlib import Path
from reference_support import ROOT, REFERENCE, FIXTURES, STAGED_NAMES, read_local, sha256, verify


def stage(root: Path = ROOT) -> dict:
    manifest = verify(root)
    destination = root / "desktop/ReservoirScope/src-tauri/resources"
    # No arbitrary destination parameter: the only write surface is this generated directory.
    owned_parents = [p for p in [destination, *destination.parents] if p == root or root in p.parents]
    if not destination.resolve().is_relative_to(root.resolve()) or any(p.is_symlink() for p in owned_parents):
        raise ValueError("Staging directory must not contain symlink parents")
    payloads = {"reference-manifest.json": read_local(root, REFERENCE.as_posix()),
                "reference-scenes.json": read_local(root, FIXTURES.as_posix())}
    original_entries = []
    for item in manifest["resources"]:
        if item["name"] in STAGED_NAMES:
            data = read_local(root, item["path"])
            if sha256(data) != item["sha256"] or len(data) != item["bytes"]:
                raise ValueError(f"Canonical input changed during staging: {item['path']}")
            payloads[item["name"]] = data
            original_entries.append({"name": item["name"], "source": item["path"],
                                     "sha256": item["sha256"], "bytes": item["bytes"]})
    if {item["name"] for item in original_entries} != set(STAGED_NAMES):
        raise ValueError("Incomplete canonical staging selection")
    fixture_identity = next(item for item in manifest["fixtures"] if item["path"] == FIXTURES.as_posix())
    if sha256(payloads["reference-scenes.json"]) != fixture_identity["sha256"] or json.loads(payloads["reference-manifest.json"]) != manifest:
        raise ValueError("Reference inputs changed during staging")
    index = {"schema": "reservoir-scope.resource-index.v1", "baselineCommit": manifest["baseline"]["commit"],
             "resources": original_entries, "referenceManifestSha256": sha256(payloads["reference-manifest.json"]),
             "referenceScenesSha256": sha256(payloads["reference-scenes.json"])}
    payloads["resource-index.json"] = (json.dumps(index, indent=2, sort_keys=True) + "\n").encode()
    destination.mkdir(parents=True, exist_ok=True)
    # Refuse unexpected directories/links and avoid recursively deleting any caller-owned tree.
    for path in destination.iterdir():
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Unexpected non-file in resource stage: {path.name}")
    for path in destination.iterdir():
        if path.name not in payloads:
            path.unlink()
    for name, data in payloads.items():
        (destination / name).write_bytes(data)
        if (destination / name).read_bytes() != data:
            raise ValueError(f"Staged resource differs: {name}")
    return {"status": "verified", "destination": str(destination), "files": len(payloads),
            "baselineCommit": manifest["baseline"]["commit"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        print(json.dumps(stage(args.repo), sort_keys=True))
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Resource staging failed: {error}\n")


if __name__ == "__main__":
    main()
