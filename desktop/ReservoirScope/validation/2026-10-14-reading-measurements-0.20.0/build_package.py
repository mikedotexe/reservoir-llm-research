#!/usr/bin/env python3
"""Prospective 0.20 build/archive wrapper adapted from qualified 0.19 tooling.

Do not run until the lead freezes final Rust/frontend receipts, preserves 0.19,
confirms GUI shutdown and coordinates disk/compiler use. Invocation performs a
build but never launches the GUI or a provider. No qualification has been run by
merely creating this preparation script.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))
from qualification_receipt import source_inventory, inventory_digest, package_inventory


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def validate_preserved(previous):
    assert previous['originalsUnchanged'] and previous['copiesByteExact']
    for key in ('archiveBefore', 'pinBefore', 'preservedArchive', 'preservedPin'):
        row = previous[key]
        path = Path(row['path'])
        assert not path.is_symlink() and path.is_file()
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], key
    assert package_inventory(Path(previous['preservedApp'])) == previous['package']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rust-receipt', type=Path, required=True)
    parser.add_argument('--frontend-receipt', type=Path, required=True)
    args = parser.parse_args()
    rust = json.loads(args.rust_receipt.read_text())
    assert rust['passed'] and rust['sourceUnchanged']
    for entry in rust['sourceAfter']:
        assert sha(ROOT / entry['path']) == entry['sha256'], entry['path']
    frontend = json.loads(args.frontend_receipt.read_text())
    assert frontend['status'] == 'passed' and not frontend['sourceChangesDuringChecks']
    # No stale comment/addendum exemption: use a final receipt for exact sources.
    for path, digest in frontend['sourceInputsSha256'].items():
        assert sha(ROOT / path) == digest, path
    previous = json.loads((OUT / 'prior-package-preserved-01.json').read_text())
    assert previous['passed']
    validate_preserved(previous)
    app = ROOT / 'target/release/bundle/macos/Reservoir Scope Tauri Preview.app'
    assert package_inventory(app) == previous['package'], 'Prior installed app changed'
    assert json.loads((ROOT / 'package.json').read_text())['version'] == '0.20.0'
    archive = app.parent / 'ReservoirScopeTauriPreview-0.20.0-macos-arm64.tar.gz'
    pinned = ROOT / 'target/qa/0.20-pinned'
    assert not archive.exists() and not pinned.exists(), 'New archive/pin must be exclusive'
    env = os.environ.copy()
    env.update(DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer',
               SDKROOT='/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk',
               CARGO_INCREMENTAL='0', CARGO_BUILD_JOBS='2',
               PATH='/Users/v/.cargo/bin:/Users/v/.nvm/versions/node/v20.20.1/bin:' + os.environ['PATH'])
    before = source_inventory()
    report = {'startedUtc': utc(), 'sourceBefore': before,
              'sourceInventorySha256': inventory_digest(before),
              'qualificationReceipts': [{'path': str(p.resolve()), 'sha256': sha(p)}
                                        for p in (args.rust_receipt, args.frontend_receipt)],
              'environment': {k: env[k] for k in ('DEVELOPER_DIR', 'SDKROOT', 'CARGO_INCREMENTAL', 'CARGO_BUILD_JOBS')},
              'checks': []}
    with (OUT / 'source-before-build-01.json').open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    commands = [('reference', ['python3', 'scripts/check_reference.py']),
                ('macos-package', ['npm', 'run', 'tauri', '--', 'build', '--bundles', 'app', '--', '--locked'])]
    for name, command in commands:
        began = time.monotonic()
        timestamp = utc()
        log = OUT / (name + '-01.log')
        with log.open('x') as stream:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
        report['checks'].append({'name': name, 'command': command, 'startedUtc': timestamp,
                                 'elapsedSeconds': time.monotonic() - began,
                                 'exitCode': result.returncode, 'logSha256': sha(log)})
        print(json.dumps(report['checks'][-1]), flush=True)
        if result.returncode:
            break
    report.update(sourceUnchanged=source_inventory() == before, finishedUtc=utc())
    with (OUT / 'package-build-01.json').open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    assert report['sourceUnchanged'] and len(report['checks']) == 2 and all(x['exitCode'] == 0 for x in report['checks'])
    built = package_inventory(app)
    assert built['version'] == '0.20.0' and built['build'] == '0.20.0'
    assert built['bundleIdentifier'] == 'research.reservoir.scope.tauri'
    with tarfile.open(archive, 'x:gz') as stream:
        stream.add(app, arcname=app.name)
    entries = []
    with tarfile.open(archive, 'r:gz') as stream:
        for member in stream.getmembers():
            relative = Path(member.name).relative_to(app.name)
            original = app / relative
            if member.isfile():
                digest = hashlib.sha256(stream.extractfile(member).read()).hexdigest()
                assert digest == sha(original)
                entries.append({'path': str(relative), 'sha256': digest, 'bytes': member.size})
            elif member.issym():
                assert original.is_symlink() and os.readlink(original) == member.linkname
            else:
                assert member.isdir() and original.is_dir()
    pinned.mkdir()
    executable = app / 'Contents/MacOS/reservoir-scope-desktop'
    shutil.copy2(executable, pinned / executable.name)
    assert sha(pinned / executable.name) == sha(executable)
    validate_preserved(previous)
    receipt = {'createdUtc': utc(), 'app': str(app), 'package': package_inventory(app),
               'archive': str(archive), 'archiveSha256': sha(archive), 'members': entries,
               'executableSha256': sha(executable), 'pinnedExecutable': str(pinned / executable.name),
               'priorArchiveAndPinUnchanged': True, 'priorFullAppCopyUnchanged': True}
    with (OUT / 'archive-check-01.json').open('x') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    command = ['python3', 'scripts/qualification_receipt.py', '--app', str(app),
               '--archive', str(archive), '--output', str(OUT / 'qualification-before-ui-01.json'),
               '--note', 'Source checks/build/archive evidence are retained separately. Native UI and provider execution remain unexecuted at capture.']
    return subprocess.run(command, cwd=ROOT, env=env).returncode


if __name__ == '__main__':
    raise SystemExit(main())
