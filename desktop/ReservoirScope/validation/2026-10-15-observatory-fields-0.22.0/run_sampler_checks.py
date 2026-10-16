#!/usr/bin/env python3
"""Explicit synthetic sampler checks; no app, process query or capture execution."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def files():
    paths = [Path(__file__), HERE / 'sample_owned_app.py', HERE / 'test_sample_owned_app.py', ROOT / 'scripts/macos_reliability.py']
    return [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', default='01')
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9]{2}', args.attempt):
        raise ValueError('Expected two-digit exclusive attempt')
    receipt = HERE / f'sampler-checks-{args.attempt}.json'
    log = HERE / f'sampler-checks-{args.attempt}.log'
    if receipt.exists() or log.exists():
        raise ValueError('Check outputs must not exist')
    command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(HERE), '-p', 'test_sample_owned_app.py', '-v']
    report = {'schema': 'reservoir-observatory-sampler-checks-v1', 'startedAtUtc': utc(), 'status': 'running',
              'command': command, 'sourceBefore': files(), 'scope': __doc__}
    with receipt.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
        try:
            with log.open('x') as output:
                result = subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
            report.update(exitCode=result.returncode, sourceAfter=files())
            report['sourceUnchanged'] = report['sourceBefore'] == report['sourceAfter']
            content = log.read_text()
            match = re.search(r'Ran (\d+) tests?', content)
            report['testsRun'] = int(match[1]) if match else None
            report['log'] = {'path': str(log), 'sha256': hashlib.sha256(log.read_bytes()).hexdigest()}
            report['status'] = 'passed' if result.returncode == 0 and report['sourceUnchanged'] and report['testsRun'] else 'failed'
        except Exception as error:
            report.update(status='failed', error=f'{type(error).__name__}: {error}')
        report['endedAtUtc'] = utc()
        stream.seek(0)
        json.dump(report, stream, indent=2)
        stream.write('\n')
        stream.truncate()
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({'status': report['status'], 'testsRun': report.get('testsRun'), 'receipt': str(receipt)}))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
