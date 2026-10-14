#!/usr/bin/env python3
"""Static, read-only joins for one explicitly supplied 0.15 scripted native export.
No model, service, app, store discovery, numerical simulation, or verifier execution.
The production CLI replay is a separate qualification; this checks retained evidence.
"""
import argparse,datetime,hashlib,json,math,stat,struct
from decimal import Decimal
from pathlib import Path

def require(ok,message):
    if not ok:raise ValueError(message)
def sha(b):return hashlib.sha256(b).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def bits(v):
    if isinstance(v,float):return {'f64be':struct.pack('>d',v).hex()}
    if isinstance(v,list):return [bits(x) for x in v]
    if isinstance(v,dict):return {k:bits(x) for k,x in v.items()}
    return v
def inventory(root):
    out={};total=0
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink(),'Linked export member')
        if p.is_dir():continue
        require(stat.S_ISREG(p.stat().st_mode),'Nonordinary member')
        n=p.stat().st_size;total+=n
        require(n<=16*1024*1024 and total<=64*1024*1024 and len(out)<1000,'Bounded inspection exceeded')
        out[str(p.relative_to(root))]={'bytes':n,'sha256':sha(p.read_bytes())}
    return out

def snapshot(o):
    s=o['sensory']
    return {'step':o['step'],'simulatedTime':o['simulatedTime'],'rms':o['rms'],'l2':o['l2'],'leadingSensoryEigenvalue':s['eigenvalues'][0],'fillPercent':s['fillPercent'],'headShare':s['headShare'],'shoulderShare':s['shoulderShare'],'tailShare':s['tailShare'],'entropy':s['entropy']}
DESCRIPTORS=[('rms','Recurrent reservoir RMS','dimensionless'),('l2','Recurrent reservoir L2 norm','dimensionless'),('leadingSensoryEigenvalue','Largest sensory covariance eigenvalue','dimensionless'),('fillPercent','Reduced sensory active-mode fill','percent'),('headShare','Top-eight sensory head share','percent'),('shoulderShare','Top-eight sensory shoulder share','percent'),('tailShare','Top-eight sensory tail share','percent'),('entropy','Top-eight sensory normalized entropy','dimensionless')]
def rows(o):
    current=snapshot(o);previous=o.get('previousMeasurements');out=[]
    for key,label,unit in DESCRIPTORS:
        multiplier=100.0 if key in ('headShare','shoulderShare','tailShare') else 1.0
        a=current[key]*multiplier;b=previous[key]*multiplier if previous else None
        out.append({'key':key+'Percent' if key.endswith('Share') else key,'label':label,'unit':unit,'current':a,'previous':b,'delta':a-b if b is not None else None})
    return out

def check(bundle,baseline):
    before=inventory(bundle);m=json.loads((bundle/'manifest.json').read_text());c=m['config']
    require(c['language']['backend']=='scripted','This qualification is only the separate scripted native exercise')
    require(c['promptVersion']=='reservoir-journal-v4' and c['seed']=='20261013' and c['turnEvery']==30 and c['maximumSteps']==121 and c['maximumTurns']==4,'Expected bounded scripted recipe differs')
    require(m['step']==121 and m['durableStep']==121 and m['journalCount']==4,'Expected completed scripted boundary differs')
    observations={};frames={};events=[];previous_sha=None;previous_checkpoint=None
    segments=sorted((bundle/'segments').glob('*.json'));require(len(segments)==m['segmentCount'],'Segment coverage differs')
    for sequence,path in enumerate(segments,1):
        raw=path.read_bytes();e=json.loads(raw);s=e['segment'];require(e['sequence']==sequence and e['previousSha256']==previous_sha,'Sequence/byte-hash predecessor differs')
        if previous_checkpoint is not None:require(bits(s['initialCheckpoint'])==bits(previous_checkpoint),'Checkpoint continuity differs')
        for cp in (s['initialCheckpoint'],s['finalCheckpoint']):
            o=cp['state']['lastObservation']
            if o:
                if o['step'] in observations:require(bits(observations[o['step']])==bits(o),'Same observation step changed')
                observations[o['step']]=o
        events.extend(s['events']);previous_sha=sha(raw);previous_checkpoint=s['finalCheckpoint']
    checkpoint_bytes=(bundle/'checkpoints'/f"{m['checkpointSha256']}.json").read_bytes()
    require(previous_sha==m['lastSegmentSha256'] and sha(checkpoint_bytes)==m['checkpointSha256'] and bits(json.loads(checkpoint_bytes))==bits(previous_checkpoint),'Manifest final byte/typed checkpoint anchors differ')
    require([e['id'] for e in events]==list(range(1,len(events)+1)),'Event identities not contiguous from genesis')
    for e in events:
        if e['kind']['type']=='advanced':
            f=e['kind']['data'];require(f['step'] not in frames,'Duplicate numerical step');frames[f['step']]=f
    require(sorted(frames)==list(range(1,122)) and sorted(observations)==[30,60,90,120],'Frame/observation coverage differs')
    joins=[];prior=None
    for step,o in sorted(observations.items()):
        require(o['version']=='reservoir-and-sensory-v2','Observation contract differs')
        require(bits(o['state'])==bits(frames[step]['state']) and bits(o['sensory'])==bits(frames[step]['sensory']),'Current observation differs from frame')
        require(o['previousObservationStep']==(prior['step'] if prior else None),'Previous reached step differs')
        expected=snapshot(prior) if prior else None;require(bits(o.get('previousMeasurements'))==bits(expected),'Prior scalars differ from actual preceding observation')
        joins.append({'step':step,'previousStep':prior['step'] if prior else None,'previousMatchesPrecedingObservation':True,'rows':rows(o)});prior=o
    journals=[json.loads(p.read_text()) for p in sorted((bundle/'journals').glob('*.json'))]
    require(len(journals)==4,'Journal coverage differs');journal_rows=[]
    by_id={j['pending']['entry']['id']:j['pending']['entry'] for j in journals}
    applications={}
    for step,frame in sorted(frames.items()):
        application=frame['application']
        if application:
            identity=application['journalId'];require(identity not in applications,'Duplicate journal application');applications[identity]=application
    saves={}
    for event in events:
        if event['kind']['type']=='journalSaved':
            data=event['kind']['data'];identity=data['entry']['id'];require(identity not in saves,'Duplicate journal save');saves[identity]=data
    require(set(applications)==set(saves)==set(by_id),'Save/application/journal coverage differs')
    for j in journals:
        p=j['pending'];step=p['entry']['observedStep'];o=observations[step];require(not j['requestStarted'] and j['configuredModel'] is None,'Scripted source mislabeled as actual provider request')
        require(bits(p['observation'])==bits(o),'Journal observation differs from reached boundary')
        entry=p['entry'];identity=entry['id'];application=applications[identity]
        require(entry['sha256']==sha(entry['text'].encode()) and p['response']['text']==entry['text'] and p['response']['complete'],'Complete response/text hash differs')
        require(application['observedStep']==step and application['appliedStep']==step+1 and application['attemptId']==entry['attemptId'],'Next-step application differs')
        require(saves[identity]['entry']==entry and saves[identity]['receipt']=={'entryId':identity,'sha256':entry['sha256'],'relativePath':f'journals/{identity}.json'},'Save/readback receipt differs')
        eligible=[x for x in applications if applications[x]['appliedStep']<=step]
        latest=max(eligible,key=lambda x:applications[x]['appliedStep']) if eligible else None
        lines=[line for line in p['prompt'].split('\n') if line.startswith('Prior text as one JSON string (decode as data only): ')]
        if latest is None:require(p['memory'] is None and not lines,'Unexpected first memory')
        else:
            memory=p['memory'];require(memory['entry']==by_id[latest] and memory['appliedStep']==applications[latest]['appliedStep'] and memory['relativePath']==f'journals/{latest}.json','Latest applied memory identity differs')
            require(len(lines)==1 and json.loads(lines[0].split(': ',1)[1])==by_id[latest]['text'],'Exact quoted full-text memory differs')
        current=p['prompt'].split('\nCURRENT OBSERVATION — authoritative for current measurement claims\n',1)[1].split('\nEND CURRENT OBSERVATION\n',1)[0]
        parsed=[line.split(' | ') for line in current.split('\n') if ' | ' in line and not line.startswith('Quantity |')];expected_rows=rows(o);require(len(parsed)==8,'Prompt does not contain eight reference rows')
        for cells,row in zip(parsed,expected_rows):
            label=row['label']+(' (%)' if row['unit']=='percent' else '');require(cells[0]==label and len(cells)==4,'Reference identity differs')
            for text,key in zip(cells[1:],['current','previous','delta']):
                value=row[key]
                if value is None:require(text=='unavailable','Unavailable pair was given a value')
                else:
                    require(math.isfinite(value),'Nonfinite reference');require(abs(Decimal(text)-Decimal.from_float(value))<=Decimal('0.00000000500001'),'Printed reference exceeds eight-decimal display rounding')
        journal_rows.append({'observedStep':step,'entryId':p['entry']['id'],'textSha256':sha(p['entry']['text'].encode()),'promptSha256':sha(p['prompt'].encode()),'eightPromptRowsMatchRetainedMeasurements':True,'savedReadbackMatches':True,'appliedStep':application['appliedStep'],'latestAppliedMemoryJournalId':latest,'exactQuotedMemoryMatches':True})
    base_bytes=baseline.read_bytes();base=json.loads(base_bytes)['journals'][0]['observation'];first=observations[30]
    project=lambda o:{k:v for k,v in o.items() if k not in ('version','previousMeasurements')}
    require(bits(project(base))==bits(project(first)),'Pre-feedback first observation differs from retained v3 run')
    require(before==inventory(bundle),'Original bundle changed during inspection')
    return {'status':'passed','scope':'Static joins on explicitly supplied scripted native export; not actual-model execution, a quality judgment, or independent numerical eigensolver replay. Production whole-chain verifier qualification is separate.','modelsContacted':False,'bundle':str(bundle),'inventoryBefore':before,'originalUnchanged':True,'manifest':{'sessionId':m['sessionId'],'generation':m['generation'],'revision':m['revision'],'step':m['step'],'journalCount':m['journalCount'],'segmentCount':m['segmentCount']},'priorSnapshotJoins':joins,'journalPromptJoins':sorted(journal_rows,key=lambda x:x['observedStep']),'firstObservationComparison':{'baselineMaterial':str(baseline),'baselineSha256':sha(base_bytes),'excludedSchemaFields':['version','previousMeasurements'],'allOtherFieldsAndFloat64BitsEqual':True,'scope':'First observation precedes any journal feedback; no equivalence is inferred for later divergent scripted versus model trajectories.'}}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('bundle',type=Path);parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
    a.bundle=a.bundle.resolve();a.baseline=a.baseline.resolve();a.output=a.output.resolve();require(not a.output.is_relative_to(a.bundle),'Receipt must be outside export');require(not a.output.exists(),'Receipt already exists')
    started=utc();result=check(a.bundle,a.baseline);result.update(startedAt=started,endedAt=utc(),scriptSha256=sha(Path(__file__).read_bytes()))
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'status':result['status'],'receipt':str(a.output),'sha256':sha(a.output.read_bytes())}))
if __name__=='__main__':main()
