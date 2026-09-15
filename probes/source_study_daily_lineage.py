"""Offline S-007 ledger lineage, historical preservation and declared release checks."""
import json
from pathlib import Path
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
    assert len(ids)==len(set(ids))
    repeated=set(ids).intersection(tracking['seen_generations'])
    assert not repeated,sorted(repeated)
    historical=(root/tracking['windows'][-1]['capture']).parent
    inherited={}
    for name in ['era-supplement.json','source-bindings.json','catchup-era.json','catchup-activation.json','catchup-bindings.json']:
        raw=(packet/name).read_bytes()
        assert raw==(historical/name).read_bytes(),name
        inherited[name]=sha(raw)
    capture=json.loads((packet/'capture.json').read_bytes())
    active_rows=[r for r in capture['records'] if r['path'].endswith('/bridge-deployment/active.json')]
    assert len(active_rows)==1
    active=json.loads(active_rows[0]['text'])
    known=report['release_eras']['journal-coherence']
    assert active['manifest_sha256']==known['astrid']['manifest_sha256']
    assert active['stage'].endswith('/journal-coherence-20260911/bridge-stage-01')
    assert all(s['pid']==known['minime']['new_pid'] for s in report['studies'])
    plan=json.loads((packet/'exploratory-readings-protocol.json').read_bytes())
    samples=json.loads((packet/'exploratory-readings.json').read_bytes())
    assert samples['selection']==plan
    assert samples['studies']==[s for s in report['studies'] if s['id'] in plan['generation_ids']]
    return dict(schema='s007_daily_lineage_v1',prior_ledger_sha256=sha(before),
                previous_cutoff=tracking['last_completed_cutoff'],window_end=protocol['until_exclusive'],
                prior_generations=len(tracking['seen_generations']),new_generations=len(ids),
                resulting_generations=len(tracking['seen_generations'])+len(ids),
                repeated_ids=[],changed_same_id_records=[],preserved_historical_files=preserved,
                historical_files=sum(preserved.values()),inherited_release_hashes=inherited,
                captured_bridge_selection_sha256=active_rows[0]['sha256'],
                captured_bridge_manifest=active['manifest_sha256'],minime_pid=known['minime']['new_pid'],
                exploratory_reading_ids=plan['generation_ids'],
                limits='Current bridge selection and generation PIDs agree with retained journal-coherence evidence; this is not a continuous process audit or proof of the deployment of each studied source revision. Exploratory readings remain outside the fixed first-three sample.')
