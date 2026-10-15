#!/usr/bin/env python3
"""Root-only prospective file freeze; no admission, provider or host queries."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent


def identity(path):
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def checked(ref):
    actual = identity(ref['path'])
    assert actual == ref, f'Identity changed: {ref["path"]}'
    return Path(actual['path'])


def required_documents(root):
    # A cleanup receipt may honestly record that no safe closure was available.
    cleanup = json.loads((root / 'cleanup-result-01.json').read_text())
    assert isinstance(cleanup, dict) and cleanup, 'Root cleanup result required'
    review = json.loads((root / 'pre-run-review-01.json').read_text())
    assert review['status'] in ('no_concrete_blocker_found', 'passed'), 'Independent review must pass'
    assert checked(review['review']) == (root / 'PRE-RUN-REVIEW.md').resolve()
    for ref in review['reviewedFiles']:
        checked(ref)
    assert (root / 'PROTOCOL.md').is_file() and (root / 'READING-PROTOCOL.md').is_file()
    return cleanup, review


def main():
    assert not os.path.lexists(HERE / 'evaluation-freeze-01.json')
    assert not os.path.lexists(HERE / 'host-admission-01.json')
    required_documents(HERE)
    plan = json.loads((HERE / 'run-plan.json').read_text())
    assert plan['schema'] == 'reservoir-time-direction-plan-v1' and plan['episodeId'] == 'time-direction-03'
    assert checked(plan['provenance']['preAdmissionCleanupReceipt']) == HERE / 'cleanup-result-01.json'
    assert not os.path.lexists(plan['ownedServiceDirectory'])
    assert not os.path.lexists(plan['provenance']['resultsDirectory'])
    reuse = json.loads((HERE / 'runtime-copy-01.json').read_text())
    assert reuse['priorDirectoryBefore'] == reuse['priorDirectoryAfter']
    refs = reuse['priorDirectoryAfter'] + reuse['priorQualification'] + reuse['sources'] + reuse['copies']
    for ref in refs:
        checked(ref)
    prior_freeze_path = checked(reuse['priorFreeze'])
    prior_freeze = json.loads(prior_freeze_path.read_text())
    for ref in prior_freeze['files']:
        checked(ref)
    checks_path = HERE / 'runtime-checks-01.json'
    checks = json.loads(checks_path.read_text())
    assert checks['passed'] and checks['sourceUnchanged'] and checks['sourceBefore'] == checks['sourceAfter']
    for ref in checks['sourceAfter']:
        checked(ref)
    # Prompt preparation/formatter qualification is inherited byte-for-byte, never rerun here.
    prior_inputs = json.loads(checked(reuse['priorInputs']).read_text())
    inputs = json.loads((HERE / 'frozen-inputs.json').read_text())
    assert inputs['schema'] == prior_inputs['schema'] and inputs['episodeId'] == plan['episodeId']
    assert inputs['runPlan'] == identity(HERE / 'run-plan.json')
    assert len(inputs['slots']) == len(prior_inputs['slots']) == 12
    for new, old in zip(inputs['slots'], prior_inputs['slots']):
        assert {k: v for k, v in new.items() if k != 'prompt'} == {k: v for k, v in old.items() if k != 'prompt'}
        assert checked(new['prompt']).is_relative_to(HERE / 'prompts')
        assert new['prompt']['sha256'] == old['prompt']['sha256'] and new['prompt']['bytes'] == old['prompt']['bytes']
    paths = [p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [Path(r['path']) for r in refs + prior_freeze['files']]
    paths += [prior_freeze_path]
    files = [identity(p) for p in sorted(set(paths))]
    assert files == [identity(r['path']) for r in files]
    value = dict(schema='reservoir-time-direction-freeze-v1', status='prospective-before-admission',
                 frozenAtUtc=dt.datetime.now(dt.timezone.utc).isoformat(), episodeId=plan['episodeId'],
                 sourceCommit=prior_freeze['sourceCommit'], sourceCommitBasis='Retained prior qualified freeze; all referenced source bytes rechecked',
                 productBuiltOrChanged=False, modelCalls=0, files=files,
                 qualification=dict(reuse=identity(HERE / 'runtime-copy-01.json'), runtime=identity(checks_path),
                                    inheritedFreeze=identity(prior_freeze_path)),
                 scope='Exact copied prompts, unchanged transport/supervision except owned paths, all prior time-direction01/02 evidence and its qualified source identities. Root cleanup/review required. No runtime execution.')
    with (HERE / 'evaluation-freeze-01.json').open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(files=len(files), freeze=identity(HERE / 'evaluation-freeze-01.json'))))


if __name__ == '__main__':
    main()
