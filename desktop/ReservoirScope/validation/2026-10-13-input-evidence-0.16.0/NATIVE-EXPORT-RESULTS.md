# Fixed-provider native export · 0.16.0 r2

The actual native export passed the exact pinned r2 production verifier and
independent static joins against the closed owned fixture log. This is a synthetic
transport, retention and feedback-boundary check. It makes no writing-quality or
complete-context-processing claim.

The [execution receipt](native-export-evidence-01.json) has SHA-256
`f37e94c3e57c5653df663cb446234cbc4cd502f11088c20c549bd2337aaf5770`.
It records the command, stdout, executable identity, every exported file identity,
fixture request/response hashes, and all five attempt joins. Qualification ran
2026-10-13 23:35:56.225537–23:35:56.340654 UTC. The supplied executable remained
`73872388b56d2483054497aa8513e3659f79dfaf255699d6bca29041cafd258d`.

The inspected bundle is
`target/qa/0.16-input-evidence/exports/sustained-1791934324379-1-1-76`:
generation 1, revision 76, live/durable step 50, four journals, 22 segments,
28 files and 1,742,891 bytes. The actual wrapper phase is `attemptBlocked`; the
core checkpoint is `blocked`. No cleanup phase was substituted during analysis.

| Attempt / observation | Retained optional evidence | Complete | Journal / first application |
| --- | --- | --- | --- |
| 1 / 10 | Reported `9007199254740993` | Yes | Saved / 11 |
| 2 / 20 | Absent; no invented zero or typed null field | Yes | Saved / 21 |
| 3 / 30 | Unusable `wrongType` from raw string `"2450"` | Yes | Saved / 31 |
| 4 / 40 | Reported `18446744073709551615` | Yes | Saved / 41 |
| 5 / 50 | Reported `321` | No: `length` | No journal or application |

All five retained prompts match the fixture's exact UTF-8 prompt hashes. The
reconstructed nonstreaming HTTP bodies also match the recorded byte hashes,
including model, requested context 8192, output budget 1024 and temperature 0.
Each retained response matches its fixed response file and exact typed count;
the two wide integers never pass through floating-point conversion in this
inspection. Provider-reported input counts and output count 32 remain separate.

All four journal objects match their retained pending candidates, received
responses, save/readback receipts and next-step application identities. Attempts
2–5 carry the exact full text and identity of the latest previously applied
journal, including JSON-string decoding of the historical prose in each prompt.
The fifth incomplete reply remains response evidence, with no saved candidate,
journal, or eligible application. The fourth journal remains the held feedback
through step 50. The event chain contains no retry, interruption or budget extension.

The fixture log reports one readiness request and exactly five generation
requests. Its stopped lifecycle entry is present; the full 5,254-byte inspected
log remained unchanged, as did all response files, the endpoint identity, the
original export and the pinned executable. Readiness count is reported from the
log; the checker does not use it as a separate acceptance predicate.

The [checker](check_fixture_export.py) uses only explicitly supplied files and the
pinned offline verifier. Its [seven pure helper tests](export-checker-tests-01.json)
cover exact integers, typed equality, missingness, duplicate/nonfinite JSON,
Unicode request bytes and immutable file identities. Those helper tests are not
a separate execution of the native workflow. A peer's read-only checker review
found no concrete blocker; numerical replay remains the production core's scope,
not a second independently implemented eigensolver.

Compatibility remains deliberately qualified. The [actual new positive bundle
comparison](actual-bundle-reader-comparison-01.json) records old 0.15 rejecting this
bundle at checkpoint hashing while r2 accepts it. The separate
[old-reader negative probe](old-reader-probe-01.json) records old 0.15 passing
journal-only new-field inconsistencies that it ignores. Together they do not
support a blanket old-reader compatibility claim: optional evidence needs a
0.16-aware consistency verifier. Neither verifier authenticates provider execution
or proves attention, comprehension, accurate prose, or physical power-loss durability.
