"""Offline journal-coherence release binding from retained activation evidence."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from source_study_daily_eras import additional_eras as previous_eras

def additional_eras(records):
    result = previous_eras(records)
    def row(suffix):
        found = [r for r in records if r['path'].endswith(suffix)]
        assert len(found) == 1, suffix
        return found[0]
    def value(suffix, lines=False):
        r = row(suffix)
        return json.loads(r['text'].splitlines()[-1] if lines else r['text'])
    def clock(text):
        return datetime.strptime(text, '%a %b %d %H:%M:%S %Y').replace(tzinfo=ZoneInfo('America/Los_Angeles')).timestamp()
    stage = '/journal-coherence-20260911/'
    activation_suffix = '/transactions/c6d672c9e4eb4255a0dd025040023608/receipt.json'
    activation = value(activation_suffix)
    reload_suffix = stage + 'minime-reload.jsonl'
    reload = value(reload_suffix, True)
    manifest = row(stage + 'bridge-stage-01/manifest.json')
    release = value(stage + 'rollout-verification.json')
    state = value(stage + 'live-after.json')
    assert activation['status'] == 'activated_verified' and activation['activation_performed']
    assert reload['outcome'] == 'success'
    assert activation['manifest_sha256'] == manifest['sha256'] == state['bridge_selection']['value']['manifest_sha256']
    identity = activation['new_process']['deployment_identity'].split(':')
    assert identity[0] == 'astrid' and len(identity) == 4
    assert json.loads(manifest['text'])['repository']['head'] == identity[1]
    for owner, pid, start in [('minime', reload['new_pid'], reload['new_started_at']),
                              ('bridge', activation['new_process']['pid'], activation['new_process']['started_at'])]:
        assert release[owner]['pid'] == pid and release[owner]['started_at'] == start
    assert release['bridge']['deployment_identity'] == activation['new_process']['deployment_identity']
    expected = state['services']['com.minime.autonomous-agent']
    assert expected['pid'] == reload['new_pid'] and expected['start'] == reload['new_started_at']
    assert release['shared_reader']['sha256'] == json.loads(manifest['text'])['artifacts']['source-study-reader']['sha256']
    result['journal-coherence'] = {
        'minime': dict(boundary=clock(reload['new_started_at']), old_pid=reload['old_pid'], new_pid=reload['new_pid'],
                       commit='96b0b615d917c8edc164ab8a457c1dd1ddb5b0df',
                       commit_basis='documented source release; seven relevant reload source hashes verified separately',
                       receipt_sha256=row(reload_suffix)['sha256'], manifest_sha256=manifest['sha256']),
        'astrid': dict(boundary=clock(activation['new_process']['started_at']), old_pid=activation['old_pid'],
                       new_pid=activation['new_process']['pid'], commit=identity[1],
                       receipt_sha256=row(activation_suffix)['sha256'], manifest_sha256=manifest['sha256'],
                       old_manifest_sha256=activation['old_identity']['manifest_sha256'])}
    return result
