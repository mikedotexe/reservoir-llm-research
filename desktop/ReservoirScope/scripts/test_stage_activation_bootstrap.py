"""Synthetic bootstrap bytes/HTTP only; no download, subprocess or runtime launch."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import stage_activation_bootstrap as stage


def digest(data):
    return hashlib.sha256(data).hexdigest()


def archive(entries):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as tar:
        for name, data, kind in entries:
            member = tarfile.TarInfo(name)
            member.type = kind
            member.size = len(data) if kind == tarfile.REGTYPE else 0
            if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
                member.linkname = "../../outside"
            tar.addfile(member, io.BytesIO(data) if kind == tarfile.REGTYPE else None)
    return output.getvalue()


class Response(io.BytesIO):
    status = 200

    def __init__(self, data, declared=None):
        super().__init__(data)
        self.headers = {} if declared is None else {"Content-Length": str(declared)}

    def geturl(self):
        return "https://release-assets.githubusercontent.com/frozen-artifact"


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="scope-bootstrap-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.python = b"synthetic python archive bytes"
        self.uv = b"synthetic executable bytes, never executed"
        self.tar = archive([(stage.UV_MEMBER, self.uv, tarfile.REGTYPE),
                            ("uv-aarch64-apple-darwin/uvx", b"not extracted", tarfile.REGTYPE)])
        self.manifest = {"schema": "activation-setup-manifest-v1",
                         "python": {"archivePath": "assets/python.tar.gz", "archiveBytes": len(self.python),
                                    "archiveSha256": digest(self.python),
                                    "url": "https://github.com/astral-sh/python-build-standalone/releases/download/test/python.tar.gz"},
                         "uv": {"path": "assets/uv", "bytes": len(self.uv), "sha256": digest(self.uv),
                                "archiveSha256": digest(self.tar),
                                "url": "https://github.com/astral-sh/uv/releases/download/test/uv.tar.gz"}}
        self.write_manifest()
        # Fail immediately if any test accidentally starts a child or opens a URL.
        self.no_network = patch.object(stage, "open_download", side_effect=AssertionError("Unexpected network"))
        self.no_network.start(); self.addCleanup(self.no_network.stop)
        self.no_process = patch.object(stage.subprocess, "run", side_effect=AssertionError("Unexpected subprocess"))
        self.no_process.start(); self.addCleanup(self.no_process.stop)

    def write_manifest(self):
        (self.root / "setup-manifest.json").write_text(json.dumps(self.manifest))

    def payload_worker(self, command, **kwargs):
        self.assertEqual(command[:4], [stage.sys.executable, "-B", str(Path(stage.__file__).resolve()), "--download-worker"])
        self.assertEqual(kwargs["timeout"], stage.DOWNLOAD_SECONDS)
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        _, _, _, _, url, path, sha, length, maximum = command
        data = self.python if url == self.manifest['python']['url'] else self.tar
        with patch.object(stage, "open_download", return_value=Response(data, len(data))):
            stage.download_payload(url, Path(path), sha, None if length == "none" else int(length), int(maximum))
        return SimpleNamespace(returncode=0, stderr="")

    def stage_fresh(self):
        with patch.object(stage.subprocess, "run", side_effect=self.payload_worker) as worker:
            result = stage.stage(self.root)
        return result, worker

    def test_fresh_stage_uses_two_pinned_payloads_and_only_extracts_uv(self):
        before = (self.root / "setup-manifest.json").read_bytes()
        result, worker = self.stage_fresh()
        self.assertEqual(result["status"], "verified")
        self.assertEqual(worker.call_count, 2)
        self.assertEqual((self.root / "assets/uv").read_bytes(), self.uv)
        self.assertEqual((self.root / "assets/python.tar.gz").read_bytes(), self.python)
        self.assertEqual({p.name for p in (self.root / "assets").iterdir()}, {"uv", "python.tar.gz", stage.UV_ARCHIVE})
        self.assertEqual((self.root / "setup-manifest.json").read_bytes(), before)
        if os.name != "nt": self.assertTrue((self.root / "assets/uv").stat().st_mode & 0o111)

    def test_matching_cache_is_byte_and_metadata_exact_without_network(self):
        self.stage_fresh()
        paths = list(self.root.rglob("*"))
        before = {str(p): (p.stat().st_ino, p.stat().st_mtime_ns, p.stat().st_mode,
                           p.read_bytes() if p.is_file() else None) for p in paths}
        result = stage.stage(self.root)
        self.assertEqual(result["downloads"], [])
        self.assertEqual(before, {str(p): (p.stat().st_ino, p.stat().st_mtime_ns, p.stat().st_mode,
                                          p.read_bytes() if p.is_file() else None) for p in paths})

    def test_missing_archive_is_not_needed_when_packaged_files_are_cached(self):
        self.stage_fresh(); (self.root / "assets" / stage.UV_ARCHIVE).unlink()
        self.assertEqual(stage.stage(self.root)["downloads"], [])
        self.assertEqual(stage.stage(self.root, check_only=True)["status"], "verified")

    def test_verified_archive_can_restore_missing_uv_without_download(self):
        self.stage_fresh(); (self.root / "assets/uv").unlink()
        self.assertEqual(stage.stage(self.root)["downloads"], [])
        self.assertEqual((self.root / "assets/uv").read_bytes(), self.uv)

    def test_check_only_missing_is_diagnostic_and_does_not_create_assets(self):
        before = (self.root / "setup-manifest.json").read_bytes()
        result = stage.stage(self.root, check_only=True)
        self.assertEqual(result["status"], "missing")
        self.assertEqual(len(result["missing"]), 2)
        self.assertFalse((self.root / "assets").exists())
        self.assertEqual((self.root / "setup-manifest.json").read_bytes(), before)

    def test_wrong_existing_bytes_refuse_before_other_missing_assets_are_fetched(self):
        assets = self.root / "assets"; assets.mkdir()
        wrong = b"wrong"; (assets / "uv").write_bytes(wrong)
        for check in (False, True):
            with self.assertRaisesRegex(ValueError, "size differs"):
                stage.stage(self.root, check_only=check)
        self.assertEqual((assets / "uv").read_bytes(), wrong)
        self.assertFalse((assets / "python.tar.gz").exists())

    def test_equal_size_cache_corruption_refuses_without_overwrite(self):
        self.stage_fresh(); uv = self.root / "assets/uv"
        wrong = b"x" * len(self.uv); uv.write_bytes(wrong)
        with self.assertRaisesRegex(ValueError, "SHA-256 differs"): stage.stage(self.root)
        self.assertEqual(uv.read_bytes(), wrong)

    def test_manifest_paths_sizes_and_hosts_are_guarded(self):
        original = json.loads(json.dumps(self.manifest))
        for path in ("../outside", "/tmp/uv", "assets/../outside", "assets/nested/uv", "assets\\uv"):
            self.manifest["uv"]["path"] = path; self.write_manifest()
            with self.assertRaises(ValueError): stage.stage(self.root)
        self.manifest = original
        self.manifest["uv"]["bytes"] = True; self.write_manifest()
        with self.assertRaisesRegex(ValueError, "size"): stage.stage(self.root)
        self.manifest["uv"]["bytes"] = len(self.uv)
        self.manifest["python"]["url"] = "https://example.com/python.tar.gz"; self.write_manifest()
        with self.assertRaisesRegex(ValueError, "HTTPS"): stage.stage(self.root)
        self.assertFalse((self.root / "assets").exists())

    def test_symlink_assets_and_leaf_are_rejected(self):
        other = self.root / "other"; other.mkdir()
        assets = self.root / "assets"
        try: assets.symlink_to(other, target_is_directory=True)
        except OSError as error:
            if os.name == "nt" and getattr(error, "winerror", None) == 1314:
                self.skipTest("Windows account lacks symlink privilege")
            raise
        with self.assertRaisesRegex(ValueError, "ordinary directory"): stage.stage(self.root)
        assets.unlink(); assets.mkdir()
        (assets / "uv").symlink_to(other / "missing")
        with self.assertRaisesRegex(ValueError, "ordinary file"): stage.stage(self.root)

    def test_atomic_publish_preserves_existing_matching_and_rejects_other_bytes(self):
        one = self.root / "one"; target = self.root / "target"
        one.write_bytes(self.uv); target.write_bytes(self.uv)
        inode = target.stat().st_ino
        stage.publish(one, target, digest(self.uv), len(self.uv), stage.MAX_ARCHIVE_BYTES)
        self.assertEqual(target.stat().st_ino, inode)
        target.write_bytes(b"different")
        with self.assertRaisesRegex(ValueError, "size differs"):
            stage.publish(one, target, digest(self.uv), len(self.uv), stage.MAX_ARCHIVE_BYTES)
        self.assertEqual(target.read_bytes(), b"different")

    def test_total_child_timeout_removes_only_own_temporary_file(self):
        assets = self.root / "assets"; assets.mkdir()
        unrelated = assets / "unrelated"; unrelated.write_text("preserve")
        with patch.object(stage.subprocess, "run", side_effect=subprocess.TimeoutExpired("synthetic", 180)) as worker:
            with self.assertRaises(subprocess.TimeoutExpired):
                stage.download(self.manifest['python']['url'], assets / "python.tar.gz", digest(self.python), len(self.python))
        self.assertEqual(worker.call_args.kwargs['timeout'], 180)
        self.assertEqual(list(assets.iterdir()), [unrelated])

    def test_failed_child_or_false_success_never_publishes(self):
        assets = self.root / "assets"; assets.mkdir()
        for status in (1, 0):
            with patch.object(stage.subprocess, "run", return_value=SimpleNamespace(returncode=status, stderr="synthetic failure")):
                with self.assertRaises(ValueError):
                    stage.download(self.manifest['python']['url'], assets / "python.tar.gz", digest(self.python), len(self.python))
            self.assertEqual(list(assets.iterdir()), [])

    def payload(self, response, *, expected=None, maximum=100):
        path = self.root / ".bootstrap-test"; path.write_bytes(b"")
        with patch.object(stage, "open_download", return_value=response):
            stage.download_payload(self.manifest['python']['url'], path, digest(self.python), expected, maximum)

    def test_stream_length_hash_and_size_fail_closed(self):
        cases = [(Response(self.python, len(self.python) + 1), None, 100, "shorter"),
                 (Response(self.python, 1000), None, 100, "Content-Length"),
                 (Response(b"x" * 101), None, 100, "byte bound"),
                 (Response(b"x" * len(self.python)), len(self.python), 100, "SHA-256"),
                 (Response(self.python), len(self.python) + 1, 100, "size differs")]
        for response, expected, maximum, reason in cases:
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                self.payload(response, expected=expected, maximum=maximum)

    def test_short_read_trickle_hits_deadline_without_acceptance(self):
        response = Response(self.python)
        response.read1 = lambda size: b"x"
        # Start, before/after first short read, before/after second short read.
        with patch.object(stage.time, 'monotonic', side_effect=[0, 1, 80, 100, 181]):
            with self.assertRaisesRegex(TimeoutError, "deadline"):
                self.payload(response)

    def test_http_failure_and_unapproved_redirect_refuse(self):
        response = Response(self.python); response.status = 503
        with self.assertRaisesRegex(ValueError, "HTTP 503"): self.payload(response)
        for url in ("http://github.com/file", "https://example.com/file", "https://user:password@github.com/file"):
            with self.assertRaises(ValueError): stage.checked_url(url)
        with self.assertRaises(ValueError):
            stage.BootstrapRedirect().redirect_request(None, None, 302, '', {}, 'http://github.com/file')

    def test_archive_missing_duplicate_link_and_traversal_fail_without_uv(self):
        cases = [[("uvx", b"other", tarfile.REGTYPE)],
                 [(stage.UV_MEMBER, self.uv, tarfile.REGTYPE)] * 2,
                 [(stage.UV_MEMBER, b"", tarfile.SYMTYPE)],
                 [(stage.UV_MEMBER, b"", tarfile.LNKTYPE)],
                 [("../outside", self.uv, tarfile.REGTYPE)],
                 [(stage.UV_MEMBER, b"short", tarfile.REGTYPE)]]
        for entries in cases:
            with self.subTest(entries=entries):
                source = self.root / "uv.tar.gz"; source.write_bytes(archive(entries))
                with self.assertRaises(ValueError):
                    stage.extract_uv(source, self.root / "uv", digest(self.uv), len(self.uv))
                self.assertFalse((self.root / "uv").exists())
                self.assertFalse(list(self.root.glob('.bootstrap-*')))

    def test_archive_valid_shape_but_wrong_binary_hash_fails(self):
        source = self.root / "uv.tar.gz"; source.write_bytes(self.tar)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            stage.extract_uv(source, self.root / "uv", "0" * 64, len(self.uv))
        self.assertFalse((self.root / "uv").exists())
        self.assertFalse(list(self.root.glob('.bootstrap-*')))


if __name__ == "__main__":
    unittest.main()
