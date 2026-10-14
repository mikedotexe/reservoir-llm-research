"""Pure fixture checks: no socket, child process, app, or model service."""
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("input_evidence_fixture", Path(__file__).with_name("owned_provider.py"))
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class FixtureTests(unittest.TestCase):
    def request(self, **changes):
        body = {"model": fixture.MODEL, "stream": False,
                "messages": [{"role": "user", "content": "Owned synthetic prompt."}],
                "options": {"num_predict": 1024, "temperature": 0, "num_ctx": 8192}}
        body.update(changes)
        return json.dumps(body).encode()

    def test_wide_numbers_retain_integer_lexemes(self):
        for index, number in [(1, 9007199254740993), (4, 18446744073709551615)]:
            _, raw = fixture.response_for(index)
            self.assertIn(f'"prompt_eval_count":{number}'.encode(), raw)
            self.assertEqual(json.loads(raw)["prompt_eval_count"], number)

    def test_missing_and_malformed_are_complete_unchanged_prose(self):
        _, absent = fixture.response_for(2)
        _, malformed = fixture.response_for(3)
        self.assertNotIn("prompt_eval_count", json.loads(absent))
        self.assertEqual(json.loads(malformed)["prompt_eval_count"], "2450")
        self.assertTrue(json.loads(absent)["done"])
        self.assertTrue(json.loads(malformed)["done"])

    def test_incomplete_is_not_a_complete_fixture_response(self):
        _, raw = fixture.response_for(5)
        body = json.loads(raw)
        self.assertFalse(body["done"])
        self.assertEqual(body["done_reason"], "length")
        self.assertEqual(body["prompt_eval_count"], 321)

    def test_bounded_sequence_has_no_retry_or_wrap(self):
        for n in [0, 6, -1]:
            with self.assertRaises(ValueError): fixture.response_for(n)

    def test_request_metadata_omits_prompt_body(self):
        raw = self.request()
        retained = fixture.validate_request(raw)
        self.assertEqual(retained["requestSha256"], fixture.digest(raw))
        self.assertNotIn("Owned synthetic prompt", json.dumps(retained))
        self.assertEqual(retained["promptBytes"], len(b"Owned synthetic prompt."))

    def test_wrong_model_budget_and_shape_reject(self):
        for changes in [{"model": "not-the-fixture"}, {"stream": True},
                        {"options": {"num_predict": 256, "temperature": 0, "num_ctx": 8192}},
                        {"messages": []}, {"format": "json"}]:
            with self.assertRaises(ValueError): fixture.validate_request(self.request(**changes))

    def test_request_bound_and_scalar_reject(self):
        for raw in [b"", b"[]", b"null", b" " * (fixture.MAX_REQUEST_BYTES + 1)]:
            with self.assertRaises((ValueError, TypeError)): fixture.validate_request(raw)


if __name__ == "__main__":
    unittest.main()
