#!/usr/bin/env python3
"""Explicit selected-cache staging and bounded owned Ollama supervision.

No work happens on import. `stage` reads/copies the selected blobs; `launch`
starts the selected executable. Never invokes a client, pull, default endpoint,
or process inventory. Conventional credentials/config are lstat-only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import ctypes as C
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import time

SELECTION_SHA256 = "7de0ae35b3d231201679b2242484cb24a9122a8f9ce866b8554dfe6384a2d86a"
SELECTION_PATH = Path(__file__).resolve().parents[1] / "2026-10-13-reading-0.12.1/model-selection.json"
CHUNK = 1024 * 1024
MAX_LOG_BYTES = 16 * CHUNK
MAX_LINE_BYTES = 65536
PORT_PATTERN = re.compile(rb"Listening on 127\.0\.0\.1:(\d{1,5})(?=[\s\"\)]|$)")


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def metadata(path: Path) -> dict:
    """Do not read key/config contents, including for a hash."""
    try:
        s = path.lstat()
    except FileNotFoundError:
        return {"path": str(path), "exists": False}
    return {
        "path": str(path), "exists": True,
        "ordinaryFile": stat.S_ISREG(s.st_mode),
        "symlink": stat.S_ISLNK(s.st_mode),
        "device": str(s.st_dev), "inode": str(s.st_ino),
        "sizeBytes": s.st_size, "mtimeNs": str(s.st_mtime_ns),
        "ctimeNs": str(s.st_ctime_ns), "mode": format(stat.S_IMODE(s.st_mode), "04o"),
        "uid": s.st_uid,
    }


def ordinary_ancestors(path: Path) -> None:
    if not path.is_absolute():
        raise ValueError("An absolute path is required")
    for ancestor in reversed(path.parents):
        s = ancestor.lstat()
        if not stat.S_ISDIR(s.st_mode) or stat.S_ISLNK(s.st_mode):
            raise ValueError(f"Nonordinary ancestor: {ancestor}")


def open_read(path: Path):
    ordinary_ancestors(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError(f"Not an ordinary file: {path}")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    opened = os.fstat(fd)
    if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
        os.close(fd)
        raise ValueError(f"File identity changed at open: {path}")
    return os.fdopen(fd, "rb")


def hash_file(path: Path, maximum_bytes: int) -> dict:
    before = metadata(path)
    if before.get("sizeBytes", maximum_bytes + 1) > maximum_bytes:
        raise ValueError(f"File exceeds expected bound: {path}")
    digest = hashlib.sha256()
    count = 0
    with open_read(path) as stream:
        while block := stream.read(CHUNK):
            count += len(block)
            if count > maximum_bytes:
                raise ValueError(f"File grew past bound: {path}")
            digest.update(block)
    if metadata(path) != before:
        raise ValueError(f"File identity changed during read: {path}")
    return {**before, "sha256": digest.hexdigest(), "readBytes": count}


def read_json(path: Path, maximum_bytes: int = CHUNK) -> dict:
    with open_read(path) as stream:
        raw = stream.read(maximum_bytes + 1)
    if len(raw) > maximum_bytes:
        raise ValueError("JSON input exceeded bound")
    return json.loads(raw)


def write_json_new(path: Path, value: dict) -> None:
    ordinary_ancestors(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def load_selection() -> dict:
    identity = hash_file(SELECTION_PATH, CHUNK)
    if identity["sha256"] != SELECTION_SHA256:
        raise ValueError("Selection receipt changed; review and explicitly repin the helper")
    selection = read_json(SELECTION_PATH)
    if selection["selectedModel"]["tag"] != "gemma3:4b":
        raise ValueError("Unexpected selected model")
    return selection


def conventional_metadata(selection: dict) -> list:
    result = []
    for item in selection["conventionalOllamaMetadata"]:
        path = Path(item["path"])
        ordinary_ancestors(path)
        value = metadata(path)
        if value["exists"] and (not value["ordinaryFile"] or value["uid"] != os.getuid()):
            raise ValueError(f"Unexpected conventional key/config type or owner: {path}")
        if item["exists"] != value["exists"]:
            raise ValueError(f"Conventional key/config existence changed: {path}")
        if item["exists"] and any(value[k] != item[k] for k in ("mode", "uid", "sizeBytes")):
            raise ValueError(f"Conventional key/config metadata differs from selection: {path}")
        result.append(value)
    return result


def selected_files(selection: dict, destination: Path) -> list:
    model = selection["selectedModel"]
    manifest = model["manifest"]
    source_manifest = Path(model["manifestIdentity"]["path"])
    source_models = source_manifest.parents[4]
    files = [(source_manifest, destination / "manifests/registry.ollama.ai/library/gemma3/4b",
              model["manifestIdentity"]["sizeBytes"], model["manifestIdentity"]["sha256"])]
    refs = [manifest["config"], *manifest["layers"]]
    if len(refs) != 5:
        raise ValueError("Expected exactly five selected objects")
    for ref in refs:
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", ref["digest"]):
            raise ValueError("Invalid selected digest")
        name = ref["digest"].replace(":", "-")
        files.append((source_models / "blobs" / name, destination / "blobs" / name,
                      ref["size"], ref["digest"].split(":", 1)[1]))
    return files


def verify_expected(path: Path, size: int, digest: str) -> dict:
    identity = hash_file(path, size)
    if identity["readBytes"] != size or identity["sha256"] != digest:
        raise ValueError(f"Selected size/SHA-256 mismatch: {path}")
    return identity


def copy_exact(source: Path, destination: Path, size: int, digest: str) -> dict:
    """Ordinary byte copy; never a symlink/hard link to the shared cache."""
    before = metadata(source)
    ordinary_ancestors(destination)
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    hashed = hashlib.sha256()
    count = 0
    with os.fdopen(fd, "wb") as out, open_read(source) as inp:
        while block := inp.read(CHUNK):
            count += len(block)
            if count > size:
                raise ValueError(f"Source grew during copy: {source}")
            out.write(block)
            hashed.update(block)
        out.flush()
        os.fsync(out.fileno())
    if metadata(source) != before or count != size or hashed.hexdigest() != digest:
        raise ValueError(f"Source changed/mismatched during copy: {source}")
    copied = verify_expected(destination, size, digest)
    if (copied["device"], copied["inode"]) == (before["device"], before["inode"]):
        raise ValueError("Private copy unexpectedly shares the source inode")
    return {"source": before, "copied": copied}


def software_identity(selection: dict) -> dict:
    installed = selection["installedSoftware"]
    executable = Path(installed["resolvedExecutablePath"])
    if Path(installed["commandPath"]).resolve() != executable:
        raise ValueError("Selected command symlink resolution changed")
    plist = verify_expected(Path(installed["plistPath"]), installed["plistSizeBytes"], installed["plistSha256"])
    binary = hash_file(executable, 1024 * CHUNK)
    if not os.access(executable, os.X_OK):
        raise ValueError("Selected executable is not executable")
    return {"executable": binary, "plist": plist, "versionFromPlist": installed["CFBundleShortVersionString"]}


def stage(selection: dict) -> None:
    root = Path(selection["proposedLaunch"]["workingDirectory"])
    ordinary_ancestors(root)
    root.mkdir(mode=0o700)  # No exist_ok; never reuse or erase another run.
    try:
        credentials = conventional_metadata(selection)
        software = software_identity(selection)
        required = selection["selectedModel"]["declaredSelectedCopyBytesIncludingManifest"]
        if required >= selection["selectedModel"]["copyBudgetBytesExclusive"]:
            raise ValueError("Selected copy exceeds bound")
        if shutil.disk_usage(root).free < selection["resourceQualification"]["suggestedFreeDiskHeadroomBytes"]:
            raise ValueError("Less than the proposed 8 GiB free-disk headroom")
        models = root / "models"
        (models / "manifests/registry.ollama.ai/library/gemma3").mkdir(parents=True, mode=0o700)
        (models / "blobs").mkdir(mode=0o700)
        files = selected_files(selection, models)
        # Validate all selected inputs before copying any of them.
        validated = [verify_expected(source, size, digest) for source, _, size, digest in files]
        copied = [copy_exact(source, target, size, digest) for source, target, size, digest in files]
        if conventional_metadata(selection) != credentials:
            raise ValueError("Conventional key/config metadata changed during staging")
        write_json_new(root / "stage-receipt.json", {
            "format": "reservoir-owned-model-stage-v1", "completedAtUtc": utc(),
            "selectionSha256": SELECTION_SHA256, "software": software,
            "conventionalMetadataBefore": credentials, "conventionalMetadataAfter": credentials,
            "credentialCheckLimit": "lstat continuity only; no key/config content read or hash",
            "validatedSources": validated, "copies": copied, "copiedBytes": required,
            "rootIdentity": metadata(root), "launchExecuted": False,
        })
        print(json.dumps({"stage": "complete", "receipt": str(root / "stage-receipt.json")}))
    except BaseException as exc:
        write_json_new(root / "stage-failure.json", {"atUtc": utc(), "error": str(exc), "partialFilesPreserved": True})
        raise


def child_environment(selection: dict, inherited: dict) -> dict:
    env = {k: v for k, v in inherited.items()
           if not k.upper().startswith("OLLAMA_")
           and k.lower() not in {"http_proxy", "https_proxy", "all_proxy", "no_proxy"}}
    env.update(selection["proposedLaunch"]["environment"])
    if env.get("HOME") != inherited.get("HOME"):
        raise ValueError("HOME must remain unchanged")
    return env


def listener_port(line: bytes) -> int | None:
    match = PORT_PATTERN.search(line)
    if not match:
        return None
    port = int(match.group(1))
    if not 1 <= port <= 65535:
        raise ValueError("Invalid owned listener port")
    return port


def exited_without_reaping(child: subprocess.Popen) -> bool:
    # Keep the direct child waitable, even after an early exit. Its PID cannot
    # be recycled while we decide whether to signal its owned process group.
    status = os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    if status is not None and status.si_pid != child.pid:
        raise ValueError("Unexpected owned-child wait identity")
    return status is not None


class BSDInfo(C.Structure):
    # Public proc_bsdinfo ABI from the macOS SDK sys/proc_info.h.
    _fields_ = [(n, C.c_uint32) for n in ("flags", "status", "xstatus", "pid", "ppid", "uid", "gid", "ruid", "rgid", "svuid", "svgid", "reserved")] + [
        ("comm", C.c_char * 16), ("name", C.c_char * 32)] + [(n, C.c_uint32) for n in ("nfiles", "pgid", "jobc", "tdev", "tpgid")] + [
        ("nice", C.c_int32), ("start_seconds", C.c_uint64), ("start_microseconds", C.c_uint64)]


def darwin_group_members(pgid: int) -> list[dict]:
    """Only this known process group; no command lines, paths, or global listing."""
    if sys.platform != "darwin":
        raise ValueError("Owned group supervision requires qualified macOS libproc")
    lib = C.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    lib.proc_listpids.argtypes = [C.c_uint32, C.c_uint32, C.c_void_p, C.c_int]
    lib.proc_listpids.restype = C.c_int
    lib.proc_pidinfo.argtypes = [C.c_int, C.c_int, C.c_uint64, C.c_void_p, C.c_int]
    lib.proc_pidinfo.restype = C.c_int
    buffer = (C.c_int * 128)()
    C.set_errno(0)
    count = lib.proc_listpids(2, pgid, buffer, C.sizeof(buffer))  # PROC_PGRP_ONLY
    code = C.get_errno()
    if count < 0 or (count == 0 and code) or count >= C.sizeof(buffer) or count % C.sizeof(C.c_int):
        raise OSError(code or errno.EOVERFLOW, "proc_listpids exact group failed or exceeded128members")
    pids = sorted(pid for pid in list(buffer)[:count // C.sizeof(C.c_int)] if pid)
    if len(set(pids)) != len(pids):
        raise ValueError("Duplicate PID in owned group inventory")
    members = []
    for pid in pids:
        info = BSDInfo()
        C.set_errno(0)
        size = lib.proc_pidinfo(pid, 3, 0, C.byref(info), C.sizeof(info))  # PROC_PIDTBSDINFO
        if size != C.sizeof(info):
            raise OSError(C.get_errno() or errno.EIO, f"proc_pidinfo({pid}) identity unavailable")
        members.append({"pid": pid, "ppid": info.ppid, "pgid": info.pgid,
                        "sid": None if info.status == 5 else os.getsid(pid), "uid": info.uid, "realUid": info.ruid,
                        "savedUid": info.svuid, "status": info.status,
                        "startSeconds": str(info.start_seconds), "startMicroseconds": str(info.start_microseconds)})
    return members


def checked_owned_group(child: subprocess.Popen) -> dict:
    if child.returncode is not None:
        raise ValueError("Refusing group inspection after owned child was reaped")
    # Two matching bounded snapshots avoid acting on a changing/missing member.
    # Keep the waitable leader unreaped so this PGID cannot be recycled.
    for _ in range(3):
        try:
            before = darwin_group_members(child.pid)
            after = darwin_group_members(child.pid)
        except OSError as exc:
            if exc.errno == errno.ESRCH:
                continue  # A member exited while the selected group was read.
            raise
        if before != after:
            continue
        exited = exited_without_reaping(child)
        for member in after:
            # A zombie cannot act or acquire another session; getsid may no
            # longer expose it. Its public BSD group/UID/status still bind it.
            allowed_sessions = (None, child.pid) if member["status"] == 5 else (child.pid,)
            if (member["pgid"] != child.pid or member["sid"] not in allowed_sessions
                    or any(member[k] != os.getuid() for k in ("uid", "realUid", "savedUid"))
                    or member["status"] not in (1, 2, 3, 4, 5)):
                raise ValueError("Unknown/foreign owner, session, group, or status; no signal authorized")
        if not exited and not any(m["pid"] == child.pid for m in after):
            raise ValueError("Live owned leader missing from stable group inventory")
        return {"leaderExitedUnreaped": exited, "members": after,
                "quiescent": exited and all(m["status"] == 5 for m in after)}  # SZOMB
    raise ValueError("Owned group membership did not stabilize; no signal authorized")


def signal_owned_group(child: subprocess.Popen, sig: int, events: list | None = None) -> bool:
    events = events if events is not None else []
    snapshot = checked_owned_group(child)
    # Do not use killpg(...,0) for liveness: XNU filters zombie members and may
    # return EPERM when only our intentionally-unreaped leader remains.
    if sig == 0:
        return not snapshot["quiescent"]
    event = {"atUtc": utc(), "operation": "killpg", "pgid": child.pid,
             "signal": int(sig), "before": snapshot, "sent": False}
    events.append(event)
    if snapshot["quiescent"]:
        event["outcome"] = "already quiescent; no signal sent"
        return False
    try:
        os.killpg(child.pid, sig)
    except OSError as exc:
        event.update(errno=exc.errno, error=str(exc))
        if exc.errno in (errno.ESRCH, errno.EPERM):
            # A live group can become zombie-only between inspection and kill.
            # Never reinterpret EPERM without fresh, scoped read-only proof.
            after = checked_owned_group(child)
            event["afterError"] = after
            if after["quiescent"]:
                event["outcome"] = "quiescent after syscall error; no delivery claim"
                return False
        raise OSError(exc.errno, f"killpg({child.pid},{sig}) failed; owned cleanup incomplete") from exc
    event.update(sent=True, outcome="syscall accepted; quiescence still requires verification")
    return True


def cleanup_owned(child: subprocess.Popen, grace_seconds: float = 10, audit: dict | None = None) -> dict:
    """Keep the leader unreaped until the original group is proved quiescent."""
    result = audit if audit is not None else {}
    result.update(events=[], sigtermSentToOwnedGroup=False, sigkillSentToOwnedGroup=False)
    result["sigtermSentToOwnedGroup"] = signal_owned_group(child, signal.SIGTERM, result["events"])
    deadline = time.monotonic() + grace_seconds
    while signal_owned_group(child, 0):
        if time.monotonic() >= deadline:
            result["sigkillSentToOwnedGroup"] = signal_owned_group(child, signal.SIGKILL, result["events"])
            break
        time.sleep(0.1)
    deadline = time.monotonic() + 5
    while True:
        final = checked_owned_group(child)
        if final["quiescent"]:
            result["finalGroupBeforeReap"] = final
            break
        if time.monotonic() >= deadline:
            raise TimeoutError("Owned group still has live members after cleanup deadline; leader remains unreaped")
        time.sleep(0.1)
    # This is the only reaping operation, after the last group-directed action.
    child.wait(timeout=5)
    result["exitCode"] = child.returncode
    result["cleanupLimit"] = "Original owned process group verified quiescent before leader reap. Escaped descendants were not inventoried."
    return result


def read_pipe_ready(selector, pipe) -> bytes:
    block = os.read(pipe.fileno(), 8192)
    if not block:
        selector.unregister(pipe)  # EOF must not stay continuously readable.
    return block


def create_supervision_directory(path: Path, allowed_root: Path) -> Path:
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Supervision directory must be an explicit absolute owned path")
    try:
        relative = path.relative_to(allowed_root)
    except ValueError as exc:
        raise ValueError("Supervision directory must be under this desktop target/qa") from exc
    if not relative.parts:
        raise ValueError("Refusing the shared target/qa root as a supervision directory")
    ordinary_ancestors(path)
    path.mkdir(mode=0o700)  # Exclusive: preserve every prior launch and partial.
    return path


def launch(selection: dict, seconds: int, supervision_directory: Path) -> None:
    if not 1 <= seconds <= 900:
        raise ValueError("Owned lifetime must be between 1 and 900 seconds")
    if not all(hasattr(os, name) for name in ("waitid", "WNOWAIT", "WEXITED", "WNOHANG", "P_PID")):
        raise ValueError("This Python lacks non-reaping child waits; refusing unsafe supervision")
    root = Path(selection["proposedLaunch"]["workingDirectory"])
    ordinary_ancestors(root / "stage-receipt.json")
    staged = read_json(root / "stage-receipt.json")
    if staged.get("selectionSha256") != SELECTION_SHA256:
        raise ValueError("Staging receipt does not bind this selection")
    # Directory mtime/size naturally change as new owned artifacts appear.
    identity = metadata(root)
    if any(identity[k] != staged["rootIdentity"][k] for k in ("device", "inode", "uid", "mode")):
        raise ValueError("Owned staging directory identity changed")
    before = conventional_metadata(selection)
    if before != staged["conventionalMetadataAfter"]:
        raise ValueError("Conventional key/config metadata changed since staging")
    software = software_identity(selection)
    if software != staged["software"]:
        raise ValueError("Selected binary/version identity changed since staging")
    for _, target, size, digest in selected_files(selection, root / "models"):
        verify_expected(target, size, digest)
    cache_root = root
    root = create_supervision_directory(supervision_directory, Path(__file__).resolve().parents[2] / "target/qa")
    argv = selection["proposedLaunch"]["argv"]
    env = child_environment(selection, dict(os.environ))
    write_json_new(root / "launch-intent.json", {
        "atUtc": utc(), "argv": argv, "workingDirectory": str(root),
        "cacheDirectory": str(cache_root), "supervisionRootIdentity": metadata(root),
        "stageReceiptSha256": hashlib.sha256((cache_root / "stage-receipt.json").read_bytes()).hexdigest(),
        "selectionSha256": SELECTION_SHA256, "software": software,
        "childOverrides": selection["proposedLaunch"]["environment"],
        "homePreserved": True, "maximumLifetimeSeconds": seconds,
        "conventionalMetadataBefore": before,
    })
    stop = False
    def request_stop(_signum, _frame):
        nonlocal stop
        stop = True
    previous_handlers = {s: signal.signal(s, request_stop) for s in (signal.SIGINT, signal.SIGTERM)}
    child = None
    started = time.monotonic()
    reason = "supervision error"
    errors = []
    result = {}
    log_bytes = 0
    dropped_log_bytes = 0
    port = None
    pending = b""
    try:
        log_fd = os.open(root / "service.log", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(log_fd, "wb") as log:
            child = subprocess.Popen(argv, cwd=root, env=env, start_new_session=True,
                                     stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if os.getpgid(child.pid) != child.pid or os.getsid(child.pid) != child.pid:
                raise ValueError("Child did not acquire its own process session/group")
            result = {"pid": child.pid, "pgid": child.pid, "sid": child.pid,
                      "directChildOfSupervisorPid": os.getpid(), "spawnedAtUtc": utc(),
                      "spawnedAtMonotonicSeconds": started, "software": software}
            write_json_new(root / "owned-process.json", result)
            print(json.dumps({"ownedProcess": result, "stopRequestFile": str(root / "stop-request")}), flush=True)
            assert child.stdout is not None
            os.set_blocking(child.stdout.fileno(), False)
            selector = selectors.DefaultSelector()
            selector.register(child.stdout, selectors.EVENT_READ)
            try:
                while not exited_without_reaping(child):
                    elapsed = time.monotonic() - started
                    stop_meta = metadata(root / "stop-request")
                    if stop_meta["exists"] and not stop_meta["ordinaryFile"]:
                        raise ValueError("Stop request must be an ordinary owned file")
                    if stop or stop_meta["exists"] or elapsed >= seconds:
                        reason = "explicit stop" if stop or stop_meta["exists"] else "lifetime reached"
                        break
                    for _key, _mask in selector.select(timeout=0.2):
                        block = read_pipe_ready(selector, child.stdout)
                        if not block:
                            continue
                        kept = block[:max(0, MAX_LOG_BYTES - log_bytes)]
                        log.write(kept); log.flush()
                        log_bytes += len(kept); dropped_log_bytes += len(block) - len(kept)
                        pending += block
                        while b"\n" in pending:
                            line, pending = pending.split(b"\n", 1)
                            found = listener_port(line[:MAX_LINE_BYTES])
                            if found is not None:
                                if port is not None and found != port:
                                    raise ValueError("Owned listener log changed port unexpectedly")
                                if port is None:
                                    port = found
                                    endpoint = {"atUtc": utc(), "endpoint": f"http://127.0.0.1:{port}",
                                                "port": port, "pid": child.pid, "selectionSha256": SELECTION_SHA256,
                                                "source": "owned process listener log; no endpoint contacted"}
                                    write_json_new(root / "endpoint.json", endpoint)
                                    print(json.dumps(endpoint), flush=True)
                        if len(pending) > MAX_LINE_BYTES:
                            pending = pending[-MAX_LINE_BYTES:]
                if exited_without_reaping(child):
                    reason = "child exited"
            finally:
                selector.close()
    except BaseException as exc:
        errors.append(str(exc))
    finally:
        if child is not None:
            cleanup = {}
            try:
                cleanup_owned(child, audit=cleanup)
            except BaseException as exc:
                cleanup["failure"] = {"type": type(exc).__name__, "errno": getattr(exc, "errno", None), "message": str(exc)}
                errors.append(f"Owned cleanup: {exc}")
            finally:
                result["cleanup"] = cleanup
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
        # Metadata only, including after a service/startup failure.
        after = [metadata(Path(item["path"])) for item in selection["conventionalOllamaMetadata"]]
        if after != before:
            errors.append("Conventional key/config metadata changed; investigate before another launch")
        write_json_new(root / "supervision-result.json", {
            "format": "reservoir-owned-model-supervision-v1", "endedAtUtc": utc(),
            "elapsedMonotonicSeconds": time.monotonic() - started, "reason": reason,
            "selectionSha256": SELECTION_SHA256, "process": result, "endpointPort": port,
            "conventionalMetadataBefore": before, "conventionalMetadataAfter": after,
            "conventionalMetadataUnchanged": after == before,
            "credentialCheckLimit": "lstat continuity only; no key/config content read or hash",
            "retainedLogBytes": log_bytes, "discardedLogBytes": dropped_log_bytes,
            "errors": errors, "runtimeQualityOrMemoryQualification": False,
        })
    if errors:
        raise RuntimeError("; ".join(errors))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("stage", help="Validate and privately copy only the pinned selected cache")
    run = sub.add_parser("launch", help="Launch once from a completed stage receipt and supervise")
    run.add_argument("--seconds", type=int, default=900)
    run.add_argument("--supervision-directory", type=Path, required=True,
                     help="New absolute directory under desktop target/qa; pinned private model cache is revalidated and reused")
    args = parser.parse_args()
    selection = load_selection()
    if args.command == "stage":
        stage(selection)
    else:
        launch(selection, args.seconds, args.supervision_directory)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
