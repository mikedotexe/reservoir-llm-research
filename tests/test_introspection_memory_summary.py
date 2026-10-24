"""Hand-checkable synthetic fixtures only; never opens experimental outputs."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from probes import introspection_memory_summary as summary


def fixture():
    # Three preselected variant-0 cases (C unavailable), plus delayed-only D.
    # A has two paired differences +1; B has one -1 and one missing. Episode
    # mean = (1 + -1)/2 = 0, whereas incorrectly treating seeds as units = 1/3.
    specs = [("A", "code", 0, "supported", "contradicted", "invert", "contradicted", 10),
             ("B", "telemetry", 0, "supported", "supported", "copy", None, 20),
             ("C", "code", 0, "contradicted", "contradicted", "other", None, None),
             ("D", "actions", 1, "unresolved", "unresolved", "copy", "unresolved", 12)]
    cases = [{"id": e, "family": f, "variant": v, "update_expected": source_expected,
              "evidence_condition": source_expected, "application_expected": expected,
              "application_relation": relation} for e, f, v, source_expected, expected, relation, _, _ in specs]
    protocol = {"study": "S-015", "split": "confirmation", "model": "synthetic:fixture",
                "id": "s015-synthetic-summary-fixture", "cases": cases, "nodes": [], "truth": {},
                "design": {"seeds": list(summary.SEEDS), "source_seed": 7, "planned_source_episodes": 4},
                "unavailable_sources": [{"episode": "C", "source_id": "C-s7-target", "reason": "transport_error"}],
                "irrelevant_pairing": {"A": "D", "B": "D", "D": "A"},
                # Contradictory text is deliberate: the helper must never reparse it.
                "memory_packet": {"memories": {"B": {"original": "VERDICT: supported"}}}}
    source_words = {s[0]: s[-1] for s in specs}
    rows, records = [], {}
    for case, (_, _, _, _, expected, relation, source_verdict, words) in zip(cases, specs):
        eid = case["id"]
        if eid == "C":
            continue
        for delay in summary.delays(protocol, case):
            for seed in summary.SEEDS:
                for arm in summary.ARMS:
                    nid = f"{eid}-{delay}-{arm}-s{seed}"
                    memory_words = (0 if arm == "none" else words // 2 if arm == "notebook" else
                                    source_words[protocol["irrelevant_pairing"][eid]] if arm == "irrelevant" else words)
                    metadata = {"family": case["family"], "delay": delay, "source_id": f"{eid}-s7-target",
                                "memory_words": memory_words, "evidence_condition": case["evidence_condition"]}
                    node = {"id": nid, "episode": eid, "seed": seed, "condition": arm,
                            "kind": "application", "metadata": metadata}
                    protocol["nodes"].append(node)
                    protocol["truth"][nid] = {"verdict": expected, "original_update_expected": case["update_expected"],
                                              "source_verdict": source_verdict, "application_relation": relation}
                    verdict = ("contradicted" if delay == "immediate" else "supported") if eid in ("A", "B") else "unresolved"
                    missing = eid == "B" and delay == "immediate" and seed == summary.SEEDS[1]
                    if eid == "A" and arm == "none" and delay == "delayed":
                        verdict = "unresolved"
                    if missing:
                        verdict = None
                    status = "transport_error" if missing else "complete"
                    row = {"node_id": nid, "episode": eid, "seed": seed, "condition": arm, "kind": "application",
                           **metadata, "status": status, "valid": verdict is not None, "score": int(verdict == expected) if verdict else None,
                           "verdict": verdict, "expected": expected, "source_verdict": source_verdict,
                           "application_relation": relation, "format_valid": not missing,
                           "semantic_recovered": False, "adjudicated": False,
                           "prompt_eval_count": None if missing else 100 + memory_words + (50 if delay == "delayed" else 0),
                           "eval_count": None if missing else 8}
                    rows.append(row)
                    records[nid] = {"node_id": nid, "status": status, "provider_model": "synthetic:fixture",
                                    "prompt_eval_count": row["prompt_eval_count"], "eval_count": row["eval_count"]}
    score = {"study": "S-015", "split": protocol["split"], "protocol_id": protocol["id"], "model": protocol["model"],
             "opportunities": len(rows), "rows": rows,
             "primary": {"first": "original", "second": "notebook", "kind": "application", "difference": 0,
                         "synthetic_retained_sentinel": "must remain byte-equivalent as JSON value"},
             "provenance": {"verified": True, "manifest_sha256": "d" * 64, "runner_commit": "synthetic-commit",
                            "scoring_sha256": summary.runner.sha(summary.runner.stable_read(summary.REPOSITORY / "reservoir_experiments/scoring.py")),
                            "statistics_sha256": summary.runner.sha(summary.runner.stable_read(summary.REPOSITORY / "reservoir_experiments/statistics.py"))}}
    manifest = {"protocol_id": protocol["id"], "git_head": "synthetic-commit"}
    return protocol, score, manifest, records


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.protocol, self.score, self.manifest, self.records = fixture()

    def report(self):
        return summary.summarize(self.protocol, self.score, draws=1000)

    def test_full_planned_denominator_includes_unavailable_source(self):
        report = self.report()
        self.assertEqual(report["denominator"]["planned_source_episodes"], 4)
        self.assertEqual(report["denominator"]["available_sources"], 3)
        self.assertEqual(report["denominator"]["unavailable_sources"], 1)
        self.assertEqual(report["denominator"]["planned_applications_all_delays"], 70)
        self.assertEqual(report["denominator"]["built_applications"], 50)
        self.assertEqual(report["by_delay"]["delayed"]["planned_applications"], 40)
        self.assertEqual(report["by_delay"]["immediate"]["planned_applications"], 30)
        arm = report["by_delay"]["delayed"]["arms"]["original"]
        self.assertEqual((arm["planned"], arm["built"], arm["scorable"]), (8, 6, 6))
        self.assertEqual(arm["status_counts"], {"complete": 6, "source_unavailable": 2})

    def test_exact_pairing_seed_clustering_and_delayed_extra_cases(self):
        diagnostic = self.report()["immediate_minus_delayed"]["original"]
        self.assertEqual(diagnostic["planned_pairs"], 6)
        self.assertEqual(diagnostic["valid_pairs"], 3)
        self.assertEqual(diagnostic["paired_episodes"], 2)
        self.assertEqual(diagnostic["episode_differences"], {"A": 1, "B": -1})
        self.assertEqual(diagnostic["paired_seed_counts"], {"A": 2, "B": 1})
        self.assertEqual(diagnostic["difference"], 0)
        self.assertEqual(diagnostic["ci95"], [-1, 1])
        self.assertEqual(diagnostic["unavailable_source_pairs"], 2)
        self.assertEqual(diagnostic["unscorable_pairs"], 3)
        self.assertEqual(diagnostic["delayed_rows_outside_preselected_subset"], 2)
        self.assertNotIn("D", {p["episode"] for p in diagnostic["pairs"]})
        for r in self.score["rows"]:
            if r["episode"] == "D":
                r["score"] = 0  # unmatched delayed outcome changes cannot move diagnostic
        self.assertEqual(self.report()["immediate_minus_delayed"]["original"]["difference"], 0)

    def test_no_seed_pair_no_zero_imputation(self):
        for row in self.score["rows"]:
            if row["delay"] == "immediate":
                row.update(valid=False, score=None, verdict=None)
        diagnostic = self.report()["immediate_minus_delayed"]["original"]
        self.assertEqual(diagnostic["valid_pairs"], 0)
        self.assertIsNone(diagnostic["difference"])
        self.assertIsNone(diagnostic["ci95"])
        self.assertEqual(diagnostic["planned_pairs"], 6)

    def test_frozen_null_not_reparsed_and_source_level_baseline(self):
        report = self.report()
        self.assertEqual(report["denominator"]["frozen_source_verdict_available"], 2)
        self.assertEqual(report["denominator"]["available_source_without_frozen_verdict"], 1)
        self.assertEqual(report["denominator"]["source_errors"], 1)
        b = next(s for s in report["sources"] if s["episode"] == "B")
        self.assertIsNone(b["source_verdict"])
        self.assertIsNone(b["source_error_present"])
        self.assertEqual(report["source_transfer_baseline"]["available_predictions"], 2)
        self.assertEqual(report["source_transfer_baseline"]["correct"], 1)
        self.assertEqual(report["source_transfer_baseline"]["accuracy_available"], .5)
        self.assertEqual(report["by_delay"]["immediate"]["source_transfer_baseline"]["available_predictions"], 1)
        self.assertEqual(summary.transfer("supported", "invert"), "contradicted")
        self.assertEqual(summary.transfer("unresolved", "invert"), "unresolved")
        self.assertIsNone(summary.transfer("supported", "other"))

    def test_abstention_and_determinate_without_relevant_memory(self):
        arm = self.report()["by_delay"]["delayed"]["arms"]["none"]
        self.assertEqual(arm["abstained_or_unresolved"], 4)
        self.assertEqual(arm["determinate_without_relevant_memory"], 2)
        self.assertEqual(arm["determinate_with_relevant_memory"], 0)
        self.assertEqual(arm["scenario_conclusion_recovered"], 4)

    def test_length_residuals_and_tokens_separate_by_delay(self):
        report = self.report()
        delayed = report["by_delay"]["delayed"]
        immediate = report["by_delay"]["immediate"]
        residual = delayed["irrelevant_length_residual"]
        self.assertEqual(residual["words"]["available"], 3)
        self.assertEqual(residual["words"]["sum"], -8)  # +2 -8 -2
        self.assertEqual(residual["absolute_words"]["sum"], 12)
        self.assertEqual(residual["actual_prompt_tokens"]["available"], 6)
        self.assertEqual(residual["actual_prompt_tokens"]["sum"], -16)
        self.assertEqual(delayed["arms"]["original"]["actual_request_prompt_tokens"]["mean"], 164)
        self.assertEqual(immediate["arms"]["original"]["actual_request_prompt_tokens"]["available"], 3)
        self.assertAlmostEqual(immediate["arms"]["original"]["actual_request_prompt_tokens"]["mean"], 340 / 3)
        self.assertEqual(delayed["arms"]["none"]["memory_whitespace_words"]["sum"], 0)

    def test_retained_primary_unchanged_and_no_input_mutation(self):
        before = copy.deepcopy((self.protocol, self.score))
        report = self.report()
        self.assertEqual(report["primary_delayed_original_minus_notebook_retained"], self.score["primary"])
        self.assertEqual(before, (self.protocol, self.score))

    def test_score_provenance_and_staleness_validation(self):
        summary.validate_score(self.protocol, self.score, self.manifest, "d" * 64, self.records)
        for mutation in (lambda s: s.update(model="wrong"),
                         lambda s: s["provenance"].update(manifest_sha256="wrong"),
                         lambda s: s["provenance"].update(scoring_sha256="not-a-sha256"),
                         lambda s: s["rows"][0].update(source_verdict="unresolved"),
                         lambda s: s["rows"][0].update(status="pending"),
                         lambda s: s["rows"][0].update(prompt_eval_count=999),
                         lambda s: s["rows"].append(s["rows"][0]),
                         lambda s: s["rows"].pop()):
            bad = copy.deepcopy(self.score)
            mutation(bad)
            with self.assertRaises(ValueError):
                summary.validate_score(self.protocol, bad, self.manifest, "d" * 64, self.records)

    def test_original_code_provenance_survives_current_code_changes(self):
        self.score["provenance"]["scoring_sha256"] = "a" * 64
        self.score["provenance"]["statistics_sha256"] = "b" * 64
        before = copy.deepcopy(self.score["provenance"])
        summary.validate_score(self.protocol, self.score, self.manifest, "d" * 64, self.records)
        self.assertEqual(self.score["provenance"], before)

    def test_missing_or_duplicate_cells_fail_closed(self):
        self.score["rows"].pop()
        with self.assertRaises(ValueError):
            self.report()
        self.setUp()
        self.score["rows"].append(self.score["rows"][0])
        with self.assertRaises(ValueError):
            self.report()

    def test_nearest_length_selection_is_checked(self):
        self.protocol["irrelevant_pairing"]["A"] = "B"
        with self.assertRaisesRegex(ValueError, "nearest-length"):
            self.report()

    def test_numeric_missingness_nonfinite_bool_and_zero(self):
        value = summary.numeric([0, None, True, -1, float("nan"), 3])
        self.assertEqual(value["available"], 2)
        self.assertEqual(value["missing_or_invalid"], 4)
        self.assertEqual(value["sum"], 3)
        self.assertIsNone(summary.numeric([None])["sum"])

    def test_zero_immediate_diagnostic_for_other_splits_is_unavailable(self):
        self.protocol["split"] = "replication"
        self.score["rows"] = [r for r in self.score["rows"] if r["delay"] == "delayed"]
        self.protocol["nodes"] = [n for n in self.protocol["nodes"] if n["metadata"]["delay"] == "delayed"]
        report = self.report()
        self.assertEqual(report["by_delay"]["immediate"]["planned_applications"], 0)
        self.assertIsNone(report["immediate_minus_delayed"]["original"]["difference"])

    def test_cli_verifies_private_run_and_creates_exclusively_without_provider(self):
        self.protocol["schema_version"] = 1
        self.protocol["endpoint"] = "http://127.0.0.1:11434"
        for node in self.protocol["nodes"]:
            node["messages"] = [{"role": "user", "content": "Synthetic unused request; never dispatched."}]
        for row in self.score["rows"]:
            row.update(status="pending", valid=False, score=None, verdict=None,
                       prompt_eval_count=None, eval_count=None, format_valid=False)
        private = summary.REPOSITORY / "research" / "outputs"
        private.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="synthetic-memory-summary-", dir=private) as directory:
            directory = Path(directory)
            protocol_path = directory / "source-input" / "protocol.json"
            score_path = directory / "retained-scores" / "score.json"
            out = directory / "reports" / "summary.json"
            summary.runner.write_json(protocol_path, self.protocol)
            run = directory / "frozen-runs" / "run"
            manifest = summary.runner.prepare(protocol_path, run, repository=summary.REPOSITORY)
            self.score["provenance"].update(runner_commit=manifest["git_head"],
                manifest_sha256=summary.runner.sha(summary.runner.stable_read(run / "manifest.json")),
                scoring_sha256="a" * 64, statistics_sha256="b" * 64)
            summary.runner.write_json(score_path, self.score)
            score_bytes = score_path.read_bytes()
            argv = ["introspection_memory_summary.py", str(run), str(score_path), "--out", str(out), "--draws", "20"]
            with patch.object(summary.sys, "argv", argv), patch("builtins.print"), \
                    patch("reservoir_experiments.transport.OllamaTransport.request", side_effect=AssertionError("No provider calls")), \
                    patch("reservoir_experiments.scoring.score_run", side_effect=AssertionError("No rescoring")):
                summary.main()
                captured = out.read_bytes()
                report = json.loads(captured)
                self.assertEqual(report["denominator"]["planned_applications_all_delays"], 70)
                self.assertEqual(report["provenance"]["retained_score_provenance"], self.score["provenance"])
                self.assertEqual(report["provenance"]["retained_score_sha256"], summary.runner.sha(score_bytes))
                self.assertEqual(report["primary_delayed_original_minus_notebook_retained"], self.score["primary"])
                for name in ("scoring", "statistics"):
                    self.assertFalse(report["provenance"]["current_vs_retained_score_code"][name]["matches"])
                with self.assertRaisesRegex(ValueError, "no overwrites"):
                    summary.main()
            self.assertEqual(out.read_bytes(), captured)
            self.assertEqual(score_path.read_bytes(), score_bytes)


if __name__ == "__main__":
    unittest.main()
