# Temporary recorded-evidence interface

This is the 0.2.0 desktop reading contract. Portable scientific formats remain owned
by the frozen reference and their independently tested Rust decoders. This interface
is not a new portable format, Library schema or session execution contract.

Rust keeps original bytes, the numerical verification report and bounded inspection
views. The frontend never parses portable JSON or decides verification/save status.
An original record can contain ignored future fields; only fields interpreted by the
verified typed decoder enter a display view. Unknown bytes survive export unchanged.

| Command | Input | Result |
| --- | --- | --- |
| `open_record` | Request ID; optional explicit bundled example ID, otherwise native file dialog | Echoed request ID, cancellation, verification report, accepted summary or null |
| `get_record_frame` | Request ID, opaque record/track ID, frame index | Echoed ownership and one recorded frame |
| `get_record_turn` | Request ID, opaque record/track ID, turn index | Echoed ownership and one retained language/action turn |
| `export_record` | Request ID, record ID; native save dialog | Echoed ownership, original-byte export identity or cancellation |
| `close_record` | Record ID | Idempotent release; no source file change |

Each accepted open creates a distinct handle. A frontend replacement is accepted
only after its summary and first available frame arrive; a zero-frame record needs
no frame request. Late results cannot replace a newer generation. Stale candidates
are released, while invalid incoming files leave the accepted handle and cursor
intact. Closing invalidates pending reader callbacks. Playback pauses on navigation,
visibility loss or a read failure and advances stored frames at at most 2 Hz.

Resource and external reads are bounded; the record reader admits at most four
handles and 256 MiB of original bytes combined. File/open verification operations
within this reader are serialized. This bound excludes decoded data and numerical
workspace, which also consume memory. Capacity failure is visible. No persistent
watcher, automatic directory scan, model connection or Library publication occurs.

Track summaries carry at most 600 scalar samples, an explicit stride and the final
frame. Samples are original recorded points; missing values and skipped intervals
are not interpolated into measurements. Full selected states are fetched separately.
Seeds, step identities, turn identities and tape IDs cross IPC as decimal strings;
existing portable files keep their numeric integer encoding. Counts/indices remain
bounded numbers. All optional scientific values are explicit nulls.

The view distinguishes signed reservoir state, sensory covariance eigenvalues and
reduced fill. No fill is computed for a family that lacks a recorded fill field.
Configured model and provider-reported identity are separate; an absent request flag
is unknown, and tape replay is not reclassified as a provider call. Journal-save
receipts describe internally checked retained evidence, not a new filesystem write.
Historical paths stay inert text. Export does not promote failed saves into feedback.

The frontend renders imported text as inert React text. Commands are registered
explicitly in the Tauri app manifest and main-window capability. Verification runs
in a worker; no model service is started, queried or substituted by this interface.
The full long-session cancellation, save/quit and recovery contract is later work.
