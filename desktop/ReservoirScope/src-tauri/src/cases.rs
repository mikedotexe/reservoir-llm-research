use crate::files::{self, digest, AppError, FileProof};
use reservoir_core::cases::{CaseCatalog, ResearchCase, SCOPE};
use serde::Serialize;
use std::{
    collections::HashMap,
    sync::{
        atomic::{AtomicBool, AtomicU64, Ordering},
        Arc, Mutex,
    },
};
use tauri_plugin_dialog::DialogExt;

#[derive(Clone, Default)]
pub struct CaseState {
    inner: Arc<Mutex<HashMap<String, Stored>>>,
    serial: Arc<AtomicU64>,
    busy: Arc<AtomicBool>,
}
struct Stored {
    filename: String,
    bytes: Arc<Vec<u8>>,
    catalog: CaseCatalog,
}
pub struct CaseGuard(Arc<AtomicBool>);
impl Drop for CaseGuard {
    fn drop(&mut self) {
        self.0.store(false, Ordering::Release)
    }
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CatalogSummary {
    pub catalog_id: String,
    pub filename: String,
    pub origin: String,
    pub sha256: String,
    pub scope: String,
    pub cases: Vec<CaseSummary>,
}
#[derive(Clone, Serialize)]
pub struct CaseSummary {
    pub id: String,
    pub title: String,
    pub question: String,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CaseOpenResult {
    pub request_id: String,
    pub cancelled: bool,
    pub catalog: Option<CatalogSummary>,
}
impl CaseOpenResult {
    pub fn cancelled(request_id: String) -> Self {
        Self {
            request_id,
            cancelled: true,
            catalog: None,
        }
    }
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CaseViewResult {
    pub request_id: String,
    pub catalog_id: String,
    pub index: usize,
    pub research_case: ResearchCase,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SelectedCaseExportResult {
    pub request_id: String,
    pub catalog_id: String,
    pub index: usize,
    pub case_id: String,
    pub source_catalog_sha256: String,
    pub file: Option<FileProof>,
}
pub struct SelectedCaseSnapshot {
    pub filename: String,
    pub bytes: Vec<u8>,
    pub source_catalog_sha256: String,
}

fn selected_filename(id: &str) -> String {
    // Native ASCII filename policy, bounded for ordinary desktop filesystems.
    // The complete original ID stays in the derivative and response.
    let safe: String = id
        .chars()
        .filter(|c| c.is_ascii_alphanumeric() || *c == '-' || *c == '_')
        .take(120)
        .collect();
    format!(
        "{}.json",
        if safe.is_empty() {
            "reviewed-research-case"
        } else {
            &safe
        }
    )
}
impl CaseState {
    pub fn begin_operation(&self) -> Result<CaseGuard, AppError> {
        self.busy
            .compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
            .map_err(|_| {
                AppError::new(
                    "cases",
                    "busy",
                    "A case file operation is already in progress.",
                )
            })?;
        Ok(CaseGuard(self.busy.clone()))
    }
    pub fn open(
        &self,
        request_id: String,
        filename: String,
        origin: &str,
        bytes: Vec<u8>,
    ) -> Result<CaseOpenResult, AppError> {
        let catalog = CaseCatalog::decode(&bytes)
            .map_err(|e| AppError::new("open-cases", "verification", e.to_string()))?;
        let mut store = self
            .inner
            .lock()
            .map_err(|_| AppError::new("cases", "state", "Case state unavailable."))?;
        if store.len() >= 4
            || store.values().map(|v| v.bytes.len()).sum::<usize>() + bytes.len()
                > 128 * 1024 * 1024
        {
            return Err(AppError::new(
                "open-cases",
                "capacity",
                "Close an open case catalog before opening another.",
            ));
        }
        let id = format!(
            "case-catalog-{}",
            self.serial.fetch_add(1, Ordering::Relaxed)
        );
        let summary = CatalogSummary {
            catalog_id: id.clone(),
            filename: filename.clone(),
            origin: origin.into(),
            sha256: digest(&bytes),
            scope: SCOPE.into(),
            cases: catalog
                .cases
                .iter()
                .map(|v| CaseSummary {
                    id: v.id.clone(),
                    title: v.title.clone(),
                    question: v.question.clone(),
                })
                .collect(),
        };
        store.insert(
            id,
            Stored {
                filename,
                bytes: Arc::new(bytes),
                catalog,
            },
        );
        Ok(CaseOpenResult {
            request_id,
            cancelled: false,
            catalog: Some(summary),
        })
    }
    pub fn view(
        &self,
        request_id: String,
        catalog_id: String,
        index: usize,
    ) -> Result<CaseViewResult, AppError> {
        let store = self
            .inner
            .lock()
            .map_err(|_| AppError::new("cases", "state", "Case state unavailable."))?;
        let case = store
            .get(&catalog_id)
            .and_then(|s| s.catalog.cases.get(index))
            .ok_or_else(|| {
                AppError::new("read-case", "identity", "This case is no longer available.")
            })?
            .clone();
        Ok(CaseViewResult {
            request_id,
            catalog_id,
            index,
            research_case: case,
        })
    }
    pub fn snapshot(&self, id: &str) -> Result<(String, Arc<Vec<u8>>), AppError> {
        let store = self
            .inner
            .lock()
            .map_err(|_| AppError::new("cases", "state", "Case state unavailable."))?;
        let v = store.get(id).ok_or_else(|| {
            AppError::new(
                "export-cases",
                "identity",
                "This case catalog is no longer available.",
            )
        })?;
        Ok((v.filename.clone(), v.bytes.clone()))
    }
    pub fn selected_snapshot(
        &self,
        id: &str,
        index: usize,
        case_id: &str,
    ) -> Result<SelectedCaseSnapshot, AppError> {
        let (selected, original) = {
            let store = self.inner.lock().map_err(|_| {
                AppError::new("export-selected-case", "state", "Case state unavailable.")
            })?;
            let stored = store.get(id).ok_or_else(|| {
                AppError::new(
                    "export-selected-case",
                    "identity",
                    "This case catalog is no longer available.",
                )
            })?;
            let item = stored.catalog.cases.get(index).filter(|item| item.id == case_id)
                .ok_or_else(|| AppError::new("export-selected-case", "identity", "The selected case is no longer available. Select it again before exporting."))?;
            (
                CaseCatalog {
                    format: stored.catalog.format.clone(),
                    cases: vec![item.clone()],
                },
                stored.bytes.clone(),
            )
        };
        let bytes = selected
            .selected_encoded(0, case_id)
            .map_err(|e| AppError::new("export-selected-case", "verification", e.to_string()))?;
        Ok(SelectedCaseSnapshot {
            filename: selected_filename(case_id),
            bytes,
            source_catalog_sha256: digest(&original),
        })
    }
    pub fn close(&self, id: &str) -> Result<(), AppError> {
        self.inner
            .lock()
            .map_err(|_| AppError::new("cases", "state", "Case state unavailable."))?
            .remove(id);
        Ok(())
    }
}

#[tauri::command]
pub async fn export_selected_case(
    app: tauri::AppHandle,
    state: tauri::State<'_, CaseState>,
    request_id: String,
    catalog_id: String,
    index: usize,
    case_id: String,
) -> Result<SelectedCaseExportResult, AppError> {
    let guard = state.begin_operation()?;
    let state = state.inner().clone();
    let root = crate::resource_root(&app, "export-selected-case")?;
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = guard;
        // Construct and check identity before displaying the destination dialog.
        // Cancellation and any verification error leave the accepted catalog alone.
        let selected = state.selected_snapshot(&catalog_id, index, &case_id)?;
        let file = if let Some(file) = app
            .dialog()
            .file()
            .set_title("Export selected case with embedded evidence")
            .set_file_name(&selected.filename)
            .add_filter("JSON", &["json"])
            .blocking_save_file()
        {
            let path = file
                .into_path()
                .map_err(|e| AppError::new("export-selected-case", "local-file", e.to_string()))?;
            Some(files::atomic_export(&path, &selected.bytes, &root)?)
        } else {
            None
        };
        Ok(SelectedCaseExportResult {
            request_id,
            catalog_id,
            index,
            case_id,
            source_catalog_sha256: selected.source_catalog_sha256,
            file,
        })
    })
    .await
    .map_err(|e| AppError::new("export-selected-case", "worker", e.to_string()))?
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_replacement_retains_accepted_bytes_and_views() {
        let bytes = std::fs::read(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("resources/research-cases-v1.json"),
        )
        .unwrap();
        let s = CaseState::default();
        let result = s
            .open("one".into(), "cases.json".into(), "external", bytes.clone())
            .unwrap();
        let id = result.catalog.unwrap().catalog_id;
        assert!(s
            .open("bad".into(), "bad.json".into(), "external", b"{}".to_vec())
            .is_err());
        assert_eq!(s.snapshot(&id).unwrap().1.as_slice(), bytes);
        assert_eq!(s.view("read".into(), id.clone(), 0).unwrap().index, 0);
        assert!(s.view("bad-index".into(), id.clone(), 99).is_err());
        s.close(&id).unwrap();
        assert!(s.snapshot(&id).is_err());
    }
    #[test]
    fn selected_export_is_independent_preserves_original_and_rejects_stale_selection() {
        let mut bytes = include_bytes!("../resources/research-cases-v1.json").to_vec();
        bytes.extend_from_slice(b"\n  \n");
        let state = CaseState::default();
        let opened = state
            .open(
                "open".into(),
                "original.json".into(),
                "external",
                bytes.clone(),
            )
            .unwrap();
        let catalog = opened.catalog.unwrap();
        let selected = state
            .selected_snapshot(&catalog.catalog_id, 1, &catalog.cases[1].id)
            .unwrap();
        let derivative = CaseCatalog::decode(&selected.bytes).unwrap();
        assert_eq!(derivative.cases.len(), 1);
        assert_eq!(derivative.cases[0].id, catalog.cases[1].id);
        assert_eq!(selected.source_catalog_sha256, digest(&bytes));
        assert!(state
            .selected_snapshot(&catalog.catalog_id, 1, &catalog.cases[0].id)
            .is_err());
        assert!(state
            .selected_snapshot(&catalog.catalog_id, 99, &catalog.cases[1].id)
            .is_err());
        assert_eq!(
            state.snapshot(&catalog.catalog_id).unwrap().1.as_slice(),
            bytes
        );
        assert_eq!(
            state
                .view("read".into(), catalog.catalog_id.clone(), 1)
                .unwrap()
                .research_case
                .id,
            catalog.cases[1].id
        );
        let dir = tempfile::tempdir().unwrap();
        let file = dir.path().join("選択された事例.json");
        let proof =
            files::atomic_export(&file, &selected.bytes, &dir.path().join("resources")).unwrap();
        let reopened = state
            .open(
                "reopen".into(),
                proof.name,
                "external",
                std::fs::read(file).unwrap(),
            )
            .unwrap();
        assert_eq!(reopened.catalog.unwrap().cases.len(), 1);
        state.close(&catalog.catalog_id).unwrap();
        assert!(state
            .selected_snapshot(&catalog.catalog_id, 1, &catalog.cases[1].id)
            .is_err());
        assert!(CaseCatalog::decode(&selected.bytes).is_ok());
    }
    #[test]
    fn selected_export_suggests_a_safe_bounded_filename_and_serializes_dialogs() {
        assert_eq!(
            selected_filename("../../<script>é-abc_42"),
            "script-abc_42.json"
        );
        assert_eq!(selected_filename("👩‍🔬研究"), "reviewed-research-case.json");
        assert_eq!(selected_filename(&"a".repeat(300)).len(), 125);
        let state = CaseState::default();
        let guard = state.begin_operation().unwrap();
        assert!(state.begin_operation().is_err());
        drop(guard);
        assert!(state.begin_operation().is_ok());
    }
}
