use crate::{
    activation::{ActivationState, Annotation, Config, Snapshot},
    files::AppError,
};
use serde_json::{json, Value};
use tauri::Manager;
use tauri_plugin_dialog::DialogExt;
fn join(e: impl std::fmt::Display) -> AppError {
    AppError::new("activation", "worker", e.to_string())
}
#[tauri::command]
pub async fn activation_inspect(
    state: tauri::State<'_, ActivationState>,
    config: Config,
) -> Result<Value, AppError> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || state.inspect(config))
        .await
        .map_err(join)?
}
#[tauri::command]
pub async fn activation_create(
    state: tauri::State<'_, ActivationState>,
    config: Config,
) -> Result<Snapshot, AppError> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || state.create(config))
        .await
        .map_err(join)?
}
#[tauri::command]
pub async fn activation_start(
    app: tauri::AppHandle,
    state: tauri::State<'_, ActivationState>,
    session_id: String,
) -> Result<Snapshot, AppError> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        let admission = app.state::<crate::execution_admission::ExecutionAdmission>();
        let _guard = admission.0.lock().map_err(join)?;
        if app
            .state::<crate::sessions::SessionState>()
            .execution_busy()
            || app.state::<crate::sustained::SustainedState>().is_busy()
        {
            return Err(AppError::new(
                "activation",
                "other-session",
                "Pause or stop the other experiment before starting activation work",
            ));
        }
        state.start(&session_id)
    })
    .await
    .map_err(join)?
}
#[tauri::command]
pub async fn activation_stop(
    state: tauri::State<'_, ActivationState>,
    session_id: String,
) -> Result<Snapshot, AppError> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || state.stop(&session_id))
        .await
        .map_err(join)?
}
#[tauri::command]
pub async fn activation_get(
    state: tauri::State<'_, ActivationState>,
    session_id: Option<String>,
) -> Result<Option<Snapshot>, AppError> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || state.get(session_id.as_deref()))
        .await
        .map_err(join)?
}
#[tauri::command]
pub async fn activation_list(
    state: tauri::State<'_, ActivationState>,
) -> Result<Vec<Snapshot>, AppError> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || state.list())
        .await
        .map_err(join)?
}
#[tauri::command]
pub async fn activation_restore(
    state: tauri::State<'_, ActivationState>,
    session_id: String,
) -> Result<Snapshot, AppError> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || state.restore(&session_id))
        .await
        .map_err(join)?
}
#[tauri::command]
pub async fn activation_annotate(
    state: tauri::State<'_, ActivationState>,
    session_id: String,
    annotation: Annotation,
) -> Result<Snapshot, AppError> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || state.annotate(&session_id, annotation))
        .await
        .map_err(join)?
}
#[tauri::command]
pub async fn activation_export(
    app: tauri::AppHandle,
    state: tauri::State<'_, ActivationState>,
    session_id: String,
) -> Result<Value, AppError> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        let Some(path) = app
            .dialog()
            .file()
            .set_title("Export activation experiment")
            .set_file_name(format!("{session_id}.activation.json"))
            .blocking_save_file()
        else {
            return Ok(json!({"path":null,"verified":false}));
        };
        let path = path.into_path().map_err(join)?;
        state.export(&session_id, &path)?;
        Ok(json!({"path":path,"verified":true}))
    })
    .await
    .map_err(join)?
}
#[tauri::command]
pub async fn activation_import(
    app: tauri::AppHandle,
    state: tauri::State<'_, ActivationState>,
) -> Result<Option<Snapshot>, AppError> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        let Some(path) = app
            .dialog()
            .file()
            .set_title("Import activation experiment")
            .add_filter("Activation export", &["json"])
            .blocking_pick_file()
        else {
            return Ok(None);
        };
        state.import(&path.into_path().map_err(join)?).map(Some)
    })
    .await
    .map_err(join)?
}
