#!/usr/bin/env python3
"""Fixed episode02 file-continuity check; no imports from runnable helpers."""
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / '2026-10-14-context-order-01'


def identity(path):
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def load(path):
    return json.loads(path.read_bytes())


def main():
    started = datetime.now(timezone.utc).isoformat()
    manifest = load(HERE / 'copy-manifest-01.json')
    assert manifest['priorDirectoryBefore'] == manifest['priorDirectoryAfter']
    assert manifest['priorDirectoryUnchanged'] is True
    prior_paths = sorted(p for p in OLD.rglob('*') if p.is_file())
    prior_before = [identity(p) for p in prior_paths]
    assert prior_before == manifest['priorDirectoryBefore']
    for ref in manifest['priorBindings']:
        assert identity(Path(ref['path'])) == ref
    for pair in manifest['copies']:
        assert identity(Path(pair['source']['path'])) == pair['source']
        assert identity(Path(pair['copy']['path'])) == pair['copy']
        if pair['mode'] == 'byteExact':
            assert Path(pair['source']['path']).read_bytes() == Path(pair['copy']['path']).read_bytes()
    changes = [('run_probe.py', b'0.20-context-order-gemma3-4b-run01', b'0.20-context-order-gemma3-4b-run02', 2),
               ('test_run_probe.py', b'0.20-context-order-gemma3-4b-run01', b'0.20-context-order-gemma3-4b-run02', 1),
               ('admit_once.py', b'"context-order-01"', b'"context-order-02"', 1)]
    for name, old, new, count in changes:
        raw = (OLD / name).read_bytes()
        assert raw.count(old) == count and raw.replace(old, new) == (HERE / name).read_bytes()
    old_plan, new_plan = load(OLD / 'run-plan.json'), load(HERE / 'run-plan.json')
    expected = copy.deepcopy(old_plan)
    expected['episodeId'] = 'context-order-02'
    expected['ownedServiceDirectory'] = old_plan['ownedServiceDirectory'].removesuffix('run01') + 'run02'
    expected['provenance'].update(priorRefusal=identity(OLD / 'outcome-01.json'),
        authorization='A fresh user-authorized window after the closed01 admission refusal; no automatic retry or threshold relaxation.',
        resultsDirectory=str(HERE.parents[1] / 'target/qa/0.20-context-order-results02'))
    assert new_plan == expected
    old_inputs, new_inputs = load(OLD / 'frozen-inputs.json'), load(HERE / 'frozen-inputs.json')
    expected = copy.deepcopy(old_inputs)
    expected['episodeId'] = 'context-order-02'
    expected['runPlan'] = identity(HERE / 'run-plan.json')
    expected['provenance'].update(reusedInputs=identity(OLD / 'frozen-inputs.json'),
                                  priorRefusal=identity(OLD / 'outcome-01.json'))
    for slot in expected['slots']:
        path = HERE / 'prompts' / Path(slot['prompt']['path']).name
        old_path = Path(slot['prompt']['path'])
        assert path.read_bytes() == old_path.read_bytes()
        slot['prompt'] = identity(path)
    assert expected == new_inputs and len(expected['slots']) == 12
    prompt_paths = sorted((HERE / 'prompts').glob('*.txt'))
    assert len(prompt_paths) == 12
    source_review = load(OLD / 'independent-inputs-review-01.json')
    assert source_review['status'] == 'passed' and source_review['inputsUnchanged'] is True
    for key in ['sourceReceipt', 'sourceMaterial']:
        assert identity(Path(new_inputs['provenance'][key]['path'])) == new_inputs['provenance'][key]
    tests = load(HERE / 'preparation-checks-01.json')
    assert tests['passed'] is True and tests['exitCode'] == 0 and tests['testCount'] == 12
    assert tests['sourceUnchanged'] is True and tests['sourceBefore'] == tests['sourceAfter']
    assert tests['sourceAfter'] == [identity(Path(r['path'])) for r in tests['sourceAfter']]
    assert identity(Path(tests['log']['path'])) == tests['log']
    names = ['PROTOCOL.md', 'READING-PROTOCOL.md', 'run-plan.json', 'frozen-inputs.json',
             'run_probe.py', 'test_run_probe.py', 'admit_once.py', 'owned_model.py',
             'test_owned_model.py', 'render_blind_pack.py', 'test_render_blind_pack.py',
             'copy-manifest-01.json', 'preparation-attempt-01.json', 'preparation-checks-01.json',
             'test_episode_reuse.py', 'freeze_inputs.py']
    reviewed = [identity(HERE / n) for n in names] + [identity(p) for p in prompt_paths]
    prior_after = [identity(p) for p in prior_paths]
    assert prior_before == prior_after
    assert reviewed == [identity(Path(r['path'])) for r in reviewed]
    result = dict(schema='reservoir-context-order-reuse-review-v1', status='passed',
                  startedAtUtc=started, endedAtUtc=datetime.now(timezone.utc).isoformat(),
                  script=identity(Path(__file__)), priorBefore=prior_before, priorAfter=prior_after,
                  priorUnchanged=True, reviewedFiles=reviewed, promptCopiesExact=12,
                  boundsUnchanged=True, runnerChangedBasenameOccurrences=2,
                  testChangedBasenameOccurrences=1, admissionChangedEpisodeIds=1,
                  priorSourceReview=identity(OLD / 'independent-inputs-review-01.json'),
                  scope='File bytes and declared configuration only. No tests, host probes, runtime, network or model calls.')
    with (HERE / 'independent-reuse-review-01.json').open('x') as out:
        json.dump(result, out, indent=2)
        out.write('\n')
    print(json.dumps(dict(status='passed', priorFiles=len(prior_before), prompts=12,
                         receipt=identity(HERE / 'independent-reuse-review-01.json'))))


if __name__ == '__main__':
    main()
