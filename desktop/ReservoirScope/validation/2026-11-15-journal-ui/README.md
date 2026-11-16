# Journal UI qualification

The synthetic preview imports the real My reservoir components and the existing
in-memory test controller. It has deliberately long entries and a delayed read
to expose replacement flicker. No model requests, native commands or persisted
sessions are used. Launch the normal Vite development server and open
`/validation/2026-11-15-journal-ui/preview.html`.

1. At 1280×860, append while following. The result should identify a new entry,
   unchanged page/reader offsets, and the same pane and article DOM nodes.
2. Scroll the entry with Page Down. Append again. The entry and both offsets
   should stay unchanged; Follow latest should show a new-entry count.
3. At 720×860, open Session controls, tab into it and press Escape. The panel
   should close and return focus. Check no horizontal page overflow.
4. Follow latest explicitly. It should load the newest entry at the pane's top.
5. Check the schedule is expanded initially, disclosures retain optional data,
   and icon buttons retain descriptive accessible names.

The completed checks and native preview are described in
[the release record](../../RELEASE-0.52.0.md). Detailed local logs and the copied
journal evidence remain private under `research/outputs/journal-ui-20261115/`.

## Identity and action follow-up

Open `actions.html` for the 0.53.0 follow-up. It uses synthetic prose and retained
native test receipts; its model/outcome selectors change only the displayed
fixture. Check all three model identities, unresolved and rejected results,
keyboard expansion of the action summary, original parameters and 720px layout.
The measurement-load button deliberately reports that a native app is needed;
unit tests cover native command arguments and matching against the saved fixture.
No model or store operation is performed. The [0.53.0 record](../../RELEASE-0.53.0.md)
owns these results.
