#!/usr/bin/env python3
"""Prospective file-based 0.24 closeout. Execute only after lead freezes docs.

No tests/build/UI/model/service calls. Optional --check-owned-pid authorizes one
exact ps query for the PID in this episode's launch/close receipts. All prior
artifacts and any failed review receipt remain untouched; use a new attempt.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1]
ROOT = DESKTOP.parents[1]
sys.path.insert(0, str(DESKTOP / 'scripts'))
from qualification_receipt import file_entry, inventory_digest, package_inventory, source_inventory
import checks_common
VERSION = '0.24.0'
ALLOWED_DOCS = {
    'desktop/ReservoirScope/README.md', 'desktop/ReservoirScope/STATUS.md',
    'desktop/ReservoirScope/RESEARCH-LANGUAGE.md', 'shared/reservoir-scope/PARITY.md',
}


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def identity(path):
    path = Path(path)
    return file_entry(path, str(path))


def local_links(documents):
    rows = []
    external = 0
    for doc in documents:
        text = re.sub(r'(?ms)^```.*?^```[^\n]*', '', doc.read_text())
        targets = re.findall(r'!?\[[^\]]*\]\(<?([^\s)>]+)>?(?:\s+"[^"]*")?\)', text)
        targets += re.findall(r'(?m)^\s*\[[^\]]+\]:\s*<?([^\s>]+)>?', text)
        for target in targets:
            link = urlsplit(target)
            if link.scheme or target.startswith('//'):
                external += 1
                continue
            path = (doc.parent / unquote(link.path)).resolve() if link.path else doc.resolve()
            inside = path.is_relative_to(ROOT)
            rows.append({'source': str(doc.relative_to(ROOT)), 'target': target,
                         'path': str(path), 'status': ('passed' if path.exists() else 'failed') if inside else 'outside-worktree-not-inspected'})
    return {'documents': [identity(p) for p in documents], 'links': rows,
            'checkedLocalCount': sum(r['status'] in ('passed', 'failed') for r in rows),
            'externalReferencesNotFetched': external,
            'scope': 'Local Markdown link target existence only; no network fetch or heading-fragment validation.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', default='01')
    parser.add_argument('--build-attempt', default='01')
    parser.add_argument('--frontend-attempt', default='01')
    parser.add_argument('--rust-attempt', default='01')
    parser.add_argument('--check-owned-pid', action='store_true')
    args = parser.parse_args()
    for number in (args.attempt, args.build_attempt, args.frontend_attempt, args.rust_attempt):
        assert re.fullmatch(r'[0-9]{2}', number), 'Use two-digit attempt IDs'
    report = {'schema': 'reservoir-compact-reading-postbuild-review-v1', 'startedAtUtc': utc(),
              'status': 'running', 'errors': [], 'helper': identity(Path(__file__)),
              'scope': 'File/hash/link closeout only; optional one exact owned-PID ps observation. No test/build/UI/model/service execution.'}
    def need(condition, message):
        if not condition:
            report['errors'].append(message)
    def load(name):
        return json.loads((HERE / name).read_bytes())
    output = HERE / f'postbuild-review-{args.attempt}.json'
    with output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.flush()
        try:
            receipts = [f'frontend-checks-{args.frontend_attempt}.json', f'package-build-{args.build_attempt}.json',
                        f'archive-check-{args.build_attempt}.json', f'qualification-before-ui-{args.build_attempt}.json',
                        'prior-package-preserved-01.json', 'ui-launch-01.json', 'ui-close-01.json']
            documents = [DESKTOP/'RESEARCH-LANGUAGE.md', HERE/'README.md', HERE/'MACOS-UI.md',
                         DESKTOP/'STATUS.md', DESKTOP/'README.md', ROOT/'shared/reservoir-scope/PARITY.md', ROOT/'TAURI-ROADMAP.md']
            reviewed = [identity(p) for p in [*(HERE/n for n in receipts), *documents]]
            frontend = load(receipts[0])
            current_front = checks_common.inputs('frontend')
            need(frontend['status'] == 'passed' and not frontend['sourceChangesDuringChecks'], 'Frontend qualification failed or changed during checks')
            need(current_front == frontend['sourceInputsSha256'], 'Current frontend membership/hashes differ')
            for name, digest in frontend['helperInputsSha256'].items():
                need(identity(HERE/name)['sha256'] == digest, 'Frontend helper changed: '+name)
            for command in frontend['commands']:
                need(identity(HERE/command['log'])['sha256'] == command['sha256'], 'Frontend log changed: '+command['log'])
            vite = (DESKTOP/'vite.config.ts').read_text()
            excluded = bool(re.search(r'''test\s*:\s*\{\s*exclude\s*:\s*\[\s*\.\.\.configDefaults\.exclude\s*,\s*['"]target/\*\*['"]\s*\]''', vite))
            need(excluded, 'Vite test target/** exclusion missing or structurally changed')
            report['frontend'] = {'inputCount': len(current_front), 'counts': frontend['counts'],
                                  'currentMatchesQualified': current_front == frontend['sourceInputsSha256'],
                                  'vite': identity(DESKTOP/'vite.config.ts'), 'testTargetExcluded': excluded,
                                  'reason': 'The ignored target tree contains copied historical source/tests; it is excluded from current Vitest discovery, while configDefaults.exclude is retained.'}
            rust_path=HERE/f'rust-checks-{args.rust_attempt}.json'
            rust_qualification=checks_common.validate_rust_receipt(rust_path)
            current_rust=checks_common.inputs('rust')
            build=load(receipts[1])
            need(build['sourceUnchanged'] and build['sourceBefore']==build['sourceAfter'], 'Source changed during build')
            need(current_rust==build['rustQualification']['sourceInputsSha256']==build['rustQualificationRechecked']['sourceInputsSha256'], 'Current Rust inputs differ from build qualification')
            report['rustQualification']={'receipt':identity(rust_path),'inputCount':len(current_rust),
                                         'checks':rust_qualification['checks'],'inheritedResults':False}
            archive = load(receipts[2])
            app = Path(archive['app'])
            package = package_inventory(app)
            need(package == archive['package'] and len(package['files']) == 46, 'Current app differs from qualified 46-file package')
            need(package['version'] == package['build'] == VERSION, 'Current package version/build incorrect')
            current_archive, pin = identity(archive['archive']), identity(archive['pinnedExecutable'])
            need(current_archive['sha256'] == archive['archiveSha256'], 'Current archive changed')
            need(pin['sha256'] == package['binary']['sha256'] == archive['executableSha256'], 'Current pinned/package executable changed')
            qualified = load(receipts[3])
            need(qualified['package'] == package and qualified['codesign']['status'] == 'verified', 'Pre-UI signing/package evidence differs')
            report['package'] = {'fileCount': len(package['files']), 'app': str(app), 'inventorySha256': package['inventorySha256'],
                                 'archive': current_archive, 'pin': pin, 'executableSha256': package['binary']['sha256'],
                                 'signing': 'Prior local ad-hoc signature verification with unchanged package bytes; not rerun and no notarization claim.'}
            preserved = load(receipts[4])
            need(preserved['passed'] and preserved['copiesByteExact'] and preserved['originalsUnchanged'], 'Prior preservation failed')
            old_app = package_inventory(Path(preserved['preservedApp']))
            need(old_app == preserved['package'], 'Preserved 0.23.0 full app changed')
            old_files = []
            for key in ('basis', 'archiveBefore', 'pinBefore', 'preservedArchive', 'preservedPin'):
                entry = preserved[key]
                actual = file_entry(Path(entry['path']), entry['path'], include_mode=True)
                need(actual == entry, 'Prior preservation identity changed: '+key)
                old_files.append({'role': key, **actual})
            snapshot_error_count = len(report['errors'])
            source_rows = preserved['sourceInventory'] + [preserved['roadmap']]
            snapshot = Path(preserved['sourceSnapshot'])
            need(len(source_rows) == preserved['sourceFileCount'] == 346, 'Prior source snapshot count differs')
            for entry in source_rows:
                need(file_entry(snapshot/entry['path'], entry['path']) == entry, 'Prior source snapshot changed: '+entry['path'])
            actual_names = sorted(p.relative_to(snapshot).as_posix() for p in snapshot.rglob('*') if p.is_file() or p.is_symlink())
            need(actual_names == sorted(x['path'] for x in source_rows), 'Prior source snapshot membership changed')
            report['priorPreservation'] = {'app': preserved['preservedApp'], 'appFileCount': len(old_app['files']),
                                          'sourceSnapshot': str(snapshot), 'sourceFileCount': len(source_rows),
                                          'sourceBytes': sum(x['bytes'] for x in source_rows), 'sourceCopiesExact': len(report['errors']) == snapshot_error_count,
                                          'files': old_files, 'scope': 'Old original archive/pin and independently copied app/archive/pin/source remain unchanged; shared app build path intentionally now holds0.24.0.'}
            current = source_inventory()
            before = {x['path']: x for x in build['sourceAfter']}
            after = {x['path']: x for x in current}
            changes = [{'path': p, 'build': before.get(p), 'current': after.get(p)} for p in sorted(before.keys() | after.keys()) if before.get(p) != after.get(p)]
            need(all(x['path'] in ALLOWED_DOCS and x['build'] and x['current'] for x in changes), 'Unexpected postbuild product/config/input change')
            report['sourceInventory'] = {'buildCount': len(before), 'currentCount': len(after), 'changes': changes,
                                         'allowedDocumentationPaths': sorted(ALLOWED_DOCS), 'currentSha256': inventory_digest(current),
                                         'unchangedCount': sum(before.get(p) == after.get(p) for p in before.keys() & after.keys()),
                                         'rootRoadmapSeparate': identity(ROOT/'TAURI-ROADMAP.md')}
            links = local_links(documents)
            for link in links['links']:
                need(link['status'] != 'failed', 'Broken local Markdown target: '+link['source']+' -> '+link['target'])
            report['markdownLinks'] = links
            close, launch = load('ui-close-01.json'), load('ui-launch-01.json')
            need(close['ownedPid'] == launch['pid'] and close['ownedProcessAbsent'], 'Owned close/launch receipt mismatch')
            report['ownedClose'] = {'launch': identity(HERE/'ui-launch-01.json'), 'close': identity(HERE/'ui-close-01.json'),
                                    'pid': launch['pid'], 'freshProcessQuery': False}
            if args.check_owned_pid:
                pid = launch['pid']
                assert type(pid) is int and 0 < pid < 2**31
                command = ['ps', '-p', str(pid), '-o', 'pid=,comm=']
                result = subprocess.run(command, capture_output=True, text=True, timeout=10)
                absent = result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip()
                need(absent, 'Exact owned PID absence not confirmed')
                report['ownedClose'].update(freshProcessQuery=True, command=command, exitCode=result.returncode,
                                            stdout=result.stdout, stderr=result.stderr, absenceConfirmed=absent, checkedAtUtc=utc())
            for entry in reviewed:
                need(identity(entry['path']) == entry, 'Reviewed evidence/doc changed during review: '+entry['path'])
            need(source_inventory() == current, 'Product source changed during review')
            need(package_inventory(app) == package, 'Package changed during review')
            report['reviewedInputs'] = reviewed
            report['limits'] = ['Automated identity/link existence check, not semantic Markdown review or native UI re-execution.',
                                'Full current Rust/check results are source-bound here; this review does not rerun them.',
                                'No new performance, model-writing, endurance, accessibility, distribution or other-platform qualification.']
        except Exception as error:
            report['errors'].append(f'{type(error).__name__}: {error}')
        report['status'] = 'passed' if not report['errors'] else 'failed'
        report['endedAtUtc'] = utc()
        stream.seek(0)
        json.dump(report, stream, indent=2)
        stream.write('\n')
        stream.truncate()
        stream.flush()
    print(json.dumps({'status': report['status'], 'receipt': str(output), 'sha256': identity(output)['sha256'], 'errors': report['errors']}))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
