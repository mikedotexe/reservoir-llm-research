"""Synthetic bootstrap staging; no network, executable helper or model is used."""
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import Mock

import stage_activation_bootstrap as staging


def archive_for(payload, *, symlink=False, duplicate=False):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for _ in range(2 if duplicate else 1):
            entry = tarfile.TarInfo("uv-aarch64-apple-darwin/uv")
            if symlink:
                entry.type = tarfile.SYMTYPE
                entry.linkname = "/outside"
                archive.addfile(entry)
            else:
                entry.size = len(payload)
                archive.addfile(entry, io.BytesIO(payload))
    return buffer.getvalue()


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bundle = Path(self.temp.name) / "bundle"
        self.bundle.mkdir()
        self.python = b"synthetic pinned Python archive"
        self.uv = b"synthetic executable bytes, never run"
        self.archive = archive_for(self.uv)
        self.manifest = {"schema": "activation-setup-manifest-v1", "python": {
            "archivePath": "assets/python.tar.gz", "archiveSha256": staging.sha(self.python),
            "archiveBytes": len(self.python), "url": "https://example.test/python.tar.gz"},
            "uv": {"path": "assets/uv", "sha256": staging.sha(self.uv), "bytes": len(self.uv),
                   "archiveSha256": staging.sha(self.archive), "url": "https://example.test/uv.tar.gz"}}
        self.write_manifest()
        (self.bundle / "model-files.json").write_bytes(b"unchanged model metadata")
        self.downloader = Mock(side_effect=lambda url: self.python if url.endswith("python.tar.gz") else self.archive)

    def write_manifest(self):
        (self.bundle / "setup-manifest.json").write_text(json.dumps(self.manifest))

    def test_exact_stage_and_idempotent_reuse_preserve_metadata(self):
        before = {p.name: p.read_bytes() for p in self.bundle.iterdir()}
        result = staging.stage(self.bundle, self.downloader)
        self.assertEqual(result["downloadedAssets"], 2)
        self.assertEqual((self.bundle / "assets/python.tar.gz").read_bytes(), self.python)
        self.assertEqual((self.bundle / "assets/uv").read_bytes(), self.uv)
        self.assertEqual(sorted(p.name for p in (self.bundle / "assets").iterdir()), ["python.tar.gz", "uv"])
        if os.name == "posix":
            self.assertTrue((self.bundle / "assets/uv").stat().st_mode & 0o111)
        again = staging.stage(self.bundle, Mock(side_effect=AssertionError("Unexpected download")))
        self.assertEqual(again["downloadedAssets"], 0)
        for name, data in before.items():
            self.assertEqual((self.bundle / name).read_bytes(), data)

    def test_different_existing_file_refused_before_download(self):
        (self.bundle / "assets").mkdir()
        target = self.bundle / "assets/uv"
        target.write_bytes(b"different")
        with self.assertRaises(ValueError):
            staging.stage(self.bundle, self.downloader)
        self.downloader.assert_not_called()
        self.assertEqual(target.read_bytes(), b"different")

    def test_download_hash_and_size_failures_publish_nothing(self):
        for key, value in [("archiveSha256", "0" * 64), ("archiveBytes", len(self.python) + 1)]:
            with self.subTest(key=key):
                original = self.manifest["python"][key]
                self.manifest["python"][key] = value
                self.write_manifest()
                with self.assertRaises(ValueError):
                    staging.stage(self.bundle, self.downloader)
                self.assertFalse((self.bundle / "assets").exists())
                self.manifest["python"][key] = original

    def test_uv_archive_and_extracted_file_are_independently_verified(self):
        for change in ("archive", "extracted", "symlink", "duplicate"):
            with self.subTest(change=change):
                self.archive = archive_for(self.uv, symlink=change == "symlink", duplicate=change == "duplicate")
                self.manifest["uv"]["archiveSha256"] = "0" * 64 if change == "archive" else staging.sha(self.archive)
                self.manifest["uv"]["sha256"] = "0" * 64 if change == "extracted" else staging.sha(self.uv)
                self.write_manifest()
                with self.assertRaises(ValueError):
                    staging.stage(self.bundle, self.downloader)
                self.assertFalse((self.bundle / "assets").exists())

    def test_manifest_cannot_write_outside_assets(self):
        for path in ("../outside", "/outside", "assets/../outside", "assets/sub/uv", "assets\\uv"):
            with self.subTest(path=path):
                self.manifest["uv"]["path"] = path
                self.write_manifest()
                with self.assertRaises(ValueError):
                    staging.stage(self.bundle, self.downloader)
        self.downloader.assert_not_called()

    @unittest.skipUnless(os.name == "posix", "Unprivileged symlink creation")
    def test_existing_symlink_is_not_followed(self):
        outside = Path(self.temp.name) / "outside"
        outside.write_bytes(self.uv)
        (self.bundle / "assets").mkdir()
        (self.bundle / "assets/uv").symlink_to(outside)
        with self.assertRaises(ValueError):
            staging.stage(self.bundle, self.downloader)
        self.downloader.assert_not_called()
        self.assertEqual(outside.read_bytes(), self.uv)


if __name__ == "__main__":
    unittest.main()
