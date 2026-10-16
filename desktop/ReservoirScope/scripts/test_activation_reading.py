"""Portable reading derivation tests; no model/runtime imports or inference."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import prepare_activation_reading as reading


class ReadingValidationTests(unittest.TestCase):
    def fixture(self):
        return {"format": reading.FORMAT, "readings": [{"events": [{"id": "event-1"}],
            "entries": [{"text": "Exact prose\nwith a final line.", "sha256": reading.digest("Exact prose\nwith a final line."),
                "prompt": "Exact invitation", "promptSha256": reading.digest("Exact invitation"),
                "eventIds": ["event-1"], "status": "incomplete", "savedStep": None, "appliedStep": None}],
            "disclosure": {"notes": []}}]}

    def test_changed_prose_and_prompt_are_rejected(self):
        for key in ("text", "prompt"):
            value = self.fixture()
            value["readings"][0]["entries"][0][key] += " altered"
            with self.assertRaisesRegex(ValueError, "hash differs"):
                reading.validate(value)

    def test_incomplete_cannot_be_saved_or_applied(self):
        reading.validate(self.fixture())
        for key in ("savedStep", "appliedStep"):
            value = self.fixture()
            value["readings"][0]["entries"][0][key] = 20
            with self.assertRaisesRegex(ValueError, "Incomplete writing"):
                reading.validate(value)

    def test_dangling_reference_and_host_path_are_rejected(self):
        value = self.fixture()
        value["readings"][0]["entries"][0]["eventIds"] = ["missing"]
        with self.assertRaisesRegex(ValueError, "Dangling"):
            reading.validate(value)
        for leaked in ("/Users/example/private", "/Volumes/source", "/private/tmp/owned", "modelPath"):
            value = self.fixture(); value["leaked"] = leaked
            with self.assertRaisesRegex(ValueError, "leaked"):
                reading.validate(value)

    def test_note_hash_is_checked(self):
        value = self.fixture()
        value["readings"][0]["disclosure"]["notes"] = [{"text": "Note", "sha256": "0" * 64}]
        with self.assertRaisesRegex(ValueError, "Note content"):
            reading.validate(value)


@unittest.skipUnless(all((reading.ROOT / source[1] / "latest.json").is_file() for source in reading.SOURCES), "Private retained example sources are not present")
class RetainedReadingDerivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory(prefix="activation-reading-test-")
        cls.destination = Path(cls.folder.name)
        cls.result = reading.prepare(cls.destination)
        cls.collection = json.loads((cls.destination / "activation-preview-v1.json").read_text())
        cls.receipt = json.loads((cls.destination / "activation-preview-v1.derivation.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def test_complete_selection_and_entire_unfinished_response_match_originals(self):
        self.assertEqual([len(r["entries"]) for r in self.collection["readings"]], [6, 3])
        for source, result in zip(reading.SOURCES, self.collection["readings"]):
            root = reading.ROOT / source[1]
            manifest = json.loads((root / "latest.json").read_text())
            record = json.loads((root / manifest["recordFile"]).read_text())
            complete = [e for e in result["entries"] if e["status"] == "complete"]
            self.assertEqual([e["text"] for e in complete], [j["text"] for j in record["state"]["journals"]])
            for entry in result["entries"]:
                response = json.loads((root / f'{entry["requestId"]}-response.json').read_text())
                request = json.loads((root / f'{entry["requestId"]}-request.json').read_text())
                self.assertEqual(entry["text"], response["text"])
                self.assertEqual(entry["prompt"], request["prompt"])
                self.assertEqual(entry["contentTokens"], len(response["generatedTokenIds"]))
        unfinished = self.collection["readings"][1]["entries"][-1]
        self.assertEqual(unfinished["status"], "incomplete")
        self.assertEqual(unfinished["contentTokens"], 1024)
        self.assertEqual(unfinished["stopReason"], "max_tokens")
        self.assertEqual(len(unfinished["text"]), 3928)

    def test_all_sources_remain_identical_and_note_passages_are_exact(self):
        note_sources = []
        for path, expected in self.receipt["sourceFiles"].items():
            raw = (reading.ROOT / path).read_bytes()
            self.assertEqual(reading.digest(raw), expected, path)
            if path.endswith(".md"):
                note_sources.append((expected, raw.decode()))
        for result in self.collection["readings"]:
            for note in result["disclosure"]["notes"]:
                source = next(body for sha, body in note_sources if sha == note["sourceSha256"])
                self.assertIn(note["text"], source)
        self.assertFalse(self.receipt["sourceFilesModified"])
        self.assertEqual(self.receipt["modelCalls"], 0)

    def test_derivative_is_portable_and_does_not_claim_matched_comparison(self):
        reading.validate(self.collection)
        self.assertIn("not a matched comparison", self.collection["scope"])
        self.assertNotEqual(self.collection["readings"][0]["disclosure"]["modelManifestSha256"], self.collection["readings"][1]["disclosure"]["modelManifestSha256"])
        self.assertEqual(self.receipt["collectionSha256"], reading.digest((self.destination / "activation-preview-v1.json").read_bytes()))

    def test_generator_refuses_overwrite_and_changed_record_identity(self):
        with self.assertRaisesRegex(ValueError, "not overwritten"):
            reading.prepare(self.destination)
        with self.assertRaisesRegex(ValueError, "identity differs"):
            source = reading.SOURCES[0]
            reading.derive_reading(reading.ROOT / source[1], "reading-a", "0" * 64, "Synthetic altered identity", reading.frozen_inventory())

    def test_mutation_before_derivation_is_rejected_by_prior_receipts(self):
        sources = self.receipt["sourceFiles"]
        headroom = reading.SOURCES[1][1]
        mutations = [
            (f"{headroom}/latest.json", lambda d: d["config"].update(arm="recurrent")),
            (f"{headroom}/latest.json", lambda d: d.update(modelManifestSha256="f" * 64)),
            (f"{headroom}/latest.json", lambda d: d.update(calibrationSha256="f" * 64)),
            (f"{headroom}/request-21-response.json", lambda d: d.update(text=d["text"] + " changed")),
            (f"{headroom}/request-5-request.json", lambda d: d.update(prompt=d["prompt"] + " changed")),
            ("desktop/ReservoirScope/validation/2026-10-16-activation-headroom/READING-BLIND.md", None),
            ("desktop/ReservoirScope/validation/2026-10-15-activation-0.26.0/PILOT-READING-BLIND.md", None),
            ("research/outputs/activation-headroom-20261016/cohort-inventory-after-analysis.json", None),
        ]
        with tempfile.TemporaryDirectory(prefix="activation-reading-mutated-copy-") as folder:
            copied = Path(folder)
            for relative in sources:
                target = copied / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(reading.ROOT / relative, target)
            for relative, mutate in mutations:
                path = copied / relative
                original = path.read_bytes()
                if mutate is None:
                    path.write_bytes(original + b"\nchanged")
                else:
                    value = json.loads(original); mutate(value)
                    path.write_text(json.dumps(value))
                with self.subTest(source=relative), patch.object(reading, "ROOT", copied):
                    with self.assertRaisesRegex(ValueError, "Frozen source identity differs"):
                        reading.prepare(copied / "output")
                path.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
