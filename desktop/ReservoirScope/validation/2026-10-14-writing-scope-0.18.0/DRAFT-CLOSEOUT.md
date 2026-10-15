# Draft closeout · writing scope 0.18.0

Prepared 2026-10-14 after source qualification, while the distinct 0.18.0 package
build is in progress. This is proposed wording for the roadmap and parity ledger,
not a package or native-acceptance receipt. Update those outcomes only from the
separate completed checks. Historical evidence remains unchanged.

## Proposed roadmap text

New sustained sessions use `reservoir-journal-v6`. It preserves the v5 compact
optional readout, exact previous eligible journal and open invitation, changing
only the version header and adding two sentences to SESSION CONTEXT:

> Writing is the only action available here. Describing a control change or experiment does not execute it, and no new readout arrives while this entry is written.

Topic, form, imagery, length and reflective stance remain open. The existing
numerical text encoding, forcing, noise, regulation, cadence and budgets are
unchanged. Complete writing still requires durable save/readback before next-step
feedback; the latest applied journal returns as full-text memory. No command
parser, new measurement channel, rewriting or factuality gate was added. Restored
v1–v5 sessions keep their original versions and exact prompts; an omitted historical
version remains v1. Full retained observations remain available separately from the
compact subset supplied to the model.

Source qualification passed: 200 core tests, 194 desktop tests with two explicitly
ignored, 362 frontend tests, TypeScript, strict core/desktop Clippy and 26 pure helper
tests. The desktop first run remains preserved: 191 passed, two failed and two were
ignored. Both failures were stale v5 expectations after the new default became v6.
The correction pins historical v5 coverage, adds v6 reanchored-prompt rejection and
updates the current-default worker expectation; no production behavior changed to
make those tests pass.

Package identity, historical bundle replay and actual native synthetic
export/recovery are **pending at this draft's cutoff**. No real-model request has
been made for this implementation tranche. Synthetic qualification cannot establish
whether v6 reduces invented actions or improves writing. A later real-model episode
needs its own prospective bounds and complete-response review; the known v5 writing
is reference material, not an unseen control.

The earlier CI run passed macOS but stopped on Windows and Linux at a cross-language
covariance test requiring bitwise equality. The separate test-only correction uses
the existing tight cross-language comparison and retains exact same-runtime reset
coverage. Production numerical code and verifier tolerance are unchanged. Corrected
remote CI and packaged Windows/Linux acceptance remain unqualified.

## Proposed parity ledger entry

| Area | Implemented and source-qualified | Still pending |
| --- | --- | --- |
| M5b sustained writing context | V6 makes available actions explicit while preserving open-ended writing, compact optional measurements, full-text memory and existing save/application rules. V1–v5 restore and reconstruction remain distinct; unknown versions and relabeled evidence are rejected. | Distinct 0.18.0 package identity, native synthetic export/recovery and historical bundle replay; real-model effects on writing and factual grounding are unmeasured. |
| Platform qualification | Test-only correction for the earlier Windows/Linux cross-language covariance assertion; exact same-runtime reset invariant retained. | Corrected remote CI and native packaged acceptance on Windows/Linux. Local macOS source checks do not establish those outcomes. |

## Evidence to retain with either entry

| Evidence | Scope |
| --- | --- |
| [Protocol](PROTOCOL.md) and [template](PROMPT-V6-TEMPLATE.txt) | Exact two-sentence change and unchanged contracts. |
| [First Rust receipt](rust-checks-01.json), [failure analysis](rust-failure-analysis-01.json) | 200 core passes and the preserved two stale desktop assertions; original failure is not erased. |
| [Final Rust receipt](rust-checks-02.json) | 194 desktop passes, two ignored, strict checks; preceding core result reused only with matching core inputs. |
| [Frontend receipt](frontend-checks-01.json) and [comment addendum](frontend-comment-addendum-01.json) | 362 tests in 39 files and TypeScript; subsequent change was only the documented v5-to-v6 default comment. |
| [Helper receipt](synthetic-harness-tests-01.json) | 26 pure helper tests; no provider launch or native workflow result. |
| [Platform CI account](../2026-10-14-platform-ci-0.17.0/README.md) | Original platform failures and the bounded test-only correction. |
| [Native qualification plan](NATIVE-QUALIFICATION-PLAN.md) | Prospective synthetic workflow, not an executed result. |

No production source, roadmap, parity ledger or frozen historical receipt was edited
while preparing this draft.
