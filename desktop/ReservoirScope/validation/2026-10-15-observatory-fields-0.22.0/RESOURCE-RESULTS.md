# Observatory 0.22: short main-process resource results

The bounded capture completed with 121 usable samples and no recorded collection errors. It describes four short, operator-declared windows of the exact macOS 0.22 app. It does not qualify total application or GPU performance. The independent arithmetic and identity review is in [FINAL-RESOURCE-REVIEW.md](FINAL-RESOURCE-REVIEW.md).

The [raw capture](main-process-samples-01.jsonl) targets main PID **74000**, with executable SHA-256 `788b636ec898f9863e146e7dfe67c380910ae38943b0b178f6e22b8e8d794051`. The header is dated **2026-10-15 21:57:54.879034 UTC** and the completed footer **22:07:54.889205 UTC**. Header-to-footer monotonic elapsed time is **600.014794792 seconds**; the first-to-last sample span is **599.999199083 seconds**. The last sample was taken **600.000141167 seconds** after the capture's monotonic origin; final hashing/footer bookkeeping accounts for the remaining duration. This is a nominal ten-minute capture, not four ten-minute windows.

## Closed windows and measured coverage

The [prospective freeze](measurement-freeze-01.json) and [protocol](RESOURCE-PROTOCOL.md) specified five-second sampling, at least 15 seconds of settling, and four windows of at least 60 seconds. The [monotonic markers](resource-markers-01.jsonl) show respective immediately preceding settling intervals of **27.111, 27.145, 26.098 and 31.218 seconds**. Each named window was closed before the next UI inspection or transition.

CPU below is duration-weighted cumulative task CPU time divided by the eligible monotonic intervals: **100% means one CPU core**. CPU intervals must start and end inside the same closed window and be at most 7.5 seconds. RSS is a point-sampled distribution, with **1 MiB = 1,048,576 bytes**. Values are rounded here; the [analysis JSON](main-process-analysis-01.json) preserves the unrounded values.

| Operator-declared phase | Declared / CPU-covered seconds | CPU, weighted % | RSS median [minimum, maximum], MiB | Metric samples / CPU intervals |
|---|---:|---:|---:|---:|
| Visible idle, paused | 84.494 / 80.067 | 0.004507 | 119.359 [118.781, 119.391] | 17 / 16 |
| Visible playback, 4 rows/s control setting | 69.535 / 60.045 | 3.040869 | 119.484 [119.422, 119.562] | 13 / 12 |
| Minimized | 71.163 / 65.047 | 0.002465 | 105.750 [94.578, 106.547] | 14 / 13 |
| Restored idle, paused | 64.696 / 60.045 | 0.002853 | 97.906 [95.219, 98.375] | 13 / 12 |

The four declared windows total **289.887441251 seconds**; **53 CPU intervals cover 265.203332291 seconds**. Their point statistics use 57 of the 121 capture samples. Samples during settling, UI transitions, and the tail after the final marker remain in the raw file but are outside the named phase summaries. Boundary-crossing CPU intervals were excluded, rather than assigned to whichever phase contained the endpoint. Every phase still has at least 60 seconds of fully contained CPU coverage.

No process sample or descriptor reading is missing, no raw sample/footer error is recorded, and all 121 samples record verified identity. Sequence numbers are continuous, 0–120. Consecutive sample intervals range from **4.544579792 to 5.005165750 seconds**, with the shorter final interval ending at the duration bound. All 121 descriptor counts are **13**. Thread counts within the four windows are respectively **20–22, 22, 20–21 and 20–21**. The first sample has no CPU interval because it establishes the cumulative counter origin; that is not a missing process sample.

## UI witnesses and qualification limit

The [UI witness receipt](resource-ui-witnesses-01.json) reports a **1280 × 860** window with the **PC1 residual** field, **PC2 / PC3** trajectory, WebGL2, and the same scroll position. Only part of the surface/trajectory and the upper spectrum were visible. Idle row 0/draw count 1 was unchanged across the visible-idle window. Restored row 603/draw count 605 was unchanged across the restored-idle window.

The protocol requested exact settled playback start/end rows. Those rows were **not recorded synchronously with the phase markers**, to avoid inspecting the UI during the settled interval. The available witnesses are pre-settle AX row **25 / 26 draws**, a subsequent nonsimultaneous screenshot showing **49 draws**, and after the playback window closed, row **586 / 587 draws**. Restore inspection showed row **603 / 605 draws**, paused. These witnesses include settling and transition work. They do not establish an exact settled-window row count, rows/second, FPS, zero hidden draws, or GPU activity. This is an explicit limitation of the planned row-boundary qualification; the process samples and phase coverage remain usable.

The operator reports **zero UI queries while minimized**. Visibility handling intentionally pauses recorded playback, and restore inspection found it paused. Minimized and visible-playback phases therefore represent different workloads. Draw counters count submissions for a renderer instance, not presented frames or GPU time. The [native UI account](MACOS-UI.md) contains the functional evidence; the original tool-interruption undercount is preserved with a separate [reporting correction](ui-functional-correction-01.json), recording two refreshed-state requests.

## Interpretation limits

Playback had higher main-process CPU in this one capture than the three paused windows. The RSS medians decreased later in the sequence; this short, ordered observation does not identify a mechanism, establish a leak or its absence, or compare 0.22 against another version. There was no randomized repetition, prospective performance threshold, or total-process accounting.

The sampler excludes separate WebKit/render/GPU processes and model processes. It measures no GPU utilization, energy, temperature, frame latency, total app memory/CPU, or responsiveness. The operator discloses no builds, tests, or real-model work during capture, but small receipt/document work did occur; this was not a measured quiet-host energy experiment. There is no new real-model, long-run reliability, minimum-hardware, Windows/Linux, or accessibility qualification in these measurements.
