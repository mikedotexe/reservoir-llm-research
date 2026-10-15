#!/usr/bin/env python3
"""Offline, deliberately partial journal transcription checks and review aids.

An exit status of zero means the report was produced, never that the prose is
scientifically correct. No network, provider, runtime or UI calls are made.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
from decimal import Decimal, InvalidOperation
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import stat

SCHEMA = 'reservoir-journal-quality-review-v1'
RULESET = 'open-writing-review-3'
MAX_BYTES = 16 * 1024 * 1024
MAX_TEXT = 65536
MAX_CLAIMS_PER_KIND = 32
MAX_CLAUSE = 512
MAX_NUMERIC_MENTIONS = 128
PROMPT_VERSIONS = ('reservoir-journal-v1', 'reservoir-journal-v2', 'reservoir-journal-v3', 'reservoir-journal-v4', 'reservoir-journal-v5', 'reservoir-journal-v6')
NUMBER = r'[-+−]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d{1,3})?'
# A bounded label-to-number candidate, never a claim to parse arbitrary prose.
# Periods/semicolons/questions/newlines and another metric label stop association.
SUFFIX = (r'(?P<bridge>[ \tA-Za-z’\'…,:=()—–-]{0,96}?)(?P<number>' + NUMBER
          + r')(?!\w|\.\d)(?P<percent>\s*(?:%|percent\b))?')
LABELS = {
    'rms': r'\b(?:recurrent (?:reservoir )?)?RMS',
    'fillPercent': r'\b(?:(?:separate )?(?:reduced )?(?:sensory |active-mode ))?fill(?: percent(?:age)?)?',
    'leadingEigenvalue': r'\b(?:sensory (?:leading|top|largest) (?:covariance )?eigenvalue|(?:leading|top|largest) (?:sensory )?(?:covariance )?eigenvalue|dominant (?:sensory )?mode(?:\s*\(\s*eigenvalue)?|eigenvalue)',
    'headSharePercent': r'\b(?:sensory )?head share',
    'shoulderSharePercent': r'\b(?:sensory )?shoulder share',
    'tailSharePercent': r'\b(?:sensory )?tail share',
    'entropy': r'\b(?:top-eight (?:sensory )?)?(?:normalized )?entropy',
    'l2': r'(?<!state-change )\bL2(?!\s+(?:change|distance))',
    'changeL2': r'\b(?:(?:recurrent )?state-coordinate L2 distance|state-change L2|L2 distance|L2 change(?: since previous observation)?|changeL2)',
}
PATTERNS = {key: re.compile(label + SUFFIX, re.I) for key, label in LABELS.items()}
LABEL_PATTERNS = {key: re.compile(label, re.I) for key, label in LABELS.items()}
PERCENT_METRICS = {'fillPercent', 'headSharePercent', 'shoulderSharePercent', 'tailSharePercent'}
PLAIN_BRIDGE_WORDS = frozenset(('is of at remains was around approximately about roughly relatively low high '
                              'now still clinging to that the stubbornly currently measured reads reading '
                              'value equals stayed stays has reached sits a an just though norm').split())
DIGIT_MENTION = re.compile(r'(?<![\w.])' + NUMBER + r'(?!\w|\.\d)(?:\s*(?:%|percent\b))?', re.I)
NUMBER_WORD = r'(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)'
WORD_PERCENT = re.compile(r'\b' + NUMBER_WORD + r'(?:[ -]' + NUMBER_WORD + r'){0,3}\s+percent\b', re.I)
QUOTED = re.compile(r'"(?:\\.|[^"\\])*"|“[^”]*”|‘[^’]*’|(?<!\w)\x27[^\x27\n]+\x27')
LOCAL_SPLIT = re.compile(r'[,;]|\b(?:but|whereas|while)\b', re.I)
DIRECTIONS = {'increase': r'\b(?:grow(?:s|ing)?|grew|ris(?:e|es|ing)|rose|increas\w*|expand\w*|creep\w*)\b',
              'decrease': r'\b(?:fall(?:s|ing)?|fell|decreas\w*|declin\w*|shrink\w*|shrank|drop\w*)\b',
              'unchanged': r'\b(?:unchanged|constant|remains|stays|stable|fixed)\b'}
STEP = re.compile(r'\b(?P<label>current step|global step|observation|step)\s*(?:is\s+|of\s+|[=:]\s*)?(?P<number>\d+)\b', re.I)
EXACT_OPENING = re.compile(r'^Step (?P<number>\d+)\.')
HISTORY = re.compile(r'\b(?:previous|prior|earlier|memory|historical|formerly|was|reported|quoted)\b', re.I)
QUALIFIED = re.compile(r"\b(?:not|no|never|cannot|can't|isn't|incorrect|wrong|rather than|next|future|will|would|could|if|hypothesis|hypothetical)\b", re.I)
INFERENCE_CUES = {
    'stability_or_convergence': r'\b(?:stable|stability|converg\w*)\b',
    'uniform_spectrum': r'\b(?:uniform\w*|all 32 modes|consistent eigenvalue\w*)\b',
    'eigenvectors_or_spatial_semantics': r'\b(?:eigenvector\w*|spatial|sensory exploration)\b',
    'learning_or_intent': r'\b(?:learn\w*|train\w*|deliberat\w*|intend\w*|conscious\w*)\b',
    'causality': r'\b(?:caus\w*|because|due to|led to|resulted in)\b',
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def bounded_json(path: Path):
    if not stat.S_ISREG(path.lstat().st_mode) or path.stat().st_size > MAX_BYTES:
        raise ValueError(f'Expected ordinary bounded JSON file: {path}')
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError('JSON input exceeded bound')
    value = json.loads(raw, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f'Nonfinite JSON: {token}')))
    return value, {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': sha(raw)}


def context(text: str, start: int, end: int):
    """A local clause, not a claim to understand arbitrary discourse or quotes."""
    boundaries = list(re.finditer(r'(?<=[.!?;])\s+|\n', text))
    left = max((m.end() for m in boundaries if m.end() <= start), default=0)
    right = min((m.start() for m in boundaries if m.start() >= end), default=len(text))
    return text[left:right], left, right


def claim_scope(text: str, start: int, end: int):
    clause, _, _ = context(text, start, end)
    if any(match.start() <= start < match.end() or match.start() < end <= match.end() for match in QUOTED.finditer(text)):
        return 'quoted_scope_review', clause
    # Scope each mention locally so an earlier "was" does not silently mark a
    # later "now" claim as historical. Ambiguous compound sentences stay review.
    _, left, right = context(text, start, end)
    splits = list(LOCAL_SPLIT.finditer(text, left, right))
    local_left = max((m.end() for m in splits if m.end() <= end), default=left)
    local_right = min((m.start() for m in splits if m.start() >= end), default=right)
    local = text[local_left:local_right]
    # A trailing correction can qualify the value across a comma. Stop before
    # the next explicit metric so its separate negation is not borrowed.
    trailing = text[local_right:min(right, local_right + MAX_CLAUSE)]
    next_metrics = [p.search(trailing) for p in LABEL_PATTERNS.values()]
    trailing = trailing[:min((m.start() for m in next_metrics if m), default=len(trailing))]
    if ('?' in clause or QUALIFIED.search(local)
            or QUALIFIED.search(trailing)
            or re.search(r'\b(?:if|would|could|suppose|recall\w*|imagin\w*|fiction\w*|pretend\w*|metaphor\w*)\b', clause, re.I)):
        return 'qualified_or_hypothetical_review', clause
    if HISTORY.search(local):
        return 'historical_scope_review', clause
    return 'current_candidate', clause


def rounding_agrees(token: str, expected: float):
    """Precision of the written token plus eight-decimal prompt tolerance."""
    try:
        written = Decimal(token.replace('−', '-'))
    except InvalidOperation as error:
        raise ValueError('Invalid numeric token') from error
    if not written.is_finite() or not math.isfinite(expected):
        raise ValueError('Nonfinite measurement')
    exponent = written.as_tuple().exponent
    if not -16 <= exponent <= 16:
        return None, None
    tolerance = Decimal(5).scaleb(exponent - 1) + Decimal('0.00000001')
    return abs(written - Decimal(str(expected))) <= tolerance, str(tolerance)


def expected_values(observation):
    sensory = observation['sensory']
    values = {'rms': observation['rms'], 'fillPercent': sensory['fillPercent'],
              'leadingEigenvalue': sensory['eigenvalues'][0], 'headSharePercent': sensory['headShare'] * 100,
              'shoulderSharePercent': sensory.get('shoulderShare') * 100 if sensory.get('shoulderShare') is not None else None,
              'tailSharePercent': sensory.get('tailShare') * 100 if sensory.get('tailShare') is not None else None,
              'entropy': sensory['entropy'], 'l2': observation['l2'], 'changeL2': observation['changeL2']}
    if any(value is not None and (type(value) not in (float, int) or not math.isfinite(value)) for value in values.values()):
        raise ValueError('Nonfinite or nonnumeric source measurement')
    return values


def metric_claims(text: str, observation):
    expected = expected_values(observation)
    claims = []
    for metric, pattern in PATTERNS.items():
        for label_match in itertools.islice(LABEL_PATTERNS[metric].finditer(text), MAX_CLAIMS_PER_KIND):
            match = pattern.match(text, label_match.start())
            if match is None:
                continue
            bridge = match.group('bridge')
            if any(p.search(bridge) for p in LABEL_PATTERNS.values()):
                continue
            scope, clause = claim_scope(text, match.start(), match.end())
            token = match.group('number')
            value = expected[metric]
            status = 'scope_requires_review'
            unit_known = bool(match.group('percent')) == (metric in PERCENT_METRICS)
            association_review = any(word.lower() not in PLAIN_BRIDGE_WORDS for word in re.findall(r'[A-Za-z]+', bridge))
            bare_eigenvalue = metric == 'leadingEigenvalue' and match.group().lower().startswith('eigenvalue')
            if bare_eigenvalue:
                value = None  # A rank-unspecified eigenvalue is not the leading value.
            agreement, tolerance = (None, None) if value is None else rounding_agrees(token, value)
            if not unit_known:
                status = 'unit_requires_review'
            elif bare_eigenvalue:
                status = 'measurement_identity_requires_review'
            elif association_review and scope == 'current_candidate':
                status = 'association_requires_review'
            elif scope == 'current_candidate':
                status = 'source_unavailable' if value is None else 'precision_requires_review' if agreement is None else 'consistent_at_written_precision' if agreement else 'numeric_mismatch'
            claims.append({'metric': metric, 'span': [match.start(), match.end()], 'text': match.group(),
                           'numberSpan': list(match.span('number')), 'associationRequiresReview': association_review,
                           'token': token, 'unit': 'percent' if match.group('percent') else 'scalar_or_unspecified',
                           'scope': scope, 'clause': clause[:MAX_CLAUSE], 'clauseTruncated': len(clause) > MAX_CLAUSE,
                           'expectedCurrent': value, 'roundingTolerance': tolerance,
                           'agreesWithCurrentAtWrittenPrecision': agreement, 'status': status})
    return sorted(claims, key=lambda claim: claim['span'])


def previous_values(observation):
    previous = observation.get('previousMeasurements')
    if previous is None:
        return None, None
    if (type(previous.get('step')) is not int or not 0 <= previous['step'] < observation['step']
            or previous['step'] != observation.get('previousObservationStep')):
        raise ValueError('Previous measurement step must match the earlier reached observation')
    mapping = {'rms': 'rms', 'l2': 'l2', 'leadingEigenvalue': 'leadingSensoryEigenvalue',
               'fillPercent': 'fillPercent', 'headSharePercent': 'headShare',
               'shoulderSharePercent': 'shoulderShare', 'tailSharePercent': 'tailShare', 'entropy': 'entropy'}
    values = {}
    for metric, key in mapping.items():
        value = previous[key]
        if type(value) not in (float, int) or not math.isfinite(value):
            raise ValueError('Previous measurement must be finite numeric evidence')
        values[metric] = value * 100 if key in ('headShare', 'shoulderShare', 'tailShare') else value
    return previous['step'], values


def direction_cues(text, observation):
    current = expected_values(observation)
    prior_step, prior = previous_values(observation)
    cues = []
    for metric, label in LABEL_PATTERNS.items():
        for match in itertools.islice(label.finditer(text), MAX_CLAIMS_PER_KIND):
            clause, _, end = context(text, match.start(), match.end())
            tail = text[match.end():min(end, match.end() + 96)]
            other = [p.search(tail) for p in LABEL_PATTERNS.values()]
            next_label = min((m.start() for m in other if m), default=len(tail))
            tail = tail[:next_label]
            for direction, pattern in DIRECTIONS.items():
                cue = re.search(pattern, tail, re.I)
                if cue and len(cues) < MAX_CLAIMS_PER_KIND:
                    ambiguous_identity = metric == 'leadingEigenvalue' and match.group().lower().startswith('eigenvalue')
                    previous = prior.get(metric) if prior and not ambiguous_identity else None
                    value = current[metric] if not ambiguous_identity else None
                    delta = value - previous if value is not None and previous is not None else None
                    start = match.end() + cue.start(); stop = match.end() + cue.end()
                    scope, _ = claim_scope(text, match.start(), stop)
                    cues.append({'metric': metric, 'span': [match.start(), stop], 'cueSpan': [start, stop],
                                 'text': text[match.start():stop], 'directionCandidate': direction,
                                 'scope': scope, 'currentStep': observation['step'], 'currentValue': value,
                                 'previousObservationStep': prior_step, 'previousValue': previous,
                                 'signedEndpointChange': delta,
                                 'measurementIdentityRequiresReview': ambiguous_identity,
                                 'changeUnit': 'percentage_points' if metric in PERCENT_METRICS else 'scalar',
                                 'referenceSource': 'unavailable_measurement_identity' if ambiguous_identity else 'typed_previousMeasurements' if previous is not None else 'unavailable',
                                 'decision': 'manual_review_only', 'clause': clause[:MAX_CLAUSE],
                                 'limit': 'An endpoint difference does not establish a trajectory, monotonic trend, oscillation, stability or cause. Prior prose/journal identity is not substituted for a previous observation.'})
    return sorted(cues, key=lambda cue: cue['span'])


def numeric_inventory(text, claims, steps):
    mentions = {m.span(): {'text': m.group(), 'form': 'digits'} for m in DIGIT_MENTION.finditer(text)}
    mentions.update({m.span(): {'text': m.group(), 'form': 'word_percent_unparsed'} for m in WORD_PERCENT.finditer(text)})
    # Label-adjacent forms such as RMS0.8 are present even though the generic
    # numeral inventory excludes digits embedded in arbitrary identifiers.
    for claim in claims:
        span = tuple(claim['numberSpan'])
        if not any(a <= span[0] and b >= span[1] for a, b in mentions):
            mentions[span] = {'text': text[span[0]:span[1]], 'form': 'digits'}
    rows = []
    for (start, end), item in sorted(mentions.items())[:MAX_NUMERIC_MENTIONS]:
        linked = [i for i, c in enumerate(claims) if c['span'][0] <= start and c['span'][1] >= end]
        linked_steps = [i for i, c in enumerate(steps) if c['span'][0] <= start and c['span'][1] >= end]
        scope, clause = claim_scope(text, start, end)
        rows.append({**item, 'span': [start, end], 'metricCandidateIndices': linked,
                     'stepCandidateIndices': linked_steps, 'scope': scope,
                     'status': 'associated_candidate_review' if linked or linked_steps else 'unmatched_mention_review',
                     'clause': clause[:MAX_CLAUSE], 'clauseTruncated': len(clause) > MAX_CLAUSE})
    return {'mentions': rows, 'totalRecognizedMentions': len(mentions), 'truncated': len(mentions) > MAX_NUMERIC_MENTIONS,
            'limit': 'Bounded partial lexical inventory, not all numbers or all factual claims. Word-percent phrases are visible but not numerically interpreted; tone/frequency and other ambiguous quantities are not silently mapped to eigenvalues.'}


def step_claims(text: str, current: int):
    rows = []
    for match in itertools.islice(STEP.finditer(text), MAX_CLAIMS_PER_KIND):
        scope, clause = claim_scope(text, match.start(), match.end())
        number = int(match.group('number'))
        rows.append({'span': [match.start(), match.end()], 'text': match.group(), 'value': number,
                     'expectedCurrent': current, 'scope': scope, 'clause': clause[:MAX_CLAUSE], 'clauseTruncated': len(clause) > MAX_CLAUSE,
                     'status': ('consistent_current_label' if number == current else 'current_step_mismatch')
                     if scope == 'current_candidate' else 'scope_requires_review'})
    return rows


def evaluate_journal(journal, *, prompt_version):
    if prompt_version not in PROMPT_VERSIONS:
        raise ValueError('Unknown prompt version')
    text = journal['journalText']
    if not isinstance(text, str) or len(text.encode()) > MAX_TEXT:
        raise ValueError('Journal text exceeded bound')
    observation = journal['observation']
    if type(observation['step']) is not int or not 0 <= observation['step'] <= 1000000:
        raise ValueError('Invalid observation step')
    claims = metric_claims(text, observation)
    steps = step_claims(text, observation['step'])
    directions = direction_cues(text, observation)
    inventory = numeric_inventory(text, claims, steps)
    memory = journal.get('memory')
    memory_text = memory['entry']['text'] if memory is not None else ''
    if not isinstance(memory_text, str) or len(memory_text.encode()) > MAX_TEXT:
        raise ValueError('Memory text exceeded bound')
    # This checks lexical coincidence only. It does not infer a causal channel.
    prior_claims = metric_claims(memory_text, observation) if memory_text else []
    for claim in claims:
        if claim['status'] == 'numeric_mismatch':
            prior = [p for p in prior_claims if p['metric'] == claim['metric'] and Decimal(p['token'].replace('−', '-')) == Decimal(claim['token'].replace('−', '-'))]
            claim['matchingPriorTextSpans'] = prior[:8]
            claim['matchingPriorSpansTruncated'] = len(prior) > 8
            claim['carryoverCandidate'] = bool(claim['matchingPriorTextSpans'])
    prior_steps = step_claims(memory_text, observation['step'])
    for claim in steps:
        if claim['status'] == 'current_step_mismatch':
            prior = [p for p in prior_steps if p['value'] == claim['value']]
            claim['matchingPriorTextLabels'] = prior[:8]
            claim['matchingPriorLabelsTruncated'] = len(prior) > 8
            claim['carryoverCandidate'] = bool(claim['matchingPriorTextLabels'])
    cues = []
    for category, pattern in INFERENCE_CUES.items():
        for match in itertools.islice(re.finditer(pattern, text, re.I), MAX_CLAIMS_PER_KIND):
            clause, start, end = context(text, match.start(), match.end())
            cues.append({'category': category, 'span': [match.start(), match.end()], 'cue': match.group(),
                         'clauseSpan': [start, end], 'clause': clause[:MAX_CLAUSE], 'clauseTruncated': len(clause) > MAX_CLAUSE, 'decision': 'manual_review_only'})
    opening = EXACT_OPENING.match(text)
    recognized = {claim['metric'] for claim in claims if claim['scope'] == 'current_candidate'}
    required = ['rms', 'fillPercent'] if prompt_version == 'reservoir-journal-v2' else []
    words = re.findall(r"\b[\w]+(?:['’][\w]+)*\b", text)
    preface = bool(re.match(r"\s*(?:Okay\b|Sure\b|Here(?:'|’)s\b|Here is\b)", text, re.I))
    headings = bool(re.search(r'^\s*(?:#{1,6}\s|\*\*.+\*\*\s*$)', text, re.M))
    return {'identity': journal.get('identity'), 'promptVersion': prompt_version,
            'observationStep': observation['step'], 'journalTextSha256': sha(text.encode()),
            'stepClaims': steps, 'metricClaims': claims, 'numericMentionInventory': inventory,
            'metricDirectionCues': directions,
            'coverage': {'requiredCurrentMetrics': required, 'recognizedCurrentMetrics': sorted(recognized),
                         'missingRequiredMetrics': [metric for metric in required if metric not in recognized],
                         'correctExactOpening': bool(opening and int(opening.group('number')) == observation['step']),
                         'exactOpeningRequired': prompt_version == 'reservoir-journal-v2',
                         'limit': 'Recognition is partial; coverage does not establish all assertions were extracted or correct.'},
            'style': {'wordCount': len(words), 'target60To100Words': None if prompt_version in ('reservoir-journal-v3', 'reservoir-journal-v4', 'reservoir-journal-v5', 'reservoir-journal-v6') else 60 <= len(words) <= 100,
                      'assistantPrefaceCandidate': preface, 'markdownHeadingCandidate': headings,
                      'decision': ('Descriptive form observations only; v6 has no required length, heading, metrics, form or topic. No scientific verdict.'
                                   if prompt_version == 'reservoir-journal-v6' else 'Descriptive form observations only; v5 has no required length, heading, metrics, form or topic. No scientific verdict.'
                                   if prompt_version == 'reservoir-journal-v5' else 'Descriptive form observations only; v4 has no required length, heading, metrics, form or topic. No scientific verdict.'
                                   if prompt_version == 'reservoir-journal-v4' else 'Descriptive form observations only; v3 has no required length, heading, metrics, form or topic. No scientific verdict.')},
            'inferenceReviewCues': cues, 'manualWholeTextReviewRequired': True,
            'extractionBound': {'maximumClaimsPerKind': MAX_CLAIMS_PER_KIND,
                                'metricsTruncated': [key for key, pattern in LABEL_PATTERNS.items() if sum(1 for _ in pattern.finditer(text)) > MAX_CLAIMS_PER_KIND],
                                'stepsTruncated': sum(1 for _ in STEP.finditer(text)) > MAX_CLAIMS_PER_KIND,
                                'numericMentionsTruncated': inventory['truncated'],
                                'directionCueLimitReached': len(directions) == MAX_CLAIMS_PER_KIND,
                                'inferenceCuesTruncated': [key for key, pattern in INFERENCE_CUES.items() if sum(1 for _ in re.finditer(pattern, text, re.I)) > MAX_CLAIMS_PER_KIND],
                                'maximumClauseCharacters': MAX_CLAUSE},
            'qualityVerdict': 'not_assigned',
            'literalClaimReviewRequired': 'A detected span may be a metaphor, hypothetical, quotation or creative form. The reviewer establishes whether it asserts a present fact before treating any mismatch as an error.',
            'manualRubric': {'currentIdentity': None, 'numericTranscription': None, 'memoryAttribution': None,
                             'inferenceAndUncertainty': None, 'readability': None,
                             'unrecognizedAssertions': None, 'evidenceAnnotations': []}}


def evaluate_material(material, *, prompt_version):
    if prompt_version not in PROMPT_VERSIONS:
        raise ValueError('Unknown prompt version')
    journals = material['journals']
    if not isinstance(journals, list) or len(journals) > 16:
        raise ValueError('Expected at most16 short-run journal entries')
    rows = [evaluate_journal(j, prompt_version=prompt_version) for j in journals]
    return {'schema': SCHEMA, 'ruleset': RULESET, 'status': 'analysis_complete_manual_review_required',
            'qualityVerdict': 'not_assigned', 'promptVersion': prompt_version,
            'journalCount': len(rows), 'journals': rows,
            'summary': {'recognizedMetricClaims': sum(len(row['metricClaims']) for row in rows),
                        'recognizedNumericMentions': sum(row['numericMentionInventory']['totalRecognizedMentions'] for row in rows),
                        'unmatchedNumericMentionsShown': sum(sum(m['status'] == 'unmatched_mention_review' for m in row['numericMentionInventory']['mentions']) for row in rows),
                        'directionCuesForManualReview': sum(len(row['metricDirectionCues']) for row in rows),
                        'metricClaimStatuses': dict(collections.Counter(c['status'] for row in rows for c in row['metricClaims'])),
                        'stepClaimStatuses': dict(collections.Counter(c['status'] for row in rows for c in row['stepClaims'])),
                        'entriesMissingRequiredMetrics': sum(bool(row['coverage']['missingRequiredMetrics']) for row in rows),
                        'entriesMissingCorrectRequiredOpening': sum(row['coverage']['exactOpeningRequired'] and not row['coverage']['correctExactOpening'] for row in rows)},
            'limits': ['No global scientific pass or natural-language completeness claim.',
                       'Inferences and ambiguous/current-versus-historical scopes need whole-text review.',
                       'Repeated prior text is a carryover candidate, not a causal attribution.',
                       'No-claim expressive prose need not report metrics. Empty/failed output and absence of numerical claims are distinct outcomes.',
                       'V3/v4/v5/v6 have no mandatory metric, step-heading, length, topic or creative-expression condition.',
                       'An unmatched mention or ambiguous association remains visible; zero recognized claims is not complete coverage or a scientific pass.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--material', required=True, type=Path)
    parser.add_argument('--integrity-receipt', required=True, type=Path)
    parser.add_argument('--prompt-version', required=True, choices=PROMPT_VERSIONS)
    parser.add_argument('--protocol', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    material, material_id = bounded_json(args.material)
    receipt, receipt_id = bounded_json(args.integrity_receipt)
    protocol, protocol_id = bounded_json(args.protocol)
    if receipt.get('status') != 'passed' or receipt.get('originalUnchanged') is not True or receipt.get('reviewMaterial', {}).get('sha256') != material_id['sha256']:
        raise ValueError('Review material must be hash-bound to a passing immutable-export receipt')
    config = receipt['evidence']['manifest']['config']
    actual_version = config.get('promptVersion', 'reservoir-journal-v1')
    if args.prompt_version != actual_version:
        raise ValueError('Requested version differs from retained config (missing means legacyv1)')
    if protocol.get('schema') != 'reservoir-journal-grounding-protocol-v1':
        raise ValueError('Unexpected frozen protocol')
    if protocol.get('promptVersion', args.prompt_version) != args.prompt_version:
        raise ValueError('Frozen protocol differs from selected and retained prompt version')
    report = evaluate_material(material, prompt_version=args.prompt_version)
    report.update({'startedAtUtc': started, 'endedAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(),
                   'modelsContacted': False, 'material': material_id, 'integrityReceipt': receipt_id,
                   'protocol': protocol_id, 'checker': {'path': str(Path(__file__).resolve()), 'sha256': sha(Path(__file__).read_bytes())},
                   'mechanicalOutcome': {'attemptCount': receipt['evidence']['attemptCount'],
                                         'turnCount': receipt['evidence']['turnCount'],
                                         'nonSuccessEvents': receipt['evidence']['nonSuccessEvents'],
                                         'eventCounts': receipt['evidence']['eventCounts'],
                                         'finalCorePhase': receipt['evidence'].get('finalCorePhase'),
                                         'receivedResponses': receipt['evidence'].get('receivedResponses'),
                                         'startedAttemptEvents': receipt['evidence'].get('startedAttemptEvents'),
                                         'responseEvidenceScope': 'Retained attempt outcomes, including unsaved/incomplete replies; null fields mean absent in the historical checker, not zero events. Only saved journals enter the prose rubric.'}})
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=2, allow_nan=False); output.write('\n')
    print(json.dumps({'status': report['status'], 'qualityVerdict': report['qualityVerdict'], 'journalCount': report['journalCount'], 'output': str(args.output)}))


if __name__ == '__main__':
    main()
