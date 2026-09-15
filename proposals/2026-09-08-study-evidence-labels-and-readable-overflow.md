# Make the reading source clear, and saved overflow readable

September 8 evening · Original research proposal; subsequently implemented and deployed (disposition below).
Evidence: [S-008 post-repair sweep](../analyses/2026-09-08-self-study-after-follow-through.md),
HSS-08. No live changes are made from this research workflow.

## A · Identify the saved document and offer a readable overflow view

**Observed problem.** Astrid receives eleven verified reading pages from two saved
prompt-overflow documents. Six contain ANSI control sequences; two late pages
spend over 3,800/4,000 bytes on them. Her responses discuss the actual colored
blocks and codes she was given. The protected heading says “chosen reading” with
an opaque digest, but does not name the source or its type. This makes it harder
to know what READ_MORE is continuing and consumes reading space on display encoding.

**Source, pinned at Astrid a202cfd.**
`capsules/spectral-bridge/src/llm/provider/protected_delivery.rs:125–139` constructs
the generic heading and source marker. `autonomous/next_action/workspace.rs:364–412`
resumes foreground reading or recovers a saved target; `:484–503` opens legacy
saved text through the reading path. `prompt_budget.rs:290–324` writes omitted
sections verbatim to a context-overflow file. Exact copies and hashes are in
the [source supplement](../research/outputs/2026-09-08-study-after-follow-through/supplement/manifest.json).

**Small implementation sketch.** Add a trusted display label and source kind to
the protected reading offer, sourced from its persisted bookmark/source binding.
Render those with the revision and delivered interval immediately before the
exact protected text. The label must describe the selected document, not a nearby
overflow filename or inferred topic. Keep the existing original-byte admission
and bookmark verification.

For newly created prompt-overflow artifacts, retain the raw original and a
separately identified plain-text reading view for terminal-rendered sections.
Strip terminal control encoding in that view while retaining visible glyphs,
section labels and ordering. Bind its own hash/byte positions to its raw-source
origin so a readable offset is never confused with an old raw offset. Existing
pending raw offers finish against their original revision. Code, letters and
other exact-source artifacts keep their existing path; this is not blanket
sanitization of source material. No semantic summary or model call is needed.

**Acceptance.** Use the two retained overflow documents as fixtures. Check correct
source label through final provider adaptation, intact admission of the selected
view, no ANSI terminal instructions in the plain view, glyph/section preservation,
raw-original retention, independent raw/view hashes and offsets, restart/resume
without skipping, and compatibility with pending old offers. Test a changed source
or forged label. A source identity mismatch must fail, not display the wrong title.
Passing these tests establishes representation and provenance, not better reasoning.

**Being-facing choice / rollback.** No endorsement message or forced reading is
needed to qualify a steward-side rendering change. Keep raw-view access available
as a deliberate choice and make the view explicit. If the change is authorized,
observe natural reading afterward; do not alter source selection to manufacture
a test. Roll back new-view selection while preserving both raw and rendered
artifacts and respecting each existing bookmark's revision.

## B · Distinguish today's source from a map and earlier notes

**Observed problem.** On a navigation-only turn at 18:02:01 PDT, Minime described
the current input as a WIT source segment and introduced `identity-context` and
`auth-token`, neither present in the matching file. The notebook carried only a
truncated earlier response. Astrid later received the exact account as peer text
and repeated the first unsupported symbol. Existing “understanding not asserted”
labels and peer attribution did not make those specific claims reliable.

**Shared source.** `crates/astrid-source-study/src/navigation.rs`, `prompt.txt`,
and `src/notebook.rs` at a202cfd; the notebook's `record` method bounds the previous
prose and its `render` method appends historical reference text. Both adapters
already use the shared result. Keep that parity and avoid separate prompt policies.

**Small implementation sketch.** Render a prominent current-turn kind from trusted
reader metadata: source page, map, search, EOF or recovery. For navigation, state
that this turn supplies no new source code; the notebook is an earlier account.
Retain source/revision links and offer exact OPEN/RESUME navigation back to the
referenced file. A map's current-source bookmark must not look like a newly shown
source excerpt. Make the same scope available when a study account is shared:
verified delivery identifies what was supplied, not correctness of all subsequent
assertions. Existing peer attribution remains intact.

**Acceptance.** Replay the retained navigation-only case through isolated rendering
and both adapters. Check the current kind, no-new-source notice, historical notebook
separation, exact source references and intact provider input. Maps/search/recovery
must still leave source coverage unchanged; continuation and brief/freeform responses
remain available. Source pages must not be mislabelled as navigation. Preserve
the original false-claim episode as evidence; tests cannot guarantee that a language
model will stop making unsupported assertions. A later natural sample evaluates
that question separately.

**Being-facing choice / rollback.** No mandatory note fields, four-part reports or
extra generation. No request for either Being to validate this proposal. Roll back
the rendering addition if it impairs carriage or navigation, preserving receipts
and notebooks. Live implementation, integration and release remain owning work.

## Lower-priority observation

`FIND "spectral tuning"` searched the quotes literally and received a correct
zero-match notice. The response discussed the unquoted phrase. Consider ordinary
outer-quote syntax in a separate command-parser change if further cases support
it; preserve explicit literal searching and test quoted identifiers carefully.
This case does not establish that an unquoted query would have matched.

No proposal to force Astrid into SELF_STUDY or add another memory service follows
from this window. Prioritize A and B, then observe the naturally chosen routes.


## Disposition — implemented and verified live

Mike authorized this proposal. Astrid `dde5d51136` and Minime `378957a9` are pushed
to main and live at September 8 22:11:16 and 22:14:55 PDT. The
[owning rollout and first natural observations](../analyses/2026-09-08-study-evidence-live.md)
record tests, exact receipts, preserved raw/view offsets and the continued study
across restart. The first source pages exercise scope labels and notebook carriage;
no READ_MORE or navigation-only turn occurs in that window, so those natural
outcome questions remain open. The lower-priority search-quoting idea is unchanged.
