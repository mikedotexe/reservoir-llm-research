# 0.53.0 · Run identity and entry action results

Local follow-up to the 0.52.0 journal-first preview, on
`codex/journal-desktop-ui`. Mike selected the first two proposed improvements:
identifying the model/run at a glance and connecting each entry to its recorded
action outcome. History filters, fill trends and navigation changes remain later
proposals.

## Run identity

The Journal heading carries the configured model, a stable family accent and a
short session identifier. Peer sessions also show their saved participant name.
Gemma, GLM and Mistral/Ministral have different accents; model text remains the
primary identifier. The short ID is a display abbreviation, not a provenance key.
The full session and generation remain in its tooltip and session evidence.
Restoring a session keeps the same abbreviation. No names or settings are written
back into the experiment.

## Entry action strip

Each entry shows the parsed NEXT choice, its scope and recorded outcome before
the prose. The strip distinguishes copied experiments, live inputs, state pulses,
control changes and peer-history capture. It distinguishes pending, skipped,
rejected, unchanged, measured, no-contrast, no-stimulus and unresolved outcomes.
Scheduled conversations say actions are off. Prose alone never establishes an
executed action; entries without a retained action record say so.

View result / View reason expands that entry's own receipt, exact action line and
parameters. Copied results can load matching measurements through the existing
passive saved-state command (`scan: false`, no operator question). Reports must
match the session/generation, result ID and originating step. The UI never uses
a newer report in place of the selected entry's result. When the bounded cache
no longer retains it, the receipt remains visible with an explicit message.
Real impulses retain the distinction between the observed immediate paired
effect and later copied forecasts. Reading an outcome performs no intervention.

The entry article remains mounted during journal updates; its action disclosure
resets only when the selected entry changes. Scrolling or interacting with the
entry continues to hold the selection. The fill diagram's zero label is also
moved to its radial origin.

## Qualification

- Frontend: 622 passed, one existing skip. Production TypeScript/Vite and the
  ad-hoc signed native bundle passed. No numerical or host contract changed.
- Synthetic interaction: model identity switches among Gemma, GLM and Ministral;
  rejection details open with the keyboard; unresolved results retain their own
  label. At 720 pixels, client and scroll widths both measured 705 pixels.
- Reading after keyboard scrolling had settled: appending an entry retained
  page scroll 131, reader scroll 420, pane top 139, and the same pane/article
  nodes and selected entry. Follow latest reported the new arrival.
- The matching-result tests use the retained native experiment fixture. They
  check an older result beside a newer one, cache eviction, wrong originating
  step, mismatched session/generation and passive command arguments.
- Native preserved-history verification and paused restoration passed: 31
  journals through step 930, generation 4. The entry at step 750 opened its own
  question-scan receipt and loaded its matching saved comparison at origin step
  751. The preview remains paused on that entry; no model request, operator scan
  or real intervention was started. The retained writing-attention boundary
  remains unresolved, as in the earlier preview.

Repeatable browser fixtures are in `validation/2026-11-15-journal-ui/`.
Private native-build receipts remain in `research/outputs/journal-ui-20261115/`.
The preview identifier is still `research.reservoir.scope.journal-preview`;
the three ongoing 0.51.0 experiments retain their binaries, stores and settings.
This is a local preview, not a published sharing release.
