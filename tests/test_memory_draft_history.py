"""Synthetic transform evidence and review-history fixtures; no run files or calls."""
import copy
import json
import unittest

from reservoir_experiments.correction_memory import (
    approve_memory_entry, digest, memory_review_packet, revise_memory_draft,
)


ORIGINAL = "This synthetic record preserves the supplied evidence and its uncertainty."
FIELDS = {"propositions": ["The supplied evidence remains uncertain."],
          "paraphrase": ORIGINAL, "notebook": "The supplied evidence remains uncertain."}
EMPTY_STATE_HASH = digest('{"notebook":null,"paraphrase":null,"propositions":[]}')


def draft(raw, status="incomplete"):
    protocol = {"id": "synthetic-transforms-v2", "protocol_version": 2,
                "split": "development", "model": "synthetic:fixture",
                "cases": [{"id": "synthetic-episode"}],
                "memory_sources": {"synthetic-episode": {
                    "source_id": "synthetic-episode-s7-target", "original": ORIGINAL,
                    "source_sha256": digest(ORIGINAL)}}}
    records = {"synthetic-episode-transform": {"status": status, "text": raw}}
    before = copy.deepcopy((protocol, records))
    entry = memory_review_packet(protocol, records)["memories"]["synthetic-episode"]
    assert before == (protocol, records)
    return entry


def reviewers(entry):
    return [{"name": name, "approved": True, "rationale": "Synthetic source fidelity checked.",
             "source_sha256": digest(entry["original"]),
             "paraphrase_sha256": digest(entry["paraphrase"]),
             "notebook_sha256": digest(entry["notebook"])}
            for name in ("fixture-reader-a", "fixture-reader-b")]


def repair(entry):
    return revise_memory_draft(entry, **FIELDS, editor="fixture-editor",
                               rationale="Pre-application repair against the retained source.")


class MemoryDraftHistoryTests(unittest.TestCase):
    def assert_unavailable(self, entry):
        self.assertEqual([], entry["propositions"])
        self.assertIsNone(entry["paraphrase"])
        self.assertIsNone(entry["notebook"])
        self.assertFalse(entry["reviewed"])
        with self.assertRaisesRegex(ValueError, "Missing memory text: paraphrase"):
            approve_memory_entry(entry, [])

    def test_incomplete_and_failed_raw_text_is_preserved_exactly(self):
        truncated = ' \r\n{"propositions": ["uncertain π"], "paraphrase": "unfinished'
        for status in ("incomplete", "transport_error"):
            for raw in (truncated, "", " \r\n"):
                with self.subTest(status=status, raw=raw):
                    entry = draft(raw, status)
                    self.assertEqual({"text": raw, "sha256": digest(raw), "status": status},
                                     entry["original_transform_draft"])
                    self.assertEqual(digest(raw), entry["transform_sha256"])
                    self.assert_unavailable(entry)

    def test_valid_json_incomplete_is_not_usable_without_logged_repair(self):
        raw = json.dumps(FIELDS)
        entry = draft(raw)
        self.assertEqual(raw, entry["original_transform_draft"]["text"])
        self.assert_unavailable(entry)
        entry.update(copy.deepcopy(FIELDS))
        with self.assertRaisesRegex(ValueError, "without a retained edit history"):
            approve_memory_entry(entry, reviewers(entry))

    def test_logged_repair_starts_from_unavailable_state_and_retains_raw_hash(self):
        for raw in ('{"paraphrase": "truncated', json.dumps(FIELDS)):
            with self.subTest(raw=raw):
                entry = draft(raw)
                revised = repair(entry)
                self.assertEqual(EMPTY_STATE_HASH, revised["edit_history"][0]["before_sha256"])
                self.assertEqual(entry["original_transform_draft"], revised["original_transform_draft"])
                self.assertEqual(digest(raw), revised["transform_sha256"])
                self.assertFalse(revised["reviewed"])
                self.assertEqual([], revised["reviewers"])
                approved = approve_memory_entry(revised, reviewers(revised))
                self.assertTrue(approved["reviewed"])
                second = revise_memory_draft(approved, **FIELDS, editor="another-fixture-editor",
                                             rationale="Retain a second logged pre-application review pass.")
                self.assertEqual(2, len(second["edit_history"]))
                self.assertFalse(second["reviewed"])
                self.assertTrue(approve_memory_entry(second, reviewers(second))["reviewed"])

    def test_original_raw_hash_and_edit_chain_tampering_fail_closed(self):
        entry = repair(draft(json.dumps(FIELDS)))
        for mutate in (lambda e: e["original_transform_draft"].update(text="changed"),
                       lambda e: e["original_transform_draft"].update(sha256="changed"),
                       lambda e: e.update(transform_sha256="changed"),
                       lambda e: e["edit_history"][0].update(before_sha256="changed")):
            changed = copy.deepcopy(entry)
            mutate(changed)
            with self.assertRaises(ValueError):
                approve_memory_entry(changed, reviewers(changed))

    def test_completed_and_legacy_completed_packets_still_approve(self):
        for status in ("complete", "completed"):
            with self.subTest(status=status):
                entry = draft(json.dumps(FIELDS), status)
                self.assertEqual(FIELDS, {key: entry[key] for key in FIELDS})
                approved = approve_memory_entry(entry, reviewers(entry))
                self.assertTrue(approved["reviewed"])
                revised = repair(approved)
                self.assertTrue(approve_memory_entry(revised, reviewers(revised))["reviewed"])
                legacy = copy.deepcopy(approved)
                legacy["transform_protocol_version"] = 1
                legacy.pop("original_transform_draft")
                legacy.pop("edit_history")
                self.assertEqual(legacy, approve_memory_entry(legacy, legacy["reviewers"]))

    def test_legacy_null_incomplete_draft_and_logged_repair_still_validate(self):
        entry = draft(None)
        self.assertEqual({"text": None, "sha256": None, "status": "incomplete"},
                         entry["original_transform_draft"])
        self.assertIsNone(entry["transform_sha256"])
        self.assert_unavailable(entry)
        # The earlier packet format started repairs from these same empty fields.
        entry["edit_history"] = [{"editor": "legacy-fixture-editor",
            "rationale": "Pre-application repair recorded by the prior packet workflow.",
            "before_sha256": EMPTY_STATE_HASH,
            "after_sha256": digest(json.dumps(FIELDS, sort_keys=True, ensure_ascii=False,
                                               allow_nan=False, separators=(",", ":"))),
            "after": copy.deepcopy(FIELDS)}]
        entry.update(copy.deepcopy(FIELDS))
        approved = approve_memory_entry(entry, reviewers(entry))
        self.assertTrue(approved["reviewed"])
        self.assertIsNone(approved["transform_sha256"])
        self.assertEqual(entry["edit_history"], approved["edit_history"])
        self.assertTrue(approve_memory_entry(repair(approved), reviewers(approved))["reviewed"])

    def test_array_valued_text_is_rejected_until_logged_repair(self):
        for field in ("paraphrase", "notebook"):
            with self.subTest(field=field):
                fields = {**FIELDS, field: [FIELDS[field]]}
                raw = json.dumps(fields)
                entry = draft(raw, "complete")
                self.assertEqual(fields[field], entry[field])
                with self.assertRaisesRegex(ValueError, "Missing memory text: " + field):
                    approve_memory_entry(entry, [])
                unlogged = copy.deepcopy(entry)
                unlogged[field] = FIELDS[field]
                with self.assertRaisesRegex(ValueError, "without a retained edit history"):
                    approve_memory_entry(unlogged, reviewers(unlogged))
                revised = repair(entry)
                self.assertTrue(approve_memory_entry(revised, reviewers(revised))["reviewed"])
                self.assertEqual(raw, revised["original_transform_draft"]["text"])
                self.assertEqual(digest(raw), revised["transform_sha256"])


if __name__ == "__main__":
    unittest.main()
