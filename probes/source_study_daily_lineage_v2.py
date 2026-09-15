"""Offline S-007 day-7 lineage and predeclared map-to-source continuation."""
import json
from reservoir_research.study_capture import sha
def build(packet):
    root=packet.parents[2]
    before=(packet/'tracking-before.json').read_bytes()
    tracking=json.loads(before)
    protocol=json.loads((packet/'protocol.json').read_bytes())
    report=json.loads((packet/'final-report/report.json').read_bytes())
    assert sha(before)==protocol['ledger_sha256']
    assert tracking['last_completed_cutoff']==protocol['since']
    assert tracking['next_window']['until_exclusive']==protocol['until_exclusive']
    preserved={}
    for window in tracking['windows']:
        historical=(root/window['capture']).parent
        manifest=json.loads((historical/'packet-manifest.json').read_bytes())
        for path,digest in manifest.items():
            assert sha((historical/path).read_bytes())==digest,(historical.name,path)
        preserved[historical.name]=len(manifest)
    ids=[s['id'] for s in report['studies']]
    assert len(ids)==len(set(ids)) and not set(ids).intersection(tracking['seen_generations'])
    historical=(root/tracking['windows'][-1]['capture']).parent
    inherited={}
    for name in ['era-supplement.json','source-bindings.json','catchup-era.json','catchup-activation.json','catchup-bindings.json']:
        raw=(packet/name).read_bytes()
        assert raw==(historical/name).read_bytes()
        inherited[name]=sha(raw)
    capture=json.loads((packet/'capture.json').read_bytes())
    active_rows=[r for r in capture['records'] if r['path'].endswith('/bridge-deployment/active.json')]
    assert len(active_rows)==1
    active=json.loads(active_rows[0]['text'])
    known=report['release_eras']['catalog-navigation-sep15']
    assert active['manifest_sha256']==known['astrid']['manifest_sha256']
    pids={report['release_eras'][e]['minime']['new_pid'] for e in ['journal-coherence','catalog-navigation-sep15']}
    assert {s['pid'] for s in report['studies']}==pids
    return dict(schema='s007_daily_lineage_v2',prior_ledger_sha256=sha(before),
        previous_cutoff=tracking['last_completed_cutoff'],window_end=protocol['until_exclusive'],
        prior_generations=len(tracking['seen_generations']),new_generations=len(ids),
        resulting_generations=len(tracking['seen_generations'])+len(ids),
        repeated_ids=[],changed_same_id_records=[],preserved_historical_files=preserved,
        historical_files=sum(preserved.values()),inherited_release_hashes=inherited,
        captured_bridge_selection_sha256=active_rows[0]['sha256'],
        captured_bridge_manifest=active['manifest_sha256'],minime_pids=sorted(pids),
        limits='Captured bridge selection and PIDs agree with reviewed releases; not continuous surveillance or proof of deployment of studied source revisions.')
def followup(packet):
    root=packet.parents[2]
    protocol=json.loads((packet/'protocol.json').read_bytes())
    tracking=json.loads((packet/'tracking-before.json').read_bytes())
    previous=json.loads((root/tracking['windows'][-1]['report']).read_bytes())
    report=json.loads((packet/'final-report/report.json').read_bytes())
    prior=previous['studies'][-1]
    first=report['studies'][0]
    assert prior['next_action']=='SELF_STUDY MAP astrid --page 29'
    assert first['action_text']==prior['next_action'] and first['kind']=='map' and first['receipt_verified']
    links=[]
    for ident in report['close_reading_ids']:
        i=next(i for i,s in enumerate(report['studies']) if s['id']==ident)
        a,b=report['studies'][i:i+2]
        assert a['next_action']==b['action_text'] and b['receipt_verified'] and b['kind']=='map'
        current=a['user_text'].split('RECALLED ACCOUNT')[0]
        assert 'steward-notes/' in current and not a['pages']
        assert 'spectral_explorer' in a['notebook']['fields']['previous']['text']
        links.append(dict(from_id=a['id'],next_action=a['next_action'],to_id=b['id'],input_kind=b['input_kind']))
    source=next((s for s in report['studies'] if s['receipt_verified'] and s['pages']),None)
    return dict(schema='s007_map_source_followup_v1',selection=protocol['followup'],
        prior_last_generation_id=prior['id'],prior_last_next=prior['next_action'],
        first_observed_study=first,selected_navigation_links=links,first_verified_source=source,
        before_first_source_count=report['studies'].index(source) if source else len(report['studies']),
        limits='Predeclared exposure-based follow-up separate from first-three sample; not correction prevalence or a causal release effect.')
