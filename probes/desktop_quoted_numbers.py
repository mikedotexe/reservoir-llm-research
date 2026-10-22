#!/usr/bin/env python3
"""Count the percentages an entry quotes and say whether the prompt showed them.

Inputs: one or more desktop sustained-session directories (0.3x stores:
journals/journal-<step>-<index>-<sha>.json, each holding the prompt that was sent and the
entry that came back). For every entry, every percentage in its text (`\\d+(?:\\.\\d+)?%`) is
classified against that turn's prompt: `tag` when it equals the fill on the prompt's
"Optional context: step N · fill X%" line, `inherited` when it appears as a percentage
elsewhere in the prompt (the returned entry texts), and `new` when it appears in neither. A
value written without decimals matches a shown value within half a point, one with decimals
within 0.05. Per session it prints, with n: how many prompts carried a tag; entries with any
percentage; entries whose percentages are all tag or inherited; entries with a new value, the
first such entry and up to eight of its values; entries with a value of 95 or more and the
largest value quoted. Then one table line per session. In a no-tag arm no number is a tag, so
every value not inherited from a shown entry is new. Standard library only. Subject: the
laptop apparatus, never the beings.
"""
import glob
import json
import os
import re
import sys

PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s?%")
TAG_LINE = re.compile(r"^Optional context: step \d+ · fill (\d+(?:\.\d+)?)%.*$", re.M)


def percentages(text):
    """Every percentage in the text, in order, as (value, written with decimals)."""
    return [(float(m.group(1)), "." in m.group(1)) for m in PERCENT.finditer(text)]


def matches(value, decimals, shown):
    tolerance = 0.05 if decimals else 0.5
    return any(abs(value - s) <= tolerance + 1e-9 for s in shown)


def tag_value(prompt):
    found = TAG_LINE.search(prompt)
    return float(found.group(1)) if found else None


def classify(prompt, text):
    """The distinct percentages of an entry by where the prompt showed them."""
    tag = tag_value(prompt)
    shown = [v for v, _ in percentages(TAG_LINE.sub("", prompt))]
    out = {"tag": [], "inherited": [], "new": []}
    seen = set()
    for value, decimals in percentages(text):
        key = (value, decimals)
        if key in seen:
            continue
        seen.add(key)
        if tag is not None and matches(value, decimals, [tag]):
            out["tag"].append(value)
        elif matches(value, decimals, shown):
            out["inherited"].append(value)
        else:
            out["new"].append(value)
    return out


def load(session_dir):
    out = {}
    for path in glob.glob(os.path.join(session_dir, "journals", "journal-*.json")):
        with open(path) as handle:
            pending = json.load(handle)["pending"]
        index = int(os.path.basename(path).split("-")[2])
        out[index] = {"step": pending["observation"]["step"], "prompt": pending["prompt"], "text": pending["entry"]["text"]}
    return out


def summarise(session_dir):
    entries = load(session_dir)
    summary = {
        "label": os.path.basename(os.path.dirname(os.path.abspath(session_dir))) + "/" + os.path.basename(os.path.abspath(session_dir)),
        "n": len(entries), "tagged_prompts": 0, "with_percentage": 0, "shown_only": 0, "with_new": 0,
        "first_new": None, "new_values": [], "high": 0, "max": None, "per_entry": [],
    }
    for index in sorted(entries):
        e = entries[index]
        kinds = classify(e["prompt"], e["text"])
        values = kinds["tag"] + kinds["inherited"] + kinds["new"]
        summary["tagged_prompts"] += tag_value(e["prompt"]) is not None
        summary["per_entry"].append({"index": index, "step": e["step"], **kinds})
        if not values:
            continue
        summary["with_percentage"] += 1
        if kinds["new"]:
            summary["with_new"] += 1
            if summary["first_new"] is None:
                summary["first_new"] = (index, e["step"])
            summary["new_values"].extend(kinds["new"])
        else:
            summary["shown_only"] += 1
        if max(values) >= 95:
            summary["high"] += 1
        summary["max"] = max(values) if summary["max"] is None else max(summary["max"], max(values))
    return summary


def show(s):
    first = f"first at entry {s['first_new'][0]}, step {s['first_new'][1]}" if s["first_new"] else "none"
    shown = ", ".join(f"{v:g}" for v in s["new_values"][:8]) or "–"
    print(f"{s['label']}: {s['n']} entries (n) · prompts with a fill tag {s['tagged_prompts']} of {s['n']}")
    print(f"  entries with a percentage {s['with_percentage']} · all of them shown (tag or inherited) {s['shown_only']}"
          f" · with a value the prompt never showed {s['with_new']} ({first}) · values ≥ 95 in {s['high']} entries"
          f" · largest {s['max'] if s['max'] is None else f'{s['max']:g}'}%")
    print(f"  new values (up to 8): {shown}")


def main(argv):
    if not argv:
        print(__doc__)
        return
    rows = []
    for d in argv:
        s = summarise(d)
        show(s)
        rows.append(s)
    print()
    print(f"{'source':44s} {'n':>3s} {'any%':>5s} {'shown':>5s} {'new':>4s} {'first':>6s} {'≥95':>4s} {'max':>7s}")
    for s in rows:
        first = str(s["first_new"][0]) if s["first_new"] else "–"
        biggest = "–" if s["max"] is None else f"{s['max']:g}"
        print(f"{s['label'][-44:]:44s} {s['n']:3d} {s['with_percentage']:5d} {s['shown_only']:5d} {s['with_new']:4d} {first:>6s} {s['high']:4d} {biggest:>7s}")


if __name__ == "__main__":
    main(sys.argv[1:])
