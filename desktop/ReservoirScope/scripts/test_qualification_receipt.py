"""Receipt honesty and identity tests, using disposable source/package trees."""
import json
from pathlib import Path
import plistlib
import tempfile
import unittest
from qualification_receipt import CHECKS, inventory_digest, package_inventory, reported_checks, source_inventory


class QualificationReceiptChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="scope-receipt-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_no_results_are_inferred(self):
        checks, source = reported_checks(None)
        self.assertEqual(len(checks), len(CHECKS))
        self.assertTrue(all(item["status"] == "unexecuted" for item in checks))
        self.assertIsNone(source)

    def test_reported_success_requires_and_labels_evidence(self):
        path = self.root / "checks.json"
        path.write_text(json.dumps([{"id": "frontend-tests", "status": "passed"}]))
        with self.assertRaisesRegex(ValueError, "require command and evidence"):
            reported_checks(path)
        path.write_text(json.dumps([{"id": "frontend-tests", "status": "passed", "command": "npm test", "evidence": "Retained test log reports 10 passed"}]))
        checks, source = reported_checks(path)
        result = next(item for item in checks if item["id"] == "frontend-tests")
        self.assertIn("not executed by receipt", result["evidenceOrigin"])
        self.assertIn("sha256", source)

    def test_implementation_inventory_excludes_outputs(self):
        for relative in ("desktop/ReservoirScope/src/main.tsx", "shared/reservoir-scope/reference-manifest.json", ".github/workflows/tauri.yml", "desktop/ReservoirScope/target/app", "desktop/ReservoirScope/node_modules/lib/index.js", "desktop/ReservoirScope/src-tauri/resources/fixture.json", "desktop/ReservoirScope/validation/receipt.json"):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("input")
        entries = source_inventory(self.root)
        self.assertEqual(len(entries), 3)
        self.assertTrue(any(item["path"].endswith("main.tsx") for item in entries))

    def test_package_identity_detects_changed_binary(self):
        app = self.root / "Preview.app"
        binary = app / "Contents/MacOS/preview"
        binary.parent.mkdir(parents=True)
        (app / "Contents/Info.plist").write_bytes(plistlib.dumps({"CFBundleExecutable": "preview", "CFBundleIdentifier": "test.preview"}))
        binary.write_bytes(b"first binary")
        first = package_inventory(app)
        binary.write_bytes(b"second binary")
        second = package_inventory(app)
        self.assertNotEqual(first["binary"]["sha256"], second["binary"]["sha256"])
        self.assertNotEqual(first["inventorySha256"], second["inventorySha256"])
        self.assertEqual(second["inventorySha256"], inventory_digest(second["files"]))
        binary.unlink()
        with self.assertRaisesRegex(ValueError, "executable is missing"):
            package_inventory(app)


if __name__ == "__main__":
    unittest.main()
