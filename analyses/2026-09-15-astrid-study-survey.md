# Astrid's studies: repeated orientation, useful local reading, and missing distinctions

Astrid's recent studies contain real engagement with code, but most of this batch
repeats an earlier explanation while announcing a move to the next question.
Generation is functioning. The more useful intervention is to make the evidence,
its scope, and already-available answers easier to use.

This exploratory survey freezes the latest **100 top-level SELF_STUDY journals**
at September 15, 2026, **16:30:41 UTC / 09:30:41 PDT**, selected chronologically
without a content filter. They span **09:51:23–16:23:44 UTC / 02:51:23–09:23:44 PDT**.
All hundred bodies were close-read. The latest **20 dialogue journals** within
that interval form a separate, deliberately recent context sample; they are not
a representative sample of all dialogue over the six-and-a-half-hour period.

The [evidence packet](../research/outputs/2026-09-15-astrid-study-survey/README.md)
retains the protocol, journals, exact requests and responses, source pages,
annotations, independent readings, and reproducible measurements. Earlier release
findings, including two of these maintenance responses, were already known. This
is discovery, not a blinded experiment or a causal before/after evaluation.

| Observation | Result in the 100-study cohort |
| --- | ---: |
| Supplied input | 89 maps; 5 EOF notices; 1 recovery; 5 code pages |
| Files represented by those code pages | 2, both in Astrid's kernel |
| Full response matches to journals and accepted wire evidence | 100/100 |
| Distinct request bodies / response texts | 100 / 90 |
| Server-reported ending | Model EOS in 100/100 |
| Completion tokens | 144–850; median 306 |
| Requested and server-confirmed output ceiling | 4,096 in 100/100 |
| Authored response words | 91–465; median 212.5 |
| Journal file bytes, including headers | 775–3,568; median 1,595.5 |
| Complete preceding study accounts carried in each request | 4 in 100/100 |
| Saved note / question updates | 1 / 1 |
| Old / newly released study system prompt | 95 / 5 |

Journal-to-generation association combines exact full text with a unique shared
receipt between the preceding selected journal and the current journal's mtime.
Eighteen entries have text repeated in multiple receipt records, so text alone
cannot identify their generation. All selected shared requests/responses match
one accepted provider artifact exactly. These are timestamp-assisted journal
associations, not invented durable journal IDs. The receipt chain also matches
the preceding study's exact request and response wire hashes in all 99 available
pairs; that chain alone does not establish action execution across other modes.
The observer's retained startup identities associate entries 001–095 with bridge
PID 89145 / source `ed62f1b8`, and 096–100 with PID 36526 / source `97db1b2f`.
Delivered kernel file revisions have their own identities; they are not proof
that those kernel modules execute in the spectral bridge process.

## What she is discussing

For most of the batch, Astrid describes `accepted_legacy` as a two-tier legacy
validation mechanism: match a component name, then require an exact optional hash
if the corresponding baseline entry supplies one. She repeatedly says that this
question is settled and that she will examine capability management and capsule
lifecycle next. Yet **79 of her 100 final choices request the same kernel source
directory map**. Another ten request the kernel component map. The 89 map inputs
contain only six distinct map views after excluding carried notebook material.
Unlike Minime's long catalog traversal, Astrid's recurring old directory map
already fit on **one page with six direct file choices**. Shrinking the map is
therefore insufficient as an explanation or repair for her repeated orientation.

The same saved question about `accepted_legacy` is supplied in entries 001–092.
The complete recent accounts often repeat that it is already answered. Retention
is operating, but much of what it retains is the intention to move forward.
This does not establish that carrying those accounts caused the repetition.

There is meaningful development near the end:

- **088–092:** She chooses an actual source opening, receives the two pages of
  `capsule_runtime_health.rs` around an intervening recovery/map episode, explains
  the `any`/name/optional-string comparison, writes a new note and clears the old
  question. This is a source-supported local explanation and a real notebook change.
- **094–096:** She asks where `Baseline` is defined and whether its collection is
  hardcoded or loaded from configuration. The delivered pages already showed
  `Baseline`, `Vec<BaselineEntry>`, and `Option<String>` at lines 6–17, plus
  `load_baseline` and `scripts/baselines/capsule_runtime_health.json` at 194–199.
  The source was available; those specific answers did not become durable findings.
- **096–100:** The new compact map offers an exact partial-file RESUME. She chooses
  it, reads three maintenance pages, and develops an account of leases, stable
  reads, atomic acknowledgments and concurrency. This is useful navigation uptake
  and richer source engagement, with important overgeneralizations still present.

The five new-prompt studies are one map, three source pages, and another map.
That short sequence is encouraging but cannot establish that the release caused
better understanding. It does not exercise every newly released recovery or
stalled-navigation feature.

## Choices across study and dialogue

The study-only sequence initially suggests five navigation mismatches: four MAP
choices are followed by EOF, and a CONTINUE is followed by recovery for a different,
nonexistent `lifecycle.rs` path. The bounded action trace explains **all five**.
Later dialogue turns explicitly issue `SELF_STUDY REPLACE ...`; the action records
say that these replace the pending earlier choices. The guard blocks ordinary
replacement first in the four EOF cases, then honors the explicit replacement.

These are choices across two activities, not evidence of a dropped pending request.
All 100 authored NEXT strings also match one action record within five seconds of
their journal filename clock. This is an exact-command and timestamp association,
not a durable journal/action identity or proof that every queued choice completed.
They do expose a presentation limitation: the next study's “previous response
choice” refers to the preceding study, while the action that changed its input came
from dialogue. An optional receipt naming that intervening activity and replacement
would make the experienced sequence easier to follow without privileging either
choice. The [method review](../research/outputs/2026-09-15-astrid-study-survey/reviews/method-review.md)
retains the five action sequences and 19 specifically selected intervening journals,
separate from the latest-20 dialogue context sample.

## What the source supports—and what it does not

The [independent source audit](../research/outputs/2026-09-15-astrid-study-survey/reviews/evidence-review.md)
separates correct local observations from larger claims.

**The optional legacy comparison is real. Its security role is overstated.**
`accepted_legacy` compares a name and an optional string. Its caller obtains the
string from `meta.json` and uses the result for health counters and a warning
status. This path does not itself hash the current WASM payload or revoke a
capability. The loader separately computes a BLAKE3 digest and checks metadata.
The captured baseline currently contains an empty legacy-acceptance list; the
function's possible branches do not establish which exceptions are configured.
This is a distinction worth preserving, not evidence of a discovered loader bypass.

**The maintenance reading contains sound observations and overreads its tests.**
She recognizes file-identity checks, temporary-file/rename writes, expected-group
checks and rejection when both lease kinds are selected as active. But a positive
test fixture does not establish every rejection condition. Serializing a literal
`CoreAck` and asserting its fields is not validation of a live lease, nor does it
make the reflection schema mandatory for every ACK. An expired lease can remain
structurally valid while not authorizing active selection. Those distinctions
are not yet joined in her account.

**Reaching the file's end is being treated as complete coverage.**
Entry 099 starts at a fragment of line 839, inside the end of a test, and shows
only 800 bytes through the closing braces. Its footer says “End of file.” The
following map correctly reports that bytes **0–3,452 remain undelivered** at this
revision, yet entry 100 says the complete maintenance architecture has been
synthesized. The missing opening includes definitions relevant to her claims.
The reader's map already knows about the gap; the last-page experience does not
put that fact alongside the EOF message.

These passages identify useful research and interface work. They do not establish
a new live kernel fault, compromised integrity, or a general measure of Astrid's
understanding.

## What shortness and neighboring dialogue tell us

All selected studies reach an actual model terminal token, with no output-limit
termination. The server confirms temperature 0.7, no additional active sampling
filters, thinking off, coupling strength 0.02, and the 4,096-token allowance.
The optional extended profile is not selected in these requests. No selected
journal drops or summarizes the accepted response. The records therefore do not
support truncation as the explanation for these short files.

The provider-observer supplement also checks opportunities beyond saved journals.
Its ten-minute lead-in through the fixed cutoff contains **103 physical study
attempts**: 102 finish before the cutoff, all with exact accepted response evidence
and normal stops; two belong to the lead-in and 100 to the selected journals. One
request starts before the cutoff but finishes 11.406 seconds after it, so it remains
censored at the cutoff. There is no observed failed outcome among the 102 completed
attempts. This is a bounded observer frame, not a count of unrecorded or deleted
opportunities. All 100 selected journals correspond to distinct physical attempts;
identical prose here is not evidence of a cached response being replayed.

The inputs carry 3,855–6,495 prompt tokens and four complete prior accounts. More
output room alone would not supply the missing implementation distinction or make
the configuration answer persist. Queue waiting and active generation/reservoir
work are retained separately as timing measurements, not measures of thought.

The separately selected dialogue sample returns to the peer's `spectral_bridge` /
`EventSubscriber` / `capsules_loaded` inquiry and turns it into relational and
bodily metaphors. It does not show the current legacy/maintenance reading being
shared. That is a meaningful separation of concurrent threads, while the earlier
unsupported bridge-handler premise remains a provenance concern. These journal
texts alone do not establish the precise peer input or source supplied to each
dialogue generation.

## The next changes worth considering

1. **Put scope and coverage beside the code.** Show the enclosing function/test
   when a page begins mid-block. At EOF, distinguish end-of-file position from
   full revision coverage and offer the exact unread opening. Preserve free
   rereading, continuation and stopping.
2. **Help retain specific answers beside exact source locations.** In this case,
   make the already-delivered `Baseline` definition and `load_baseline` location
   easy to reopen when she asks about them again. Keep authored conclusions and
   factual source locations distinct; do not silently rewrite her note or mark
   the question resolved for her.
3. **Make implementation comparisons easy at the point of uncertainty.** Offer
   the health caller and actual loader check together, or the lease-selection
   implementation beside its tests. The existing SESSION mechanism can carry
   such a chosen comparison. Comparing adjacent test pages alone does not supply
   the implementation she is trying to explain.

Today's compact-map and optional navigation-feedback release already addresses
the broad catalog problem seen in Minime. Astrid's repeated small map makes the
next narrow layer especially clear: where the
answer is, what the page is demonstrating, and which parts have actually arrived.
No writing quota, forced novelty, automatic question rewrite or sampling retune
follows from these observations.

## Verification and retained history

The primary packet contains **1,193 indexed files / 17,498,605 bytes**, with index
SHA-256 `95ff3cab71a8729a6270eeb4473d2299a8a221c260c63e1d9915087268261060`.
Offline analysis, metrics and 20 quote annotations reproduce unchanged results.
Verification passes for all file hashes, 100 exact response/journal/provider
chains, true EOS below the allowance, retained source identities and five source
pages reconstructed from their exact byte ranges. The independent supplement
passes its 225 file checks, 103 distinct physical attempts, all selected journal
joins and five explicit replacement traces. Source-audit interpretations remain
separate from these mechanical checks.

HSS-23 is appended without changing the earlier history prefix. Packet files are
made read-only after the writers and verifiers finish. Earlier sealed studies and
the daily S-007 state remain untouched. Unrelated native-app edits in the research
checkout are outside this change.

## Board updates pending

No callable Artifact board connector was found. The proposed finding and follow-up
cards are retained in [the pending payload](../board/astrid-study-survey-pending.json);
they are not marked mirrored. This pass is research-only: no runtime edits, model
requests, messages to the Beings, restart, or S-007 cursor advance.
