"""Prepare one pinned local activation runtime; never import MLX or infer.

Rust owns the process group and overall deadline. This driver additionally watches
its parent and terminates its own direct child if the parent disappears. Explicit
preparation may use HTTPS; inspection only reads assets and invokes a metadata-only
interpreter check. Progress is versioned JSON-lines, never terminal control output.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import ssl
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request


class SetupError(ValueError):
    pass


class Cancelled(SetupError):
    pass


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def relative_path(root, relative):
    path = Path(relative)
    if path.is_absolute() or not path.parts or any(p in (".", "..") for p in path.parts):
        raise SetupError("Asset path must be relative and remain inside its owned directory")
    result = root / path
    for component in [result, *result.parents]:
        if component == root.parent:
            break
        if component.is_symlink():
            raise SetupError(f"Unexpected symbolic link in setup assets: {component.name}")
    return result


def atomic_json(path, value):
    temporary = path.with_name(path.name + ".pending")
    if path.is_symlink() or temporary.is_symlink():
        raise SetupError("Refusing a symlink at a setup receipt boundary")
    with temporary.open("wb") as stream:
        stream.write(json_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def emit(phase, status="running", **fields):
    print(json.dumps({"schema": "activation-setup-progress-v1", "phase": phase,
                      "status": status, **fields}, ensure_ascii=False), flush=True)


def clean_environment(root):
    # No user Python/uv/pip configuration, authentication or mirror selection.
    # HOME retains its actual meaning; installer caches/config are separately owned.
    env = {key: os.environ[key] for key in ("HOME", "TMPDIR", "LANG", "LC_ALL") if key in os.environ}
    env.update({"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONNOUSERSITE": "1", "UV_NO_CONFIG": "1", "UV_PYTHON_DOWNLOADS": "never",
                "UV_CACHE_DIR": str(root / "download-cache"), "UV_NO_PROGRESS": "1",
                "UV_CREDENTIALS_DIR": str(root / "package-credentials"),
                "UV_KEYRING_PROVIDER": "disabled", "NETRC": "/dev/null",
                "XDG_CONFIG_HOME": str(root / "package-config"),
                "XDG_DATA_HOME": str(root / "package-data"),
                "UV_HTTP_TIMEOUT": "60", "UV_HTTP_RETRIES": "0"})
    return env


class Supervisor:
    def __init__(self, parent_pid=None, parent_getter=os.getppid):
        self.cancelled = threading.Event()
        self.child = None
        self.child_lock = threading.Lock()
        self.parent_pid = parent_pid
        self.parent_getter = parent_getter
        self.done = threading.Event()
        self.watcher = None

    def check(self):
        if self.cancelled.is_set():
            raise Cancelled("Preparation stopped; verified files and owned partial downloads were retained")
        if self.parent_pid is not None and self.parent_getter() != self.parent_pid:
            self.cancelled.set()
            raise Cancelled("The application closed; preparation was stopped")

    def start_watch(self):
        def watch():
            while not self.done.wait(0.25):
                if self.parent_pid is not None and self.parent_getter() != self.parent_pid:
                    self.cancelled.set()
                if self.cancelled.is_set():
                    with self.child_lock:
                        child = self.child
                    if child is not None and child.poll() is None:
                        child.terminate()
                        deadline = time.monotonic() + 5
                        while child.poll() is None and time.monotonic() < deadline:
                            time.sleep(0.05)
                        if child.poll() is None:
                            child.kill()
                    return
        self.watcher = threading.Thread(target=watch, daemon=True)
        self.watcher.start()

    def run(self, command, root, *, input_data=None):
        self.check()
        with self.child_lock:
            self.child = subprocess.Popen(command, stdin=subprocess.PIPE if input_data is not None else subprocess.DEVNULL,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=root, env=clean_environment(root))
            child = self.child
        try:
            self.check()
            try:
                stdout, stderr = child.communicate(input=input_data, timeout=1200)
            except subprocess.TimeoutExpired:
                child.terminate()
                try:
                    child.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.communicate()
                raise SetupError("A setup subprocess exceeded its bounded deadline")
            self.check()
            if child.returncode:
                detail = stderr[-12000:].decode("utf-8", errors="replace")
                raise SetupError(f"Setup subprocess failed ({child.returncode}): {detail}")
            return stdout
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)
            with self.child_lock:
                self.child = None

    def close(self):
        self.done.set()
        if self.watcher:
            self.watcher.join(timeout=1)


RUNTIME_PROBE = r'''
import importlib.metadata as m, json, platform, sys
expected = json.load(sys.stdin)
versions = {item['name']: m.version(item['name']) for item in expected['wheels']}
if any(versions[item['name']] != item['version'] for item in expected['wheels']):
    raise ValueError('Installed packages differ from the frozen dependency versions')
if platform.python_version() != expected['pythonVersion']:
    raise ValueError('Python differs from the qualified pinned version')
print(json.dumps({'pythonVersion': platform.python_version(), 'architecture': platform.machine(), 'versions': versions}))
'''


class Setup:
    def __init__(self, root, resources, supervisor, reporter=emit):
        if root.is_symlink() or resources.is_symlink():
            raise SetupError("Setup and resource roots must not be symbolic links")
        self.root, self.resources = root.resolve(), resources.resolve(strict=True)
        self.supervisor, self.report = supervisor, reporter
        self.manifest_path = relative_path(self.resources, "setup-manifest.json")
        self.manifest = json.loads(self.manifest_path.read_text())
        if self.manifest.get("schema") != "activation-setup-manifest-v1":
            raise SetupError("Unsupported setup manifest")
        self.manifest_sha = digest(self.manifest_path)
        self.runtime_id = self.manifest["runtimeId"]
        if not re.fullmatch(r"[a-zA-Z0-9._-]{1,160}", self.runtime_id):
            raise SetupError("Invalid setup runtime identity")
        self.runtime = relative_path(self.root, "runtime/" + self.runtime_id)
        self.python = relative_path(self.runtime, self.manifest["python"]["executableRelativePath"])
        self.venv = self.runtime / "venv"
        # A venv interpreter is an expected symlink to its owned standalone Python.
        self.venv_python = self.venv / "bin/python"
        self.uv = relative_path(self.resources, self.manifest["uv"]["path"])
        self.locks = {}
        for key, entry in self.manifest["locks"].items():
            path = relative_path(self.resources, entry["path"])
            if digest(path) != entry["sha256"]:
                raise SetupError(f"Packaged {key} lock differs from the setup manifest")
            self.locks[key] = path
        self.wheels = json.loads(self.locks["wheelInventory"].read_text())["wheels"]
        self.model_spec = json.loads(self.locks["model"].read_text())
        revision = self.model_spec["revision"]
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise SetupError("Invalid pinned model revision")
        self.model = relative_path(self.root, "models/" + revision)
        self.ready = relative_path(self.root, "ready.json")

    def check_platform(self):
        spec = self.manifest["platform"]
        if platform.system() != spec["system"] or platform.machine() != spec["architecture"]:
            raise SetupError("Activation setup requires an Apple Silicon Mac running natively")
        major = int(platform.mac_ver()[0].split(".")[0] or 0)
        if major < spec["minimumMacOSMajor"]:
            raise SetupError(f"Activation setup requires macOS {spec['minimumMacOSMajor']} or later")
        if platform.python_version() != self.manifest["python"]["version"]:
            raise SetupError("Setup must run with its bundled pinned Python interpreter")
        if Path(sys.executable).resolve() != self.python.resolve(strict=True):
            raise SetupError("Setup must use the owned standalone interpreter at its final path")

    def validate_runtime(self):
        if not self.venv_python.is_file():
            raise SetupError("The activation environment has not been prepared")
        if not self.venv_python.resolve().is_relative_to(self.runtime):
            raise SetupError("The activation interpreter points outside its owned runtime")
        expected = {"wheels": self.wheels, "pythonVersion": self.manifest["python"]["version"]}
        result = self.supervisor.run([str(self.venv_python), "-I", "-B", "-c", RUNTIME_PROBE], self.root,
                                     input_data=json.dumps(expected).encode())
        return json.loads(result)

    def validate_model(self):
        self.supervisor.check()
        for item in self.model_spec["files"]:
            path = relative_path(self.model, item["path"])
            if not path.is_file() or path.stat().st_size != item["bytes"] or digest(path) != item["sha256"]:
                raise SetupError(f"Model asset needs attention: {item['path']}")
            self.supervisor.check()
        provenance = relative_path(self.model, "model-provenance.json")
        if not provenance.is_file() or json.loads(provenance.read_text()) != self.model_spec["provenance"]:
            raise SetupError("Model provenance differs from the frozen inventory")
        expected = {f["path"] for f in self.model_spec["files"]} | {"model-provenance.json", ".setup-owner"}
        present = {str(path.relative_to(self.model)) for path in self.model.rglob("*") if path.is_file()}
        if present != expected:
            raise SetupError("Model directory contains unexpected or incomplete files")
        return digest(provenance)

    def inspect(self):
        self.check_platform()
        if not self.ready.is_file():
            raise SetupError("Activation setup is not ready")
        try:
            receipt = json.loads(self.ready.read_text())
            if not isinstance(receipt, dict):
                raise SetupError("Setup receipt is not an object")
            if receipt.get("schema") != "activation-setup-ready-v1" or receipt.get("manifestSha256") != self.manifest_sha:
                raise SetupError("Setup receipt belongs to a different preview runtime")
            if receipt.get("pythonPath") != str(self.venv_python) or receipt.get("modelPath") != str(self.model):
                raise SetupError("Setup receipt paths differ from the owned installation")
            self.validate_runtime()
            if self.validate_model() != receipt.get("modelProvenanceSha256"):
                raise SetupError("Model provenance changed after preparation")
            return receipt
        except Cancelled:
            raise
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise SetupError(f"Prepared installation failed validation: {error}. Prepared files and the readiness receipt "
                             "are preserved. This is not an interrupted preparation; Resume cannot repair it. "
                             "Contact the preview maintainer with this diagnostic.") from error

    def prepare_environment(self):
        self.report("environment", message="Preparing the pinned Python packages")
        if digest(self.uv) != self.manifest["uv"]["sha256"]:
            raise SetupError("Bundled package installer differs from the manifest")
        if self.venv.is_symlink():
            raise SetupError("Refusing a symlink at the owned environment path")
        marker = relative_path(self.runtime, ".environment-owner")
        owner = {"schema": "activation-setup-environment-owner-v1", "runtimeId": self.runtime_id,
                 "manifestSha256": self.manifest_sha}
        if marker.exists():
            if json.loads(marker.read_text()) != owner:
                raise SetupError("Environment ownership differs from this preview runtime")
        elif self.venv.exists():
            raise SetupError("Existing environment has no matching setup ownership receipt")
        else:
            # Mark ownership before uv creates anything, so an interrupted venv
            # creation can be safely rebuilt by the next explicit Prepare action.
            atomic_json(marker, owner)
        if self.venv.exists() and (not self.venv_python.exists() or not (self.venv / "pyvenv.cfg").is_file()):
            self.report("environment", message="Rebuilding the interrupted owned Python environment")
            shutil.rmtree(self.venv)
        if not self.venv.exists():
            self.supervisor.run([str(self.uv), "--no-config", "venv", "--python", str(self.python),
                                 "--no-python-downloads", str(self.venv)], self.root)
        self.supervisor.run([str(self.uv), "--no-config", "pip", "sync", "--python", str(self.venv_python),
                             "--no-python-downloads", "--require-hashes", "--only-binary", ":all:",
                             "--default-index", "https://pypi.org/simple", "--link-mode", "copy",
                             str(self.locks["wheels"])], self.root)
        return self.validate_runtime()

    def download_model_file(self, item, opener=None):
        # No ambient proxy credentials or provider clients; this setup-only HTTPS
        # opener follows the pinned Hugging Face download's CDN redirects.
        if opener is None:
            minor = ".".join(self.manifest["python"]["version"].split(".")[:2])
            ca_file = self.venv / f"lib/python{minor}/site-packages/certifi/cacert.pem"
            context = ssl.create_default_context(cafile=ca_file)
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                                urllib.request.HTTPSHandler(context=context)).open
        destination = relative_path(self.model, item["path"])
        partial = relative_path(self.model, item["path"] + ".download")
        if destination.exists():
            if destination.stat().st_size == item["bytes"] and digest(destination) == item["sha256"]:
                return
            self.retain_failed_download(destination)
            raise SetupError(f"Existing model file has a different hash: {item['path']}. The failed bytes were retained; prepare again to fetch a fresh copy.")
        offset = partial.stat().st_size if partial.exists() else 0
        if offset > item["bytes"]:
            self.retain_failed_download(partial)
            raise SetupError(f"Partial model file exceeds its expected size: {item['path']}. Prepare again to fetch a fresh copy.")
        if offset < item["bytes"]:
            request = urllib.request.Request(item["url"], headers={"User-Agent": "ReservoirScope-activation-setup/1",
                                                                  "Accept-Encoding": "identity"})
            if offset:
                request.add_header("Range", f"bytes={offset}-")
            self.supervisor.check()
            with opener(request, timeout=30) as response:
                if not response.geturl().startswith("https://"):
                    raise SetupError("Model download redirected away from HTTPS")
                status = response.status
                if status == 206:
                    content_range = response.headers.get("Content-Range", "")
                    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", content_range)
                    if not match or int(match[1]) != offset or int(match[3]) != item["bytes"]:
                        raise SetupError("Resumed model response has an unexpected byte range")
                elif status == 200:
                    offset = 0  # A server may ignore Range; start this owned partial again.
                else:
                    raise SetupError(f"Model download returned HTTP {status}")
                with partial.open("ab" if offset else "wb") as stream:
                    last_report = 0.0
                    while True:
                        self.supervisor.check()
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        offset += len(chunk)
                        if offset > item["bytes"]:
                            raise SetupError("Model download exceeded its frozen size")
                        stream.write(chunk)
                        now = time.monotonic()
                        if now - last_report >= 0.25:
                            self.report("model", file=item["path"], downloadedBytes=offset, totalBytes=item["bytes"])
                            last_report = now
                    stream.flush()
                    os.fsync(stream.fileno())
        self.supervisor.check()
        if partial.stat().st_size != item["bytes"] or digest(partial) != item["sha256"]:
            # A short response remains resumable. Complete wrong bytes cannot be
            # resumed; retain them separately so a new explicit attempt can fetch
            # a fresh copy without requiring filesystem edits in Terminal.
            if partial.stat().st_size == item["bytes"]:
                self.retain_failed_download(partial)
            raise SetupError(f"Downloaded model asset failed its frozen hash: {item['path']}. The failed attempt was retained; prepare again to continue.")
        os.replace(partial, destination)

    def retain_failed_download(self, path):
        failures = relative_path(self.root, "model-download-failures")
        failures.mkdir(parents=True, exist_ok=True)
        target = relative_path(failures, f"{time.time_ns()}-{path.name}")
        os.replace(path, target)

    def prepare_model(self):
        owner = {"schema": "activation-setup-model-owner-v1", "modelLockSha256": self.manifest["locks"]["model"]["sha256"]}
        # This marker precedes directory creation, closing the crash window
        # between mkdir and the in-directory marker's atomic publication.
        owner_root = relative_path(self.root, "model-owners")
        owner_root.mkdir(parents=True, exist_ok=True)
        outer_marker = relative_path(owner_root, self.model_spec["revision"] + ".json")
        if outer_marker.exists():
            if json.loads(outer_marker.read_text()) != owner:
                raise SetupError("Model directory belongs to different frozen assets")
        elif self.model.exists():
            raise SetupError("Model directory is not an owned resumable download for these assets")
        else:
            atomic_json(outer_marker, owner)
        # No .json suffix: the worker intentionally refuses any unmanifested model
        # JSON/tokenizer file. This ownership marker is preparation metadata only.
        marker = relative_path(self.model, ".setup-owner")
        if self.model.exists():
            if not marker.is_file() and set(p.name for p in self.model.iterdir()).issubset({".setup-owner.pending"}):
                atomic_json(marker, owner)
            elif not marker.is_file() or json.loads(marker.read_text()) != owner:
                raise SetupError("Model directory is not an owned resumable download for these assets")
        else:
            self.model.mkdir(parents=True)
            atomic_json(marker, owner)
        allowed = {f["path"] for f in self.model_spec["files"]}
        allowed |= {f["path"] + ".download" for f in self.model_spec["files"]}
        allowed |= {".setup-owner", "model-provenance.json", "model-provenance.json.pending"}
        if any(str(p.relative_to(self.model)) not in allowed or p.is_symlink() for p in self.model.rglob("*")):
            raise SetupError("Owned model staging contains unexpected files")
        self.report("model", message="Downloading and verifying the pinned Qwen3 model")
        for item in self.model_spec["files"]:
            self.download_model_file(item)
        atomic_json(relative_path(self.model, "model-provenance.json"), self.model_spec["provenance"])
        return self.validate_model()

    def prepare(self):
        self.check_platform()
        self.root.mkdir(parents=True, exist_ok=True)
        lock_path = relative_path(self.root, "setup.lock")
        with lock_path.open("a+b") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise SetupError("Another activation preparation is already running")
            self.supervisor.check()
            if self.ready.exists():
                receipt = self.inspect()
                self.report("ready", "complete", receiptPath=str(self.ready), receipt=receipt)
                return receipt
            if shutil.disk_usage(self.root).free < self.manifest["minimumFreeBytes"]:
                raise SetupError("Activation preparation needs at least 8 GiB of available disk space")
            self.prepare_environment()
            provenance_sha = self.prepare_model()
            self.report("verification", message="Checking the complete installed runtime and model inventory")
            runtime = self.validate_runtime()
            self.supervisor.check()
            receipt = {"schema": "activation-setup-ready-v1", "runtimeId": self.runtime_id,
                       "manifestSha256": self.manifest_sha, "pythonPath": str(self.venv_python),
                       "modelPath": str(self.model), "modelProvenanceSha256": provenance_sha,
                       "lockSha256": self.manifest["locks"]["wheels"]["sha256"],
                       "completedAtUtc": utc_now(), "runtime": runtime}
            atomic_json(self.ready, receipt)
            # Receipt publication is the completion boundary. A later cancellation
            # cannot turn this verified installation back into a partial download.
            self.report("ready", "complete", receiptPath=str(self.ready), receipt=receipt)
            return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup-root", required=True, type=Path)
    parser.add_argument("--resources", required=True, type=Path)
    parser.add_argument("--parent-pid", required=True, type=int)
    parser.add_argument("--mode", choices=("prepare", "inspect"), default="prepare")
    args = parser.parse_args()
    supervisor = Supervisor(args.parent_pid)
    old_handlers = {sig: signal.signal(sig, lambda *_: supervisor.cancelled.set()) for sig in (signal.SIGTERM, signal.SIGINT)}
    supervisor.start_watch()
    try:
        setup = Setup(args.setup_root, args.resources, supervisor)
        if args.mode == "prepare":
            setup.prepare()
        else:
            receipt = setup.inspect()
            emit("ready", "complete", receiptPath=str(setup.ready), receipt=receipt)
    except (SetupError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        emit("cancelled" if isinstance(error, Cancelled) else "failed", "cancelled" if isinstance(error, Cancelled) else "failed",
             diagnostic=str(error))
        raise SystemExit(130 if isinstance(error, Cancelled) else 1)
    finally:
        supervisor.close()
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)
