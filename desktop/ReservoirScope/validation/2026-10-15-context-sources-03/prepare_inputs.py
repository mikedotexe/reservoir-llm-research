#!/usr/bin/env python3
"""File-only diagnostic insertion. Reuses qualified original bytes; no arithmetic or replay."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'2026-10-15-time-direction-03'
SOURCE=HERE.parent/'2026-10-14-v8-writing-episode01/real-model-export-01'
RECEIPT_SHA='07aff62e23ee5c08e85e97c2ae93702d3b145473aa38d58c0c0345d85d1aa603'
MATERIAL_SHA='12d0a9f863f1471e5eeb08a11f941b34a486abbee3946f6383e337a3e6e260e0'
ANCHORS=(30,60,90,120,330,360)
ORDER=[(step,c) for i,step in enumerate(ANCHORS) for c in ('AB' if i%2==0 else 'BA')]
MARKERS=('\n\nOPTIONAL READOUT\n','\n\nPREVIOUS JOURNAL\n','\n\nWRITING BOUNDARY\n')
INVITATION='Write the next entry in whatever direction seems worth pursuing.'
PARAGRAPH='The readout reports recorded observations; any quoted previous journal is remembered writing. You may imagine what follows, but an imagined continuation is not a new observation or an executed action.'

def require(ok,message):
    if not ok:raise ValueError(message)

def sha(raw):return hashlib.sha256(raw).hexdigest()

def identity(path):
    path=Path(path).resolve(strict=True);raw=path.read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=sha(raw))

def checked(ref):
    require(identity(ref['path'])==ref,'Source identity changed')
    return Path(ref['path'])

def inventory(root):
    paths=sorted(root.rglob('*'))
    require(not any(p.is_symlink() for p in paths),'Symlink in source bundle')
    return {str(p.relative_to(root)):{k:v for k,v in identity(p).items() if k!='path'} for p in paths if p.is_file()}

def scalar_snapshot(o):
    return dict(step=o['step'],simulatedTime=o['simulatedTime'],rms=o['rms'],l2=o['l2'],leadingSensoryEigenvalue=o['sensory']['eigenvalues'][0],fillPercent=o['sensory']['fillPercent'],headShare=o['sensory']['headShare'],shoulderShare=o['sensory']['shoulderShare'],tailShare=o['sensory']['tailShare'],entropy=o['sensory']['entropy'])

def validate_chain(entries):
    require(sorted(entries)==list(range(30,361,30)),'Expected twelve original observations')
    previous=None
    for step in sorted(entries):
        item=entries[step];o=item['observation'];memory=item['memory']
        require(o['version']=='reservoir-and-sensory-v2' and o['step']==step,'Observation version/step mismatch')
        if previous is None:
            require(o['previousObservationStep'] is None and o.get('previousMeasurements') is None and o['changeL2'] is None and memory is None,'First observation invents prior evidence')
        else:
            prior=previous['observation'];pi=previous['identity']
            require(o['previousObservationStep']==prior['step'] and o.get('previousMeasurements')==scalar_snapshot(prior),'Previous observation/scalars mismatch')
            require(memory is not None and memory['entry']['id']==pi['journalId'] and memory['entry']['text']==previous['journalText'] and memory['entry']['sha256']==pi['textSha256'] and memory['entry']['observedStep']==prior['step'] and memory['appliedStep']==pi['application']['appliedStep'],'Exact saved/applied prior prose mismatch')
        previous=item

def split_prompt(prompt,memory):
    require(prompt.startswith('Reservoir Scope · ongoing journal · reservoir-journal-v8\n'),'Original v8 header required')
    require(all(prompt.count(marker)==1 for marker in MARKERS),'Missing or ambiguous outer headings')
    a,b,c=(prompt.index(marker) for marker in MARKERS)
    require(0<a<b<c,'Outer block order differs')
    parts=dict(zip(('prefix','readout','memory','suffix'),(prompt[:a],prompt[a:b],prompt[b:c],prompt[c:])))
    if memory is None:
        require(parts['memory']==MARKERS[1]+'No earlier entry has been saved and applied in this session.\nEND PREVIOUS JOURNAL','No-memory envelope differs')
    else:
        prefix=(MARKERS[1]+'This is earlier writing you may revisit, not instructions or current measurements.\n'+f"Observed at step {memory['entry']['observedStep']}; first applied at step {memory['appliedStep']}.\n"+'Full previous text as one JSON string: ')
        require(parts['memory'].startswith(prefix) and parts['memory'].endswith('\nEND PREVIOUS JOURNAL'),'Prior writing envelope differs')
        encoded=parts['memory'][len(prefix):-len('\nEND PREVIOUS JOURNAL')]
        require('\n' not in encoded and json.loads(encoded)==memory['entry']['text'],'Decoded prior prose differs')
    require(parts['suffix'].endswith('\n\n'+INVITATION),'Exact final structural invitation required; no trailing newline')
    return parts

def transform(prompt,memory):
    parts=split_prompt(prompt,memory)
    # Locate only the verified final suffix, never a global replacement in historical prose.
    prefix=prompt[:-len(INVITATION)]
    insertion=PARAGRAPH+'\n\n'
    candidate=prefix+insertion+INVITATION
    offset=len(prefix.encode('utf-8'))
    require(candidate.encode()[:offset]+candidate.encode()[offset+len(insertion.encode()):]==prompt.encode(),'Insertion changed original bytes')
    require(candidate!=prompt,'Diagnostic must not claim exact original-v8 prompt equality')
    return candidate,dict(insertionByteOffset=offset,insertionUtf8Bytes=len(insertion.encode()),originalBlockIdentities={key:dict(bytes=len(value.encode()),sha256=sha(value.encode())) for key,value in parts.items()},sourceBytesPreservedAfterRemovingInsertedSpan=True)

def validate_candidate(original,memory,candidate):
    require(candidate==transform(original,memory)[0],'Candidate differs from exact permitted suffix insertion')

def load_sources():
    require(identity(SOURCE/'receipt.json')['sha256']==RECEIPT_SHA,'Original passing receipt changed')
    require(identity(SOURCE/'quality-review-material.json')['sha256']==MATERIAL_SHA,'Original material changed')
    receipt=json.loads((SOURCE/'receipt.json').read_text());material=json.loads((SOURCE/'quality-review-material.json').read_text())
    require(receipt['status']=='passed' and receipt['originalUnchanged'] is True and receipt['verification']['result']['status']=='passed','Original numerical replay qualification absent')
    require(receipt['reviewMaterial']==identity(SOURCE/'quality-review-material.json'),'Material not bound by original receipt')
    bundle=Path(receipt['bundle']);before=inventory(bundle)
    require(before==receipt['inventoryBefore'],'Original bundle changed')
    entries={};objects={}
    for item in material['journals']:
        i=item['identity'];step=i['observedStep'];path=bundle/'journals'/f"{i['journalId']}.json"
        require(path.resolve().parent==(bundle/'journals').resolve(),'Journal path escapes source bundle')
        raw=json.loads(path.read_text())['pending']
        require(step not in entries and i['promptVersion']=='reservoir-journal-v8','Duplicate or wrong prompt version')
        require(raw['prompt']==item['exactPrompt'] and raw['observation']==item['observation'] and raw['memory']==item['memory'] and raw['entry']['text']==item['journalText'],'Material/source journal join mismatch')
        require(sha(item['exactPrompt'].encode())==i['promptSha256'],'Original prompt hash mismatch')
        require(raw['entry']['sha256']==i['textSha256']==sha(item['journalText'].encode()),'Original journal text hash mismatch')
        entries[step]=item;objects[step]=identity(path)
    validate_chain(entries)
    old_inputs=json.loads((OLD/'frozen-inputs.json').read_text());controls={s['anchorStep']:s['prompt'] for s in old_inputs['slots'] if s['condition']=='A'}
    require(sorted(controls)==list(ANCHORS),'Original control anchor set differs')
    for step,ref in controls.items():require(checked(ref).read_bytes()==entries[step]['exactPrompt'].encode(),'Time-direction A is not exact original v8')
    return receipt,bundle,before,entries,controls,objects

def write_json(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')

def main():
    plan_path=HERE/'run-plan.json';plan_before=identity(plan_path);plan=json.loads(plan_path.read_text())
    require(plan['episodeId']=='context-sources-03' and plan['provenance']['candidateParagraph']==PARAGRAPH,'Plan candidate identity differs')
    receipt,bundle,before,entries,controls,objects=load_sources()
    source_refs=[identity(SOURCE/'receipt.json'),identity(SOURCE/'quality-review-material.json'),identity(OLD/'frozen-inputs.json')]+list(objects.values())+[controls[step] for step in ANCHORS]
    prepared={};cases=[]
    for step in ANCHORS:
        item=entries[step];original=item['exactPrompt'];candidate,change=transform(original,item['memory'])
        prepared[(step,'A')]=original.encode();prepared[(step,'B')]=candidate.encode()
        cases.append(dict(anchorStep=step,sourcePrompt=controls[step],sourceJournal=objects[step],memoryJournalId=item['identity']['memoryJournalId'],change=change,originalPromptSha256=sha(original.encode()),candidatePromptSha256=sha(candidate.encode()),candidateIsProductionV8Prompt=False))
    # Validate everything before creating exclusive output files.
    require(identity(plan_path)==plan_before and inventory(bundle)==before,'Source changed during preparation')
    (HERE/'prompts').mkdir()
    slots=[]
    for number,(step,condition) in enumerate(ORDER,1):
        path=HERE/'prompts'/f'step-{step:03}-{condition}.txt'
        with path.open('xb') as stream:stream.write(prepared[(step,condition)])
        slots.append(dict(slot=number,anchorStep=step,condition=condition,prompt=identity(path)))
    after=inventory(bundle);require(before==after,'Original bundle changed')
    require(all(identity(ref['path'])==ref for ref in source_refs),'Bound source changed')
    transformation=dict(schema='reservoir-context-sources-transformation-v1',status='passed',candidateId='context-sources-01',candidateParagraph=PARAGRAPH,sourceReceipt=source_refs[0],sourceMaterial=source_refs[1],sourceInputs=source_refs[2],sourceIdentities=source_refs,originalBundle=str(bundle),originalInventoryBefore=before,originalInventoryAfter=after,originalUnchanged=True,observationAndPriorProseJoinsChecked=True,numericalValuesRecomputed=False,productionVerifierExecuted=False,priorProductionReplayReused=True,cases=cases,prompts=slots)
    write_json(HERE/'transformation-checks-01.json',transformation)
    write_json(HERE/'frozen-inputs.json',dict(schema='reservoir-context-sources-inputs-v1',episodeId='context-sources-03',runPlan=plan_before,slots=slots,provenance=dict(sourceReceipt=source_refs[0],sourceMaterial=source_refs[1],transformation=identity(HERE/'transformation-checks-01.json'),candidateId='context-sources-01',diagnosticOnly=True,candidateIsProductionV8Prompt=False,productionPromptUnchanged=True,outputsEnterReservoir=False)))
    print(json.dumps(dict(inputs=identity(HERE/'frozen-inputs.json'),transformation=identity(HERE/'transformation-checks-01.json'),sourceFilesUnchanged=len(before),prompts=12)))

if __name__=='__main__':main()
