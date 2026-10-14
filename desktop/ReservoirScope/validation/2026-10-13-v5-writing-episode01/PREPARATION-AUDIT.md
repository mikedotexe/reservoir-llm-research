# Preparation and Start witness audit

The retained preparation records are consistent: all 21 frozen inputs match, the qualified 0.17.0 package remains unchanged, and both saved early-session snapshots match the selected v5 configuration. This audit reads saved files only and makes no claim about the eventual twelve-opportunity outcome.

The [machine-readable audit](preparation-audit-01.json) records exact input identities, file comparisons and timing arithmetic. The [full prospective freeze](evaluation-freeze-01.json) was written at 2026-10-14 01:56:01.199519 UTC. Its 21 files still match by path, byte count and SHA-256. The separate [checker freeze](checker-freeze-01.json) preserves the exact 3,122 bytes originally written under the subsequently reserved overall-freeze filename; its SHA-256 remains `b2986fd76101a15f67527f7adde71a51460b7d0140ce5b8c4d9fbcf0a67d4e19`. This was a filename correction before the overall freeze, with no altered checker-freeze content. The 31 integrity-checker and 47 episode-local quality-helper tests passed before the overall freeze; their source and log hashes still match. No tests were rerun by this audit.

## Admission and Start

The single retained [admission receipt](host-admission-01.json), at 01:56:04.787449 UTC, binds the full freeze SHA-256 and records normal pressure level 1, 52% reported free memory and 11,902,164,992 free disk bytes. Those observations pass the frozen 35% memory and 8 GiB disk minimums. This audit did not take another admission sample or inspect present resource conditions.

The [pre-click bound](bound-before-start-01.json) records the owned service spawn at 01:56:13.007748 UTC, a 1,200-second lifetime, and 1,160.841630 seconds remaining at its separately recorded check. The retained native Start witnesses are:

| Witness | UTC | Remaining service seconds | Margin above 1,140 seconds |
|---|---|---:|---:|
| [Immediately before](ui-start-before-01.json) | 01:57:02.055 | 1,150.952 | 10.952 |
| [Immediately after](ui-start-after-01.json) | 01:57:02.146 | 1,150.861 | 10.861 |

The bracket spans 0.091 seconds. Both values pass the required Start margin and agree, to within a millisecond, with arithmetic from the retained UTC spawn time and 1,200-second lifetime. The earlier bound receipt also retains the spawn's monotonic timestamp and the parent's monotonic pre-click remaining-time check. These are operator-recorded Start witnesses, not authenticated operating-system click timestamps. Wall-clock agreement alone cannot prove the absence of a clock jump; this audit performed no new clock, process or service query.

## Accepted configuration and package

The [first passive manifest snapshot](passive-manifest-01.json) records session `sustained-1791942995555-1`, generation `1`, revision `33`, step/durable step 30, no saved journal and `awaitingLanguage`. The [second snapshot](passive-manifest-02.json) records the same session and generation at revision `37`, step/durable step 31, one journal and `running`. Their configurations are identical and match every frozen [plan](run-plan.json) field:

- `reservoir-journal-v5`, seed `20261013`, cadence 30, maximum 361 steps and 12 attempts.
- 900 active seconds, 64 MiB storage and 1,000-millisecond pacing.
- Leak 0.65, noise amplitude 0.02, initial retention 0.955 and regulation enabled.
- Owned Ollama endpoint `http://127.0.0.1:60782`, model `gemma3:4b`, requested context 8,192, output limit 1,024 and request deadline 180 seconds.

Temperature zero is part of the fixed app transport and frozen protocol; it is not a separately stored language-configuration field in these manifest snapshots. The snapshot files were inspected here; their recorded live-store paths were not followed. Whole-chain numerical, prompt, save/application and provider-response joins await the immutable export.

The [package provenance](package-provenance-01.json) was compared with the current ordinary files: its exact 46-file app path set, every file hash, archive and pinned verifier all match. The app executable and pin remain SHA-256 `7d46719838495b7a9ba57eea69ac9c940bb81f2fdc47cd12b761d97bb472d081`; the archive remains `3628110243c963d5aeca943864b174ea9873b357dbbfd949ee497299d9d5190a`. Existing qualification/archive-check receipts also remain exact. This is identity continuity, with no new build, signature execution or UI test.

The [helper continuity receipt](helper-continuity-01.json), exact copied supervisor/tests, prior reuse receipt and selected-model metadata receipt all match their bound hashes. This audit did not re-read model blobs, private key/config contents, running process state or an endpoint. Actual launch revalidation and eventual cleanup remain separate supervisor evidence.

No frozen source, run plan, historical evidence or production file was edited. No model/provider request, UI action, signal, new process inventory, resource poll or live-store read was performed. Preparation agreement does not establish future resource safety, complete context processing, writing quality, causal improvement or completion of all twelve slots.

Audit receipt SHA-256: `c9d76ca57284ddbfb9254d4af1244673c3f0b90194e3fee515cd104cc277112f`.
