"""Offline verification for S-007 daily v3, including retained gaps, failed and private-writing lanes."""
import argparse
import copy
import json
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reservoir_research.study_capture import encoded, epoch, sha
from reservoir_research.study_sequences import receipt_records, user_text
from source_study_fidelity_daily_v5 import build
from source_study_daily_compat import failed_wire as verify_failed_wire


def annotations(folder, report):
    source = json.loads((folder / 'claim-annotations.json').read_bytes())
    studies = {s['id']: s for s in report['studies']}
    rows = []
    for claim in source['claims']:
        assert claim['generation_id'] in report['close_reading_ids']
        text = studies[claim['generation_id']]['text']
        positions = [m.start() for m in re.finditer(re.escape(claim['quote']), text)]
        assert len(positions) == claim.get('expected_occurrences', 1), claim['id']
        rows.append(dict(claim, spans=[dict(start=p, end=p+len(claim['quote'])) for p in positions],
                         response_sha256=sha(text.encode())))
    return dict(source, claims=rows, claim_checks=len(rows),
                limits='Selected interpretive checks; computational span verification does not validate judgments. Repetition is not independent evidence.')


def verify(folder):
    report = json.loads((folder / 'final-report/report.json').read_bytes())
    assert encoded(build(folder)) == (folder / 'final-report/report.json').read_bytes()
    packets = [json.loads((folder / name).read_bytes()) for name in ['capture.json', 'supplement.json', 'era-supplement.json', 'catchup-era.json', 'catchup-activation.json', 'new-era.json', 'new-era-validation.json']]
    records = [r for p in packets for r in p['records']]
    for p in packets:
        assert not p['errors']
    for r in records:
        assert sha(r['text'].encode()) == r['sha256'] and len(r['text'].encode()) == r['bytes'], r['path']
    preserved = {}
    for name in ['2026-09-08-source-study-fidelity', '2026-09-09-source-study-fidelity-day1', '2026-09-10-source-study-fidelity-day2']:
        f = ROOT / 'research/outputs' / name
        manifest = json.loads((f / 'packet-manifest.json').read_bytes())
        for path, digest in manifest.items():
            assert sha((f / path).read_bytes()) == digest, path
        preserved[name] = len(manifest)
    assert not report['capture_errors'] and not report['join_issues'] and not report['unverified_receipts_in_window']
    assert not report['duplicate_baseline_ids']
    assert all('unverified-pid' not in s['era'] for s in report['studies'])
    jobs = {json.loads(r['text'])['job_id']: json.loads(r['text']) for r in records if r['kind'] in ['job_job.json', 'linked_job_job.json']}
    generations = {json.loads(r['text'])['generation_id']: json.loads(r['text']) for r in records if r['kind'] == 'generation'}
    lo = epoch(report['selection']['since']); hi = epoch(report['selection']['until_exclusive'])
    incoming_jobs = []
    for s in report['studies']:
        job = jobs[s['job_id']]
        assert job['worker_pid'] == s['pid']
        assert epoch(job['created_at']) < hi
        if epoch(job['created_at']) < lo:
            assert not s['job_captured'] and s['linked_job_captured']
            incoming_jobs.append(s['job_id'])
        attempts = job.get('phase_timings', {}).get('attempts', []) + job.get('outcome', {}).get('phase_timings', {}).get('attempts', [])
        assert any(a.get('generation_id') == s['id'] for a in attempts), s['id']
        if s['actual_route'] == 'source_study' and s['status'] == 'ok':
            assert s['receipt_verified']
            # Journal transformation/absence stays explicit; wire delivery is a separate check.
        if s['actual_route'] == 'extended_writing':
            assert job['action_text'].startswith('WRITE ') and not s['pages']
        if s['input_kind'] == 'relationships':
            assert s['kind'] == 'relationships', 'notebook footer misclassified as EOF'
    incomplete = [j['job_id'] for j in jobs.values() if not j.get('finished_at') or epoch(j['finished_at']) >= hi]
    failed_wire = []
    for r in records:
        if r['kind'] != 'source_study_failure':
            continue
        d = json.loads(r['text'])
        matches = [s for s in report['studies'] if s['backend_timing'].get('source_study_diagnostic_path') == r['path']]
        assert len(matches) == 1
        check = verify_failed_wire(d, matches[0], user_text)
        failed_wire.append(dict(check, diagnostic=r['path']))
    bindings = json.loads((folder / 'source-bindings.json').read_bytes())
    for b in bindings['bindings']:
        r = next(r for r in records if r['path'] == b['reload_path'])
        assert r['sha256'] == b['reload_file_sha256']
        reload = json.loads(r['text'].splitlines()[-1])
        for c in b['checks']:
            assert c['matches'] and c['git_source_sha256'] == c['reload_sha256'] == reload['source_inputs'][c['path']]
    catchup = json.loads((folder / 'catchup-bindings.json').read_bytes())
    reload_row = next(r for r in records if r['path'] == catchup['reload_path'])
    assert reload_row['sha256'] == catchup['reload_sha256']
    reload = json.loads(reload_row['text'].splitlines()[-1])
    assert report['release_eras']['journal-coherence']['minime']['commit'] == catchup['commit']
    for check in catchup['checks']:
        assert check['commit'] == catchup['commit'] and check['matches']
        assert check['source_sha256'] == check['reload_sha256'] == reload['source_inputs'][check['path']]
    journals = {Path(r['path']).name.lstrip('!'): r for r in records if r['kind'] == 'journal'}
    transformed = []
    unresolved = []
    for study in report['studies']:
        if study['status'] != 'ok' or study['actual_route'] != 'source_study' or study['journal_status'] != 'no_full_journal_match':
            continue
        matches = []
        for artifact in study['linked_artifacts']:
            if artifact.get('kind') != 'journal':
                continue
            journal = journals.get(Path(artifact['path']).name.lstrip('!'))
            altered = study['text'].replace('</s>', '')
            if journal and '</s>' in study['text'] and altered in journal['text']:
                matches.append(dict(generation_id=study['id'], journal_path=journal['path'], journal_sha256=journal['sha256'],
                                    transformation='literal </s> removed; result is a contiguous journal substring',
                                    removed_occurrences=study['text'].count('</s>'), transformed_response_sha256=sha(altered.encode()),
                                    journal_start=journal['text'].index(altered), journal_end=journal['text'].index(altered)+len(altered)))
        if matches:
            transformed.extend(matches)
        else:
            unresolved.append(study['id'])
    new_binding=json.loads((folder/'new-era-bindings.json').read_bytes())
    new_reload=next(r for r in records if r['path']==new_binding['reload_path'])
    assert new_reload['sha256']==new_binding['reload_sha256']
    new_values=json.loads(new_reload['text'].splitlines()[-1])
    assert new_binding['commit']==report['release_eras']['catalog-navigation-sep15']['minime']['commit']
    for check in new_binding['checks']:
        assert check['matches'] and check['source_sha256']==check['reload_sha256']==new_values['source_inputs'][check['path']]
    ann = annotations(folder, report)
    # Integrity, exposure and quoted-text negative controls use only research copies.
    with tempfile.TemporaryDirectory(dir=folder, prefix='verify-control-') as tmp:
        t = Path(tmp)
        for name in ['protocol.json','supplement.json','era-supplement.json','catchup-era.json','catchup-activation.json','new-era.json','new-era-validation.json','tracking-before.json']:
            (t / name).write_bytes((folder / name).read_bytes())
        broken = copy.deepcopy(packets[0]); broken['records'][0]['text'] += 'changed'
        (t / 'capture.json').write_bytes(encoded(broken))
        try:
            build(t)
        except AssertionError:
            pass
        else:
            raise AssertionError('Corrupt retained content accepted')
        invented = json.loads((folder / 'claim-annotations.json').read_bytes())
        invented['claims'][0]['quote'] = 'invented quotation control'
        (t / 'claim-annotations.json').write_bytes(encoded(invented))
        try:
            annotations(t, report)
        except AssertionError:
            pass
        else:
            raise AssertionError('Invented quotation accepted')
    r = copy.deepcopy(next(r for r in records if r['kind'] == 'delivery'))
    d = json.loads(r['text']); request = json.loads(d['request_json'])
    for m in request['messages']:
        if m['role'] == 'user':
            m['content'] = 'negative control: removed supplied source'
    d['request_json'] = json.dumps(request); raw = encoded(d)
    r.update(text=raw.decode(), bytes=len(raw), sha256=sha(raw), being='minime')
    r['path'] = str(Path(r['path']).with_name(sha(raw)+'.json'))
    assert 'whole supplied page/navigation absent' in receipt_records([r])[0]['errors']
    selected = [s for s in report['studies'] if s['id'] in report['close_reading_ids']]
    pages = [p for s in selected for p in s['pages']]
    seen = json.loads((folder/'tracking-before.json').read_bytes())['seen_generations']
    expected_selected = [s['id'] for s in report['studies'] if s['status']=='ok' and s['text'].strip() and s['id'] not in seen][:3]
    assert report['close_reading_ids'] == expected_selected
    assert len({s['id'] for s in report['studies']}) == len(report['studies'])
    selected_pages = [dict(generation_id=s['id'], pages=s['pages'], kind=s['kind']) for s in selected]
    return dict(schema='s007_daily_verification_v5', report_sha256=sha((folder/'final-report/report.json').read_bytes()),
        packet_hashes={name:sha((folder/name).read_bytes()) for name in ['capture.json','supplement.json','era-supplement.json','source-bindings.json','catchup-era.json','catchup-activation.json','catchup-bindings.json','new-era.json','new-era-validation.json','new-era-bindings.json']},
        retained_record_occurrences=len(records), preserved_historical_files=preserved, replay_identical=True,
        generation_job_attempt_matches=len(report['studies']), generation_statuses=dict(Counter(s['status'] for s in report['studies'])),
        source_study_statuses=dict(Counter(s['status'] for s in report['studies'] if s['actual_route']=='source_study')),
        private_writing_generations=sum(s['actual_route']=='extended_writing' for s in report['studies']),
        original_filename_jobs=report['jobs_queued'],expanded_linked_jobs=len(jobs),job_statuses=dict(Counter(j['status'] for j in jobs.values())),
        jobs_not_finished_by_cutoff=incomplete,complete_journal_matches=report['complete_writing_matches'],
        summarized_journals=[s['id'] for s in report['studies'] if s['journal_status']=='similarity_summary'],
        complete_source_wire_matches=report['verified_receipt_matches'], retained_failed_wires=failed_wire,
        failures_without_retained_wire=[s['id'] for s in report['studies'] if s['status']=='error' and s['id'] not in {w['generation_id'] for w in failed_wire}],
        kinds=dict(Counter(s['kind'] for s in report['studies'])),
        source_paths=len({s['source'] for s in report['sources']}),source_revisions=len(report['sources']),
        source_page_opportunities=sum(s['page_opportunities'] for s in report['sources']),
        full_revision_hashes=sum(s['full_file_hash_verified'] for s in report['sources']),
        repositories=dict(Counter(s['repository'] for s in report['sources'])),
        selected_inputs=selected_pages, transformed_journals=transformed, unresolved_completed_source_journals=unresolved, jobs_created_before_window=incoming_jobs,
        selected_claim_checks=ann['claim_checks'],selected_claim_spans=sum(len(c['spans']) for c in ann['claims']),
        process_eras=len({s['pid'] for s in report['studies']}),transition_generations=sum(bool(s['transitions']) for s in report['studies']),
        new_paired_releases=sum(lo<=e['minime']['boundary']<hi for e in report['release_eras'].values()),
        extra_schema_source_hash_bindings=sum(len(b['checks']) for b in bindings['bindings']), catchup_source_hash_bindings=len(catchup['checks']), new_release_source_hash_bindings=len(new_binding['checks']),
        models=dict(Counter(s['model'] for s in report['studies'])),
        effective_caps=dict(Counter(s['effective_tokens'] for s in report['studies'])),
        cap_hits=dict(Counter(s['status'] for s in report['studies'] if s['cap_hit'])),
        notebook_supplied=sum(s['notebook']['status']=='included_in_submitted_user_text' for s in report['studies']),
        negative_controls=dict(changed_record_rejected=True,missing_wire_source_rejected=True,invented_quote_rejected=True),
        limits='Checks retained evidence and computation, not exhaustive opportunity capture, semantic judgments or comprehension. WRITE-only failures outside filename frame are not enumerated.'), ann


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('packet',type=Path);a=p.parse_args()
    assert a.packet.resolve().is_relative_to(ROOT/'research/outputs')
    result,ann=verify(a.packet)
    for name,data in [('verification.json',result),('verified-claim-checks.json',ann)]:
        with (a.packet/name).open('xb') as out:out.write(encoded(data))
        (a.packet/name).chmod(0o600)
    print(json.dumps(result,indent=2))
