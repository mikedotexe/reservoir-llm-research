#!/usr/bin/env python3
"""Dimensionality of a being's reservoir-state window, read-only (spec M1 on minime).

Input: one or more `esn_state_window.bin` captures (rows × 128 little-endian f32, row-major,
as minime's engine writes to workspace/capacity/ every 30 s; copied read-only). Prints per
window, with n rows: state RMS, saturation share, effective rank (Roy–Vetterli), participation
ratio, k90/k95 from the PCA curve, and the temporal structure that separates dynamics from
noise: the lag-1 autocorrelation of the top principal-component scores and the share of
variance carried by components whose lag-1 autocorrelation exceeds 0.9 ("slow" variance).
A window of white noise has effective rank near its column count and no slow variance; a
window of slow dynamics has slow variance concentrated in few components. NumPy only.
Subject: minime's logged state, a steward instrument; never surfaced into a prompt.
"""
import glob, json, os, sys
import numpy as np

def analyse(path, cols=128):
    raw = np.fromfile(path, dtype='<f4')
    if raw.size % cols: return None
    X = raw.reshape(-1, cols).astype(np.float64); T = len(X)
    Xc = X - X.mean(0); U, s, Vt = np.linalg.svd(Xc, full_matrices=False); lam = s ** 2 / max(T - 1, 1)
    p = s / s.sum(); erank = float(np.exp(-(p * np.log(p)).sum())); pr = float(lam.sum() ** 2 / (lam ** 2).sum())
    cev = np.cumsum(lam) / lam.sum(); k90 = int(np.searchsorted(cev, 0.9) + 1); k95 = int(np.searchsorted(cev, 0.95) + 1)
    scores = U * s
    ac1 = np.array([np.corrcoef(scores[:-1, i], scores[1:, i])[0, 1] if s[i] > 0 else 0.0 for i in range(len(s))])
    slow = float(lam[ac1 > 0.9].sum() / lam.sum())
    return dict(rows=T, rms=float(np.sqrt((X ** 2).mean())), sat=float((np.abs(X) > 0.9).mean()), erank=erank, pr=pr, k90=k90, k95=k95,
                ac1_top=[float(a) for a in ac1[:5]], slow_share=slow, top5_share=float(cev[4]))

def main(argv):
    print(f"{'window':<30} {'rows':>5} {'rms':>6} {'sat':>5} {'erank':>6} {'PR':>5} {'k90':>4} {'k95':>4} {'top5%':>6} {'slow%':>6}  lag-1 autocorr of PC1..5")
    for path in argv:
        r = analyse(path)
        if not r: print(os.path.basename(path), 'unexpected size'); continue
        meta = path[:-4] + '.meta.json'; t = json.load(open(meta)).get('t_ms') if os.path.exists(meta) else None
        print(f"{os.path.basename(path)[:30]:<30} {r['rows']:>5} {r['rms']:>6.3f} {r['sat']:>5.2f} {r['erank']:>6.1f} {r['pr']:>5.1f} {r['k90']:>4} {r['k95']:>4} {100*r['top5_share']:>6.1f} {100*r['slow_share']:>6.1f}  " + ' '.join(f"{a:+.2f}" for a in r['ac1_top']) + (f"  t_ms {t}" if t else ''))

if __name__ == '__main__':
    main(sys.argv[1:])
