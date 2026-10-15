#!/usr/bin/env python3
"""Prospective native-phase freeze after the qualified 0.20 package exists.

Read/hash only; never launches a provider, verifier, app, build or toolchain.
The exclusive receipt also preserves failed admission to this qualification step.
Root must authorize execution and keep all frozen inputs unchanged afterward.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1]
sys.path.insert(0, str(DESKTOP / 'scripts'))
from qualification_receipt import file_entry, inventory_digest, package_inventory, source_inventory


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(path):
    require(path == path.resolve(strict=True), 'Redirected input: ' + str(path))
    row = file_entry(path, str(path))
    require(row['kind'] == 'file', 'Expected ordinary input: ' + str(path))
    return {key: row[key] for key in ('path', 'bytes', 'sha256')}


def load(name):
    return json.loads((HERE / name).read_text())


def verify_row(row, base=DESKTOP):
    path = Path(row['path'])
    if not path.is_absolute():
        path = base / path
    actual = identity(path)
    require(actual['sha256'] == row['sha256']
            and ('bytes' not in row or actual['bytes'] == row['bytes']),
            'Qualified input differs: ' + str(path))
    return actual


def main():
    output = HERE / 'prospective-freeze-01.json'
    report = {'schema': 'reservoir-v8-native-prospective-freeze-v1',
              'startedAtUtc': datetime.now(timezone.utc).isoformat(), 'status': 'running',
              'scope': 'Prospective fixed synthetic native procedure only. Existing receipt/source/package checks; no new process, build, UI, verifier or provider invocation.',
              'files': []}
    with output.open('x') as stream:
        try:
            names = [
                'PROTOCOL.md', 'PROMPT-V8-TEMPLATE.txt', 'QUALIFICATION-PLAN.md',
                'NATIVE-QUALIFICATION-PLAN.md', 'packaged-ui-plan-01.json',
                'owned_provider.py', 'test_owned_provider.py', 'synthetic-provider-copy-01.json',
                'check_fixture_export.py', 'test_check_fixture_export.py',
                'check_reanchored_tamper.py', 'test_reanchored_tamper.py',
                'run_helper_checks.py', 'synthetic-harness-tests-01.json', 'synthetic-harness-tests-01.log',
                'build_package.py', 'run_rust_checks_02.py', 'run_frontend_checks_02.py',
                'freeze_ui.py', 'compare_recovery.py',
                'rust-checks-02.json', 'frontend-checks-02.json',
                'archive-check-01.json', 'package-build-01.json', 'source-before-build-01.json',
                'qualification-before-ui-01.json', 'prior-package-preserved-01.json',
                'source-before-preparation-01.json', 'prior-v7-evidence-inventory-01.json',
                'replay_historical.py', 'prepare_historical_replay_01.py',
                'historical-replay-cases-01.json', 'historical-replay-preparation-01.json',
            ]
            paths = [HERE / name for name in names]
            helper = load('synthetic-harness-tests-01.json')
            require(helper['status'] == 'passed' and helper['sourceUnchanged']
                    and helper['exitCode'] == 0 and helper['testCount'] == 41,
                    'Expected final 41 passing pure helper tests')
            require(helper['sourceBefore'] == helper['sourceAfter'], 'Helper source changed during tests')
            for row in helper['sourceAfter']:
                actual = verify_row(row)
                paths.append(Path(actual['path']))
            verify_row(helper['log'])
            rust = load('rust-checks-02.json')
            require(rust['passed'] and rust['sourceUnchanged']
                    and rust['sourceBefore'] == rust['sourceAfter'], 'Rust checks/source failed')
            require([r['name'] for r in rust['checks']] == ['desktop-tests', 'core-clippy', 'desktop-clippy']
                    and all(r['exitCode'] == 0 for r in rust['checks']), 'Missing desktop/Clippy pass')
            for row in rust['sourceAfter']:
                verify_row(row)
            reused = rust['reusedCoreTests']
            verify_row({'path': reused['receipt'], 'sha256': reused['receiptSha256']})
            require(reused['check']['name'] == 'core-tests' and reused['check']['exitCode'] == 0,
                    'Missing preserved passing core test result')
            paths.append(Path(reused['receipt']))
            for row in [reused['check']] + rust['checks']:
                path = HERE / row['log']
                verify_row({'path': str(path), 'sha256': row['sha256']})
                paths.append(path)
            front = load('frontend-checks-02.json')
            require(front['status'] == 'passed' and not front['sourceChangesDuringChecks']
                    and all(row['exitCode'] == 0 for row in front['commands']), 'Frontend checks failed')
            for path, digest in front['sourceInputsSha256'].items():
                verify_row({'path': path, 'sha256': digest})
            for row in front['commands']:
                path = HERE / row['log']
                verify_row({'path': str(path), 'sha256': row['logSha256']})
                paths.append(path)
            built = load('package-build-01.json')
            require(built['sourceUnchanged'] and len(built['checks']) == 2
                    and all(row['exitCode'] == 0 for row in built['checks']), 'Build or reference gate failed')
            for row in built['qualificationReceipts']:
                verify_row(row)
            expected_checks = {str(HERE / 'rust-checks-02.json'), str(HERE / 'frontend-checks-02.json')}
            require({row['path'] for row in built['qualificationReceipts']} == expected_checks,
                    'Build did not use the intended final test receipts')
            source = source_inventory()
            before_build = load('source-before-build-01.json')
            qualification = load('qualification-before-ui-01.json')
            require(source == built['sourceBefore'] == before_build['sourceBefore']
                    == qualification['implementation']['files'], 'Current source differs from built/qualified source')
            require(qualification['codesign']['status'] == 'verified', 'Recorded package signature did not verify')
            archive = load('archive-check-01.json')
            app = DESKTOP / 'target/release/bundle/macos/Reservoir Scope Tauri Preview.app'
            pin = DESKTOP / 'target/qa/0.20-pinned/reservoir-scope-desktop'
            archive_path = app.parent / 'ReservoirScopeTauriPreview-0.20.0-macos-arm64.tar.gz'
            require(archive['app'] == str(app) and archive['pinnedExecutable'] == str(pin)
                    and archive['archive'] == str(archive_path), 'Unexpected packaged artifact path')
            package = package_inventory(app)
            require(package == archive['package'] == qualification['package'], 'Actual packaged files differ')
            require(package['version'] == package['build'] == '0.20.0'
                    and package['bundleIdentifier'] == 'research.reservoir.scope.tauri', 'Wrong packaged version/identity')
            require(identity(pin)['sha256'] == archive['executableSha256'] == package['binary']['sha256'],
                    'Pinned executable differs from package')
            require(identity(archive_path)['sha256'] == archive['archiveSha256']
                    == qualification['archive']['sha256'], 'Archive identity differs')
            paths += [pin, archive_path]
            prior = load('prior-package-preserved-01.json')
            require(prior['passed'] and prior['copiesByteExact'], 'Prior package preservation failed')
            for key in ('archiveBefore', 'pinBefore', 'preservedArchive', 'preservedPin'):
                verify_row(prior[key])
            require(package_inventory(Path(prior['preservedApp'])) == prior['package'], 'Preserved 0.19 app changed')
            fixture_out = DESKTOP / 'target/qa/0.20-reading-measurements-provider-01'
            require(not fixture_out.exists(), 'Prospective fixture directory already exists')
            rows = [identity(path) for path in sorted(set(paths))]
            require([identity(Path(row['path'])) for row in rows] == rows, 'Freeze inputs changed during read')
            require(source_inventory() == source and package_inventory(app) == package,
                    'Source/package changed during freeze')
            report.update(status='passed', frozenAt=datetime.now(timezone.utc).isoformat(), files=rows,
                          package=package, archive=identity(archive_path), pinnedExecutable=identity(pin),
                          sourceFileCount=len(source), sourceInventorySha256=inventory_digest(source),
                          sourceUnchanged=True, prior019ArtifactsUnchanged=True,
                          helperTests=41, historicalCases=14,
                          executionState='Preparation only; this tool did not launch native UI or the synthetic provider.')
        except Exception as error:
            report.update(status='failed', error=f'{type(error).__name__}: {error}')
        report['endedAtUtc'] = datetime.now(timezone.utc).isoformat()
        json.dump(report, stream, indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({'status': report['status'], 'files': len(report['files']), 'output': str(output),
                      'error': report.get('error')}))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
