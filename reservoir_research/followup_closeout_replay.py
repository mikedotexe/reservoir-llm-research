"""Supported closeout build/replay from a private snapshot of explicit hashed inputs.

The original v1 recovery and report code stays immutable. Its daily readers reopen
files, so every v1 calculation here receives only a private snapshot populated from
one stable, hash-checked read per explicit input. No recovery or source-path lookup.
"""
from __future__ import annotations

import json
import os
import re
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path

from . import followup_closeout as v1
from . import research_followups as frozen

FILES = ("reservoir_research/followup_closeout_replay.py",
         "probes/research_followups_closeout_replay.py", "tests/test_research_followups_closeout_replay.py")
TOTAL_LIMIT = 512 * 1024**2
FILE_LIMIT = 256 * 1024**2
INPUT_COUNT_LIMIT = 256


def identity():
    return {name: frozen.sha((v1.ROOT / name).read_bytes()) for name in FILES}


def stable_bytes(path, limit):
    """Check path, open descriptor and final inode/metadata; refuse unstable reads."""
    path = Path(path).absolute()
    v1.require(path == path.resolve() and not path.is_symlink(), "Noncanonical snapshot input")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(descriptor)
        v1.require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, "Snapshot file size/type cap")
        parts, remaining = [], before.st_size + 1
        while remaining:
            chunk = os.read(descriptor, min(1024**2, remaining))
            if not chunk:
                break
            parts.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(parts)
        after = os.fstat(descriptor)
        current = path.lstat()
        keys = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
        witness = lambda value: tuple(getattr(value, key) for key in keys)
        v1.require(witness(before) == witness(after) == witness(current) and
                   path == path.resolve() and len(raw) == before.st_size,
                   "Snapshot input changed during read")
        return raw
    finally:
        os.close(descriptor)


@contextmanager
def snapshot_inputs(manifest_path, data_root):
    """Read originals once; yield only the copied bytes to historical calculations."""
    raw_manifest = stable_bytes(manifest_path, 8 * 1024**2)
    manifest = json.loads(raw_manifest)
    v1.require(manifest["schema"] == v1.SCHEMA, "Unknown closeout input schema")
    files = manifest["files"]
    v1.require(isinstance(files, dict) and 0 < len(files) <= INPUT_COUNT_LIMIT, "Explicit input count cap")
    original_root = Path(data_root).absolute()
    v1.require(original_root == original_root.resolve() and not original_root.is_symlink(),
               "Noncanonical retained root")
    total = 0
    with tempfile.TemporaryDirectory(prefix="bounded-followup-snapshot-") as temp:
        target = Path(temp).resolve()
        target.chmod(0o700)
        for name, expected in files.items():
            v1.require(isinstance(name, str) and isinstance(expected, str) and
                       re.fullmatch(r"[0-9a-f]{64}", expected), "Invalid explicit input identity")
            source = v1.safe(original_root, name)
            raw = stable_bytes(source, min(FILE_LIMIT, TOTAL_LIMIT - total))
            v1.require(frozen.sha(raw) == expected, "Snapshot input hash mismatch: " + name)
            total += len(raw)
            destination = v1.safe(target, name)
            destination.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(raw)
            destination.chmod(0o400)
        proof = dict(schema="bounded_followup_input_snapshot_v1", input_manifest_sha256=frozen.sha(raw_manifest),
                     explicit_files=len(files), input_bytes=total, stable_hash_checked_reads=True,
                     original_inputs_reopened_by_v1=False)
        yield manifest, target, proof


def calculate(manifest_path, data_root):
    wrapper_identity, original_identity = identity(), v1.identity()
    with snapshot_inputs(manifest_path, data_root) as (manifest, root, proof):
        report = v1.build_report(manifest, root)
    v1.require(identity() == wrapper_identity and v1.identity() == original_identity,
               "Code identity changed during snapshot replay")
    return manifest, report, dict(proof, wrapper_code=wrapper_identity, v1_code=original_identity)


def build(manifest_path, data_root, out):
    manifest, report, proof = calculate(manifest_path, data_root)
    folder = v1.output_directory(out)
    v1.write_json(folder / "inputs.json", manifest)
    v1.write_json(folder / "report.json", report)
    v1.write_json(folder / "construction.json", dict(schema="bounded_followup_snapshot_construction_v1",
        status="constructed_verification_pending", report_sha256=frozen.sha(frozen.encoded(report)),
        input_snapshot=proof, original_sources_read=False, ledger_written=False))
    v1.seal(folder)
    return dict(output=str(folder), status="constructed_verification_pending",
                report_sha256=frozen.sha(frozen.encoded(report)), snapshot=proof)


def verify(manifest_path, data_root, report_path):
    actual = stable_bytes(report_path, 64 * 1024**2)
    _manifest, expected, proof = calculate(manifest_path, data_root)
    v1.require(actual == frozen.encoded(expected), "Closeout report does not replay exactly")
    return dict(schema="bounded_followup_snapshot_verification_v1", verified=True,
                report_sha256=frozen.sha(actual), snapshot=proof,
                source_paths_followed=False, ledger_written=False)
