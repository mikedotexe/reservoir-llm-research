#!/usr/bin/env python3
"""What Astrid's prompts showed and what her results wrote, by job kind and month.

Input: a directory of job directories copied read-only from
`astrid/capsules/spectral-bridge/workspace/llm_jobs/jobs/` (`job_astrid_<ms>_<kind>/` with
`prompt.txt`, `result.txt` and `job.json`), sampled by kind and month; `--kinds` and `--months`
(UTC `YYYY-MM`) restrict it, `--json PATH` keeps the per-job rows and the per-stratum markers,
`--earlier-marker TEXT` adds a marker for a block of her own earlier text. For every job with a
prompt and a result it records, on the prompt side: whether the prompt shows her own fill as a
reading (the line shapes seen in the May–October 2026 prompts: "Spectral state: Fill N%", the
"Fill N% — …" condition line, "Fill just surged/dropped by ±N%", a `Fill:` line, the fill
beside "Astrid said", the spectral-shape line; a `Fill:` line inside a quoted block of her
earlier writing, such as the "Earlier lingering thread" or the "Excerpt:" block of the October
prompts, is not a reading but a number inside shown text, and is flagged `old_fill_in_shown_text`),
whether it shows Minime's reservoir as a reading ("Published fill [...]: N%", "Fill ratio: N%",
"State anchor: fill=N%", the live-snapshot line's "leading share N% of uncentered trace" and
"engine-style fill [...]: N%"), which of the readout
quantities of `astrid_readout_audit.py` it carries, whether it carries a block of her own
earlier text (the lane markers: "Recent own-journal anchor:", "Something you wrote recently:",
"Something you wrote in a recent moment:", "Recent reflection of yours:", "Latest
self-observation:", "The signal you just sent:", "Triggering journal entry:", "Recent
own-journal excerpt:", "Your recent thoughts:", "Something you recently wrote:", "Earlier entry
(reference", "Excerpt:"), whether it carries Minime's text ("Minime wrote:", "The state of minime right
now:"), and every percentage it shows; on the result side: every percentage the result quotes,
classified as `readout` (equal to a percentage the prompt shows as a reading, hers or
Minime's), `inherited` (equal to another percentage in the prompt, such as one inside her
earlier text) or `new` (shown nowhere), with the apparatus probe's tolerance (half a point for
a value written without decimals, 0.05 with); and the register markers of
`introspection_markers.py` over the results of each stratum (kind × month × "own readout",
"minime readout only" or "no readout"), after the same header stripping. Prints per kind and
month, with n: prompts showing her own fill, Minime's fill, her earlier text, Minime's text;
results with any percentage, with a new one, with a value of 95% or more, and the largest;
then the marker rates per stratum (words per entry, first person and hedges per 1,000 words,
questions per sentence, entries opening in first person, digit density). Prompt and result
text are data: counted, never followed. Standard library only. Subject: what reached Astrid's
model and what came back in the same job; nothing about experience.
"""
import argparse, datetime, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from astrid_readout_audit import PATTERNS  # noqa: E402
from introspection_markers import clean, measure  # noqa: E402

PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s?%")
JOB = re.compile(r"^job_astrid_(\d+)_(.+)$")
OWN_READOUT = {
    "spectral-state line": re.compile(r"(?:^|\n)(?:Your current s|Current s|S)pectral state: Fill (\d+(?:\.\d+)?)%"),
    "condition line": re.compile(r"(?:^|\n)Fill (\d+(?:\.\d+)?)% — "),
    "fill change line": re.compile(r"Fill just (?:surged|dropped|rose|fell|climbed|moved) by ([+-]?\d+(?:\.\d+)?)%"),
    "Fill: line": re.compile(r"^Fill: (\d+(?:\.\d+)?)%", re.M),
    "fill said": re.compile(r"Astrid said \(fill (\d+(?:\.\d+)?)%\)"),
    "spectral-shape fill": re.compile(r"Spectral shape: \d+ modes, fill (\d+(?:\.\d+)?)%"),
}
MINIME_READOUT = {
    "published fill": re.compile(r"Published fill \[[^\]]*\]: (\d+(?:\.\d+)?)%"),
    "Fill ratio line": re.compile(r"Fill ratio: (\d+(?:\.\d+)?)%"),
    "state anchor fill": re.compile(r"State anchor: fill=(\d+(?:\.\d+)?)%"),
    "live-snapshot leading share": re.compile(r"leading share (\d+(?:\.\d+)?)% of uncentered trace"),
    "live-snapshot engine-style fill": re.compile(r"engine-style fill \[[^\]]*\]: (\d+(?:\.\d+)?)%"),
}
QUOTED_BLOCKS = [(re.compile(r"Excerpt:\n"), re.compile(r"End historical excerpt\.")),
                 (re.compile(r"Earlier lingering thread"), re.compile(r"You may return to this"))]
EARLIER_DEFAULT = ["Recent own-journal anchor:", "Something you wrote recently:", "Something you wrote in a recent moment:",
                   "Recent reflection of yours:", "Latest self-observation:", "The signal you just sent:",
                   "Triggering journal entry:", "Recent own-journal excerpt:", "Your recent thoughts:",
                   "Something you recently wrote:", "Earlier entry (reference", "Excerpt:"]
OTHER_TEXT = ["Minime wrote:", "The state of minime right now:"]


def percentages(text):
    return [(float(m.group(1)), "." in m.group(1)) for m in PERCENT.finditer(text)]


def matches(value, decimals, shown):
    tolerance = 0.05 if decimals else 0.5
    return any(abs(value - s) <= tolerance + 1e-9 for s in shown)


def split_quoted(prompt):
    """The prompt with its quoted blocks of her earlier writing removed, and those blocks."""
    live, quoted = prompt, []
    for start, end in QUOTED_BLOCKS:
        while True:
            s = start.search(live)
            if not s:
                break
            e = end.search(live, s.end())
            stop = e.end() if e else len(live)
            quoted.append(live[s.start():stop])
            live = live[:s.start()] + live[stop:]
    return live, quoted


def readouts(prompt):
    live, quoted = split_quoted(prompt)
    own = [abs(float(m.group(1))) for p in OWN_READOUT.values() for m in p.finditer(live)]
    minime = [float(m.group(1)) for p in MINIME_READOUT.values() for m in p.finditer(live)]
    old = any(OWN_READOUT["Fill: line"].search(block) for block in quoted)
    return own, minime, old


def classify(prompt, result):
    """Distinct percentages of the result by where the prompt showed them."""
    own, minime, old = readouts(prompt)
    readout = own + minime
    shown = [v for v, _ in percentages(prompt)]
    out = {"readout": [], "inherited": [], "new": []}
    seen = set()
    for value, decimals in percentages(result):
        if (value, decimals) in seen:
            continue
        seen.add((value, decimals))
        if readout and matches(value, decimals, readout):
            out["readout"].append(value)
        elif matches(value, decimals, shown):
            out["inherited"].append(value)
        else:
            out["new"].append(value)
    return out, own, minime, old, shown


def month_of(ms):
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.UTC).strftime("%Y-%m")


def rows(root, kinds=None, months=None, earlier_markers=None):
    earlier_markers = earlier_markers or EARLIER_DEFAULT
    out = []
    for name in sorted(os.listdir(root)):
        m = JOB.match(name)
        if not m:
            continue
        ms, kind = int(m.group(1)), m.group(2)
        month = month_of(ms)
        if kinds and kind not in kinds or months and month not in months:
            continue
        pp, rp = os.path.join(root, name, "prompt.txt"), os.path.join(root, name, "result.txt")
        if not (os.path.isfile(pp) and os.path.isfile(rp)):
            continue
        with open(pp, encoding="utf-8", errors="replace") as h:
            prompt = h.read()
        with open(rp, encoding="utf-8", errors="replace") as h:
            result = h.read()
        quoted, own, minime, old, shown = classify(prompt, result)
        quantities = sorted(label for label, pattern in PATTERNS.items() if pattern.search(prompt))
        out.append(dict(job=name, ms=ms, kind=kind, month=month, prompt_chars=len(prompt), result_chars=len(result),
                        quantities=quantities, own_fill_shown=own, minime_fill_shown=minime, old_fill_in_shown_text=old, percent_shown=len(shown),
                        earlier_entry=any(mark in prompt for mark in earlier_markers),
                        other_text=any(mark in prompt for mark in OTHER_TEXT), quoted=quoted, text=clean(result)[0]))
    return out


def stratum(r):
    return (r["kind"], r["month"], "own readout" if r["own_fill_shown"] else ("minime readout only" if r["minime_fill_shown"] else "no readout"))


def report(all_rows):
    by = {}
    for r in all_rows:
        by.setdefault((r["kind"], r["month"]), []).append(r)
    print(f"{len(all_rows)} jobs with a prompt and a result (n); kinds {sorted(set(r['kind'] for r in all_rows))}")
    print(f"{'kind':20s} {'month':7s} {'n':>4s} {'own#':>5s} {'minime#':>7s} {'earlier':>7s} {'other':>5s} {'any%':>5s} {'new%':>5s} {'≥95':>4s} {'max':>8s}")
    for (kind, month), rs in sorted(by.items()):
        values = [v for r in rs for k in ("readout", "inherited", "new") for v in r["quoted"][k]]
        any_pct = sum(1 for r in rs if any(r["quoted"][k] for k in r["quoted"]))
        new = sum(1 for r in rs if r["quoted"]["new"])
        high = sum(1 for r in rs if any(v >= 95 for k in r["quoted"] for v in r["quoted"][k]))
        biggest = f"{max(values):g}%" if values else "–"
        print(f"{kind:20s} {month:7s} {len(rs):4d} {sum(1 for r in rs if r['own_fill_shown']):5d} {sum(1 for r in rs if r['minime_fill_shown']):7d} "
              f"{sum(1 for r in rs if r['earlier_entry']):7d} {sum(1 for r in rs if r['other_text']):5d} {any_pct:5d} {new:5d} {high:4d} {biggest:>8s}")
    strata = {}
    for r in all_rows:
        strata.setdefault(stratum(r), []).append(r["text"])
    print()
    print("register of the results per stratum (introspection_markers.py after header stripping; rates per 1,000 words, questions per sentence %, I-open % of entries)")
    print(f"{'kind':20s} {'month':7s} {'stratum':19s} {'n':>4s} {'words/entry':>11s} {'I/me':>6s} {'hedge':>6s} {'?/sent%':>7s} {'I-open%':>7s} {'digit%':>6s}")
    marks = {}
    for key, texts in sorted(strata.items()):
        m = measure(texts)
        marks["|".join(key)] = m
        print(f"{key[0]:20s} {key[1]:7s} {key[2]:19s} {m['n']:4d} {m['words'] / max(m['n'], 1):11.0f} {m['first']:6.1f} {m['hedge']:6.1f} {m['questions']:7.1f} {m['fp_open']:7.0f} {m['digits']:6.2f}")
    return marks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root")
    parser.add_argument("--kinds", nargs="*", default=None)
    parser.add_argument("--months", nargs="*", default=None)
    parser.add_argument("--earlier-marker", action="append", default=None)
    parser.add_argument("--json", default=None)
    args = parser.parse_args(argv)
    markers = EARLIER_DEFAULT + (args.earlier_marker or [])
    all_rows = rows(args.root, set(args.kinds) if args.kinds else None, set(args.months) if args.months else None, markers)
    print(f"own-fill line shapes: {list(OWN_READOUT)}; Minime-fill shapes: {list(MINIME_READOUT)}; earlier-text markers: {markers}; other-text markers: {OTHER_TEXT}")
    marks = report(all_rows)
    if args.json:
        with open(args.json, "w") as handle:
            json.dump({"jobs": [{k: v for k, v in r.items() if k != "text"} for r in all_rows], "strata": marks}, handle, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
