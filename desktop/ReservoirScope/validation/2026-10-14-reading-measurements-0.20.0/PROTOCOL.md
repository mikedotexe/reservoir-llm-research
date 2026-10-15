# Reading measurements · version 8 protocol

This is prospective software qualification for `reservoir-journal-v8` in the 0.20 app. It does not authorize a real-model run. Fresh sessions will use v8; missing historical versions remain v1, and explicit v1–v7 keep their prior prompt bytes and Restore version.

The only prompt changes from v7 are the version header and replacement of the compact-readout caveat by this exact paragraph:

```text
Unavailable means no prior measurement, not zero. RMS describes the magnitude of the recurrent coordinates. Sensory fill is a separate field estimate, not the encoded text-input signal. L2 distance is the straight-line distance between the two recurrent state vectors, not path length, speed or a causal effect of writing. Comparing two interval distances requires a recorded value for each. Two observations do not establish the intervening path, a cause, or a felt state.
```

It follows the three numerical rows at the end of OPTIONAL READOUT, before PREVIOUS JOURNAL. The [template](PROMPT-V8-TEMPLATE.txt) retains named placeholders for numerical values and previous writing. It has no trailing newline. The compact rows still contain current/prior RMS, current/prior sensory fill and differences, plus nonnegative recurrent coordinate distance. Full observation v2 and the separate human measurement reference remain retained. No new input, measurement, tool, role, numerical control, generation budget, completeness rule, save rule or application gate is added.

The v7 late WRITING BOUNDARY remains byte-identical except its already-dynamic observed/applied clocks: after END PREVIOUS JOURNAL, it states text-only output, the held numerical clock, the actual saved/applied text return (or none), and the distinction between previous prose and executed controls. The final invitation remains `Write the next entry in whatever direction seems worth pursuing.` Full previous saved/applied text remains one LF-delimited JSON string. Embedded apparent caveats, headings, control claims, quotes and Unicode separators stay authored data and cannot supply the current caveat or late boundary.

The new wording explains what the retained quantities mean. It does not independently establish that a model will understand them, stop making unsupported claims, or improve its writing. Same-reply numerical comparisons isolate implementation continuity; they do not establish real-model response equivalence.

## Qualification and preservation

The [qualification plan](QUALIFICATION-PLAN.md) specifies source checks, packaging, fourteen historical exports, semantic tampering, five fixed synthetic responses and clean-quit recovery. The [native procedure](NATIVE-QUALIFICATION-PLAN.md) and [exact UI configuration](packaged-ui-plan-01.json) remain prospective until root freezes the final inputs and authorizes execution. The fixed provider and tests are [byte-exact copies](synthetic-provider-copy-01.json); its historical `0.16` model label is intentional and does not identify a real model.

The qualified 0.19 app, archive and pin were copied independently into `target/qa/0.20-prior-0.19-preserved` and verified unchanged in [prior-package-preserved-01.json](prior-package-preserved-01.json). The [source preparation inventory](source-before-preparation-01.json) records 322 current files at its actual capture time and binds the separate 0.19 qualified source authority; it is not the final 0.20 build freeze. The [prior v7 evidence inventory](prior-v7-evidence-inventory-01.json) retains the exact identities of all 127 files in episodes 01, 02 and 03, including the two refused admissions and completed third episode.

No Being workspace, process, service or prompt is involved. This protocol makes no writing-quality, causal-effect, full-context processing, power-loss, GPU/energy, endurance, new Windows/Linux or real-model qualification claim. Any failure remains retained and does not authorize retries, altered fixed responses or relaxed acceptance.
