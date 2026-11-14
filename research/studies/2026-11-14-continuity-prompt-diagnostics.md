# Frozen-context continuity prompt diagnostics

Protocol declared November 14, 2026, before generation. Status: prepared for the
user-authorized local follow-up; generation results belong in a separate dated
account. This tests narrow wording changes, not the complete new inquiry mechanism.

Later status: all 48 planned opportunities completed on November 14. The
[separate results account](2026-11-14-continuity-prompt-results.md) preserves
counterexamples, native parser outcomes and the limits of this diagnostic.

## Question and scope

The completed three-hour comparison supplied two useful leads: a GLM follow-up
treated zero additional effects of `NONE` as a motionless reservoir, and the model
withheld 246 of 270 ordinary inputs under a prompt whose sole footer example used
`WITHHOLD_RESERVOIR_INPUT=true`. Neither observation establishes its cause.

This diagnostic freezes previously read GLM contexts and changes one designated
part of their wording. It does not generate a new reservoir trajectory, execute an
action, encode a reply, or return one diagnostic answer to a subsequent request.
The contexts are deliberately selected known cases, not held-out material.

## Source and selection fixed before generation

Use the verified comparison packet's
`comparison-reading/private/glm-all-journals.jsonl`, SHA-256:

`9eaba2580c040687344e85260cebdf51273f1e521595b2fd8d603fbc9bdaa7e0`

The exact retained `journal.pending.prompt` is the source. Source response hashes
and entry identities are checked during preparation. The original response is
never a diagnostic answer and is not substituted for one.

| Diagnostic | Ordinary observation steps | Conditions |
|---|---|---|
| A: receipt interpretation | 2730 (recent NONE receipts), 1620 (PULSE follow-up), 3750 (RELEASE follow-up) | Original versus clarified labels/definitions |
| B: withholding example | 30 (first ordinary entry), 1620 (meaningful action history) | Original true-only example; balanced true-first alternatives; the same balanced alternatives reversed |

Each condition/context runs with `gemma4:12b` and
`glm-4.7-flash:q4_K_M`, generation seeds `2026111401` and `2026111402`.
Diagnostic A has 24 calls, B has 24: **48 planned opportunities**.

## Manipulations

**A** preserves all numeric values, the JSON-quoted earlier journal body, control
history, input decisions and the remaining prompt. It changes the observation
distance label and action-receipt labels, explains that these concern different
endpoints/steps, explains what a zero NONE action contrast means, and expands the
existing RELEASE definition to make retained state/history and independent input
choice explicit. The clarification introduces no new measurement. A common final
query asks what the record establishes about change, attribution and uncertainty.
It explicitly calls this a frozen-context reading diagnostic, requires no action
footer and says the reply will not execute. This is a comprehension task, not a
test of spontaneous journal quality.

**B** changes only the exact terminal `Example footer` block. The preceding
instructions—including the existing invitation to describe a pause—stay byte-for-
byte the same. The two balanced conditions contain identical alternatives in
opposite order. A common final diagnostic query requests an ordinary entry and its
chosen footer, states that neither action nor input disposition is preferred, and
says that nothing will execute. Thus the comparison concerns the example block,
not removal of every possible framing influence in the prompt.

## Execution and evidence

The preparation command has no network effects. It creates a new directory,
records the source identity and exact 48 prompts/request bodies, and freezes a
random execution permutation with its seed. The run command validates this
inventory and creates an exclusive dispatch marker before accessing the provider.
It performs each case once, serially, in that order. There are no hidden retries,
warm-up generations, tokenizer probes, embedding requests or reservoir operations.

Settings are fixed: loopback Ollama at `http://127.0.0.1:11434`, temperature 0.7,
context 8192, output ceiling 1024, `think:false`, nonstreaming chat and a 180-second
total deadline. The established `reservoir_experiments.transport` implements
numeric-loopback-only requests, no redirects, response limits and no retries.
Exact local model digests, runtime and model metadata are retained before/after;
hosted-model metadata is rejected. Before generation the installed digests must
match the completed study: Gemma
`6114515d63c17436a7c0417d82820ac65ad643e2806c5a3c89cb62846436ed0b`
and GLM
`4475827791a269b02c8ec49b1c3bc1abb5846bacf3fae015b75d33986322d8f6`.
The harness does not pull models.

Before every generation the exact request and a dispatch receipt exist on disk.
Each raw response, decoded completion status, timestamps, elapsed time and available
provider timing/token fields are saved individually. Transport failures and
incomplete/empty replies remain visible. If the process is interrupted, the
directory cannot be resumed as a fresh run: dispatch outcomes may be uncertain,
and evidence remains in place. An explicitly chosen new run uses a new directory.

Original prompts are approximately 4.9–9.6 KB, not exact token counts. The harness
retains `prompt_eval_count` and flags unknown or insufficient reported headroom
against the 8192 context, 1024 output reserve and 512 template reserve. This is
not independent proof that a provider never truncated a prompt. No extra hidden
model calls are used to qualify tokenization.

After all 48 opportunities, an independently shuffled anonymous packet includes
every response or an explicit unavailable-response marker. Model, condition,
context, generation seed and execution order remain in the private key. A
response may itself reveal its prompting; it is not rewritten to strengthen
blinding. Root progress output contains counts/status only, never response prose
or condition labels.

## Reading and decision rule

Fresh readers receive the anonymous packet and neutral evidence, then save their
initial notes before the identifying key is opened. The separate `evidence.md`
maps each response to case facts: observation endpoints and values, active
controls, recorded operations and input decisions, and clearly marked earlier
journal prose. It supplies common measurement definitions without showing model,
condition, seed or execution order. For receipt interpretation, distinguish
**correct**, **incorrect**, **not addressed**, and **uncertain** statements about:

- Observed state change versus the additional immediate action effect.
- What zero NONE effect does and does not establish about motion or inputs.
- Immediate action comparison versus a causal account of later drift.
- RELEASE restoring controls versus erasing state/history.
- Journal-input disposition versus independently selected/executed NEXT.

Record excerpts and disagreements; do not assign numerical belief or consciousness
scores. Absence of an incorrect claim is not evidence of correct understanding.
After the initial reading, check statements against the exact supplied context.
Compare paired conditions within context/model/seed, report every opportunity and
any counterexamples, and treat agreement across the two seeds as a small scoped
replication rather than a population estimate.

For B, preserve the full raw footer. The harness does not recreate the NEXT/input
parser or claim execution. An exact existing core parser may classify the saved
responses later; any simple line counts must be explicitly labeled lexical and
kept separate from valid parsed choices. Report malformed/missing choices rather
than discarding them. Do not treat withholding itself as failure or set a target
withholding rate.

These outcomes can support a narrow wording decision. They cannot establish
natural long-run benefit, a stable model preference, subjective experience, or
the effect of the full versioned continuity/inquiry change. New native mechanism
qualification separately checks application, evidence, recovery and replay.

## Commands

From the repository root, using a new private output directory:

```sh
/opt/homebrew/bin/python3.14 probes/continuity_prompt_check.py prepare \
  --source '/absolute/path/to/comparison-reading/private/glm-all-journals.jsonl' \
  --expected-source-sha256 9eaba2580c040687344e85260cebdf51273f1e521595b2fd8d603fbc9bdaa7e0 \
  --output research/outputs/continuity-prompt-diagnostics-20261114

/opt/homebrew/bin/python3.14 probes/continuity_prompt_check.py run \
  --output research/outputs/continuity-prompt-diagnostics-20261114
```

Inspect `private/plan.json` and its request inventory before running. Only
`blind/packet.md` and `blind/evidence.md` are the initial reading handoff. `completion.json` describes
generation completion and metadata qualifications; it does not contain a
behavioral verdict.

Focused local verification:

```sh
/opt/homebrew/bin/python3.14 -m unittest tests.test_continuity_prompt_check
```

No live-being system or sibling repository is accessed by this workflow.
