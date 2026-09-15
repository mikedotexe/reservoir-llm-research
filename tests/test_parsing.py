"""Synthetic fixtures reproduce inspected formats without copying private prose."""

from datetime import datetime, timezone
import unittest

from reservoir_research.parsing import filename_timestamp, parse_journal


class JournalParsingTests(unittest.TestCase):
    def test_astrid_epoch_mode_and_percent(self):
        result = parse_journal("=== ASTRID JOURNAL ===\nMode: dialogue_live\nFill: 73.0%\nTimestamp: 1788736645\n\nA question remains.\nNEXT: **READ_MORE** page\n", "astrid", "!astrid_1788736645.txt")
        self.assertEqual(result["occurred_at"], 1788736645.0)
        self.assertEqual(result["lane"], "dialogue_live")
        self.assertEqual(result["content_kind"], "prose")
        self.assertEqual(result["metadata"]["fill_percent"], 73.0)
        self.assertEqual(result["body_text"], "A question remains.")
        self.assertEqual(result["next_raw"], "**READ_MORE** page")
        self.assertEqual(result["next_verb"], "READ_MORE")

    def test_modern_wrappers_aware_time_and_notice(self):
        raw = """=== MOMENT CAPTURE ===
Timestamp: 2026-09-06T23:06:20+00:00
Prompt contract: private_moment_context_v3
Prompt captured at (UTC): 2026-09-06T23:05:00+00:00
Prompt-state anchor (supplied to model):
Fill=71.0%, lambda1_cov=8.535

Header-only telemetry:
λ₁: 8.53
Fill %: 71.0%
Cov λ₁: 8.5

--- GENERATED JOURNAL ---
Could a distinction travel across contexts?

[Pressure-vocabulary cooldown — narrative preserved.
An appended notice [with a nested bracket].]

--- ACTION TAIL ---
NEXT: DAYDREAM
"""
        result = parse_journal(raw, "minime", "moment_2026-09-06T16-06-20.txt")
        self.assertEqual(result["time_source"], "header_aware_utc")
        self.assertEqual(result["occurred_at"], datetime(2026, 9, 6, 23, 6, 20, tzinfo=timezone.utc).timestamp())
        self.assertEqual(result["body_text"], "Could a distinction travel across contexts?")
        self.assertEqual(result["contract"], "private_moment_context_v3")
        self.assertEqual(result["next_verb"], "DAYDREAM")
        self.assertIn("system_notice_removed", result["warnings"])
        self.assertIn("lambda1_provenance_ambiguous_raw_label_retained", result["warnings"])
        self.assertNotIn("lambda1", result["metadata"])

    def test_naive_local_time_and_filename_prefilter(self):
        raw = "=== RECESS DAYDREAM ===\nTimestamp: 2026-09-06T16:06:20.123456\nFill %: 68.4%\n\nAn ordinary passage."
        result = parse_journal(raw, "minime", "!daydream_2026-09-06T16-06-20.123456.txt")
        expected = datetime(2026, 9, 6, 23, 6, 20, 123456, tzinfo=timezone.utc).timestamp()
        self.assertEqual(result["occurred_at"], expected)
        self.assertEqual(filename_timestamp("daydream_2026-09-06T16-06-20.123456.txt", "Minime"), expected)
        self.assertIn("naive_timestamp_assumed_America/Los_Angeles", result["warnings"])

    def test_aware_header_takes_precedence_over_filename(self):
        result = parse_journal("=== BOREDOM ===\nTimestamp: 2026-09-06T10:00:00-04:00\n\nA note.", "minime", "boredom_2026-09-06T10-00-00.txt")
        self.assertEqual(result["occurred_at"], datetime(2026, 9, 6, 14, tzinfo=timezone.utc).timestamp())
        self.assertIn("header_filename_timestamp_disagree", result["warnings"])

    def test_dst_invalid_dates_and_epoch_boundaries(self):
        self.assertIsNone(filename_timestamp("moment_2026-11-01T01-30-00.txt", "minime"))
        self.assertIsNone(filename_timestamp("moment_2026-03-08T02-30-00.txt", "minime"))
        self.assertIsNone(filename_timestamp("moment_2026-02-31T10-30-00.txt", "minime"))
        self.assertIsNone(filename_timestamp("astrid_1788736645000.txt", "astrid"))
        self.assertEqual(filename_timestamp("astrid_1788736645.txt", "astrid"), 1788736645)

    def test_last_next_outside_both_fence_types(self):
        raw = """=== RECESS DAYDREAM ===
Timestamp: 2026-09-06T16:00:00

NEXT: NOTICE
```text
NEXT: REST
```
~~~text
NEXT: EXAMINE
~~~
NEXT: `SHADOW_DECOMPOSE` focus <end_of_turn>
"""
        result = parse_journal(raw, "minime", "daydream_2026-09-06T16-00-00.txt")
        self.assertEqual(result["next_verb"], "SHADOW_PREFLIGHT")
        self.assertIn("NEXT: REST", result["body_text"])
        self.assertNotIn("NEXT: NOTICE", result["body_text"])
        self.assertIn("multiple_next_lines_last_used", result["warnings"])

    def test_source_supported_aliases_and_transcript_rejection(self):
        cases = {"EXEXPERIMENT_PLAN": "EXPERIMENT_PLAN", "EXPERIENCE_PLAN": "EXPERIMENT_PLAN",
                 "WEAVE_TRACE focus": "SHADOW_PREFLIGHT", "UNSHAPED_BASELINE": "CONSTRAINT_AUDIT",
                 "RESEARCH_BUDGET_STATUS latest": "EXPERIMENT_RESEARCH_BUDGET_STATUS",
                 "RESEARCH_BUDGET_STATUS keep_floor": "EXPERIMENT_RESEARCH_BUDGET_STATUS",
                 "STABLE_CORE_EXPERIMENTS": "ACTION_PREFLIGHT", "KEEP_FLOOR 0.1": "ACTION_PREFLIGHT",
                 "EXPERIMENT_RUN failed: test": None}
        for action, expected in cases.items():
            with self.subTest(action=action):
                result = parse_journal(f"=== BOREDOM ===\nTimestamp: 2026-09-06T16:00:00\n\nA note.\nNEXT: {action}", "minime", "boredom.txt")
                self.assertEqual(result["next_verb"], expected)

    def test_operational_and_explicit_steward_records(self):
        raw = "=== ASTRID JOURNAL ===\nMode: pressure_source_audit\nFill: 73.0%\nTimestamp: 1788736649\n\n=== PRESSURE SOURCE AUDIT REVIEW SUMMARY ===\nAction: PRESSURE_SOURCE_AUDIT\n"
        self.assertEqual(parse_journal(raw, "astrid", "astrid_1788736649.txt")["content_kind"], "operational")
        steward = parse_journal("A steward letter with no journal header.", "astrid", "mike_feedback_example_1788736649.txt")
        self.assertEqual(steward["content_kind"], "steward")
        self.assertEqual(steward["body_text"], "A steward letter with no journal header.")

    def test_assistant_summary_style_does_not_change_prose_kind(self):
        raw = "=== GROWTH ASPIRATION ===\nTimestamp: 2026-09-06T16:00:00\nPrompt: A supplied question?\n\nOkay, I'm holding this continuity state. A question remains."
        result = parse_journal(raw, "minime", "aspiration.txt")
        self.assertEqual(result["content_kind"], "prose")
        self.assertIn("assistant_summary_candidate", result["metadata"]["style_flags"])
        self.assertNotIn("A supplied question?", result["body_text"])

    def test_unknown_format_preserved_and_no_body_metric_inference(self):
        raw = "A text I cannot confidently split.\n\nFill: 81.0% is something I remember."
        result = parse_journal(raw, "astrid", "unusual.txt")
        self.assertEqual(result["body_text"], raw)
        self.assertEqual(result["content_kind"], "unknown")
        self.assertIsNone(result["occurred_at"])
        self.assertNotIn("fill_percent", result["metadata"])

    def test_unclosed_fence_and_notice_are_conservative(self):
        result = parse_journal("=== BOREDOM ===\nTimestamp: 2026-09-06T16:00:00\n\nA note.\n[Agency-vernacular notice incomplete\n```text\nNEXT: REST", "minime", "boredom.txt")
        self.assertIsNone(result["next_verb"])
        self.assertIn("[Agency-vernacular", result["body_text"])
        self.assertIn("unclosed_code_fence", result["warnings"])
        self.assertIn("unclosed_system_notice_preserved", result["warnings"])

    def test_reservoir_resonance_separates_both_header_blocks_from_mixed_prose(self):
        metrics = "Minime <-> Astrid resonance:\n  divergence: 1.148252\n  correlation: -0.8545\n  trajectory RMSD: 2.512466"
        body = "Could two perspectives change together?\n\nINBOX_REPLY literal_target\n\nMike, a second question remains."
        raw = "=== RESERVOIR RESONANCE ===\nTimestamp: 2026-09-06T19:29:13.844347\nλ₁: 4.73\nFill %: 69.1%\n\n" + metrics + "\n\n" + body + "\nNEXT: SHADOW_TRAJECTORY tail\n"
        result = parse_journal(raw, "minime", "reservoir_resonance_2026-09-06T19-29-13.844338.txt")
        self.assertEqual(result["entry_type"], "reservoir_resonance")
        self.assertEqual(result["lane"], "reservoir_resonance")
        self.assertEqual(result["content_kind"], "prose")
        self.assertEqual(result["body_text"], body)
        self.assertIn(metrics, result["header_text"])
        self.assertEqual(result["metadata"]["resonance_block"], {"raw_text": metrics, "model_exposure": "unknown"})
        self.assertEqual(result["metadata"]["parser_version"], "journal-v2")
        self.assertEqual(result["metadata"]["fill_percent"], 69.1)
        self.assertEqual(result["next_verb"], "SHADOW_TRAJECTORY")

    def test_resonance_prose_and_unrecognized_block_are_preserved(self):
        for body in ("I mentioned resonance.\n\nMinime <-> Astrid resonance:\n  divergence: an example",
                     "Minime <-> Astrid resonance:\nA prose passage follows this heading."):
            with self.subTest(body=body):
                raw = "=== RESERVOIR RESONANCE ===\nTimestamp: 2026-09-06T19:29:13\n\n" + body
                result = parse_journal(raw, "minime", "resonance.txt")
                self.assertEqual(result["body_text"], body)
                self.assertNotIn("resonance_block", result["metadata"])


if __name__ == "__main__":
    unittest.main()
