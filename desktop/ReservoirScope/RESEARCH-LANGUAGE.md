# Everyday research language

This pass treats Reservoir Scope as a research tool people can use, rather than a
porting project they need to understand. The 0.22.1 pass changed interface copy and
presentation; 0.23 adds direct navigation and retained reading state, and 0.24
separates the history window from the selected journal while improving keyboard
reading and zoom. The 0.25 layout puts selected prose first and keeps current sensory
fill visible alongside session status. Production prompt v8, authored journals and
source records keep their exact text and behavior.

## Working conventions

- A workspace heading names the place: Guided tour, Library, Research cases,
  Geometry bookmarks, Observatory, My reservoir, Recording or New experiment.
  Avoid a second all-caps label repeating the same name or a slogan in its place.
- Controls describe the action: Resume, Retry save, Open history file, Export
  original file. Words such as explicit, durable, backend and boundary belong in
  technical explanations when they add necessary meaning.
- Show the source, save/application state, missing measurements and actionable
  failures alongside the work. Simplifying a label must not equate a received
  response with a saved journal, or a saved journal with applied feedback.
- Let prose and visualizations lead. Put request IDs, hashes, successful export
  details and graphics counters in closed disclosures. Keep full evidence available.
- Give concise help where a choice needs it. Keep version/platform qualification
  and file-dialog/reference-scene checks under About this app.
- Use synthetic/example labels for scripted material. Neither the user nor the
  numerical reservoir is described as authoring the model's journal.

## Applied examples

| Previous wording | Current wording |
| --- | --- |
| THE CROSS-PLATFORM LAB; global version · My reservoir badge | Reservoir Scope; About this app |
| From input to choice. | Guided tour |
| Questions, evidence, limits. | Research cases |
| Watch the reservoir change. | Observatory |
| Recording reader | Recording |
| Fresh experiments | New experiment |
| Journal durability boundary | Journal save pending |
| Journals and their return | Journal |
| Resume explicitly / Retry durable save | Resume / Retry save |
| Search metadata / Family / Recorded route | Search recordings / Experiment type / Recorded source |
| Choose a file. Keep it explicit. | File dialog checks, inside About |

Graphics frame counters remain available under Graphics diagnostics. Context loss,
fallback, zero references, signed scales and unavailable values remain near their
views. Exact original-file export behavior is unchanged.

The installed name **Reservoir Scope** (Reservoir Scope Tauri Preview before 0.39.0), the
separate application identity and stores, and the qualification status remain deliberate coexistence decisions.
Removing those would be a release/identity decision, not wording housekeeping.

## Navigation and remaining inspection work

The [0.25 journal-first pass](validation/2026-10-15-journal-first-0.25.0/README.md)
puts the complete selected entry and Earlier/Later before the history list. Live
visuals are adjacent on wide screens and follow reading on narrow screens; exact
coordinates remain in a closed disclosure. History, Follow latest, failures and
pending save/application states retain their behavior. Current sensory fill uses
the current frame, independently of the journal being read; missing values remain
unavailable, while actual zero is shown as zero.

[Getting started](GETTING-STARTED.md) connects compiling, selecting an installed
local Ollama model, Create and Start. Feedback is already included: successful
save/readback precedes encoded next-step input, and application precedes eligible
full-text memory. Offline example writing remains the initial selection. The local
address/model fields remain blank until entered; checking availability is separate
from generation.

Use **sensory fill (%)** for the smoothed active-mode estimate. A fill rate requires
a time derivative and is not supplied here. When regulation is enabled, the optional
explanation names its 68% target and 64–72% error deadband as controller settings,
not a demonstrated special state or guaranteed result. The 0.25 source checks pass
431 frontend tests, TypeScript/Vite and reference checks; Rust qualification is
reused from exact 0.24 inputs except version metadata, not rerun. The package build
passes. Its [native walkthrough](validation/2026-10-15-journal-first-0.25.0/MACOS-UI.md)
confirms Earlier/Later/Follow latest, current-versus-selected fill and readable
125%/200% zoom/reset at 1280 × 860. Three scripted journals first apply at steps
31/61/91, then the run holds at 91. Normal quit and offline replay preserve the
record. This adds no new real-model writing, pinned-arrival, native compact-window
or export/recovery qualification.

The [0.24 compact-reading tranche](validation/2026-10-15-compact-reading-0.24.0/README.md)
uses **Earlier/Later entry** for reading and **Older/Newer history** for the list
window. The selected journal keeps its chronological position when the list moves
or new writing arrives. **Refresh this page** preserves the accepted window;
**Follow latest** explicitly returns to the newest entry. A failed or stale read
keeps the current prose and gives an actionable error.

Evidence stays closed and exact. Its bounded text panels have distinct accessible
names and can receive keyboard focus. View's Zoom In, Zoom Out and Actual Size are
presentation controls, separate from experiment parameters. The
[native walkthrough](validation/2026-10-15-compact-reading-0.24.0/MACOS-UI.md)
confirms zoom/reset, skip-link focus and numerical-panel scrolling at the actual
1830 × 1050 window. A 36-journal scripted run qualifies pinning/refresh, both history
directions, the twenty-row boundary, outside-window Earlier, workspace return and
explicit Follow latest during arrivals. Failed resize gestures leave 900 × 700
and 720 × 600 open; broader accessibility and collaborator acceptance remain separate.
The same-build post-quit verifier confirms the scripted record unchanged; native
export/recovery dialogs were not repeated. These mechanical checks do not establish
writing quality or collaborator usability.

The [0.23 navigation tranche](validation/2026-10-15-navigation-0.23.0/README.md)
makes My reservoir the initial sixth destination, retaining the five original
research destinations. Preparation history lives once in Observatory, with a Library
shortcut. Selected reports, disclosures and subview scroll survive return; the
Library keeps result position for an unchanged query. Scoped native checks confirm
those returns and an older journal staying selected while another entry arrives.
Later entry then selects the new saved-and-applied journal. That 0.23 check was
limited to its two-entry scenario; the separate 0.24 account covers multi-page
navigation. Neither establishes broader accessibility or collaborator usability.

Setup now gives Create/Start guidance once beside Create. Source and limit summaries
remain visible, while detailed pace guidance stays in Advanced settings. The
save → apply → later memory distinction, pending failures and incomplete replies
remain explicit; removing duplicate empty-state text changes no execution behavior.

Exact source/clock distinctions are necessary. Some successful identity and
historical receipt summaries remain prominent; review these during real
read/inspect/export tasks and compact layouts rather than hiding scientific detail
indiscriminately. Broader accessibility and collaborator acceptance remain open.

No new test assertions were added just to freeze preferred wording. Existing
presentation assertions were updated while preserving their behavioral boundaries.
The [0.22.1 copy](validation/2026-10-15-research-language-0.22.1/README.md),
[0.23 navigation](validation/2026-10-15-navigation-0.23.0/README.md),
[0.24 compact-reading](validation/2026-10-15-compact-reading-0.24.0/README.md) and
[0.25 journal-first](validation/2026-10-15-journal-first-0.25.0/README.md) accounts
record the checks actually run and their limits. The 0.24 and 0.25 regression tests
cover reading behavior, keyboard evidence access, layout order and current-versus-selected
measurements. Collaborator usability acceptance remains separate from implementation
and agent inspection.
