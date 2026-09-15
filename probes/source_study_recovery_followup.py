"""Descriptive post hoc recovery follow-up on frozen S-007 daily reports only."""
import json
from collections import Counter
from pathlib import Path
from itertools import groupby

def build(packet):
    report = json.loads((packet/'final-report/report.json').read_bytes())
    studies = report['studies']
    runs = []
    for (kind, action), group in groupby(studies, key=lambda s:(s['kind'],s['action_text'])):
        group = list(group)
        if kind != 'recovery':
            continue
        i = studies.index(group[0]); j = i+len(group)
        runs.append(dict(action=action,n=len(group),ids=[s['id'] for s in group],
                         first=group[0]['completed'],last=group[-1]['completed'],
                         touches_window_start=i==0,touches_window_end=j==len(studies),
                         next_observed_study=None if j==len(studies) else {k:studies[j][k] for k in ['id','completed','kind','action_text']}))
    selected_end = max(studies.index(s) for s in studies if s['id'] in report['close_reading_ids'])
    next_code = next((s for s in studies[selected_end+1:] if s['receipt_verified'] and s['pages']),None)
    return dict(schema='s007_recovery_followup_v1',selection=json.loads((packet/'exploratory-protocol.json').read_bytes()),
                recoveries=sum(s['kind']=='recovery' for s in studies),
                recovery_actions=dict(Counter(s['action_text'] for s in studies if s['kind']=='recovery')),
                maximal_same_action_runs=runs,
                first_later_numbered_source=None if not next_code else {k:next_code[k] for k in ['id','completed','kind','action_text','pages']},
                source_study_counts=dict(Counter(s['status'] for s in studies if s['actual_route']=='source_study')),
                prompt_system_hash_sets=[dict(hashes=list(k),n=v) for k,v in Counter(tuple(s['system_hashes']) for s in studies).items()],
                limits='Runs are consecutive within the captured generation lane, not the full action stream. Repetition can be chosen rereading; recovery counts denote unavailable requested source, not model/service failure or a semantic grade.')
