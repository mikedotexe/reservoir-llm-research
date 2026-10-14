//! Capability-bound session commands. Provider endpoints are explicit validated configuration; filesystem paths remain backend-owned.
use crate::{
    files::{self, AppError, FileProof},
    session_store::{Checkpoint, RecoveryPage},
    sessions::{
        RegulationDetails, SessionConfig, SessionFrameResult, SessionState, SessionTurnResult,
        SessionUpdate,
    },
};
use std::sync::Arc;
use tauri::ipc::Channel;
use tauri_plugin_dialog::DialogExt;
fn worker(e: impl std::fmt::Display) -> AppError {
    AppError::new("session", "worker", e.to_string())
}
#[tauri::command]
pub async fn create_session(
    state: tauri::State<'_, SessionState>,
    request_id: String,
    config: SessionConfig,
) -> Result<SessionUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || s.create(request_id, config))
        .await
        .map_err(worker)?
}
#[tauri::command]
pub async fn get_session(
    state: tauri::State<'_, SessionState>,
    request_id: String,
    on_update: Channel<SessionUpdate>,
) -> Result<SessionUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        s.get(
            request_id,
            Some(Arc::new(move |m| on_update.send(m).is_ok())),
        )
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn step_session(
    app: tauri::AppHandle,
    state: tauri::State<'_, SessionState>,
    request_id: String,
    session_id: String,
    generation: String,
    pulse: Option<bool>,
) -> Result<SessionUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        crate::execution_admission::start_finite(&app, || {
            s.step(request_id, &session_id, &generation, pulse.unwrap_or(false))
        })
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn run_session(
    app: tauri::AppHandle,
    state: tauri::State<'_, SessionState>,
    request_id: String,
    session_id: String,
    generation: String,
    on_update: Channel<SessionUpdate>,
) -> Result<SessionUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        crate::execution_admission::start_finite(&app, || {
            s.run(
                request_id,
                &session_id,
                &generation,
                Arc::new(move |m| on_update.send(m).is_ok()),
            )
        })
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn pause_session(
    state: tauri::State<'_, SessionState>,
    request_id: String,
    session_id: String,
    generation: String,
) -> Result<SessionUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || s.pause(request_id, &session_id, &generation))
        .await
        .map_err(worker)?
}
#[tauri::command]
pub async fn stop_session(
    state: tauri::State<'_, SessionState>,
    request_id: String,
    session_id: String,
    generation: String,
) -> Result<SessionUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || s.stop(request_id, &session_id, &generation))
        .await
        .map_err(worker)?
}
#[tauri::command]
pub async fn reset_session(
    state: tauri::State<'_, SessionState>,
    request_id: String,
    session_id: String,
    generation: String,
    discard: bool,
) -> Result<SessionUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        s.reset(request_id, &session_id, &generation, discard)
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn get_session_frame(
    state: tauri::State<'_, SessionState>,
    request_id: String,
    session_id: String,
    generation: String,
    index: usize,
    track_id: Option<String>,
) -> Result<SessionFrameResult, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        s.frame_for(request_id, session_id, generation, index, track_id)
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn get_session_regulation_details(
    state: tauri::State<'_, SessionState>,
    request_id: String,
    session_id: String,
    generation: String,
    cursor_step: usize,
) -> Result<RegulationDetails, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        s.regulation_details(request_id, session_id, generation, cursor_step)
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn get_session_turn(
    state: tauri::State<'_, SessionState>,
    request_id: String,
    session_id: String,
    generation: String,
    index: usize,
    track_id: Option<String>,
) -> Result<SessionTurnResult, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        s.turn_for(request_id, session_id, generation, index, track_id)
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn request_session_journal(
    app: tauri::AppHandle,
    state: tauri::State<'_, SessionState>,
    request_id: String,
    session_id: String,
    generation: String,
) -> Result<SessionUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        crate::execution_admission::start_finite(&app, || {
            s.request_journal(request_id, &session_id, &generation)
        })
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn save_session_journal(
    state: tauri::State<'_, SessionState>,
    request_id: String,
    session_id: String,
    generation: String,
    arm: String,
    entry_id: String,
) -> Result<SessionUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        s.save_journal_for(request_id, &session_id, &generation, &arm, &entry_id)
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn save_session_record(
    state: tauri::State<'_, SessionState>,
    request_id: String,
    session_id: String,
    generation: String,
) -> Result<SessionUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        s.save_record(request_id, &session_id, &generation)
    })
    .await
    .map_err(worker)?
}
#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SessionExportResult {
    request_id: String,
    session_id: String,
    generation: String,
    revision: String,
    file: Option<FileProof>,
}
#[tauri::command]
pub async fn export_session_record(
    app: tauri::AppHandle,
    state: tauri::State<'_, SessionState>,
    request_id: String,
    session_id: String,
    generation: String,
) -> Result<SessionExportResult, AppError> {
    let s = state.inner().clone();
    let root = super::resource_root(&app, "export-session")?;
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = s.begin_export()?;
        let (name, bytes, revision) = s.snapshot(&session_id, &generation)?;
        let file = if let Some(f) = app
            .dialog()
            .file()
            .set_title("Export current finite experiment snapshot")
            .set_file_name(&name)
            .add_filter("JSON record", &["json"])
            .blocking_save_file()
        {
            let p = f.into_path().map_err(worker)?;
            Some(files::atomic_export(&p, &bytes, &root)?)
        } else {
            None
        };
        Ok(SessionExportResult {
            request_id,
            session_id,
            generation,
            revision,
            file,
        })
    })
    .await
    .map_err(worker)?
}
#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RecoveryResult {
    request_id: String,
    #[serde(flatten)]
    page: RecoveryPage,
}
#[tauri::command]
pub async fn list_session_recovery(
    state: tauri::State<'_, SessionState>,
    request_id: String,
) -> Result<RecoveryResult, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        Ok(RecoveryResult {
            request_id,
            page: s.store.recovery()?,
        })
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn get_recovered_session(
    state: tauri::State<'_, SessionState>,
    session_id: String,
) -> Result<Checkpoint, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || s.store.read_checkpoint(&session_id))
        .await
        .map_err(worker)?
}
#[tauri::command]
pub async fn export_recovered_session(
    app: tauri::AppHandle,
    state: tauri::State<'_, SessionState>,
    request_id: String,
    session_id: String,
    kind: Option<String>,
    expected_generation: String,
    expected_revision: String,
) -> Result<SessionExportResult, AppError> {
    let s = state.inner().clone();
    let root = super::resource_root(&app, "export-recovery")?;
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = s.begin_export()?;
        let c = s.store.read_checkpoint(&session_id)?;
        if c.generation!=expected_generation||c.revision!=expected_revision{return Err(worker("Recovery checkpoint changed since inspection. Refresh and review before exporting."));}
        let selected = kind.as_deref().unwrap_or(if c.pending_journal.is_some() || c.pending_language.is_some() || c.record_sha256.is_none() {
            "checkpoint"
        } else {
            "record"
        });
        let (bytes, name) = match selected {
            "checkpoint" => (
                serde_json::to_vec_pretty(&c).map_err(worker)?,
                format!("{session_id}-recovery-checkpoint.json"),
            ),
            "record" => {
                let hash = c
                    .record_sha256
                    .as_deref()
                    .ok_or_else(|| worker("No committed portable snapshot exists."))?;
                let b = s.store.read_record(&session_id, hash)?;
                if reservoir_core::verify_bytes(&b).status
                    != reservoir_core::VerificationStatus::Passed
                {
                    return Err(worker(
                        "Recovered portable snapshot did not pass verification.",
                    ));
                }
                (
                    b,
                    format!("{session_id}-durable-step-{}.json", c.durable_step),
                )
            }
            _ => return Err(worker("Choose record or checkpoint recovery export.")),
        };
        let file = if let Some(f) = app
            .dialog()
            .file()
            .set_title("Export retained session recovery evidence")
            .set_file_name(&name)
            .add_filter("JSON evidence", &["json"])
            .blocking_save_file()
        {
            Some(files::atomic_export(
                &f.into_path().map_err(worker)?,
                &bytes,
                &root,
            )?)
        } else {
            None
        };
        Ok(SessionExportResult {
            request_id,
            session_id,
            generation: c.generation,
            revision: c.revision,
            file,
        })
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn finish_session_close(
    app: tauri::AppHandle,
    state: tauri::State<'_, SessionState>,
    allow_discard: bool,
) -> Result<bool, AppError> {
    let s = state.inner().clone();
    let epoch = super::close_epoch(&app);
    let worker_app = app.clone();
    let accepted = tauri::async_runtime::spawn_blocking(move || {
        if !super::close_finish_is_current(&worker_app, epoch) {
            return Ok(false);
        }
        let result = s.finish_close(allow_discard);
        if !super::settle_close_finish(&worker_app, epoch) {
            return Ok(false);
        }
        result
    })
    .await
    .map_err(worker)??;
    if accepted && !super::request_session_close_at(&app, epoch, false) {
        app.exit(0);
    }
    Ok(accepted)
}

#[tauri::command]
pub fn cancel_session_close(app: tauri::AppHandle) {
    super::cancel_all_close(&app);
}
#[tauri::command]
pub async fn update_session_controls(
    state: tauri::State<'_, SessionState>,
    request_id: String,
    session_id: String,
    generation: String,
    controls: reservoir_core::exploration::ExplorationControls,
) -> Result<SessionUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        s.update_controls(request_id, &session_id, &generation, controls)
    })
    .await
    .map_err(worker)?
}
