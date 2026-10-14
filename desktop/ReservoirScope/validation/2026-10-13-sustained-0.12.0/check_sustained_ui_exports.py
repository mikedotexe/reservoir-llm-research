#!/usr/bin/env python3
"""Read-only actual-export qualification; only fresh scratch copies are mutated.
The supplied executable is copied before use. No sockets/providers are contacted.
"""
import argparse
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def digest(b):
    return hashlib.sha256(b).hexdigest()


def identity(path):
    path = Path(path)
    b = path.read_bytes()
    return {'path': str(path.resolve()), 'sizeBytes': len(b), 'sha256': digest(b)}


def inventory(root):
    return {str(p.relative_to(root)): {'sizeBytes': p.stat().st_size, 'sha256': digest(p.read_bytes())}
            for p in sorted(root.rglob('*')) if p.is_file()}


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_bytes(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode())


def links(root):
    return sorted((root / 'segments').glob('segment-*.json'))


def reanchor(root):
    previous = None
    for path in links(root):
        value = read(path)
        value['previousSha256'] = previous
        for entry in value['journalSha256s']:
            value['journalSha256s'][entry] = digest((root / 'journals' / f'{entry}.json').read_bytes())
        write(path, value)
        previous = digest(path.read_bytes())
    m = read(root / 'manifest.json')
    m['lastSegmentSha256'] = previous
    write(root / 'manifest.json', m)


def verify(executable, bundle):
    before = identity(executable)
    r = subprocess.run([str(executable), '--verify-sustained', str(bundle)], text=True,
                       capture_output=True, timeout=180)
    after = identity(executable)
    assert before == after, 'Pinned verifier changed during invocation'
    try:
        result = json.loads(r.stdout)
    except json.JSONDecodeError:
        result = {'unparsedStdout': r.stdout}
    return {'exitCode': r.returncode, 'result': result, 'stderr': r.stderr,
            'command': [str(executable), '--verify-sustained', str(bundle)]}


def request_evidence(root, entries):
    manifest = read(root / 'manifest.json')
    config = manifest['config']['language']
    post = [e for e in entries if e.get('method') == 'POST']
    responses = {e['response']: e for e in entries if 'response' in e}
    events = [e for p in links(root) for e in read(p)['segment']['events']]
    applications = {e['kind']['data']['application']['journalId']: e['kind']['data']['application']
                    for e in events if e['kind']['type'] == 'advanced' and e['kind']['data']['application']}
    frames = {e['step']: e['kind']['data'] for e in events if e['kind']['type'] == 'advanced'}
    journals = sorted((read(p) for p in (root / 'journals').glob('*.json')),
                      key=lambda j: j['pending']['entry']['attemptId'])
    matched = []
    for journal in journals:
        pending = journal['pending']
        entry, response, timing = pending['entry'], pending['response'], journal['timing']
        assert digest(entry['text'].encode()) == entry['sha256']
        assert response['text'] == entry['text'] and response['complete']
        assert journal['requestStarted'] is True and journal['configuredModel'] == config['model']
        assert response == {'text': entry['text'], 'providerModel': config['model'],
                            'stopReason': 'stop', 'tokenCount': 63, 'complete': True}
        candidates = [p for p in post if p['body']['messages'] == [{'role': 'user', 'content': pending['prompt']}]
                         and responses.get(p['request'], {}).get('textSha256') == entry['sha256']]
        assert len(candidates) == 1, f'Expected one exact fixture request for {entry["id"]}'
        request = candidates[0]
        expected_body = {'model': config['model'], 'stream': False,
                         'messages': [{'role': 'user', 'content': pending['prompt']}],
                         'options': {'temperature': 0, 'num_predict': 256, 'num_ctx': config['contextTokens']}}
        assert request['path'] == '/api/chat' and request['body'] == expected_body
        reconstructed = json.dumps(request['body'], ensure_ascii=False, separators=(',', ':')).encode()
        assert digest(reconstructed) == request['bodySha256']
        assert entry['observedStep'] == pending['observation']['step']
        assert pending['observation']['state'] == frames[entry['observedStep']]['state']
        assert pending['observation']['sensory'] == frames[entry['observedStep']]['sensory']
        earlier = [j for j in journals if j['pending']['entry']['id'] in applications
                   and applications[j['pending']['entry']['id']]['appliedStep'] <= entry['observedStep']]
        earlier = [j for j in earlier if j['pending']['entry']['id'] != entry['id']]
        expected_memory = max(earlier, key=lambda j: applications[j['pending']['entry']['id']]['appliedStep']) if earlier else None
        memory = pending['memory']
        if expected_memory:
            previous = expected_memory['pending']['entry']
            assert memory['entry'] == previous
            assert memory['relativePath'] == f'journals/{previous["id"]}.json'
            assert memory['appliedStep'] == applications[previous['id']]['appliedStep']
            assert previous['text'] in pending['prompt'] and previous['sha256'] in pending['prompt']
        else:
            assert memory is None
        assert timing['attemptId'] == entry['attemptId']
        dispatch, received, published = [int(timing[k]) for k in ('dispatchedAtMs', 'receivedAtMs', 'publishedAtMs')]
        assert dispatch <= request['at'] <= received <= published
        assert isinstance(timing['transportDurationMs'], int) and timing['transportDurationMs'] >= 0
        matched.append({'request': request['request'], 'turnId': entry['turnId'], 'attemptId': entry['attemptId'],
                        'observedStep': entry['observedStep'], 'journalId': entry['id'], 'textSha256': entry['sha256'],
                        'requestBodySha256': request['bodySha256'], 'promptSha256': digest(pending['prompt'].encode()),
                        'memoryJournalId': memory['entry']['id'] if memory else None,
                        'application': applications.get(entry['id']), 'timing': timing,
                        'fixtureRequestAtMs': request['at'], 'fixtureHandlerCompletedAtMs': responses[request['request']]['at'],
                        'fixtureHoldDurationMs': responses[request['request']]['at'] - request['at']})
    assert len(matched) == manifest['journalCount']
    rejected = []
    for path in links(root):
        for checkpoint in [read(path)['segment']['finalCheckpoint']]:
            phase = checkpoint['state']['phase']
            if phase['kind'] != 'blocked':
                continue
            pending = phase['value']['pending']
            candidates = [p for p in post if p['body']['messages'] == [{'role': 'user', 'content': pending['prompt']}]]
            for request in candidates:
                if request['request'] in {v['request'] for v in matched}:
                    continue
                attempt = pending['attemptId']
                received = [e for e in events if e['kind']['type'] == 'languageReceived' and e['kind']['data']['attempt_id'] == attempt]
                saved = [j for j in journals if j['pending']['entry']['attemptId'] == attempt]
                cancelled = [e for e in events if e['kind']['type'] == 'languageCancelled' and e['kind']['data']['attempt_id'] == attempt]
                assert cancelled and not received and not saved
                response = responses.get(request['request'])
                if response:
                    assert all(j['pending']['entry']['sha256'] != response['textSha256'] for j in journals)
                rejected.append({'request': request['request'], 'attemptId': attempt, 'observedStep': pending['observedStep'],
                                 'reason': phase['value']['reason'], 'cancelledEvent': cancelled[-1],
                                 'fixtureHandlerResponse': response, 'acceptedResponses': 0, 'journals': 0})
    counts = {}
    for e in events:
        k = e['kind']['type']; counts[k] = counts.get(k, 0) + 1
    return {'sessionId': manifest['sessionId'], 'seed': manifest['config']['seed'], 'step': manifest['step'],
            'journalCount': len(matched), 'eventCounts': counts, 'exactMatchedRequests': matched,
            'cancelledRequestsWithNoAcceptedResponseOrJournal': rejected}


def mutate(root, name):
    mpath = root / 'manifest.json'
    manifest = read(mpath)
    jp = sorted((root / 'journals').glob('*.json'))[0]
    sp = links(root)
    if name.startswith('journal-'):
        j = read(jp)
        if name == 'journal-text': j['pending']['entry']['text'] += ' Changed.'
        elif name == 'journal-configured-model-reanchored': j['configuredModel'] = 'wrong-model'
        elif name == 'journal-prompt-reanchored': j['pending']['prompt'] += '\nUnretained instruction.'
        elif name == 'journal-negative-duration-reanchored': j['timing']['transportDurationMs'] = -1
        write(jp, j)
        if name.endswith('reanchored'): reanchor(root)
    elif name == 'manifest-clock':
        manifest['step'] += 1; manifest['durableStep'] += 1; write(mpath, manifest)
    elif name == 'manifest-journal-count':
        manifest['journalCount'] += 1; write(mpath, manifest)
    elif name == 'manifest-seed':
        manifest['config']['seed'] = '9'; write(mpath, manifest)
    elif name == 'missing-segment': sp[0].unlink()
    elif name == 'reordered-segment':
        a, b = sp[0].read_bytes(), sp[1].read_bytes(); sp[0].write_bytes(b); sp[1].write_bytes(a)
    elif name == 'non-genesis-checkpoint-reanchored':
        j = read(sp[0]); j['segment']['initialCheckpoint'] = copy.deepcopy(j['segment']['finalCheckpoint']); write(sp[0], j); reanchor(root)
    elif name == 'numerical-state-reanchored':
        j = read(sp[0]); next(e for e in j['segment']['events'] if e['kind']['type'] == 'advanced')['kind']['data']['state'][0] += .01; write(sp[0], j); reanchor(root)
    elif name == 'event-order-reanchored':
        p = next(p for p in sp if any(e['kind']['type'] == 'languageReceived' for e in read(p)['segment']['events']))
        j = read(p); es = j['segment']['events']; i = next(i for i,e in enumerate(es) if e['kind']['type'] == 'languageReceived'); es[i-1], es[i] = es[i], es[i-1]; write(p, j); reanchor(root)
    elif name == 'missing-journal': jp.unlink()
    else: raise AssertionError(name)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--executable', required=True, type=Path)
    p.add_argument('--requests', required=True, type=Path)
    p.add_argument('--scratch', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('bundles', nargs='+', type=Path)
    a = p.parse_args()
    assert not a.output.exists(), 'Receipt already exists'
    a.scratch.mkdir(parents=True, exist_ok=False)
    source_executable = identity(a.executable)
    executable = a.scratch.resolve() / 'reservoir-scope-desktop-pinned'
    executable.write_bytes(a.executable.read_bytes()); executable.chmod(0o755)
    assert identity(a.executable) == source_executable and digest(executable.read_bytes()) == source_executable['sha256']
    request_bytes = a.requests.read_bytes(); assert request_bytes.endswith(b'\n')
    (a.scratch / 'requests.snapshot.jsonl').write_bytes(request_bytes)
    entries = [json.loads(line) for line in request_bytes.splitlines()]
    receipt = {'schema': 'reservoir-sustained-ui-export-qualification-v1', 'createdAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'modelsContacted': False, 'scope': 'Offline qualification of explicit UI-exported bundles against a pinned production CLI and owned fixture log. No real model/provider calls. Fixture response log proves handler completion, not receipt by a cancelled client. Local timestamps are recorded observations, not authenticated execution.',
               'verifierSource': source_executable, 'pinnedVerifier': identity(executable), 'requestLogSnapshot': identity(a.scratch / 'requests.snapshot.jsonl'),
               'checker': identity(Path(__file__)), 'bundles': [], 'negativeControls': [], 'status': 'passed'}
    controls = ['journal-text', 'journal-configured-model-reanchored', 'journal-prompt-reanchored', 'journal-negative-duration-reanchored',
                'manifest-clock', 'manifest-journal-count', 'manifest-seed', 'missing-segment', 'reordered-segment',
                'non-genesis-checkpoint-reanchored', 'numerical-state-reanchored', 'event-order-reanchored', 'missing-journal']
    for bundle in a.bundles:
        before = inventory(bundle)
        result = verify(executable, bundle.resolve())
        if result['exitCode'] != 0 or result['result'].get('status') != 'passed': receipt['status'] = 'failed'
        evidence = request_evidence(bundle, entries)
        receipt['bundles'].append({'path': str(bundle.resolve()), 'before': before, 'verification': result, 'requestEvidence': evidence})
        for name in controls:
            altered = a.scratch / f'{bundle.name}-{name}'
            shutil.copytree(bundle, altered)
            mutate(altered, name)
            result = verify(executable, altered.resolve())
            rejected = result['exitCode'] != 0 and result['result'].get('status') == 'failed'
            if not rejected: receipt['status'] = 'failed'
            receipt['negativeControls'].append({'original': bundle.name, 'control': name, 'expected': 'rejected', 'passed': rejected, 'verification': result})
        after = inventory(bundle)
        receipt['bundles'][-1]['originalUnchanged'] = before == after
        if before != after: receipt['status'] = 'failed'
    receipt['pinnedVerifierUnchanged'] = identity(executable) == receipt['pinnedVerifier']
    receipt['requestLogOriginalPrefixUnchanged'] = a.requests.read_bytes().startswith(request_bytes)
    receipt['summary'] = {'originals': len(a.bundles), 'negativeControls': len(receipt['negativeControls']),
                          'negativeControlsRejected': sum(c['passed'] for c in receipt['negativeControls'])}
    if not receipt['pinnedVerifierUnchanged'] or not receipt['requestLogOriginalPrefixUnchanged']: receipt['status'] = 'failed'
    with a.output.open('x') as f: json.dump(receipt, f, indent=2); f.write('\n')
    print(json.dumps({'status': receipt['status'], 'receipt': str(a.output), **receipt['summary']}))
    raise SystemExit(0 if receipt['status'] == 'passed' else 1)

if __name__ == '__main__': main()
