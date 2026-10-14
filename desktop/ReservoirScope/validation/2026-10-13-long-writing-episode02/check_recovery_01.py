#!/usr/bin/env python3
"""One read-only recovery/freeze audit for explicitly handed-off episode02 exports.

Runs only the pinned offline verifier. Does not inspect app state/processes,
contact a provider, rerun the main checker, or change any original receipt.
Full package resources/archive are intentionally not rehashed: the extra runtime
content-hash budget is restricted to the package executable and its pinned copy.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

ROOT = Path(__file__).absolute().parent
DESKTOP = ROOT.parents[1]
ORIGINAL = DESKTOP / 'target/qa/0.16-long-writing-episode02/exports/sustained-1791938932286-3-3-423'
RECOVERED = DESKTOP / 'target/qa/0.16-long-writing-episode02/exports/sustained-1791938932286-3-4-424'
EXPECTED_EXE = '73872388b56d2483054497aa8513e3659f79dfaf255699d6bca29041cafd258d'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def metadata(path):
    value = path.lstat()
    require(stat.S_ISREG(value.st_mode), f'Not an ordinary file: {path}')
    return {'device': value.st_dev, 'inode': value.st_ino, 'bytes': value.st_size,
            'modifiedNs': value.st_mtime_ns, 'changedNs': value.st_ctime_ns}


def read(path, limit=32 * 1024 * 1024):
    require(path.is_absolute(), 'Input path is not absolute')
    for p in path.parents:
        require(stat.S_ISDIR(p.lstat().st_mode), f'Linked/nonordinary ancestor: {p}')
    before = metadata(path)
    require(before['bytes'] <= limit, 'Input exceeds bound')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        opened = os.fstat(stream.fileno())
        require((opened.st_dev, opened.st_ino) == (before['device'], before['inode']), 'File changed at open')
        raw = stream.read(limit + 1)
    require(len(raw) <= limit and before == metadata(path), 'File changed during read')
    return raw


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(path):
    raw = read(path)
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def inventory(folder):
    out, total = {}, 0
    for path in sorted(folder.rglob('*')):
        require(not path.is_symlink(), 'Linked export member')
        if path.is_dir():
            continue
        item = identity(path)
        total += item['bytes']
        require(total <= 64 * 1024 * 1024 and len(out) < 1000, 'Export inspection bound exceeded')
        out[str(path.relative_to(folder))] = {key: item[key] for key in ('bytes', 'sha256')}
    return out


def main():
    output = ROOT / 'recovery-audit-01.json'
    note = ROOT / 'RECOVERY-RESULTS.md'
    require(not output.exists() and not note.exists(), 'Audit outputs must be new/exclusive')
    result = {'schema': 'reservoir-recovery-and-final-freeze-audit-v1', 'startedAtUtc': utc(),
              'script': identity(Path(__file__).absolute()), 'status': 'failed',
              'scope': 'Offline verification and explicit immutable-file comparisons only. Native quit/relaunch/Restore actions are parent-observed, not observed by this script.',
              'modelOrProviderCalls': False, 'uiOrProcessInspection': False,
              'mainCheckerRerun': False}
    try:
        original_receipt_path = ROOT / 'real-model-export-01/receipt.json'
        original_receipt_raw = read(original_receipt_path)
        original_receipt = json.loads(original_receipt_raw)
        require(original_receipt['status'] == 'passed' and original_receipt['originalUnchanged'], 'Original qualification is not passed')
        original_before, recovered_before = inventory(ORIGINAL), inventory(RECOVERED)
        require(original_before == original_receipt['inventoryBefore'], 'Original differs from initial qualified export')

        provenance_path = ROOT / 'package-provenance-01.json'
        provenance_raw = read(provenance_path)
        provenance = json.loads(provenance_raw)
        pinned_expected = provenance['pinnedVerifier']
        package_expected = next(row for row in provenance['appFiles']
                                if row['path'].endswith('/Contents/MacOS/reservoir-scope-desktop'))
        require(pinned_expected['bytes'] + package_expected['bytes'] < 40 * 1000 * 1000,
                'Executable hashing exceeds parent budget')
        runtime = []
        for expected in (package_expected, pinned_expected):
            path = Path(expected['path'])
            before_stat = metadata(path)
            actual = identity(path)
            runtime.append({'expected': expected, 'actual': actual, 'matches': expected == actual,
                            'metadataBefore': before_stat})
        result['executableAudit'] = {
            'contentBytesHashed': sum(row['actual']['bytes'] for row in runtime),
            'files': runtime,
            'fullPackageResourceContentRehashed': False,
            'archiveRehashed': False,
            'omissionReason': 'Prior package resource contents total248,015,048bytes and archive96,675,714bytes; outside the requested cheap<40MB runtime hashing scope.'}
        require(all(row['matches'] and row['actual']['sha256'] == EXPECTED_EXE for row in runtime), 'Executable identity differs')
        pinned = Path(pinned_expected['path'])
        command = [str(pinned), '--verify-sustained', str(RECOVERED)]
        start = utc()
        run = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
        result['recoveredReplay'] = {'command': command, 'startedAtUtc': start, 'endedAtUtc': utc(),
                                     'returncode': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr}
        require(run.returncode == 0, 'Recovered production replay failed')
        replay = json.loads(run.stdout)
        require(replay['status'] == 'passed' and replay['modelsContacted'] is False, 'Recovered replay did not report model-free success')
        for row in runtime:
            row['metadataAfter'] = metadata(Path(row['actual']['path']))
            row['metadataUnchangedThroughReplay'] = row['metadataBefore'] == row['metadataAfter']
        require(all(row['metadataUnchangedThroughReplay'] for row in runtime), 'Executable metadata changed through replay')

        old_manifest = json.loads(read(ORIGINAL / 'manifest.json'))
        new_manifest = json.loads(read(RECOVERED / 'manifest.json'))
        changed = [{'path': name, 'original': original_before.get(name), 'recovered': recovered_before.get(name)}
                   for name in sorted(set(original_before) | set(recovered_before))
                   if original_before.get(name) != recovered_before.get(name)]
        manifest_diff = [{'field': key, 'original': old_manifest.get(key), 'recovered': new_manifest.get(key)}
                         for key in sorted(set(old_manifest) | set(new_manifest))
                         if old_manifest.get(key) != new_manifest.get(key)]
        expected_diff = [{'field': 'generation', 'original': '3', 'recovered': '4'},
                         {'field': 'phase', 'original': 'budgetReached', 'recovered': 'paused'},
                         {'field': 'revision', 'original': '423', 'recovered': '424'}]
        result['exportComparison'] = {'original': str(ORIGINAL), 'recovered': str(RECOVERED),
                                      'originalInventory': original_before, 'recoveredInventory': recovered_before,
                                      'originalFileCount': len(original_before), 'recoveredFileCount': len(recovered_before),
                                      'changedFiles': changed, 'manifestChanges': manifest_diff,
                                      'expectedManifestChanges': expected_diff,
                                      'byteIdenticalMembers': sum(original_before[k] == recovered_before.get(k) for k in original_before),
                                      'originalStillMatchesInitialQualification': True}
        require(len(original_before) == len(recovered_before) == 73
                and [row['path'] for row in changed] == ['manifest.json']
                and manifest_diff == expected_diff, 'Unexpected recovered file or manifest difference')

        freeze_path = ROOT / 'evaluation-freeze-01.json'
        freeze_raw = read(freeze_path)
        freeze = json.loads(freeze_raw)
        freeze_rows = []
        for expected in freeze['files']:
            actual = identity(Path(expected['path']))
            freeze_rows.append({'expected': expected, 'actual': actual, 'matches': expected == actual})
        result['freezeAudit'] = {'freeze': identity(freeze_path), 'expectedCount': 22,
                                'actualCount': len(freeze_rows), 'files': freeze_rows}
        require(len(freeze_rows) == 22 and len({r['expected']['path'] for r in freeze_rows}) == 22
                and all(row['matches'] for row in freeze_rows), 'Frozen input mismatch')
        require(read(freeze_path) == freeze_raw and read(provenance_path) == provenance_raw
                and read(original_receipt_path) == original_receipt_raw, 'Original receipt changed during audit')
        require(inventory(ORIGINAL) == original_before and inventory(RECOVERED) == recovered_before,
                'Export bytes changed during audit')
        result['originalIntegrityReceipt'] = identity(original_receipt_path)
        result['packageProvenance'] = identity(provenance_path)
        result['bothExportsAndOriginalReceiptsUnchanged'] = True
        result['status'] = 'passed'
    except Exception as error:
        result['error'] = {'type': type(error).__name__, 'message': str(error)}
    result['endedAtUtc'] = utc()
    with output.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    if result['status'] == 'passed':
        text = '''# Offline recovery and final identity audit

The separately exported recovered session passed the same pinned0.16.0 r2
production verifier. The [audit receipt](recovery-audit-01.json) and
[reproducible script](check_recovery_01.py) retain the exact command, result,
every exported-file identity, manifest differences, frozen-file hashes and
executable hashes. The original full checker was not rerun.

Both exports contain73 files. Exactly72 are byte-identical: all59 segments,
all12 journal objects and the exact final checkpoint. Only `manifest.json`
changed, precisely:

| Field | Original | Recovered |
| --- | --- | --- |
| Generation | 3 | 4 |
| Revision | 423 | 424 |
| Wrapper phase | budgetReached | paused |

Configuration, numerical step361, twelve journals, elapsed time, diagnostics,
all prompt/response/provider-count evidence, full-text memory and application
history are unchanged. The core checkpoint remains Ready. No new numerical
step, journal, application or provider attempt was added. Both exported inputs
and the original qualification receipt remained unchanged during this audit.
The original [mechanical result](MECHANICS-RESULTS.md) and exact
[twelve-text rendering](JOURNALS.md) therefore apply to the identical retained
history; no new prose result is manufactured by restoring.

All22 files in the episode's prospective freeze still match their recorded byte
lengths and SHA-256 hashes. The packaged executable and its original pinned copy
both match
`73872388b56d2483054497aa8513e3659f79dfaf255699d6bca29041cafd258d`.
Their combined content-hash cost was33,967,488 bytes. File identity metadata
remained unchanged through the verifier call. The248,015,048-byte package
resource contents and96,675,714-byte archive were not rehashed; their earlier
package proof is retained, not presented as a fresh full-content check here.

The parent separately observed clean Cmd-Q, idle relaunch and explicit paused
Restore with Resume disabled. This script did not observe those UI actions or
inspect processes, and makes no crash/power-loss durability, new model,
writing-quality or full-context-processing claim.
'''
    else:
        text = '# Recovery audit did not pass\n\nThe first outcome is preserved in [recovery-audit-01.json](recovery-audit-01.json). No success is inferred; original inputs and earlier receipts have not been rewritten.\n'
    with note.open('x', encoding='utf-8') as handle:
        handle.write(text)
    print(json.dumps({'status': result['status'], 'receipt': str(output),
                      'receiptSha256': sha(read(output)), 'results': str(note),
                      'resultsSha256': sha(read(note)), 'error': result.get('error')}))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
