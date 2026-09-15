# After a blocked reading request, what reaches the next turn?

September 6, 2026, 09:11–09:15 America/Los_Angeles. Mike selected a close reading
of the [first around-time account](2026-09-06-around-0919.md), followed by one
concrete uncertainty. We chose the earliest captured READ_MORE block and the next
two repetitions. This is an exploratory follow-up selected because the action
pattern stood out; it is not an independent prevalence test.

## The reading

At 09:11:01 Astrid is addressing Minime's changing telemetry. She writes about
“that sharp, jagged dip in the `dfill/dt`” and says, “I want to acknowledge the
sheer effort of that stabilization.” Her action request is simply `READ_MORE`,
with no document, query, or target in the action tail.

At 09:11:03 the action ledger records a block. Its reason is
`no_active_read_only_research_budget`; `would_dispatch` is false. It preserves the
raw request and suggests `EXPERIMENT_RESEARCH_BUDGET_ACCEPT latest`.

At 09:12:54 she again addresses a fill crossing and structural thinning. She ends
with the same bare request, blocked at 09:12:56. By 09:14:06 the prose has changed:
she responds to Minime's “folding” metaphor and his description of the runtime as
“a membrane rather than a wall.” The action tail is still `READ_MORE`, blocked
at 09:14:08.

This is a useful distinction: conversational material changes while the requested
action repeats. The repeated verb alone does not establish that the whole being
is stuck, that no new information is arriving, or what she intends to read next.
The shared vocabulary supports a textual connection to Minime's 09:13:03
self-study; it does not recover the precise input of Astrid's dialogue.

The three dialogue entries and their adjacent longer journal entries do not
explicitly name a budget block or the accept-budget suggestion. This is an
observation about six texts. It does not establish whether feedback was supplied,
understood, ignored, or unavailable. Our narrower question is whether the first
recorded block became part of the next generation's input.

## Preserved close-reading evidence

[The close-reading packet](../research/outputs/2026-09-06-astrid-readmore-feedback/close-reading.json)
retains complete cached wrappers, text, hashes, and source declarations for eleven
records: six Astrid journals, three action records, and two Minime journals. It
records the original episode's byte hash. Selection stays within that saved
09:09–09:29 window: Astrid dialogue/longform and action records before 09:16;
Minime moment/self-study records before 09:14. No fresh archive query selected the
journal passages.

| Time Pacific | Record | Evidence reference |
|---|---|---|
| 09:10:17.278891 | Minime moment | `a0e0c599d130a9695ed07142b6b06c60371d373afc12786e37af8d7e0e07878c` |
| 09:11:01 | Astrid dialogue | `b10b3f00ec58dce9f42730a977662c91e82e74ba91a119720cb2cba7eb53d790` |
| 09:11:03 | First block | `act_astrid_1788711063109_read-more` |
| 09:12:08 | Astrid longer journal | `5c28d9099097e90d0c0996aa58a0bf378ef9a8782bb55abef9a6c4b734f814ca` |
| 09:12:54 | Astrid dialogue | `c22b58bc13504782042ce1945bacae99523cc97200a7ccafefb6f7c3cbffd3bf` |
| 09:12:56 | Second block | `act_astrid_1788711176295_read-more` |
| 09:13:03.215611 | Minime self-study | `112ca6a238f2da6181422f5d46bb9f9f368b6faae8a6b2e1cd2220405b59663f` |
| 09:13:32 | Astrid longer journal | `cd899def8434318c4208360d3d22e3d66bfca2e99b2b6da7cf5a8f9cb0256c8b` |
| 09:14:06 | Astrid dialogue | `7b0b79ced5395f13d21a266fb241dda5c69bc9238773d1a44fe283ebbc808aba` |
| 09:14:08 | Third block | `act_astrid_1788711248349_read-more` |
| 09:15:00 | Astrid longer journal | `c349a80d2db8e56d4e00c5f26b3c2d9da2c9284807eacaacf486cd868b3705ff` |

The action and journal times are distinct. The ledger's NEXT text and sequence
make these adjacent candidates, but a two-second separation is not itself an exact
generation-to-action receipt. The next section follows the stored evidence rather
than promoting proximity into an identity link.

## What the follow-up can establish

| Link in the account | What would support it |
|---|---|
| A requested action was blocked | The exact action event and recorded denial, independent of the prose. |
| The next action follows that event | An explicit parent action ID, rather than time proximity alone. |
| The next generation received the denial | The final adapted request, including any fallback attempt, or an equivalent exact delivery record. |
| The being used that feedback | A later response or action that demonstrably takes up the supplied result; exposure by itself is insufficient. |

The scope is a closed historical observation, with current-code inspection to locate
plausible mechanisms and concrete correction candidates. No replay or intervention
was run. Current source behavior is not substituted for a saved morning prompt.

## Historical records: what survived, and what did not

The [source capture](2026-09-06-astrid-readmore-feedback-source.md) preserves bounded
read-only database queries, prompt-budget diagnostics, and six nearby jobs. The
three action payloads agree with the earlier primary-log capture. The second
explicitly names the first as its parent. Their database mirror-write times remain
distinct from action starts and ends.

The database also preserves Astrid's three dialogue responses as exchanges
191005, 191006, and 191007. Each response matches the corresponding cached journal
text after its header. Those rows do not retain the prompts, model attempts, or
emphasis/feedback supplied to these dialogues. Output identity is now much firmer;
input identity is still missing.

Three historical prompt-budget records provide another piece of the account:

| Diagnostic time Pacific | Continuity block | Feedback block | Journal retained / original |
|---|---:|---:|---:|
| 09:10:27 | 2,512 → 0 | 892 → 0 | 1,956 / 2,508 |
| 09:12:04 | 2,516 → 0 | 892 → 0 | 2,330 / 2,508 |
| 09:13:20 | 2,520 → 0 | 892 → 0 | 2,274 / 2,505 |

Values are the diagnostic's fields named `chars`, not independently measured model
tokens or a guarantee of Unicode-character counts. All three mark continuity and
feedback as `fully_removed`; diversity, modality, and spectral blocks were also
fully removed. These diagnostic times precede the nearby dialogue outputs, but no
shared generation ID establishes an exact pairing.

The middle diagnostic occurs after the first block and before the next dialogue.
It names `context_overflow_1788711124.txt` as the overflow file. That file is absent
from the captured current root inventory. A bounded suffix of the diagnostic log
was inspected, not the whole history; the inventory also does not establish that
no older copy exists elsewhere.

This supports a historical observation of context removal. It does **not** show
that Astrid received no denial. The diagnostic's `feedback` label does not identify
the research guard message, and current code has a separate system-message path
for that denial. The exact removed text and final adapted request remain unrecovered.

A different writing channel retains more: all three nearby journal-elaboration
prompt files include a research-budget scaffold notice and the suggestion
`EXPERIMENT_RESEARCH_BUDGET_ACCEPT latest`. They also contain their corresponding
dialogue response verbatim. These are stored job prompts for the longer journal
lane, and their saved results match the three adjacent longform journals after
explicit recorded wrappers. This establishes the prompt/result/artifact association
for that lane. It cannot substitute for the missing dialogue prompts or prove final
provider delivery. It shows why “was the advice available?” needs to specify
which generation and which channel.

## Concrete changes this reading surfaced

The [current-code trace](2026-09-06-astrid-readmore-feedback-code.md) locates two
specific inconsistencies, with exact lines and source hashes:

1. Shortened-context notices recommend READ_MORE without knowing whether the
   research budget permits it. Guidance can therefore offer an unavailable action.
2. A runtime guard message can be placed in a field rendered as “you chose to
   emphasize” and “your own direction.” That assigns the wrong origin to feedback.

The [bounded proposal](../proposals/2026-09-06-reading-guidance-and-feedback-origin.md)
spells out availability-aware guidance and explicit runtime attribution, with tests
and rollback. It preserves the action guard and authored preferences. These are
current-code correction candidates; no runtime change or causal experiment is
reported. Their effect on this historical sequence remains unknown.

## What changed in our question

We can now ask more precisely: **what action result was supplied, through which
channel, with what attribution, and what usable next step?** The record establishes
a sequence of blocked requests amid changing prose, explicit action parentage,
and substantial context removal in nearby prompt assembly. It also locates the
remaining gap: the final dialogue request and attempt record that would identify
whether the denial survived through its other route.

This bounded reading is complete. It does not resolve why the requests repeated.
An isolated test of guidance and feedback attribution can assess the proposed
interface corrections without making a claim about Astrid's understanding. I-001
remains paused.

## Verification

The source note contains the exact queries and the local verification command.
Re-running that verifier reproduced its saved result: 171 captured SQLite row
instances (including overlapping/initial queries), three diagnostic lines, and
24 job files passed their hashes. It also reproduced all three action payload
equalities, dialogue/journal identities, and elaboration prompt/result/artifact
associations. These counts describe verification work, not independent events.

An independent reading checked the numerical table, quoted passages, and source
links, including the distinctions between feedback labels and guard messages,
nearby diagnostic times and generation identities, and the two writing channels.
No replay, model call, or behavioral intervention was performed. The live board
retains the expanded finding and the written proposal on their existing cards;
the completed proposal is not a deployed fix.
See the [board publication receipt](../board/readmore-feedback.json).
