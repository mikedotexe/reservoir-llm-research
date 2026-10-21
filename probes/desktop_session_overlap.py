#!/usr/bin/env python3
"""Verbatim-sentence overlap between consecutive journals of a Tauri My reservoir session.

Input: a sustained session directory, e.g.
  ~/Library/Application Support/research.reservoir.scope.tauri/sustained-v1/sustained-<id>
Reads journals/*.json only. Prints, per entry: sentence count, sentences copied verbatim from
the previous entry, their fraction, and the first new sentence. Standard library only.
Subject: the laptop preview's own writing loop, never the beings.
"""
import glob, json, os, re, sys

def sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.replace('\n', ' ')) if len(s.strip()) > 20]

def main(session):
    files = sorted(glob.glob(os.path.join(session, 'journals', '*.json')),
                   key=lambda f: int(os.path.basename(f).split('-')[1]))
    print(f"journals: {len(files)}  (n)")
    print("step  sents  verbatim_from_prev  frac  first_new_sentence")
    previous = None
    for f in files:
        entry = json.load(open(f))['pending']['entry']
        ss = sentences(entry['text'])
        if previous is None:
            print(f"{entry['observedStep']:>4}  {len(ss):>5}  {'-':>18}")
        else:
            rep = [s for s in ss if s in previous]
            new = [s for s in ss if s not in previous]
            print(f"{entry['observedStep']:>4}  {len(ss):>5}  {len(rep):>18}  {len(rep)/len(ss):.2f}  {new[0][:80] if new else ''}")
        previous = set(ss)

if __name__ == '__main__':
    main(sys.argv[1])
