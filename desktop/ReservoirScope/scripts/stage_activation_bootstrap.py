#!/usr/bin/env python3
"""Restore only the two hash-pinned bootstrap assets required by the Tauri bundle.

Uses the committed setup manifest without refreezing locks, licenses or model
metadata. Downloads public archives; never executes their contents or loads a model.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
import tempfile
import urllib.parse
import urllib.request

DEFAULT_BUNDLE = Path(__file__).resolve().parents[1] / "activation_setup_bundle"
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "ReservoirScope-bootstrap-stage/1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(data) > MAX_ARCHIVE_BYTES:
        raise ValueError("Bootstrap archive exceeds the staging limit")
    return data


def asset_path(bundle: Path, value: str) -> Path:
    if not isinstance(value, str) or "\\" in value:
        raise ValueError("Bootstrap asset path must be a direct child of assets/")
    path = PurePosixPath(value)
    if len(path.parts) != 2 or path.parts[0] != "assets" or path.parts[1] in (".", ".."):
        raise ValueError("Bootstrap asset path must be a direct child of assets/")
    return bundle / path.parts[0] / path.parts[1]


def validate_bytes(data: bytes, expected_sha: str, expected_size: int | None, label: str) -> None:
    if len(data) > MAX_ARCHIVE_BYTES or (expected_size is not None and len(data) != expected_size):
        raise ValueError(f"Bootstrap size mismatch: {label}")
    if sha(data) != expected_sha:
        raise ValueError(f"Bootstrap SHA-256 mismatch: {label}")


def existing_matches(path: Path, expected_sha: str, size: int) -> bool:
    if not path.exists() and not path.is_symlink():
        return False
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError(f"Bootstrap destination must be an ordinary file: {path.name}")
    if path.stat().st_size != size:
        raise ValueError(f"Refusing different existing bootstrap bytes: {path.name}")
    validate_bytes(path.read_bytes(), expected_sha, size, path.name)
    return True


def publish(path: Path, data: bytes, executable: bool) -> None:
    # Same-directory hard-link publication is atomic and never replaces an existing
    # file. The staged temporary is removed on success or failure.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".bootstrap-", delete=False) as staged:
            temporary = Path(staged.name)
            staged.write(data)
            staged.flush()
            os.fsync(staged.fileno())
        temporary.chmod(0o755 if executable else 0o644)
        try:
            os.link(temporary, path)
        except FileExistsError:
            existing_matches(path, sha(data), len(data))
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def stage(bundle: Path = DEFAULT_BUNDLE, downloader=None) -> dict:
    downloader = downloader or fetch
    bundle = Path(bundle)
    if bundle.is_symlink() or not bundle.is_dir():
        raise ValueError("Setup bundle must be an ordinary existing directory")
    manifest = json.loads((bundle / "setup-manifest.json").read_text())
    if manifest.get("schema") != "activation-setup-manifest-v1":
        raise ValueError("Unsupported setup manifest")
    python, uv = manifest["python"], manifest["uv"]
    specs = [
        (asset_path(bundle, python["archivePath"]), python["archiveSha256"], python["archiveBytes"], False),
        (asset_path(bundle, uv["path"]), uv["sha256"], uv["bytes"], True),
    ]
    if specs[0][0] == specs[1][0]:
        raise ValueError("Bootstrap destinations must differ")
    for _, digest, size, _ in specs:
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Invalid bootstrap SHA-256")
        if type(size) is not int or not 0 < size <= MAX_ARCHIVE_BYTES:
            raise ValueError("Invalid bootstrap size")
    if not isinstance(uv["archiveSha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", uv["archiveSha256"]):
        raise ValueError("Invalid uv archive SHA-256")
    for spec in (python, uv):
        url = urllib.parse.urlsplit(spec["url"])
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            raise ValueError("Bootstrap downloads require an HTTPS URL without credentials")
    assets = bundle / "assets"
    if assets.is_symlink() or (assets.exists() and not assets.is_dir()):
        raise ValueError("Bootstrap assets must be an ordinary directory")
    present = [existing_matches(path, digest, size) for path, digest, size, _ in specs]
    payloads = {}
    if not present[0]:
        data = downloader(python["url"])
        validate_bytes(data, specs[0][1], specs[0][2], "Python archive")
        payloads[0] = data
    if not present[1]:
        data = downloader(uv["url"])
        validate_bytes(data, uv["archiveSha256"], None, "uv archive")
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            members = [m for m in archive.getmembers() if PurePosixPath(m.name).name == "uv"]
            if len(members) != 1 or not members[0].isfile() or members[0].size != specs[1][2]:
                raise ValueError("uv archive must contain exactly one ordinary uv file of the pinned size")
            with archive.extractfile(members[0]) as source:
                executable = source.read(specs[1][2] + 1)
        validate_bytes(executable, specs[1][1], specs[1][2], "uv executable")
        payloads[1] = executable
    # Verify every downloaded input before publishing either final asset.
    assets.mkdir(exist_ok=True)
    for index, data in payloads.items():
        path, _, _, executable = specs[index]
        publish(path, data, executable)
    for path, digest, size, executable in specs:
        if not existing_matches(path, digest, size):
            raise ValueError(f"Bootstrap asset missing after staging: {path.name}")
        if executable:
            path.chmod(path.stat().st_mode | 0o111)
    return {"status": "verified", "downloadedAssets": len(payloads),
            "assets": [{"path": p.relative_to(bundle).as_posix(), "sha256": h, "bytes": n}
                       for p, h, n, _ in specs]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    args = parser.parse_args()
    try:
        print(json.dumps(stage(args.bundle), sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError) as error:
        parser.exit(1, f"Bootstrap staging failed: {error}\n")


if __name__ == "__main__":
    main()
