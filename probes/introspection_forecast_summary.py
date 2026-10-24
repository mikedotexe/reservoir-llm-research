#!/usr/bin/env python3
"""Describe S-014 scores and optional paired reader notes without new exclusions."""
from collections import Counter
import argparse
import json
from pathlib import Path
from statistics import mean
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reservoir_experiments import runner


def numeric_summary(rows, field):
    values=[r[field] for r in rows if type(r.get(field)) in (int,float)]
    return {'available':len(values),'mean':mean(values) if values else None,
            'min':min(values) if values else None,'max':max(values) if values else None}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run',type=Path)
    ap.add_argument('--score',type=Path,required=True)
    ap.add_argument('--reading',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    runner.verify(args.run)
    _,p=runner.load_run(args.run)
    s=runner.read_json(args.score)
    if p['study']!='S-014' or s['protocol_id']!=p['id']:
        raise ValueError('Protocol/score mismatch')
    manifest_sha=runner.sha((args.run/'manifest.json').read_bytes())
    if s['provenance']['manifest_sha256']!=manifest_sha:
        raise ValueError('Score does not reference this run')
    rows=s['rows']; targets=[r for r in rows if r['kind']=='target']
    diagnostics=set(p.get('design',{}).get('diagnostic_episodes',[]))
    result={'study':p['study'],'model':p['model'],'split':p['split'],
            'primary':s['primary'], 'status_counts':s['status_counts'],
            'targets':{'planned':len(targets),'scorable':sum(r['valid'] for r in targets),
                       'correct':sum(r['score'] for r in targets if r['valid']),
                       'verdicts':dict(Counter(r['verdict'] for r in targets)),
                       'initial_wrong_on_initial_evidence':dict(Counter(str(r['initial_wrong_on_initial_evidence']).lower() for r in targets)),
                       'changed_from_initial':dict(Counter(str(r['changed_from_initial']).lower() for r in targets))},
            'forecasts':{},'brier':{},'diagnostics':{},
            'score_sha256':runner.sha(args.score.read_bytes()),'manifest_sha256':manifest_sha,
            'code_sha256':runner.sha(Path(__file__).read_bytes())}
    for c in ('self','observer'):
        group=[r for r in rows if r['kind']=='forecast' and r['condition']==c]
        result['forecasts'][c]={'planned':len(group),**numeric_summary(group,'forecast_probability'),
                               'probability_counts':dict(Counter(str(r['forecast_probability']) for r in group))}
    for name in ('self_brier','observer_brier','baseline_brier'):
        result['brier'][name]=numeric_summary(s['paired_forecasts'],name)
    if diagnostics:
        groups={'matched_main':[r for r in targets if r['episode'] in diagnostics]}
        groups.update({c:[r for r in rows if r['condition']==c] for c in ('neutral_update','retained_forecast_update','target_duplicate')})
        for c,group in groups.items():
            result['diagnostics'][c]={'planned':len(group),'scorable':sum(r['valid'] for r in group),
                                     'correct':sum(r['score'] for r in group if r['valid']),
                                     **{field:numeric_summary(group,field) for field in ('prompt_eval_count','eval_count','intermediate_eval_count','intermediate_words')}}
    if args.reading:
        folder=args.reading
        receipt=runner.read_json(folder/'receipt.json')
        for name,digest in receipt['files'].items():
            if runner.sha((folder/name).read_bytes())!=digest:raise ValueError('Reading export changed')
        expected={f"{item['packet_number']:03d}" for item in runner.read_json(folder/'allocation-key.json')}
        readers={c:runner.read_json(folder/f'reader-{c}-pass2.json') for c in ('a','b')}
        for c,r in readers.items():
            if set(r['packets'])!=expected or not (folder/f'reader-{c}-pass1.json').exists():
                raise ValueError('Incomplete reading coverage or missing first pass')
        result['reading']={'selected':len(expected),'readers':{},'rationale_disagreements':[]}
        for c,r in readers.items():
            records=list(r['packets'].values())
            result['reading']['readers'][c]={
                'verdict_counts':dict(Counter(x['verdict'] for x in records)),
                'rationale_fidelity':dict(Counter(x['rationale_fidelity'] for x in records)),
                'correction_of_prior_error':dict(Counter(str(x['correction_of_prior_error']).lower() for x in records)),
                'file_sha256':runner.sha((folder/f'reader-{c}-pass2.json').read_bytes())}
        for number in sorted(expected):
            labels={c:r['packets'][number]['rationale_fidelity'] for c,r in readers.items()}
            if len(set(labels.values()))>1:result['reading']['rationale_disagreements'].append({'packet':number,'labels':labels})
        result['reading']['boundary']='Original notes retained; no merged rationale judgment, no changes to primary scoring.'
    runner.write_json(runner.guard_output(args.out,ROOT),result)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
