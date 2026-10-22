#!/usr/bin/env python3
"""Which earlier entry each turn returned (desktop 0.36.0 `memoryPolicy`), per session.

Inputs: one or more Tauri sustained session directories (`manifest.json` with the config;
`journals/*.json`, each with `pending.memory` and, under a choosing policy, the recorded
`pending.memoryChoice`; under the 0.38.0 two-entry prompt version also `pending.latestShown`).
Per session it prints, with n: the policy, the prompt version and the recent-return window;
the journals that carried an earlier entry; the age of the returned entry in entries (0 is
the latest applied one; share at 0, median, max) and in steps (observed step minus the
entry's application step); how many distinct entries were returned, the most-returned entry's
count and, for entries returned more than once, the turns between their returns (min and
median); the cosine score distribution (the state policies); the candidates at the last turn;
under a window (0.38.0) how many turns kept at least one entry out, how many lapsed (every
older entry inside the window, so all competed) and the mean number kept out; and a fidelity
check that every returned entry's saved text, and the latest entry's text when it was also
shown, appears verbatim in that turn's prompt. Standard library only. Subject: the laptop
apparatus, never the beings.
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
    window = cfg.get('memoryRecentExclusion', 0); version = cfg.get('promptVersion', 'reservoir-journal-v1')
    turns = sorted(journals.values(), key=lambda j: j['entry']['observedStep'])
    with_memory = [j for j in turns if j.get('memory')]
    ages, steps, scores, returned, fidelity_misses, candidates = [], [], [], [], 0, None
    excluded, lapses, with_latest, latest_misses = [], 0, 0, 0
    for j in with_memory:
        m = j['memory']; c = j.get('memoryChoice')
        if c:
            ages.append(c['age']); steps.append(j['entry']['observedStep'] - c['appliedStep']); returned.append(c['entryId']); candidates = c['candidates']
            if c.get('score') is not None: scores.append(c['score'])
            assert c['entryId'] == m['entry']['id'], 'choice and memory disagree'
            kept_out = c.get('excludedRecent', 0)
            if kept_out:
                excluded.append(kept_out)
                if kept_out == c['candidates'] - 1: lapses += 1
        else:
            ages.append(0); steps.append(j['entry']['observedStep'] - m['appliedStep']); returned.append(m['entry']['id'])
        saved = journals.get(m['entry']['id'])
        if saved is None or saved['entry']['text'] not in j['prompt']: fidelity_misses += 1
        latest = j.get('latestShown')
        if latest:
            with_latest += 1
            saved_latest = journals.get(latest['entry']['id'])
            if saved_latest is None or saved_latest['entry']['text'] not in j['prompt']: latest_misses += 1
    counts, last_seen, gaps = {}, {}, []
    for turn, r in enumerate(returned):
        counts[r] = counts.get(r, 0) + 1
        if r in last_seen: gaps.append(turn - last_seen[r])
        last_seen[r] = turn
    return dict(name=os.path.basename(os.path.dirname(session.rstrip('/'))), policy=policy, version=version, window=window, n=len(turns), with_memory=len(with_memory), ages=ages, steps=steps, scores=scores,
                distinct=len(counts), most=max(counts.values()) if counts else 0, gaps=gaps, candidates=candidates, misses=fidelity_misses,
                excluded=excluded, lapses=lapses, with_latest=with_latest, latest_misses=latest_misses)

def show(r):
    print(f"\n{r['name']}: policy {r['policy']} · {r['version']}" + (f" · window {r['window']} turns" if r['window'] else '') + f" · {r['n']} journals (n), {r['with_memory']} with an earlier entry")
    if r['ages']:
        a, s = r['ages'], r['steps']
        print(f"  age of the returned entry: {100*sum(1 for x in a if x == 0)/len(a):.0f}% at 0 (the latest) · median {statistics.median(a):.0f} entries, max {max(a)} · in steps median {statistics.median(s):.0f}, max {max(s)}")
        print(f"  distinct entries returned {r['distinct']} of {len(a)} returns · most-returned entry {r['most']}×" + (f" · candidates at the last turn {r['candidates']}" if r['candidates'] is not None else '')
              + (f" · turns between returns of the same entry: min {min(r['gaps'])}, median {statistics.median(r['gaps']):.0f} (n={len(r['gaps'])})" if r['gaps'] else ' · no entry returned twice'))
        if r['scores']: print(f"  cosine score: median {statistics.median(r['scores']):+.3f}, min {min(r['scores']):+.3f}, max {max(r['scores']):+.3f} (n={len(r['scores'])})")
        if r['window']:
            print(f"  window: kept at least one entry out on {len(r['excluded'])} of {len(a)} turns (mean {statistics.mean(r['excluded']) if r['excluded'] else 0:.1f} kept out) · lapsed (all older entries inside the window) on {r['lapses']}")
        print(f"  fidelity: returned text verbatim in the prompt on {len(a) - r['misses']} of {len(a)} turns" + (f" · latest entry also shown on {r['with_latest']} turns, verbatim on {r['with_latest'] - r['latest_misses']}" if r['with_latest'] else ''))

def main(argv):
    for s in argv: show(analyse(s))

if __name__ == '__main__':
    main(sys.argv[1:])
