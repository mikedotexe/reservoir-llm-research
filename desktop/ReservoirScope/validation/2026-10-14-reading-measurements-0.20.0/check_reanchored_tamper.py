#!/usr/bin/env python3
"""Offline 0.20 negative copies; never mutate the supplied positive export.

Journal prompt-only corruption is reanchored through journal byte hashes,
segment predecessor hashes and the manifest. Core checkpoint and segment payload
bytes remain untouched: this does NOT attempt Python reconstruction of canonical
Rust float-state hashes. Separate core tests cover typed checkpoint corruption.
Execute only after the lead supplies the qualified pin and positive v8 export.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('fixture_check', HERE / 'check_fixture_export.py')
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)
CASES = ('held-clock', 'recorded-return', 'authority', 'removed', 'relocated', 'manifest-version', 'measurement-caveat-removed')
CHAIN_DIAGNOSTIC = 'Segment chain does not begin at exact genesis or previous committed continuation'
JOURNAL_DIAGNOSTIC = 'Immutable journal differs from its replayed response/save evidence'


def replace_json_string(raw: bytes, key: str, expected: str, value: str) -> bytes:
    pattern = re.compile(rb'("' + re.escape(key.encode()) + rb'"\s*:\s*)("(?:[^"\\]|\\.)*")')
    matches = list(pattern.finditer(raw))
    C.require(len(matches) == 1 and C.decode(matches[0][2]) == expected,
              'Expected one exact JSON string field: ' + key)
    m = matches[0]
    return raw[:m.start(2)] + json.dumps(value, ensure_ascii=False).encode() + raw[m.end(2):]


def raw_json_field(raw: bytes, key: str) -> bytes:
    """Read one field's exact UTF-8 span without reserializing floats or integers."""
    text = raw.decode('utf-8')
    pattern = re.compile(r'"' + re.escape(key) + r'"\s*:\s*')
    matches = list(pattern.finditer(text))
    C.require(len(matches) == 1, 'Expected one exact JSON field: ' + key)
    start = matches[0].end()
    _, end = json.JSONDecoder().raw_decode(text, start)
    return text[start:end].encode('utf-8')


def replace_hash(raw: bytes, old: str, new: str) -> bytes:
    old_token = ('"' + old + '"').encode()
    C.require(raw.count(old_token) == 1, 'Expected one byte-anchor occurrence')
    return raw.replace(old_token, ('"' + new + '"').encode(), 1)


def check_anchors(bundle: Path) -> None:
    C.require(bundle.is_dir() and not bundle.is_symlink(), 'Bundle must be an ordinary directory')
    manifest = C.decode(C.read(bundle / 'manifest.json'))
    previous = None
    paths = sorted((bundle / 'segments').glob('*.json'))
    C.require(len(paths) == manifest['segmentCount'] and paths, 'Segment count differs or is empty')
    C.require([p.name for p in paths] == [f'segment-{n:08}.json' for n in range(1, len(paths) + 1)],
              'Segment filenames must be contiguous')
    for sequence, path in enumerate(paths, 1):
        raw = C.read(path)
        link = C.decode(raw)
        C.require(link['sequence'] == sequence and link['previousSha256'] == previous,
                  'Envelope predecessor differs')
        for entry, digest in link['journalSha256s'].items():
            C.require(re.fullmatch(r'[A-Za-z0-9_-]+', entry) is not None, 'Unsafe journal identity')
            C.require(C.sha(C.read(bundle / 'journals' / (entry + '.json'))) == digest,
                      'Journal byte anchor differs')
        previous = C.sha(raw)
    C.require(previous == manifest['lastSegmentSha256'], 'Manifest segment anchor differs')
    checkpoint = bundle / 'checkpoints' / (manifest['checkpointSha256'] + '.json')
    C.require(C.sha(C.read(checkpoint)) == manifest['checkpointSha256'], 'Checkpoint byte anchor differs')


def mutate_copy(original: Path, output: Path, case: str) -> dict:
    C.require(case in CASES and not output.exists(), 'Known case and exclusive copy required')
    C.inventory(original)  # Reject links/nonordinary members before copying.
    check_anchors(original)
    shutil.copytree(original, output)
    manifest_path = output / 'manifest.json'
    raw_manifest = C.read(manifest_path)
    manifest = C.decode(raw_manifest)
    C.require(manifest['config']['promptVersion'] == C.PROMPT_VERSION, 'Expected v8 positive bundle')
    if case == 'manifest-version':
        manifest_path.write_bytes(replace_json_string(raw_manifest, 'promptVersion', C.PROMPT_VERSION,
                                                      'reservoir-journal-v7'))
        check_anchors(output)
        return {'mutation': 'Manifest config only relabeled v7; byte anchors retained.',
                'allByteAnchorsConsistent': True,
                'expectedDiagnostic': CHAIN_DIAGNOSTIC}
    candidates = []
    for path in sorted((output / 'journals').glob('*.json')):
        obj = C.decode(C.read(path))
        candidates.append((obj['pending']['entry']['attemptId'], path, obj))
    C.require(len(candidates) >= 2, 'Need first and later saved journals')
    _, journal, obj = sorted(candidates)[1 if case == 'recorded-return' else 0]
    pending = obj['pending']
    C.check_compact_prompt(pending)
    original_prompt = pending['prompt']
    boundary = C.writing_boundary(pending['observation'], pending['memory'])
    C.require(original_prompt.count(boundary) == 1, 'Unique active writing boundary required')
    if case == 'held-clock':
        text = f"held at observation step {pending['observation']['step']};"
        changed = boundary.replace(text, f"held at observation step {pending['observation']['step'] + 1};")
    elif case == 'recorded-return':
        step = pending['memory']['appliedStep']
        changed = boundary.replace(f'input at step {step}.', f'input at step {step + 1}.')
    elif case == 'authority':
        changed = boundary.replace('Describing a control change does not execute it;',
                                   'Describing a control change executes it;')
    elif case == 'measurement-caveat-removed':
        changed = boundary  # Preserve the late boundary; mutate only the v8 caveat.
    else:
        changed = ''
    prompt = original_prompt.replace(boundary, changed, 1)
    if case == 'measurement-caveat-removed':
        C.require(pending['memory'] is None and original_prompt.count(C.MEASUREMENT_CAVEAT) == 1,
                  'Use the first prompt with one active caveat and no historical prose')
        prompt = prompt.replace(C.MEASUREMENT_CAVEAT, '', 1)
    if case == 'relocated':
        prompt = prompt.replace('\n\nPREVIOUS JOURNAL\n', '\n\n' + boundary + '\n\nPREVIOUS JOURNAL\n', 1)
    C.require(prompt != original_prompt, 'Mutation must change exact prompt bytes')
    old_journal_raw = C.read(journal)
    journal.write_bytes(replace_json_string(old_journal_raw, 'prompt', original_prompt, prompt))
    old_journal_sha, new_journal_sha = C.sha(old_journal_raw), C.sha(C.read(journal))
    entry_id = pending['entry']['id']
    previous = None
    touched = 0
    for path in sorted((output / 'segments').glob('*.json')):
        raw = C.read(path)
        link = C.decode(raw)
        if link['previousSha256'] != previous:
            C.require(link['previousSha256'] is not None and previous is not None, 'Genesis must remain intact')
            raw = replace_hash(raw, link['previousSha256'], previous)
        if entry_id in link['journalSha256s']:
            C.require(link['journalSha256s'][entry_id] == old_journal_sha, 'Unexpected old journal anchor')
            raw = replace_hash(raw, old_journal_sha, new_journal_sha)
            touched += 1
        C.require(raw_json_field(C.read(path), 'segment') == raw_json_field(raw, 'segment'),
                  'Core segment payload bytes changed')
        path.write_bytes(raw)
        previous = C.sha(raw)
    C.require(touched == 1, 'Journal must have exactly one committed anchor')
    manifest_path.write_bytes(replace_hash(raw_manifest, manifest['lastSegmentSha256'], previous))
    for path in (original / 'checkpoints').glob('*.json'):
        C.require(C.read(path) == C.read(output / 'checkpoints' / path.name), 'Core checkpoint bytes changed')
    check_anchors(output)
    return {'journal': journal.name, 'entryId': entry_id,
            'originalPromptSha256': C.sha(original_prompt.encode()), 'mutatedPromptSha256': C.sha(prompt.encode()),
            'journalByteAnchorsRecomputed': touched, 'allByteAnchorsConsistent': True,
            'coreSegmentPayloadsAndCheckpointBytesUnchanged': True,
            'expectedDiagnostic': JOURNAL_DIAGNOSTIC}


def run(cli: Path, bundle: Path, output: Path, name: str, expected_sha: str) -> dict:
    before = C.identity(cli)
    C.require(before['sha256'] == expected_sha, 'Executable differs before replay')
    command = [str(cli), '--verify-sustained', str(bundle)]
    result = subprocess.run(command, capture_output=True, timeout=120)
    for suffix, raw in [('stdout.json', result.stdout), ('stderr.txt', result.stderr)]:
        with (output / (name + '.' + suffix)).open('xb') as stream:
            stream.write(raw)
    after = C.identity(cli)
    C.require(before == after, 'Executable changed during replay')
    return {'command': command, 'executableBefore': before, 'executableAfter': after,
            'exitCode': result.returncode,
            'stdout': result.stdout.decode('utf-8', errors='replace'),
            'stderr': result.stderr.decode('utf-8', errors='replace')}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('bundle', 'cli', 'output-directory'):
        parser.add_argument('--' + flag, type=Path, required=True)
    parser.add_argument('--expected-cli-sha256', required=True)
    args = parser.parse_args()
    C.require(not args.bundle.is_symlink() and not args.cli.is_symlink(), 'Linked input root or CLI')
    bundle, cli, output = (p.resolve() for p in (args.bundle, args.cli, args.output_directory))
    qa = (HERE.parents[1] / 'target/qa').resolve()
    C.require(output != qa and output.is_relative_to(qa) and not output.is_relative_to(bundle) and not bundle.is_relative_to(output),
              'New scratch directory must be separate and inside this worktree owned QA')
    C.require(not output.exists(), 'Output must be exclusive')
    before, binary = C.inventory(bundle), C.identity(cli)
    C.require(binary['sha256'] == args.expected_cli_sha256, 'Pinned executable differs')
    output.mkdir(parents=True)
    report = {'startedAtUtc': C.utc(), 'status': 'running', 'bundle': str(bundle),
              'executable': binary, 'script': C.identity(Path(__file__).resolve()),
              'checker': C.identity(HERE / 'check_fixture_export.py'), 'originalInventoryBefore': before,
              'modelsContacted': False,
              'scope': 'Seven offline synthetic negative copies; no model, service, restore or UI actions. Byte anchors repaired; canonical Rust state payloads never reconstructed by Python.', 'cases': []}
    try:
        positive = run(cli, bundle, output, 'positive', args.expected_cli_sha256)
        report['positive'] = positive
        C.require(positive['exitCode'] == 0 and C.decode(positive['stdout'].encode())['status'] == 'passed',
                  'Qualified positive must replay before negative tests')
        for case in CASES:
            target = output / case
            details = mutate_copy(bundle, target, case)
            inventory = C.inventory(target)
            result = run(cli, target, output, case, args.expected_cli_sha256)
            report['cases'].append({'name': case, **details, **result, 'inventory': inventory})
            C.require(result['exitCode'] != 0, 'Tampered copy was accepted: ' + case)
            diagnostic = result['stdout'] + result['stderr']
            C.require(details['expectedDiagnostic'] in diagnostic, 'Unexpected rejection cause: ' + case)
            C.require(inventory == C.inventory(target), 'Verifier changed negative copy')
        report['status'] = 'passed'
    except Exception as error:
        report.update(status='failed', error=f'{type(error).__name__}: {error}')
    finally:
        if report.get('positive', {}).get('exitCode') == 0:
            try:
                after = run(cli, bundle, output, 'positive-after', args.expected_cli_sha256)
                report['positiveAfter'] = after
                C.require(after['exitCode'] == 0 and C.decode(after['stdout'].encode())['status'] == 'passed',
                          'Positive failed after negative tests')
            except Exception as error:
                report.update(status='failed', finalPositiveError=f'{type(error).__name__}: {error}')
        report.update(endedAtUtc=C.utc(), originalUnchanged=C.inventory(bundle) == before,
                      executableUnchanged=C.identity(cli) == binary)
        if not report['originalUnchanged'] or not report['executableUnchanged']:
            report['status'] = 'failed'
        with (output / 'receipt.json').open('x') as stream:
            json.dump(report, stream, indent=2)
            stream.write('\n')
    print(json.dumps({'status': report['status'], 'receipt': str(output / 'receipt.json')}))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
