#!/usr/bin/env python3
"""Remove only this desktop's rebuildable incremental cache, preserving evidence."""
from pathlib import Path
import datetime as dt
import fcntl
import hashlib
import json
import os
import shutil
import stat

HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1]
CACHE = DESKTOP / "target/debug/incremental"


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_new(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def inventory(roots):
    result = {}
    pending = list(roots)
    while pending:
        path = pending.pop()
        if path == HERE:
            continue  # New concurrent episode documents are not historical inputs.
        st = path.lstat()
        if stat.S_ISDIR(st.st_mode):
            pending.extend(path.iterdir())
        elif stat.S_ISREG(st.st_mode):
            with path.open("rb") as stream:
                sha = hashlib.file_digest(stream, "sha256").hexdigest()
            result[str(path.relative_to(DESKTOP))] = {"bytes": st.st_size, "sha256": sha}
        elif stat.S_ISLNK(st.st_mode):
            result[str(path.relative_to(DESKTOP))] = {"link": os.readlink(path)}
        else:
            raise ValueError(f"Unexpected protected file kind: {path}")
    return result


def main():
    # Do not follow a replaced cache or ancestor outside the owned checkout.
    for path in (CACHE, *CACHE.parents):
        if not stat.S_ISDIR(path.lstat().st_mode):
            raise ValueError(f"Nonordinary directory: {path}")
    lock = CACHE.parent / ".cargo-lock"
    fd = os.open(lock, os.O_RDWR | os.O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        files = []
        for path in CACHE.rglob("*"):
            st = path.lstat()
            if stat.S_ISDIR(st.st_mode):
                continue
            if (not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid()
                    or path.suffix not in {".o", ".bin", ".lock", ".rmeta"}):
                raise ValueError(f"Unexpected incremental cache member: {path}")
            files.append({"path": str(path.relative_to(CACHE)), "bytes": st.st_size})
        protected_roots = [DESKTOP / "validation", DESKTOP / "target/qa", DESKTOP / "target/release/bundle"]
        before = inventory(protected_roots)
        write_new("cleanup-protected-before.json", before)
        free_before = shutil.disk_usage(DESKTOP).free
        write_new("cleanup-intent.json", {
            "atUtc": utc(), "authorization": "User requested safe disk cleanup preserving all evidence and the Beings.",
            "onlyRemoval": str(CACHE), "cacheFiles": files, "cacheLogicalBytes": sum(x["bytes"] for x in files),
            "protectedFileCount": len(before), "freeDiskBytesBefore": free_before,
            "guard": "Exclusive existing Cargo debug lock held; ordinary owned cache members only.",
            "noProcessControl": True,
        })
        shutil.rmtree(CACHE)
        after = inventory(protected_roots)
        changes = [name for name in before.keys() | after.keys() if before.get(name) != after.get(name)]
        free_after = shutil.disk_usage(DESKTOP).free
        receipt = {"atUtc": utc(), "removedOnly": str(CACHE), "cacheAbsent": not CACHE.exists(),
                   "removedCacheFiles": len(files), "logicalBytesRemoved": sum(x["bytes"] for x in files),
                   "freeDiskBytesBefore": free_before, "freeDiskBytesAfter": free_after,
                   "observedFreeDiskIncreaseBytes": free_after - free_before,
                   "diskDeltaLimit": "Concurrent filesystem activity and APFS allocation may affect the observed free-space delta.",
                   "protectedFileCount": len(before), "protectedIdentitiesUnchanged": not changes,
                   "changedProtectedPaths": changes, "status": "passed" if not changes and not CACHE.exists() else "failed",
                   "noAppsOrServicesStopped": True, "noModelRequests": True}
        write_new("cleanup-result.json", receipt)
        print(json.dumps(receipt))
    finally:
        os.close(fd)


if __name__ == "__main__":
    main()
