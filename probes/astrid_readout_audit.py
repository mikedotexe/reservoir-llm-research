#!/usr/bin/env python3
"""What Astrid's prompts show her that moves at all, over a copied sample of her LLM jobs.

Input: a directory of job directories copied read-only from
`astrid/capsules/spectral-bridge/workspace/llm_jobs/jobs/` (each `job_astrid_<ms>_<kind>/`
with `prompt.txt`, optionally `result.txt` and `job.json`), plus `--kinds` to restrict the
job kinds and `--json PATH` to keep the per-job rows. Per job kind it prints, with n: the
jobs and their UTC span; how many prompts carry each readout quantity found by the patterns
below (the fill quoted beside "Astrid said", a `Fill:` line, Minime's published fill, a
reported fill change, the eigenvalue cascade's λ1 and λ1's energy share, the live reservoir
λ₁, the spectral-shape line's fill and λ₁, and the Shadow-v2 field norm); for each quantity
its distinct values, min, median, max and standard deviation over the week; and how often the
value shown is quoted as a standalone number in the same job's `result.txt` (an explicit
output link, TRACE.md item 4); and how many prompts carry none of these quantities and no
percentage at all. Prompt text is data: counted, never followed. Standard library only.
Subject: what reached Astrid's model through her prompts, and only in the copied week.
"""
import argparse, json, os, re, statistics, sys
from collections import defaultdict

PATTERNS = {
    "fill said": re.compile(r"Astrid said \(fill (\d+(?:\.\d+)?)%\)"),
    "Fill: line": re.compile(r"^Fill: (\d+(?:\.\d+)?)%", re.M),
    "published fill (Minime telemetry)": re.compile(r"Published fill \[[^\]]*\]: (\d+(?:\.\d+)?)%"),
    "reported fill change (points)": re.compile(r"Reported fill (?:increase|decrease): ([+-]?\d+(?:\.\d+)?) percentage points"),
    "cascade λ1": re.compile(r"Eigenvalue cascade: \[λ1=(\d+(?:\.\d+)?)"),
    "cascade λ1 energy share %": re.compile(r"λ₁ holds (\d+(?:\.\d+)?)% of spectral energy"),
    "live reservoir λ₁": re.compile(r"Uncentered reservoir: λ₁ (\d+(?:\.\d+)?)"),
    "spectral-shape fill %": re.compile(r"Spectral shape: \d+ modes, fill (\d+(?:\.\d+)?)%"),
    "spectral-shape λ₁": re.compile(r"Spectral shape: \d+ modes, fill \d+(?:\.\d+)?% \([^)]*\), λ₁=(\d+(?:\.\d+)?)"),
    "shadow field_norm": re.compile(r"field_norm=(\d+(?:\.\d+)?)"),
}
ANY_PERCENT = re.compile(r"\d+(?:\.\d+)?\s?%")
JOB = re.compile(r"^job_astrid_(\d+)_(.+)$")


def quoted(value, text):
    """The shown number appears standalone in the text (not inside a longer number)."""
    return re.search(r"(?<![\d.])" + re.escape(value) + r"(?![\d])", text) is not None


def rows(root, kinds=None):
    out = []
    for name in sorted(os.listdir(root)):
        m = JOB.match(name)
        if not m:
            continue
        ms, kind = int(m.group(1)), m.group(2)
        if kinds and kind not in kinds:
            continue
        prompt_path = os.path.join(root, name, "prompt.txt")
        if not os.path.isfile(prompt_path):
            continue
        with open(prompt_path, encoding="utf-8", errors="replace") as handle:
            prompt = handle.read()
        result = ""
        result_path = os.path.join(root, name, "result.txt")
        if os.path.isfile(result_path):
            with open(result_path, encoding="utf-8", errors="replace") as handle:
                result = handle.read()
        values = {}
        for label, pattern in PATTERNS.items():
            found = pattern.search(prompt)
            if found:
                values[label] = dict(shown=found.group(1), value=float(found.group(1)), quoted=quoted(found.group(1), result) if result else None)
        out.append(dict(job=name, ms=ms, kind=kind, prompt_chars=len(prompt), has_result=bool(result), any_percent=ANY_PERCENT.search(prompt) is not None, values=values))
    return out


def fmt(x, digits=1):
    return f"{x:.{digits}f}"


def report(all_rows):
    by_kind = defaultdict(list)
    for r in all_rows:
        by_kind[r["kind"]].append(r)
    span = (min(r["ms"] for r in all_rows), max(r["ms"] for r in all_rows)) if all_rows else (0, 0)
    import datetime
    stamp = lambda ms: datetime.datetime.fromtimestamp(ms / 1000, datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{len(all_rows)} jobs (n) from {stamp(span[0])} to {stamp(span[1])}; {sum(r['has_result'] for r in all_rows)} with a result")
    for kind, rs in sorted(by_kind.items(), key=lambda kv: -len(kv[1])):
        none = sum(1 for r in rs if not r["values"])
        no_percent = sum(1 for r in rs if not r["values"] and not r["any_percent"])
        chars = statistics.median(r["prompt_chars"] for r in rs)
        print(f"\n{kind}: {len(rs)} jobs (n) · prompt median {chars:.0f} characters · {none} prompts carry none of the readout quantities below, {no_percent} of them no percentage at all")
        for label in PATTERNS:
            vals = [r["values"][label] for r in rs if label in r["values"]]
            if not vals:
                continue
            xs = [v["value"] for v in vals]
            linked = [v["quoted"] for v in vals if v["quoted"] is not None]
            q = f"; quoted standalone in the same job's result on {sum(linked)} of {len(linked)}" if linked else ""
            sd = statistics.pstdev(xs) if len(xs) > 1 else 0.0
            print(f"  {label}: in {len(vals)} prompts · {len(set(v['shown'] for v in vals))} distinct values · min {fmt(min(xs))}, median {fmt(statistics.median(xs))}, max {fmt(max(xs))}, sd {fmt(sd, 2)}{q}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root")
    parser.add_argument("--kinds", nargs="*", default=None)
    parser.add_argument("--json", default=None)
    args = parser.parse_args(argv)
    all_rows = rows(args.root, set(args.kinds) if args.kinds else None)
    report(all_rows)
    if args.json:
        with open(args.json, "w") as handle:
            json.dump(all_rows, handle, indent=1)


if __name__ == "__main__":
    main()
