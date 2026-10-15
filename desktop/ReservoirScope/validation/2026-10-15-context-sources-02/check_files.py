#!/usr/bin/env python3
"""Run explicit file/synthetic checks with byte identities; never launch a model."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
HERE=Path(__file__).resolve().parent

def identity(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 mode=sys.argv[1];dest=HERE/f'{mode}-01.json'
 if dest.exists():raise FileExistsError(dest)
 sources=[p for p in sorted(HERE.glob('*.py'))]+[HERE/'run-plan.json']
 before=[identity(p) for p in sources]
 args={'preparation-checks':[sys.executable,'-m','unittest','-v','test_prepare_inputs'], 'input-generation':[sys.executable,'prepare_inputs.py'], 'runtime-checks':[sys.executable,'-m','unittest','-v','test_owned_model','test_run_probe','test_render_blind_pack','test_runtime_reuse']}[mode]
 started=dt.datetime.now(dt.timezone.utc).isoformat()
 run=subprocess.run(args,cwd=HERE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
 log=HERE/f'{mode}-01.log';log.write_bytes(run.stdout)
 after=[identity(p) for p in sources]
 result=dict(atUtc=started,command=args,exitCode=run.returncode,passed=run.returncode==0 and before==after,sourceUnchanged=before==after,sourceBefore=before,sourceAfter=after,log=identity(log),scope='Synthetic/file-only tests or file-only preparation; no model/service/host admission.')
 if mode=='input-generation' and run.returncode==0:result['outputs']=[identity(p) for p in sorted((HERE/'prompts').glob('*.txt'))]+[identity(HERE/'transformation-checks-01.json'),identity(HERE/'frozen-inputs.json')]
 with dest.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(dict(mode=mode,passed=result['passed'],log=str(log),tail=run.stdout.decode()[-1000:])))
 return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
