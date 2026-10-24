#!/usr/bin/env python3
"""Build/freeze the four local studies or summarize their retained receipts.

Standard library only. Does not dispatch model calls; execution is the separate
``python -m reservoir_experiments run`` command. All generated text stays inside
the repository's ignored research/outputs directory.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reservoir_experiments import runner
from reservoir_experiments.scoring import score_run


def build(args):
    from reservoir_experiments.attribution_catalog import build_attribution, build_catalog
    from reservoir_experiments.correction_memory import build_correction, build_memory
    if args.study == "S-013":
        protocol = build_attribution(args.split, args.model)
    elif args.study == "S-014":
        protocol = build_correction(args.split, args.model)
    elif args.study == "S-015":
        if args.memory_packet is None:
            raise ValueError("S-015 requires a reviewed memory packet")
        packet = runner.read_json(args.memory_packet)
        protocol = build_memory(args.split, args.model, packet)
        protocol.setdefault("sources", []).append({"path": str(args.memory_packet.resolve()),
                                                    "sha256": runner.sha(args.memory_packet.read_bytes())})
        protocol["sources"].extend(packet.get("provenance_files", []))
    else:
        protocol = build_catalog(args.split, args.model, args.catalog)
        protocol.setdefault("sources", []).append({"path": str(args.catalog.resolve()),
                                                    "sha256": runner.sha(args.catalog.read_bytes())})
    builder = "attribution_catalog.py" if args.study in ("S-013", "S-016") else "correction_memory.py"
    for name in (builder, "scoring.py", "statistics.py"):
        source = ROOT / "reservoir_experiments" / name
        protocol.setdefault("sources", []).append({"path": str(source), "sha256": runner.sha(source.read_bytes())})
    path = runner.guard_output(args.out, ROOT)
    runner.validate_protocol(protocol)
    runner.write_json(path, protocol)
    return {"protocol": str(path), "sha256": runner.sha(path.read_bytes()),
            "nodes": len(protocol["nodes"]), "episodes": len({n["episode"] for n in protocol["nodes"]}),
            "study": args.study, "split": args.split, "model": args.model}


def evidence_files(run, node_ids):
    files = [Path(run) / name for name in ("manifest.json", "protocol.json", "identity.json")]
    files.extend(Path(run) / "nodes" / nid / "result.json" for nid in node_ids)
    return [{"path": str(path.resolve()), "sha256": runner.sha(runner.stable_read(path))} for path in files]


def transform_stage(args):
    from reservoir_experiments.correction_memory import build_memory_transforms, memory_review_packet
    runner.verify(args.run)
    _, source = runner.load_run(args.run)
    records = runner.read_results(args.run)
    if args.command == "transforms":
        protocol = build_memory_transforms(source, records)
        ids = [entry["source_id"] for entry in protocol["memory_sources"].values()]
        protocol["sources"] = evidence_files(args.run, ids)
        for name in ("correction_memory.py", "scoring.py", "statistics.py"):
            path = ROOT / "reservoir_experiments" / name
            protocol["sources"].append({"path": str(path), "sha256": runner.sha(path.read_bytes())})
        runner.validate_protocol(protocol)
        value = protocol
    else:
        value = memory_review_packet(source, records)
        value["provenance_files"] = list(source.get("sources", [])) + evidence_files(args.run, records)
    path = runner.guard_output(args.out, ROOT)
    runner.write_json(path, value)
    return {"path": str(path), "sha256": runner.sha(path.read_bytes()),
            "stage": args.command, "nodes": len(value.get("nodes", [])),
            "memories": len(value.get("memories", {})),
            "unavailable_sources": len(value.get("unavailable_sources", []))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("build")
    command.add_argument("study", choices=("S-013", "S-014", "S-015", "S-016"))
    command.add_argument("--split", choices=("development", "confirmation", "replication"), required=True)
    command.add_argument("--model", choices=("gemma4:12b", "mistral-small:24b"), required=True)
    command.add_argument("--catalog", type=Path)
    command.add_argument("--memory-packet", type=Path)
    command.add_argument("--out", type=Path, required=True)
    command = sub.add_parser("score")
    command.add_argument("run", type=Path)
    command.add_argument("--annotations", type=Path)
    command.add_argument("--baseline-run", type=Path)
    command.add_argument("--out", type=Path, required=True)
    for name in ("transforms", "review-packet"):
        command = sub.add_parser(name)
        command.add_argument("run", type=Path)
        command.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        result = build(args)
    elif args.command in ("transforms", "review-packet"):
        result = transform_stage(args)
    else:
        baseline = None
        if args.baseline_run:
            from reservoir_experiments.correction_memory import development_baseline
            runner.verify(args.baseline_run)
            _, protocol = runner.load_run(args.baseline_run)
            baseline = development_baseline(protocol, runner.read_results(args.baseline_run))
            _, target = runner.load_run(args.run)
            if protocol["model"] != target["model"]:
                raise ValueError("Development baseline must use the same model")
        result = score_run(args.run, annotations=args.annotations, out=args.out, baseline=baseline)
        result = {k: result[k] for k in ("study", "split", "model", "opportunities", "status_counts", "primary")}
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
