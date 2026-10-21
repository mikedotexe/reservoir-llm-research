#!/usr/bin/env python3
"""Per-step fill, spectrum shares, state RMS, retention and feedback application for a
Tauri My reservoir session, plus cosine similarity of consecutive encoded feature vectors.

Input: a sustained session directory (see desktop_session_overlap.py). Reads segments/*.json
and journals/*.json only. Prints every 5th step and every step within 3 of a writing boundary.
Standard library only. Subject: the laptop preview's own loop, never the beings.
"""
import glob, json, math, os, sys

def main(session):
    seen = {}
    for f in sorted(glob.glob(os.path.join(session, 'segments', '*.json'))):
        for ev in json.load(open(f))['segment']['events']:
            if ev['kind']['type'] == 'advanced':
                d = ev['kind']['data']; seen[d['step']] = d
    boundaries = {s for s in seen if s % 30 in (0, 1, 2, 3, 28, 29)}
    print(f"steps: {len(seen)}  (n)")
    print("step  fill%   entropy  head   rms     retUsed  maxInput  applied")
    for s in sorted(seen):
        if s % 5 == 0 or s in boundaries or s <= 4:
            d = seen[s]; k = d['sensory']; st = d['state']
            rms = math.sqrt(sum(x * x for x in st) / len(st))
            applied = '' if d['application'] is None else f"journal@{d['application']['observedStep']}"
            print(f"{s:>4}  {k['fillPercent']:>6.2f}  {k['entropy']:.3f}  {k['headShare']:.3f}  {rms:.4f}  {d['retentionUsed']:.3f}   {max(abs(x) for x in d['input']):.3f}   {applied}")
    files = sorted(glob.glob(os.path.join(session, 'journals', '*.json')),
                   key=lambda f: int(os.path.basename(f).split('-')[1]))
    vecs = []
    for f in files:
        p = json.load(open(f))['pending']; vecs.append((p['entry']['observedStep'], p['encodedFeatures']))
    def cos(a, b):
        return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))
    print("\nencoded feature vectors: dim", len(vecs[0][1]) if vecs else 0, " cosine to previous entry:")
    for i in range(1, len(vecs)):
        print(f"  step {vecs[i][0]:>3} vs {vecs[i-1][0]:>3}: {cos(vecs[i][1], vecs[i-1][1]):.4f}")

if __name__ == '__main__':
    main(sys.argv[1])
