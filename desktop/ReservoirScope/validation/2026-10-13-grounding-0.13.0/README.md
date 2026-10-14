# 0.13.0: open journal writing and retained prompt contracts

**Implemented and packaged; qualification is partial.** New sessions invite open
writing through `reservoir-journal-v3`. Topic, form and developing threads are left
open; there is no assigned metric summary, heading or word count. Current readings
and exact prior writing remain distinct context. Literal factual claims can be
reviewed without treating metaphor as measurement or using an editorial score to
gate otherwise valid saved feedback.

The user's clarification superseded the constrained v2 candidate before any v2
model request. V1/v2 remain exact replay contracts; missing historical version means
v1 and is still omitted on serialization. Session versions cannot change in place.
The [design note](OPEN-WRITING-DESIGN.md) records the small read-only Minime refresher.
Its private source text was not copied into app prompts or fixtures, and no Being
process, service or workspace was changed.

## What executed

- **329 frontend tests**, TypeScript and production asset build passed.
- **162 core tests** and strict all-target Clippy passed, including exact legacy
  prompts, v3 reconstruction, free-form journal acceptance and save/memory gates.
- **172 desktop tests passed; two pre-existing cases ignored.** Strict all-target
  Clippy and the final package build passed. A subsequent two-line import-format
  change passed formatting, the three affected version checks and strict Clippy.
- Frozen reference check passed. The archive's 46 regular files match the app;
  39 canonical inputs and 42 bundled resource files passed identity checks.
- **40 frozen evaluation tests** (26 quality, 14 integrity) and **19 owned-service
  helper mocks** passed. These do not qualify real writing or runtime cleanup.
- The final executable replays the old immutable v1 export with 121 steps, four
  journals and 19 segments, without changing its original bytes.

Receipts: [frontend](frontend-final-02.json), [core](core-source-checks-02.json),
[desktop](desktop-build-checks-02.json), [format-only change](format-only-repair.json),
[final build](final-package-checks-03.json), [archive](archive-check.json),
[resources](package-resource-check.json), [evaluation freeze](evaluation-freeze-v3-01.json)
and [independent source review](FINAL-SOURCE-REVIEW.md). Focused counts are subsets,
not additions. Initial frontend typecheck and desktop test-harness failures remain
retained; the corrected final checks passed. No native Swift changes were made.

## Actual model outcome

The [prospective v3 plan](PROTOCOL-V3.md) allowed one bounded run with the privately
staged Gemma3:4b, four opportunities and a 256-token response bound. It reached the
first opportunity at step 30, returned **one incomplete `length` response at 256
tokens**, and held: **zero saved journals, zero feedback applications, three
opportunities unstarted**. No retries, skips, extensions or replacement samples
were used. The actual response and its failure remain evidence.

An initial Go to Folder automation problem required a labeled passive copy to
continue offline inspection. After user assistance and explicitly raising the
native sheet, **native export succeeded**: all four committed files exactly match
the earlier copy, and pinned production replay passed for 30 steps and two segments.
Clean quit, idle relaunch, explicit verification and paused restore then preserved
the same checkpoint, v3 contract, budgets and blocked attempt without another model
request. The restored snapshot was also exported through the native dialog.
See [the native export supplement](NATIVE-EXPORT-SUPPLEMENT.md),
[the recovered-export verification](RECOVERY-EXPORT-SUPPLEMENT.md),
[the recovery receipt](native-recovery-completed-01.json), and
[the complete reading review](REAL-MODEL-RESULTS.md). Original blocker/copy evidence
remains historical; it was not rewritten into a native export pass.

The output bound is a concrete usability limitation for this rehearsal. One cutoff
cannot establish a general prompt/model effect. Real v3 journal saving, subsequent
memory, feedback and continued writing remain unobserved. The earlier four completed
real-model journals belong to 0.12.2 and are not substituted for this outcome.

## Native interaction and cleanup

The [actual walkthrough](MACOS-UI.md) records legacy v1 restoration, readable prose
and Evidence, two successful visible-target pointer/minimize/reopen cycles, and a
native export cancellation, followed by successful v3 export and clean relaunch/
paused recovery. The macOS reopen handler restores and focuses the existing window
without starting a session. Earlier intermittent pointer behavior is not fully
explained; the sheet succeeded after user assistance and an explicit Raise action.
These executed checks do not substitute for broader pointer/accessibility acceptance.

The owned model server received TERM after its single response. Its supervisor
reported a post-TERM group-stability check failure. Three subsequent scoped checks
found the exact server, supervisor and original group absent, without additional
signals or endpoint contact. The [original and supplemental evidence](owned-model-cleanup-supplement-01.json)
remain distinct. Improve that verifier's bounded transient-read handling and audit
before another supervised launch; do not call the failed helper run a clean pass.

## Package and scope

- Preview: `0.13.0`, macOS arm64, separate Tauri application identity.
- Executable SHA-256: `689ed9e13e6cdbea8774c232b88018eaebd0c8fcbd2aaedc2d0fb0c6e1bb3b5b`.
- Archive SHA-256: `d64cbd5e43618a5d178085b6f89769b687270264558c40e69e6bfd84c5a3ce5e`.
- Archive: `target/release/bundle/macos/ReservoirScopeTauriPreview-0.13.0-macos-arm64.tar.gz`.
- Local ad-hoc signature verification passes; notarization/distribution signing is
  not claimed. [Qualification identity](qualification.json) records final continuity.
  [The native follow-up identity check](post-recovery-continuity.json) confirms the
  same package and runtime source after the completed export/recovery walkthrough.

The two-hour minimized measurement remains 0.12.0-specific. This is not a causal
prompt comparison, proof of emergence, Minime/Astrid replication, a new long-run
result, Windows/Linux acceptance, or a GPU/power measurement. The application still
uses user-selected writing cadence and one latest saved-and-applied memory entry.

## Next bounded tranche

Native export/recovery for this retained cutoff is complete. Separately freeze and
qualify sufficient bounded output and context for open
writing, with explicit storage/deadline behavior and no mandatory prose template.
Keep failed responses inspectable. Only after completed entries are observed should
we assess continuity across several turns, and then consider richer retained memory
or model-chosen timing under new explicit contracts.
