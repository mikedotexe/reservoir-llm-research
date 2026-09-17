"""Typed release-evidence adapters. Definitions supply identities and selectors;
they cannot supply code or weaken a validator's cross-evidence requirements."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from .inputs import DailyError, require, checked_call
from reservoir_research.study_capture import sha

def _readers(records, spec):

    def row(key):
        selector = spec['records'][key]
        require(isinstance(selector, dict) and len(selector) == 1, f'Invalid selector: {key}')
        if 'path' in selector:
            rows = [r for r in records if r['path'] == selector['path']]
        elif 'suffix' in selector:
            rows = [r for r in records if r['path'].endswith(selector['suffix'])]
        else:
            raise DailyError(f'Unsupported selector: {key}')
        require(len(rows) == 1, f'Expected exactly one retained record for {key}; got {len(rows)}')
        r = rows[0]
        require(sha(r['text'].encode()) == r['sha256'] and len(r['text'].encode()) == r['bytes'], f'Retained record integrity differs: {key}')
        return r

    def value(key, lines=False):
        text = row(key)['text']
        return json.loads(text.splitlines()[-1] if lines else text)
    return (row, value)

def clock(text):
    return datetime.strptime(text, '%a %b %d %H:%M:%S %Y').replace(tzinfo=ZoneInfo('America/Los_Angeles')).timestamp()

def _paired(records, spec):
    row, value = _readers(records, spec)
    rollout = value('rollout')
    manifest = row('manifest')
    require(manifest['sha256'] == rollout['manifest_sha256'], 'Release manifest hash mismatch')
    activation_row = row('activation')
    reload_row = row('reload')
    activation = value('activation')
    reload = value('reload', True)
    require(activation_row['path'] == rollout['bridge']['activation_receipt'] and reload_row['path'] == rollout['minime']['receipt'], 'Rollout receipt binding differs')
    require(activation.get('status') == 'activated_verified' and reload.get('outcome') == 'success', 'Release activation was not successful')
    require(activation['new_process']['pid'] == rollout['bridge']['new_pid'] and reload['new_pid'] == rollout['minime']['new_pid'] and (activation['manifest_sha256'] == rollout['manifest_sha256']) and (activation['new_process']['started_at'] == rollout['bridge']['started_at']) and (reload['new_started_at'] == rollout['minime']['started_at']), 'Release activation identity mismatch')
    result = {}
    for being, key, hashkey in (('astrid', 'activation', 'activation_receipt_sha256'), ('minime', 'reload', 'receipt_sha256')):
        info = rollout['bridge' if being == 'astrid' else 'minime']
        receipt = row(key)
        require(receipt['sha256'] == info[hashkey], 'Activation receipt hash mismatch')
        result[being] = dict(boundary=clock(info['started_at']), old_pid=info['old_pid'], new_pid=info['new_pid'], commit=rollout[being + '_commit'], receipt_sha256=receipt['sha256'], manifest_sha256=manifest['sha256'])
    old = row('previous_manifest')
    require(old['sha256'] == activation['old_identity']['manifest_sha256'], 'Prior release manifest mismatch')
    result['astrid']['old_manifest_sha256'] = old['sha256']
    return result

def resolve_eras(records, definitions):
    adapters = {'paired-rollout-v1': _paired, 'extended-writing-v1': _extended, 'activation-controls-v1': _extended, 'study-navigation-v1': _extended, 'journal-coherence-v1': _coherence, 'catalog-navigation-v1': _catalog, 'study-interface-v1': _interface}
    result = {}
    previous_boundary = float('-inf')
    for spec in definitions:
        require(isinstance(spec, dict), 'Invalid era definition')
        name, kind = (spec.get('id'), spec.get('validator'))
        require(isinstance(name, str) and name and (name not in result), 'Invalid or duplicate era identity')
        require(kind in adapters, f'Unknown era validator: {kind}')
        require(isinstance(spec.get('records'), dict), f'Missing era records: {name}')
        era = checked_call(adapters[kind], records, spec)
        require(era['minime']['boundary'] >= previous_boundary, 'Era definitions are not chronological')
        previous_boundary = era['minime']['boundary']
        result[name] = era
    return result

def _extended(records, spec):
    row, value = _readers(records, spec)
    commit = spec['minime_commit']
    activation = value('activation')
    reload = value('reload', True)
    manifest = row('manifest')
    require(activation['status'] in ['activated_verified', 'transition_recovered'], "Evidence check failed: activation['status'] in ['activated_verified', 'transition_recovered']")
    require(activation['activation_performed'] and reload['outcome'] == 'success', "Evidence check failed: activation['activation_performed'] and reload['outcome'] == 'success'")
    require(activation['manifest_sha256'] == manifest['sha256'], "Evidence check failed: activation['manifest_sha256'] == manifest['sha256']")
    identity = activation['new_process']['deployment_identity'].split(':')
    require(identity[0] == 'astrid' and len(identity) == 4, "Evidence check failed: identity[0] == 'astrid' and len(identity) == 4")
    if spec['validator'] == 'extended-writing-v1':
        release = value('rollout')
        require(release['verified'] and release['manifest_sha256'] == manifest['sha256'], "Evidence check failed: release['verified'] and release['manifest_sha256'] == manifest['sha256']")
        require(release['bridge']['activation_receipt_sha256'] == row('activation')['sha256'], "Evidence check failed: release['bridge']['activation_receipt_sha256'] == row('activation')['sha256']")
        require(release['minime']['receipt_sha256'] == row('reload')['sha256'], "Evidence check failed: release['minime']['receipt_sha256'] == row('reload')['sha256']")
        require(release['minime']['new_pid'] == reload['new_pid'], "Evidence check failed: release['minime']['new_pid'] == reload['new_pid']")
        require(release['minime']['started_at'] == reload['new_started_at'], "Evidence check failed: release['minime']['started_at'] == reload['new_started_at']")
        require(release['astrid_commit'] == identity[1] and release['minime_commit'] == commit, "Evidence check failed: release['astrid_commit'] == identity[1] and release['minime_commit'] == commit")
        failure = row('failure')
        require(failure['sha256'] == activation['original_failure_sha256'], "Evidence check failed: failure['sha256'] == activation['original_failure_sha256']")
    if spec['validator'] == 'activation-controls-v1':
        state = value('state')
        require(state['selection']['value']['manifest_sha256'] == manifest['sha256'], "Evidence check failed: state['selection']['value']['manifest_sha256'] == manifest['sha256']")
        expected = state['processes']['com.minime.autonomous-agent']
        require(expected['pid'] == reload['new_pid'] and expected['started_at'] == reload['new_started_at'], "Evidence check failed: expected['pid'] == reload['new_pid'] and expected['started_at'] == reload['new_started_at']")
    if spec['validator'] == 'study-navigation-v1':
        state = value('state')
        expected = state['services']['com.minime.autonomous-agent']['after']
        require(expected['pid'] == reload['new_pid'] and expected['started_at'] == reload['new_started_at'], "Evidence check failed: expected['pid'] == reload['new_pid'] and expected['started_at'] == reload['new_started_at']")
        require(state['minime_source_loaded_matches_receipt'], "Evidence check failed: state['minime_source_loaded_matches_receipt']")
    return {'minime': dict(boundary=clock(reload['new_started_at']), old_pid=reload['old_pid'], new_pid=reload['new_pid'], commit=commit, commit_basis='documented release; reload source hashes retained separately', receipt_sha256=row('reload')['sha256'], manifest_sha256=manifest['sha256']), 'astrid': dict(boundary=clock(activation['new_process']['started_at']), old_pid=activation['old_pid'], new_pid=activation['new_process']['pid'], commit=identity[1], receipt_sha256=row('activation')['sha256'], manifest_sha256=manifest['sha256'], old_manifest_sha256=activation['old_identity']['manifest_sha256'])}

def _coherence(records, spec):
    row, value = _readers(records, spec)
    activation = value('activation')
    reload = value('reload', True)
    manifest = row('manifest')
    release = value('release')
    state = value('state')
    require(activation['status'] == 'activated_verified' and activation['activation_performed'], "Evidence check failed: activation['status'] == 'activated_verified' and activation['activation_performed']")
    require(reload['outcome'] == 'success', "Evidence check failed: reload['outcome'] == 'success'")
    require(activation['manifest_sha256'] == manifest['sha256'] == state['bridge_selection']['value']['manifest_sha256'], "Evidence check failed: activation['manifest_sha256'] == manifest['sha256'] == state['bridge_selection']['value']['manifest_sha256']")
    identity = activation['new_process']['deployment_identity'].split(':')
    require(identity[0] == 'astrid' and len(identity) == 4, "Evidence check failed: identity[0] == 'astrid' and len(identity) == 4")
    require(json.loads(manifest['text'])['repository']['head'] == identity[1], "Evidence check failed: json.loads(manifest['text'])['repository']['head'] == identity[1]")
    for owner, pid, start in [('minime', reload['new_pid'], reload['new_started_at']), ('bridge', activation['new_process']['pid'], activation['new_process']['started_at'])]:
        require(release[owner]['pid'] == pid and release[owner]['started_at'] == start, "Evidence check failed: release[owner]['pid'] == pid and release[owner]['started_at'] == start")
    require(release['bridge']['deployment_identity'] == activation['new_process']['deployment_identity'], "Evidence check failed: release['bridge']['deployment_identity'] == activation['new_process']['deployment_identity']")
    expected = state['services']['com.minime.autonomous-agent']
    require(expected['pid'] == reload['new_pid'] and expected['start'] == reload['new_started_at'], "Evidence check failed: expected['pid'] == reload['new_pid'] and expected['start'] == reload['new_started_at']")
    require(release['shared_reader']['sha256'] == json.loads(manifest['text'])['artifacts']['source-study-reader']['sha256'], "Evidence check failed: release['shared_reader']['sha256'] == json.loads(manifest['text'])['artifacts']['source-study-reader']['sha256']")
    return {'minime': dict(boundary=clock(reload['new_started_at']), old_pid=reload['old_pid'], new_pid=reload['new_pid'], commit=spec['minime_commit'], commit_basis='documented source release; seven relevant reload source hashes verified separately', receipt_sha256=row('reload')['sha256'], manifest_sha256=manifest['sha256']), 'astrid': dict(boundary=clock(activation['new_process']['started_at']), old_pid=activation['old_pid'], new_pid=activation['new_process']['pid'], commit=identity[1], receipt_sha256=row('activation')['sha256'], manifest_sha256=manifest['sha256'], old_manifest_sha256=activation['old_identity']['manifest_sha256'])}

def _catalog(records, spec):
    row, value = _readers(records, spec)
    act = value('activation')
    reload = value('reload', True)
    manifest = row('manifest')
    verification = value('verification')
    commits = value('commits')
    require(act['status'] == 'activated_verified' and act['activation_performed'], "Evidence check failed: act['status'] == 'activated_verified' and act['activation_performed']")
    require(reload['outcome'] == 'success' and verification['complete_startup_hashes_match'], "Evidence check failed: reload['outcome'] == 'success' and verification['complete_startup_hashes_match']")
    require(act['manifest_sha256'] == manifest['sha256'] == verification['selection']['manifest_sha256'], "Evidence check failed: act['manifest_sha256'] == manifest['sha256'] == verification['selection']['manifest_sha256']")
    require(act['new_process']['pid'] == verification['astrid_pid'], "Evidence check failed: act['new_process']['pid'] == verification['astrid_pid']")
    require(reload['new_pid'] == verification['minime_pid'], "Evidence check failed: reload['new_pid'] == verification['minime_pid']")
    identity = act['new_process']['deployment_identity'].split(':')
    require(identity[0] == 'astrid' and len(identity) == 4, "Evidence check failed: identity[0] == 'astrid' and len(identity) == 4")
    require(json.loads(manifest['text'])['repository']['head'] == identity[1], "Evidence check failed: json.loads(manifest['text'])['repository']['head'] == identity[1]")
    minime_commit = next((c['implementation'] for c in commits if c['repo'] == '/Users/v/other/minime'))
    require(next((c['implementation'] for c in commits if c['repo'] == '/Users/v/other/astrid')) == identity[1], "Evidence check failed: next((c['implementation'] for c in commits if c['repo'] == '/Users/v/other/astrid')) == identity[1]")
    return {'minime': dict(boundary=clock(reload['new_started_at']), old_pid=reload['old_pid'], new_pid=reload['new_pid'], commit=minime_commit, commit_basis='owning implementation metadata; relevant startup hashes verified separately', receipt_sha256=row('reload')['sha256'], manifest_sha256=manifest['sha256']), 'astrid': dict(boundary=clock(act['new_process']['started_at']), old_pid=act['old_pid'], new_pid=act['new_process']['pid'], commit=identity[1], receipt_sha256=row('activation')['sha256'], manifest_sha256=manifest['sha256'], old_manifest_sha256=act['old_identity']['manifest_sha256'])}

def _interface(records, spec):
    row, value = _readers(records, spec)
    first = value('evidence/stage01-transaction/receipt.json')
    recovery_path = 'evidence/stage01-transaction/stopped-transition-recoveries/eebb4acb2e7d434dbcbc57a8681c5a78/receipt.json'
    recovery = value(recovery_path)
    final_path = 'evidence/stage02-transaction/receipt.json'
    final = value(final_path)
    reload_path = 'evidence/minime-reload.jsonl'
    reload = value(reload_path, True)
    m1 = value('bridge-stage-01/manifest.json')
    m2 = value('bridge-stage-02/manifest.json')
    source = value('evidence/paired-after/minime/runtime/autonomous_agent_source_status.json')
    host = value('evidence/minime-host-after.json')
    pair = value('evidence/paired-verification.json')
    integration = value('evidence/integration.json')
    followup = value('evidence/manifest-integration/receipt.json')
    review = value('evidence/stage02-independent-review.json')
    require(first['status'] == 'failed_requires_review' and (not first['activation_performed']), "Evidence check failed: first['status'] == 'failed_requires_review' and (not first['activation_performed'])")
    require(recovery['status'] == 'transition_recovered' and recovery['activation_performed'], "Evidence check failed: recovery['status'] == 'transition_recovered' and recovery['activation_performed']")
    require(not any((recovery[k] for k in ['signal_sent', 'drain_requested', 'force_used'])), "Evidence check failed: not any((recovery[k] for k in ['signal_sent', 'drain_requested', 'force_used']))")
    require(recovery['original_failure_sha256'] == row('evidence/stage01-transaction/receipt.json')['sha256'], "Evidence check failed: recovery['original_failure_sha256'] == row('evidence/stage01-transaction/receipt.json')['sha256']")
    require(recovery['manifest_sha256'] == row('bridge-stage-01/manifest.json')['sha256'] == first['manifest_sha256'], "Evidence check failed: recovery['manifest_sha256'] == row('bridge-stage-01/manifest.json')['sha256'] == first['manifest_sha256']")
    require(final['status'] == 'activated_verified' and final['activation_performed'], "Evidence check failed: final['status'] == 'activated_verified' and final['activation_performed']")
    require(final['old_pid'] == recovery['new_process']['pid'] == spec['first_astrid_pid'], "Evidence check failed: final['old_pid'] == recovery['new_process']['pid'] == spec['first_astrid_pid']")
    require(final['new_process']['pid'] == pair['astrid_pid'] == spec['final_astrid_pid'], "Evidence check failed: final['new_process']['pid'] == pair['astrid_pid'] == spec['final_astrid_pid']")
    require(final['manifest_sha256'] == row('bridge-stage-02/manifest.json')['sha256'] == pair['manifest_sha256'] == host['manifest_sha256'], "Evidence check failed: final['manifest_sha256'] == row('bridge-stage-02/manifest.json')['sha256'] == pair['manifest_sha256'] == host['manifest_sha256']")
    require(final['new_process'] == pair['astrid_startup'], "Evidence check failed: final['new_process'] == pair['astrid_startup']")
    require(final['new_process']['deployment_identity'].split(':')[1] == m2['repository']['head'] == spec['final_commit'], "Evidence check failed: final['new_process']['deployment_identity'].split(':')[1] == m2['repository']['head'] == spec['final_commit']")
    require(integration['minime_new'] == spec['minime_commit'], "Evidence check failed: integration['minime_new'] == spec['minime_commit']")
    require(integration['astrid_new'] == m1['repository']['head'] == followup['old'], "Evidence check failed: integration['astrid_new'] == m1['repository']['head'] == followup['old']")
    require(followup['new'] == spec['final_commit'], "Evidence check failed: followup['new'] == spec['final_commit']")
    require(reload['outcome'] == 'success' and (not reload['forced_termination']), "Evidence check failed: reload['outcome'] == 'success' and (not reload['forced_termination'])")
    require(reload['old_pid'] == spec['old_minime_pid'] and reload['new_pid'] == host['pid'] == source['pid'] == pair['minime_pid'] == spec['minime_pid'], "Evidence check failed: reload['old_pid'] == spec['old_minime_pid'] and reload['new_pid'] == host['pid'] == source['pid'] == pair['minime_pid'] == spec['minime_pid']")
    require(reload['source_inputs'] == source['source_inputs_at_start'], "Evidence check failed: reload['source_inputs'] == source['source_inputs_at_start']")
    require(len(reload['source_inputs']) == host['startup_inputs'] == pair['minime_sources'] == spec['source_count'], "Evidence check failed: len(reload['source_inputs']) == host['startup_inputs'] == pair['minime_sources'] == spec['source_count']")
    require(not source['source_changed_since_start'] and (not source['reload_required']) and (host['changed'] == []), "Evidence check failed: not source['source_changed_since_start'] and (not source['reload_required']) and (host['changed'] == [])")
    require(host['no_launchd_helper_or_root_override'], "Evidence check failed: host['no_launchd_helper_or_root_override']")
    require(host['selected_helper'] == m2['artifacts']['source-study-reader']['path'], "Evidence check failed: host['selected_helper'] == m2['artifacts']['source-study-reader']['path']")
    require(host['selected_helper_sha256'] == m1['artifacts']['source-study-reader']['sha256'] == m2['artifacts']['source-study-reader']['sha256'] == spec['helper_sha256'], "Evidence check failed: host['selected_helper_sha256'] == m1['artifacts']['source-study-reader']['sha256'] == m2['artifacts']['source-study-reader']['sha256'] == spec['helper_sha256']")
    require(review['verified'] and review['failures'] == [] and all(review['checks'].values()), "Evidence check failed: review['verified'] and review['failures'] == [] and all(review['checks'].values())")
    require(review['manifest_sha256'] == final['manifest_sha256'] and review['expected_commit'] == spec['final_commit'], "Evidence check failed: review['manifest_sha256'] == final['manifest_sha256'] and review['expected_commit'] == spec['final_commit']")
    for index, manifest in [(1, m1), (2, m2)]:
        name = f'bridge-stage-0{index}/source-inputs.json'
        require(row(name)['sha256'] == manifest['source_inputs']['sha256'], "Evidence check failed: row(name)['sha256'] == manifest['source_inputs']['sha256']")
    require(clock(recovery['new_process']['started_at']) < clock(reload['new_started_at']) < clock(final['new_process']['started_at']), "Evidence check failed: clock(recovery['new_process']['started_at']) < clock(reload['new_started_at']) < clock(final['new_process']['started_at'])")
    return {'minime': dict(boundary=clock(reload['new_started_at']), old_pid=spec['old_minime_pid'], new_pid=spec['minime_pid'], commit=spec['minime_commit'], commit_basis=f"owning integration metadata; exact {spec['source_count']} declared reload hashes independently equal recorded loaded inputs", receipt_sha256=row(reload_path)['sha256'], manifest_sha256=final['manifest_sha256']), 'astrid': dict(boundary=clock(recovery['new_process']['started_at']), old_pid=spec['old_astrid_pid'], new_pid=spec['first_astrid_pid'], commit=m1['repository']['head'], receipt_sha256=row(recovery_path)['sha256'], manifest_sha256=recovery['manifest_sha256'], old_manifest_sha256=first['old_identity']['manifest_sha256'], final_stage=dict(boundary=clock(final['new_process']['started_at']), new_pid=spec['final_astrid_pid'], commit=spec['final_commit'], manifest_sha256=final['manifest_sha256'], receipt_sha256=row(final_path)['sha256'])), 'helper_sha256': spec['helper_sha256'], 'helper_identity_limit': 'Both interface stages have identical helper bytes. Study-direction and interface releases share an exact study system prompt; clock strata and prompts do not prove each invocation binary.', 'paired_verification_utc': pair['paired_verification_utc'], 'host_reload_verified_at': reload['recorded_at']}
