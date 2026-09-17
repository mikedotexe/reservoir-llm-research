#!/usr/bin/env python3
"""One preregistered active-state example, retaining every outcome. No retries or model startup."""
import argparse, datetime, hashlib, json, pathlib, subprocess, urllib.parse, urllib.request
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--cli',type=pathlib.Path,required=True)
p.add_argument('--fixture',type=pathlib.Path,required=True)
p.add_argument('--output',type=pathlib.Path,required=True)
p.add_argument('--endpoint',required=True)
p.add_argument('--model',default='phi3:mini')
p.add_argument('--expected-digest',default='4f222292793889a9a40a020799cfd28d53f3e01af25d48e06c5e708610fc47e9')
a=p.parse_args()
u=urllib.parse.urlsplit(a.endpoint)
if u.scheme!='http' or u.hostname not in ['127.0.0.1','localhost','::1'] or not u.port or u.path not in ['', '/'] or u.query or u.fragment or u.username:
    p.error('An explicit HTTP loopback endpoint with a port is required.')
subprocess.run([str(a.cli),'verify',str(a.fixture)],check=True)
f=json.loads(a.fixture.read_text())
assert f['specification']['forcingProfile']=='continuousSensoryV1'
assert f['specification']['comparisonKind']=='observation'
magnitudes=[max(map(abs,f['right']['frames'][step-1]['state'])) for step in [30,60,90]]
assert all(x>=.25 for x in magnitudes), 'Active-state qualification failed; do not change parameters automatically.'
a.output.mkdir(parents=True,exist_ok=False)
now=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
spec=dict(f['specification'])
spec.update(promptVersion=2,
    language=dict(backend='ollama',endpoint=a.endpoint,model=a.model,contextTokens=4096,responseFormat='json'),
    question='What writing occurs when current indexed reservoir coordinates are supplied during active input?',
    expectedDifference='The added-state arm can cite current signed coordinates. No writing improvement is predicted.',
    alternativeExplanation='Extra prompt content, model variability and order may change prose; sensory measurements already provide system information.',
    stoppingPoint='One 120-step run, opportunities30/60/90, at most six requests. Alternate left/right order. Preserve both outcomes at a failed opportunity, then stop. No retries.')
recipe=a.output/'active-observation.recipe.json'
recipe.write_text(json.dumps(spec,indent=2)+'\n')
manifest=dict(schema='reservoir-scope.guided-observation-recording.v1',registered_at_utc=now(),
    status='registered',model_name=a.model,expected_model_digest=a.expected_digest,
    cli_sha256=hashlib.sha256(a.cli.read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256(a.fixture.read_bytes()).hexdigest(),
    specification=spec,prompt_version=2,temperature=0,output_tokens=256,context_tokens=4096,response_format='json',word_instruction=40,
    qualification=dict(steps=[30,60,90],minimum_maximum_absolute_state=.25,observed_maximum_absolute_state=magnitudes),
    scope='S-009 synthetic teaching fixture selected by numerical qualification, separate from live Being studies. Different prose is not improved fidelity.',
    request_order=['left,right','right,left','left,right'],maximum_model_requests=6,attempts=[])
path=a.output/'guided-observation-recording.json'
def save(): path.write_text(json.dumps(manifest,indent=2)+'\n')
save()
try:
    with urllib.request.urlopen(a.endpoint.rstrip('/')+'/api/tags',timeout=5) as response: inventory=json.load(response)
    (a.output/'model-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    model=next((m for m in inventory['models'] if m['name']==a.model),None)
    if model is None or model.get('digest')!=a.expected_digest: raise ValueError('Installed model does not match the frozen identity.')
except Exception as error:
    manifest.update(status='unavailable',error=str(error),finished_at_utc=now()); save()
    print(json.dumps(dict(status=manifest['status'],error=manifest['error']))); raise SystemExit(0)
manifest.update(status='recording',model=model); save()
output=a.output/'example-model-observation-active.json'
started=now()
with (a.output/'active-observation.log').open('w') as log:
    result=subprocess.run([str(a.cli),'actions','--config',str(recipe),'--output',str(output)],stdout=log,stderr=subprocess.STDOUT)
attempt=dict(started_at_utc=started,finished_at_utc=now(),exit_code=result.returncode,record=output.name)
if output.exists():
    verification=subprocess.run([str(a.cli),'verify',str(output)],capture_output=True,text=True)
    r=json.loads(output.read_text())
    attempt.update(verified=verification.returncode==0,verification=verification.stdout+verification.stderr,
        sha256=hashlib.sha256(output.read_bytes()).hexdigest(),status=r['status'],steps=len(r['right']['frames']),
        journal_counts={arm:len(r[arm]['journals']) for arm in ['left','right'] if r.get(arm)},
        request_count=sum(x.get('requestStarted',False) for arm in ['left','right'] if r.get(arm) for x in r[arm]['actions']))
    assert attempt['request_count']<=6
manifest.update(status=attempt.get('status','failed'),finished_at_utc=now(),attempts=[attempt]);save()
print(json.dumps(attempt))
if not attempt.get('verified',False): raise SystemExit(1)
