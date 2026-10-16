# Packaged macOS compact-reading check — 0.24.0

Scoped agent inspection used native accessibility and screenshots, not a browser
demonstration. [Launch](ui-launch-01.json) binds PID **9390** and the exact 0.24.0
package to `target/qa/0.24-compact-reading-ui01/library`. The [plan](ui-plan-01.json)
was saved before session creation: scripted writing, seed 20260909, cadence 10,
maximum 361 steps / 40 attempts / 600 seconds / 64 MiB, requested pace 1,000 ms.
Other numerical and prompt defaults remained unchanged. No real provider was used.

## Observed behavior

1. Native window maximization produced an actual **1830 × 1050** screenshot.
   Border/titlebar/menu gestures did not establish the intended smaller dimensions.
   Optional manual assistance was requested; no successful manual resize was
   observed before close. The baseline 0.23 window was separately 900 × 860.
2. Advanced settings showed the planned limits. Create produced **Ready · not
   started**, live/saved step 0, with Start still explicit. Start began the session.
3. Cmd+Shift+= visibly enlarged the interface to the requested 125%; repeated
   shortcuts reached 200%. View → Zoom In also worked. Cmd+0 restored actual size;
   Cmd+minus reduced zoom again without changing the selected journal. These are
   observed changes in rendered size, not native zoom readback measurements.
4. At 100% and 200%, Library details showed a coherent label/value grid including
   the complete hash and source metadata. The viewport and controls remained
   scrollable at the observed window size.
5. At 200%, Tab reached Observatory’s Fill & state button with a visible focus ring.
   Eight Shift-Tabs reached **Skip to workspace**, visibly above the header and
   sticky navigation. Return activated its workspace anchor. This does not prove
   screen-reader behavior on each platform.
6. At live step 106, the step-20 entry was selected as **Journal 2 of 10**. New
   entries did not replace it. Evidence remained optional and initially closed.
   Three Tabs from its expanded summary reached the named **Numerical observation**
   region. Page Down scrolled its JSON contents while the document scroll position
   remained 0.6049877 and the same journal stayed selected. Its focus ring was visible.
7. Refresh at live step 173 retained the anchored step-100-through-step-10 history
   window and step-20 prose; its newest-first offsets adjusted to the newer total.
8. At live step 233, Newer history opened steps 230 through 40, a twenty-entry window.
   **Journal 2 of 23** and the step-20 prose remained; the UI explicitly said the
   selected entry was outside that history window. Earlier entry then opened step
   10 / Journal 1 at live step 242, proving navigation still worked from that selection.
9. Newer history opened steps 220 through 30. Selecting its final row showed
   **Journal 3 of 26**, step 30. Earlier entry crossed that twenty-row boundary and
   opened step 20 / Journal 2 at live step 273. A subsequent Newer/Older history pair
   preserved that choice and returned steps 40, 30, 20 and 10 with a boundary overlap.
10. Leaving for Observatory and using Go to My reservoir returned at live step 306
    to **Journal 2 of 30**, the same step-20 prose. The clock had continued.
11. Explicit Follow latest selected step 320 / **Journal 32 of 32** at live step 324.
    Later arrivals opened automatically. The session naturally held at **Run limit
    reached**, live/saved step **361**, **36 journals**, displayed running time
    **6 minutes 14 seconds**, latest entry step 360 and first application step 361.
12. Cmd+Q quit normally. A receipt-bound `ps` check found PID 9390 absent. No app
    observation followed that quit, avoiding the baseline tool’s relaunch behavior.

## Evidence boundaries

Session identity: `sustained-1792110972477-1`. The same-build replay receipt records
exact elapsed time, hashes, full configuration and file preservation separately.
The scripted prose is a deterministic UI fixture, not evidence about model voice.

The remaining native geometry checks are **900 × 700 and 720 × 600**, including
those sizes with enlarged text. No successful compact-height result is inferred
from source CSS or full-window zoom. Native export/recovery, sleep/wake, real-model
writing, GPU/power measurements, other OSes and human collaborator acceptance were
not executed by this walkthrough. Production v8 remains unchanged.

[Post-quit replay](ui-session-check-02.json) passed for all 36 journals and 179 segments, with 374162 ms retained active elapsed time. All 217 files (13391013 bytes) remained unchanged. The first wrapper attempt stopped before replay on the owner bookkeeping file; its receipt and original helper remain preserved. The corrected helper passed six discovery controls before this read-only retry.
