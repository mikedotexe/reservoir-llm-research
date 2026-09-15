"""Verify the frozen first live observer window without accessing live services."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);args=parser.parse_args()
    root=args.root
    deployment=root/'release-verification'
    binding=json.loads((deployment/'verification.json').read_text())
    activation=json.loads((deployment/'activation-projected.json').read_text())
    manifest_raw=(deployment/'manifest.json').read_bytes()
    manifest=json.loads(manifest_raw)
    inputs_raw=(deployment/'source-inputs.json').read_bytes()
    inputs=json.loads(inputs_raw)
    assert sha(manifest_raw)==binding['manifest_sha256']==activation['manifest_sha256']
    assert sha(inputs_raw)==binding['source_inputs_sha256']==manifest['source_inputs']['sha256']
    assert len(inputs['files'])==binding['source_count']
    assert all(row['verified'] is True for row in binding['source_checks'])
    expected={row['path']:row['sha256'] for row in inputs['files']}
    assert expected=={row['path']:row['sha256'] for row in binding['source_checks']}
    assert binding['artifacts']['spectral-bridge']==activation['binary_sha256']
    assert activation['status']=='activated_verified' and activation['force_used'] is False
    assert activation['new_process']['pid']==binding['pid']
    assert activation['new_process']['new_saved_exchange_observed'] is True
    assert activation['startup_lineage']['state_targets_this_binary'] is True
    before=json.loads((root/'before-activation.json').read_text())
    after=json.loads((root/'after-activation.json').read_text())
    protected=[key for key in before['processes'] if key!='com.astrid.spectral-bridge']
    assert all(before['processes'][key]==after['processes'][key] for key in protected)
    assert after['processes']['com.astrid.spectral-bridge']['pid']==binding['pid']
    assert before['processes']['com.astrid.spectral-bridge']['plist_sha256']==after['processes']['com.astrid.spectral-bridge']['plist_sha256']
    final=json.loads((root/'final-process-snapshot.json').read_text())
    assert all(before['processes'][key]==final['processes'][key] for key in protected)
    assert final['processes']['com.astrid.spectral-bridge']['pid']==binding['pid']
    restored=json.loads((root/'control-restoration.json').read_text())
    assert restored['before_state']['paused'] is True
    assert restored['after_state']['paused'] is False
    assert restored['after_state']['pause_generation']==restored['before_state']['pause_generation']+1
    assert restored['after_state']['actor']=='codex-provider-observer-rollout'
    directory=root/'natural-window'
    summary=json.loads((directory/'summary.json').read_text())
    inventory=json.loads((directory/'manifest.json').read_text())
    events=[];generations=[];raws={}
    for row in inventory:
        path=directory/row['capture'];raw=path.read_bytes()
        assert sha(raw)==row['sha256'] and len(raw)==row['bytes']
        assert row['source_mode']=='0o600'
        if row['capture'].startswith('events/'):
            events.append(json.loads(raw))
        elif row['capture'].startswith('generations/'):
            generations.append(json.loads(raw))
        else:
            assert row['capture'].startswith('raw/') and sha(raw)==path.stem
            raws[row['capture']]=raw
    assert summary['source_spool_mode']=='0o700'
    dispatch={e['attempt_id']:e for e in events if e['stage']=='dispatch_started'}
    outcomes={e['attempt_id']:e for e in events if e['stage']=='provider_outcome'}
    decisions=[e for e in events if e['stage']=='dialogue_decision']
    assert len(dispatch)==summary['dispatches'] and len(outcomes)==summary['outcomes']
    assert sorted(dispatch.keys()-outcomes.keys())==summary['pending_attempts']
    assert len(dispatch)+len(outcomes)+len(decisions)==len(events)
    for aid,d in dispatch.items():
        assert summary['window_start_unix_ms'] <= d['created_at_unix_ms'] < summary['window_end_unix_ms']
        assert d['pid']==binding['pid']
        release=d['release_before']
        assert release['status']=='startup_verified_process_binding'
        assert release['manifest_sha256']==binding['manifest_sha256']
        assert release['binary_sha256']==binding['artifacts']['spectral-bridge']
        if aid not in outcomes:
            continue
        o=outcomes[aid]
        assert o['release_before']==o['release_after']==release
        assert all(o[k]==d[k] for k in ['pid','request_sha256','generation_id','logical_attempt_index','provider','created_at_unix_ms'])
        assert o['created_at_unix_ms']+o['elapsed_ms'] < summary['window_end_unix_ms']+120000
        if o.get('raw_artifact'):
            assert sha(raws[o['raw_artifact']])==o['raw_response_sha256']
        if o['input_availability']=='observed_no_markers_raw_not_retained':
            assert o['marker_observed_total']==0 and o.get('raw_artifact') is None
    decision_keys=set()
    for decision in decisions:
        key=(decision['generation_id'],decision['logical_attempt_index'])
        assert key not in decision_keys
        decision_keys.add(key)
        for link in decision['attempts']:
            if link['attempt_id'] in outcomes:
                outcome=outcomes[link['attempt_id']]
                assert link['outcome']==outcome['outcome']
                assert link['input_availability']==outcome['input_availability']
        matches=[g for g in generations if (g['generation_id'],g['attempt_index'])==key]
        assert len(matches)==1
        g=matches[0];obs=g['provider_observation']
        assert g['pid']==binding['pid'] and obs['status']=='enabled'
        assert obs['decision_recording_status']=='recorded'
        assert obs['attempts']==decision['attempts']
        assert obs['accepted_output_sha256']==decision['accepted_output_sha256']
        if g.get('response_text') is not None:
            assert sha(g['response_text'].encode())==g['response_sha256']
    linked={(d['generation_id'],d['logical_attempt_index']) for d in dispatch.values() if d.get('generation_id')}
    result={'schema':'provider_observer_live_window_verification_v1','verified':True,
        'pid':binding['pid'],'protected_service_identities_unchanged':len(protected),
        'controller_restored_unpaused':True,
        'capture_files_verified':len(inventory),'dispatches':len(dispatch),'outcomes':len(outcomes),
        'pending_attempts':summary['pending_attempts'],'dialogue_decisions':len(decisions),
        'generation_records':len(generations),'missing_decision_keys':sorted(linked-decision_keys),
        'provider_counts':dict(Counter(d['provider'] for d in dispatch.values())),
        'outcome_counts':dict(Counter(o['outcome'] for o in outcomes.values())),
        'input_availability':dict(Counter(o['input_availability'] for o in outcomes.values())),
        'earlier_recording_status':dict(Counter(o['earlier_recording_status'] for o in outcomes.values())),
        'raw_artifacts':len(raws),'observed_marker_total':sum(o.get('marker_observed_total') or 0 for o in outcomes.values()),
        'unknown_marker_inputs':sum(o.get('marker_observed_total') is None for o in outcomes.values()),
        'window_start_unix_ms':summary['window_start_unix_ms'],'window_end_unix_ms':summary['window_end_unix_ms'],
        'limits':'Startup window only. Source byte checks were run on host and their bindings checked here. No operational or experienced benefit inferred.'}
    (root/'independent-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
