#!/usr/bin/env python3
"""Effective rank and participation ratio of the laptop apparatus, per session, against fill.

Inputs: Tauri sustained session directories (segments/*.json hold every frame: the 32-d
recurrent state, the 32 sensory-field eigenvalues, fill, retention, application marks).
For each session: (1) the field's effective rank (Roy–Vetterli: exp of the entropy of the
normalised eigenvalues) and participation ratio ((Σλ)²/Σλ²) per frame, straight from the
recorded eigenvalues, with fill, so the apparatus's "fill" can be read in rank units;
(2) the recurrent state's effective rank and participation ratio over sliding windows of
W steps (centred state matrix), binned by the window's mean fill. Prints medians per fill
bin with n. The recurrent reservoir does not receive the field, so by construction its
rank need not track fill; the probe measures whether it does anyway. Standard library plus
NumPy (SVD). Subject: the laptop apparatus, never the beings.
"""
import glob, json, os, sys
import numpy as np

def frames(session):
    out = {}
    for f in sorted(glob.glob(os.path.join(session, 'segments', '*.json'))):
        for ev in json.load(open(f))['segment']['events']:
            if ev['kind']['type'] == 'advanced':
                d = ev['kind']['data']; out[d['step']] = d
    return [out[k] for k in sorted(out)]

def erank_from_values(v):
    v = np.clip(np.asarray(v, float), 0, None); s = v.sum()
    if s <= 0: return float('nan')
    p = v / s; p = p[p > 0]
    return float(np.exp(-(p * np.log(p)).sum()))

def pr_from_values(v):
    v = np.clip(np.asarray(v, float), 0, None)
    return float(v.sum() ** 2 / (v ** 2).sum()) if (v ** 2).sum() > 0 else float('nan')

def window_ranks(X):
    Xc = X - X.mean(0); s = np.linalg.svd(Xc, compute_uv=False)
    lam = s ** 2 / max(len(X) - 1, 1)
    return erank_from_values(s), pr_from_values(lam)

def main(argv):
    W = 64
    for s in argv:
        fr = frames(s); fills = np.array([d['sensory']['fillPercent'] for d in fr])
        field_er = np.array([erank_from_values(d['sensory']['eigenvalues']) for d in fr])
        field_pr = np.array([pr_from_values(d['sensory']['eigenvalues']) for d in fr])
        X = np.array([d['state'] for d in fr])
        label = os.path.join(os.path.basename(os.path.dirname(s.rstrip('/'))), os.path.basename(s.rstrip('/')))
        print(f"\nsession {label}: {len(fr)} frames (n); fill min {fills.min():.1f} median {np.median(fills):.1f} max {fills.max():.1f}")
        print("  field (32 eigenvalues per frame): fill bin → median effective rank / participation ratio (n frames)")
        for lo in range(0, 100, 10):
            m = (fills >= lo) & (fills < lo + 10)
            if m.sum() >= 20:
                print(f"    {lo:>2}–{lo+10:<3}%  erank {np.median(field_er[m]):5.2f}  PR {np.median(field_pr[m]):5.2f}  (n={m.sum()})")
        ers, prs, wf = [], [], []
        for a in range(0, len(X) - W + 1, W // 2):
            er, pr = window_ranks(X[a:a + W]); ers.append(er); prs.append(pr); wf.append(fills[a:a + W].mean())
        ers, prs, wf = map(np.array, (ers, prs, wf))
        print(f"  recurrent state, {W}-step windows (n={len(ers)}): erank median {np.median(ers):.2f} (min {ers.min():.2f} max {ers.max():.2f}); PR median {np.median(prs):.2f}")
        for lo in range(0, 100, 10):
            m = (wf >= lo) & (wf < lo + 10)
            if m.sum() >= 3:
                print(f"    fill {lo:>2}–{lo+10:<3}%  state erank {np.median(ers[m]):5.2f}  PR {np.median(prs[m]):5.2f}  (n={m.sum()} windows)")
        apps = [i for i, d in enumerate(fr) if d.get('application')]
        if apps:
            near = [window_ranks(X[max(0, i - 8):i + 24])[0] for i in apps if i + 24 <= len(X)]
            print(f"  state erank in 32-step windows around applications: median {np.median(near):.2f} (n={len(near)})")

if __name__ == '__main__':
    main(sys.argv[1:])
