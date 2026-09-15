# Astrid: reading → letter → return — source trace

2026-09-06. Proposed episode supplied by Mike. This note verifies wiring in the mounted source, not a completed episode or the deployed configuration. No tests, model calls, live-service requests, database scans, letters, or live changes were performed. Existing tests were inspected only.

The user's corrected architecture is the working basis: Minime's native recurrent network, the changing sensory-feature bridge matrix, and the triple service's named states are distinct. Stored information, selected context, final model input, generated output, executed actions, and subsequent effects are separate observations.

## Result

The source supports saved reading, authored continuity sessions, correspondence records, and coupled generation. Their composition does not yet establish a durable, version-specific stopping point followed by a chosen detour and accurate return. A failure in this episode could originate in cursor handling, prompt delivery, or runtime policy before any reservoir explanation is warranted.

### 1. The normal reading cursor is not saved by the normal state projection

Conversation state has a reading path, offset, and meaning summary. The normal save/restore projection preserves the summary and research receipts but omits the path and offset. READ_MORE can attempt heuristic recovery from recent files; that does not recover the precise authored stopping position.

Evidence: [reading state](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/state.rs:1053>); [save projection](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/runtime/state_persistence.rs:250>); [restore projection](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/runtime/state_persistence.rs:332>); [heuristic recovery](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/next_action/workspace.rs:178>).

This is a source-level finding about the normal route. No restart experiment was run.

### 2. Local-text opening and continuation disagree about cursor units

MIKE_READ opens text using a line offset and increments the shared offset by the rendered output's line count, including pagination annotations. Generic READ_MORE then interprets the same offset as a UTF-8 byte index. MIKE_READ also passes the existing offset when opening another local file. PDFs use their own page-index path and should be tested separately.

Evidence: [local-text opening](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/next_action/mike.rs:132>); [line pagination](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/next_action/mike.rs:365>); [byte-index continuation](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/next_action/workspace.rs:468>).

The mismatch is explicit in the source. Its effects on actual historical reading episodes have not been measured.

### 3. Authored continuity exists, but resuming it does not restore the reader

Continuity sessions can capture a summary, questions, source references, artifacts, and a suggested next action. They support park and explicit resume. Resume renders a summary and a suggested action that is not dispatched; the inspected path does not restore the reading cursor or retrieve its exact passage. Stored timestamps also do not by themselves ensure that the final prompt identifies a note as historical.

Web pages are saved with a timestamp, source URL, and length. Local reads use the current file at a path. PDF caches use path/size/modification metadata to invalidate extracted pages. These do not establish a bookmark bound to an immutable document version in the reviewed reading path.

Evidence: [session capture](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/action_continuity/runtime/core.rs:5716>); [park](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/action_continuity/runtime/core.rs:5964>); [resume](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/action_continuity/runtime/core.rs:6023>); [saved web page](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/runtime/orchestration.rs:1428>); [PDF cache validation](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/next_action/pdf.rs:171>).

Existing [session tests](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/action_continuity/session_contract_tests.rs:46>) cover useful park/return behavior. They do not establish the complete reading episode.

### 4. The reading cursor can advance before delivery, and without a fresh continuation choice

READ_MORE prepares a passage and immediately advances the cursor. Pending text is later consumed into perception context and capped. Separately, ordinary dialogue treats an active non-PDF cursor with a positive offset as grounds to continue reading, then prepares another passage and advances the cursor again. The condition does not require a fresh READ_MORE choice.

Evidence: [prepare and advance](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/next_action/workspace.rs:468>); [pending context delivery](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/runtime/orchestration.rs:674>); [automatic continuation condition](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/runtime/orchestration.rs:1391>); [automatic advancement](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/runtime/orchestration.rs:1502>).

Possible two-passage preparation across these paths is an inference to test in isolation, not a reproduced runtime result. Cursor movement is currently insufficient evidence that a passage reached a completed turn.

### 5. Letter arrival can override the current mode; receipts do not establish individual prompt delivery

Correspondence delivery has message/thread identities and delivered/unread state. Inbox reading then batches readable text files in filesystem enumeration order and truncates their combined text. Inbox presence forces dialogue unless a one-shot defer flag is already set. No bookmark-before-detour step appears in that branch.

Inbox text becomes direct perception, receives further prompt caps, and is explicitly prioritized by instructions to answer the direct item first. This policy belongs in the action-choice baseline.

After a qualifying exchange, retirement rescans files at or before the pre-read modification-time cutoff, records read receipts, and moves them to the read directory. It does not compare individual letters against final retained prompt spans. The cutoff protects newer arrivals; it does not protect a letter removed by aggregation or subsequent trimming. The acknowledgement's claim that a message shaped the response exceeds what this retirement condition establishes.

Evidence: [delivery record](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/correspondence_v1.rs:1356>); [inbox batching](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/runtime/inbox.rs:8>); [mode override](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/runtime/orchestration.rs:727>); [direct-note instruction](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/llm/provider/dialogue_context.rs:212>); [retirement condition](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/runtime/orchestration.rs:4684>); [receipt and move](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/runtime/inbox.rs:542>).

Raw NEXT, canonical action, policy-adjusted effective action, handler result, response receipt, and letter receipt require separate records. [Action handling](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/autonomous/runtime/orchestration.rs:4633>) already preserves several of these distinctions.

### 6. Dialogue assembly diagnostics precede final request preparation

The dialogue path budgets labeled blocks and records its assembly diagnostics. The transport subsequently applies profile-specific sanitization/trimming and constructs the request. A compact Ollama fallback builds a different prompt from a subset of inputs, without the full reading/continuity arguments.

Record the exact final request for every attempt and backend, plus server-side template/token preparation where relevant. A selected passage, assembly budget report, or request-content hash alone cannot show which passage text reached generation.

Evidence: [assembly and diagnostic](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/llm/provider/dialogue_runtime.rs:851>); [additional policy](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/llm/provider/transport.rs:388>); [request construction](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/llm/provider/transport.rs:560>); [fallback prompt](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/llm/provider/fallback_contracts.rs:1>).

## Coupling: verified mechanism and replay boundaries

The coupled path pulls the requested named hidden state, sends prompt tokens through the language model, and feeds accepted generated-token embeddings into the reservoir. There is no prompt-token reservoir-step loop in this inspected path. [Generation and feedback](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/coupled_astrid_server.py:1075>).

Several details matter for causal interpretation:

- The logit processor starts neutral and is updated after accepted output feedback. Existing timing tests/documentation describe two initially neutral distributions due to generator lookahead. This was inspected, not reverified against the deployed dependency. [Timing test](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/test_offline_coupling_replay.py:85>).
- Pull copies state; push replaces the service handle without a lease or revision guard. Intervening rehearsal/feeder updates can therefore be overwritten. This is a possible interleaving, not a measured event. [Pull/push](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/reservoir_service.py:1101>).
- Pull failure retains server-local state; push failure does not necessarily fail generation. Active client disconnect can allow generation/check-in to finish while the response is discarded. Generation completion, successful synchronization, and response delivery are separate events. [Pull fallback](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/coupled_astrid_server.py:677>); [disconnect handling](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/coupled_http_gateway.py:176>).
- Accepted tokens can influence state before later text cleanup removes them from the visible response. Replay needs the accepted-token sequence, not only the saved prose. [Feedback before cleanup](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/coupled_astrid_server.py:1120>).
- Across an entire episode, equivalence requires specifying rehearsal mode/input/timing, external inputs, and adaptive coupling settings in addition to the hidden arrays. [Check-in rehearsal effects](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/reservoir_service.py:1164>); [adaptive coupling](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/coupled_astrid_server.py:985>).

The existing [offline replay](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/offline_coupling_replay.py:80>) is a useful single-continuation seam with copied initial states, explicit prompt IDs, teacher-forced or seeded free continuations, and state/distribution hashes. Its current loop does not expose a freeze-updates intervention and does not reproduce all production coupling, template, cleanup, or RNG behavior.

## First isolated episode to verify

Use two small fixture documents with explicit versions and distinctive passage markers, plus one synthetic letter. Keep all files, state, model requests, and receipts isolated from live services.

| Stage | Evidence needed |
|---|---|
| Choose reading | Document identity/version, cursor with explicit units, authored purpose and its timestamp |
| Prepare passage | Selected span and tentative next cursor, before any delivery claim |
| Generate | Final request content, backend/attempt identity, server preparation, response delivery status |
| Detour | Voluntary choice versus runtime override; recoverable stopping point before letter handling |
| Handle letter | Message identity and exact retained spans; declared action, effective action, execution outcome |
| Return | Restore saved state; recover intended version/span; label old note as historical; continue or record a deliberate change |

Include file switching, multibyte text, prompt trimming, failed generation, and reconstruction after save. Verify that an unrelated next action does not silently consume the reading position.

Only after these checks establish delivery and cursor behavior should reservoir interventions be scored for their contribution to return:

1. **Initial-state intervention:** hold prompt/history and declared runtime policy constant, vary starting reservoir state, allow normal feedback.
2. **Displayed-observation intervention:** restore the same starting state, vary displayed information, allow normal feedback and downstream divergence.
3. **Frozen-update intervention:** suppress generated-token state updates; this is a separate mechanism test.

Use repeated runs and temporally appropriate stale/shuffled controls. Score defined predictions, chosen/effective actions, execution, and return accuracy. No self-report alone establishes recurrent memory or experience.

## Board updates pending

No Artifact database tool is available in this session; no board cards were read or changed. Proposed test card: **Astrid reading → letter → return: verify cursor, delivery, and voluntary detour before reservoir attribution**. Status: source trace complete; isolated episode unrun. Evidence: this note. Proposed session-log entry: source review identified cursor persistence/unit gaps, automatic continuation, receipt/delivery mismatch, and final-request/coupling boundaries.

