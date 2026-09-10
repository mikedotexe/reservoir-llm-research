"""Observe natural provider receipts after authorized rollout; no generation calls."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path('/Users/v/other')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--since-ms',type=int,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True,mode=0o700)
    report={'schema':'provider_controls_natural_rollout_v1','since_unix_ms':args.since_ms,'astrid':[],'minime':[],
        'natural_requests_only':True,'model_requests_induced':0}
    astrid=ROOT/'astrid/capsules/spectral-bridge/workspace/provider_observations/20260908-live-01/events'
    for path in sorted(astrid.glob('*-outcome.json')):
        if path.stat().st_mtime*1000 < args.since_ms:continue
        d=json.loads(path.read_text());controls=d.get('generation_controls')
        if not controls or d.get('created_at_unix_ms',0)<args.since_ms:continue
        report['astrid'].append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            attempt_id=d.get('attempt_id'),label=d.get('label'),provider=d.get('provider'),outcome=d.get('outcome'),
            pid=d.get('pid'),controls=controls))
    for path in sorted((ROOT/'minime/workspace/generations').glob('*/*.json')):
        if path.stat().st_mtime*1000 < args.since_ms:continue
        d=json.loads(path.read_text());controls=d.get('generation_controls')
        if not controls or d.get('created_at_unix_ms',0)<args.since_ms:continue
        report['minime'].append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            generation_id=d.get('generation_id'),lane=d.get('lane'),backend=d.get('backend'),status=d.get('status'),
            pid=d.get('pid'),controls=controls,backend_timing=d.get('backend_timing')))
    (args.output/'natural-control-receipts.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({being:len(report[being]) for being in ['astrid','minime']}))

if __name__=='__main__':main()
