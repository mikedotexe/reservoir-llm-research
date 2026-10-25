#!/usr/bin/env python3
"""Build, preview, score, gate and export S-020 without provider access."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reservoir_experiments import runner, reproduced_check as study


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    command = sub.add_parser('design')
    command.add_argument('--split', choices=study.SPLITS, required=True)
    command.add_argument('--out', type=Path, required=True)
    command = sub.add_parser('build')
    command.add_argument('design', type=Path)
    command.add_argument('--out', type=Path, required=True)
    command.add_argument('--ledger-out', type=Path, required=True)
    command.add_argument('--reproduction-gate', type=Path)
    command.add_argument('--matched-gate', type=Path)
    command.add_argument('--source', type=Path, action='append', default=[])
    for name in ('preview', 'score', 'gate', 'reading'):
        command = sub.add_parser(name)
        command.add_argument('design', type=Path)
        command.add_argument('--out', type=Path, required=True)
        if name != 'preview':
            command.add_argument('--run', type=Path, required=True)
        if name == 'gate':
            command.add_argument('--score', type=Path, required=True)
    args = parser.parse_args()
    out = study.guard_output(args.out)
    if out.exists():
        raise ValueError('Refusing existing output')
    if args.command == 'design':
        value = study.make_design(args.split)
    elif args.command == 'preview':
        value = study.preview(args.design)
    elif args.command == 'build':
        ledger_out = study.guard_output(args.ledger_out)
        if ledger_out == out or ledger_out.exists():
            raise ValueError('Ledger must be a distinct new path')
        value, ledger = study.build(args.design, reproduction_gate=args.reproduction_gate,
                                    matched_gate=args.matched_gate, additional_sources=args.source)
        runner.write_json(ledger_out, ledger)
        value['sources'].append(study.source(ledger_out))
    elif args.command == 'gate':
        value = study.make_gate(args.design, args.run, args.score)
    elif args.command == 'reading':
        value = study.reading(args.design, args.run, out)
        print(json.dumps({'out': str(out), 'packets': value['packets']}))
        return
    else:
        value = study.score(args.design, args.run)
    runner.write_json(out, value)
    print(json.dumps({'out': str(out), 'sha256': study.digest(out),
                      'nodes': len(value.get('nodes', [])), 'rows': len(value.get('rows', []))}))


if __name__ == '__main__':
    main()
