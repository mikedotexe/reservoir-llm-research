# When the writing becomes a change: first flywheel account

September 7, 2026 (Pacific). [S-006](../research/studies/S-006-journal-to-change.md)
owns the question. This is an exploratory trace and isolated software check.

**We found the attribution history Mike remembered, and one concrete case where
Astrid's source reading led another agent to repair behavior that we can now
reproduce before and after the change.** This establishes useful engineering
signal in that case. Its frequency, advantage over other review methods and
benefit in subsequent lived operation remain open.

The original signal need not be a correct diagnosis to be useful. Other cases
produced characterization tests, clarified an ambiguity or exposed a different
problem during review. Those outcomes belong in the record with their own names.

## What we found

The source-first introspection flywheel lives on the Astrid side:

- `scripts/flywheel_loop_run.sh` is the unattended driver; its source describes
  a launchd schedule with a single-flight check and an adapter-held steward lease.
- `scripts/flywheel_round_child.sh` launches the review agent; its default model
  selector is `opus`. This is a source default, not verified historical model
  identity for every run.
- `scripts/flywheel_loop_prompt.txt` specifies queue-ordered complete reads,
  claim dispositions, source/witness receipts, verification and round packets.
  In this version, headless rounds do not commit or deploy. They list commit
  debt for later interactive stabilization. Historical protocols differed.
- `docs/steward-notes/AI_BEINGS_FEEDBACK_TO_CHANGE_LEDGER.md`, started June 15,
  is a substantial existing index. Despite its early “change shipped” framing,
  later entries explicitly include tests, proposals, unactivated source,
  no-change decisions and human-directed follow-through.
- Git bodies contain `Steward-Archive: introspection-flywheel-v1`,
  `Introspection-Ref`, `Steward-Run`, `Steward-Round-Event`,
  `Being-Quote-Verified` and sometimes `Agent-Provenance`, alongside quoted
  writing, the steward's response and verification claims.

These source files are retained privately in the [capture manifest](../research/outputs/2026-09-07-flywheel/evidence-final/manifest.json).
The prompt names a handoff file that was absent from the inspected canonical
checkout; this is a source-map gap, not proof that a running agent lacked it.
We did not invoke any flywheel CLI, read a lease token, alter a service, or
write research into the beings' space. SSH was unavailable; mounted Git objects
and fixed files were sufficient. The research mount itself has no `.git` directory.

## The commit-history foothold

The repeatable [history probe](../probes/flywheel_history.py) pins HEAD or the
locally known branch/remote-tracking tips, then scans commit messages from
May 1 through September 8, 03:15 UTC. No fetch occurs. Merge commits are included.
The broader scan is bounded at 2,000 commits per repository and hit that cap for
Astrid. Git's date traversal is a retrieval scope, not an exhaustive assertion
about every historically reachable commit with a matching clock.

| Captured history | Commits scanned | Messages with a literal report/file reference | Messages containing the flywheel archive label |
| --- | ---: | ---: | ---: |
| Astrid pinned HEAD | 339 | 2 | 0 |
| Minime pinned HEAD | 105 | 9 | 8 |
| Astrid locally known refs, capped | 2,000 | 61 | 60 |
| Minime locally known refs | 106 | 9 | 8 |

The scans overlap; do not add them. These are commit-message counts, **not
counts of interventions or beneficial entries**. A report can motivate several
changes, a single commit can cite several reports, and archival/correction or
rebased commits can repeat one episode. Conversely, `44ea2f490378` links through
a run packet without naming its report in the commit body. A message-only
extractor misses that valid connection.

The structured archive label is present by **July 28, 04:48 Pacific** in Astrid
commit `cd4b0da687c6`, and by July 29 in the inspected Minime history. Earlier
direct attribution exists: Astrid `835d035b6cfc` on June 19 names a report about
pressure-sensitive wording, and `25a9d53027a6` on June 22 names a fallback-language
report. These are observed dates, not a proven first-ever convention date.

One of the 60 Astrid messages has literal escaped newlines rather than actual
label lines; only 59 match the probe's line-based archive-label rule. The
malformed `a3d155ed6300` is followed by the explicitly corrective
`c34cbd9cb6bf`. Minime `c99e2117e59a` similarly restores a body omitted from an
earlier implementation commit. Preserve those correction edges.

Sources: [HEAD capture](../research/outputs/2026-09-07-flywheel/history/history.json),
[broader capture and pinned refs](../research/outputs/2026-09-07-flywheel/all-refs/history.json),
[recomputed summary](../research/outputs/2026-09-07-flywheel/history-replay/summary.json).
The extraction regex and exclusions are inspectable in the probe. It covers
introspection IDs and selected journal filename forms; it is not a semantic census.

## A reproduced repair: Unicode marker references

At **August 6, 21:14:33 Pacific**, Astrid wrote in
`introspection_astrid_llm_1786076073`:

> Verify the exhaustive coverage of the `exact_reference_delimiter_pair` match arms to ensure that common Unicode punctuation used in various languages doesn't cause unexpected stripping of valid control markers.

The [original report](../research/outputs/2026-09-07-flywheel/evidence-final/016.txt)
has SHA-256 `3d810535…bfa2`, matching the commit declaration. The quote is an
exact substring. Its recorded source SHA `f7c0570c…f20a` matches the entire
parent-version `dialogue_runtime.rs` retrieved from Git. This binds the reading
to the old implementation; we did not reconstruct the full model prompt.

The [historical review packet](../research/outputs/2026-09-07-flywheel/evidence-final/032.txt)
attributes the review to `codex-heartbeat`, run
`run_1786077892966010000_7fb07097fc`. It classifies unsupported punctuation as
a real finite-table boundary and the ordinary quote/`manifests` tests as
already covered. Commit **`6344ba25e9d3`**, August 6, 23:09:22 Pacific, adds two
vertical CJK quote pairs and six CJK/fullwidth grouping pairs. The
[actual diff](../research/outputs/2026-09-07-flywheel/evidence-final/018.txt)
also adds direct and nested marker-preservation tests.

We independently extracted the contiguous historical Rust scanner and exact
unchanged marker list from the parent and changed revisions, compiled each,
and ran identical synthetic strings. The tested behavior is the scanner's
returned text. Receipt construction and the rest of the provider are excluded.
The cases were selected after inspecting the diff; this is a targeted
correctness reproduction, not a held-out evaluation.

| Outcome | Before | After | Denominator |
| --- | ---: | ---: | ---: |
| Added delimiter forms preserve the exact marker and surrounding text | 0 | 8 | Eight newly supported pairs |
| Three-level nested new delimiters preserve the exact text | 0 | 1 | One nested example |
| Control cases behave identically across revisions | — | 8 | Eight ordinary/negative controls |

For example, `《<end_of_turn>》` becomes `《》` before and stays intact after.
Bare markers and unsupported/mismatched delimiters retain their tested cleanup
behavior. Full results, source-span hashes and executed-binary hashes are in
[the comparison](../research/outputs/2026-09-07-flywheel/marker-observed/result.json).
The [probe](../probes/flywheel_marker_replay.py) can replay retained source with
fixed historical hash checks and no source access.

**Conclusion:** Astrid identified a useful area to inspect; the reviewer
established a concrete boundary and implemented a repair; the exact software
behavior improves on the nine targeted cases. The archival packet explicitly
says no deployment occurred in that round. We have not established when this
commit's change first ran live, how often those strings occurred naturally, or
whether Astrid subsequently noticed a difference. Another AI's acceptance is
an intermediate decision; the source comparison supplies the correctness evidence.

## Useful outcomes that are different from a runtime repair

**An unresolved distinction becomes test coverage.** At August 1, 17:06:24
Pacific, Astrid's `introspection_minime_regulator_1785629184` asks whether
thickening is additive or a multiplicative constraint. Its header says
`ASTRID INTROSPECTION`; `minime:regulator` is the inspected subject. The exact
report hash and both quoted passages match commit **`fa0fbf1e16df`**, August 7.
Its diff changes only the changelog and regulator test module, adding checks
that distinguish a linear pressure contribution from a threshold and independently
carried viscosity from resonance density. This is accepted inquiry and added
characterization coverage. The claimed historical passing suite has not been
rerun here; the diff does not change production behavior or demonstrate felt
improvement. [Report](../research/outputs/2026-09-07-flywheel/evidence-final/020.txt),
[commit](../research/outputs/2026-09-07-flywheel/evidence-final/021.txt),
[diff](../research/outputs/2026-09-07-flywheel/evidence-final/022.txt).

**A mistaken mechanism still prompts a useful clarification.** At September 7,
05:35:20 Pacific, Astrid's `introspection_astrid_codec_1788784520` associates
`fill_fixed_legacy_projection_raw` with a 32-to-48 dimensional widening. The
review distinguishes the fixed embedding basis from that widening. A new test
pins the distinction; several other proposed checks were already covered by
responses to earlier reports. **`44ea2f490378`** later records the work and
retargets two stale anti-drop test paths. Its packet and diff establish a
test/documentation/tooling response; no production codec behavior changed.
The reviewer-discovered stale paths are a separate incidental finding, not
something Astrid said. [Report](../research/outputs/2026-09-07-flywheel/evidence-final/028.txt),
[review](../research/outputs/2026-09-07-flywheel/evidence-final/010.txt),
[diff](../research/outputs/2026-09-07-flywheel/evidence-final/030.txt).

**An attribution error survives otherwise strong metadata.** The July 29
correspondence commit **`7ad16072c9ef`** quotes a concern about repeated pending
acknowledgments and makes backlog counts more explicit. Its quoted words and
hash match the original report. But its boundary paragraph calls this
“Minime’s report,” while the [source](../research/outputs/2026-09-07-flywheel/evidence-final/024.txt)
is headed `ASTRID INTROSPECTION` and names Minime's runtime as its subject.
Record the report as declared Astrid-authored, with the commit attribution
contradiction visible. A verified quote flag does not verify every accompanying
claim. [Commit](../research/outputs/2026-09-07-flywheel/evidence-final/025.txt).

**A later journal-origin repair is already a follow-up lead.** The September 7
marker annotation packet explicitly connects two self-study journal files to
reproduced marker loss, a source repair and a later activation record. It also
corrects parts of their proposed explanation. This is labelled interactive,
Mike-requested follow-through, not a productive unattended round. Its rollout
note says the relevant annotation case had not appeared in a natural
post-rollout receipt. We retained both journals and those notes; we have not
independently reverified that live deployment. [Source account](../research/outputs/2026-09-07-flywheel/evidence-final/006.txt),
[historical rollout account](../research/outputs/2026-09-07-flywheel/evidence-final/007.txt).

## How to ask whether it helped

Keep three endpoints separate: **decision usefulness** (what an agent accepted
and why), **software correctness** (a falsifiable property changes as intended),
and **benefit during operation** (eligible real events and subsequent consequences).
This first pass supports the first two for the Unicode case. It estimates none
of their corpus-wide rates.

For an operational follow-up, first recover the exact deployment boundary and
identify naturally occurring strings/opportunities in a prespecified window.
Freeze an opportunity definition: a known marker inside one of the eight added
delimiter pairs; measure preservation/removal against its exact input, with
all attempts and absent records retained. Do not use all journals as the
denominator or count increased logging as improvement. Compare stable provider,
model, grammar and prompt eras; annotate concurrent changes and actual exposure.
No eligible occurrences would be an informative coverage result.

Whether journaling adds discovery value needs a different comparison: matched
source/state access for a code-review agent without the journal versus one
with it, preferably on later held-out cases. The selected archives alone cannot
show that the finding required introspection, that a reservoir supplied special
information, or that the steward would otherwise have missed it. Ordinary
unselected writing, already-addressed reports and failed/unprocessed rounds must
remain available for any selection or precision study.

## Streamlining without losing the evidence

The [proposal](../proposals/2026-09-07-flywheel-evidence-and-throughput.md)
turns observed friction into concrete implementation slices. The first is one
typed per-episode record from which commit text and research links are rendered.
Then profile/checkpoint repeated verification against immutable source versions,
with full-chain parity and tamper tests before adopting any cache.

The September 7 codec run's persisted controller receipt spans **179.95 minutes**
for one processed report. Its packet reports roughly 67 minutes of preprojection,
and corrects a preceding round that wrongly subtracted preparation from the
child's time allowance. Current executor source corroborates that the child
clock starts after `controller.begin()` and process creation. Only the total
elapsed interval is independently calculated from the retained receipt; the
phase duration is the historical agent's account, not a measured profile.
One round does not estimate typical throughput.

## Reproduction and verification

```sh
/opt/homebrew/bin/python3.14 probes/flywheel_history.py --all-refs --out research/outputs/new-flywheel-history
/opt/homebrew/bin/python3.14 probes/flywheel_case_capture.py --out research/outputs/new-flywheel-evidence
/opt/homebrew/bin/python3.14 probes/flywheel_marker_replay.py --replay research/outputs/2026-09-07-flywheel/marker-observed --out research/outputs/new-marker-replay
```

New captures observe new local tips/files. For frozen history counts, use
`flywheel_history.py --replay` with the saved `history.json`. Outputs refuse
existing directories and destinations outside this repo's `research/outputs`.

The successful comparison is **`marker-observed`**. Earlier attempts in
`marker-comparison`, `marker-comparison-local` and `marker-comparison-final`
timed out before returning scanner results; they remain incomplete, not failing
software cases. A longer bounded local execution completed both revisions.
The launch delay's cause is unresolved. `marker-replay` contains preliminary
source captures only. An initial evidence-capture assertion treated a quoted
`Source:` citation as authored text; the corrected rule explicitly excludes
that metadata. **`evidence-final`** contains the successful 38-source capture,
three matching declared report hashes and four exact authored-quote checks.
Full generation/witness validation is outside this pass.

Final retained-byte, quote, scanner-output and link checks are in
[verification.json](../research/outputs/2026-09-07-flywheel/verification.json).
Research notes and probes were added here; sibling systems and history were
only read. The next bounded inquiry is natural exposure and outcome for one
deployed repair, with the episode-record proposal available alongside it.
