# Context order, first bounded diagnostic

Prospective plan, October 14, 2026. Subject: Reservoir Scope’s standalone local writing context. This is an app-side investigation selected by the steward; no Being, live workspace, shared model endpoint or production prompt is altered.

## Question and alternatives

Does exchanging the positions of the optional readout and preceding journal change how the next response carries forward imagery and composition in these retained contexts?

The [retained-context audit](RETAINED-CONTEXT-AUDIT.md) separates technical scaffold adoption in v7 from an authored composition carried through v8. Both sequences are already known. They motivated this question and are not held-out evidence. Moving the readout later could increase its prominence; moving prior prose earlier could weaken immediate imitation. The same composition could persist, or differences could be mixed and local. No desired writing style, subject, novelty or emotional tone is specified.

## Fixed material and contrast

Use steps 60, 120, 180, 240, 300 and 360: every second observation of the one completed twelve-entry v8 episode. Each prompt contains the full immediately preceding applied journal. This systematic anchor rule is selected before generating new responses, with historical outcomes known.

- **A:** the exact original v8 prompt from the passing, pinned export check.
- **B:** the same prompt with the entire OPTIONAL READOUT and PREVIOUS JOURNAL outer blocks exchanged. Their leading blank lines travel with each block. Prefix, session context, readout payload, decoded prior writing, late writing boundary and final invitation remain byte-identical.

The transform identifies LF-delimited outer headings. Headings occurring inside JSON-quoted memory remain escaped content. [Preparation](prepare_inputs.py), [tests](test_prepare_inputs.py), and [transformation receipt](transformation-checks-01.json) check this explicitly. Equal UTF-8 byte length is not a claim of equal tokenization or processing.

B is a diagnostic artifact, not a valid new production-v8 replay record, even though the copied header retains its original version label. The context describes the original session’s clocks and history. These fresh outputs are standalone responses: no numerical advance, journal publication, feedback, experiment record, app session or subsequent context is created from them.

Generate fresh A and B once per anchor, in this fixed order: 60 AB, 120 BA, 180 AB, 240 BA, 300 AB, 360 BA. The original saved response is a known reference; the comparison is between fresh A and fresh B. No output becomes another request’s memory. Alternation limits one simple ordering imbalance but does not remove cache/runtime drift.

## Bounds and transport

[run-plan.json](run-plan.json) and [frozen-inputs.json](frozen-inputs.json) own exact identities and request order. Reuse the selected private gemma3:4b material and independently checked Ollama 0.40.4 overlay. The supervisor is copied unchanged from the closed v8 episode. It creates one new owned process group and a fresh loopback port; no default endpoint discovery, download or shared service is used.

Before launch, freeze protocols, scripts, source records and prepared inputs. Make exactly one passive host admission: normal pressure level 1, system-wide memory-free reading at least 35%, and at least 8 GiB free disk. Refusal closes this attempt with all request slots unstarted; it authorizes no retry, cleanup of other applications, memory purge or model unload.

One inventory request (five-second deadline) must identify the exact selected model and digest. Then at most twelve POST requests, with the app’s single-user-message body: 8,192 context tokens, 1,024 maximum output tokens, temperature zero, no structured format, extra seed or additional chat history. Preserve exact request bytes, bounded raw responses and provider bookkeeping separately from interpretation.

Each request has a total 180-second deadline and a one-MiB response limit. The probe lasts at most 900 seconds, including readiness; do not dispatch a request unless its full 180 seconds remain. Persist at most 64 MiB. The owned service has a 1,200-second lifetime, with at least 1,140 seconds remaining at probe start. The stricter remaining-budget gate may leave slots unstarted even after otherwise successful responses.

No redirects, proxies, retries, replacements, skips or extensions. Stop on the first failed or incomplete generation. Retain partial bytes and all twelve slot outcomes. App completion semantics are checked independently of factual or literary assessment. Stop only the verified owned service through its supervisor; preserve its logs and cleanup receipt.

## Reading and finish line

Follow [READING-PROTOCOL.md](READING-PROTOCOL.md). First read a shuffled, condition-masked pack with full response text and opaque labels, preserving notes before unmasking. Source/condition blindness is limited: reviewers know the historical texts and design, and responses may reveal their source. Then inspect each exact prompt and predecessor, account for concrete factual claims, and compare within each anchor. Repetition can be continuity; changing images need not mean better writing. No mechanical creativity score or prose gate is introduced.

Complete this diagnostic when all planned slots have a preserved terminal or unstarted outcome, owned-process cleanup is recorded, first-reading notes are fixed, source-grounded comparisons are written, and roadmap/parity status reflects the executed scope. An admission refusal or incomplete request can complete the bounded attempt without answering the writing question.

Six paired contexts from one dependent historical episode are not six independent episodes. One response per condition gives no repeated estimate of model variance. This contrast jointly changes prose and readout positions: it cannot isolate attention, recency or comprehension, and establishes neither long-run diversity nor an improvement to the reservoir loop. It is not packaged-app, platform, GPU or numerical-feedback qualification. Production v8 remains unchanged; any later prompt version needs its own decision and qualification.
