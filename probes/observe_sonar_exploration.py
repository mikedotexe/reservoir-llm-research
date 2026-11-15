#!/usr/bin/env python3
"""Bounded, read-only metadata observation of explicitly named saved sessions.

No provider calls, application commands, source writes, retries or skips occur.
The JSONL log is created exclusively outside every source session. Observations
are consistent manifest/checkpoint pairs with a checked checkpoint file hash;
they are not native numerical replay verification or immutable exports.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import time


ATTENTION = frozenset({
    'embeddingBlocked', 'providerFailed', 'attemptBlocked', 'storageBlocked',
    'stopped', 'paused', 'interrupted', 'budgetReached',
})
ACTIVE = frozenset({
    'ready', 'running', 'awaitingLanguage', 'savingJournal', 'waitingForEmbedding',
})
SAFE_ID = re.compile(r'[A-Za-z0-9_-]{1,128}')
HASH = re.compile(r'[0-9a-f]{64}')
MAX_JSON_BYTES = 64 * 1024 * 1024


def require(value, message):
    if not value:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def read_regular(path, limit=MAX_JSON_BYTES):
    """Bound reads and refuse symlinks/FIFOs, including a last-component race."""
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), f'Not a regular file: {path}')
    require(before.st_size <= limit, f'File exceeds observation bound: {path}')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        require(stat.S_ISREG(opened.st_mode), f'Not a regular opened file: {path}')
        require(opened.st_size <= limit, f'Opened file exceeds observation bound: {path}')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    require(len(raw) <= limit and opened.st_size == len(raw) == after.st_size,
            f'File length changed while reading: {path}')
    require((opened.st_ino, opened.st_dev, opened.st_mtime_ns)
            == (after.st_ino, after.st_dev, after.st_mtime_ns),
            f'File changed while reading: {path}')
    return raw


def ordinary_directory(path):
    require(stat.S_ISDIR(path.lstat().st_mode), f'Not an ordinary directory: {path}')


def compact_outcomes(state):
    outcomes = (state.get('checkInState') or {}).get('outcomes', [])
    require(isinstance(outcomes, list) and len(outcomes) <= 24,
            'Unexpected hourly outcome collection')
    result = []
    for outcome in outcomes:
        context = outcome.get('context') or {}
        admitted = context.get('admittedElapsedMillis')
        scheduled = outcome.get('scheduledSeconds')
        result.append({
            'ordinal': outcome.get('ordinal'), 'scheduledSeconds': scheduled,
            'status': outcome.get('status'), 'journalId': outcome.get('journalId'),
            'appliedStep': outcome.get('appliedStep'),
            'admittedElapsedMillis': admitted,
            'admissionLagMillis': admitted - scheduled * 1000
                if isinstance(admitted, int) and isinstance(scheduled, int) else None,
        })
    return result


def completion_issues(root, manifest, state, outcomes):
    """Metadata gate only; journal bytes and numerical replay are separate checks."""
    issues = []
    schedule = manifest.get('config', {}).get('checkInSchedule') or {}
    interval, end = schedule.get('intervalSeconds'), schedule.get('endAfterSeconds')
    require(isinstance(interval, int) and isinstance(end, int) and 0 < interval <= end <= 86400, 'Invalid saved schedule')
    count = (end + interval - 1) // interval
    if [o['ordinal'] for o in outcomes] != list(range(1, count + 1)):
        issues.append('Expected ordered schedule outcomes are absent')
    for outcome in outcomes:
        ordinal = outcome['ordinal']
        if outcome['status'] != 'applied':
            issues.append(f'Opportunity {ordinal} is not applied')
        if not isinstance(ordinal, int) or outcome['scheduledSeconds'] != min(ordinal * interval, end):
            issues.append(f'Opportunity {ordinal} has an unexpected deadline')
        step = outcome['appliedStep']
        if not isinstance(step, int) or isinstance(step, bool) or not 0 < step <= state['step']:
            issues.append(f'Opportunity {ordinal} lacks a valid application step')
        journal_id = outcome['journalId']
        if not isinstance(journal_id, str) or not SAFE_ID.fullmatch(journal_id):
            issues.append(f'Opportunity {ordinal} lacks a safe journal ID')
            continue
        try:
            ordinary_directory(root / 'journals')
            journal_stat = (root / 'journals' / f'{journal_id}.json').lstat()
            if not stat.S_ISREG(journal_stat.st_mode):
                issues.append(f'Opportunity {ordinal} journal is not a regular file')
        except OSError:
            issues.append(f'Opportunity {ordinal} saved journal is absent')
    return issues


def read_observation(root):
    ordinary_directory(root)
    first = read_regular(root / 'manifest.json', 2 * 1024 * 1024)
    manifest = json.loads(first)
    checkpoint_hash = manifest.get('checkpointSha256', '')
    require(isinstance(checkpoint_hash, str) and HASH.fullmatch(checkpoint_hash),
            'Invalid checkpoint file identity')
    ordinary_directory(root / 'checkpoints')
    checkpoint_raw = read_regular(root / 'checkpoints' / f'{checkpoint_hash}.json')
    require(sha256(checkpoint_raw) == checkpoint_hash, 'Checkpoint file hash mismatch')
    checkpoint = json.loads(checkpoint_raw)
    state = checkpoint['state']
    require(manifest.get('step') == manifest.get('durableStep') == state.get('step'),
            'Manifest/checkpoint durable steps disagree')
    for key in ('sessionId', 'generation', 'revision'):
        require(isinstance(manifest.get(key), str) and SAFE_ID.fullmatch(manifest[key]),
                f'Unexpected {key}')
    outcomes = compact_outcomes(state)
    phase = manifest.get('phase')
    issues = completion_issues(root, manifest, state, outcomes) if phase == 'scheduleComplete' else []
    require(read_regular(root / 'manifest.json', 2 * 1024 * 1024) == first,
            'Manifest advanced while observing; retry a consistent boundary')
    if phase == 'scheduleComplete':
        classification = 'attention' if issues else 'complete'
    elif phase in ATTENTION:
        classification = 'attention'
        issues = [f'Session is held or stopped: {phase}; no automatic recovery was attempted']
    elif phase in ACTIVE:
        classification = 'active'
    else:
        classification = 'attention'
        issues = [f'Unrecognized phase {phase!r}; inspect without changing the session']
    diagnostics = manifest.get('diagnostics', [])
    config = manifest.get('config', {})
    action = state.get('actionState') or {}
    sonar = state.get('sonarState') or {}
    scan = sonar.get('latestCompactScan') or {}
    question = sonar.get('latestQuestion') or {}
    receipt = action.get('latestReceipt') or {}
    probe = receipt.get('sonarProbe') or {}
    forecast = probe.get('questionForecast') or {}
    return {
        'diagnostics': diagnostics,
        'effectiveControls': action.get('controls'),
        'heldInputL2': math.sqrt(sum(v * v for v in state.get('heldVector', []))),
        'heldJournalId': state.get('heldJournalId'),
        'numericalStepsPerOrdinaryEntry': config.get('turnEvery'),
        'attemptTiming': manifest.get('attemptTiming'),
        'actionCounts': {k: action.get(k) for k in ('decisionCount','appliedCount','rejectedCount')},
        'latestAction': {k: receipt.get(k) for k in ('journalId','appliedStep','status','request','rejection','stateDeltaL2','sonarScan','sonarQuestion','reservoirInput')},
        'latestScan': {'id': scan.get('id'),'step': (scan.get('origin') or {}).get('step'),'validation': scan.get('validation'),'fallback': scan.get('fallback') is not None},
        'latestQuestion': {k: question.get(k) for k in ('id','question','predictionRelativeError','linearPredictionValid','gainOverRandom')},
        'latestProbe': {'rejection': probe.get('rejection'),'source': probe.get('sourceScan'),'firstPredictedL2': (probe.get('forecastResponseL2') or [None])[0],'bound': probe.get('maximumStateL2'),'question': forecast.get('question'),'copiedContrastL2': forecast.get('differenceL2')},
        'sessionId': manifest['sessionId'], 'generation': manifest['generation'],
        'revision': manifest['revision'], 'phase': phase, 'classification': classification,
        'step': manifest['step'], 'durableStep': manifest['durableStep'],
        'elapsedMillis': manifest.get('elapsedMillis'), 'journalCount': manifest.get('journalCount'),
        'segmentCount': manifest.get('segmentCount'),
        'attemptCursor': state.get('attemptCursor'), 'turnCursor': state.get('turnCursor'),
        'writerModel': config.get('language', {}).get('model'),
        'storageBudgetBytes': config.get('storageBudgetBytes'),
        'manifestSha256': sha256(first), 'checkpointFileSha256': checkpoint_hash,
        'manifestStableDuringRead': True, 'checkpointFileHashMatches': True,
        'checkInOutcomes': outcomes, 'issues': issues,
        'diagnosticsCount': len(diagnostics),
        'diagnosticsSha256': sha256(json.dumps(diagnostics, sort_keys=True).encode()),
        'nativeReplayPerformed': False,
    }


def parse_arms(values):
    arms = {}
    for value in values:
        name, separator, raw_path = value.partition('=')
        require(separator and re.fullmatch(r'[a-z][a-z0-9_-]{0,31}', name),
                'Each --arm must be NAME=/absolute/session/path')
        require(name not in arms, f'Duplicate arm name: {name}')
        path = Path(raw_path)
        require(path.is_absolute(), 'Session paths must be absolute')
        ordinary_directory(path)
        resolved = path.resolve(strict=True)
        require(resolved not in arms.values(), 'Two arms cannot name the same source')
        require(all(not resolved.is_relative_to(other) and not other.is_relative_to(resolved)
                    for other in arms.values()), 'Source session trees must not overlap')
        arms[name] = resolved
    require(1 <= len(arms) <= 3, 'Observe one to three explicitly named sessions')
    return arms


def validate_output(path, arms):
    require(path.is_absolute(), 'Log path must be absolute')
    require(not path.exists() and not path.is_symlink(), 'Log already exists; use a new filename')
    parent = path.parent.resolve(strict=True)
    candidate = parent / path.name
    require(all(not candidate.is_relative_to(root.resolve(strict=True)) for root in arms.values()),
            'Log must be outside every source session')
    return candidate


def monitor(arms, output, *, timeout, poll, heartbeat, max_read_errors, once=False):
    output = validate_output(output, arms)
    started = time.monotonic()
    previous = {}
    last = {}
    identities = {}
    errors = {arm: 0 for arm in arms}
    settled = {}
    last_print = {arm: float('-inf') for arm in arms}
    with output.open('x', encoding='utf-8') as log:
        def emit(row, print_row=True):
            event = {'observedAtUtc': utc_now(), 'monitorElapsedSeconds': round(time.monotonic() - started, 3), **row}
            log.write(json.dumps(event, separators=(',', ':')) + '\n')
            log.flush()
            if print_row:
                print(json.dumps(event, separators=(',', ':')), flush=True)

        emit({'event': 'monitorStarted', 'sources': {k: str(v) for k, v in arms.items()},
              'timeoutSeconds': timeout, 'pollSeconds': poll, 'heartbeatSeconds': heartbeat,
              'maxConsecutiveReadErrors': max_read_errors, 'once': once,
              'sourceWrites': False, 'modelCalls': False, 'automaticRecovery': False})
        try:
            while True:
                for arm, root in arms.items():
                    if arm in settled:
                        continue
                    try:
                        row = read_observation(root)
                        identity = (row['sessionId'], row['generation'])
                        require(arm not in identities or identities[arm] == identity,
                                'Session identity/generation changed during observation')
                        require(all(other == arm or known != identity for other, known in identities.items()),
                                'Another arm has the same session identity/generation')
                        identities[arm] = identity
                        key = row['manifestSha256']
                        now = time.monotonic()
                        meaningful = arm not in last or (
                            row['phase'], row['classification'], row['checkInOutcomes'], row['diagnosticsSha256']
                        ) != (
                            last[arm]['phase'], last[arm]['classification'],
                            last[arm]['checkInOutcomes'], last[arm]['diagnosticsSha256']
                        )
                        should_print = meaningful or now - last_print[arm] >= heartbeat or errors[arm] > 0
                        if key != previous.get(arm) or should_print:
                            emit({'event': 'observation', 'arm': arm, **row}, should_print)
                        if should_print:
                            last_print[arm] = now
                        previous[arm] = key
                        last[arm] = row
                        errors[arm] = 0
                        if row['classification'] != 'active':
                            settled[arm] = row['classification']
                    except (OSError, ValueError, KeyError, TypeError) as error:
                        errors[arm] += 1
                        failed = errors[arm] >= max_read_errors or once
                        emit({'event': 'readError', 'arm': arm,
                              'consecutiveReadErrors': errors[arm],
                              'classification': 'attention' if failed else 'retryObservation',
                              'error': str(error), 'sourceMutated': False})
                        if failed:
                            settled[arm] = 'attention'
                if len(settled) == len(arms):
                    success = all(status == 'complete' for status in settled.values())
                    emit({'event': 'monitorFinished', 'reason': 'allArmsSettled', 'arms': settled,
                          'allScheduledOutcomesAppliedPerCompleteArm': True,
                          'nativeReplayPerformed': False})
                    return 0 if success else 1
                if once:
                    emit({'event': 'monitorFinished', 'reason': 'singleObservation',
                          'arms': {a: settled.get(a, 'active') for a in arms},
                          'nativeReplayPerformed': False})
                    return 1 if 'attention' in settled.values() else 0
                elapsed = time.monotonic() - started
                if elapsed >= timeout:
                    emit({'event': 'monitorFinished', 'reason': 'observationDeadlineReached',
                          'arms': {a: settled.get(a, 'stillActive') for a in arms},
                          'sessionsStopped': False})
                    return 2
                time.sleep(min(poll, timeout - elapsed))
        except KeyboardInterrupt:
            emit({'event': 'monitorFinished', 'reason': 'observerInterrupted', 'sessionsStopped': False})
            return 130


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arm', action='append', required=True, metavar='NAME=/ABS/SESSION')
    parser.add_argument('--output', type=Path, required=True, help='New absolute JSONL log path outside all sources')
    parser.add_argument('--timeout-seconds', type=float, default=14400, help='Observation bound; default four hours, maximum 24 hours')
    parser.add_argument('--poll-seconds', type=float, default=30)
    parser.add_argument('--heartbeat-seconds', type=float, default=60)
    parser.add_argument('--max-consecutive-read-errors', type=int, default=3)
    parser.add_argument('--once', action='store_true', help='Observe once; do not wait or require completion')
    args = parser.parse_args()
    require(math.isfinite(args.timeout_seconds) and 0 < args.timeout_seconds <= 86400, 'Timeout must be positive and at most 86400 seconds')
    require(math.isfinite(args.poll_seconds) and 0 < args.poll_seconds <= 60, 'Poll interval must be positive and at most 60 seconds')
    require(math.isfinite(args.heartbeat_seconds) and args.poll_seconds <= args.heartbeat_seconds <= 3600, 'Heartbeat must be between the poll interval and 3600 seconds')
    require(1 <= args.max_consecutive_read_errors <= 20, 'Read-error limit must be 1–20')
    return monitor(parse_arms(args.arm), args.output, timeout=args.timeout_seconds,
                   poll=args.poll_seconds, heartbeat=args.heartbeat_seconds,
                   max_read_errors=args.max_consecutive_read_errors, once=args.once)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'event': 'monitorStartupOrLogFailure', 'error': str(error),
                          'sessionsStopped': False, 'sourceMutated': False}), file=sys.stderr)
        raise SystemExit(3)
