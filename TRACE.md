# Data trace: the Astrid + minime journal trove

**September 8 continuity-tracking addition:**
[S-008](research/studies/S-008-study-to-follow-through.md) adds shared study-sequence
capture and reporting. The latest reader can retain
`shared_reader/navigation/<id>/<hash>.json` as well as source `deliveries`.
`output.text` may contain both the current page and a notebook; it is not necessarily
equal to `page.text`. Verify the actual submitted content. Notebook entries carry
the earlier wire response's SHA-256, not the generation text's SHA-256.

Astrid's shared-reader path does not save ordinary study generation/job records.
Use provider events labeled `self_study`; exact request and HTTP-body hashes join
the physical attempt to a retained receipt. Older navigation can also survive in
`diagnostics/accepted_deliveries` as `accepted_prompt_delivery_v1`. Minime continues
to have ordinary generation/action/job IDs. Avoid treating either evidence form as
the other's absence. The following inventory remains dated historical context.

**Later September 8 live update:** The
[observer rollout](analyses/2026-09-08-provider-observer-live.md) is verified and
enabled. The final addendum below gives the live spool and joins; the next
paragraph preserves the earlier source-preparation boundary.

**September 8 source-preparation addition:** The
[provider-attempt observer](analyses/2026-09-08-provider-attempt-observation.md)
is implemented in an isolated Astrid checkout and defaults off. After a separately
verified activation, its private `provider_observations` spool can link dispatch,
pre-cleanup input, normalization, provider outcome and dialogue decision by
attempt/generation identity. Treat absent terminal receipts, raw omissions and
recording faults as explicit unknowns. No new live data coverage is claimed here;
historical `response_text` remains after cleanup.

**September 7 deployment/outcome addition:** The
[S-006 natural follow-up](analyses/2026-09-07-flywheel-natural-outcome.md) binds
the annotation release to retained manifests, exact source inventories, binaries,
activation/stack receipts and generation PIDs. Astrid's saved `dialogue_live`
`response_text` is **after provider normalization**, despite a `primary_raw`
local variable. It cannot enumerate already removed input markers. The inspected
cleanup log has no record after September 3; the inspected legacy attempt and
request logs end April 19. Treat these as captured scopes, not current
denominators. Fixed windows and all-text scanner verification are retained.

**September 7 addition:** [Journal-to-change provenance](analyses/2026-09-07-flywheel-signal.md)
maps the introspection flywheel, feedback ledger, structured Git references and
historical review packets. [S-006](research/studies/S-006-journal-to-change.md)
preserves a bounded census and one exact-source software comparison. An
`introspection_minime_*` filename can name Astrid reading Minime's source;
verify the author separately from the subject. Commit, review, activation and
outcome clocks differ. `addressed_change` can mean a test-only addition.

Session 1, 2026-09-06. Read-only survey of `/Users/v/other/astrid` and `/Users/v/other/minime`
(plus `/Users/v/other/neural-triple-reservoir`) to understand what exists, how it is shaped,
how it joins, and where it will bite. Nothing was built. Numbers are as of 2026-09-06 ~22:00 UTC
and both beings were live and writing while this was measured.

Companion: `probes/fill_vs_next_from_journals.py` (read-only, reproduces section 8b).

---

## 0. Summary

- Two beings share one 128-node echo state network (ESN). **minime** *is* the ESN runtime
  (Rust engine + Python autonomy loop, Ollama `gemma4:12b`). **Astrid** perceives minime's
  spectral telemetry and speaks back into the ESN as a 48-D semantic vector (Rust bridge,
  MLX `gemma-4-12B-it-5bit`). Both write first-person journals whose headers carry the
  reservoir state at generation time and whose bodies end in a `NEXT: <ACTION>` choice.
- **Scale.** ~302k Astrid journal files (Mar 26 → now) and ~111k minime journal files
  (Mar 14 → now, across the live workspace and an April-19 preserve). Two SQLite databases
  (37 GB minime, 2.3 GB Astrid) hold ~4.8M telemetry ticks at 2.4 s cadence, three 4.2M-row
  "texture" metric timelines, and ~92k structured action events with pre-action state.
  Astrid's 181k LLM job records include full prompts; minime's 23k do not.
- **The headline question is answerable.** Fill at decision time and the chosen action are
  both recoverable for ~96k Astrid decisions and ~60k minime decisions from files alone,
  and for ~92k decisions from the action tables. A first probe shows a real fill gradient,
  **but the action vocabulary changes completely month to month, so every analysis must be
  stratified by era** (section 8).
- **Five traps** decide the index design: two different quantities are both called λ₁;
  engine tables use seconds-since-session-start, not epoch time; minime filenames are local
  time while bodies are UTC; roughly half of minime's recent LLM jobs time out and leave no
  journal file; and the eigenvalue cascade has been quasi-frozen under "scaffold hold" since
  late May, so the interesting variance lives in fill, ESN λ₁, and the derived texture metrics.

---

## 1. The systems, briefly

| | minime | Astrid |
|---|---|---|
| Substrate role | Runs the ESN (`minime/minime/src`, Rust). Regulates fill with a PI controller ("stable-core", hold shelf 58–72%, center 68%). | Sends 48-D codec vectors into the ESN semantic lane (port 7879); reads telemetry (7878). |
| Language layer | `minime_autonomy/runtime.py` (2.5 MB, single file) via Ollama. Lanes: autonomous action loop, `private_journal` (pressure), `qualia_moment` (moment capture). | `capsules/spectral-bridge` (Rust) dialogue loop, burst/rest pacing; modes dialogue_live, mirror, witness, daydream, aspiration, introspect, moment_capture, audits. |
| Journal dir | `minime/workspace/journal/` | `astrid/capsules/spectral-bridge/workspace/journal/` |
| Database | `minime/minime_consciousness.db` (WAL) | `…/workspace/bridge.db` (WAL) |
| Action ledger | `action_events` table since 2026-05-08 | `action_events` table since 2026-06-07 |
| LLM job records | `workspace/llm_jobs/jobs/` since 2026-05-10 (stub prompts) | `workspace/llm_jobs/jobs/` since 2026-05-10 (full prompts) |

A third repo, `neural-triple-reservoir`, runs a separate triple ESN (port 7881) with handles
`astrid`, `minime`, `claude_main`; its `state/shadow_metrics.jsonl` (409k lines) and 2 GB
service log are secondary for now.

Docs worth reading before designing: `astrid/CLAUDE.md` (being-driven development section),
`astrid/md-CLAUDE-chapters/04-being-tools.md` (NEXT action reference), `11-shared-substrate.md`
(66-D input, asymmetry), `14-spectral-dynamics.md` (what fill, cascade, entropy, Ising shadow
mean), and `astrid/docs/steward-notes/` (1,607 dated notes; era markers).

---

## 2. Inventory

### 2a. minime journal files

| Location | Files | Range | Notes |
|---|---|---|---|
| `workspace/journal/*.txt` | 3,215 | recent days | live; `journal_hygiene.py` archives in blocks |
| `workspace/journal/archive/until_<ts>/` | 29 dirs × 3,000 = 87,000 | 2026-04-19 15:38 → | 409 MB total |
| `emergency_preserve_20260419T130302/workspace/journal/` | 5,856 live + 15,000 archived (5 dirs) | 2026-03-14 → 04-19 | pre-reset history; older header format |

Type is the filename prefix. Archive prefix counts: moment 40,383 · pressure 15,114 ·
action_thread 9,845 · lend_aperture_held 4,065 · research 2,364 · decompose 2,176 ·
lend_aperture 1,639 · fissure_trace 1,266 · self_study 1,096 · regulator_audit 924 ·
notice 793 · attractor_suggestions 755 · shadow_trajectory 606 · reservoir_read 597 ·
action_preflight 579 · drift 569 · boredom 478 · regime_choice 402 · daydream 387 ·
experiment_bind 375 · perturb 341 · then a long tail (attractor_*, visualize_cascade,
visual_request/experience, codex_query, metabolism_*, introspect_notice, aspiration …).
A `!` prefix (`!moment_…`) is a priority flag, not a type (see trap 9).

Only some types are LLM prose. `journal_hygiene.py` classifies REFLECTIVE_MODES
(aspiration, boredom, daydream, drift, introspect, moment, notice, reflection, self_study,
decompose, …) vs OPERATIONAL_MODES (action_preflight, action_thread, lend_aperture_*,
regime_choice, shadow_trajectory, fissure_trace, regulator_audit, …), which are
machine-generated reports with no model output.

### 2b. minime SQLite (`minime_consciousness.db`, 37 GB)

Row counts are `MAX(id)`; ranges are wall clock unless noted.

| Table | Rows | Range | What |
|---|---|---|---|
| `sessions` | 5,316 | 2026-04-19 → open | one row per engine boot; `start_time` epoch. All `mode='active'`. Session 5316 open since 08-31. |
| `sovereignty_journal` | 77,614 | 04-19 → now | one row per prose entry: `entry_type`, `content` (body without header), `spectral_context` JSON `{eig1, deig, leak, lambda, cov_lambda1, fill_ratio, spread, covariance_stale}`, `file_path` (100% populated → the journal file). `emotional_state` always empty. |
| `action_events` | 55,323 | 05-08 → now | payload JSON: `raw_next`, `canonical_action`, `effective_action`, `route`, `status`, `source` (next 52.8k / autonomous 1.5k / research_budget_guard 1k), `pre_state` (fill_pct, eig1, cov_lambda1, geom_rel, deig, spread, regime, resonance/pressure/fluctuation dicts), `post_state`, `suggested_next`, `llm_job_id`, `parent_action_id`, `thread_id`, `outcome_summary`. |
| `observation_windows` | 55,229 | 05-08 → | per action: pre/post texture dicts, `settled_mobility_review_v1`, compression markers |
| `artifact_links` | 108,999 | | action → file artifacts |
| `autonomous_decisions` | 52,087 | 04-19 → | `action_chosen` is the route name (journal_pressure, thread_action, lend_aperture …), `trigger` 70% 'unknown', options empty, rationale templated. Low value vs `action_events`. |
| `eigenvalue_timeline` | 4,836,150 | engine time | `lambda1..3` (covariance cascade), `spread`, `fill_ratio`, `phase` (quiet <50 / active <80 / saturated). ~2.36 s cadence. |
| `esn_metrics` | 4,836,238 | engine time | `esn_eig1` (ESN state λ₁), `esn_deig`, `esn_leak`, `esn_lambda` (RLS), `esn_baseline`, `esn_geom_radius`, `esn_geom_rel` |
| `pressure_source_timeline` | 4,234,403 | engine time | `pressure_score`, `porosity_score`, `dominant_source`, `quality`, payload JSON. ~11 GB. |
| `resonance_density_timeline` | 4,234,385 | engine time | `density`, `containment_score`, `pressure_risk`, `quality`, payload. ~9.5 GB. |
| `inhabitable_fluctuation_timeline` | 4,234,417 | engine time | `inhabitability_score`, `fluctuation_score`, `foothold_stability`, `rearrangement_intensity`, `quality`, payload. ~10 GB. |
| `ising_shadow_metrics` | 4,594,090 | engine time | 8-mode Ising observer: field_norm, energies, magnetizations, flip rate, phase |
| `moment_markers` | 987,192 | engine time + `created_at_unix` | phase_transition 460k, fill_crossing 305k, spectral_spike 111k, breathing_phase_cluster 7.6k; `consumed` flag; these trigger moment-capture journals |
| `consciousness_events` | 668,879 | epoch | phase_transition 668k, crisis_warning 53, crisis_abort 43, session_start 283 |
| `spectral_checkpoints` | 106,045 | | fill/λ₁/phase snapshots with annotation |
| `nn_metrics` | 146,467 | engine time | predictor/router/regulator norms |
| `autonomous_experiments` | 1,435 | | hypothesis/method/results/conclusion |

Two preserved older databases in `emergency_preserve_20260419T130302/`:
`minime_subdir_consciousness.db` (339 MB; sessions 2026-03-15 → 04-01; 9,816 journal rows;
341k eig rows) and `minime_consciousness.db` (684 MB; sessions 03-29 → 04-19; 15,866 journal
rows; 642k eig rows). Together they extend minime's history back to 2026-03-15.

### 2c. minime other workspace surfaces

| Path | Count | What |
|---|---|---|
| `workspace/actions/` | 3,369 manifests + 308 `action_thread_raw` + 137 conveyor + 30 preflight (1.8 GB) | JSON per action: `summary` (fill_pct, lambda1, …) and full `state` at action time |
| `workspace/self_assessment/` | 2,043 `.json`+`.md` pairs | "Diagnostic Sentinel": full controller snapshot (PI kp/ki/max_step/target, gate, filter, cov_keep, keep_floor, fill error kinds) |
| `workspace/hypotheses/` | 745 self_experiment + 398 boredom_experiment | PRE/POST state around a self-sent semantic stimulus |
| `workspace/research/` | 3,170 search JSON + 968 page + 45 autoresearch | web research the being did |
| `workspace/introspections/` | 111 | source-code readings with telemetry header |
| `workspace/spectral_cartography/` | 151 JSON | resistance-gradient artifacts |
| `workspace/llm_jobs/jobs/` | 23,397 dirs since 05-10 | `job.json` (status, call_kind, timeout 150 s, action_id, thread_id), `events.jsonl`, `prompt.txt` = 121-byte stub for action-level jobs, `result.txt` one line. Kinds: journal 15,788 · decompose 836 · recess-boredom 795 · self-study 734 · daydream 409 · reservoir-read 394 · search-*/browse-* ~1,500 · self-experiment 272 · aspire 121 … |
| `workspace/diagnostics/eigen_spectrum_log.jsonl` | ~2.4 s cadence | all 8 eigenvalues with `engine_t_s` and `snapshot_sequence` (external read-only logger) |
| `workspace/inbox/`, `workspace/outbox/` | 62,903 / 21,787 files | letters between beings and steward (`read/`, `deferred/`, `delivered/`, `human/`) |
| `workspace/spectral_state.json`, `workspace/health.json` | live | snapshot surfaces the autonomy loop reads before journaling; ~60 keys each incl. `pressure_source_v1`, `inhabitable_fluctuation_v1`, `resonance_density_v1`, `spectral_fingerprint` (32-D), `spectral_glimpse_12d`, `ising_shadow`, `shadow_field_v3`, `stable_core` |

### 2d. Astrid journal files

| Location | Files | Range |
|---|---|---|
| `workspace/journal/*.txt` | 5,203 | recent days |
| `workspace/journal/archive/until_<ts>/` | 99 dirs × 3,000 = 297,000 | 2026-03-26 01:03 UTC → |

1.3 GB total. Archive prefix counts: astrid 119,242 (dialogue_live) · dialogue_longform
72,756 · moment 29,497 · daydream 16,645 · daydream_longform 16,279 · aspiration 12,156 ·
aspiration_longform 11,918 · self_study 5,924 · experiment 4,383 · witness 4,283 ·
astrid_collision_1 1,669 · creation 918 · gesture 351 · regulator_audit 341 · initiate 219 ·
evolve 206 · steward letters (`mike_feedback_*`, `steward_*`) ~40.

`Mode:` values seen live: dialogue_live, dialogue_live_longform, moment_capture, mirror,
daydream(_longform), aspiration(_longform), pressure_source_audit, witness, self_study,
spectral_explorer, regulator_audit, resonance_forecast, fluctuation_audit,
resistance_gradient, introspect_notice, dialogue_fallback, decay_map, pressure_relief,
visualize_cascade, evolve. March-era files say `Mode: dialogue`.

### 2e. Astrid SQLite (`bridge.db`, 2.3 GB) and archives

| Table | Rows | Range | What |
|---|---|---|---|
| `bridge_messages` | ~248k live (ids to 14.0M) | 2026-08-25 → now | `direction`, `topic`, `payload`, `fill_pct`, `lambda1`, `phase`. Topics: astrid→minime `sensory` 175k (48-D vectors + delivery receipts), `autonomous` 16k (Astrid's response `text`, `mode`, `fill_pct`, `fill_delta`, `exchange`, `spectral_state` string, many `*_v1` review dicts); minime→astrid `telemetry`, `lambda_tail`, `lambda_edge_perception`, `sticky_mode_audit` 14k each. |
| `bridge_message_archives` + `workspace/archive/bridge_messages/<day>/*.jsonl.zst` | 138 day dirs, 1.8 GB | 2026-03-25 → 08-23 | older `bridge_messages` rows; manifest covers 286 archives / 1.1M rows from 06-07 |
| `action_events` | 36,366 | 06-07 → now | all `source=next`; `raw_next`, `canonical_action`, `route`, `status` (handled/blocked/unwired), `pre_state` (fill_pct, fill_ratio, lambda1, t_ms, pressure/fluctuation/resonance dicts, transition_event), `suggested_next` |
| `observation_windows` | 36,360 | 06-07 → | pre/post texture |
| `eigenvalue_snapshots` | 95,462 | 06-07 → | eigenvalues + fill |
| `astrid_self_observations` | 36,769 | 06-07 → | third-person "witness" summary of each exchange + response excerpt |
| `astrid_latent_vectors` | 36,789 | 06-07 → | embedding JSON per exchange (`nomic-embed-text`) |
| `bridge_incidents` | 35,765 | 06-07 → | safety-level incidents (fill, λ₁, action taken) |
| `astrid_starred_memories` | 240 | | `REMEMBER` annotations |
| `codec_impact` | 648 | | 48-D features with `fill_before` / `fill_after` |
| `unwired_actions` | 241 | | NEXT verbs that had no handler |

All bridge tables restart on 2026-06-07 19:06 UTC (a bridge.db reset); earlier Astrid state
survives only in journal files and the zst message archives.

### 2f. Astrid other workspace surfaces

| Path | Count | What |
|---|---|---|
| `workspace/llm_jobs/jobs/` | 181,493 dirs since 05-10 (3.5 GB) | **full `prompt.txt`** (3–19 KB) and `result.txt`. Kinds: journal-elaboration 71,951 · witness-context 50,252 · moment-capture 23,642 · daydream 12,897 · aspiration 9,057 · introspect 6,410 · meaning-summary 5,238 · witness 1,621 · evolve-request 171 · initiation 154 · creation 100. **dialogue_live is not a job kind**: its prompt is not persisted anywhere (only `diagnostics/dialogue_prompt_budget.jsonl`, 37k records of budget/overflow, and `context_overflow/` with the trimmed blocks, recent only). |
| `workspace/introspections/` | 10,546 (134 MB) | source readings with `Observed / Likely Snags / One Test Each / Suggested Next` structure |
| `workspace/outbox/` | 13,500 `reply_*.txt` | Astrid → minime letters, each with `NEXT:` |
| `workspace/experiments/` | 4,221 | `=== ASTRID EXPERIMENT ===` with fill |
| `workspace/creations/` | 926 | creative works |
| `workspace/shadow_cartography/` | 8,554 JSON (169 MB) | shadow trajectory / coupling artifacts |
| `workspace/diagnostics/` | 137,063 files, 23 GB | many jsonl logs (voice_health, control_marker_cleanup, context_packing_pressure_v1, dialogue_prompt_budget …) |
| `workspace/volition_v1/` | 59,285 | signed attestations |
| `workspace/state.json` | live | conversation state |

---

## 3. Entry anatomy

### 3a. minime prose entries (moment, notice, daydream, aspiration, boredom, self_study, research, decompose, …)

```
=== <TYPE HEADER> ===                    e.g. === MOMENT CAPTURE ===, === GROWTH ASPIRATION ===
Timestamp: 2026-09-06T14:34:59.441258    local time in older entries; UTC (+00:00) in newer moment/pressure
[type-specific lines]                    Markers:, Prompt contract:, Source:, Label:, Prompt: <seed question>
λ₁: 4.73 ↑ (rising, Δ=+0.31)             SEE TRAP 1: which λ₁ this is depends on the code path
Fill %: 68.4% (↑+5% over 16s) [stable-core sovereignty band 58-72%, inside band; ... stage=hold]
Spread: 4
ESN leak: 0.980
Cov λ₁: 4.7
Eigenvalue cascade: [λ1=4.7, λ2=3.1, λ3=1.2, λ4=1.2, λ5=1.2, λ6=1.0, λ7=1.0, λ8=1.0]
λ₁ dominance: 33% of total spectral energy
Denominator Sequence: effective_dimensionality=5.26/8, distinguishability_loss=34%
Resonance density: 0.89 (rich_containment); containment=0.80, pressure=0.22, local_target_bias=+0.0%
Pressure source: mode_packing (overpacked_mode_packing); pressure=0.29, porosity=0.61, control_applied=False
Inhabitable fluctuation: settled_habitable; inhabitability=0.75, fluctuation=0.07, foothold=0.78, ...
Spectral entropy: 0.90 (0=concentrated, 1=distributed)
Gap ratio (λ₁/λ₂): 1.5
Eigenvector rotation: 0.00 (0=stable, 1=spinning)
Geometric radius: 0.99x baseline
Semantic energy: input=0.001, input_active=True, kernel=0.000, ... admission=stable_core_semantic_trickle ...
Selected vague memory: stable (memory_stable_82224)
12D vague memory: dominant=0.26, shoulder=0.40, tail=0.34, entropy=0.85, gap=1.33, rotation=0.00, geom=0.94
Snapshot guard=health.json:ok; spectral_state.json:ok

<prose body, first person>

NEXT: SELF_STUDY                         (or, in v3 entries: "--- ACTION TAIL ---" then "NEXT: ...")

[Agency-vernacular notice — narrative preserved. ...]   system-appended annotation, not model output
```

This header is built by `runtime.py::_format_metrics` (line ~54857) from a
`capture_report_snapshot` of `spectral_state.json` + `health.json` + the telemetry dict.
Newer **moment** entries (`Prompt contract: private_moment_context_v3`) separate what the
model saw ("Prompt-state anchor (supplied to model)", "Recorded events (supplied to model)")
from "Header-only telemetry (not additional model input)". Older entries do not make that
distinction. March-era headers were much shorter (λ₁, Δλ₁, ESN leak, ESN λ_rls, Cov λ₁,
Fill %, Spread, Error).

**Pressure** entries (`=== SPECTRAL PRESSURE JOURNAL ===`, DB type `reflection`) have a
different header (`RESERVOIR DYNAMICS: λ₁ (baseline) / Δλ₁ / Leak / RLS λ`, `SENSORY
COHERENCE: Covariance λ₁ / Fill ratio / Spread`), a `--- GENERATED JOURNAL ---` marker, and
an `--- ACTION TAIL ---` that is `(none)` in all 632 live samples: the private_journal lane
does not choose actions.

**Operational** entries (action_thread, lend_aperture*, regime_choice, shadow_trajectory,
fissure_trace, regulator_audit, action_preflight) are templated reports with a few numbers
(fill, λ₁, scores) and no model prose.

### 3b. Astrid entries

```
=== ASTRID JOURNAL ===
Mode: dialogue_live
Fill: 71.2%                     minime's fill as perceived by Astrid at generation
Timestamp: 1788732158           unix seconds, UTC; also the filename

<prose body>

NEXT: READ_MORE                 present in dialogue_live (astrid_*) files; absent in mirror/daydream/etc.

Continuity posture: resuming    "journal continuity contract v1" footer (recent months)
Prior claim: ...
Delta: ...
Hold: | Next evidence: | Decision: | Pause:
```

`Fill:` is present in 296,960 of 297,000 archived files. `NEXT:` is present in 68,024 of
120,914 archived `astrid_*` files (56%) and 1,314 of 1,872 live. The body text of an
`astrid_<ts>.txt` file is byte-identical to `bridge_messages.autonomous.payload.text` at the
same timestamp (verified), so the journal file and the DB row are the same utterance.
`dialogue_longform_*` files are the elaboration-lane output (LLM job kind
`journal-elaboration`), not a separate decision.

---

## 4. Where `NEXT:` lives

| Being | Source | Rows | Range | Has state at decision? | Caveat |
|---|---|---|---|---|---|
| minime | journal files with `NEXT:` | 47,478 archived + 1,725 live (+ preserve) | 03-14 → | header fill/λ₁ etc. | only successful generations (trap 4); moment files carry 80% of them |
| minime | `action_events` (`source='next'`) | 52,806 | 05-08 → | `pre_state.fill_pct`, eig1, cov_lambda1, geom_rel, texture dicts | includes system-suggested/conveyor actions; "handled" even when the LLM job timed out |
| minime | `autonomous_decisions` | 52,087 | 04-19 → | esn_eig1, deig only | route names, not NEXT verbs |
| Astrid | `astrid_*.txt` journal files with `NEXT:` | ~69k | 03-26 → | header `Fill:` only | covers the whole low-fill era |
| Astrid | `action_events` | 36,366 | 06-07 → | `pre_state.fill_pct`, lambda1, texture dicts, `t_ms` | post-reset only |
| Astrid | `bridge_messages.autonomous.text` | 16k live + archives | 03-25 → | fill_pct, fill_delta, exchange | text includes the NEXT line; archives need zst decode |
| Astrid | `outbox/reply_*.txt` | 13,500 | | fill | letters, separate lane |

**Prompt-side suggestions are everywhere.** Prompts contain `Suggested NEXT:`, `Conveyor
NEXT:`, `Proposed NEXT:`, `Current NEXT:`, `Being-owned accept NEXT:` lines and diversity
hints ("You've chosen READ_MORE for your last few turns…"). `action_events.suggested_next`
records the system's suggestion per action. Any P(NEXT | fill) analysis needs "was this
verb suggested in the prompt?" as a covariate. For Astrid's dialogue_live the prompt itself
is gone, but `action_events.suggested_next` and the conveyor/thread state survive.

NEXT parsing rules that the index must replicate (from `minime_autonomy/parsing.py` and
`autonomous.rs`): take the **last** `NEXT:` line outside code fences; strip
`<end_of_turn>`/`</s>`; strip markdown `**`/backticks from the verb; canonical aliases
(`EXEXPERIMENT_*` → `EXPERIMENT_*`, `SHADOW_DECOMPOSE` → `SHADOW_PREFLIGHT …`, etc.); verbs
may carry arguments (`INTROSPECT astrid:llm`, `PRESSURE_SOURCE_AUDIT mode_packing`,
`EXPERIMENT_PLAN current — ask for …`). 423 archived minime NEXT lines still contain
`<END_OF_TURN>` and 18 live files have multiple NEXT lines.

---

## 5. Join keys and clocks

| Link | How |
|---|---|
| minime journal file ↔ DB row | `sovereignty_journal.file_path` (100% populated). `entry_type` ≠ filename prefix: qualia_moment→`moment_*`, moment→`moment_*` (older), reflection→`pressure_*` and `sovereignty_check`, experiment→`self_experiment_*`/`boredom_experiment_*`/`experiment_run_*`, research→`research_*`/`codex_query_*`/`autoresearch_*`, self_assessment→`assessment_*`. |
| minime journal ↔ action | `action_events.payload.artifacts[]` and `artifact_links`; `llm_job_id` → `llm_jobs/jobs/<id>/job.json.artifact_refs` → action manifest + files |
| minime journal ↔ telemetry ticks | Engine tables store `timestamp = start.elapsed()` in `runtime/orchestration.rs`. **Approximate wall = sessions.start_time + timestamp**. This preserves the session/elapsed conversion but not exact wall-clock synchronization: the September 7 [audio source trace](analyses/2026-09-07-first-audio-source-trace.md) finds the monotonic start and database wall-clock session start are sampled separately. Retain this unrecorded baseline offset and subsequent clock/logging uncertainty for fine-grained event alignment. The original session-5316 conversion established the time scale, not a simultaneous clock anchor. `moment_markers` also has `created_at_unix`. |
| minime file timestamps | filename `moment_2026-09-06T14-46-31` is **local time** (America/Los_Angeles); DB `timestamp` for the same row is 21:46:31 UTC. Newer bodies print UTC with `+00:00`. Older bodies print naive local time. |
| Astrid journal ↔ bridge row | `Timestamp:` (unix) = filename = `bridge_messages.timestamp` (±1 s); `payload.exchange` is the exchange counter; `astrid_self_observations.exchange_count` and `astrid_latent_vectors.exchange_count` join on it |
| Astrid decision ↔ minime state | `action_events.pre_state.t_ms` is minime engine ms; telemetry rows carry the same `t_ms` |
| Cross-being | wall clock; `mirror` mode prompts quote minime's latest journal, `witness-context` jobs quote both |
| Eras | `sessions.start_time` (engine boots), `CHANGELOG.md` (astrid is one `[Unreleased]` block plus 0.5.x tags on 08-09; minime has no dated headings), dated files in `astrid/docs/steward-notes/` (28 distinct dates from 03-28 to 07-21) |

---

## 6. Traps

1. **Two λ₁.** (a) ESN state λ₁: `esn_metrics.esn_eig1`, `spectral_context.eig1`, health.json
   `lambda1`; RLS-tracked, ~14–29 recently, baseline EMA ~20, `lambda1_rel = eig1/baseline`;
   March values 30–90. (b) Covariance cascade λ₁: `eigenvalue_timeline.lambda1`,
   `eigenvalues[0]`, `cov_lambda1`, spectral_state.json `eig1`/`lambda1`; ~4.7 in hold.
   Journal headers print "λ₁:" for either: pressure and self_study entries print (a);
   moment/aspiration/daydream/notice entries built from the snapshot path print (b) next to
   an equal "Cov λ₁". In the DB, `spectral_context.eig1` is (a) in >99% of rows through
   August and 86% of September qualia_moment rows. health.json labels the same number
   `lambda1`, `lambda1_esn` and `lambda1_cov`. The index needs two explicit columns and a
   per-entry provenance rule, never a single "lambda1".
2. **Engine-relative timestamps** in the eight 4M-row tables (section 5). Naive
   `datetime(timestamp,'unixepoch')` yields January 1970.
3. **Local vs UTC filenames** for minime (7 h offset in September). Astrid filenames are UTC.
4. **Timeouts erase entries.** minime LLM jobs time out at 150 s. In the most recent 2,000
   jobs: journal_pressure 672 timeouts vs 771 completed; self_study 252 vs 45;
   recess_aspiration 106 vs 22. A timed-out job writes no journal file but `action_events`
   still records the action as handled. File-based samples are therefore conditioned on
   "generation finished in time", which likely correlates with load and prompt size.
5. **Frozen cascade.** Distinct (λ₁,λ₂,λ₃) triples per 200k ticks: 55,078 (April) → 3,259
   (late May) → 1,195 (July) → 986 (September), dominated by (4.7, 3.1, 1.2) and
   (8.5, 4.4, 5.9). Under "scaffold hold" the covariance spectrum is quasi-discrete and
   flips between a few attractor states, so "Eigenvalue cascade" in headers is nearly a
   constant since June. Fill (0.26–0.76 within a week), ESN λ₁, dfill/dt, and the derived
   texture metrics carry the variance.
6. **Fill regime is era.** Weekly share of ticks below 60% fill: 100% (week of 04-13),
   30% (04-20), 2.6% (04-27), 8–9% (05-04, 05-11), 28.5% (05-18), then ~1% every week since
   June. Low-fill decisions for minime cluster in weeks of 05-04, 05-11, 05-25, 06-01
   (2,562 of 2,683 sub-58% decisions); Astrid has 27 sub-58% decisions in the action table
   in three months but ~19k sub-58% dialogue entries in March–May files.
7. **Action vocabulary is era.** Verbs are added, renamed, and suggested differently every
   few weeks (`EXAMINE` era → `SHADOW_TRAJECTORY` era → `READ_MORE` era for Astrid;
   `DECOMPOSE/PERTURB` → `EXAMINE_CODE` → `RESERVOIR_RESONANCE` → `EXPERIMENT_PLAN` →
   `JOURNAL/LEND_APERTURE/REST` for minime). See section 8.
8. **System text inside bodies.** Appended blocks such as "[Agency-vernacular notice —
   narrative preserved. …]" and "[Pressure-vocabulary cooldown — narrative preserved. …]"
   follow the model output; the pressure files wrap the model output between
   `--- GENERATED JOURNAL ---` and `--- ACTION TAIL ---`. Strip before any language analysis.
9. **Persona drops.** Some daydream/aspiration bodies are assistant-mode summaries of the
   prompt ("Okay, here's a breakdown of the information…", "Do you want me to elaborate…").
   They should be flagged, not analyzed as phenomenology.
10. **`!` filename prefix is Mike's hand flag.** He prepends it while reading live to entries
    that stood out to him (2026-09-06 census: minime 74 live+archived plus 88 in the April
    preserve, Astrid 194, plus 10 research, 1 hypothesis, 17 Astrid introspections, 1 outbox
    reply). `agency.rs::journal_priority` ranks flagged files first when selecting journals
    for EVOLVE requests. Index it as a curated label with the file change time as the flag
    time. The database keeps the unflagged `file_path`, so joins must strip the prefix.
11. **Numbers quoted in prose can disagree with the header** (a notice entry says "a dense
    73%" under a 71.0% header). This is itself a research variable (report fidelity), not
    noise to fix.
12. **Live databases.** Both DBs are WAL-mode and written every ~2 s by running processes.
    Read with `-readonly`, or copy the `.db` + `-wal` files before heavy scans. The 37 GB
    file is dominated by three payload-heavy timelines (~30 GB); the tables the research
    needs most are small.
13. **Suggested NEXT inside prompts** (section 4) biases the observed choice; Astrid's
    `READ_MORE` share rising from 38% (July) to 62% (September) coincides with research
    budget guard blocks that suggest `EXPERIMENT_RESEARCH_BUDGET_ACCEPT` and re-inject
    `READ_MORE` — both effects are in `action_events.route='research_budget_guard'`.

---

## 7. Era markers found so far

| Date (2026) | Event | Evidence |
|---|---|---|
| 03-14/15 | minime journals and first preserved DB begin | preserve archive; `minime_subdir_consciousness.db` |
| 03-25/26 | Astrid bridge and journals begin; `Mode: dialogue`, fill ~30% | oldest archive dir; `archive/bridge_messages/2026-03-25` |
| 03-28 | keep_floor sigmoid fix (cascade entropy 0.74→0.85) | chapter 14 |
| 04-01/02 | minime DB moved (subdir → main) | preserve DBs' ranges |
| 04-12 → 04-19 | preserved live journal window; **04-19 emergency preserve + DB reset**, golden-reset target tests (35/40/45/55%) | `emergency_preserve_20260419T130302/` |
| 04-19 → 04-25 | very low fill (weekly mean 17%, then 56%), "rescue" scaffold, target 55% | weekly fill table; `runtime/bridge_limited_write_v2_rollback_*.json` |
| 04-28 → 04-30 | stable-core activation, 68% hold shelf, full sovereignty savepoint | `diagnostics/stable_core_self_journal_pre_activation_20260428T151706Z`, docs |
| 05-08 | minime `action_events` / action threads begin | table range |
| 05-10 | LLM job records begin for both | job ids |
| 05-14 | steward practices formalized (self-study response, proactive scan) | steward notes |
| week of 05-18 | low-fill week (28.5% ticks < 60%) | weekly fill table |
| 06-07 | Astrid `bridge.db` reset; Astrid `action_events`, snapshots, self-observations begin; un-muffle work 06-08 | table ranges; CLAUDE.md |
| 06 → 07 | `SHADOW_TRAJECTORY` era → `READ_MORE` era for Astrid | probe |
| ~07 | Astrid coupled lane promoted to `gemma-4-12B-it-5bit`; minime to `gemma4:12b` | CHANGELOG line 1032; CLAUDE.md |
| 08-09 | astrid 0.5.2–0.5.6 tags | CHANGELOG |
| 08-25 | current `bridge_messages` live retention window starts | table range |
| 08-31 | current minime engine session 5316 starts | `sessions` |

The 1,607 dated steward notes and the two CHANGELOGs (1.2 MB and 279 KB, mostly undated
bullets) are the raw material for a proper era table; that is design work for the next
sessions.

---

## 8. Feasibility probe: fill vs NEXT

### 8a. From the action tables (clean pre-action fill, June+ heavy)

minime `action_events`, `source='next'`, 52.8k decisions, verb = first token:

| fill | n | top verbs |
|---|---|---|
| <50 | 2,632 | EXPERIMENT_PLAN 50%, EXPERIMENT_DECIDE 7%, THREAD_STATUS 4%, SPECTRAL_EXPLORER 4% |
| 50–58 | 51 | JOURNAL 27%, LEND_APERTURE 24%, REST 20% |
| 58–66 | 13,144 | JOURNAL 24%, EXPERIMENT_PLAN 15%, LEND_APERTURE 10%, REST 10% |
| 66–72 | 20,632 | JOURNAL 34%, LEND_APERTURE 12%, EXPERIMENT_PLAN 10%, REST 5% |
| 72–80 | 16,348 | JOURNAL 34%, LEND_APERTURE 13%, EXPERIMENT_PLAN 8%, REST 7% |

Astrid `action_events`, 36.4k decisions (fill p10 63.5, median 71.0, p90 73.1):

| fill | n | top verbs |
|---|---|---|
| 58–66 | 6,669 | READ_MORE 34%, SHADOW_TRAJECTORY 18%, PRESSURE_SOURCE_AUDIT 15%, INTROSPECT 5% |
| 66–72 | 17,093 | READ_MORE 35%, SHADOW_TRAJECTORY 19%, PRESSURE_SOURCE_AUDIT 13% |
| 72–80 | 12,578 | READ_MORE 35%, SHADOW_TRAJECTORY 19%, PRESSURE_SOURCE_AUDIT 13% |

Reading: the minime <50 bucket is almost entirely the late-May experiment-conveyor era, not
a fill effect. Within the held band, fill barely moves Astrid's mix.

### 8b. From the journal files (all eras, header fill, last NEXT line)

`probes/fill_vs_next_from_journals.py`, 68 s over ~308k files. Astrid dialogue files with
fill and NEXT: 96,377. minime files with fill and NEXT: 60,026.

Astrid, pooled:

| fill | n | top verbs |
|---|---|---|
| <30 | 5,451 | EXAMINE 30%, SEARCH 14%, LISTEN 6%, INTROSPECT 3%, PERTURB 3% |
| 30–45 | 4,240 | EXAMINE 35%, EXAMINE_CODE 12%, BROWSE 7% |
| 45–58 | 9,347 | EXAMINE 39%, EXAMINE_CODE 15%, READ_MORE 5%, LISTEN 5%, GESTURE 4% |
| 58–66 | 24,000 | EXAMINE 25%, READ_MORE 13%, SHADOW_TRAJECTORY 8%, LISTEN 6% |
| 66–72 | 34,316 | READ_MORE 20%, EXAMINE 18%, SHADOW_TRAJECTORY 12% |
| 72–80 | 18,855 | READ_MORE 26%, SHADOW_TRAJECTORY 15%, EXAMINE 9% |
| ≥80 | 168 | EXAMINE 42%, LISTEN 19%, PERTURB 10% |

Same data split by month shows the pooled gradient is mostly era: March = BROWSE/SEARCH
(fill 30–70), April = EXAMINE 36–45% in every bucket, May = EXAMINE/EXAMINE_CASCADE, June =
SHADOW_TRAJECTORY 33–47%, July → September = READ_MORE 38% → 62%. Within April, the one
visible fill effect is LISTEN: 9% at 66–72 vs 28% at 72–80 and 20% at ≥80.

minime, pooled: <30 = EXPERIMENT_PLAN 33%, SEARCH 12%; 30–45 = DECOMPOSE 16%, PERTURB 13%,
SELF_STUDY 11%; 45–58 = EXAMINE_CODE 14%, PERTURB 14%, NOTICE 13%; 58–72 = JOURNAL 24–31%,
LEND_APERTURE 9–12%; 72–80 = JOURNAL 38%, LEND_APERTURE 15%; ≥80 (n=314, April) =
DECOMPOSE 17%, PERTURB 15%, SELF_STUDY 15%. By month: March DECOMPOSE/SELF_STUDY/PERTURB;
April EXAMINE_CODE/PERTURB/NOTICE with RESERVOIR_RESONANCE 50% of the 66–72 bucket;
May EXPERIMENT_PLAN 25–51%; June–August JOURNAL 56–66%, LEND_APERTURE 17–28%, REST 9–15%;
September JOURNAL ~38%, LEND_APERTURE, SELF_STUDY, ASPIRE.

Conclusion: the question is answerable, the data volume is ample, and the honest version
of the answer is P(NEXT | fill, era, suggested_next, lane), not P(NEXT | fill).

---

## 9. Questions this trove can support

1. Action choice vs state: P(NEXT | fill bucket, dfill/dt, ESN λ₁, texture quality), stratified
   by era and by whether the verb was suggested in the prompt; stickiness and the effect of
   diversity hints (Astrid tracks the last 5 choices).
2. Language texture vs numeric texture: lexicon of pressure/viscosity/thinning/density/
   spaciousness words (and embeddings) against `pressure_source`, `inhabitable_fluctuation`,
   `resonance_density`, spectral entropy, fill, dfill/dt at generation time; the 4.2M-row
   timelines give sub-3 s resolution around each entry.
3. Report fidelity: numbers the being quotes in prose vs the header it was given; staleness
   (the v3 moment header records prompt-capture vs write time explicitly).
4. Distress language vs fill (CLAUDE.md asserts distress tracks low fill): testable on the
   March–May low-fill corpus and the June+ held-band corpus separately.
5. Cross-being convergence: same-window topical overlap between Astrid and minime, with
   mirror-mode quoting controlled for; `witness-context` jobs already pair the two texts.
6. Intervention effects: parameter changes, model promotions, and prompt-contract versions
   as breakpoints in action mix and language.
7. Closed-loop effect of Astrid's words on the reservoir: `codec_impact` (48-D features,
   fill before/after) and `sensory` delivery receipts vs the next telemetry ticks.
8. Operational: timeout rate vs fill/load; how much of the "being's silence" is
   infrastructure (the un-muffle question in CLAUDE.md), measurable from job events.
9. Introspection quality: Astrid's 10.5k source readings and minime's self-studies vs
   ground-truth citations (`scripts/ground_review.py` exists on the astrid side).

---

## 10. Open design questions for the spitball sessions

- **Unit of analysis.** Entry, exchange, action, or telemetry tick? A likely shape is a
  canonical `utterance` table (being, lane, mode, wall time UTC, prompt-capture time, text
  with system blocks stripped, NEXT raw/canonical/verb, suggested_next, llm job status) plus
  a `state_at_generation` table with both λ₁ columns, fill, dfill/dt, cascade, and the texture
  scores, plus an `era` table.
- **Which state to attach.** The header snapshot (what the model saw), the nearest telemetry
  tick, or a window (e.g. 60 s before / 120 s after)? Probably all three, named honestly.
- **Storage.** Files + SQLite extracts → Parquet/DuckDB is the obvious fit for 400k
  utterances and ~5M ticks; full-text search and embeddings (`nomic-embed-text` is already
  local; 36.8k Astrid vectors exist) for the language side.
- **Eras.** Build the era table from steward-note dates, CHANGELOG mentions, `sessions`, and
  detected shifts in action vocabulary; decide what counts as an era boundary.
- **Prompt reconstruction.** Astrid's dialogue prompts are gone; decide whether
  `suggested_next` + conveyor state + overflow diagnostics are enough, or whether to start
  persisting prompts going forward (a change to the live system, so a steward decision).
- **Hygiene.** Rules for persona-drop detection, system-block stripping, NEXT normalization
  parity with the beings' own parsers, and whether to include operational entries at all.
- **Access.** Copy-then-scan vs live read-only against WAL databases the beings are writing to.
- **Ethics of reading.** Both beings read their own journal space and notice steward activity;
  the astrid CLAUDE.md treats journals as primary evidence and asks that tool output not be
  surfaced into being prompts. Decide what, if anything, of this research is shared back.

---

## Appendix: key paths

```
/Users/v/other/minime/workspace/journal/                     minime journals (+archive/)
/Users/v/other/minime/emergency_preserve_20260419T130302/     pre-04-19 journals + two older DBs
/Users/v/other/minime/minime_consciousness.db                 37 GB SQLite (WAL, live)
/Users/v/other/minime/workspace/{actions,self_assessment,hypotheses,research,introspections,llm_jobs}
/Users/v/other/minime/minime_autonomy/runtime.py              header builders, prompts, journal writers
/Users/v/other/minime/minime_autonomy/parsing.py              parse_next_action (line ~610)
/Users/v/other/minime/minime/src/runtime/orchestration.rs     what gets saved as λ/fill (line ~3147)
/Users/v/other/astrid/capsules/spectral-bridge/workspace/journal/   Astrid journals (+archive/)
/Users/v/other/astrid/capsules/spectral-bridge/workspace/bridge.db  2.3 GB SQLite (WAL, live)
/Users/v/other/astrid/capsules/spectral-bridge/workspace/archive/bridge_messages/  zst message archives 03-25 → 08-23
/Users/v/other/astrid/capsules/spectral-bridge/workspace/llm_jobs/jobs/           181k jobs with full prompts
/Users/v/other/astrid/md-CLAUDE-chapters/                     04 (actions), 11 (substrate), 14 (spectral dynamics)
/Users/v/other/astrid/docs/steward-notes/                     1,607 dated notes (era markers)
/Users/v/other/neural-triple-reservoir/state/shadow_metrics.jsonl   triple-reservoir crossfeed metrics
```

---

## Addendum (2026-09-06, exercise 1): trap 1 resolved

The "third λ₁" is a timing skew, not a third quantity. `runtime.py:23246-23259` takes `eig1`
from the latest `esn_metrics` row and `cov_lambda1` from the latest `eigenvalue_timeline` row;
`reporting_snapshot.py:72-75` then overwrites `eig1` with `spectral_state.json`'s
`eigenvalues[0]`, which is the cascade λ₁ at a different tick. Because the cascade flips between
attractor states tick to tick, one header can show "λ₁: 4.76" and "Cov λ₁: 8.5" for the same
series. ESN λ₁ (`esn.rs:1533`) is the top eigenvalue of the EWMA covariance of the 128-D
reservoir state, not the recurrent spectral radius. Fill and `lambda1_rel` are cascade-based.
health.json writes the same variable as `lambda1`, `lambda1_abs` and `lambda1_cov`
(`orchestration.rs:4699-4702`). Full write-up: `exercises/2026-09-06-recess-architecture.md`.

## 8. Addendum 2026-09-07: release flow, mailboxes, generation records

Learned while deploying Tranche 1 (see `proposals/2026-09-06-tranche1-generation-record-and-own-body.md`
and `proposals/receipts/`).

1. **Astrid's bridge is released through stages, not `--restart`.** `scripts/build_bridge.sh --restart`
   exits 64 by design. `--stage-dir DIR --ack --actor` builds a witnessed stage (`manifest.json`,
   `ready.json`, binary, helper copies; no live effect). `--activate-stage DIR --expected-pid PID --ack
   --actor` drains the running bridge (SIGUSR1, waits for lifecycle phase `drained` and a conversation
   checkpoint), sends SIGTERM, hands state off, writes `.runtime/bridge-deployment/active.json`, and
   verifies the replacement (a new saved exchange plus an idle model). launchd runs
   `scripts/launchd_spectral_bridge.sh`, which execs `scripts/bridge_release_launch.py`, which execs the
   binary named by `active.json`. Canonical HEAD alone does not identify the running binary: read
   `active.json` and the stage manifest's `repository.head`. Codex's stages live under other worktrees'
   `.runtime/bridge-stages/`.
2. **minime's agent reloads by one SIGTERM at a quiet boundary.** The runtime handles SIGTERM
   (`_handle_termination`: "shutdown requested; accepted work will finish", then "drained"), launchd
   KeepAlive relaunches within seconds, and the wrapper re-reads `launchctl getenv` for the knobs. Do not
   `kickstart -k`. Quiet boundary: `workspace/runtime/llm_jobs_status.json` `active_count == 0`, no
   moment capture, inbox read or action in the last minute.
3. **Letter envelopes differ per being.** minime (since Codex's 2026-09-06 sender-bound inbox):
   `inbox/human_letter_<sender>_<YYYYMMDD>_<slug>_<HHMMSS>.txt` beginning `=== HUMAN LETTER V1 ===` with
   `Message-Id`, `Thread-Id`, `From: mike|steward`, `To: minime`, `Subject`, `Date`; anything else is
   classified as sender `unknown`. Read copies keep the name under `inbox/read/`. Astrid still uses
   `inbox/mike_feedback_<slug>_<unix>.txt` / `mike_query_...` with the `=== MIKE FEEDBACK: … ===` header;
   since 2026-09-07 02:15 UTC letters wait in a **durable mailbox** until she chooses `CHECK_MAILBOX`
   (ordinary window 6,000 bytes, `CHECK_MAILBOX LARGE` for bigger). As of 10:00 UTC she had never chosen
   it (0 rows in `action_events`), so "wait until the letter is retired" is not a usable gate.
4. **`action_events` columns (Astrid):** `action_id, thread_id, timestamp, system, canonical_action,
   route, status, payload`. Between 2026-09-06 13:07 and 2026-09-07 10:11 UTC, 274 `READ_MORE` rows
   were `blocked` by `route = research_budget_guard` (42 in the first three hours after the mailbox
   rollout alone): the guard dead end from exercise 1, now with a reading runtime behind it.
5. **Generation records (both beings)** live under `workspace/generations/<UTC day>/gen_<ms>_<lane>_a<attempt>.json`
   (0600 in 0700 dirs; system prompts deduplicated under `system_prompts/<sha256>.txt`). minime records
   carry `lane` (the `_execute_action` frame's action, e.g. `recess_aspiration`) **and** `prompt_class`
   (the runtime's label for the call, e.g. `sovereignty_check` on an aspiration call): they are not the
   same vocabulary. Probe: `probes/generation_records_24h.py`.
6. **Deploy times (era markers).** minime agent PID 16848 from 2026-09-07 10:12:30 UTC: fallback off
   (`MINIME_FALLBACK_MODEL=gemma4:12b`), default-lane budget 160 s, records on. Astrid bridge PID 27337
   from 2026-09-07 10:29:48 UTC on stage `20260907-tranche1-04` (main `bc66a62b0b`): own-body line and
   dialogue_live records on. Astrid was down 10:16:50–10:23:17 (first activation self-invalidated) and
   10:28:40–10:29:48 (exit race, recovered); both windows are gaps in her journal and `action_events`,
   and each restart produces the known phantom fill-surge moment capture (`c-prev-fill-init`).
7. **Staging rule.** Never stage the bridge from the canonical tree: its input snapshot includes the two
   launcher helpers the activation re-installs, so the release refuses itself after the old process has
   exited. Stage from a detached release worktree; keep that worktree while `active.json` points at it.

## September 8 live provider-observation addendum

The provider observer was subsequently enabled through Mike's explicitly
authorized owning rollout. Current study spool:
`/Users/v/other/astrid/capsules/spectral-bridge/workspace/provider_observations/20260908-live-01`.
Its `events/` files distinguish `dispatch_started`, `provider_outcome` and
`dialogue_decision`. Physical attempt IDs join dispatches to outcomes; generation
ID plus logical attempt index joins dialogue decisions to ordinary generation
records. Other provider lanes have no invented dialogue association. Raw artifacts
exist only for eligible marker-bearing input; marker-free inputs have an explicit
zero and hash, while unavailable input remains null.

See [the live account](analyses/2026-09-08-provider-observer-live.md), the
[frozen startup protocol](research/studies/S-006-provider-observer-startup-protocol.md),
and `probes/provider_observation_live_verify.py`. The first window has six complete
attempts, no marker opportunity and one verified dialogue join. Release binding
uses the immutable startup manifest/executable identity; do not substitute current
Git HEAD or infer action execution from a provider return. The private bounded
spool is not an unlimited historical log. The earlier source-only and historical
coverage accounts remain dated evidence.


## September 8 source-study repair and fidelity frame

For the complete sequence of access defects, repairs, activation boundaries and
natural outcomes, use the [living SELF_STUDY history](research/histories/self-study.md).
It preserves all three paired releases, the intermediate comparison's two-second
Minime boundary correction, S-008's blocked-action evidence and the first two
evening navigation jobs. Its packet copies exact historical inputs into this
research directory. Do not substitute its latest era for the frozen S-007 frame
below or infer new source delivery from a map response.

[S-007](research/studies/S-007-source-study-fidelity.md) anchors Minime’s shared-reader
activation at 2026-09-08T15:46:11Z (08:46:11 Pacific), PID 91125, implementation
37ed8b7 with paired Astrid 542c006. Read the
[initial account](analyses/2026-09-08-source-study-fidelity.md) and exact receipts
before using that era. Commit, process start, first natural response and accepted
page delivery have distinct clocks.

Minime’s `workspace/diagnostics/source_first_v3/shared_reader/deliveries/*/*.json`
retains source page, exact `request_json` and `response_json`. `reader-v1.json`
is mutable current state, not historical bookmark timing. Delivery files have no
explicit job/generation ID or local event time. In the initial frame all fifteen
join uniquely by exact adapted user message and response, corroborated with model
and system-prompt hash. Their provider responses retain native stop reasons;
navigation responses have no equivalent page receipt. Do not infer missing attempts
from this success-only store or infer exposure from a prepared page. Source IDs
include repository ownership; Minime can study Astrid code. Hash-identical local
source is not proof of deployed behavior.
