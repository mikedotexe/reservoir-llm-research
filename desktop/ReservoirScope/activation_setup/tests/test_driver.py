"""Synthetic setup lifecycle tests. No real packages, network or model calls."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from activation_setup.driver import (Cancelled, Setup, SetupError, Supervisor,
                                     atomic_json, clean_environment, digest,
                                     json_bytes, relative_path)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class FakeSupervisor:
    def __init__(self):
        self.cancelled = False
        self.commands = []

    def check(self):
        if self.cancelled:
            raise Cancelled("cancelled")

    def run(self, command, root, input_data=None):
        self.check()
        self.commands.append(command)
        if "venv" in command:
            target = Path(command[-1]) / "bin/python"
            target.parent.mkdir(parents=True)
            target.symlink_to(Path(command[command.index("--python") + 1]))
            (Path(command[-1]) / "pyvenv.cfg").write_text("synthetic owned environment")
        return b'{"pythonVersion":"3.12.13","architecture":"arm64","versions":{"sample":"1.0"}}'


class Response(io.BytesIO):
    def __init__(self, body, status=200, headers=None, url="https://cdn.example/file"):
        super().__init__(body)
        self.status = status
        self.headers = headers or {}
        self.url = url

    def geturl(self):
        return self.url


class Fixture:
    def __init__(self, directory):
        self.root = directory / "user local setup"
        self.resources = directory / "resources"
        self.resources.mkdir()
        (self.resources / "uv").write_bytes(b"synthetic installer")
        self.contents = {"config.json": b'{"model_type":"qwen3"}', "tokenizer.json": b'{}',
                         "model.safetensors": b"synthetic weights"}
        files = [{"path": name, "sha256": sha(data), "bytes": len(data), "url": "https://example.test/" + name}
                 for name, data in self.contents.items()]
        self.provenance = {"modelId": "synthetic", "revision": "1" * 40,
                           "files": [{"path": row["path"], "sha256": row["sha256"]} for row in files]}
        model = {**self.provenance, "files": files, "provenance": self.provenance}
        locks = {"model": ("model.json", json_bytes(model)),
                 "wheelInventory": ("wheels.json", json_bytes({"wheels": [{"name": "sample", "version": "1.0"}]})),
                 "wheels": ("wheels.lock", b"sample==1.0 --hash=sha256:synthetic\n")}
        for name, data in locks.values():
            (self.resources / name).write_bytes(data)
        self.manifest = {"schema": "activation-setup-manifest-v1", "runtimeId": "test-runtime",
                         "platform": {"system": "Darwin", "architecture": "arm64", "minimumMacOSMajor": 26},
                         "python": {"version": "3.12.13", "executableRelativePath": "python/bin/python3.12"},
                         "uv": {"path": "uv", "sha256": sha(b"synthetic installer")}, "minimumFreeBytes": 0,
                         "locks": {key: {"path": name, "sha256": sha(data)} for key, (name, data) in locks.items()}}
        self.write_manifest()
        self.supervisor = FakeSupervisor()
        self.events = []
        self.setup = Setup(self.root, self.resources, self.supervisor,
                           reporter=lambda *args, **kwargs: self.events.append((args, kwargs)))
        self.setup.python.parent.mkdir(parents=True)
        self.setup.python.write_bytes(b"synthetic Python")

    def write_manifest(self):
        (self.resources / "setup-manifest.json").write_bytes(json_bytes(self.manifest))

    def prepare(self):
        def write_model(item):
            (self.setup.model / item["path"]).write_bytes(self.contents[item["path"]])
        with patch.object(self.setup, "check_platform"), patch.object(self.setup, "download_model_file", side_effect=write_model):
            return self.setup.prepare()


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.fixture = Fixture(Path(self.temporary.name).resolve())

    def tearDown(self):
        self.temporary.cleanup()

    def test_prepare_uses_final_paths_hashes_no_python_downloads_and_atomic_receipt(self):
        f = self.fixture
        receipt = f.prepare()
        self.assertEqual(receipt["manifestSha256"], digest(f.resources / "setup-manifest.json"))
        self.assertEqual(receipt["pythonPath"], str(f.setup.venv_python))
        self.assertEqual(json.loads(f.setup.ready.read_text()), receipt)
        self.assertFalse(f.setup.ready.with_name("ready.json.pending").exists())
        command = next(c for c in f.supervisor.commands if "sync" in c)
        self.assertIn("--require-hashes", command)
        self.assertIn("--only-binary", command)
        self.assertIn("--no-python-downloads", command)
        self.assertIn(str(f.setup.venv_python), command)
        self.assertEqual(f.events[-1][0], ("ready", "complete"))

    def test_repeat_and_inspect_are_read_only_and_do_not_install_again(self):
        f = self.fixture
        f.prepare()
        def inventory():
            return {str(p.relative_to(f.root)): (digest(p), p.stat().st_mtime_ns)
                    for p in f.root.rglob("*") if p.is_file() and p.name != "setup.lock"}
        before = inventory()
        commands = len([c for c in f.supervisor.commands if "sync" in c])
        with patch.object(f.setup, "check_platform"):
            f.setup.inspect()
            f.setup.prepare()
        self.assertEqual(before, inventory())
        self.assertEqual(commands, len([c for c in f.supervisor.commands if "sync" in c]))

    def test_runtime_failure_never_publishes_ready(self):
        f = self.fixture
        with patch.object(f.setup, "check_platform"), patch.object(f.setup, "prepare_environment", side_effect=SetupError("mismatch")):
            with self.assertRaisesRegex(SetupError, "mismatch"):
                f.setup.prepare()
        self.assertFalse(f.setup.ready.exists())

    def test_damaged_prepared_installation_is_preserved_without_repair(self):
        f = self.fixture
        f.prepare()
        (f.setup.model / "model.safetensors").unlink()
        def inventory():
            return {str(p.relative_to(f.root)): (digest(p), p.stat().st_mtime_ns)
                    for p in f.root.rglob("*") if p.is_file() and p.name != "setup.lock"}
        before = inventory()
        with patch.object(f.setup, "check_platform"), \
                patch.object(f.setup, "prepare_environment") as environment, \
                patch.object(f.setup, "prepare_model") as model:
            for operation in (f.setup.inspect, f.setup.prepare):
                with self.assertRaisesRegex(SetupError, "not an interrupted preparation; Resume cannot repair"):
                    operation()
            environment.assert_not_called()
            model.assert_not_called()
        self.assertEqual(inventory(), before)
        self.assertFalse((f.setup.model / "model.safetensors").exists())

    def test_explicit_resume_rebuilds_only_owned_incomplete_environment(self):
        f = self.fixture
        owner = {"schema": "activation-setup-environment-owner-v1", "runtimeId": f.setup.runtime_id,
                 "manifestSha256": f.setup.manifest_sha}
        atomic_json(f.setup.runtime / ".environment-owner", owner)
        f.setup.venv.mkdir()
        (f.setup.venv / "interrupted").write_text("owned partial installation")
        outside = f.setup.runtime / "keep-me"
        outside.write_text("preserve")
        f.setup.prepare_environment()
        self.assertTrue(f.setup.venv_python.is_file())
        self.assertFalse((f.setup.venv / "interrupted").exists())
        self.assertEqual(outside.read_text(), "preserve")
        self.assertTrue(any("Rebuilding" in e[1].get("message", "") for e in f.events))

    def test_unowned_incomplete_environment_is_not_removed(self):
        f = self.fixture
        f.setup.venv.mkdir()
        retained = f.setup.venv / "user-file"
        retained.write_text("preserve")
        with self.assertRaisesRegex(SetupError, "no matching setup ownership"):
            f.setup.prepare_environment()
        self.assertEqual(retained.read_text(), "preserve")

    def test_cancel_before_publication_retains_model_but_no_ready_receipt(self):
        f = self.fixture
        original = f.setup.validate_runtime
        count = [0]
        def validation():
            result = original()
            count[0] += 1
            if count[0] == 2:
                f.supervisor.cancelled = True
            return result
        with patch.object(f.setup, "validate_runtime", side_effect=validation):
            with self.assertRaises(Cancelled):
                f.prepare()
        self.assertFalse(f.setup.ready.exists())
        self.assertTrue((f.setup.model / "model-provenance.json").is_file())

    def test_frozen_lock_mutation_refused(self):
        f = self.fixture
        (f.resources / "wheels.lock").write_text("different")
        with self.assertRaisesRegex(SetupError, "lock differs"):
            Setup(f.root, f.resources, f.supervisor)

    def test_receipt_wrong_paths_and_runtime_are_refused(self):
        f = self.fixture
        receipt = f.prepare()
        receipt["pythonPath"] = "/different/python"
        atomic_json(f.setup.ready, receipt)
        with patch.object(f.setup, "check_platform"), self.assertRaisesRegex(SetupError, "paths differ"):
            f.setup.inspect()

    def test_nonowned_model_directory_is_not_modified(self):
        f = self.fixture
        f.setup.model.mkdir(parents=True)
        existing = f.setup.model / "unrelated.txt"
        existing.write_text("preserve")
        with self.assertRaisesRegex(SetupError, "not an owned"):
            f.setup.prepare_model()
        self.assertEqual(existing.read_text(), "preserve")

    def test_resume_repairs_model_directory_creation_crash_window(self):
        f = self.fixture
        owner = {"schema": "activation-setup-model-owner-v1", "modelLockSha256": f.manifest["locks"]["model"]["sha256"]}
        outer = f.root / "model-owners" / (f.setup.model_spec["revision"] + ".json")
        outer.parent.mkdir()
        atomic_json(outer, owner)
        f.setup.model.mkdir(parents=True)
        (f.setup.model / ".setup-owner.pending").write_text("interrupted receipt")
        def write_model(item):
            (f.setup.model / item["path"]).write_bytes(f.contents[item["path"]])
        with patch.object(f.setup, "download_model_file", side_effect=write_model):
            f.setup.prepare_model()
        self.assertEqual(json.loads((f.setup.model / ".setup-owner").read_text()), owner)
        self.assertTrue((f.setup.model / "model-provenance.json").is_file())

    def test_model_extra_json_or_symlink_refused(self):
        f = self.fixture
        f.prepare()
        extra = f.setup.model / "unexpected.json"
        extra.write_text("{}")
        with self.assertRaisesRegex(SetupError, "unexpected"):
            f.setup.validate_model()
        extra.unlink()
        (f.setup.model / "model.safetensors").unlink()
        (f.setup.model / "model.safetensors").symlink_to(f.setup.python)
        with self.assertRaisesRegex(SetupError, "symbolic link"):
            f.setup.validate_model()

    def test_path_escape_and_symlink_receipts_refused(self):
        f = self.fixture
        for name in ("../outside", "/absolute"):
            with self.assertRaises(SetupError):
                relative_path(f.root, name)
        outside = Path(self.temporary.name) / "outside"
        outside.write_text("preserve")
        f.setup.ready.symlink_to(outside)
        with self.assertRaisesRegex(SetupError, "symlink"):
            atomic_json(f.setup.ready, {})
        self.assertEqual(outside.read_text(), "preserve")

    def test_platform_floor_and_architecture_refused(self):
        f = self.fixture
        with patch("activation_setup.driver.platform.system", return_value="Darwin"), patch("activation_setup.driver.platform.machine", return_value="arm64"), patch("activation_setup.driver.platform.mac_ver", return_value=("25.6", (), "")):
            with self.assertRaisesRegex(SetupError, "macOS 26"):
                f.setup.check_platform()
        with patch("activation_setup.driver.platform.machine", return_value="x86_64"):
            with self.assertRaisesRegex(SetupError, "Apple Silicon"):
                f.setup.check_platform()

    def test_environment_omits_user_python_package_and_auth_settings(self):
        with patch.dict(os.environ, {"PYTHONPATH": "private", "UV_INDEX_URL": "private", "HF_TOKEN": "private", "PIP_CONFIG_FILE": "private", "NETRC": "private", "UV_CREDENTIALS_DIR": "private", "UV_KEYRING_PROVIDER": "subprocess"}):
            env = clean_environment(self.fixture.root)
        for key in ("PYTHONPATH", "UV_INDEX_URL", "HF_TOKEN", "PIP_CONFIG_FILE"):
            self.assertNotIn(key, env)
        self.assertEqual(env["UV_PYTHON_DOWNLOADS"], "never")
        # uv always checks netrc separately from --no-config. Neither its
        # credential store nor that fallback may consult the recipient's files.
        self.assertEqual(env["NETRC"], "/dev/null")
        self.assertEqual(env["UV_CREDENTIALS_DIR"], str(self.fixture.root / "package-credentials"))
        self.assertEqual(env["UV_KEYRING_PROVIDER"], "disabled")
        self.assertEqual(env["XDG_CONFIG_HOME"], str(self.fixture.root / "package-config"))

    def test_parent_loss_terminates_and_reaps_its_owned_child(self):
        parent = [111]
        supervisor = Supervisor(111, lambda: parent[0])
        supervisor.start_watch()
        outcomes = []
        def run():
            try:
                supervisor.run([sys.executable, "-c", "import time; time.sleep(60)"], self.fixture.root)
            except Cancelled:
                outcomes.append("cancelled")
        thread = threading.Thread(target=run)
        thread.start()
        deadline = time.monotonic() + 3
        while supervisor.child is None and time.monotonic() < deadline:
            time.sleep(0.01)
        child = supervisor.child
        self.assertIsNotNone(child)
        parent[0] = 222
        thread.join(timeout=4)
        supervisor.close()
        self.assertFalse(thread.is_alive())
        self.assertIsNotNone(child.poll())
        self.assertEqual(outcomes, ["cancelled"])


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.fixture = Fixture(Path(self.temporary.name).resolve())
        self.setup = self.fixture.setup
        self.setup.model.mkdir(parents=True)
        self.item = self.setup.model_spec["files"][-1]
        self.data = self.fixture.contents[self.item["path"]]
        self.destination = self.setup.model / self.item["path"]
        self.partial = self.destination.with_name(self.destination.name + ".download")

    def tearDown(self):
        self.temporary.cleanup()

    def test_verified_download_and_recheck_never_redownloads(self):
        calls = []
        def open_response(request, timeout):
            calls.append(request)
            return Response(self.data)
        self.setup.download_model_file(self.item, opener=open_response)
        self.setup.download_model_file(self.item, opener=open_response)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.destination.read_bytes(), self.data)

    def test_resume_uses_verified_content_range(self):
        self.partial.write_bytes(self.data[:4])
        def open_response(request, timeout):
            self.assertEqual(request.get_header("Range"), "bytes=4-")
            return Response(self.data[4:], 206, {"Content-Range": f"bytes 4-{len(self.data)-1}/{len(self.data)}"})
        self.setup.download_model_file(self.item, opener=open_response)
        self.assertEqual(self.destination.read_bytes(), self.data)

    def test_range_ignored_restarts_owned_partial(self):
        self.partial.write_bytes(self.data[:4])
        self.setup.download_model_file(self.item, opener=lambda *a, **k: Response(self.data))
        self.assertEqual(self.destination.read_bytes(), self.data)

    def test_wrong_range_leaves_partial_unchanged(self):
        self.partial.write_bytes(self.data[:4])
        with self.assertRaisesRegex(SetupError, "byte range"):
            self.setup.download_model_file(self.item, opener=lambda *a, **k: Response(self.data[4:], 206, {"Content-Range": f"bytes 5-{len(self.data)-1}/{len(self.data)}"}))
        self.assertEqual(self.partial.read_bytes(), self.data[:4])

    def test_wrong_hash_retains_failed_partial_without_publishing(self):
        wrong = b"x" * len(self.data)
        with self.assertRaisesRegex(SetupError, "frozen hash"):
            self.setup.download_model_file(self.item, opener=lambda *a, **k: Response(wrong))
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.partial.exists())
        failures = list((self.setup.root / "model-download-failures").iterdir())
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].read_bytes(), wrong)
        self.setup.download_model_file(self.item, opener=lambda *a, **k: Response(self.data))
        self.assertEqual(self.destination.read_bytes(), self.data)

    def test_network_failure_preserves_partial_for_explicit_next_attempt(self):
        self.partial.write_bytes(self.data[:4])
        with self.assertRaisesRegex(OSError, "network unavailable"):
            self.setup.download_model_file(self.item, opener=lambda *a, **k: (_ for _ in ()).throw(OSError("network unavailable")))
        self.assertEqual(self.partial.read_bytes(), self.data[:4])

    def test_non_https_redirect_refused(self):
        with self.assertRaisesRegex(SetupError, "away from HTTPS"):
            self.setup.download_model_file(self.item, opener=lambda *a, **k: Response(self.data, url="http://example.test/file"))
        self.assertFalse(self.partial.exists())

    def test_cancelled_download_does_not_publish(self):
        self.fixture.supervisor.cancelled = True
        with self.assertRaises(Cancelled):
            self.setup.download_model_file(self.item, opener=lambda *a, **k: Response(self.data))
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
