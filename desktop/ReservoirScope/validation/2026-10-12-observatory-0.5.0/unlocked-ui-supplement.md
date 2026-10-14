# Preview 0.5.0 — resumed packaged checks after unlock

October 12, 2026. The native control tool could open the app after the user requested
a retry. App/archive identities were independently rechecked: binary SHA-256
`283dc8060a944f6335f4675bcc82061dd2095fdb12d4763661c8846917512be9`, archive
`c1ac7a6f4123cdc683e401f79ea1d9e10fdf5f0e0af4ec72952597bdda7cf14b`;
all 41 files, modes and sizes matched the original receipt.

Observed in the actual packaged WebView:

- Observatory navigation showed an explicit Open bundled recordings action and no
  playback. Explicit open displayed 507 history rows with the exact first fill
  67.31251478%, unavailable initial backward rate, three retained direction values
  4.72739172 / 3.07596111 / 1.20072341 and distinct ESN-state covariance lambda1.
- The fill canvas had zero draws while offscreen, then one after entering view.
  Its count remained one across later idle observations. This is an event-driven
  rendering observation, not a power or frame-rate measurement.
- Explicit context loss showed the loss/fallback state and retained values. Restore
  was requested while offscreen; the restored canvas/state appeared when scrolled
  into view, at two frames drawn. The UI remained in the lost state until then.
- The state track showed 1,024 ordinal rows, explicit absence of row timestamps and
  paired fill, exact row 0 / coordinate 0 value 0.35750484466552734 and retained
  geometry metrics. No cross-track clock join appeared.
- Opening Library without Refresh updated the old index automatically. Searching
  controller showed the bundled regulation example with Verify & open enabled,
  alongside the prior managed controller import. Recently opened retained the
  managed controller entry. This directly exercises the 0.4-to-0.5 catalog repair.

A concrete presentation defect was found in the screenshot: global definition-list
styles collided with nested Observatory rows, squeezing exact values into narrow
columns (including one character per line for UTC). The fill value table also had
unintended nested columns. This is a failed layout check. The new 0.5.1 candidate
repairs scoped CSS and reduces the introductory vertical footprint. Its source,
package, checks and receipts are separate. No 0.5 receipt or archive was replaced.
