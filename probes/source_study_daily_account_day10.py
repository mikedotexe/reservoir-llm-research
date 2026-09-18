#!/usr/bin/env python3
"""Day10 descriptive extension. Reads retained inputs only; does not score writing."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(packet: Path, report_path: Path) -> dict:
    packet, report_path = Path(packet), Path(report_path)
    report = json.loads(report_path.read_text())
    plan_path = packet / 'sample-adjacent-followup-plan.json'
    plan = json.loads(plan_path.read_text())
    rows = report['studies']
    records = []
    for name in ('capture.json', 'supplement.json'):
        records.extend(json.loads((packet / name).read_text())['records'])
    checks = {}
    def require(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise ValueError('day10 descriptive account: ' + name)
    def unique_record(path):
        matches = [r for r in records if r['path'] == path]
        distinct = {r['sha256']: r for r in matches}
        require('unambiguous retained record ' + path, len(distinct) == 1)
        rec = next(iter(distinct.values()))
        require('retained hash ' + path, sha(rec['text'].encode()) == rec['sha256'])
        return rec
    require('unique generation IDs', len({r['id'] for r in rows}) == len(rows))
    require('generation denominator', len(rows) == report['generation_count'])
    selected = report['close_reading_ids']
    require('declared third sample is fixed third selection', selected[2] == plan['fixed_sample3'])
    third = next(r for r in rows if r['id'] == plan['fixed_sample3'])
    later = sorted((r for r in rows if r['actual_route'] == 'source_study' and r['completed'] > third['completed']), key=lambda r: (r['completed'], r['id']))
    require('immediately subsequent retained source-study exists', bool(later))
    following = later[0]
    command = plan['candidate_command']
    require('third authored choice equals declared candidate', third['next_action'] == command and 'NEXT: ' + command in third['text'])
    wire_rec = unique_record(third['receipt_path'])
    wire = json.loads(wire_rec['text'])
    require('previous wire verified', third['receipt_verified'])
    marker = 'PREVIOUS RESPONSE CHOICE'
    text = following['user_text']
    require('single prior choice block', text.count(marker) == 1)
    choice = json.loads(text.split(marker, 1)[1].split('\n', 1)[1].split('\n', 1)[0])
    require('prior choice input identity', choice['input_id'] == wire['output']['navigation_id'])
    require('prior request hash', choice['request_sha256'] == sha(wire['request_json'].encode()))
    require('prior wire response hash', choice['response_sha256'] == sha(wire['response_json'].encode()))
    require('selected next propagated', choice['feedback']['selected_next'] == command and choice['feedback']['selection_kind'] == 'explicit_next')
    actions = []
    for rec in records:
        if rec['kind'] == 'action':
            decoded = json.loads(rec['text'])
            if decoded.get('action_id') == following['action_id']:
                actions.append((rec, decoded))
    require('exactly one retained follow-up action', len(actions) == 1)
    rec, action = actions[0]
    unique_record(rec['path'])
    payload = json.loads(action['payload'])
    require('parent action is third sample', payload['parent_action_id'] == third['action_id'])
    require('dispatch matches corrected command', payload['canonical_action'] == command and following['action_text'] == command)
    require('job identity', payload['llm_job_id'] == following['job_id'])
    require('following input receipt verified', following['receipt_verified'])
    require('following response retained as exact writing', bool(following['writing']))
    require('one following source page', len(following['pages']) == 1)
    page = following['pages'][0]
    require('corrected source delivered from beginning', page['source'] == command.split()[2] and page['start']['byte'] == 0 and page['start']['line'] == 1)
    require('same revision as fixed sample1', page['revision']['sha256'] == next(r for r in rows if r['id'] == selected[0])['pages'][0]['revision']['sha256'])
    unique_record(following['receipt_path'])
    source_rows = [r for r in rows if r['actual_route'] == 'source_study']
    private_rows = [r for r in rows if r['actual_route'] == 'extended_writing']
    pages = [p for r in source_rows for p in r['pages']]
    return {
        'schema': 's007-day10-descriptive-account-v1', 'status': 'passed',
        'capture_sha256': report['capture_sha256'], 'supplement_sha256': report['supplement_sha256'],
        'report_sha256': sha(report_path.read_bytes()), 'followup_plan_sha256': sha(plan_path.read_bytes()),
        'counts': {'generations': len(rows), 'routes': dict(sorted(Counter(r['actual_route'] for r in rows).items())),
                   'source_study_completed': sum(r['status'] == 'ok' for r in source_rows),
                   'private_writing_generations': len(private_rows),
                   'source_page_opportunities': len(pages), 'source_page_opportunities_by_repository': dict(sorted(Counter(p['source'].split('/')[0] for p in pages).items())),
                   'source_revisions': len(report['sources']), 'fully_reconstructed_revisions': sum(s['full_file_hash_verified'] for s in report['sources']),
                   'notebooks_supplied': sum(r['notebook'].get('status') == 'included_in_submitted_user_text' for r in source_rows),
                   'kinds': dict(sorted(Counter(r['kind'] for r in rows).items())),
                   'statuses': dict(sorted(Counter(r['status'] for r in rows).items())),
                   'cap_hits': sum(bool(r['cap_hit']) for r in rows)},
        'sources': report['sources'], 'censored_jobs': report['jobs_without_window_generation'],
        'minime_owned_page': next(({'id': r['id'], 'page': p} for r in source_rows for p in r['pages'] if p['source'].split('/')[0] == 'minime'), None),
        'close_reading_ids': selected,
        'adjacent_followup': {'classification': plan['classification'], 'selection': plan['selection'],
            'previous_generation_id': third['id'], 'generation_id': following['id'],
            'completed': following['completed'], 'action_id': following['action_id'],
            'parent_action_id': payload['parent_action_id'], 'job_id': following['job_id'],
            'action_record_sha256': rec['sha256'], 'record_sha256': following['record_sha256'],
            'response_sha256': following['response_sha256'], 'command': command,
            'prior_choice': choice, 'page': page,
            'result': 'Corrected authored choice, explicit parent/action/job linkage, and verified next source delivery. Understanding and durable saved revision are not established.',
            'limits': plan['limits']},
        'checks': checks,
        'limits': ['Selected interpretive spans are not an accuracy denominator.',
                   'Full retained file reconstruction does not establish model understanding.',
                   'No exhaustive later-correction search or causal before/after improvement claim.',
                   'Private writing is a separate route within the filename-selected capture frame.',
                   'A running cutoff job is censored, not classified as a failed generation.']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('packet', type=Path)
    p.add_argument('--report', type=Path)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    result = build(args.packet, args.report or args.packet / 'final-report/report.json')
    with args.out.open('x') as handle:
        handle.write(json.dumps(result, indent=2, sort_keys=True) + '\n')

if __name__ == '__main__':
    main()
