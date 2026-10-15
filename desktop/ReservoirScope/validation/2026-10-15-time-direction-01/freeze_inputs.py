#!/usr/bin/env python3
"""Prospective file-only freeze. Root runs after independent review; never invokes providers."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
DESKTOP=HERE.parents[1]
REPO=DESKTOP.parents[1]

def identity(path):
    path=Path(path).resolve(strict=True);raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def checked(ref):
    actual=identity(ref['path'])
    assert actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes'], f'Identity changed: {ref["path"]}'
    return Path(actual['path'])

def qualification(name):
    path=(HERE/name).resolve(strict=True);assert path.parent==HERE
    doc=json.loads(path.read_text())
    assert doc.get('passed') is True or doc.get('status')=='passed'
    assert doc['sourceUnchanged'] is True and doc['sourceBefore']==doc['sourceAfter']
    for ref in doc['sourceAfter']:checked(ref)
    return doc,path

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preparation-checks',default='preparation-checks-01.json')
    ap.add_argument('--runtime-checks',default='runtime-checks-02.json')
    args=ap.parse_args()
    assert not (HERE/'evaluation-freeze-01.json').exists()
    assert not (HERE/'host-admission-01.json').exists()
    plan=json.loads((HERE/'run-plan.json').read_text())
    assert plan['schema']=='reservoir-time-direction-plan-v1' and plan['episodeId']=='time-direction-01'
    assert not Path(plan['ownedServiceDirectory']).exists()
    assert not Path(plan['provenance']['resultsDirectory']).exists()
    assert (HERE/'PRE-RUN-REVIEW.md').is_file()
    assert (HERE/'PROTOCOL.md').is_file() and (HERE/'READING-PROTOCOL.md').is_file()
    prepared,prepared_path=qualification(args.preparation_checks)
    runtime,runtime_path=qualification(args.runtime_checks)
    transformed=json.loads((HERE/'transformation-checks-01.json').read_text())
    # Each exact binary/source reference is retained by the preparer's qualification.
    formatter=prepared['formatter']
    formatter_paths=[checked(formatter[k]) for k in ('source','wrapper','binary')]
    assert formatter_paths[0]==(DESKTOP/'crates/reservoir-core/src/prompt_number.rs').resolve()
    assert all(p.is_relative_to(HERE) for p in formatter_paths[1:])
    for key in ('source','wrapper','binary'):
        assert transformed['formatter'][key]==formatter[key]
    inputs=json.loads((HERE/'frozen-inputs.json').read_text())
    assert inputs['schema']=='reservoir-time-direction-inputs-v1' and inputs['episodeId']==plan['episodeId']
    assert identity(HERE/'run-plan.json')==inputs['runPlan']
    expected=[(step,c) for i,step in enumerate((30,60,90,120,330,360)) for c in ('AB' if i%2==0 else 'BA')]
    assert len(inputs['slots'])==12
    for number,(slot,(step,condition)) in enumerate(zip(inputs['slots'],expected),1):
        assert slot['slot']==number and slot['anchorStep']==step and slot['condition']==condition
        assert checked(slot['prompt']).is_relative_to(HERE/'prompts')
    copied=json.loads((HERE/'runtime-copy-01.json').read_text())
    assert copied['priorDirectoryBefore']==copied['priorDirectoryAfter']
    for ref in copied['priorDirectoryAfter']+copied['priorQualification']+copied['sources']+copied['copies']:checked(ref)
    paths=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [Path(r['path']) for r in copied['priorDirectoryAfter']+copied['priorQualification']]
    paths += formatter_paths+[prepared_path,runtime_path,Path(plan['softwareSelectionPath']),
              HERE.parent/'2026-10-13-reading-0.12.1/model-selection.json',
              HERE.parent/'2026-10-14-v6-writing-episode02/owned-helper-tests-02.json']
    for name in ('2026-10-14-v7-writing-episode03','2026-10-14-v8-writing-episode01'):
        paths += [p for p in (HERE.parent/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [p for tree in ('src','src-tauri/src','crates','shared') for p in (DESKTOP/tree).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [p for p in (REPO/'shared/reservoir-scope').rglob('*') if p.is_file() and p.name!='PARITY.md']
    paths += [DESKTOP/n for n in ('Cargo.lock','Cargo.toml','package-lock.json','package.json','src-tauri/tauri.conf.json','src-tauri/Cargo.toml')]
    assert identity(HERE/'owned_model.py')['sha256']=='415a585dfa4502e555331b4472cf08b6afbd3207944e6d02d952e133175f8c1b'
    assert identity(plan['softwareSelectionPath'])['sha256']==plan['softwareSelectionSha256']
    files=[identity(p) for p in sorted(set(paths))]
    assert files==[identity(f['path']) for f in files]
    value={'schema':'reservoir-time-direction-freeze-v1','status':'prospective-before-admission',
           'frozenAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'episodeId':plan['episodeId'],
           'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
           'productBuiltOrChanged':False,'modelCalls':0,'files':files,
           'qualification':{'preparation':identity(prepared_path),'runtime':identity(runtime_path),'formatter':formatter},
           'scope':'Prepared diagnostic, exact formatting artifacts, preserved context01/02/03, selected source episodes and product sources. No runtime/model execution.'}
    with (HERE/'evaluation-freeze-01.json').open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps({'files':len(files),'freeze':identity(HERE/'evaluation-freeze-01.json')}))

if __name__=='__main__':main()
