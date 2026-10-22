#!/usr/bin/env python3
"""Read the difference-signal ladder (S-011 M5): what a gain did against its gain-0 twin.

Inputs: `--twin <session dir>` (the gain-0 run at the same seed and regulation) and one or
more session directories with a nonzero gain (desktop 0.35.0 stores: segments/*.json hold
every frame with `differenceInput`, `differenceGainUsed`, `differenceGainDropped`, the
state, fill, retention, and `entryEffect` on application frames; manifest.json holds the
config). Per session it prints, with n: the config echo; fill min/median/max, its standard
deviation and the largest trailing-90-step standard deviation; a spectrum of the fill
series over non-overlapping 90-step windows (mean removed, rfft, power averaged; the top
three periods and the power share at periods shorter than 30 steps); the retention
actuation rate (share of steps that changed retention, mean |Δ|); the recurrent state's
effective rank and participation ratio over 64-step windows; entry-effect shift and
alignment summaries; the channel's own contribution (RMS per step, share of dead-band-silent
steps, clip hits); watchdog drops; and a fidelity check that recomputes the contribution
from the recorded states with the same matrix recipe (SplitMix64, Box–Muller) and reports
the largest discrepancy. Then the deltas against the twin. `--calibrate <gain-0 session dirs>`
instead prints the noise floor of the filtered motion d_f those runs would have produced and the
spec's implied dead band δ = 2 × RMS (step 0 of the ladder). NumPy only. Subject: the laptop
apparatus, never the beings.
"""
import glob, json, math, os, sys
import numpy as np

MASK = (1 << 64) - 1
DIFFERENCE_SEED = 0x0044494646455245

class SplitMix64:
    def __init__(self, seed): self.state = seed & MASK
    def next_u64(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK; z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK; z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)
    def unit(self): return (self.next_u64() >> 11) * (1.0 / 9007199254740992.0)

def difference_matrix(seed):
    rng = SplitMix64(seed); out = []; scale = 1.0 / math.sqrt(32)
    while len(out) < 48 * 32:
        u1 = max(rng.unit(), 1e-300); u2 = rng.unit(); r = math.sqrt(-2.0 * math.log(u1))
        out.append(r * math.cos(2 * math.pi * u2) * scale); out.append(r * math.sin(2 * math.pi * u2) * scale)
    return np.array(out).reshape(48, 32)

def frames(session):
    out = {}
    for f in sorted(glob.glob(os.path.join(session, 'segments', '*.json'))):
        for ev in json.load(open(f))['segment']['events']:
            if ev['kind']['type'] == 'advanced':
                d = ev['kind']['data']; out[d['step']] = d
    return [out[k] for k in sorted(out)]

def erank(values):
    v = np.clip(np.asarray(values, float), 0, None); s = v.sum()
    if s <= 0: return float('nan')
    p = v / s; p = p[p > 0]; return float(np.exp(-(p * np.log(p)).sum()))

def window_ranks(X):
    Xc = X - X.mean(0); s = np.linalg.svd(Xc, compute_uv=False); lam = s ** 2 / max(len(X) - 1, 1)
    return erank(s), float(lam.sum() ** 2 / (lam ** 2).sum()) if (lam ** 2).sum() > 0 else float('nan')

def spectrum(fill, W=90):
    windows = [fill[a:a + W] for a in range(0, len(fill) - W + 1, W)]
    if not windows: return None
    power = np.zeros(W // 2 + 1)
    for w in windows:
        w = np.asarray(w) - np.mean(w); power += np.abs(np.fft.rfft(w)) ** 2
    power /= len(windows); freqs = np.fft.rfftfreq(W, d=1.0)
    order = np.argsort(power[1:])[::-1][:3] + 1
    top = [(1.0 / freqs[i], power[i]) for i in order]
    short = power[freqs > 1.0 / 30.0].sum() / power[1:].sum() if power[1:].sum() > 0 else float('nan')
    return top, short, len(windows)

def analyse(session):
    fr = frames(session); cfg = json.load(open(os.path.join(session, 'manifest.json')))['config']
    seed = int(cfg['seed']); gain = cfg.get('differenceGain', 0.0); tau = cfg.get('differenceTau', 3.0); band = cfg.get('differenceDeadBand', 0.02); clip = cfg.get('differenceClip', 0.2)
    fill = np.array([d['sensory']['fillPercent'] for d in fr]); X = np.array([d['state'] for d in fr])
    trailing = [fill[a:a + 90].std() for a in range(0, len(fill) - 90 + 1)]
    ret = np.array([d['nextRetention'] - d['retentionUsed'] for d in fr])
    ranks = [window_ranks(X[a:a + 64]) for a in range(0, len(X) - 64 + 1, 32)]
    effects = [d['entryEffect'] for d in fr if d.get('application') and d.get('entryEffect')]
    contributions = [np.array(d['differenceInput']) for d in fr if d.get('differenceInput')]
    drops = [(d['step'], d['differenceGainDropped']['reason'][:12]) for d in fr if d.get('differenceGainDropped')]
    # fidelity: recompute d_f and u from recorded states; observation steps are multiples of turnEvery below maximumSteps
    fidelity = float('nan')
    if gain != 0.0 and contributions:
        W = difference_matrix((seed ^ DIFFERENCE_SEED) & MASK); turn = cfg['turnEvery']; max_steps = cfg['maximumSteps']
        d_f = np.zeros(32); ref = np.zeros(32); ref_step = 0; worst = 0.0; active = True; prev_state = np.zeros(32)
        for d in fr:
            step = d['step']
            if not active or not d.get('differenceInput'):
                if d.get('differenceGainDropped'): active = False
                prev_state = np.array(d['state']); continue
            elapsed = step - 1 - ref_step
            raw = np.zeros(32) if elapsed == 0 else (prev_state - ref) / elapsed
            d_f = d_f + (raw - d_f) / (tau + 1.0)
            banded = np.where(d_f > band, d_f - band, np.where(d_f < -band, d_f + band, 0.0))
            u = np.clip(gain * (W @ banded), -clip, clip)
            worst = max(worst, float(np.max(np.abs(u - np.array(d['differenceInput'])))))
            if d.get('differenceGainDropped'): active = False
            prev_state = np.array(d['state'])
            if step % turn == 0 and step < max_steps and active:
                ref = prev_state.copy(); ref_step = step
        fidelity = worst
    return dict(name=os.path.basename(os.path.dirname(session.rstrip('/'))), gain=gain, regulation=cfg['regulationEnabled'], retention=cfg['initialRetention'], seed=seed, n=len(fr),
                fill_min=fill.min(), fill_med=float(np.median(fill)), fill_max=fill.max(), fill_std=fill.std(), trailing_max=max(trailing) if trailing else float('nan'),
                spectrum=spectrum(fill), act_rate=float((ret != 0).mean()), act_mean=float(np.abs(ret).mean()),
                erank=float(np.median([r[0] for r in ranks])), pr=float(np.median([r[1] for r in ranks])),
                shift=[e['shift'] for e in effects], align=[e['alignment'] for e in effects if e.get('alignment') is not None],
                u_rms=float(np.sqrt(np.mean([float((c ** 2).mean()) for c in contributions]))) if contributions else 0.0,
                silent=float(np.mean([bool(np.all(c == 0)) for c in contributions])) if contributions else float('nan'),
                clip_hits=int(sum(int(np.sum(np.abs(c) >= clip - 1e-12)) for c in contributions)), drops=drops, fidelity=fidelity)

def show(r, twin=None):
    sp = r['spectrum']; tops = ' '.join(f"{p:.0f}-step" for p, _ in sp[0]) if sp else '-'
    print(f"\n{r['name']}: gain {r['gain']:+.2f} · regulation {'on' if r['regulation'] else 'off'} (retention {r['retention']}) · seed {r['seed']} · {r['n']} frames (n)")
    print(f"  fill min/median/max {r['fill_min']:.1f}/{r['fill_med']:.1f}/{r['fill_max']:.1f} · std {r['fill_std']:.2f} · max trailing-90 std {r['trailing_max']:.2f} · top periods {tops} · short-period share {sp[1]:.2f} (windows {sp[2]})" if sp else "  no spectrum")
    print(f"  retention actuation: {100*r['act_rate']:.0f}% of steps, mean |Δ| {r['act_mean']:.4f} · state erank {r['erank']:.2f} PR {r['pr']:.2f}")
    if r['shift']: print(f"  entry effect: shift median {np.median(r['shift']):.3f} (n={len(r['shift'])}) · alignment median {np.median(r['align']):+.3f} (n={len(r['align'])})" if r['align'] else f"  entry effect: shift median {np.median(r['shift']):.3f} (n={len(r['shift'])})")
    if r['gain'] != 0.0: print(f"  channel: contribution RMS {r['u_rms']:.4f} · dead-band-silent steps {100*r['silent']:.0f}% · clip hits {r['clip_hits']} · watchdog drops {r['drops'] or 'none'} · recompute max |Δ| {r['fidelity']:.2e}")
    if twin:
        print(f"  vs twin: fill std {r['fill_std'] - twin['fill_std']:+.2f} · trailing-90 std {r['trailing_max'] - twin['trailing_max']:+.2f} · short-period share {(r['spectrum'][1] - twin['spectrum'][1]) if r['spectrum'] and twin['spectrum'] else float('nan'):+.2f} · actuation {100*(r['act_rate'] - twin['act_rate']):+.0f} pts · erank {r['erank'] - twin['erank']:+.2f} · PR {r['pr'] - twin['pr']:+.2f}" + (f" · shift median {np.median(r['shift']) - np.median(twin['shift']):+.3f}" if r['shift'] and twin['shift'] else ''))

def filtered_motion(session, tau=None):
    """The filtered motion d_f the channel would compute from this session's recorded states (the
    recursion of the fidelity check, at any gain): rows are steps, columns the 32 coordinates."""
    fr = frames(session); cfg = json.load(open(os.path.join(session, 'manifest.json')))['config']
    tau = cfg.get('differenceTau', 3.0) if tau is None else tau; turn = cfg['turnEvery']; max_steps = cfg['maximumSteps']
    d_f = np.zeros(32); ref = np.zeros(32); ref_step = 0; prev_state = np.zeros(32); rows = []
    for d in fr:
        step = d['step']; elapsed = step - 1 - ref_step
        raw = np.zeros(32) if elapsed == 0 else (prev_state - ref) / elapsed
        d_f = d_f + (raw - d_f) / (tau + 1.0); rows.append(d_f.copy()); prev_state = np.array(d['state'])
        if step % turn == 0 and step < max_steps: ref = prev_state.copy(); ref_step = step
    return np.array(rows), cfg

def longest_run(flags):
    best = run = 0
    for f in flags:
        run = run + 1 if f else 0; best = max(best, run)
    return best

def watchdog_baseline(session):
    """What the three watchdog rules would have seen on this run: the largest trailing-90-step fill
    standard deviation (ring full) with the step it ends at, and the largest over windows ending after
    step 180 (past the start-up climb); the longest run of steps with fill outside 15–98%; the largest
    count of nodes beyond |x| > 0.95 and the longest run of steps with more than 16 such nodes."""
    fr = frames(session); fill = np.array([d['sensory']['fillPercent'] for d in fr]); X = np.array([d['state'] for d in fr])
    trailing = [(fill[a:a + 90].std(), a + 90) for a in range(0, len(fill) - 90 + 1)]
    worst = max(trailing) if trailing else (float('nan'), 0); late = [t for t in trailing if t[1] > 180]; worst_late = max(late) if late else (float('nan'), 0)
    sat = (np.abs(X) > 0.95).sum(1)
    return (f"watchdog baseline: max trailing-90 fill std {worst[0]:.2f} (window ending step {worst[1]}), after step 180 {worst_late[0]:.2f} (ending step {worst_late[1]})"
            f" · longest run outside 15–98% fill {longest_run((fill < 15) | (fill > 98))} steps · max saturated nodes {int(sat.max())}, longest run with more than 16: {longest_run(sat > 16)} steps")

def calibrate(sessions, band=0.02):
    """The spec's dead-band rule: δ = 2 × the noise floor of d_f measured at gain 0. Per gain-0
    session: the RMS of d_f over all steps and coordinates, the per-coordinate RMS range, the share of
    coordinate-steps beyond the current band, the implied δ; then the pooled values."""
    pooled = []
    for s in sessions:
        M, cfg = filtered_motion(s); pooled.append(M)
        rms = float(np.sqrt((M ** 2).mean())); per = np.sqrt((M ** 2).mean(0)); beyond = float((np.abs(M) > band).mean())
        print(f"{os.path.basename(os.path.dirname(s.rstrip('/')))}: gain {cfg.get('differenceGain', 0.0):+.2f} · {len(M)} steps (n) · d_f RMS {rms:.4f} · per-coordinate RMS {per.min():.4f}–{per.max():.4f} · |d_f| > {band} on {100*beyond:.1f}% of coordinate-steps · implied δ = 2×RMS = {2*rms:.4f}")
        print("  " + watchdog_baseline(s))
    if pooled:
        M = np.concatenate(pooled); rms = float(np.sqrt((M ** 2).mean()))
        print(f"pooled: {len(M)} steps (n) · d_f RMS {rms:.4f} · implied δ {2*rms:.4f} · |d_f| > {band} on {100*float((np.abs(M) > band).mean()):.1f}% of coordinate-steps")

def main(argv):
    if argv and argv[0] == '--calibrate':
        calibrate(argv[1:]); return
    twin = None
    if argv and argv[0] == '--twin':
        twin = analyse(argv[1]); show(twin); argv = argv[2:]
    for s in argv: show(analyse(s), twin)

if __name__ == '__main__':
    main(sys.argv[1:])
