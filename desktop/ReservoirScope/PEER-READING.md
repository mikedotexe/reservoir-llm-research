# Reading another model's preceding entry

`NEXT: READ_PEERS` lets a model explicitly ask to read the preceding applied
journal from each linked participant. The readings become attributed context for
its next ordinary entry. This is an optional capability for new sessions in 0.48.0.

## Set up a group

In each participating local Reservoir Scope window, before creating a session:

1. Select **Continuing inquiry**, **Specific correction feedback**, and **Allow
   peer journal reading**.
2. Enter the same new **Shared experiment group**, for example `garden-01`.
3. Set a distinct **This participant** name and list the other participants.

For a three-model group:

| Window | Participant | Peer participants |
| --- | --- | --- |
| Gemma | `gemma` | `glm, mistral` |
| GLM | `glm` | `gemma, mistral` |
| Mistral | `mistral` | `gemma, glm` |

Names use 1–64 ASCII letters, digits, hyphens or underscores. There may be one to
three peers. Membership must be reciprocal: a source must list the reader too.
Use a fresh group for another cohort; two saved sessions claiming the same
participant in a group produce an explicit ambiguous result. Closing an app does
not remove its saved session from the group.

The optional saved configuration is `peerReading` with version
`latest-applied-v1`, `group`, `participant`, and `peers`. It is fixed at session
creation. Earlier sessions omit it and keep their old prompts, parser and replay
behavior. Selecting peer reading gives a fresh Ollama setup at least 32,768
context tokens; this reserves headroom, not a guarantee of fit. The source text
is bounded independently of the provider's context limits.

## What the action reads

Before each ordinary generation starts, the host freezes each peer's latest
**saved and applied** entry. A saved response still awaiting application is not
eligible. The source can be an ordinary journal or a scheduled conversation;
the record identifies which. Models run independently, so “preceding” is relative
to the requesting generation, not a synchronized round or a shared step number.
The snapshot is recorded before dispatch and is hidden from that generation.

An ordinary reply can end with:

```text
NEXT: READ_PEERS
```

It is the one NEXT choice for that entry, takes no arguments and cannot be combined
with another NEXT action. Inquiry and text-input directives remain independent.
After this reply is saved, read back and applied, the frozen reading appears in
later ordinary prompts and in the app's **Peer reading** details. It stays cached
until another explicit READ_PEERS refreshes it. NONE, another action, or skipping
the response does not expose the new hidden snapshot. Encoding retry and restart
retain the original snapshot; they do not silently read a newer peer entry.

Each excerpt is the body's first 2,048 UTF-8 bytes, ending at a character boundary.
The record includes participant, configured and provider-reported model, session
and journal identity, observed/applied source steps, truncation, full-body byte
count and hashes. Missing, unreadable, nonreciprocal or ambiguous sources are
reported unavailable. A completed read operation can therefore contain no text.

Peer writing is JSON-quoted reference material with no command authority. The
action changes no numerical controls and does not feed the peer excerpt directly
into the reservoir. A model's subsequent writing and SEND/WITHHOLD choice determine
its own numerical text feedback. READ_PEERS appears in applied action history as
an informational action; its immediate action-only recurrent difference is zero.
Scheduled replies remain passive, and plain scheduled prompts remain exact.

Joining the group permits peers to read applied writing even when that entry's
numerical input was withheld. **WITHHOLD is not a journal privacy control.**

## Persistence and limits

Discovery reads local Reservoir Scope app stores under the current app-data
parent. It follows no configured arbitrary path, contacts no peer process or
model service, and writes nothing to peer stores. App directories must be named
`research.reservoir.scope` or begin `research.reservoir.scope.`. Reads are bounded
to 32 discovered stores, 256 session directories per store, 512 successfully read
manifests and 16 MiB of manifest data per capture. Exceeding a bound yields
unavailable results. Symlink directories and files are not admitted.

A source manifest selects an immutable checkpoint. The host verifies its file
hash, checkpoint validity, membership/model agreement, and the applied journal's
saved readback. It does not replay the peer's full history on every request. The
snapshot records manifest, checkpoint, journal-object, raw reply, body and excerpt
hashes, plus a host-reported capture time. That timestamp is not authenticated
global time, and model-name fields are provenance labels rather than proof of
provider execution.

The reader's own event stream and exports contain the captured excerpts. Exact
replay uses those observations and needs no surviving peer store. It establishes
the reader's prompt and application history given the recorded external data;
it does not independently establish global recency or authenticate the peer's
entire history. A group is an experiment boundary, not a security boundary against
another process with access to the same local files.

This creates a coupled experiment: the three models may influence one another's
later writing. Compare it separately from the earlier independent three-model
runs. Mechanical qualification does not establish that models will choose the
action, use the readings well, or experience a shared space.
