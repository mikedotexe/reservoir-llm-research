#!/usr/bin/env python3
"""Preserve qualified 0.22 artifacts before 0.22.1 build; no app/build/service calls.

Creates one exclusive ignored QA directory, with independent full app/archive/pin
copies. Originals and the 0.22 archive qualification are verified before and after.
No deletion, hard links, code signing, or process inspection is performed.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1]
sys.path.insert(0, str(DESKTOP / "scripts"))
from qualification_receipt import file_entry, package_inventory

BINARY_SHA = "788b636ec898f9863e146e7dfe67c380910ae38943b0b178f6e22b8e8d794051"
ARCHIVE_SHA = "9d4359f695289c24a0fefc7949ae731354cea29b83cced4eb953640307ce48d2"

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
              "scope": "Read/hash/copy exact qualified 0.22 app/archive/pin only; no build/test/application/provider/process invocation."}
    with receipt.open("x") as stream:
        try:
            basis = HERE.parent / "2026-10-15-observatory-fields-0.22.0/archive-check-01.json"
            basis_before = info(basis)
            assert basis_before["sha256"] == "4200ed7a6de46a26f78f83d80e783a67fb24a487dc872a69388882bb52966eef", "Qualified archive receipt changed"
            old = json.loads(basis.read_text())
            app = DESKTOP / "target/release/bundle/macos/Reservoir Scope Tauri Preview.app"
            archive = DESKTOP / "target/release/bundle/macos/ReservoirScopeTauriPreview-0.22.0-macos-arm64.tar.gz"
            pin = DESKTOP / "target/qa/0.22-pinned/reservoir-scope-desktop"
            assert str(app) == old["app"] and str(archive) == old["archive"] and str(pin) == old["pinnedExecutable"]
            assert old["executableSha256"] == BINARY_SHA and old["archiveSha256"] == ARCHIVE_SHA
            package = package_inventory(app)
            assert package == old["package"] and package["version"] == "0.22.0"
            assert all(f["kind"] == "file" for f in package["files"]), "Qualified package has an unexpected symlink"
            archive_before, pin_before = info(archive), info(pin)
            assert archive_before["sha256"] == ARCHIVE_SHA and pin_before["sha256"] == BINARY_SHA
            needed = sum(f["bytes"] for f in package["files"]) + archive_before["bytes"] + pin_before["bytes"]
            free_before = available()
            assert free_before > needed + 1024**3, "Insufficient preservation headroom"
            destination = DESKTOP / "target/qa/0.22.1-prior-0.22-preserved"
            destination.mkdir(mode=0o700)  # Exclusive. Leave partial output on failure.
            preserved_app = destination / app.name
            shutil.copytree(app, preserved_app, symlinks=True)
            shutil.copy2(archive, destination / archive.name)
            shutil.copy2(pin, destination / "reservoir-scope-desktop-0.22.0-pinned")
            preserved_package = package_inventory(preserved_app)
            archive_copy = info(destination / archive.name)
            pin_copy = info(destination / "reservoir-scope-desktop-0.22.0-pinned")
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
