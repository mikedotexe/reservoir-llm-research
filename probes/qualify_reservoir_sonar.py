#!/usr/bin/env python3
"""Read-only native replay/scan qualification of explicitly supplied local exports.

Writes only a new output directory. Journal text is never interpreted as instructions.
This is apparatus qualification, not a model experiment or a topology inference.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inventory(root):
    files = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Source contains symlink: {path}')
        if path.is_file():
            files[str(path.relative_to(root))] = digest(path)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--export', action='append', required=True, metavar='LABEL=PATH')
    parser.add_argument('--scan', action='store_true', help='Also scan each verified final checkpoint')
    args = parser.parse_args()
    sources = []
    for item in args.export:
        label, path = item.split('=', 1)
        if not re.fullmatch(r'[a-z0-9-]+', label) or any(label == old[0] for old in sources):
            parser.error('Labels must be distinct lowercase alphanumeric/dash strings')
        source = Path(path).resolve(strict=True)
        if args.output.resolve().is_relative_to(source):
            parser.error('Output must be outside every source')
        sources.append((label, source))
    args.output.mkdir(parents=True, exist_ok=False)
    binary = args.binary.resolve(strict=True)

    def run(source):
        label, path = source
        before = inventory(path)
        (args.output / f'{label}-input-hashes.json').write_text(json.dumps(before, indent=2) + '\n')
        started = time.monotonic()
        reports = {}
        for operation in (['verify', 'scan'] if args.scan else ['verify']):
            target = args.output / f'{label}-{operation}.json'
            with target.open('w') as out, (args.output / f'{label}-{operation}.stderr').open('w') as err:
                completed = subprocess.run([str(binary), f'--{operation}-sustained', str(path)], stdout=out, stderr=err, timeout=1800, check=False)
            reports[operation] = {'exitCode': completed.returncode, 'output': target.name}
        unchanged = before == inventory(path)
        result = {'label': label, 'source': str(path), 'sourceUnchanged': unchanged,
                  'seconds': time.monotonic() - started, 'operations': reports,
                  'passed': unchanged and all(r['exitCode'] == 0 for r in reports.values())}
        print(json.dumps(result), flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, sources))
    report = {'binary': str(binary), 'binarySha256': digest(binary), 'modelsContacted': False,
              'results': results, 'passed': all(r['passed'] for r in results)}
    (args.output / 'qualification.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
