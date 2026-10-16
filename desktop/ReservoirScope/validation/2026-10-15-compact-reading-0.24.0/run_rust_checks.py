#!/usr/bin/env python3
"""Explicit full Rust suites/Clippy and resource/format gates; no GUI/provider launch.

Unit tests may create their own ephemeral loopback fixtures, never model services.
No previous test execution is reused. Do not run concurrently with another cargo job.
"""
import argparse,json,os,sys
sys.dont_write_bytecode=True
from pathlib import Path
from checks_common import OUT,attempt,commands,environment,execute,inputs,sha,utc

def rows(values):return [{'path':p,'sha256':v} for p,v in sorted(values.items())]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--attempt',default='01');a=p.parse_args();number=attempt(a.attempt)
    jobs=commands('rust');out=OUT/f'rust-checks-{number}.json'
    if any((OUT/f'{n}-{number}.log').exists() for n,_ in jobs):raise ValueError('Check logs must be new; use a new attempt')
    before=inputs('rust');env=environment();report={'schema':'compact-reading-rust-checks-v1','startedAtUtc':utc(),'scope':__doc__,'sourceBefore':rows(before),'helperInputsSha256':{p.name:sha(p) for p in [Path(__file__),OUT/'checks_common.py']},'environment':{k:env[k] for k in ['DEVELOPER_DIR','SDKROOT','CARGO_INCREMENTAL','CARGO_BUILD_JOBS']},'checks':[],'passed':False}
    with out.open('x') as f:
        json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
        try:
            for name,command in jobs:
                row=execute(name,command,number,env);report['checks'].append(row);print(json.dumps(row),flush=True)
                if row['exitCode']:break
        except Exception as error:report['error']=f'{type(error).__name__}: {error}'
        after=inputs('rust');report.update(sourceAfter=rows(after),sourceUnchanged=before==after,endedAtUtc=utc())
        report['passed']=len(report['checks'])==len(jobs) and all(r['exitCode']==0 for r in report['checks']) and report['sourceUnchanged'] and 'error' not in report
        f.seek(0);json.dump(report,f,indent=2);f.write('\n');f.truncate();f.flush();os.fsync(f.fileno())
    print(json.dumps({'passed':report['passed'],'sourceUnchanged':report['sourceUnchanged'],'receipt':str(out)}),flush=True)
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
