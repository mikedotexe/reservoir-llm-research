#!/usr/bin/env python3
"""Render reproducible offline sonar validation figures (NumPy + Matplotlib)."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from refine_reservoir_sonar import sha

SHORT = ["G4 · ind.", "GLM · ind.", "M3 · ind.", "G4 · paused", "GLM · paused", "M3 · paused"]
FULL = [f"{name} · {group}" for group in ("independent", "paused peer-enabled")
        for name in ("Gemma4", "GLM-4.7-Flash", "Ministral 3")]
TEAL, ORANGE, PURPLE = "#167b78", "#bc6b22", "#7356a5"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = args.results / "results.json"
    compact_source = args.results / "compact-calibration/results.json"
    result = json.loads(source.read_text())
    compact = json.loads(compact_source.read_text())
    ends = result["endpoints"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    amplitudes = np.array(result["amplitudes"])
    for key, color, label in [("calibrated", TEAL, "Measured response map"),
                              ("scaledWiring", ORANGE, "Best scalar × fixed wiring"),
                              ("scrambled", PURPLE, "Scrambled map")]:
        errors = np.array([[s["horizons"][0][key]["aggregateRelativeError"] * 100
                            for s in end["resolution"]] for end in ends])
        axes[0, 0].plot(amplitudes, np.median(errors, axis=0), "o-", color=color, label=label, markersize=4)
        axes[0, 0].fill_between(amplitudes, errors.min(axis=0), errors.max(axis=0), color=color, alpha=.13)
    ax = axes[0, 0]
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Held-out input impulse · L2 amplitude")
    ax.set_ylabel("Immediate prediction error (%)")
    ax.set_title("A   Predicting 64 unseen signed directions", loc="left", weight="bold")
    ax.legend(fontsize=8, loc="lower right"); ax.grid(alpha=.15)
    ax.text(.02, .05, "Line: median of six endpoints\nBand: endpoint range, not uncertainty", transform=ax.transAxes, fontsize=8)

    ax = axes[0, 1]
    own, other = [], []
    for end in ends:
        rows = end["temporalSamples"]
        energy = sum(r["currentMap"]["observedAggregateL2"] ** 2 for r in rows)
        own.append(100 * np.sqrt(sum(r["currentMap"]["absoluteErrorL2"] ** 2 for r in rows) / energy))
        other.append(100 * np.sqrt(sum(r["otherTimesMeanMap"]["absoluteErrorL2"] ** 2 for r in rows) / energy))
    x = np.arange(6)
    ax.bar(x - .18, own, .36, color=TEAL, label="Current map")
    ax.bar(x + .18, other, .36, color=ORANGE, label="Mean map from seven other times")
    ax.set_yscale("log"); ax.set_ylim(.01, 100)
    ax.set_xticks(x, SHORT, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("Pooled prediction error (%)")
    ax.set_title("B   The map changes along a continuation", loc="left", weight="bold")
    ax.legend(fontsize=8, loc="upper left"); ax.grid(axis="y", alpha=.15)

    ax = axes[1, 0]
    gain = [end["questionProbe"]["trials"][0]["gainOverMedianRandom"] for end in ends]
    ax.bar(x, gain, color=TEAL)
    ax.axhline(1, color="#555", linestyle="--", linewidth=1, label="Median random probe")
    for i, g in enumerate(gain): ax.text(i, g + .12, f"{g:.1f}×", ha="center", fontsize=9)
    ax.set_ylim(0, 7.2); ax.set_xticks(x, SHORT, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("State-discrimination signal / random median")
    ax.set_title("C   Inputs chosen to answer a specific question", loc="left", weight="bold")
    ax.text(.02, .91, "Actual versus zero starting state; equal input energy", transform=ax.transAxes, fontsize=8)
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(0, .87)); ax.grid(axis="y", alpha=.15)

    ax = axes[1, 1]
    full = np.array([r["full"]["aggregateRelativeError"] * 100 for r in compact["rows"]])
    sparse = np.array([r["compact"]["aggregateRelativeError"] * 100 for r in compact["rows"]])
    limits = [min(full.min(), sparse.min()) * .9, max(full.max(), sparse.max()) * 1.08]
    ax.plot(limits, limits, color="#777", linestyle="--", linewidth=1, label="Equal prediction error")
    ax.scatter(full, sparse, s=32, color=TEAL, alpha=.65, edgecolors="white", linewidth=.4)
    ax.set_xlim(limits); ax.set_ylim(limits)
    ax.set_xlabel("96-branch calibration · prediction error (%)")
    ax.set_ylabel("2-branch calibration · prediction error (%)")
    ax.set_title("D   Two probes recover first-step sensitivity", loc="left", weight="bold")
    ax.text(.03, .93, "48 states · 64 fresh signed directions each\nKnown wiring; seven origins include clipping", transform=ax.transAxes, va="top", fontsize=8)
    ax.legend(fontsize=8, loc="lower right"); ax.grid(alpha=.15)

    fig.suptitle("Reservoir sonar: signal that predicts new measurements", fontsize=18, y=.98)
    fig.subplots_adjust(left=.08, right=.98, top=.90, bottom=.12, hspace=.48, wspace=.28)
    fig.text(.5, .025, "Copies share input, controls and noise. Maps calibrated at amplitude 0.001; panels B–D tested at 0.001.\nSix historical endpoints, plus simulated continuation states. Local response geometry; no global topology or model ranking.", ha="center", fontsize=9)
    for suffix in ("png", "pdf"):
        fig.savefig(args.output / f"sonar-predictive-validation.{suffix}", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    arrays = np.load(args.results / "compact-calibration/arrays.npz")
    for ax, end, title in zip(axes.flat, ends, FULL):
        label = end["label"]
        leak = end["origin"]["controls"]["leak"]
        gates = np.array([arrays[f"{label}_offset{o}_trueGates"] / leak for o in result["temporalOffsets"]])
        image = ax.imshow(gates, cmap="viridis", vmin=0, vmax=1, aspect="auto", interpolation="nearest")
        ax.set_title(title, fontsize=11)
        ax.set_yticks(np.arange(8), [f"+{s['offset']:02} · {'on' if s['nextForcingOn'] else 'off'}" for s in end["temporalSamples"]], fontsize=8)
        ax.set_xlabel("Recurrent coordinate (0–31)")
        ax.set_ylabel("Step offset · next forcing gate", fontsize=8)
    fig.suptitle("What changes: the sensitivity of each recurrent coordinate", fontsize=17)
    fig.subplots_adjust(left=.09, right=.87, top=.87, bottom=.15, hspace=.4, wspace=.43)
    fig.colorbar(image, cax=fig.add_axes([.90, .24, .015, .5])).set_label("Sensitivity / leak · 0 closed, 1 maximum")
    fig.text(.5, .035, "Immediate derivative = coordinate sensitivities × fixed input wiring. Axes identify coordinates, not spatial regions.\nOffset 0 is the saved endpoint; later rows are frozen-input/control continuations. Forcing phase, state and clipping vary together.", ha="center", fontsize=9)
    for suffix in ("png", "pdf"):
        fig.savefig(args.output / f"sonar-changing-sensitivity.{suffix}", dpi=180)
    plt.close(fig)
    metadata = {"inputHashes": {str(source): sha(source), str(compact_source): sha(compact_source)},
                "plotScriptSha256": sha(Path(__file__)), "numpyVersion": np.__version__,
                "matplotlibVersion": matplotlib.__version__, "labels": SHORT,
                "temporalOwnPooledErrorPercent": own, "temporalOtherPooledErrorPercent": other,
                "questionProbeGain": gain, "scope": result["scope"]}
    (args.output / "figure-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
