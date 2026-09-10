import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE = Path(__file__).resolve().parents[1] / "probes/study_evidence_revision.py"
spec = importlib.util.spec_from_file_location("study_evidence_revision", MODULE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
review_spec = importlib.util.spec_from_file_location("study_evidence_revision_review", MODULE.with_name("study_evidence_revision_review.py"))
review_probe = importlib.util.module_from_spec(review_spec)
review_spec.loader.exec_module(review_probe)


class FrozenRevisionTests(unittest.TestCase):
    def test_recalled_bytes_and_order_survive_additional_material(self):
        original = "first evidence\n\nRECALLED ACCOUNT — your study notebook\nold wrong account\nolder account"
        baseline = probe.messages_for("same system", original, "")
        variant = probe.messages_for("same system", original, "newly supplied roles/source")
        self.assertEqual(baseline[1]["content"], original)
        self.assertEqual(baseline[0], variant[0])
        marker = "RECALLED ACCOUNT — your study notebook"
        self.assertEqual(original.split(marker)[1], variant[1]["content"].split(marker)[1])
        self.assertLess(variant[1]["content"].index("newly supplied"), variant[1]["content"].index(marker))

    def test_ambiguous_notebook_boundary_is_rejected(self):
        with self.assertRaises(ValueError):
            probe.messages_for("system", "no notebook", "source")

    def test_outcome_cannot_overwrite_an_existing_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "result.json"
            probe.save(path, {"outcome": "resource_limit"})
            with self.assertRaises(FileExistsError):
                probe.save(path, {"outcome": "better response"})
            self.assertEqual(json.loads(path.read_text())["outcome"], "resource_limit")

    def test_numbered_source_is_exact_and_bounded(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.rs"
            path.write_text("one\ntwo\nthree\n")
            self.assertEqual(probe.numbered(path, 2, 3), "2: two\n3: three")
            with self.assertRaises(ValueError):
                probe.numbered(path, 0, 4)

    def test_review_preserves_missing_and_unavailable_cells(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            specs = [{"id": "one", "seed": 91, "arm": "retained"}, {"id": "two", "seed": 91, "arm": "source"}]
            probe.save(root / "protocol.json", {"trials": specs, "cases": {"retained": [], "source": []}})
            probe.save(root / "one.json", {"spec": specs[0], "outcome": "cell_wall_resource_limit", "result": None})
            result = review_probe.review(root)
            self.assertEqual(result["planned"], 2)
            self.assertEqual(result["outcomes"], {"cell_wall_resource_limit": 1, "missing": 1})
            self.assertEqual(result["matched_nonempty_seeds"], [])
            self.assertEqual(result["arms"]["retained"]["tokens"], [])

    def test_choice_in_code_block_does_not_replace_final_authored_choice(self):
        result = review_probe.authored_fields("```\nNEXT: FALSE\n```\nSTUDY_NOTE: I am uncertain.\nNEXT: SELF_STUDY CONTINUE")
        self.assertEqual(result["NEXT"], "SELF_STUDY CONTINUE")
        self.assertEqual(result["STUDY_NOTE"], "I am uncertain.")
        self.assertIsNone(result["STUDY_QUESTION"])


if __name__ == "__main__":
    unittest.main()
