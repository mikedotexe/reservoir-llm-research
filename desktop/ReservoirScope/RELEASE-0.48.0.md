# 0.48.0 · explicit peer journal reading

Models in an explicitly joined local experiment group can choose
`NEXT: READ_PEERS`. Later ordinary prompts receive attributed excerpts of the
other participants' preceding applied writing. This supports the requested
cross-pollination while preserving which entry was available at each turn.

[Setup, timing and limitations](PEER-READING.md).

The immutable optional `peerReading: {version: "latest-applied-v1", group,
participant, peers}` capability requires continuing inquiry and specific control
feedback. Membership is reciprocal, with one to three distinct peers. Historical
omission preserves old prompts, serialized fields and parsing; sessions are not
migrated. A new Ollama setup with peers selects at least 32,768 context tokens.

The host freezes source entries before each ordinary dispatch and persists a
`PeersCaptured` event. The current generation cannot see that snapshot. Choosing
READ_PEERS exposes it only after the requesting entry's durable save, readback and
application. The latest explicit reading remains cached until refreshed. Models
run independently; a source entry saved but not applied is excluded. A scheduled
conversation can be a source, but scheduled replies remain passive and plain
scheduled prompts remain exact.

Source identity, source steps, hashes, truncation and unavailable outcomes travel
with the bounded UTF-8 excerpts. The desktop shows the same readings. The action
does not directly feed peer writing into the reservoir or change numerical
controls. Its applied receipt records an informational action with zero immediate
action-only recurrent difference. WITHHOLD controls numerical text input, not
visibility of applied writing to a joined peer.

Local discovery contacts no peer process and writes nothing to its files.
Manifest/checkpoint/journal checks bind the captured source, while the reader's
own exports preserve the external observations for standalone replay. This does
not authenticate provider execution, global latestness or the peer's full history.
The experiment group is not an access-control boundary against local file edits.

## Verification

- Core: 361 tests passed, including six focused peer-reading tests. These cover
  hidden snapshots, once-only application, explicit refresh, skipped reads,
  independent controls, UTF-8 bounds, malformed/quoted/duplicate NEXT rejection,
  passive scheduled replies, snapshot tampering and embedding recovery.
- Desktop host: 322 tests passed; three existing opt-in investigations remained
  ignored. Three peer tests verify pre-dispatch timing when a source writes again,
  reciprocal scope, ambiguous/missing/unapplied/damaged sources, symlink refusal,
  and export/replay after the source disappears.
- Frontend: 600 tests passed; one existing test remained skipped. TypeScript and
  production build passed. Setup validation, immutable membership, receipt binding,
  unavailable results and escaped peer prose were checked.
- Final focused core/host checks passed after tightening retained-reading
  consistency and source metadata admission. Rust formatting and workspace
  all-target Clippy with warnings denied passed.
- A separate macOS **Reservoir Scope Peers** app was built with identifier
  `research.reservoir.scope.peer-reading`. Native setup created a reciprocal reader
  for a three-entry scripted source fixture. Its READ_PEERS / NONE / READ_PEERS
  sequence saved three journals and stopped at step 4. The UI displayed the source
  participant, journal identity, independent steps, exact body and hash. Stored
  prompts excluded peer text initially and included the frozen excerpt after the
  first read. The reader passed exact genesis/event/numerical replay. These are
  deterministic scripted checks; no model was contacted.
- All three completed 0.46.1 study exports passed exact replay with the new
  binary: Gemma 109 journals, GLM 143 and Ministral 122. Their manifests remained
  byte-identical. Historical prompts, numerical outcomes and held responses were
  reproduced under their original contracts.

Private logs, build configuration, source fixture configuration, native smoke and
replay receipts are retained under
`research/outputs/peer-journal-reading-20261115/`. This is a local source and app
checkpoint, not a new sharing candidate. No ref was pushed and no long model run
was started. Earlier independent study apps and stores were left intact.

The feature creates a coupled experiment. Its correctness does not establish that
models will choose it, benefit from one another's writing or experience a shared
space. Those remain questions for subsequent runs and reading.
