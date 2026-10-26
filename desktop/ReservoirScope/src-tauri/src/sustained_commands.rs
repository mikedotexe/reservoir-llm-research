//! Narrow IPC for explicit sustained runs, durable journal inspection and export.
use crate::{
    files::AppError,
    sustained::{
        JournalDetail, JournalPage, SustainedConfig, SustainedRunLimits, SustainedState,
        SustainedUpdate,
    },
    sustained_store::{BundleReport, RecoveryDetail, RecoveryPage},
};
use std::sync::Arc;
use tauri::ipc::Channel;
use tauri_plugin_dialog::DialogExt;
fn worker(e: impl std::fmt::Display) -> AppError {
    AppError::new("sustained-command", "worker", e.to_string())
}
#[tauri::command]
pub async fn create_sustained(
    state: tauri::State<'_, SustainedState>,
    request_id: String,
    config: SustainedConfig,
) -> Result<SustainedUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || s.create(request_id, config))
        .await
        .map_err(worker)?
}
#[tauri::command]
pub async fn extend_sustained_limits(
    state: tauri::State<'_, SustainedState>,
    request_id: String,
    session_id: String,
    generation: String,
    expected_revision: String,
    limits: SustainedRunLimits,
) -> Result<SustainedUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        s.extend_limits(
            request_id,
            &session_id,
            &generation,
            &expected_revision,
            limits,
        )
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn get_sustained(
    state: tauri::State<'_, SustainedState>,
    request_id: String,
    on_update: Channel<SustainedUpdate>,
) -> Result<SustainedUpdate, AppError> {
    let s = state.inner().clone();
    let subscription_id = request_id.clone();
    tauri::async_runtime::spawn_blocking(move || {
        s.get(
            request_id,
            Some(Arc::new(move |mut u| {
                u.request_id = subscription_id.clone();
                on_update.send(u).is_ok()
            })),
        )
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn start_sustained(
    app: tauri::AppHandle,
    state: tauri::State<'_, SustainedState>,
    request_id: String,
    session_id: String,
    generation: String,
) -> Result<SustainedUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        crate::execution_admission::start_sustained(&app, || {
            s.start(request_id, &session_id, &generation)
        })
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn pause_sustained(
    state: tauri::State<'_, SustainedState>,
    request_id: String,
    session_id: String,
    generation: String,
) -> Result<SustainedUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || s.pause(request_id, &session_id, &generation))
        .await
        .map_err(worker)?
}
#[tauri::command]
pub async fn stop_sustained(
    state: tauri::State<'_, SustainedState>,
    request_id: String,
    session_id: String,
    generation: String,
) -> Result<SustainedUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || s.stop(request_id, &session_id, &generation))
        .await
        .map_err(worker)?
}
#[tauri::command]
pub async fn retry_sustained_save(
    state: tauri::State<'_, SustainedState>,
    request_id: String,
    session_id: String,
    generation: String,
) -> Result<SustainedUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || s.retry_save(request_id, &session_id, &generation))
        .await
        .map_err(worker)?
}
#[tauri::command]
pub async fn retry_sustained_language(
    app: tauri::AppHandle,
    state: tauri::State<'_, SustainedState>,
    request_id: String,
    session_id: String,
    generation: String,
) -> Result<SustainedUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        crate::execution_admission::start_sustained(&app, || {
            s.retry_language(request_id, &session_id, &generation)
        })
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn skip_sustained_feedback(
    state: tauri::State<'_, SustainedState>,
    request_id: String,
    session_id: String,
    generation: String,
    expected_entry_id: Option<String>,
    expected_attempt_id: Option<u64>,
) -> Result<SustainedUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        s.skip(
            request_id,
            &session_id,
            &generation,
            expected_entry_id,
            expected_attempt_id,
        )
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn open_sustained_journal_folder(
    state: tauri::State<'_, SustainedState>,
    session_id: String,
    generation: String,
) -> Result<(), AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        // Resolve only the selected session's owned directory. Release the state
        // lock before handing the folder to the system file manager.
        let path = s.journal_directory(&session_id, &generation)?;
        tauri_plugin_opener::open_path(path, None::<&str>).map_err(|e| {
            AppError::new(
                "journal-folder",
                "open",
                format!("Could not open the journal folder: {e}"),
            )
        })
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn list_sustained_journals(
    state: tauri::State<'_, SustainedState>,
    request_id: String,
    session_id: String,
    generation: String,
    offset: usize,
    limit: usize,
) -> Result<JournalPage, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        s.journal_page(request_id, &session_id, &generation, offset, limit)
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn get_sustained_journal(
    state: tauri::State<'_, SustainedState>,
    request_id: String,
    session_id: String,
    generation: String,
    entry_id: String,
) -> Result<JournalDetail, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        s.journal(request_id, &session_id, &generation, &entry_id)
    })
    .await
    .map_err(worker)?
}
#[tauri::command]
pub async fn list_sustained_recovery(
    state: tauri::State<'_, SustainedState>,
    request_id: String,
) -> Result<RecoveryPage, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || s.recovery(request_id))
        .await
        .map_err(worker)?
}
#[tauri::command]
pub async fn inspect_sustained_recovery(
    state: tauri::State<'_, SustainedState>,
    request_id: String,
    session_id: String,
) -> Result<RecoveryDetail, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || s.inspect(request_id, &session_id))
        .await
        .map_err(worker)?
}
#[tauri::command]
pub async fn resume_sustained(
    state: tauri::State<'_, SustainedState>,
    request_id: String,
    session_id: String,
    expected_generation: String,
    expected_revision: String,
) -> Result<SustainedUpdate, AppError> {
    let s = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        s.resume(
            request_id,
            &session_id,
            &expected_generation,
            &expected_revision,
        )
    })
    .await
    .map_err(worker)?
}
#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ExportResult {
    request_id: String,
    session_id: String,
    generation: String,
    revision: String,
    bundle: Option<BundleReport>,
}
#[tauri::command]
pub async fn export_sustained(
    app: tauri::AppHandle,
    state: tauri::State<'_, SustainedState>,
    request_id: String,
    session_id: String,
    generation: String,
    expected_revision: Option<String>,
) -> Result<ExportResult, AppError> {
    let s = state.inner().clone();
    let root = super::resource_root(&app, "export-sustained")?;
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = s.begin_export()?;
        let inspected = s.inspect(request_id.clone(), &session_id)?;
        if inspected.manifest.generation != generation
            || expected_revision
                .as_ref()
                .is_some_and(|r| r != &inspected.manifest.revision)
        {
            return Err(worker(
                "Selected snapshot changed before opening the export dialog",
            ));
        }
        let revision = inspected.manifest.revision;
        let bundle = if let Some(folder) = app
            .dialog()
            .file()
            .set_title("Choose parent folder for a new sustained session bundle")
            .blocking_pick_folder()
        {
            let path = folder.into_path().map_err(worker)?;
            Some(
                s.export(&session_id, &generation, Some(&revision), &path, &[root])?
                    .1,
            )
        } else {
            None
        };
        Ok(ExportResult {
            request_id,
            session_id,
            generation,
            revision,
            bundle,
        })
    })
    .await
    .map_err(worker)?
}
