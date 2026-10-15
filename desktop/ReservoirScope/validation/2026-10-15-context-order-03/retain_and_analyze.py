#!/usr/bin/env python3
"""Closed, file-only context03 accounting. Never contacts services or reads prose semantically.
Copies exact source bytes to exclusive evidence directories; original ledger paths stay intact.
Provider bookkeeping and original-group cleanup remain source assertions, not authenticity,
context coverage, fresh post-reap process absence, or writing-quality evidence.
"""
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import stat

HERE=Path(__file__).resolve().parent
DESKTOP=HERE.parents[1]
RUN=DESKTOP/'target/qa/0.20-context-order-results03'
SERVICE=DESKTOP/'target/qa/0.20-context-order-gemma3-4b-run03'
LEDGER_SHA='fe49740ff34ecaba9cf38d484a134bcc81ae7fa60706a4917d09be00a231a851'
MAX_BYTES=64*1024*1024
ORDER=[(step,c) for i,step in enumerate(range(60,361,60)) for c in ('AB' if i%2==0 else 'BA')]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(condition,message):
    if not condition:raise ValueError(message)
def data(path):
    require(path.is_absolute() and path==path.resolve(strict=True),'Noncanonical evidence path')
    require(stat.S_ISREG(path.lstat().st_mode),'Nonordinary evidence file')
    require(path.stat().st_size<=MAX_BYTES,'Evidence file exceeds bound')
    return path.read_bytes()
def identity(path):
    raw=data(path);return dict(path=str(path),bytes=len(raw),sha256=sha(raw))
def read(path):return json.loads(data(path))
def canonical(doc):return json.dumps(doc,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def inventory(root):
    require(root==root.resolve(strict=True) and root.is_dir(),'Noncanonical evidence directory')
    files=[]
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink(),'Symlink evidence refused')
        if p.is_dir():continue
        require(len(files)<128,'Evidence file count bound')
        row=identity(p);row['relativePath']=p.relative_to(root).as_posix();files.append(row)
    require(sum(x['bytes'] for x in files)<=MAX_BYTES,'Evidence directory exceeds retained limit')
    return files
def bound(ref,root=None):
    p=Path(ref['path'])
    if root is not None:require(p.parent==root,'Unexpected evidence-reference directory')
    raw=data(p);require(len(raw)==ref['bytes'] and sha(raw)==ref['sha256'],'Evidence identity mismatch')
    return raw
def preserve(source,destination,before):
    destination.mkdir(mode=0o700,exist_ok=False)
    for ref in before:
        p=destination/ref['relativePath'];p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(bound(ref,source))
    after=inventory(source);require(before==after,'Original evidence changed during copy')
    copied=inventory(destination)
    require([(r['relativePath'],r['bytes'],r['sha256']) for r in before]==[(r['relativePath'],r['bytes'],r['sha256']) for r in copied],'Copied evidence differs')
    return dict(sourceDirectory=str(source),copyDirectory=str(destination),sourceBefore=before,sourceAfter=after,copies=copied,sourceUnchanged=True,byteExact=True,fileCount=len(before),logicalBytes=sum(r['bytes'] for r in before))

def main():
    receipt_path=HERE/'run-analysis-01.json'
    with receipt_path.open('x') as output:
        report=dict(schema='reservoir-context-order-closed-analysis-v1',atUtc=dt.datetime.now(dt.timezone.utc).isoformat(),status='running',errors=[],script=identity(Path(__file__).resolve()),scope='File-only accounting of closed owned sources; no runtime/verifier/process/network invocation or prose interpretation.')
        try:
            original_run=inventory(RUN);original_service=inventory(SERVICE)
            expected_run={'input-identities.json','inventory-response.bin','ledger.json','ownership.json'}|{f'slot-{i:02}-{part}' for i in range(1,13) for part in ('request.json','response.bin','text.txt')}
            require({x['relativePath'] for x in original_run}==expected_run,'Unexpected runner file set')
            require({x['relativePath'] for x in original_service}=={'endpoint.json','launch-intent.json','owned-process.json','service.log','stop-request','supervision-result.json'},'Unexpected service file set')
            require(identity(RUN/'ledger.json')['sha256']==LEDGER_SHA,'Handed-off ledger mismatch')
            report['runRetention']=preserve(RUN,HERE/'run-output-01',original_run)
            report['serviceRetention']=preserve(SERVICE,HERE/'service-output-01',original_service)
            report['ledger']=identity(RUN/'ledger.json')
            ledger=read(RUN/'ledger.json');inputs=read(HERE/'frozen-inputs.json');plan=read(HERE/'run-plan.json')
            require(identity(HERE/'run-plan.json')==inputs['runPlan'],'Frozen plan identity mismatch')
            require(ledger['schema']=='reservoir-context-order-run-v1' and ledger['episodeId']==plan['episodeId']=='context-order-03','Episode identity mismatch')
            require(ledger['status']=='completed' and ledger['stopReason']=='all_twelve_completed','Not a completed12 response ledger')
            require(ledger['completedCount']==12 and ledger['unstartedCount']==0 and ledger['inputIdentitiesUnchanged'] is True,'Ledger summary mismatch')
            require(len(ledger['slots'])==len(inputs['slots'])==12,'Twelve slots required')
            require(ledger['elapsedSeconds']<=plan['probeBudgetSeconds'],'Probe duration exceeded')
            require(ledger['serviceRemainingAtProbeStartSeconds']>=plan['minimumServiceRemainingAtStart'],'Start margin missed')
            inventory_meta=ledger['inventory'];require(inventory_meta['method']=='GET' and inventory_meta['path']=='/api/tags' and inventory_meta['status']==200 and inventory_meta['error'] is None and not inventory_meta['responseTruncated'],'Readiness metadata mismatch')
            require(inventory_meta['elapsedSeconds']<=plan['inventoryDeadlineSeconds'],'Inventory deadline exceeded')
            raw_inventory=bound(inventory_meta['raw'],RUN);models=json.loads(raw_inventory)['models'];selected=[r for r in models if r['name']==plan['model']]
            require(len(selected)==1 and selected[0]['digest']==plan['modelManifestSha256'],'Inventory exact identity mismatch')
            per_slot=[];durations=[];tokens=[];prompt_tokens=[]
            for i,(slot,frozen,(step,condition)) in enumerate(zip(ledger['slots'],inputs['slots'],ORDER),1):
                require(slot['slot']==frozen['slot']==i and slot['anchorStep']==frozen['anchorStep']==step and slot['condition']==frozen['condition']==condition,'Request order mismatch')
                prompt=bound(frozen['prompt']).decode('utf-8')
                expected_body=canonical({'model':plan['model'],'stream':False,'messages':[{'role':'user','content':prompt}],'options':{'num_ctx':plan['contextTokens'],'num_predict':plan['outputTokens'],'temperature':plan['temperature']}})
                require(bound(slot['request'],RUN)==expected_body,'Exact app-style request body/prompt changed')
                raw=bound(slot['response'],RUN);response=json.loads(raw);text=response['message']['content'];require(type(text)is str,'Response content type invalid')
                require(bound(slot['text'],RUN)==text.encode('utf-8'),'Exact decoded full-text copy mismatch')
                ex=slot['exchange'];parsed=slot['parsed']
                require(ex['method']=='POST' and ex['path']=='/api/chat' and ex['status']==200 and ex['error'] is None and not ex['responseTruncated'],'Generation HTTP mismatch')
                require(len(raw)<=1024*1024 and ex['rawBytes']==len(raw) and ex['rawSha256']==sha(raw),'Response bound/hash mismatch')
                require(ex['deadlineSeconds']==plan['requestDeadlineSeconds'] and ex['elapsedSeconds']<=plan['requestDeadlineSeconds'],'Generation deadline mismatch')
                require(plan['probeBudgetSeconds']-(ex['startedMonotonicSeconds']-ledger['startMonotonicSeconds'])>=plan['requestDeadlineSeconds'],'Insufficient full dispatch budget')
                count=response.get('eval_count');complete=response['done'] is True and response.get('done_reason')!='length' and (count is None or type(count)is int and 0<=count<=plan['outputTokens'])
                require(complete and parsed['transportComplete'] is True and slot['status']=='complete','Transport completeness mismatch')
                require(response.get('model') in (None,plan['model']) and parsed['providerModel']==response.get('model'),'Returned model mismatch')
                require(parsed['done']==response['done'] and parsed['stopReason']==response.get('done_reason') and parsed['tokenCount']==(str(count) if count is not None else None),'Typed completion bookkeeping mismatch')
                input_count=response.get('prompt_eval_count');require(type(input_count)is int and 0<=input_count<2**64,'Unexpected prompt bookkeeping shape')
                require(parsed['providerPromptEvaluation']=={'status':'reported','count':str(input_count)},'Prompt bookkeeping identity mismatch')
                durations.append(ex['elapsedSeconds']);tokens.append(count);prompt_tokens.append(input_count)
                per_slot.append(dict(slot=i,anchorStep=step,condition=condition,status=slot['status'],prompt=frozen['prompt'],request=slot['request'],response=slot['response'],text=slot['text'],elapsedSeconds=ex['elapsedSeconds'],providerOutputTokens=str(count),providerPromptEvaluationTokens=str(input_count),providerDoneReason=response.get('done_reason'),providerTotalDurationNanoseconds=str(response.get('total_duration')),providerLoadDurationNanoseconds=str(response.get('load_duration')),providerPromptEvalDurationNanoseconds=str(response.get('prompt_eval_duration')),providerEvalDurationNanoseconds=str(response.get('eval_duration'))))
            service=read(SERVICE/'supervision-result.json');proc=read(SERVICE/'owned-process.json');launch=read(SERVICE/'launch-intent.json');endpoint=read(SERVICE/'endpoint.json');cleanup=service['process']['cleanup']
            require(service['errors']==[] and service['reason']=='explicit stop','Owned supervisor error/reason mismatch')
            require(service['process']['pid']==proc['pid']==endpoint['pid'] and proc['pid']==proc['pgid']==proc['sid'],'Owned identity mismatch')
            require(service['endpointPort']==endpoint['port'],'Endpoint identity mismatch')
            require(cleanup['exitCode']==0 and cleanup['sigtermSentToOwnedGroup'] is True and cleanup['sigkillSentToOwnedGroup'] is False and cleanup['finalGroupBeforeReap']['quiescent'] is True,'Cleanup mismatch')
            require(service['conventionalMetadataUnchanged'] is True and service['conventionalMetadataBefore']==service['conventionalMetadataAfter'],'Conventional metadata changed')
            require(service['elapsedMonotonicSeconds']<=plan['serviceLifetimeSeconds']==launch['maximumLifetimeSeconds'],'Owned lifetime exceeded')
            require(proc['software']==launch['software'] and proc['software']['versionFromPlist']=='0.40.4','Software launch identity mismatch')
            require(proc['softwareSelection']['receipt']['sha256']==plan['softwareSelectionSha256'],'Software overlay mismatch')
            log=data(SERVICE/'service.log').decode('utf-8');http_lines=[line for line in log.splitlines() if '[GIN]' in line]
            request_log=[]
            for line in http_lines:
                m=re.search(r'\|\s*(\d{3})\s*\|.*\|\s*(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+"([^"]+)"',line)
                require(m is not None,'Unparsed HTTP service-log line')
                request_log.append(dict(status=int(m[1]),method=m[2],path=m[3]))
            require(request_log==[dict(status=200,method='GET',path='/api/tags')]+[dict(status=200,method='POST',path='/api/chat')]*12,'HTTP log sequence differs; extra/missing request')
            require(service['discardedLogBytes']==0 and service['retainedLogBytes']==len(data(SERVICE/'service.log')),'Service log truncation/size mismatch')
            require(f'Listening on 127.0.0.1:{endpoint["port"]} (version 0.40.4)' in log,'Actual listener/version log missing')
            freeze=read(HERE/'evaluation-freeze-01.json');require(len(freeze['files'])==572,'Freeze file count differs')
            freeze_errors=[r['path'] for r in freeze['files'] if identity(Path(r['path']))!=r]
            require(not freeze_errors,'Frozen inputs changed')
            copied=read(HERE/'copy-manifest-01.json');prior=copied['priorDirectoryAfter'];require(len(prior)==94,'Prior count mismatch')
            require(prior==copied['priorDirectoryBefore'] and prior==[identity(Path(r['path'])) for r in prior],'Prior episode inputs changed')
            require(inventory(RUN)==original_run and inventory(SERVICE)==original_service,'Closed source outputs changed after analysis')
            require(identity(Path(__file__).resolve())==report['script'],'Analysis source changed')
            report.update(status='passed',metadataOnly=True,runner=dict(status=ledger['status'],completeResponses=12,completePairs=6,unstarted=0,probeElapsedSeconds=ledger['elapsedSeconds'],serviceRemainingAtProbeStartSeconds=ledger['serviceRemainingAtProbeStartSeconds'],oneInventoryGet=True,generationPostCount=12,retriesObserved=0,requestBodiesAndFrozenPromptsExact=True,fullResponseTextCopiesExact=True,logicalRetainedBytes=sum(r['bytes'] for r in original_run),storageBudgetBytes=plan['storageBudgetBytes'],generationElapsedSeconds=dict(min=min(durations),max=max(durations),sum=sum(durations)),providerOutputTokenCounts=tokens,providerPromptEvaluationTokenCounts=prompt_tokens,slots=per_slot),ownedService=dict(pid=proc['pid'],pgid=proc['pgid'],sid=proc['sid'],supervisorPid=proc['directChildOfSupervisorPid'],endpoint=endpoint['endpoint'],softwareVersion='0.40.4',software=proc['software'],elapsedSeconds=service['elapsedMonotonicSeconds'],stopReason=service['reason'],sigtermSent=True,sigkillSent=False,quiescentBeforeLeaderReap=True,unreadableLeaderExitProven=cleanup['finalGroupBeforeReap']['unreadableLeaderExitProven'],exitCode=cleanup['exitCode'],conventionalMetadataUnchanged=True,credentialCheckLimit=service['credentialCheckLimit'],cleanupLimit=cleanup['cleanupLimit'],httpLog=request_log,logBytes=service['retainedLogBytes'],discardedLogBytes=0,errors=[]),preservation=dict(freeze=identity(HERE/'evaluation-freeze-01.json'),frozenFileCount=572,frozenFilesUnchanged=True,priorCopyManifest=identity(HERE/'copy-manifest-01.json'),priorFileCount=94,priorFilesUnchanged=True,sourceOutputFilesUnchanged=True),limits=['No prose was interpreted or printed by this analysis.','Provider token/duration counts are bookkeeping claims, not proof of full context processing.','Transport-complete does not mean app journal eligibility, save, numerical application or writing quality.','Cleanup proof covers original owned group before leader reap; no fresh process inventory or escaped-descendant claim.','No GPU, platform, endurance, causal writing or stable model-effect qualification.'])
        except Exception as error:
            report['status']='failed';report['errors'].append(f'{type(error).__name__}: {error}')
        report['endedAtUtc']=dt.datetime.now(dt.timezone.utc).isoformat()
        json.dump(report,output,indent=2);output.write('\n')
    print(json.dumps(dict(status=report['status'],errors=report['errors'],receipt=identity(receipt_path),runFiles=report.get('runRetention',{}).get('fileCount'),serviceFiles=report.get('serviceRetention',{}).get('fileCount'))))
    return 0 if report['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
