#!/usr/bin/env python3
"""Replay the Tauri My reservoir sensory field offline and test feedback policies on fill.

Input: a sustained session directory (see desktop_session_overlap.py). Reads the step-0
checkpoint, every recorded frame and every journal's semantic vector. Re-implements
SensoryField::step, ReducedFill, RetentionController and forcing() from
desktop/ReservoirScope/crates/reservoir-core/src/math.rs (0.27.1) in Python with NumPy
(NumPy is used only for the symmetric eigenvalues; nalgebra does the same in Rust).

First it replays the recorded session (held vectors applied at their recorded steps) and
prints recorded vs replayed fill at each writing step as a fidelity check. Then it replays
the same session under alternative feedback policies: scaled held vectors, a one-step or
three-step pulse, exponential decay, and no feedback. The reservoir itself is not replayed;
it does not feed the sensory field. Subject: the laptop app's apparatus, never the beings.
"""
import glob, json, math, os, sys
import numpy as np

MASK = (1 << 64) - 1
FIELD_SEED = 0x53454E534F5259

class SplitMix64:
    def __init__(self, seed): self.state = seed & MASK
    def next_u64(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)
    def unit(self): return (self.next_u64() >> 11) * (1.0 / 9007199254740992.0)
    def signed(self): return 2.0 * self.unit() - 1.0

def forcing(step, dt):
    x = np.zeros(66)
    if (step - 1) % 30 >= 12: return x
    t = (step - 1) * dt
    for i in range(8): x[i] = 0.45 + 0.35 * math.sin(t * (0.19 + i * 0.07) + i)
    for i in range(8, 16): x[i] = 0.3 + 0.25 * math.sin(t * (0.31 + (i - 8) * 0.11) + i * 0.7)
    return x

SCALE = np.array([0.75] * 8 + [0.72] * 8 + [1.12] * 2 + [0.42] * 48)

class Field:
    def __init__(self, projection, covariance):
        self.P = projection.reshape(32, 66); self.C = covariance.reshape(32, 32).copy()
    def step(self, inp, r):
        a = np.tanh(inp * SCALE * 0.58)
        z = self.P @ a / math.sqrt(66)
        rms = math.sqrt(float(z @ z) / 32)
        z = z / rms if rms > 1e-12 else np.zeros(32)
        nxt = r * self.C + (1 - r) * np.outer(z, z)
        tr = float(np.trace(nxt))
        if rms > 1e-12 and tr > 1e-12: nxt *= min(32 / tr, 2.0)
        self.C = nxt
        ev = np.clip(np.linalg.eigvalsh(nxt)[::-1], 0, None)
        return ev, z

def fill_update(fill, ev, dt):
    mean = float(np.clip(ev, 0, None).mean())
    active = int((np.clip(ev, 0, None) > 0.12 * mean).sum()) if mean > 1e-12 else 0
    inst = max(active / len(ev), 0.04) if active > 0 else 0.0
    return min(max(0.10 * inst + 0.90 * (1.0 - min(0.006 * dt, 0.15)) * fill, 0.0), 1.0)

def controller_update(ret, integ, fill_pct):
    error = fill_pct - 68.0
    e = (-1.0 if error < 0 else 1.0) * max(abs(error) - 4.0, 0.0) / 20.0
    tentative = min(max(0.85 * integ + e, -1.0), 1.0)
    u = min(max(0.55 * e + 0.04 * tentative, -0.12), 0.12)
    requested = min(max(0.955 - u, 0.82), 0.995)
    if (requested <= 0.82 and e > 0) or (requested >= 0.995 and e < 0): integ *= 0.85
    else: integ = tentative
    ret += min(max(requested - ret, -0.01), 0.01)
    return ret, integ

def load(session):
    segs = sorted(glob.glob(os.path.join(session, 'segments', '*.json')),
                  key=lambda f: int(os.path.basename(f).split('-')[1].split('.')[0]))
    first = json.load(open(segs[0]))['segment']['initialCheckpoint']['state']
    frames = {}
    for f in segs:
        for ev in json.load(open(f))['segment']['events']:
            if ev['kind']['type'] == 'advanced':
                d = ev['kind']['data']; frames[d['step']] = d
    journals = sorted(glob.glob(os.path.join(session, 'journals', '*.json')),
                      key=lambda f: int(os.path.basename(f).split('-')[1]))
    vectors = {}
    for f in journals:
        p = json.load(open(f))['pending']
        vectors[p['entry']['observedStep'] + 1] = np.array(p['semanticVector'])
    manifest = json.load(open(os.path.join(session, 'manifest.json')))
    return first, frames, vectors, manifest

def replay(first, vectors, projection, steps, dt, regulation, policy, scale=1.0, hold=None, decay=None,
           sensory_noise=0.0, forcing_always=False, fixed_retention=None, noise_seed=1):
    field = Field(projection, np.array(first['sensoryCovariance']))
    fill, ret, integ = first['reducedFill'], first['retention'], first['controllerIntegral']
    if fixed_retention is not None: ret, regulation = fixed_retention, False
    nrng = np.random.default_rng(noise_seed)
    held = np.zeros(48); since = None; last_vec = None; out = {}
    for step in range(1, steps + 1):
        if step in vectors:
            last_vec = vectors[step] * scale; held = last_vec.copy(); since = 0
        elif step > max(vectors) and (step - 1) % 30 == 0 and last_vec is not None:
            held = last_vec.copy(); since = 0          # keep re-applying the last vector each cycle
        elif since is not None:
            since += 1
            if policy == 'pulse' and since >= hold: held = np.zeros(48)
            if policy == 'decay': held = held * decay
        inp = forcing(((step - 1) % 30) + 1, dt) if forcing_always else forcing(step, dt); inp[18:] = held
        if sensory_noise > 0: inp = inp + nrng.uniform(-1, 1, 66) * sensory_noise
        ev, _ = field.step(inp, ret)
        fill = fill_update(fill, ev, dt)
        if regulation: ret, integ = controller_update(ret, integ, 100 * fill)
        out[step] = (100 * fill, ret)
    return out

def main(session, horizon=420):
    first, frames, vectors, manifest = load(session)
    cfg = manifest['config']; seed = int(cfg['seed']); dt = frames[1]['simulatedTime']
    rng = SplitMix64(seed ^ FIELD_SEED); projection = np.array([rng.signed() for _ in range(2112)])
    print(f"session {manifest['sessionId']} · seed {seed} · dt {dt:.6f} · regulation {cfg['regulationEnabled']} · recorded steps {len(frames)} · journals {len(vectors)}  (n)")
    rec = replay(first, vectors, projection, max(frames), dt, cfg['regulationEnabled'], 'held')
    print("\nfidelity: step  recorded_fill  replayed_fill  recorded_ret  replayed_ret")
    worst = 0.0
    for s in sorted(frames):
        fr = frames[s]; rf = fr['sensory']['fillPercent']; pf = rec[s][0]
        worst = max(worst, abs(rf - pf))
        if s % 30 in (0, 1) or s in (1, 2, 5, 15): print(f"          {s:>4}  {rf:>13.4f}  {pf:>13.4f}  {fr['nextRetention']:>12.4f}  {rec[s][1]:>12.4f}")
    print(f"largest |recorded - replayed| fill over all {len(frames)} steps: {worst:.4f} points")
    print(f"\npolicies, replayed to step {horizon} (last journal vector re-applied every 30 steps after the recorded ones):")
    print("policy            fill@60  fill@120  fill@210  fill@300  fill@420  mean300-420  ret@420")
    variants = [('held ×1.00 (as built)', dict(policy='held', scale=1.0)), ('held ×0.50', dict(policy='held', scale=0.5)),
                ('held ×0.25', dict(policy='held', scale=0.25)), ('held ×0.10', dict(policy='held', scale=0.1)),
                ('held ×0.05', dict(policy='held', scale=0.05)), ('no feedback', dict(policy='held', scale=0.0)),
                ('pulse 1 step', dict(policy='pulse', scale=1.0, hold=1)), ('pulse 3 steps', dict(policy='pulse', scale=1.0, hold=3)),
                ('decay 0.80/step', dict(policy='decay', scale=1.0, decay=0.8)), ('decay 0.95/step', dict(policy='decay', scale=1.0, decay=0.95))]
    for name, kw in variants:
        o = replay(first, vectors, projection, horizon, dt, cfg['regulationEnabled'], **kw)
        m = sum(o[s][0] for s in range(300, horizon + 1)) / (horizon - 299)
        print(f"{name:<18}  {o[60][0]:>7.2f}  {o[120][0]:>8.2f}  {o[210][0]:>8.2f}  {o[300][0]:>8.2f}  {o[420][0]:>8.2f}  {m:>11.2f}  {o[420][1]:>7.3f}")
    hypothetical(first, vectors, projection, dt, horizon)

def hypothetical(first, vectors, projection, dt, horizon=420):
    print(f"\nhypothetical apparatus changes, not available in the app (held ×1.00 unless stated), to step {horizon}:")
    print("variant                                  fill@60  fill@120  fill@210  fill@300  fill@420  mean300-420  ret@420")
    variants = [('fixed retention 0.995, no regulation', dict(policy='held', fixed_retention=0.995)),
                ('fixed retention 0.98, no regulation', dict(policy='held', fixed_retention=0.98)),
                ('forcing on every step', dict(policy='held', forcing_always=True)),
                ('sensory noise 0.05 on all 66 inputs', dict(policy='held', sensory_noise=0.05)),
                ('sensory noise 0.10', dict(policy='held', sensory_noise=0.10)),
                ('sensory noise 0.20', dict(policy='held', sensory_noise=0.20)),
                ('sensory noise 0.40', dict(policy='held', sensory_noise=0.40)),
                ('sensory noise 0.20 + held ×0.25', dict(policy='held', scale=0.25, sensory_noise=0.20)),
                ('sensory noise 0.20, no feedback', dict(policy='held', scale=0.0, sensory_noise=0.20)),
                ('sensory noise 0.20 + forcing every step', dict(policy='held', sensory_noise=0.20, forcing_always=True))]
    for name, kw in variants:
        o = replay(first, vectors, projection, horizon, dt, True, **kw)
        m = sum(o[s][0] for s in range(300, horizon + 1)) / (horizon - 299)
        print(f"{name:<40} {o[60][0]:>7.2f}  {o[120][0]:>8.2f}  {o[210][0]:>8.2f}  {o[300][0]:>8.2f}  {o[420][0]:>8.2f}  {m:>11.2f}  {o[420][1]:>7.3f}")

if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 420)
