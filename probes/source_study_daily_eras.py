"""Offline S-007 release bindings for the September 9–10 extended schemas."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo


def additional_eras(records):
    def row(suffix):
        found = [r for r in records if r['path'].endswith(suffix)]
        assert len(found) == 1, suffix
        return found[0]

    def value(suffix, lines=False):
        r = row(suffix)
        return json.loads(r['text'].splitlines()[-1] if lines else r['text'])

    def clock(text):
        return datetime.strptime(text, '%a %b %d %H:%M:%S %Y').replace(tzinfo=ZoneInfo('America/Los_Angeles')).timestamp()

    result = {}
    definitions = [
        ('extended-writing', 'longform-20260909',
         '/stopped-transition-recoveries/98ce3bc70c2e4623918c164430faa256/receipt.json',
         '/longform-20260909/minime-reload.jsonl', '33c324d229893a061ea958891f19fa450f232bd6'),
        ('activation-controls', 'activation-controls-20260909',
         '/transactions/27a2ff67cdcf4785802e5b10128b12cc/receipt.json',
         '/activation-controls-20260909/minime-reload-v2.jsonl', '997de4f04244f334313eb900f20ea3a4f7071d50'),
        ('study-navigation', 'study-navigation-20260910',
         '/study-navigation-20260910/bridge-activated-receipt.json',
         '/study-navigation-20260910/minime-reload.json', '15df37ea4524375c1d9e816e5c8a447d02cc4cb5'),
    ]
    for name, stage, activation_suffix, reload_suffix, commit in definitions:
        activation = value(activation_suffix)
        reload = value(reload_suffix, True)
        manifest = row('/' + stage + '/bridge-stage-01/manifest.json')
        assert activation['status'] in ['activated_verified', 'transition_recovered']
        assert activation['activation_performed'] and reload['outcome'] == 'success'
        assert activation['manifest_sha256'] == manifest['sha256']
        identity = activation['new_process']['deployment_identity'].split(':')
        assert identity[0] == 'astrid' and len(identity) == 4
        if name == 'extended-writing':
            release = value('/2026-09-09-extended-writing-qualification/rollout/live-rollout.json')
            assert release['verified'] and release['manifest_sha256'] == manifest['sha256']
            assert release['bridge']['activation_receipt_sha256'] == row(activation_suffix)['sha256']
            assert release['minime']['receipt_sha256'] == row(reload_suffix)['sha256']
            assert release['minime']['new_pid'] == reload['new_pid']
            assert release['minime']['started_at'] == reload['new_started_at']
            assert release['astrid_commit'] == identity[1] and release['minime_commit'] == commit
            failure = row('/transactions/1ec9dc0fb1c94c76ba6170542570d701/receipt.json')
            assert failure['sha256'] == activation['original_failure_sha256']
        if name == 'activation-controls':
            state = value('/activation-controls-20260909/final-provider-rollout.json')
            assert state['selection']['value']['manifest_sha256'] == manifest['sha256']
            expected = state['processes']['com.minime.autonomous-agent']
            assert expected['pid'] == reload['new_pid'] and expected['started_at'] == reload['new_started_at']
        if name == 'study-navigation':
            state = value('/study-navigation-20260910/live-verified.json')
            expected = state['services']['com.minime.autonomous-agent']['after']
            assert expected['pid'] == reload['new_pid'] and expected['started_at'] == reload['new_started_at']
            assert state['minime_source_loaded_matches_receipt']
        result[name] = {
            'minime': dict(boundary=clock(reload['new_started_at']), old_pid=reload['old_pid'], new_pid=reload['new_pid'],
                           commit=commit, commit_basis='documented release; reload source hashes retained separately',
                           receipt_sha256=row(reload_suffix)['sha256'], manifest_sha256=manifest['sha256']),
            'astrid': dict(boundary=clock(activation['new_process']['started_at']), old_pid=activation['old_pid'],
                           new_pid=activation['new_process']['pid'], commit=identity[1],
                           receipt_sha256=row(activation_suffix)['sha256'], manifest_sha256=manifest['sha256'],
                           old_manifest_sha256=activation['old_identity']['manifest_sha256'])}
    return result
