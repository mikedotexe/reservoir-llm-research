#!/usr/bin/env python3
"""Read-only arithmetic/visibility audit of the scripted 0.51.0 native fixture.

Not a substitute for native --verify-sustained replay. No provider or live access.
"""
import argparse
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    assert not args.output.resolve().is_relative_to(args.export.resolve())
    m=json.loads((args.export/'manifest.json').read_text())
    cp=json.loads((args.export/'checkpoints'/f"{m['checkpointSha256']}.json").read_text())
    state=cp['state'];reports=state['sonarState']['experiments']
    assert m['step']==19 and m['journalCount']==6 and len(reports)==2
    first,follow=reports
    assert first['request']['name']=='leak-comparison' and follow['request']['name']=='pulse-follow-up'
    assert first['origin']==follow['origin'] and first['origin']['step']==6
    assert follow['request']['followUpOf']==first['id']
    assert follow['request']['origin']['id']==first['id']
    assert follow['request']['probe']['direction']['id']==first['id']
    assert [o['controls']['leak'] for o in first['conditionOrigins']]==[0.65,0.2]
    assert all(r['returnStep']==(4 if r['condition']==0 else 12) for r in first['responses'])
    receipts=state['actionState']['recentReceipts']
    probe=next(r for r in receipts if r['request']['kind']=='probeExperiment')
    assert probe['status']=='applied' and probe['appliedStep']==10
    assert probe['experimentProbe']['sourceId']==first['id']
    assert probe['stateDeltaL2']==probe['experimentProbe']['forecastResponseL2'][0]
    assert 0<probe['stateDeltaL2']<=0.05
    assert all(r['controlsAfter']['leak']==0.65 for r in receipts)
    assert all(r['stateDeltaL2']==0 for r in receipts if r['request']['kind']=='experiment')
    journals=[json.loads(p.read_text())['pending'] for p in sorted((args.export/'journals').glob('*.json'))]
    assert len(journals)==6
    prompts=[p['prompt'] for p in journals]
    assert any(first['id'] in p for p in prompts) and any(follow['id'] in p for p in prompts)
    assert all('PARAMETERIZED EXPERIMENTS' in p for p in prompts)
    result={'sessionId':m['sessionId'],'step':m['step'],'journals':m['journalCount'],
        'resultIds':[r['id'] for r in reports],'originStep':first['origin']['step'],
        'realImpulseStep':probe['appliedStep'],'realImmediateL2':probe['stateDeltaL2'],
        'forecastImmediateL2':probe['experimentProbe']['forecastResponseL2'][0],
        'leakConditions':[0.65,0.2],'returnStepsByCondition':[4,12],
        'liveLeakUnchanged':True,'followupReusesOrigin':True,'resultsReachLaterPrompts':True,
        'maximumPromptBytes':max(len(p.encode()) for p in prompts),
        'exportFileBytes':sum(p.stat().st_size for p in args.export.rglob('*') if p.is_file()),
        'passed':True,'modelsContacted':False,'sourceWrites':False,
        'scope':'Scripted arithmetic and visibility checks, not model competence or independent numerical replay.'}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
