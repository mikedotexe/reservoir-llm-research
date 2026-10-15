#!/usr/bin/env python3
"""Exclusive numbered receipts for explicit file/synthetic checks; no model launch."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def identity(path):
    path = Path(path).resolve(); raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def main():
    mode = sys.argv[1]; number = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    destination = HERE / f'{mode}-{number:02}.json'; log = HERE / f'{mode}-{number:02}.log'
    if destination.exists() or log.exists(): raise FileExistsError(destination)
    sources = sorted(HERE.glob('*.py')) + [HERE / 'run-plan.json']
    before = [identity(p) for p in sources]
    commands = {
        'preparation-checks': [sys.executable, '-m', 'unittest', '-v', 'test_prepare_inputs'],
        'input-generation': [sys.executable, 'prepare_inputs.py'],
        'runtime-checks': [sys.executable, '-m', 'unittest', '-v', 'test_owned_model', 'test_run_probe',
                           'test_render_blind_pack', 'test_runtime_reuse', 'test_admit_once', 'test_freeze_dependencies'],
    }
    args = commands[mode]; started = dt.datetime.now(dt.timezone.utc).isoformat()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    run = subprocess.run(args, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120, env=env)
    ended = dt.datetime.now(dt.timezone.utc).isoformat()
    with log.open('xb') as stream: stream.write(run.stdout)
    after = [identity(p) for p in sources]
    matches = re.findall(r'Ran (\d+) tests? in', run.stdout.decode())
    result = dict(startedUtc=started, endedUtc=ended, command=args, environment={'PYTHONDONTWRITEBYTECODE': '1'},
                  exitCode=run.returncode, passed=run.returncode == 0 and before == after,
                  sourceUnchanged=before == after, sourceBefore=before, sourceAfter=after,
                  testsRun=int(matches[-1]) if matches else None, log=identity(log),
                  scope='Synthetic/file-only tests or file-only preparation. Host admission is mocked; no model/owned provider/live host admission.')
    if mode == 'input-generation' and run.returncode == 0:
        result['outputs'] = [identity(p) for p in sorted((HERE / 'prompts').glob('*.txt'))] + [
            identity(HERE / 'transformation-checks-01.json'), identity(HERE / 'frozen-inputs.json')]
    with destination.open('x') as stream: json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps(dict(mode=mode, passed=result['passed'], tests=result['testsRun'], receipt=identity(destination),
                         tail=run.stdout.decode()[-1400:])))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
