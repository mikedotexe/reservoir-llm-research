#!/usr/bin/env python3
"""Fixed local text-representation diagnostic; standard library only.

prepare is offline and freezes eight four-text groups plus32 ordinary journals.
summarize is offline and reads output from the codec_distinction Rust example.
embed is an explicit loopback-only collection step, disabled until the source
six-hour session is complete and the operator supplies --root-release.
No journal prose is printed. All retained vectors and failures remain evidence.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import itertools
import json
import math
import statistics
import time
import urllib.error
import urllib.request

MODEL = 'nomic-embed-text:latest'
ENDPOINT = 'http://127.0.0.1:11434'
SEEDS = [20260909, 20260910, 0x50524F4A45435433]
GROUPS = [
    ('roles', 'The dog chased the cat.', 'The cat was pursued by the dog.',
     'The cat chased the dog.', 'The baker cooled the bread.'),
    ('support', 'I support Alice, not Bob.', 'My support goes to Alice rather than Bob.',
     'I support Bob, not Alice.', 'I packed apples, not pears.'),
    ('valves', 'Open the north valve and close the south valve.',
     'Let water through the northern valve while shutting the southern valve.',
     'Close the north valve and open the south valve.',
     'Paint the blue doorway and clean the white window.'),
    ('memory', 'I want to preserve this memory rather than erase it.',
     'I would prefer to keep this recollection instead of deleting it.',
     'I want to erase this memory rather than preserve it.',
     'I want to repair this bicycle rather than replace it.'),
    ('withholding', 'I will keep writing while withholding the text from numerical input.',
     'I plan to continue the journal but keep its words out of the reservoir input.',
     'I will keep writing while sending the text as numerical input.',
     'I will keep walking while watching the clouds over the harbor.'),
    ('temperature', 'The room became warmer after the heater was switched on.',
     'Turning on the heater raised the room\'s temperature.',
     'The room became colder after the heater was switched on.',
     'The path became steeper after the trail crossed the bridge.'),
    ('causality', 'The train arrived late because the bridge was closed.',
     'A bridge closure caused the train\'s late arrival.',
     'The bridge was closed because the train arrived late.',
     'The cake tasted sweet because the baker added honey.'),
    ('revision', 'I changed my mind after reading the new evidence.',
     'The new evidence persuaded me to revise my earlier view.',
     'I kept my view after reading the new evidence.',
     'I washed my hands after working in the garden.'),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_new(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def prepare(args):
    args.output.mkdir(parents=True, exist_ok=True)
    items = []
    for group, *texts in GROUPS:
        for role, text in zip(('anchor', 'paraphrase', 'changed', 'unrelated'), texts):
            items.append({'id': f'{group}-{role}', 'cohort': 'controlled',
                          'group': group, 'role': role, 'text': text})
    for step in range(300, 9601, 300):
        paths = list((args.baseline_store / 'journals').glob(f'journal-{step}-*.json'))
        if len(paths) != 1:
            raise ValueError(f'Expected one saved ordinary entry at step {step}')
        raw = paths[0].read_bytes()
        p = json.loads(raw)['pending']
        if p.get('checkIn') is not None or p['entry']['observedStep'] != step:
            raise ValueError('Selected journal is not the prescribed ordinary entry')
        items.append({'id': f'ordinary-{step}', 'cohort': 'ordinary',
                      'text': p['entry'].get('body') or p['entry']['text'],
                      'source': {'step': step, 'file': paths[0].name,
                                 'journalId': p['entry']['id'], 'objectSha256': sha(raw)},
                      'retainedSurface': p['encodedFeatures'],
                      'retainedFeedback': p['semanticVector']})
    corpus = {'format': 'codec-distinction-corpus-v1', 'frozenAt': stamp(),
              'baselineStore': str(args.baseline_store.resolve()), 'projectionSeeds': SEEDS,
              'model': MODEL, 'taskPrefix': None, 'truncate': False, 'items': items}
    write_new(args.output / 'corpus.json', corpus)
    receipt = {'frozenAt': corpus['frozenAt'],
               'corpusSha256': sha((args.output / 'corpus.json').read_bytes()),
               'controlledTexts': 32, 'ordinaryTexts': 32,
               'maxUtf8Bytes': max(len(x['text'].encode()) for x in items),
               'maxWhitespaceWords': max(len(x['text'].split()) for x in items),
               'projectionSeeds': SEEDS, 'providerRequests': 0}
    write_new(args.output / 'corpus-receipt.json', receipt)
    print(json.dumps(receipt, indent=2))


def request(path, payload=None):
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(ENDPOINT + path, data=body,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as response:
        raw = response.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            raise ValueError('Response exceeds diagnostic byte limit')
        return raw, json.loads(raw)


def collect(args):
    if not args.root_release:
        raise ValueError('No calls permitted without explicit --root-release after parent authorization')
    corpus_path = args.output / 'corpus.json'
    corpus = json.loads(corpus_path.read_text())
    source = Path(corpus['baselineStore'])
    manifest = json.loads((source / 'manifest.json').read_text())
    if manifest['phase'] != 'scheduleComplete' or manifest['elapsedMillis'] < 21600000:
        raise ValueError('The six-hour baseline has not completed; no request was sent')
    journal = args.output / 'embedding-requests.jsonl'
    if journal.exists() or (args.output / 'embedded-corpus.json').exists() or (args.output / 'collection-start.json').exists():
        raise ValueError('Refusing to replace a prior collection; preserve failures and make a new output directory')
    write_new(args.output / 'collection-start.json', {'startedAt': stamp(),
              'sourceCorpusSha256': sha(corpus_path.read_bytes()),
              'baselineSessionId': manifest['sessionId'],
              'baselineCompletionRevision': manifest['revision'], 'rootRelease': True})
    before_raw, before = request('/api/tags')
    model = next(x for x in before['models'] if x['name'] == MODEL)
    (args.output / 'provider-tags-before.json').write_bytes(before_raw)
    version_raw, _ = request('/api/version')
    (args.output / 'provider-version.json').write_bytes(version_raw)
    started = stamp()
    success = 0
    for item in corpus['items']:
        payload = {'model': MODEL, 'input': [item['text']], 'truncate': False}
        row = {'id': item['id'], 'textSha256': sha(item['text'].encode()),
               'startedAt': stamp(), 'request': payload, 'modelDigest': model['digest']}
        begin = time.monotonic()
        try:
            raw, response = request('/api/embed', payload)
            row.update(response=response, responseSha256=sha(raw))
            vectors = response['embeddings']
            if response.get('model', MODEL) != MODEL or len(vectors) != 1:
                raise ValueError('Unexpected model or embedding count')
            vector = vectors[0]
            if len(vector) != 768 or any(not math.isfinite(x) for x in vector) or norm(vector) == 0:
                raise ValueError('Unexpected embedding dimensions or values')
            item['embedding'] = vector
            success += 1
            row['status'] = 'complete'
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, TypeError) as error:
            row.update(status='failed', error=str(error))
            if 'response' in row:
                row['responseRawUtf8'] = raw.decode(errors='replace')
                del row['response']
            if isinstance(error, urllib.error.HTTPError):
                row['httpErrorBody'] = error.read(65536).decode(errors='replace')
            item['embeddingError'] = row['error']
        row['durationSeconds'] = time.monotonic() - begin
        with journal.open('a') as f:
            f.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
        print(json.dumps({'id': item['id'], 'status': row['status'], 'seconds': row['durationSeconds']}), flush=True)
    after_raw, after = request('/api/tags')
    after_model = next(x for x in after['models'] if x['name'] == MODEL)
    (args.output / 'provider-tags-after.json').write_bytes(after_raw)
    if model['digest'] != after_model['digest']:
        raise ValueError('Embedding model digest changed during collection')
    write_new(args.output / 'embedded-corpus.json', corpus)
    receipt = {'startedAt': started, 'finishedAt': stamp(), 'model': MODEL,
               'modelDigest': model['digest'], 'taskPrefix': None, 'truncate': False,
               'requests': len(corpus['items']), 'complete': success,
               'failed': len(corpus['items']) - success,
               'baselineCompletionRevision': manifest['revision'],
               'sourceCorpusSha256': sha(corpus_path.read_bytes())}
    write_new(args.output / 'embedding-receipt.json', receipt)
    print(json.dumps(receipt, indent=2))


def norm(a):
    return math.sqrt(sum(x*x for x in a))


def unit(a):
    size = norm(a)
    return [x / size for x in a] if size else [0.0] * len(a)


def cosine(a, b):
    return sum(x*y for x, y in zip(unit(a), unit(b)))


def stats(values):
    values = sorted(values)
    if not values:
        return {'n': 0}
    return {'n': len(values), 'minimum': values[0], 'median': statistics.median(values),
            'mean': statistics.mean(values), 'p95': values[min(len(values)-1, math.ceil(.95*len(values))-1)],
            'maximum': values[-1]}


def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranked = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = (start + end - 1) / 2
        for i in order[start:end]:
            ranked[i] = rank
        start = end
    return ranked


def correlation(a, b):
    ma, mb = statistics.mean(a), statistics.mean(b)
    aa, bb = [x-ma for x in a], [y-mb for y in b]
    den = norm(aa)*norm(bb)
    return sum(x*y for x, y in zip(aa, bb))/den if den else None


def summarize(args):
    data = json.loads(args.vectors.read_text())
    rows = data['rows']
    names = sorted({name for r in rows for name in r['vectors']})
    result = {'format': 'codec-distinction-report-v1', 'vectorsSha256': sha(args.vectors.read_bytes()),
              'corpusSha256': data['corpusSha256'], 'representationCounts': {},
              'cohorts': {}, 'controlledGroups': {}, 'projectionGeometry': {}}
    for name in names:
        result['representationCounts'][name] = sum(name in r['vectors'] for r in rows)
    for cohort in ('controlled', 'ordinary'):
        selected = [r for r in rows if r['cohort'] == cohort]
        cohort_stats = {}
        for name in names:
            available = [r for r in selected if name in r['vectors']]
            if not available:
                continue
            vecs = [r['vectors'][name] for r in available]
            units = [unit(v) for v in vecs]
            mean = [statistics.mean(c) for c in zip(*units)]
            pairs = [(a,b) for a,b in itertools.combinations(available,2)]
            item = {'texts': len(available), 'dimensions': len(vecs[0]),
                    'nonzeroDimensionsMax': max(sum(x != 0 for x in v) for v in vecs),
                    'unitMeanNorm': norm(mean), 'meanDirectionEnergyFraction': norm(mean)**2,
                    'vectorL2': stats([norm(v) for v in vecs]),
                    'pairwiseCosine': stats([cosine(a['vectors'][name],b['vectors'][name]) for a,b in pairs]),
                    'exactCollisionPairs': [[a['id'],b['id']] for a,b in pairs if a['vectors'][name] == b['vectors'][name]]}
            if name in ('surface', 'retained-surface-feedback'):
                common_energy = sum(x*x for x in mean)
                item['commonDirectionContributors'] = sorted(
                    ({'slot':i, 'meanUnitValue':x, 'fractionOfMeanDirectionEnergy':x*x/common_energy}
                     for i,x in enumerate(mean)),
                    key=lambda x:x['fractionOfMeanDirectionEnergy'], reverse=True)
            if cohort == 'ordinary':
                item['adjacentSampleCosine'] = stats([cosine(a['vectors'][name],b['vectors'][name]) for a,b in zip(available,available[1:])])
            cohort_stats[name] = item
        result['cohorts'][cohort] = cohort_stats
        for name in names:
            if not (name.startswith('embedding32-') or name.startswith('diagnostic')):
                continue
            available = [r for r in selected if name in r['vectors'] and 'embedding-raw' in r['vectors']]
            raw, projected = [], []
            for a,b in itertools.combinations(available,2):
                raw.append(cosine(a['vectors']['embedding-raw'],b['vectors']['embedding-raw']))
                projected.append(cosine(a['vectors'][name],b['vectors'][name]))
            result['projectionGeometry'].setdefault(cohort,{})[name] = {
                'cosineAbsoluteError': stats([abs(a-b) for a,b in zip(raw,projected)]),
                'pairwiseCosineSpearman': correlation(ranks(raw),ranks(projected)) if raw else None}
    for name in names:
        groups = []
        for group, *_ in GROUPS:
            group_rows = {r['role']:r for r in rows if r.get('group')==group and name in r['vectors']}
            if set(group_rows) != {'anchor','paraphrase','changed','unrelated'}:
                continue
            a,p,c,u = [group_rows[role]['vectors'][name] for role in ('anchor','paraphrase','changed','unrelated')]
            ap,au,ac = cosine(a,p),cosine(a,u),cosine(a,c)
            groups.append({'group':group,'paraphraseCosine':ap,'unrelatedCosine':au,'changedMeaningCosine':ac,
                           'paraphraseMargin':ap-au,'paraphraseAboveUnrelated':ap>au,
                           'changedMeaningExactCollision':a==c,
                           'changedMeaningUnitDistance':norm([x-y for x,y in zip(unit(a),unit(c))])})
        if groups:
            result['controlledGroups'][name] = {'n':len(groups),
                'paraphraseAboveUnrelated':sum(x['paraphraseAboveUnrelated'] for x in groups),
                'changedMeaningExactCollisions':sum(x['changedMeaningExactCollision'] for x in groups),'groups':groups}
    write_new(args.report,result)
    compact = {'representations':result['representationCounts'],
               'controlled':{k:{x:v[x] for x in ('n','paraphraseAboveUnrelated','changedMeaningExactCollisions')} for k,v in result['controlledGroups'].items()},
               'ordinary':{k:{'pairwiseCosineMean':v['pairwiseCosine']['mean'],'adjacentSampleCosineMedian':v['adjacentSampleCosine']['median'],'unitMeanNorm':v['unitMeanNorm']} for k,v in result['cohorts']['ordinary'].items()}}
    print(json.dumps(compact,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='operation',required=True)
    p=sub.add_parser('prepare');p.add_argument('--baseline-store',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.set_defaults(run=prepare)
    p=sub.add_parser('embed');p.add_argument('--output',type=Path,required=True);p.add_argument('--root-release',action='store_true');p.set_defaults(run=collect)
    p=sub.add_parser('summarize');p.add_argument('--vectors',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.set_defaults(run=summarize)
    args=parser.parse_args();args.run(args)


if __name__=='__main__':
    main()
