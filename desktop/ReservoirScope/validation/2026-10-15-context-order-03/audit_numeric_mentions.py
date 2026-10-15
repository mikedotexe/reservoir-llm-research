#!/usr/bin/env python3
"""Reproduce a post-reading, scoped current-scalar audit. No model calls or quality gate."""
import datetime as dt
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Semantic assignment from full manual reading, in decimal-mention order.
FIELDS = {1: ['rms','fill','distance'], 2: ['rms','distance'],
          3: ['rms','fillChange','distance'], 4: ['rms','fill','distance'],
          5: ['rms','fill','distance'], 6: ['rms','fill','distance'],
          7: ['rms','fill','distance'], 8: ['rms','fill','distance'],
          9: ['rms','fill','distance'], 10: ['fill','distance'],
          11: ['distance','fill','rms'], 12: ['rms','distance','fill']}

def identity(p):
    raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def main():
    ledger=json.loads((HERE/'run-output-01/ledger.json').read_text())
    mapping=json.loads((HERE/'sealed-map-01.json').read_text())
    ids={x['sourceSlot']['slot']:x['reading']['readingId'] for x in mapping['slots']}
    prior_path=HERE.parent/'2026-10-14-v8-writing-episode01/real-model-export-01/quality-review-material.json'
    prior={x['identity']['observedStep']:x for x in json.loads(prior_path.read_text())['journals']}
    rows=[]; refs=[identity(prior_path),identity(HERE/'run-output-01/ledger.json'),identity(HERE/'sealed-map-01.json')]
    historical=[]
    for s in ledger['slots']:
        n=s['slot']; step=s['anchorStep']
        request_path=HERE/'run-output-01'/Path(s['request']['path']).name
        text_path=HERE/'run-output-01'/Path(s['text']['path']).name
        assert identity(request_path)['sha256']==s['request']['sha256']
        assert identity(text_path)['sha256']==s['text']['sha256']
        refs.extend([identity(request_path),identity(text_path)])
        prompt=json.loads(request_path.read_text())['messages'][0]['content']
        text=text_path.read_text()
        expected={'rms':re.search(r'Recurrent state RMS: current ([0-9.]+)',prompt)[1],
                  'fill':re.search(r'Separate sensory fill \(%\): current ([0-9.]+)',prompt)[1],
                  'fillChange':re.search(r'Separate sensory fill.*?change ([+-][0-9.]+)',prompt)[1],
                  'distance':re.search(r'L2 distance since the previous observation: ([0-9.]+)\.',prompt)[1]}
        mentions=list(re.finditer(r'\d+\.\d+',text))
        assert len(mentions)==len(FIELDS[n]), (n,len(mentions))
        obs=prior[step]['observation']
        assert expected['rms']==f"{obs['rms']:.8f}"
        assert expected['fill']==f"{obs['sensory']['fillPercent']:.8f}"
        assert expected['distance']==f"{obs['changeL2']:.8f}"
        for m,field in zip(mentions,FIELDS[n]):
            rows.append({'slot':n,'readingId':ids[n],'anchorStep':step,'condition':s['condition'],
                         'field':field,'emitted':m[0],'supplied':expected[field],
                         'exactNumericMatch':Decimal(m[0])==Decimal(expected[field]),
                         'countedAsCurrentScalar':field!='fillChange',
                         'span':text[max(0,m.start()-65):min(len(text),m.end()+65)]})
        historical.append({'slot':n,'condition':s['condition'],'anchorStep':step,
                           'freshTextEqualsHistoricalText':text==prior[step]['journalText']})
    counts={c:{'mentions':sum(r['condition']==c and r['countedAsCurrentScalar'] for r in rows),
               'matching':sum(r['condition']==c and r['countedAsCurrentScalar'] and r['exactNumericMatch'] for r in rows),
               'mismatching':sum(r['condition']==c and r['countedAsCurrentScalar'] and not r['exactNumericMatch'] for r in rows)} for c in ('A','B')}
    result={'schema':'reservoir-context-order-numeric-mentions-v1','auditedAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'script':identity(Path(__file__).resolve()),'inputs':refs,'currentScalarCounts':counts,'mentions':rows,
            'historicalTextComparison':historical,
            'limits':['Post-reading semantic assignments, not an automatic factuality classifier.',
                      'Counts cover all decimal mentions of current RMS/resonance, sensory fill and interval L2 in these twelve texts only; the separate rounded fill-change mention is retained but excluded.',
                      'Matching a scalar is not correct metric meaning, direction, time, causality or a general accuracy score.',
                      'The twelve responses are six paired dependent historical contexts; no significance or stable model-effect claim.',
                      'Fresh A bytes equaling historical text does not mean historical responses were substituted: request, transport and service receipts establish fresh requests.']}
    with (HERE/'numeric-mentions-01.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'counts':counts,'historicalExactA':sum(x['condition']=='A' and x['freshTextEqualsHistoricalText'] for x in historical),
                      'historicalExactB':sum(x['condition']=='B' and x['freshTextEqualsHistoricalText'] for x in historical)}))

if __name__=='__main__': main()
