#!/usr/bin/env python3
"""Exclusive file-only reuse of window02. No regenerated prompts or runtime calls."""
import datetime as dt
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / '2026-10-15-time-direction-02'


def identity(path):
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def write(name, raw):
    with (HERE / name).open('xb') as stream:
        stream.write(raw)


def write_json(name, value):
    write(name, (json.dumps(value, indent=2) + '\n').encode())


def main():
    cleanup = identity(HERE / 'cleanup-result-01.json')
    prior = json.loads((OLD / 'runtime-copy-01.json').read_text())
    old_paths = [p for p in OLD.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths = sorted(set(old_paths + [Path(r['path']) for r in prior['priorDirectoryAfter']]))
    before = [identity(p) for p in paths]
    exact = ['owned_model.py', 'test_owned_model.py', 'render_blind_pack.py', 'test_render_blind_pack.py', 'READING-PROTOCOL.md']
    changed = ['run_probe.py', 'test_run_probe.py', 'admit_once.py']
    for name in exact:
        write(name, (OLD / name).read_bytes())
    for name in changed:
        text = (OLD / name).read_text()
        if name == 'admit_once.py':
            assert text.count('"time-direction-02"') == 1
            text = text.replace('"time-direction-02"', '"time-direction-03"')
        else:
            assert text.count('0.20-time-direction-gemma3-4b-run02') == (2 if name == 'run_probe.py' else 1)
            text = text.replace('0.20-time-direction-gemma3-4b-run02', '0.20-time-direction-gemma3-4b-run03')
        write(name, text.encode())
    plan = json.loads((OLD / 'run-plan.json').read_text())
    plan['episodeId'] = 'time-direction-03'
    plan['ownedServiceDirectory'] = plan['ownedServiceDirectory'].replace('gemma3-4b-run02', 'gemma3-4b-run03')
    plan['provenance']['resultsDirectory'] = plan['provenance']['resultsDirectory'].replace('results02', 'results03')
    plan['provenance']['authorization'] = ('Fresh explicit user authorization for one new serial time/distance comparison. Same twelve inputs/order/bounds; no restart between slots, automatic retry or threshold reduction. Root records no application changes in this window.')
    plan['provenance']['priorRefusal'] = identity(OLD / 'outcome-01.json')
    plan['provenance']['priorRefusals'].append(identity(OLD / 'outcome-01.json'))
    plan['provenance']['priorTimeDirectionFreeze'] = identity(OLD / 'evaluation-freeze-01.json')
    plan['provenance']['preAdmissionCleanupReceipt'] = cleanup
    write_json('run-plan.json', plan)
    inputs = json.loads((OLD / 'frozen-inputs.json').read_text())
    inputs['episodeId'] = plan['episodeId']
    inputs['runPlan'] = identity(HERE / 'run-plan.json')
    (HERE / 'prompts').mkdir()
    for slot in inputs['slots']:
        source = Path(slot['prompt']['path'])
        assert identity(source) == slot['prompt']
        destination = HERE / 'prompts' / source.name
        with destination.open('xb') as stream:
            stream.write(source.read_bytes())
        slot['prompt'] = identity(destination)
    inputs['provenance']['reusedInputs'] = identity(OLD / 'frozen-inputs.json')
    inputs['provenance']['priorRefusal'] = identity(OLD / 'outcome-01.json')
    write_json('frozen-inputs.json', inputs)
    after = [identity(p) for p in paths]
    assert before == after
    qualifications = prior['priorQualification'] + [identity(OLD / 'runtime-checks-01.json')]
    write_json('runtime-copy-01.json', dict(
        schema='reservoir-time-direction-reuse-copy-v1', atUtc=dt.datetime.now(dt.timezone.utc).isoformat(),
        priorEpisodes=prior['priorEpisodes'] + [str(OLD)], priorDirectoryBefore=before,
        priorDirectoryAfter=after, priorFilesUnchanged=True,
        sourceEpisodeFileCount=len(old_paths), inheritedPriorFileCount=len(prior['priorDirectoryAfter']),
        sources=[identity(OLD / n) for n in exact + changed], copies=[identity(HERE / n) for n in exact + changed],
        exactCopies=exact, changedScope={'run_probe.py': 'Two owned service basename run02 to run03 literals only',
            'test_run_probe.py': 'One synthetic owned service basename only', 'admit_once.py': 'Recorded episodeId only'},
        priorQualification=qualifications, priorInputs=identity(OLD / 'frozen-inputs.json'),
        priorRefusal=identity(OLD / 'outcome-01.json'), priorFreeze=identity(OLD / 'evaluation-freeze-01.json'),
        promptCopies=[s['prompt'] for s in inputs['slots']], promptsRegenerated=False, noRuntimeCalls=True))
    print(json.dumps(dict(priorFiles=len(before), sourceEpisodeFiles=len(old_paths), inputs=identity(HERE / 'frozen-inputs.json'))))


if __name__ == '__main__':
    main()
