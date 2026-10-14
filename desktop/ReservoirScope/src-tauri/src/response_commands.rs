//! Desktop transport for temporary response evidence; only native dialogs open files.
use crate::{
    files::{self, AppError, FileProof},
    resources, response,
};
use tauri_plugin_dialog::DialogExt;

#[tauri::command]
pub async fn open_response(
    app: tauri::AppHandle,
    state: tauri::State<'_, response::ResponseState>,
    request_id: String,
    source: String,
    previous_response_id: Option<String>,
) -> Result<response::ResponseOpenResult, AppError> {
    let guard = state.begin_operation()?;
    let state = state.inner().clone();
    let root = super::resource_root(&app, "open-response")?;
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = guard;
        let (filename, bytes, origin, kind) = match source.as_str() {
            "native-example" | "simulation-example" => {
                let (filename, kind) = if source == "native-example" {
                    ("native-action-response.json", "native")
                } else {
                    ("state-response.json", "simulation")
                };
                (
                    filename.to_owned(),
                    resources::catalog_bytes(&root, filename)?,
                    "bundled",
                    kind,
                )
            }
            "native-file" => {
                let Some(file) = app
                    .dialog()
                    .file()
                    .set_title("Open native action rehearsal receipts")
                    .add_filter("JSON receipts", &["json"])
                    .blocking_pick_file()
                else {
                    return Ok(response::ResponseOpenResult::cancelled(request_id));
                };
                let path = file
                    .into_path()
                    .map_err(|e| AppError::new("open-response", "local-file", e.to_string()))?;
                let bytes = files::read_bounded(&path, 8 * 1024 * 1024, "open-response")?;
                (
                    path.file_name()
                        .unwrap_or_default()
                        .to_string_lossy()
                        .into_owned(),
                    bytes,
                    "openedFile",
                    "native",
                )
            }
            _ => {
                return Err(AppError::new(
                    "open-response",
                    "source",
                    "Choose a bundled response or explicitly open native rehearsal receipts.",
                ))
            }
        };
        state.open(
            request_id,
            filename,
            origin,
            kind,
            bytes,
            previous_response_id.as_deref(),
        )
    })
    .await
    .map_err(|e| AppError::new("open-response", "worker", e.to_string()))?
}

#[tauri::command]
pub fn get_response_frame(
    state: tauri::State<'_, response::ResponseState>,
    request_id: String,
    response_id: String,
    index: usize,
) -> Result<response::ResponseFrameResult, AppError> {
    state.frame(request_id, &response_id, index)
}
#[tauri::command]
pub fn get_response_event(
    state: tauri::State<'_, response::ResponseState>,
    request_id: String,
    response_id: String,
    index: usize,
) -> Result<response::ResponseEventResult, AppError> {
    state.event(request_id, &response_id, index)
}
#[tauri::command]
pub fn close_response(
    state: tauri::State<'_, response::ResponseState>,
    response_id: String,
) -> Result<(), AppError> {
    state.close(&response_id)
}
#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ResponseExportResult {
    request_id: String,
    response_id: String,
    file: Option<FileProof>,
}
#[tauri::command]
pub async fn export_response(
    app: tauri::AppHandle,
    state: tauri::State<'_, response::ResponseState>,
    request_id: String,
    response_id: String,
) -> Result<ResponseExportResult, AppError> {
    let guard = state.begin_operation()?;
    let (filename, bytes) = state.snapshot(&response_id)?;
    let root = super::resource_root(&app, "export-response")?;
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = guard;
        let file = if let Some(file) = app
            .dialog()
            .file()
            .set_title("Export original response evidence bytes")
            .set_file_name(&filename)
            .add_filter("JSON evidence", &["json"])
            .blocking_save_file()
        {
            let path = file
                .into_path()
                .map_err(|e| AppError::new("export-response", "local-file", e.to_string()))?;
            Some(files::atomic_export(&path, &bytes, &root)?)
        } else {
            None
        };
        Ok(ResponseExportResult {
            request_id,
            response_id,
            file,
        })
    })
    .await
    .map_err(|e| AppError::new("export-response", "worker", e.to_string()))?
}
