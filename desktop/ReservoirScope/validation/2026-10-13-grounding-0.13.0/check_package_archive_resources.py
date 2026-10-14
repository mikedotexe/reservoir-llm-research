"""Validate already-built 0.13.0 bundle, archive exclusively, compare frozen resources.

Does not build, launch, sign, install, or mutate any app/canonical/staged resource.
The parent captured package-before-ui.json before UI launch. This separate check
compares the bundle against that accepted identity before and after reading it.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tarfile

VALIDATION = Path(__file__).resolve().parent
DESKTOP = VALIDATION.parents[1]
ROOT = DESKTOP.parents[1]
sys.path.insert(0, str(DESKTOP / "scripts"))
from qualification_receipt import file_entry, inventory_digest, package_inventory, source_inventory, observe


def write_new(name, receipt):
    with (VALIDATION / name).open("x", encoding="utf-8") as output:
        json.dump(receipt, output, indent=2)
        output.write("\n")


def digest_stream(stream):
    digest = hashlib.sha256()
    size = 0
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        size += len(chunk)
        digest.update(chunk)
    return size, digest.hexdigest()


def plain_file(path, label):
    value = file_entry(path, label)
    if value["kind"] != "file":
        raise ValueError(f"Expected a regular file: {path}")
    return value


# These living prose files are not imported by the current build. Changes are
# allowed only when explicitly named at invocation and are retained in the receipt.
DOCUMENTATION_PATHS = {
    "desktop/ReservoirScope/README.md",
    "shared/reservoir-scope/PARITY.md",
}


def compare_sources(before, after, allowed):
    old = {item["path"]: item for item in before}
    new = {item["path"]: item for item in after}
    assert len(old) == len(before) and len(new) == len(after), "Duplicate source inventory paths"
    assert old.keys() == new.keys(), "Source inventory file set changed since build"
    assert set(allowed) <= DOCUMENTATION_PATHS, "Unreviewed documentation exclusion"
    changes = [{"path": path, "before": old[path], "after": new[path]}
               for path in sorted(old) if old[path] != new[path]]
    assert all(item["path"] in allowed and item["before"]["kind"] == item["after"]["kind"] == "file"
               for item in changes), "Unapproved source change since build"
    preserved = [item for item in before if item["path"] not in allowed]
    assert preserved == [item for item in after if item["path"] not in allowed]
    return {"allSourcesUnchanged": not changes,
            "explicitDocumentationAllowlist": sorted(allowed),
            "documentationChanges": changes,
            "allOtherSourceFilesUnchanged": True,
            "otherSourceFileCount": len(preserved),
            "otherSourceInventorySha256": inventory_digest(preserved),
            "beforeInventorySha256": inventory_digest(before),
            "afterInventorySha256": inventory_digest(after)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-binary-sha256", required=True)
    parser.add_argument("--allow-documentation-change", action="append", default=[], choices=sorted(DOCUMENTATION_PATHS))
    args = parser.parse_args()
    before = json.loads((VALIDATION / "package-before-ui.json").read_text())
    source_before = json.loads((VALIDATION / "source-before-build-final.json").read_text())
    app = DESKTOP / "target/release/bundle/macos/Reservoir Scope Tauri Preview.app"
    package = package_inventory(app)
    assert package == before["package"], "App differs from pre-UI identity"
    assert package["version"] == package["build"] == "0.13.0", "Unexpected package version"
    assert package["binary"]["sha256"] == args.expected_binary_sha256, "Binary identity differs from parent-provided candidate"
    source_check = compare_sources(source_before["files"], source_inventory(), args.allow_documentation_change)
    signing = {"display": observe(["codesign", "--display", "--verbose=4", str(app)]),
               "verification": observe(["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(app)])}
    assert signing["display"]["exitCode"] == signing["verification"]["exitCode"] == 0, "Local codesign verification failed"
    signing["meaning"] = "Local signature verification only; no notarization, distribution identity, UI, or model-execution claim."
    signing["status"] = "verified"
    write_new("package-signing-check.json", {"capturedAtUtc": datetime.now(timezone.utc).isoformat(),
              "packageInventorySha256": package["inventorySha256"], "binary": package["binary"], "codesign": signing})
    archive = app.parent / "ReservoirScopeTauriPreview-0.13.0-macos-arm64.tar.gz"
    with tarfile.open(archive, "x:gz", compresslevel=3, dereference=False) as output:
        output.add(app, arcname=app.name)
    expected = {app.name: app}
    for parent, directories, files in os.walk(app, followlinks=False):
        for name in [*directories, *files]:
            path = Path(parent) / name
            expected[f"{app.name}/{path.relative_to(app).as_posix()}"] = path
    members = []
    with tarfile.open(archive, "r:gz") as packed:
        names = [member.name for member in packed.getmembers()]
        assert len(set(names)) == len(names), "Archive has duplicate member names"
        assert set(names) == set(expected), "Archive member set differs from app"
        for member in packed.getmembers():
            path = expected[member.name]
            metadata = path.lstat()
            item = {"name": member.name, "mode": oct(member.mode)}
            assert stat.S_IMODE(metadata.st_mode) == member.mode, member.name
            if member.isdir():
                assert stat.S_ISDIR(metadata.st_mode), member.name
                item["kind"] = "directory"
            elif member.issym():
                assert path.is_symlink() and os.readlink(path) == member.linkname, member.name
                item.update(kind="symlink", target=member.linkname)
            elif member.isfile() or member.islnk():
                assert stat.S_ISREG(metadata.st_mode), member.name
                if member.islnk():
                    assert member.linkname in expected and os.path.samefile(path, expected[member.linkname]), member.name
                stream = packed.extractfile(member)
                assert stream is not None
                with stream:
                    size, digest = digest_stream(stream)
                current = plain_file(path, member.name)
                assert size == current["bytes"] and digest == current["sha256"], member.name
                item.update(kind="file", bytes=size, sha256=digest)
            else:
                raise ValueError(f"Unsupported archive member type: {member.name}")
            members.append(item)
    assert package_inventory(app) == package, "App changed during archive verification"
    archive_identity = plain_file(archive, str(archive))
    write_new("archive-check.json", {
        "capturedAtUtc": datetime.now(timezone.utc).isoformat(),
        "archive": str(archive), "bytes": archive_identity["bytes"], "sha256": archive_identity["sha256"],
        "creation": "Python tarfile x:gz, compression level3, existing archive refused",
        "passed": True, "allMembersMatchApp": True, "allRegularFilesMatchApp": True,
        "regularFiles": sum(item["kind"] == "file" for item in members),
        "packageUnchangedSincePreUiCapture": True,
        "packageInventorySha256": package["inventorySha256"], "members": members,
        "limits": "Identity and archive-member verification. UI may run concurrently; this is not a completed-UI qualification claim.",
    })

    staged = DESKTOP / "src-tauri/resources"
    resources = app / "Contents/Resources/resources"
    index_bytes = (staged / "resource-index.json").read_bytes()
    assert (resources / "resource-index.json").read_bytes() == index_bytes
    index = json.loads(index_bytes)
    assert index["schema"] == "reservoir-scope.resource-index.v1"
    assert len(index["resources"]) == 39
    canonical = []
    names = {"resource-index.json", "reference-manifest.json", "reference-scenes.json"}
    for item in index["resources"]:
        name = item["name"]
        assert Path(name).name == name and name not in names
        names.add(name)
        source = Path(item["source"])
        assert not source.is_absolute() and ".." not in source.parts
        identities = [plain_file(path, str(path.relative_to(ROOT))) for path in (ROOT / source, staged / name, resources / name)]
        assert all(entry["bytes"] == item["bytes"] and entry["sha256"] == item["sha256"] for entry in identities), name
        canonical.append({**item, "canonicalStagedAndPackageMatch": True})
    assert {p.name for p in resources.iterdir()} == names, "Unexpected or missing packaged resource"
    assert {p.name for p in staged.iterdir()} == names, "Unexpected or missing staged resource"
    references = []
    for name, source, expected_hash in [
        ("reference-manifest.json", ROOT / "shared/reservoir-scope/reference-manifest.json", index["referenceManifestSha256"]),
        ("reference-scenes.json", ROOT / "shared/reservoir-scope/fixtures/reference-scenes.json", index["referenceScenesSha256"]),
    ]:
        data = source.read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected_hash
        assert (staged / name).read_bytes() == data and (resources / name).read_bytes() == data
        references.append({"name": name, "source": str(source.relative_to(ROOT)), "bytes": len(data), "sha256": expected_hash})
    manifest = json.loads((ROOT / "shared/reservoir-scope/reference-manifest.json").read_bytes())
    assert manifest["baseline"]["commit"] == index["baselineCommit"]
    frozen_resources = {item["name"]: item for item in manifest["resources"]}
    for item in canonical:
        frozen = frozen_resources[item["name"]]
        assert (item["source"], item["sha256"], item["bytes"]) == (frozen["path"], frozen["sha256"], frozen["bytes"])
    source_after = source_inventory()
    source_check = compare_sources(source_before["files"], source_after, args.allow_documentation_change)
    assert package_inventory(app) == package
    write_new("package-resource-check.json", {
        "capturedAtUtc": datetime.now(timezone.utc).isoformat(), "passed": True,
        "canonicalInputs": canonical, "canonicalCount": len(canonical),
        "totalPackagedResourceFiles": len(names), "frozenManifestAndScenesMatch": True,
        "references": references, "stagedIndexMatches": True,
        "indexSha256": hashlib.sha256(index_bytes).hexdigest(),
        "sourceInventorySha256": inventory_digest(source_after),
        "sourceContinuity": source_check, "packageUnchangedSincePreUiCapture": True,
        "packageInventorySha256": package["inventorySha256"],
        "archiveAllFilesCheck": "archive-check.json",
        "signingCheck": "package-signing-check.json",
        "helperSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    })
    print(json.dumps({"passed": True, "archive": str(archive), "archiveSha256": archive_identity["sha256"],
                      "archiveBytes": archive_identity["bytes"], "regularFiles": sum(item["kind"] == "file" for item in members),
                      "canonicalResources": len(canonical), "packagedResources": len(names)}))


if __name__ == "__main__":
    main()
