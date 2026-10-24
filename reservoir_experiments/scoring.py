"""Verified study scoring and episode-paired summaries; no model calls."""
from __future__ import annotations

from collections import Counter, defaultdict
import copy
import json
import math
from pathlib import Path

from . import runner
from .statistics import finite_score, paired_contrast, summarize


def instrument_summary(records):
    result = {}
    for field in ("prompt_eval_count", "eval_count", "elapsed_seconds"):
        values = [r[field] for r in records.values()
                  if type(r.get(field)) in (int, float) and r[field] >= 0
                  and (type(r[field]) is int or math.isfinite(r[field]))]
        result[field] = {"available": len(values), "min": min(values) if values else None,
                         "max": max(values) if values else None, "sum": sum(values)}
    return result


def duplicate_receipts(protocol, records, run):
    """Compare repeated requests only when their rendered request hashes match."""
    pairs = []
    nodes = {n["id"]: n for n in protocol["nodes"]}
    for node in nodes.values():
        if not (node["kind"] == "duplicate" or node.get("metadata", {}).get("replicate")):
            continue
        original = protocol.get("truth", {}).get(node["id"], {}).get("matched_target_id")
        if original is None:
            original = next((p for p in node.get("after", [])
                             if nodes[p]["episode"] == node["episode"]), None)
        if original is None:
            raise ValueError(f"Duplicate has no declared match: {node['id']}")
        a, b = records.get(original, {}), records.get(node["id"], {})
        request_a = Path(run) / "nodes" / original / "request.json"
        request_b = Path(run) / "nodes" / node["id"] / "request.json"
        identical_request = (request_a.exists() and request_b.exists()
                             and request_a.read_bytes() == request_b.read_bytes())
        available = a.get("status") == b.get("status") == "complete"
        pairs.append({"original": original, "duplicate": node["id"],
                      "identical_request": identical_request,
                      "both_complete": available,
                      "identical_text": a.get("text") == b.get("text") if available else None})
    eligible = [p for p in pairs if p["identical_request"] and p["both_complete"]]
    return {"planned_pairs": len(pairs), "eligible_pairs": len(eligible),
            "different_text_pairs": sum(not p["identical_text"] for p in eligible), "pairs": pairs}


def study_report(protocol, records, annotations=None, baseline=None):
    from .attribution_catalog import score_attribution, score_catalog
    from .correction_memory import score_correction, score_memory
    annotations = annotations or {}
    study = protocol["study"]
    if study == "S-013":
        report = score_attribution(protocol, records)
        report["primary"] = {"definition": "all four fields correct, by source condition",
                             "groups": summarize([r for r in report["rows"] if r["kind"] == "attribution"])}
    elif study == "S-014":
        report = score_correction(protocol, records, baseline=baseline,
                                  adjudications=annotations.get("verdicts"))
        by_id = {r["node_id"]: r for r in report["rows"]}
        losses = []
        for node in protocol["nodes"]:
            if node["kind"] != "target":
                continue
            target = by_id[node["id"]]
            truth = protocol["truth"][node["id"]]
            for condition, key in (("self", "self_forecast_id"), ("observer", "observer_forecast_id")):
                forecast = by_id[truth[key]]
                valid = bool(target["valid"] and forecast["forecast_probability"] is not None)
                losses.append({"episode": node["episode"], "seed": node["seed"],
                               "condition": condition, "kind": "brier", "valid": valid,
                               "score": (forecast["forecast_probability"] - target["score"]) ** 2 if valid else None})
        report["brier_rows"] = losses
        report["primary"] = paired_contrast(losses, "self", "observer", kind="brier")
        report["primary"]["lower_is_better"] = True
    elif study == "S-015":
        report = score_memory(protocol, records, adjudications=annotations.get("verdicts"))
        report["primary"] = paired_contrast([r for r in report["rows"] if r["delay"] == "delayed"],
                                             "original", "notebook", kind="application")
    elif study == "S-016":
        report = score_catalog(protocol, records)
        report["primary"] = paired_contrast(report["rows"], "full", "concise_padded", kind="catalog")
        nodes = {n["id"]: n for n in protocol["nodes"]}
        grouped = defaultdict(list)
        for row in report["rows"]:
            row["filler"] = nodes[row["node_id"]]["metadata"]["filler"]
            if row["kind"] == "catalog":
                grouped[(row["condition"], None, None)].append(row)
                grouped[(row["condition"], row["filler"], row["seed"])].append(row)
        report["lexical_totals"] = []
        for (condition, filler, sample_seed), group in grouped.items():
            valid = [r for r in group if finite_score(r)]
            words = sum(r["words"] for r in valid)
            hits = sum(r["phrase_count"] for r in valid)
            report["lexical_totals"].append({"condition": condition, "filler": filler, "seed": sample_seed,
                                             "planned": len(group), "scorable": len(valid),
                                             "prose_words": words, "phrase_occurrences": hits,
                                             "pooled_per_1000_words": hits * 1000 / words if words else None})
    else:
        raise ValueError(f"No scorer for study {study}")
    if "groups" in report:
        report["study_groups"] = report["groups"]
    numeric_rows = [r for r in report["rows"] if r["kind"] not in ("forecast", "neutral_ack", "prose")]
    report["groups"] = summarize(numeric_rows)
    report["semantic_counts"] = dict(Counter((r["kind"] + "/" + ("not_applicable" if r["kind"] == "neutral_ack"
                                             else "valid" if r["valid"] else "unavailable_or_invalid"))
                                             for r in report["rows"]))
    report["format_counts"] = dict(Counter((r["kind"] + "/" + ("not_applicable" if r["kind"] == "neutral_ack"
                                           else "valid" if r.get("format_valid", r["valid"]) else "unavailable_or_invalid"))
                                           for r in report["rows"]))
    report["status_counts"] = dict(Counter(records.get(n["id"], {}).get("status", "pending")
                                          for n in protocol["nodes"]))
    report["protocol_id"] = protocol["id"]
    report["model"] = protocol["model"]
    report["split"] = protocol["split"]
    report["opportunities"] = len(protocol["nodes"])
    report["instrument"] = instrument_summary(records)
    return report


def score_run(run, *, annotations=None, out=None, baseline=None):
    from . import attribution_catalog, correction_memory
    run = Path(run)
    verification = runner.verify(run)
    manifest, protocol = runner.load_run(run)
    records = runner.read_results(run)
    annotation_bytes = runner.stable_read(Path(annotations)) if annotations else None
    notes = json.loads(annotation_bytes) if annotation_bytes is not None else {}
    baseline = copy.deepcopy(baseline)
    report = study_report(protocol, records, annotations=notes, baseline=baseline)
    if protocol["study"] == "S-014" and baseline is not None:
        report["baseline"] = copy.deepcopy(baseline)
    report["duplicates"] = duplicate_receipts(protocol, records, run)
    rows = {r["node_id"]: r for r in report["rows"]}
    metric_deltas = []
    for pair in report["duplicates"]["pairs"]:
        a, b = rows.get(pair["original"], {}), rows.get(pair["duplicate"], {})
        if pair["identical_request"] and finite_score(a) and finite_score(b):
            pair["metric_difference"] = b["score"] - a["score"]
            metric_deltas.append(abs(pair["metric_difference"]))
    report["duplicates"]["scorable_metric_pairs"] = len(metric_deltas)
    report["duplicates"]["mean_absolute_metric_difference"] = (sum(metric_deltas) / len(metric_deltas)
                                                                 if metric_deltas else None)
    study_module = {"S-013": attribution_catalog, "S-014": correction_memory,
                    "S-015": correction_memory, "S-016": attribution_catalog}[protocol["study"]]
    report["provenance"] = {"manifest_sha256": runner.sha(runner.stable_read(run / "manifest.json")),
                            "runner_commit": manifest["git_head"], "verified": verification["valid"],
                            "scoring_sha256": runner.sha(runner.stable_read(Path(__file__))),
                            "statistics_sha256": runner.sha(runner.stable_read(Path(__file__).with_name("statistics.py"))),
                            "study_scoring_module": study_module.__name__,
                            "study_scoring_sha256": runner.sha(runner.stable_read(Path(study_module.__file__))),
                            "annotations_sha256": runner.sha(annotation_bytes) if annotation_bytes is not None else None}
    if out is not None:
        destination = runner.guard_output(Path(out), Path(manifest["repository"]))
        runner.write_json(destination, report)
    return report
