#!/usr/bin/env python3
"""Passively sample one explicitly named owned committed manifest after Start.

No journal, prompt, checkpoint, directory inventory, app, process or network access.
The manifest is not a numerical replay or a live-memory snapshot. A held/terminal
phase, unexpected identity/read failure, or the hard time limit ends observation;
this helper never stops, resumes or retries the application. Output is exclusive.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

MAX_MANIFEST = 128 * 1024
MAX_SAMPLES = 61
ACTIVE = {'running', 'awaitingLanguage', 'savingJournal'}
HELD = {'ready', 'paused', 'stopped', 'budgetReached', 'storageBlocked', 'providerFailed',
        'compatibilityBlocked', 'attemptBlocked', 'interrupted'}
FIELDS = ('sessionId', 'generation', 'revision', 'phase', 'step', 'durableStep', 'journalCount',
          'segmentCount', 'elapsedMillis', 'checkpointSha256', 'lastSegmentSha256')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate manifest field: ' + key)
        result[key] = value
    return result


def ordinary_parents(path):
    require(path.is_absolute() and '..' not in path.parts, 'Explicit absolute path without traversal required')
    for parent in path.parents:
        require(stat.S_ISDIR(parent.lstat().st_mode), 'Linked or nonordinary ancestor: ' + str(parent))


def read_snapshot(path, session_id, generation):
    ordinary_parents(path)
    require(stat.S_ISREG(path.lstat().st_mode), 'Manifest must be an ordinary unlinked file')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_MANIFEST, 'Manifest exceeds bounded ordinary-file scope')
        raw = stream.read(MAX_MANIFEST + 1)
        after = os.fstat(stream.fileno())
    identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
    require(len(raw) <= MAX_MANIFEST and len(raw) == before.st_size and identity(before) == identity(after),
            'Opened manifest changed during read')
    # The app publishes by atomic rename. Reading the old opened inode remains a
    # valid committed snapshot; the next sample can observe a newer revision.
    manifest = json.loads(raw, object_pairs_hook=unique_pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    require(manifest['format'] == 'reservoir-sustained-bundle-v1'
            and manifest['sessionId'] == session_id and manifest['generation'] == generation,
            'Manifest format/session/generation differs from explicit selection')
    require(manifest['config']['promptVersion'] == 'reservoir-journal-v8', 'Manifest is not the selected v8 session')
    require(type(manifest['revision']) is str and re.fullmatch(r'[1-9][0-9]*', manifest['revision'])
            and int(manifest['revision']) < 1 << 64, 'Invalid retained revision')
    require(manifest['phase'] in ACTIVE | HELD, 'Unknown manifest phase; observation stops')
    for field in ('step', 'durableStep', 'journalCount', 'segmentCount', 'elapsedMillis'):
        require(type(manifest[field]) is int and 0 <= manifest[field] < 1 << 64, 'Invalid retained counter: ' + field)
    require(manifest['durableStep'] <= manifest['step'], 'Durable step exceeds committed wrapper step')
    config = json.dumps(manifest['config'], sort_keys=True, ensure_ascii=False,
                        separators=(',', ':'), allow_nan=False).encode('utf-8')
    return {'capturedAtUtc': utc(), 'source': str(path), 'sourceBytes': len(raw), 'sourceSha256': sha(raw),
            'openedFile': {'device': before.st_dev, 'inode': before.st_ino, 'modifiedNs': before.st_mtime_ns},
            'manifest': {field: manifest[field] for field in FIELDS},
            'parsedConfigSha256': sha(config),
            'scope': 'One committed manifest projection only; no prose, numerical replay or live-memory inspection.'}


def check_progress(previous, current):
    if previous is None:
        return
    require(current['parsedConfigSha256'] == previous['parsedConfigSha256'], 'Accepted configuration changed; observation stops')
    for field in ('revision', 'step', 'durableStep', 'journalCount', 'segmentCount', 'elapsedMillis'):
        require(int(current['manifest'][field]) >= int(previous['manifest'][field]),
                'Committed progress regressed: ' + field)
    if current['manifest']['revision'] == previous['manifest']['revision']:
        require(current['sourceSha256'] == previous['sourceSha256'], 'Same revision has different bytes')


def write_new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def sample(path, session_id, generation, output, duration, interval, clock=time.monotonic, sleep=time.sleep):
    require(type(duration) is int and 1 <= duration <= 900, 'Observation duration must be 1–900 seconds')
    require(type(interval) is int and 15 <= interval <= 45, 'Sample interval must be 15–45 seconds')
    start = clock()
    result = {'schema': 'reservoir-v8-passive-manifest-observation-v1', 'status': 'running',
              'startedAtUtc': utc(), 'manifest': str(path), 'sessionId': session_id, 'generation': generation,
              'durationLimitSeconds': duration, 'intervalSeconds': interval, 'samples': [],
              'modelsContacted': False, 'appActivated': False, 'processActions': False,
              'limitations': ['Committed manifest can lag volatile progress. It is not a verification of response/save/application content.',
                             'A bounded sampling interval can miss intermediate states; actual timestamps and elapsed intervals are retained.',
                             'The sampler stops itself only and does not control the app, provider or numerical clock.']}
    previous = None
    try:
        while True:
            elapsed = clock() - start
            if elapsed > duration:
                result['status'] = 'duration_limit_reached'
                break
            require(len(result['samples']) < MAX_SAMPLES, 'Sample-count bound reached')
            row = read_snapshot(path, session_id, generation)
            check_progress(previous, row)
            row['elapsedMonotonicSeconds'] = clock() - start
            row['sample'] = len(result['samples']) + 1
            dest = output / f"passive-manifest-{row['sample']:02d}.json"
            write_new(dest, row)
            result['samples'].append({'path': str(dest), 'sha256': sha(dest.read_bytes()),
                                      'capturedAtUtc': row['capturedAtUtc'], 'elapsedMonotonicSeconds': row['elapsedMonotonicSeconds'],
                                      **row['manifest']})
            print(json.dumps({'sample': row['sample'], **row['manifest']}), flush=True)
            if row['manifest']['phase'] in HELD:
                result['status'] = 'held_or_terminal_observed'
                result['observedPhase'] = row['manifest']['phase']
                break
            previous = row
            remaining = duration - (clock() - start)
            if remaining <= 0:
                result['status'] = 'duration_limit_reached'
                break
            sleep(min(interval, remaining))
    except Exception as error:
        result.update(status='observation_failed', error={'type': type(error).__name__, 'message': str(error)})
    result['endedAtUtc'] = utc()
    result['elapsedMonotonicSeconds'] = clock() - start
    result['sampler'] = {'path': str(Path(__file__).resolve()), 'sha256': sha(Path(__file__).read_bytes())}
    write_new(output / 'sampling-result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--session-id', required=True)
    parser.add_argument('--generation', required=True)
    parser.add_argument('--output-directory', type=Path, required=True)
    parser.add_argument('--duration-seconds', type=int, default=900)
    parser.add_argument('--interval-seconds', type=int, default=30)
    args = parser.parse_args()
    require(re.fullmatch(r'sustained-[0-9]+-[0-9]+', args.session_id), 'Explicit owned session ID required')
    require(re.fullmatch(r'[1-9][0-9]*', args.generation) and int(args.generation) < 1 << 64, 'Explicit generation required')
    expected = Path.home() / 'Library/Application Support/research.reservoir.scope.tauri/sustained-v1' / args.session_id / 'manifest.json'
    require(args.manifest == expected, 'Only the exact selected owned Tauri session manifest is permitted')
    ordinary_parents(args.manifest)
    ordinary_parents(args.output_directory)
    desktop = Path(__file__).resolve().parents[2]
    allowed = [Path(__file__).resolve().parent, desktop / 'target/qa']
    require(any(args.output_directory.is_relative_to(root) and args.output_directory != root for root in allowed)
            and not args.output_directory.exists() and not args.output_directory.is_symlink(),
            'Output must be a new child directory in this episode or worktree QA')
    require(1 <= args.duration_seconds <= 900 and 15 <= args.interval_seconds <= 45, 'Invalid observation bounds')
    args.output_directory.mkdir()
    result = sample(args.manifest, args.session_id, args.generation, args.output_directory,
                    args.duration_seconds, args.interval_seconds)
    print(json.dumps({'status': result['status'], 'receipt': str(args.output_directory / 'sampling-result.json')}), flush=True)
    return 1 if result['status'] == 'observation_failed' else 0


if __name__ == '__main__':
    raise SystemExit(main())
