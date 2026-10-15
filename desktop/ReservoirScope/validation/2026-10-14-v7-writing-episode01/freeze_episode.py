#!/usr/bin/env python3
"""Freeze explicit v7 episode preparation once, before admission or output."""
from pathlib import Path
import datetime as dt
import hashlib,json

def identity(path):
    path=path.resolve()
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest()}

def main():
    here=Path(__file__).resolve().parent; desktop=here.parents[1]
    assert not (here/'host-admission-01.json').exists()
    names=['PROTOCOL.md','RUBRIC.md','EVALUATION.md','run-plan.json','admit_once.py','freeze_episode.py','owned_model.py','test_owned_model.py','helper-continuity-01.json','journal_quality.py','test_journal_quality.py','quality-helper-tests-01.json','quality-helper-tests-01.log','check_real_model_export.py','test_real_model_export.py','checker-tests-01.json','checker-tests-01.log','checker-freeze-01.json','preparation-identities-01.json','ui-preparation-01.json']
    paths=[here/n for n in names]
    prior=here.parent/'2026-10-14-v6-writing-episode02'
    paths += [prior/n for n in ['software-selection.json','runtime-review-01.json','RUNTIME-REVIEW.md','owned-helper-tests-02.json','owned_model.py','test_owned_model.py','check_real_model_export.py','test_real_model_export.py']]
    paths += sorted(p for p in (prior/'runtime-sources-01').rglob('*') if p.is_file())
    paths += [here.parent/'2026-10-13-reading-0.12.1/model-selection.json']
    paths += [desktop/'crates/reservoir-core/tests/fixtures/sustained-prompts'/n for n in ['v7-observation-10.txt','v7-memory-20.txt','v7-provenance.json']]
    paths += [here.parent/'2026-10-14-action-boundaries-0.19.0'/n for n in ['PROTOCOL.md','PROMPT-V7-TEMPLATE.txt','qualification-close-01.json','source-before-build-01.json','archive-check-01.json']]
    paths += [Path(i['path']) for i in json.loads((here/'preparation-identities-01.json').read_text())['files']]
    paths += [Path('/Users/v/other/reservoir-llm-research/desktop/ReservoirScope/target/qa/0.12.1-real-gemma3-4b/stage-receipt.json')]
    files=[identity(p) for p in sorted(set(paths))]
    plan=json.loads((here/'run-plan.json').read_text())
    assert plan['plannedOpportunities']==12 and plan['promptVersion']=='reservoir-journal-v7'
    out={'schema':'reservoir-v7-episode-preparation-freeze-v1','frozenAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'prospective-before-admission','episodeId':plan['episodeId'],'plannedSlots':12,'newSessionCreated':False,'newModelCalls':0,'files':files}
    with (here/'evaluation-freeze-01.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps({'frozenFiles':len(files),'status':out['status']}))
if __name__=='__main__': main()
