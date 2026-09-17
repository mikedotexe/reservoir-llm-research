"""Private, manifest-verified research snapshots. Never follows provenance paths."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

SCHEMA = "reservoir-research-archive-v1"
EXCLUDED = {".build", ".swiftpm", ".venv", "__pycache__", ".pytest_cache", ".research"}


class ArchiveError(RuntimeError):
    pass


def _sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _relative(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ArchiveError("Invalid archive path")
    p = Path(value)
    if p.is_absolute() or any(x in ("..", ".", "") for x in value.split("/")):
        raise ArchiveError("Unsafe archive path")
    return p


def _link(root, path, target):
    if not isinstance(target, str) or Path(target).is_absolute():
        raise ArchiveError("Only internal relative links can be archived")
    try:
        resolved = (path.parent / target).resolve()
        resolved.relative_to(root.resolve())
    except (ValueError, RuntimeError, OSError) as e:
        raise ArchiveError("Link escapes archive or forms a cycle") from e


def inventory(root, *, excluded=EXCLUDED):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ArchiveError("Source directory is unavailable")
    result = []
    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in excluded)
        for name in sorted(dirs + files):
            if name in excluded:
                continue
            p = Path(base) / name
            s = p.lstat()
            rel = str(p.relative_to(root))
            mode = stat.S_IMODE(s.st_mode) & 0o700
            if stat.S_ISLNK(s.st_mode):
                target = os.readlink(p)
                _link(root, p, target)
                result.append(dict(path=rel, kind="symlink", target=target))
                if name in dirs:
                    dirs.remove(name)
            elif stat.S_ISDIR(s.st_mode):
                result.append(dict(path=rel, kind="directory", mode=mode | 0o700))
            elif stat.S_ISREG(s.st_mode):
                digest = _sha(p)
                after = p.stat()
                if (s.st_size, s.st_mtime_ns, s.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
                    raise ArchiveError("Source changed while reading: " + rel)
                result.append(dict(path=rel, kind="file", size=s.st_size, sha256=digest, mode=mode | 0o400))
            else:
                raise ArchiveError("Unsupported special file: " + rel)
    return sorted(result, key=lambda e: e["path"])


def _save(path, value):
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    path.chmod(0o600)


def _check_tree(tree, entries):
    if not isinstance(entries, list):
        raise ArchiveError("Invalid entry inventory")
    paths = set()
    for e in entries:
        if not isinstance(e, dict):
            raise ArchiveError("Invalid archive entry")
        rel = _relative(e.get("path"))
        if str(rel) in paths:
            raise ArchiveError("Duplicate archive path")
        paths.add(str(rel))
        p = tree / rel
        for parent in rel.parents:
            if parent != Path(".") and (tree / parent).is_symlink():
                raise ArchiveError("Archive entry traverses a symlink")
        kind = e.get("kind")
        if kind != "symlink" and p.exists() and stat.S_IMODE(p.lstat().st_mode) & 0o077:
            raise ArchiveError("Archive permissions are not private: " + str(rel))
        if kind in ("file", "directory") and (type(e.get("mode")) is not int or e["mode"] & ~0o700 or not e["mode"] & 0o400):
            raise ArchiveError("Invalid private archive mode")
        if kind == "file" and (type(e.get("size")) is not int or e["size"] < 0):
            raise ArchiveError("Invalid archive file size")
        if kind == "symlink":
            _link(tree, p, e.get("target"))
            if not p.is_symlink() or os.readlink(p) != e["target"]:
                raise ArchiveError("Link differs: " + str(rel))
        elif kind == "directory":
            if p.is_symlink() or not p.is_dir():
                raise ArchiveError("Directory differs: " + str(rel))
        elif kind == "file":
            if p.is_symlink() or not p.is_file() or p.stat().st_size != e.get("size") or _sha(p) != e.get("sha256"):
                raise ArchiveError("File differs: " + str(rel))
        else:
            raise ArchiveError("Unknown archive entry kind")
    actual = set()
    for base, dirs, files in os.walk(tree, followlinks=False):
        for name in dirs + files:
            actual.add(str((Path(base) / name).relative_to(tree)))
    if actual != paths:
        raise ArchiveError("Archive has missing or unlisted entries")


def verify(snapshot):
    snapshot = Path(snapshot).resolve()
    try:
        manifest = json.loads((snapshot / "manifest.json").read_text())
    except (OSError, ValueError) as e:
        raise ArchiveError("Archive manifest is unavailable or invalid") from e
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA or manifest.get("status") != "complete":
        raise ArchiveError("Unsupported or incomplete archive")
    tree = snapshot / "tree"
    if tree.is_symlink() or not tree.is_dir():
        raise ArchiveError("Archive tree is unavailable")
    _check_tree(tree, manifest.get("entries"))
    entries = manifest["entries"]
    return dict(status="verified", schema=SCHEMA, entries=len(entries),
                files=sum(e["kind"] == "file" for e in entries),
                bytes=sum(e.get("size", 0) for e in entries),
                manifest_sha256=_sha(snapshot / "manifest.json"))


def snapshot(source, destination):
    source = Path(source).resolve()
    destination = Path(destination).parent.resolve() / Path(destination).name
    if destination.exists() or destination.is_symlink():
        raise ArchiveError("Snapshot destination already exists")
    if destination.is_relative_to(source):
        raise ArchiveError("Snapshot destination must be outside source")
    entries = inventory(source)
    destination.mkdir(parents=True, mode=0o700)
    destination.chmod(0o700)
    tree = destination / "tree"
    tree.mkdir(mode=0o700)
    _save(destination / "started.json", dict(schema=SCHEMA, status="incomplete", source=str(source), excluded=sorted(EXCLUDED)))
    try:
        _copy(source, tree, entries)
        if inventory(source) != entries:
            raise ArchiveError("Source changed during snapshot; incomplete copy preserved")
        _check_tree(tree, entries)
        _save(destination / "manifest.json", dict(schema=SCHEMA, status="complete", source_provenance=str(source), excluded=sorted(EXCLUDED), entries=entries))
        return verify(destination)
    except (OSError, ValueError) as e:
        raise ArchiveError("Snapshot failed; incomplete files preserved: " + str(e)) from e


def _copy(source, target, entries):
    for e in entries:
        rel = _relative(e["path"])
        p = target / rel
        if e["kind"] == "directory":
            p.mkdir(parents=True, exist_ok=True, mode=0o700)
        else:
            p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            if e["kind"] == "symlink":
                _link(target, p, e["target"])
                p.symlink_to(e["target"])
            else:
                with (source / rel).open("rb") as src, p.open("xb") as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)
                p.chmod(e["mode"] & 0o700)


def restore(snapshot, destination):
    snapshot = Path(snapshot).resolve()
    destination = Path(destination).parent.resolve() / Path(destination).name
    result = verify(snapshot)
    if destination.exists() or destination.is_symlink():
        raise ArchiveError("Restore destination already exists")
    if destination.is_relative_to(snapshot):
        raise ArchiveError("Restore destination must be outside snapshot")
    manifest = json.loads((snapshot / "manifest.json").read_text())
    destination.mkdir(parents=True, mode=0o700)
    destination.chmod(0o700)
    try:
        _copy(snapshot / "tree", destination, manifest["entries"])
        _check_tree(destination, manifest["entries"])
    except OSError as e:
        raise ArchiveError("Restore failed; partial destination preserved: " + str(e)) from e
    return dict(result, status="restored", destination=str(destination))
