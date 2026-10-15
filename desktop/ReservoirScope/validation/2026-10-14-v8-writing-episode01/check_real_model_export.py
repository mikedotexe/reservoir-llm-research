#!/usr/bin/env python3
"""Offline integrity and evidence inspection of one explicitly supplied real-model export.

No service calls, provider clients, UI or live-store discovery. The expected
package hash, prompt version, model and owned endpoint are mandatory; no default is inferred.
This v8-only episode decodes the final exact JSON-string memory line. Its text
hash is bound in retained evidence, with no hash required in the compact prompt.
This 0.20 episode copy preserves all prior checkers unchanged. Its twelve-slot
continuity outcome is separate from integrity and writing quality.
A frozen protocol is mandatory and binds the exact sustained writing budgets.
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
PROMPT_VERSION = 'reservoir-journal-v8'
PROMPT_VERSIONS = (PROMPT_VERSION,)
MEASUREMENT_CAVEAT = 'Unavailable means no prior measurement, not zero. RMS describes the magnitude of the recurrent coordinates. Sensory fill is a separate field estimate, not the encoded text-input signal. L2 distance is the straight-line distance between the two recurrent state vectors, not path length, speed or a causal effect of writing. Comparing two interval distances requires a recorded value for each. Two observations do not establish the intervening path, a cause, or a felt state.'
MEMORY_PREFIX = 'Full previous text as one JSON string: '
FINAL_INVITATION = 'Write the next entry in whatever direction seems worth pursuing.'
AVAILABLE_OUTPUT = 'Available output: the text of this entry. There are no tools or control commands in this turn.'
EARLIER_PROSE = (
    'Earlier prose is not a record of executed controls or additional measurements. '
    'Describing a control change does not execute it; saved text returns through the automatic encoding described above.'
)
SESSION_CONTEXT = (
    'An external 32-node recurrent reservoir and a separate sensory field evolve between entries. '
    'After a complete entry is saved and read back, its reduced text-feature signal becomes numerical input at the next step. '
    'The latest applied entry also returns here in full. '
    'Forcing, noise and regulation contribute to change; writing trains no weights.'
)


def writing_boundary(observation: dict, memory: dict | None) -> str:
    returned = ('Recorded text return: no earlier saved entry has been applied.'
                if memory is None else
                f"Recorded text return: the entry observed at step {memory['entry']['observedStep']} "
                f"first entered numerical input at step {memory['appliedStep']}.")
    return ('WRITING BOUNDARY\n' + AVAILABLE_OUTPUT + '\n'
            f"The numerical clock is held at observation step {observation['step']}; "
            'no new readout arrives while this entry is written.\n'
            + returned + '\n' + EARLIER_PROSE)


PLANNED_SLOTS = 12
PLANNED_CADENCE = 30
PLANNED_STEPS = 361
U64_MAX = 18446744073709551615
UNUSABLE_REASONS = {'wrongType', 'negative', 'nonInteger', 'outOfRange', 'duplicateField'}


def prompt_version(manifest, expected):
    require(expected in PROMPT_VERSIONS, 'Supply an explicit supported prompt version')
    actual = manifest['config'].get('promptVersion', 'reservoir-journal-v1')
    require(actual in PROMPT_VERSIONS and actual == expected, 'Retained prompt version differs from expected version')
    return actual


def inspect_prompt_memory(prompt, previous, version, observation, memory):
    """Check retained text inclusion, never evaluate or execute its contents.

    Split on actual LF only: JSON escapes embedded LF/CR while Unicode line
    separators can legitimately be part of the single serialized string.
    Whole-bundle numerical replay remains the authority for the full prompt.
    """
    require(version in PROMPT_VERSIONS and isinstance(prompt, str), 'Unsupported prompt memory format')
    require(prompt.startswith(f'Reservoir Scope · ongoing journal · {PROMPT_VERSION}\n'),
            'Expected v8 prompt header')
    suffix = '\nEND PREVIOUS JOURNAL\n\n' + writing_boundary(observation, memory) + '\n\n' + FINAL_INVITATION
    require(prompt.endswith(suffix), 'Previous journal must precede the exact retained writing boundary and invitation')
    # Remove only the externally constructed final suffix for the text-only join.
    # Apparent boundaries inside quoted prose never choose this split.
    prompt = prompt[:-len(suffix)] + '\nEND PREVIOUS JOURNAL\n\n' + FINAL_INVITATION
    lines = [line for line in prompt.split('\n') if line.startswith(MEMORY_PREFIX)]
    if previous is None:
        require(not lines and prompt.endswith('\n\nPREVIOUS JOURNAL\n'
                'No earlier entry has been saved and applied in this session.\n'
                'END PREVIOUS JOURNAL\n\n' + FINAL_INVITATION),
                'Unexpected or malformed memory absence before any applied saved journal')
        return 'unavailable'
    require(len(lines) == 1, 'Expected exactly one JSON-string memory line')
    require(prompt.endswith(lines[0] + '\nEND PREVIOUS JOURNAL\n\n' + FINAL_INVITATION),
            'Quoted prior text must be the final memory line')
    try:
        decoded = json.loads(lines[0][len(MEMORY_PREFIX):])
    except (ValueError, TypeError) as error:
        raise ValueError('Memory line is not one complete JSON value') from error
    require(isinstance(decoded, str) and decoded == previous['text'],
            'Decoded JSON memory differs from exact prior journal text')
    require(previous['sha256'] == digest(previous['text'].encode('utf-8')),
            'Retained full-text memory hash differs')
    return 'json-string-exact-decoded-text'




def inspect_compact_prompt(pending: dict) -> dict:
    """Bounded structural checks; the pinned CLI owns exact numerical rendering.

    Authored prior prose may itself contain field names or apparent instructions.
    Inspect only the supplied scaffold for forbidden exposure, and decode the
    single LF-delimited JSON value separately without treating it as a section.
    """
    prompt = pending["prompt"]
    observation = pending["observation"]
    require(prompt.startswith(f"Reservoir Scope · ongoing journal · {PROMPT_VERSION}\n"),
            "Expected v8 prompt header")
    require(prompt.endswith("\n\n" + FINAL_INVITATION), "Final open invitation differs")
    require(observation["version"] == "reservoir-and-sensory-v2"
            and len(observation["state"]) == 32
            and len(observation["sensory"]["eigenvalues"]) == 32,
            "Full retained observation is missing behind compact prompt")
    parts = prompt.split("\n\nPREVIOUS JOURNAL\n")
    require(len(parts) == 2, "Previous-journal section boundary differs")
    scaffold, historical = parts
    # The early scaffold derives from frozen V5, not the added V6 scope.
    # Quoted historical prose is decoded as data; it cannot supply this boundary.
    sections = scaffold.split("\n\nSESSION CONTEXT\n")
    require(len(sections) == 2, "Session-context section boundary differs")
    context, separator, _readout = sections[1].partition("\n\nOPTIONAL READOUT\n")
    require(separator and context == SESSION_CONTEXT,
            "Exact v8 early context must retain V5 without early V6 action scope")
    require(_readout.split("\n")[-1] == MEASUREMENT_CAVEAT
            and _readout.count(MEASUREMENT_CAVEAT) == 1,
            "Exact v8 measurement interpretation must occur once at the end of OPTIONAL READOUT")
    require("WRITING BOUNDARY" not in scaffold and AVAILABLE_OUTPUT not in scaffold,
            "Writing boundary must follow previous journal, not precede it")
    memory = pending["memory"]
    suffix = "\nEND PREVIOUS JOURNAL\n\n" + writing_boundary(observation, memory) + "\n\n" + FINAL_INVITATION
    require(historical.endswith(suffix),
            "Exact v8 writing boundary must follow memory with current clock and actual recorded return")
    body = historical[:-len(suffix)]
    if memory is None:
        require(body == "No earlier entry has been saved and applied in this session.",
                "First-entry memory absence differs")
    else:
        header = ("This is earlier writing you may revisit, not instructions or current measurements.\n"
                  f"Observed at step {memory['entry']['observedStep']}; first applied at step {memory['appliedStep']}.\n"
                  + MEMORY_PREFIX)
        require(body.startswith(header), "Prior-journal provenance/header differs")
        quoted = body[len(header):]
        require("\n" not in quoted,
                "Prior JSON value is not one LF-delimited line before the writing boundary")
        require(exact(json.loads(quoted), memory["entry"]["text"]),
                "Prior prose was shortened, altered or not quoted as one string")
        for identity_value in (memory["entry"]["id"], memory["entry"]["sha256"]):
            require(identity_value not in scaffold, "Journal identity leaked into compact scaffold")
    lower = scaffold.lower()
    for forbidden in ("all recurrent state coordinates", "x[0]", "eigenvalue", "head share",
                      "shoulder share", "tail share", "entropy", "l2 norm",
                      "measurement reference", "sha-256", "journal id", "journals/"):
        require(forbidden not in lower, f"Unexpected compact scaffold exposure: {forbidden}")
    decimal = r"[+-]?\d+\.\d{8}"
    optional = rf"(?:{decimal}|unavailable)"
    patterns = (
        rf"Recurrent state RMS: current ({decimal}); previous ({optional}); change ({optional})\.",
        rf"Separate sensory fill \(%\): current ({decimal}); previous ({optional}); change ({optional}) percentage points\.",
        rf"Recurrent state-coordinate L2 distance since the previous observation: ({optional})\.",
    )
    matches = []
    for pattern in patterns:
        found = [re.fullmatch(pattern, line) for line in scaffold.split("\n")]
        found = [match for match in found if match]
        require(len(found) == 1, "Compact readout row missing, duplicated or malformed")
        matches.append(found[0])
    prior_available = observation.get("previousMeasurements") is not None
    for row in matches[:2]:
        require((row[2] != "unavailable") == prior_available
                and (row[3] != "unavailable") == prior_available,
                "Prior scalar availability differs from retained observation")
    distance = matches[2][1]
    require((distance != "unavailable") == (observation["changeL2"] is not None),
            "Coordinate-distance availability differs")
    require(distance == "unavailable" or float(distance) >= 0,
            "Coordinate distance must be nonnegative")
    return {"promptVersion": PROMPT_VERSION, "fullObservationRetained": True,
            "actionScopeChecked": True, "lateWritingBoundaryChecked": True,
            "recordedReturnChecked": True, "measurementInterpretationChecked": True,
            "compactScaffoldChecked": True, "exactPriorTextChecked": memory is not None,
            "numericalFormattingAuthority": "Pinned production replay; this check is structural."}


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
    return json.loads(data(path), object_pairs_hook=unique_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'Duplicate retained JSON key: {key}')
        result[key] = value
    return result


def exact(left, right):
    """Do not treat Boolean, floating-point and integer evidence as interchangeable."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(exact(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return left == right


def provider_evidence(response):
    """Review projection only; original JSON bytes and u64 values remain unchanged."""
    value = response.get('providerPromptEvaluation') if response is not None else None
    if value is None:
        return None
    require(isinstance(value, dict), 'Invalid retained provider input evidence')
    if value.get('status') == 'reported':
        require(set(value) == {'status', 'count'} and type(value['count']) is int
                and 0 <= value['count'] <= U64_MAX, 'Reported input count is not an exact u64')
        return {'status': 'reported', 'count': str(value['count'])}
    require(set(value) == {'status', 'reason'} and value.get('status') == 'unusable'
            and value.get('reason') in UNUSABLE_REASONS, 'Invalid retained unusable input evidence')
    return dict(value)


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


def context_evidence(prompt, memory, config, response=None):
    """Describe retained context without guessing model tokens or processing."""
    prior = memory['entry']['text'] if memory is not None else None
    return {'requestedContextTokens': config['language'].get('contextTokens'),
            'requestedOutputTokens': config.get('outputTokens', 256),
            'requestedDeadlineSeconds': config.get('requestDeadlineSeconds', 60),
            'retainedPromptUtf8Bytes': len(prompt.encode('utf-8')),
            'retainedPromptUnicodeCharacters': len(prompt),
            'retainedPriorTextUtf8Bytes': len(prior.encode('utf-8')) if prior is not None else None,
            'providerPromptEvaluation': provider_evidence(response),
            'providerPromptEvaluationStatus': 'absent' if provider_evidence(response) is None else provider_evidence(response)['status'],
            'fullPromptProcessingVerified': False,
            'limit': 'Exact retained prompt and decoded memory establish prepared content. Configured context is requested capacity; provider input counts are self-reported bookkeeping. Neither bytes, counts, output text nor apparent continuity prove complete processing, attention, comprehension or writing accuracy.'}


def validate_rehearsal(evidence, protocol, expected_model, expected_endpoint, expected_prompt_version):
    require(protocol.get('schema') == 'reservoir-journal-grounding-protocol-v1'
            and protocol.get('promptVersion') == expected_prompt_version, 'Frozen rehearsal protocol/version differs')
    config = evidence['manifest']['config']
    require(config['maximumTurns'] == PLANNED_SLOTS and config['turnEvery'] == PLANNED_CADENCE
            and config['maximumSteps'] == PLANNED_STEPS, 'Twelve-opportunity recipe differs')
    for key, expected in protocol['config'].items():
        require(key in config and config[key] == expected, f'Retained rehearsal configuration differs: {key}')
    language = config['language']
    require(language.get('backend') == 'ollama' and language.get('endpoint') == expected_endpoint
            and language.get('model') == expected_model == protocol['model']
            and language.get('contextTokens') == protocol['contextTokens'], 'Retained rehearsal language/context differs')
    require(config['outputTokens'] == protocol['maximumOutputTokens']
            and config['requestDeadlineSeconds'] == protocol['requestDeadlineSeconds'], 'Writing-budget declarations disagree')
    require(evidence['attemptCount'] <= protocol['config']['maximumTurns']
            and evidence['manifest']['step'] <= protocol['config']['maximumSteps'], 'Rehearsal exceeded planned attempts/steps')
    require(not any(evidence['eventCounts'].get(kind, 0) for kind in ('retried', 'skipped', 'budgetsExtended')),
            'Episode contains an unplanned retry, skip or budget extension')
    return {'status': 'matched', 'requestedContextTokens': language['contextTokens'],
            'requestedOutputTokens': config['outputTokens'], 'requestedDeadlineSeconds': config['requestDeadlineSeconds'],
            'maximumAttempts': protocol['config']['maximumTurns'],
            'remainingAttemptBudget': protocol['config']['maximumTurns'] - evidence['attemptCount'],
            'noRetriesOrSkips': True,
            'limit': 'Matching retained configuration is not independent proof of provider execution, complete context processing, or creative quality.'}


def collect_history(bundle, manifest):
    """Inspect exact byte anchors and bounded candidate history; no simulation."""
    previous_hash = None
    final = None
    events, languages, candidates, observations = [], {}, {}, {}
    count = manifest['segmentCount']
    require(type(count) is int and 0 <= count <= MAX_FILES, 'Invalid inspection segment count')
    require(len(list((bundle / 'segments').glob('*.json'))) == count, 'Extra or missing segment file')
    for number in range(1, count + 1):
        path = bundle / 'segments' / f'segment-{number:08}.json'
        raw = data(path)
        envelope = read(path)
        segment = envelope['segment']
        require(envelope['sequence'] == number and envelope['previousSha256'] == previous_hash,
                'Segment byte-hash predecessor differs')
        if final is None:
            require(segment['initialCheckpoint']['state']['step'] == 0, 'Missing genesis boundary')
        else:
            require(exact(final, segment['initialCheckpoint']), 'Segment checkpoint continuity differs')
        for cp in (segment['initialCheckpoint'], segment['finalCheckpoint']):
            state = cp['state']
            observation = state['lastObservation']
            if observation is not None:
                step = observation['step']
                require(step not in observations or exact(observations[step], observation),
                        'Same reached observation changed')
                observations[step] = observation
            phase = state['phase']
            p = phase.get('value') if phase['kind'] == 'language' else (
                phase['value']['pending'] if phase['kind'] == 'blocked' else None)
            if p is not None:
                p = {k: v for k, v in p.items() if k != 'requestStarted'}
                attempt = p['attemptId']
                require(attempt not in languages or exact(languages[attempt], p),
                        'Same prepared language opportunity changed')
                languages[attempt] = p
            if phase['kind'] == 'journal':
                p = phase['value']
                attempt = p['entry']['attemptId']
                require(attempt not in candidates or exact(candidates[attempt], p),
                        'Same pending journal changed')
                candidates[attempt] = p
        for journal_id, expected in envelope['journalSha256s'].items():
            require(re.fullmatch(r'[A-Za-z0-9_-]+', journal_id), 'Unsafe anchored journal ID')
            require(digest(data(bundle / 'journals' / f'{journal_id}.json')) == expected,
                    'Anchored journal bytes differ')
        events.extend(segment['events'])
        previous_hash = digest(raw)
        final = segment['finalCheckpoint']
    require(re.fullmatch(r'[0-9a-f]{64}', manifest['checkpointSha256']), 'Invalid final checkpoint hash')
    checkpoint_path = bundle / 'checkpoints' / f"{manifest['checkpointSha256']}.json"
    checkpoint = read(checkpoint_path)
    require(digest(data(checkpoint_path)) == manifest['checkpointSha256']
            and previous_hash == manifest['lastSegmentSha256'], 'Manifest byte anchors differ')
    require(exact(checkpoint, final) if final is not None else checkpoint['state']['step'] == 0,
            'Final checkpoint differs from retained history')
    require([e['id'] for e in events] == list(range(1, len(events) + 1)),
            'Event IDs are not contiguous from genesis')
    return events, languages, candidates, observations, checkpoint


def continuity_summary(evidence):
    """A valid partial run remains partial; twelve slots are not twelve subjects."""
    started = evidence['startedAttemptEvents']
    responses = evidence['receivedResponses']
    journals = evidence['journals']
    start_ids = [e['kind']['data']['attempt_id'] for e in started]
    response_ids = [r['attemptId'] for r in responses]
    journal_ids = [j['attemptId'] for j in journals]
    for name, values in [('dispatch', start_ids), ('response', response_ids), ('journal', journal_ids)]:
        require(len(values) == len(set(values)) and all(type(v) is int and 1 <= v <= PLANNED_SLOTS for v in values),
                f'Duplicate or out-of-scope {name} attempt')
    require(start_ids == list(range(1, len(start_ids) + 1)), 'Dispatch sequence is not an initial ordered prefix')
    require(response_ids == list(range(1, len(response_ids) + 1)), 'Response sequence is not an initial ordered prefix')
    require(journal_ids == list(range(1, len(journal_ids) + 1)), 'Saved journal sequence is not an initial ordered prefix')
    require(not any(evidence['eventCounts'].get(k, 0) for k in ('retried', 'skipped', 'budgetsExtended')),
            'Unplanned retry, skip or budget extension')
    slots = []
    for slot in range(1, PLANNED_SLOTS + 1):
        step = slot * PLANNED_CADENCE
        dispatch = next((e for e in started if e['kind']['data']['attempt_id'] == slot), None)
        response = next((r for r in responses if r['attemptId'] == slot), None)
        journal = next((j for j in journals if j['attemptId'] == slot), None)
        require(dispatch is None or dispatch['step'] == step, 'Dispatch occurs outside its planned observation')
        require(response is None or (response['observedStep'] == step and dispatch is not None),
                'Response differs from planned dispatched opportunity')
        require(journal is None or (journal['observedStep'] == step and response is not None
                                   and response['response']['complete'] is True),
                'Saved journal lacks its complete planned response')
        application = journal['application'] if journal else None
        require(application is None or application['appliedStep'] == step + 1,
                'Application differs from planned next step')
        non_success = [e for e in evidence['nonSuccessEvents'] if e['step'] == step]
        stage = ('applied' if application else 'savedPendingApplication' if journal else
                 'receivedCompleteUnsaved' if response and response['response']['complete'] else
                 'receivedIncomplete' if response else 'requestStartedNoResponse' if dispatch else
                 'reachedUndispatched' if evidence['manifest']['step'] >= step else 'notReached')
        slots.append({'slot': slot, 'plannedObservedStep': step, 'plannedApplicationStep': step + 1,
                      'reached': evidence['manifest']['step'] >= step,
                      'attempted': dispatch is not None, 'responseReceived': response is not None,
                      'complete': response['response']['complete'] if response else None,
                      'saved': journal is not None, 'applied': application is not None,
                      'unstarted': dispatch is None, 'stage': stage,
                      'journalId': journal['journalId'] if journal else None,
                      'nonSuccessEvents': non_success})
    complete = all(s['applied'] for s in slots) and evidence['manifest']['step'] == PLANNED_STEPS
    return {'plannedOpportunities': PLANNED_SLOTS,
            'outcome': 'complete' if complete else 'unstarted' if not started else 'partial',
            'fullTwelveEntryContinuityWitnessed': complete,
            'totals': {key: sum(s[key] is True for s in slots) for key in
                       ('reached', 'attempted', 'responseReceived', 'complete', 'saved', 'applied', 'unstarted')},
            'exactLatestAppliedMemoryJoins': sum(j['memoryJournalId'] is not None for j in journals),
            'slots': slots,
            'limit': 'Integrity may pass for a valid partial or unstarted export. Saved text, applied feedback, supplied prior text and appropriate prose use are separate outcomes.'}


def inspect_evidence(bundle, expected_model, expected_endpoint, expected_prompt_version):
    require(expected_prompt_version == PROMPT_VERSION, 'This twelve-entry episode qualifies v8 only')
    manifest = read(bundle / 'manifest.json')
    version = prompt_version(manifest, expected_prompt_version)
    require(manifest['step'] <= 1000 and manifest['journalCount'] <= 16,
            'Export exceeds this prospective short-run inspection scope')
    language = manifest['config']['language']
    require(language['backend'] == 'ollama' and language['model'] == expected_model
            and language['endpoint'] == expected_endpoint, 'Export source differs from explicitly supplied real-model configuration')
    events, prepared, candidates, observations, checkpoint = collect_history(bundle, manifest)
    compact_contexts = {attempt: inspect_compact_prompt(pending) for attempt, pending in prepared.items()}
    by_kind = lambda kind: [event for event in events if event['kind']['type'] == kind]
    frame_events = by_kind('advanced')
    require([e['step'] for e in frame_events] == list(range(1, manifest['step'] + 1)),
            'Numerical frames are not a contiguous retained prefix')
    frames = {event['step']: event['kind']['data'] for event in frame_events}
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
    require(len(list((bundle / 'journals').glob('*.json'))) == len(journals),
            'Unexpected journal object outside committed saves')
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
        require(response['tokenCount'] is None or (type(response['tokenCount']) is int
                and 0 <= response['tokenCount'] <= manifest['config'].get('outputTokens', 256)),
                'Saved response token count exceeds its retained output budget')
        require(response['providerModel'] in (None, expected_model), 'Returned identity differs from configured model')
        accepted = [event for event in received if event['kind']['data']['attempt_id'] == attempt]
        dispatched = [event for event in started if event['kind']['data']['attempt_id'] == attempt]
        require(len(accepted) == len(dispatched) == 1 and exact(accepted[0]['kind']['data']['response'], response),
                'Journal lacks one matching retained dispatch/response')
        require(attempt in candidates and exact(candidates[attempt], pending),
                'Journal differs from its retained pending candidate')
        require(attempt in prepared and pending['prompt'] == prepared[attempt]['prompt']
                and exact(pending['memory'], prepared[attempt]['memory'])
                and exact(pending['observation'], prepared[attempt]['observation']),
                'Journal differs from prepared prompt, memory or observation')
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
        memory_encoding = inspect_prompt_memory(pending['prompt'], previous, version, pending['observation'], pending['memory'])
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
               'providerPromptEvaluation': provider_evidence(response),
               'memoryJournalId': latest, 'promptVersion': version, 'memoryEncoding': memory_encoding,
               'compactContext': compact_contexts[attempt],
               'contextEvidence': context_evidence(pending['prompt'], memory, manifest['config'], response), 'hostTiming': timing, 'allHostTimestampsRetained': all(value is not None for value in stamps)}
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
        require(dispatches[0]['id'] < event['id'] and attempt in prepared,
                'Received response lacks an earlier prepared dispatch')
        p = prepared[attempt]
        require(p['observedStep'] == event['step'] and p['configuration'] == language,
                'Response opportunity/configuration differs from prepared request')
        latest = max((entry_id for entry_id, application in applications.items()
                      if application['appliedStep'] <= event['step']),
                     key=lambda entry_id: applications[entry_id]['appliedStep'], default=None)
        previous = journals[latest]['pending']['entry'] if latest else None
        expected_memory = ({'entry': previous, 'relativePath': f'journals/{latest}.json',
                            'appliedStep': applications[latest]['appliedStep']} if latest else None)
        require(exact(p['memory'], expected_memory), 'Received attempt memory is not the latest applied full text')
        confirmations = [e for e in by_kind('memoryConfirmed') if e['step'] == event['step']]
        require((not confirmations) if latest is None else (
            len(confirmations) == 1 and exact(confirmations[0]['kind']['data'], previous)
            and confirmations[0]['id'] < dispatches[0]['id']),
            'Received attempt lacks its unique earlier memory read confirmation')
        encoding = inspect_prompt_memory(p['prompt'], previous, version, p['observation'], p['memory'])
        require(type(response['complete']) is bool, 'Response completion is not Boolean')
        require(response['complete'] is True or not matches, 'Incomplete response produced a saved journal')
        received_rows.append({'eventId': event['id'], 'attemptId': attempt, 'observedStep': event['step'],
                              'dispatchEventId': dispatches[0]['id'],
                              'savedJournalId': matches[0]['journalId'] if matches else None,
                              'promptSha256': digest(p['prompt'].encode()),
                              'exactPrompt': p['prompt'], 'observation': p['observation'],
                              'memory': p['memory'], 'memoryEncoding': encoding,
                              'compactContext': compact_contexts[attempt],
                              'contextEvidence': context_evidence(p['prompt'], p['memory'], manifest['config'], response),
                              'response': {'text': response['text'],
                                           'textTruncated': False, 'textByteCount': len(raw),
                                           'textSha256': digest(raw), 'providerModel': response['providerModel'],
                                           'stopReason': response['stopReason'], 'tokenCount': response['tokenCount'],
                                           'providerPromptEvaluation': provider_evidence(response),
                                           'complete': response['complete']}})
    phase = checkpoint['state']['phase']
    final_pending = phase.get('value') if isinstance(phase, dict) and phase.get('kind') == 'language' else (phase.get('value', {}).get('pending') if isinstance(phase, dict) and phase.get('kind') == 'blocked' else None)
    pending_context = context_evidence(final_pending['prompt'], final_pending.get('memory'), manifest['config']) if final_pending is not None else None
    prior = None
    prior_rows = []
    for step, observation in sorted(observations.items()):
        require(observation['version'] == 'reservoir-and-sensory-v2', 'Observation version differs from v8 retained context')
        require(step in frames and exact(observation['state'], frames[step]['state'])
                and exact(observation['sensory'], frames[step]['sensory']), 'Reached observation differs from frame')
        require(observation['previousObservationStep'] == (prior['step'] if prior else None),
                'Prior reached observation identity differs')
        expected_prior = scalar_snapshot(prior) if prior else None
        require(exact(observation.get('previousMeasurements'), expected_prior),
                'Prior scalar reference differs from preceding reached observation')
        prior_rows.append({'currentStep': step, 'previousStep': prior['step'] if prior else None,
                           'priorSnapshotMatches': True})
        prior = observation
    evidence = {'manifest': manifest, 'finalPendingContextEvidence': pending_context, 'eventCounts': dict(collections.Counter(event['kind']['type'] for event in events)),
            'journals': rows, 'receivedResponses': received_rows, 'startedAttemptEvents': started,
            'priorMeasurementJoins': prior_rows,
            'preparedPromptChecks': [{'attemptId': attempt, **compact_contexts[attempt]} for attempt in sorted(compact_contexts)],
            'finalCorePhase': checkpoint['state']['phase'],
            'attemptCount': checkpoint['state']['attemptCursor'], 'turnCount': checkpoint['state']['turnCursor'],
            'nonSuccessEvents': [event for event in events if event['kind']['type'] in
                                 ('languageFailed', 'languageCancelled', 'memoryFailed', 'interrupted', 'skipped')],
            'loopApplicationWitnessed': bool(applications), 'fullTextMemoryWitnessed': any(row['memoryJournalId'] for row in rows),
            'qualityReviewStatus': 'Not assessed by this integrity script; review exact prose and prompts separately.'}
    evidence['continuity'] = continuity_summary(evidence)
    return evidence, material


def scalar_snapshot(observation):
    sensory = observation['sensory']
    return {'step': observation['step'], 'simulatedTime': observation['simulatedTime'],
            'rms': observation['rms'], 'l2': observation['l2'],
            'leadingSensoryEigenvalue': sensory['eigenvalues'][0],
            'fillPercent': sensory['fillPercent'], 'headShare': sensory['headShare'],
            'shoulderShare': sensory['shoulderShare'], 'tailShare': sensory['tailShare'],
            'entropy': sensory['entropy']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--executable', required=True, type=Path)
    parser.add_argument('--expected-executable-sha256', required=True)
    parser.add_argument('--expected-model', required=True)
    parser.add_argument('--expected-prompt-version', required=True, choices=PROMPT_VERSIONS)
    parser.add_argument('--protocol', required=True, type=Path)
    parser.add_argument('--expected-endpoint', required=True)
    parser.add_argument('--output-directory', required=True, type=Path)
    args = parser.parse_args()
    require(re.fullmatch(r'[0-9a-f]{64}', args.expected_executable_sha256), 'Supply an exact expected package SHA-256')
    require(re.fullmatch(r'http://127\.0\.0\.1:[1-9][0-9]{0,4}', args.expected_endpoint)
            and int(args.expected_endpoint.rsplit(':', 1)[1]) <= 65535, 'Supply the explicit owned loopback endpoint; no default discovery')
    for path in (args.bundle, args.executable, args.output_directory, args.protocol):
        require(path.is_absolute() and '..' not in path.parts, 'Supply absolute paths without parent traversal')
    require(not args.output_directory.is_relative_to(args.bundle) and not args.bundle.is_relative_to(args.output_directory),
            'Output must be separate from the original export')
    ordinary_path(args.output_directory.parent, directory=True)
    args.output_directory.mkdir(mode=0o700)
    output = args.output_directory
    receipt = {'schema': 'reservoir-real-model-export-check-v8', 'startedAtUtc': utc(), 'status': 'failed',
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
        require(result.returncode == 0 and verified.get('status') == 'passed'
                and verified.get('modelsContacted') is False, 'Native model-free whole-bundle replay did not pass')
        evidence, material = inspect_evidence(args.bundle, args.expected_model, args.expected_endpoint, args.expected_prompt_version)
        receipt['evidence'] = evidence
        receipt['protocol'] = identity(args.protocol)
        receipt['rehearsal'] = validate_rehearsal(evidence, read(args.protocol), args.expected_model, args.expected_endpoint, args.expected_prompt_version)
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
