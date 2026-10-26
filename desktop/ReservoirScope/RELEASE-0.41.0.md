# 0.41.0 · keep the same journal going

October 25, 2026. Local development checkpoint on `codex/s021-walkthrough`.

A short first session can now grow into a longer one. In **My reservoir**, pause
if running, open **Extend session limits**, choose **Add 1 hour** or edit the new
totals, save, then explicitly Resume. A session held at a run limit can be extended
too. The hour shortcut raises time, step and writing-attempt capacity together.
Near the duration ceiling it offers **Extend to 24 hours** instead.

The [first-session guide](GETTING-STARTED.md) covers the short invitation and this
continuation path. The clearer README, complete source setup and Plain journal
choice from [0.40.1](RELEASE-0.40.1.md) remain in place.

## What is retained

An extension preserves the session's seed, numerical state, earlier writing,
elapsed time and original configuration. Each accepted change is recorded in the
replayed event history and matching manifest receipt. The UI displays the effective
limits while leaving original settings available in session details.

Totals only increase, within the existing ceilings of 24 hours, 10,000 writing
attempts and 1,000,000 numerical steps. Storage keeps its original budget.
In-flight work, unsaved failures and storage holds must be resolved first.
A prepared, durably saved writing boundary survives the extension unchanged.
Saving alone starts no worker or model request; a duration-only increase may still
leave another limit holding the session, which the UI explains.

The backend checks the session identity, generation and revision, prepares the
change separately, and publishes it before granting a larger running budget.
Verification checks the receipt against its event and the original genesis.
Existing records without extensions retain their serialized form. Readers before
0.41.0 do not support the new extension evidence.

## Verification

| Check | Result |
|---|---|
| Frontend suite | 527 tests passed across 63 files. |
| Core Rust suite | 276 tests passed; doc tests passed. |
| Desktop Rust suite | 268 passed; 3 opt-in research investigations ignored. |
| Latest extension-focused Rust run | 7 passed, including the command-permission check added after the full suite compiled. |
| Formatting, TypeScript and production frontend build | Passed; existing bundle-size advisory remains. |
| Native macOS debug app | Built and ad-hoc signed, with the separate preview identity. |
| Source/setup and implementation review | Completed; identified issues corrected. |

The native UI check used **Offline example writing**, with one initial attempt,
100 steps and a one-minute limit. It held at step 3 after one saved/applied entry.
Add 1 hour saved limits of 3,700 steps, 1,801 attempts and 3,660 seconds, without
starting execution. Explicit Resume continued the same session to six saved/applied
entries at step 13; Pause stopped it there.

Native export produced a verified 38-file bundle. After normal quit and relaunch,
Find saved sessions → Verify and inspect → Restore paused recovered all six entries,
step 13, the extended limits and one recorded extension. Generation advanced from
1 to 2 while the original configuration and elapsed time were retained. No model
request was made. The separate S-021 packet's hash remained unchanged.

Private local screenshots, export and receipt are in
`research/outputs/session-extension-20261025/` (ignored). The setup helper's fresh
asset download/reuse check is recorded with [0.40.1](RELEASE-0.40.1.md).

This checks continuation and recovery, not hours of endurance or a first install
on another machine. The current build remains a development preview, separate
from 0.27.0 candidate 04 and the frozen 0.39.0 instrument. No new study, live-system
change or publication is part of this checkpoint.
