"""Validate and summarize the frozen order study without changing any evidence.

This reads retained files only. It never loads a model, re-tokenizes prompts,
executes generated choices, or writes into live state. Claim coding remains human
or reviewer-authored; exact hashes/quotes establish provenance, not correctness.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def sibling(name):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


previous_review = sibling("study_evidence_revision_review")
order_probe = sibling("study_evidence_order")
ARMS = ("evidence_then_recall", "recall_then_evidence")
SEEDS = (307, 419, 631, 887)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def natural_integer(value, label):
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


def validate_inputs(root, protocol):
    if protocol.get("schema") != "study_evidence_order_v1":
        raise ValueError("wrong order-study schema")
    expected = [{"id": f"order-{seed}-{arm}", "seed": seed, "arm": arm}
                for index, seed in enumerate(SEEDS)
                for arm in (ARMS if index % 2 == 0 else tuple(reversed(ARMS)))]
    if protocol["trials"] != expected or set(protocol["cases"]) != set(ARMS):
        raise ValueError("study must retain the planned four balanced seed pairs")
    cases = protocol["cases"]
    prefix, evidence, recall = order_probe.split_blocks(cases[ARMS[0]])
    if cases[ARMS[1]] != [cases[ARMS[0]][0], {"role": "user", "content": prefix + recall + evidence}]:
        raise ValueError("comparison changes more than the E/R block order")
    for name, text in (("prefix", prefix), ("evidence", evidence), ("recall", recall)):
        raw = (root / f"block-{name}.txt").read_bytes()
        if raw != text.encode() or protocol["blocks"][name] != {"bytes": len(raw), "sha256": sha(raw)}:
            raise ValueError(f"frozen {name} block differs")
    for arm in ARMS:
        if read_json(root / f"input-{arm}.json") != cases[arm]:
            raise ValueError("retained input differs from protocol")
    if (root / "system.txt").read_text() != cases[ARMS[0]][0]["content"]:
        raise ValueError("frozen system differs")
    if (root / "baseline-user.txt").read_text() != prefix + evidence + recall:
        raise ValueError("frozen source-arm baseline differs")
    for name, identity in protocol["source_map"].items():
        if sha((root / "source-snapshot" / name).read_bytes()) != identity["sha256"]:
            raise ValueError(f"source snapshot differs: {name}")
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        if manifest["protocol_sha256"] != sha((root / "protocol.json").read_bytes()):
            raise ValueError("manifest protocol identity differs")
        for section in ("frozen_files", "source_snapshots"):
            for path, expected_sha in manifest[section].items():
                if sha(Path(path).read_bytes()) != expected_sha:
                    raise ValueError(f"manifest retained file differs: {path}")
    return {"protocol_sha256": sha((root / "protocol.json").read_bytes()),
            "blocks": protocol["blocks"], "source_snapshots": len(protocol["source_map"]),
            "manifest_available": manifest_path.exists()}


def validate_render(root, protocol, arm):
    path = root / f"rendered-{arm}.json"
    if not path.exists():
        return None
    row = read_json(path)
    if row["arm"] != arm or row["rendered_sha256"] != sha(row["rendered_text"].encode()):
        raise ValueError("rendered prompt identity differs")
    natural_integer(row["token_count"], "prompt token count")
    if len(row["token_ids"]) != row["token_count"]:
        raise ValueError("rendered token count differs from retained token IDs")
    for token in row["token_ids"]:
        natural_integer(token, "prompt token ID")
    # The pinned Gemma template trims the outside of each message. The complete
    # internally ordered text must still be present; we do not retokenize here.
    system, user = [message["content"].strip() for message in protocol["cases"][arm]]
    start = row["rendered_text"].find(system)
    following = row["rendered_text"].find(user, start + len(system))
    if start < 0 or following < 0:
        raise ValueError("rendered message content is missing or out of order")
    return row


def validate_result(result, rendering, settings):
    if rendering is None:
        raise ValueError("generated result lacks a retained rendered prompt")
    if result["prompt_sha256"] != rendering["rendered_sha256"] or result["prompt_tokens"] != rendering["token_count"]:
        raise ValueError("result prompt differs from rendered receipt")
    completion = natural_integer(result["completion_tokens"], "completion count")
    if completion != len(result["tokens"]) or completion > settings["max_tokens"]:
        raise ValueError("yielded completion count or allowance differs")
    for token in result["tokens"]:
        natural_integer(token, "completion token ID")
    filtered = natural_integer(result["filtered_tokens"], "filtered count")
    terminal = natural_integer(result["terminal_tokens"], "terminal count")
    if terminal > 1 or filtered + terminal > completion:
        raise ValueError("filtered/terminal counts exceed yielded completion")
    finish = result["finish"]
    if finish not in ("stop", "length", "error"):
        raise ValueError("unknown completion finish")
    if finish == "stop" and terminal != 1:
        raise ValueError("terminal stop lacks a terminal token")
    if finish == "length" and (terminal or completion != settings["max_tokens"]):
        raise ValueError("allowance finish differs from actual exhaustion")
    for control in ("temperature", "top_p"):
        if result["controls"][control] != settings[control]:
            raise ValueError("applied local sampling controls differ")
    initial, final = result["initial_cache_positions"], result["final_cache_positions"]
    if not initial or len(initial) != len(final):
        raise ValueError("cache layer receipts are absent or differ in length")
    for offset in initial + final:
        natural_integer(offset, "cache position")
    if any(initial):
        raise ValueError("trial cache was not fresh")
    expected = result["prompt_tokens"] + completion
    if finish != "error":
        if any(offset != expected for offset in final):
            raise ValueError("successful cache progression differs from generator lookahead")
        cache_status = "prompt_plus_yielded_completion"
    else:
        # A guard may fire during prefill, between layer updates, or after the
        # lookahead forward but before recording that yielded token.
        if any(offset > expected + 1 for offset in final):
            raise ValueError("error cache exceeds possible partial/lookahead progression")
        cache_status = "partial_generation_error_not_full_parity"
    return {"status": cache_status, "initial_unique": sorted(set(initial)),
            "final_unique": sorted(set(final)), "prompt_plus_completion": expected}


def review(root):
    protocol = read_json(root / "protocol.json")
    integrity = validate_inputs(root, protocol)
    renderings = {arm: validate_render(root, protocol, arm) for arm in ARMS}
    caches = {}
    for spec in protocol["trials"]:
        path = root / f"{spec['id']}.json"
        if not path.exists():
            continue
        row = read_json(path)
        if row["spec"] != spec:
            raise ValueError("result spec differs from frozen plan")
        result = row.get("result")
        if result is not None:
            if row["outcome"] == "returned" and result["finish"] == "error":
                raise ValueError("returned outcome hides a generation error")
            if row["outcome"] == "generation_error" and result["finish"] != "error":
                raise ValueError("generation error lacks corresponding finish")
            caches[spec["id"]] = validate_result(result, renderings[spec["arm"]], protocol["settings"])
        elif row["outcome"] == "returned":
            raise ValueError("returned outcome lacks a generation result")
    # Reuse the established hash/quote checks, authored-field extraction and
    # missing-cell denominators. The predecessor itself remains unchanged.
    report = previous_review.review(root)
    report["schema"] = "study_evidence_order_review_v1"
    report["integrity"] = integrity
    report["renderings"] = {arm: None if row is None else {key: row[key] for key in ("token_count", "rendered_sha256")}
                            for arm, row in renderings.items()}
    report["cache_progression"] = caches
    report["pairs"] = [{"seed": seed, "planned": 2,
                        "outcomes": {row["arm"]: row["outcome"] for row in report["cells"] if row["seed"] == seed},
                        "nonempty": sum(row["nonempty"] for row in report["cells"] if row["seed"] == seed)}
                       for seed in SEEDS]
    report["limits"] = ("Four paired seeds, one retained episode, isolated MLX continuation of historical Minime Ollama input. "
                        "Block order, adjacency and terminal position change together; the pinned template trims message boundaries. "
                        "Equal token counts are not assumed. Rendered token IDs are retained receipts, not independently retokenized here. "
                        "Coding blinding follows annotation provenance. Missing/failed cells stay in denominators; length is descriptive. "
                        "No live Being inference, generated NEXT execution or checkpoint writes.")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(review(args.root.resolve()), indent=2, ensure_ascii=False))
