"""Replay S-008 overnight scope/cap metrics from the frozen capture, with no live reads."""
from collections import Counter
from datetime import datetime
import hashlib, json, re, statistics, sys
from pathlib import Path

capture, report, out = map(Path, sys.argv[1:])
raw = capture.read_bytes(); packet = json.loads(raw); results = json.loads(report.read_bytes())
assert results['capture_sha256'] == hashlib.sha256(raw).hexdigest()
start = datetime.fromisoformat('2026-09-09T05:17:00+00:00').timestamp()
end = datetime.fromisoformat('2026-09-09T15:30:00+00:00').timestamp()
records = packet['records']; by_path = {r['path']: r for r in records}
def counts(xs): return dict(sorted(Counter(xs).items()))
def summary(xs):
    return {'n':len(xs),'min':min(xs),'median':statistics.median(xs),'max':max(xs)} if xs else {'n':0}
def read(r): return json.loads(r['text'])
def word_count(text): return len(re.findall(r'\S+', text))
metrics = {'capture_sha256': results['capture_sha256'], 'window': [start,end], 'beings':{}}
selected=[]
for being in ['astrid','minime']:
    studies = [s for s in results['studies'] if s['being']==being]
    selected += studies[:3]+studies[-3:]
    wires=[]
    for s in studies:
        receipt=read(by_path[s['receipt']]) if isinstance(s['receipt'],str) else None
        if receipt is None:
            # Reporter retains the exact artifact in a structured receipt field.
            path=s['receipt'].get('path',s['receipt'].get('artifact_path'))
            receipt=read(by_path[path])
        wire=receipt.get('attempt',receipt)
        wires.append((json.loads(wire['request_json']),json.loads(wire['response_json'])))
    generation=[read(r) for r in records if r['kind']=='generation' and r['being']==being]
    generation=[g for g in generation if start<=g.get('created_at_unix_ms',0)/1000<end]
    paths={s['receipt'] if isinstance(s['receipt'],str) else s['receipt'].get('path',s['receipt'].get('artifact_path')) for s in studies}
    progress=[p for p in results['source_progress'] if p['being']==being and p['path'] in paths]
    metrics['beings'][being] = {
        'unique_verified_study_inputs':len(studies),'kinds':counts(s['kind'] for s in studies),
        'authored_note':sum(bool(s['authored']['STUDY_NOTE']) for s in studies),
        'authored_question':sum(bool(s['authored']['STUDY_QUESTION']) for s in studies),
        'study_words':summary([word_count(s['text']) for s in studies]),
        'study_requested_output_caps':counts(str(req.get('max_tokens',req.get('options',{}).get('num_predict'))) for req,_ in wires),
        'study_native_finish':counts(str(s['native_finish']) for s in studies),
        'new_source_bytes':sum(p['new_bytes'] for p in progress),
        'repeated_source_bytes':sum(p['repeated_bytes'] for p in progress),
        'generation_statuses':counts(str(g.get('status')) for g in generation),
        'generation_lanes':counts(str(g.get('lane')) for g in generation),
        'study_eval_count': summary([resp['eval_count'] for _,resp in wires if isinstance(resp.get('eval_count'),int)]),
        'study_elapsed_s':summary([s['completed']-s['started'] for s in studies if s.get('completed')]),
        'study_without_NEXT_but_terminal_bare_choice':[s['id'] for s in studies if not s.get('next',{}).get('raw') and re.search(r'(?:^|\n)SELF_STUDY (?:OPEN|MAP|FIND|RESUME|CONTINUE)\b[^\n]*\s*$',s['text'])],
    }
reading=[]
for r in records:
    if r['kind']!='accepted_delivery':continue
    q=read(r);a=q['attempt'];response=json.loads(a['response_json'])
    if a['admission']['kind']=='reading' and start<=response.get('created',0)<end:
        reading.append({'path':r['path'],'created':response['created'],'admission':a['admission']})
metrics['new_accepted_reading_deliveries']=reading
metrics['read_more_actions']=len([a for a in results['reading_actions'] if a['requested_category']=='READ_MORE'])
metrics['reading_action_statuses']=counts(a['status'] for a in results['reading_actions'] if a['requested_category']=='READ_MORE')
metrics['provider_outcomes']=counts(str((q.get('label'),q.get('outcome'))) for r in records if r['kind']=='provider_event' and (q:=read(r)).get('stage')=='provider_outcome' and start<=q.get('created_at_unix_ms',0)/1000<end)
metrics['notes']=[
    'Unique verified provider inputs are not a count of all journals or attempted Actions.',
    'Astrid gateway usage is a zero placeholder; do not interpret as actual token counts.',
    'READ_MORE handled status alone is not delivery; no new retained reading request in this window.',
    'Source progress is measured against all earlier retained receipt coverage, not comprehension.',
    'First/last cases are deterministic; added mechanism cases do not estimate incidence.',
]
out.mkdir(parents=True,exist_ok=True)
for name,data in [('metrics.json',metrics),('selected-first-last.json',selected)]:
    path=out/name
    with path.open('x') as f:
        import os
        os.chmod(path,0o600)
        json.dump(data,f,indent=2);f.write('\n')
print(json.dumps(metrics,indent=2))
