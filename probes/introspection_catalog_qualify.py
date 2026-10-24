#!/usr/bin/env python3
"""Qualify exact catalog prompts serially and enforce the frozen 1% length match.

This probe makes explicit local model calls with one output token at context32768.
It never consumes their generated prose. Study context stays16384. Completed
qualification receipts can be reused; a dispatched unfinished probe is not retried.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reservoir_experiments import runner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("protocol", type=Path)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--case-index", type=int, action="append")
    args = parser.parse_args()
    protocol = runner.read_json(args.protocol)
    if protocol["study"] != "S-016":
        raise ValueError("Only static S-016 protocols are eligible")
    runner.validate_protocol(protocol)
    root = runner.guard_output(args.qualification_root, ROOT)
    known, unfinished = {}, set()
    for request in sorted(root.glob("**/planned-request.json")):
        key = runner.prompt_hash(runner.read_json(request))
        directory = request.parent
        if (directory / "qualification.json").exists():
            q = runner.read_qualification(directory)
            known[key] = (directory, q)
        elif (directory / "dispatch.json").exists():
            unfinished.add(key)
    selected = [n for n in protocol["nodes"] if args.case_index is None or n["metadata"]["case_index"] in args.case_index]
    used, counts = {}, {}
    for node in selected:
        if node.get("inputs"):
            raise ValueError("Catalog qualification requires static prompts")
        request = json.loads(runner.render_request(protocol, node, {}, check_context=False))
        key = runner.prompt_hash(request)
        if key not in known:
            if key in unfinished:
                raise ValueError(f"Unresolved qualification attempt for {key}; no retry")
            directory = root / "exact-prompts" / key
            q = runner.qualify(args.protocol, node["id"], directory)
            known[key] = (directory, q)
            print(json.dumps({"qualified_node": node["id"], "prompt_tokens": q["prompt_eval_count"]}), flush=True)
        directory, q = known[key]
        if q["planned_num_ctx"] != protocol["options"]["num_ctx"]:
            raise ValueError("Qualified planned context differs")
        used[key] = str(directory.resolve())
        counts[node["id"]] = q["prompt_eval_count"]
    cells = {(n["episode"], n["seed"], n["condition"]): counts[n["id"]]
             for n in selected if not n["metadata"].get("replicate")}
    matches = []
    for node in selected:
        if node["condition"] not in ("concise_padded", "neutral"):
            continue
        full = cells[(node["episode"], node["seed"], "full")]
        count = counts[node["id"]]
        residual = (count - full) / full
        matches.append({"node": node["id"], "full": full, "tokens": count,
                        "fractional_residual": residual, "qualified": abs(residual) <= .01})
    report = {"kind": "catalog-token-qualification", "base_protocol_sha256": runner.sha(args.protocol.read_bytes()),
              "unique_prompts": len(used), "opportunities": len(selected), "matches": matches,
              "all_within_one_percent": all(m["qualified"] for m in matches)}
    out = runner.guard_output(args.out, ROOT)
    if args.case_index is not None:
        runner.write_json(out, report)
    else:
        if not report["all_within_one_percent"]:
            raise ValueError("Input token matching exceeds1%; qualify adjusted padding before study outcomes")
        protocol["context_qualifications"] = list(used.values())
        protocol["token_matching"] = report
        runner.write_json(out, protocol)
    print(json.dumps({"out": str(out), "unique_prompts": len(used),
                      "all_within_one_percent": report["all_within_one_percent"],
                      "max_abs_residual": max(abs(m["fractional_residual"]) for m in matches)}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
