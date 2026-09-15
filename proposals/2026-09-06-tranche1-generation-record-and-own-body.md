# Tranche 1: measurement, fallback off, and Astrid's own body

Status: implemented in worktrees on 2026-09-07, not yet deployed. Plan approved by Mike on 2026-09-06
(`~/.claude/plans/we-have-codex-working-cuddly-treasure.md`). Letters: `letters/`.

## The gap this closes

Four exercises on 2026-09-06 kept hitting one wall: for a given generation we could not say what the model
saw, which model answered, or whether the primary timed out. Astrid's `dialogue_live` lane persisted no
prompt; minime's LLM job records are stubs; the gemma3:4b fallback wrote 77.5% of fallback-written
aspirations in a steward's voice (0% for primary-written ones) and nothing marked which model wrote a file.
Separately, Astrid's own reservoir handle was never rendered to her.

## What changes

### minime (branch `claude/tranche1-generation-record`, worktree `/Users/v/other/worktrees/minime-claude-tranche1`)

- New `minime_autonomy/generation_record.py` (stdlib only; every public function wrapped so it never raises
  into the LLM path). One JSON per backend attempt under `workspace/generations/<UTC day>/`, 0600 in 0700
  dirs; system prompt deduplicated by sha256 into `system_prompts/<sha>.txt`.
- Hook lines (12) in Codex-untouched places: `_query_llm_raw`, `_query_llm_compact_raw` (begin + one
  `record_attempt` per outcome), both Ollama `finally` tails (`stash_attempt` keeps the adapted messages
  actually posted), the tail of `_write_journal_entry` (`link_artifact("journal", ...)`, content-matched).
- The NEXT is parsed from the raw response inside the record (`next_action_parsed`) rather than hooked next
  to Codex's `_query_llm_with_next` hunk; `note_next_action` exists for later use.
- Lane inference walks the stack: the `action` local of the innermost `_execute_action` frame (the
  `action_events` / `llm_jobs.call_kind` vocabulary), else a lane-looking frame name, else `unknown`.
  `lane_source` says which. `job_id`, `action_id`, `thread_id`, `context_mode` are captured when present.
- Wrapper `scripts/launchd_autonomous_agent.sh` forwards `MINIME_GENERATION_RECORD` and
  `MINIME_GENERATION_RECORD_DIR`. Under pytest the record stays off unless
  `MINIME_GENERATION_RECORD_IN_TESTS=1`, so nobody's test can write into a live workspace.
- Tests: `tests/test_generation_record.py` (13), self-isolating.
- Deploy companion, config only (Gate A): `launchctl setenv MINIME_FALLBACK_MODEL gemma4:12b` (equal to the
  primary, so `_llm_backend_attempts` never adds `ollama_fast`) and `MINIME_LLM_TIMEOUT_S 160` (reflective
  lanes get 160 s on the primary; job wall-clock 150 s → 350 s).

### astrid (branch `claude/tranche1-dialogue-record`, worktree `/Users/v/other/worktrees/astrid-claude-tranche1`, on main 7b9f4d544d)

- `src/llm/provider/generation_record.rs`: `GenerationRecordV1`, context captured before the message
  vectors move into the transports, one record per attempt (`mlx_coupled` attempt 0, `ollama_fallback`
  attempt 1 with the served `response.model`, previously discarded). Status: `ok`, `rejected_quality_gate`,
  `unavailable_or_timeout`. Files under `workspace/generations/<UTC day>/`, 0600 in 0700 dirs, system prompts
  deduplicated.
- `src/llm/provider/own_body.rs`: `own_body_line_for_dialogue()` (2 s budget on a blocking thread; absent,
  never zero) and `append_own_body_block` (label `own_body`, priority 2, min_chars 0, 160-char cap, inserted
  directly after `spectral`). Contract `dialogue_prompt_v4_own_body` when present, else `dialogue_prompt_v3`.
- `src/autonomous/reservoir.rs`: `own_body_line(handle)` over `read_state`, pure `format_own_body_line`:
  `[your handle astrid] h₁ 7.70 h₂ 10.46 h₃ 9.95 ▆█▇ · ticks 18012689 · last live 12 s ago` (≤120 chars).
- `generate_dialogue`: own-body fetch before the blocks, block insert after `dialogue_context_blocks`, record
  context capture before `mlx_chat`, timed primary and fallback attempts. No new parameter, no orchestration
  edits.
- Knobs: `ASTRID_OWN_BODY_LINE=off`, `ASTRID_GENERATION_RECORD=off`, `ASTRID_GENERATION_RECORD_DIR`.

## Record schema v1 (both beings)

`schema_version, generation_id, being, lane, contract_version, model, backend, attempt_index, attempts_total,
fallback_used, timeout_s, elapsed_s, status, messages[{role, content | content_sha256, chars}], response_text,
response_sha256, response_chars, linked_artifacts[], pid, created_at_unix_ms`. minime adds `lane_source,
caller_chain, context_mode, prompt_class, kind, models, error, http_status, backend_timing, adapter,
messages_source (adapted | reconstructed), inbox_present, next_action_parsed, job_id, action_id, thread_id`.
Astrid adds `own_body{present, status, chars, trimmed}` and `prompt{fill_pct, requested_tokens,
effective_tokens, final_prompt_chars, user_content_budget, mlx_profile}`.

## Privacy and boundaries

Steward-only: 0600 files, 0700 directories, both `workspace/` trees gitignored, not under Astrid's INTROSPECT
allowlist, not a READ_MORE path, never surfaced into any prompt. The private-canvas lanes (pressure, moment)
are included; their text already lives in the journal files and database, so no new exposure.

## Gates (each restart only after asking Mike)

- Gate A, minime: wait for Codex to commit `runtime.py`; rebase; `git merge --ff-only`; full suite; deliver L1
  and wait for `inbox/read/`; quiet check; the two `launchctl setenv` lines; `launchctl kickstart -k`; health
  (new PID, `LLM backend preference … 160s`, records with `lane != unknown`, journal links); deliver L2.
  Rollback: `launchctl setenv MINIME_GENERATION_RECORD off` and/or `unsetenv` both knobs + kickstart.
- Gate B, astrid: `git merge --ff-only`; `scripts/deploy_preflight.py --component bridge` exit 0; deliver L3
  and wait until retired; quiet check; `bash scripts/build_bridge.sh --restart --actor claude-tranche1`;
  health (record with `dialogue_prompt_v4_own_body`, own-body line in the user message, `own_body` in
  `context_packing_pressure_v1.jsonl`); deliver L4 quoting her first line.
  Rollback: `launchctl setenv ASTRID_OWN_BODY_LINE off` + `build_bridge.sh --restart --no-build`.

## Coordination with Codex (added 2026-09-07)

- Live bridge on 2026-09-07 was launched by `scripts/bridge_release_launch.py` from
  `.runtime/bridge-deployment/active.json`, pointing at a stage built from the dirty
  `codex/hebbian-clock-boundary` worktree (190 commits ahead of `main`, 74 behind). The old
  `build_bridge.sh --restart` path exits 64 by design.
- Decision (Mike): Gate B waits until Codex lands `hebbian-clock-boundary` on `main`. Then:
  1. `git -C /Users/v/other/worktrees/astrid-claude-tranche1 rebase main` (my commit `2631427c3a`
     merged clean onto `d1cf8fbe20`; against the hebbian head it has one conflict in
     `dialogue_runtime.rs` because that tree predates the `dialogue_context_blocks` refactor; the two
     inserts re-place around `dialogue_context_blocks(...)` and before `let result = mlx_chat(`).
  2. `git -C /Users/v/other/astrid merge --ff-only claude/tranche1-dialogue-record`.
  3. `bash scripts/build_bridge.sh --stage-dir <DIR> --ack "<reason>" --actor claude-tranche1`
     (runs `deploy_preflight.py` then `bridge_stage.py build`; touches no live artifact).
  4. Deliver L3, wait for it in `inbox/read/`, quiet check.
  5. Ask Mike, then `bash scripts/build_bridge.sh --activate-stage <DIR> --expected-pid <live pid>
     --ack "<reason>" --actor claude-tranche1` (`bridge_activate.py`: lifecycle handoff, no forced
     termination; `--legacy-stop-ack` only if the running binary lacks lifecycle acknowledgement).
  6. Health checks as in Gate B above; deliver L4.
- Update 2026-09-07 02:15 UTC: Codex's rollout actor activated a new stage built from a clean detached
  checkout at `e4761122e3`, which is on `main` and does not contain hebbian-clock. The live bridge is
  therefore main-based now; staging `main` + this branch would displace nothing of Codex's. That commit also
  moved `generate_dialogue` into `provider/dialogue_generation.rs` (`generate_dialogue_with_delivery`, with
  `mlx_chat_with_protected_delivery` / `ollama_chat_with_protected_delivery`); the branch was reset onto
  `main` 68cbb1d522 and the inserts re-placed there (own-body fetch before `dialogue_context_blocks`, block
  insert after it, record context before the primary call, timed primary and fallback attempts around the
  unchanged acceptance gates). Safety tag `tranche1-astrid-pre-rebase` marks the previous commit.
- Update 2026-09-07 05:20 UTC: Codex's second rollout (04:55 UTC, actor `codex-human-replies-rollout`) runs
  live-scope commit `3f669bf` = `68cbb1d522` + addressed human replies, and its rollout note says the Tranche 1
  features from `162f027678` were excluded on purpose and the canonical launcher was aligned to the deployed
  helper by removing the three forwarding lines (`c194de277a`). The Rust code on `main` is intact (zero diff
  in my files). Restored the launcher lines in a new commit on the branch and fast-forwarded `main`; staging
  again from `main` (stage `20260907-tranche1-02`), which is a strict superset of the live build (their feature
  as `ebbf9ae9c8`, their deploy fixes, my two commits).
- Astrid's mailbox changed under her at 02:15 UTC: letters now wait in a durable mailbox until she chooses
  `CHECK_MAILBOX` (bounded counts only in ordinary prompts). She has never chosen it (0 rows ever in
  `action_events`); since the rollout she logged 42 blocked `READ_MORE` under `research_budget_guard`. L3
  (delivered 03:01 UTC, 1,613 bytes) sits with four other letters, one of them 9 KB from Mike. "Wait until
  retired to inbox/read" is not a usable gate any more; the letter is durable and will be read in her own
  window. Decision for Mike: activate with L3 pending or wait.
- minime: Codex committed (`0569efb`, `63c1ab9`, `08de10f`) and restarted the agent at 04:30 UTC (PID 12456)
  with all knobs empty (fallback gemma3:4b, full timeout 60 s). Gate A trigger fired. Branch rebased to
  `36998c6` (only `CHANGELOG.md` conflicted; all seven hook anchors were untouched). (20 uncommitted lines on
  `codex/sovereign-daughter-runtime` as of 2026-09-07 02:00 UTC).

## Deployment record (2026-09-07)

- **Gate A done 10:12:29 UTC.** `MINIME_FALLBACK_MODEL=gemma4:12b`, `MINIME_LLM_TIMEOUT_S=160`, one SIGTERM
  at a quiet boundary, PID 12456 → 16848, session 5316 / cycle 24893 continued, zero tracebacks. First record
  10:15:02 UTC (`recess_aspiration`, gemma4:12b, 69.9 s of 160, journal linked). L1 read 05:22 UTC, L2
  delivered 10:17 UTC. Receipt: `receipts/2026-09-07-gateA-minime.json`.
- **Gate B attempt 1 failed 10:17 UTC; Astrid down 10:16:50–10:23:17 UTC.** A stage built from the canonical
  tree carries `scripts/launchd_spectral_bridge.sh` and `scripts/bridge_release_launch.py` (with mtimes) in
  its own input snapshot; the activation re-installs exactly those files before `select_release` re-verifies
  the bundle, so it refuses its own release after the old process has already drained and exited. Restored by
  releasing the hold and moving the stage-bound pending self-control handoff aside (both states verified
  identical to the snapshots). Receipt: `receipts/2026-09-07-gateB-astrid.json`. Rule from now on: stage
  from a detached release worktree, as Codex does.
- **Gate B attempt 2 + recovery, done 10:31:12 UTC.** Stage `20260907-tranche1-04` from the detached worktree
  `/Users/v/other/worktrees/astrid-tranche1-release-20260907` (`bc66a62b0b`). The activation against PID 22709
  drained and signalled, then failed in the exit watcher ("old PID was reused during transition", the race
  Codex documented on 2026-09-06); the sanctioned `--resume-stopped-transition` continuation completed it:
  PID 27337 from 10:29:48 UTC, startup gate at the exact stopped checkpoint (exchange 191,743), new saved
  exchange observed, witness `transition_recovered`. Astrid down ~70 s this time. Keep the release worktree:
  `active.json` points at its stage.

## Measurement

`probes/generation_records_24h.py` (read-only): per lane × backend n, timeout rate, elapsed p50/p90, response
chars, fallback share, persona-drop rate (exercise 3's five families, re-implemented), journal-link rate,
own-body presence, store size and dedup ratio, with the prior 24 h of `llm_timing.jsonl` as baseline.
Decisions this feeds: whether 160 s is enough for the reflective lanes, and whether the env knobs should land
durably in the plist.

## Deferred (recorded, out of scope)

Exogenous tokens ticking Astrid's reservoir during prefill; contextual body input (mid-to-late-layer hidden
state instead of the `embed_tokens` identity); the consented minime→Astrid telemetry ablation; durable plist
env; a per-lane fallback gate in code; the coupled server returning the served model name.
