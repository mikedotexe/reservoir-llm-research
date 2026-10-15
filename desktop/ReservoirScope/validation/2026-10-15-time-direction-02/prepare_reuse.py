#!/usr/bin/env python3
"""Copy the refused window's exact inputs; no regeneration or runtime actions."""
import datetime as dt
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / '2026-10-15-time-direction-01'


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
    prior = json.loads((OLD / 'runtime-copy-01.json').read_text())
    old_paths = [p for p in OLD.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths = sorted(set(old_paths + [Path(r['path']) for r in prior['priorDirectoryAfter']]))
    before = [identity(p) for p in paths]
    exact = ['owned_model.py', 'test_owned_model.py', 'render_blind_pack.py',
             'test_render_blind_pack.py', 'READING-PROTOCOL.md']
    changed = ['run_probe.py', 'test_run_probe.py', 'admit_once.py']
    for name in exact:
        write(name, (OLD / name).read_bytes())
    for name in changed:
        text = (OLD / name).read_text()
        if name == 'admit_once.py':
            assert text.count('"time-direction-01"') == 1
            text = text.replace('"time-direction-01"', '"time-direction-02"')
        else:
            assert text.count('0.20-time-direction-gemma3-4b-run01') == (2 if name == 'run_probe.py' else 1)
            text = text.replace('0.20-time-direction-gemma3-4b-run01', '0.20-time-direction-gemma3-4b-run02')
        write(name, text.encode())
    plan = json.loads((OLD / 'run-plan.json').read_text())
    plan['episodeId'] = 'time-direction-02'
    plan['ownedServiceDirectory'] = plan['ownedServiceDirectory'].replace('gemma3-4b-run01', 'gemma3-4b-run02')
    plan['provenance']['resultsDirectory'] = plan['provenance']['resultsDirectory'].replace('results01', 'results02')
    plan['provenance']['authorization'] = ('Fresh explicit user authorization after the refused first window, including root-owned safe memory cleanup and one new admission. Same inputs and bounds; no automatic retry or threshold relaxation.')
    plan['provenance']['otherApplicationsOrBeingsTouched'] = False
    plan['provenance']['cleanupScope'] = ('The probe and supervisor do not clean up other applications or Beings. Any separately authorized pre-admission app closure is recorded by root in cleanup-result-01.json.')
    plan['provenance']['priorRefusal'] = identity(OLD / 'outcome-01.json')
    plan['provenance']['priorRefusals'].append(identity(OLD / 'outcome-01.json'))
    plan['provenance']['priorTimeDirectionFreeze'] = identity(OLD / 'evaluation-freeze-01.json')
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
    inputs['provenance']['promptsRegenerated'] = False
    write_json('frozen-inputs.json', inputs)
    after = [identity(p) for p in paths]
    assert before == after
    qualification = prior['priorQualification'] + [identity(OLD / n) for n in
        ['runtime-checks-02.json', 'preparation-checks-01.json', 'transformation-checks-01.json', 'input-generation-01.json']]
    write_json('runtime-copy-01.json', dict(
        schema='reservoir-time-direction-reuse-copy-v1', atUtc=dt.datetime.now(dt.timezone.utc).isoformat(),
        priorEpisodes=prior['priorEpisodes'] + [str(OLD)], priorDirectoryBefore=before,
        priorDirectoryAfter=after, priorFilesUnchanged=True,
        sourceEpisodeFileCount=len(old_paths), inheritedPriorFileCount=len(prior['priorDirectoryAfter']),
        sources=[identity(OLD / n) for n in exact + changed],
        copies=[identity(HERE / n) for n in exact + changed],
        exactCopies=exact, changedScope={'run_probe.py': 'Two owned service basename run01 to run02 literals only',
            'test_run_probe.py': 'One synthetic owned service basename only', 'admit_once.py': 'Recorded episodeId only'},
        priorQualification=qualification, priorInputs=identity(OLD / 'frozen-inputs.json'),
        priorRefusal=identity(OLD / 'outcome-01.json'), priorFreeze=identity(OLD / 'evaluation-freeze-01.json'),
        promptCopies=[s['prompt'] for s in inputs['slots']], promptsRegenerated=False, noRuntimeCalls=True))
    print(json.dumps({'priorFiles': len(before), 'sourceEpisodeFiles': len(old_paths),
                      'inputs': identity(HERE / 'frozen-inputs.json'), 'copyReceipt': identity(HERE / 'runtime-copy-01.json')}))


if __name__ == '__main__':
    main()
