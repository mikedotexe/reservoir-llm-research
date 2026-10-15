#!/usr/bin/env python3
"""Exclusive file-only preparation of the explicitly relaxed admission window."""
import datetime as dt
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / '2026-10-15-context-sources-02'
SOFTWARE = HERE.parent / '2026-10-15-runtime-0.40.5/software-selection.json'
EXACT = ('owned_model.py', 'test_owned_model.py', 'render_blind_pack.py',
         'test_render_blind_pack.py', 'test_prepare_inputs.py', 'audit_source_context.py',
         'READING-PROTOCOL.md')
ADAPTED = ('run_probe.py', 'test_run_probe.py', 'prepare_inputs.py', 'retain_and_analyze.py')
REPLACEMENTS = (('context-sources-02', 'context-sources-03'),
                ('context-sources-gemma3-4b-run02', 'context-sources-gemma3-4b-run03'),
                ('context-sources-results02', 'context-sources-results03'))


def identity(path):
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def write(name, raw):
    with (HERE / name).open('xb') as stream:
        stream.write(raw)


def write_json(name, value):
    write(name, (json.dumps(value, indent=2) + '\n').encode())


def adapted(name, count):
    text = (OLD / name).read_text()
    for previous, current in REPLACEMENTS:
        text = text.replace(previous, current)
    if name == 'retain_and_analyze.py':
        assert text.count('len(prior)==438') == 1
        text = text.replace('len(prior)==438', f'len(prior)=={count}')
    return text.encode()


def main():
    previous = json.loads((OLD / 'runtime-copy-01.json').read_text())
    old_paths = [p for p in OLD.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths = sorted(set(old_paths + [Path(r['path']) for r in previous['priorDirectoryAfter']]))
    before = [identity(p) for p in paths]
    for name in EXACT:
        write(name, (OLD / name).read_bytes())
    for name in ADAPTED:
        write(name, adapted(name, len(before)))
    write_json('cleanup-result-01.json', dict(
        status='no_cleanup_requested_or_performed', atUtc=dt.datetime.now(dt.timezone.utc).isoformat(),
        scope='The user authorized a lower prospective memory threshold. No app closure, cache purge, model unload, Being or shared-service action was performed.'))
    plan = json.loads((OLD / 'run-plan.json').read_text())
    plan['episodeId'] = 'context-sources-03'
    plan['ownedServiceDirectory'] = str(HERE.parents[1] / 'target/qa/0.20-context-sources-gemma3-4b-run03')
    p = plan['provenance']
    p['authorization'] = 'October 15: the user explicitly authorized relaxing the conservative 35% memory guard on the dedicated Mac and one fresh comparison window. Parent selected a provisional 30% reported-free floor; all other request/runtime/resource limits are unchanged. Admission and launch wait for explicit parent release after product checks.'
    p['resultsDirectory'] = str(HERE.parents[1] / 'target/qa/0.20-context-sources-results03')
    p['hostAdmission']['minimumFreePercent'] = 30
    p['admissionPolicyId'] = 'normal-pressure-reported-free-30-v1'
    p['admissionRationale'] = '35% was an inherited operational margin, not a measured model minimum. On this 64-GiB M4 Pro host, use 30% reported free provisionally with normal pressure level 1 and 8 GiB free disk. The percentage is not literal unused RAM or a guaranteed allocatable budget; neither a single admission nor source/synthetic runtime qualification proves continued capacity or successful execution. Historical refusals remain valid under their frozen 35% rule.'
    p['preAdmissionCleanupReceipt'] = identity(HERE / 'cleanup-result-01.json')
    p['priorAttempt'] = identity(OLD / 'outcome-01.json')
    p['priorAttempts'] = [identity(HERE.parent / f'2026-10-15-context-sources-{i:02}' / 'outcome-01.json') for i in (1, 2)]
    p['priorFrozenInputs'] = identity(OLD / 'frozen-inputs.json')
    p['runtimeInterpretation'] = 'Same explicit 0.40.5 software selection as refused window02. Source/synthetic preflight remains conditional; no actual owned startup/inventory/generation has been qualified by windows01/02. This distinct window is limited to its frozen bounds.'
    write_json('run-plan.json', plan)
    after = [identity(p) for p in paths]
    assert before == after
    write_json('runtime-copy-01.json', dict(
        schema='reservoir-context-sources-runtime-copy-v1', atUtc=dt.datetime.now(dt.timezone.utc).isoformat(),
        priorEpisodes=previous['priorEpisodes'] + [str(OLD)], priorDirectoryBefore=before,
        priorDirectoryAfter=after, priorFilesUnchanged=True, sourceEpisodeFileCount=len(old_paths),
        inheritedPriorFileCount=len(previous['priorDirectoryAfter']),
        sources=[identity(OLD / n) for n in EXACT + ADAPTED],
        copies=[identity(HERE / n) for n in EXACT + ADAPTED], exactCopies=list(EXACT),
        changedScope='Copied runner/analysis code: episode and owned paths plus retained prior-file count only. Separate admission implementation changes only the provisional free-percentage floor and explicitly validates/binds its frozen policy. Prompt, model, transport and supervisor limits unchanged.',
        substitutions=list(REPLACEMENTS), priorQualification=previous['priorQualification'] + [
            identity(OLD / 'runtime-checks-01.json'), identity(OLD / 'preparation-checks-01.json')],
        priorInputs=identity(OLD / 'frozen-inputs.json'), priorFreeze=identity(OLD / 'evaluation-freeze-01.json'),
        softwareSelection=identity(SOFTWARE), noRuntimeCalls=True))
    print(json.dumps(dict(priorFiles=len(before), plan=identity(HERE / 'run-plan.json'))))


if __name__ == '__main__':
    main()
