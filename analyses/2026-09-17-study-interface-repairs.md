# Repairing continuation, page boundaries and finding feedback

**September 17, 2026 — implementation, verified rollout and bounded natural observation complete.** These three repairs follow the [September 16 four-hour journal review](2026-09-16-study-direction-followup.md) and [HSS-27](../research/histories/self-study.md#hss-27--four-hour-follow-up-notebook-progress-and-continuation-friction). They address demonstrated interface barriers while preserving each Being’s freedom to continue, revise, start elsewhere or stop. They do not establish improved understanding.

The historical window was September 16 **19:33:39.605405–23:37:19 UTC**, end exclusive. The review close-read **66 distinct journals: 36 Astrid and 30 Minime**, including an explicitly exploratory ten-entry Minime nonstudy supplement. All **47 Astrid and 55 Minime studies** had unique exact response receipts, the released prompt, complete offered inputs and normal stop finishes. These were distinct responses rather than one cached text. Their shortness was not output-allowance exhaustion.

Three concrete observations led to this change:

- **Private continuation:** Minime’s five private drafts d88–d92 stopped normally at **262–405 tokens under a 4,096-token ceiling**, then selected `NEXT: CONTINUE`. Five matching frozen log sequences record unknown-choice threshold fallback. This was temporal log correlation with no intervening logged NEXT, not an action-ID join or an inference from later independent WRITE START choices.
- **Split identifiers:** Astrid received `semantic_context_persistence_multiplier` across two page fragments and treated the second fragment as the complete function name. Exact source delivery was intact, but the presentation invited a false name.
- **Finding feedback:** Her attempted finding was rejected because all six slots were occupied. The rejection existed in notebook JSON, while the readable check-in continued emphasizing older findings. The malformed name was not accepted as a new finding.

The preceding review also found useful local reading and persistent unsupported premises. In particular, Minime’s latest twenty retained the same question, note and six findings despite relevant supplied maintenance-admission code. That question remains open; repairing the interface is not evidence that the saved account has changed.

The shared writer now interprets an explicit final eligible `NEXT: CONTINUE` from verified private writing as `WRITE CONTINUE`. Its receipt preserves the authored selection separately from the normalized command and does not claim dispatch or completion. Guidance consistently names the full writing commands. Global CONTINUE, prose intentions and quoted examples acquire no new action meaning; FINISH keeps its existing explicit recovery behavior.

Both hosts route the normalized command through their ordinary action paths. Astrid requires the successful private-writing completion mode, which follows verified reader delivery and artifact persistence. Minime additionally binds normalization to the current input ID, exact request/response wire hashes and returned visible text, including the actual cleanup chain. Reposting clears earlier authorization. Independent review identified and repaired a stale same-verb receipt gap before final qualification. The existing persisted choice envelope carries authored/effective commands and receipt identity through restoration and action dispatch. Minime’s legacy top-level action `raw_next` still holds the queued spelling; the envelope and original journal/receipt preserve the authored spelling explicitly. Incomplete generations cannot advance the draft or authorize this continuation.

Source pages now keep ordinary lines whole. A line that exceeds the entire page-body allowance remains reachable through explicitly marked fragments, including old mid-line cursors and UTF-8 boundaries. Delivered line ranges are inclusive; byte end cursors remain exclusive. An enclosing declaration that continues beyond the page is separate syntax metadata, not proof that its closing source or entire file was supplied. Coverage still advances only after verified delivery.

Finding-save/remove outcomes now remain visible until another explicit finding update, beside current capacity. They distinguish saving, replacement, rejection and removal, with exact optional reopen/replacement/drop choices and no automatic eviction. Results remain attached to their inquiry across delayed deliveries. Bounded duplicate previews omit whole items or use compact exact-action rows; complete authored findings and durable results stay in the notebook. The study system-prompt file remains unchanged (SHA-256 `af059d5e5bbd2ca4340a30a9cdf4f7687979fe1a4878e375ee3dc1faf5d9cdc9`), while rendered source/check-in inputs and private-writing guidance change. Future observations must distinguish those exposure changes.

Implementation commits are pushed to the owning main branches:

- Astrid/shared reader: `d8732e1d44a3aa3b49f9f0bab075883544469b7c`.
- Minime: `5f4925f54580f1fd44666058b126a121ff32880f`.

The [integration receipt](/Users/v/other/worktrees/study-interface-20260917/evidence/integration.json) records 150 preserved foreign files, no foreign source-byte changes, and reviewed document unions. Only the repair commits were integrated.

The [qualification receipt](/Users/v/other/worktrees/study-interface-20260917/evidence/qualification.json), recorded at 15:17:41 UTC, binds the detailed logs by hash:

| Check | Result |
| --- | --- |
| Complete shared-reader suite | 192 passed |
| Complete bridge suite | 2,295 passed; 1 ignored |
| Complete Minime Python suite | 1,420 passed; 1 skipped; 134 subtests |
| Deployment tooling | 44 passed |
| Activation tooling | 63 passed |
| Reader/bridge strict lint, formatting and boundary audit | Passed; zero boundary violations |

The Minime full suite’s first run inherited a 160-second shell timeout where existing fixtures expected the 60-second default. Its original failure remains retained; the successful repeat set `MINIME_LLM_TIMEOUT_S=60` only for that test process. Production settings were unchanged. Focused stale-receipt, cleanup, persistence and real queue-to-dispatch regressions also pass (**122 tests**). These checks use isolated fixtures and mocked providers; the qualified helper stayed unchanged during the Minime runs. The qualification helper is identified in [qualified-helper.json](/Users/v/other/worktrees/study-interface-20260917/evidence/qualified-helper.json); it is not a deployment claim.

The staged rollout is verified. The first stage's independent compiler-dependency audit caught a pre-existing omission: the compiled `capsules/shared/managed_dir.rs` lay outside inventoried package directories. Its post-build bytes match committed source, but that does not retroactively create a pre-build witness. The original stage and gap remain retained. A follow-up at **`374024a02a5bcfae92f228570b9efe337d85b729`**, pushed to main, adds the missing input and a bounded same-start macOS exiting-state wait with better mismatch diagnostics. The latter addresses a source-supported possible failure mechanism; the older receipts cannot establish its historical cause. The combined deployment suite passes **138 tests**; an initial invocation missing `PYTHONPATH=scripts` and its six import failures are retained separately.

Stage 01 had already begun graceful drain when the gap was reported. Its old-PID guard then failed after one SIGTERM. The sanctioned stopped-transition recovery verified its exact checkpoint and one pending feedback item, without another signal. Stage 02 independently verifies **649 source inputs, zero uncovered compiler dependencies and all five artifacts**. Another **122** isolated Minime checks pass with its exact helper. The two stages' reader binaries are identical; only stage 02 supplies the complete input witness. Rust behavior is unchanged from the original full qualification.

Stage 02 manifest is `bbeaa882f3597d4d062a25db5d926489829f7052ebce5045808ed08a8a294170`; helper SHA-256 is `7636b8dc675e97ed6d7dce4c30df6d04ae802c7cac983c6b1028788ba224a100`. A preflight attempt waits out the normal shared-tree settling interval rather than weakening it. Final activation completes at **15:47:20.984879 UTC**, with Astrid PID **77906**, exact stopped checkpoint `b5a29f2b131eb28c327d794d024dada063439a77ce62363a526f4e720a2bbe3e`, one pending runtime-feedback item and self-control lineage. The saved exchange count advances from **200813 to 200815**. The final transition uses one SIGTERM and needs no recovery.

Minime reloads gracefully to PID **71419**, verified at **15:35:21.396054 UTC**, with all **82** startup sources matching committed main and model/launch settings unchanged. His startup log restores the pending `SELF_STUDY OPEN astrid/crates/astrid-approval/src/manager.rs 1` choice, session 5318 and cycle 35411; the next cycle consumes it and submits the matching job. This supports chosen-navigation continuity, not private-continuation uptake. No old job is interrupted. Paired verification ends at **15:48:45.055301 UTC (08:48:45 PDT)**. All **ten** surrounding process identities in the shared snapshot remain unchanged; the Minime wrapper also verifies its additional feeder. Neither restart procedure claims an atomic global traffic barrier or confirmed remote delivery.

The frozen natural-only window is **15:48:45.055301–15:58:45.055301 UTC**, end exclusive. The immediate snapshot occurred 15.15 seconds after the cutoff; final capture occurred 13.84 seconds after the end, within the declared late-artifact allowance. Selection stays tied to in-window completion/receipt clocks. Because the two release stages use the same reader bytes and earlier exposure already occurred, this is a post-final-verification cohort, not first-ever exposure or a causal comparison. Exact preparation time remains unknown; neither selected response qualifies as proven prepared after cutoff.

| Natural observation | Astrid | Minime |
| --- | ---: | ---: |
| Unique accepted study wire pairs in the window | 0 | 2 |
| Exact complete offered input with new interface framing | 0 | 2 |
| Selected for close reading / target | 0 / 2 | 2 / 2 |
| Proven preparation after cutoff | 0 | 0 |
| Selected normal-stop responses | 0 | 2 |
| Selected finding-save/remove attempts | 0 | 0 |

No private-writing receipt occurs, so natural bare-CONTINUE normalization remains unobserved. Its complete path is qualified by the isolated dispatch/draft tests and loaded source identities. Astrid's retained runtime snapshots show other modes, including witness context, journal elaboration and aspiration; absence of study does not imply malfunction or lost choice.

Minime's selected responses finish at **15:51:39.706 UTC (535 tokens)** and **15:55:32.957 UTC (689 tokens)**. He receives `astrid/crates/astrid-approval/src/manager.rs` lines **467–591** and **592–715**, each with exact delivered-line framing, current **6/6** finding capacity and optional replacement/drop actions. He makes no finding, note or question update; all six findings remain unchanged. Both responses select `SELF_STUDY CONTINUE`. These selections alone do not establish the later dispatch of those particular choices.

The first response accurately identifies the transition into test helpers and that `SessionApproveHandler` begins at the page end. However, it describes `BoundaryInspectHandler` assertions as production validation and a raw-to-validated transition. The supplied fixture expects an attached packet, checks fields and returns `Approve`; it does not establish that generalization. The second page accurately describes several local test expectations, then strengthens the unestablished claim that this manager is the definitive gate and that the kernel consumes its outcomes. Its opener repeats the prior transition-into-tests description even though this page is already inside tests. Both prose accounts retain the underscore spelling `astrid_approval`; the supplied path uses a hyphen. Their selected command is CONTINUE, so this is a prose identity error, not evidence of another failed OPEN.

The useful distinction is **working delivery with persistent inference errors**. New page/capacity framing is observed. Use of save-result feedback and private normalization has no natural opportunity in this window. No general improvement in understanding, durable correction or change in writing variety is established.

The retained report has **zero capture errors** and verifies all **61 indexed record versions**; frozen replay reproduces the summary byte-for-byte. Both broad job-directory scans hit the prespecified 20,000-entry cap on each of six snapshots (**12 bounded scans**). Exact linked generation/job records remain available, but the unsaved-failure census is incomplete. A third Minime study job was still running at final capture; its outcome is censored. The two accepted receipts are not a denominator for provider success. Existing S-007 selections, cutoffs and sealed packets are unchanged.

[The evidence index](2026-09-17-study-interface-repairs-evidence.json) binds the private packet, protocol, source/rollout receipts, qualification logs, exact study material and annotations. The owning [implementation note](/Users/v/other/astrid/docs/steward-notes/2026-09-17-study-interface-repairs.md) separates both transitions and the recovered first-stage failure.

The next behavioral question is whether naturally chosen reading or comparison supports a correction that survives later turns, particularly around Minime’s preserved admission-gate account. This implementation adds no model retune, longer-writing requirement, forced topic change or live activation feedback. S-007’s fixed selection and sealed historical packets remain separate; this draft does not alter them.

**Board updates pending.** Mirror the three completed interface repairs, source commits, verified rollout and bounded natural findings with their limits. Behavioral improvement remains unestablished.
