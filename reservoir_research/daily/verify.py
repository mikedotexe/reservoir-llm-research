"""Offline verification; all negative controls are memory-only copies."""
import copy, json, re
from collections import Counter
from pathlib import Path
from reservoir_research.study_capture import encoded, epoch, sha
from reservoir_research.study_sequences import receipt_records, user_text
from .report import build_report
from .compat import failed_wire as verify_failed_wire
from .inputs import DailyError, require, checked_call, PACKET_NAMES

def verify_report(packet, report_path, annotations_path=None):
    if annotations_path is not None:
        raw = Path(annotations_path).read_bytes()
        require(raw == packet.raw('claim-annotations.json'), 'Annotations must match the declared manifest input')
    raw = Path(report_path).read_bytes()
    result, claims = checked_call(_verify, packet, raw)
    return dict(verification=result, verified_claims=claims, pipeline=dict(schema='s007-maintained-pipeline-verification-v1', manifest_sha256=packet.manifest_sha256, report_sha256=sha(raw), era_definitions_sha256=packet.manifest['era_definitions_sha256'], historical_files=packet.history_counts, historical_file_count=sum(packet.history_counts.values()), packet_code_executed=False, source_paths_followed=False))

def annotations(source, report):
    studies = {s['id']: s for s in report['studies']}
    rows = []
    for claim in source['claims']:
        require(claim['generation_id'] in report['close_reading_ids'], "Evidence check failed: claim['generation_id'] in report['close_reading_ids']")
        text = studies[claim['generation_id']]['text']
        positions = [m.start() for m in re.finditer(re.escape(claim['quote']), text)]
        require(len(positions) == claim.get('expected_occurrences', 1), claim['id'])
        rows.append(dict(claim, spans=[dict(start=p, end=p + len(claim['quote'])) for p in positions], response_sha256=sha(text.encode())))
    return dict(source, claims=rows, claim_checks=len(rows), limits='Selected interpretive checks; computational span verification does not validate judgments. Repetition is not independent evidence.')

def _verify(packet, report_raw):
    report = json.loads(report_raw)
    require(encoded(build_report(packet)) == report_raw, 'Evidence check failed: encoded(build_report(packet)) == report_raw')
    packets = [packet.json(name) for name in ['capture.json', 'supplement.json', 'era-supplement.json', 'catchup-era.json', 'catchup-activation.json', 'new-era.json', 'new-era-validation.json', 'interface-era.json']]
    records = [r for p in packets for r in p['records']]
    for p in packets:
        require(not p['errors'], "Evidence check failed: not p['errors']")
    for r in records:
        require(sha(r['text'].encode()) == r['sha256'] and len(r['text'].encode()) == r['bytes'], r['path'])
    preserved = packet.legacy_history
    require(not report['capture_errors'] and (not report['join_issues']) and (not report['unverified_receipts_in_window']), "Evidence check failed: not report['capture_errors'] and (not report['join_issues']) and (not report['unverified_receipts_in_window'])")
    require(not report['duplicate_baseline_ids'], "Evidence check failed: not report['duplicate_baseline_ids']")
    require(all(('unverified-pid' not in s['era'] for s in report['studies'])), "Evidence check failed: all(('unverified-pid' not in s['era'] for s in report['studies']))")
    jobs = {json.loads(r['text'])['job_id']: json.loads(r['text']) for r in records if r['kind'] in ['job_job.json', 'linked_job_job.json']}
    generations = {json.loads(r['text'])['generation_id']: json.loads(r['text']) for r in records if r['kind'] == 'generation'}
    lo = epoch(report['selection']['since'])
    hi = epoch(report['selection']['until_exclusive'])
    incoming_jobs = []
    for s in report['studies']:
        job = jobs[s['job_id']]
        require(job['worker_pid'] == s['pid'], "Evidence check failed: job['worker_pid'] == s['pid']")
        require(epoch(job['created_at']) < hi, "Evidence check failed: epoch(job['created_at']) < hi")
        if epoch(job['created_at']) < lo:
            require(not s['job_captured'] and s['linked_job_captured'], "Evidence check failed: not s['job_captured'] and s['linked_job_captured']")
            incoming_jobs.append(s['job_id'])
        attempts = job.get('phase_timings', {}).get('attempts', []) + job.get('outcome', {}).get('phase_timings', {}).get('attempts', [])
        require(any((a.get('generation_id') == s['id'] for a in attempts)), s['id'])
        if s['actual_route'] == 'source_study' and s['status'] == 'ok':
            require(s['receipt_verified'], "Evidence check failed: s['receipt_verified']")
        if s['actual_route'] == 'extended_writing':
            require(job['action_text'].startswith('WRITE ') and (not s['pages']), "Evidence check failed: job['action_text'].startswith('WRITE ') and (not s['pages'])")
        if s['input_kind'] == 'relationships':
            require(s['kind'] == 'relationships', 'notebook footer misclassified as EOF')
    incomplete = [j['job_id'] for j in jobs.values() if not j.get('finished_at') or epoch(j['finished_at']) >= hi]
    failed_wire = []
    for r in records:
        if r['kind'] != 'source_study_failure':
            continue
        d = json.loads(r['text'])
        matches = [s for s in report['studies'] if s['backend_timing'].get('source_study_diagnostic_path') == r['path']]
        require(len(matches) == 1, 'Evidence check failed: len(matches) == 1')
        check = verify_failed_wire(d, matches[0], user_text)
        failed_wire.append(dict(check, diagnostic=r['path']))
    bindings = packet.json('source-bindings.json')
    for b in bindings['bindings']:
        r = next((r for r in records if r['path'] == b['reload_path']))
        require(r['sha256'] == b['reload_file_sha256'], "Evidence check failed: r['sha256'] == b['reload_file_sha256']")
        reload = json.loads(r['text'].splitlines()[-1])
        for c in b['checks']:
            require(c['matches'] and c['git_source_sha256'] == c['reload_sha256'] == reload['source_inputs'][c['path']], "Evidence check failed: c['matches'] and c['git_source_sha256'] == c['reload_sha256'] == reload['source_inputs'][c['path']]")
    catchup = packet.json('catchup-bindings.json')
    reload_row = next((r for r in records if r['path'] == catchup['reload_path']))
    require(reload_row['sha256'] == catchup['reload_sha256'], "Evidence check failed: reload_row['sha256'] == catchup['reload_sha256']")
    reload = json.loads(reload_row['text'].splitlines()[-1])
    require(report['release_eras']['journal-coherence']['minime']['commit'] == catchup['commit'], "Evidence check failed: report['release_eras']['journal-coherence']['minime']['commit'] == catchup['commit']")
    for check in catchup['checks']:
        require(check['commit'] == catchup['commit'] and check['matches'], "Evidence check failed: check['commit'] == catchup['commit'] and check['matches']")
        require(check['source_sha256'] == check['reload_sha256'] == reload['source_inputs'][check['path']], "Evidence check failed: check['source_sha256'] == check['reload_sha256'] == reload['source_inputs'][check['path']]")
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
            if journal and '</s>' in study['text'] and (altered in journal['text']):
                matches.append(dict(generation_id=study['id'], journal_path=journal['path'], journal_sha256=journal['sha256'], transformation='literal </s> removed; result is a contiguous journal substring', removed_occurrences=study['text'].count('</s>'), transformed_response_sha256=sha(altered.encode()), journal_start=journal['text'].index(altered), journal_end=journal['text'].index(altered) + len(altered)))
        if matches:
            transformed.extend(matches)
        else:
            unresolved.append(study['id'])
    new_binding = packet.json('new-era-bindings.json')
    new_reload = next((r for r in records if r['path'] == new_binding['reload_path']))
    require(new_reload['sha256'] == new_binding['reload_sha256'], "Evidence check failed: new_reload['sha256'] == new_binding['reload_sha256']")
    new_values = json.loads(new_reload['text'].splitlines()[-1])
    require(new_binding['commit'] == report['release_eras']['catalog-navigation-sep15']['minime']['commit'], "Evidence check failed: new_binding['commit'] == report['release_eras']['catalog-navigation-sep15']['minime']['commit']")
    for check in new_binding['checks']:
        require(check['matches'] and check['source_sha256'] == check['reload_sha256'] == new_values['source_inputs'][check['path']], "Evidence check failed: check['matches'] and check['source_sha256'] == check['reload_sha256'] == new_values['source_inputs'][check['path']]")
    ann = annotations(packet.json('claim-annotations.json'), report)
    control_index = next(i for i, value in enumerate(packets) if value['records'])
    broken = copy.deepcopy(packets[control_index])
    broken['records'][0]['text'] += 'changed'
    try:
        build_report(packet.replaced(PACKET_NAMES[control_index], broken))
    except DailyError:
        pass
    else:
        raise DailyError('Corrupt retained content accepted')
    invented = packet.json('claim-annotations.json')
    if invented['claims']:
        invented['claims'][0]['quote'] = 'invented quotation control'
        control_report = report
    else:
        invented['claims'] = [dict(id='control', generation_id='control', quote='invented quotation control')]
        control_report = dict(close_reading_ids=['control'], studies=[dict(id='control', text='retained fixture')])
    try:
        annotations(invented, control_report)
    except DailyError:
        pass
    else:
        raise DailyError('Invented quotation accepted')
    delivery = next((r for r in records if r['kind'] == 'delivery'), None)
    if delivery is not None:
        r = copy.deepcopy(delivery)
        d = json.loads(r['text'])
        request = json.loads(d['request_json'])
        for m in request['messages']:
            if m['role'] == 'user':
                m['content'] = 'negative control: removed supplied source'
        d['request_json'] = json.dumps(request)
        raw = encoded(d)
        r.update(text=raw.decode(), bytes=len(raw), sha256=sha(raw), being='minime')
        r['path'] = str(Path(r['path']).with_name(sha(raw) + '.json'))
        require('whole supplied page/navigation absent' in receipt_records([r])[0]['errors'], "Evidence check failed: 'whole supplied page/navigation absent' in receipt_records([r])[0]['errors']")
    selected = [s for s in report['studies'] if s['id'] in report['close_reading_ids']]
    pages = [p for s in selected for p in s['pages']]
    seen = packet.json('tracking-before.json')['seen_generations']
    expected_selected = [s['id'] for s in report['studies'] if s['status'] == 'ok' and s['text'].strip() and (s['id'] not in seen)][:3]
    require(report['close_reading_ids'] == expected_selected, "Evidence check failed: report['close_reading_ids'] == expected_selected")
    require(len({s['id'] for s in report['studies']}) == len(report['studies']), "Evidence check failed: len({s['id'] for s in report['studies']}) == len(report['studies'])")
    selected_pages = [dict(generation_id=s['id'], pages=s['pages'], kind=s['kind']) for s in selected]
    return (dict(schema='s007_daily_verification_v6', report_sha256=sha(report_raw), packet_hashes={name: sha(packet.raw(name)) for name in ['capture.json', 'supplement.json', 'era-supplement.json', 'source-bindings.json', 'catchup-era.json', 'catchup-activation.json', 'catchup-bindings.json', 'new-era.json', 'new-era-validation.json', 'new-era-bindings.json', 'interface-era.json']}, retained_record_occurrences=len(records), preserved_historical_files=preserved, replay_identical=True, generation_job_attempt_matches=len(report['studies']), generation_statuses=dict(Counter((s['status'] for s in report['studies']))), source_study_statuses=dict(Counter((s['status'] for s in report['studies'] if s['actual_route'] == 'source_study'))), private_writing_generations=sum((s['actual_route'] == 'extended_writing' for s in report['studies'])), original_filename_jobs=report['jobs_queued'], expanded_linked_jobs=len(jobs), job_statuses=dict(Counter((j['status'] for j in jobs.values()))), jobs_not_finished_by_cutoff=incomplete, complete_journal_matches=report['complete_writing_matches'], summarized_journals=[s['id'] for s in report['studies'] if s['journal_status'] == 'similarity_summary'], complete_source_wire_matches=report['verified_receipt_matches'], retained_failed_wires=failed_wire, failures_without_retained_wire=[s['id'] for s in report['studies'] if s['status'] == 'error' and s['id'] not in {w['generation_id'] for w in failed_wire}], kinds=dict(Counter((s['kind'] for s in report['studies']))), source_paths=len({s['source'] for s in report['sources']}), source_revisions=len(report['sources']), source_page_opportunities=sum((s['page_opportunities'] for s in report['sources'])), full_revision_hashes=sum((s['full_file_hash_verified'] for s in report['sources'])), repositories=dict(Counter((s['repository'] for s in report['sources']))), selected_inputs=selected_pages, transformed_journals=transformed, unresolved_completed_source_journals=unresolved, jobs_created_before_window=incoming_jobs, selected_claim_checks=ann['claim_checks'], selected_claim_spans=sum((len(c['spans']) for c in ann['claims'])), process_eras=len({s['pid'] for s in report['studies']}), transition_generations=sum((bool(s['transitions']) for s in report['studies'])), new_paired_releases=sum((lo <= e['minime']['boundary'] < hi for e in report['release_eras'].values())), extra_schema_source_hash_bindings=sum((len(b['checks']) for b in bindings['bindings'])), catchup_source_hash_bindings=len(catchup['checks']), new_release_source_hash_bindings=len(new_binding['checks']), models=dict(Counter((s['model'] for s in report['studies']))), effective_caps=dict(Counter((s['effective_tokens'] for s in report['studies']))), cap_hits=dict(Counter((s['status'] for s in report['studies'] if s['cap_hit']))), notebook_supplied=sum((s['notebook']['status'] == 'included_in_submitted_user_text' for s in report['studies'])), negative_controls=dict(changed_record_rejected=True, missing_wire_source_rejected=True if delivery is not None else 'not_applicable', invented_quote_rejected=True), limits='Checks retained evidence and computation, not exhaustive opportunity capture, semantic judgments or comprehension. WRITE-only failures outside filename frame are not enumerated.'), ann)
