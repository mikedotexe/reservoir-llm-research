#!/usr/bin/env python3
"""Read the selected completed QA episode; no provider, restoration or writes to it.

The exact packaged verifier owns numerical/prompt replay. This companion makes
the request count, full-text memory chain and file preservation reviewable.
"""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import subprocess

V = Path(__file__).resolve().parent
D = V.parents[1]


def identity(path):
    raw = path.read_bytes()
    return dict(path=str(path.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def inventory(root):
    return [dict(relativePath=str(p.relative_to(root)), **identity(p))
            for p in sorted(root.rglob('*')) if p.is_file()]


def main():
    plan = json.loads((V / 'run-plan.json').read_bytes())
    launch = json.loads((V / 'ui-launch-01.json').read_bytes())
    s = Path(plan['appRunDirectory']) / 'library/sustained-v1/sustained-1792190416197-1'
    assert subprocess.run(['/bin/ps', '-p', str(launch['pid']), '-o', 'pid='],
                          capture_output=True).returncode != 0, 'Quit owned GUI first'
    before = inventory(s)
    manifest = json.loads((s / 'manifest.json').read_bytes())
    assert manifest['step'] == manifest['durableStep'] == 121
    assert manifest['journalCount'] == 4
    assert manifest['phase'] == 'budgetReached'
    for key in ('seed', 'turnEvery', 'maximumSteps', 'maximumTurns',
                'maximumDurationSeconds', 'storageBudgetBytes', 'paceMs',
                'promptVersion', 'outputTokens', 'requestDeadlineSeconds'):
        assert manifest['config'][key] == plan['session'][key], key
    assert manifest['config']['language']['model'] == plan['model']
    assert manifest['config']['language']['contextTokens'] == plan['session']['contextTokens']
    journals = sorted((json.loads(p.read_bytes()) for p in (s / 'journals').glob('*.json')),
                      key=lambda j: j['pending']['entry']['observedStep'])
    events = [e for p in sorted((s / 'segments').glob('*.json'))
              for e in json.loads(p.read_bytes())['segment']['events']]
    counts = dict(collections.Counter(e['kind']['type'] for e in events))
    assert counts['languageStarted'] == counts['languageReceived'] == counts['journalSaved'] == 4
    applications = [e['kind']['data']['application'] for e in events
                    if e['kind']['type'] == 'advanced' and e['kind']['data'].get('application')]
    assert [a['appliedStep'] for a in applications] == [31, 61, 91, 121]
    rows = []
    previous = None
    for index, journal in enumerate(journals):
        p = journal['pending']; entry = p['entry']; response = p['response']
        assert entry['observedStep'] == 30 * (index + 1)
        assert response['complete'] is True and response['stopReason'] == 'stop'
        assert response['providerModel'] == 'gemma3:4b' and journal['requestStarted'] is True
        assert entry['text'] == response['text']
        assert hashlib.sha256(entry['text'].encode()).hexdigest() == entry['sha256']
        memory_exact = (p['memory'] is None if previous is None
                        else p['memory']['entry'] == previous)
        assert memory_exact
        if previous:
            marker = '\nFull previous text as one JSON string: '
            encoded = p['prompt'].split(marker, 1)[1]
            decoded, consumed = json.JSONDecoder().raw_decode(encoded)
            assert decoded == previous['text']
            assert encoded[consumed:].startswith('\nEND PREVIOUS JOURNAL\n')
        assert p['prompt'].startswith('Reservoir Scope · ongoing journal · reservoir-journal-v8\n')
        assert journal['timing']['transportDurationMs'] <= 180000
        rows.append(dict(step=entry['observedStep'], journalId=entry['id'], textSha256=entry['sha256'],
                         textBytes=len(entry['text'].encode()), tokenCount=response['tokenCount'],
                         complete=response['complete'], stopReason=response['stopReason'],
                         exactPriorJournalMemory=memory_exact, timing=journal['timing']))
        previous = entry
    exe = Path(launch['executable'])
    assert identity(exe)['sha256'] == launch['executableSha256']
    result = subprocess.run([str(exe), '--verify-sustained', str(s)], capture_output=True,
                            text=True, timeout=60)
    with (V / 'offline-replay-01.json').open('x') as f:
        json.dump(dict(command=[str(exe), '--verify-sustained', str(s)], exit=result.returncode,
                       stdout=result.stdout, stderr=result.stderr), f, indent=2); f.write('\n')
    assert result.returncode == 0 and json.loads(result.stdout)['status'] == 'passed'
    after = inventory(s)
    assert before == after, 'Read-only replay changed saved files'
    frozen = json.loads((V / 'evaluation-freeze-01.json').read_bytes())
    for expected in frozen['files']:
        assert identity(Path(expected['path'])) == expected, expected['path']
    report = dict(recordedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  source=identity(Path(__file__)), sessionPath=str(s), manifest=manifest,
                  events=counts, applications=applications, journals=rows,
                  filesBefore=before, filesAfter=after, unchangedFiles=len(before),
                  totalRetainedBytes=sum(f['bytes'] for f in after), frozenFilesUnchanged=len(frozen['files']),
                  numericalReplayPassed=True, modelsContactedByAudit=False)
    with (V / 'episode-audit-01.json').open('x') as f: json.dump(report, f, indent=2); f.write('\n')
    print(json.dumps({k: report[k] for k in ('events', 'applications', 'unchangedFiles',
                                           'totalRetainedBytes', 'frozenFilesUnchanged', 'numericalReplayPassed')}))


if __name__ == '__main__':
    main()
