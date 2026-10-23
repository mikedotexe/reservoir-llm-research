# Arm configurations

Every arm the laptop apparatus ran on October 21–22, 2026 (S-010 and S-011), as the exact
configuration file the headless runner consumed, so that any of them can be rerun with the
same app source and the same local model. The files are settings only (seed, cadence,
budgets, numerical controls, prompt version, codec, memory policy, difference channel, the
local model and endpoint); the sessions they produced, the prompts, the entries and the
blind samples are private captures in the session scratchpad and never enter the repo.
Numbers from these arms live in the dated accounts named in the index below, with n.

## Running an arm

The runner is an ignored test in the desktop crate, `run_arm_from_env` in
`desktop/ReservoirScope/src-tauri/src/sustained_arms.rs`. From
`desktop/ReservoirScope/src-tauri`, with the app source at the release the index names
(the runner binary each chain used was the desktop test binary built from that release):

```
ARM_STORE=<new empty dir> ARM_CONFIG=research/arms/configs/<arm>.json \
ARM_ENTRIES=<journals to collect> ARM_MINUTES=<wall-clock cap> \
cargo test --locked -p reservoir-scope-desktop run_arm_from_env -- --ignored --nocapture
```

It creates one session under `ARM_STORE` (`sustained-<ms>-<n>/` with `manifest.json`,
`segments/`, `checkpoints/`, `journals/`), runs it until the entry count, a terminal phase
or the time cap, and prints one JSON line (`sessionId`, `phase`, `journals`, `step`,
`seconds`, `skipped`). Model arms need a loopback Ollama with the named model pulled
(`gemma4:12b`, `mistral-small:24b` or `dolphin-mixtral:8x7b-v2.7`) and, for the embedding
codec, `nomic-embed-text`; scripted arms need no model. Run arms one at a time: two
sessions on one Ollama interleave requests and lose bit reproduction. The provider itself
forks on about 2% of identical-prompt turns (`research/METHODS.md`), so a rerun of a model
arm can part from the recorded one at any entry; scripted arms reproduce exactly. The
configuration fields are documented in `desktop/ReservoirScope/SUSTAINED-SESSIONS.md`; an
omitted `promptVersion` means the legacy v1 prompt, so every file here names its version.

Reading a store: `probes/introspection_markers.py`, `probes/desktop_session_overlap.py`,
`probes/desktop_embedding_reduction.py`, `probes/desktop_memory_choice.py`,
`probes/concept_chains.py`, `probes/desktop_entry_effect.py`,
`probes/desktop_difference_channel.py`, `probes/desktop_arm_identity.py` (where two stores
part), and `probes/desktop_blind_sample.py` (a shuffled, unlabelled sample for reading
before the key). Each prints its inputs and n.

## Index

Runner: the desktop release whose test binary ran the arm. Policy: the memory policy, with
the recent-return window in turns when set. Gain: the difference-channel gain. Retention:
the initial retention and whether regulation was on. Read in: the account that reports the
arm's numbers.


### Difference ladder (desktop 0.35.0, scripted backend)

Read in: `analyses/2026-10-21-difference-ladder.md`. 72 configurations.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `ladder-fixed-s1-gm0.01` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.01 | 0.95 fixed | 20260909 | 30 / 600 |
| `ladder-fixed-s1-gm0.02` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.02 | 0.95 fixed | 20260909 | 30 / 600 |
| `ladder-fixed-s1-gm0.05` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.05 | 0.95 fixed | 20260909 | 30 / 600 |
| `ladder-fixed-s1-gm0.10` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.1 | 0.95 fixed | 20260909 | 30 / 600 |
| `ladder-fixed-s1-gm0.20` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.2 | 0.95 fixed | 20260909 | 30 / 600 |
| `ladder-fixed-s1-gp0.00` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0 | 0.95 fixed | 20260909 | 30 / 600 |
| `ladder-fixed-s1-gp0.01` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.01 | 0.95 fixed | 20260909 | 30 / 600 |
| `ladder-fixed-s1-gp0.02` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.02 | 0.95 fixed | 20260909 | 30 / 600 |
| `ladder-fixed-s1-gp0.05` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.05 | 0.95 fixed | 20260909 | 30 / 600 |
| `ladder-fixed-s1-gp0.10` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.1 | 0.95 fixed | 20260909 | 30 / 600 |
| `ladder-fixed-s1-gp0.20` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.2 | 0.95 fixed | 20260909 | 30 / 600 |
| `ladder-fixed-s7-gm0.01` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.01 | 0.95 fixed | 7 | 30 / 600 |
| `ladder-fixed-s7-gm0.02` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.02 | 0.95 fixed | 7 | 30 / 600 |
| `ladder-fixed-s7-gm0.05` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.05 | 0.95 fixed | 7 | 30 / 600 |
| `ladder-fixed-s7-gm0.10` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.1 | 0.95 fixed | 7 | 30 / 600 |
| `ladder-fixed-s7-gm0.20` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.2 | 0.95 fixed | 7 | 30 / 600 |
| `ladder-fixed-s7-gp0.00` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0 | 0.95 fixed | 7 | 30 / 600 |
| `ladder-fixed-s7-gp0.01` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.01 | 0.95 fixed | 7 | 30 / 600 |
| `ladder-fixed-s7-gp0.02` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.02 | 0.95 fixed | 7 | 30 / 600 |
| `ladder-fixed-s7-gp0.05` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.05 | 0.95 fixed | 7 | 30 / 600 |
| `ladder-fixed-s7-gp0.10` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.1 | 0.95 fixed | 7 | 30 / 600 |
| `ladder-fixed-s7-gp0.20` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.2 | 0.95 fixed | 7 | 30 / 600 |
| `ladder-reg-s1-d0.02-gm0.01` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.01 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-d0.02-gm0.02` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.02 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-d0.02-gm0.05` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.05 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-d0.02-gm0.10` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.1 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-d0.02-gm0.20` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.2 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-d0.02-gm0.50` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.5 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-d0.02-gm1.00` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -1.0 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-d0.02-gp0.01` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.01 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-d0.02-gp0.02` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.02 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-d0.02-gp0.05` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.05 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-d0.02-gp0.10` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.1 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-d0.02-gp0.20` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.2 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-d0.02-gp0.50` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.5 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-d0.02-gp1.00` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 1.0 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-gm0.01` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.01 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-gm0.02` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.02 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-gm0.05` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.05 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-gm0.10` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.1 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-gm0.20` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.2 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-gp0.00` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-gp0.01` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.01 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-gp0.02` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.02 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-gp0.05` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.05 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-gp0.10` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.1 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s1-gp0.20` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.2 | 0.955 regulated | 20260909 | 30 / 600 |
| `ladder-reg-s7-d0.02-gm0.01` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.01 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-d0.02-gm0.02` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.02 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-d0.02-gm0.05` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.05 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-d0.02-gm0.10` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.1 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-d0.02-gm0.20` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.2 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-d0.02-gm0.50` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.5 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-d0.02-gm1.00` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -1.0 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-d0.02-gp0.01` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.01 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-d0.02-gp0.02` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.02 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-d0.02-gp0.05` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.05 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-d0.02-gp0.10` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.1 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-d0.02-gp0.20` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.2 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-d0.02-gp0.50` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.5 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-d0.02-gp1.00` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 1.0 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-gm0.01` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.01 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-gm0.02` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.02 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-gm0.05` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.05 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-gm0.10` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.1 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-gm0.20` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | -0.2 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-gp0.00` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-gp0.01` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.01 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-gp0.02` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.02 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-gp0.05` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.05 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-gp0.10` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.1 | 0.955 regulated | 7 | 30 / 600 |
| `ladder-reg-s7-gp0.20` | 0.35.0 | scripted | `reservoir-journal-inert-effect-v1` | surface | latest | 0.2 | 0.955 regulated | 7 | 30 / 600 |

### Difference-channel calibration twins (0.33.0, scripted backend)

Read in: `analyses/2026-10-21-difference-ladder.md` (calibration) and S-011 progress. 7 configurations.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `calib-ret0.82` | 0.33.0 | scripted | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.82 fixed | 20260909 | 30 / 2000 |
| `calib-ret0.86` | 0.33.0 | scripted | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.86 fixed | 20260909 | 30 / 2000 |
| `calib-ret0.90` | 0.33.0 | scripted | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.9 fixed | 20260909 | 30 / 2000 |
| `calib-ret0.93` | 0.33.0 | scripted | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.93 fixed | 20260909 | 30 / 2000 |
| `calib-ret0.95` | 0.33.0 | scripted | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.95 fixed | 20260909 | 30 / 2000 |
| `calib-ret0.97` | 0.33.0 | scripted | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.97 fixed | 20260909 | 30 / 2000 |
| `calib-ret0.99` | 0.33.0 | scripted | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.99 fixed | 20260909 | 30 / 2000 |

### Fill sweep by retention (0.33.0)

Read in: S-011 progress (`research/studies/S-011-self-observation-stack.md`). 10 configurations.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `sweep-low-gemma4` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.955 fixed | 20260909 | 30 / 2000 |
| `sweep-low-gemma4-seed7` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.955 fixed | 7 | 30 / 2000 |
| `sweep-r82-gemma4` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.82 fixed | 20260909 | 30 / 2000 |
| `sweep-r82-gemma4-seed7` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.82 fixed | 7 | 30 / 2000 |
| `sweep-r90-gemma4` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.9 fixed | 20260909 | 30 / 2000 |
| `sweep-r90-gemma4-seed7` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.9 fixed | 7 | 30 / 2000 |
| `sweep-r95-gemma4` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.95 fixed | 20260909 | 30 / 2000 |
| `sweep-r95-gemma4-seed7` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.95 fixed | 7 | 30 / 2000 |
| `sweep-r99-gemma4` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.99 fixed | 20260909 | 30 / 2000 |
| `sweep-r99-gemma4-seed7` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.99 fixed | 7 | 30 / 2000 |

### No-tag controls (0.34.0; the lower-fill ones 0.36.0)

Read in: S-011 progress and `analyses/2026-10-21-concept-chains.md`. 8 configurations.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `notag-inert-gemma4` | 0.34.0 | gemma4:12b | `reservoir-journal-inert-no-tag-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `notag-inert-gemma4-seed7` | 0.34.0 | gemma4:12b | `reservoir-journal-inert-no-tag-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `notag-plain-gemma4` | 0.34.0, 0.36.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `notag-plain-gemma4-seed7` | 0.34.0, 0.36.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `notag-plain-r82-gemma4` | 0.36.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | surface | latest | 0 | 0.82 fixed | 20260909 | 30 / 2000 |
| `notag-plain-r82-gemma4-seed7` | 0.36.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | surface | latest | 0 | 0.82 fixed | 7 | 30 / 2000 |
| `notag-plain-r90-gemma4` | 0.36.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | surface | latest | 0 | 0.9 fixed | 20260909 | 30 / 2000 |
| `notag-plain-r90-gemma4-seed7` | 0.36.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | surface | latest | 0 | 0.9 fixed | 7 | 30 / 2000 |

### Scrambled-tag control (0.34.0)

Read in: S-011 progress and `analyses/2026-10-21-concept-chains.md`. 2 configurations.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `scrambled-plain-gemma4` | 0.34.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-scrambled-tag-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `scrambled-plain-gemma4-seed7` | 0.34.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-scrambled-tag-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |

### State-chosen memory (0.36.0, 0.37.0)

Read in: `analyses/2026-10-21-state-chosen-memory.md`. 14 configurations.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `policy-latest-gemma4` | 0.36.0, 0.37.0, 0.38.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `policy-latest-gemma4-rep` | 0.36.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `policy-latest-gemma4-seed7` | 0.36.0, 0.37.0, 0.38.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `policy-latest-scripted` | 0.36.0 | scripted | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 600 |
| `policy-random-gemma4` | 0.36.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | random | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `policy-random-gemma4-seed7` | 0.36.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | random | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `policy-random-older-gemma4` | 0.37.0, 0.38.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | random-older | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `policy-random-older-gemma4-seed7` | 0.37.0, 0.38.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | random-older | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `policy-random-scripted` | 0.36.0 | scripted | `reservoir-journal-inert-plain-contract-v1` | surface | random | 0 | 0.955 regulated | 20260909 | 30 / 600 |
| `policy-state-aligned-gemma4` | 0.36.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | state-aligned | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `policy-state-aligned-gemma4-seed7` | 0.36.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | state-aligned | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `policy-state-aligned-scripted` | 0.36.0 | scripted | `reservoir-journal-inert-plain-contract-v1` | surface | state-aligned | 0 | 0.955 regulated | 20260909 | 30 / 600 |
| `policy-state-residual-gemma4` | 0.37.0, 0.38.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | state-residual | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `policy-state-residual-gemma4-seed7` | 0.37.0, 0.38.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | state-residual | 0 | 0.955 regulated | 7 | 30 / 2000 |

### Recent-return window (0.38.0)

Read in: `analyses/2026-10-22-two-entry-slot.md`. 2 configurations.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `excl3-state-residual-gemma4` | 0.38.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | state-residual (window 3) | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `excl3-state-residual-gemma4-seed7` | 0.38.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | state-residual (window 3) | 0 | 0.955 regulated | 7 | 30 / 2000 |

### Two-entry slot (0.38.0)

Read in: `analyses/2026-10-22-two-entry-slot.md`. 4 configurations.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `both-random-older-gemma4` | 0.38.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-two-v1` | embedding | random-older | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `both-random-older-gemma4-seed7` | 0.38.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-two-v1` | embedding | random-older | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `both-state-residual-gemma4` | 0.38.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-two-v1` | embedding | state-residual | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `both-state-residual-gemma4-seed7` | 0.38.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-two-v1` | embedding | state-residual | 0 | 0.955 regulated | 7 | 30 / 2000 |

### Fill calibration under the embedding codec (0.39.0)

Read in: `analyses/2026-10-22-threshold-battery.md` (calibration section). 4 configurations;
no-tag `latest`, so the texts are the no-tag arms' by construction and only the fill series is
new (post-climb medians 61.4, 63.6, 74.8, 76.7).

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `calib-embed-r0.92` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | embedding | latest | 0 | 0.92 fixed | 20260909 | 30 / 2000 |
| `calib-embed-r0.93` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | embedding | latest | 0 | 0.93 fixed | 20260909 | 30 / 2000 |
| `calib-embed-r0.965` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | embedding | latest | 0 | 0.965 fixed | 20260909 | 30 / 2000 |
| `calib-embed-r0.97` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | embedding | latest | 0 | 0.97 fixed | 20260909 | 30 / 2000 |

### Threshold battery, leg A (0.39.0): no-tag single slot, regulation off, fill below and above the shelf

Read in: `analyses/2026-10-22-threshold-battery.md`. 6 model configurations, 2 scripted gate
configurations (`state-residual` on scripted texts at the two retentions, 40 entries, read for
whether the pick sequence moves with retention at all) and 1 primer (`prime-notag-gemma4`, one
entry, the same first prompt as every battery arm, run first so each real arm follows an arm
that sent it). Retention 0.93 gives a post-climb fill median of 63.6 and 0.97 one of 76.7
under this codec (S-011, 2026-10-22 15:00).

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `thr-lo-state-residual-gemma4` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | embedding | state-residual | 0 | 0.93 fixed | 20260909 | 30 / 2000 |
| `thr-lo-state-residual-gemma4-seed7` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | embedding | state-residual | 0 | 0.93 fixed | 7 | 30 / 2000 |
| `thr-hi-state-residual-gemma4` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | embedding | state-residual | 0 | 0.97 fixed | 20260909 | 30 / 2000 |
| `thr-hi-state-residual-gemma4-seed7` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | embedding | state-residual | 0 | 0.97 fixed | 7 | 30 / 2000 |
| `thr-lo-random-older-gemma4` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | embedding | random-older | 0 | 0.93 fixed | 20260909 | 30 / 2000 |
| `thr-lo-random-older-gemma4-seed7` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | embedding | random-older | 0 | 0.93 fixed | 7 | 30 / 2000 |
| `gate-lo-state-residual-scripted` | 0.39.0 | scripted | `reservoir-journal-inert-plain-contract-v1` | surface | state-residual | 0 | 0.93 fixed | 20260909 | 30 / 1300 |
| `gate-hi-state-residual-scripted` | 0.39.0 | scripted | `reservoir-journal-inert-plain-contract-v1` | surface | state-residual | 0 | 0.97 fixed | 20260909 | 30 / 1300 |
| `prime-notag-gemma4` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-no-tag-v1` | embedding | latest | 0 | 0.93 fixed | 20260909 | 30 / 2000 |

### Two-entry slot without a context line (0.39.0, leg B of the threshold battery)

Read in: `analyses/2026-10-22-threshold-battery.md` (leg B). 4 configurations.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `bothnotag-random-older-gemma4` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-two-no-tag-v1` | embedding | random-older | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `bothnotag-random-older-gemma4-seed7` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-two-no-tag-v1` | embedding | random-older | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `bothnotag-state-residual-gemma4` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-two-no-tag-v1` | embedding | state-residual | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `bothnotag-state-residual-gemma4-seed7` | 0.39.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-two-no-tag-v1` | embedding | state-residual | 0 | 0.955 regulated | 7 | 30 / 2000 |

### Entry-effect readout (0.33.0)

Read in: S-011 progress and `analyses/2026-10-21-frame-arms.md`. 2 configurations.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `inert-effect-gemma4` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-effect-v1` | embedding | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-effect-gemma4-seed7` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-effect-v1` | embedding | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |

### Entry-effect readout under the plain contract (0.33.0)

Read in: S-011 progress and `analyses/2026-10-21-frame-arms.md`. 3 configurations.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `plain-effect-gemma4` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-effect-v1` | embedding | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `plain-effect-gemma4-seed7` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-effect-v1` | embedding | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `plain-effect-mistral` | 0.33.0 | mistral-small:24b | `reservoir-journal-inert-plain-contract-effect-v1` | embedding | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |

### Embedding codec arms (0.30.0)

Read in: `analyses/2026-10-21-frame-arms.md` and `analyses/2026-10-21-embedding-reduction-offline.md`. 2 configurations.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `inert-embed-gemma4` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-v1` | embedding | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-embed-gemma4-seed7` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-v1` | embedding | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |

### Byte-identity witness capture (0.34.0)

Read in: `desktop/ReservoirScope/crates/reservoir-core/tests/fixtures/sustained-prompts/v34-gain-zero-segment.json`. 1 configuration.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `witness-v034` | 0.34.0 | scripted | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.955 regulated | 7 | 3 / 40 |

### Runner smoke check

Read in: none (a check that the headless runner works). 1 configuration.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `smoke-inert` | 0.30.0 | mistral-small:24b | `reservoir-journal-inert-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |

### Frame and contract arms (S-010, 0.30.0–0.32.0)

Read in: `analyses/2026-10-21-frame-arms.md`. 35 configurations.

| arm | runner | model | prompt version | codec | policy | gain | retention | seed | turn every / max steps |
|---|---|---|---|---|---|---|---|---|---|
| `control-v8` | 0.30.0, 0.32.0 | mistral-small:24b | `reservoir-journal-v8` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `control-v8-embed` | 0.30.0 | mistral-small:24b | `reservoir-journal-v8` | embedding | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `control-v8-gemma4` | 0.31.0, 0.32.0 | gemma4:12b | `reservoir-journal-v8` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `control-v8-gemma4-seed7` | 0.32.0 | gemma4:12b | `reservoir-journal-v8` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `control-v8-mixtral` | 0.31.0, 0.32.0 | dolphin-mixtral:8x7b-v2.7 | `reservoir-journal-v8` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `control-v8-seed7` | 0.31.0 | mistral-small:24b | `reservoir-journal-v8` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `inert` | 0.32.0 | mistral-small:24b | `reservoir-journal-inert-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-gemma4` | 0.31.0, 0.32.0 | gemma4:12b | `reservoir-journal-inert-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-gemma4-seed7` | 0.32.0 | gemma4:12b | `reservoir-journal-inert-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `inert-inviting-contract` | 0.31.0, 0.32.0 | mistral-small:24b | `reservoir-journal-inert-inviting-contract-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-inviting-contract-gemma4` | 0.31.0, 0.32.0 | gemma4:12b | `reservoir-journal-inert-inviting-contract-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-inviting-contract-gemma4-seed7` | 0.32.0 | gemma4:12b | `reservoir-journal-inert-inviting-contract-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `inert-inviting-contract-mixtral` | 0.31.0, 0.32.0 | dolphin-mixtral:8x7b-v2.7 | `reservoir-journal-inert-inviting-contract-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-inviting-contract-seed7` | 0.31.0 | mistral-small:24b | `reservoir-journal-inert-inviting-contract-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `inert-inviting-embed` | 0.30.0 | mistral-small:24b | `reservoir-journal-inert-inviting-contract-v1` | embedding | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-inviting-varied-contract` | 0.31.0, 0.32.0 | mistral-small:24b | `reservoir-journal-inert-inviting-varied-contract-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-inviting-varied-contract-gemma4` | 0.31.0, 0.32.0 | gemma4:12b | `reservoir-journal-inert-inviting-varied-contract-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-inviting-varied-contract-gemma4-seed7` | 0.32.0 | gemma4:12b | `reservoir-journal-inert-inviting-varied-contract-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `inert-inviting-varied-contract-seed7` | 0.31.0 | mistral-small:24b | `reservoir-journal-inert-inviting-varied-contract-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `inert-mixtral` | 0.31.0, 0.32.0 | dolphin-mixtral:8x7b-v2.7 | `reservoir-journal-inert-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-no-memory` | 0.30.0 (cargo) | mistral-small:24b | `reservoir-journal-inert-no-memory-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-no-memory-seed7` | 0.31.0 | mistral-small:24b | `reservoir-journal-inert-no-memory-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `inert-open-contract` | 0.31.0, 0.32.0 | mistral-small:24b | `reservoir-journal-inert-open-contract-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-open-contract-gemma4` | 0.31.0, 0.32.0 | gemma4:12b | `reservoir-journal-inert-open-contract-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-open-contract-gemma4-seed7` | 0.32.0 | gemma4:12b | `reservoir-journal-inert-open-contract-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `inert-open-contract-seed7` | 0.31.0 | mistral-small:24b | `reservoir-journal-inert-open-contract-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `inert-plain-contract` | 0.31.0, 0.32.0 | mistral-small:24b | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-plain-contract-gemma4` | 0.31.0, 0.32.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-plain-contract-gemma4-seed7` | 0.32.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `inert-plain-contract-mixtral` | 0.31.0, 0.32.0 | dolphin-mixtral:8x7b-v2.7 | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `inert-plain-contract-seed7` | 0.31.0 | mistral-small:24b | `reservoir-journal-inert-plain-contract-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `inert-seed7` | 0.31.0 | mistral-small:24b | `reservoir-journal-inert-v1` | surface | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `plain-embed-gemma4` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
| `plain-embed-gemma4-seed7` | 0.33.0 | gemma4:12b | `reservoir-journal-inert-plain-contract-v1` | embedding | latest | 0 | 0.955 regulated | 7 | 30 / 2000 |
| `plain-embed-mistral` | 0.33.0 | mistral-small:24b | `reservoir-journal-inert-plain-contract-v1` | embedding | latest | 0 | 0.955 regulated | 20260909 | 30 / 2000 |
