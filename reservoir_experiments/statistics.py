"""Small, dependency-free summaries for paired episode experiments.

Resampling units are episodes, not turns or sampler seeds. Intervals describe the
retained constructed episode bank; they are not population prevalence estimates.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from statistics import mean


def finite_score(row):
    value = row.get("score")
    return (row.get("valid", False) and isinstance(value, (int, float))
            and not isinstance(value, bool) and math.isfinite(value))


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row.get("kind", ""), row["condition"])].append(row)
    result = []
    for (kind, condition), group in sorted(groups.items()):
        values = [r["score"] for r in group if finite_score(r)]
        result.append({"kind": kind, "condition": condition,
                       "planned": len(group), "scorable": len(values),
                       "unavailable": len(group) - len(values),
                       "episodes": len({r["episode"] for r in group}),
                       "mean_valid": mean(values) if values else None})
    return result


def paired_contrast(rows, first, second, *, kind=None, draws=10000, seed=20261024):
    """Average seed-paired differences within episodes, then across episodes.

Only exact episode+seed pairs with two valid scores contribute. Additional
duplicate requests must have a distinct kind, or be excluded by the caller.
"""
    if not isinstance(draws, int) or draws < 1:
        raise ValueError("draws must be a positive integer")
    selected = [r for r in rows if r["condition"] in (first, second)
                and (kind is None or r.get("kind") == kind)]
    cells = {}
    for r in selected:
        key = (r["episode"], r["seed"], r["condition"])
        if key in cells:
            raise ValueError(f"duplicate comparison cell: {key}")
        cells[key] = r
    episodes = defaultdict(list)
    candidate_pairs = {(r["episode"], r["seed"]) for r in selected}
    for episode, sample_seed in sorted(candidate_pairs):
        a = cells.get((episode, sample_seed, first), {})
        b = cells.get((episode, sample_seed, second), {})
        if finite_score(a) and finite_score(b):
            episodes[episode].append(a["score"] - b["score"])
    differences = {episode: mean(values) for episode, values in sorted(episodes.items())}
    values = list(differences.values())
    output = {"first": first, "second": second, "kind": kind,
              "candidate_pairs": len(candidate_pairs),
              "valid_pairs": sum(map(len, episodes.values())),
              "paired_episodes": len(values), "episode_differences": differences,
              "difference": mean(values) if values else None,
              "ci95": None, "bootstrap_draws": draws, "bootstrap_seed": seed}
    if values:
        rng = random.Random(seed)
        boot = sorted(mean(rng.choices(values, k=len(values))) for _ in range(draws))
        output["ci95"] = [boot[int(.025 * (draws - 1))], boot[int(.975 * (draws - 1))]]
    return output
