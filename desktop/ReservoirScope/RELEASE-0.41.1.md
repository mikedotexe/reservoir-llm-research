# 0.41.1 · open the journal folder

October 25, 2026.

**Open journal folder** now sits beside the Journal heading in **My reservoir**.
It opens the current session’s saved JSON files in Finder, File Explorer or the
Linux file manager. The folder is available as soon as the session is created,
including before its first entry. Opening it leaves execution and reading in place.
Failures appear beside the journals; repeated clicks wait for the pending open.

The Rust command takes a session identity and generation, resolves its owned
journal directory and uses [Tauri’s opener](https://v2.tauri.app/plugin/opener/).
It accepts no caller-supplied path or executable. Missing or linked directories
are rejected without recreating them. The session lock is released before the
file manager is launched. No general frontend opener permission is granted.

The README and [first-session guide](GETTING-STARTED.md) point out the shortcut.
Export remains the way to make a portable saved-session copy.

## Verification

- Frontend: 528 tests passed across 63 files, including pending-open behavior,
  failure reporting and ignoring a completion from a replaced session.
- Focused desktop Rust: four tests passed, covering the owned directory, unchanged
  session history, invalid identity/generation, missing paths and linked storage
  (including the existing journal-link regression).
- TypeScript, production frontend build and Rust formatting passed.
- Independent implementation review completed; the pending-open reading fix is included.

The native macOS debug app built successfully with the separate preview identity.
After restoring the existing offline example paused, clicking the new button opened
Finder at that session’s `journals` directory with all six JSON files visible.
The app stayed paused at step 13, with no additional writing. The manifest and all
six journal files were byte-identical before and after opening. Private screenshots
and the receipt are under `research/outputs/journal-folder-20261025/` (ignored).

Windows and Linux use the platform opener but were not run on this machine. This is
a source checkpoint, with no new study or live-system change.
