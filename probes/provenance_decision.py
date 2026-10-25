#!/usr/bin/env python3
"""Build, score and export S-017; provider dispatch stays in reservoir_experiments."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reservoir_experiments import runner, provenance_decision as study


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    command = sub.add_parser('design')
    command.add_argument('--split', choices=('development', 'confirmation'), required=True)
    command.add_argument('--out', type=Path, required=True)
    command = sub.add_parser('build-stage')
    command.add_argument('design', type=Path)
    command.add_argument('stage', choices=study.STAGES)
    command.add_argument('--initial-run', type=Path)
    command.add_argument('--revision-run', type=Path)
    command.add_argument('--out', type=Path, required=True)
    command.add_argument('--ledger-out', type=Path, required=True)
    command.add_argument('--source', type=Path, action='append', default=[], help='Additional immutable source, e.g. the prospective study document')
    for name in ('score', 'reading'):
        command = sub.add_parser(name)
        command.add_argument('design', type=Path)
        for stage in study.STAGES:
            command.add_argument('--' + stage + '-run', type=Path, required=True)
        command.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = runner.guard_output(args.out, ROOT)
    if out.exists():
        raise ValueError('Refusing existing output')
    if args.command == 'design':
        value = study.make_design(args.split)
    elif args.command == 'build-stage':
        ledger_out = runner.guard_output(args.ledger_out, ROOT)
        if ledger_out == out or ledger_out.exists():
            raise ValueError('Ledger output must be a distinct new path')
        value, ledger = study.build_stage(args.design, args.stage, initial_run=args.initial_run, revision_run=args.revision_run)
        value['sources'].extend(study._source(path) for path in args.source)
        runner.write_json(ledger_out, ledger)
        value['sources'].append(study._source(ledger_out))
        if not value['nodes']:
            value = {'stage': args.stage, 'no_dispatch': True, 'ledger': str(ledger_out), 'reason': 'No eligible nodes'}
    else:
        runs = {s: getattr(args, s + '_run') for s in study.STAGES}
        if args.command == 'reading':
            value = study.reading(args.design, runs, out)
            print(json.dumps({'out': str(out), 'packets': value['packets']}))
            return
        value = study.score(args.design, runs)
    runner.write_json(out, value)
    print(json.dumps({'out': str(out), 'sha256': study.digest(out), 'nodes': len(value.get('nodes', [])),
                      'rows': len(value.get('rows', []))}))


if __name__ == '__main__':
    main()
