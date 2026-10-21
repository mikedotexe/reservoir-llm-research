#!/usr/bin/env python3
"""Offline test of a content-carrying reduction for My reservoir entries (S-010 Part B).

Inputs: one or more sustained session directories. For every retained entry the script
requests an embedding from the laptop's loopback Ollama (`nomic-embed-text`, 768 dims,
no task prefix), caches it beside the script's output directory, projects it to 32
coordinates with a fixed SplitMix64-seeded Gaussian matrix (Box–Muller from the same
generator the apparatus uses), and compares three representations of the same entries:
the apparatus' surface codec (`encodedFeatures`, first 32), the full embedding, and the
32-coordinate projection. Printed with n: consecutive-entry cosine per session, drift
from each session's first entry, matched-step cosine between sessions, and a tale/recital
contrast. Network: loopback only. Subject: the laptop apparatus, never the beings.
"""
import glob, hashlib, json, math, os, sys, urllib.request

ENDPOINT = 'http://127.0.0.1:11434/api/embed'
MODEL = 'nomic-embed-text'
MASK = (1 << 64) - 1
PROJECTION_SEED = 0x50524F4A45435433  # "PROJECT3"

class SplitMix64:
    def __init__(self, seed): self.state = seed & MASK
    def next_u64(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)
    def unit(self): return (self.next_u64() >> 11) * (1.0 / 9007199254740992.0)

def gaussian_matrix(rows, cols, seed):
    g = SplitMix64(seed); out = []
    for _ in range(rows):
        row = []
        while len(row) < cols:
            u1, u2 = max(g.unit(), 1e-300), g.unit()
            r = math.sqrt(-2.0 * math.log(u1))
            row.append(r * math.cos(2 * math.pi * u2)); row.append(r * math.sin(2 * math.pi * u2))
        out.append(row[:cols])
    return out

def embed(texts, cache):
    missing = [t for t in texts if hashlib.sha256(t.encode()).hexdigest() not in cache]
    for i in range(0, len(missing), 8):
        batch = missing[i:i + 8]
        req = urllib.request.Request(ENDPOINT, data=json.dumps({'model': MODEL, 'input': batch}).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.load(r)
        for t, e in zip(batch, d['embeddings']):
            cache[hashlib.sha256(t.encode()).hexdigest()] = e
    return [cache[hashlib.sha256(t.encode()).hexdigest()] for t in texts]

def cos(a, b):
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else float('nan')

def project(vec, matrix):
    scale = 1.0 / math.sqrt(len(matrix[0]))
    return [sum(m * v for m, v in zip(row, vec)) * scale for row in matrix]

def entries(session):
    files = sorted(glob.glob(os.path.join(session, 'journals', '*.json')), key=lambda f: int(os.path.basename(f).split('-')[1]))
    out = []
    for f in files:
        p = json.load(open(f))['pending']
        out.append((p['entry']['observedStep'], p['entry']['text'], p['encodedFeatures'][:32]))
    return out

def main(sessions, cache_path):
    cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    matrix = gaussian_matrix(32, 768, PROJECTION_SEED)
    data = {}
    for s in sessions:
        es = entries(s)
        vecs = embed([t for _, t, _ in es], cache)
        data[os.path.basename(s)] = [(step, text, codec, emb, project(emb, matrix)) for (step, text, codec), emb in zip(es, vecs)]
    json.dump(cache, open(cache_path, 'w'))
    print(f"embedding model {MODEL} · 768 dims · projection 32 x 768 Gaussian, seed {PROJECTION_SEED:#x}")
    for name, rows in data.items():
        n = len(rows)
        cc = [cos(rows[i][2], rows[i-1][2]) for i in range(1, n)]
        ce = [cos(rows[i][3], rows[i-1][3]) for i in range(1, n)]
        cp = [cos(rows[i][4], rows[i-1][4]) for i in range(1, n)]
        de = [cos(rows[i][3], rows[0][3]) for i in range(1, n)]
        dp = [cos(rows[i][4], rows[0][4]) for i in range(1, n)]
        print(f"\nsession {name}: {n} entries (n)")
        print("  consecutive cosine   surface codec  mean %.4f  min %.4f" % (sum(cc)/len(cc), min(cc)))
        print("                       embedding 768  mean %.4f  min %.4f" % (sum(ce)/len(ce), min(ce)))
        print("                       projection 32  mean %.4f  min %.4f" % (sum(cp)/len(cp), min(cp)))
        print("  cosine to first entry, by entry (embedding / projection):")
        print("    " + "  ".join(f"{rows[i][0]}:{de[i-1]:.2f}/{dp[i-1]:.2f}" for i in range(1, n)))
    names = list(data)
    if len(names) >= 2:
        a, b = data[names[-2]], data[names[-1]]
        print(f"\nmatched-step cosine, {names[-2]} vs {names[-1]} (surface / embedding / projection):")
        for x, y in zip(a, b):
            print(f"  step {x[0]:>3}: {cos(x[2], y[2]):.4f} / {cos(x[3], y[3]):.4f} / {cos(x[4], y[4]):.4f}")
    tale = "The traveler dives beneath the surface, joining the bioluminescent creatures in their aquatic dance."
    recital = "The recurrent state RMS of 0.26844701 suggests a moderate level of activity; the sensory fill at 94.31040364% indicates near-complete absorption."
    t, r = embed([tale, recital], cache)
    print(f"\ncontrast: tale vs recital sentence cosine  embedding {cos(t, r):.3f}  projection {cos(project(t, matrix), project(r, matrix)):.3f}")
    json.dump(cache, open(cache_path, 'w'))

if __name__ == '__main__':
    main(sys.argv[1:-1], sys.argv[-1])
