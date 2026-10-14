# macOS packaged UI observations — 2026-10-11

Agent-operated smoke checks through the native Computer Use accessibility and
screenshot interface. These observations are not human acceptance or parity
qualification. The host reported macOS **27.0.1**, Apple silicon (`aarch64`).
The application was built locally from this workspace and launched from:

`target/release/bundle/macos/Reservoir Scope Tauri Preview.app`

No model, live feed, or beings' service was contacted. File-dialog checks used
the bundled reference scene document and a generated copy in `target/qa/`.

## Initial package: detailed smoke check

Executable SHA-256:
`0959f0e0a545780ae6d1596ee02119673253a0e1b046c1cbd5384f300acfec83`

| Check | Observed result |
| --- | --- |
| Launch and IPC | Guided tour foundation opened. Both 32- and 128-coordinate reference scenes loaded through Rust. Build panel identified macOS / aarch64 and matching bundled resource hashes. |
| Rendering | Both WebGL2 surfaces displayed geometry, contours, legends, and selection markers. Inline screenshots captured the initial and scrolled surfaces. |
| Exact selection | Clicking coordinate 15 then pressing Right selected coordinate 16, displaying `0.23055394657602063`. Clicking the 32-node surface selected coordinate 11, displaying `0.5096707578294796`. |
| Linked camera | Right and Up on the focused 32-node canvas visibly changed both surfaces together. Both frame counts advanced. |
| Explicit fallback | Selecting table fallback removed both surfaces and exposed the fallback explanation. Clearing it recreated both WebGL2 surfaces; coordinate 11 remained selected. |
| Context recovery | Explicit loss and restoration were exercised separately on both surfaces. Values remained available during loss; geometry returned on restoration. **Defect found:** the restored canvas background became black. This prompted the clear-color correction checked separately below. |
| Workspaces | All five navigation destinations were exercised. Experiments, Research cases, Geometry bookmarks, and Observatory clearly stated they were not implemented. Returning to Guided tour retained the selection and file proof result. |
| Native Open cancellation | Cancel returned the explicit cancellation message and retained the previous result. The automation connection briefly reported a closed native pipe; rebinding showed the application still usable. This was not treated as an application crash. |
| Native Save cancellation | Cancel returned the explicit cancellation message and retained the previous result. |
| Export and reopen | Saved `référence-宇宙.json` in `target/qa/`, then reopened it through native Open. The filesystem represented the accented name in decomposed Unicode. Both operations reported 6,013 bytes and the same hash; an independent byte/hash check matched the bundled original. |
| Window layout | Screenshots observed 1280 × 860 and a native left-tiled 920 × 1050 window. The narrower layout retained readable surfaces and adapted coordinate grids. This does not qualify minimum size, multiple displays, or all scaling factors. |
| Close and relaunch | Closing the last window terminated `reservoir-scope-desktop` (targeted process lookup returned no match). Reopening through the native app interface produced a fresh, working foundation window. No headless surviving process was observed. |

Exported and original reference document SHA-256:
`616726ee8ec30827fe08690288f1a176e09b9497d83a24368d16fd4585026c59`

Screenshots were reviewed inline in the Computer Use tool responses. The tool
did not expose a documented local image export path; no image files are claimed
as retained evidence.

## Corrections and source checks

- `SurfaceView.tsx` reapplies `0x071018` after Three.js recreates renderer state
  during context restoration.
- `tauri.conf.json` aligns `devUrl` with Vite's `127.0.0.1:1420` listener and
  supplies a separate development CSP. The development policy permits React's
  inline refresh preamble and the loopback Vite HTTP/WebSocket endpoint. The
  production policy remains unchanged. This requirement was confirmed in the
  installed Tauri configuration schema, React Vite plugin HTML transform, and
  Vite WebSocket client; development mode was not launched during packaged QA.
- After these edits, `npm test` passed **10 tests across 2 files**, and
  `npm run build` passed TypeScript and the production Vite build. Vite emitted
  its chunk-size advisory for the combined Three.js/React bundle.

## Final package: focused regression

The final rebuild completed successfully. Its executable SHA-256 is:
`f17b7a4d6dcb2e7cc8841e69138108a6a7b98ce4282e8a73ef0fa30d60ebb533`

The production frontend build emitted `index-dMYzQkB8.js` after the clear-color
correction. The final launch attempt through Computer Use was blocked before
inspection because the host screen was locked. The tool reported:

> The Mac is locked and automatic unlock could not unlock it. Ask the user to unlock the Mac manually before continuing.

Final-package visual launch and context-restoration regression therefore remain
**unexecuted**. The earlier detailed checks above belong to the initial executable
and must not be represented as a full rerun on the final package. The source fix
has passed the frontend test/build checks above, but its visual result on the
final package has not been observed.

## Explicitly unexecuted

- VoiceOver/screen-reader acceptance and complete keyboard-only traversal.
- Explicit second-process single-instance check; the locked screen prevented
  establishing the final application session. Initial close/relaunch observations
  do not qualify this check.
- GPU/CPU timing, sustained memory, battery or power measurements.
- Minimum macOS 14, other Apple silicon hardware, display transitions, or
  comprehensive high-DPI/zoom qualification.
- Windows 11, Ubuntu 24.04, installer/signing/notarization, or clean-machine
  deployment acceptance.
- Full native feature parity, replay verification, Library import, engine,
  model, and live-feed behavior; these are later milestones.
- Human acceptance/sign-off.
