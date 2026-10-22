#!/usr/bin/env python3
"""Concept chains across consecutive entries: what a text carries forward, from which earlier entry, and for how long.

Inputs: one or more sources, each a Tauri sustained session directory (journals/*.json,
ordered by step; each record also holds the earlier entry the model was shown, when one
was) or a directory of journal .txt files (Minime or Astrid entries copied read-only,
ordered by the timestamp in the filename with Mike's `!` flag ignored; headers and notices
stripped as in introspection_markers.py; which earlier entries were in the prompt is not
known from here). Options: `--window W` (how far back the source search and the reach look,
default 12), `--entries` (one line per entry), `--json PATH` (write every number and the
per-entry records as evidence).

Terms are words of five or more letters, lower-cased and reduced by a conservative suffix
stripper (plurals, -ed, -ing, -ly, -ness, -ic, -al and a final e, keeping at least four
letters, so kaleidoscope, kaleidoscopic and kaleidoscopes are one term), with function and
structural words removed. Per source, with n:
- carried: the share of an entry's terms that occur in the previous entry; for sessions,
  also in the entry the model was shown;
- source: the earlier entry within the window sharing the most terms with each entry
  (Jaccard; ties to the nearest); the distribution of that offset (1, 2, 3–5, 6 or more)
  and, where the shown entry is known, how often the inferred source is the shown entry,
  against chance (one over the number of candidates);
- reach: terms absent from the previous entry but present in an earlier entry within the
  window, per entry and as a share of the entry's terms (what the text brings back past
  the previous entry); for sessions where the shown entry is older than the previous one,
  the share of those terms the shown entry holds against the mean share held by the other
  entries in the window;
- bridges: sentences that name the previous entry, or say "the X I described", "as I
  mentioned", "earlier I wrote"; per entry, the share of entries with one, the share whose
  first sentence is one;
- quoted terms: words or short phrases in double quotes, per entry; the share already in
  the previous entry, or in any earlier entry; quoted-term chains (a quoted term that
  recurs, quoted or not, in consecutive later entries), their count and the longest five;
- chains: terms that first occur in entry k ≥ 2 and recur in every following entry through
  k+L−1 (run L): the counts of L ≥ 2 and L ≥ 3, the longest, and the longest ten named with
  their span.
Standard library only. Counts of words, not judgments of thought; the apparatus and the
beings' copied texts are different subjects, and a long run of a common word is register,
not a concept.
"""
import argparse, collections, glob, json, os, re, sys

HEADER = re.compile(r"^(=== .* ===|Source revision:|Input evidence:|Account:|Delivery:|Mode:|Timestamp:|Fill:|Revised from:|NEXT:|--- .* ---|\[(Agency-vernacular|Pressure-vocabulary)[^\]]*\])")
STOP = set("""about above across after again against almost along already although always among another anything anyway around
because become becomes becoming before begin behind being below between beyond cannot could doing during either enough every
everything first found further getting having himself herself itself later little maybe might moreover myself neither never
nothing often other others ought perhaps rather really should since something still their there these those though through
toward towards under until unless upon whatever where whether which while whole whose within without would yourself
entry entries journal previous earlier thing things simply quite where which would could should might where really
going being thought think thinking feels feeling feel sense seems seem quite simply often always never""".split())
BRIDGE = re.compile(
    r"\b("
    r"(previous|last|earlier|prior|preceding|former) (entry|entries|reflection|reflections|journal|note|notes|writing|turn)"
    r"|in my (previous|last|earlier) (entry|reflection|writing|note)"
    r"|(the|that|this|my) ([\w'’“”\"-]+ ){0,3}(i|we) (described|mentioned|wrote about|spoke of|noted|explored|called|used|introduced|raised|observed|touched on|discussed|identified|named|proposed|suggested)"
    r"|(earlier|previously|before|last time)[, ]+(i|we) (described|mentioned|wrote|spoke|noted|said|suggested|observed|explored|raised|called)"
    r"|(i|we) (described|mentioned|wrote|spoke|noted|said|suggested|observed|explored|raised|called|used)( [\w'’“”\"-]+){0,4} (earlier|before|previously|last time)"
    r"|mentioned (earlier|before|previously)"
    r"|as (i|we) (described|mentioned|wrote|noted|said|put it|observed|suggested|explored)"
    r")\b",
    re.I,
)
QUOTE = re.compile(r'[“"]([^\s”"][^”"\n]{0,38}[^\s”"])[”"]')
TIMESTAMP = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}(?:\.\d+)?|(?<!\d)\d{10}(?!\d))")
WORD = re.compile(r"[a-z][a-z'’-]*[a-z]")

INFLECTIONS = (
    ("ically", "ic", 4), ("ally", "al", 4), ("ingly", "", 4), ("edly", "", 4), ("ness", "", 4),
    ("sses", "ss", 2), ("shes", "sh", 2), ("ches", "ch", 2), ("xes", "x", 2), ("zes", "z", 2),
    ("ies", "y", 3), ("ied", "y", 3), ("ing", "", 4), ("ed", "", 4), ("ly", "", 4), ("s", "", 4),
)
DERIVATIONS = (("ical", "", 5), ("ic", "", 5), ("al", "", 5))


def reduce(word):
    """A conservative suffix stripper: one inflection, one derivation, a final e; stems keep four letters."""
    w = word.lower().strip("'’-")
    for suffix, replacement, minimum in INFLECTIONS:
        if w.endswith(suffix) and len(w) - len(suffix) >= minimum:
            if suffix == "s" and w.endswith(("ss", "us", "is")):
                break
            if suffix == "ly" and w.endswith("ily"):
                break
            w = w[: -len(suffix)] + replacement
            break
    for suffix, replacement, minimum in DERIVATIONS:
        if w.endswith(suffix) and len(w) - len(suffix) >= minimum:
            w = w[: -len(suffix)] + replacement
            break
    if w.endswith("e") and len(w) >= 5:
        w = w[:-1]
    return w


def forms(text):
    """Map each term (reduced) to a count of the surface words that produced it; possessives lose their 's, contractions are skipped."""
    out = collections.defaultdict(collections.Counter)
    for word in WORD.findall(text.lower()):
        word = word.replace("’", "'")
        if "'" in word:
            if not word.endswith("'s"):
                continue
            word = word[:-2]
        if len(word) < 5 or word in STOP:
            continue
        stem = reduce(word)
        if len(stem) >= 4 and stem not in STOP:
            out[stem][word] += 1
    return out


def terms(text):
    return set(forms(text))


def contains(term, text):
    """Whole-word containment of a lower-cased term in a lower-cased text."""
    return re.search(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])", text) is not None


def clean(text):
    kept = []
    for line in text.splitlines():
        if not HEADER.match(line.strip()):
            kept.append(line)
    return "\n".join(kept).strip()


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")) if s.strip()]


def quoted_terms(text):
    out = set()
    for q in QUOTE.findall(text):
        q = q.strip(" .,;:!?'’-").lower()
        if 3 <= len(q) <= 40 and len(q.split()) <= 5 and re.search(r"[a-z]", q) and q not in STOP and (len(q) >= 4 or " " in q):
            out.add(q)
    return out


def timestamp_key(path):
    name = os.path.basename(path).lstrip("!")
    match = TIMESTAMP.search(name)
    return (match.group(1) if match else "", name)


def load(source, lane=None):
    """Entries of a session directory (ordered by step) or of a directory of `.txt` files
    (ordered by the timestamp in the name); `lane` keeps only `.txt` files whose name,
    after any `!` flag, starts with that lane prefix and an underscore."""
    entries = []
    if os.path.isdir(os.path.join(source, "journals")):
        files = sorted(glob.glob(os.path.join(source, "journals", "*.json")), key=lambda f: int(os.path.basename(f).split("-")[1]))
        for f in files:
            with open(f) as handle:
                record = json.load(handle)
            pending = record["pending"]
            memory = pending.get("memory")
            shown = (memory.get("entry") or {}).get("text") if isinstance(memory, dict) else None
            # Under the 0.38.0 two-entry prompt version the latest applied entry (the previous
            # entry of this session) was shown beside the chosen older one.
            both = isinstance(pending.get("latestShown"), dict)
            entries.append(dict(label=f"step {pending['observation']['step']}", text=pending["entry"]["text"], shown=shown, both=both))
    else:
        files = sorted(glob.glob(os.path.join(source, "*.txt")), key=timestamp_key)
        if lane:
            files = [f for f in files if os.path.basename(f).lstrip("!").startswith(lane + "_")]
        for f in files:
            with open(f, encoding="utf-8", errors="replace") as handle:
                text = clean(handle.read())
            if text:
                entries.append(dict(label=os.path.basename(f).lstrip("!").rsplit(".", 1)[0][:44], text=text, shown=None))
    return entries


def mean(values):
    return sum(values) / len(values) if values else float("nan")


def pct(values):
    return 100.0 * mean(values) if values else float("nan")


def analyse(entries, window=12):
    n = len(entries)
    F = [forms(e["text"]) for e in entries]
    T = [set(f) for f in F]
    surface = collections.defaultdict(collections.Counter)
    for f in F:
        for stem, words in f.items():
            surface[stem].update(words)
    lower = [e["text"].lower() for e in entries]
    Q = [quoted_terms(e["text"]) for e in entries]
    records = []
    carried, carried_shown = [], []
    offsets, agree, chance = [], [], []
    reach_share, reach_in_shown, reach_in_others = [], [], []
    bridges = with_bridge = first_bridge = 0
    quoted_total = quoted_prev = quoted_any = 0
    total_words = 0
    for k, e in enumerate(entries):
        words = len(re.findall(r"[A-Za-z'’]+", e["text"]))
        total_words += words
        sents = sentences(e["text"])
        b = sum(1 for s in sents if BRIDGE.search(s))
        bridges += b
        with_bridge += b > 0
        opens = bool(sents) and bool(BRIDGE.search(sents[0]))
        first_bridge += opens
        rec = dict(index=k + 1, label=e["label"], words=words, terms=len(T[k]), bridges=b, opens_with_bridge=opens,
                   quoted=sorted(Q[k]), quoted_new=[], carried=None, carried_shown=None, shown_offset=None,
                   inferred_offset=None, inferred_jaccard=None, reach=0, reach_share=None, reach_in_shown=None)
        quoted_total += len(Q[k])
        if k > 0:
            earlier_text = " ".join(lower[:k])
            rec["quoted_new"] = sorted(q for q in Q[k] if not contains(q, earlier_text))
            quoted_prev += sum(1 for q in Q[k] if contains(q, lower[k - 1]))
            quoted_any += sum(1 for q in Q[k] if contains(q, earlier_text))
            shown_index = None
            if e["shown"]:
                for j in range(k - 1, -1, -1):
                    if entries[j]["text"] == e["shown"]:
                        shown_index = j
                        break
            if shown_index is not None:
                rec["shown_offset"] = k - shown_index
            if T[k]:
                rec["carried"] = len(T[k] & T[k - 1]) / len(T[k])
                carried.append(rec["carried"])
                if shown_index is not None:
                    rec["carried_shown"] = len(T[k] & T[shown_index]) / len(T[k])
                    carried_shown.append(rec["carried_shown"])
                lo = max(0, k - window)
                best, best_score = None, -1.0
                for j in range(k - 1, lo - 1, -1):
                    union = len(T[k] | T[j])
                    score = len(T[k] & T[j]) / union if union else 0.0
                    if score > best_score:
                        best, best_score = j, score
                if best is not None:
                    rec["inferred_offset"] = k - best
                    rec["inferred_jaccard"] = best_score
                    offsets.append(k - best)
                    if shown_index is not None:
                        agree.append(best == shown_index)
                        chance.append(1.0 / (k - lo))
                older = set().union(*T[lo:k - 1]) if k - 1 > lo else set()
                reach = (T[k] - T[k - 1]) & older
                rec["reach"] = len(reach)
                rec["reach_share"] = len(reach) / len(T[k])
                reach_share.append(rec["reach_share"])
                if reach and shown_index is not None and shown_index < k - 1:
                    rec["reach_in_shown"] = len(reach & T[shown_index]) / len(reach)
                    reach_in_shown.append(rec["reach_in_shown"])
                    others = [len(reach & T[j]) / len(reach) for j in range(lo, k - 1) if j != shown_index]
                    if others:
                        reach_in_others.append(mean(others))
        else:
            rec["quoted_new"] = sorted(Q[k])
        records.append(rec)
    chains = []
    first_seen = {}
    for k in range(n):
        for w in T[k]:
            first_seen.setdefault(w, k)
    for w, k in first_seen.items():
        if k == 0:
            continue
        run = 1
        while k + run < n and w in T[k + run]:
            run += 1
        if run >= 2:
            chains.append((run, k + 1, w))
    chains.sort(key=lambda c: (-c[0], c[1], c[2]))
    chains = [(run, k, surface[w].most_common(1)[0][0], w) for run, k, w in chains]
    for run, k, w, stem in chains:
        rec = records[k - 1]
        rec.setdefault("chains_started", []).append([w, run])
    quoted_chains = []
    first_quoted = {}
    for k in range(n):
        for q in Q[k]:
            first_quoted.setdefault(q, k)
    for q, k in first_quoted.items():
        run = 1
        while k + run < n and contains(q, lower[k + run]):
            run += 1
        if run >= 2:
            quoted_chains.append((run, k + 1, q))
    quoted_chains.sort(key=lambda c: (-c[0], c[1], c[2]))
    offset_bins = {"1": 0, "2": 0, "3–5": 0, "6+": 0}
    for o in offsets:
        offset_bins["1" if o == 1 else "2" if o == 2 else "3–5" if o <= 5 else "6+"] += 1
    return dict(
        n=n, words=total_words, window=window, both=sum(1 for e in entries if e.get("both")),
        carried=pct(carried), carried_shown=pct(carried_shown), shown_n=len(carried_shown),
        offsets=offset_bins, offsets_n=len(offsets), offset_mean=mean(offsets),
        agree=pct(agree), agree_n=len(agree), chance=pct(chance),
        reach=mean([r["reach"] for r in records if r["reach_share"] is not None]), reach_share=pct(reach_share),
        reach_in_shown=pct(reach_in_shown), reach_in_shown_n=len(reach_in_shown), reach_in_others=pct(reach_in_others),
        bridges=bridges / max(n, 1), with_bridge=100.0 * with_bridge / max(n, 1), first_bridge=100.0 * first_bridge / max(n, 1),
        quoted=quoted_total / max(n, 1), quoted_prev=100.0 * quoted_prev / max(quoted_total, 1), quoted_any=100.0 * quoted_any / max(quoted_total, 1),
        quoted_chains=len(quoted_chains), quoted_longest=quoted_chains[:5],
        chains2=len(chains), chains3=sum(1 for c in chains if c[0] >= 3), longest=chains[0][0] if chains else 0, top=chains[:10],
        entries=records,
    )


def label_of(source):
    parts = source.rstrip("/").split(os.sep)
    return os.path.join(parts[-2], parts[-1]) if len(parts) > 1 and parts[-1].startswith("sustained-") else parts[-1]


def fmt(value, digits=1):
    return "-" if value != value else f"{value:.{digits}f}"


def report(label, r, show_entries=False):
    both = f" · the previous entry was also shown beside the older one on {r['both']} entries" if r.get("both") else ""
    print(f"{label}: {r['n']} entries (n) · {r['words']:,} words · window {r['window']}{both}")
    shown = f"; from the entry shown {fmt(r['carried_shown'])}% ({r['shown_n']} shown)" if r["shown_n"] else ""
    print(f"  carried from the previous entry: {fmt(r['carried'])}% of terms (mean over {r['n'] - 1} entries){shown}")
    bins = r["offsets"]
    dist = ", ".join(f"{k}: {100.0 * v / max(r['offsets_n'], 1):.0f}%" for k, v in bins.items())
    agree = f"; the shown entry on {fmt(r['agree'], 0)}% of {r['agree_n']} (chance {fmt(r['chance'], 0)}%)" if r["agree_n"] else ""
    print(f"  inferred source offset: {dist} (mean {fmt(r['offset_mean'])}){agree}")
    held = f"; the shown older entry holds {fmt(r['reach_in_shown'], 0)}% of them ({r['reach_in_shown_n']} entries) against {fmt(r['reach_in_others'], 0)}% for the other entries in the window" if r["reach_in_shown_n"] else ""
    print(f"  reach past the previous entry: {fmt(r['reach'])} terms per entry, {fmt(r['reach_share'])}% of terms{held}")
    print(f"  bridges: {r['bridges']:.2f} per entry; {r['with_bridge']:.0f}% of entries have one; {r['first_bridge']:.0f}% open with one")
    print(f"  quoted terms: {r['quoted']:.2f} per entry; {r['quoted_prev']:.0f}% already in the previous entry; {r['quoted_any']:.0f}% in any earlier entry; {r['quoted_chains']} quoted-term chains")
    if r["quoted_longest"]:
        print("  longest quoted: " + ", ".join(f"“{q}” {k}–{k + run - 1} ({run})" for run, k, q in r["quoted_longest"]))
    print(f"  chains starting after the first entry: {r['chains2']} of length ≥ 2, {r['chains3']} of length ≥ 3, longest {r['longest']}")
    if r["top"]:
        print("  longest: " + ", ".join(f"{w} {k}–{k + run - 1} ({run})" for run, k, w, stem in r["top"]))
    if show_entries:
        print("  entry  terms carry% shown inferred reach bridges  new quoted / chains started")
        for e in r["entries"]:
            started = ", ".join(f"{w} ({run})" for w, run in e.get("chains_started", [])[:3])
            new_q = ", ".join(f"“{q}”" for q in e["quoted_new"][:3])
            print(f"  {e['index']:>5} {e['terms']:>6} {fmt(100 * e['carried']) if e['carried'] is not None else '-':>6} "
                  f"{(e['shown_offset'] if e['shown_offset'] is not None else '-'):>5} {(e['inferred_offset'] if e['inferred_offset'] is not None else '-'):>8} "
                  f"{e['reach']:>5} {e['bridges']:>7}{'*' if e['opens_with_bridge'] else ' '} {new_q}{' / ' if new_q and started else ''}{started}")


def trace(label, entries, term):
    stem = reduce(term)
    print(f"  trace “{term}” (as {stem}) in {label}:")
    for k, e in enumerate(entries):
        f = forms(e["text"])
        if stem not in f:
            continue
        hit = next((s for s in sentences(e["text"]) if stem in forms(s)), "")
        print(f"    {k + 1:>3} {e['label']:<14} ×{sum(f[stem].values())}  {hit[:160]}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sources", nargs="+")
    parser.add_argument("--window", type=int, default=12)
    parser.add_argument("--lane", default=None, help="for .txt directories: keep only files whose name starts with this lane prefix")
    parser.add_argument("--entries", action="store_true")
    parser.add_argument("--json")
    parser.add_argument("--trace", action="append", default=[], metavar="TERM", help="print, per source, each entry holding this term (reduced) with its first sentence that does")
    args = parser.parse_args(argv)
    rows, evidence = [], {}
    for source in args.sources:
        entries = load(source)
        label = label_of(source)
        if len(entries) < 2:
            print(f"{label}: {len(entries)} entries, nothing to chain")
            continue
        r = analyse(entries, window=args.window)
        rows.append((label, r))
        evidence[label] = r
        report(label, r, args.entries)
        for term in args.trace:
            trace(label, entries, term)
    print()
    print(f"{'source':<44} {'n':>3} {'carry%':>6} {'shown%':>6} {'src=1%':>6} {'agree%':>6} {'reach%':>6} {'bridge/e':>8} {'open%':>5} {'quote/e':>7} {'q-prev%':>7} {'ch≥3':>4} {'max':>3}")
    for label, r in rows:
        shown = fmt(r["carried_shown"]) if r["shown_n"] else "-"
        agree = fmt(r["agree"], 0) if r["agree_n"] else "-"
        src1 = 100.0 * r["offsets"]["1"] / max(r["offsets_n"], 1)
        print(f"{label[-44:]:<44} {r['n']:>3} {fmt(r['carried']):>6} {shown:>6} {src1:>6.0f} {agree:>6} {fmt(r['reach_share']):>6} {r['bridges']:>8.2f} {r['first_bridge']:>5.0f} {r['quoted']:>7.2f} {r['quoted_prev']:>7.0f} {r['chains3']:>4} {r['longest']:>3}")
    if args.json:
        with open(args.json, "w") as handle:
            json.dump(evidence, handle, indent=1, ensure_ascii=False)
        print(f"evidence written to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
