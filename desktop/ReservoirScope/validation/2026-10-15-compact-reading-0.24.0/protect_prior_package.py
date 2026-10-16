#!/usr/bin/env python3
"""Preserve qualified 0.23.0 artifacts before 0.24.0 build; no app/build/service calls.

Creates one exclusive ignored QA directory, with independent full app/archive/pin
copies. Originals and the 0.23.0 archive qualification are verified before and after.
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
from qualification_receipt import file_entry, package_inventory, source_inventory, inventory_digest
REPOSITORY = DESKTOP.parents[1]

BINARY_SHA = "7b8245932cae928b069fe4ca6609597f94ad3a54dbd8a0082c30a505c26a024b"
ARCHIVE_SHA = "9862d89a0901cd86e6dc734afc6346a5164e09aef8a93edbfdc180afaed39c7c"

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
              "scope": "Read/hash/copy exact current source and root roadmap plus qualified 0.23.0 app/archive/pin; no build/test/application/provider/process invocation."}
    with receipt.open("x") as stream:
        try:
            source_before = source_inventory()
            roadmap_before = file_entry(REPOSITORY/'TAURI-ROADMAP.md', 'TAURI-ROADMAP.md')
            source_rows = source_before + [roadmap_before]
            assert all(x['kind']=='file' for x in source_rows), 'Unexpected source symlink/type; preservation requires review'
            basis = HERE.parent / "2026-10-15-navigation-0.23.0/archive-check-01.json"
            basis_before = info(basis)
            assert basis_before["sha256"] == "ff34d710332fc8892a65151ddd4e834eb371529802ef3af2a99c5aaeaa05cc97", "Qualified archive receipt changed"
            old = json.loads(basis.read_text())
            app = DESKTOP / "target/release/bundle/macos/Reservoir Scope Tauri Preview.app"
            archive = DESKTOP / "target/release/bundle/macos/ReservoirScopeTauriPreview-0.23.0-macos-arm64.tar.gz"
            pin = DESKTOP / "target/qa/0.23.0-pinned/reservoir-scope-desktop"
            assert str(app) == old["app"] and str(archive) == old["archive"] and str(pin) == old["pinnedExecutable"]
            assert old["executableSha256"] == BINARY_SHA and old["archiveSha256"] == ARCHIVE_SHA
            package = package_inventory(app)
            assert package == old["package"] and package["version"] == "0.23.0"
            assert all(f["kind"] == "file" for f in package["files"]), "Qualified package has an unexpected symlink"
            archive_before, pin_before = info(archive), info(pin)
            assert archive_before["sha256"] == ARCHIVE_SHA and pin_before["sha256"] == BINARY_SHA
            needed = sum(f["bytes"] for f in package["files"]) + archive_before["bytes"] + pin_before["bytes"] + sum(x["bytes"] for x in source_rows)
            free_before = available()
            assert free_before > needed + 1024**3, "Insufficient preservation headroom"
            destination = DESKTOP / "target/qa/0.24-prior-0.23-preserved"
            destination.mkdir(mode=0o700)  # Exclusive. Leave partial output on failure.
            source_destination = destination/'source'
            source_destination.mkdir(mode=0o700)
            copied_sources=[]
            for row in source_rows:
                source = REPOSITORY/row['path']
                target = source_destination/row['path']
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(source,target)
                copied=file_entry(target,row['path'])
                assert copied==row, 'Source copy changed: '+row['path']
                copied_sources.append(copied)
            assert source_inventory()==source_before, 'Source changed during snapshot'
            assert file_entry(REPOSITORY/'TAURI-ROADMAP.md','TAURI-ROADMAP.md')==roadmap_before
            preserved_app = destination / app.name
            shutil.copytree(app, preserved_app, symlinks=True)
            shutil.copy2(archive, destination / archive.name)
            shutil.copy2(pin, destination / "reservoir-scope-desktop-0.23.0-pinned")
            preserved_package = package_inventory(preserved_app)
            archive_copy = info(destination / archive.name)
            pin_copy = info(destination / "reservoir-scope-desktop-0.23.0-pinned")
            assert preserved_package == package
            assert archive_copy["sha256"] == ARCHIVE_SHA and archive_copy["bytes"] == archive_before["bytes"]
            assert pin_copy["sha256"] == BINARY_SHA and pin_copy["bytes"] == pin_before["bytes"]
            assert package_inventory(app) == package
            assert info(archive) == archive_before and info(pin) == pin_before and info(basis) == basis_before
            assert source_inventory()==source_before, 'Source changed during package preservation'
            assert file_entry(REPOSITORY/'TAURI-ROADMAP.md','TAURI-ROADMAP.md')==roadmap_before
            report.update(passed=True, basis=basis_before, package=package,
                sourceSnapshot=str(source_destination),sourceInventory=source_before,
                sourceInventorySha256=inventory_digest(source_before),roadmap=roadmap_before,
                sourceFileCount=len(source_rows),sourceBytes=sum(x['bytes'] for x in source_rows),
                sourceSnapshotByteExact=True,sourceUnchangedDuringPreservation=True,
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
