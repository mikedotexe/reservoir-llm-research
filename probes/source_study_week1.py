"""Bounded S-007 week-one synthesis from seven immutable daily packets; stdlib, offline only.
No source-system reads, generation, collector, ledger mutation or quality-score computation.
"""
import json,hashlib
from collections import Counter,defaultdict
from pathlib import Path
from datetime import datetime

def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
def epoch(value):return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
def union_bytes(ranges):
    end=-1;total=0
    for a,b in sorted(ranges):
        assert 0<=a<=b
        total+=max(0,b-max(a,end));end=max(end,b)
    return total
def build(packet):
    root=packet.parents[2]
    protocol=json.loads((packet/'protocol.json').read_bytes())
    ledger=json.loads((packet/'tracking-after-day7.json').read_bytes())
    windows=[w for w in ledger['windows'] if w['kind']=='prospective_daily']
    assert len(windows)==7 and [w['day'] for w in windows]==list(range(1,8))
    assert windows[0]['since']==protocol['since'] and windows[-1]['until_exclusive']==protocol['until_exclusive']
    historical={}
    for w in ledger['windows']:
        folder=(root/w['capture']).parent
        raw=(folder/'packet-manifest.json').read_bytes();manifest=json.loads(raw)
        for name,digest in manifest.items():
            assert sha((folder/name).read_bytes())==digest,(folder.name,name)
        historical[folder.name]=dict(files=len(manifest),manifest_sha256=sha(raw))
    daily=[];gens={};job_versions=defaultdict(dict);sources={};pages=set();claims=[];selection=[]
    for index,w in enumerate(windows):
        if index:assert windows[index-1]['until_exclusive']==w['since']
        folder=(root/w['capture']).parent
        raw=(root/w['report']).read_bytes();a=json.loads(raw)
        v=json.loads((root/w['verification']).read_bytes())
        ann=json.loads((root/w['annotations']).read_bytes())
        assert sha(raw)==w['report_sha256']==v['report_sha256']
        assert sha((root/w['capture']).read_bytes())==w['capture_sha256']
        jobs={}
        for name in ['capture.json','supplement.json','job-link-supplement.json']:
            p=folder/name
            if not p.exists():continue
            evidence=json.loads(p.read_bytes())
            assert not evidence['errors']
            for rec in evidence['records']:
                if rec['kind'] not in ['job_job.json','linked_job_job.json']:continue
                assert sha(rec['text'].encode())==rec['sha256']
                j=json.loads(rec['text'])
                jobs[j['job_id']]=j
                job_versions[j['job_id']][rec['sha256']]=dict(day=w['day'],status=j['status'],created_at=j['created_at'],finished_at=j.get('finished_at'))
        expected_jobs=v['expanded_linked_job_frame'] if w['day']==1 else v['expanded_linked_jobs']
        expected_status=v['expanded_job_statuses'] if w['day']==1 else v['job_statuses']
        assert len(jobs)==expected_jobs and dict(Counter(j['status'] for j in jobs.values()))==expected_status
        before=json.loads((folder/'tracking-before.json').read_bytes())
        ss=a['studies']
        chosen=[s['id'] for s in ss if s['status']=='ok' and s['text'].strip() and s['id'] not in before['seen_generations']][:3]
        assert chosen==w['close_reading_ids']==a['close_reading_ids'] and len(chosen)==3
        for s in ss:
            assert epoch(w['since'])<=epoch(s['completed'])<epoch(w['until_exclusive'])
            assert s['id'] not in gens
            assert ledger['seen_generations'][s['id']]['record_sha256']==s['record_sha256']
            assert ledger['seen_generations'][s['id']]['response_sha256']==s['response_sha256']
            if w['day']==1:
                assert jobs[s['job_id']]['action_text'].startswith(('SELF_STUDY','INTROSPECT'))
            route=s.get('actual_route','source_study')
            gens[s['id']]=dict(day=w['day'],record_sha256=s['record_sha256'],response_sha256=s['response_sha256'],status=s['status'],route=route)
            for p in s['pages']:
                assert s['receipt_verified']
                key=(p['source'],p['revision']['sha256'])
                if key not in sources:sources[key]=dict(source=key[0],revision=key[1],repository=key[0].split('/')[0],file_bytes=p['revision']['bytes'],intervals=[],opportunities=0,days=set(),daily_full_hash_verified=False)
                dest=sources[key]
                assert dest['file_bytes']==p['revision']['bytes']
                dest['intervals'].append((p['start']['byte'],p['end']['byte']))
                dest['opportunities']+=1;dest['days'].add(w['day'])
                pages.add((key[0],key[1],p['start']['byte'],p['end']['byte']))
        for source in a['sources']:
            if source['full_file_hash_verified']:sources[(source['source'],source['revision'])]['daily_full_hash_verified']=True
        for c in ann['claims']:
            assert c['generation_id'] in chosen
            s=next(s for s in ss if s['id']==c['generation_id'])
            assert c['quote'] in s['text']
            claims.append(dict(day=w['day'],claim=c))
        source_studies=[s for s in ss if s.get('actual_route','source_study')=='source_study']
        full=v['complete_writing_matches'] if w['day']==1 else v['complete_journal_matches']
        wire=v['complete_wire_matches'] if w['day']==1 else v['complete_source_wire_matches']
        row=dict(day=w['day'],since=w['since'],until_exclusive=w['until_exclusive'],packet=str(folder.relative_to(root)),
            report=w['report'],report_sha256=sha(raw),generation_attempts=len(ss),
            source_completed=sum(s['status']=='ok' for s in source_studies),source_failed=sum(s['status']=='error' for s in source_studies),
            private_writing=len(ss)-len(source_studies),wire_verified=wire,
            wire_gaps=[s['id'] for s in source_studies if s['status']=='ok' and not s['receipt_verified']],
            full_journals=full,summarized_journals=v.get('summarized_journals',[]),
            transformed_journals=v.get('transformed_journals',[]),unresolved_journals=v.get('unresolved_completed_source_journals',[]),
            jobs=len(jobs),job_statuses=expected_status,jobs_not_finished_by_cutoff=v['jobs_not_finished_by_cutoff'],
            page_opportunities=v['source_page_opportunities'],
            source_paths=len({s['source'] for s in a['sources']}),source_revisions=len(a['sources']),
            daily_full_revision_hashes=sum(s['full_file_hash_verified'] for s in a['sources']),
            source_kinds=dict(Counter(s['kind'] for s in source_studies)),pids=dict(Counter(str(s['pid']) for s in ss)),
            models=dict(Counter(s['model'] for s in ss)),effective_caps=dict(Counter(str(s['effective_tokens']) for s in ss)),
            cap_hits=dict(Counter(s['status'] for s in ss if s['cap_hit'])),
            prompt_sets=[dict(hashes=list(k),n=n) for k,n in Counter(tuple(s['system_hashes']) for s in ss).items()],
            eras=a['eras'],release_eras=a.get('release_eras',{}),
            new_paired_releases=v['verified_release_pairs'] if w['day']==1 else v['new_paired_releases'],
            transition_generations=v['transition_generations'],selected_ids=chosen,selected_checks=len(ann['claims']),
            annotation_file=w['annotations'],delayed_capture=w.get('delayed_capture'),
            schema_note='Day 1 lacks actual_route/journal_status; all linked job actions verify SELF_STUDY or INTROSPECT, and its verifier establishes full journal matches. Later schemas retain explicit route/disposition.' if w['day']==1 else None)
        assert row['source_completed']==wire+len(row['wire_gaps'])
        assert row['source_completed']==full+len(row['summarized_journals'])+len(row['transformed_journals'])+len(row['unresolved_journals'])
        assert row['page_opportunities']==sum(len(s['pages']) for s in ss)
        daily.append(row);selection.extend(chosen)
    normalized=[]
    for key,s in sorted(sources.items()):
        s=dict(s,days=sorted(s['days']),unique_bytes=union_bytes(s['intervals']))
        s['intervals']=sorted(set(s['intervals']))
        normalized.append(s)
    varying={ident:versions for ident,versions in job_versions.items() if len({(v['status'],v['created_at'],v['finished_at']) for v in versions.values()})>1}
    statuses=Counter()
    for ident,versions in job_versions.items():
        if ident not in varying:statuses[next(iter(versions.values()))['status']]+=1
    sumkeys=['generation_attempts','source_completed','source_failed','private_writing','wire_verified','full_journals','page_opportunities','selected_checks','new_paired_releases','transition_generations']
    totals={key:sum(d[key] for d in daily) for key in sumkeys}
    totals.update(distinct_generations=len(gens),distinct_jobs=len(job_versions),job_frame_occurrences=sum(d['jobs'] for d in daily),
        stable_job_statuses=dict(statuses),jobs_with_changing_retained_status=len(varying),
        summarized_journals=sum(len(d['summarized_journals']) for d in daily),
        transformed_journals=sum(len(d['transformed_journals']) for d in daily),
        unresolved_journals=sum(len(d['unresolved_journals']) for d in daily),
        wire_gaps=sum(len(d['wire_gaps']) for d in daily),selected_responses=len(selection),
        unique_source_paths=len({s['source'] for s in normalized}),unique_source_revisions=len(normalized),
        unique_page_intervals=len(pages),unique_revision_bytes=sum(s['unique_bytes'] for s in normalized),
        revisions_with_daily_full_hash_verification=sum(s['daily_full_hash_verified'] for s in normalized),
        source_repository_page_opportunities=dict(Counter({repo:sum(s['opportunities'] for s in normalized if s['repository']==repo) for repo in {s['repository'] for s in normalized}})),
        verified_historical_files=sum(x['files'] for x in historical.values()))
    assert totals['generation_attempts']==totals['distinct_generations']
    assert totals['generation_attempts']==totals['source_completed']+totals['source_failed']+totals['private_writing']
    assert len(selection)==len(set(selection))==21
    return dict(schema='s007_week1_synthesis_v1',protocol=protocol,ledger_sha256=sha((packet/'tracking-after-day7.json').read_bytes()),
        baseline='Separate September 8 07:00–18:34 UTC baseline: 92 pre / 20 post. Not included in prospective totals.',
        totals=totals,daily=daily,sources=normalized,generation_identities=gens,job_record_versions=dict(job_versions),
        changing_job_status_records=varying,historical_manifests=historical,selected_checks=claims,
        limits=['One Being, dependent sequential responses; no population accuracy or causal effect estimate.',
                'Page opportunities count repeated delivery; paths and source revisions are deduplicated separately.',
                'Full hashes require a daily verified reconstruction; union coverage alone is not called a full-hash verification.',
                'Filename-bounded collector and explicit linked-job extension are not exhaustive live opportunity enumeration; WRITE-only failures outside that frame remain out of scope.',
                'Daily release eras, prompts, caps, process transitions, failures, journal transformations and delayed captures remain explicit.',
                'Baseline and overlapping release-specific studies are not independent replications of these seven windows.'])
