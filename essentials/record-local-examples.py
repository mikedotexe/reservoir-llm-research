#!/usr/bin/env python3
"""Record one finite batch against an explicitly selected, already-running local model.

No pulls, service startup, automatic retries, or text substitutions. Every attempt
is retained, including failed runs. The output directory must be new.
"""
import argparse, datetime, hashlib, json, pathlib, subprocess, urllib.parse, urllib.request

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--cli', type=pathlib.Path, required=True)
p.add_argument('--output', type=pathlib.Path, required=True)
p.add_argument('--endpoint', required=True)
p.add_argument('--model', required=True)
p.add_argument('--expected-digest', required=True)
a = p.parse_args()
u = urllib.parse.urlsplit(a.endpoint)
if u.scheme != 'http' or u.hostname not in ['127.0.0.1', 'localhost', '::1'] or not u.port or u.path not in ['', '/'] or u.query or u.fragment or u.username:
    p.error('Choose an explicit HTTP loopback endpoint with a port.')
with urllib.request.urlopen(a.endpoint.rstrip('/') + '/api/tags', timeout=5) as response:
    inventory = json.load(response)
model = next((m for m in inventory['models'] if m['name'] == a.model), None)
if model is None or model['digest'] != a.expected_digest:
    p.error('Installed model does not match the frozen model identity.')
a.output.mkdir(parents=True, exist_ok=False)
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
manifest = {'schema': 'reservoir-scope.local-recording-batch.v1', 'registered_at_utc': now(),
    'model': model, 'cli_sha256': hashlib.sha256(a.cli.read_bytes()).hexdigest(),
    'output_tokens': 256, 'temperature': 0, 'context_tokens': 4096, 'response_format': 'json',
    'prompt_version': 2, 'steps': 120, 'opportunities': [30, 60, 90], 'seed': 20260909,
    'scope': 'S-009 isolated synthetic preparation; different prose is not an improvement score.',
    'stopping_rule': 'One run per named recipe; preserve each failed opportunity and stop that run. No automatic retry.',
    'attempts': []}
path = a.output/'model-recordings.json'
path.write_text(json.dumps(manifest, indent=2)+'\n')
for key in ['4', '5', '6', '7', '8', 'observation']:
    observation = key == 'observation'
    spec = dict(stage=4 if observation else int(key), comparisonKind='observation' if observation else 'components',
        promptVersion=2, mode='independentGeneration', comparePrevious=observation, steps=120, turnEvery=30, seed=20260909,
        language=dict(backend='ollama', endpoint=a.endpoint, model=a.model, contextTokens=4096, responseFormat='json'),
        question='What changes in writing when the current indexed reservoir state is supplied?' if observation else 'What journal and subsequent mechanism outcomes occur in this component configuration?',
        expectedDifference='The added observation arm can refer to current signed reservoir coordinates.' if observation else 'Inspect the recorded writing and the enabled return, memory, choice, or regulation mechanism.',
        alternativeExplanation='Additional prompt content and model variability may change wording; differences do not establish improved accuracy.',
        stoppingPoint='120 steps; opportunities 30, 60, 90. Retain both arms of a failed opportunity, then stop. One run, no retries.')
    recipe = a.output/f'model-{key}.recipe.json'
    recipe.write_text(json.dumps(spec, indent=2)+'\n')
    output = a.output/f'example-model-{key}.json'
    started = now()
    with (a.output/f'model-{key}.log').open('w') as log:
        result = subprocess.run([str(a.cli.resolve()), 'actions', '--config', str(recipe), '--output', str(output)], stdout=log, stderr=subprocess.STDOUT)
    attempt = dict(recipe=recipe.name, record=output.name, started_at_utc=started, finished_at_utc=now(), exit_code=result.returncode)
    if output.exists():
        verify = subprocess.run([str(a.cli.resolve()), 'verify', str(output)], capture_output=True, text=True)
        attempt.update(verified=verify.returncode == 0, verification=verify.stdout+verify.stderr, sha256=hashlib.sha256(output.read_bytes()).hexdigest())
        record = json.loads(output.read_text())
        attempt.update(status=record['status'], steps=len(record['right']['frames']),
            journal_counts={k: len(record[k]['journals']) for k in ['left', 'right'] if record.get(k)},
            opportunity_counts={k: len(record[k]['actions']) for k in ['left', 'right'] if record.get(k)})
    manifest['attempts'].append(attempt)
    path.write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(attempt), flush=True)
