"""Synthetic figure checks; no protocols, responses, providers, or real scores."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from probes import introspection_matched_figure as figure


def summary(mean=.25, interval=None, *, valid=3, episodes=2):
    return {"mean": mean, "ci95_episode_bootstrap": interval,
            "planned_episode_seed_pairs": 24, "valid_episode_seed_pairs": valid,
            "unavailable_episode_seed_pairs": 24 - valid, "contributing_episodes": episodes,
            "bootstrap_draws": 1000, "bootstrap_seed": 20261024,
            "interval_scope": "Synthetic retained episode-bootstrap summary"}


def synthetic_comparison():
    """Small hand-specified summaries shaped like the private comparison helper."""
    report = {"schema_version": 1, "synthetic_validation_only": True,
              "plan_sha256": "0" * 64, "script_sha256": "1" * 64, "studies": {}}
    for study in figure.STUDIES:
        block = {"preselected_episodes": figure.expected_episodes(study), "models": {}}
        report["studies"][study] = block
        # Poison optional between-model and marginal quantities: none is displayed.
        block["cross_model_secondary_descriptive"] = {"mean": 987654321}
        for model, model_name in figure.MODELS.items():
            item = {"model": model_name, "split": figure.SPLITS[model], "within_model_contrasts": {}}
            block["models"][model] = item
            if study == "S-013":
                item["condition_means"] = {
                    condition: summary((index + (model == "mistral")) / 5, [0, 1])
                    for index, condition in enumerate(figure.CONDITIONS)}
            else:
                first, second = figure.CONTRASTS[study]
                estimate = .2 if study != "S-016" else 4.5
                interval = [-.1, .6] if study != "S-016" else [-2, 12]
                item["within_model_contrasts"][f"{first}_minus_{second}"] = {
                    "first": first, "second": second, "difference": summary(estimate, interval),
                    "first_on_same_pairs": summary(777), "second_on_same_pairs": summary(888)}
                item["condition_means"] = {first: summary(999), second: summary(998)}
    # Missing estimate, available estimate with no interval, and unequal support.
    report["studies"]["S-013"]["models"]["mistral"]["condition_means"]["absent"] = summary(None, valid=0, episodes=0)
    report["studies"]["S-014"]["models"]["gemma"]["within_model_contrasts"]["self_minus_observer"]["difference"] = summary(None, valid=0, episodes=0)
    report["studies"]["S-015"]["models"]["mistral"]["within_model_contrasts"]["original_minus_notebook"]["difference"] = summary(.75, valid=2, episodes=1)
    return report


class FigureDataTests(unittest.TestCase):
    def test_retained_within_model_contrasts_not_marginals_or_cross_model(self):
        panels = figure.prepare_panels(synthetic_comparison(), synthetic=True)
        row = panels["S-016"]["rows"][0]
        self.assertEqual(row["mean"], 4.5)
        self.assertEqual(row["ci95_episode_bootstrap"], [-2, 12])
        self.assertEqual(panels["S-013"]["xlim"], [0, 1])
        self.assertFalse(panels["S-013"]["intervals_displayed"])

    def test_asymmetric_interval_fits_symmetric_limits(self):
        panels = figure.prepare_panels(synthetic_comparison(), synthetic=True)
        for study in figure.CONTRASTS:
            low, high = panels[study]["xlim"]
            self.assertEqual(low, -high)
            for row in panels[study]["rows"]:
                for endpoint in row["ci95_episode_bootstrap"] or []:
                    self.assertLess(low, endpoint)
                    self.assertGreater(high, endpoint)

    def test_interval_not_containing_mean_is_retained(self):
        report = synthetic_comparison()
        row = report["studies"]["S-016"]["models"]["gemma"]["within_model_contrasts"]["full_minus_concise_padded"]["difference"]
        row.update(mean=-3, ci95_episode_bootstrap=[1, 2])
        displayed = figure.prepare_panels(report, synthetic=True)["S-016"]["rows"][0]
        self.assertEqual(displayed["mean"], -3)
        self.assertEqual(displayed["ci95_episode_bootstrap"], [1, 2])

    def test_missing_is_null_and_null_interval_stays_unavailable(self):
        panels = figure.prepare_panels(synthetic_comparison(), synthetic=True)
        missing = panels["S-014"]["rows"][0]
        self.assertIsNone(missing["mean"])
        self.assertEqual(figure.estimate_text(missing), "Estimate unavailable")
        self.assertEqual(figure.count_text(missing), "0/24 pairs · 0/12 episodes\n24 unavailable pairs")
        no_interval = panels["S-015"]["rows"][1]
        self.assertIsNone(no_interval["ci95_episode_bootstrap"])
        self.assertIn("interval unavailable", figure.estimate_text(no_interval))
        self.assertEqual(no_interval["contributing_episodes"], 1)

    def test_zero_and_all_missing_have_nonzero_contrast_scale(self):
        report = synthetic_comparison()
        for study in figure.CONTRASTS:
            first, second = figure.CONTRASTS[study]
            for item in report["studies"][study]["models"].values():
                item["within_model_contrasts"][f"{first}_minus_{second}"]["difference"] = summary(0, [0, 0])
        panels = figure.prepare_panels(report, synthetic=True)
        self.assertEqual(panels["S-016"]["xlim"], [-1, 1])
        self.assertEqual(panels["S-014"]["xlim"], [-.1, .1])
        for item in report["studies"]["S-014"]["models"].values():
            item["within_model_contrasts"]["self_minus_observer"]["difference"] = summary(None, valid=0, episodes=0)
        self.assertEqual(figure.prepare_panels(report, synthetic=True)["S-014"]["xlim"], [-.1, .1])

    def test_schema_identity_support_and_finite_values_fail_closed(self):
        report = synthetic_comparison()
        with self.assertRaisesRegex(ValueError, "synthetic flag"):
            figure.prepare_panels(report)
        for change in (lambda r: r["studies"].pop("S-016"),
                       lambda r: r["studies"]["S-013"]["preselected_episodes"].pop(),
                       lambda r: r["studies"]["S-013"]["models"]["gemma"].update(model="wrong")):
            other = copy.deepcopy(report)
            change(other)
            with self.assertRaises(ValueError):
                figure.prepare_panels(other, synthetic=True)
        for invalid in (summary(float("nan")), summary(True), summary(.5, [1, -1]),
                        summary(0, valid=0, episodes=0), summary(.5, valid=24, episodes=2)):
            with self.assertRaises(ValueError):
                figure.checked_summary(invalid, "S-014")

    def test_import_needs_no_optional_dependency_or_runner(self):
        program = ("import runpy, sys; runpy.run_path(sys.argv[1]); "
                   "assert 'matplotlib' not in sys.modules; "
                   "assert not any(n.startswith('reservoir_experiments') for n in sys.modules)")
        subprocess.run([sys.executable, "-S", "-c", program, str(Path(figure.__file__))], check=True)

    def test_path_guard_resolves_symlinks_and_rejects_public_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            private = base / "research" / "outputs"
            private.mkdir(parents=True)
            with patch.object(figure, "PRIVATE_ROOT", private):
                self.assertEqual(figure.private_path(private / "new" / "figure"), private / "new" / "figure")
                for path in (base / "published.png", private / ".." / "public.png"):
                    with self.assertRaisesRegex(ValueError, "private research/outputs"):
                        figure.private_path(path)
                (private / "escape").symlink_to(base, target_is_directory=True)
                with self.assertRaises(ValueError):
                    figure.private_path(private / "escape" / "published.png")


@unittest.skipUnless(importlib.util.find_spec("matplotlib"), "optional matplotlib is unavailable")
class FigureRenderTests(unittest.TestCase):
    def test_render_geometry_missingness_and_no_s013_intervals(self):
        panels = figure.prepare_panels(synthetic_comparison(), synthetic=True)
        canvas, axes, _ = figure.build_figure(panels, synthetic=True)
        canvas.canvas.draw()
        self.assertEqual(axes["S-013"].get_xlim(), (0, 1))
        self.assertEqual(len(axes["S-013"].collections), 0)
        self.assertEqual(len(axes["S-013"].lines), 9)  # One absent estimate gets no dot.
        self.assertIn("unavailable", [t.get_text() for t in axes["S-014"].texts])
        # Horizontal segments retain asymmetric endpoints exactly.
        segment = axes["S-016"].collections[0].get_segments()[0]
        self.assertEqual(list(segment[:, 0]), [-2, 12])
        labels = "\n".join(t.get_text() for a in canvas.axes for t in a.texts)
        self.assertIn("interval unavailable", labels)
        self.assertIn("24 unavailable pairs", labels)
        canvas.clear()

    def test_exclusive_private_outputs_receipt_hashes_and_input_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            private = Path(directory).resolve() / "research" / "outputs"
            private.mkdir(parents=True)
            source = private / "synthetic.json"
            raw = (json.dumps(synthetic_comparison()) + "\n").encode()
            source.write_bytes(raw)
            with patch.object(figure, "PRIVATE_ROOT", private):
                paths = figure.render(source, private / "figure", synthetic=True, dpi=72)
                receipt = json.loads(Path(paths["json"]).read_text())
                self.assertEqual(receipt["input"]["sha256"], hashlib.sha256(raw).hexdigest())
                self.assertEqual(receipt["code_sha256"], hashlib.sha256(Path(figure.__file__).read_bytes()).hexdigest())
                for ext in ("png", "svg"):
                    self.assertEqual(receipt["outputs_sha256"][ext], hashlib.sha256(Path(paths[ext]).read_bytes()).hexdigest())
                self.assertTrue(Path(paths["png"]).read_bytes().startswith(b"\x89PNG"))
                self.assertIn("SYNTHETIC FIXTURE", Path(paths["svg"]).read_text())
                self.assertIn("<text", Path(paths["svg"]).read_text())
                self.assertEqual(source.read_bytes(), raw)
                retained = {ext: Path(path).read_bytes() for ext, path in paths.items()}
                with self.assertRaisesRegex(ValueError, "overwrite"):
                    figure.render(source, private / "figure", synthetic=True)
                for ext, path in paths.items():
                    self.assertEqual(Path(path).read_bytes(), retained[ext])
                with self.assertRaisesRegex(ValueError, "overwrite"):
                    figure.render(source, private / "synthetic", synthetic=True)
                self.assertFalse((private / "synthetic.png").exists())


if __name__ == "__main__":
    unittest.main()
