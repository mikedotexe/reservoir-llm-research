#!/usr/bin/env python3
"""Build an explicitly invoked frontend-only candidate after source-bound checks.

Never launch an app/model. Reuse prior Rust evidence only through exact preserved
input membership/content, with the five validated application-version changes.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

sys.dont_write_bytecode = True
from checks_common import ROOT, OUT, inputs, sha, utc, environment, execute, validate_metadata
sys.path.insert(0, str(ROOT / 'scripts'))
from qualification_receipt import package_inventory, source_inventory, file_entry

OLD = OUT.parent / '2026-10-15-compact-reading-0.24.0'
METADATA = {'package.json', 'package-lock.json', 'Cargo.lock', 'src-tauri/Cargo.toml', 'src-tauri/tauri.conf.json'}


def preserve_check():
    saved = json.loads((OUT / 'prior-preservation-01.json').read_text())
    assert saved['passed'] and saved['sourceUnchangedDuringPreservation']
    assert package_inventory(Path(saved['preservedApp'])) == saved['package']
    assert sha(Path(saved['archive'])) == saved['archiveSha256']
    assert sha(Path(saved['pinnedExecutable'])) == saved['pinnedExecutableSha256']
    for row in saved['sourceFiles']:
        assert file_entry(Path(saved['sourceSnapshot']) / row['path'], row['path']) == row
    return saved


def rust_reuse(saved):
    receipt = json.loads((OLD / 'rust-checks-01.json').read_text())
    assert receipt['passed'] and receipt['sourceUnchanged']
    assert receipt['sourceBefore'] == receipt['sourceAfter']
    for check in receipt['checks']:
        assert check['exitCode'] == 0 and sha(OLD / check['log']) == check['sha256']
    for name, digest in receipt['helperInputsSha256'].items():
        assert sha(OLD / name) == digest
    old = {r['path']: r['sha256'] for r in receipt['sourceAfter']}
    actual = inputs('rust')
    assert old.keys() == actual.keys(), 'Rust input membership changed'
    changes = []
    for name, digest in old.items():
        original = Path(saved['sourceSnapshot']) / 'desktop/ReservoirScope' / name
        assert sha(original) == digest, name
        if actual[name] != digest:
            assert name in METADATA, name
            assert (ROOT / name).read_bytes().replace(b'"0.25.0"', b'"0.24.0"') == original.read_bytes(), name
            changes.append(name)
    assert set(changes) == METADATA
    return {'scope': 'Reused prior Rust checks; not rerun. Exact inputs except validated application-version metadata.',
            'priorReceipt': str(OLD / 'rust-checks-01.json'), 'priorReceiptSha256': sha(OLD / 'rust-checks-01.json'),
            'inputCount': len(old), 'versionOnlyChanges': sorted(changes),
            'sourceInputsSha256': actual, 'checks': receipt['checks'], 'passed': True}


def main():
    saved = preserve_check()
    metadata = validate_metadata()
    rust = rust_reuse(saved)
    front_path = OUT / 'frontend-checks-01.json'
    front = json.loads(front_path.read_text())
    assert front['status'] == 'passed' and not front['sourceChangesDuringChecks']
    assert inputs('frontend') == front['sourceInputsSha256']
    for row in front['commands']:
        assert row['exitCode'] == 0 and sha(OUT / row['log']) == row['sha256']
    app = ROOT / 'target/release/bundle/macos/Reservoir Scope Tauri Preview.app'
    assert package_inventory(app) == saved['package']
    archive = app.parent / 'ReservoirScopeTauriPreview-0.25.0-macos-arm64.tar.gz'
    pinned = ROOT / 'target/qa/0.25.0-pinned'
    assert not archive.exists() and not pinned.exists()
    before = source_inventory()
    report = {'startedUtc': utc(), 'helperSha256': sha(Path(__file__)),
              'checksCommonSha256': sha(OUT / 'checks_common.py'),
              'frontendReceiptSha256': sha(front_path), 'rustQualificationReuse': rust,
              'sourceBefore': before, 'versionMetadataBefore': metadata, 'checks': []}
    with (OUT / 'source-before-build-01.json').open('x') as f:
        json.dump(report, f, indent=2); f.write('\n')
    check = execute('macos-package', ['npm', 'run', 'tauri', '--', 'build', '--bundles', 'app', '--', '--locked'], '01', environment())
    report['checks'].append(check)
    report.update(finishedUtc=utc(), sourceAfter=source_inventory())
    report['sourceUnchanged'] = report['sourceAfter'] == before
    with (OUT / 'package-build-01.json').open('x') as f:
        json.dump(report, f, indent=2); f.write('\n')
    assert check['exitCode'] == 0 and report['sourceUnchanged']
    assert validate_metadata() == metadata and inputs('frontend') == front['sourceInputsSha256']
    assert rust_reuse(saved) == rust
    built = package_inventory(app)
    assert built['version'] == built['build'] == '0.25.0'
    assert built['bundleIdentifier'] == 'research.reservoir.scope.tauri'
    with tarfile.open(archive, 'x:gz') as f:
        f.add(app, arcname=app.name)
    with tarfile.open(archive, 'r:gz') as f:
        for member in f.getmembers():
            original = app / Path(member.name).relative_to(app.name)
            if member.isfile():
                import hashlib
                assert hashlib.sha256(f.extractfile(member).read()).hexdigest() == sha(original)
            elif member.issym():
                assert original.is_symlink() and os.readlink(original) == member.linkname
            else:
                assert member.isdir() and original.is_dir()
    pinned.mkdir()
    exe = app / 'Contents/MacOS/reservoir-scope-desktop'
    shutil.copy2(exe, pinned / exe.name)
    assert sha(pinned / exe.name) == sha(exe)
    preserve_check()
    receipt = {'createdUtc': utc(), 'app': str(app), 'package': built, 'archive': str(archive),
               'archiveSha256': sha(archive), 'pinnedExecutable': str(pinned / exe.name),
               'executableSha256': sha(exe), 'priorPreservationVerified': True}
    with (OUT / 'archive-check-01.json').open('x') as f:
        json.dump(receipt, f, indent=2); f.write('\n')
    command = ['python3', 'scripts/qualification_receipt.py', '--app', str(app), '--archive', str(archive),
               '--output', str(OUT / 'qualification-before-ui-01.json'), '--note',
               '0.25 journal-first UI: fresh frontend checks/build; exact-input version-only reuse of 0.24 Rust qualification. Native UI unexecuted at capture. No model/service or Being interaction.']
    result = subprocess.run(command, cwd=ROOT)
    print(json.dumps({'packageBuild': check, 'archiveSha256': sha(archive), 'rustInputCount': rust['inputCount']}), flush=True)
    return result.returncode


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        with (OUT / 'package-failure-01.json').open('x') as f:
            json.dump({'createdUtc': utc(), 'error': f'{type(error).__name__}: {error}'}, f, indent=2)
        raise
