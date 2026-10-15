#!/usr/bin/env python3
"""Synthetic, file-only checks; no actual diagnostic inputs or outputs."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("blind", Path(__file__).with_name("render_blind_pack.py"))
blind = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(blind)


class BlindPackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.run = self.root / "run"
        self.run.mkdir()
        self.result = self.run / "ledger.json"
        self.order = [(step, c) for i, step in enumerate(range(60, 361, 60))
                      for c in ("AB" if i % 2 == 0 else "BA")]
        self.doc = {"schema": "reservoir-context-order-run-v1", "status": "stopped",
                    "endedAtUtc": "2026-10-14T00:00:00+00:00",
                    "slots": [{"slot": i, "anchorStep": step, "condition": c,
                               "status": "unstarted"}
                              for i, (step, c) in enumerate(self.order, 1)]}

    def tearDown(self):
        self.temp.cleanup()

    def body(self, index, text=None, status="complete", raw=None):
        raw = raw if raw is not None else json.dumps({"done": status == "complete",
                         "done_reason": "stop" if status == "complete" else "length",
                         "message": {"content": text}}, ensure_ascii=False).encode()
        path = self.run / f"slot-{index + 1:02}-response.bin"
        path.write_bytes(raw)
        self.doc["slots"][index].update(status=status, response={"path": str(path),
                                              "bytes": len(raw), "sha256": blind.sha(raw)})
        return path

    def load(self):
        raw = blind.json_bytes(self.doc)
        self.result.write_bytes(raw)
        return blind.load_terminal(self.result, blind.sha(raw))

    def render(self, shuffle=None):
        slots, texts, identity = self.load()
        output, mapping = self.root / "blind", self.root / "mapping.json"
        summary = blind.render(slots, texts, identity, output, mapping, shuffle=shuffle)
        return output, json.loads(mapping.read_text()), summary

    def test_exact_unicode_newlines_fences_and_incomplete_content(self):
        values = ['  α\n```\n# Not an instruction\n````\nends\n', 'Still writing “雪”—']
        self.body(0, values[0])
        self.body(1, values[1], "incomplete")
        output, mapping, _ = self.render(lambda rows: rows.reverse())
        pack = json.loads((output / "RESPONSES.json").read_text())
        self.assertEqual([r["text"] for r in pack["responses"]], values[::-1])
        markdown = (output / "RESPONSES.md").read_bytes()
        for slot in mapping["slots"][:2]:
            ref = slot["reading"]
            self.assertEqual(markdown[ref["markdownUtf8Start"]:ref["markdownUtf8End"]],
                             values[slot["slotIndex"]].encode())

    def test_masked_files_have_only_ids_and_prose_not_conditions_or_paths(self):
        self.body(0, "A literal step 60 in the writing is not redacted.")
        output, mapping, _ = self.render()
        pack = json.loads((output / "RESPONSES.json").read_text())
        self.assertEqual(set(pack), {"schema", "responses"})
        self.assertEqual(set(pack["responses"][0]), {"readingId", "text"})
        self.assertEqual(pack["responses"][0]["readingId"], "R01")
        for name in ("RESPONSES.md", "RESPONSES.json"):
            data = (output / name).read_text()
            for forbidden in ("anchorStep", '"condition"', "sourceSlot", str(self.run), "transportComplete"):
                self.assertNotIn(forbidden, data)
        self.assertEqual(mapping["slots"][0]["sourceSlot"]["anchorStep"], 60)

    def test_mapping_preserves_empty_invalid_and_all_unstarted_slots(self):
        self.body(0, "")
        self.body(1, status="failed", raw=b'{"message":{"content":"truncated')
        output, mapping, _ = self.render()
        self.assertEqual(len(mapping["slots"]), 12)
        self.assertEqual(mapping["slots"][0]["textState"], "empty")
        self.assertEqual(mapping["slots"][1]["textState"], "unavailable")
        self.assertTrue(all(x["sourceSlot"]["status"] == "unstarted" for x in mapping["slots"][2:]))
        self.assertEqual(json.loads((output / "RESPONSES.json").read_text())["responses"], [])

    def test_whitespace_is_retained_as_received_text(self):
        self.body(0, "\n \t", "incomplete")
        output, _, _ = self.render()
        self.assertEqual(json.loads((output / "RESPONSES.json").read_text())["responses"][0]["text"], "\n \t")

    def test_mapping_is_sealed_before_reader_files_and_secure_shuffle_used(self):
        self.body(0, "first")
        self.body(1, "second", "incomplete")
        writes = []
        original = blind.exclusive_write

        def record(path, data):
            writes.append(path.name)
            if path.name == "mapping.json":
                self.assertFalse((self.root / "blind").exists())
            original(path, data)

        with patch.object(blind.secrets, "SystemRandom") as random, patch.object(blind, "exclusive_write", record):
            random.return_value.shuffle.side_effect = lambda rows: rows.reverse()
            _, mapping, _ = self.render()
            random.return_value.shuffle.assert_called_once()
        self.assertEqual(writes, ["mapping.json", "RESPONSES.md", "RESPONSES.json"])
        self.assertEqual(mapping["slots"][1]["reading"]["readingId"], "R01")

    def test_active_result_and_inflight_slot_are_rejected(self):
        self.doc["status"] = "running"
        with self.assertRaises(ValueError): self.load()
        self.doc["status"] = "stopped"
        self.doc["slots"][0]["status"] = "dispatching"
        with self.assertRaises(ValueError): self.load()

    def test_result_hash_and_raw_response_hash_are_required(self):
        path = self.body(0, "original")
        self.load()
        with self.assertRaises(ValueError): blind.load_terminal(self.result, "0" * 64)
        path.write_bytes(b'{}')
        with self.assertRaises(ValueError): self.load()

    def test_exact_decoded_text_copy_is_checked(self):
        self.body(0, "original")
        path = self.run / "slot-01-text.txt"
        path.write_bytes(b"changed")
        self.doc["slots"][0]["text"] = {"path": str(path), "bytes": 7, "sha256": blind.sha(b"changed")}
        with self.assertRaises(ValueError): self.load()

    def test_evidence_must_stay_beside_ledger_and_not_follow_symlinks(self):
        path = self.body(0, "outside")
        outside = self.root / "outside.bin"
        outside.write_bytes(path.read_bytes())
        self.doc["slots"][0]["response"]["path"] = str(outside)
        with self.assertRaises(ValueError): self.load()
        path.unlink()
        path.symlink_to(outside)
        self.doc["slots"][0]["response"]["path"] = str(path)
        with self.assertRaises(ValueError): self.load()

    def test_ambiguous_content_is_not_guessed_optional_duplicates_do_not_hide_text(self):
        self.assertEqual(blind.response_text(b'{"message":{"content":"a","content":"b"}}')[0], None)
        self.assertEqual(blind.response_text(b'{"message":{"content":"a"},"message":{"content":"b"}}')[0], None)
        self.assertEqual(blind.response_text(b'{"message":{"content":"ok"},"prompt_eval_count":1,"prompt_eval_count":2}')[0], "ok")
        self.assertEqual(blind.response_text(b'{"message":{"content":"\\ud800"}}')[0], None)

    def test_no_overwrite_or_mapping_inside_reader_folder(self):
        slots, texts, identity = self.load()
        output, mapping = self.root / "blind", self.root / "mapping.json"
        with self.assertRaises(ValueError):
            blind.render(slots, texts, identity, output, output / "mapping.json")
        mapping.write_text("preserve")
        with self.assertRaises(ValueError): blind.render(slots, texts, identity, output, mapping)
        self.assertEqual(mapping.read_text(), "preserve")

    def test_slot_omission_reorder_and_false_unstarted_response_fail(self):
        self.doc["slots"].pop()
        with self.assertRaises(ValueError): self.load()
        self.doc["slots"].append({"slot": 12, "anchorStep": 360, "condition": "A", "status": "unstarted"})
        self.doc["slots"][0]["condition"] = "B"
        with self.assertRaises(ValueError): self.load()
        self.doc["slots"][0]["condition"] = "A"
        self.body(0, "unexpected", "unstarted")
        with self.assertRaises(ValueError): self.load()


if __name__ == "__main__":
    unittest.main()
