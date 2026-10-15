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


def require_qualification(doc):
    assert doc.get('passed') is True or doc.get('status')=='passed'
    assert doc['sourceUnchanged'] is True and doc['sourceBefore']==doc['sourceAfter']
    for ref in doc['sourceAfter']:checked(ref)


def main():
    assert not os.path.lexists(HERE / 'evaluation-freeze-01.json')
    assert not os.path.lexists(HERE / 'host-admission-01.json')
    required_documents(HERE)
    plan = json.loads((HERE / 'run-plan.json').read_text())
    assert plan['schema'] == 'reservoir-context-sources-plan-v1' and plan['episodeId'] == 'context-sources-01'
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
    prepared=json.loads((HERE/'preparation-checks-01.json').read_text())
    require_qualification(prepared)
    generation=json.loads((HERE/'input-generation-01.json').read_text())
    require_qualification(generation)
    for ref in generation['outputs']:checked(ref)
    transformed=json.loads((HERE/'transformation-checks-01.json').read_text())
    assert transformed['status']=='passed' and transformed['originalUnchanged'] is True
    assert transformed['originalInventoryBefore']==transformed['originalInventoryAfter']
    assert transformed['productionVerifierExecuted'] is False and transformed['numericalValuesRecomputed'] is False
    source_refs=transformed['sourceIdentities']
    source_refs += [dict(path=str(Path(transformed['originalBundle'])/name),**ref) for name,ref in transformed['originalInventoryAfter'].items()]
    for ref in source_refs:checked(ref)
    inputs=json.loads((HERE/'frozen-inputs.json').read_text())
    assert inputs['schema']=='reservoir-context-sources-inputs-v1' and inputs['episodeId']==plan['episodeId']
    assert inputs['runPlan']==identity(HERE/'run-plan.json')
    assert inputs['provenance']['transformation']==identity(HERE/'transformation-checks-01.json')
    assert inputs['slots']==transformed['prompts'] and len(inputs['slots'])==12
    expected=[(step,c) for i,step in enumerate((30,60,90,120,330,360)) for c in ('AB' if i%2==0 else 'BA')]
    cases={case['anchorStep']:case for case in transformed['cases']}
    for number,(slot,(step,condition)) in enumerate(zip(inputs['slots'],expected),1):
        assert slot['slot']==number and slot['anchorStep']==step and slot['condition']==condition
        assert checked(slot['prompt']).is_relative_to(HERE/'prompts')
        assert slot['prompt']['sha256']==cases[step]['originalPromptSha256' if condition=='A' else 'candidatePromptSha256']
    assert (HERE/'audit_source_context.py').is_file()  # Bound now; execute only after fixed masked notes.
    paths = [p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [Path(r['path']) for r in refs + prior_freeze['files']]
    paths += [prior_freeze_path]+[Path(r['path']) for r in source_refs]
    files = [identity(p) for p in sorted(set(paths))]
    assert files == [identity(r['path']) for r in files]
    value = dict(schema='reservoir-context-sources-freeze-v1', status='prospective-before-admission',
                 frozenAtUtc=dt.datetime.now(dt.timezone.utc).isoformat(), episodeId=plan['episodeId'],
                 sourceCommit=prior_freeze['sourceCommit'], sourceCommitBasis='Retained prior qualified freeze; all referenced source bytes rechecked',
                 productBuiltOrChanged=False, modelCalls=0, files=files,
                 qualification=dict(reuse=identity(HERE / 'runtime-copy-01.json'), runtime=identity(checks_path),
                                    inheritedFreeze=identity(prior_freeze_path)),
                 scope='Source-label insertion diagnostic, exact original readout and prior prose, qualified unchanged transport/supervisor behavior, all prior time-direction/context evidence. No new production replay or runtime execution.')
    with (HERE / 'evaluation-freeze-01.json').open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(files=len(files), freeze=identity(HERE / 'evaluation-freeze-01.json'))))


if __name__ == '__main__':
    main()
