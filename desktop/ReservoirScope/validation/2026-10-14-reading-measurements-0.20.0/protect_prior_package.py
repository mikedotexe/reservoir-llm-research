#!/usr/bin/env python3
"""Preserve qualified 0.19 artifacts before 0.20 build; no app/build/service calls.

Creates one exclusive ignored QA directory, with independent full app/archive/pin
copies. Originals and the 0.19 archive qualification are verified before and after.
No deletion, hard links, code signing, or process inspection is performed.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1]
sys.path.insert(0, str(DESKTOP / "scripts"))
from qualification_receipt import file_entry, package_inventory

BINARY_SHA = "65462e49b6301d89856e28496c3c51b25383935a46b1aa8b8832c7af68c83211"
ARCHIVE_SHA = "82f4298b856e5d5a5cb6f96066a900835472da76cd4e7cc06de95c0385a1cad1"

def info(path):
    value = file_entry(path, str(path), include_mode=True)
    if value["kind"] != "file":
        raise ValueError("Only ordinary files are accepted: " + str(path))
    return value

def available():
    s = os.statvfs(DESKTOP)
    return s.f_bavail * s.f_frsize

def main():
    receipt = HERE / "prior-package-preserved-01.json"
    report = {"schema": "reservoir-prior-package-preservation-v2",
              "startedAtUtc": datetime.now(timezone.utc).isoformat(),
              "scope": "Read/hash/copy exact qualified 0.19 app/archive/pin only; no build/test/application/provider/process invocation."}
    with receipt.open("x") as stream:
        try:
            basis = HERE.parent / "2026-10-14-action-boundaries-0.19.0/archive-check-01.json"
            basis_before = info(basis)
            old = json.loads(basis.read_text())
            app = DESKTOP / "target/release/bundle/macos/Reservoir Scope Tauri Preview.app"
            archive = DESKTOP / "target/release/bundle/macos/ReservoirScopeTauriPreview-0.19.0-macos-arm64.tar.gz"
            pin = DESKTOP / "target/qa/0.19-pinned/reservoir-scope-desktop"
            assert str(app) == old["app"] and str(archive) == old["archive"] and str(pin) == old["pinnedExecutable"]
            assert old["executableSha256"] == BINARY_SHA and old["archiveSha256"] == ARCHIVE_SHA
            package = package_inventory(app)
            assert package == old["package"] and package["version"] == "0.19.0"
            assert all(f["kind"] == "file" for f in package["files"]), "Qualified package has an unexpected symlink"
            archive_before, pin_before = info(archive), info(pin)
            assert archive_before["sha256"] == ARCHIVE_SHA and pin_before["sha256"] == BINARY_SHA
            needed = sum(f["bytes"] for f in package["files"]) + archive_before["bytes"] + pin_before["bytes"]
            free_before = available()
            assert free_before > needed + 1024**3, "Insufficient preservation headroom"
            destination = DESKTOP / "target/qa/0.20-prior-0.19-preserved"
            destination.mkdir(mode=0o700)  # Exclusive. Leave partial output on failure.
            preserved_app = destination / app.name
            shutil.copytree(app, preserved_app, symlinks=True)
            shutil.copy2(archive, destination / archive.name)
            shutil.copy2(pin, destination / "reservoir-scope-desktop-0.19.0-pinned")
            preserved_package = package_inventory(preserved_app)
            archive_copy = info(destination / archive.name)
            pin_copy = info(destination / "reservoir-scope-desktop-0.19.0-pinned")
            assert preserved_package == package
            assert archive_copy["sha256"] == ARCHIVE_SHA and archive_copy["bytes"] == archive_before["bytes"]
            assert pin_copy["sha256"] == BINARY_SHA and pin_copy["bytes"] == pin_before["bytes"]
            assert package_inventory(app) == package
            assert info(archive) == archive_before and info(pin) == pin_before and info(basis) == basis_before
            report.update(passed=True, basis=basis_before, package=package,
                archiveBefore=archive_before, pinBefore=pin_before,
                preservedApp=str(preserved_app), preservedArchive=archive_copy,
                preservedPin=pin_copy, originalsUnchanged=True, copiesByteExact=True,
                copiedLogicalBytes=needed, availableBytesBefore=free_before,
                availableBytesAfter=available(), headroomLimit="Filesystem availability at preservation only, not reservation or future build guarantee.")
        except Exception as error:
            report.update(passed=False, error=f"{type(error).__name__}: {error}")
        report["endedAtUtc"] = datetime.now(timezone.utc).isoformat()
        json.dump(report, stream, indent=2); stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({"passed": report["passed"], "receipt": str(receipt), "receiptSha256": hashlib.sha256(receipt.read_bytes()).hexdigest(), "copiedLogicalBytes": report.get("copiedLogicalBytes"), "availableBytesAfter": report.get("availableBytesAfter")}))
    return 0 if report["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
