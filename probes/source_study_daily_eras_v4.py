"""Offline binding of the September-15 catalog navigation release."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from source_study_daily_eras_v3 import additional_eras as older_eras

def additional_eras(records):
    result=older_eras(records)
    def row(suffix):
        rows=[r for r in records if r['path'].endswith(suffix)]
        assert len(rows)==1,suffix
        return rows[0]
    def value(suffix,lines=False):
        raw=row(suffix)['text']
        return json.loads(raw.splitlines()[-1] if lines else raw)
    stage='/study-navigation-20260915/'
    act_suffix='/transactions/417c7c5b1bb14cf6bc433b4eaec03aca/receipt.json'
    reload_suffix=stage+'minime-restart.jsonl'
    act=value(act_suffix);reload=value(reload_suffix,True)
    manifest=row(stage+'bridge-stage-01/manifest.json')
    verification=value(stage+'evidence/paired-verification.json')
    commits=value(stage+'evidence/implementation-commits.json')
    assert act['status']=='activated_verified' and act['activation_performed']
    assert reload['outcome']=='success' and verification['complete_startup_hashes_match']
    assert act['manifest_sha256']==manifest['sha256']==verification['selection']['manifest_sha256']
    assert act['new_process']['pid']==verification['astrid_pid']
    assert reload['new_pid']==verification['minime_pid']
    identity=act['new_process']['deployment_identity'].split(':')
    assert identity[0]=='astrid' and len(identity)==4
    assert json.loads(manifest['text'])['repository']['head']==identity[1]
    minime_commit=next(c['implementation'] for c in commits if c['repo']=='/Users/v/other/minime')
    assert next(c['implementation'] for c in commits if c['repo']=='/Users/v/other/astrid')==identity[1]
    def clock(text):
        return datetime.strptime(text,'%a %b %d %H:%M:%S %Y').replace(tzinfo=ZoneInfo('America/Los_Angeles')).timestamp()
    result['catalog-navigation-sep15']={
        'minime':dict(boundary=clock(reload['new_started_at']),old_pid=reload['old_pid'],new_pid=reload['new_pid'],
                      commit=minime_commit,commit_basis='owning implementation metadata; relevant startup hashes verified separately',
                      receipt_sha256=row(reload_suffix)['sha256'],manifest_sha256=manifest['sha256']),
        'astrid':dict(boundary=clock(act['new_process']['started_at']),old_pid=act['old_pid'],new_pid=act['new_process']['pid'],
                      commit=identity[1],receipt_sha256=row(act_suffix)['sha256'],manifest_sha256=manifest['sha256'],
                      old_manifest_sha256=act['old_identity']['manifest_sha256'])}
    return result
