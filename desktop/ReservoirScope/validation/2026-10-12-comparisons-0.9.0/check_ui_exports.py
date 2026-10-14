"""Check the explicit dialog-created 0.9 exports; run from desktop/ReservoirScope."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

BASE = Path('target/qa/0.9-ui')
OUT = Path(__file__).parent / 'recovery-export-equality.json'
checks = []

def identity(path):
    data = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

def check(name, passed):
    assert passed, name
    checks.append({'name': name, 'passed': True})

h = json.loads((BASE / 'paired-h-fixed-11.json').read_bytes())
o = json.loads((BASE / 'observation-active-8.json').read_bytes())
c = json.loads((BASE / 'half-boundary.json').read_bytes())
for name in ['paired-h-fixed-11', 'observation-active-8']:
    check(name + ' recovered exact bytes', (BASE / (name + '.json')).read_bytes() == (BASE / (name + '-recovered.json')).read_bytes())
check('wide seed preserved', h['specification']['seed'] == o['specification']['seed'] == 2**64 - 1)
check('H fixed pair complete', h['status'] == 'completed' and h['specification']['mode'] == 'fixedReplay' and h['left']['stage'] == 7 and h['right']['stage'] == 8)
check('H both three turns two journals', all(len(h[a]['actions']) == 3 and len(h[a]['journals']) == 2 for a in ['left', 'right']))
check('H fixed shared forcing keeps state equal', all(l['state'] == r['state'] for l, r in zip(h['left']['frames'], h['right']['frames'])))
check('H retention differs from G', any(l['retentionUsed'] != r['retentionUsed'] for l, r in zip(h['left']['frames'], h['right']['frames'])))
for arm in ['left', 'right']:
    actions = h[arm]['actions']
    check(arm + ' 6 to 7 application', actions[1]['observedStep'] == 6 and actions[1]['applicationStep'] == 7)
    check(arm + ' memory from saved journal', actions[1]['memoryText'] == h[arm]['journals'][0]['text'])
    check(arm + ' WAIT lacks new save and application', actions[2]['chosenAction'] == 'WAIT' and actions[2]['saveReceipt'] is None and actions[2]['applicationStep'] is None)
    check(arm + ' owned journal namespace', all(a['saveReceipt']['relativePath'].startswith(arm + '/') for a in actions[:2]))
check('observation active D/D complete', o['status'] == 'completed' and o['left']['stage'] == o['right']['stage'] == 4 and o['specification']['forcingProfile'] == 'continuousSensoryV1')
check('observation exact equal frames', o['left']['frames'] == o['right']['frames'])
check('observation alternating actual orders', [a['requestOrder'] for a in o['left']['actions']] == [1, 2] and [a['requestOrder'] for a in o['right']['actions']] == [2, 1])
check('observation coordinates only on right', all('x[31]=' in a['prompt'] for a in o['right']['actions']) and all('x[31]=' not in a['prompt'] for a in o['left']['actions']))
# D retains the computed codec vector as evidence, but never applies it to state.
check('observation no application receipts', all(a['applicationStep'] is None for arm in ['left', 'right'] for a in o[arm]['actions']))
check('observation semantic input stays zero', all(not any(f['semanticInput']) for arm in ['left', 'right'] for f in o[arm]['frames']))
check('checkpoint distinct current and durable steps', c['step'] == 3 and c['durableStep'] == 0 and c['pairedBoundary']['step'] == 3)
left, right = c['pairedBoundary']['arms']
check('checkpoint retains saved left only', left['arm'] == 'left' and left['receipt']['saveReceipt']['status'] == 'saved' and left['journal'] is not None and right['arm'] == 'right' and right['receipt'] is None and right['journal'] is None)
check('same ID still distinct arms', c['pendingJournal']['arm'] == 'right' and c['pendingJournal']['entry']['id'] == left['journal']['id'] and c['pendingJournal']['relativePath'].startswith('right/') and left['receipt']['saveReceipt']['relativePath'].startswith('left/'))
check('checkpoint saved text hash', hashlib.sha256(left['journal']['text'].encode()).hexdigest() == left['journal']['sha256'])
check('checkpoint attempt belongs to left', len(c['attempts']) == 1 and c['attempts'][0]['arm'] == 'left' and c['attempts'][0]['status'] == 'committed')
receipt = {'capturedAtUtc': datetime.now(timezone.utc).isoformat(), 'passed': True,
           'script': identity(Path(__file__)), 'inputs': [identity(p) for p in sorted(BASE.glob('*.json'))], 'checks': checks,
           'limits': 'Exact-byte recovery and exported field assertions. Portable exports separately pass independent replay. Partial checkpoint consistency is not numerical replay or physical crash/power-loss qualification.'}
with OUT.open('x') as output:
    json.dump(receipt, output, indent=2)
    output.write('\n')
print(f'{len(checks)} export and recovery checks passed')
