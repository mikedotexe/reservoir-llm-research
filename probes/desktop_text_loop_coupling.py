#!/usr/bin/env python3
"""Trace the text feedback loop of two Tauri My reservoir sessions that share seed, field
noise and forcing and differ only in the text that fed back (e.g. greedy vs sampled).

Inputs: two session directories A and B (see desktop_session_overlap.py).
Prints, with n: (1) how far the two sessions' reservoir state and readouts diverge at the
same steps, i.e. how much the differing text moved the numbers; (2) the one-step state kick
at each feedback application against the median step; (3) selected codec features per
entry (digits, hedges, first person, questions, curiosity, reflection, length) and the
cosine between consecutive and between matched entries; (4) whether each entry quotes the
readout values it was shown. Standard library only. Subject: the laptop apparatus.
"""
import glob, json, math, os, re, sys

NAMES = {3: 'digits', 9: 'hedge', 12: 'first-person', 18: 'questions', 26: 'curiosity', 27: 'reflection', 30: 'length'}

def frames(session):
    out = {}
    for f in sorted(glob.glob(os.path.join(session, 'segments', '*.json'))):
        for ev in json.load(open(f))['segment']['events']:
            if ev['kind']['type'] == 'advanced':
                d = ev['kind']['data']; out[d['step']] = d
    return out

def journals(session):
    files = sorted(glob.glob(os.path.join(session, 'journals', '*.json')),
                   key=lambda f: int(os.path.basename(f).split('-')[1]))
    return [json.load(open(f)) for f in files]

def rms(v): return math.sqrt(sum(x * x for x in v) / len(v))
def l2(a, b): return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
def cos(a, b):
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else float('nan')

def main(a, b):
    fa, fb = frames(a), frames(b)
    common = sorted(set(fa) & set(fb))
    print(f"shared steps: {len(common)}  (n)")
    after = [s for s in common if s > 30]
    dfill = [abs(fa[s]['sensory']['fillPercent'] - fb[s]['sensory']['fillPercent']) for s in after]
    drms = [abs(rms(fa[s]['state']) - rms(fb[s]['state'])) for s in after]
    dstate = [l2(fa[s]['state'], fb[s]['state']) for s in after]
    print("divergence between sessions at the same step, steps 31..%d (n=%d):" % (after[-1], len(after)))
    print(f"  |fill A - fill B|   max {max(dfill):.3f} pts  mean {sum(dfill)/len(dfill):.3f}")
    print(f"  |RMS A - RMS B|     max {max(drms):.4f}      mean {sum(drms)/len(drms):.4f}")
    print(f"  state L2 A vs B     max {max(dstate):.4f}      mean {sum(dstate)/len(dstate):.4f}   (state RMS itself is ~0.5)")
    for name, fr in (('A', fa), ('B', fb)):
        steps = sorted(fr)
        kicks = [l2(fr[s]['state'], fr[s - 1]['state']) for s in steps if s > 1]
        med = sorted(kicks)[len(kicks) // 2]
        apps = [(s, l2(fr[s]['state'], fr[s - 1]['state'])) for s in steps if s > 1 and fr[s]['application']]
        print(f"session {name}: median one-step state change {med:.4f}; at feedback applications: " + ", ".join(f"step {s}: {k:.3f}" for s, k in apps[:6]))
    for name, session in (('A', a), ('B', b)):
        js = journals(session)
        print(f"\nsession {name} entries (n={len(js)}): selected codec features (x2 scaled, ±5 clamp) and readout quoting")
        print("step  " + "  ".join(f"{NAMES[i]:>12}" for i in NAMES) + "   cos(prev)  quotes fill  quotes RMS")
        prev = None
        for j in js:
            p = j['pending']; e = p['entry']; v = p['encodedFeatures']
            m1 = re.search(r'fill \(%\): current ([0-9.]+)', p['prompt']); m2 = re.search(r'RMS: current ([0-9.]+)', p['prompt'])
            q1 = m1 and m1.group(1) in e['text']; q2 = m2 and m2.group(1) in e['text']
            c = cos(v, prev) if prev else float('nan')
            print(f"{e['observedStep']:>4}  " + "  ".join(f"{v[i]:>12.3f}" for i in NAMES) + f"   {c:>8.4f}  {str(bool(q1)):>11}  {str(bool(q2)):>10}")
            prev = v
    ja, jb = journals(a), journals(b)
    print("\ncosine of matched entries across sessions (same step, different text):")
    for x, y in zip(ja, jb):
        print(f"  step {x['pending']['entry']['observedStep']:>3}: {cos(x['pending']['encodedFeatures'], y['pending']['encodedFeatures']):.4f}")

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
