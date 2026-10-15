#!/usr/bin/env python3
"""Post-terminal file-only retention/accounting; never contacts or inventories processes.
No response prose is printed or interpreted. Requires root-supplied final hashes.
Exact copies preserve original ledger paths. Completion is transport-only; provider
bookkeeping and original-group cleanup assertions do not establish writing quality,
context coverage, fresh process absence, escaped-child cleanup, GPU or endurance.
"""
import argparse
import collections
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat

HERE=Path(__file__).resolve().parent
DESKTOP=HERE.parents[1]
RUN=DESKTOP/'target/qa/0.20-time-direction-results03'
SERVICE=DESKTOP/'target/qa/0.20-time-direction-gemma3-4b-run03'
MAX_BYTES=64*1024*1024
ORDER=[(step,c) for i,step in enumerate((30,60,90,120,330,360)) for c in ('AB' if i%2==0 else 'BA')]
TERMINAL={'completed','stopped','interrupted','refused_or_failed','failed_identity','refused_before_network'}

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
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-ledger-sha256',required=True)
    parser.add_argument('--expected-supervision-sha256',required=True)
    args=parser.parse_args()
    for value in (args.expected_ledger_sha256,args.expected_supervision_sha256):
        require(re.fullmatch('[0-9a-f]{64}',value) is not None,'Exact terminal SHA256 required')
    receipt_path=HERE/'run-analysis-01.json'
    with receipt_path.open('x') as output:
        report=dict(schema='reservoir-time-direction-closed-analysis-v1',atUtc=dt.datetime.now(dt.timezone.utc).isoformat(),status='running',errors=[],script=identity(Path(__file__).resolve()),scope='Closed explicit owned files only. No host/process/network/model/UI action or semantic prose reading.')
        try:
            require(identity(RUN/'ledger.json')['sha256']==args.expected_ledger_sha256,'Handed-off ledger mismatch')
            require(identity(SERVICE/'supervision-result.json')['sha256']==args.expected_supervision_sha256,'Handed-off supervisor result mismatch')
            ledger=read(RUN/'ledger.json');service=read(SERVICE/'supervision-result.json')
            require(ledger['status'] in TERMINAL and ledger.get('endedAtUtc'),'Runner is not terminal')
            require(service.get('reason') and 'elapsedMonotonicSeconds' in service,'Supervisor lacks terminal evidence')
            original_run=inventory(RUN);original_service=inventory(SERVICE)
            require({r['relativePath'] for r in original_service}=={'endpoint.json','launch-intent.json','owned-process.json','service.log','stop-request','supervision-result.json'},'Unexpected service file set')
            allowed={'ledger.json','input-identities.json','inventory-response.bin','ownership.json'}|{f'slot-{i:02}-{part}' for i in range(1,13) for part in ('request.json','response.bin','text.txt')}
            require({r['relativePath'] for r in original_run}<=allowed,'Unexpected runner file set')
            report['runRetention']=preserve(RUN,HERE/'run-output-01',original_run)
            report['serviceRetention']=preserve(SERVICE,HERE/'service-output-01',original_service)
            report['ledger']=identity(RUN/'ledger.json')
            inputs=read(HERE/'frozen-inputs.json');plan=read(HERE/'run-plan.json')
            require(inputs['runPlan']==identity(HERE/'run-plan.json'),'Plan identity mismatch')
            require(plan['ownedServiceDirectory']==str(SERVICE) and plan['provenance']['resultsDirectory']==str(RUN),'Owned path mismatch')
            require(ledger['schema']=='reservoir-time-direction-run-v1' and ledger.get('episodeId')==plan['episodeId']=='time-direction-03','Episode identity mismatch')
            require(len(ledger['slots'])==len(inputs['slots'])==12,'All twelve slots must be retained')
            require(ledger.get('inputIdentitiesUnchanged') is True,'Runner did not confirm retained input identities')
            require(ledger['elapsedSeconds']<=plan['probeBudgetSeconds'],'Probe budget exceeded')
            require(ledger['serviceRemainingAtProbeStartSeconds']>=plan['minimumServiceRemainingAtStart'],'Actual start margin missed')
            spec=importlib.util.spec_from_file_location('retained_probe_decoder',HERE/'run_probe.py')
            probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
            expected_files={'ledger.json','input-identities.json','ownership.json'}
            for ref in read(RUN/'input-identities.json'):bound(ref)
            inventory_meta=ledger.get('inventory');expected_http=[]
            if inventory_meta is not None:
                expected_files.add('inventory-response.bin');raw=bound(inventory_meta['raw'],RUN)
                require(inventory_meta['method']=='GET' and inventory_meta['path']=='/api/tags','Wrong inventory route')
                require(len(raw)<=1024*1024,'Inventory bound exceeded')
                expected_http.append(dict(status=inventory_meta['status'],method='GET',path='/api/tags'))
                if inventory_meta['error'] is None:
                    require(200<=inventory_meta['status']<300 and not inventory_meta['responseTruncated'],'Inventory HTTP failure')
                    require(probe.decode_inventory(raw,plan)==inventory_meta['selected'],'Exact inventory model/digest mismatch')
            statuses=collections.Counter();durations=[];output_tokens=[];prompt_evidence=[];slot_metrics=[];posts=0;stopped=False
            for number,(slot,frozen,(step,condition)) in enumerate(zip(ledger['slots'],inputs['slots'],ORDER),1):
                require(slot['slot']==frozen['slot']==number and slot['anchorStep']==frozen['anchorStep']==step and slot['condition']==frozen['condition']==condition,'Fixed slot order mismatch')
                statuses[slot['status']]+=1
                prompt=bound(frozen['prompt']).decode('utf-8')
                prefix=f'slot-{number:02}'
                if slot.get('request'):
                    expected_files.add(prefix+'-request.json')
                    require(bound(slot['request'],RUN)==probe.request_body(prompt,plan),'Exact request body/prompt changed')
                exchange=slot.get('exchange')
                metric=dict(slot=number,status=slot['status'])
                if exchange is not None:
                    require(not stopped,'Request followed a failed/incomplete or unstarted slot')
                    posts+=1;expected_files.add(prefix+'-response.bin')
                    require(slot.get('request') is not None and slot.get('response') is not None,'Exchange lacks physical request/response evidence')
                    raw=bound(slot['response'],RUN)
                    require(exchange['method']=='POST' and exchange['path']=='/api/chat','Wrong generation route')
                    require(len(raw)<=1024*1024 and exchange['rawBytes']==len(raw) and exchange['rawSha256']==sha(raw),'Response bound/hash mismatch')
                    require(exchange['deadlineSeconds']==plan['requestDeadlineSeconds'],'Request deadline changed')
                    require(plan['probeBudgetSeconds']-(exchange['startedMonotonicSeconds']-ledger['startMonotonicSeconds'])>=plan['requestDeadlineSeconds'],'Dispatch lacked full remaining request budget')
                    expected_http.append(dict(status=exchange['status'],method='POST',path='/api/chat'))
                    durations.append(exchange['elapsedSeconds'])
                    metric.update(httpStatus=exchange['status'],elapsedSeconds=exchange['elapsedSeconds'],transportError=exchange['error'],responseTruncated=exchange['responseTruncated'])
                    if slot.get('parsed') is not None:
                        require(exchange['error'] is None and 200<=exchange['status']<300 and not exchange['responseTruncated'],'Parsed success contradicts HTTP evidence')
                        text,parsed=probe.decode_response(raw,plan)
                        require(parsed==slot['parsed'],'Typed response metadata mismatch')
                        expected_files.add(prefix+'-text.txt')
                        require(bound(slot['text'],RUN)==text.encode('utf-8'),'Full decoded text bytes differ')
                        require(slot['status']==('complete' if parsed['transportComplete'] else 'incomplete'),'Completion predicate differs')
                        require(exchange['elapsedSeconds']<=plan['requestDeadlineSeconds'],'Successful response exceeded deadline')
                        output_tokens.append(parsed['tokenCount']);prompt_evidence.append(parsed['providerPromptEvaluation'])
                        metric.update(providerDone=parsed['done'],providerStopReason=parsed['stopReason'],providerOutputTokens=parsed['tokenCount'],providerPromptEvaluation=parsed['providerPromptEvaluation'],transportComplete=parsed['transportComplete'])
                if slot['status']!='complete':stopped=True
                slot_metrics.append(metric)
            require({r['relativePath'] for r in original_run}==expected_files,'Unaccounted runner files')
            require(statuses['complete']==ledger['completedCount'] and statuses['unstarted']==ledger['unstartedCount'],'Ledger totals differ')
            if ledger['status']=='completed':require(statuses['complete']==12 and ledger['stopReason']=='all_twelve_completed','Completed ledger is not complete')
            proc=read(SERVICE/'owned-process.json');launch=read(SERVICE/'launch-intent.json');endpoint=read(SERVICE/'endpoint.json');cleanup=service['process']['cleanup']
            require(service['errors']==[] and service['reason']=='explicit stop','Supervisor reported errors or unexpected stop')
            require(service['process']['pid']==proc['pid']==endpoint['pid'] and proc['pid']==proc['pgid']==proc['sid'],'Owned process identity mismatch')
            require(service['endpointPort']==endpoint['port'],'Endpoint mismatch')
            require(cleanup['exitCode']==0 and cleanup['finalGroupBeforeReap']['quiescent'] is True,'Original owned group did not report clean quiescence')
            require(service['conventionalMetadataUnchanged'] is True and service['conventionalMetadataBefore']==service['conventionalMetadataAfter'],'Conventional metadata changed')
            require(service['elapsedMonotonicSeconds']<=plan['serviceLifetimeSeconds']==launch['maximumLifetimeSeconds'],'Owned lifetime exceeded')
            require(proc['software']==launch['software'] and proc['software']['versionFromPlist']=='0.40.4','Software launch identity mismatch')
            require(proc['softwareSelection']['receipt']['sha256']==plan['softwareSelectionSha256'],'Software overlay mismatch')
            log_bytes=data(SERVICE/'service.log');log=log_bytes.decode('utf-8');request_log=[]
            for line in log.splitlines():
                if '[GIN]' not in line:continue
                match=re.search(r'\|\s*(\d{3})\s*\|.*\|\s*(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+"([^"]+)"',line)
                require(match is not None,'Unparsed HTTP service log record')
                request_log.append(dict(status=int(match[1]),method=match[2],path=match[3]))
            # A terminal failed socket can lack a server access record; preserve that as a discrepancy.
            log_matches=request_log==expected_http
            require(log_matches,'Service access log differs from retained exchanges; inspect without inventing retries')
            require(service['discardedLogBytes']==0 and service['retainedLogBytes']==len(log_bytes),'Service log incomplete')
            require(f'Listening on 127.0.0.1:{endpoint["port"]} (version 0.40.4)' in log,'Actual listener/version log missing')
            freeze=read(HERE/'evaluation-freeze-01.json');require(len(freeze['files'])==762,'Unexpected frozen file count')
            for ref in freeze['files']:require(identity(Path(ref['path']))==ref,'Frozen input changed')
            copied=read(HERE/'runtime-copy-01.json');prior=copied['priorDirectoryAfter'];require(len(prior)==285,'Unexpected prior file count')
            require(prior==copied['priorDirectoryBefore'] and prior==[identity(Path(r['path'])) for r in prior],'Prior evidence changed')
            require(inventory(RUN)==original_run and inventory(SERVICE)==original_service,'Closed source outputs changed during analysis')
            require(identity(Path(__file__).resolve())==report['script'],'Analysis script changed')
            complete_pairs=sum(all(s['status']=='complete' for s in ledger['slots'][i:i+2]) for i in range(0,12,2))
            report.update(status='passed',metadataOnly=True,runner=dict(status=ledger['status'],stopReason=ledger['stopReason'],completeResponses=statuses['complete'],completePairs=complete_pairs,slotStatuses=dict(statuses),probeElapsedSeconds=ledger['elapsedSeconds'],serviceRemainingAtProbeStartSeconds=ledger['serviceRemainingAtProbeStartSeconds'],inventoryGetCount=int(inventory_meta is not None),generationPostCount=posts,retriesObserved=0,requestBodiesAndFrozenPromptsExact=True,fullDecodedTextCopiesExact=True,logicalRetainedBytes=sum(r['bytes'] for r in original_run),storageBudgetBytes=plan['storageBudgetBytes'],generationElapsedSeconds=dict(min=min(durations) if durations else None,max=max(durations) if durations else None,sum=sum(durations)),providerOutputTokenCounts=output_tokens,providerPromptEvaluation=prompt_evidence,slots=slot_metrics),ownedService=dict(pid=proc['pid'],pgid=proc['pgid'],sid=proc['sid'],supervisorPid=proc['directChildOfSupervisorPid'],endpoint=endpoint['endpoint'],softwareVersion='0.40.4',elapsedSeconds=service['elapsedMonotonicSeconds'],stopReason=service['reason'],sigtermSent=cleanup['sigtermSentToOwnedGroup'],sigkillSent=cleanup['sigkillSentToOwnedGroup'],quiescentBeforeLeaderReap=True,unreadableLeaderExitProven=cleanup['finalGroupBeforeReap']['unreadableLeaderExitProven'],exitCode=cleanup['exitCode'],conventionalMetadataUnchanged=True,credentialCheckLimit=service['credentialCheckLimit'],cleanupLimit=cleanup['cleanupLimit'],httpLog=request_log,logMatchesRetainedExchanges=log_matches,logBytes=len(log_bytes),discardedLogBytes=0,errors=[]),preservation=dict(freeze=identity(HERE/'evaluation-freeze-01.json'),frozenFileCount=762,frozenFilesUnchanged=True,priorCopyManifest=identity(HERE/'runtime-copy-01.json'),priorFileCount=285,priorFilesUnchanged=True,sourceOutputFilesUnchanged=True),limits=['No prose interpreted or printed; per-slot metadata is not a masked reading.', 'Provider token counts are bookkeeping, not full-context coverage proof.', 'Transport completeness is separate from app journal/save/feedback eligibility.', 'Cleanup covers original owned group before leader reap, not fresh post-reap absence or escaped descendants.', 'No causal writing, GPU, endurance or broad platform claim.'])
        except Exception as error:
            report['status']='failed';report['errors'].append(f'{type(error).__name__}: {error}')
        report['endedAtUtc']=dt.datetime.now(dt.timezone.utc).isoformat()
        json.dump(report,output,indent=2);output.write('\n')
    print(json.dumps(dict(status=report['status'],errors=report['errors'],receipt=identity(receipt_path),runFiles=report.get('runRetention',{}).get('fileCount'),serviceFiles=report.get('serviceRetention',{}).get('fileCount'))))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())

