# Browser fixture observations — 2026-10-13

The root agent exercised the My reservoir experience in the Codex in-app browser using an owned Vite preview. This report transcribes those observed checks and records their fixture scope. It is **not a native Tauri app check** or a claim of actual journal persistence.

## Fixture identity and lifetime

- Entry: [reading-preview.html](reading-preview.html), loading [reading-preview.tsx](reading-preview.tsx).
- Address during the check: `http://127.0.0.1:1438/validation/2026-10-13-reading-0.12.1/reading-preview.html`.
- Owned command: `node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 1438 --strictPort`; PID 70308.
- Start: **2026-10-13T18:16:59.981049Z**, recorded in [preview-start.json](preview-start.json).
- Browser tab closed first; the still-identified owned server was then stopped with SIGTERM at **2026-10-13T18:21:02.432561Z**, recorded in [preview-closed.json](preview-closed.json).

The fixture imports the current frontend and an in-memory `reservoirFixture()` API. Its visible notice identifies simulated state and synthetic prose. Its scenario initialization and control callbacks operate on that fixture, not a Tauri backend, actual numerical engine, journal store or model. No native app activation or provider contact is part of these checks.

| Evidence file | SHA-256 |
| --- | --- |
| `reading-preview.html` | `6dbe45a26bb4ed17d9fc217c6fae67e3eca73b3cdf3511c30152798cc06c5338` |
| `reading-preview.tsx` | `43c6042ed1268368df769dad2c19f75ed0a3af8cd31a814547961fe0aee2be72` |
| `preview-start.json` | `908a4c76ad77aebcaaf22954032785b7e217f98fa5f54775576ec03e5e018a4b` |
| `preview-closed.json` | `b1e6d63c6a4d7032b8163d1ce6cc7d356b575d5f2a2ffc76b52ec74558e8a7c6` |

## Observed checks

| Area | Observed result | Scope of the evidence |
| --- | --- | --- |
| Initial setup | The visible defaults showed a 6-hour duration, 256 MiB storage and writing every 30 steps at a requested 1-second pace. Advanced settings was closed. | Browser layout and displayed configuration only. |
| Exact duration | Entering 0 hours, 1 minute and 1 second produced exactly 61 seconds. | Browser input behavior backed by the source conversion tests. |
| Invalid duration | Entering 60 in the seconds field was invalid and disabled Create. | No silent normalization to another duration was observed. The exhaustive valid-duration check is a separate source test. |
| Explicit creation | Clicking fixture Create prepared the session only. Start remained separate. | Mock controller behavior; no numerical run or network request was started by this action. |
| Independent reading | The reading scenario showed a selected journal from step 3 while current step was 90 and the header reported 3 saved journals. The complete synthetic prose was readable, with Evidence closed. | This demonstrates presentation of an independently selected earlier entry. It is not an observed multi-hour live arrival or real save/readback test. |
| Retained text | Synthetic journal prose displayed as inert text, with paragraph breaks preserved. | Visual observation plus source escaping tests; no separate browser exploit/security qualification is claimed. |
| Save failure | The fixture's storage error opened Writing and feedback review, exposed Retry durable save and Skip, and placed the header in an attention state. | Visibility and labeling were inspected. Successful retry, disk mutation, feedback application and backend failure recovery were not exercised. |

The running fixture explicitly supplied step 90, durable step 90, simulated time 30, three journals and three attempts. Its selected text was authored synthetic prose. The save-failure fixture explicitly supplied `storageBlocked`, a pending entry and retry/skip capabilities. These values were not measurements from the frozen packaged reliability run.

Screenshots were visually inspected inline in the computer-use tool results. **No screenshot artifacts were saved**, so this report does not link to or imply a retained image file.

## Relation to final source checks and the frozen run

The browser preview closed before the late reliability analysis window started at **18:21:05.920848Z**. Its lifetime remains concurrent host activity to disclose for any earlier window. The final source checks at **18:21:34.819000–18:21:39.229833Z** overlapped the late window and are separately recorded in [integrated-02-qualification.json](integrated-02-qualification.json).

The final integrated source checks passed 323 tests across 36 files and the type check. They include the subsequent attention-state color adjustment; that final visual adjustment was not rechecked in the browser. The earlier integrated-01 invocation failed only after discovering two retained backup test files, despite all 323 production tests passing; [README.md](README.md) retains the exact outcome and repair history.

The actual frozen 0.12.0 app was not replaced, rebuilt or driven for this browser pass. Its executable SHA-256 remained separately recorded as `f68a3752a628edf11ac6161a26e6979bb22dcf4c3ee1c63f10add2cea86ab40d`.

## Still unexecuted here

Native webview layout and input behavior, actual Tauri create/start/readiness IPC, model generation, durable journal publication, native export/close dialogs, retained-prefix recovery, minimized/offscreen GPU behavior, screen-reader use and other operating systems were not qualified by this browser fixture. Real save and application claims require their backend/package evidence. The next packaged check must identify its own final source and executable before using this report as a checklist.
