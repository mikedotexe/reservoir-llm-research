#!/usr/bin/env python3
"""Bind a packaged app to frozen staged inputs; verify copies without source access."""
import argparse
import datetime
import hashlib
import json
import pathlib
import plistlib
import subprocess

NATIVE = pathlib.Path("native/ReservoirScope")
COMPONENTS = ("reservoir", "spectral_bridge", "llm", "regulation", "stages", "actions", "runner")
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def safe(value):
    path = pathlib.PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts): raise ValueError("Invalid identity path")
    return pathlib.Path(*path.parts)
def source_paths(root):
    native = root / NATIVE
    result = list((native / "Sources/ReservoirScope").glob("*.swift")) + [path for path in (native / "Tests").glob("*") if path.suffix in (".swift", ".py")]
    result += [path for path in (native / "Tests/Fixtures/geometry-bookmarks").glob("*")
               if path.is_file() and path.suffix in (".py", ".json", ".md")]
    result += list(native.glob("*.sh")) + list(native.glob("*.py"))
    result += [native / "Package.swift", native / "resource-manifest.json"]
    core = root / "essentials"
    result += [core / "Package.swift", core / "build.sh"]
    for component in COMPONENTS + ("tests",):
        result += [path for path in (core / component).rglob("*") if path.is_file()
                   and path.suffix in (".swift", ".py", ".sh", ".json", ".md") and "__pycache__" not in path.parts]
    for name in ("README.md", "EXPLORE.md", "ACTIONS.md", "check.sh"):
        if (core / name).is_file(): result.append(core / name)
    return sorted(set(result))
def stage_receipt(root):
    receipt = json.loads((root / "staged-inputs.json").read_text())
    if receipt["schema"] != "reservoir-scope.staged-inputs.v1": raise ValueError("Unsupported staged inputs")
    current = {str(path.relative_to(root)): sha(path) for path in source_paths(root)}
    if current != receipt["files"]: raise ValueError("Staged source drift, omission or extra input")
    directory = root / NATIVE / "Sources/ReservoirScope/Resources"
    if any(not path.is_file() or path.is_symlink() for path in directory.iterdir()): raise ValueError("Invalid staged resource")
    current_resources = {path.name: sha(path) for path in directory.iterdir()}
    if current_resources != receipt["resource_sha256"]: raise ValueError("Staged resource drift or omission")
    return receipt
def toolchain():
    def output(*args): return subprocess.check_output(args, text=True).strip()
    return {"swift":output("xcrun","swiftc","--version"), "sdk_path":output("xcrun","--show-sdk-path"),
            "sdk_version":output("xcrun","--show-sdk-version"), "architecture":output("uname","-m")}
def validate_catalogs(resources, sealed, require_cases):
    catalog = json.loads((resources / "examples-index.json").read_text())
    if len(catalog) < 15: raise ValueError("Required portable examples are missing")
    for item in catalog:
        if item["file"] not in sealed: raise ValueError("Unsealed example")
        if item.get("group") not in ("guided","model","comparison","preparation"): raise ValueError("Unknown example group")
    lessons = json.loads((resources / "guided-lessons.json").read_text())
    if lessons["format"] != "reservoir-guided-lessons-v1" or sorted(x["stage"] for x in lessons["lessons"]) != list(range(1,9)):
        raise ValueError("Invalid guided route")
    for lesson in lessons["lessons"]:
        for key in ("scriptedFile","modelFile"):
            if lesson.get(key) and lesson[key] not in sealed: raise ValueError("Unsealed guided recording")
        points = lesson["checkpoints"]
        if not points or points != sorted(set(points)) or not all(1 <= step <= 120 for step in points):
            raise ValueError("Invalid lesson checkpoints")
    required = {"example-observation-active-scripted.json", "example-regulation-controller.json",
                "guided-observation-recording.json", "guided-observation-amendment.json"}
    if not required.issubset(sealed): raise ValueError("Required teaching evidence missing")
    case_count = 0
    if require_cases:
        cases = json.loads((resources / "research-cases-v1.json").read_text())
        if cases["format"] != "research-cases-v1" or not cases["cases"]: raise ValueError("Missing reviewed cases")
        for case in cases["cases"]:
            material = {item["id"]:item for item in case["materials"]}
            if len(material) != len(case["materials"]) or not case["limits"]: raise ValueError("Invalid case evidence or limits")
            for item in material.values():
                if hashlib.sha256(item["content"].encode()).hexdigest() != item["sha256"]: raise ValueError("Case material hash mismatch")
            for claim in case["claims"]:
                if not claim["quote"] or material[claim["materialID"]]["content"].count(claim["quote"]) != 1:
                    raise ValueError("Case quotation mismatch")
                if not claim["evidenceIDs"] or any(key not in material for key in claim["evidenceIDs"]):
                    raise ValueError("Case evidence reference missing")
        case_count = len(cases["cases"])
    return len(catalog), case_count
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("create","verify"))
    parser.add_argument("--app", type=pathlib.Path, required=True)
    parser.add_argument("--repo", type=pathlib.Path)
    parser.add_argument("--stage", type=pathlib.Path)
    parser.add_argument("--core-cache", type=pathlib.Path)
    parser.add_argument("--expected-staged-sha256")
    parser.add_argument("--expected-core-sha256")
    args = parser.parse_args()
    resources = args.app / "Contents/Resources"
    target = resources / "release-identity.json"
    plist = plistlib.loads((args.app / "Contents/Info.plist").read_bytes())
    if args.operation == "create":
        if args.repo is None or args.stage is None or args.core_cache is None or not args.expected_staged_sha256 or not args.expected_core_sha256:
            parser.error("create requires --repo, --stage, --core-cache and the initially captured staged/core SHA-256 values")
        if sha(args.stage / "staged-inputs.json") != args.expected_staged_sha256: raise ValueError("Initial staged receipt identity changed")
        if sha(args.core_cache / "lib/libEssentialsCore.a") != args.expected_core_sha256: raise ValueError("Core archive changed after the pre-link identity capture")
        receipt = stage_receipt(args.stage)
        canonical = {str(path.relative_to(args.repo)): sha(path) for path in source_paths(args.repo)}
        if canonical != receipt["files"]: raise ValueError("Canonical input drift, omission or extra input after staging")
        if toolchain() != receipt["toolchain"]: raise ValueError("Compiler or SDK changed since staging")
        compiled = {}
        expected = {}
        for component in COMPONENTS:
            for path in (args.stage / "essentials" / component).glob("*.swift"):
                relative = component + "/" + path.name
                expected[relative] = sha(path)
            for path in (args.core_cache / "sources" / component).glob("*.swift"):
                compiled[component + "/" + path.name] = sha(path)
        if compiled != expected: raise ValueError("Core compiler inputs differ from the frozen staged sources")
        resource_hashes = {path.name:sha(path) for path in resources.iterdir() if path.is_file() and path != target}
        if resource_hashes != receipt["resource_sha256"]: raise ValueError("Packaged resources differ from frozen staging")
        record = {
            "schema":"reservoir-scope.packaged-identity.v2",
            "created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "version":plist["CFBundleShortVersionString"], "build":plist["CFBundleVersion"],
            "base_commit":receipt["source_commit"],
            "source_sha256":receipt["files"], "resource_sha256":resource_hashes,
            "staged_inputs_sha256":sha(args.stage / "staged-inputs.json"),
            "resource_manifest_sha256":sha(resources / "resource-manifest.json"),
            "toolchain":receipt["toolchain"],
            "build_settings":{"swift_language_version":"5","optimization":"-O","deployment_target":"macosx14.0"},
            "core_archive_sha256":sha(args.core_cache / "lib/libEssentialsCore.a"),
            "runner_sha256":sha(args.app / "Contents/MacOS/essentials-run"),
            "source_scope":"Exact frozen staged Swift, package, script and supporting inputs. Base commit alone does not describe the research build.",
            "signing_scope":"Ad-hoc signed for trusted research Macs. Final application/archive hashes are recorded externally; no notarization claim."
        }
        manifest = json.loads((resources / "resource-manifest.json").read_text())
        if str(manifest["release"]["version"]) != record["version"] or str(manifest["release"]["build"]) != record["build"]:
            raise ValueError("Bundle version differs from the resource manifest release")
        target.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status":"created","schema":record["schema"],"sources":len(record["source_sha256"])}))
        return
    record = json.loads(target.read_text())
    if record["schema"] not in ("reservoir-scope.packaged-identity.v1","reservoir-scope.packaged-identity.v2"):
        raise ValueError("Unsupported package identity")
    for name, digest in record["resource_sha256"].items():
        if safe(name).name != name or sha(resources / name) != digest: raise ValueError("Resource differs: " + name)
    if (resources / "essentials-workspace.txt").exists(): raise ValueError("Checkout hint must not be packaged")
    v2 = record["schema"].endswith(".v2")
    if v2:
        actual = {path.name for path in resources.iterdir() if path != target}
        if any(not path.is_file() or path.is_symlink() for path in resources.iterdir()): raise ValueError("Unexpected resource directory or link")
        if actual != set(record["resource_sha256"]): raise ValueError("Resource omission or undeclared addition")
        if sha(resources / "resource-manifest.json") != record["resource_manifest_sha256"]: raise ValueError("Resource manifest mismatch")
        manifest = json.loads((resources / "resource-manifest.json").read_text())
        declared = {item["name"]:item["sha256"] for item in manifest["resources"]}
        if len(declared) != len(manifest["resources"]): raise ValueError("Duplicate resource declaration")
        if set(declared) | {"resource-manifest.json"} != actual: raise ValueError("Packaged resources do not match manifest")
        for name, digest in declared.items():
            if record["resource_sha256"][name] != digest: raise ValueError("Resource identity mismatch")
        if sha(args.app / "Contents/MacOS/essentials-run") != record["runner_sha256"]: raise ValueError("Headless runner differs")
        if str(manifest["release"]["version"]) != record["version"] or str(manifest["release"]["build"]) != record["build"]:
            raise ValueError("Release metadata mismatch")
        if plist["CFBundleShortVersionString"] != record["version"] or plist["CFBundleVersion"] != record["build"]:
            raise ValueError("Bundle metadata mismatch")
        if args.stage:
            receipt = stage_receipt(args.stage)
            if receipt["files"] != record["source_sha256"] or receipt["resource_sha256"] != record["resource_sha256"]:
                raise ValueError("Selected staged inputs differ from package identity")
            if sha(args.stage / "staged-inputs.json") != record["staged_inputs_sha256"]:
                raise ValueError("Staged receipt differs from packaged identity")
    examples, cases = validate_catalogs(resources, set(record["resource_sha256"]), v2)
    subprocess.run(["codesign","--verify","--deep","--strict",str(args.app)],check=True)
    print(json.dumps({"status":"verified","version":record["version"],"build":record["build"],
                      "resources":len(record["resource_sha256"]),"examples":examples,"reviewed_cases":cases,
                      "staged_inputs_checked":bool(args.stage and v2)}))
if __name__ == "__main__": main()
