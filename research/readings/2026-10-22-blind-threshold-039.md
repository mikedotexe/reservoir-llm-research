# Blind reading, 2026-10-22: the 0.39.0 threshold-battery arms

**Sample.** `blind-policy-039/blind-sample.md` in the session scratchpad, drawn at 18:45 PDT with
`probes/desktop_blind_sample.py --per 2 --skip 9 --seed 39` from nine of the ten gemma4 arms
of the threshold battery (`thr-lo-state-residual-gemma4[-seed7]`, `thr-hi-state-residual-gemma4`,
`thr-lo-random-older-gemma4[-seed7]`, `bothnotag-state-residual-gemma4[-seed7]`,
`bothnotag-random-older-gemma4[-seed7]`; plain contract with no context line, embedding codec,
40 entries each). The seed-7 high-fill arm is left out because it is byte-identical to its
low-fill twin (40 of 40). Entries 10 and 40 of each arm: 18 entries, all distinct by hash,
numbered, with their step; the key beside it is unopened. The chain's own draw (entries 2 and
40, `--per 2` with the first entry skipped) was set aside unread because entry 2 is shared by
every arm at one seed whose prompts are still identical then, which the identity probe showed
without a text being read; `--skip N` was added to the probe for this
(`tests/test_desktop_blind_sample.py`). The numbers were read before the draw and are in
`analyses/2026-10-22-threshold-battery.md`; no entry text had been read when this file was
created. Readers: Mike and Claude.

## Claude's notes before the key

(pending the joint reading)

## Mike's reading before the key

(pending)

## What the key showed

(pending)
