#!/usr/bin/env python3
"""Read-only 0.20 closeout against the fixed, already-executed receipt set.

No subprocess, verifier, application, UI, provider, network or lifecycle action.
The only write is an exclusive closeout receipt in this validation directory.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1]
ROOT = DESKTOP.parents[1]
sys.path.insert(0, str(DESKTOP / 'scripts'))
# These functions only read files. Do not call capture()/observe(), which run tools.
from qualification_receipt import file_entry, inventory_digest, package_inventory, source_inventory

ALLOWED_DOCS = {'TAURI-ROADMAP.md', 'shared/reservoir-scope/PARITY.md',
                'desktop/ReservoirScope/README.md'}
INPUTS = {}


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(value, message):
    if not value:
        raise ValueError(message)


def identity(path):
    path = Path(path).absolute()
    require(path == path.resolve(strict=True), 'Redirected input: ' + str(path))
    entry = file_entry(path, str(path))
    require(entry['kind'] == 'file', 'Not an ordinary file: ' + str(path))
    row = {k: entry[k] for k in ('path', 'bytes', 'sha256')}
    previous = INPUTS.setdefault(str(path), row)
    require(previous == row, 'Input changed during closeout: ' + str(path))
    return row


def load(name):
    path = HERE / name
    identity(path)
    return json.loads(path.read_bytes())


def verify_row(row, base=ROOT):
    path = Path(row['path'])
    if not path.is_absolute():
        path = base / path
    actual = identity(path)
    require(actual['sha256'] == row['sha256']
            and ('bytes' not in row or actual['bytes'] == row['bytes']),
            'Recorded identity differs: ' + str(path))
    if 'mode' in row:
        require(oct(path.stat().st_mode & 0o7777) == row['mode'], 'Recorded mode differs: ' + str(path))
    return actual


def inventory(directory):
    directory = Path(directory)
    require(directory == directory.resolve(strict=True), 'Redirected directory')
    rows = {}
    for parent, directories, files in os.walk(directory, followlinks=False):
        require(not any((Path(parent) / n).is_symlink() for n in directories), 'Linked directory in evidence')
        for name in sorted(files):
            path = Path(parent) / name
            row = identity(path)
            rows[path.relative_to(directory).as_posix()] = {k: row[k] for k in ('bytes', 'sha256')}
    return dict(sorted(rows.items()))


def listed_inventory(rows):
    return {r['path']: {k: r[k] for k in ('bytes', 'sha256')} for r in rows}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def local_links(path):
    # Validate file targets, not Markdown heading anchors or remote destinations.
    text = path.read_text()
    text = re.sub(r'^(```|~~~).*?^\1[^\n]*$', '', text, flags=re.M | re.S)
    targets = re.findall(r'\[[^\]\n]*\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\)', text)
    targets += re.findall(r'^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)', text, flags=re.M)
    local, skipped = [], []
    for raw in targets:
        target = raw.strip('<>')
        parts = urlsplit(target)
        if parts.scheme or parts.netloc or not parts.path:
            skipped.append(target)
            continue
        target_path = Path(unquote(parts.path))
        if not target_path.is_absolute():
            target_path = path.parent / target_path
        target_path = target_path.resolve(strict=False)
        # Documentation links are checked only within the authorized research workspaces.
        require(target_path.is_relative_to(ROOT)
                or target_path.is_relative_to(Path('/Users/v/other/reservoir-llm-research')),
                'Local link outside authorized research workspaces: ' + str(target_path))
        local.append({'target': target, 'resolvedPath': str(target_path), 'exists': target_path.exists()})
    return {'document': str(path), 'localLinks': local, 'localLinkCount': len(local),
            'missing': [row for row in local if not row['exists']],
            'remoteOrAnchorOnlyLinksNotChecked': len(skipped),
            'scope': 'Local file existence only; URL availability and heading anchors not evaluated.'}


def main():
    output = HERE / 'closeout-01.json'
    report = {'schema': 'reservoir-v8-closeout-preservation-v1', 'startedAtUtc': utc(),
              'status': 'running', 'scope': 'Fixed 0.20 receipt-set preservation and documentation closeout only.',
              'runtimeActions': False, 'modelsContacted': False, 'newVerifierInvocations': 0,
              'checks': {}, 'errors': [], 'script': identity(Path(__file__))}

    def check(name, action):
        try:
            report['checks'][name] = {'status': 'passed', **action()}
        except Exception as error:
            message = f'{type(error).__name__}: {error}'
            report['checks'][name] = {'status': 'failed', 'error': message}
            report['errors'].append({'check': name, 'error': message})

    with output.open('x') as stream:
        json.dump(report, stream, indent=2); stream.flush(); os.fsync(stream.fileno())

        def frozen():
            receipt = load('prospective-freeze-01.json')
            require(receipt['status'] == 'passed' and len(receipt['files']) == 45, 'Expected 45 frozen inputs')
            rows = [verify_row(row) for row in receipt['files']]
            return {'basis': identity(HERE / 'prospective-freeze-01.json'), 'count': len(rows),
                    'allUnchanged': True, 'currentIdentitiesSha256': digest(rows)}
        check('frozenInputs', frozen)

        def packages():
            archive = load('archive-check-01.json')
            qualification = load('qualification-before-ui-01.json')
            freeze = load('prospective-freeze-01.json')
            current = package_inventory(Path(archive['app']))
            require(current == archive['package'] == qualification['package'] == freeze['package'],
                    'Current packaged app differs')
            require(current['version'] == current['build'] == '0.20.0', 'Wrong current package version')
            current_archive = verify_row(freeze['archive'])
            pin = verify_row(freeze['pinnedExecutable'])
            require(current_archive['sha256'] == archive['archiveSha256'] == qualification['archive']['sha256'],
                    'Current archive differs')
            require(pin['sha256'] == current['binary']['sha256'] == archive['executableSha256'], 'Current pin differs')
            prior = load('prior-package-preserved-01.json')
            require(prior['passed'] and prior['copiesByteExact'], 'Prior preservation did not pass')
            rows = {key: verify_row(prior[key]) for key in
                    ('archiveBefore', 'pinBefore', 'preservedArchive', 'preservedPin')}
            require(package_inventory(Path(prior['preservedApp'])) == prior['package'], 'Preserved 0.19 app differs')
            require(prior['package']['version'] == '0.19.0', 'Wrong preserved package')
            return {'packageFiles': len(current['files']), 'packageInventorySha256': current['inventorySha256'],
                    'archive': current_archive, 'pin': pin, 'preserved019Files': len(prior['package']['files']),
                    'preserved019InventorySha256': prior['package']['inventorySha256'],
                    'priorOriginalsAndCopies': rows,
                    'codesign': 'Existing qualification receipt says verified; no new codesign invocation.',
                    'archiveMembers': 'Whole archive bytes match prior member-verified receipt; no re-extraction.'}
        check('packagesAndPins', packages)

        def prior_validation():
            basis = load('prior-v7-evidence-inventory-01.json')
            count = 0
            result = []
            for episode, rows in basis['filesByEpisode'].items():
                expected = {str(Path(r['path']).relative_to((HERE.parent / episode).relative_to(ROOT))):
                            {k: r[k] for k in ('bytes', 'sha256')} for r in rows}
                actual = inventory(HERE.parent / episode)
                # Match source inventory policy: bytecode caches are not evidence inputs.
                actual = {k: v for k, v in actual.items() if '__pycache__' not in Path(k).parts
                          and not k.endswith(('.pyc', '.pyo')) and Path(k).name != '.DS_Store'}
                require(actual == expected, 'Prior v7 validation inventory differs: ' + episode)
                count += len(actual)
                result.append({'episode': episode, 'fileCount': len(actual), 'inventorySha256': digest(actual)})
            require(count == basis['fileCount'] == 127, 'Expected 127 prior v7 validation files')
            return {'fileCount': count, 'episodes': result, 'allUnchanged': True}
        check('priorV7Validation', prior_validation)

        def historical():
            selection = load('historical-replay-cases-01.json')
            replay = load('historical-replay-01.json')
            require(replay['status'] == 'passed' and replay['allOriginalsUnchanged'], 'Historical replay did not pass')
            verify_row(replay['selection'])
            require(len(selection['cases']) == len(replay['cases']) == 14, 'Expected 14 selected historical exports')
            rows = []
            for selected, verified in zip(selection['cases'], replay['cases']):
                require(selected['name'] == verified['name'] and selected['bundle'] == verified['bundle'],
                        'Historical selection/replay identities differ')
                actual = inventory(Path(selected['bundle']))
                require(actual == selected['expectedInventory'] == verified['inventoryBefore'] == verified['inventoryAfter'],
                        'Historical export changed: ' + selected['name'])
                rows.append({'name': selected['name'], 'bundle': selected['bundle'], 'promptVersion': selected['promptVersion'],
                             'files': len(actual), 'inventorySha256': digest(actual), 'unchanged': True})
            require(sum(r['files'] for r in rows) == 665, 'Expected 665 selected historical files')
            return {'cases': rows, 'caseCount': len(rows), 'fileCount': 665, 'newReplayInvocations': 0,
                    'v2HistoricalExportCoverage': selection['v2HistoricalExportCoverage']}
        check('historicalExports', historical)

        def synthetic_exports():
            basis = load('recovery-comparison-01.json')
            require(basis['status'] == 'passed', 'Recovery comparison did not pass')
            for row in basis['verificationReceipts']:
                verify_row(row)
            a, b = Path(basis['original']), Path(basis['recovered'])
            x, y = inventory(a), inventory(b)
            require(x == basis['inventoryOriginal'] and y == basis['inventoryRecovered'], 'Synthetic export changed')
            require(x.keys() == y.keys() and len(x) == 28, 'Expected equal 28-file exports')
            exact = [n for n in x if n != 'manifest.json' and (a / n).read_bytes() == (b / n).read_bytes()]
            require(len(exact) == 27, 'Expected 27 byte-identical non-manifest files')
            old, new = [json.loads((p / 'manifest.json').read_bytes()) for p in (a, b)]
            differences = {k: {'original': old.get(k), 'recovered': new.get(k)}
                           for k in old.keys() | new.keys() if old.get(k) != new.get(k)}
            require(differences == basis['manifestDifferences'], 'Synthetic manifest changes differ')
            return {'original': str(a), 'recovered': str(b), 'filesEach': 28, 'identicalNonManifestFiles': 27,
                    'manifestDifferences': differences, 'originalUnchanged': True, 'recoveredUnchanged': True,
                    'retainedCorePhase': basis['finalCorePhase'], 'newReplayInvocations': 0}
        check('syntheticExports', synthetic_exports)

        def managed_v7():
            before, after = load('v7-reader-before-01.json'), load('v7-reader-native-01.json')
            require(after['status'] == 'passed' and before['root'] == after['root'], 'Wrong managed reader basis')
            require(identity(HERE / 'v7-reader-before-01.json')['sha256'] == after['beforeReceiptSha256'], 'Reader before basis differs')
            path = Path(after['root'])
            require(path == Path('/Users/v/Library/Application Support/research.reservoir.scope.tauri/sustained-v1/sustained-1792001665258-1'),
                    'Managed store access is limited to the explicitly authorized session')
            actual = inventory(path)
            require(actual == listed_inventory(after['files']) and len(actual) == 73, 'Managed v7 session changed after native reading')
            original = listed_inventory(before['files'])
            require(actual.keys() == original.keys()
                    and all(actual[n] == original[n] for n in actual if n != 'manifest.json'), 'Managed retained history changed')
            manifest = json.loads((path / 'manifest.json').read_bytes())
            expected = dict(before['manifest']); expected.update(generation='3', revision='425')
            require(manifest == expected and manifest['phase'] == 'paused', 'Unexpected managed manifest changes')
            require(manifest['step'] == manifest['durableStep'] == 361 and manifest['journalCount'] == 12,
                    'Managed historical progress changed')
            return {'root': str(path), 'files': 73, 'nonManifestFilesUnchanged': 72,
                    'manifestChangesFromBeforeReader': after['manifestChanges'],
                    'generation': manifest['generation'], 'revision': manifest['revision'], 'phase': manifest['phase'],
                    'step': manifest['step'], 'journals': manifest['journalCount'],
                    'scope': 'Only this explicitly addressed Tauri session was read; no app state or lifecycle was changed.'}
        check('managedV7Reader', managed_v7)

        def sources():
            before = load('source-before-build-01.json')
            built = load('package-build-01.json')
            qualified = load('qualification-before-ui-01.json')
            require(before['sourceBefore'] == built['sourceBefore'] == qualified['implementation']['files']
                    and built['sourceUnchanged'], 'Build/source bases differ')
            actual = source_inventory()
            a, b = [{r['path']: r for r in rows} for rows in (before['sourceBefore'], actual)]
            require(a.keys() == b.keys(), 'Source files added or removed after build')
            changes = [{'path': name, 'before': a[name], 'after': b[name]}
                       for name in sorted(a) if a[name] != b[name]]
            require(all(c['path'] in ALLOWED_DOCS for c in changes), 'Product source differs after qualification')
            require(source_inventory() == actual, 'Source changed during comparison')
            return {'fileCountBefore': len(a), 'fileCountAfter': len(b),
                    'sourceInventorySha256Before': inventory_digest(before['sourceBefore']),
                    'sourceInventorySha256After': inventory_digest(actual), 'changes': changes,
                    'allowedDocumentationPaths': sorted(ALLOWED_DOCS), 'productSourceUnchanged': True,
                    'sourceInventoryScope': qualified['implementation']['roots'],
                    'rootRoadmapScope': 'TAURI-ROADMAP.md is outside the build source inventory; its final identity is bound under documents.',
                    'repositoryScope': 'No git mutation/status claim. Prior 0.18/0.19 uncommitted work is not attributed to this closeout.'}
        check('postQualificationSource', sources)

        def executed_receipts():
            names = ['core-focused-01.json', 'rust-checks-01.json', 'rust-checks-02.json',
                     'frontend-focused-01.json', 'frontend-checks-01.json', 'frontend-checks-02.json',
                     'synthetic-harness-tests-01.json', 'package-build-01.json', 'archive-check-01.json',
                     'qualification-before-ui-01.json', 'historical-replay-01.json', 'native-execution-01.json',
                     'original-export-evidence-01.json', 'reanchored-tamper-01.json',
                     'tamper-execution-continuity-01.json', 'recovered-export-evidence-01.json',
                     'recovery-comparison-01.json', 'provider-stopped-01.json', 'v7-reader-before-01.json',
                     'v7-reader-native-01.json']
            rows = []
            for name in names:
                data = load(name)
                rows.append({'identity': identity(HERE / name),
                             'recordedStatus': data.get('status', data.get('passed', data.get('sourceUnchanged'))),
                             'interpretation': 'Existing execution evidence, not re-executed by closeout.'})
            provider = load('provider-stopped-01.json')
            require(provider['status'] == 'passed', 'Provider retention did not pass')
            require(inventory(Path(provider['retainedDirectory'])) == provider['files'], 'Retained stopped-provider copies changed')
            require(inventory(Path(provider['fixtureDirectory'])) == provider['files'], 'Original stopped-provider files changed')
            return {'receipts': rows, 'count': len(rows), 'stoppedProviderFilesExact': len(provider['files']),
                    'earlierFailedChecks': 'First failed Rust/frontend receipts remain retained; final receipts carry the qualified outcome.'}
        check('executedReceiptsAndFixtureRetention', executed_receipts)

        def documents():
            paths = [HERE / 'README.md', HERE / 'MACOS-UI.md'] + [ROOT / name for name in sorted(ALLOWED_DOCS)]
            rows = [identity(p) for p in paths]
            links = [local_links(p) for p in paths]
            require(not any(r['missing'] for r in links), 'One or more final local documentation links are missing')
            return {'files': rows, 'links': links, 'documents': len(paths),
                    'localLinkCount': sum(r['localLinkCount'] for r in links), 'allLocalFileTargetsExist': True}
        check('documents', documents)

        def unchanged():
            # Recheck every addressed file read by this helper, including basis receipts.
            rows = list(INPUTS.values())
            for row in rows:
                verify_row(row)
            package = load('archive-check-01.json')
            prior = load('prior-package-preserved-01.json')
            require(package_inventory(Path(package['app'])) == package['package'], 'Current package changed during closeout')
            require(package_inventory(Path(prior['preservedApp'])) == prior['package'], 'Prior app changed during closeout')
            source_check = report['checks'].get('postQualificationSource', {})
            require(source_check.get('status') == 'passed'
                    and inventory_digest(source_inventory()) == source_check['sourceInventorySha256After'],
                    'Source changed after closeout comparison')
            return {'addressedOrdinaryFilesRechecked': len(rows), 'identitiesSha256': digest(rows),
                    'allAddressedFilesUnchangedDuringCheck': True, 'sourceAndPackagesUnchangedDuringCheck': True}
        check('finalReadback', unchanged)

        report['status'] = 'passed' if not report['errors'] else 'failed'
        report['endedAtUtc'] = utc()
        report['limits'] = [
            'Byte and file-inventory preservation does not establish real-model prose quality or effect of prompt v8.',
            'Native UI behavior and cleanup come from the separately bound root observations; no new lifecycle observation was made.',
            'No rebuild, verification rerun, signing command, process probe, network, model or Being access occurred.',
            'The addressed managed v7 session was deliberately left paused; Follow latest is UI evidence, not inferred from file bytes.',
        ]
        stream.seek(0); stream.truncate(); json.dump(report, stream, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({'status': report['status'], 'output': str(output), 'errors': report['errors']}))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
