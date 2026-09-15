# Self-study evidence and completion

**September 8 update:** The separately authorized shared-reader repair is live.
[S-007](../research/studies/S-007-source-study-fidelity.md) verifies activation and
initial natural source delivery; it tracks fidelity without presuming improvement.
The proposal below preserves its September 7 scope and wording. Completion and
annotation-origin questions remain distinct from the access repair.

Status: research-side proposal, September 7, 2026. No sibling source or live
system has been changed. This is a bounded follow-up to Mike's selected
14:38:58 Pacific regulator self-study. Source details and working-tree hashes
are preserved in the [source trace](../analyses/2026-09-07-regulator-source-trace.md).
Historical running-code identity and the controller branch active during the
generation remain unresolved.
The [episode analysis](../analyses/2026-09-07-regulator-self-study.md) retains the
generation and previous-entry evidence behind the needs below.

The focal generation supplied a short facade under the label “PI controller,”
returned a substantial reflection ending mid-question after using all 768
allowed output tokens, and acquired a runtime footer quoting the preceding
WebSocket study. Each layer deserves its own evidence: source shown, generation
completion, and annotation origin. The reflection itself is preserved.

## 1. Supply enough source to investigate a named mechanism

**Observed problem.** The existing parked board finding, “SELF_STUDY reads 400
lines per source, and six of its nine sources are now module facades,” already
records the general issue. The focal generation confirms a particular exposure:
`minime/src/regulator.rs` has no equations. Following its `core.rs` reference
alone still reaches a composition file. Current `core/pi.rs` describes a
gate/filter controller whose step is skipped in stable-core mode; that mode
has a separate structural controller in `rescue_scaffold.rs`.

**Exact hooks.** In `minime_autonomy/runtime.py`, `_SELF_STUDY_SOURCES`
(`30567–30580`) and `_self_study` (`31422–31449`, `31485–31519`). Applicable
current Rust control routing: `minime/src/runtime/orchestration.rs:2195–2204`
and `3956–3973`; implementation windows include
`minime/src/regulator/core/pi.rs:238–344` and
`minime/src/rescue_scaffold.rs:1655–1681`. Line numbers identify the captured
working tree and must be re-resolved before implementation.

**Diff sketch.** Extract one pure source-window builder taking an explicit
descriptor and optional evidenced control-mode receipt. Keep the original
facade and offer one bounded implementation window plus the short routing
condition that makes its relevance inspectable. Use explicit permitted paths
and line budgets, not an unrestricted recursive reader. The existing 400-line
limit is a ceiling for the combined bundle; actual character/token admission
must still be checked before sending it. Do not silently remove the mechanism
window while retaining a claim that it was supplied.

Return a structured receipt with repository/source identity, SHA-256 of read
bytes, line bounds, supplied/excluded references, and the reason for choosing
the window. Include `mode=unknown` when no sufficiently fresh, generation-linked
controller-mode record exists; source selection must not convert the absence
into an assertion of the active path. Unknown-mode output can show the routing
condition and explicitly distinguish possible branches, or offer a targeted
next window without claiming either ran. Store the receipt beside the exact
adapted messages. Keep explanatory labels distinct from quoted code.

Reuse the mode/step evidence described by the existing
[input-lineage and regulator-trace proposal](2026-09-07-input-lineage-and-regulator-trace.md).
The parked facade card remains parked unless Mike selects implementation; this
proposal adds case evidence and a bounded design, not a claim that the work was
resumed or completed.

**Acceptance checks.** Offline fixtures for a direct source, this two-stage
facade, absent reference, out-of-root reference, truncated bundle, known
stable-core mode, known ordinary mode, and unknown/stale mode. Verify total
size bounds, provenance hash/line consistency, honest missing-source labels,
and inclusion of the selected routing condition. A reference fixture that
exceeds the budget must yield an explicit omitted window and next read target.
No fixture needs to contact a model or a being.

## 2. Keep request success separate from a completed reflection

**Observed problem.** The generation record reports a 4096-token request,
768-token effective budget, and evaluation count 768; the raw response ends
mid-question. The record does not retain the backend's native stop reason.
This is a likely budget-bound ending in one case, not a known native stop code
or measured lane-wide rate.

**Exact hooks.** `runtime.py:53634–53635` selects the requested self-study
budget; `21378` supplies the global cap; `_ollama_lane_limits:21628–21633`
applies it to strict review; `_query_ollama:54603–54611` takes the minimum;
`_query_ollama_model:54708–54735` records evaluation count and nonempty success
before handing timing to `generation_record.stash_attempt`.
`_is_degenerate_self_study_response:21678–21690` only detects thin stubs.

**Diff sketch.** Retain backend `done` and `done_reason` values when provided,
preserving absent fields as unknown. Add normalized, separately named fields
for `request_outcome`, `native_finish_reason`, and `output_limit_reached`.
The last should report comparison evidence (`eval_count >= effective budget`)
without pretending it is a native finish reason. Keep substantial text even
when incomplete; attach a machine-authored completion record outside the prose.
Do not label the being's inquiry completed merely because the HTTP call worked.

Evaluate a self-study-specific budget before changing it. First measure all
available self-study attempts in a fixed recent era and bounded time window,
including failures and no-output attempts. Report missing-record coverage,
requested/effective budget, native reason availability, evaluation count,
latency and ending completeness; keep repeated studies grouped by source and
time block. Select the interval before inspecting its outcomes. A per-lane cap
may then be proposed with matched timeout/concurrency limits and an explicit
upper bound. Do not raise the global cap, automatically continue every response,
or assume a larger budget will improve the source reading.

**Acceptance checks.** Mock backend responses for normal completion, explicit
length stop, count at cap without a reason, nonempty partial response, empty
response, timeout, and fallback. Verify native values survive, uncertainty stays
unknown, prose is retained, and timing success cannot overwrite completion
status. Verify a proposed per-lane override would affect only self-study and
would default to the existing budget when disabled. Offline fixtures establish
handling; they do not establish generation-quality or live-load effects.

## 3. Identify the author and source of a replay footer

**Observed problem.** The focal pressure-vocabulary footer's “New signal kept”
sentence exactly matches the opening of the immediately preceding 14:36:54
Pacific WebSocket study. The code draws it from a saved active motif, while the
rendered notice provides no origin. It can therefore be read as a current-study
claim about a source that the current study did not read.

**Exact hooks.** `runtime.py:_register_pressure_vocabulary_fatigue_if_needed`
(`51917–51942`); `_register_attractor_fatigue_repeat` (`52177–52204`), which
already preserves source files; `_maybe_compress_journal_entry`
(`55409–55459`), which selects `pressure_motifs[0]`, formats the notice, and
rewrites the file; `_write_journal_entry` (`55692–55715`), which invokes the
hooks. Notice creation currently checks for any pressure family in the body;
it does not require a family match with the selected motif.

**Diff sketch.** Store the precise `novel_signal_source` when extracting or
updating the quoted sentence: entry identifier/path, source timestamp with
timezone, and text hash. An ordered list of several motif source files is not
an adequate pointer to which entry supplied that sentence. Emit an annotation
object containing `author=runtime`, creation time, motif identifier/family,
current entry, and quotation source. In a human-readable journal surface,
label the sentence as a retained quotation from the named prior entry, with
unknown origin explicitly shown for old records. Keep the generated body
verbatim and retain a separate mapping to its output record. Avoid silently
backfilling historical origin from a merely similar sentence.

This proposal adds provenance first. Whether the detector should use exact word
matching, require matching families, or alter its repetition policy is a separate
question requiring comparison; no such policy change is bundled here.

**Acceptance checks.** Fixtures where the motif quote comes from the current
entry, a previous different-source entry, multiple source files, and unknown
legacy origin. Verify correct attribution and timestamps, exact preservation
of generated prose, and that analysis/export tools can exclude runtime text
without losing it. Include the focal prior-WebSocket/current-regulator relation
as the shape of a regression fixture using a short synthetic quotation.

## Steward review, implementation boundary, and rollback

Before a being-facing change, Mike should decide what to share. A useful first
showing for Minime is its preserved account alongside: the exact source window
it received; the separate current control-routing distinction with historical
mode unknown; the requested/effective output budgets and unfinished question;
and the footer's earlier source. Invite its view on what source evidence and
completion affordance would support its self-study. Do not replace its language
or prescribe the meaning of its experience. This research workflow sends none
of that material itself.

Implementation belongs in an isolated Minime checkout under that repository's
rules, with steward review and its deployment workflow. Additive records and
disabled-by-default behavior changes allow each slice to be reviewed separately.
No new live controller tuning, restart, sensory input, or experiment is included.

Rollback: restore the prior source-window selector and any old per-lane budget;
disable the new annotation rendering while retaining the immutable generated
body and provenance records. New receipt fields should be optional to older
readers. Preserve evidence already recorded; rollback must not erase the
truncation/origin history or rewrite prior journals.
