"""Read-only latest-100 Astrid discovery survey; writes only this research packet.

No model calls, live state writes, database imports, or S-007 cursor updates.
Selection uses filename time; file mtimes bound supplementary receipt discovery.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
LIVE = Path('/Users/v/other/astrid/capsules/spectral-bridge/workspace')
OUT = ROOT / 'research/outputs/2026-09-15-astrid-study-survey'
if (Path(__file__).resolve().parent / 'protocol.json').is_file():
    OUT = Path(__file__).resolve().parent  # Offline verification from a sealed copy.
CUTOFF = datetime.fromisoformat('2026-09-15T16:30:41+00:00').timestamp()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    path.chmod(0o600)


def utc(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat()


def response(data):
    if data.get('choices'):
        return data['choices'][0].get('message', {}).get('content') or ''
    return data.get('message', {}).get('content') or data.get('response') or ''


def wire(data):
    data = data.get('attempt', data)
    return json.loads(data.get('request_json') or '{}'), json.loads(data.get('response_json') or '{}')


def capture():
    assert not (OUT / 'protocol.json').exists(), 'Refusing to replace frozen cohort'
    write(OUT / 'protocol.json', {
        'cutoff_utc': utc(CUTOFF),
        'selection': 'Latest 100 top-level SELF_STUDY journals by filename epoch <= cutoff, chronological without content filtering. Latest 20 astrid/dialogue_longform journals in the same span form a separately labelled dialogue context sample.',
        'discovery': 'Exploratory, not blinded or causal. Recent release findings and two post-release responses were known before selection. No new cohort bodies read before protocol freeze.',
        'receipt_frame': 'Shared and accepted receipts with mtime in [first journal minus 600 seconds, cutoff]. One directory level, no cap on eligible files. All filename-selected job metadata in this interval; self-study job companions retained.',
        'limits': 'Existing top-level completed journals, not all opportunities. Stable individual files, not atomic snapshot. Receipt mtime is an observed clock, not authenticated preparation time. No induced studies or live writes.'})
    inventory = []
    for item in os.scandir(LIVE / 'journal'):
        m = re.fullmatch(r'!?(.+)_(\d+)\.txt', item.name)
        if item.is_file(follow_symlinks=False) and m and int(m[2]) <= CUTOFF:
            inventory.append(dict(path=item.path, name=item.name, mode=m[1], epoch=int(m[2]), bytes=item.stat().st_size, mtime_ns=item.stat().st_mtime_ns))
    selected = sorted((r for r in inventory if r['mode'] == 'self_study'), key=lambda r:(r['epoch'],r['name']))[-100:]
    assert len(selected) == 100
    lower = selected[0]['epoch']
    context = sorted((r for r in inventory if r['mode'] in {'astrid','dialogue_longform'} and r['epoch'] >= lower), key=lambda r:(r['epoch'],r['name']))[-20:]
    write(OUT / 'selection.json', dict(entries=selected, context_entries=context, start_epoch=lower, end_epoch=CUTOFF))
    write(OUT / 'journal-inventory.json', [r for r in inventory if r['epoch'] >= lower])
    retained, errors, scans = {}, [], []

    def retain(src, kind):
        src = Path(src)
        if str(src) in retained:
            return retained[str(src)]['retained']
        try:
            before = src.stat()
            assert not src.is_symlink() and before.st_size <= 12_000_000
            raw = src.read_bytes()
            after = src.stat()
            assert (before.st_size,before.st_mtime_ns,before.st_ino) == (after.st_size,after.st_mtime_ns,after.st_ino)
            digest = sha(raw)
            rel = Path('raw') / kind / (digest + src.suffix)
            dest = OUT / rel
            dest.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            dest.write_bytes(raw); dest.chmod(0o600)
            retained[str(src)] = dict(source=str(src), retained=str(rel), kind=kind, sha256=digest, bytes=len(raw), mtime_ns=before.st_mtime_ns)
            return str(rel)
        except (OSError, AssertionError) as exc:
            errors.append(dict(source=str(src), error=repr(exc)))
            return None

    for row in selected + context:
        retain(row['path'], 'journal' if row['mode']=='self_study' else 'dialogue')
    shared = LIVE / 'diagnostics/source_first_v3/shared_reader'
    for kind, directory in [('shared',shared/'deliveries'),('navigation',shared/'navigation'),('provider',LIVE/'diagnostics/accepted_deliveries')]:
        count, eligible, kept = 0, 0, 0
        for entry in os.scandir(directory):
            candidates = [entry] if entry.is_file(follow_symlinks=False) else list(os.scandir(entry.path)) if entry.is_dir(follow_symlinks=False) else []
            for item in candidates:
                count += 1
                if not item.is_file(follow_symlinks=False) or not item.name.endswith('.json') or not lower-600 <= item.stat().st_mtime <= CUTOFF:
                    continue
                eligible += 1
                if kind == 'provider':
                    try:
                        data = json.loads(Path(item.path).read_text())
                        req, _ = wire(data)
                        if not any('You are studying the source of your system' in str(m.get('content','')) for m in req.get('messages',[])):
                            continue
                    except (OSError,ValueError) as exc:
                        errors.append(dict(source=item.path,error=repr(exc)))
                        continue
                if retain(item.path,kind):
                    kept += 1
        scans.append(dict(kind=kind, metadata_scanned=count, eligible_by_mtime=eligible, retained=kept))
    jobs = []
    for item in os.scandir(LIVE/'llm_jobs/jobs'):
        m = re.search(r'_(\d{13})_',item.name)
        if not m or not lower-600 <= int(m[1])/1000 <= CUTOFF or not item.is_dir(follow_symlinks=False):
            continue
        p = Path(item.path)/'job.json'
        rel = retain(p,'job')
        if rel:
            data = json.loads((OUT/rel).read_text())
            jobs.append(dict(path=str(p), retained=rel, call_kind=data.get('call_kind'), status=data.get('status')))
            if 'study' in json.dumps(data).lower():
                for name in ['prompt.txt','result.txt','phase_timings.json','events.jsonl']:
                    p = Path(item.path)/name
                    if p.exists():
                        retain(p,'job-companion')
    write(OUT/'job-frame.json',jobs)
    for p in [shared/'reader-v1.json',LIVE/'runtime/astrid_autonomous_source_status.json',LIVE/'runtime/llm_jobs_status.json',LIVE.parents[2]/'.runtime/bridge-deployment/active.json']:
        if p.is_file():
            retain(p,'runtime-observed-after-cutoff')
    write(OUT/'capture-index.json',dict(captured_utc=utc(datetime.now(timezone.utc).timestamp()), files=list(retained.values()),scans=scans,errors=errors))
    print(json.dumps(dict(selected=len(selected),context=len(context),start=utc(lower),last=utc(selected[-1]['epoch']),retained=len(retained),scans=scans,errors=errors),indent=2))


def analyze():
    index=json.loads((OUT/'capture-index.json').read_text())
    by_source={r['source']:r for r in index['files']}
    shared=[]; providers=[]
    for r in index['files']:
        if r['kind'] not in {'shared','navigation','provider'}:
            continue
        data=json.loads((OUT/r['retained']).read_text()); req,resp=wire(data)
        (providers if r['kind']=='provider' else shared).append((r,data,req,resp,response(resp)))
    rows=[]
    selected=json.loads((OUT/'selection.json').read_text())['entries']
    for i,j in enumerate(selected,1):
        jr=by_source[j['path']]; body=(OUT/jr['retained']).read_text()
        content_matches=[x for x in shared if x[4] and x[4] in body]
        # Identical text can recur across distinct generations. A hash alone is
        # not an identity. Preserve candidate counts and the temporal assumption.
        previous=selected[i-2]['mtime_ns'] if i>1 else (j['epoch']-600)*1e9
        matches=[x for x in content_matches if previous < x[0]['mtime_ns'] <= j['mtime_ns']]
        row=dict(ordinal=i,**j,journal=jr['retained'],exact_content_candidates=len(content_matches),shared_matches=len(matches),join_method='exact full response plus unique shared receipt mtime after preceding selected journal and before this journal; timestamp-assisted association, not durable journal generation ID')
        if len(matches)==1:
            record,data,req,resp,content=matches[0]
            output=data.get('output') or {}
            user='\n'.join(str(m.get('content','')) for m in req.get('messages',[]) if m.get('role')=='user')
            system='\n'.join(str(m.get('content','')) for m in req.get('messages',[]) if m.get('role')=='system')
            pm=[x for x in providers if x[4]==content and x[2].get('messages')==req.get('messages')]
            row.update(shared=record['retained'],input_kind=output.get('input_kind'),page=output.get('page') or data.get('page'),session_pages=output.get('session_pages'),question_id=output.get('question_id'),navigation_id=output.get('navigation_id'),output_heading=(output.get('text') or '').splitlines()[:1],response_sha256=sha(content.encode()),response_chars=len(content),response_words=len(content.split()),system_sha256=sha(system.encode()),provider_matches=len(pm),providers=[p[0]['retained'] for p in pm],usage=resp.get('usage'),finish_reason=(resp.get('choices') or [{}])[0].get('finish_reason'),model=resp.get('model'),requested_controls={k:v for k,v in req.items() if k not in {'messages','model'}},next_lines=re.findall(r'^NEXT:\s*(.*)$',content,re.M),note_updates=re.findall(r'^STUDY_NOTE:\s*(.*)$',content,re.M),question_updates=re.findall(r'^STUDY_QUESTION:\s*(.*)$',content,re.M))
            for suffix,text in [('response',content),('input',user),('system',system)]:
                p=OUT/'readings'/f'{i:03d}-{suffix}.txt';p.parent.mkdir(exist_ok=True,mode=0o700);p.write_text(text);p.chmod(0o600)
        rows.append(row)
    write(OUT/'linked-sequence.json',rows)
    summary=dict(count=len(rows),exact_content_and_temporal_shared_joins=sum(r['shared_matches']==1 for r in rows),exact_unique_provider_wire_joins=sum(r.get('provider_matches')==1 for r in rows),input_kinds=dict(Counter(r.get('input_kind') for r in rows)),finishes=dict(Counter(r.get('finish_reason') for r in rows)),system_hashes=dict(Counter(r.get('system_sha256') for r in rows)),source_paths=dict(Counter((r.get('page') or {}).get('source') for r in rows)),note_updates=sum(len(r.get('note_updates',[])) for r in rows),question_updates=sum(len(r.get('question_updates',[])) for r in rows),words={k:f([r['response_words'] for r in rows if 'response_words' in r]) for k,f in [('min',min),('median',statistics.median),('max',max)]})
    write(OUT/'summary.json',summary);print(json.dumps(summary,indent=2))


def metrics():
    rows=json.loads((OUT/'linked-sequence.json').read_text())
    details=[]
    for row in rows:
        d=json.loads((OUT/row['shared']).read_text());req,resp=wire(d)
        user=(OUT/'readings'/f"{row['ordinal']:03d}-input.txt").read_text()
        notebook_start=user.index('\n{',user.index('RECALLED ACCOUNT'))+1
        notebook,_=json.JSONDecoder().raw_decode(user[notebook_start:])
        choice_start=user.index('\n{',user.index('PREVIOUS RESPONSE CHOICE'))+1
        choice,_=json.JSONDecoder().raw_decode(user[choice_start:])
        accounts=[v for v in [notebook.get('previous'),*notebook.get('recent',[])] if v]
        out=d['output']['text']
        fresh=out.split('RECALLED ACCOUNT')[0]
        if 'Shared system map' in fresh:
            fresh=fresh[fresh.index('Shared system map'):].rstrip()
        details.append(dict(ordinal=row['ordinal'],next=row['next_lines'],input_kind=row['input_kind'],request_sha256=sha(d['request_json'].encode()),response_wire_sha256=sha(d['response_json'].encode()),input_sha256=sha(user.encode()),fresh_view_sha256=sha(fresh.encode()),response_sha256=row['response_sha256'],system_sha256=row['system_sha256'],note=notebook.get('note'),question=notebook.get('question'),account_count=len(accounts),complete_accounts=sum(a.get('complete') is True for a in accounts),choice=choice,server=resp.get('coupled_generation_v1'),qos=resp.get('model_qos_timing_v1'),usage=resp.get('usage'),requested_max_tokens=req.get('max_tokens'),journal_bytes=row['bytes'],response_words=row['response_words']))
    distribution=lambda xs:dict(min=min(xs),median=statistics.median(xs),max=max(xs))
    summary=dict(
        tokens=distribution([r['usage']['completion_tokens'] for r in details]),
        prompt_tokens=distribution([r['usage']['prompt_tokens'] for r in details]),
        journal_bytes=distribution([r['journal_bytes'] for r in details]),
        requested_max_tokens=dict(Counter(r['requested_max_tokens'] for r in details)),
        server_max_tokens=dict(Counter(r['server']['controls']['max_tokens'] for r in details)),
        server_termination=dict(Counter(r['server']['termination']['kind'] for r in details)),
        server_filters=dict(Counter(json.dumps(r['server']['controls']['active_filters']) for r in details)),
        server_temperatures=dict(Counter(r['server']['controls']['temperature'] for r in details)),
        server_thinking=dict(Counter(r['server']['controls']['thinking'] for r in details)),
        server_coupling=dict(Counter(r['server']['controls']['reservoir_coupling_strength'] for r in details)),
        unique_responses=len({r['response_sha256'] for r in details}),
        unique_requests=len({r['request_sha256'] for r in details}),
        unique_inputs=len({r['input_sha256'] for r in details}),
        distinct_fresh_map_views=len({r['fresh_view_sha256'] for r in details if r['input_kind']=='map'}),
        nexts=dict(Counter(r['next'][0] for r in details)),
        full_account_counts=dict(Counter((r['account_count'],r['complete_accounts']) for r in details)),
        question_texts=dict(Counter((r['question'] or {}).get('text') for r in details)),
        previous_choice_chains=sum(b['choice']['request_sha256']==a['request_sha256'] and b['choice']['response_sha256']==a['response_wire_sha256'] for a,b in zip(details,details[1:])),
        previous_choice_chain_denominator=len(details)-1,
        previous_choice_limit='Matches identify the preceding study response, not that its choice was the latest across all interleaved modes, queued, or executed.',
        queue_ms=distribution([r['qos']['queue_wait_ms'] for r in details]),
        active_generation_and_reservoir_ms=distribution([r['qos']['active_generation_and_reservoir_ms'] for r in details]),
    )
    summary['full_account_counts']={str(k):v for k,v in summary['full_account_counts'].items()}
    write(OUT/'metrics-details.json',details);write(OUT/'metrics.json',summary);print(json.dumps(summary,indent=2))


def verify():
    index=json.loads((OUT/'packet-index.json').read_text())
    for row in index['files']:
        raw=(OUT/row['path']).read_bytes()
        assert len(raw)==row['bytes'] and sha(raw)==row['sha256'],row['path']
    capture=json.loads((OUT/'capture-index.json').read_text())
    for row in capture['files']:
        raw=(OUT/row['retained']).read_bytes()
        assert len(raw)==row['bytes'] and sha(raw)==row['sha256'],row['retained']
    rows=json.loads((OUT/'linked-sequence.json').read_text())
    details=json.loads((OUT/'metrics-details.json').read_text())
    assert len(rows)==len(details)==100
    assert len({r['shared'] for r in rows})==100
    previous=(rows[0]['epoch']-600)*1e9
    retained={r['retained']:r for r in capture['files']}
    for row,detail in zip(rows,details):
        d=json.loads((OUT/row['shared']).read_text());req,resp=wire(d)
        text=response(resp)
        assert text in (OUT/row['journal']).read_text()
        assert text==(OUT/'readings'/f"{row['ordinal']:03d}-response.txt").read_text()
        assert previous<retained[row['shared']]['mtime_ns']<=row['mtime_ns']
        assert row['response_sha256']==sha(text.encode())==detail['response_sha256']
        assert detail['request_sha256']==sha(d['request_json'].encode())
        assert detail['response_wire_sha256']==sha(d['response_json'].encode())
        provider=json.loads((OUT/row['providers'][0]).read_text())
        assert provider['accepted_completion']==text
        assert wire(provider)==(req,resp)
        assert resp['coupled_generation_v1']['completion_tokens']<resp['coupled_generation_v1']['controls']['max_tokens']
        assert resp['coupled_generation_v1']['termination']['model_eos_reached'] is True
        previous=row['mtime_ns']
    for annfile in (OUT/'reviews').glob('*annotations.json'):
        data=json.loads(annfile.read_text())
        for ann in data.get('annotations',[]) if isinstance(data,dict) else data:
            filename=ann.get('file') or ann.get('response')
            if filename and 'quote' in ann:
                text=(OUT/filename).read_text()
                assert ann['quote'] in text,ann
                if 'start_character' in ann:
                    assert text[ann['start_character']:ann['end_character']]==ann['quote']
                if 'response_sha256' in ann:
                    assert sha(text.encode())==ann['response_sha256']
    sources=json.loads((OUT/'reviews/claim-sources/index.json').read_text())
    for source in sources['sources']:
        for version in source['versions'].values():
            raw=(OUT/version['retained']).read_bytes()
            assert sha(raw)==version['sha256'] and len(raw)==version['bytes']
    for row in rows:
        page=row.get('page')
        if not page:
            continue
        source=next(s for s in sources['sources'] if 'astrid/'+s['relative']==page['source'])
        raw=(OUT/source['versions']['canonical']['retained']).read_bytes()
        assert sha(raw)==page['revision']['sha256']
        assert len(raw)==page['revision']['bytes']
        part=raw[page['start']['byte']:page['end']['byte']].decode()
        line=page['start']['line']; expected=''
        for fragment in part.splitlines(keepends=True):
            expected+=f'{line:>6} | '+fragment+('' if fragment.endswith('\n') else '\n')
            line+=int(fragment.endswith('\n'))
        assert '\n'+expected+'\n' in page['text']
        assert line==page['end']['line']
    print(json.dumps(dict(verified_files=len(index['files']),selected_journals=len(rows),packet_index_sha256=sha((OUT/'packet-index.json').read_bytes())),indent=2))


if __name__=='__main__':
    {'capture':capture,'analyze':analyze,'metrics':metrics,'verify':verify}[sys.argv[1]]()
