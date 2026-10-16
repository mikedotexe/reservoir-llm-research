#!/usr/bin/env python3
"""Explicit full frontend tests, TypeScript/Vite, metadata and reference checks; no app/provider/package launch."""
import argparse,json,os,sys
sys.dont_write_bytecode=True
from checks_common import OUT,attempt,commands,environment,execute,inputs,sha,utc,validate_metadata
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--attempt',default='01');a=p.parse_args();number=attempt(a.attempt)
    jobs=commands('frontend');out=OUT/f'frontend-checks-{number}.json'
    if any((OUT/f'{n}-{number}.log').exists() for n,_ in jobs):raise ValueError('Check logs must be new; use a new attempt')
    before=inputs('frontend');report={'schema':'reservoir-scope-frontend-source-checks-v1','startedAtUtc':utc(),'scope':'Full frontend suite, TypeScript/Vite, consistent package/lock versions and reference checks on final 0.24.0 code/config; no app, provider, service or package build.','sourceInputsSha256':before,'helperInputsSha256':{p.name:sha(p) for p in [Path(__file__),OUT/'checks_common.py']},'commands':[],'status':'running'}
    with out.open('x') as f:
        json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
        try:
            report['metadataBefore']=validate_metadata()
            for name,command in jobs:
                row=execute(name,command,number,environment());report['commands'].append(row);print(json.dumps(row),flush=True)
                if row['exitCode']:break
            report['metadataAfter']=validate_metadata()
            assert report['metadataBefore']==report['metadataAfter'], 'Metadata changed during checks'
        except Exception as error:report['error']=f'{type(error).__name__}: {error}'
        after=inputs('frontend');report['sourceChangesDuringChecks']=[p for p in sorted(before.keys()|after.keys()) if before.get(p)!=after.get(p)]
        report['counts']=report['commands'][0].get('counts') if report['commands'] else None
        report['status']='passed' if len(report['commands'])==len(jobs) and all(r['exitCode']==0 for r in report['commands']) and not report['sourceChangesDuringChecks'] and 'error' not in report else 'failed'
        report['finishedAtUtc']=utc();f.seek(0);json.dump(report,f,indent=2);f.write('\n');f.truncate();f.flush();os.fsync(f.fileno())
    print(json.dumps({'status':report['status'],'counts':report['counts'],'receipt':str(out)}),flush=True)
    return 0 if report['status']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
