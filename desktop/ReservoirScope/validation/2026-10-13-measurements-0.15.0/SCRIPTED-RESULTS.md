# Scripted v4 context, save chain and recovered export

The separate native **scripted** session completed 121 numerical steps and four saved journals in 19 immutable segments. The pinned production verifier passed, and independent static joins confirmed the current/prior measurement references, exact saved-text memory and one next-step application per journal. This is a mechanical qualification of the v4 context and reader, not a model-writing or accuracy result. The planned real-model rehearsal remained [unexecuted after host admission failed](REAL-MODEL-RESULTS.md).

The actual configuration was seed `20261013`, `reservoir-journal-v4`, cadence 30, a 1,000 ms pace, 121 steps, four attempts, 900 seconds and 64 MiB. The [accepted configuration](scripted-bound-before-start.json) and [native start](native-scripted-start-01.json) bind the separate exercise. Its retained entries have `requestStarted=false` and no configured model.

## Original export and independent checks

The [native folder export](native-scripted-export-01.json) produced `sustained-1791931028053-1-1-143`, generation 1 / revision 143. The [pinned CLI receipt](scripted-cli-01.json) reports 121 steps, four journals, 19 segments and 1,747,206 bytes, with no diagnostics. The executable SHA-256 remained `18949732cf48c926003ffcf7b5b216bccc32ea071d0bff8a411e841eaba123d5` before and after offline replay. The original manifest SHA-256 is `281de345c12a3f0d07b96e68d9da96e0485483282c57a563907ba4e6257ddaa1`.

The independent [static companion checker](check_scripted_measurement_chain.py) and [original result](scripted-measurement-chain-01.json) inspect the exported bytes. They bind segment predecessors, contiguous event identities, the final checkpoint, actual reached observations and journal/save/application identities. They do not implement a second eigensolver or replace the production replay.

| Journal observation | Retained prior measurement | Exact memory from prior applied entry | Application step |
|---:|---:|---:|---:|
| 30 | Unavailable | None | 31 |
| 60 | 30 | 30, applied at 31 | 61 |
| 90 | 60 | 60, applied at 61 | 91 |
| 120 | 90 | 90, applied at 91 | 121 |

All eight rows in every retained prompt agree with independently projected values: recurrent RMS and L2 norm, largest sensory covariance eigenvalue, reduced sensory fill, top-eight head/shoulder/tail shares and entropy. Prior scalars match the preceding reached observation exactly. Differences are current minus prior; percentage rows use percentage points. First-observation prior values remain unavailable. Fixed eight-decimal prompt rendering is checked with a display-rounding allowance, not a changed numerical verification tolerance. The three memory-bearing prompts decode to the full exact preceding applied journal text; no prose is used as measurement history.

For a concrete endpoint check, the scripted step-120 sensory fill is `17.21206692391617%`, prior step-90 fill is `14.387920516180028%`, and the difference is `+2.8241464077361407` percentage points. This is an endpoint difference, not evidence of a trend or cause.

The first step-30 observation matches the retained 0.14 v3 first observation in every field and every binary64 value after excluding only the schema fields `version` and `previousMeasurements`. That boundary precedes feedback. Later scripted and model trajectories are different; this check makes no later trajectory-equivalence claim. The baseline source and hash are retained in the result.

The companion check initially compared a checkpoint file-byte hash with a typed state hash. The [failed checker attempt](scripted-measurement-chain-attempt-01.json) and [initial helper](check_scripted_measurement_chain-initial.py) are preserved. The corrected check binds each hash to its actual object; no application, original export or verifier change was made. Original bundle inventories were unchanged after inspection.

## Native recovery and unchanged evidence

The [native UI account](MACOS-UI.md) and [recovery receipt](native-scripted-recovery-01.json) record clean quit, idle relaunch, explicit paused Restore, disabled Resume at the exhausted budget, the retained table and a second native export. The root operator's pinned replay passed that recovered export.

The companion checker also [passed on the recovered export](scripted-measurement-chain-recovered-01.json). The [independent comparison](scripted-recovery-comparison-01.json) confirms both exports contain 25 files: all 24 non-manifest files are byte-identical. Only manifest generation `1→2`, revision `143→144` and phase `budgetReached→paused` changed. The checkpoint, 19 segments, four journals, exact prompts, memory, measurement references and application history remained unchanged.

This evidence qualifies this owned macOS scripted run and explicit paused recovery. It does not establish real-model use of the table, improved factual writing, causal interpretation, long-run stability, physical power-loss durability, or Windows/Linux behavior. No model, provider, live Being system or app UI was accessed by these independent offline checks.
