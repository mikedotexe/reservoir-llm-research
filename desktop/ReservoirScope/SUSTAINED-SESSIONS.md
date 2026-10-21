# My reservoir: sustained session contract

This is the Tauri-first personal lab, introduced in `0.12.0`, extended with versioned open-ended journaling in `0.13.0`, explicit writing budgets in `0.14.0` and paired measurement context in `0.15.0`. It is a new scientific record family,
separate from the finite Essentials formats. Their limits, meanings and independent
Swift verifier remain unchanged. It is a reduced synthetic reservoir, not a copy of
Minime or Astrid, and it makes no claim of learning or benefit to a Being.

## Starting and reading

Choose **Experiments → My reservoir**, configure a seed, pace, observation cadence,
run budgets and either the explicit scripted demonstration or a loopback model.
Model endpoint and name must be supplied deliberately. Creating a session records
its genesis without contacting a model. Start begins the Rust-owned run. An inventory
check remains a separate explicit action and is not a guarantee of generation capacity.

The interface separates the recurrent state surface from the sensory field's reduced
fill. The live view and journal reader have independent selection: reading an older
entry does not rewind the engine or move when a new entry arrives. Follow latest is
explicit. Prompts, replies and journals render as inert text.

Only one lab may be admitted to active work at a time. Retain or reset unsaved finite
work before starting My reservoir; settle or stop the personal session before starting
another finite run. Opening a workspace starts neither computation nor networking.

## Numerical and observation version

`reservoir-and-sensory-v1` exposes all 32 signed recurrent coordinates in fixed index
order, recurrent RMS and L2 norm, and L2 change from the previous observation. The
first change is unavailable. It separately exposes the 32 descending sensory
eigenvalues, normalized spectral summaries and reduced active-mode fill. These are
retained numerical observations, independent of camera position and human selection.
Prompts use the existing qualified eight-decimal formatter, with explicit step and
simulated seconds. A numerical step represents one third of a simulated second;
the selected wall-clock pace is a separate quantity.

The mechanism retains seeded recurrent/input weights, current SplitMix64 noise
state, recurrent state, sensory projection identity and full covariance, fill
smoothing, current retention and controller integral. Optional retention regulation
uses the existing reduced controller. The seed never restarts at a storage boundary.
All authoritative values remain full-precision Rust values; display buffers are not
checkpoints. Full-width seed/configuration identities cross IPC as decimal strings.

At an opportunity, stepping holds while the last saved-and-applied journal is
physically reread, a prompt is prepared, and one bounded generation is completed.
The full latest eligible journal is the sole memory entry. Earlier entries remain
readable but are not silently concatenated into the prompt. The opportunity cadence is still configured by the user; this protocol does not yet
let the model choose WAIT/WRITE or its own timing. Historical action experiments retain their own choices.

The text codec reduces qualified textual features into 48 coordinates, of which 32
carry features and 16 remain zero. Sensory measurements shape that vector. It is
not a learned semantic embedding. A saved vector replaces the held feedback at the
recorded next numerical step and continues as input until replaced. It does not
train model weights or recurrent weights. Forcing, seeded noise and regulation also
contribute to change; pre/post observations do not isolate the effect of words.

Two numerical settings were added after the first laptop session (0.28.0). **Sensory
input noise amplitude** adds uniform noise to all 66 field inputs at every step; it is
separate from the seeded reservoir noise, never enters the recurrence, and is drawn
from a step-indexed SplitMix64 stream so checkpoints carry no extra RNG state. **Text
feedback scale** multiplies the held 48-coordinate vector as it enters both the
reservoir and the field; the stored held vector stays unscaled. Noise 0 with scale 1
is byte-for-byte the earlier mechanism `essentials32-splitmix64-codec48-held-feedback-v1`;
any other values identify the checkpoint as
`essentials32-splitmix64-codec48-scaled-feedback-field-noise-v2`. Historical
sessions omit the fields and replay unchanged. The fresh defaults are noise 0.5 and scale 0.4:
offline replay of the first recorded session showed that forcing plus one held text
vector spans about twelve of the field's 32 modes, so the controller stayed on its
0.995 rail near 14% fill, while these values settled fill near 70%, inside the 64–72%
band ([account](../../analyses/2026-10-21-laptop-first-sustained-session.md)).

**Writing temperature** (0.29.0) lives on the language configuration. Omitted, as in
every historical session, it means greedy decoding; a value in 0–2 is sent as the
provider's temperature together with a sampler seed derived from the session seed and
the attempt number (`sampling_seed` in the core), so entries differ from one another
yet a repeated attempt with the same prompt reproduces its text on the same model and
backend. The pending-language record carries the temperature and continuation
validation guards it; each journal object records the temperature and the seed it was
requested with. Finite experiments are unchanged and remain greedy. Fresh Ollama
sessions propose 0.7. Sampling changes which text the model emits, not what the
numerical loop does with it.

## Open-ended writing and prompt history

New sessions use `reservoir-journal-v8`: an ongoing journal invitation with no
human question to answer. The model chooses its topic and form, may continue or
revise prior writing, and need not name any metric. Current reservoir readings and
prior writing are context, not a checklist. Questions, expressive imagery and
ordinary observations are welcome. There is no mandatory heading, word count or
prescribed conclusion. The transport still bounds output tokens and generation time.

V5 places a compact optional readout before the full previous journal, then ends
with an invitation to write in whatever direction seems worth pursuing. It includes
RMS, separate sensory fill and coordinate distance; full vectors and all eight
measurement rows remain in Evidence. This is a versioned context refinement, not
evidence of better prose. See the [versioned writing contract](../../shared/reservoir-scope/continuing-writing.md).

V6 adds a brief action-scope clarification to the retained v5 context. Writing
supplies numerical feedback and eligible prose memory; describing a control change
or an experiment does not execute it or fetch a new reading during the reply.
The invitation remains open, and authored claims never become a factuality gate
for durable saving or feedback. Existing v1–v5 sessions retain their exact wording.

V7 places a short WRITING BOUNDARY after the previous journal and before the open
invitation. It states the held observation step and the actual previous entry's
first input step, or that no entry has yet been applied. There are no tools or
control commands in that turn. Describing a control change remains writing; saved
text returns through the existing automatic encoding. This version changes context
placement and clarity, not the available mechanism or a prose acceptance rule.
Historical v1–v6 sessions keep their exact prompts. A separate real-model reading
is required before claiming an effect on invented actions or writing quality.

V8 keeps that invitation, prior-text memory and writing boundary. It replaces only
the compact readout’s explanatory paragraph: RMS describes recurrent coordinate
magnitude, sensory fill is distinct from encoded text input, and coordinate distance
compares endpoints rather than path length, speed or the effect of writing. Comparing
interval distances needs a recorded value for each. No new measurements, mandatory
reporting format or prose-quality save gate are added; v1–v7 replay unchanged.
Mechanical qualification and any later real-model reading remain separate.

This supports the user's aim of leaving room for emergent behavior. It does not
establish that emergence occurred, or replicate Minime or Astrid's richer systems.
A prompt envelope still exists and the model is called at configured opportunities.
The latest saved-and-applied entry is carried verbatim as memory; older history is
available to the reader, not automatically retrieved by the model. Self-chosen
silence/timing and richer continuity require separately versioned future work.

The exact prompt version belongs to the immutable session specification, manifest
and checkpoint. Missing historical versions mean `reservoir-journal-v1`, preserving
its original prompt and serialized checkpoint bytes. `reservoir-journal-v2` preserves
the structured candidate prepared during the 0.13 tranche; it was superseded before any
real-model run. Existing sessions keep their version when restored; new defaults
never rewrite historical journals or prompts. Unknown versions are rejected.

V3–v6 separate JSON-quoted prior prose from current numerical readings. The prior
text remains fully recoverable, including newlines and Unicode. A repeated claim in
memory is not a measurement. When an entry makes a factual claim, its source and
precision can be reviewed; creative language, an unfinished thought, or omission of
metrics is not a failed journal. Quality review remains separate from numerical
verification, transport completeness and save/feedback eligibility. The app neither
rewrites prose to improve a score nor suppresses valid feedback based on editorial
judgment. Prompt versions and exact evidence are available inside the reader's
closed Evidence section.

## Recorded measurement reference

V4–v6 use `reservoir-and-sensory-v2`. It retains the same current measurements and a
fixed-size summary of the previous reached numerical observation: its step and
simulated time, recurrent RMS/L2, largest sensory covariance eigenvalue, reduced
sensory fill, top-eight head/shoulder/tail shares and normalized entropy. It does not
nest prior observations or grow a history inside each observation. V1–v3 continue
using their original observation version and serialization.

Rust constructs a compact table of current, previous and signed current-minus-prior
values. Percent-valued differences are percentage points. Recurrent coordinate
L2 distance is distinct from the difference in L2 norms. A previous observation may
have produced a failed or skipped writing opportunity; it is not necessarily the
observation associated with the latest saved-and-applied journal. Exact journal
memory retains its separate observed/applied identities. Whole-history verification
checks the numerical comparison against the replayed observations.

The first observation has no previous comparison. Legacy entries may name a prior
step without retaining the prior scalar summary; the reader reports that comparison
as unavailable. The new closed **Recorded measurements** panel belongs to the
selected entry, independently of the live state, and exposes the Rust-supplied table.
The full retained observation and exact prompt remain in **Evidence**.

Two endpoints establish net change, not an intervening trend, convergence, spatial
meaning or writing-only cause. The largest covariance eigenvalue is not a measured
tone or frequency. The invitation permits prose with no metrics at all. This
reference is neither an automatic truth assessment nor a journal eligibility gate;
any inaccurate writing remains retained evidence for separate review.

## Bounded room for writing

Fresh sessions retain an explicit `outputTokens` ceiling of 1,024 and a
`requestDeadlineSeconds` limit of 180. Advanced settings allow integer ceilings of
256–2,048 tokens and 60–180 seconds. Selecting a local model for a new session
starts with 8,192 context tokens. These are resource allowances, not instructions
about the entry's length or form. V1–v4 prompts remain frozen; v5 shortens the optional readout without assigning a writing format.

Each setting is fixed at creation and bound to genesis, pending requests and replay.
Missing historical settings mean the original 256 tokens / 60 seconds and serialize
without new legacy fields, preserving old checkpoint hashes. Recovery does not
upgrade an old budget. Finite experiments retain their own original limits.
Older app builds may reject bundles carrying the new explicit budget fields; they
must not silently reinterpret those records using their former hardcoded limits.

An explicit context size must exceed the output ceiling. This simple configuration
check does not prove that a provider tokenized or processed all supplied context.
The app retains the exact full latest applied journal, never truncating it to make a
request appear to fit. Longer context can cost more memory; actual capacity requires
an explicitly configured run. Temperature remains zero, the response bound remains
one MiB, and text/codec limits still apply. A length stop, over-budget reported token
count, timeout or incomplete response cannot become new journal feedback. No
automatic retry or silent increase in output, context or duration is performed.

## Durable boundary

Each session has an owned directory, immutable event segments and journal objects,
content-addressed continuation checkpoints, and a small atomically published
manifest. Scientific bytes are separate from any rebuildable Library metadata.
No historical source path is followed and neither native storage nor a Being's
workspace is discovered or migrated.

The owner follows these gates:

1. Persist the exact observation and prepared prompt with turn and attempt identity.
2. Retain dispatch and the bounded provider outcome. Unknown or interrupted dispatch
   never permits an automatic resend.
3. Publish and read back the exact journal object. A failed or uncertain save cannot
   grant feedback or prompt-memory eligibility.
4. Persist the saved journal identity, encoded features, shaped vector and intended
   next-step application. This is prepared feedback, not an applied receipt.
5. Authorize that committed preparation, advance once, and retain its first actual
   application with the numerical continuation. Pause alone does not skip feedback.

Segments have a bounded event outbox. Only a successful segment/checkpoint/manifest
publication acknowledges it. Checkpoints retain the complete continuation and pending
boundary. An application permission is ephemeral and must be reacquired from durable
evidence after restoration. Recovery verifies the genesis and ordered segment chain,
not just individual file hashes. Reading a recoverable session does not run it.

The new bundle is exported under its own version. An old Swift verifier is not
expected to accept this new protocol. The core's headless segment check certifies
numerical/event replay from the segment's declared checkpoint; whole-history
verification additionally needs the complete ordered chain back to genesis. Neither
check authenticates an external provider or proves historical physical disk durability.

## Budgets and lifecycle

Defaults target a modest paced run: 10,800 numerical steps, at most 360 prepared
attempts, an opportunity every 30 steps, one second between numerical steps, six
hours of permitted running time, and 256 MiB of storage. The first reached bound
stops new progress visibly. An already dispatched request may settle within its own
retained request deadline and be saved after the duration budget; its prepared feedback
stays unapplied while that budget is exhausted. Model latency adds wall time while
the numerical clock holds.
There is no new opportunity on the final permitted numerical step.

Each session grows only inside its displayed quota; running does not silently delete old
journals to make room. Retained sessions and explicitly exported copies occupy separate
space; this is a per-session limit rather than a global archive quota. The writer reserves space for transaction metadata and bounded
pending evidence. A save failure pauses with its candidate retained for explicit
retry. Request failure, cancellation, unsupported text and exhausted limits remain
visible; there is no provider substitution or unlimited automatic retry.

The Rust worker owns pacing. Navigation and minimization suspend unneeded rendering
without driving or stopping the run. On macOS, a scoped
[`NSActivityUserInitiatedAllowingIdleSystemSleep`](https://developer.apple.com/documentation/foundation/processinfo/activityoptions/userinitiatedallowingidlesystemsleep?language=objc)
activity identifies explicitly requested work to App Nap, while still allowing system
and display sleep. It ends when the worker ends; no login item or daemon is installed.

Actual macOS workspace sleep/wake notifications interrupt the session. They use
[`NSWorkspace`'s notification center](https://developer.apple.com/documentation/appkit/nsworkspace/willsleepnotification),
not window visibility. A conservative backend timing-gap check is additional
protection, not a claim that every platform's sleep behavior has been qualified.
Resume is explicit, and no missed wall-clock steps are simulated. Close and Quit
consult both lab owners; pending writes or unresolved evidence require review.
Checkpoint and quit can retain fully committed, still-unapplied feedback. Relaunch
exposes recovery without automatically running or resending a request; restoring
that checkpoint stays paused until an explicit Start applies it once.

## Qualification boundary

The implementation's tests, synthetic/fake-provider runs, actual packaged-app tasks,
real-model checks and human acceptance are separate evidence. The roadmap's multi-hour
and 24-hour soaks remain qualification goals until a receipt records those durations.
An accelerated numerical test is not a 24-hour run. Windows/Linux lifecycle, actual
system sleep/wake and measured GPU/power efficiency each require their own checks.
