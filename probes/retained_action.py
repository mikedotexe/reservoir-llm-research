#!/usr/bin/env python3
"""Build, score and export S-018; this probe never accesses a model provider."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reservoir_experiments import runner, retained_action as study


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    command = sub.add_parser('design')
    command.add_argument('--split', choices=('development', 'confirmation'), required=True)
    command.add_argument('--out', type=Path, required=True)
    command = sub.add_parser('build')
    command.add_argument('design', type=Path)
    command.add_argument('--out', type=Path, required=True)
    command.add_argument('--ledger-out', type=Path, required=True)
    command.add_argument('--source', type=Path, action='append', default=[],
                         help='Additional immutable source, such as the prospective study or review')
    for name in ('score', 'reading'):
        command = sub.add_parser(name)
        command.add_argument('design', type=Path)
        command.add_argument('--run', type=Path, required=True)
        command.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = study.guard_output(args.out)
    if out.exists():
        raise ValueError('Refusing existing output')
    if args.command == 'design':
        value = study.make_design(args.split)
    elif args.command == 'build':
        ledger_out = study.guard_output(args.ledger_out)
        if ledger_out == out or ledger_out.exists():
            raise ValueError('Ledger output must be a distinct new path')
        value, ledger = study.build(args.design, additional_sources=args.source)
        runner.write_json(ledger_out, ledger)
        value['sources'].append(study.source(ledger_out))
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
