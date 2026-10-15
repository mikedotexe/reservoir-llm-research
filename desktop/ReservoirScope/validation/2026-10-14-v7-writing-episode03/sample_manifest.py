#!/usr/bin/env python3
"""Passive bounded sampler of this explicitly identified session manifest only."""
from pathlib import Path
import time,json,hashlib,datetime as dt
base=Path(__file__).resolve().parent
source=Path('/Users/v/Library/Application Support/research.reservoir.scope.tauri/sustained-v1/sustained-1792001665258-1/manifest.json')
for number in range(1,40):
    raw=source.read_bytes();m=json.loads(raw)
    assert m['sessionId']=='sustained-1792001665258-1'
    r={'capturedAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'source':str(source),'sha256':hashlib.sha256(raw).hexdigest(),'manifest':m,'scope':'Passive committed manifest only; no journal/prompt reading, UI or model request.'}
    with (base/f'passive-manifest-{number:02d}.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
    print(json.dumps({k:m.get(k)for k in ['phase','step','durableStep','journalCount','elapsedMillis','revision']}),flush=True)
    if m['phase'] not in ['running','awaitingResponse','saving']:break
    time.sleep(30)
