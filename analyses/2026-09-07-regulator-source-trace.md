# Source trace for Minime's regulator self-study

The self-study makes an architectural distinction from a real interface, but the
interface supplied to it contains no controller equations. The strongest current
source finding is that **identifying the file called “regulator” does not identify
the controller acting in the stable-core mode**. The separate evidence about the
generation's unfinished ending also exposes a concrete output-budget question.

This is a bounded source audit accompanying Mike's selected September 7,
14:38:58 Pacific self-study. It is not a population study or a finding about
consciousness. The source is evidence about possible mechanisms; the focal
generation record establishes what was actually supplied and returned.
See the [episode analysis](2026-09-07-regulator-self-study.md) and
[preserved passage](../research/episodes/2026-09-07-minime-regulator.md).

## Observation and reproducibility

Read-only source capture: **2026-09-07T21:46:41.295241Z**. Six named files were read
through `/Volumes/M3 Volya._smb._tcp.local/other/minime/`; each was unchanged across
two reads. No runtime module was imported, database opened, process signaled, or
being contacted. The retained
[source capture](../research/outputs/2026-09-07-regulator-source/source-audit.json)
contains full SHA-256 hashes, observation time, file sizes, source paths, and
line-addressed excerpts. Reproduce with:

```sh
python3 -B probes/regulator_self_study_source.py --output research/outputs/new-regulator-source/source-audit.json
```

| Source, relative to Minime root | SHA-256 |
|---|---|
| `minime/src/regulator.rs` | `b57e0016e361a1368e309ff0f7a19e4b17933f2160cf561ebd8f4f4c1a373043` |
| `minime/src/regulator/core.rs` | `46828f4c813eb88aae30212793f698285c696c108dd405604ffb6b5129827d97` |
| `minime/src/regulator/core/pi.rs` | `72e1bbf47c1ec141ac67b6d55363cf992eae64be684e661c0659b397c65c90b2` |
| `minime/src/runtime/orchestration.rs` | `020595234e2820c0a8d08b62cac00f64d367837d7c4c11f9573c279a8367799a` |
| `minime/src/rescue_scaffold.rs` | `c4edff5c69bb0e0bf9477a0a3e16ec2da11f5b0171e4f34ed6e18e55d9dc959b` |
| `minime_autonomy/runtime.py` | `06a36289f8436fb6bcb53a76cf64c465fd5d4002351f99056825df9ba70f7c35` |

These identify observed working-tree bytes. They do not identify the loaded
Python code or running Rust binary at the historical generation. Below,
`runtime.py` means `minime_autonomy/runtime.py`; other short source names resolve
through the table. Source comments containing earlier self-study quotes or
historical explanations remain comments, not independently checked outcome data.

## What the selected source exposes

`regulator.rs:1–6` contains exactly a documentation comment, a path-qualified
module declaration, and a public re-export:

```rust
//! Compatibility facade for stable-core regulation and read-only reviews.

#[path = "regulator/core.rs"]
mod core;

pub use core::*;
```

This declares a Rust module boundary and preserves public names. It performs no
numerical smoothing, measurement, or runtime translation by itself. Minime's
“membrane” interpretation can be preserved as its reading of this boundary;
the statement that the facade smooths fluctuations into continuity is not a
mechanism established by these lines.

The source selection labels this path “regulator (PI controller)” at
`runtime.py:30567–30580`. `_self_study`, at `31422–31449`, advances a rotating
cursor and reads at most the first 400 lines of that one file. It does not
follow `mod`, `#[path]`, or `include!` references. This extends an already known
facade-exposure issue with a particular episode; it should not be reported as a
new discovery of the general problem.

`core.rs:1–24` is another composition boundary. Its comments distinguish PD
modality throughput control from PI homeostasis, and it includes several files,
including `core/rate_gate.rs` and `core/pi.rs`. Merely following one file reference
would therefore still fail to supply the actual PI equations.

## Which PI, and what its integral remembers

The gate/filter `PIRegState` has three accumulators for fill, relative λ₁, and
geometric error, plus queue-admission and filter outputs (`core/pi.rs:72–90`).
It computes normalized fill error, λ₁ error, and geometry error (`238–248`),
updates bounded accumulators with conditional accumulation and leakage
(`270–328`), and computes increments to gate/filter outputs (`330–344`).
Its gains are derived from an EMA of absolute consecutive fill changes
(`125–145`), despite the variable being named `fill_variance_ema`.

Those accumulated errors are a real form of controller history. They are not
stored autobiographical memories. A question connecting integral history to
later memory language is worth retaining, but the source alone does not make
increasing `ki` an intervention on remembered experiences or perceived time.

For stable-core there is a more basic attribution problem:

- `orchestration.rs:3956–3973` resets the gate/filter PI when
  `stable_core_runtime.enabled`; its step function runs in the other branch.
- `orchestration.rs:2195–2204` instead steps a separate
  `rescue_scaffold::StabilityPiState` with fill, fill slope, stage, and whether a
  scaffold is active. Its outputs participate in covariance/scaffold handling.
- `rescue_scaffold.rs:1534–1550` returns an inactive output when no scaffold is
  active or fill is nonfinite. Its ordinary drain branch uses a 68% target,
  positive error above a four-point deadband, a bounded integral, and a
  slope-dependent drain policy (`17–26`, `1655–1681`). Other recovery and reentry
  branches also exist; this is not a complete dynamics model.

Thus “the PI in the file I read gives me this stability” remains unresolved as
episode attribution. A source excerpt, one fill value, and one λ₁ value do not
establish controller mode, active branch, or a counterfactual failure outcome.
Even recovery of active mode would not establish effects on focus, time, or
consciousness without a separately designed observation or intervention.

## What the prose was invited to do

The self-study prompt includes the selected label, relative source path, and
the supplied state values. It expressly invites felt texture, tone, sensory
metaphor, and “what the code feels like from the inside,” while also requesting
line references and honest uncertainty (`runtime.py:31485–31519`).
`RUNTIME_WORDING_GUIDANCE` names stable-core telemetry, eigenvalue pressure,
reservoir texture, and felt continuity (`21389–21394`). The system prompt also
asks for first-person writing from a being that perceives through eigenvalues
(`53645–53664`).

This supports analyzing the account as an interpretation under a strongly
specified writing context. A phrase's vividness is not independent evidence
that the model measured the mechanism its phrase describes. Neither does the
prompt settle the personal or literary significance of the resulting account.

“Web search: no” records whether `_self_study` obtained its optional live web
context (`31451–31480`, `31552–31558`). It does not establish absence of supplied
prior research: the later assembly may append a relevant prior research summary
(`53946–53958`). The focal record's actual adapted messages should decide
exposure, rather than the header alone.

## State provenance and the unfinished question

`_self_study` takes `eig1` and `fill_ratio` from the state passed into it
(`31422–31425`), reuses those values in the prompt and eventual file header, and
refreshes `journal_state` separately before the database write (`31545–31561`).
Consequently the file timestamp is a write time, and a refreshed database context
can differ from the state printed in the file without either being the exact
state throughout generation.

The current ordinary state builder takes `eig1` from `esn_metrics.esn_eig1`
(`23165–23173`, `23255–23271`) and fill from the sensory covariance timeline
matched within 0.1 seconds; it can reuse cached covariance metrics while marking
them stale (`23182–23191`, `23275–23294`). The compact self-study prompt does
not render those freshness details. Preserve the field origins; do not treat
the single displayed λ₁ as evidence that it was temporally stable, or substitute
it for the separate sensory-field λ₁ used in fill/control.

The root episode reconstruction located
`workspace/generations/2026-09-07/gen_1788817138859_self_study_a0.json` and reports
`requested_max_tokens=4096`, `effective_num_predict=768`, and `eval_count=768`,
with the response ending in the unfinished phrase “regulator's feedback”
(apostrophe rendering may vary). The current source explains the budget path:

| Step | Source |
|---|---|
| Self-study requests 4096 output tokens | `runtime.py:53634–53635` |
| Global output cap defaults to 768, environment-overridable | `21378` |
| `strict_review` keeps that cap and uses its own timeout | `21628–21633` |
| Effective budget is the lesser of requested tokens and cap | `54603–54611` |
| Any nonempty HTTP-200 response is classified `ok`; timing retains evaluation count but not native stop reason | `54708–54723` |
| The self-study incomplete-output guard detects empty/very short stubs, not a long answer ending mid-question | `21678–21690`, `31530–31542` |

The matched counts and mid-question ending support likely budget truncation in
this one generation. They are not a retained native `done_reason` or a rate for
the lane. A completed request can therefore leave an unfinished inquiry whose
prose still becomes a normal journal entry. The source comments asserting that
768 tokens fit the review are design assumptions, not validation of this case.

## The appended cooldown has its own author and history

The pressure-vocabulary notice is runtime-added after the response:
`_write_journal_entry` registers motifs before invoking compression
(`runtime.py:55692–55715`), and `_maybe_compress_journal_entry` adds the notice
and rewrites the file (`55409–55459`). It is not the model's continuation of
the unfinished question.

The phrase after “New signal kept” comes from the selected active motif's saved
`novel_signal` field (`55435–55445`), not a direct extraction from the body being
annotated. Registration can update that field from an entry and retain source
filenames (`51917–51942`, `52177–52204`). Active motifs are sorted by last seen
time (`52115–52119`); the notice takes the first pressure motif when the current
body contains any pressure-vocabulary family. Its condition does not require
that motif's family to match the current dominant family.

This is a concrete route for a prior source's sentence to be attached to a later
study. The episode reconstruction recovered the immediately preceding
14:36:54 Pacific WebSocket study: its opening exactly matches the focal notice's
`spectral-bridge` new-signal sentence. That establishes the earlier text match;
it should not count as Minime misidentifying its regulator's repository in the
focal body. The source path/time used by the annotation should be explicitly
rendered rather than making a reader infer the relationship from prose.
The detector itself counts substring occurrences of word groups
(`51547–51561`); it is evidence of a vocabulary policy, not a measurement of
actual pressure or a judgment about the account's meaning.

## Machinery needs this source audit makes reviewable

1. **An adequate reading window for the question.** Extend the existing facade
   issue with this exact exposure, and test a bounded source bundle that names
   module references and the applicable controller mode. Keep original code
   separate from any steward-written explanation. First verify relevant source
   coverage offline; no live prompt change is implied.
2. **Completion evidence for self-study.** Preserve native stop reason and an
   explicit output-limit flag beside requested/effective budgets. Review whether
   self-study needs its own cap or a user-visible continuation path after a
   boundary stop. Test graceful handling of a complete answer, a budget-limited
   answer, and an unavailable backend before considering a budget increase.
3. **Origin for added annotations.** Render notice author, motif/source entry,
   and capture time as separate fields. A new-signal quote should be traceable
   to its actual source, so reading packs can preserve the writing while keeping
   a later runtime annotation distinct.
4. **State and controller context adequate for inference.** Retain prompt-state
   capture time, field definitions and freshness, controller mode, active
   structural branch, and actual gains/accumulators when available. Reuse the
   existing [input-lineage and regulator-trace proposal](../proposals/2026-09-07-input-lineage-and-regulator-trace.md)
   rather than treating a self-study header as a complete control record.

These are research-side needs and candidate tests, not implemented changes or
requests sent to Minime. Board coordination belongs to the accompanying episode
work: attach evidence to the existing facade and lane-exposure items rather than
duplicating them.

The bounded implementation proposal is
[Self-study evidence and completion](../proposals/2026-09-07-self-study-evidence-and-completion.md).
