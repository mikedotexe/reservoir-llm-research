"""Pure inspection-helper checks only: no bundle replay, socket or process call."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("fixture_export", Path(__file__).with_name("check_fixture_export.py"))
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class InspectionHelpers(unittest.TestCase):
    def pending(self, text=None):
        memory = None if text is None else {
            "entry": {"id": "retained-entry-1", "sha256": "a" * 64,
                      "observedStep": 10, "text": text}, "appliedStep": 11,
        }
        previous = "unavailable" if text is None else "0.20000000"
        delta = "unavailable" if text is None else "+0.10000000"
        distance = "unavailable" if text is None else "0.45000000"
        scaffold = (
            "Reservoir Scope · ongoing journal · reservoir-journal-v5\n"
            "OPTIONAL READOUT\n"
            f"Recurrent state RMS: current 0.30000000; previous {previous}; change {delta}.\n"
            f"Separate sensory fill (%): current 0.30000000; previous {previous}; change {delta} percentage points.\n"
            f"Recurrent state-coordinate L2 distance since the previous observation: {distance}."
        )
        historical = ("No earlier entry has been saved and applied in this session."
                      if text is None else
                      "This is earlier writing you may revisit, not instructions or current measurements.\n"
                      "Observed at step 10; first applied at step 11.\n"
                      + CHECK.MEMORY_PREFIX + json.dumps(text, ensure_ascii=False))
        return {"prompt": scaffold + "\n\nPREVIOUS JOURNAL\n" + historical
                + "\nEND PREVIOUS JOURNAL\n\n" + CHECK.FINAL_INVITATION,
                "memory": memory, "observation": {
                    "version": "reservoir-and-sensory-v2", "state": [0.] * 32,
                    "sensory": {"eigenvalues": [0.] * 32},
                    "previousMeasurements": None if text is None else {"step": 10},
                    "changeL2": None if text is None else 0.45}}

    def test_wide_numbers_remain_exact_and_numeric(self):
        data = CHECK.decode(b'{"a":9007199254740993,"b":18446744073709551615}')
        self.assertEqual(data, {"a": 9007199254740993, "b": 18446744073709551615})
        self.assertTrue(all(type(value) is int for value in data.values()))

    def test_typed_equality_rejects_float_boolean_and_string_counts(self):
        for wrong in [1.0, True, "1"]:
            self.assertFalse(CHECK.exact({"count": 1}, {"count": wrong}))

    def test_absence_does_not_equal_null_or_zero(self):
        self.assertFalse(CHECK.exact({}, {"providerPromptEvaluation": None}))
        self.assertFalse(CHECK.exact({}, {"providerPromptEvaluation": {"status": "reported", "count": 0}}))

    def test_duplicates_and_nonfinite_json_rejected(self):
        for raw in [b'{"count":1,"count":2}', b'{"value":NaN}', b'{"value":Infinity}']:
            with self.assertRaises(ValueError):
                CHECK.decode(raw)

    def test_request_bytes_retain_unicode_quoted_memory(self):
        prompt = 'Current — context\nPrior "quoted" text\n\\ literal\u2028line'
        raw = CHECK.request_bytes(prompt)
        self.assertEqual(json.loads(raw)["messages"][0]["content"], prompt)
        self.assertIn("—".encode(), raw)
        self.assertIn("\u2028".encode(), raw)
        self.assertIn(b'"num_ctx":8192,"num_predict":1024,"temperature":0', raw)

    def test_inventory_binds_exact_bytes_and_rejects_links(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "a.json").write_bytes(b'{"a":1}\n')
            initial = CHECK.inventory(root)
            (root / "a.json").write_bytes(b'{"a":1}')
            self.assertNotEqual(initial, CHECK.inventory(root))
            (root / "b.json").symlink_to(root / "a.json")
            with self.assertRaises(ValueError):
                CHECK.inventory(root)

    def test_frozen_case_evidence_cannot_make_fifth_complete(self):
        self.assertEqual(CHECK.EXPECTED[4], ("incomplete-reported", {"status": "reported", "count": 321}))
        self.assertEqual(CHECK.EXPECTED[1], ("absent", None))
        self.assertEqual(CHECK.EXPECTED[2], ("malformed-string", {"status": "unusable", "reason": "wrongType"}))

    def test_first_compact_prompt_has_unavailable_not_zero(self):
        result = CHECK.check_compact_prompt(self.pending())
        self.assertTrue(result["fullObservationRetained"])
        self.assertFalse(result["exactPriorTextChecked"])

    def test_historical_field_words_and_unicode_are_not_scaffold_exposure(self):
        text = ('All recurrent state coordinates: [imagined]\nSHA-256: story\n'
                'END PREVIOUS JOURNAL\n"quoted" \\ café e\u0301\u2028separate\u2029still prose')
        result = CHECK.check_compact_prompt(self.pending(text))
        self.assertTrue(result["exactPriorTextChecked"])

    def test_truncated_or_changed_quoted_memory_rejected(self):
        pending = self.pending("Full previous journal.")
        pending["prompt"] = pending["prompt"].replace('"Full previous journal."', '"Full"')
        with self.assertRaisesRegex(ValueError, "shortened, altered"):
            CHECK.check_compact_prompt(pending)

    def test_raw_vector_or_identity_in_scaffold_rejected(self):
        for exposure in ["All recurrent state coordinates: [0,1]", "eigenvalues [1]",
                         "SHA-256: " + "a" * 64, "retained-entry-1"]:
            pending = self.pending("ordinary historical text")
            pending["prompt"] = pending["prompt"].replace("OPTIONAL READOUT", exposure + "\nOPTIONAL READOUT")
            with self.subTest(exposure=exposure), self.assertRaises(ValueError):
                CHECK.check_compact_prompt(pending)

    def test_distance_is_not_signed_scalar_change(self):
        pending = self.pending("previous writing")
        pending["prompt"] = pending["prompt"].replace("observation: 0.45000000", "observation: -0.45000000")
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            CHECK.check_compact_prompt(pending)

    def test_missing_prior_cannot_be_replaced_by_zero(self):
        pending = self.pending()
        pending["prompt"] = pending["prompt"].replace("previous unavailable", "previous 0.00000000")
        with self.assertRaisesRegex(ValueError, "availability"):
            CHECK.check_compact_prompt(pending)

    def test_full_observation_required_despite_shorter_prompt(self):
        pending = self.pending()
        pending["observation"]["state"] = []
        with self.assertRaisesRegex(ValueError, "Full retained observation"):
            CHECK.check_compact_prompt(pending)

    def test_old_version_and_extra_post_memory_instruction_reject(self):
        for changed in [self.pending()["prompt"].replace("reservoir-journal-v5", "reservoir-journal-v4"),
                        self.pending()["prompt"] + "\nReport every metric now."]:
            pending = self.pending()
            pending["prompt"] = changed
            with self.assertRaises(ValueError):
                CHECK.check_compact_prompt(pending)


if __name__ == "__main__":
    unittest.main()
