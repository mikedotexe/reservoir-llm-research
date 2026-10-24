"""Command-line interface for isolated local experiments."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from . import runner


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m reservoir_experiments")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="Freeze a protocol and explicit source inputs")
    prepare.add_argument("protocol", type=Path)
    prepare.add_argument("--out", type=Path, required=True)
    command = commands.add_parser("qualify", help="Explicit larger-context token-count probe; one physical call")
    command.add_argument("protocol", type=Path)
    command.add_argument("node_id")
    command.add_argument("--out", type=Path, required=True)
    command.add_argument("--qualification-num-ctx", type=int, default=32768)
    for name in ("run", "resume"):
        command = commands.add_parser(name, help="Dispatch only never-attempted cells")
        command.add_argument("run", type=Path)
        command.add_argument("--limit", type=int)
        command.add_argument("--identity-every", type=int, default=20)
    for name in ("status", "verify"):
        command = commands.add_parser(name)
        command.add_argument("run", type=Path)
        command.add_argument("--verbose", action="store_true")
    command = commands.add_parser("blind")
    command.add_argument("run", type=Path)
    command.add_argument("--out", type=Path, required=True)
    command.add_argument("--seed", type=int, default=20261024)
    command.add_argument("--kind", action="append", dest="kinds")
    command = commands.add_parser("score")
    command.add_argument("run", type=Path)
    command.add_argument("--annotations", type=Path)
    command.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = runner.prepare(args.protocol, args.out)
            result = {k: result[k] for k in ("protocol_id", "opportunities", "git_head")}
        elif args.command == "qualify":
            result = runner.qualify(args.protocol, args.node_id, args.out,
                                    qualification_num_ctx=args.qualification_num_ctx)
        elif args.command in ("run", "resume"):
            result = runner.run_protocol(args.run, limit=args.limit, identity_every=args.identity_every,
                                         progress=lambda record: print(json.dumps(record), flush=True))
            result.pop("nodes", None)
        elif args.command == "status":
            result = runner.status(args.run)
            if not args.verbose:
                result.pop("nodes", None)
        elif args.command == "verify":
            result = runner.verify(args.run)
            if not args.verbose:
                result["status"].pop("nodes", None)
        elif args.command == "blind":
            result = runner.blind(args.run, args.out, seed=args.seed, kinds=args.kinds)
        else:
            runner.verify(args.run)
            try:
                from .scoring import score_run
            except ImportError as exc:
                raise runner.ExperimentError("Study scoring module is not installed") from exc
            result = score_run(args.run, annotations=args.annotations, out=args.out)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
        return 0
    except (runner.ExperimentError, runner.TransportError, ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc), "command": args.command}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
