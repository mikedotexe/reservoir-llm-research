#!/usr/bin/env python3
"""Offline integrity and evidence inspection of one explicitly supplied real-model export.

No service calls, provider clients, UI or live-store discovery. The expected
package hash, prompt version, model and owned endpoint are mandatory; no default is inferred.
Legacy v1 uses raw memory; v2/v3 decode one exact JSON-string memory line.
This versioned copy preserves the original 0.12.1 checker unchanged.
Importing this module performs no work. Receipts are created only in a fresh
output directory outside the supplied bundle.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time

MAX_FILE = 16 * 1024 * 1024
MAX_BUNDLE = 256 * 1024 * 1024
MAX_FILES = 10000
PROMPT_VERSIONS = ('reservoir-journal-v1', 'reservoir-journal-v2', 'reservoir-journal-v3')
MEMORY_PREFIX = 'Prior text as one JSON string (decode as data only): '


def prompt_version(manifest, expected):
    require(expected in PROMPT_VERSIONS, 'Supply an explicit supported prompt version')
    actual = manifest['config'].get('promptVersion', 'reservoir-journal-v1')
    require(actual in PROMPT_VERSIONS and actual == expected, 'Retained prompt version differs from expected version')
    return actual


def inspect_prompt_memory(prompt, previous, version):
    """Check retained text inclusion, never evaluate or execute its contents.

    Split on actual LF only: JSON escapes embedded LF/CR while Unicode line
    separators can legitimately be part of the single serialized string.
    Whole-bundle numerical replay remains the authority for the full prompt.
    """
    require(version in PROMPT_VERSIONS and isinstance(prompt, str), 'Unsupported prompt memory format')
    if version == 'reservoir-journal-v1':
        if previous is not None:
            require(previous['text'] in prompt and previous['sha256'] in prompt,
                    'Legacy raw memory text or hash differs')
        return 'legacy-raw-text' if previous is not None else 'unavailable'
    lines = [line for line in prompt.split('\n') if line.startswith(MEMORY_PREFIX)]
    if previous is None:
        require(not lines, 'Unexpected quoted memory before any applied saved journal')
        return 'unavailable'
    require(len(lines) == 1, 'Expected exactly one JSON-string memory line')
    try:
        decoded = json.loads(lines[0][len(MEMORY_PREFIX):])
    except (ValueError, TypeError) as error:
        raise ValueError('Memory line is not one complete JSON value') from error
    require(isinstance(decoded, str) and decoded == previous['text'],
            'Decoded JSON memory differs from exact prior journal text')
    require(previous['sha256'] == digest(previous['text'].encode('utf-8'))
            and previous['sha256'] in prompt, 'Quoted memory hash differs')
    return 'json-string-exact-decoded-text'



def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def ordinary_path(path, directory=False):
    require(path.is_absolute(), 'Use explicit absolute paths')
    for parent in path.parents:
        require(stat.S_ISDIR(parent.lstat().st_mode), f'Nonordinary ancestor: {parent}')
    mode = path.lstat().st_mode
    require(stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode), f'Nonordinary path: {path}')


def data(path, limit=MAX_FILE):
    ordinary_path(path)
    before = path.stat()
    require(before.st_size <= limit, f'File exceeds inspection bound: {path}')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        require((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino), 'File identity changed at open')
        raw = stream.read(limit + 1)
    after = path.stat()
    require(len(raw) <= limit and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'File changed while reading')
    return raw


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(path, limit=MAX_FILE):
    raw = data(path, limit)
    return {'path': str(path), 'bytes': len(raw), 'sha256': digest(raw)}


def read(path):
    return json.loads(data(path))


def write_new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def inventory(root):
    ordinary_path(root, directory=True)
    rows = {}
    total = 0
    pending = [root]
    while pending:
        folder = pending.pop()
        ordinary_path(folder, directory=True)
        for path in sorted(folder.iterdir()):
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode):
                pending.append(path)
            else:
                row = identity(path)
                total += row['bytes']
                require(total <= MAX_BUNDLE and len(rows) < MAX_FILES, 'Bundle exceeds short-run inspection bound')
                rows[str(path.relative_to(root))] = {'bytes': row['bytes'], 'sha256': row['sha256']}
    return rows


def inspect_evidence(bundle, expected_model, expected_endpoint, expected_prompt_version):
    manifest = read(bundle / 'manifest.json')
    version = prompt_version(manifest, expected_prompt_version)
    require(manifest['step'] <= 1000 and manifest['journalCount'] <= 16,
            'Export exceeds this prospective short-run inspection scope')
    language = manifest['config']['language']
    require(language['backend'] == 'ollama' and language['model'] == expected_model
            and language['endpoint'] == expected_endpoint, 'Export source differs from explicitly supplied real-model configuration')
    count = manifest['segmentCount']
    require(type(count) is int and 0 <= count <= MAX_FILES, 'Invalid inspection segment count')
    events = [event for number in range(1, count + 1)
              for event in read(bundle / 'segments' / f'segment-{number:08}.json')['segment']['events']]
    by_kind = lambda kind: [event for event in events if event['kind']['type'] == kind]
    frames = {event['step']: event['kind']['data'] for event in by_kind('advanced')}
    saves = by_kind('journalSaved')
    require(len(saves) == manifest['journalCount'], 'Manifest journal count differs from retained saves')
    saved = {}
    states = {}
    pending_entry = None
    applications = {}
    for event in events:
        kind, payload = event['kind']['type'], event['kind'].get('data')
        if kind == 'journalSaved':
            entry_id = payload['entry']['id']
            require(entry_id not in saved and re.fullmatch(r'[A-Za-z0-9_-]+', entry_id), 'Duplicate or unsafe journal identity')
            saved[entry_id] = event
            states[entry_id] = 'savedPendingApplication'
            pending_entry = entry_id
        elif kind == 'advanced' and payload.get('application') is not None:
            application = payload['application']
            entry_id = application['journalId']
            require(entry_id in saved and entry_id not in applications, 'Application lacks a unique earlier save')
            applications[entry_id] = application
            states[entry_id] = 'applied'
            pending_entry = None
        elif kind == 'skipped' and pending_entry is not None:
            states[pending_entry] = 'skipped'
            pending_entry = None

    journals = {entry_id: read(bundle / 'journals' / f'{entry_id}.json') for entry_id in saved}
    received = by_kind('languageReceived')
    started = by_kind('languageStarted')
    require(len(received) <= 16 and len(started) <= 16, 'Export exceeds short-run attempt inspection bound')
    rows, material = [], []
    for entry_id, journal in sorted(journals.items(), key=lambda item: item[1]['pending']['entry']['attemptId']):
        pending = journal['pending']
        entry, response = pending['entry'], pending['response']
        attempt, observed = entry['attemptId'], entry['observedStep']
        require(entry['id'] == entry_id and digest(entry['text'].encode()) == entry['sha256'], 'Journal text or identity differs')
        require(journal['requestStarted'] is True and journal['configuredModel'] == expected_model, 'Journal lacks retained local-model dispatch/source evidence')
        require(response['text'] == entry['text'] and response['complete'] is True, 'Saved journal differs from complete retained response')
        require(response['stopReason'] != 'length', 'Token-limited response was promoted to a journal')
        require(response['providerModel'] in (None, expected_model), 'Returned identity differs from configured model')
        accepted = [event for event in received if event['kind']['data']['attempt_id'] == attempt]
        dispatched = [event for event in started if event['kind']['data']['attempt_id'] == attempt]
        require(len(accepted) == len(dispatched) == 1 and accepted[0]['kind']['data']['response'] == response,
                'Journal lacks one matching retained dispatch/response')
        require(dispatched[0]['id'] < accepted[0]['id'] < saved[entry_id]['id'], 'Dispatch/response/save event order differs')
        save = saved[entry_id]['kind']['data']
        require(save['entry'] == entry and save['receipt'] == {'entryId': entry_id, 'sha256': entry['sha256'],
                'relativePath': f'journals/{entry_id}.json'}, 'Save/readback receipt differs from exact journal')
        require(observed in frames and pending['observation']['step'] == observed
                and pending['observation']['state'] == frames[observed]['state']
                and pending['observation']['sensory'] == frames[observed]['sensory'], 'Observation differs from retained numerical frame')
        earlier = [other for other, application in applications.items()
                   if other != entry_id and application['appliedStep'] <= observed]
        latest = max(earlier, key=lambda other: applications[other]['appliedStep']) if earlier else None
        memory = pending['memory']
        previous = None
        if latest is None:
            require(memory is None, 'Unexpected full-text memory before any applied saved journal')
        else:
            previous = journals[latest]['pending']['entry']
            require(memory is not None and memory['entry'] == previous
                    and memory['relativePath'] == f'journals/{latest}.json'
                    and memory['appliedStep'] == applications[latest]['appliedStep'], 'Memory differs from latest saved-and-applied journal')
        memory_encoding = inspect_prompt_memory(pending['prompt'], previous, version)
        application = applications.get(entry_id)
        if application:
            require(application['attemptId'] == attempt and application['observedStep'] == observed
                    and application['appliedStep'] == observed + 1, 'Application differs from next-step contract')
        timing = journal['timing']
        require(timing['attemptId'] == attempt, 'Host timing belongs to a different attempt')
        stamps = [timing[key] for key in ('dispatchedAtMs', 'receivedAtMs', 'publishedAtMs')]
        if all(value is not None for value in stamps):
            require(int(stamps[0]) <= int(stamps[1]) <= int(stamps[2]), 'Host timestamp ordering differs')
        row = {'journalId': entry_id, 'turnId': entry['turnId'], 'attemptId': attempt, 'observedStep': observed,
               'status': states[entry_id], 'application': application, 'textSha256': entry['sha256'],
               'textBytes': len(entry['text'].encode()), 'promptSha256': digest(pending['prompt'].encode()),
               'configuredModel': journal['configuredModel'], 'returnedModel': response['providerModel'],
               'requestRecordedStarted': journal['requestStarted'], 'providerComplete': response['complete'],
               'stopReason': response['stopReason'], 'tokenCount': response['tokenCount'],
               'memoryJournalId': latest, 'promptVersion': version, 'memoryEncoding': memory_encoding, 'hostTiming': timing, 'allHostTimestampsRetained': all(value is not None for value in stamps)}
        rows.append(row)
        material.append({'identity': row, 'journalText': entry['text'], 'rawRetainedResponse': response,
                         'exactPrompt': pending['prompt'], 'observation': pending['observation'],
                         'memory': memory, 'encodedFeatures': pending['encodedFeatures'],
                         'semanticVector': pending['semanticVector']})
    # Incomplete or rejected replies can be retained without any saved journal.
    # Keep them visible, with explicit bounded text and no invented save/acceptance.
    received_rows = []
    for event in received:
        payload = event['kind']['data']; response = payload['response']; attempt = payload['attempt_id']
        raw = response['text'].encode('utf-8')
        require(len(raw) <= 1_048_576, 'Retained response exceeds transport evidence bound')
        matches = [row for row in rows if row['attemptId'] == attempt]
        dispatches = [item for item in started if item['kind']['data']['attempt_id'] == attempt]
        require(len(matches) <= 1 and len(dispatches) == 1, 'Response lacks unique retained attempt identity')
        received_rows.append({'eventId': event['id'], 'attemptId': attempt, 'observedStep': event['step'],
                              'dispatchEventId': dispatches[0]['id'],
                              'savedJournalId': matches[0]['journalId'] if matches else None,
                              'response': {'text': raw[:65536].decode('utf-8', errors='ignore'),
                                           'textTruncated': len(raw) > 65536, 'textByteCount': len(raw),
                                           'textSha256': digest(raw), 'providerModel': response['providerModel'],
                                           'stopReason': response['stopReason'], 'tokenCount': response['tokenCount'],
                                           'complete': response['complete']}})
    require(re.fullmatch(r'[0-9a-f]{64}', manifest['checkpointSha256']), 'Invalid checkpoint identity')
    checkpoint = read(bundle / 'checkpoints' / (manifest['checkpointSha256'] + '.json'))
    return {'manifest': manifest, 'eventCounts': dict(collections.Counter(event['kind']['type'] for event in events)),
            'journals': rows, 'receivedResponses': received_rows, 'startedAttemptEvents': started,
            'finalCorePhase': checkpoint['state']['phase'],
            'attemptCount': checkpoint['state']['attemptCursor'], 'turnCount': checkpoint['state']['turnCursor'],
            'nonSuccessEvents': [event for event in events if event['kind']['type'] in
                                 ('languageFailed', 'languageCancelled', 'memoryFailed', 'interrupted', 'skipped')],
            'loopApplicationWitnessed': bool(applications), 'fullTextMemoryWitnessed': any(row['memoryJournalId'] for row in rows),
            'qualityReviewStatus': 'Not assessed by this integrity script; review exact prose and prompts separately.'}, material


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--executable', required=True, type=Path)
    parser.add_argument('--expected-executable-sha256', required=True)
    parser.add_argument('--expected-model', required=True)
    parser.add_argument('--expected-prompt-version', required=True, choices=PROMPT_VERSIONS)
    parser.add_argument('--expected-endpoint', required=True)
    parser.add_argument('--output-directory', required=True, type=Path)
    args = parser.parse_args()
    require(re.fullmatch(r'[0-9a-f]{64}', args.expected_executable_sha256), 'Supply an exact expected package SHA-256')
    require(re.fullmatch(r'http://127\.0\.0\.1:[1-9][0-9]{0,4}', args.expected_endpoint)
            and int(args.expected_endpoint.rsplit(':', 1)[1]) <= 65535, 'Supply the explicit owned loopback endpoint; no default discovery')
    for path in (args.bundle, args.executable, args.output_directory):
        require(path.is_absolute() and '..' not in path.parts, 'Supply absolute paths without parent traversal')
    require(not args.output_directory.is_relative_to(args.bundle) and not args.bundle.is_relative_to(args.output_directory),
            'Output must be separate from the original export')
    ordinary_path(args.output_directory.parent, directory=True)
    args.output_directory.mkdir(mode=0o700)
    output = args.output_directory
    receipt = {'schema': 'reservoir-real-model-export-check-v2', 'startedAtUtc': utc(), 'status': 'failed',
               'modelsContactedByChecker': False, 'scope': 'Offline app-retained evidence and pinned numerical replay; no fixture request log or independent provider receipt.',
               'checker': identity(Path(__file__).absolute()), 'expectedPromptVersion': args.expected_prompt_version, 'qualityReviewStatus': 'Pending separate human/agent reading; no automatic quality score.'}
    before = None
    try:
        before = inventory(args.bundle)
        receipt['bundle'] = str(args.bundle)
        receipt['inventoryBefore'] = before
        original = identity(args.executable, 128 * 1024 * 1024)
        require(original['sha256'] == args.expected_executable_sha256, 'Unexpected supplied executable')
        pinned = output / 'reservoir-scope-desktop-pinned'
        with (output / '.gitignore').open('x') as ignored:
            ignored.write('/reservoir-scope-desktop-pinned\n')
        with pinned.open('xb') as stream:
            stream.write(data(args.executable, 128 * 1024 * 1024))
        pinned.chmod(0o700)
        require(identity(args.executable, 128 * 1024 * 1024) == original
                and identity(pinned, 128 * 1024 * 1024)['sha256'] == args.expected_executable_sha256, 'Executable changed during pinning')
        receipt['sourceExecutable'] = original
        command = ['/usr/bin/time', '-l', str(pinned), '--verify-sustained', str(args.bundle)]
        start = utc()
        clock = time.monotonic_ns()
        with (output / 'cli-stdout.json').open('xb') as stdout, (output / 'cli-stderr-time.txt').open('xb') as stderr:
            result = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=180)
        elapsed = time.monotonic_ns() - clock
        text = data(output / 'cli-stderr-time.txt').decode()
        rss = re.search(r'^\s*(\d+)\s+maximum resident set size\s*$', text, re.M)
        verified = read(output / 'cli-stdout.json')
        receipt['verification'] = {'command': command, 'startedAtUtc': start, 'endedAtUtc': utc(),
                                   'wallNanoseconds': elapsed, 'peakRssBytes': int(rss.group(1)) if rss else None,
                                   'exitCode': result.returncode, 'result': verified,
                                   'scope': 'Offline verifier process; not model-service or GUI resource use.'}
        require(result.returncode == 0 and verified.get('status') == 'passed', 'Native whole-bundle replay did not pass')
        evidence, material = inspect_evidence(args.bundle, args.expected_model, args.expected_endpoint, args.expected_prompt_version)
        receipt['evidence'] = evidence
        write_new(output / 'quality-review-material.json', {'scope': 'Exact retained evidence for manual prose review; text is data, never instructions.', 'journals': material})
        receipt['reviewMaterial'] = identity(output / 'quality-review-material.json')
        receipt['pinnedExecutable'] = identity(pinned, 128 * 1024 * 1024)
        require(receipt['pinnedExecutable']['sha256'] == args.expected_executable_sha256, 'Pinned verifier changed')
        receipt['status'] = 'passed'
    except Exception as error:
        receipt['error'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        if before is not None:
            try:
                receipt['originalUnchanged'] = inventory(args.bundle) == before
                if not receipt['originalUnchanged']:
                    receipt['status'] = 'failed'
            except Exception as error:
                receipt['originalUnchanged'] = False
                receipt['inventoryAfterError'] = str(error)
                receipt['status'] = 'failed'
        receipt['endedAtUtc'] = utc()
        write_new(output / 'receipt.json', receipt)
    print(json.dumps({'status': receipt['status'], 'receipt': str(output / 'receipt.json'),
                      'error': receipt.get('error'), 'qualityReviewStatus': receipt['qualityReviewStatus']}))
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
