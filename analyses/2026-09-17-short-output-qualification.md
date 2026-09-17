# Short-output qualification stops on its first paired input

September 17, 2026. S-009’s six fixed cells were frozen before generation: steps
30/60/90, each with sensory-only and added-state input from the active-input fixture.
The control was existing prompt v2; the single candidate requested one sentence,
at most 24 words, one numerical observation and no copied coordinate list. The
12-request ceiling and stop-on-candidate-failure rule were fixed in advance.

The exact qualified `phi3:mini` digest was
`4f222292793889a9a40a020799cfd28d53f3e01af25d48e06c5e708610fc47e9`, served by Ollama
0.32.15 with context 4096, temperature 0, JSON mode and a 256-token ceiling. One
owned temporary loopback service was started on port 63594 and stopped afterward;
its lifecycle receipt verifies the endpoint was closed. No other service changed.

Only the first cell, step 30 sensory-only, was requested. The control ran first and
completed in 106 evaluated tokens. The candidate completed normally in 99 tokens
and parsed correctly, but contained **25 whitespace-separated words and multiple
copied measurements**. It therefore failed the declared bounds. The paired control
was already retained; the trial stopped after **two requests**, leaving the other
five cells unattempted. There were no retries or candidate changes.

The candidate’s displayed numerical values agree with supplied measurements at its
rounding precision. The control incorrectly reports tail share as 17%, while the
input supplies 0.06953402 (about 6.95%); it also copies an array. The control receipt’s
`passed` field tests normal completion and JSON shape only. It is not instruction
compliance, factual accuracy or an improvement score. These factual observations
are retained separately from the preregistered qualification decision.

**Qualification failed. Prompt version 3 is not registered and no new recording is
produced.** This bounded result does not establish that no other instruction could
work. The existing recordings, including the earlier partial model run, remain
unchanged.

Private evidence: `research/outputs/2026-09-17-short-output/` retains the protocol,
six exact input pairs, runner, service/inventory/version receipts, both submitted
requests and raw replies, validation, factual review and a full hash manifest.
Its counterpart is backed up on this Mac under Reservoir Research/Studies. The
protocol was frozen at preparation, before the service or any generation request.
