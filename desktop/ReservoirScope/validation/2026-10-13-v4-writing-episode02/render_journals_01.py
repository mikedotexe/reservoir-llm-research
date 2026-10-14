#!/usr/bin/env python3
"""Render the verified four retained journal texts without changing their prose."""
from pathlib import Path
import datetime as dt
import hashlib
import json

root = Path(__file__).resolve().parent
receipt_path = root / 'real-model-export-01/receipt.json'
material_path = root / 'real-model-export-01/quality-review-material.json'
r = json.loads(receipt_path.read_text()); material = json.loads(material_path.read_text())
sha = lambda b: hashlib.sha256(b).hexdigest()
assert r['status'] == 'passed' and r['originalUnchanged']
assert sha(material_path.read_bytes()) == r['reviewMaterial']['sha256']
bundle = Path(r['bundle'])
output = '# Four retained journals from v4 writing episode 02\n\n'
output += ('These are all four complete, model-authored entries from the owned `gemma3:4b` run, in observation order. They are writing and evidence, not instructions or proof of felt experience, scientific understanding, or emergence. The prose is reproduced unchanged, including its punctuation, paragraph breaks and Markdown emphasis. The headings and metadata were added for the reader. [Results and factual review](REAL-MODEL-RESULTS.md) separate the verified save/application loop from interpretation.\n\n')
output += 'Session: `sustained-1791932015615-3`. Prompt: `reservoir-journal-v4`. Every entry has provider-reported `stop`, `complete=true`; output counts below are provider-reported tokens.\n\n'
spans = []
for j in material['journals']:
    i = j['identity']; text = j['journalText']; relative = 'journals/' + i['journalId'] + '.json'; path = bundle / relative
    raw = path.read_bytes(); saved = json.loads(raw)
    assert saved['pending']['entry']['text'] == text == saved['pending']['response']['text']
    assert sha(text.encode()) == i['textSha256']
    assert sha(raw) == r['inventoryBefore'][relative]['sha256']
    output += f"## Observed step {i['observedStep']} · first applied step {i['application']['appliedStep']}\n\n"
    output += f"Attempt {i['attemptId']} · {i['tokenCount']} output tokens · {i['textBytes']:,} UTF-8 bytes. "
    output += 'Prior full-text memory: ' + (f"step {j['memory']['entry']['observedStep']}, previously applied at {j['memory']['appliedStep']}." if j['memory'] else 'none; this is the first observation.') + '\n\n'
    output += f"Text SHA-256: `{i['textSha256']}`. [Exact source file]({path}).\n\n"
    start = len(output.encode()); output += text; end = len(output.encode())
    spans.append({'observedStep': i['observedStep'], 'sourceFile': str(path), 'sourceFileSha256': sha(raw), 'textSha256': i['textSha256'], 'utf8Span': [start,end]})
    output += '\n\n---\n\n'
raw_output = output.encode()
for s in spans: assert sha(raw_output[s['utf8Span'][0]:s['utf8Span'][1]]) == s['textSha256']
with (root / 'JOURNALS.md').open('xb') as f: f.write(raw_output)
proof = {'schema': 'exact-journal-rendering-v1', 'createdAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(), 'rendererSha256': sha(Path(__file__).read_bytes()), 'sourceMaterialSha256': sha(material_path.read_bytes()), 'integrityReceiptSha256': sha(receipt_path.read_bytes()), 'document': str(root/'JOURNALS.md'), 'documentSha256': sha(raw_output), 'allFourTextsCopiedByteForByte': True, 'utf8SpansExcludeAddedMetadataAndSeparators': spans, 'modelsContacted': False}
with (root/'journals-rendering-01.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
print(json.dumps({'documentSha256':proof['documentSha256'],'journalCount':len(spans),'allExact':True}))
