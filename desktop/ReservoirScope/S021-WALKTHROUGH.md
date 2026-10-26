# S-021 walkthrough

The **Study** tab opens with question → result → one paired example →
**Recalculate saved results**. The button recomputes the six action-count/cost
rows and the 12-pair changed-rule mean difference from saved prefixes and model
continuations. It makes no model calls. The study report, intervals, qualification
and qualitative readings remain in the [full account](../../analyses/2026-10-25-prefix-continuation.md).

Introduced in 0.40.0 and retained in development version 0.40.1. The frozen 0.39.0 research instrument and
0.27.0 sharing candidate retain their separate identities and status. This UI
check is not newcomer acceptance or a newly qualified sharing release.

## Include the saved data in a local build

The original study archive and its derived packet are private, ignored assets.
A source checkout alone shows the reported result and an explicit unavailable
message for the exact example/recalculation. Obtain the closed S-021 archive
through the research collaboration; no download or provider setup is required
to use a local package that already includes the packet.

From the repository root, with Python 3.12+:

```sh
python3 -B probes/stage_s021_walkthrough.py /absolute/path/to/prefix-continuation-20261025
cd desktop/ReservoirScope
npm ci
npm test -- src/studyReplay.test.tsx
npm run build
```

The staging script checks pinned design/score/closure hashes, then checks each
request, result and provider response against the saved evidence manifest. It
writes only `src/local-studies/s021.json` (about 95 KB). The source archive is
read-only. The app assembles exact prefix + continuation, rejects duplicate JSON
keys and missing/duplicate trial slots, and independently derives costs 0/4/1.
The calculation is in `src/studyReplay.ts`; reported comparison values are kept
separate from the staged raw inputs. The private-data test explicitly skips when
the packet is absent; the synthetic tests still run.

For native development, use the existing [build instructions](GETTING-STARTED.md).
Stage the packet before building. The resulting local package contains private
model text; it has not been authorized for publication. Rebuilding without the
packet produces the reported-result-only view.

The example is world 00, changed rule, seed7, correct/flipped conditions. Both
calls belong to the fixed reading sample. Its captions distinguish researcher
inputs, generated choices/accounts and simulated outcomes. No claim about
private introspection or the live Beings follows from this walkthrough.
