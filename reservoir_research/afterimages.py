"""Offline Afterimage accounts from bounded captures, without source reads.

The capture is retained intact. Source declarations, hash checks, temporal context
and unknown links have separate meanings; successful generation is not uptake.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re

from . import store
from .parsing import parse_journal

CAPTURE_SCHEMA = 'afterimage_capture_v1'
REPORT_SCHEMA = 'afterimage_trace_v1'
ID = re.compile(r'ai_\d{4}-\d{2}-\d{2}_[A-Za-z0-9_]+\Z')
KINDS = {'physical_trace', 'trace_updates', 'cue_state', 'exposure', 'opened',
         'association', 'generation', 'job', 'job_prompt', 'job_result', 'journal',
         'action', 'request_policy', 'runtime_manifest', 'delivery_artifact', 'selected_page'}


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def epoch(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, str):
        if re.fullmatch(r'\d{10}(?:\.\d+)?', value):
            return float(value)
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return parsed.timestamp() if parsed.tzinfo else None
        except (ValueError, OverflowError):
            return None
    return None


def wall_time(payload):
    """Only named wall clocks; no conversion of generic engine-relative t_ms."""
    for key in ('recorded_at_unix_ms', 'created_at_unix_ms', 'timestamp_ms',
                'anchor_unix_ms', 'created_at_ms', 'started_at_unix_ms'):
        value = payload.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
            return value / 1000, key
    for key in ('timestamp', 'created_at', 'started_at', 'recorded_at', 'occurred_at'):
        value = epoch(payload.get(key))
        if value is not None:
            return value, key
    return None, 'unknown'


def iso(value):
    if value is None:
        return 'unknown time'
    try:
        return datetime.fromtimestamp(value, timezone.utc).isoformat()
    except (ValueError, OverflowError, OSError):
        return 'unrepresentable time'


def exact_reference(payload, identifier):
    # An exact literal reference is a retrieval lead, not evidence of exposure.
    return bool(re.search(r'(?<![A-Za-z0-9_])' + re.escape(identifier) +
                          r'(?![A-Za-z0-9_])', canonical(payload)))


def decode_source(source, issues):
    content, kind = source['content'], source['kind']
    if kind in ('journal', 'job_prompt', 'job_result'):
        return [('text', {'text': content})]
    try:
        value = json.loads(content, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        if isinstance(value, list):
            for i, row in enumerate(value):
                if not isinstance(row, dict):
                    issues.append({'code': 'invalid_array_member', 'source_id': source['source_id'], 'locator': f'item:{i}'})
            return [(f'item:{i}', row) for i, row in enumerate(value) if isinstance(row, dict)]
        if isinstance(value, dict):
            return [('json', value)]
        raise ValueError('expected object or array')
    except (ValueError, TypeError):
        pass
    result = []
    offset = source.get('byte_offset', 0)
    lines = content.splitlines(keepends=True)
    for number, line in enumerate(lines, 1):
        location = f'line:{number};byte:{offset}'
        offset += len(line.encode('utf-8'))
        if not line.strip():
            continue
        if number == len(lines) and not line.endswith('\n') and not source['complete_file']:
            issues.append({'code': 'partial_line', 'source_id': source['source_id'], 'locator': location})
            continue
        try:
            row = json.loads(line, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
            if not isinstance(row, dict):
                raise ValueError('expected object')
            result.append((location, row))
        except (ValueError, TypeError):
            issues.append({'code': 'malformed_json', 'source_id': source['source_id'], 'locator': location})
    return result


def identities(payload):
    """Top-level machine identities and explicit `source`/`context` declarations.

    Arbitrary prose, nested prompts and example JSON never become join keys.
    """
    result = defaultdict(set)
    names = {'generation_id': 'generation_id', 'job_id': 'job_id', 'llm_job_id': 'job_id',
             'action_id': 'action_id', 'thread_id': 'thread_id', 'opportunity_id': 'opportunity_id',
             'content_id': 'content_id', 'attempt_id': 'attempt_id'}
    nested = payload.get('payload')
    if isinstance(nested, str):
        try:
            nested = json.loads(nested)
        except ValueError:
            nested = None
    for row in [payload, *[payload[key] for key in ('source', 'context') if isinstance(payload.get(key), dict)],
                *([nested] if isinstance(nested, dict) else [])]:
        for name, category in names.items():
            if isinstance(row.get(name), str) and row[name]:
                result[category].add(row[name])
    return {key: sorted(value) for key, value in result.items()}


def validated_capture(capture):
    if not isinstance(capture, dict) or capture.get('schema') != CAPTURE_SCHEMA:
        raise ValueError('Expected afterimage_capture_v1 capture')
    if not isinstance(capture.get('afterimage_id'), str) or not ID.fullmatch(capture['afterimage_id']):
        raise ValueError('Invalid Afterimage ID')
    start, end = epoch(capture.get('since')), epoch(capture.get('until'))
    if start is None or end is None or start >= end:
        raise ValueError('Capture requires an ordered, timezone-aware window')
    if not isinstance(capture.get('sources'), list) or len(capture['sources']) > 10000:
        raise ValueError('Invalid or excessive captured sources')
    sources, seen = [], set()
    for original in capture['sources']:
        if not isinstance(original, dict):
            raise ValueError('Invalid captured source')
        source = deepcopy(original)
        sid, content = source.get('source_id'), source.get('content')
        if not isinstance(sid, str) or not sid or sid in seen:
            raise ValueError('Missing or duplicate source ID')
        seen.add(sid)
        if source.get('kind') not in KINDS or source.get('being') not in ('astrid', 'minime', 'both', 'system'):
            raise ValueError('Unknown source kind or being')
        if not isinstance(source.get('path'), str) or not isinstance(content, str):
            raise ValueError('Captured source requires path and exact UTF-8 content')
        if digest(content) != source.get('sha256'):
            raise ValueError(f'Captured source hash mismatch: {sid}')
        if type(source.get('bytes_read')) is not int or source['bytes_read'] != len(content.encode('utf-8')):
            raise ValueError(f'Captured byte count mismatch: {sid}')
        if type(source.get('byte_offset')) is not int or source['byte_offset'] < 0:
            raise ValueError('Invalid captured byte offset')
        if type(source.get('complete_file')) is not bool or type(source.get('stable')) is not bool:
            raise ValueError('Captured stability/completeness must be explicit')
        source['verified'] = True  # Integrity of retained content, not authenticity of its claims.
        sources.append(source)
    canonical(capture)  # Reject non-finite values and non-JSON metadata before any writes.
    return sources, start, end


def build_afterimage_trace(capture):
    sources, start, end = validated_capture(capture)
    identifier = capture['afterimage_id']
    issues = deepcopy(capture.get('issues', []))
    records, opportunities = [], []

    def add(source, location, kind, payload, forced=False):
        at, time_basis = wall_time(payload)
        relation = 'literal_reference' if exact_reference(payload, identifier) else 'temporal_context'
        if kind == 'physical_trace' and payload.get('id') == identifier:
            relation = 'explicit_identity'
        if payload.get('afterimage_id') == identifier or payload.get('artifact_id') == identifier:
            relation = 'explicit_identity'
        if kind == 'association':
            relation = payload.get('relation') if payload.get('relation') in ('temporal_context', 'authored_reference') else 'source_declared_association'
        parsed = None
        if kind == 'journal':
            parsed = parse_journal(payload['text'], source['being'], PurePosixPath(source['path']).name)
            at, time_basis = parsed['occurred_at'], parsed['time_source']
        if not forced and relation == 'temporal_context' and at is not None and not start <= at < end:
            return
        if at is None and relation == 'temporal_context':
            relation = 'captured_context_unknown_time'
        record = {'id': 'r_' + digest(source['source_id'] + ':' + location)[:24],
                  'source_id': source['source_id'], 'kind': kind, 'being': source['being'],
                  'at': at, 'time_basis': time_basis, 'locator': location, 'relation': relation,
                  'payload': deepcopy(payload), 'identities': identities(payload),
                  'source_stable': source['stable']}
        record['window_role'] = ('unknown_time' if at is None else
                                 'in_window' if start <= at < end else 'outside_window_context')
        # These fields are supplied by the capture's fixed directory/schema adapter,
        # not extracted from a journal or prompt. Keep their weaker basis explicit.
        for key in ('job_id', 'generation_id'):
            if isinstance(source.get(key), str) and source[key]:
                record['identities'].setdefault(key, [])
                if source[key] not in record['identities'][key]:
                    record['identities'][key].append(source[key])
                record.setdefault('capture_declared_context', {})[key] = source[key]
        if parsed:
            record['journal'] = parsed
        records.append(record)
        return record

    for source in sources:
        if not source['stable']:
            issues.append({'code': 'unstable_source', 'source_id': source['source_id'],
                           'message': 'Valid retained records remain inspectable; acceptance cannot rely on this source.'})
        for location, payload in decode_source(source, issues):
            if source['kind'] == 'cue_state':
                candidates = payload.get('opportunities', {})
                if not isinstance(candidates, dict):
                    issues.append({'code': 'invalid_cue_opportunities', 'source_id': source['source_id']})
                    continue
                for key, opportunity in candidates.items():
                    if not isinstance(opportunity, dict):
                        continue
                    selection = opportunity.get('selection')
                    row = {**opportunity, 'opportunity_id': key}
                    if selection and isinstance(selection, dict):
                        row['afterimage_id'] = selection.get('id')
                    record = add(source, location + '.opportunities.' + key, 'cue_opportunity', row)
                    if record:
                        opportunities.append({**deepcopy(row), 'id': record['id'], 'being': source['being'],
                                              'source_id': source['source_id']})
                # The full state remains in sources, but an enabled flag is not an exposure.
                continue
            if source['kind'] == 'physical_trace' and payload.get('id') != identifier:
                issues.append({'code': 'physical_identity_mismatch', 'source_id': source['source_id']})
                continue
            add(source, location, source['kind'], payload, forced=True)
    records.sort(key=lambda row: (row['at'] is None, row['at'] or 0, row['id']))
    links, gaps = [], []
    link_keys = set()

    def link(left, right, basis, meaning, status='supported'):
        key = (left['id'], right['id'], basis, meaning)
        if left['id'] != right['id'] and key not in link_keys:
            link_keys.add(key)
            links.append({'source': left['id'], 'target': right['id'], 'basis': basis,
                          'status': status, 'meaning': meaning})
            return links[-1]

    def gap(code, message, record_ids=()):
        gaps.append({'code': code, 'message': message, 'record_ids': list(record_ids)})

    traces = [row for row in records if row['kind'] == 'physical_trace']
    for row in records:
        if row['kind'] == 'association' and row['payload'].get('afterimage_id') == identifier:
            for trace in traces:
                link(trace, row, row['relation'], 'Producer-labelled association; preserve its original relation.')
            continue
        if row['kind'] != 'physical_trace' and row['relation'] in ('explicit_identity', 'literal_reference'):
            for trace in traces:
                link(trace, row, 'source_declared' if row['relation'] == 'explicit_identity' else 'literal_reference',
                     'Names this physical trace; does not establish that its contents were supplied.')
    by_identity = defaultdict(list)
    for row in records:
        for kind, values in row['identities'].items():
            if kind == 'thread_id':
                continue  # A shared thread alone is too broad for an episode edge.
            for value in values:
                by_identity[(row['being'], kind, value)].append(row)
    for (_, kind, _), members in by_identity.items():
        # A small star avoids quadratic expansion for reused job/action identities.
        for member in members[1:]:
            link(members[0], member, 'source_declared', f'Shared {kind}; producer-declared association only.')

    generations = [row for row in records if row['kind'] == 'generation']
    exposures = []
    for row in records:
        if row['kind'] != 'exposure' or row['payload'].get('afterimage_id') != identifier:
            continue
        payload = row['payload']
        exposure = {**deepcopy(payload), 'id': row['id'], 'source_id': row['source_id'],
                    'acceptance_status': 'unresolved', 'generation_ids': []}
        matching = []
        for generation in generations:
            value = generation['payload']
            if (generation['being'] == row['being'] and payload.get('generation_id')
                    and payload['generation_id'] == value.get('generation_id')
                    and type(payload.get('attempt_index')) is int and payload['attempt_index'] >= 0
                    and type(value.get('attempt_index')) is int and value['attempt_index'] >= 0
                    and payload['attempt_index'] == value.get('attempt_index')):
                matching.append(generation)
                exposure['generation_ids'].append(generation['id'])
                link(row, generation, 'source_declared', 'Same canonical generation and provider attempt.')
        signatures = {canonical(generation['payload']) for generation in matching}
        if len(signatures) > 1:
            gap('ambiguous_generation_attempt', 'Conflicting captured records share the same canonical generation/attempt.',
                [row['id'], *[generation['id'] for generation in matching]])
        for generation in matching:
            value = generation['payload']
            messages = value.get('messages')
            final_match = (value.get('messages_source') == 'adapted' and isinstance(messages, list)
                           and digest(canonical(messages)) == payload.get('final_messages_fingerprint'))
            response = value.get('response_text')
            response_match = isinstance(response, str) and bool(response) and digest(response) == value.get('response_sha256')
            explicitly_accepted = value.get('accepted') is True or value.get('status') == 'accepted'
            known_schema = value.get('schema_version') == 1 and type(value.get('schema_version')) is int
            selected = [opportunity for opportunity in opportunities
                        if opportunity.get('opportunity_id') == payload.get('opportunity_id')
                        and opportunity['being'] == row['being'] and opportunity.get('afterimage_id') == identifier]
            selections = [opportunity.get('selection', {}) for opportunity in selected]
            selected_texts = {item.get('text') for item in selections if isinstance(item.get('text'), str)}
            cue_verified = False
            if len(selected_texts) == 1 and selected:
                cue_text = selected_texts.pop()
                cue_verified = (bool(cue_text) and digest(cue_text) == payload.get('content_fingerprint')
                                and all(item.get('fingerprint') == digest(cue_text) for item in selections)
                                and all(next(source for source in sources if source['source_id'] == item['source_id'])['stable'] for item in selected)
                                and isinstance(messages, list)
                                and any(isinstance(message, dict) and isinstance(message.get('content'), str)
                                        and cue_text in message['content'] for message in messages))
            if final_match:
                link(row, generation, 'verified_hash', 'Canonical adapted-message JSON matches the exposure fingerprint recipe; not a hash of HTTP bytes.')
            if (payload.get('included') is True and final_match and response_match and explicitly_accepted
                    and known_schema and cue_verified and len(signatures) == 1
                    and row['source_stable'] and generation['source_stable']):
                exposure['acceptance_status'] = 'explicit_accepted'
            if payload.get('included') is False and final_match:
                # Accepted generation without the selected cue is not accepted cue exposure.
                exposure['acceptance_status'] = 'contradicted'
        if payload.get('included') is False:
            gap('cue_omitted', 'The receipt declares the complete selected cue absent from prepared messages; retained request verification is separate.', [row['id']])
            if not payload.get('reason'):
                gap('omission_reason_missing', 'The receipt gives no omission reason or measured admission budget.', [row['id']])
        if exposure['acceptance_status'] != 'explicit_accepted':
            gap('accepted_output_unresolved', 'Prepared-request evidence does not identify an accepted cue-bearing output.', [row['id']])
        if not matching:
            gap('generation_link_missing', 'No shared canonical generation/attempt link recovered for this receipt.', [row['id']])
        exposures.append(exposure)

    # Explicit journal references are useful even when exact response matching fails.
    source_by_id = {source['source_id']: source for source in sources}
    journals = [row for row in records if row['kind'] == 'journal']
    for context in [row for row in records if row['kind'] in ('job_prompt', 'job_result', 'generation')]:
        text = context['payload'].get('response_text') if context['kind'] == 'generation' else context['payload'].get('text')
        if not isinstance(text, str):
            continue
        for journal in journals:
            body = journal['journal']['body_text']
            if context['being'] != journal['being'] or len(body) < 80 or body not in text:
                continue
            position = text.index(body)
            edge = link(journal, context, 'exact_text_containment',
                        'Exact cleaned journal body appears in captured ' + context['kind'] +
                        '; text equality alone does not establish authorship, final request exposure or unique identity.')
            if edge:
                edge['evidence'] = {'field': 'response_text' if context['kind'] == 'generation' else 'text',
                                    'start_char': position, 'end_char': position + len(body),
                                    'text_sha256': digest(body), 'occurrences': text.count(body),
                                    'journal_field': 'journal.body_text'}
    for association in [row for row in records if row['kind'] == 'association']:
        declared = association['payload'].get('source')
        if not isinstance(declared, dict):
            continue
        path = declared.get('path') or declared.get('source_ref')
        for journal in journals:
            if journal['being'] == association['being'] and source_by_id[journal['source_id']]['path'] == path:
                link(association, journal, 'source_declared',
                     'Association names this journal path; original relation is ' + association['relation'] + '.')
    for generation in generations:
        value = generation['payload']
        response = value.get('response_text')
        refs = value.get('linked_artifacts', [])
        for journal in journals:
            if generation['being'] != journal['being']:
                continue
            journal_path = source_by_id[journal['source_id']]['path']
            for ref in refs if isinstance(refs, list) else []:
                if isinstance(ref, dict) and ref.get('kind') == 'journal' and ref.get('path') == journal_path:
                    link(generation, journal, 'source_declared',
                         'Generation declares this journal artifact; matching method retained in original payload.')
            if isinstance(response, str) and response and value.get('response_sha256') == digest(response):
                if response == journal['journal']['body_text'] or response == journal['payload']['text']:
                    link(generation, journal, 'verified_hash', 'Exact response text matches captured journal text; not unique authorship proof.')

    if not traces:
        gap('physical_trace_missing', 'The requested physical artifact was not recovered.')
    for trace in traces:
        if trace['payload'].get('status') == 'incomplete':
            gap('physical_coverage_incomplete', 'Physical coverage is incomplete; inspect per-metric reasons before interpretation.', [trace['id']])
    if not exposures:
        gap('no_exposure_record', 'No exposure record for this trace in the declared captured scope; not proof of no exposure.')
    if not any(row['acceptance_status'] == 'explicit_accepted' for row in exposures):
        gap('no_verified_accepted_chain', 'No verified automatic-cue-to-accepted-output chain was recovered in this capture.')
    for opened in [row for row in records if row['kind'] == 'opened' and row['relation'] == 'explicit_identity']:
        gap('opened_receipt_requires_artifact_verification',
            'A runtime opened-page acknowledgement is retained; its request/completion artifact needs independent verification.', [opened['id']])
    counts = Counter(row['kind'] for row in records)
    report = {'schema': REPORT_SCHEMA, 'afterimage_id': identifier,
              'window': {'since': capture['since'], 'until': capture['until']},
              'captured_at_utc': capture.get('captured_at_utc'),
              'capture_sha256': digest(canonical(capture)), 'sources': sources,
              'coverage': deepcopy(capture.get('coverage', [])), 'issues': issues,
              'records': records, 'opportunities': opportunities, 'exposures': exposures,
              'links': links, 'gaps': gaps,
              'reading_view': {'rule': 'Trace-related records and three hops of declared/hash/text links, plus two journals before/after the first receipt per being, request/job context within two seconds and one hop to its declared companion files.',
                               'full_evidence': 'All captured sources and records remain in account.json; the Markdown reading view is a declared subset.'},
              'summary': {'sources': len(sources), 'records': len(records), 'records_by_kind': dict(counts),
                          'in_window_records': sum(row['window_role'] == 'in_window' for row in records),
                          'outside_window_context': sum(row['window_role'] == 'outside_window_context' for row in records),
                          'selected_opportunities': sum(row.get('afterimage_id') == identifier for row in opportunities),
                          'exposure_records': len(exposures),
                          'included_true': sum(row.get('included') is True for row in exposures),
                          'included_false': sum(row.get('included') is False for row in exposures),
                          'explicit_accepted': sum(row['acceptance_status'] == 'explicit_accepted' for row in exposures)},
              'interpretation': 'Recorded availability, preparation, acceptance and later use are distinct. No causal or felt-effect claim.'}
    report['result_sha256'] = digest(canonical(report))
    return report


def quoted(text):
    # Blockquote each source line so untrusted Markdown cannot become report structure.
    return '\n'.join('> ' + line for line in str(text).splitlines()) + '\n'


def table_cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def focal_records(report):
    selected = {row['id'] for row in report['records'] if row['relation'] in ('explicit_identity', 'literal_reference', 'authored_reference')
                or (row['kind'] == 'association' and row['payload'].get('afterimage_id') == report['afterimage_id'])}
    for _ in range(3):
        extra = set()
        for edge in report['links']:
            if edge['basis'] in ('source_declared', 'verified_hash', 'exact_text_containment'):
                if edge['source'] in selected:
                    extra.add(edge['target'])
                if edge['target'] in selected:
                    extra.add(edge['source'])
        selected |= extra
    times = [row.get('recorded_at_unix_ms') for row in report['exposures']]
    times = [value / 1000 for value in times if isinstance(value, (int, float)) and not isinstance(value, bool)]
    if times:
        center = min(times)
        for being in ('astrid', 'minime'):
            journals = [row for row in report['records'] if row['kind'] == 'journal' and row['being'] == being and row['at'] is not None]
            before = sorted([row for row in journals if row['at'] < center], key=lambda row: row['at'])[-2:]
            after = sorted([row for row in journals if row['at'] >= center], key=lambda row: row['at'])[:2]
            selected |= {row['id'] for row in before + after}
        selected |= {row['id'] for row in report['records'] if row['kind'] in ('request_policy', 'job')
                     and row['at'] is not None and abs(row['at'] - center) <= 2}
        # Include fixed companion files for those nearby jobs; the connection of
        # the job to the cue is still explicitly temporal.
        neighbors = set()
        for edge in report['links']:
            if edge['basis'] == 'source_declared':
                if edge['source'] in selected:
                    neighbors.add(edge['target'])
                if edge['target'] in selected:
                    neighbors.add(edge['source'])
        selected |= neighbors
    return selected


def action_fields(value):
    nested = value.get('payload')
    if isinstance(nested, str):
        try:
            nested = json.loads(nested)
        except ValueError:
            nested = None
    merged = {**value, **nested} if isinstance(nested, dict) else value
    return {key: merged[key] for key in ('action_id', 'parent_action_id', 'thread_id', 'llm_job_id',
            'raw_next', 'canonical_action', 'effective_action', 'route', 'status', 'started_at', 'ended_at',
            'suggested_next', 'outcome_summary', 'reason') if key in merged}


def render_afterimage_trace(report):
    summary = report['summary']
    focal = focal_records(report)
    sections = [f"# Afterimage account: {report['afterimage_id']}\n",
                f"Window: {report['window']['since']} → {report['window']['until']} (end exclusive).\n",
                f"Captured: {report['captured_at_utc']}. This account reads retained files only.\n",
                '## What the evidence establishes\n',
                f"{summary['selected_opportunities']} selected opportunities for this trace; "
                f"{summary['exposure_records']} exposure records. Receipts declare included: {summary['included_true']}; "
                f"omitted: {summary['included_false']}. Verified accepted cue-bearing outputs: {summary['explicit_accepted']}.\n",
                'Counts describe this capture. Absence of an output link is an evidence gap, not a conclusion about silence or uptake.\n',
                '## Physical history\n']
    for row in report['records']:
        if row['kind'] != 'physical_trace':
            continue
        value = row['payload']
        coverage = value.get('coverage') or {}
        compact_coverage = {key: val for key, val in coverage.items() if key != 'channels'}
        compact_coverage['channels'] = {name: {**{key: val for key, val in channel.items() if key != 'gaps'},
                                             'gap_count': len(channel.get('gaps', []))}
                                        for name, channel in coverage.get('channels', {}).items()}
        measurements = {key: val for key, val in (value.get('measurements') or {}).items() if key != 'channel_changes'}
        sections += [f"Record `{row['id']}`; source `{row['source_id']}`.\n",
                     quoted(canonical({key: value.get(key) for key in ('id', 'session_id', 'origin', 'status', 'anchor_unix_ms', 'reasons')})),
                     f"{len(value.get('events', []))} retained event identities; {len(value.get('samples', []))} observations. Raw events, channel comparisons and sample intervals remain in account.json.\n",
                     quoted(json.dumps({'coverage': compact_coverage, 'measurements': measurements}, ensure_ascii=False, indent=2))]
    sections.append('## Cue selection and prepared requests\n')
    for row in report['opportunities']:
        if row.get('afterimage_id') != report['afterimage_id']:
            continue
        selection = row.get('selection') or {}
        sections += [f"**{row['being']}**, opportunity `{row['opportunity_id']}`; record `{row['id']}`.\n",
                     quoted(selection.get('text', '(exact cue text unavailable)'))]
    for exposure in report['exposures']:
        sections += [f"Receipt `{exposure['id']}`: included=`{exposure.get('included')}`, "
                     f"outcome=`{exposure.get('outcome')}`, reason=`{exposure.get('reason')}`, "
                     f"acceptance=`{exposure['acceptance_status']}`.\n"]
    sections.append('## Writing, requests and outcomes in the captured window\n')
    sections.append(report['reading_view']['rule'] + ' ' + report['reading_view']['full_evidence'] + '\n')
    sections.append('Each record below is labelled by its connection. Chronological neighbors are context; they are not attributed to the cue. NEXT text is a request until an action record establishes routing and outcome.\n')
    for row in report['records']:
        if row['kind'] not in ('journal', 'generation', 'job', 'job_result', 'action', 'opened', 'association', 'request_policy'):
            continue
        if row['id'] not in focal:
            continue
        sections.append(f"### {row['being']} · {row['kind']} · {iso(row['at'])}\n")
        sections.append(f"Record `{row['id']}`; source `{row['source_id']}`; {row['locator']}; **{row['relation']}**, {row['window_role']}.\n")
        value = row['payload']
        if row['kind'] == 'journal':
            sections.append(quoted(row['journal']['body_text']))
            sections.append('Requested NEXT (research parser): ' + quoted(row['journal']['next_raw'] or '(none found)'))
        elif row['kind'] == 'generation':
            sections.append(quoted(canonical({key: value.get(key) for key in ('generation_id', 'attempt_index', 'lane', 'backend', 'model', 'messages_source', 'status', 'accepted', 'action_id', 'job_id')})))
            sections.append(quoted(value.get('response_text') or '(no response retained)'))
            sections.append('Recorded NEXT: ' + quoted(value.get('next_action_parsed') or value.get('next_action_raw') or '(unavailable)'))
        elif row['kind'] == 'action':
            sections.append(quoted(json.dumps(action_fields(value), ensure_ascii=False, indent=2)))
        elif row['kind'] == 'job':
            compact_job = {key: value[key] for key in ('job_id', 'action_id', 'thread_id', 'event', 'phase', 'call_kind',
                           'status', 'created_at', 'started_at', 'finished_at', 'timestamp', 'timeout_s',
                           'summary', 'error', 'next_policy', 'exposure_record_id') if key in value}
            sections.append(quoted(json.dumps(compact_job, ensure_ascii=False, indent=2)))
            sections.append('Other job fields remain in the captured payload.\n')
        else:
            sections.append(quoted(json.dumps(value, ensure_ascii=False, indent=2)))
    sections += ['## All captured writing and action records\n',
                 'Compact inventory; full text and payloads remain in account.json. Rows outside the window remain explicitly labelled context.\n',
                 '| Time (UTC) | Being / kind | Record | Requested NEXT or recorded action | Status / relation |\n|---|---|---|---|---|\n']
    for row in report['records']:
        if row['kind'] not in ('journal', 'action'):
            continue
        value = action_fields(row['payload']) if row['kind'] == 'action' else row['journal']
        request = value.get('next_raw') if row['kind'] == 'journal' else value.get('raw_next') or value.get('canonical_action')
        sections.append('| ' + ' | '.join(table_cell(v) for v in (iso(row['at']), row['being'] + ' / ' + row['kind'], row['id'],
                         request or '(none recorded)', value.get('status') or row['relation'])) + ' |\n')
    sections += ['## Evidence connections\n', '| From | To | Basis | Meaning |\n|---|---|---|---|\n']
    for edge in report['links']:
        if edge['source'] in focal and edge['target'] in focal:
            sections.append('| ' + ' | '.join(table_cell(edge[key]) for key in ('source', 'target', 'basis', 'meaning')) + ' |\n')
    sections.append('\n## Unresolved links and system opportunities\n')
    for gap in report['gaps']:
        sections.append(f"- **{gap['code']}**: {gap['message']} " + ' '.join(f"`{rid}`" for rid in gap['record_ids']) + '\n')
    compact = [row for row in report['coverage'] if row.get('status') not in ('captured',)]
    sections += ['\n## Capture coverage and issues\n', quoted(json.dumps(compact, ensure_ascii=False, indent=2)),
                 quoted(json.dumps(report['issues'], ensure_ascii=False, indent=2)),
                 '## Source manifest\n',
                 f"All {summary['sources']} source IDs, paths, hashes, capture offsets and exact contents are retained in [account.json](account.json). Source paths are evidence fields and are never opened by this report.\n"]
    sections += ['\n## Reading questions\n',
                 'What was available in the exact supplied source? What does the writing add, revise or leave unresolved? Which later request has a recorded outcome? What alternative context explains the same passage? These questions are for close reading; the report does not score development or comprehension.\n']
    return '\n'.join(sections)


def export_afterimage_trace(report, out):
    expected = report.get('result_sha256')
    copy = {key: value for key, value in report.items() if key != 'result_sha256'}
    if report.get('schema') != REPORT_SCHEMA or digest(canonical(copy)) != expected:
        raise ValueError('Afterimage report digest mismatch')
    # Do not resolve or open source-supplied paths. Compare normalized declarations;
    # known live roots are separately guarded by the repository helper.
    requested = Path(out).expanduser()
    if requested.exists() or requested.is_symlink():
        raise ValueError('Output directory already exists')
    destination = store.guard_output(requested)
    for source in report['sources']:
        declared = source['path']
        if declared.startswith('/'):
            parent = Path(os.path.normpath(declared)).parent
            if destination == parent or parent in destination.parents:
                raise ValueError('Output cannot be inside a captured source directory')
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    created = []
    try:
        for name, content in (('account.json', json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'),
                              ('account.md', render_afterimage_trace(report))):
            path = destination / name
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            created.append(path)
            with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
                stream.write(content)
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        destination.rmdir()
        raise
    return {'json': str(destination / 'account.json'), 'markdown': str(destination / 'account.md'),
            'summary': report['summary'], 'result_sha256': expected}
