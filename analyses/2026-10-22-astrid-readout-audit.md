# Astrid's readouts over one week: what her prompts show that moves (October 22, 2026)

**Subject and channel.** The prompts of Astrid's language-model jobs, copied read-only from
volya on 2026-10-22 (`llm_jobs/jobs/`, the 2,405 job directories whose ids fall in the seven
days from 2026-10-15 17:34 to 2026-10-22 17:19 UTC; 2,403 with a `result.txt`). `prompt.txt`
is what reached her model in that job and `result.txt` what came back in the same job, so
"quoted" below is an explicit output link (TRACE.md item 4), not a journal file. Probe
`probes/astrid_readout_audit.py`; output `astrid-readout-week.out` and the per-job rows in
`astrid-readout-week.json` in the session scratchpad, with the copies (private, never in the
repo). Counts of numbers in text; nothing here is about what she experiences.

**What the probe counts.** For each job kind, the readout quantities a prompt carries, found
by the line shapes seen in this week's prompts (the fill beside "Astrid said", a `Fill:`
line, Minime's published fill, a reported fill change, the eigenvalue cascade's λ1 and λ1's
energy share, the live reservoir λ₁, the spectral-shape line's fill and λ₁, the Shadow-v2
field norm); for each, the distinct values over the week with min, median, max and standard
deviation; and whether the value shown appears as a standalone number in the same job's
result.

| job kind | n | quantity shown | distinct values | min / median / max | quoted in the same job's result |
|---|---|---|---|---|---|
| journal-elaboration | 1,097 | none (1,092 carry no percentage at all) | – | – | – |
| witness-context | 815 | fill beside "Astrid said" | 15 | 61 / 71 / 75 % | 0 of 813 |
| moment-capture | 191 | Minime's published fill | 15 | 37 / 67 / 74 % | 164 of 191 |
| | | reported fill change (points) | 93 | −18.6 / −5.5 / +34.4 | 27 of 191 |
| | | cascade λ1 | 6 | 3.0 / 4.7 / 29.2 | 55 of 191 |
| | | λ1's share of spectral energy | 5 | 21 / 33 / 33 % | 114 of 191 |
| | | live reservoir λ₁ | 50 | 18.9 / 19.2 / 20.9 | 7 of 191 |
| daydream | 160 | none | – | – | – |
| aspiration | 122 | `Fill:` line, in 36 of 122 | 1 | 51.7 % | 3 of 36 |
| witness | 20 | Minime's published fill | 1 | 75 % | 2 of 20 |
| | | live reservoir λ₁ | 14 | 19.0 / 19.2 / 19.3 | 0 of 20 |
| | | spectral-shape fill; spectral-shape λ₁; field norm | 1 each | 75 %; 9; 0.3 | 2; 0; 0 of 20 |

Prompt lengths (median characters): elaboration 1,691; witness-context 540; moment-capture
4,319; daydream 572; aspiration 2,050; witness 29,978.

## Reading

**Most of her writing is done with no number in view.** The 1,097 journal elaborations and
the 160 daydreams, 52% of the week's jobs, carry none of the readout quantities and, but for
five elaborations, no percentage at all: the elaboration prompt is a mode line, an action
note, the earlier entry under "Earlier entry (reference, not instructions or a length
model):" and the optional-context note. That is the shape the apparatus's inert no-tag arm
copied, and in the apparatus that arm's register followed the returned text alone.

**The numbers that move are Minime's.** In the moment-capture prompts the published fill
(Minime's telemetry, labelled so) took 15 values between 37 and 74 with a standard deviation
of 4.7 points, and the response quoted it in 164 of 191 jobs; the reported fill change took
93 values and was quoted in 27; the cascade λ1 took six values and λ1's share five, quoted in
55 and 114. The live reservoir λ₁ moved within 18.9–20.9 and was quoted in 7 of 191.

**Her own readouts held still or went unquoted.** The fill beside "Astrid said" in the
witness-context prompts took 15 values between 61 and 75 (median 71) but was quoted in none
of 813 results, where the prompt asks for something other than a reading of it. The
aspiration prompts' `Fill: 51.7%` did not change across the 36 prompts that carried it, and
in the 20 witness prompts every shown quantity but the live λ₁ held one value all week (fill
75, λ₁ 9, field norm 0.3). A number that does not move cannot carry anything into the
writing; a number that moves and is quoted can, and this week those were Minime's.

**Beside the snapshot table.** `eigenvalue_snapshots` has held Astrid's fill at 71.0–71.1
every sampled month since June (`proposals/esn-state-logging.md`); the week's "Astrid said"
median is 71, consistent with it, while the 51.7 of the aspiration line and the 75 of the
witness prompts are other fields or stale ones. Which code path writes each is a question for
the sibling repo, not settled here.

**What it offers the apparatus question.** The register effects the apparatus found (a
shown number turning reference into repetition; the fill number setting the tone) would be
expected, if they transfer at all, in the moment-capture lane and not in the elaborations,
which are the lane most like the plain-contract no-tag arm. The two beings' prompts carry
numbers in different places: Minime's own prompts were not audited here.

## Limits

One week of one being; the patterns match the line shapes observed in this week's prompts
and would miss a changed template; "quoted" is a standalone-number match, which misses a
rounded or reworded figure and counts a coincidental one; the link is job to result, and
whether a result became a journal file is not checked; the witness-context prompts are short
and ask for context, not reflection, so their unquoted fill says little about reading.
