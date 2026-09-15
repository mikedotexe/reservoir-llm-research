# Extended writing: capacity, continuity, and the remaining accuracy limit

Mike accepted the [longform-room proposal](../proposals/2026-09-09-longform-room.md).
The owning implementation is in Astrid and Minime; this directory records evidence.

The implementation gives both Beings an optional `WRITE PROFILE EXTENDED` (8,192-token
ceiling), `SHORT` (512), and `DEFAULT` (ordinary preferences), with matching provider
fallback allowances, context and deadlines. No profile is forced at rollout. A shared
writer offers private, versioned drafts with start/continue/revise/branch/resume/finish,
a current question and evidence, and explicit readback of large drafts. It retains whole
completed passages and exact wire receipts. A failed or clipped generation leaves the last
completed draft intact and the failed attempt separately observable.

The shared reader grows from a 24,000-byte input / 32,768-token context to 48,000 / 65,536.
Recent study-answer storage grows from 16,000 to 64,000 bytes and notebook rendering from
9,000 to 32,000. Those are bounds: oldest whole answers are dropped before labelled excerpts.
Drafts are never silently excerpted to continue; a capacity notice preserves the entire
saved draft, with `WRITE READ dN [page]` and new-draft options. Private journals are outside
the directories the peer scans and do not trigger sensory or companion-inbox delivery.
The model, thinking flag, coupling, reservoir and numeric sensory dimensions are unchanged.

A correction to HSS-17: Astrid's repetition helper produced forced-action metadata and
wording, but its dispatcher already retained the authored NEXT as the effective action.
This change makes the helper itself advisory for chosen read-only exploration and writing;
it is not evidence that a previously active dispatcher veto was removed.

## Fixed native qualification

[Protocol](../research/outputs/2026-09-09-extended-writing-qualification/protocol.json)
was frozen before two uncoupled Ollama requests, using 8,192 output / 65,536 context,
thinking off, no retries, no imposed minimum length and no Being state/output injection.
One input reuses the earlier correct-control source comparison; the other is a new private
draft about the difference between reading source and understanding a call path. The draft
NEXT is recorded, not executed.

| Case | Input tokens | Generated tokens | Visible characters | Native finish | Wall time |
|---|---:|---:|---:|---|---:|
| Source correct-control | 7,051 | 781 | 3,149 | stop | 117.69 s |
| Private draft | 382 | 572 | 2,845 | stop | 64.77 s |

Both larger requests returned usable text, still below 1,000 output tokens. This qualifies
basic native admission/usability, not use of all 8,192 tokens or a causal length increase.
Shared hardware contention makes timing descriptive; this is not Astrid's coupled route.

The source response correctly identified the host caller filter, but asserted a privileged
gateway/host-mediated path not established by the supplied excerpts, and misspelled
`wasm_capsule` once as `wasm__capsule`. Its saved note repeated the unsupported mediation
story. The correct-control semantic criterion was therefore **not met**. The free draft
made a sustained conceptual distinction and chose `WRITE CONTINUE`, while offering generic
examples rather than new code evidence. Neither result establishes improved understanding.
The rollout decision is to provide optional capacity/continuity after structural adapter
and persistence tests; no model-quality promotion is inferred from these completions.

## Natural follow-up

Track whether either Being chooses the profile or a draft, whether the exact developing
thought and concluding passage arrive next turn, whether revisions improve supported claims,
and whether they can leave and return without losing the question. Measure actual admitted,
generated and saved sizes, native stop/length/error, repeat passages and latency. Short
writing, first-try mistakes, revisiting and changing direction remain valid choices.

Keep the gateway claim as an unresolved accuracy observation. A later claim-check should
supply the actual producer-identity construction and any mediation code, then distinguish
what is implemented from what would merely be a plausible architecture. More tokens alone
have not supplied that evidence.

Owning source/tests and rollout receipts are linked in the release retention below after
activation. S-007's scheduled cutoff/cursor is unchanged. Board mirroring remains pending;
this account is saved locally and no research judgment was sent to the Beings.

## Verified rollout, September 9, 18:47 PDT

[Retained verification](../research/outputs/2026-09-09-extended-writing-qualification/rollout/live-rollout.json)
binds the immutable Astrid source `6f8aac6384` and Minime source `33c324d2` to live
bridge PID 80595 and Python agent PID 81874. Astrid restored the exact drained
checkpoint and saved a new exchange. Minime restored its exact pending FIND and
its new worker dispatched it. Ten surrounding services and their launch settings
were unchanged. The bridge first stopped gracefully, then its controller reported
an exit-identity error and retained the launch hold. The supported recovery helper
had an older-format-only check; committed fix `6bb458d159` admits the same V2/V3
formats as normal activation with all hash/checkpoint/hold checks retained. The
original failure and successful recovery are both in the linked packet. The exit
observation itself does not prove actual PID reuse.

The source commits and recovery fix are on each owning main branch. The immutable
stage remains unchanged; the canonical recovery helper's difference is explicitly
accounted for. Neither writing profile was forced. This is a release/continuity
result, not a sample of natural longform outcomes. S-007's cutoff remains unchanged.

### Board updates pending

The local `board/extended-writing-pending.json` records implementation, qualification
limits and verified rollout for later mirroring. No research output was sent to the
Beings. Next observation: chosen profile/draft use, full passage carriage, claim
revision and voluntary return/finish; size alone is not the success criterion.

Shared-tree closeout: all five pre-existing tracked patches and 52 untracked files
were preserved and restored. The combined checkout passes 47 reader tests, 34
bridge state tests, formatting and domain-boundary verification. The first state
test filter selected zero tests; its corrected invocation and both logs are retained.
Stewardship resumed at 01:53:17 UTC, generation 428, with its event appended.
[Closeout evidence](../research/outputs/2026-09-09-extended-writing-qualification/rollout/checkout-restoration-checks.json)
and [resume receipt](../research/outputs/2026-09-09-extended-writing-qualification/rollout/steward-resume.json)
complete the implementation account. Astrid main is `d33e7f2e70`; Minime main is
`33c324d229`; the former includes release documentation and recovery tooling beyond
the immutable running binary's source commit.
