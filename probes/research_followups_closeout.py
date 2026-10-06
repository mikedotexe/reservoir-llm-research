#!/usr/bin/env python3
"""One bounded historical recovery; explicit-input offline build and verification."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reservoir_research.followup_closeout import recover, build, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("recover")
    p.add_argument("plan")
    p.add_argument("--data-root", required=True)
    p = sub.add_parser("build")
    p.add_argument("inputs")
    p.add_argument("--data-root", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("verify")
    p.add_argument("inputs")
    p.add_argument("--data-root", required=True)
    p.add_argument("--report", required=True)
    args = parser.parse_args()
    if args.command == "recover":
        result = recover(args.plan, args.data_root)
    elif args.command == "build":
        result = build(args.inputs, args.data_root, args.out)
    else:
        result = verify(args.inputs, args.data_root, args.report)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
