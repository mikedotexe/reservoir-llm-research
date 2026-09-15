#!/usr/bin/env python3
"""Check one explicitly synthetic input-lineage example; stdlib, no writes/network.

This is a narrow relational checker, NOT the future producer schema validator,
runtime replay, instrumentation-parity test, or causal evidence. It covers two fresh
samples on the stable-core path only. Held input may have aggregate lineage; other
modes, admission transformations, preview evaluations, and overflow need separate
producer tests. Independent fill-latch and slope histories are preserved here.
Hashes check the saved effective vectors, not the authenticity of source claims.

Run from any directory: python3 -B probes/input_lineage_contract.py --self-test
The default input is proposals/fixtures/input-lineage-v1.json. JSON goes to stdout.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct


DEFAULT = Path(__file__).resolve().parents[1] / "proposals/fixtures/input-lineage-v1.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def vector_hash(vector):
    require(len(vector) == 8, "example effective vector must have eight components")
    require(all(type(x) in (int, float) and math.isfinite(x) for x in vector),
            "effective vector must contain finite numbers")
    return hashlib.sha256(struct.pack("<8f", *vector)).hexdigest()


def validate(doc):
    require(doc["purpose"] == "synthetic_relational_example", "not a synthetic example")
    require(doc["version"] == 1, "unsupported example version")
    scope, coverage, events = doc["scope"], doc["coverage"], doc["events"]
    prefix = f'{scope["boot_id"]}/{scope["session_id"]}/'
    require(scope["clock"] == "receiver_monotonic_microseconds", "wrong clock domain")
    require(coverage["status"] in ("complete", "partial"), "invalid coverage status")
    complete = coverage["status"] == "complete"
    ids, unknown, by_kind = {}, [], {}
    previous_time, previous_seq = -1, 0
    for event in events:
        eid, seq, stamp = event["id"], event["observer_seq"], event["monotonic_us"]
        require(eid.startswith(prefix) and eid not in ids, "cross-scope or duplicate ID")
        require(type(seq) is int and seq > previous_seq, "non-increasing observer sequence")
        require(type(stamp) is int and stamp >= previous_time, "non-monotonic event time")
        ids[eid] = event
        by_kind.setdefault(event["kind"], []).append(event)
        previous_time, previous_seq = stamp, seq
    window = coverage["declared_window_seq"]
    require(window == [1, 12], "this example checks only its declared 12-event window")
    observed = {e["observer_seq"] for e in events}
    expected = set(range(window[0], window[1] + 1))
    require(observed <= expected, "record outside declared window")
    gaps = set()
    for gap in coverage["gaps"]:
        require(gap["reason"], "gap reason required")
        gaps.update(range(gap["from_seq"], gap["through_seq"] + 1))
    require(gaps == expected - observed, "gap declaration disagrees with record sequence")
    dropped = coverage["observer_dropped_count"]
    require(dropped is None or (type(dropped) is int and dropped >= 0), "invalid drop count")
    if complete:
        require(not gaps and dropped == 0, "observer gap cannot be called complete")
    else:
        unknown.append("coverage is partial; missing activity is not zero")
        if dropped is None:
            unknown.append("observer drop count is unknown")

    def ref(owner, key, kind=None):
        value = owner[key]
        if isinstance(value, dict):
            require(set(value) == {"unknown"} and bool(value["unknown"]), "malformed unknown reference")
            require(not complete, "unknown reference in complete example")
            unknown.append(f'{owner.get("id", "batch item")}.{key}: {value["unknown"]}')
            return None
        require(isinstance(value, str) and value.startswith(prefix), "cross-boot/session reference")
        require(value in ids, f"dangling reference: {value}")
        target = ids[value]
        require(kind is None or target["kind"] == kind, f"wrong record kind for {key}")
        if "monotonic_us" in owner:
            require(target["monotonic_us"] <= owner["monotonic_us"], f"future input in {key}")
        return target

    def one(kind):
        rows = by_kind.get(kind, [])
        require(len(rows) == 1, f"this narrow example requires one {kind}")
        return rows[0]

    for event in events:
        for key in event:
            if key.endswith("_ref"):
                ref(event, key)
    batch = one("batch")
    require(batch["path"] == "stable_core_first_native_last_projection", "unsupported path")
    require([i["position"] for i in batch["items"]] == [0, 1], "wrong batch order")
    for item in batch["items"]:
        require(item["freshness"] == "fresh", "held/aggregate lineage is outside this example")
        require(item["transformation"] == "identity", "only explicit identity is modeled here")
        require(item["effective_sha256"] == vector_hash(item["effective_vector"]), "inconsistent input hash")
        ingress = ref(item, "ingress_ref", "ingress")
        if ingress:
            require(ingress["monotonic_us"] <= batch["monotonic_us"], "batch precedes ingress")
            require(ingress["feature_sha256"] == vector_hash(ingress["feature_vector"]), "ingress hash mismatch")
            require(ingress["feature_sha256"] == item["effective_sha256"], "undeclared input transformation")

    def selection(event, position):
        selected_batch = ref(event, "batch_ref", "batch")
        require(selected_batch is batch, "batch must be known for this example")
        require(event["batch_position"] == position, "native first and reported last were conflated")
        require(event["input_sha256"] == batch["items"][position]["effective_sha256"], "selected input hash mismatch")

    mix, native, projection = one("native_mix_trace"), one("native_step"), one("sensory_projection")
    selection(mix, 0)
    selection(native, 0)
    selection(projection, 1)
    require(native["result"] == "succeeded", "example requires a successful native step")
    require(ref(native, "mix_trace_ref", "native_mix_trace") is mix, "missing actual mixing trace")
    require(native["leak_applied"] == mix["mixing_coefficient"], "nominal leak substituted for actual leak")
    require(0 <= mix["mixing_coefficient"] <= 1, "invalid applied coefficient")
    require(native["leak_applied"] != native["leak_nominal"], "example must demonstrate distinct leak values")

    evaluation = one("controller_evaluation")
    require(evaluation["evaluation_kind"] == "committed", "preview is not a committed evaluation")
    fill_input = ref(evaluation, "fill_input_ref", "fill_estimate")
    require(fill_input is not None, "fill-latch input must be known in this example")
    require(evaluation["fill_input_value"] == fill_input["fill_percent"], "fill-latch value mismatch")
    slope_prev = ref(evaluation, "slope_previous_ref", "fill_estimate")
    slope_latest = ref(evaluation, "slope_latest_ref", "fill_estimate")
    require(slope_prev is not None and slope_latest is not None, "slope history required")
    dt = (slope_latest["monotonic_us"] - slope_prev["monotonic_us"]) / 1_000_000
    require(dt > 0, "invalid slope history order")
    require(evaluation["slope_method"] == "configured_reg_tick_seconds", "wrong slope method")
    denominator = evaluation["slope_denominator_s"]
    require(type(denominator) in (int, float) and math.isfinite(denominator) and denominator > 0,
            "invalid configured slope denominator")
    require(denominator != dt, "example must distinguish configured tick from elapsed history")
    require(math.isclose(evaluation["slope_pp_per_s"],
                         (slope_latest["fill_percent"] - slope_prev["fill_percent"]) / denominator),
            "slope does not match its independent history and configured denominator")
    field = one("field_write")
    require(ref(field, "evaluation_ref", "controller_evaluation") is evaluation, "wrong evaluation reference")
    require(ref(field, "projection_ref", "sensory_projection") is projection, "wrong projection context")
    require(field["write_result"] == "succeeded" and field["status"] == "applied",
            "failed field write cannot be labeled applied")
    require(field["mode"] == "scaffold_hold" and field["new_sensory_vector_applied"] is False,
            "projection context is not new-vector application under this hold example")
    report = one("report")
    current_fill = ref(report, "current_fill_ref", "fill_estimate")
    require(current_fill is not None, "current fill must be known in this example")
    require("field_write_ref" in current_fill, "stale fill relabeled current: no current field write")
    require(ref(current_fill, "field_write_ref", "field_write") is field, "stale fill relabeled current")
    require(current_fill["monotonic_us"] > field["monotonic_us"], "fill predates applied field")
    require(current_fill["estimate_seq"] > fill_input["estimate_seq"], "fill estimate did not advance")
    require(ref(report, "projection_ref", "sensory_projection") is projection, "report lost last-sample lineage")
    require(ref(report, "native_step_ref", "native_step") is native, "report lost native-step lineage")
    return {"valid": True, "coverage": coverage["status"], "events_checked": len(events),
            "unknowns": unknown, "causality": "not tested", "producer_acceptance": "not tested"}


def mutate(doc, scenario):
    out = copy.deepcopy(doc)
    rows = {e["id"].rsplit("/", 1)[1]: e for e in out["events"]}
    if scenario == "reported_last_replaces_native_first":
        rows["native"]["batch_position"] = 1
        rows["native"]["input_sha256"] = rows["batch"]["items"][1]["effective_sha256"]
    elif scenario == "dangling_id":
        rows["native"]["mix_trace_ref"] = rows["mix"]["id"] + "-missing"
    elif scenario == "cross_boot_id":
        rows["native"]["mix_trace_ref"] = rows["mix"]["id"].replace("synthetic-boot-a", "synthetic-boot-b")
    elif scenario == "future_fill_input":
        rows["evaluation"]["fill_input_ref"] = rows["fill-current"]["id"]
        rows["evaluation"]["fill_input_value"] = rows["fill-current"]["fill_percent"]
    elif scenario == "stale_fill_relabeled_current":
        rows["report"]["current_fill_ref"] = rows["fill-latched"]["id"]
    elif scenario == "nominal_leak_substituted":
        rows["native"]["leak_applied"] = rows["native"]["leak_nominal"]
    elif scenario == "inconsistent_input_hash":
        rows["batch"]["items"][0]["effective_vector"][0] += 0.125
    elif scenario == "failed_field_write_marked_applied":
        rows["field"]["write_result"] = "lock_failed"
    elif scenario == "preview_relabeled_committed":
        rows["evaluation"]["evaluation_kind"] = "preview_clone"
    elif scenario == "wrong_slope_denominator":
        rows["evaluation"]["slope_denominator_s"] = 0.5
    elif scenario == "wrong_slope_method":
        rows["evaluation"]["slope_method"] = "actual_elapsed_seconds"
    elif scenario in ("valid_partial", "observer_gap_called_complete"):
        out["events"].remove(rows["ingress-B"])
        rows["batch"]["items"][1]["ingress_ref"] = {"unknown": "observer_gap: original ingress record unavailable"}
        out["coverage"]["gaps"] = [{"from_seq": 4, "through_seq": 4, "reason": "record unavailable"}]
        if scenario == "valid_partial":
            out["coverage"]["status"] = "partial"
            out["coverage"]["observer_dropped_count"] = None
    else:
        raise ValueError("unknown mutation")
    return out


def self_test(doc):
    base = validate(doc)
    partial = validate(mutate(doc, "valid_partial"))
    require(partial["unknowns"] and partial["coverage"] == "partial", "partial became zero/complete")
    names = ["reported_last_replaces_native_first", "dangling_id", "cross_boot_id",
             "future_fill_input", "stale_fill_relabeled_current", "nominal_leak_substituted",
             "inconsistent_input_hash", "failed_field_write_marked_applied",
             "preview_relabeled_committed", "observer_gap_called_complete",
             "wrong_slope_denominator", "wrong_slope_method"]
    rejected = []
    for name in names:
        try:
            validate(mutate(doc, name))
        except (ValueError, KeyError) as exc:
            rejected.append({"scenario": name, "rejected": True, "reason": str(exc)})
        else:
            raise ValueError(f"bad example unexpectedly accepted: {name}")
    return {"synthetic_only": True, "complete_example": base, "partial_example": partial,
            "invalid_examples_rejected": len(rejected), "scenarios": rejected,
            "scope": "narrow relational checker; no producer, replay, performance or causal acceptance"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=DEFAULT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        require(args.fixture.stat().st_size <= 1_048_576, "fixture exceeds 1 MiB bound")
        doc = json.loads(args.fixture.read_text(encoding="utf-8"))
        result = self_test(doc) if args.self_test else validate(doc)
    except (OSError, ValueError, KeyError, TypeError, OverflowError, struct.error) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
