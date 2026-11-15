#!/usr/bin/env python3
"""Scientific figures from map_sustained_response.py artifacts; NumPy + Matplotlib.

Reads completed offline outputs only. Distances use all 32 state coordinates;
PCA is a shared centered projection without coordinate standardization.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = args.output
    results = json.loads((root / "results.json").read_text())
    data = [np.load(root / (s["sessionId"] + "-arrays.npz")) for s in results["sessions"]]
    states = [d["states"][1:] for d in data]
    names = ["Gemma4", "GLM-4.7-Flash", "Ministral 3"]
    colors = ["#376eb5", "#d16e30", "#3a8c75"]
    whole = np.vstack(states)
    center = whole.mean(axis=0)
    _, singular, axes = np.linalg.svd(whole - center, full_matrices=False)
    share = singular ** 2 / np.sum(singular ** 2)
    projected = [(s - center) @ axes[:2].T for s in states]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})

    fig, ax = plt.subplots(1, 3, figsize=(13, 4.6), sharex=True, sharey=True)
    for index, (plot, xy, session) in enumerate(zip(ax, projected, results["sessions"])):
        plot.plot(xy[:, 0], xy[:, 1], lw=0.3, color="#777777", alpha=0.22)
        scatter = plot.scatter(xy[:, 0], xy[:, 1], c=np.linspace(0, 1, len(xy)), cmap="viridis", s=3, vmin=0, vmax=1)
        for hour, step in enumerate(session["hourlySteps"], 1):
            point = xy[step - 1]
            plot.scatter(*point, color="#e3514c", marker="x", s=45, zorder=5)
            plot.annotate(str(hour), point, xytext=(4, 5), textcoords="offset points", fontsize=9)
        plot.set_title(f"{names[index]} · {len(xy):,} states")
        plot.set_xlabel(f"Shared PC1 ({share[0]:.1%} variance)")
        plot.set_aspect("equal", adjustable="box")
    ax[0].set_ylabel(f"Shared PC2 ({share[1]:.1%} variance)")
    fig.suptitle("Where the recurrent state travelled", fontsize=16, y=0.98)
    fig.text(0.5, 0.91, f"November 14 independent runs · shared axes retain {share[:2].sum():.1%} of pooled variance · red × = hourly response applied", ha="center", fontsize=10)
    fig.subplots_adjust(left=0.07, right=0.88, bottom=0.16, top=0.82, wspace=0.15)
    cb = fig.colorbar(scatter, cax=fig.add_axes([0.91, 0.22, 0.014, 0.52]))
    cb.set_label("Fraction of recorded numerical steps")
    fig.text(0.5, 0.025, "A projection of visited states, not a basin map. These axes have no assigned semantic meaning.", ha="center", fontsize=10)
    fig.savefig(root / "state-map.png", dpi=180)
    fig.savefig(root / "state-map.pdf")
    plt.close(fig)

    recurrence, metadata = [], []
    for session, state in zip(results["sessions"], states):
        indices = np.unique(np.linspace(0, len(state) - 1, 500, dtype=int))
        x = state[indices]
        distance = np.linalg.norm(x[:, None, :] - x[None, :, :], axis=2)
        far = np.abs(indices[:, None] - indices[None, :]) > 30
        recurrence.append(distance)
        quantiles = np.quantile(distance[far], [0.05, 0.5, 0.95])
        same_phase = ((indices[:, None] - indices[None, :]) % 30 == 0) & far
        metadata.append({"sessionId": session["sessionId"], "sampledStates": len(indices),
                         "sampleSteps": (indices + 1).tolist(), "distanceQuantilesExcluding30StepNeighbors": quantiles.tolist(),
                         "sameForcingPhasePairs": int(same_phase.sum()),
                         "sameForcingPhaseMedianDistance": float(np.median(distance[same_phase])),
                         "otherPhaseMedianDistance": float(np.median(distance[far & ~same_phase]))})
    vmax = max(float(np.quantile(d, 0.95)) for d in recurrence)
    fig, ax = plt.subplots(1, 3, figsize=(13, 4.6))
    for index, (plot, d, s) in enumerate(zip(ax, recurrence, results["sessions"])):
        im = plot.imshow(d, origin="lower", cmap="magma", vmin=0, vmax=vmax,
                         extent=[1, s["frames"], 1, s["frames"]], aspect="equal")
        plot.set_title(names[index])
        plot.set_xlabel("Numerical step")
    ax[0].set_ylabel("Numerical step")
    fig.suptitle("Return visits measured in all 32 coordinates", fontsize=16, y=0.98)
    fig.text(0.5, 0.91, "Darker = closer state vectors · 500 uniformly spaced observations per run · one common distance scale", ha="center")
    fig.subplots_adjust(left=0.07, right=0.88, bottom=0.16, top=0.82, wspace=0.22)
    cb = fig.colorbar(im, cax=fig.add_axes([0.91, 0.22, 0.014, 0.52]))
    cb.set_label("Euclidean state distance")
    fig.text(0.5, 0.025, "The diagonal is self-similarity. Shared forcing and held text inputs can produce repeated structure.", ha="center")
    fig.savefig(root / "recurrence-map.png", dpi=180)
    fig.savefig(root / "recurrence-map.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.9))
    for index, session in enumerate(results["sessions"]):
        curves = np.array([np.array(t["separationL2"]) / t["actualInitialL2"] for t in session["stateTrials"]])
        # Suppress long-horizon floating-point floors rather than draw them as memory.
        x = np.arange(17)
        ax[0].fill_between(x, curves[:, :17].min(0), curves[:, :17].max(0), color=colors[index], alpha=0.10)
        ax[0].plot(x, np.median(curves[:, :17], axis=0), color=colors[index], label=names[index], lw=2)
        horizons = [1, 2, 4, 8, 16]
        values = np.array([[t["all48SingularValues"][0] for t in session["inputTrials"] if t["horizon"] == h] for h in horizons])
        ax[1].fill_between(horizons, values.min(1), values.max(1), color=colors[index], alpha=0.10)
        ax[1].plot(horizons, np.median(values, axis=1), "o-", color=colors[index], label=names[index], lw=2, ms=4)
    ax[0].axhline(0.1, color="#444444", ls="--", lw=1)
    ax[0].text(10, 0.13, "10% of initial displacement", fontsize=9)
    ax[0].set(title="State perturbations are rapidly forgotten", xlabel="Numerical steps after perturbation", ylabel="L2 separation / actual initial L2")
    ax[0].set_ylim(1e-8, 2)
    ax[1].set(title="Input impulse response also decays", xlabel="Steps after a one-step input impulse", ylabel="Largest response singular value")
    ax[1].set_ylim(1e-12, 10)
    for plot in ax:
        plot.set_yscale("log")
        plot.grid(axis="y", alpha=0.15)
        plot.legend(frameon=False, loc="lower left", fontsize=9)
    fig.suptitle("How long does a change survive under the same future drive?", fontsize=15)
    fig.text(0.5, 0.88, "Six fixed moments per run · lines = medians, shaded bands = observed ranges", ha="center", fontsize=10)
    fig.subplots_adjust(left=0.08, right=0.97, bottom=0.22, top=0.77, wspace=0.25)
    fig.text(0.5, 0.075, "72 signed state perturbations per model; input map estimated with ±0.01 impulses in each of 48 slots.", ha="center", fontsize=10)
    fig.text(0.5, 0.025, "Future inputs, noise and recorded actions held identical. This does not replay a changed LLM conversation.", ha="center", fontsize=10)
    fig.savefig(root / "response-map.png", dpi=180)
    fig.savefig(root / "response-map.pdf")
    plt.close(fig)
    (root / "figure-metadata.json").write_text(json.dumps({"plotProbeSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "numpy": np.__version__, "matplotlib": matplotlib.__version__, "pooledPcaVarianceShares": share.tolist(),
        "recurrence": metadata}, indent=2) + "\n")


if __name__ == "__main__":
    main()
