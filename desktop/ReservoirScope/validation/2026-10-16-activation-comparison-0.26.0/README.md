# Activation comparison — October 16, 2026

The new bounded attempt completed one six-entry trace sequence, then stopped
before its second model load because the resource-preparation window expired.
The three-condition comparison remains incomplete. No inference was retried and
no admission threshold was changed. No live Being service was contacted or changed.

The [prospective study](../../../../research/studies/2026-10-16-activation-comparison.md)
and [exact protocol](../../../../shared/reservoir-scope/activation-comparison-20261016.json)
were committed as `ed8731c` before dispatch, after runner `7d3c930`. The new runner
accepts a separate protocol and retains timestamped resource observations,
protocol and runner hashes, and a limited post-exit worker-command observation.
All 17 runner tests passed using synthetic processes and clocks. An independent
source review found no blocker; sampling starts can be slightly more than ten
seconds apart because the interval follows completion of each bounded sample.
The retained timestamps expose the actual spacing.

The same preserved inference binary, pinned worker/runtime, calibration,
observations, seed, condition order, prompt and previous-prose policy were used.
Only resource preparation changed. The binary SHA-256 remains
`e2d332c0dcc84b657016338db73dccb19dbb97f8a295a19a6fc26da6ce60cb0e`.
No new application package or cross-platform qualification is claimed.

## Execution boundary

Private evidence is retained under
`research/outputs/activation-comparison-20261016/comparison-01/`.

| Condition | Observed outcome |
| --- | --- |
| Decaying trace / Reading A | Readiness reached on the fourth sample, after three consecutive healthy readings. Rust admitted at pressure 1 and 34% free. Completed 12 quiet observations, six journals and 121 numerical steps. Replay passed. |
| No steering | Preparation exhausted its 120-second window after 12 samples. No CLI, worker, quiet capture or journal request was dispatched. |
| Recurrent | Not started after the stop. |

The trace preparation ran from 15:13:36 to 15:14:06 UTC. The second preparation
ran from 15:16:11 to 15:18:11 UTC. The runner's post-exit process observation
found no exact configured Python worker command. That observation is scoped by
command identity; it does not provide a retained owned-child PID or prove a
particular prior kill/wait outcome. The [resource audit](RESOURCE-AUDIT.md)
preserves the earlier evidence and its causal limits.

## Mechanical evidence

The [mechanical summary](mechanical-comparison-summary.json) checks the retained
session `activation-1792163647254165000`. Twelve quiet captures sampled zero
tokens. All six journals ended with EOS within the original ceiling, producing
3,758 content tokens. Across 7,603 processed journal positions, the requested
1% residual intervention measured 0.9974981107540175%–1.0184566783300046% after
bf16 rounding. Eighteen projected captures, comprising 576 coordinates, match
independent Float64 recomputation within the original tolerance.

All six exact journal saves were verified before feedback application at steps
21, 41, 61, 81, 101 and 121. The Rust verifier passed 48 retained events and
121 steps without contacting a model. The updated read-only analysis probe also
passed against the original pilot before this new attempt began. These checks
establish retained mechanical consistency; the absent unsteered and recurrent
outputs still prevent an account of which words steering changed.

## Repeat and complete-sequence reading

The [same-condition comparison](repeat-and-resource-summary.json) finds all six
journal texts identical to the original trace run, with matching retained token
sequences, activation vectors, projected inputs and final numerical state. This
is an exact repeat under the frozen settings. It is not an independent sample of
writing, evidence of a benefit, or the missing comparison with another condition.

A fresh reader read every complete entry with allocation concealed and saved its
[initial note](READING-BLIND.md) before disclosure. It had general research context
from required repository guidance, including NOW.md; it had not read the earlier
experimental prose or readings. The [reading account](READING.md) separates that
interpretation from the later disclosure of prompt, memory policy and allocation.
The lead collaborator also read all six complete entries with allocation known.

## Scope and next prerequisite

The original pilot remains untouched. The post-stop check found all 209 files
matching the before-work inventory and passed 30 frozen-identity checks. The
read-only probe is `probes/2026-10-16-activation-preservation.py`; the private
closure receipt is `research/outputs/activation-comparison-20261016/preservation-check-02.json`.
The earlier check-01 is also retained and predates the preparation timeout.
The [closure receipt](closure-receipt.json) binds the frozen plan, outcome,
reading packet, before/after-disclosure notes and analysis artifacts by hash.
The runner's original result remains unchanged; reading status is recorded here
after the retained sequence was read.

The model and numerical engine were unchanged, so the prior mechanical
qualification remains the relevant qualification for them. The new preparation
logic has its own tests and actual observations here. This stopped attempt does
not establish a three-condition writing result or repair the missing baseline.
Stable headroom for the intended conditions is the next execution prerequisite.
Title-cue and previous-prose contrasts require separate prospective protocols;
neither was run as an extension of this attempt.

To reproduce the retained-data analyses, run
`probes/2026-10-15-activation-pilot.py` on the new comparison,
`probes/2026-10-16-activation-repeat.py` on the original pilot and new comparison,
and `probes/2026-10-16-activation-preservation.py` with the before-work inventory.
Each command's help gives its arguments. Choose new output files outside the
experiment directories; the probes refuse to overwrite an existing result.
Only the mechanics probe requires the pinned NumPy runtime. None runs a model.
