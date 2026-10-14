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


if __name__ == "__main__":
    unittest.main()
