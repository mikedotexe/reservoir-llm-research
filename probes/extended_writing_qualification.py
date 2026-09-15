"""Two fixed uncoupled native-backend capacity/admission trials, no Being state writes.
No length target, retries for prose, model/coupling changes, or output injection.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/outputs/2026-09-09-extended-writing-qualification'
HELPER=Path('/Users/v/other/worktrees/longform-20260909/astrid/target/debug/astrid-source-study')
def sha(raw): return hashlib.sha256(raw).hexdigest()
def main():
    OUT.mkdir(exist_ok=False)
    previous=ROOT/'research/outputs/2026-09-09-study-claim-check/attempt-4.json'
    prior=json.loads(previous.read_text())
    control=json.loads(prior['request_json'])
    control['options'].update(num_predict=8192,num_ctx=65536,seed=91)
    control['messages'][0]['content'] += '\nAn output ceiling of 8192 tokens is available. Develop your account at the length you find useful; there is no minimum length.'
    args=dict(astrid_root='/Users/v/other/astrid', minime_root='/Users/v/other/minime', state_directory=str(OUT/'isolated-draft'),operation='prepare',action='WRITE PROFILE EXTENDED')
    result=subprocess.run([str(HELPER)],input=json.dumps(args),capture_output=True,text=True,check=True)
    args['action']='WRITE START What distinguishes reading more source from understanding a call path? Consider what evidence could change a saved explanation, and what remains uncertain.'
    offer=json.loads(subprocess.run([str(HELPER)],input=json.dumps(args),capture_output=True,text=True,check=True).stdout)
    draft=json.loads(json.dumps(control));draft['messages']=[dict(role='system',content=offer['system_prompt']),dict(role='user',content=offer['text'])]
    plan=[dict(case='source_correct_control',request=control),dict(case='private_draft',request=draft)]
    protocol=dict(schema='extended_writing_qualification_v1',frozen_at=datetime.now(timezone.utc).isoformat(),source_record_sha256=sha(previous.read_bytes()),helper_sha256=sha(HELPER.read_bytes()),route='http://localhost:11434/api/chat',deadline_seconds=1200,plan=plan,
      scope='Two uncoupled Ollama requests with the proposed output/context allowance; no natural Being-learning or coupled-Astrid conclusion. A short response remains valid. This checks admission/usability, not proven use of all 8192 tokens.',
      stop='No retries. Stop after transport, empty or length-terminated generation; retain all evidence.')
    (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    (OUT/'probe.py').write_bytes(Path(__file__).read_bytes())
    for i,item in enumerate(plan):
        raw=json.dumps(item['request'],ensure_ascii=False,separators=(',',':')).encode()
        record=dict(case=item['case'],request_json=raw.decode(),request_sha256=sha(raw),started_utc=datetime.now(timezone.utc).isoformat())
        print(json.dumps(dict(case=item['case'],started=record['started_utc'])),flush=True)
        started=time.monotonic()
        try:
            req=urllib.request.Request(protocol['route'],data=raw,headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=1200) as response:
                body=response.read();record['http_status']=response.status
            parsed=json.loads(body);text=parsed.get('message',{}).get('content','')
            record.update(response_json=body.decode(),response_sha256=sha(body),finish=parsed.get('done_reason'),generated_tokens=parsed.get('eval_count'),prompt_tokens=parsed.get('prompt_eval_count'),visible_chars=len(text),complete=bool(parsed.get('done') and parsed.get('done_reason')=='stop' and text.strip()))
        except Exception as error: record.update(complete=False,error=f'{type(error).__name__}: {error}')
        record['wall_seconds']=time.monotonic()-started
        (OUT/f'attempt-{i}.json').write_text(json.dumps(record,indent=2)+'\n')
        print(json.dumps({k:v for k,v in record.items() if k not in {'request_json','response_json'}}),flush=True)
        if not record['complete']:break
if __name__=='__main__':main()
