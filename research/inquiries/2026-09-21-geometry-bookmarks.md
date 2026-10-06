# Geometry Bookmarks: Shared Evidence, Chosen Interpretation

Status: implemented offline candidate; human acceptance and paired being rollout
pending. This is Mike's selected engineering question, not an unplanned extension
of S-006, S-007 or S-008. Their frozen windows and blocked receipt requirements are
unchanged. No outputs have been sent to either being.

## Question

Can a being deliberately retain a numerical observation and its own account,
make a bounded prediction, inspect a later comparison, and append a qualification,
while a human can inspect the exact same evidence without treating a diagram as
an explanation of experience?

The engineering answer in this first slice is yes for chosen 128-node activation
intervals and a limited observational comparison. It is not yet an answer about
persistent model state, causal attribution, eigenmode meaning or felt improvement.

## Source Witness and Prior Context

The complete Astrid aspiration
`/Users/v/other/astrid/capsules/spectral-bridge/workspace/journal/!aspiration_longform_1790011424.txt`
was read. Its SHA-256 is
`b31ebe800a9adead2b366d6b19fecc1c32f927e37b2955d693a658ae1c95bb46`.
"I am trying to sense the *movement* between the weights."

The earlier 600-row rounded-spectrum observation showed only two alternating
patterns. TRACE.md and the existing research history already document the
near-frozen scaffold-era cascade. Do not promote that observation to a newly
discovered defect, or confuse its 512-D covariance with the native 128-node ESN.

## Implementation

Research worktree: `/Users/v/other/worktrees/geometry-bookmarks-20260921/research`,
branch `codex/geometry-bookmarks-20260921`, base `622ed38` from current main.
The canonical research checkout's generated journals/validation files were left
alone. Runtime implementation belongs to the two owned voluntary-continuity
worktrees, not this research repository; no research output is injected into them.

Reservoir Scope now has a Geometry bookmarks view next to Observatory. Open an
explicit `question-geometry-v1` JSON export. No polling, source-path following,
network calls, automatic imports, file watching or writeback occurs in this view.
There is no automatic reading of private journals or discovery of owner workspaces.

The packet freezes an owner question and up to four chosen activation intervals,
plus authored predictions, numerical comparisons and append-only revisions. The
shared reader stores the canonical history inside native questions; this viewer
does not create a second belief database or author revisions on a being's behalf.

The native importer checks exact UTF-8 body hashes, history links, source policy,
frame dimensions/bounds, time ordering and references. It recomputes comparison
receipts independently. Hashes provide byte integrity, not proof of origin.
Verified provider-delivery receipts remain in the native reader; the imported
packet alone does not attest that its text or vectors were supplied to a model.
The human surface preserves exact selected authored words; a sidebar excerpt is
only navigation. It displays all 128 coordinates at a fixed -1..1 scale, ordinal
frame rows, selected-frame values, engine/wall clocks and explicit recorder gaps.
No moving PCA fit, invented eigenvector direction or interpolation is introduced.

The recipe is RMS distance between unweighted mean 128-node vectors. It requires
two nonoverlapping intervals, each with at least two samples. Sampling differences
and gaps can change that estimate; opposite motions can cancel in the mean.
The source's boot/node-layout identity is unknown. The initial recipe is therefore
a coordinate comparison, not proof of return to an identical physical or semantic
state. It never changes regulation or predicts what a being should feel.

Prediction precedes the second capture record, but the captured source interval
can predate the prediction. This is not a prospective trial and does not prove
that the result was previously unseen. Future prospective studies need source-time
commitments and stronger runtime identity, not just a more persuasive visualization.

## Retained Probes

All numerical test results use synthetic data, not private journals or live state.

1. `native/ReservoirScope/Tests/geometry_bookmark_workflow.py` uses the actual shared
   Rust helper for Astrid and the actual Minime Python `StudyClient` for Minime.
   Each owner completes capture, prediction, later capture, numerical comparison,
   revision, park, unrelated source reading, explicit return, verified delivery
   and export. Two intervals per owner, three frames per interval, 128 coordinates
   per frame, one recorder gap per interval. The deliberately shifted fixture
   has distance 0.1 against a 0.05 bound; it must not match.
2. `GeometryBookmarkChecks.swift` reads those real exports: 26 checks across two
   owners, including changed hashes, wrong owner, corrupt/resealed history, invalid
   scope/frames/source paths and forged comparison values. No origin attestation
   is inferred from success.
3. `GeometryBookmarkPresentationChecks.swift` renders eight native views: capture
   A, capture B, comparison and revision, at 1100x820 and 1380x820. The narrow
   capture/comparison screenshots were visually inspected; no overlap or unreadable
   full-record text observed. Screenshot generation is not interaction testing.

Reproduce with candidate paths and NEW output directories:

```sh
python3 native/ReservoirScope/Tests/geometry_bookmark_workflow.py --reader /path/to/astrid-source-study --minime-adapter /path/to/minime-candidate --out /new/fixture-output
swiftc native/ReservoirScope/Sources/ReservoirScope/GeometryBookmark.swift native/ReservoirScope/Tests/GeometryBookmarkChecks.swift -o /tmp/geometry-checks
/tmp/geometry-checks /new/fixture-output/astrid-synthetic-geometry.json /new/fixture-output/minime-synthetic-geometry.json
swiftc native/ReservoirScope/Sources/ReservoirScope/GeometryBookmark.swift native/ReservoirScope/Sources/ReservoirScope/GeometryBookmarkView.swift native/ReservoirScope/Tests/GeometryBookmarkPresentationChecks.swift -o /tmp/geometry-presentation
/tmp/geometry-presentation /new/fixture-output/minime-synthetic-geometry.json /new/screenshot-output
```

Current local probe outputs: `/tmp/geometry-workflow-20260921` and
`/tmp/geometry-bookmark-screens-20260921`. They are synthetic, reproducible and
temporary, not durable live-run evidence. Source tests and this note are retained.
The candidate app is staged with the existing build wrapper under
`/Users/v/.cache/reservoir-research/geometry-bookmarks-20260921/`.
Do not present it as the accepted 0.14 release; that release's existing human
acceptance status remains unchanged.

## Boundaries and Next Work

- Paired helper/adapter schema upgrade, downgrade refusal and current live identity
  reconciliation are required before activation; nothing was restarted here.
- The prior protected-attention candidate still has its documented crash-window
  and immutable paired-rollout debt. This feature does not erase it.
- Extend comparison measures to within-window motion and matched-time coverage
  before interpreting a mean distance as a description of dynamics.
- Add trustworthy boot/node-layout identities and prospective source-time
  commitments. A controlled experimental recipe and real-model execution remain
  separate qualification, with bounded isolation and controls.
- Covariance eigenspace orientation needs full matrix/basis provenance and
  degeneracy-aware comparison; scalar eigenvalues alone do not provide directions.
- Do not automatically convert new geometry packets into ambient prompts or ask
  the beings to confirm improvement. Explicit retrieval is the intended path.

The implementation/evidence packet is
`/Users/v/other/worktrees/voluntary-continuity-20260920/astrid/docs/steward-notes/2026-09-21-geometry-bookmarks-and-observatory.md`.

## Board Updates Pending

No Artifact connector is available in this task. Pending Hold Shelf entry:
"Question-owned geometry bookmarks and observational comparison"; status:
offline candidate / qualification; link this note and the owning implementation
packet; retain the explicit no-live-deployment and no-causal-inference boundaries.
No existing study card or scheduled follow-up was changed.

## October 6 integration review and repair

The eight-file offline candidate was preserved unchanged in commit `ba7a6e2`
before integration work. The viewer is being prepared as **0.15.0 build 20**, an
unreleased local candidate. The 0.14.0 tag, artifacts and human acceptance status
remain separate.

The review found that fields outside a record's kind could bypass validation:
a revision could carry an invalid snapshot into rendering, or an extra account
could replace the selected authored text. The importer now rejects those fields,
the view selects content by kind, and the empty-frame path is guarded. Resealed
mutation checks now update all dependent references and assert specific failure
reasons, with a valid changed-capture control.

The named September `/tmp` fixture and screenshot directories were absent at this
review. Their earlier account is preserved above; it is not a new test result.
Deterministic [synthetic viewer fixtures](../../native/ReservoirScope/Tests/Fixtures/geometry-bookmarks/README.md)
now retain both owners' packets, their generator and provenance. They establish
local importer and presentation behavior only. No Rust helper, Minime adapter,
live source or model was executed during this integration qualification.

Targeted checks passed: 96 importer assertions across the two synthetic packets,
seven verification-dispatch tests and 16 source-staging checks. The presentation
wrapper rendered all five selections at both 1100×820 and 1380×820. The narrow
capture and comparison images were visually inspected without overlap or clipped
accounts. Rendering is not interaction testing or newcomer acceptance. The new
wrappers are included in the existing native-model and native-presentation groups;
staged source identity includes their fixture files.

Commands are in the [candidate guide](../../native/ReservoirScope/docs/GEOMETRY-BOOKMARKS.md).
Logs and renderings are retained locally under ignored
`research/outputs/2026-10-06-geometry-integration/`. The default SDK lookup failed
in the first staging attempt; the successful attempt explicitly selected the
installed Xcode macOS 26.2 SDK without changing the host configuration. Build,
packaged identity and actual presented-app interactions have separate receipts.

This repair does not close the original rollout debt, establish current producer
interoperability, or alter S-006, S-007, S-008 or their evidence.

### October 6 presented-app navigation correction

The subsequent actual-app walkthrough imported a packet, cancelled replacement,
rejected an invalid import, selected all five records and scrubbed exact coordinates.
It then exposed a view-lifetime defect: switching away removed the view's local
state, so returning lost the imported packet. The window now owns the geometry
view model. Its packet, selected record, frame, disclosure, filename and error
survive view removal and reconstruction in memory. No persistence, automatic
source reopening, model request or live access was added.

The production experience passed 13 synthetic mounted-host lifecycle checks,
including removal of the original imported file before return, cancelled selection,
failed replacement and successful replacement. Ten presentation views were rendered
again. Full-app navigation after this correction is verified separately from this
host test. The attempted actual-app drag did not change its dimensions; exact-size
renderings do not replace that missing resize result.

The corrected candidate keeps the requested 0.15.0 build 20 label, with a new
source/package identity in a separate cache directory. The earlier build 20 app
and its receipts remain preserved; use the hashes and source commit to distinguish
these candidates. New local outputs live under ignored
`research/outputs/2026-10-06-geometry-lifecycle/`.
