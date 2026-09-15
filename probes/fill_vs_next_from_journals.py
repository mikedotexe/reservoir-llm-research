#!/usr/bin/env python3
"""Read-only feasibility probe: does the chosen NEXT action vary with fill?

Scans both beings' journal text files (live + archive), pulls the fill value
from the header and the last `NEXT:` line from the body, and cross-tabulates
the action verb against fill buckets, split by month so era effects are visible.

This is a probe for the 2026-09-06 data trace, not the index. It does not
write anything. Run: python3 probes/fill_vs_next_from_journals.py
"""
from __future__ import annotations

import collections
import datetime as dt
import os
import re
import sys

ASTRID_JOURNAL = "/Users/v/other/astrid/capsules/spectral-bridge/workspace/journal"
MINIME_JOURNAL = "/Users/v/other/minime/workspace/journal"
MINIME_PRESERVE = "/Users/v/other/minime/emergency_preserve_20260419T130302/workspace/journal"

FILL_RE = re.compile(r"^Fill(?: %| ratio)?:\s*([0-9.]+)%", re.M)
NEXT_RE = re.compile(r"^NEXT:\s*(.+)$", re.M)
UNIX_RE = re.compile(r"(\d{10})")
ISO_RE = re.compile(r"(\d{4}-\d{2})-\d{2}T")
BUCKETS = [(0, 30, "<30"), (30, 45, "30-45"), (45, 58, "45-58"), (58, 66, "58-66"),
           (66, 72, "66-72"), (72, 80, "72-80"), (80, 101, ">=80")]


def bucket(fill: float) -> str:
    for lo, hi, name in BUCKETS:
        if lo <= fill < hi:
            return name
    return "?"


def verb(next_line: str) -> str:
    tok = next_line.strip().split()[0] if next_line.strip() else "(empty)"
    tok = re.sub(r"<END_OF_TURN>|</S>", "", tok.upper())
    return tok.strip("`*,.:;()[]\"'") or "(empty)"


def iter_files(root: str):
    with os.scandir(root) as it:
        for e in it:
            if e.is_file() and e.name.endswith(".txt"):
                yield e.path, e.name
    arch = os.path.join(root, "archive")
    if os.path.isdir(arch):
        with os.scandir(arch) as it:
            for sub in it:
                if sub.is_dir():
                    with os.scandir(sub.path) as it2:
                        for e in it2:
                            if e.is_file() and e.name.endswith(".txt"):
                                yield e.path, e.name


def month_of(being: str, name: str) -> str:
    if being == "astrid":
        m = UNIX_RE.search(name)
        return dt.datetime.fromtimestamp(int(m.group(1)), dt.UTC).strftime("%Y-%m") if m else "?"
    m = ISO_RE.search(name)
    return m.group(1) if m else "?"


def scan(being: str, roots: list[str], name_filter=None):
    by_bucket = collections.defaultdict(collections.Counter)
    by_month_bucket = collections.defaultdict(collections.Counter)
    n_files = n_fill = n_both = 0
    for root in roots:
        if not os.path.isdir(root):
            continue
        for path, name in iter_files(root):
            base = name.lstrip("!")
            if name_filter and not name_filter(base):
                continue
            n_files += 1
            try:
                with open(path, "r", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            fm = FILL_RE.search(text)
            if not fm:
                continue
            n_fill += 1
            nexts = NEXT_RE.findall(text)
            if not nexts:
                continue
            n_both += 1
            fill = float(fm.group(1))
            v = verb(nexts[-1])
            b = bucket(fill)
            by_bucket[b][v] += 1
            by_month_bucket[(month_of(being, name), b)][v] += 1
    print(f"\n=== {being}: files={n_files} with_fill={n_fill} with_fill_and_NEXT={n_both} ===")
    print(f"{'bucket':7s} {'n':>7s}  top verbs (share of bucket)")
    for _, _, b in BUCKETS:
        c = by_bucket[b]
        n = sum(c.values())
        if not n:
            continue
        top = ", ".join(f"{v} {k / n * 100:.0f}%" for v, k in c.most_common(6))
        print(f"{b:7s} {n:7d}  {top}")
    print(f"\n--- {being}: month x bucket (n, top-3 verbs) ---")
    for (m, b), c in sorted(by_month_bucket.items()):
        n = sum(c.values())
        if n < 20:
            continue
        top = ", ".join(f"{v} {k / n * 100:.0f}%" for v, k in c.most_common(3))
        print(f"{m} {b:7s} n={n:6d}  {top}")


if __name__ == "__main__":
    scan("astrid", [ASTRID_JOURNAL], name_filter=lambda b: b.startswith("astrid_") or b.startswith("dialogue_"))
    scan("minime", [MINIME_JOURNAL, MINIME_PRESERVE])
    print("\ndone", file=sys.stderr)
