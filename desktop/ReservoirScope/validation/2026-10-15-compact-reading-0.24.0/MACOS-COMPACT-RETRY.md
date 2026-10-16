# Native compact-window retry — unchanged 0.24.0

October 15, 2026, Pacific. This is an additive agent UI check requested after the
earlier resize difficulty. It preserves [the original walkthrough](MACOS-UI.md)
and its receipts. No source, package, prompt or numerical contract changed.

**Result:** native sizing remains unresolved through automation. The fresh window
remained **1280 × 860** in whole-window screenshots. Enlarged-text reading and a
copied, exhausted session's paused restoration worked at that geometry. These
observations do not qualify the intended smaller physical windows.

## Identity and fixture

- [Plan](compact-window-plan-02.json), [launch](compact-window-launch-02.json),
  and [close/preservation check](compact-window-close-02.json).
- Exact existing 46-file 0.24.0 package; executable SHA-256
  `9546aa02c101016d50cc20363bae7721549a93257808bb0020e19f0563f59a38`.
- Owned PID **16834**, isolated Library at `target/qa/0.24-compact-window-ui02/library`.
  Launch 2026-10-16T00:55:36Z; absence checked at 00:59:57Z.
- Copied all 217 verified files of scripted session
  `sustained-1792110972477-1` from the original UI01 Library. The original remains
  unchanged. No new writing run, model service, Start or Resume occurred.
- The fixture initially omitted the store's ownership marker. Find saved sessions
  reported `No such file or directory (os error 2)`. The
  [fixture correction](compact-window-fixture-correction-02.json) records copying
  the exact verified 29-byte original marker into this isolated store. This was a
  fixture preparation error, not a failed scientific record or silent empty catalog.

## Resize attempts and measurement limits

Native CUA screenshots and accessibility were used, not a browser demonstration.
At initial geometry, corner drag `(1278,858) → (898,730)` and right-edge drag
`(1278,430) → (898,430)` had no effect. Raising/focusing the window did not resolve
it. The green-button native menu exposed Top Left, but activating it returned
`elementHasNoFrame`; selecting its parent did not resize the window. The menu was
dismissed through its exposed Cancel action. Further right-border drags at x1278
and x1279, and left-border drag `(0,430) → (380,430)`, left geometry unchanged.

The initial and later 125% screenshots were independently read as JPEG SOF
dimensions **1280 × 860**. An initial attempt to interpret JPEG bytes as a PNG
header produced nonsense dimensions and was discarded. All displayed screenshots
throughout this check retained the same outer dimensions. Screenshots and AX
observations are in the task tool transcript; no separate screenshot files were
saved in this folder.

The configured minimum 720 × 600 is a logical **content-area** size. Pinned Tauri
uses `with_min_inner_size`; Tao's macOS implementation adds the frame/titlebar when
setting the native minimum. The targets are therefore content 900 × 700 and
720 × 600, with outer geometry and display scaling to be recorded separately.
Neither content target was achieved or measured here. Zoom changes rendered size;
it does not establish the requested native dimensions or a measured CSS viewport.

## Observed reading and controls

1. Four Cmd+Shift+= actions visibly enlarged the interface to requested 200%.
   Setup text wrapped, and normal scrolling reached Create my reservoir and Saved
   sessions and recovery. Navigation remained reachable. No creation was requested.
2. After correcting the fixture marker, Find saved sessions listed one exhausted
   session. Verify and inspect showed **361 verified steps, 36 journals, 179
   segments and 13,391,013 bytes**. Restore paused showed Paused, live/saved step
   361, 36 journals, and a **disabled Resume** control at the exhausted step bound.
3. At 200%, Earlier entry changed Journal 36 / step 360 to **Journal 35 / step
   350**, with first application step 351. Normal scrolling showed its complete
   scripted prose and closed Recorded measurements and Evidence disclosures.
   History and Earlier/Later controls were readable. This adds no model-voice or
   new-arrival claim; the original live-arrival check remains separate.
4. Experiments → Library displayed 22 included entries and the explicit incomplete
   managed-scan diagnostic for the fresh Library. Recording controls and Details
   were reachable. The selected metadata appeared as readable stacked label/value
   pairs, including filename, format and identity. This was not an import test.
5. Observatory opened included recordings. Next row changed 0 to **1**, with
   retained elapsed time **2.35556412 seconds** and fill **69.72500086%**. Previous,
   Play, Next, row input, speed and position controls fit the observed enlarged
   layout. Playback was not started. At 125%, the fill/selected-sample layout was
   readable and the fill sphere rendered; this is not a graphics-performance test.
6. Cmd+0 restored Actual Size, one Cmd+Shift+= visibly reached 125%, and a final
   Cmd+0 restored Actual Size. These are requested zoom settings with visible
   effects, not an independent native zoom-value readback.
7. Cmd+Q quit normally. No CUA observation followed quit. Receipt-bound `ps`
   confirmed PID 16834 absent. Both process logs were empty.

## Preservation and remaining work

The exact package, all previous validation files and all 217 original session files
remained unchanged. In the isolated copy, only `manifest.json` changed: generation
1 → 2, revision 543 → 544 and phase `budgetReached` → `paused`. All other manifest
fields and all 216 nonmanifest files stayed exact; no files were added or lost.
The restore did not increase steps, elapsed time, journals or segments.

Actual compact-window sizing, broader keyboard/screen-reader acceptance, GPU and
whole-app resource attribution, other platforms and collaborator acceptance remain
open. Export, new writing, sleep/wake, failed-save recovery and endurance were not
tested here. No new build or rerun of unchanged source suites was needed.
