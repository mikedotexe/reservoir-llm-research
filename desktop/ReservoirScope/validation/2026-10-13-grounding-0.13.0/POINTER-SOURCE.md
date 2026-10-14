# Pointer and reopen source review

Source review dated2026-10-13. This file does not establish the cause of the earlier click-path observation or report a packaged pointer pass. Root's actual UI evidence is separate. No renderer, CSS, journal handler, native mouse policy or numerical/session behavior was changed by this audit.

## Confirmed source behavior

- `myReservoirController.ts::followLatest` sets `followLatest=true` and updates the seen count synchronously before its page IPC. `journals(..., false)` also updates seen count before IPC. A still-visible `3 new` label after an attempted activation therefore does not establish blocked Rust journal I/O. Both page buttons are disabled only by `readingPage`.
- `sustained_commands.rs` dispatches journal reads with `spawn_blocking`; page reads use the in-memory bounded catalog. Journal contents are separate exact-object reads. There is no frontend numerical timer in this path.
- `SurfaceView.tsx` owns pointer capture only on its canvas. It releases capture on pointerup and clears drag state on pointercancel. No application-wide pointer cancellation or custom titlebar drag region was found. Visibility listeners in the renderer update the draw scheduler; they do not disable journal buttons or suspend the controller.
- `styles.css` has sticky workspace navigation with z-index20, so a coordinate covered by that navigation is not a journal hit target. `MyReservoirClosePanel` uses a native HTML modal dialog; if open, the underlying document is inert. Neither condition was established as the historical cause.
- The configured macOS window uses the pinned default `acceptFirstMouse=false` (wry0.57.0 / tauri-utils2.10.1). An inactive-window first click can activate without reaching WebView content. This does not explain repeated confirmed foreground clicks by itself.

[Source identity comparison](pointer-review-source-identity.json) binds the reviewed renderer, render policy, CSS, journal controller/view and Tauri config to the qualified0.12.2source. These files were unchanged when read. The current app's new layout work is separately owned and qualified; it is not inferred from those historical hashes.

## Explicit macOS reopen handling

The pinned local stack contains:

- `tao-0.37.1/src/platform_impl/macos/app_delegate.rs:205`: `application_should_handle_reopen` forwards `AppState::reopen(has_visible_windows)` and returns that argument.
- `tauri-runtime-wry-2.12.1/src/lib.rs`: Tao Reopen is forwarded to runtime Reopen (verify the exact pinned runtime version in Cargo.lock; no behavior beyond the read source is assumed).
- `tauri-2.12.3/src/app.rs:275`: `RunEvent::Reopen` is the macOS application reopen event.
- App `main.rs`: the prior run callback handled ExitRequested only. The single-instance callback already called unminimize/show/focus, but a normal application reopen need not create another process.

Root authorized the narrow `#[cfg(target_os="macos")] RunEvent::Reopen` arm in `main.rs`. It finds the existing main window and calls unminimize, show and set_focus. It does not create or restore a session, call Start, change a pending boundary, contact a model or alter the exit guard. Non-macOS builds do not compile that event arm. This is explicit desktop lifecycle handling; it is not asserted to causally fix the unresolved historical click episode. Compile and actual packaged reopen checks belong to the integrated0.13qualification, not this source review.

## Bounded qualification procedure

Use an already-retained session and no model request to test input. Establish actual pointer activation with a refreshed screenshot/AX target. Select an older journal, minimize, then distinguish binding/capturing an app from an actual OS restore. Explicitly close any native menu before evaluating content input. Reopen through the OS, verify the older reading selection remains, activate Follow latest with the pointer, then activate and cancel a native export dialog. Repeat minimize/reopen and compare keyboard separately. Record disabled controls, menu state, restore action, target coordinates/bounds and whether synchronous labels change. If a failure persists on an actually restored window, repeat with exact-values-only graphics before considering renderer changes.

A unit test mirroring `unminimize/show/focus` calls would not establish native event delivery. No such test was added. No tool-internal click implementation or coordinate mapping was inspected, so this review does not assign blame to the automation tool. A screenshot or successful keyboard path alone does not establish a visible, normally pointer-responsive window.

## Primary references inspected2026-10-13

[W3C Pointer Events, implicit capture release](https://www.w3.org/TR/pointerevents3/#implicit-release-of-pointer-capture) requires clearing capture after pointerup/pointercancel. This limits the claim that a missing explicit release in a cancel handler is itself a permanent-capture defect.

[HTML modal dialogs and inert subtrees](https://html.spec.whatwg.org/multipage/interaction.html#modal-dialogs-and-inert-subtrees) defines the inertness created by showModal.

[Tauri acceptFirstMouse configuration](https://v2.tauri.app/reference/config/#acceptfirstmouse) documents the inactive-window click-through option. [Tauri RunEvent](https://docs.rs/tauri/2.12.3/tauri/enum.RunEvent.html#variant.Reopen) describes the macOS reopen event; pinned local crate source was used for the actual forwarding review.
