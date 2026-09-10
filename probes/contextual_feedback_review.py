"""Read-only review of frozen offline cells; never interprets NEXT as instructions."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reservoir_research.study_sequences import command


def outcome_class(cell):
    """Keep native outcomes intact while separating admission from generation."""
    if cell.get('result') is not None:
        return 'generated'
    if cell['outcome'] == 'missing_complete_contextual_replay':
        return 'unavailable_prerequisite'
    if 'no idle live-service window' in cell.get('error', ''):
        return 'resource_admission_failure'
    if 'live service not healthy' in cell.get('error', ''):
        return 'health_admission_failure'
    return 'no_generation_receipt'


def review(root):
    protocol=json.loads((root/'protocol.json').read_text())
    result={'schema':'contextual_feedback_review_v1','protocol_sha256':hashlib.sha256((root/'protocol.json').read_bytes()).hexdigest(),
            'planned_free':24,'planned_fixed':32,'cells':[], 'missing':[], 'conditions':{},
            'length_is_success_criterion':False,'live_state_writes':0,'behavioral_annotations':[],
            'choice_scope':'Offline textual choices, never dispatched; parser is a research subset.',
            'fixed_text_scope':'Imposed teacher tokens; not authored claims or voluntary choices.'}
    grouped=defaultdict(list)
    for spec in protocol['trials']:
        path=root/(spec['id']+'.json')
        if not path.exists():result['missing'].append(spec['id']);continue
        cell=json.loads(path.read_text());value=cell.get('result') or {};text=value.get('text','')
        record=dict(id=spec['id'],case=spec['case'],kind=spec['kind'],arm=spec['arm'],state=spec['state'],seed=spec['seed'],
            outcome=cell['outcome'],outcome_class=outcome_class(cell),error=cell.get('error'),
            generated=bool(value),nonempty_terminal=bool(text.strip()) and value.get('finish')=='stop',
            tokens=value.get('completion_tokens'),chars=len(text),words=len(text.split()),
            seconds=value.get('seconds'),
            next_choice=command(text,'minime',terminal_source_choice=True,inquiry_navigation=True) if spec['kind']=='free' else None,
            final_state_norms=value.get('final_state_norms'),evidence=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        if value.get('trace'):
            rows=value['trace'];record['trace_rows']=len(rows)
            record['mean_context_saturation']=statistics.mean(r.get('contextual_saturated_fraction',0) for r in rows)
            record['mean_lookup_norm']=statistics.mean(r['lookup_projected_norm'] for r in rows)
            record['mean_context_norm']=statistics.mean(r['contextual_projected_norm'] for r in rows)
        result['cells'].append(record);grouped[spec['kind']+'-'+spec['arm']].append(record)
    for key,rows in grouped.items():
        seconds=[r['seconds'] for r in rows if r['seconds'] is not None]
        result['conditions'][key]=dict(n=len(rows),planned=sum(t['kind']+'-'+t['arm']==key for t in protocol['trials']),
            generated=sum(r['generated'] for r in rows),nonempty_terminal=sum(r['nonempty_terminal'] for r in rows),
            outcomes=dict(Counter(r['outcome'] for r in rows)),outcome_classes=dict(Counter(r['outcome_class'] for r in rows)),
            median_seconds=statistics.median(seconds) if seconds else None,word_counts=[r['words'] for r in rows])
    result['denominators']={kind:dict(planned=sum(t['kind']==kind for t in protocol['trials']),
        recorded=sum(r['kind']==kind for r in result['cells']),
        generated=sum(r['kind']==kind and r['generated'] for r in result['cells']),
        nonempty_terminal=sum(r['kind']==kind and r['nonempty_terminal'] for r in result['cells']))
        for kind in ('free','fixed')}
    annotations=root/'claim-annotations.json'
    if annotations.exists():
        annotated=json.loads(annotations.read_text())
        free_ids={t['id'] for t in protocol['trials'] if t['kind']=='free'}
        seen=set()
        for row in annotated:
            identity=row['trial_id']
            if identity not in free_ids or identity in seen:
                raise ValueError('annotation must uniquely identify a frozen free trial: '+identity)
            seen.add(identity)
            cell=json.loads((root/(identity+'.json')).read_text())
            response=(cell.get('result') or {}).get('text','')
            if row['response_sha256']!=hashlib.sha256(response.encode()).hexdigest():
                raise ValueError('annotation response identity changed: '+identity)
            for claim in row.get('claims',[]):
                if claim['quote'] not in response:
                    raise ValueError('annotation quote not present in response: '+identity)
        result['behavioral_annotations']=annotated
        result['unannotated_free']=[t['id'] for t in protocol['trials'] if t['kind']=='free' and t['id'] not in seen]
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=review(args.root)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(observed=len(result['cells']),missing=len(result['missing']),conditions=result['conditions']),indent=2))

if __name__=='__main__':main()
