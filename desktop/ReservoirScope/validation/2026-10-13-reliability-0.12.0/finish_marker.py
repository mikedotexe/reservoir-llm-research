#!/usr/bin/env python3
"""Append an operator marker with passive owned-session/process evidence; no UI or signals."""
import argparse
import datetime as dt
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'scripts'))
from macos_reliability import MacProcess, manifest_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', required=True)
    parser.add_argument('--event', required=True)
    parser.add_argument('--note', required=True)
    parser.add_argument('--require-two-hours', action='store_true')
    args = parser.parse_args()
    prior = [json.loads(line) for line in (HERE / 'ui-markers.jsonl').read_text().splitlines()]
    minimum = next(row for row in prior if row['event'] == 'minimize-action-acknowledged')
    now, mono = dt.datetime.now(dt.timezone.utc), time.monotonic_ns()
    lower = (mono - int(minimum['monotonicNs'])) / 1e9
    if args.require_two_hours and lower < 7200:
        raise ValueError('Two actual hours have not yet elapsed; do not activate the window')
    expected = next(row for row in json.loads((HERE / 'owned-process-identities.json').read_text())['processes'] if row['role'] == 'app')
    identity = MacProcess(expected['pid']).identity()
    if any(identity[key] != expected[key] for key in ('pid', 'startSeconds', 'startMicroseconds', 'executablePath')):
        raise ValueError('Original app process identity changed; preserve interruption separately')
    session = Path('/Users/v/Library/Application Support/research.reservoir.scope.tauri/sustained-v1/sustained-1791908510756-1')
    snapshot = manifest_snapshot(session)
    row = dict(phase=args.phase, event=args.event, wallUtc=now.isoformat(), monotonicNs=str(mono),
               secondsSinceMinimizeMarker=lower, processIdentity=identity, manifest=snapshot, note=args.note)
    with (HERE / 'ui-markers.jsonl').open('a') as output:
        output.write(json.dumps(row, separators=(',', ':')) + '\n')
    print(json.dumps(row))


if __name__ == '__main__':
    main()
