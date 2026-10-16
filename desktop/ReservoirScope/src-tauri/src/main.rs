#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod activation;
mod activation_commands;
mod cases;
mod desktop_menu;
mod execution_admission;
mod files;
mod geometry;
mod guide;
mod library;
#[cfg(target_os = "macos")]
mod macos_lifecycle;
#[cfg(target_os = "macos")]
mod macos_termination;
mod model_readiness;
mod model_transport;
mod observatory;
mod preparation;
mod records;
mod resources;
mod response;
mod response_commands;
mod run_activity;
mod session_commands;
mod session_store;
mod sessions;
mod sustained;
mod sustained_commands;
mod sustained_store;

use files::{AppError, FileProof};
use records::{FrameResult, OpenResult, RecordState, TurnResult};
use resources::{BuildInfo, ReferenceScenes};
use tauri::{Emitter, Manager};
use tauri_plugin_dialog::DialogExt;

#[tauri::command]
async fn open_observatory(
    app: tauri::AppHandle,
    state: tauri::State<'_, observatory::ObservatoryState>,
    request_id: String,
) -> Result<observatory::ObservatoryOpenResult, AppError> {
    let state = state.inner().clone();
    let root = app
        .path()
        .resource_dir()
        .map_err(|e| AppError::new("open-observatory", "resource-path", e.to_string()))?
        .join("resources");
    tauri::async_runtime::spawn_blocking(move || state.open(&root, request_id))
        .await
        .map_err(|e| AppError::new("open-observatory", "worker", e.to_string()))?
}
#[tauri::command]
fn get_observatory_timeline(
    state: tauri::State<'_, observatory::ObservatoryState>,
    request_id: String,
    observatory_id: String,
    track_id: String,
    start: usize,
    limit: usize,
    node_index: Option<usize>,
) -> Result<observatory::ObservatoryTimelineResult, AppError> {
    state.timeline(
        request_id,
        &observatory_id,
        &track_id,
        start,
        limit,
        node_index,
    )
}
#[tauri::command]
fn get_observatory_frame(
    state: tauri::State<'_, observatory::ObservatoryState>,
    request_id: String,
    observatory_id: String,
    track_id: String,
    index: usize,
) -> Result<observatory::ObservatoryFrameResult, AppError> {
    state.frame(request_id, &observatory_id, &track_id, index)
}
#[tauri::command]
fn seek_observatory(
    state: tauri::State<'_, observatory::ObservatoryState>,
    request_id: String,
    observatory_id: String,
    track_id: String,
    position: f64,
    mode: String,
) -> Result<observatory::ObservatoryFrameResult, AppError> {
    state.seek(request_id, &observatory_id, &track_id, position, &mode)
}
#[tauri::command]
fn close_observatory(
    state: tauri::State<'_, observatory::ObservatoryState>,
    observatory_id: String,
) -> Result<(), AppError> {
    state.close(&observatory_id)
}

#[tauri::command]
async fn open_record(
    app: tauri::AppHandle,
    state: tauri::State<'_, RecordState>,
    request_id: String,
    example_id: Option<String>,
) -> Result<OpenResult, AppError> {
    let guard = state.begin_operation()?;
    let state = state.inner().clone();
    let root = app
        .path()
        .resource_dir()
        .map_err(|e| AppError::new("open-record", "resource-path", e.to_string()))?
        .join("resources");
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = guard;
        let (filename, bytes, origin) = if let Some(id) = example_id {
            let (name, bytes) = resources::record_example(&root, &id)?;
            (name, bytes, "bundled")
        } else {
            let Some(file) = app
                .dialog()
                .file()
                .set_title("Open and verify a recorded experiment")
                .add_filter("JSON recordings", &["json"])
                .blocking_pick_file()
            else {
                return Ok(OpenResult::cancelled(request_id));
            };
            let path = file
                .into_path()
                .map_err(|e| AppError::new("open-record", "local-file", e.to_string()))?;
            let bytes = files::read_bounded(
                &path,
                reservoir_core::MAX_RECORD_BYTES as u64,
                "open-record",
            )?;
            (
                path.file_name()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .into_owned(),
                bytes,
                "external",
            )
        };
        state.open(request_id, filename, origin, bytes)
    })
    .await
    .map_err(|e| AppError::new("open-record", "worker", e.to_string()))?
}

#[tauri::command]
fn get_record_frame(
    state: tauri::State<'_, RecordState>,
    request_id: String,
    record_id: String,
    track_id: String,
    index: usize,
) -> Result<FrameResult, AppError> {
    state.frame(request_id, record_id, track_id, index)
}

#[tauri::command]
fn get_record_turn(
    state: tauri::State<'_, RecordState>,
    request_id: String,
    record_id: String,
    track_id: String,
    index: usize,
) -> Result<TurnResult, AppError> {
    state.turn(request_id, record_id, track_id, index)
}

#[tauri::command]
fn close_record(state: tauri::State<'_, RecordState>, record_id: String) -> Result<(), AppError> {
    state.close(&record_id)
}

#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
struct ExportResult {
    request_id: String,
    record_id: String,
    file: Option<FileProof>,
}

#[tauri::command]
async fn export_record(
    app: tauri::AppHandle,
    state: tauri::State<'_, RecordState>,
    request_id: String,
    record_id: String,
) -> Result<ExportResult, AppError> {
    let guard = state.begin_operation()?;
    let (filename, bytes) = state.snapshot(&record_id)?;
    let root = app
        .path()
        .resource_dir()
        .map_err(|e| AppError::new("export-record", "resource-path", e.to_string()))?
        .join("resources");
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = guard;
        let file = if let Some(file) = app
            .dialog()
            .file()
            .set_title("Export original verified recording bytes")
            .set_file_name(&filename)
            .add_filter("JSON recordings", &["json"])
            .blocking_save_file()
        {
            let path = file
                .into_path()
                .map_err(|e| AppError::new("export-record", "local-file", e.to_string()))?;
            Some(files::atomic_export(&path, &bytes, &root)?)
        } else {
            None
        };
        Ok(ExportResult {
            request_id,
            record_id,
            file,
        })
    })
    .await
    .map_err(|e| AppError::new("export-record", "worker", e.to_string()))?
}

#[tauri::command]
async fn get_build_info(app: tauri::AppHandle) -> Result<BuildInfo, AppError> {
    let root = app
        .path()
        .resource_dir()
        .map_err(|e| AppError::new("build-info", "resource-path", e.to_string()))?
        .join("resources");
    let data = files::app_data_path(
        app.path()
            .app_data_dir()
            .map_err(|e| AppError::new("build-info", "app-data", e.to_string()))?,
    )?;
    tauri::async_runtime::spawn_blocking(move || resources::build_info(&root, &data))
        .await
        .map_err(|e| AppError::new("build-info", "worker", e.to_string()))?
}

#[tauri::command]
async fn get_reference_scenes(app: tauri::AppHandle) -> Result<ReferenceScenes, AppError> {
    let root = app
        .path()
        .resource_dir()
        .map_err(|e| AppError::new("reference-scenes", "resource-path", e.to_string()))?
        .join("resources");
    tauri::async_runtime::spawn_blocking(move || resources::reference_scenes(&root))
        .await
        .map_err(|e| AppError::new("reference-scenes", "worker", e.to_string()))?
}

#[tauri::command]
async fn open_file_proof(app: tauri::AppHandle) -> Result<Option<FileProof>, AppError> {
    tauri::async_runtime::spawn_blocking(move || {
        let Some(file) = app
            .dialog()
            .file()
            .set_title("Inspect a file’s bytes (no import or numerical verification)")
            .blocking_pick_file()
        else {
            return Ok(None);
        };
        let path = file
            .into_path()
            .map_err(|e| AppError::new("open-file", "local-file", e.to_string()))?;
        files::inspect_file(&path).map(Some)
    })
    .await
    .map_err(|e| AppError::new("open-file", "worker", e.to_string()))?
}

#[tauri::command]
async fn save_file_proof(app: tauri::AppHandle) -> Result<Option<FileProof>, AppError> {
    let root = app
        .path()
        .resource_dir()
        .map_err(|e| AppError::new("save-file", "resource-path", e.to_string()))?
        .join("resources");
    tauri::async_runtime::spawn_blocking(move || {
        // Export the same bounded snapshot whose bytes were hash-checked.
        let bytes = resources::reference_scene_bytes(&root)?;
        let Some(file) = app
            .dialog()
            .file()
            .set_title("Export the reference-scene fixture")
            .set_file_name("reservoir-scope-reference-scenes.json")
            .add_filter("JSON", &["json"])
            .blocking_save_file()
        else {
            return Ok(None);
        };
        let path = file
            .into_path()
            .map_err(|e| AppError::new("save-file", "local-file", e.to_string()))?;
        files::atomic_export(&path, &bytes, &root).map(Some)
    })
    .await
    .map_err(|e| AppError::new("save-file", "worker", e.to_string()))?
}

fn resource_root(app: &tauri::AppHandle, operation: &str) -> Result<std::path::PathBuf, AppError> {
    app.path()
        .resource_dir()
        .map(|p| p.join("resources"))
        .map_err(|e| AppError::new(operation, "resource-path", e.to_string()))
}

#[tauri::command]
async fn get_guided_catalog(app: tauri::AppHandle) -> Result<guide::GuideCatalog, AppError> {
    let root = resource_root(&app, "guide")?;
    tauri::async_runtime::spawn_blocking(move || guide::catalog(&root))
        .await
        .map_err(|e| AppError::new("guide", "worker", e.to_string()))?
}
#[tauri::command]
async fn open_cases(
    app: tauri::AppHandle,
    state: tauri::State<'_, cases::CaseState>,
    request_id: String,
    bundled: bool,
) -> Result<cases::CaseOpenResult, AppError> {
    let guard = state.begin_operation()?;
    let state = state.inner().clone();
    let root = resource_root(&app, "open-cases")?;
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = guard;
        let (filename, bytes, origin) = if bundled {
            (
                "research-cases-v1.json".into(),
                resources::catalog_bytes(&root, "research-cases-v1.json")?,
                "bundled",
            )
        } else {
            let Some(file) = app
                .dialog()
                .file()
                .set_title("Open a reviewed research case")
                .add_filter("Research case JSON", &["json"])
                .blocking_pick_file()
            else {
                return Ok(cases::CaseOpenResult::cancelled(request_id));
            };
            let path = file
                .into_path()
                .map_err(|e| AppError::new("open-cases", "local-file", e.to_string()))?;
            let bytes = files::read_bounded(
                &path,
                reservoir_core::cases::MAX_CASE_BYTES as u64,
                "open-cases",
            )?;
            (
                path.file_name()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .into_owned(),
                bytes,
                "external",
            )
        };
        state.open(request_id, filename, origin, bytes)
    })
    .await
    .map_err(|e| AppError::new("open-cases", "worker", e.to_string()))?
}
#[tauri::command]
async fn get_case(
    state: tauri::State<'_, cases::CaseState>,
    request_id: String,
    catalog_id: String,
    index: usize,
) -> Result<cases::CaseViewResult, AppError> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || state.view(request_id, catalog_id, index))
        .await
        .map_err(|e| AppError::new("read-case", "worker", e.to_string()))?
}
#[tauri::command]
fn close_cases(
    state: tauri::State<'_, cases::CaseState>,
    catalog_id: String,
) -> Result<(), AppError> {
    state.close(&catalog_id)
}
#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
struct CaseExportResult {
    request_id: String,
    catalog_id: String,
    file: Option<FileProof>,
}
#[tauri::command]
async fn export_cases(
    app: tauri::AppHandle,
    state: tauri::State<'_, cases::CaseState>,
    request_id: String,
    catalog_id: String,
) -> Result<CaseExportResult, AppError> {
    let guard = state.begin_operation()?;
    let (filename, bytes) = state.snapshot(&catalog_id)?;
    let root = resource_root(&app, "export-cases")?;
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = guard;
        let file = if let Some(file) = app
            .dialog()
            .file()
            .set_title("Export original case catalog bytes")
            .set_file_name(&filename)
            .add_filter("JSON", &["json"])
            .blocking_save_file()
        {
            let path = file
                .into_path()
                .map_err(|e| AppError::new("export-cases", "local-file", e.to_string()))?;
            Some(files::atomic_export(&path, &bytes, &root)?)
        } else {
            None
        };
        Ok(CaseExportResult {
            request_id,
            catalog_id,
            file,
        })
    })
    .await
    .map_err(|e| AppError::new("export-cases", "worker", e.to_string()))?
}
#[tauri::command]
async fn open_geometry(
    app: tauri::AppHandle,
    state: tauri::State<'_, geometry::GeometryState>,
    request_id: String,
    synthetic_example: bool,
) -> Result<geometry::GeometryOpenResult, AppError> {
    let guard = state.begin_operation()?;
    let state = state.inner().clone();
    let root = resource_root(&app, "open-geometry")?;
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = guard;
        let (filename, bytes, origin) = if synthetic_example {
            (
                "synthetic-geometry-example.json".into(),
                resources::catalog_bytes(&root, "synthetic-geometry-example.json")?,
                "syntheticExample",
            )
        } else {
            let Some(file) = app
                .dialog()
                .file()
                .set_title("Open a geometry bookmark packet")
                .add_filter("Geometry JSON", &["json"])
                .blocking_pick_file()
            else {
                return Ok(geometry::GeometryOpenResult::cancelled(request_id));
            };
            let path = file
                .into_path()
                .map_err(|e| AppError::new("open-geometry", "local-file", e.to_string()))?;
            let bytes = files::read_bounded(
                &path,
                reservoir_core::geometry::MAX_PACKET_BYTES as u64,
                "open-geometry",
            )?;
            (
                path.file_name()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .into_owned(),
                bytes,
                "openedFile",
            )
        };
        state.open(request_id, filename, origin, bytes)
    })
    .await
    .map_err(|e| AppError::new("open-geometry", "worker", e.to_string()))?
}
#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
struct GeometryExportResult {
    request_id: String,
    packet_id: String,
    file: Option<FileProof>,
}
#[tauri::command]
async fn export_geometry(
    app: tauri::AppHandle,
    state: tauri::State<'_, geometry::GeometryState>,
    request_id: String,
    packet_id: String,
) -> Result<GeometryExportResult, AppError> {
    let guard = state.begin_operation()?;
    let (filename, bytes) = state.snapshot(&packet_id)?;
    let root = resource_root(&app, "export-geometry")?;
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = guard;
        let file = if let Some(file) = app
            .dialog()
            .file()
            .set_title("Export original geometry packet bytes")
            .set_file_name(&filename)
            .add_filter("JSON", &["json"])
            .blocking_save_file()
        {
            let path = file
                .into_path()
                .map_err(|e| AppError::new("export-geometry", "local-file", e.to_string()))?;
            Some(files::atomic_export(&path, &bytes, &root)?)
        } else {
            None
        };
        Ok(GeometryExportResult {
            request_id,
            packet_id,
            file,
        })
    })
    .await
    .map_err(|e| AppError::new("export-geometry", "worker", e.to_string()))?
}
#[tauri::command]
async fn library_query(
    state: tauri::State<'_, library::LibraryState>,
    query: library::LibraryQuery,
) -> Result<library::LibraryPage, AppError> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || state.query(query))
        .await
        .map_err(|e| AppError::new("library-query", "worker", e.to_string()))?
}
#[tauri::command]
async fn library_import(
    app: tauri::AppHandle,
    state: tauri::State<'_, library::LibraryState>,
    request_id: String,
) -> Result<library::LibraryImportResult, AppError> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        let Some(file) = app
            .dialog()
            .file()
            .set_title("Import an experiment into the Tauri Library")
            .add_filter("Experiment JSON", &["json"])
            .blocking_pick_file()
        else {
            return Ok(library::LibraryImportResult::cancelled(request_id));
        };
        let path = file
            .into_path()
            .map_err(|e| AppError::new("library-import", "local-file", e.to_string()))?;
        state.import_path(request_id, &path)
    })
    .await
    .map_err(|e| AppError::new("library-import", "worker", e.to_string()))?
}
#[tauri::command]
async fn library_open(
    state: tauri::State<'_, library::LibraryState>,
    records: tauri::State<'_, RecordState>,
    request_id: String,
    entry_id: String,
) -> Result<OpenResult, AppError> {
    let state = state.inner().clone();
    let records = records.inner().clone();
    let guard = records.begin_operation()?;
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = guard;
        state.open(&records, request_id, &entry_id)
    })
    .await
    .map_err(|e| AppError::new("library-open", "worker", e.to_string()))?
}
#[tauri::command]
async fn library_scan(
    state: tauri::State<'_, library::LibraryState>,
    rebuild: bool,
) -> Result<library::ScanStatus, AppError> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || state.scan(rebuild))
        .await
        .map_err(|e| AppError::new("library-scan", "worker", e.to_string()))?
}
#[tauri::command]
fn library_scan_status(state: tauri::State<'_, library::LibraryState>) -> library::ScanStatus {
    state.scan_status()
}
#[tauri::command]
fn library_cancel_scan(state: tauri::State<'_, library::LibraryState>) -> library::ScanStatus {
    state.cancel_scan()
}

// OS close/quit only requests review; no UI timer or frontend claim can approve
// dropping evidence. The backend atomically authorizes the eventual exit.
fn reopen_close_gates(app: &tauri::AppHandle) {
    app.state::<activation::ActivationState>().cancel_close();
    app.state::<sessions::SessionState>().cancel_close();
    app.state::<sustained::SustainedState>().cancel_close();
}

fn cancel_all_close(app: &tauri::AppHandle) {
    app.state::<execution_admission::ExecutionAdmission>()
        .1
        .cancel(|| reopen_close_gates(app));
}

fn close_epoch(app: &tauri::AppHandle) -> u64 {
    app.state::<execution_admission::ExecutionAdmission>()
        .1
        .epoch()
}

fn close_finish_is_current(app: &tauri::AppHandle, epoch: u64) -> bool {
    app.state::<execution_admission::ExecutionAdmission>()
        .1
        .current(epoch, |state| !state.committed)
        .unwrap_or(false)
}

fn settle_close_finish(app: &tauri::AppHandle, epoch: u64) -> bool {
    app.state::<execution_admission::ExecutionAdmission>()
        .1
        .settled(epoch, || {
            app.state::<sessions::SessionState>()
                .reopen_after_stale_close();
            app.state::<sustained::SustainedState>()
                .reopen_after_stale_close();
        })
}

fn request_session_close(app: &tauri::AppHandle) -> bool {
    app.state::<activation::ActivationState>().request_close();
    request_session_close_at(app, close_epoch(app), false)
}

fn request_session_close_at(app: &tauri::AppHandle, epoch: u64, deferred: bool) -> bool {
    enum Decision {
        Exit,
        Retain,
        Defer,
        Review { finite: bool, sustained: bool },
    }
    let admission = app.state::<execution_admission::ExecutionAdmission>();
    // Only nonblocking owner/admission inspection runs under this short gate.
    // Return cannot cross a final authorization decision. UI work runs below.
    let decision = admission.1.current(epoch, |close| {
        if close.committed {
            return Decision::Exit;
        }
        if deferred {
            close.deferred = false;
        }
        let Ok(_guard) = admission.0.try_lock() else {
            reopen_close_gates(app);
            if close.deferred {
                return Decision::Retain;
            }
            close.deferred = true;
            return Decision::Defer;
        };
        close.deferred = false;
        let finite = app.state::<sessions::SessionState>();
        let sustained = app.state::<sustained::SustainedState>();
        let finite_ready = finite.authorize_clean_close();
        let sustained_ready = sustained.authorize_clean_close();
        if finite_ready && sustained_ready {
            close.committed = true;
            return Decision::Exit;
        }
        // A clean owner must stay usable if its peer requires review.
        reopen_close_gates(app);
        if !finite_ready {
            finite.request_close_pause();
        }
        if !sustained_ready {
            sustained.request_close_pause();
        }
        Decision::Review {
            finite: !finite_ready,
            sustained: !sustained_ready,
        }
    });
    match decision {
        Some(Decision::Exit) => false,
        Some(Decision::Defer) => {
            let app = app.clone();
            std::thread::spawn(move || {
                let admission = app.state::<execution_admission::ExecutionAdmission>();
                let Ok(guard) = admission.0.lock() else {
                    return;
                };
                drop(guard);
                // Validate the original epoch inside the same short gate that
                // authorizes exit, not before releasing the admission mutex.
                if !request_session_close_at(&app, epoch, true) {
                    app.exit(0);
                }
            });
            true
        }
        Some(Decision::Review { finite, sustained }) => {
            let main_app = app.clone();
            let _ = app.run_on_main_thread(move || {
                // Recheck after queued main-thread dispatch, then release the
                // gate before native window calls. Late UI notifications cannot
                // authorize exit, resume a worker or reopen a committed gate.
                if !close_finish_is_current(&main_app, epoch) {
                    return;
                }
                if let Some(window) = main_app.get_webview_window("main") {
                    let _ = window.unminimize();
                    let _ = window.show();
                    let _ = window.set_focus();
                    if finite {
                        let _ = window.emit("session-close-requested", ());
                    }
                    if sustained {
                        let _ = window.emit("sustained-close-requested", ());
                    }
                }
            });
            true
        }
        Some(Decision::Retain) | None => true,
    }
}

#[tauri::command]
async fn finish_sustained_close(
    app: tauri::AppHandle,
    allow_discard: bool,
) -> Result<bool, AppError> {
    let state = app.state::<sustained::SustainedState>().inner().clone();
    let epoch = close_epoch(&app);
    let worker_app = app.clone();
    let accepted = tauri::async_runtime::spawn_blocking(move || {
        if !close_finish_is_current(&worker_app, epoch) {
            return Ok(false);
        }
        let result = state.finish_close(allow_discard);
        if !settle_close_finish(&worker_app, epoch) {
            return Ok(false);
        }
        result
    })
    .await
    .map_err(|e| AppError::new("close-sustained", "worker", e.to_string()))??;
    if accepted && !request_session_close_at(&app, epoch, false) {
        app.exit(0);
    }
    Ok(accepted)
}
#[tauri::command]
fn cancel_sustained_close(app: tauri::AppHandle) {
    cancel_all_close(&app);
}

fn main() {
    let activation_args: Vec<String> = std::env::args().skip(1).collect();
    if activation_args
        .first()
        .is_some_and(|s| s == "--verify-activation")
    {
        let result = activation_args
            .get(1)
            .ok_or_else(|| AppError::new("activation", "usage", "--verify-activation DIRECTORY"))
            .and_then(|p| activation::verify(std::path::Path::new(p)));
        match result {
            Ok(v) => {
                println!("{v}");
                std::process::exit(0)
            }
            Err(e) => {
                println!(
                    "{}",
                    serde_json::json!({"status":"failed","message":e.message,"modelsContacted":false})
                );
                std::process::exit(1)
            }
        }
    }
    if activation_args
        .first()
        .is_some_and(|s| s == "--activation-run")
    {
        let result = (|| -> Result<serde_json::Value, AppError> {
            if !matches!(activation_args.len(), 4 | 6)
                || activation_args[2] != "--output"
                || (activation_args.len() == 6 && activation_args[4] != "--activation-calibration")
            {
                return Err(AppError::new("activation","usage","--activation-run CONFIG.json --output NEW_DIRECTORY [--activation-calibration FILE]"));
            }
            let config: activation::Config = serde_json::from_slice(&files::read_bounded(
                std::path::Path::new(&activation_args[1]),
                1024 * 1024,
                "activation",
            )?)
            .map_err(|e| AppError::new("activation", "configuration", e.to_string()))?;
            let root = std::path::PathBuf::from(&activation_args[3]);
            if root.exists() {
                return Err(AppError::new(
                    "activation",
                    "output",
                    "Choose a new output directory",
                ));
            }
            let state = activation::ActivationState::new(
                root,
                std::path::PathBuf::from(&config.worker_path),
            );
            let session = state.create(config)?;
            if let Some(path) = activation_args.get(5) {
                state.seed_calibration(&session.session_id, std::path::Path::new(path))?;
            }
            state.start(&session.session_id)?;
            while state.is_busy() {
                std::thread::sleep(std::time::Duration::from_millis(50));
            }
            let snapshot = state.get(Some(&session.session_id))?.unwrap();
            serde_json::to_value(snapshot)
                .map_err(|e| AppError::new("activation", "serialization", e.to_string()))
        })();
        match result {
            Ok(v) => {
                let success = v["status"] == "completed";
                println!("{v}");
                std::process::exit(if success { 0 } else { 1 })
            }
            Err(e) => {
                println!(
                    "{}",
                    serde_json::json!({"status":"failed","message":e.message})
                );
                std::process::exit(1)
            }
        }
    }
    // Explicit read-only CLI: no WebView, model transport, restoration or run.
    let mut arguments = std::env::args_os().skip(1);
    if arguments.next().as_deref() == Some(std::ffi::OsStr::new("--verify-sustained")) {
        let Some(path) = arguments.next().filter(|_| arguments.next().is_none()) else {
            eprintln!("Usage: reservoir-scope-desktop --verify-sustained DIRECTORY");
            std::process::exit(2);
        };
        match sustained_store::verify_bundle(std::path::Path::new(&path)) {
            Ok(report) => {
                println!("{}", serde_json::to_string_pretty(&serde_json::json!({"status":"passed","modelsContacted":false,"report":report})).expect("verification report"));
                std::process::exit(0);
            }
            Err(error) => {
                println!(
                    "{}",
                    serde_json::json!({"status":"failed","operation":error.operation,"category":error.category,"message":error.message,"modelsContacted":false})
                );
                std::process::exit(1);
            }
        }
    }
    tauri::Builder::default()
        .manage(desktop_menu::MainWindowZoom::default())
        .manage(RecordState::default())
        .manage(execution_admission::ExecutionAdmission::default())
        .manage(model_readiness::ModelReadinessState::default())
        .manage(observatory::ObservatoryState::default())
        .manage(response::ResponseState::default())
        .manage(cases::CaseState::default())
        .manage(geometry::GeometryState::default())
        .setup(|app| {
            let data = files::app_data_path(app.path().app_data_dir()?)
                .map_err(|e| std::io::Error::other(e.message))?;
            let library = library::LibraryState::new(
                data.join("library-v1"),
                app.path().resource_dir()?.join("resources"),
            );
            app.manage(sessions::SessionState::new(
                data.join("sessions-v1"),
                library.clone(),
            ));
            app.manage(library);
            let sustained = sustained::SustainedState::new(data.join("sustained-v1"));
            app.manage(sustained.clone());
            let packaged_worker = app
                .path()
                .resource_dir()?
                .join("activation_worker/__main__.py");
            let worker = if packaged_worker.exists() {
                packaged_worker
            } else {
                std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                    .parent()
                    .unwrap()
                    .join("activation_worker/__main__.py")
            };
            app.manage(activation::ActivationState::new(
                data.join("activation-v1"),
                worker,
            ));
            #[cfg(target_os = "macos")]
            {
                macos_termination::install(app.handle())?;
                macos_lifecycle::install(move |reason| sustained.interrupt(reason))?;
            }
            Ok(())
        })
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.unminimize();
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_dialog::init())
        .menu(desktop_menu::build)
        .on_menu_event(|app, event| {
            if event.id().as_ref() == desktop_menu::QUIT {
                if !request_session_close(app) {
                    app.exit(0);
                }
            } else {
                desktop_menu::handle_zoom(app, event.id().as_ref());
            }
        })
        .on_window_event(|window, event| {
            if window.label() == "main" {
                if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                    if request_session_close(window.app_handle()) {
                        api.prevent_close();
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            activation_commands::activation_inspect,
            activation_commands::activation_create,
            activation_commands::activation_start,
            activation_commands::activation_stop,
            activation_commands::activation_get,
            activation_commands::activation_list,
            activation_commands::activation_restore,
            activation_commands::activation_export,
            activation_commands::activation_import,
            activation_commands::activation_annotate,
            sustained_commands::create_sustained,
            sustained_commands::get_sustained,
            sustained_commands::start_sustained,
            sustained_commands::pause_sustained,
            sustained_commands::stop_sustained,
            sustained_commands::retry_sustained_save,
            sustained_commands::retry_sustained_language,
            sustained_commands::skip_sustained_feedback,
            sustained_commands::list_sustained_journals,
            sustained_commands::get_sustained_journal,
            sustained_commands::list_sustained_recovery,
            sustained_commands::inspect_sustained_recovery,
            sustained_commands::resume_sustained,
            sustained_commands::export_sustained,
            finish_sustained_close,
            cancel_sustained_close,
            model_readiness::check_local_model,
            model_readiness::cancel_local_model_check,
            session_commands::create_session,
            session_commands::get_session,
            session_commands::step_session,
            session_commands::run_session,
            session_commands::pause_session,
            session_commands::stop_session,
            session_commands::reset_session,
            session_commands::update_session_controls,
            session_commands::cancel_session_close,
            session_commands::get_session_frame,
            session_commands::get_session_regulation_details,
            session_commands::get_session_turn,
            session_commands::request_session_journal,
            session_commands::save_session_journal,
            session_commands::save_session_record,
            session_commands::export_session_record,
            session_commands::list_session_recovery,
            session_commands::get_recovered_session,
            session_commands::export_recovered_session,
            session_commands::finish_session_close,
            response_commands::open_response,
            response_commands::get_response_frame,
            response_commands::get_response_event,
            response_commands::close_response,
            response_commands::export_response,
            preparation::list_preparation_history,
            preparation::get_preparation_report,
            preparation::export_preparation_report,
            open_observatory,
            get_observatory_timeline,
            get_observatory_frame,
            seek_observatory,
            close_observatory,
            get_build_info,
            get_reference_scenes,
            open_file_proof,
            save_file_proof,
            open_record,
            get_record_frame,
            get_record_turn,
            export_record,
            close_record,
            get_guided_catalog,
            open_cases,
            get_case,
            close_cases,
            export_cases,
            cases::export_selected_case,
            open_geometry,
            export_geometry,
            library_query,
            library_import,
            library_open,
            library_scan,
            library_scan_status,
            library_cancel_scan,
        ])
        .build(tauri::generate_context!())
        .expect("Reservoir Scope could not start")
        .run(|app, event| match event {
            tauri::RunEvent::ExitRequested { api, .. } => {
                if request_session_close(app) {
                    api.prevent_exit();
                }
            }
            #[cfg(target_os = "macos")]
            tauri::RunEvent::Reopen { .. } => {
                // A Dock/Finder reopen need not start a second process. Restore
                // the existing window without changing any session boundary.
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.unminimize();
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
            _ => {}
        });
}
