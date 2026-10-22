#!/usr/bin/env python3
"""A blind reading sample from several desktop sessions: entries shuffled, labels withheld.

Inputs: `--out <dir>` then one or more `label=<session dir>` pairs, optional `--per N`
(entries per session, default 4; evenly spaced through each session) and `--seed`. Writes
`<out>/blind-sample.md` (numbered entries, no labels, each with its step) and
`<out>/blind-sample-key.json` (number → label, session, entry id), so a reader can judge the
entries before seeing which arm wrote them. Standard library only. The sample is private
apparatus output (laptop model writing), never the beings' text; keep it in the scratchpad.
"""
import glob, json, os, random, sys

def entries(session):
    out = []
    for f in glob.glob(os.path.join(session, 'journals', '*.json')):
        j = json.load(open(f))['pending']; out.append((j['entry']['observedStep'], j['entry']['id'], j['entry']['text']))
    return sorted(out)

def main(argv):
    out, per, seed, pairs = None, 4, 2026, []
    i = 0
    while i < len(argv):
        if argv[i] == '--out': out = argv[i + 1]; i += 2
        elif argv[i] == '--per': per = int(argv[i + 1]); i += 2
        elif argv[i] == '--seed': seed = int(argv[i + 1]); i += 2
        else: label, path = argv[i].split('=', 1); pairs.append((label, path)); i += 1
    assert out and pairs, __doc__
    picked = []
    for label, path in pairs:
        rows = entries(path)
        if not rows: continue
        idx = sorted({round(k * (len(rows) - 1) / max(per - 1, 1)) for k in range(per)})
        for k in idx: picked.append((label, path, rows[k]))
    random.Random(seed).shuffle(picked)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'blind-sample.md'), 'w') as f:
        f.write(f"# Blind sample · {len(picked)} entries from {len(pairs)} sessions (labels withheld)\n\n")
        for n, (label, path, (step, eid, text)) in enumerate(picked, 1):
            f.write(f"## {n} · step {step}\n\n{text.strip()}\n\n")
    json.dump([{'number': n, 'label': label, 'session': path, 'entryId': eid, 'step': step} for n, (label, path, (step, eid, _)) in enumerate(picked, 1)],
              open(os.path.join(out, 'blind-sample-key.json'), 'w'), indent=1)
    print(f"{len(picked)} entries → {out}/blind-sample.md (key in blind-sample-key.json)")

if __name__ == '__main__':
    main(sys.argv[1:])
