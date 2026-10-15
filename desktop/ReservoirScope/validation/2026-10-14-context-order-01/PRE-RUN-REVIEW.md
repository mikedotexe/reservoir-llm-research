# Independent pre-run input review

No concrete blocker was found in the prepared contrast or its prospective interpretation. This review covers preparation, the twelve prompt files and the written protocol; it does not qualify the separate HTTP runner or authorize launch. No new responses, service, model, application or live store were accessed.

## Executed checks

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_prepare_inputs.py`: all six tests passed. Cases cover escaped headings/Unicode/newlines, wrong decoded memory, ambiguous or missing headings, changed version and changed invitation.
- `PYTHONDONTWRITEBYTECODE=1 python3 independent_inputs_review.py`: passed. This separate reconstruction does not import the preparation function. Its [receipt](independent-inputs-review-01.json) binds before/after identities and the exact command's [implementation](independent_inputs_review.py).
- All twelve prepared files match their frozen descriptors. At each of six anchors, A is byte-identical both to the pinned material's prompt and to the original exported journal object's prompt. B is exactly prefix + original memory block + original readout block + original suffix. Leading separators travel with their blocks. Header, session context, writing boundary and invitation are unchanged. Paired UTF-8 sizes are 3,552, 3,564, 3,498, 3,466, 3,309 and 3,315 bytes for steps 60 through 360 respectively.
- Each decoded JSON memory equals the full preceding original journal entry, with its actual observed/application clocks; the late boundary retains the same return record. The six transformation receipts' block hashes match the independent slices. Escaped journal headings cannot become these LF-delimited outer headings.
- All 73 source-export files still match the inventory in the prior passing receipt. That receipt, its review material and its pinned executable match their recorded identities. Existing production replay evidence is reused; no new verifier process was executed.
- Slots are exactly 1–12, with anchors 60/120/180/240/300/360 and orders AB/BA/AB/BA/AB/BA. Run-plan identity and the declared request/budget bounds agree with the prepared inventory. All reviewed inputs remained unchanged during the checks.

## Design and limits

The [run protocol](PROTOCOL.md) and [reading protocol](READING-PROTOCOL.md) preserve fresh-A versus fresh-B comparisons, stop/partial/unstarted outcomes, and a masked response-only reading before exact-source comparison. Historical outputs are known references. The same complete information is present in both arms; no fresh output feeds later context or numerical state. B keeps the copied v8 header but is explicitly an offline diagnostic, not a production-v8 record.

The intervention changes both blocks' positions, not memory availability. It cannot separately identify recency, salience, attention or comprehension, and identical byte lengths do not prove identical tokenization. Six paired snapshots from one dependent episode and one response per arm do not estimate general model variance or long-run writing benefit. Metaphors, repeated imagery and a chosen form are not automatic factual errors or style failures. These limitations are appropriately retained; no criteria change is requested.

## Reviewed identities

| File | SHA-256 |
|---|---|
| [prepare_inputs.py](prepare_inputs.py) | `4d2f899ca3a27d39e0a47839a8d03843a48afbb50af17da6c83f741a2dbcd0b7` |
| [test_prepare_inputs.py](test_prepare_inputs.py) | `a10ac9813d9cb25999591e707021c6928adbd4896f619393b985686059b5eb8a` |
| [PROTOCOL.md](PROTOCOL.md) | `1af4720524e37e64f3e578d1057c817213989d2a7ef7d16001dfb7750102115a` |
| [run-plan.json](run-plan.json) | `356a87a10ea335667668bc8018455aeec9c20e7c90b174ec48644579bf5f833e` |
| [frozen-inputs.json](frozen-inputs.json) | `56aaa35d7889aeb590d739e9ad8f0c63c85996cdf619681b74f403ff7644871c` |
| [transformation-checks-01.json](transformation-checks-01.json) | `1c27074c7a6bd5888457ac1e51972b23609ef553735365d45c4b042c8c30ee70` |
| [independent_inputs_review.py](independent_inputs_review.py) | `d5cd042823611960fecd5e3be97b5a2b27b6f0f7c244094dc3d18f462f072c60` |
| [independent-inputs-review-01.json](independent-inputs-review-01.json) | `4313aa7c46251bbf1f141800047c56d5fdd4f56d2e869edf4a642d99b1886494` |
