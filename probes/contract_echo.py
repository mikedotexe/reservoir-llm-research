#!/usr/bin/env python3
"""How much of a standing contract's own vocabulary comes back in the entries it governs.

Inputs: a contract name (PLAIN, INVITING, OPEN, INVITING_VARIED, read from the desktop
crate's frozen constants in crates/reservoir-core/src/sustained.rs) or `--file <path>` holding
any standing prompt text (for example a being's, copied read-only and kept private), and one
or more sources: Tauri sustained session directories (journals/*.json) or directories of
journal .txt files (headers and NEXT lines stripped as in introspection_markers.py). The contract's content words (lowercased,
stemmed crudely by stripping common suffixes, stopwords and short words removed) form the
echo set. Prints, per session: entries, words, the rate per 1,000 words of tokens whose
stem is in the echo set, the number of distinct contract stems that appear, and the ten
most frequent echoed stems. Run the same contract against a no-contract session to get the
model's baseline rate for those words. These are word counts, not judgments. Standard
library only; read-only.
"""
import glob, json, os, re, sys
from collections import Counter

STOP = set("""a an the and or but if then so of to in on at by for from with without as is are was were be been
being have has had do does did not no nor your you yours yourself it its itself this that these those which
who whom what when where how may might can could would should shall will there here than too very also any
some such own same other each either neither both all more most much many few less least into onto over
under again further once only ever never about above below between through during before after up down out
off just still yet while whether because though although even itself they them their themselves we our ours
us i me my mine he she his her him one ones thing things way ways""".split())
SUFFIXES = ('ations', 'ation', 'ingly', 'ness', 'ments', 'ment', 'ings', 'ing', 'edly', 'ies', 'ied', 'ers', 'er', 'ed', 'es', 's', 'ly')

def stem(w):
    for suf in SUFFIXES:
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[:-len(suf)]
    return w

def tokens(text):
    return [w.replace('’', "'") for w in re.findall(r"[A-Za-z'’]+", text.lower())]

def contract_text(name):
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'desktop', 'ReservoirScope', 'crates', 'reservoir-core', 'src', 'sustained.rs')
    const = {'PLAIN': 'PLAIN_CONTRACT_V1', 'INVITING': 'INVITING_CONTRACT_V1', 'OPEN': 'OPEN_CONTRACT_V1', 'INVITING_VARIED': 'INVITING_VARIED_CONTRACT_V1'}[name]
    m = re.search(r'pub const ' + const + r': &str = "((?:[^"\\]|\\.)*)";', open(src, encoding='utf-8').read())
    return m.group(1).encode().decode('unicode_escape')

def echo_set(text):
    return {stem(w) for w in tokens(text) if w not in STOP and len(w) > 3}

HEADER = re.compile(r"^(=== .* ===|Source revision:|Input evidence:|Account:|Delivery:|Mode:|Timestamp:|Fill:|Revised from:|NEXT:|--- .* ---|\[(Agency-vernacular|Pressure-vocabulary)[^\]]*\])")

def load(session):
    if os.path.isdir(os.path.join(session, 'journals')):
        files = sorted(glob.glob(os.path.join(session, 'journals', '*.json')), key=lambda f: int(os.path.basename(f).split('-')[1]))
        return [json.load(open(f))['pending']['entry']['text'] for f in files]
    texts = []
    for f in sorted(glob.glob(os.path.join(session, '*.txt'))):
        kept = [line for line in open(f, encoding='utf-8', errors='replace').read().splitlines() if not HEADER.match(line.strip())]
        t = '\n'.join(kept).strip()
        if t: texts.append(t)
    return texts

def main(argv):
    if argv[0] == '--file':
        name, contract, sessions = os.path.basename(argv[1]), open(argv[1], encoding='utf-8').read(), argv[2:]
    else:
        name, sessions = argv[0].upper(), argv[1:]
        contract = contract_text(name)
    echo = echo_set(contract)
    print(f"contract {name}: {len(tokens(contract))} words, {len(echo)} content stems")
    print(f"{'session':<44} {'n':>3} {'words':>6} {'echo/1000':>9} {'stems':>5}  top echoed stems")
    for s in sessions:
        texts = load(s); toks = [w for t in texts for w in tokens(t)]
        hits = Counter(stem(w) for w in toks if stem(w) in echo and w not in STOP and len(w) > 3)
        label = os.path.join(os.path.basename(os.path.dirname(s.rstrip('/'))), os.path.basename(s.rstrip('/')))[-44:]
        top = ', '.join(f"{k} {v}" for k, v in hits.most_common(10))
        print(f"{label:<44} {len(texts):>3} {len(toks):>6} {1000.0 * sum(hits.values()) / max(len(toks), 1):>9.1f} {len(hits):>5}  {top}")

if __name__ == '__main__':
    main(sys.argv[1:])
