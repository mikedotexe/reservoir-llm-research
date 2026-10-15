"""Source-bound frontend qualification. No application or model launch."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
NODE = Path('/Users/v/.nvm/versions/node/v20.20.1/bin')


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    paths = set((ROOT / 'src').rglob('*'))
    paths.update(ROOT.glob('tsconfig*.json'))
    paths.update(ROOT / p for p in ['package.json', 'package-lock.json', 'vite.config.ts'])
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths) if p.is_file()}


if __name__ == '__main__':
    env = dict(os.environ, PATH=str(NODE) + ':' + os.environ['PATH'])
    before = inputs()
    report = {'schema': 'reservoir-scope-frontend-source-checks-v1', 'startedAtUtc': utc(),
              'scope': 'Frontend tests and TypeScript; v8/historical contracts, inert prose, sequential journal reading and stale-result handling. No app, provider or real model.',
              'sourceInputsSha256': before, 'commands': []}
    commands = [('frontend-tests', [str(NODE / 'npm'), 'test']),
                ('frontend-typescript', [str(NODE / 'node'), 'node_modules/typescript/bin/tsc', '--noEmit'])]
    for name, command in commands:
        log = OUT / (name + '-01.log')
        item = {'command': command, 'startedAtUtc': utc(), 'log': log.name}
        with log.open('x') as stream:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
        item.update(finishedAtUtc=utc(), exitCode=result.returncode, logSha256=sha(log))
        report['commands'].append(item)
        print(json.dumps(item), flush=True)
        if result.returncode:
            break
    after = inputs()
    report['sourceChangesDuringChecks'] = [p for p in sorted(before.keys() | after.keys()) if before.get(p) != after.get(p)]
    output = (OUT / 'frontend-tests-01.log').read_text()
    counts = re.search(r'Test Files\s+(\d+) passed.*?Tests\s+(\d+) passed', output, re.S)
    report['counts'] = {'testFiles': int(counts[1]), 'tests': int(counts[2])} if counts else None
    report['status'] = 'passed' if len(report['commands']) == 2 and all(c['exitCode'] == 0 for c in report['commands']) and not report['sourceChangesDuringChecks'] else 'failed'
    report['finishedAtUtc'] = utc()
    with (OUT / 'frontend-checks-01.json').open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': report['status'], 'counts': report['counts']}), flush=True)
    raise SystemExit(0 if report['status'] == 'passed' else 1)
