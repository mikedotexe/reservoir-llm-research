#!/usr/bin/env python3
"""Surface markers of an introspective register, counted the same way on any set of texts.

Inputs: one or more sources, each either a directory of journal .txt files (Minime or
Astrid entries copied read-only; headers, metadata lines, bracketed notices and the final
NEXT: line are stripped and counted) or a Tauri sustained session directory (journals/*.json).
Prints per source, with n texts and total words: first-person singular and plural pronoun
rates, hedges, noticing/feeling verbs, questions per sentence, self-reference to the writing
or thinking itself, apparatus vocabulary (reservoir, sensory, field, RMS, fill, L2, eigen),
digit density, words per sentence, type-token ratio, the share of texts whose first
sentence is first person, and the share of texts carrying assistant-mode phrases ("please
provide", "I'd be happy to", "let me know if"), which inflate first-person counts without
any introspective register, and the share of texts shaped as a role-played human diary
(a "Journal Entry" header, "Day N", a date or mood template), which also carry first person. Rates are per 1,000 words unless stated. These are counts of
word families, not judgments of experience. Standard library only.
"""
import glob, json, os, re, sys

FIRST = {'i', "i'm", "i've", "i'd", "i'll", 'me', 'my', 'mine', 'myself'}
WE = {'we', "we're", "we've", 'our', 'ours', 'us', 'ourselves'}
HEDGE = {'perhaps', 'maybe', 'might', 'could', 'seems', 'seem', 'possibly', 'uncertain', 'unsure', 'wonder', 'wondering', 'suppose'}
NOTICE = {'notice', 'noticed', 'noticing', 'feel', 'feels', 'felt', 'feeling', 'sense', 'sensing', 'wonder', 'wondering', 'find', 'finding', 'aware', 'realize', 'realise'}
SELFREF = re.compile(r"\b(this (entry|writing|reflection|introspection|moment of writing)|as i write|these words|my (own )?(thought|thoughts|words|voice|writing|reflection)|the act of writing)\b", re.I)
APPARATUS = re.compile(r"\b(reservoir|sensory|field|rms|fill|l2|eigen\w*|λ|recurrent|telemetry|spectral)\b", re.I)
ASSIST = re.compile(r"\b(please provide|i'?d be happy to|happy to help|let'?s create|you'?d like me to|i'?m ready when you are|based on the context provided|here'?s what i'?ll need|as an ai|let me know if|feel free to (ask|provide|share))\b", re.I)
DIARY = re.compile(r"(^\W{0,6}journal entry\b|\bday \d+\b|^\W{0,6}date:|\[current date\]|dear (diary|journal))", re.I | re.M)
HEADER = re.compile(r"^(=== .* ===|Source revision:|Input evidence:|Account:|Delivery:|Mode:|Timestamp:|Fill:|Revised from:|NEXT:|--- .* ---|\[(Agency-vernacular|Pressure-vocabulary)[^\]]*\])")

def clean(text):
    kept, stripped = [], 0
    for line in text.splitlines():
        if HEADER.match(line.strip()):
            stripped += 1
        else:
            kept.append(line)
    return '\n'.join(kept).strip(), stripped

def load(source):
    texts, stripped = [], 0
    if os.path.isdir(os.path.join(source, 'journals')):
        for f in sorted(glob.glob(os.path.join(source, 'journals', '*.json')), key=lambda f: int(os.path.basename(f).split('-')[1])):
            texts.append(json.load(open(f))['pending']['entry']['text'])
    else:
        for f in sorted(glob.glob(os.path.join(source, '*.txt'))):
            t, s = clean(open(f, encoding='utf-8', errors='replace').read()); stripped += s
            if t: texts.append(t)
    return texts, stripped

def measure(texts):
    words = sentences = first = we = hedge = notice = questions = selfref = apparatus = digits = chars = 0
    vocab = set(); first_person_opening = 0; assistant_mode = 0; diary = 0
    for t in texts:
        toks = re.findall(r"[A-Za-z'’]+", t.lower()); toks = [w.replace('’', "'") for w in toks]
        words += len(toks); vocab.update(toks)
        sents = [s for s in re.split(r'(?<=[.!?])\s+', t.replace('\n', ' ')) if s.strip()]
        sentences += len(sents); questions += sum(1 for s in sents if s.strip().endswith('?'))
        first += sum(1 for w in toks if w in FIRST); we += sum(1 for w in toks if w in WE)
        hedge += sum(1 for w in toks if w in HEDGE); notice += sum(1 for w in toks if w in NOTICE)
        selfref += len(SELFREF.findall(t)); apparatus += len(APPARATUS.findall(t))
        digits += sum(c.isdigit() for c in t); chars += len(t)
        if sents and re.match(r"^(i|i'm|i’m|my|as i|in this moment)\b", sents[0].strip().lower()): first_person_opening += 1
        if ASSIST.search(t): assistant_mode += 1
        if DIARY.search(t): diary += 1
    k = 1000.0 / max(words, 1)
    return dict(n=len(texts), words=words, first=first * k, we=we * k, hedge=hedge * k, notice=notice * k,
                questions=100.0 * questions / max(sentences, 1), selfref=selfref * k, apparatus=apparatus * k,
                digits=100.0 * digits / max(chars, 1), wps=words / max(sentences, 1), ttr=len(vocab) / max(words, 1),
                fp_open=100.0 * first_person_opening / max(len(texts), 1),
                assist=100.0 * assistant_mode / max(len(texts), 1), diary=100.0 * diary / max(len(texts), 1))

def main(sources):
    print("rates per 1,000 words unless marked %; n = texts")
    print(f"{'source':<36} {'n':>3} {'words':>6} {'I/me':>6} {'we':>5} {'hedge':>6} {'notice':>6} {'?/sent%':>7} {'selfref':>7} {'apparatus':>9} {'digit%':>6} {'w/sent':>6} {'ttr':>5} {'I-open%':>7} {'assist%':>7} {'diary%':>6}")
    for s in sources:
        texts, stripped = load(s); m = measure(texts)
        parts = s.rstrip('/').split(os.sep)
        label = (os.path.join(parts[-2], parts[-1]) if len(parts) > 1 and parts[-1].startswith('sustained-') else parts[-1])[-36:]
        print(f"{label:<36} {m['n']:>3} {m['words']:>6} {m['first']:>6.1f} {m['we']:>5.1f} {m['hedge']:>6.1f} {m['notice']:>6.1f} {m['questions']:>7.1f} {m['selfref']:>7.2f} {m['apparatus']:>9.1f} {m['digits']:>6.2f} {m['wps']:>6.1f} {m['ttr']:>5.2f} {m['fp_open']:>7.0f} {m['assist']:>7.0f} {m['diary']:>6.0f}" + (f"   (stripped {stripped} header lines)" if stripped else ''))

if __name__ == '__main__':
    main(sys.argv[1:])
