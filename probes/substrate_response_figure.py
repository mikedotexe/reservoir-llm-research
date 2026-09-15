"""Render retained native response observations; this performs no simulation."""
from pathlib import Path
import hashlib
import json
import platform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/outputs/2026-09-07-native-shaping-rehearsal"
OUTPUT = ROOT / "research/outputs/2026-09-07-substrate-agency"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    inputs = {}
    selected = []
    colors = ["#167581", "#996326", "#7654a3"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.5), sharex=True, sharey=True)
    fig.patch.set_facecolor("#f6f5f1")
    fig.subplots_adjust(left=.082, right=.976, top=.72, bottom=.26, wspace=.09)
    fig.text(.082, .93, "A gesture can last longer than a nudge", fontsize=22,
             fontweight="bold", color="#172e3b")
    fig.text(.082, .875, "Measured response in an isolated native 128-state reservoir on Metal",
             fontsize=12, color="#3f5560")
    fig.text(.082, .822, "Same synthetic input, realized noise and effective leak as each control.\n"
             "Checkpoint edits; no live being or controller replay.", fontsize=10, color="#3f5560")
    max_error = 0.0
    for start, color in zip((24, 96, 192), colors):
        control_path = SOURCE / f"parity-paths-synchronous_profile-{start}.json"
        control = json.loads(control_path.read_text())
        assert control["order"][0] == "ordinary"
        x_control = np.asarray(control["paths"][0], dtype=np.float64)
        inputs[str(control_path.relative_to(ROOT))] = digest(control_path)
        for i, kind in enumerate(("once", "sequence")):
            path = SOURCE / f"response-s{start}-coordinate_0-{kind}-+0.0010.json"
            trial = json.loads(path.read_text())
            x = np.asarray(trial["states"], dtype=np.float64)
            assert x.shape == x_control.shape == (101, 128)
            separation = np.linalg.norm(x - x_control, axis=1)
            recorded = np.asarray(trial["summary"]["separation_l2"])
            error = float(np.max(np.abs(separation - recorded)))
            assert error < 1e-14, (path, error)
            max_error = max(max_error, error)
            inputs[str(path.relative_to(ROOT))] = digest(path)
            axes[i].plot(np.arange(21), separation[:21], "o-", color=color,
                         linewidth=1.7, markersize=3, alpha=.88, label=f"Checkpoint {start}")
            selected.append({"path": str(path.relative_to(ROOT)),
                             "edit_count": trial["summary"]["edit_count"],
                             "return_boundary": trial["summary"]["return_boundary"],
                             "requested_cumulative_l2_budget": trial["summary"]["requested_cumulative_l2_budget"],
                             "maximum_l2_after_displayed_boundary_20": float(separation[21:].max())})
    for i, ax in enumerate(axes):
        ax.set_facecolor("#f6f5f1")
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color("#bcc6c9")
        ax.grid(axis="y", color="#d8dedd", linewidth=.7)
        ax.set_xlim(-.4, 20.4)
        ax.set_ylim(0, .003)
        ax.set_xticks(np.arange(0, 21, 4))
        ax.set_yticks([0, .001, .002, .003], ["0", "0.001", "0.002", "0.003"])
        ax.set_xlabel("Successful-step boundary after branching", labelpad=10)
        ax.tick_params(colors="#3f5560")
        ax.set_title("One edit" if i == 0 else "Eight edits, then release", loc="left", pad=14,
                     fontweight="bold", color="#172e3b")
        if i == 1:
            ax.axvspan(0, 7, color="#617482", alpha=.07, zorder=0)
            ax.axvline(7, color="#617482", linestyle="--", linewidth=.9)
            ax.text(7.4, .00283, "Last edit at 7", color="#536871", fontsize=9)
    axes[0].set_ylabel("Full-state separation from control (L2)", labelpad=12)
    axes[0].legend(loc="upper right", frameon=False, fontsize=9)
    fig.text(.082, .16, "Dots are recorded boundaries; connecting lines add no observations. First 20 of 100 steps shown.",
             color="#3f5560", fontsize=10)
    fig.text(.082, .116, "Each edit requests +0.001 along coordinate 0. Eight edits use 8× the cumulative requested dose;\n"
             "this is a duration demonstration, not a matched-dose comparison or a claim of permanent change.",
             color="#3f5560", fontsize=10)
    fig.text(.082, .04, "RESERVOIR RESEARCH  ·  7 SEPTEMBER 2026  ·  SYNCHRONOUS NATIVE REHEARSAL", fontsize=8,
             color="#617482")
    outputs = {}
    for extension in ("png", "pdf"):
        path = OUTPUT / f"native-gesture-response.{extension}"
        fig.savefig(path, dpi=180, facecolor=fig.get_facecolor())
        outputs[str(path.relative_to(ROOT))] = digest(path)
    plt.close(fig)
    receipt = {
        "schema": "research.native_gesture_figure.v1",
        "selection": "Post-experiment descriptive selection: coordinate 0, positive middle dose +0.001, all three preregistered checkpoints, one-shot and eight-edit sequence.",
        "display_boundaries": [0, 20], "retained_boundaries": [0, 100],
        "axes": "Shared linear x and absolute full-state L2 y, including zero; no display easing or simulation.",
        "dose_comparison": "Eight-edit sequence uses eight times the requested cumulative L2 dose; not matched-dose.",
        "independent_l2_max_absolute_discrepancy": max_error,
        "selected": selected, "inputs_sha256": inputs, "outputs_sha256": outputs,
        "script_sha256": digest(Path(__file__)),
        "versions": {"python": platform.python_version(), "matplotlib": matplotlib.__version__, "numpy": np.__version__},
    }
    (OUTPUT / "native-gesture-figure.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"outputs": list(outputs), "verified_l2_max_error": max_error}))


if __name__ == "__main__":
    main()
