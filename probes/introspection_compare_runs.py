#!/usr/bin/env python3
"""Read-only comparison of exact requests and completed texts across retained runs."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reservoir_experiments import runner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--kind", action="append")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    for run in (args.left, args.right):
        runner.verify(run)
    _, a = runner.load_run(args.left)
    _, b = runner.load_run(args.right)
    ar, br = runner.read_results(args.left), runner.read_results(args.right)
    bn = {n["id"]: n for n in b["nodes"]}
    pairs = []
    for node in a["nodes"]:
        nid = node["id"]
        if nid not in bn or args.kind and node["kind"] not in args.kind:
            continue
        left, right = args.left / "nodes" / nid / "request.json", args.right / "nodes" / nid / "request.json"
        attempted = left.exists() and right.exists()
        complete = ar.get(nid, {}).get("status") == br.get(nid, {}).get("status") == "complete"
        pairs.append({"node": nid, "kind": node["kind"], "both_requests": attempted,
                      "same_request": left.read_bytes() == right.read_bytes() if attempted else None,
                      "both_complete": complete,
                      "same_text": ar[nid]["text"] == br[nid]["text"] if complete else None})
    summary = {"left": a["id"], "right": b["id"], "pairs": len(pairs),
               "by_kind": dict(Counter(p["kind"] for p in pairs)),
               "same_requests": sum(p["same_request"] is True for p in pairs),
               "both_complete": sum(p["both_complete"] for p in pairs),
               "same_complete_texts": sum(p["same_text"] is True for p in pairs),
               "same_provider_identity": runner.stable_read(args.left / "identity.json") == runner.stable_read(args.right / "identity.json"),
               "scope": "instrument comparison; not a prospectively selected independent replication"}
    report = {"summary": summary, "pairs": pairs,
              "manifest_hashes": [runner.sha(runner.stable_read(r / "manifest.json")) for r in (args.left, args.right)]}
    runner.write_json(runner.guard_output(args.out, ROOT), report)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
