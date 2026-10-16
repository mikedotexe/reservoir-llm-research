# Bounded cohort: retained mechanical outcome

The October 16 attempt loaded one model and processed nine operations before the
third unsteered journal reached the frozen 1,024-token ceiling. The completed
prefix and incomplete response are retained. The cohort stopped without retry;
the recurrent and trace sessions contain no model operations. This is an
incomplete comparison, not a null comparison result.

| Measurement | Retained result |
| --- | --- |
| Model initialization | One actual response, copied as provenance into three sessions |
| Quiet input | Six captures; 145 processed input tokens; zero sampled tokens |
| Completed writing | Two journals, 399 and 453 content tokens, each ending with sampled EOS |
| Save and feedback | Written at steps 20 and 40; verified saved text applied at 21 and 41 |
| Incomplete writing | Third response: 585 prompt tokens and 1,024 content tokens processed; no EOS, saved-journal feedback, retained activation or projection |
| Final numerical boundary | Unsteered step 60; recurrent and trace step 0 |
| Independent projection check | Eight captures, 256 coordinates; maximum absolute error 1.6653345369377348e-16 against tolerance 1e-12 |
| Residual intervention | All 3,257 processed positions across nine operations had exactly zero actual delta ratio |
| Allocator cleanup | All nine operations returned to 2,264,693,768 active bytes and zero unused cached bytes |
| Peak allocator allocation | Largest operation peak: 3,193,685,232 bytes, approximately 2.974 GiB |

These memory quantities describe this worker's MLX allocator, including its
resident model. They do not measure total process or host RAM. The 64 MiB free-cache
policy reclaims excess on the next allocation; it is not a hard peak-memory cap.

The preserved executed binary independently verified all three sessions offline:
the unsteered record has 22 events, two journals and 60 steps; each unstarted record
has zero events, journals and steps. Every verifier reported `modelsContacted: false`.
The runner's `verifiedCompletedSessions: 0` correctly refers to complete six-journal
sessions; it does not discard this later verification of the incomplete prefix.

The new calibration's numerical contents match the earlier calibration exactly.
Only `modelManifestSha256` and the enclosing `sha256` differ, because the worker
source identity changed. There is no within-cohort matched-arm writing contrast.

[Machine-readable metadata](cohort-summary.json) preserves artifact identities and
verification hashes. Private raw evidence and the analysis result remain under
`research/outputs/activation-headroom-20261016/`; journal prose is not included here.

Reproduce the read-only mechanical analysis from the repository root, selecting
a fresh output filename:

```sh
desktop/ReservoirScope/.venv-activation/bin/python -B \
  probes/2026-10-16-activation-cohort.py \
  research/outputs/activation-headroom-20261016/cohort-01 \
  --previous-calibration research/outputs/activation-0.26.0-20261015/model-qualification-02/calibration.json \
  --output /tmp/activation-cohort-mechanics-fresh.json
```

The three offline verifications used the frozen binary identified by SHA-256
`7119c77df34eb6954a9263a3f8810e1b00af3ac0622c65e27c124afaedbc34d7`
with `--verify-activation` and each retained session directory. Their separate
receipts are `cohort-offline-verification-1.json`, `-2.json` and `-3.json` beside the
private mechanical summary. No model request or evidence mutation was performed
by these analyses.
