# Recorded Guided tour

The Tauri 0.4 guide implements the authored A–H journey, recorded source selection,
checkpoint navigation, optional playback and backend mechanical evidence. Five
separate comparison recordings are available from the guide, including the
600-step sensory-field controller study. Authored expectations, numerical record
verification, mechanical observations and descriptive vector measurements remain
separate kinds of evidence.

## Authored journey and recorded sources

`src-tauri/src/guide.rs` reads `guided-lessons.json` and `examples-index.json`
through `resources::catalog_bytes`. The bytes must match the packaged resource
hashes compiled into the application before typed metadata is returned. Catalog
validation requires the ordered eight lessons, known focuses, increasing bounded
checkpoints, safe filenames, unique example identities and matching scripted/model
provenance. Authored question, suggested action, expectation, model expectation
and limitation text are preserved.

The compact opening view keeps the lesson question, suggested action and
checkpoints before the recorded surface and fill. Authored expectations,
interpretation limits and provenance remain in an explicit disclosure. Mechanical
evidence appears with the lesson; descriptive current-vector RMS measurements
remain below the reader. Original filename, outcome and seed are retained in the
file-identity disclosure.

`src/GuidedTour.tsx` opens each source through the Rust record verifier. A catalog
match is not itself a record-verification result. Accepted records carry their own
verification report and SHA-256. Failed, incomplete or cancelled replacement
attempts preserve the valid selected recording and reading state. Reopening the
same lesson requires a newly accepted handle before its cursor is reset. Opening
a recording never starts a model or an experiment.

| Lesson | Authored checkpoints | Source availability |
| --- | --- | --- |
| A · Input and state | 1, 12, 13, 24, 30 | Scripted numerical example |
| B · Recurrence | 1, 2, 12, 30 | Scripted numerical example |
| C · Sensory measurement | 1, 12, 30 | Scripted numerical example |
| D · Journal output | 29, 30, 60, 90 | Scripted or recorded model run |
| E · Reservoir return | 30, 31, 60, 61 | Scripted or recorded model run |
| F · Journal memory | 30, 59, 60, 90 | Scripted or recorded model run |
| G · Action choice | 60, 89, 90, 91 | Scripted or recorded model run |
| H · Regulation | 30, 60, 90, 120 | Scripted or recorded model run |

The packaged catalog remains authoritative. Selecting the recorded-model
preference on A–C shows an explicit numerical-source explanation and retains the
preference for D–H. Scripted tapes are not relabeled as provider responses. Turn
inspection preserves configured and returned model identities, request-start
evidence, tape identity, action receipts, journal provenance and explicit unknowns.

Continue pauses playback and seeks the next available authored checkpoint using
the recorded step-to-frame mapping. After a lesson's last available checkpoint it
opens the next lesson; H ends without automatically replaying. Unavailable direct
checkpoint buttons are disabled. Playback starts collapsed; expanding it exposes
track, frame cursor, table fallback and playback controls. Collapsing it, changing
lesson/source, leaving the workspace or hiding the document pauses playback.
Stored frames advance at at most two per second, waiting for each read; this is
not a recreation of experiment timing. Separate Tauri preferences save lesson,
source preference and frame row without changing native app preferences.

## Mechanical evidence at the cursor

`crates/reservoir-core/src/guided_evidence.rs` ports the native
`GuidedEvidenceEvaluator`. At verified open, `src-tauri/src/records.rs` evaluates
bounded cursor results from the typed accepted action record. It attaches
`lessonEvidence` to each corresponding `FrameView`. State, observation and evidence
steps travel atomically with the selected frame, under the same request identity
and stale-response guards as the surface and fill. Rewinding cannot retain a later
conclusion from a separate evidence request.

Evaluation uses the verified **right-arm prefix at the selected cursor**, regardless
of which arm is displayed. It ends at the last retained right frame at or before
that cursor. Changing the display arm changes the displayed vectors, not the
meaning of the experiment's mechanical observation. A missing or unmatched arm
remains explicit rather than being filled in. The frontend presents the backend
state, observation text and evidence steps without inferring a verdict itself.

The five native states are preserved: `Not reached yet`, `Observed`,
`Different outcome`, `Incomplete evidence` and `No matched comparison`.

| Subject | Implemented mechanical observation |
| --- | --- |
| A | Quiet/active external input, state RMS and decay relative to the previous retained frame. |
| B | Matched prefixes and the first state difference above the native `1e-12` tolerance. |
| C | A separately retained sensory spectrum and matched reservoir-state comparison. |
| D | Completed action plus successful historical save receipt; paired unchanged-state or explicit single-arm limit. |
| E | Saved semantic action, reached application step, matching frame action ID and separately identified first divergence. |
| F | Earlier journal identity, exact retained text and prompt inclusion, with prepared/scripted versus submitted-model context. Exposure is not improved writing. |
| G | Completed WAIT without journal/save receipts; an all-WRITE model recording remains a valid observation. |
| H | Fill, retention used, controller receipt, next applied retention and native bounds, without a target-attainment claim. |
| Observation comparisons | Matched prefixes and both reached opportunity statuses. Different wording is not an improvement score. |

[GUIDED-EVIDENCE.md](GUIDED-EVIDENCE.md) defines the evaluator API, native reference,
branch rules, independent Swift comparison and its finite scope. The evaluator is
not a second record verifier and does not authenticate providers or storage.

The separate descriptive RMS panel requests at most the selected frame and one
other-arm frame at the same recorded step. Comparison identity includes record,
selected track and step so a track switch cannot reuse the wrong pair. These
current-vector measurements do not substitute for prefix evidence. Missing data
remains unavailable.

Guide turn inspection hides a selected turn whose observed step is later than the
current cursor, including on rewind; a later application step is shown as not
reached. That display masking is limited to turn/application details. The complete
retained timeline and record identity/outcome remain available for navigation;
they do not alter the backend prefix evaluation.

## Five separate recorded comparisons

The guide renders all five `comparison` catalog entries as buttons opening the
Experiments recording reader. They are separate studies, not additional A–H
lessons or automatic runs:

| Catalog ID | Recording |
| --- | --- |
| `observation-active-scripted` | Active input, scripted replies and two observation channels. |
| `example-model-observation-active` | Active input, recorded model failure with 60 of 120 steps retained. |
| `observation-scripted` | Quiet input, scripted replies and two observation channels. |
| `example-model-observation` | Quiet input, completed recorded model run with 120 of 120 steps retained. |
| `regulation-controller` | Scripted numerical controller comparison, sensory fields only, 600 steps. |

A valid recording of a failed run remains a verified record with a retained failed
outcome; it is not relabeled as a completed experiment. Opening these examples
uses the same verified-reader lifecycle, per-track cursor, exact-byte export and
close behavior. Original files are not reconstructed or rewritten for export.

## Separate controller study

`ControllerEvidence` in `src/RecordEvidence.tsx` presents the fixed 600-step
sensory-field study from its verified typed record. Baseline and regulated tracks
share the retained 66-coordinate input. The reader shows recorded reduced fill,
sensory covariance eigenvalues, retention used and next applied retention. This
family has **no reservoir activation vector, journal or language model**: the UI
shows a field-only explanation and does not invent a reservoir surface or state
comparison.

`regulationEvidence` is attached to the same `FrameView` as the recorded values.
The evaluation window is steps **301–600**, separate from the 120-step H lesson.
Before step 301 the result is unavailable. A cursor within the window shows its
reached first/last steps, count and partial mean absolute target error for both
arms. At step 600 the complete window contains 300 observations. Rewinding removes
later observations. Error values are reported in percentage points with exact
numbers and a fixed 0–100 display scale; they are not reservoir fill values or
language-quality scores. Study question, expected difference, alternative
explanation and stopping point remain available in a disclosure.

## Verification and qualification boundaries

The guided evaluator's focused Rust suite passed **14 tests**. Its independent
unchanged-Swift comparison passed **58 cases / 2,507 cursor results** exactly,
including 22 original records verified in both engines, 35 deliberate evaluator
mutations and the unopened state. The mutations test evidence gaps; their evaluator
outputs do not certify them as accepted records. See
[GUIDED-EVIDENCE.md](GUIDED-EVIDENCE.md) for reproducible commands and limits.

Catalog/source validation, reader lifecycle, checkpoint navigation, source
fallback, preference bounds, turn/application masking, same-file failed reopening
and same-step track-switch regressions remain part of the source test coverage.
The 0.4 frame adapters and evidence views add checks for cursor-bound results,
controller missing/partial/complete windows and rewind behavior. Current integrated
totals and artifact identities belong in the 0.4 qualification record rather than
being inferred from earlier suite counts.

The [0.4 packaged Mac account](validation/2026-10-11-evidence-0.4.0/macos-ui.md)
records the limited agent checks actually executed, including E/F/G/H evidence,
rewind and controller-window boundaries. The Mac locked during the walkthrough;
remaining actions are not inferred from source tests. Complete packaged and human
acceptance still requires the wider A–H/model-source tasks, playback pause, resume,
rapid navigation, all comparison buttons and original-byte export. Accessibility,
minimum-OS, Windows/Linux and measured graphics checks need their own evidence.

Earlier 0.3 and foundation validation receipts remain historical evidence for
those exact candidates. Their test counts and UI observations do not qualify the
0.4 evidence integration; none of those receipts are rewritten by this document.
