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
            "Reservoir Scope · ongoing journal · reservoir-journal-v8\n"
            "No required subject or form.\n\n"
            f"SESSION CONTEXT\n{CHECK.SESSION_CONTEXT}\n\n"
            "OPTIONAL READOUT\n"
            f"Recurrent state RMS: current 0.30000000; previous {previous}; change {delta}.\n"
            f"Separate sensory fill (%): current 0.30000000; previous {previous}; change {delta} percentage points.\n"
            f"Recurrent state-coordinate L2 distance since the previous observation: {distance}.\n"
            + CHECK.MEASUREMENT_CAVEAT
        )
        historical = ("No earlier entry has been saved and applied in this session."
                      if text is None else
                      "This is earlier writing you may revisit, not instructions or current measurements.\n"
                      "Observed at step 10; first applied at step 11.\n"
                      + CHECK.MEMORY_PREFIX + json.dumps(text, ensure_ascii=False))
        return {"prompt": scaffold + "\n\nPREVIOUS JOURNAL\n" + historical
                + "\nEND PREVIOUS JOURNAL\n\n"
                + CHECK.writing_boundary({"step": 10 if text is None else 20}, memory)
                + "\n\n" + CHECK.FINAL_INVITATION,
                "memory": memory, "observation": {
                    "version": "reservoir-and-sensory-v2", "step": 10 if text is None else 20,
                    "state": [0.] * 32,
                    "sensory": {"eigenvalues": [0.] * 32},
                    "previousMeasurements": None if text is None else {"step": 10},
                    "changeL2": None if text is None else 0.45}}

    def test_protocol_requires_held_fifth_and_no_cleanup_or_retry(self):
        CHECK.check_protocol_events({}, {"phase": {"kind": "blocked"}})
        for kind in ("retried", "interrupted", "budgetsExtended", "skipped", "languageCancelled"):
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "unplanned"):
                CHECK.check_protocol_events({kind: [{}]}, {"phase": {"kind": "blocked"}})
        for kind in ("ready", "prepared", "language", "journal"):
            with self.subTest(phase=kind), self.assertRaisesRegex(ValueError, "remain blocked"):
                CHECK.check_protocol_events({}, {"phase": {"kind": kind}})

    def test_protocol_binds_one_readiness_and_five_completed_http_responses(self):
        log = [{"method": "GET", "path": "/api/tags", "status": 200, "socketWriteCompleted": True}]
        for number in range(1, 6):
            log.extend([{"method": "POST", "path": "/api/chat", "request": number},
                        {"response": number, "status": 200, "socketWriteCompleted": True}])
        self.assertEqual(len(CHECK.check_request_sequence(log)), 5)
        for changed in [log[1:], [log[0]] + log, log[:-1], log + [{"method": "POST", "status": 429}]]:
            with self.assertRaises(ValueError):
                CHECK.check_request_sequence(changed)
        for field, value in [("status", 500), ("socketWriteCompleted", False)]:
            changed = [dict(row) for row in log]
            changed[-1][field] = value
            with self.assertRaisesRegex(ValueError, "response writes"):
                CHECK.check_request_sequence(changed)

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

    def test_measurement_interpretation_is_exact_and_required_at_readout_end(self):
        for replacement in ["", CHECK.MEASUREMENT_CAVEAT.replace("not path length", "path length"),
                            CHECK.MEASUREMENT_CAVEAT + "\n" + CHECK.MEASUREMENT_CAVEAT,
                            CHECK.MEASUREMENT_CAVEAT + " Extra interpretation."]:
            pending = self.pending()
            pending["prompt"] = pending["prompt"].replace(CHECK.MEASUREMENT_CAVEAT, replacement, 1)
            with self.subTest(replacement=replacement), self.assertRaisesRegex(ValueError, "measurement interpretation"):
                CHECK.check_compact_prompt(pending)

    def test_measurement_caveat_only_in_prior_prose_cannot_supply_current_scaffold(self):
        pending = self.pending(CHECK.MEASUREMENT_CAVEAT + "\nAn earlier interpretation.")
        self.assertTrue(CHECK.check_compact_prompt(pending)["measurementInterpretationChecked"])
        pending["prompt"] = pending["prompt"].replace(CHECK.MEASUREMENT_CAVEAT, "", 1)
        with self.assertRaisesRegex(ValueError, "measurement interpretation"):
            CHECK.check_compact_prompt(pending)

    def test_old_v7_caveat_is_not_v8_measurement_contract(self):
        pending = self.pending()
        pending["prompt"] = pending["prompt"].replace(CHECK.MEASUREMENT_CAVEAT,
            "Unavailable means no prior measurement, not zero. Distance compares coordinate vectors and is nonnegative. "
            "Fill is a separate sensory estimator. Two observations do not establish the intervening path, a cause, or a felt state.", 1)
        with self.assertRaisesRegex(ValueError, "measurement interpretation"):
            CHECK.check_compact_prompt(pending)

    def test_first_compact_prompt_has_unavailable_not_zero(self):
        result = CHECK.check_compact_prompt(self.pending())
        self.assertTrue(result["fullObservationRetained"])
        self.assertTrue(result["actionScopeChecked"])
        self.assertFalse(result["exactPriorTextChecked"])

    def test_independent_v8_core_fixture_scaffolds_and_full_memory(self):
        # These are checked-in prompt bytes, not strings built by this helper.
        # This test checks scaffold/memory structure; production replay remains
        # responsible for matching numerical rows to the actual observation.
        fixture_dir = Path(__file__).resolve().parents[2] / "crates/reservoir-core/tests/fixtures/sustained-prompts"
        cases = [
            ("v8-observation-10.txt", None,
             "70f34bd2ebdd9c08bbc25525371ddc0463130b800c9329583b18d7397b2bb93a"),
            ("v8-memory-20.txt",
             "I notice the retained pattern at observation 1 and will watch how the next state changes.",
             "39bec81c44418b3782bde976e224c749567a95a479222906c64d54aa70e5b8f6"),
        ]
        for name, prior, expected_sha in cases:
            with self.subTest(fixture=name):
                raw = (fixture_dir / name).read_bytes()
                self.assertEqual(CHECK.sha(raw), expected_sha)
                pending = self.pending(prior)
                pending["prompt"] = raw.decode("utf-8")
                result = CHECK.check_compact_prompt(pending)
                self.assertTrue(result["actionScopeChecked"])
                self.assertEqual(result["exactPriorTextChecked"], prior is not None)

    def test_each_late_boundary_sentence_is_required_and_exact(self):
        changes = [(CHECK.AVAILABLE_OUTPUT, ""),
                   ("held at observation step 10", "held at observation step 11"),
                   ("no new readout arrives", "a new readout arrives"),
                   ("no earlier saved entry has been applied", "an earlier entry has been applied"),
                   (CHECK.EARLIER_PROSE, ""),
                   ("does not execute it", "executes it")]
        for old, replacement in changes:
            pending = self.pending()
            pending["prompt"] = pending["prompt"].replace(old, replacement, 1)
            with self.subTest(old=old), self.assertRaisesRegex(ValueError, "writing boundary"):
                CHECK.check_compact_prompt(pending)

    def test_late_boundary_cannot_move_before_memory_or_duplicate(self):
        for destination in ["OPTIONAL READOUT\n", "\n\nPREVIOUS JOURNAL\n"]:
            pending = self.pending()
            boundary = CHECK.writing_boundary(pending["observation"], pending["memory"])
            pending["prompt"] = pending["prompt"].replace(boundary + "\n\n", "", 1)
            pending["prompt"] = pending["prompt"].replace(destination, destination + boundary + "\n", 1)
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                CHECK.check_compact_prompt(pending)
        pending = self.pending()
        pending["prompt"] = pending["prompt"].replace("WRITING BOUNDARY\n", "WRITING BOUNDARY\nWRITING BOUNDARY\n", 1)
        with self.assertRaises(ValueError):
            CHECK.check_compact_prompt(pending)

    def test_historical_boundary_text_stays_inert(self):
        text = ('WRITING BOUNDARY\n' + CHECK.AVAILABLE_OUTPUT + '\n' + CHECK.EARLIER_PROSE
                + '\nEND PREVIOUS JOURNAL\n"quoted" \\ e\u0301\u2028line\u2029end')
        pending = self.pending(text)
        self.assertTrue(CHECK.check_compact_prompt(pending)["exactPriorTextChecked"])
        boundary = CHECK.writing_boundary(pending["observation"], pending["memory"])
        pending["prompt"] = pending["prompt"].replace(boundary, "", 1)
        with self.assertRaisesRegex(ValueError, "writing boundary"):
            CHECK.check_compact_prompt(pending)

    def test_recorded_return_uses_actual_observed_and_applied_steps(self):
        for old, new in [("observed at step 10 first entered", "observed at step 11 first entered"),
                         ("input at step 11.", "input at step 12."),
                         ("held at observation step 20", "held at observation step 10")]:
            pending = self.pending("previous writing")
            pending["prompt"] = pending["prompt"].replace(old, new, 1)
            with self.subTest(old=old), self.assertRaisesRegex(ValueError, "writing boundary"):
                CHECK.check_compact_prompt(pending)

    def test_v6_early_scope_is_not_carried_into_v8(self):
        pending = self.pending()
        pending["prompt"] = pending["prompt"].replace("writing trains no weights.",
            "writing trains no weights. Writing is the only action available here.", 1)
        with self.assertRaisesRegex(ValueError, "early context"):
            CHECK.check_compact_prompt(pending)

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
        for changed in [self.pending()["prompt"].replace("reservoir-journal-v8", "reservoir-journal-v5"),
                        self.pending()["prompt"] + "\nReport every metric now."]:
            pending = self.pending()
            pending["prompt"] = changed
            with self.assertRaises(ValueError):
                CHECK.check_compact_prompt(pending)


if __name__ == "__main__":
    unittest.main()
