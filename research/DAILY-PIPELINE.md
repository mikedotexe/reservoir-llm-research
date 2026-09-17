# Maintained daily evidence pipeline

The `study daily` commands build and verify S-007 reports from explicit retained research inputs. They do not capture live files, contact a model, execute packet code, update the daily ledger, or alter a sealed packet. Building a report is separate from verifying it.

The maintained engine currently preserves **v6 report semantics**. The orchestration manifest has its own version, `s007-daily-inputs-v1`. Historical v1–v6 probes, packet code copies, reports, protocols and corrections remain unchanged.

## Declare inputs, then build and verify

Run from the research checkout with Python 3.12 or later. Do not use Python's `-O` option: new checks use explicit errors, but shared historical evidence helpers still contain assertions. The maintained entry point explicitly rejects optimized Python.

The following declares the existing day9 inputs and all earlier S-007 packet lineage. The output must not already exist:

```sh
python3 -B -m reservoir_research study daily manifest \
  research/outputs/2026-09-17-source-study-fidelity-day9 \
  --data-root . \
  --history research/outputs/2026-09-08-source-study-fidelity \
  --history research/outputs/2026-09-09-source-study-fidelity-day1 \
  --history research/outputs/2026-09-10-source-study-fidelity-day2 \
  --history research/outputs/2026-09-11-source-study-fidelity-day3 \
  --history research/outputs/2026-09-12-source-study-fidelity-day4 \
  --history research/outputs/2026-09-13-source-study-fidelity-day5 \
  --history research/outputs/2026-09-14-source-study-fidelity-day6 \
  --history research/outputs/2026-09-15-source-study-fidelity-day7 \
  --history research/outputs/2026-09-16-source-study-fidelity-day8 \
  --history research/outputs/2026-09-15-source-study-fidelity-week1 \
  --out research/outputs/day9-migration-inputs.json

python3 -B -m reservoir_research study daily build \
  research/outputs/day9-migration-inputs.json --data-root . \
  --out research/outputs/day9-maintained-report

python3 -B -m reservoir_research study daily verify \
  research/outputs/day9-migration-inputs.json --data-root . \
  --report research/outputs/day9-maintained-report/report.json \
  --out research/outputs/day9-maintained-verification
```

A declaration records file hashes and lengths; it is not a verification result. The loader verifies declared bytes, the protocol's completion window, its pre-window ledger hash, each historical manifest and every file named by that manifest. The verifier then checks report replay, release bindings, request/response and journal evidence, selected claim spans and negative controls. It preserves the first-three selection rule without adding a source or quality filter.

The final command writes `verification.json`, `verified-claim-checks.json` and `pipeline-verification.json` into a new directory. Omitting `--out` performs read-only verification and prints the result. No command overwrites an existing output.

Manifest input paths are relative to an explicit data root. By default this root is the manifest's directory; `--data-root` overrides it. Copy the same retained directory layout to another account or disk and supply its new root. Absolute paths inside captured records remain provenance strings and are never opened. Escaping paths, invalid hashes, conflicting revisions and unknown input names are rejected.

## Release definitions and future windows

The default registry is [era-definitions-v1.json](../reservoir_research/daily/era-definitions-v1.json). It contains thirteen ordered release definitions through the September 17 study-interface release:

- Seven paired-rollout releases, from continuity through study-choice.
- Extended writing, activation controls and the first study-navigation release.
- Journal coherence, September 15 catalog navigation and September 17 study-interface.

Definitions supply retained-record selectors, expected identities and a named validator. They cannot supply executable code or relax validation. The seven supported validator types bind the appropriate rollout, activation, reload, manifest, paired review and source-input evidence. Changing a single recorded PID or loaded-source hash remains invalid even when its outer record hash is recomputed.

For a later daily window, freeze the new protocol and ledger-before snapshot using the existing collection procedure. Supply the new window's capture/supplement, retained release packets, bindings and reviewed annotations in a new manifest. Add the newly completed historical packet to `--history`. No date, generation count or sample IDs are hardcoded into report generation.

If another release uses an existing receipt schema, add a reviewed registry entry and pass its registry file with `--eras`. A new receipt schema requires a typed validator and positive/negative qualification. Do not copy the entire report or verifier to add a release. Unknown validators, missing records, conflicting bindings and unverified process eras prevent a successful verification.

A stable host PID does not establish the selected helper or prompt revision. Separate day-specific context and descriptive analyses remain retained extensions; this migration does not merge those contexts into a causal score or change prior interpretations. The current v6 input names and binding roles remain required; this release does not claim to import arbitrary studies or historical report schemas into the maintained engine.

## Verification groups

```sh
python3 -B -m reservoir_research verify --group python --out research/outputs/python-checks
python3 -B -m reservoir_research verify --group research-replay \
  --daily-manifest research/outputs/day9-migration-inputs.json --data-root . \
  --daily-report research/outputs/day9-maintained-report/report.json \
  --out research/outputs/daily-replay-checks
```

Groups are `python`, `numerics`, `native-model`, `native-presentation`, `research-replay` and `package`. Repeat `--group` to combine them, or select `all-offline`. Package verification requires `--app`; research replay requires the explicit manifest and report. Missing platform tools or required inputs produce **incomplete** coverage and a nonzero exit code. Default invocation runs the Python group.

Receipts distinguish executed, explicitly inherited and incomplete coverage. `--inherit RECEIPT` accepts earlier passing coverage only when source/input and environment identities match; package and research evidence are always checked afresh. The runner preserves command logs, binds them by hash and detects source changes during a check. It never runs a model or discovers a live source. Human newcomer acceptance remains a separately recorded activity.

## Qualification and fallback

The [controlled qualification receipt](outputs/2026-09-17-maintained-daily-qualification/controlled-replay-final/qualification.json) demonstrates:

- Byte-identical day9 report, verification and exact claim-span outputs.
- All 355 declared historical files still matching their manifests.
- Rejection of independently rehashed host-PID and loaded-source contradictions.
- Successful build and verification of a separately labeled later, empty synthetic window, with an absent source control marked not applicable.

The repeatable qualification probe is [maintained_daily_qualification.py](../probes/maintained_daily_qualification.py). Its inputs and output directory are explicit. Qualification fixtures are research test artifacts, never new observational days.

If migration qualification fails, retain the failure and keep the current daily run on its already-qualified version. Replay a historical packet using its documented frozen procedure in an isolated restored copy. Do not repair a sealed historical packet in place, change its sample, or advance the ledger on a failed or incomplete result. Updating the daily collector or automation is a separate step; these commands do not silently switch it.
