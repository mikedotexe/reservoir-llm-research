"""Qualification-checker protocol tests; not numerical conformance evidence."""
import json
import unittest

from check_controller_export import CURSORS, prefix_matches, rust_report_matches


def result(value, code=0):
    return {"exitCode": code, "stdout": json.dumps(value)}


class ControllerExportProtocolTests(unittest.TestCase):
    def test_acceptance_requires_complete_counts_and_no_contact_claim(self):
        valid = {"status": "passed", "checkedSteps": 1200, "checkedTurns": 0, "modelsContacted": False}
        self.assertTrue(rust_report_matches(result(valid), True))
        for key, value in [("checkedSteps", 600), ("checkedTurns", 1), ("modelsContacted", True), ("status", "incomplete")]:
            self.assertFalse(rust_report_matches(result({**valid, key: value}), True))
        self.assertFalse(rust_report_matches(result(valid, None), True))

    def test_unknown_or_unparseable_negative_is_not_rejection(self):
        self.assertTrue(rust_report_matches(result({"status": "failed"}, 1), False))
        for status, code in [("incomplete", 2), ("passed", 0), ("failed", None), ("incomplete", 1)]:
            self.assertFalse(rust_report_matches(result({"status": status}, code), False))
        self.assertFalse(rust_report_matches({"exitCode": 1, "stdout": "not JSON"}, False))

    def test_prefix_equality_alone_cannot_accept_missing_sequence(self):
        equal = lambda a, b: a == b
        rows = [{"cursor": cursor, "evidence": None} for cursor in CURSORS]
        self.assertTrue(prefix_matches(result(rows), result(rows), equal))
        for incomplete in [[], rows[:-1], list(reversed(rows))]:
            self.assertFalse(prefix_matches(result(incomplete), result(incomplete), equal))
        self.assertFalse(prefix_matches(result(rows, None), result(rows), equal))

    def test_prefix_comparator_failure_and_malformed_output_do_not_pass(self):
        rows = [{"cursor": cursor, "evidence": None} for cursor in CURSORS]
        self.assertFalse(prefix_matches(result(rows), result(rows), lambda a, b: False))
        self.assertFalse(prefix_matches(result({}), result({}), lambda a, b: True))
        self.assertFalse(prefix_matches({"exitCode": 0, "stdout": ""}, result(rows), lambda a, b: True))


if __name__ == "__main__":
    unittest.main()
