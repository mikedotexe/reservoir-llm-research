#!/usr/bin/env python3
"""Freeze prepared diagnostic and preserve selected source/historical inputs; no network."""
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
DESKTOP=HERE.parents[1]
REPO=DESKTOP.parents[1]

def identity(path):
    path=path.resolve(strict=True)
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def main():
    assert not (HERE/'host-admission-01.json').exists()
    plan=json.loads((HERE/'run-plan.json').read_text())
    assert not Path(plan['ownedServiceDirectory']).exists()
    assert not Path(plan['provenance']['resultsDirectory']).exists()
    assert plan['episodeId'] == 'context-order-03'
    copied=json.loads((HERE/'copy-manifest-01.json').read_text())
    assert copied['priorDirectoryBefore'] == copied['priorDirectoryAfter']
    assert copied['priorDirectoryAfter'] == [identity(Path(f['path'])) for f in copied['priorDirectoryAfter']]
    checks=json.loads((HERE/'preparation-checks-01.json').read_text())
    assert checks['passed'] and checks['sourceUnchanged']
    for item in checks['sourceAfter']:
        assert identity(Path(item['path'])) == item
    assert (HERE/'PRE-RUN-REVIEW.md').is_file()
    assert (HERE/'cleanup-result-01.json').is_file()  # Root-owned cleanup must finish before freeze.
    inputs=json.loads((HERE/'frozen-inputs.json').read_text())
    assert identity(HERE/'run-plan.json') == inputs['runPlan']
    for slot in inputs['slots']:
        assert identity(Path(slot['prompt']['path'])) == slot['prompt']
    paths=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [Path(f['path']) for f in copied['priorDirectoryAfter']]
    paths += [Path(plan['softwareSelectionPath']),DESKTOP/'src-tauri/src/model_transport.rs',
              HERE.parent/'2026-10-13-reading-0.12.1/model-selection.json',
              HERE.parent/'2026-10-14-v6-writing-episode02/owned-helper-tests-02.json']
    for name in ('2026-10-14-v7-writing-episode03','2026-10-14-v8-writing-episode01'):
        old=HERE.parent/name
        paths += [p for p in old.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [p for tree in ('src','src-tauri/src','crates','shared') for p in (DESKTOP/tree).rglob('*')
              if p.is_file() and '__pycache__' not in p.parts]
    paths += [p for p in (REPO/'shared/reservoir-scope').rglob('*') if p.is_file() and p.name != 'PARITY.md']
    paths += [DESKTOP/name for name in ('Cargo.lock','Cargo.toml','package-lock.json','package.json','src-tauri/tauri.conf.json','src-tauri/Cargo.toml')]
    assert identity(HERE/'owned_model.py')['sha256']=='415a585dfa4502e555331b4472cf08b6afbd3207944e6d02d952e133175f8c1b'
    assert identity(Path(plan['softwareSelectionPath']))['sha256']==plan['softwareSelectionSha256']
    files=[identity(p) for p in sorted(set(paths))]
    assert files==[identity(Path(f['path'])) for f in files]
    value={'schema':'reservoir-context-order-freeze-v1','status':'prospective-before-admission',
           'frozenAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'episodeId':plan['episodeId'],
           'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
           'productBuiltOrChanged':False,'modelCalls':0,'files':files,
           'scope':'Prepared diagnostic, selected prior episode evidence, product source/contracts. No model/runtime execution.'}
    with (HERE/'evaluation-freeze-01.json').open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'files':len(files),'freeze':identity(HERE/'evaluation-freeze-01.json')}))

if __name__=='__main__':main()
