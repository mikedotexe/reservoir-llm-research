#!/usr/bin/env python3
"""Which earlier entry each turn returned (desktop 0.36.0 `memoryPolicy`), per session.

Inputs: one or more Tauri sustained session directories (`manifest.json` with the config;
`journals/*.json`, each with `pending.memory` and, under a choosing policy, the recorded
`pending.memoryChoice`). Per session it prints, with n: the policy; the journals that carried
an earlier entry; the age of the returned entry in entries (0 is the latest applied one; share
at 0, median, max) and in steps (observed step minus the entry's application step); how many
distinct entries were returned and the most-returned entry's count; the cosine score
distribution (state-aligned only); the candidates at the last turn; and a fidelity check that
every returned entry's saved text appears verbatim in that turn's prompt. Standard library
only. Subject: the laptop apparatus, never the beings.
"""
import glob, json, os, statistics, sys

def load(session):
    cfg = json.load(open(os.path.join(session, 'manifest.json')))['config']
    journals = {}
    for f in glob.glob(os.path.join(session, 'journals', '*.json')):
        j = json.load(open(f))['pending']; journals[j['entry']['id']] = j
    return cfg, journals

def analyse(session):
    cfg, journals = load(session); policy = cfg.get('memoryPolicy', 'latest')
    turns = sorted(journals.values(), key=lambda j: j['entry']['observedStep'])
    with_memory = [j for j in turns if j.get('memory')]
    ages, steps, scores, returned, fidelity_misses, candidates = [], [], [], [], 0, None
    for j in with_memory:
        m = j['memory']; c = j.get('memoryChoice')
        if c:
            ages.append(c['age']); steps.append(j['entry']['observedStep'] - c['appliedStep']); returned.append(c['entryId']); candidates = c['candidates']
            if c.get('score') is not None: scores.append(c['score'])
            assert c['entryId'] == m['entry']['id'], 'choice and memory disagree'
        else:
            ages.append(0); steps.append(j['entry']['observedStep'] - m['appliedStep']); returned.append(m['entry']['id'])
        saved = journals.get(m['entry']['id'])
        if saved is None or saved['entry']['text'] not in j['prompt']: fidelity_misses += 1
    counts = {}
    for r in returned: counts[r] = counts.get(r, 0) + 1
    return dict(name=os.path.basename(os.path.dirname(session.rstrip('/'))), policy=policy, n=len(turns), with_memory=len(with_memory), ages=ages, steps=steps, scores=scores,
                distinct=len(counts), most=max(counts.values()) if counts else 0, candidates=candidates, misses=fidelity_misses)

def show(r):
    print(f"\n{r['name']}: policy {r['policy']} · {r['n']} journals (n), {r['with_memory']} with an earlier entry")
    if r['ages']:
        a, s = r['ages'], r['steps']
        print(f"  age of the returned entry: {100*sum(1 for x in a if x == 0)/len(a):.0f}% at 0 (the latest) · median {statistics.median(a):.0f} entries, max {max(a)} · in steps median {statistics.median(s):.0f}, max {max(s)}")
        print(f"  distinct entries returned {r['distinct']} of {len(a)} returns · most-returned entry {r['most']}×" + (f" · candidates at the last turn {r['candidates']}" if r['candidates'] is not None else ''))
        if r['scores']: print(f"  cosine score: median {statistics.median(r['scores']):+.3f}, min {min(r['scores']):+.3f}, max {max(r['scores']):+.3f} (n={len(r['scores'])})")
        print(f"  fidelity: returned text verbatim in the prompt on {len(a) - r['misses']} of {len(a)} turns")

def main(argv):
    for s in argv: show(analyse(s))

if __name__ == '__main__':
    main(sys.argv[1:])
