"""Verify an S-007 daily packet offline; never imports or invokes the live reader."""
import argparse,copy,json,sys,tempfile,re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reservoir_research.study_capture import encoded,sha,epoch
from reservoir_research.study_sequences import receipt_records
from source_study_fidelity_daily import build
from source_study_fidelity_annotations import check

def verify(folder):
    report=json.loads((folder/'report/report.json').read_bytes())
    assert encoded(build(folder)) == (folder/'report/report.json').read_bytes()
    capture=json.loads((folder/'capture.json').read_bytes())
    supplement=json.loads((folder/'supplement.json').read_bytes())
    links=json.loads((folder/'job-link-supplement.json').read_bytes())
    for packet in [capture,supplement,links]:
        assert not packet['errors']
        for row in packet['records']:
            raw=row['text'].encode()
            assert sha(raw)==row['sha256'] and len(raw)==row['bytes']
    baseline=ROOT/'research/outputs/2026-09-08-source-study-fidelity'
    manifest=json.loads((baseline/'packet-manifest.json').read_bytes())
    for name,digest in manifest.items():
        assert sha((baseline/name).read_bytes())==digest,(name,'baseline changed')
    annotations=check(folder/'capture.json',folder/'claim-annotations.json')
    assert {c['generation_id'] for c in annotations['claims']} == set(report['close_reading_ids'])
    assert not report['join_issues'] and not report['unverified_receipts_in_window']
    assert report['complete_writing_matches']==report['generation_count']
    assert not report['duplicate_baseline_ids']
    assert all(':unverified-pid' not in s['era'] for s in report['studies'])
    jobs={}
    for row in capture['records']+links['records']:
        if row['kind']=='job_job.json':
            job=json.loads(row['text'])
            assert job['job_id'] not in jobs
            jobs[job['job_id']]=job
    lo=epoch(capture['selection']['since']);hi=epoch(capture['selection']['until_exclusive'])
    for s in report['studies']:
        job=jobs[s['job_id']]
        assert job['call_kind']=='self_study' and job['worker_pid']==s['pid']
        assert lo<=epoch(job['created_at'])<hi
        attempts=job.get('phase_timings',{}).get('attempts',[])
        attempts+=job.get('outcome',{}).get('phase_timings',{}).get('attempts',[])
        assert any(a.get('generation_id')==s['id'] for a in attempts),(s['id'],'job attempt ID missing')
    extra=[jobs[s['job_id']] for s in report['studies'] if not s['job_captured']]
    incomplete_at_cutoff=[j['job_id'] for j in jobs.values() if not j.get('finished_at') or epoch(j['finished_at'])>=hi]
    # Negative controls: detect corrupt retained data and missing page exposure.
    with tempfile.TemporaryDirectory(dir=folder,prefix='verify-control-') as tmp:
        t=Path(tmp)
        for n in ['protocol.json','supplement.json']:(t/n).write_bytes((folder/n).read_bytes())
        altered=copy.deepcopy(capture);altered['records'][0]['text']+='changed'
        (t/'capture.json').write_bytes(encoded(altered))
        try:build(t)
        except AssertionError:hash_rejected=True
        else:raise AssertionError('corrupt retained record accepted')
        annotated=json.loads((folder/'claim-annotations.json').read_bytes())
        annotated['claims'][0]['quote']='this is an invented annotation control'
        (t/'annotations.json').write_bytes(encoded(annotated))
        try:check(folder/'capture.json',t/'annotations.json')
        except AssertionError:quote_rejected=True
        else:raise AssertionError('invented annotation accepted')
    record=copy.deepcopy(next(x for x in capture['records'] if x['kind']=='delivery'))
    d=json.loads(record['text']);request=json.loads(d['request_json'])
    for m in request['messages']:
        if m['role']=='user':m['content']='negative control: source page removed'
    d['request_json']=json.dumps(request)
    raw=encoded(d);record.update(text=raw.decode(),sha256=sha(raw),bytes=len(raw),being='minime')
    record['path']=str(Path(record['path']).with_name(sha(raw)+'.json'))
    rejected=receipt_records([record])[0]
    assert not rejected['verified'] and 'whole supplied page/navigation absent' in rejected['errors']
    selected=next(s for s in report['studies'] if s['id']==report['close_reading_ids'][2])
    baseline_report=json.loads((baseline/'initial-report/report.json').read_bytes())
    # Exact source identity, range and numbered code text match baseline; offer IDs differ.
    basecapture=json.loads((baseline/'capture.json').read_bytes())
    current_page=json.loads(next(x['text'] for x in capture['records'] if x['path']==selected['receipt_path']))['page']
    def source_identity(page):
        body='\n'.join(line for line in page['text'].splitlines() if re.fullmatch(r'\s*\d+ \| .*',line))
        return page['source'],page['revision'],page['start'],page['end'],body
    repetitions=[json.loads(x['text'])['page']['id'] for x in basecapture['records'] if x['kind']=='delivery' and source_identity(json.loads(x['text'])['page'])==source_identity(current_page)]
    assert repetitions,'selected first code page not exactly matched in baseline'
    checks=dict(schema='source_study_fidelity_daily_verification_v1',
        capture_sha256=sha((folder/'capture.json').read_bytes()),supplement_sha256=sha((folder/'supplement.json').read_bytes()),
        linked_job_capture_sha256=sha((folder/'job-link-supplement.json').read_bytes()),
        report_sha256=sha((folder/'report/report.json').read_bytes()),
        retained_record_occurrences_hash_verified=sum(len(p['records']) for p in [capture,supplement,links]),
        baseline_files_unchanged=len(manifest),report_replay_identical=True,annotation_spans_verified=annotations['claim_checks'],
        generation_job_attempt_ids_verified=report['generation_count'],original_filename_jobs=report['jobs_queued'],
        linked_introspect_jobs=len(extra),expanded_linked_job_frame=len(jobs),
        expanded_job_statuses=dict(Counter(j['status'] for j in jobs.values())),
        jobs_not_finished_by_cutoff=incomplete_at_cutoff,
        complete_writing_matches=report['complete_writing_matches'],complete_wire_matches=report['verified_receipt_matches'],
        selected_code_page_exact_baseline_matches=len(repetitions),
        verified_release_pairs=len(report['release_eras']),transition_generations=sum(bool(s['transitions']) for s in report['studies']),
        source_files=len(report['sources']),source_page_opportunities=sum(s['page_opportunities'] for s in report['sources']),
        source_repository_counts=dict(Counter(s['repository'] for s in report['sources'])),
        full_source_hash_reconstructions=sum(s['full_file_hash_verified'] for s in report['sources']),
        models=dict(Counter(s['model'] for s in report['studies'])),
        backends=dict(Counter(s['backend'] for s in report['studies'])),
        cap_hits=sum(s['cap_hit'] is True for s in report['studies']),unknown_cap_hits=sum(s['cap_hit'] is None for s in report['studies']),
        effective_output_caps=dict(Counter(s['effective_tokens'] for s in report['studies'])),
        notebook_supplied=sum(s['notebook']['status']=='included_in_submitted_user_text' for s in report['studies']),
        negative_controls=dict(changed_record_hash_rejected=hash_rejected,invented_annotation_rejected=quote_rejected,missing_wire_page_rejected=True),
        limits='Computational verification does not establish exhaustive live capture, semantic judgment correctness, or understanding. Original filename job frame and explicit linked-job extension remain separate.')
    return checks,annotations

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('packet',type=Path);a=p.parse_args()
    assert a.packet.resolve().is_relative_to(ROOT/'research/outputs')
    result,annotations=verify(a.packet)
    for name,data in [('verification.json',result),('verified-claim-checks.json',annotations)]:
        path=a.packet/name
        with path.open('xb') as out:out.write(encoded(data))
        path.chmod(0o600)
    print(json.dumps(result,indent=2))
