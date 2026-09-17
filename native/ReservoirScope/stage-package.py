#!/usr/bin/env python3
"""Stage one coherent research package and verify every declared resource."""
import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile

NATIVE = pathlib.Path("native/ReservoirScope")
COMPONENTS = ("reservoir", "spectral_bridge", "llm", "regulation", "stages", "actions", "runner")
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def safe_relative(value):
    path = pathlib.PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError("Invalid relative input path: " + value)
    return pathlib.Path(*path.parts)
def load_resources(repo, selected=None):
    path = repo / NATIVE / "resource-manifest.json"
    manifest = json.loads(path.read_text())
    if manifest["schema"] != "reservoir-scope.resources.v1":
        raise ValueError("Unsupported resource manifest")
    names = set()
    for item in manifest["resources"]:
        name = item["name"]
        if pathlib.PurePosixPath(name).name != name or name in ("", ".", "..", "release-identity.json", "resource-manifest.json") or name in names:
            raise ValueError("Invalid or duplicate resource name: " + name)
        names.add(name)
        source = repo / safe_relative(item["source"])
        if selected is not None and name not in selected: continue
        if source.is_symlink() or not source.is_file() or not source.resolve().is_relative_to(repo.resolve()):
            raise ValueError("Missing or nonlocal canonical resource: " + str(source))
        if sha(source) != item["sha256"]:
            raise ValueError("Canonical resource differs from frozen manifest: " + item["source"])
    if selected is not None and not set(selected).issubset(names): raise ValueError("Unknown selected resource")
    return manifest
def resources(repo, destination, selected=None):
    manifest = load_resources(repo, selected)
    items = [item for item in manifest["resources"] if selected is None or item["name"] in selected]
    if destination.resolve() == (repo / NATIVE / "Sources/ReservoirScope/Resources").resolve():
        raise ValueError("Resource staging never writes into the canonical source Resources directory")
    destination.mkdir(parents=True, exist_ok=True)
    expected = {item["name"] for item in items} | {"resource-manifest.json"}
    for current in destination.iterdir():
        if current.name not in expected:
            if current.is_dir(): shutil.rmtree(current)
            else: current.unlink()
    for item in items:
        shutil.copy2(repo / safe_relative(item["source"]), destination / item["name"])
    shutil.copy2(repo / NATIVE / "resource-manifest.json", destination / "resource-manifest.json")
    return {path.name: sha(path) for path in sorted(destination.iterdir()) if path.is_file()}
def source_paths(repo):
    native = repo / NATIVE
    result = list((native / "Sources/ReservoirScope").glob("*.swift"))
    result += [path for path in (native / "Tests").glob("*") if path.suffix in (".swift", ".py")]
    result += list(native.glob("*.sh")) + list(native.glob("*.py"))
    result += [native / "Package.swift", native / "resource-manifest.json"]
    essentials = repo / "essentials"
    result += [essentials / "Package.swift", essentials / "build.sh"]
    for component in COMPONENTS + ("tests",):
        result += [path for path in (essentials / component).rglob("*")
                   if path.is_file() and path.suffix in (".swift", ".py", ".sh", ".json", ".md") and "__pycache__" not in path.parts]
    for name in ("README.md", "EXPLORE.md", "ACTIONS.md", "check.sh"):
        if (essentials / name).is_file(): result.append(essentials / name)
    return sorted(set(result))
def toolchain():
    def output(*args): return subprocess.check_output(args, text=True).strip()
    return {"swift": output("xcrun", "swiftc", "--version"),
            "sdk_path": output("xcrun", "--show-sdk-path"),
            "sdk_version": output("xcrun", "--show-sdk-version"),
            "architecture": output("uname", "-m")}
def stage(repo, destination):
    if destination.resolve() == repo.resolve() or repo.resolve().is_relative_to(destination.resolve()):
        raise ValueError("The staged repository must not replace the source repository or its parent")
    manifest = load_resources(repo)
    paths = source_paths(repo)
    before = {str(path.relative_to(repo)): sha(path) for path in paths}
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="reservoir-stage-", dir=destination.parent) as directory:
        fresh = pathlib.Path(directory)
        for relative in before:
            target = fresh / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo / relative, target)
        for name in ("examples",):
            (fresh / "essentials" / name).mkdir(parents=True, exist_ok=True)
        resource_hashes = resources(repo, fresh / NATIVE / "Sources/ReservoirScope/Resources")
        after = {str(path.relative_to(repo)): sha(path) for path in source_paths(repo)}
        if before != after: raise ValueError("Source inputs changed during staging")
        for relative, digest in before.items():
            if sha(fresh / relative) != digest: raise ValueError("Staged copy differs: " + relative)
        # Replace only owned staged source trees; unrelated cache outputs survive.
        for relative in (NATIVE, pathlib.Path("essentials")):
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists(): shutil.rmtree(target)
            shutil.move(str(fresh / relative), target)
    receipt = {"schema": "reservoir-scope.staged-inputs.v1",
               "source_commit": subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip(),
               "files": before, "resource_sha256": resource_hashes,
               "toolchain": toolchain(), "release": manifest["release"]}
    (destination / "staged-inputs.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    verify_stage(destination)
    return receipt
def verify_stage(destination):
    receipt = json.loads((destination / "staged-inputs.json").read_text())
    if receipt["schema"] != "reservoir-scope.staged-inputs.v1": raise ValueError("Unsupported staged identity")
    actual = {str(path.relative_to(destination)): sha(path) for path in source_paths(destination)}
    if actual != receipt["files"]: raise ValueError("Staged source input drift or omission")
    resource_dir = destination / NATIVE / "Sources/ReservoirScope/Resources"
    actual_resources = {path.name: sha(path) for path in resource_dir.iterdir() if path.is_file()}
    if any(path.is_dir() or path.is_symlink() for path in resource_dir.iterdir()):
        raise ValueError("Unexpected staged resource directory or link")
    if actual_resources != receipt["resource_sha256"]: raise ValueError("Staged resource drift or omission")
    manifest = json.loads((destination / NATIVE / "resource-manifest.json").read_text())
    expected_names = {item["name"] for item in manifest["resources"]} | {"resource-manifest.json"}
    if set(actual_resources) != expected_names: raise ValueError("Staged resources do not match the declared manifest")
    for item in manifest["resources"]:
        if actual_resources[item["name"]] != item["sha256"]: raise ValueError("Staged resource differs from manifest")
    return receipt
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("stage", "resources", "verify-stage"))
    parser.add_argument("--repo", type=pathlib.Path)
    parser.add_argument("--destination", type=pathlib.Path, required=True)
    parser.add_argument("--names", nargs="*")
    args = parser.parse_args()
    if args.operation == "verify-stage":
        result = verify_stage(args.destination)
    else:
        if args.repo is None: parser.error("--repo is required")
        result = stage(args.repo, args.destination) if args.operation == "stage" else resources(args.repo, args.destination, args.names)
    print(json.dumps({"status": "verified", "operation": args.operation, "destination": str(args.destination),
                      "files": len(result.get("files", result))}, sort_keys=True))
if __name__ == "__main__": main()
