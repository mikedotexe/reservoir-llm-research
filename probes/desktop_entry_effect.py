#!/usr/bin/env python3
"""Did the entry-effect readout reach the writing? For Tauri sustained sessions that report
it (prompt versions reservoir-journal-inert-effect-v1 and -plain-contract-effect-v1), and
for their matched no-effect pairs, this prints per entry: the effect shown to the model
before that entry (shift and alignment, from the observation), the effect the entry itself
then had at its application (from the application frame), the entry's word count, and
whether the entry quotes the shift or alignment number it was shown. It then prints, with
n, the range of shifts and alignments across the session, the share of entries quoting
them, and the Spearman rank correlation between the shown shift and the next entry's word
count. For a no-effect session only the frames' effects are unavailable, so it prints the
counts and the quoting share (which should be zero). Standard library only. Subject: the
laptop apparatus, never the beings.
"""
import glob, json, os, re, sys

def frames(session):
    out = {}
    for f in sorted(glob.glob(os.path.join(session, 'segments', '*.json'))):
        for ev in json.load(open(f))['segment']['events']:
            if ev['kind']['type'] == 'advanced':
                d = ev['kind']['data']; out[d['step']] = d
    return out

def journals(session):
    files = sorted(glob.glob(os.path.join(session, 'journals', '*.json')), key=lambda f: int(os.path.basename(f).split('-')[1]))
    return [json.load(open(f)) for f in files]

def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i]); r = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]: j += 1
        for k in range(i, j + 1): r[order[k]] = (i + j) / 2.0 + 1
        i = j + 1
    return r

def spearman(a, b):
    if len(a) < 3: return float('nan')
    ra, rb = ranks(a), ranks(b); ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else float('nan')

def main(sessions):
    for s in sessions:
        js = journals(s); fr = frames(s)
        effects = {d['application']['journalId']: d['entryEffect'] for d in fr.values() if d.get('application') and d.get('entryEffect')}
        label = os.path.join(os.path.basename(os.path.dirname(s.rstrip('/'))), os.path.basename(s.rstrip('/')))
        print(f"\nsession {label}: {len(js)} entries (n); prompt {js[0]['pending'].get('prompt', '')[:0]}{json.load(open(os.path.join(s, 'manifest.json')))['config']['promptVersion']}")
        print(f"{'step':>5} {'shown shift':>11} {'shown align':>11} {'own shift':>9} {'own align':>9} {'words':>5}  quotes")
        shown_shifts, next_words, quoting = [], [], 0
        for j in js:
            p = j['pending']; o = p['observation']; e = o.get('entryEffect'); text = p['entry']['text']; words = len(text.split())
            own = effects.get(p['entry']['id'])
            q = []
            if e:
                if f"{e['shift']:.2f}" in text: q.append('shift')
                if e.get('alignment') is not None and (f"{e['alignment']:+.2f}" in text or f"{e['alignment']:.2f}" in text): q.append('alignment')
                shown_shifts.append(e['shift']); next_words.append(words)
                if q: quoting += 1
            print(f"{o['step']:>5} {('%.3f' % e['shift']) if e else '-':>11} {('%+.3f' % e['alignment']) if e and e.get('alignment') is not None else '-':>11} {('%.3f' % own['shift']) if own else '-':>9} {('%+.3f' % own['alignment']) if own and own.get('alignment') is not None else '-':>9} {words:>5}  {','.join(q) or '-'}")
        owns = [v for v in effects.values()]
        if owns:
            sh = [v['shift'] for v in owns]; al = [v['alignment'] for v in owns if v.get('alignment') is not None]
            print(f"effects at application (n={len(sh)}): shift min {min(sh):.3f} median {sorted(sh)[len(sh)//2]:.3f} max {max(sh):.3f}" + (f"; alignment min {min(al):+.3f} median {sorted(al)[len(al)//2]:+.3f} max {max(al):+.3f} (n={len(al)})" if al else ''))
        if shown_shifts:
            print(f"entries shown an effect: {len(shown_shifts)}; quoting a shown number: {quoting} ({100.0*quoting/len(shown_shifts):.0f}%); Spearman(shown shift, that entry's words) = {spearman(shown_shifts, next_words):+.2f} (n={len(shown_shifts)})")
        else:
            print("no effect shown in this session (a no-effect pair)")

if __name__ == '__main__':
    main(sys.argv[1:])
