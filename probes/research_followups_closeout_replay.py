#!/usr/bin/env python3
"""Build or verify closeout from a private input snapshot; no recovery command."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reservoir_research.followup_closeout_replay import build, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "verify"):
        p = sub.add_parser(name)
        p.add_argument("inputs")
        p.add_argument("--data-root", required=True)
        p.add_argument("--out" if name == "build" else "--report", required=True)
    args = parser.parse_args()
    if args.command == "build":
        value = build(args.inputs, args.data_root, args.out)
    else:
        value = verify(args.inputs, args.data_root, args.report)
    print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
