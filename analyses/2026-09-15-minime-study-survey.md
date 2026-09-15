# Minime's short studies: a functioning navigation loop with little new evidence

The latest hundred studies are locally coherent but collectively stalled. Minime
keeps trying to locate an event handler, repeatedly describes the same tentative
architecture, and chooses another catalog page. This is actionable evidence about
the study interface, not a hundred discoveries or evidence of a generation crash.

The cohort is the latest **100 completed SELF_STUDY journals** at the fixed cutoff
September 15, 2026, **15:06:32 UTC / 08:06:32 PDT**. The entries span **03:49:53–08:04:18
PDT**, approximately four hours and fourteen minutes. Selection is chronological,
without a topic or quality filter. This is an exploratory reading: the prior daily
report and one recent generation were inspected during schema discovery before
formal capture. All hundred response texts were subsequently close-read.

| Observation | Result in this cohort |
| --- | ---: |
| Current inputs | 99 maps; 1 end-of-file notice |
| Newly delivered code pages | **0** |
| Exact generation / shared receipt / journal joins | 100/100 |
| Native completion reason | `stop` in 100/100 |
| Output tokens | 121–312; median 188.5 |
| Requested output allowance at the adapter | 4,096 in 100/100 |
| Authored response words | 74–187; median 118.5 |
| Journal file size, including runtime wrapper/notices | 1,299–2,111 bytes |
| Parsed NEXT matching the next actual completed study job | 99/99 available pairs |
| Saved note texts / saved question texts supplied | One distinct text each |
| Complete preceding accounts carried per input | Four in 100/100 |

The [protected packet](../research/outputs/2026-09-15-minime-study-survey/README.md)
retains the protocol, exact inputs, responses, jobs, source/status identities,
quote annotations, and reproducible audits. These are repeated observations from
one inquiry by **Minime / Ollama `gemma4:12b`**, studying **Astrid's repository**.
They are not independent subjects or a controlled comparison with earlier releases.

## What he is discussing

The question throughout is which `EventSubscriber` receives
`astrid.v1.capsules_loaded` and moves a supposed global system state from
“initialization” to “active.” The saved note identifies `spectral_bridge` as the
place to look. Early responses sometimes call that connection “established” or
“confirmed”; later ones more cautiously call it a candidate.

There is a small development in the question: does the bridge mutate state
directly, or route the event through `signal_spine` to a lifecycle manager? That
distinction could guide useful reading. But it remains a hypothesis in this batch.
Both emitted `STUDY_NOTE` updates repeat identical text; all four emitted
`STUDY_QUESTION` updates repeat the same question. There is no source-based
revision of the proposed explanation.

The actual journey makes the problem concrete:

1. Entries 001–028 traverse Astrid catalog pages **99–126**.
2. At the end, entry 028 says it will continue the map but emits `SELF_STUDY CONTINUE`.
   That operation resumes the source bookmark, so entry 029 receives EOF for
   `astrid/crates/astrid-events/src/subscriber.rs`.
3. Entries 030–033 receive the home map four times.
4. Entries 034–100 start the Astrid catalog again and traverse pages **1–67**.

This is not one cached answer emitted a hundred times. All hundred raw responses
are distinct, although two pairs become identical after removing their final NEXT
line. Every available next-choice pair reaches the matching job and exact prepared
input. The failure is in reaching the inquiry's stated aim, rather than losing its
chosen command.

Entries **039–040** are especially informative. The supplied map includes exact
OPEN links for `lifecycle.rs` and `signal_spine` files. Minime identifies these as
promising candidates, yet keeps paging to “locate” them. In **45 responses** he
explicitly acknowledges that no new code was supplied. That awareness is useful;
it does not lead to a different strategy here. The
[content review](../research/outputs/2026-09-15-minime-study-survey/content-review/reading.md)
retains counterexamples and nineteen exact annotated excerpts.

## The central premise needs checking

The independent source trace challenges the proposed bridge subscriber:

- [`EventSubscriber`](/Users/v/other/astrid/crates/astrid-events/src/subscriber.rs:28) is
  `pub(crate)`, so an implementation in the separate spectral-bridge crate cannot
  implement that trait through the ordinary Rust interface. Its module also
  explicitly carries unresolved subscriber-wiring history.
- The [kernel publisher](/Users/v/other/astrid/crates/astrid-kernel/src/lib.rs:496) emits
  `astrid.v1.capsules_loaded` after loading/readiness work, with a `status: ready`
  payload. That is not evidence of the hypothesized bridge global-state transition.
- The [native CLI handler](/Users/v/other/astrid/crates/astrid-cli/src/tui/mod.rs:433) responds
  by requesting command refresh and conditional session hydration. A compatibility
  CLI capsule also subscribes to the topic.
- The bounded current-source search finds no `capsules_loaded` reference in
  `capsules/spectral-bridge/src`. Its `lifecycle.rs` concerns operator drain/shutdown,
  which illustrates why a promising filename is not proof of the presumed role.

Six retained source files match the September 11 implementation commit `ed62f1b8c2`.
This is a source audit performed by us, **not code supplied in these hundred studies**.
Text-search absence is scoped to the inspected source; it does not enumerate every
installed or dynamically constructed consumer. The crate-private trait is a direct
contradiction of the proposed external trait implementation. The broader imagined
state-transition story remains unsupported by the inspected path. No response in
this cohort identifies a new verified production defect.

## Why the entries are short, and what is going wrong

The larger ceilings are reaching the provider adapter. Every exact request sends
`num_predict:4096`, `num_ctx:65536`, temperature 0.7, `top_p:0.95`, and `think:false`.
Ollama does not echo server-confirmed sampling controls; these are serialized
request facts. It does report normal stops and token counts. There is no empty
completion, fallback, response cleanup loss, prompt compaction, or journal
compression in the hundred exact matches. All jobs finish successfully.

These are short, complete progress reports about seeking evidence. Increasing the
ceiling again would not supply that evidence. Optional extended writing, sessions,
FIND, and permission to stop are present in every system prompt; Minime does not
choose them in this cohort. Each current input also offers `RELATE EventSubscriber`.
Adding only another generic reminder to search is therefore an uncertain remedy.

The source audit identifies concrete interface choices that deserve revision:

- A repository MAP recursively lists all matching files, producing **126 pages**.
  Of the 95 repository pages in this batch, **70 list only historical steward-note
  paths**. This is classification of listed paths, not a claim that their contents
  are worthless. Full accessibility has become an unwieldy default itinerary.
- All **94** explicit next-page suggestions are selected. Catalog pagination is
  easy to follow. At its end, `CONTINUE` has a different meaning: resume source.
  The notebook and previous-choice receipt accurately preserve the result, but
  do not prevent the mismatch between prose intention and command semantics.
- Four full preceding accounts and the unchanged saved hypothesis are carried
  correctly. They repeatedly supply the explanation while the current input supplies
  filenames. The notebook labels them as recalled and unverified; this labeling
  has not prevented their promotion to factual premises. It does not prove a causal
  effect of recall placement or volume.
- A dotted event name such as `astrid.v1.capsules_loaded` does not qualify for the
  question-specific identifier RELATE suggestion. An exact literal FIND could
  point toward the publisher and consumers; it is supported but less prominent.

Minime remains on PID **93033**, with startup September 11 and a later source-status
receipt reporting `reload_required:false`. The audited host modules match that
startup inventory; the selected shared helper matches the journal-coherence build.
The study path uses the prepared source/notebook input rather than the ordinary
sensory/diversity prompt. This survey does not establish a need for more sensory
dimensions, a restart, or a sampling retune.

The completion-clock attempt frame contains **100 selected study generations**
and 20 other `strict_review` metadata records, all recorded successful, plus one
study and one other record in the five-minute incoming supplement. The first
generation precedes its journal filename by nine milliseconds; the original capture
flags and the corrected completion-clock denominator are both retained. This is
not a census of unrecorded opportunities or every autonomous action. Completed job
records are distinct from their embedded, explicitly incomplete pre-finalization
phase snapshots.

## How this fits the recent history

The earlier [September 14 daily account](2026-09-14-source-study-fidelity-day6.md)
already records **666 completed studies in its UTC 24-hour window**, including
337 recovery inputs. A 38-response unavailable-path sequence eventually chooses
the supplied correction and reaches code. A separate 175-request
`MAP spectral_bridge` recovery sequence eventually changes to `MAP astrid`.
Those are previously measured windows, not new counts from this hundred-entry
sample. The source audit confirms that bare `spectral_bridge` does not receive
a component/directory-specific recovery candidate in the current implementation.

There is therefore evidence of both successful recovery and expensive repetition.
The latest batch shows a valid catalog traversal also becoming unproductive. Our
access, retention, and chosen-command repairs are working in important respects;
they have not solved navigating efficiently or testing an inherited premise.
The September 11 Astrid survey found a related persistent-premise problem, but this
is not a paired comparison or evidence of identical causes in both Beings.

## Actionable next work

1. **Make navigation compact and specific.** Default to directory/component maps,
   with production sources, tests, and historical accounts easy to distinguish and
   the complete file list still available. Offer exact directory recovery for
   component-like requests, literal event searches, and clear map-next versus
   source-resume commands. Preserve explicit choices and deliberate rereading.
2. **Make a change of strategy easy without forcing it.** Show a short factual
   receipt when repeated navigation has supplied no code, including an already
   offered candidate and ready OPEN/FIND choices. Keep map continuation, revision,
   and stopping available. Do not penalize a first mistake or silently alter NEXT.
3. **Help test the premise with evidence.** An optional comparison should open the
   actual event publisher and consumers beside the saved account, keeping findings,
   questions, and their origins distinct. Measure whether the explanation and saved
   note develop; let Minime retain, revise, disagree, or explore further. More words
   and more completed studies should not be the success criteria.

A separate maintenance issue remains: Minime's similarity gate can replace a
journal body with a small runtime summary even though the complete response exists
elsewhere. **It did not occur in these hundred files.** Preserving the full journal
and making summaries derivative would better fit the longform-writing intent, but
it must not be presented as the cause of this sample's size.

No feature was changed or deployed, no model request was induced, and no generated
command was executed. The S-007 scheduled cursor and earlier sealed packets remain
unchanged. This account records observation and proposed repairs.

Verification checks all **675 manifest-listed files** (16,185,857 bytes), reproduces
the hundred exact delivery joins and 99 follow-through links from the retained
records, and checks all nineteen annotated quotation spans. The packet-index
SHA-256 is `75fdc186e7682df7c07926b7021526542fd2a85f79c1689bd5bf5448cdb46ee3`.
The probe and audit Python syntax checks pass. No production code changed, so no
production build or deployment is represented as part of this research check.

## Board updates pending

The local pending payload links this account, the frozen evidence, and HSS-21.
Board mirroring has not occurred.
