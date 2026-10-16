# Reservoir Scope parity ledger

**Current baseline: 0.25.0 / `reservoir-journal-v8` · Reviewed October 15, 2026**

This matrix separates implemented behavior, executed qualification and remaining
work. A verifier pass does not establish complete workflow parity, scientific benefit
or live Being interoperability.

[Current status and bounded backlog](../../desktop/ReservoirScope/STATUS.md) ·
[Accepted roadmap](../../TAURI-ROADMAP.md) ·
[Desktop preview](../../desktop/ReservoirScope/README.md) ·
[Exact pre-housekeeping history](PARITY-HISTORY-2026-10-15.md)

## Current position: 0.25 journal-first reading

[0.25 qualification](../../desktop/ReservoirScope/validation/2026-10-15-journal-first-0.25.0/README.md)
pass 431 frontend tests in 46 files, TypeScript/Vite, reference checks and the
macOS package build. Rust tests and Clippy reuse the 0.24 results through exact
comparison of 164 inputs with five validated application-version-only substitutions;
they were not rerun. Complete selected prose and Earlier/Later precede the history
list; live visuals sit beside reading on wide screens and below it on narrow screens.
Current sensory fill stays distinct from the selected journal’s measurements.
Setup and [Getting started](../../desktop/ReservoirScope/GETTING-STARTED.md) explain
local-model selection and the included save/readback/next-step/memory loop. Offline
writing remains the default; checks and generation remain explicit actions.

The [native walkthrough](../../desktop/ReservoirScope/validation/2026-10-15-journal-first-0.25.0/MACOS-UI.md)
passes at 1280 × 860: three scripted journals at 30/60/90 first apply at 31/61/91,
then hold at step 91. Earlier/Later/Follow latest, the current-versus-selected fill
distinction, 125%/200% zoom and reset pass. Normal quit and offline replay preserve
all 19 recorded files. Pinned selection during new arrivals, native compact resizing
and export/recovery were not repeated. Production v8, controller arithmetic and
persistence are unchanged. The personal regulator’s 68%
target and 64–72% error deadband are disclosed as controller references, not a proven
special state, a fill rate or a guaranteed outcome. No new real-model, compact-window,
endurance or GPU/energy qualification follows from this presentation pass.

### Prior 0.24 compact reading

[0.24 qualification](../../desktop/ReservoirScope/validation/2026-10-15-compact-reading-0.24.0/README.md)
adds anchored history windows, stable selected journal positions under arrivals,
keyboard-focusable evidence and native View-menu zoom. All 427 frontend tests in
46 files, 224 core and 203 desktop tests, TypeScript/Vite, reference checks and both
strict Clippy checks pass; two opt-in desktop tests remain ignored. The distinct
46-file macOS package is archived and ad hoc signed. The
[native walkthrough](../../desktop/ReservoirScope/validation/2026-10-15-compact-reading-0.24.0/MACOS-UI.md)
confirms zoom/reset, Library details, skip-link focus and evidence-panel scrolling.
Its scripted run creates 36 journals and naturally holds at live/saved step 361.
Pinning/refresh, Older/Newer, the full twenty-row boundary, outside-window Earlier,
workspace return and explicit Follow latest pass during arrivals. Normal quit
leaves owned PID 9390 absent. Its outer screenshot is 1830 × 1050 with
100%/125%/200% zoom. Native export/recovery were not rerun in that walkthrough. The corrected
[post-quit replay](../../desktop/ReservoirScope/validation/2026-10-15-compact-reading-0.24.0/ui-session-check-02.json)
passes all 36 journals and 179 segments with all 217 files unchanged and no recorded
provider dispatch; the pre-replay wrapper refusal remains preserved. Production v8,
numerical and saved-record contracts are unchanged.

The separate [resize retry](../../desktop/ReservoirScope/validation/2026-10-15-compact-reading-0.24.0/MACOS-COMPACT-RETRY.md)
uses the unchanged package and a fresh isolated Library. Edge/corner gestures leave
the outer screenshot at 1280 × 860; **900 × 700 and 720 × 600 logical content-area
targets remain unqualified**. Visible 125%/200% zoom and reset work. At 200%, setup,
Library metadata, Observatory controls and an explicitly restored completed
scripted journal remain reachable/readable; Earlier moves Journal 36 to 35.
Restore stays paused with Resume disabled by the exhausted 361-step bound. The
copied manifest alone changes (generation 1→2, revision 543→544, budgetReached→paused);
216 nonmanifest copies, all 217 original session files, prior validation and package
bytes remain unchanged. The copied ownership-marker omission/correction is retained.
Normal quit leaves PID 16834 absent. No Start/Resume, new arrivals, export, full
recovery-workflow or GPU qualification is added.

### Prior 0.23 direct personal sessions and retained reading

[0.23 qualification](../../desktop/ReservoirScope/validation/2026-10-15-navigation-0.23.0/README.md)
adds My reservoir as the initial sixth destination alongside the native five.
Preparation history has one Observatory reader and a Library shortcut. Accepted
reports/disclosures, subview scroll and unchanged-query Library list position
survive return; repeated setup guidance is trimmed. All 417 frontend tests in 46
files, TypeScript/Vite, reference checks and the distinct 46-file macOS package with
local ad hoc signing pass. Rust checks are reused by exact comparison of 164 inputs
with five version-only substitutions, not rerun. Scoped native checks pass for
preparation-report/disclosure and Library-position retention, and a pinned journal
across workspace changes and one new arrival. The scripted run reaches 61 steps
with two saved/applied journals, then quits normally. Its unchanged 13-file stored
bundle passes the same-build verifier; native export/recovery were not rerun.
Production v8, backend and record semantics remain unchanged.

### Prior 0.22.1 everyday research language

[0.22.1 qualification](../../desktop/ReservoirScope/validation/2026-10-15-research-language-0.22.1/README.md)
simplifies headings/controls and puts engineering metadata behind About and local
disclosures. Scientific interpretation, failures, save/application states and
production v8 remain unchanged. All 413 frontend tests, TypeScript/Vite, reference
checks and the distinct macOS package build pass. Prior Rust checks are reused by
exact input equality with only the five version-metadata substitutions; they were
not rerun. Scoped native inspection covers revised headings/About/disclosures and
one capped offline scripted journal, saved at 30 and applied at 31, then clean quit.
Collaborator acceptance remains open.

### Prior 0.22 reference fields and state spectrum

[0.22 qualification](../../desktop/ReservoirScope/validation/2026-10-15-observatory-fields-0.22.0/README.md)
adds backend-derived magnitude, deviation, reconstruction/residual and the full
128-mode sample-covariance spectrum to the retained trajectory. All 224 core, 199
desktop and 413 frontend tests, TypeScript and both strict Clippy checks pass; two
opt-in desktop tests remain ignored. Independent Swift comparisons cover 56 mode
selections. The distinct 46-file macOS package/archive passed identity and local
ad hoc signature checks. Native inspection covered exact fields at rows 0 and 511,
spectrum provenance, retained preferences, fallback and context recovery. The resize
gesture did not change the window size, so compact layout remains unqualified.

A 600-second main-PID capture completed 121 samples without errors, with separate
marked idle/playback/minimized/restored phases. It excludes WebKit helpers, GPU,
power and total-app memory. This is bounded descriptive resource evidence, not
complete M3, endurance, efficiency or platform acceptance. See the
[field contract](../../desktop/ReservoirScope/RECORDED-STATE-FIELDS.md) for the
distinctions between capture covariance, per-row energy and sensory history.

V8 changes only the prompt version and compact readout explanation. Topic/form,
full eligible prior prose, writing boundary and numerical/save/application mechanisms
remain unchanged. Historical v1–v7 retain their contracts. The reader adds
Earlier/Later navigation, explicit pinning and closed optional evidence without
rewriting model-authored text.

The [0.20 qualification](../../desktop/ReservoirScope/validation/2026-10-14-reading-measurements-0.20.0/README.md)
records 219 core, 198 desktop, 375 frontend and 41 helper tests, TypeScript and both
strict Clippy checks; two opt-in desktop tests remain ignored. Fourteen historical
exports replayed with all 665 files unchanged; seven semantic negatives were rejected.
Native synthetic save/held-fifth/export/recovery passed, preserving all 27 nonmanifest
files. Native reading covered within-page navigation and a paused historical v7
restore; cross-page/new-arrival races have frontend rather than native qualification.

The separate [real v8 episode](../../desktop/ReservoirScope/validation/2026-10-14-v8-writing-episode01/README.md)
completed twelve saved/applied journals and eleven exact previous-text joins. Export
and paused recovery preserved all 72 nonmanifest files. Full readings found continuity
and repetition, correct selected current values and mistaken interval directions.
These are bounded writing observations, not an accuracy or prompt-benefit guarantee.

Standalone order and time/distance diagnostics did not change production. The
[first source-role window](../../desktop/ReservoirScope/validation/2026-10-15-context-sources-01/README.md)
refused the changed installed runtime before spawn. Separate 0.40.5 source/identity
review and 84 synthetic helper checks passed before the second window; neither of
the first two windows executed the model.
The [new window](../../desktop/ReservoirScope/validation/2026-10-15-context-sources-02/README.md)
retained exact prompts and bounds, then refused its one admission at 31% free memory
against the unchanged 35% threshold. All twelve slots are unstarted; no model service
or provider request began. Both refusals and source evidence remain exact.
A separately identified third source-role window adopts the user-approved provisional
30% reported-free floor and passed admission at 42%. It completed all twelve replies
within 172.5 seconds and stopped the owned service cleanly. Its final 14 preparation
and 97 synthetic runtime/admission checks passed. Full readings found a local benefit
but also invented present measurements; the candidate was not promoted. The
[separate report](../../desktop/ReservoirScope/validation/2026-10-15-context-sources-03/README.md)
retains the reading-order deviation and additional independent assessment. These
standalone outputs did not enter app journals or feedback, and success at 42% does
not qualify operation near the relaxed floor. Production v8 remains unchanged.
See [STATUS.md](../../desktop/ReservoirScope/STATUS.md) for the active backlog.

## Capability matrix

| Area | Implemented now | Still required |
| --- | --- | --- |
| Navigation | My reservoir is the initial sixth destination alongside the native five; entering begins no run; accepted readers/disclosures and subview scroll survive return; 0.24 native scripted checks cover anchored history and selected ordinals across the twenty-entry boundary during arrivals; playback pauses when hidden | Actual compact dimensions, broader accessibility, other-platform and collaborator workflows remain open |
| Stages 1–4 | Rust numerical replay, bounded Unicode text contract, scripted headless generation; recorded playback, finite incremental desktop stages and optional local responses for 3/4 | Unqualified Unicode/parser cases; all-target fresh-run lifecycle qualification |
| Exploration | Rust per-step control replay, contribution/noise/state checks, sensory reset/resume; fresh pulses, boundary controls, history and finite scheduling | All-target lifecycle and usability qualification |
| A–H actions | v1/v2/v3 replay; all 22 authored Library examples; tape, memory, save and feedback checks; verified-prefix mechanical evidence; fresh standalone A–H and B–H predecessor pairs in independent scripted and fixed tape modes, optional local-model D–H, real per-arm memory reads, WAIT/WRITE and H control; D/D observation pairs with alternating request order | All-target paired lifecycle qualification |
| Scientific presentation | 0.25 leads with selected journal prose and a separately labeled current sensory fill percentage; signed state, exact coordinates/input/noise, sensory spectrum and reduced fill; retained trajectory, fixed-range reference fields and whole-capture state covariance spectrum with separate row-energy evidence; unavailable values explicit | Broader controls, compact-layout, accessibility and platform visual acceptance |
| Writing/return | Exact prompts, replies, encoding, observation/application steps, saved/failed journal meaning, tape identity | Finite D–H and personal sessions use write/readback and next-step gates; eligible saved memory is physically reread. Long-duration and all-target qualification remain |
| File interchange | Original-byte exports; checked one-case derivatives preserving all embedded evidence and references; invalid replacement retains reading | All-target file/lifecycle qualification |
| Guided tour | A–H authored journey and native evidence evaluator; observation comparison; scripted/model provenance; Continue/pause and cursor masking | Broader platform and collaborator acceptance |
| Controller teaching study | Independent 600-step two-field replay; exact projections; controls and summary; reached 301–600 evaluation with rewind; fixed fresh incremental generation, complete-only portable saves, field-only views and prefix detail reads | All-target packaged qualification; distinct from H and recurrent-state experiments |
| Library | Verified atomic imports, duplicate SHA identity, SQLite metadata search/filter/recents, paginated virtualized results, visible diagnostics/rebuild; distinct created/imported origins and immutable fresh snapshots; transactional bundled catalog refresh on package/resource upgrade | Cross-platform storage/large-library performance qualification; native backport evaluation |
| Reviewed cases | Embedded evidence hashes, Unicode quotations/references, authored classifications/limits, inert material links, temporary reading, exact catalog export and checked selected-case derivative | Full accessibility/collaborator tasks |
| Geometry | Packet/chain hashes, ordered references, 128 vectors, unsigned clocks/gaps, RMS checks, explicit synthetic example and reading retention | Platform visual/accessibility review; live interoperability is not claimed |
| Text/integer contract | Retained Swift ASCII and bounded Unicode corpus; decimal-string wide integers at IPC; response integer-token and canonical-Unicode comparison checks | Unqualified Unicode clusters/scalars, ambiguous provider parser forms and canonically duplicate response source-hash keys |
| Desktop coexistence | Separate identity/store path, one window/instance configuration, scoped commands | All-target close/quit/relaunch, accessibility, installation and upgrades |
| Observatory recordings | Independent 507-sample clocked fill history and 1,024-row ordinal state replay; fill sphere/reference zones, exact coordinates and retained sensory direction estimates; linked PCA trajectory, reference fields and all 128 capture eigenvalues. Field/mode/projection preferences survive workspace return | Compact-window, broader controls/accessibility and visual qualification; selected feeds remain separate; no claim of complete M3 |
| Response evidence | Native immediate boundaries with exact Float32 differences, all receipt events, explicit external opening, immutable replacement checks and original exports; separate 65-boundary esn-divide result with paired surfaces and return-threshold inspection | All-target workflow/visual qualification; selected-file observation belongs to the later read-only feed tranche |
| Preparation history | One Observatory reader with a Library shortcut; selected reports/disclosures survive return; separate original unavailable attempt, unexecuted correction, failed partial retry and four earlier examples; exact exports and current-verifier opening | All-target dialogs, accessibility and collaborator review |
| GPU workload | Event-driven surfaces/fill sphere, bounded pixels, invisible suspension, buffer reuse and exact fallback; 0.22 native context recovery and a short main-PID CPU/RSS sample | Attributed WebKit/GPU/power/total-app memory, frame pacing, longer workload/contention and context recovery on each target; current sample does not prove savings |
| Fresh persistence | Serialized atomic journal publication/readback, retryable pending candidates, terminal failed-save retention, bounded checkpoints including a completed half of a pending pair, arm-bound candidate saves and explicit recovery exports; unsaved close guard | Physical crash/power-loss and all-target storage/UI qualification; automatic resume is intentionally absent |
| Local models | Explicit configuration/readiness and bounded generation, cancellation, held clocks and retained outcomes for stages 3/4 and independent D–H/pairs; sustained owned-model episodes through v8, exact save/application/memory evidence; optional provider-reported prompt counts | Finite-recipe real-service checks, separately qualified additional model/runtime combinations and all-target behavior; input counts do not prove full context processing; selected feeds remain separate |
| Personal sustained loop | 0.25 journal-first layout over unchanged v8 open writing, exact eligible prior prose, separate recurrent/sensory observations, automatic write/readback and next-step gates, bounded storage, explicit paused recovery and independent journal reading. Source/package/native qualification passed; a separate real v8 episode completed twelve journals/applications and eleven memory joins, with exact export/recovery | Current-build multi-hour real-model and 24-hour qualification, sleep/power-loss and all-target lifecycle; decide/implement deliberate budget extension (not currently exposed); broader pointer/accessibility and measured GPU/energy behavior. Factuality and full provider-context processing remain unestablished |

Opening is temporary viewing. Explicit experiment import or Save to Library publishes
a Library copy; opening cases and geometry never does. No watcher, model request or live feed
is started. Existing ASCII records may still be incomplete when they exercise
an unqualified response-parser edge. A passed verifier result certifies its named
checks, not desktop/workflow parity, scientific benefit or live Being interoperability.

The [next usability/resource tranche](../../desktop/ReservoirScope/STATUS.md#next-usability-and-resource-tranche)
records the 0.24 multi-page native pass and keeps actual compact dimensions and
broader GPU/resource attribution open with separate completion boundaries. Observed
zoom and keyboard access at larger geometry do not establish compact-window acceptance.

## Platform acceptance

| Target | Build evidence | Packaged behavior | Human acceptance |
| --- | --- | --- | --- |
| macOS 14+ Apple silicon | Distinct 0.25.0 package build; 431 frontend tests, TypeScript/Vite and reference checks pass. Rust tests/Clippy are reused from 0.24 by exact 164-input comparison with five version-only substitutions, not rerun | At 1280 × 860, three scripted journals save/apply and naturally hold at step 91; Earlier/Later/Follow latest, current-versus-selected fill and 125%/200% zoom/reset pass. Normal quit and same-build replay preserve all 19 files. No fresh pinned-arrival or export/recovery check; prior 0.24 evidence remains tied to that build. Actual 900 × 700 / 720 × 600 content targets, minimum OS, broader accessibility, GPU/energy attribution and endurance remain open | Pending |
| Windows 11 x64 | Initial CI passed reference/Python/frontend checks, then stopped at a core covariance assertion; a test-only correction is present but subsequent remote execution remains unqualified | Pending | Pending |
| Ubuntu 24.04 x64 | Initial CI passed reference/Python/frontend checks, then stopped at a core covariance assertion; a test-only correction is present but subsequent remote execution remains unqualified | Pending | Pending |

See [platform CI evidence](../../desktop/ReservoirScope/validation/2026-10-14-platform-ci-0.17.0/README.md).
A checked-in workflow is not a passing job, and a build is not installation, graphics,
accessibility or collaborator acceptance. Historical receipts apply to their exact
source/package; no percentage substitutes for these gates.

## Next tranches

Use the [six current work areas](../../desktop/ReservoirScope/STATUS.md#six-bounded-areas-remaining):
writing-context investigation; Observatory/reading/rendering; sustained lifecycle and
endurance; conformance and optional selected feeds; platform packages; collaborator
acceptance. Selected feeds are optional. Explicit budget extension still needs a
decision and implementation. Actual two-hour synthetic evidence remains tied to
0.12.0, not the current package.

## Historical evidence

The complete former ledger is preserved byte-for-byte in
[PARITY-HISTORY-2026-10-15.md](PARITY-HISTORY-2026-10-15.md). It includes prior test
failures, corrections, refusals and qualification accounts with their original links.
Historical “next” sections are not the current backlog. The 0.20 source and
documentation checkpoint remains at `1552bbc`; the later 0.21 checkpoint `0001b7a`
is local and unpushed. Current work through 0.25 is subsequent to it. Checkpointing adds no
package or platform acceptance.
Native backports remain focused proposals after Tauri qualification. Live Being
producers and services remain outside this implementation program.
