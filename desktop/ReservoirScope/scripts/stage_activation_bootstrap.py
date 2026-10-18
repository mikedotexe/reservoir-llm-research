#!/usr/bin/env python3
"""Stage only the two public, frozen macOS bootstrap artifacts required by Tauri.

The default bundle declares these ignored assets even for ordinary Ollama builds.
A fresh checkout therefore needs their bytes before Rust's Tauri build script
copies resources. Unlike freeze_activation_setup.py, this helper never refreezes
metadata, queries wheels/models, imports a runtime, or executes downloaded code.
Matching caches are preserved and need no network; --check never writes/downloads.
Each download runs only this tracked Python helper in a directly owned child,
with a 180-second total timeout; timeout kills and reaps it before cleanup.
Downloaded bytes are never executed. Streaming also has byte/deadline checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.parse
import urllib.request

APP = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = APP / "activation_setup_bundle"
UV_ARCHIVE = "uv-aarch64-apple-darwin.tar.gz"
UV_MEMBER = "uv-aarch64-apple-darwin/uv"
MAX_ARCHIVE_BYTES = 64 * 1024**2
MAX_EXPANDED_BYTES = 128 * 1024**2
BLOCK = 1024 * 1024
DOWNLOAD_SECONDS = 180
ALLOWED_HOSTS = {"github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}


def ordinary(path: Path, directory=False):
    info = path.lstat()
    if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise ValueError(f"Expected ordinary {'directory' if directory else 'file'}: {path}")
    return info


def exists(path):
    # Unlike exists(), this also detects dangling symlinks for rejection.
    return os.path.lexists(path)


def size(value, maximum):
    if type(value) is not int or not 0 < value <= maximum:
        raise ValueError("Invalid frozen bootstrap size")
    return value


def sha(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("Invalid frozen bootstrap SHA-256")
    return value


def asset_path(root, relative):
    if not isinstance(relative, str) or "\\" in relative:
        raise ValueError("Invalid bootstrap asset path")
    parts = PurePosixPath(relative).parts
    if len(parts) != 2 or parts[0] != "assets" or parts[1] in {".", ".."}:
        raise ValueError("Bootstrap asset must be a direct child of assets/")
    return root.joinpath(*parts)


def checked_url(value):
    parsed = urllib.parse.urlsplit(value)
    if (parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS
            or parsed.username or parsed.password or parsed.port not in (None, 443)):
        raise ValueError("Bootstrap download requires an approved HTTPS host")
    return value


class BootstrapRedirect(urllib.request.HTTPRedirectHandler):
    max_repeats = 2
    max_redirections = 5

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        checked_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_download(url):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), BootstrapRedirect())
    request = urllib.request.Request(checked_url(url), headers={
        "User-Agent": "ReservoirScope-bootstrap-stage/1", "Accept-Encoding": "identity"})
    return opener.open(request, timeout=30)


def verify(path, expected_sha, expected_size=None, maximum=MAX_ARCHIVE_BYTES, executable=False):
    info = ordinary(path)
    if info.st_size > maximum or (expected_size is not None and info.st_size != expected_size):
        raise ValueError(f"Cached bootstrap size differs: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(BLOCK):
            digest.update(block)
    if digest.hexdigest() != expected_sha:
        raise ValueError(f"Cached bootstrap SHA-256 differs: {path}")
    if executable and os.name != "nt" and not info.st_mode & 0o111:
        raise ValueError(f"Cached uv is not executable: {path}")
    return {"path": str(path), "bytes": info.st_size, "sha256": expected_sha}


def publish(temp, target, expected_sha, expected_size, maximum, executable=False):
    # A hard link publishes a complete verified file atomically without replacing
    # an existing destination. A concurrent publisher must have identical bytes.
    try:
        os.link(temp, target)
    except FileExistsError:
        verify(target, expected_sha, expected_size, maximum, executable)


def download_payload(url, temporary, expected_sha, expected_size, maximum):
    """Child-only I/O; tests call this with a synthetic response, never the network."""
    deadline = time.monotonic() + DOWNLOAD_SECONDS
    ordinary(temporary)
    digest = hashlib.sha256()
    count = 0
    with temporary.open("wb") as output, open_download(url) as response:
        checked_url(response.geturl())
        if response.status != 200:
            raise ValueError(f"Bootstrap download returned HTTP {response.status}")
        length = response.headers.get("Content-Length")
        declared = int(length) if length is not None else None
        if declared is not None and (declared < 0 or declared > maximum
                or expected_size is not None and declared != expected_size):
            raise ValueError("Bootstrap Content-Length differs or exceeds bound")
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError("Bootstrap download deadline reached")
            block = response.read1(min(BLOCK, maximum - count + 1))
            if time.monotonic() >= deadline:
                raise TimeoutError("Bootstrap download deadline reached")
            if not block:
                break
            count += len(block)
            if count > maximum:
                raise ValueError("Bootstrap download exceeds byte bound")
            output.write(block)
            digest.update(block)
        if declared is not None and count != declared:
            raise ValueError("Bootstrap download is shorter than Content-Length")
        if expected_size is not None and count != expected_size:
            raise ValueError("Bootstrap download size differs")
        if digest.hexdigest() != expected_sha:
            raise ValueError("Bootstrap download SHA-256 differs")
        output.flush()
        os.fsync(output.fileno())


def download(url, target, expected_sha, expected_size=None, maximum=MAX_ARCHIVE_BYTES):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".bootstrap-", dir=target.parent, delete=False) as output:
            temporary = Path(output.name)
        command = [sys.executable, "-B", str(Path(__file__).resolve()), "--download-worker",
                   url, str(temporary), expected_sha,
                   str(expected_size) if expected_size is not None else "none", str(maximum)]
        # subprocess.run kills and waits for its directly owned child on timeout.
        # The child performs urllib I/O only and never spawns descendants.
        result = subprocess.run(command, capture_output=True, text=True,
                                stdin=subprocess.DEVNULL, timeout=DOWNLOAD_SECONDS)
        if result.returncode:
            raise ValueError(f"Bootstrap download failed: {result.stderr.strip()}")
        verify(temporary, expected_sha, expected_size, maximum)
        temporary.chmod(0o644)
        publish(temporary, target, expected_sha, expected_size, maximum)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def extract_uv(archive, target, expected_sha, expected_size):
    temporary = None
    try:
        with tarfile.open(archive, "r:gz") as source:
            selected = None
            expanded = 0
            for index, member in enumerate(source):
                parts = PurePosixPath(member.name).parts
                if (index >= 256 or not parts or PurePosixPath(member.name).is_absolute()
                        or ".." in parts or "\\" in member.name
                        or not (member.isfile() or member.isdir())):
                    raise ValueError("Unsafe or excessive uv archive members")
                expanded += member.size
                if expanded > MAX_EXPANDED_BYTES or member.size < 0:
                    raise ValueError("uv archive expanded size exceeds bound")
                if member.name == UV_MEMBER:
                    if selected is not None or not member.isfile() or member.size != expected_size:
                        raise ValueError("uv archive member is duplicate, nonregular or wrong-sized")
                    selected = member
            if selected is None:
                raise ValueError("uv archive has no exact ordinary uv member")
            with source.extractfile(selected) as stream, tempfile.NamedTemporaryFile(
                    prefix=".bootstrap-", dir=target.parent, delete=False) as output:
                temporary = Path(output.name)
                count = 0
                digest = hashlib.sha256()
                while block := stream.read(min(BLOCK, expected_size - count + 1)):
                    count += len(block)
                    if count > expected_size:
                        raise ValueError("Extracted uv exceeds frozen size")
                    digest.update(block)
                    output.write(block)
                if count != expected_size or digest.hexdigest() != expected_sha:
                    raise ValueError("Extracted uv size or SHA-256 differs")
                output.flush()
                os.fsync(output.fileno())
            temporary.chmod(0o755)
        publish(temporary, target, expected_sha, expected_size, MAX_ARCHIVE_BYTES, True)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def stage(bundle=DEFAULT_BUNDLE, check_only=False):
    root = Path(bundle).absolute()
    for parent in (root, *root.parents):
        ordinary(parent, directory=True)
    manifest_path = root / "setup-manifest.json"
    if ordinary(manifest_path).st_size > 1024 * 1024:
        raise ValueError("Oversized setup manifest")
    original = manifest_path.read_bytes()
    manifest = json.loads(original)
    if manifest["schema"] != "activation-setup-manifest-v1":
        raise ValueError("Unsupported setup manifest")
    python, uv = manifest["python"], manifest["uv"]
    python_path = asset_path(root, python["archivePath"])
    uv_path = asset_path(root, uv["path"])
    archive = root / "assets" / UV_ARCHIVE
    if len({python_path, uv_path, archive}) != 3 or uv_path.name != "uv":
        raise ValueError("Bootstrap asset names overlap or uv path differs")
    python_sha, uv_sha, archive_sha = sha(python["archiveSha256"]), sha(uv["sha256"]), sha(uv["archiveSha256"])
    python_size, uv_size = size(python["archiveBytes"], MAX_ARCHIVE_BYTES), size(uv["bytes"], MAX_ARCHIVE_BYTES)
    for item, prefix in ((python, "https://github.com/astral-sh/python-build-standalone/releases/download/"),
                         (uv, "https://github.com/astral-sh/uv/releases/download/")):
        if not checked_url(item["url"]).startswith(prefix):
            raise ValueError("Unexpected frozen bootstrap release URL")
    assets = root / "assets"
    if exists(assets):
        ordinary(assets, directory=True)
    # Validate every existing selected cache before any network or filesystem mutation.
    for path, digest, length, executable in ((python_path, python_sha, python_size, False),
                                             (uv_path, uv_sha, uv_size, True),
                                             (archive, archive_sha, None, False)):
        if exists(path):
            verify(path, digest, length, executable=executable)
    missing = [str(path) for path in (python_path, uv_path) if not exists(path)]
    if check_only:
        return {"status": "missing" if missing else "verified", "checkOnly": True,
                "missing": missing, "downloads": [], "manifestSha256": hashlib.sha256(original).hexdigest()}
    downloads = []
    assets.mkdir(exist_ok=True)
    ordinary(assets, directory=True)
    if not exists(python_path):
        download(python["url"], python_path, python_sha, python_size, python_size)
        downloads.append(python["url"])
    if not exists(uv_path):
        if not exists(archive):
            download(uv["url"], archive, archive_sha)
            downloads.append(uv["url"])
        extract_uv(archive, uv_path, uv_sha, uv_size)
    if manifest_path.read_bytes() != original:
        raise ValueError("Frozen setup manifest changed during staging")
    return {"status": "verified", "checkOnly": False, "downloads": downloads,
            "manifestSha256": hashlib.sha256(original).hexdigest(),
            "artifacts": [verify(python_path, python_sha, python_size),
                          verify(uv_path, uv_sha, uv_size, executable=True)],
            "scope": "Pinned public bootstrap bytes only; no model, wheel query or runtime execution."}


def main():
    if len(sys.argv) == 7 and sys.argv[1] == "--download-worker":
        _, _, url, filename, digest, length, maximum = sys.argv
        path = Path(filename)
        if not path.name.startswith(".bootstrap-"):
            raise ValueError("Download worker requires its parent's unique temporary file")
        download_payload(checked_url(url), path, sha(digest),
                         None if length == "none" else size(int(length), MAX_ARCHIVE_BYTES),
                         size(int(maximum), MAX_ARCHIVE_BYTES))
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Only validate required cached files; never write or download")
    parser.add_argument("--bundle-dir", type=Path, default=DEFAULT_BUNDLE)
    args = parser.parse_args()
    try:
        result = stage(args.bundle_dir, check_only=args.check)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "verified" else 1
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"Bootstrap staging failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
