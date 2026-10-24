import unittest

from reservoir_experiments.statistics import paired_contrast, summarize


class StatisticsTests(unittest.TestCase):
    def test_pairs_before_averaging_and_preserves_missingness(self):
        rows = [dict(episode=e, seed=s, condition=c, kind="target", valid=True, score=v)
                for e, s, c, v in [("a", 7, "x", 1), ("a", 7, "y", 0),
                                    ("a", 8, "x", 0), ("b", 7, "x", 0),
                                    ("b", 7, "y", 0)]]
        rows.append(dict(episode="a", seed=8, condition="y", kind="target", valid=False, score=None))
        result = paired_contrast(rows, "x", "y", draws=100)
        self.assertEqual(result["valid_pairs"], 2)
        self.assertEqual(result["difference"], .5)
        self.assertEqual(result["episode_differences"], {"a": 1, "b": 0})
        self.assertEqual(summarize(rows)[1]["unavailable"], 1)

    def test_no_valid_pairs_is_not_zero_effect(self):
        self.assertIsNone(paired_contrast([], "x", "y", draws=10)["difference"])

    def test_duplicate_cells_refused(self):
        row = dict(episode="a", seed=7, condition="x", valid=True, score=1)
        with self.assertRaises(ValueError):
            paired_contrast([row, row], "x", "y")

    def test_nonfinite_and_bool_are_not_scores(self):
        for score in (float("nan"), float("inf"), True):
            rows = [dict(episode="a", seed=7, condition="x", valid=True, score=score)]
            self.assertIsNone(summarize(rows)[0]["mean_valid"])


if __name__ == "__main__":
    unittest.main()
