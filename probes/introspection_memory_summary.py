#!/usr/bin/env python3
"""S-015 descriptive supplement; consumes a retained score, never scores a run.

Standard library plus the checkout's read-only runner/statistics helpers. No provider
calls, text interpretation, source-verdict reparsing, score rewriting, or exclusions
based on correct/incorrect outcomes. Invoke only after required blind readings.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import statistics
import sys

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))
from reservoir_experiments import runner
from reservoir_experiments.statistics import finite_score, paired_contrast

ARMS = ("original", "paraphrase", "notebook", "irrelevant", "none")
LABELS = ("supported", "contradicted", "unresolved")
SEEDS = (7, 20260909)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def counts(values):
    return dict(sorted(Counter(values).items()))


def numeric(values, *, signed=False):
    values = list(values)
    accepted = [v for v in values if type(v) is int and (signed or v >= 0)]
    return {"planned": len(values), "available": len(accepted),
            "missing_or_invalid": len(values) - len(accepted),
            "sum": sum(accepted) if accepted else None,
            "mean": statistics.mean(accepted) if accepted else None,
            "median": statistics.median(accepted) if accepted else None,
            "min": min(accepted) if accepted else None,
            "max": max(accepted) if accepted else None}


def transfer(verdict, relation):
    require(relation in ("copy", "invert", "other"), "Unknown transfer relation")
    if verdict is None or relation == "other":
        return None
    require(verdict in LABELS, "Invalid frozen source verdict")
    return ({"supported": "contradicted", "contradicted": "supported", "unresolved": "unresolved"}
            [verdict] if relation == "invert" else verdict)


def delays(protocol, case):
    return (("delayed", "immediate") if protocol["split"] == "confirmation"
            and case["variant"] == 0 else ("delayed",))


def validate_score(protocol, score, manifest, manifest_digest, records):
    """Check retained-score provenance and structure without invoking any scorer."""
    require(protocol["study"] == "S-015", "Only S-015 application protocols are supported")
    for field, value in (("study", "S-015"), ("protocol_id", protocol["id"]),
                         ("model", protocol["model"]), ("split", protocol["split"])):
        require(score.get(field) == value, f"Score {field} does not match frozen protocol")
    require(manifest["protocol_id"] == protocol["id"], "Manifest/protocol identity mismatch")
    provenance = score.get("provenance", {})
    require(provenance.get("verified") is True, "Retained score was not verified")
    require(provenance.get("manifest_sha256") == manifest_digest, "Score manifest hash mismatch")
    require(provenance.get("runner_commit") == manifest["git_head"], "Score runner commit mismatch")
    for name in ("scoring", "statistics"):
        digest = provenance.get(name + "_sha256")
        require(isinstance(digest, str) and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest),
                f"Missing or malformed {name} provenance")
    rows = score.get("rows", [])
    indexed = {r["node_id"]: r for r in rows}
    require(len(indexed) == len(rows), "Duplicate retained score rows")
    require(set(indexed) == {n["id"] for n in protocol["nodes"]}, "Score must retain every frozen node, including missing results")
    require(score.get("opportunities") == len(indexed), "Score opportunity count mismatch")
    primary = score.get("primary", {})
    require(primary.get("first") == "original" and primary.get("second") == "notebook"
            and primary.get("kind") == "application", "Expected retained common primary contrast")
    for node in protocol["nodes"]:
        row, truth = indexed[node["id"]], protocol["truth"][node["id"]]
        metadata = node["metadata"]
        for field in ("episode", "condition", "seed", "kind"):
            require(row[field] == node[field], f"Score allocation mismatch: {node['id']}/{field}")
        for field in ("delay", "memory_words", "family", "evidence_condition"):
            require(row.get(field) == metadata.get(field), f"Score metadata mismatch: {node['id']}/{field}")
        for field, key in (("expected", "verdict"), ("source_verdict", "source_verdict"),
                           ("application_relation", "application_relation")):
            require(row.get(field) == truth[key], f"Frozen truth mismatch: {node['id']}/{field}")
        verdict = row.get("verdict")
        require(verdict is None or verdict in LABELS, "Invalid retained verdict")
        require(row["valid"] is (verdict is not None), "Score validity/verdict mismatch")
        require(row["score"] is None if verdict is None else type(row["score"]) is int,
                "Correctness score must be an integer or explicit null")
        require(row["score"] == (int(verdict == truth["verdict"]) if verdict is not None else None),
                "Retained correctness score is inconsistent")
        record = records.get(node["id"], {})
        require(row["status"] == record.get("status", "pending"), "Score is stale relative to result status")
        for field in ("prompt_eval_count", "eval_count"):
            require(row.get(field) == record.get(field), "Score is stale relative to token receipts")
        require(record.get("provider_model") in (None, protocol["model"]), "Provider model mismatch")
    return indexed


def planned_rows(protocol, score):
    """Expand explicit missing-source opportunities; reject incomplete allocations."""
    require(tuple(protocol["design"]["seeds"]) == SEEDS, "Unexpected seed plan")
    require(protocol["design"].get("source_seed") == 7, "Unexpected source seed")
    cases = {c["id"]: c for c in protocol["cases"]}
    require(len(cases) == len(protocol["cases"]), "Duplicate planned cases")
    unavailable = {u["episode"]: u for u in protocol.get("unavailable_sources", [])}
    require(len(unavailable) == len(protocol.get("unavailable_sources", [])), "Duplicate unavailable sources")
    require(set(unavailable) <= set(cases), "Unavailable source outside plan")
    require(protocol["design"]["planned_source_episodes"] == len(cases), "Source plan size mismatch")
    by_cell = {}
    nodes = {n["id"]: n for n in protocol["nodes"]}
    require(len(nodes) == len(protocol["nodes"]), "Duplicate frozen node IDs")
    for row in score["rows"]:
        key = (row["episode"], row["seed"], row["delay"], row["condition"])
        require(key not in by_cell, "Duplicate application cell")
        by_cell[key] = copy.deepcopy(row)
    output, sources, expected_cells = [], [], set()
    for eid, case in sorted(cases.items()):
        available = eid not in unavailable
        source = {"episode": eid, "family": case["family"], "variant": case["variant"],
                  "evidence_condition": case["evidence_condition"], "source_available": available,
                  "source_id": f"{eid}-s7-target", "unavailable_reason": unavailable.get(eid, {}).get("reason"),
                  "source_verdict": None, "source_verdict_available": False,
                  "source_verdict_correct": None, "source_error_present": None,
                  "source_expected": case["update_expected"], "application_expected": case["application_expected"],
                  "application_relation": case["application_relation"], "transfer_prediction": None,
                  "transfer_correct": None, "original_words": None, "irrelevant_words": None,
                  "irrelevant_minus_original_words": None, "irrelevant_source_episode": None}
        episode_rows = []
        for delay in delays(protocol, case):
            for seed in SEEDS:
                for arm in ARMS:
                    key = (eid, seed, delay, arm)
                    if available:
                        require(key in by_cell, f"Available source lacks planned application: {key}")
                        expected_cells.add(key)
                        row = by_cell[key]
                        node = nodes[row["node_id"]]
                        require(node["metadata"]["source_id"] == source["source_id"], "Source was not fixed seed-7 target")
                        truth = protocol["truth"][row["node_id"]]
                        require(truth["original_update_expected"] == case["update_expected"]
                                and truth["verdict"] == case["application_expected"]
                                and truth["application_relation"] == case["application_relation"], "Case/truth mismatch")
                    else:
                        require(key not in by_cell, "Unavailable source unexpectedly has an application")
                        row = {"node_id": None, "episode": eid, "seed": seed, "delay": delay,
                               "condition": arm, "kind": "application", "status": "source_unavailable",
                               "valid": False, "score": None, "verdict": None, "memory_words": None,
                               "prompt_eval_count": None, "eval_count": None,
                               "format_valid": False, "adjudicated": False, "semantic_recovered": False,
                               "expected": case["application_expected"]}
                    row.update(source_available=available, source_unavailable_reason=source["unavailable_reason"],
                               variant=case["variant"], family=case["family"], evidence_condition=case["evidence_condition"])
                    output.append(row)
                    episode_rows.append(row)
        if available:
            truths = [protocol["truth"][r["node_id"]] for r in episode_rows]
            frozen = truths[0]["source_verdict"]
            require(all(t["source_verdict"] == frozen for t in truths), "Frozen source verdict varies within episode")
            prediction = transfer(frozen, case["application_relation"])
            original = {r["memory_words"] for r in episode_rows if r["condition"] == "original"}
            irrelevant = {r["memory_words"] for r in episode_rows if r["condition"] == "irrelevant"}
            require(len(original) == len(irrelevant) == 1, "Memory length varies across seeds/delays")
            original_words, irrelevant_words = original.pop(), irrelevant.pop()
            require(type(original_words) is int and original_words > 0
                    and type(irrelevant_words) is int and irrelevant_words > 0, "Invalid memory word count")
            source.update(source_verdict=frozen, source_verdict_available=frozen is not None,
                          source_verdict_correct=(frozen == case["update_expected"] if frozen is not None else None),
                          source_error_present=(frozen != case["update_expected"] if frozen is not None else None),
                          transfer_prediction=prediction,
                          transfer_correct=(int(prediction == case["application_expected"]) if prediction is not None else None),
                          original_words=original_words, irrelevant_words=irrelevant_words,
                          irrelevant_minus_original_words=irrelevant_words - original_words,
                          irrelevant_source_episode=protocol["irrelevant_pairing"][eid])
        sources.append(source)
    require(set(by_cell) == expected_cells, "Unexpected frozen application cells")
    for source in sources:
        if not source["source_available"]:
            continue
        candidates = [s for s in sources if s["source_available"] and s["family"] != source["family"]]
        require(candidates, "No different-family irrelevant source")
        selected = min(candidates, key=lambda s: (abs(s["original_words"] - source["original_words"]),
                        hashlib.sha256((source["episode"] + s["episode"]).encode()).hexdigest()))
        require(selected["episode"] == source["irrelevant_source_episode"], "Irrelevant source is not deterministic nearest-length selection")
        require(selected["original_words"] == source["irrelevant_words"], "Irrelevant length differs from selected source")
    return output, sources


def baseline_summary(sources):
    known = [s for s in sources if s["transfer_correct"] is not None]
    return {"planned_source_episodes": len(sources), "available_predictions": len(known),
            "unavailable_predictions": len(sources) - len(known),
            "correct": sum(s["transfer_correct"] for s in known),
            "accuracy_available": statistics.mean(s["transfer_correct"] for s in known) if known else None,
            "relations": counts(s["application_relation"] for s in sources)}


def arm_summary(rows):
    valid = [r for r in rows if finite_score(r)]
    return {"planned": len(rows), "built": sum(r["source_available"] for r in rows),
            "source_unavailable": sum(not r["source_available"] for r in rows),
            "scorable": len(valid), "unscorable": len(rows) - len(valid),
            "scenario_conclusion_recovered": sum(r["score"] for r in valid),
            "accuracy_scorable": statistics.mean(r["score"] for r in valid) if valid else None,
            "abstained_or_unresolved": sum(r["verdict"] == "unresolved" for r in valid),
            "determinate_without_relevant_memory": sum(r["verdict"] in LABELS[:2] and r["condition"] in ("none", "irrelevant") for r in valid),
            "determinate_with_relevant_memory": sum(r["verdict"] in LABELS[:2] and r["condition"] not in ("none", "irrelevant") for r in valid),
            "format_valid": sum(r.get("format_valid") is True for r in rows),
            "semantic_recovered_format_failure": sum(r.get("semantic_recovered") is True for r in rows),
            "adjudicated": sum(r.get("adjudicated") is True for r in rows),
            "source_error_propagation_consistency": {
                "eligible_scorable_relevant_memory_answers": sum(type(r.get("source_error_propagation_consistent")) is bool for r in rows),
                "consistent": sum(r.get("source_error_propagation_consistent") is True for r in rows),
                "not_consistent": sum(r.get("source_error_propagation_consistent") is False for r in rows),
                "unavailable_or_not_applicable": sum(r.get("source_error_propagation_consistent") is None for r in rows)},
            "status_counts": counts(r["status"] for r in rows),
            "memory_whitespace_words": numeric(r.get("memory_words") for r in rows),
            "actual_request_prompt_tokens": numeric(r.get("prompt_eval_count") for r in rows),
            "actual_output_tokens": numeric(r.get("eval_count") for r in rows)}


def summarize(protocol, score, *, draws=10000, bootstrap_seed=20261024):
    rows, sources = planned_rows(protocol, score)
    result = {"schema_version": 1, "study": "S-015", "protocol_id": protocol["id"],
              "model": protocol["model"], "split": protocol["split"],
              "interpretation": "Descriptive supplement. Scenario conclusion recovery is not a false-belief rate; unresolved can be appropriate without relevant memory. No primary-contrast replacement.",
              "source_verdict_policy": "Use only frozen protocol truth.source_verdict, including null. Never reparse original texts or substitute another seed.",
              "denominator": {"planned_source_episodes": len(sources),
                              "available_sources": sum(s["source_available"] for s in sources),
                              "unavailable_sources": sum(not s["source_available"] for s in sources),
                              "unavailable_source_reasons": counts(s["unavailable_reason"] or "unspecified" for s in sources if not s["source_available"]),
                              "frozen_source_verdict_available": sum(s["source_verdict_available"] for s in sources),
                              "available_source_without_frozen_verdict": sum(s["source_available"] and not s["source_verdict_available"] for s in sources),
                              "source_verdict_correct": sum(s["source_verdict_correct"] is True for s in sources),
                              "source_errors": sum(s["source_error_present"] is True for s in sources),
                              "planned_applications_all_delays": len(rows), "built_applications": len(score["rows"])},
              "sources": sources, "source_transfer_baseline": baseline_summary(sources),
              "primary_delayed_original_minus_notebook_retained": copy.deepcopy(score["primary"]),
              "primary_policy": "Verbatim retained score.primary; not recomputed. Extra tables retain unavailable planned cells without changing its paired-scorable estimator.",
              "by_delay": {}, "immediate_minus_delayed": {}}
    for delay in ("delayed", "immediate"):
        subset = [r for r in rows if r["delay"] == delay]
        source_subset = [s for s in sources if any(r["episode"] == s["episode"] for r in subset)]
        residuals = []
        cells = {(r["episode"], r["seed"], r["condition"]): r for r in subset}
        for s in source_subset:
            for seed in SEEDS:
                a, b = cells[(s["episode"], seed, "irrelevant")], cells[(s["episode"], seed, "original")]
                delta = lambda field: a[field] - b[field] if type(a.get(field)) is int and a[field] >= 0 and type(b.get(field)) is int and b[field] >= 0 else None
                residuals.append({"episode": s["episode"], "seed": seed,
                                  "irrelevant_minus_original_prompt_tokens": delta("prompt_eval_count"),
                                  "irrelevant_minus_original_output_tokens": delta("eval_count")})
        word_residuals = [s["irrelevant_minus_original_words"] for s in source_subset]
        result["by_delay"][delay] = {"planned_applications": len(subset),
            "planned_source_episodes": len(source_subset), "source_transfer_baseline": baseline_summary(source_subset),
            "arms": {arm: arm_summary([r for r in subset if r["condition"] == arm]) for arm in ARMS},
            "irrelevant_length_residual": {"definition": "irrelevant minus original; words counted once per source episode; actual tokens paired on episode+seed within this delay",
                "words": numeric(word_residuals, signed=True),
                "absolute_words": numeric(abs(v) if v is not None else None for v in word_residuals),
                "actual_prompt_tokens": numeric((r["irrelevant_minus_original_prompt_tokens"] for r in residuals), signed=True),
                "actual_output_tokens": numeric((r["irrelevant_minus_original_output_tokens"] for r in residuals), signed=True),
                "token_pairs": residuals}}
    for arm in ARMS:
        selected = [dict(r, condition=r["delay"]) for r in rows
                    if protocol["split"] == "confirmation" and r["variant"] == 0 and r["condition"] == arm]
        contrast = paired_contrast(selected, "immediate", "delayed", kind="application", draws=draws, seed=bootstrap_seed)
        cells = {(r["episode"], r["seed"], r["condition"]): r for r in selected}
        pairs = []
        for eid, seed in sorted({(r["episode"], r["seed"]) for r in selected}):
            a, b = cells[(eid, seed, "immediate")], cells[(eid, seed, "delayed")]
            both = finite_score(a) and finite_score(b)
            pairs.append({"episode": eid, "seed": seed, "source_available": a["source_available"],
                          "immediate_status": a["status"], "delayed_status": b["status"],
                          "immediate_score": a["score"], "delayed_score": b["score"],
                          "both_scorable": both, "difference": a["score"] - b["score"] if both else None})
        contrast.update(definition="Diagnostic immediate minus delayed within the preselected variant-0 episodes, exact episode+seed+arm pairing; bootstrap episode means with seeds clustered",
                        planned_pairs=len(pairs), unavailable_source_pairs=sum(not p["source_available"] for p in pairs),
                        unscorable_pairs=sum(not p["both_scorable"] for p in pairs),
                        paired_seed_counts=counts(p["episode"] for p in pairs if p["both_scorable"]),
                        delayed_rows_outside_preselected_subset=sum(r["delay"] == "delayed" and r["condition"] == arm and (protocol["split"] != "confirmation" or r["variant"] != 0) for r in rows),
                        pairs=pairs)
        result["immediate_minus_delayed"][arm] = contrast
    result["limits"] = ["Delayed and immediate outcomes are never pooled into an arm estimate.",
        "Missing sources and unscorable observations remain explicit; no cells are removed because their answers are wrong.",
        "Token summaries use provider receipts, including available counts on unsuccessful responses; word counts are frozen request metadata, not tokens.",
        "Bootstrap intervals describe the constructed bank and resample episode means, not independent seeds; partial seed availability is shown.",
        "Source transfer and error-consistency flags are descriptive aids, not causal evidence of retention, correction, or error propagation.",
        "Original retained scores lack a full result-set digest, study-specific scoring-module hash, and adjudication-file hash. Preserve their declared provenance without upgrading it; later fields are copied when present. Manifest binding, receipt verification and row status/token checks cannot independently authenticate semantic adjudications or exclude every stale-score scenario.",
        "Current scoring/statistics hashes are compared with retained hashes for disclosure, not used to reject original scores after a reviewed code change. A mismatch does not silently trigger rescoring; the retained score and its exact primary remain authoritative for this supplement."]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="Frozen S-015 run from this checkout")
    parser.add_argument("score", type=Path, help="Already retained S-015 common score JSON")
    parser.add_argument("--out", type=Path, required=True, help="New JSON path below this checkout's research/outputs")
    parser.add_argument("--draws", type=int, default=10000)
    args = parser.parse_args()
    run, score_path = args.run.expanduser().resolve(), args.score.expanduser().resolve()
    out = runner.guard_output(args.out, REPOSITORY)
    require(REPOSITORY / "research" / "outputs" in out.parents, "Summary output must be private research/outputs")
    require(not out.exists(), "Output already exists; no overwrites")
    manifest, protocol = runner.load_run(run)
    require(Path(manifest["repository"]).resolve() == REPOSITORY, "Run belongs to another checkout")
    verification = runner.verify(run)
    require(verification["valid"] is True, "Run verification failed")
    records = runner.read_results(run)
    raw_score = runner.stable_read(score_path)
    score = json.loads(raw_score)
    manifest_raw = runner.stable_read(run / "manifest.json")
    validate_score(protocol, score, manifest, runner.sha(manifest_raw), records)
    report = summarize(protocol, score, draws=args.draws)
    report["provenance"] = {"run": str(run), "retained_score": str(score_path),
        "retained_score_sha256": runner.sha(raw_score), "manifest_sha256": runner.sha(manifest_raw),
        "protocol_sha256": runner.sha(runner.stable_read(run / "protocol.json")),
        "helper_sha256": runner.sha(runner.stable_read(Path(__file__))),
        "statistics_sha256": runner.sha(runner.stable_read(REPOSITORY / "reservoir_experiments" / "statistics.py")),
        "current_vs_retained_score_code": {name: {
            "retained_sha256": score["provenance"][name + "_sha256"],
            "current_sha256": runner.sha(runner.stable_read(REPOSITORY / "reservoir_experiments" / (name + ".py"))),
            "matches": score["provenance"][name + "_sha256"] == runner.sha(runner.stable_read(REPOSITORY / "reservoir_experiments" / (name + ".py")))
        } for name in ("scoring", "statistics")},
        "score_code_policy": "Retain original declared provenance; current-code disagreement is disclosed, not silently rescored or upgraded.",
        "retained_score_provenance": score["provenance"], "verified_results": verification["verified_results"],
        "result_receipt_sha256": {nid: runner.sha(runner.stable_read(run / "nodes" / nid / "result.json")) for nid in sorted(records)},
        "created_at": runner.now()}
    # Verify input bytes remain stable across the summary, then atomically create once.
    require(raw_score == runner.stable_read(score_path), "Score changed during summary")
    runner.verify(run)
    require(report["provenance"]["result_receipt_sha256"] == {nid: runner.sha(runner.stable_read(run / "nodes" / nid / "result.json")) for nid in sorted(runner.read_results(run))}, "Results changed during summary")
    runner.write_json(out, report)
    print(str(out))


if __name__ == "__main__":
    main()
