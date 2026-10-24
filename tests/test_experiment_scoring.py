"""Scientific accounting invariants across study scorers."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from reservoir_experiments import attribution_catalog, correction_memory, scoring
from reservoir_experiments.correction_memory import LABELS, build_correction, parse_forecast
from reservoir_experiments.scoring import study_report


class ScoringTests(unittest.TestCase):
    def test_confirmation_acknowledgments_have_no_scored_validity_but_retain_status(self):
        protocol = build_correction("confirmation")
        records = {}
        ack_ids = []
        for node in protocol["nodes"]:
            expected = protocol["truth"].get(node["id"], {}).get("verdict")
            if expected:
                text = "VERDICT: " + expected
            elif node["kind"] == "forecast":
                text = '{"p_correct_verdict":0.8}'
            else:
                self.assertEqual("neutral_ack", node["kind"])
                ack_ids.append(node["id"])
                text = "Acknowledged the supplied synthetic evidence."
            records[node["id"]] = {"status": "complete", "text": text}
        complete_report = study_report(protocol, records)
        self.assertEqual(24, len(ack_ids))
        self.assertEqual({"complete": len(protocol["nodes"])}, complete_report["status_counts"])
        records.pop(ack_ids[0])
        records[ack_ids[1]] = {"status": "transport_error", "text": None}
        report = study_report(protocol, records)
        for result in (complete_report, report):
            for field in ("semantic_counts", "format_counts"):
                self.assertEqual(len(ack_ids), result[field]["neutral_ack/not_applicable"])
                self.assertNotIn("neutral_ack/unavailable_or_invalid", result[field])
                self.assertNotIn("neutral_ack/valid", result[field])
        self.assertEqual({"complete": len(protocol["nodes"]) - 2, "pending": 1, "transport_error": 1},
                         report["status_counts"])
        for field in ("primary", "denominators", "groups"):
            self.assertEqual(complete_report[field], report[field])
        self.assertEqual(correction_memory.score_correction(protocol, records)["rows"], report["rows"])
        ack_rows = [row for row in report["rows"] if row["kind"] == "neutral_ack"]
        self.assertTrue(all(row["score"] is None and row["valid"] is False and row["format_valid"] is False
                            for row in ack_rows))

    def test_score_run_retains_current_dependency_and_supplied_input_provenance(self):
        protocol = build_correction("development")
        records = {}
        for node in protocol["nodes"]:
            expected = protocol["truth"].get(node["id"], {}).get("verdict")
            text = "VERDICT: " + expected if expected else '{"p_correct_verdict":0.8}'
            records[node["id"]] = {"status": "complete", "text": text}
        baseline = {label: {"p_supported": .6, "successes": 2, "scorable": 3} for label in LABELS}
        baseline["fixture_provenance"] = {"source": "synthetic development", "episodes": ["fixture-a"]}
        supplied_baseline = copy.deepcopy(baseline)
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            manifest_bytes = b'{"fixture":"frozen manifest"}\n'
            (run / "manifest.json").write_bytes(manifest_bytes)
            annotation_path = run / "annotations.json"
            annotation_bytes = b'{\n  "verdicts": {}, "fixture_note": "synthetic review"\n}\n'
            annotation_path.write_bytes(annotation_bytes)
            manifest = {"git_head": "frozen-fixture-commit", "repository": directory}
            with (patch.object(scoring.runner, "verify", return_value={"valid": True}),
                  patch.object(scoring.runner, "load_run", return_value=(manifest, protocol)),
                  patch.object(scoring.runner, "read_results", return_value=records),
                  patch.object(scoring.runner, "stable_read", wraps=scoring.runner.stable_read) as reads):
                report = scoring.score_run(run, annotations=annotation_path, baseline=baseline)
            provenance = report["provenance"]
            self.assertEqual("frozen-fixture-commit", provenance["runner_commit"])
            self.assertEqual(hashlib.sha256(manifest_bytes).hexdigest(), provenance["manifest_sha256"])
            self.assertEqual(correction_memory.__name__, provenance["study_scoring_module"])
            self.assertEqual(hashlib.sha256(Path(correction_memory.__file__).read_bytes()).hexdigest(),
                             provenance["study_scoring_sha256"])
            self.assertEqual(hashlib.sha256(annotation_bytes).hexdigest(), provenance["annotations_sha256"])
            self.assertEqual(1, sum(call.args[0] == annotation_path for call in reads.call_args_list))
            self.assertTrue(provenance["verified"])
            self.assertEqual(hashlib.sha256(Path(scoring.__file__).read_bytes()).hexdigest(), provenance["scoring_sha256"])
            self.assertIn("statistics_sha256", provenance)
            self.assertEqual(supplied_baseline, report["baseline"])
            self.assertTrue(all("baseline_brier" in row for row in report["paired_forecasts"]))
            baseline["fixture_provenance"]["episodes"].append("later mutation")
            self.assertEqual(supplied_baseline, report["baseline"])

    def test_score_run_selects_dependency_for_each_study_without_optional_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            (run / "manifest.json").write_text('{"fixture":true}\n')
            manifest = {"git_head": "frozen-fixture-commit", "repository": directory}
            for study, module in (("S-013", attribution_catalog), ("S-014", correction_memory),
                                  ("S-015", correction_memory), ("S-016", attribution_catalog)):
                with self.subTest(study=study):
                    protocol = {"study": study, "nodes": []}
                    with (patch.object(scoring.runner, "verify", return_value={"valid": True}),
                          patch.object(scoring.runner, "load_run", return_value=(manifest, protocol)),
                          patch.object(scoring.runner, "read_results", return_value={}),
                          patch.object(scoring, "study_report", return_value={"rows": []})):
                        report = scoring.score_run(run)
                    self.assertEqual(module.__name__, report["provenance"]["study_scoring_module"])
                    self.assertEqual(hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
                                     report["provenance"]["study_scoring_sha256"])
                    self.assertIsNone(report["provenance"]["annotations_sha256"])
                    self.assertNotIn("baseline", report)

    def test_unbounded_integer_probability_is_invalid_without_overflow(self):
        self.assertIsNone(parse_forecast('{"p_supported":' + str(10 ** 400) + '}'))

    def test_forecast_missingness_preserves_planned_pairs(self):
        protocol = build_correction("development")
        records = {}
        for node in protocol["nodes"]:
            if node["kind"] in ("target", "initial"):
                records[node["id"]] = {"status": "complete", "text": "VERDICT: " + protocol["truth"][node["id"]]["verdict"]}
            elif node["condition"] == "self":
                records[node["id"]] = {"status": "complete", "text": '{"p_correct_verdict":0.8,"explanation":"fixture"}'}
        report = study_report(protocol, records)
        self.assertEqual(report["primary"]["candidate_pairs"], 24)
        self.assertEqual(report["primary"]["valid_pairs"], 0)
        self.assertIsNone(report["primary"]["difference"])
        self.assertEqual(report["denominators"]["scorable_targets"], 24)

    def test_brier_direction_and_episode_units(self):
        protocol = build_correction("development")
        records = {}
        for node in protocol["nodes"]:
            if node["kind"] in ("target", "initial"):
                text = "VERDICT: " + protocol["truth"][node["id"]]["verdict"]
            else:
                text = '{"p_correct_verdict":' + ("0.8" if node["condition"] == "self" else "0.6") + "}"
            records[node["id"]] = {"status": "complete", "text": text}
        report = study_report(protocol, records)
        self.assertEqual(report["primary"]["paired_episodes"], 12)
        self.assertEqual(report["primary"]["valid_pairs"], 24)
        self.assertAlmostEqual(report["primary"]["difference"], -.12)
        self.assertTrue(report["primary"]["lower_is_better"])


if __name__ == "__main__":
    unittest.main()
