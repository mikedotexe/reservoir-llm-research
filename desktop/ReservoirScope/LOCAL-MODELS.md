# Explicit local models: finite generation contract

Version 0.11 introduces optional local requests to existing finite teaching recipes.
It does not launch a model server, pull a model, discover a workspace or connect on
startup. Scripted and fixed-tape behavior remains available. The Beings' services,
prompts, journals and schedules are outside this feature and its testing.

This document's 256-token/60-second limits describe **finite experiments**.
My reservoir uses a separate [sustained writing budget](SUSTAINED-SESSIONS.md#bounded-room-for-writing):
new 0.14.0 sessions default to 1,024 output tokens and 180 seconds, while historical
sessions retain 256/60. This does not change finite records or their verification.

## Configuration and readiness

Endpoint and model fields start blank. Operational addresses must be HTTP, with an
explicit port 1–65535, and host `localhost`, `127.0.0.1` or `[::1]`. Only an optional
single trailing slash is accepted. Credentials, other paths, queries, fragments,
HTTPS and non-loopback hosts are rejected. `localhost` resolution is pinned to
loopback; proxy configuration is ignored. Existing historical endpoint readers are
unchanged: an inert record may retain a historical address that cannot be dispatched.

Explicit **Check local model** performs `GET /api/tags`, bounded by five seconds and
one MiB. It requires one matching model name and consistent supplied identity, using
exact UTF-8 equality. Aliases and canonically equivalent but differently encoded names
are not silently substituted. The result names the endpoint, model, optional digest,
operation and check time. Editing configuration or cancelling invalidates the result;
a late check cannot replace a new selection. An unavailable check is not an empty
successful inventory. Readiness does not promise capacity or successful generation.

## Eligible requests

Only original stages 3/4 and independent D–H, including matched component and D/D
observation comparisons, dispatch requests. Explore, stages 1/2, A–C, fixed tapes and
the field-only controller study cannot do so. Create and Reset validate and retain
configuration without connecting. The user starts Step, Run or a manual opportunity.

The backend reconstructs the exact prompt from retained observations. F/G/H first
reread the appropriate saved journal from their own storage. An owned worker sends
one nonstreaming `POST /api/chat` outside the numerical-session mutex. There are no
redirects, automatic retries, cookies, credentials, external navigation or substituted
providers. A returned model identity, when present, must exactly match the configured
name; mismatches become transport failures before the core accepts any reply. Historical
receipts still retain their original provider/configuration identities independently.

The total deadline is 60 seconds, including reading and decoding. Responses are
limited to one MiB by declared and actual body length. Cancellation drops the socket
future and does not wait for provider cooperation. Requests use 256 output tokens,
temperature zero, and the accepted context limit (UI default 4,096; range 512–32,768).
Actions request JSON; original stages request prose. The provider envelope must be
complete, not stopped by a length limit, and have a valid retained token count when
supplied. The existing 65,536-byte text and qualified codec/parser limits also apply.

## Clock, saving and recovery

The clock holds at each request boundary. Each result belongs to a session, generation,
operation, arm, opportunity and observed step; it can settle only once. Pause stops
numerical scheduling but permits the already dispatched response to settle. Stop
cancels the request and terminalizes the opportunity. A reset or explicit discard
invalidates all prior callbacks. A required paired peer can run while both clocks hold,
in the native request order. The finite scheduler pauses after a provider boundary.

An accepted WRITE is a pending journal, not a saved journal. Actual atomic publication
and exact readback must succeed before a saved receipt grants E–H feedback eligibility.
The next step records application. WAIT preserves the previous held feedback without
creating a journal. Failed, incomplete, cancelled and unqualified responses grant no
new eligibility. Export cannot turn a failure into a successful save.

Intent metadata, exact prepared prompt and accepted configuration are checkpointed
before network dispatch. Failed preparation publication prevents a request. The core
marks the request started immediately before transport handoff, with no disk operation
between them. A crash can therefore leave a prepared checkpoint even if dispatch began
later; this older metadata does not prove that no request occurred. Subsequent pause
or settlement checkpoints retain the newer status. Recovery never resends or resumes it.
Unqualified returned text remains
bounded local diagnostic evidence, separate from native-compatible portable receipts;
its original length/hash and any truncation are disclosed. It remains ineligible for
feedback. The last complete portable snapshot and its durable step are distinct from
the current unresolved boundary.

## Qualification and next boundary

Automated providers bind ephemeral loopback ports owned by the tests. Their replies
establish transport and persistence behavior, not real-model interoperability or
writing quality. Supplied-response records are independently verified by unchanged
Swift. Packaged walkthroughs and real-service checks have separate receipts.

The next tranche is an explicitly owned sustained session while the app is open or
minimized: a new versioned session manifest, bounded record segments, automatic durable
journal publication with the same save gate, retention/storage limits, readable journal
history, and Follow latest independent of historical reading. It must not inflate
historical recipe limits or imply that closed, sleeping or crashed applications keep
running. Long-duration, minimize/restore, storage-failure and recovery qualification
remain required before claiming sustained operation.
