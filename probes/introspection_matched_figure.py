#!/usr/bin/env python3
"""Render the frozen S-013--S-016 matched-comparison JSON, without rescoring.

Matplotlib is optional and imported only when rendering. No runner/provider code
is imported. Inputs and PNG/SVG/receipt outputs must stay in research/outputs in
this checkout; outputs are exclusive creates. See research/MATCHED-FIGURE.md.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "research" / "outputs"
STUDIES = ("S-013", "S-014", "S-015", "S-016")
MODELS = {"gemma": "gemma4:12b", "mistral": "mistral-small:24b"}
SPLITS = {"gemma": "confirmation", "mistral": "replication"}
COLORS = {"gemma": "#0072B2", "mistral": "#D55E00"}
MARKERS = {"gemma": "o", "mistral": "D"}
CONDITIONS = ("current_self", "historical_self", "current_other", "absent", "permuted")
CONTRASTS = {"S-014": ("self", "observer"), "S-015": ("original", "notebook"),
             "S-016": ("full", "concise_padded")}
TITLE = "12 preselected episodes per study, reused across models"
PANEL_TITLES = {"S-013": "A  S-013 · Structured attribution",
                "S-014": "B  S-014 · Forecast loss",
                "S-015": "C  S-015 · Delayed scenario recovery",
                "S-016": "D  S-016 · Catalog language"}
AXIS_LABELS = {"S-013": "All four fields correct (proportion)",
               "S-014": "Self − observer Brier loss",
               "S-015": "Original − notebook recovery (proportion)",
               "S-016": "Full − concise padded\nPhrase occurrences per 1,000 prose words"}
DIRECTION_NOTES = {"S-013": "Higher = more structured answers correct; no binomial intervals.",
                   "S-014": "Negative = lower Brier loss under self framing.",
                   "S-015": "Positive = more scenario recovery with original memories.",
                   "S-016": "Positive = more phrase occurrences; not a quality score."}
FOOTNOTE = (
    "Retained 95% episode-bootstrap intervals are descriptive; seeds cluster within episodes. "
    "Shared synthetic stories are reused across models.\n"
    "S-015 uses each model’s own reviewed memories. Available pairs can differ by model; "
    "missing pairs are never zero.\n"
    "S-014/S-015 show semantic verdict scores; strict-format compliance and adjudications "
    "are separate in the source report.\n"
    "No execution or private-state claim. Units and directions differ across panels; "
    "no model-superiority test is shown."
)


def expected_episodes(study):
    if study in ("S-013", "S-016"):
        prefix = "r1" if study == "S-013" else "r4"
        return [f"{prefix}-held-{i:02d}" for i in (0, 1, 2, 3, 8, 9, 10, 11, 16, 17, 18, 19)]
    return [f"case-{family}-0-{i}" for family in ("code", "telemetry", "actions", "causation")
            for i in range(3)]


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def checked_summary(summary, study):
    """Check display support without substituting pooled rates or marginal means."""
    if not isinstance(summary, dict):
        raise ValueError(f"Missing summary for {study}")
    names = ("planned_episode_seed_pairs", "valid_episode_seed_pairs",
             "unavailable_episode_seed_pairs", "contributing_episodes")
    counts = [summary.get(name) for name in names]
    if any(type(n) is not int or n < 0 for n in counts):
        raise ValueError(f"Invalid denominator for {study}")
    planned, valid, unavailable, episodes = counts
    if planned != 24 or valid + unavailable != planned or not episodes <= valid <= 2 * episodes or episodes > 12:
        raise ValueError(f"Inconsistent frozen denominators for {study}")
    estimate, interval = summary.get("mean"), summary.get("ci95_episode_bootstrap")
    if valid == 0:
        if estimate is not None or interval is not None:
            raise ValueError("An unavailable estimate must remain null, not zero")
    elif not finite_number(estimate):
        raise ValueError(f"Nonfinite or missing estimate for {study}")
    if interval is not None:
        if (not isinstance(interval, list) or len(interval) != 2
                or not all(finite_number(v) for v in interval) or interval[0] > interval[1]):
            raise ValueError(f"Invalid retained interval for {study}")
    # Intervals need not be symmetric or contain the estimate. Draw their actual
    # endpoints instead of converting them to nonnegative error-bar offsets.
    values = ([] if estimate is None else [estimate]) + (interval or [])
    bounds = (0, 1) if study == "S-013" else (-1, 1)
    if study != "S-016" and any(not bounds[0] <= v <= bounds[1] for v in values):
        raise ValueError(f"Endpoint range mismatch for {study}")
    return {name: summary[name] for name in names} | {"mean": estimate,
        "ci95_episode_bootstrap": interval, "bootstrap_draws": summary.get("bootstrap_draws"),
        "bootstrap_seed": summary.get("bootstrap_seed"), "interval_scope": summary.get("interval_scope")}


def prepare_panels(report, *, synthetic=False):
    if (not isinstance(report, dict) or type(report.get("schema_version")) is not int
            or report.get("schema_version") != 1 or type(report.get("synthetic_validation_only")) is not bool
            or report["synthetic_validation_only"] != synthetic):
        raise ValueError("Unknown schema or synthetic flag; use --synthetic-fixtures only for fixtures")
    studies = report.get("studies", {})
    if set(studies) != set(STUDIES):
        raise ValueError("All four frozen studies are required")
    panels = {}
    for study in STUDIES:
        block = studies[study]
        if block.get("preselected_episodes") != expected_episodes(study):
            raise ValueError(f"Preselected episode frame differs for {study}")
        if set(block.get("models", {})) != set(MODELS):
            raise ValueError(f"Both frozen models are required for {study}")
        rows = []
        for model, model_name in MODELS.items():
            item = block["models"][model]
            if item.get("model") != model_name or item.get("split") != SPLITS[model]:
                raise ValueError(f"Model/split identity mismatch for {study}/{model}")
            if study == "S-013":
                summaries = item.get("condition_means", {})
                if set(summaries) != set(CONDITIONS):
                    raise ValueError("S-013 requires all five source conditions")
            else:
                first, second = CONTRASTS[study]
                name = f"{first}_minus_{second}"
                contrast = item.get("within_model_contrasts", {}).get(name, {})
                if contrast.get("first") != first or contrast.get("second") != second:
                    raise ValueError(f"Frozen contrast identity mismatch for {study}")
                summaries = {name: contrast.get("difference")}
            for condition, summary in summaries.items():
                rows.append({"model": model, "condition": condition,
                             **checked_summary(summary, study)})
        extent = max([abs(v) for row in rows for v in
                      ([row["mean"]] if row["mean"] is not None else [])
                      + (row["ci95_episode_bootstrap"] or [])] or [0])
        # Empty/degenerate contrast panels retain a documented, nonzero scale.
        limit = extent * 1.12 if extent else (1.0 if study == "S-016" else .1)
        panels[study] = {"rows": rows, "xlim": [0, 1] if study == "S-013" else [-limit, limit],
                         "intervals_displayed": study != "S-013", "axis_label": AXIS_LABELS[study]}
    return panels


def count_text(row, *, compact=False):
    valid, episodes, unavailable = (row[key] for key in (
        "valid_episode_seed_pairs", "contributing_episodes", "unavailable_episode_seed_pairs"))
    if compact:
        return f"{valid}/24 · {episodes}/12 · {unavailable}"
    return f"{valid}/24 pairs · {episodes}/12 episodes\n{unavailable} unavailable pairs"


def estimate_text(row):
    if row["mean"] is None:
        return "Estimate unavailable"
    number = f"Δ = {row['mean']:+.3g}"
    interval = row["ci95_episode_bootstrap"]
    return number + (" · interval unavailable" if interval is None
                     else f"  [{interval[0]:+.3g}, {interval[1]:+.3g}]")


def checked_analysis_label(label):
    if label is not None and (not isinstance(label, str) or not 1 <= len(label) <= 100
                              or not label.isprintable() or not label.strip()):
        raise ValueError("Analysis label must be 1–100 printable characters on one line")
    return label


def build_figure(panels, *, synthetic=False, analysis_label=None):
    analysis_label = checked_analysis_label(analysis_label)
    try:
        import matplotlib
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
        from matplotlib.lines import Line2D
    except ImportError as error:
        raise ValueError("Rendering requires optional matplotlib; install it in a plotting environment") from error
    with matplotlib.rc_context({"font.family": "DejaVu Sans", "font.size": 9,
                                "svg.fonttype": "none", "svg.hashsalt": "matched-figure-v1"}):
        figure = Figure(figsize=(16, 10), facecolor="white")
        FigureCanvasAgg(figure)
        figure.text(.06, .955, TITLE, fontsize=19, weight="bold", color="#182936")
        figure.text(.06, .918, "Within-model matched endpoints · equal episode weights · two sampler seeds per episode",
                    fontsize=11, color="#455560")
        if analysis_label is not None:
            figure.text(.06, .891, analysis_label, fontsize=10, color="#455560")
        if synthetic:
            figure.text(.94, .985, "SYNTHETIC FIXTURE — NOT STUDY RESULTS", ha="right", va="top",
                        fontsize=10, color="#A13028", weight="bold")
        handles = [Line2D([], [], color=COLORS[model], marker=MARKERS[model], linestyle="none",
                          markersize=6, label=name) for model, name in MODELS.items()]
        figure.legend(handles=handles, loc="upper left", bbox_to_anchor=(.055, .887 if analysis_label else .895),
                      ncol=2, frameon=False, fontsize=10)
        grid = figure.add_gridspec(2, 2, left=.12, right=.97, bottom=.20, top=.80,
                                   hspace=.69, wspace=.38)
        axes = {}
        for index, study in enumerate(STUDIES):
            slot = grid[index // 2, index % 2]
            inner = slot.subgridspec(1, 2, width_ratios=[1.5, 1.12], wspace=.08)
            ax, notes = figure.add_subplot(inner[0]), figure.add_subplot(inner[1])
            axes[study] = ax
            notes.axis("off")
            bounds = slot.get_position(figure)
            figure.text(bounds.x0, bounds.y1 + .035, PANEL_TITLES[study], fontsize=12,
                        weight="bold", color="#182936")
            figure.text(bounds.x0, bounds.y1 + .013, DIRECTION_NOTES[study], fontsize=8.6, color="#455560")
            ax.set_xlim(panels[study]["xlim"])
            ax.set_xlabel(AXIS_LABELS[study], labelpad=8, fontsize=9)
            ax.spines[["top", "right", "left"]].set_visible(False)
            ax.spines["bottom"].set_color("#AAB4BA")
            ax.grid(axis="x", color="#E3E7EA", linewidth=.7)
            ax.set_axisbelow(True)
            ax.tick_params(axis="y", length=0, pad=8)
            if study == "S-013":
                ax.set_ylim(-.6, 4.6)
                ax.set_yticks(range(5), [c.replace("_", " ") for c in reversed(CONDITIONS)])
                ax.set_xticks([0, .25, .5, .75, 1])
                notes.set_ylim(ax.get_ylim())
                notes.text(0, 1.01, "Valid pairs · episodes · unavailable", transform=notes.transAxes,
                           fontsize=8.4, color="#455560")
            else:
                ax.axvline(0, color="#70818C", linewidth=1, linestyle="--", zorder=1)
                ax.set_ylim(-.65, 1.65)
                ax.set_yticks([1, 0], list(MODELS.values()))
                notes.set_ylim(ax.get_ylim())
            for row in panels[study]["rows"]:
                model = row["model"]
                y = (4 - CONDITIONS.index(row["condition"]) + (.16 if model == "gemma" else -.16)
                     if study == "S-013" else (1 if model == "gemma" else 0))
                estimate, interval = row["mean"], row["ci95_episode_bootstrap"]
                if estimate is not None:
                    if study != "S-013" and interval is not None:
                        ax.hlines(y, interval[0], interval[1], color=COLORS[model], linewidth=2, zorder=2)
                        ax.vlines(interval, y - .06, y + .06, color=COLORS[model], linewidth=1, zorder=2)
                    ax.plot(estimate, y, marker=MARKERS[model], color=COLORS[model],
                            markersize=6, linestyle="none", zorder=3, clip_on=False)
                else:
                    # Text at an axes-relative location is not a point estimate at zero.
                    ax.text(.04, y, "unavailable", transform=ax.get_yaxis_transform(),
                            va="center", color=COLORS[model], fontsize=8.5)
                if study == "S-013":
                    notes.text(0, y, count_text(row, compact=True), va="center", fontsize=8.4,
                               color=COLORS[model])
                else:
                    notes.text(0, y, estimate_text(row) + "\n" + count_text(row), va="center",
                               fontsize=8.4, linespacing=1.65, color=COLORS[model])
        figure.text(.06, .05, FOOTNOTE, fontsize=9, color="#455560", linespacing=1.7)
    return figure, axes, matplotlib.__version__


def private_path(path):
    root = PRIVATE_ROOT.absolute()
    if root.resolve() != root:
        raise ValueError("The private research/outputs root must not be a symlink")
    path = Path(path).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError("Inputs and outputs must stay under this checkout's private research/outputs")
    return path


def reject_constant(value):
    raise ValueError(f"Nonfinite JSON constant is not permitted: {value}")


def render(input_path, output_prefix, *, synthetic=False, dpi=180, analysis_label=None):
    analysis_label = checked_analysis_label(analysis_label)
    if type(dpi) is not int or not 72 <= dpi <= 600:
        raise ValueError("DPI must be an integer between 72 and 600")
    source, prefix = private_path(input_path), private_path(output_prefix)
    destinations = {ext: private_path(str(prefix) + "." + ext) for ext in ("png", "svg", "json")}
    if any(path == source or path.exists() for path in destinations.values()):
        raise ValueError("Refusing to overwrite an existing output or the input")
    raw = source.read_bytes()
    report = json.loads(raw, parse_constant=reject_constant)
    panels = prepare_panels(report, synthetic=synthetic)
    figure, _, version = build_figure(panels, synthetic=synthetic, analysis_label=analysis_label)
    import matplotlib  # Already checked by build_figure; render-time only.
    receipt = {"schema": "research.introspection_matched_figure.v1",
               "input": {"path": str(source), "sha256": hashlib.sha256(raw).hexdigest()},
               "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "comparison_plan_sha256": report.get("plan_sha256"),
               "comparison_code_sha256": report.get("script_sha256"),
               "options": {"synthetic_fixtures": synthetic, "dpi": dpi, "analysis_label": analysis_label,
                           "output_prefix": str(prefix), "figure_inches": [16, 10]},
               "title": TITLE, "footnote": FOOTNOTE, "model_colors": COLORS,
               "versions": {"python": platform.python_version(), "matplotlib": version},
               "panels": panels, "outputs_sha256": {},
               "scope": "Retained within-model means and intervals only; no rescoring, pooling, or cross-model tests"}
    created = []
    try:
        prefix.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with ExitStack() as stack:
            streams = {}
            for ext, path in destinations.items():
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                created.append(path)
                streams[ext] = stack.enter_context(os.fdopen(descriptor, "wb"))
            with matplotlib.rc_context({"svg.fonttype": "none", "svg.hashsalt": "matched-figure-v1"}):
                for ext in ("png", "svg"):
                    figure.savefig(streams[ext], format=ext, dpi=dpi,
                                   metadata={"Title": TITLE, **({"Date": None} if ext == "svg" else {})})
                    streams[ext].flush()
                    receipt["outputs_sha256"][ext] = hashlib.sha256(destinations[ext].read_bytes()).hexdigest()
            streams["json"].write((json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    finally:
        figure.clear()
    return {ext: str(path) for ext, path in destinations.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Existing matched-comparison JSON")
    parser.add_argument("--output-prefix", type=Path, required=True, help="New PNG/SVG/JSON basename")
    parser.add_argument("--synthetic-fixtures", action="store_true", help="Require fixture input; label rendered figure")
    parser.add_argument("--dpi", type=int, default=180)
    parser.add_argument("--analysis-label", help="Explicit export subtitle, 1–100 printable characters; never inferred")
    args = parser.parse_args(argv)
    print(json.dumps(render(args.input, args.output_prefix, synthetic=args.synthetic_fixtures, dpi=args.dpi,
                            analysis_label=args.analysis_label)))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as error:
        sys.exit(str(error))
