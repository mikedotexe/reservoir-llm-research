#!/usr/bin/env python3
"""Render retained sampler data only; no process, app, service or UI access."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import macos_reliability as sampler


def segments(rows, group, key, interval, disk_every):
    result, current, previous = [], [], None
    for row in rows:
        # Disk scans are intentionally sparse; absent intermediate scans are not
        # failed observations. Scheduled missing/incomplete scans break the line.
        if group == "disk" and row.get("disk") is None and row["sequence"] % disk_every:
            continue
        obj = row.get(group)
        value = obj.get(key) if isinstance(obj, dict) else None
        valid = isinstance(value, (int, float)) and not isinstance(value, bool)
        valid = valid and (group != "disk" or obj.get("complete") is True)
        x = row["elapsedSeconds"]
        if not valid or (previous is not None and (x <= previous or x - previous > interval * 1.5)):
            if current:
                result.append(current)
            current, previous = [], None
        if valid:
            current.append((x / 60, value))
            previous = x
    if current:
        result.append(current)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--markers", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--label", default="Packaged macOS 0.12.0 · controlled synthetic provider")
    args = parser.parse_args()
    raw = sampler.read_regular(args.input, 64 * 1024 * 1024)
    rows = [json.loads(line) for line in raw.splitlines()]
    header = rows[0]
    if header.get("schema") != sampler.SCHEMA or header.get("type") != "header":
        raise ValueError("Unsupported capture header")
    complete = rows[-1].get("type") == "footer"
    if not complete and not args.allow_incomplete:
        raise ValueError("Missing footer; --allow-incomplete labels an interim plot")
    samples = [r for r in rows if r.get("type") == "sample"]
    if not samples:
        raise ValueError("No sample observations")
    marker_data = sampler.read_regular(args.markers, 131072)
    markers = [json.loads(line) for line in marker_data.splitlines()]
    if len(markers) > 128:
        raise ValueError("Marker bound exceeded")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True, layout="constrained")
    fig.set_constrained_layout_pads(w_pad=.10, h_pad=.14, hspace=.04)
    scale = 1024 * 1024
    series = [(axes[0], "process", "rssBytes", scale, "#2463a3", "Main PID RSS"),
              (axes[1], "process", "cpuIntervalPercent", 1, "#9252a8", "Main PID interval CPU"),
              (axes[2], "disk", "logicalBytes", scale, "#167765", "Owned logical bytes"),
              (axes[2], "disk", "allocatedBytes", scale, "#c1691b", "Owned allocated blocks")]
    for ax, group, key, divisor, color, label in series:
        parts = segments(samples, group, key, header["intervalSeconds"] * (header["diskEvery"] if group == "disk" else 1), header["diskEvery"])
        first = True
        for part in parts:
            ax.plot([x for x, _ in part], [y / divisor for _, y in part], color=color, linewidth=1.1,
                    marker=".", markersize=3, label=label if first else None)
            first = False
        if first:
            ax.text(.02, .8, f"No valid {label} observations", transform=ax.transAxes, fontsize=9)
    axes[0].set_ylabel("RSS (MiB)")
    axes[1].set_ylabel("CPU (% of one core)")
    axes[2].set_ylabel("Owned storage (MiB)")
    axes[2].set_xlabel("Minutes since sampler admission (not numerical time)")
    for ax in axes:
        ax.grid(alpha=.2)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        if ax.lines:
            ax.legend(loc="upper left", fontsize=8)
    start = int(header["monotonicNs"])
    xlast = samples[-1]["elapsedSeconds"] / 60
    for i, marker in enumerate(markers):
        x = (int(marker["monotonicNs"]) - start) / 60e9
        if not 0 <= x <= xlast:
            continue
        phase = str(marker.get("phase", "unknown"))[:40]
        for ax in axes:
            ax.axvline(x, color="#555555", linewidth=.7, linestyle="--", alpha=.55)
        axes[0].text(x, 1.025 + (i % 2) * .055, phase, transform=axes[0].get_xaxis_transform(), fontsize=8, rotation=0)
    prefix = "INTERIM · missing final footer\n" if not complete else ""
    footer_status = rows[-1].get("status", "unknown") if complete else "unclosed capture"
    fig.suptitle(prefix + args.label + f"\nSelected PID {header['process']['pid']} · {len(samples)} samples · end: {footer_status}", fontsize=12)
    # Footnote is reserved below the axes; sampled gaps are never connected.
    fig.get_layout_engine().set(rect=(0, .10, 1, .90))
    fig.text(.012, .013, "Main PID only: excludes shared WebKit/GPU, provider and sampler processes; CPU is not GPU activity or energy.\n"
             "Marker phases are operator-declared. Missing/failed scans break lines. CPU values are interval averages at endpoints.\n"
             "Disk is a non-atomic metadata scan; APFS allocated blocks need not equal unique physical storage.\n"
             f"Input SHA-256: {hashlib.sha256(raw).hexdigest()}", fontsize=8, va="bottom")
    with args.output.open("xb") as output:
        fig.savefig(output, format="png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
