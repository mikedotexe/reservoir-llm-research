"""Scientific accounting invariants across study scorers."""
import unittest

from reservoir_experiments.correction_memory import build_correction
from reservoir_experiments.scoring import study_report


class ScoringTests(unittest.TestCase):
    def test_forecast_missingness_preserves_planned_pairs(self):
        protocol = build_correction("development")
        records = {}
        for node in protocol["nodes"]:
            if node["kind"] in ("target", "initial"):
                records[node["id"]] = {"status": "complete", "text": "VERDICT: " + protocol["truth"][node["id"]]["verdict"]}
            elif node["condition"] == "self":
                records[node["id"]] = {"status": "complete", "text": '{"p_supported":0.8,"explanation":"fixture"}'}
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
                text = '{"p_supported":' + ("0.8" if node["condition"] == "self" else "0.6") + "}"
            records[node["id"]] = {"status": "complete", "text": text}
        report = study_report(protocol, records)
        self.assertEqual(report["primary"]["paired_episodes"], 12)
        self.assertEqual(report["primary"]["valid_pairs"], 24)
        self.assertAlmostEqual(report["primary"]["difference"], -.12)
        self.assertTrue(report["primary"]["lower_is_better"])


if __name__ == "__main__":
    unittest.main()
