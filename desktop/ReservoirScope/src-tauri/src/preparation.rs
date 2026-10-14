use crate::{
    files::{self, AppError, FileProof},
    resources,
};
use reservoir_core::preparation::{
    self, InspectedReport, PreparationExample, ReportKind, ReportSummary, ReportView,
};
use serde::Serialize;
use std::{
    path::Path,
    sync::atomic::{AtomicBool, Ordering},
};
use tauri_plugin_dialog::DialogExt;

static EXPORTING: AtomicBool = AtomicBool::new(false);
struct ExportGuard;
impl ExportGuard {
    fn acquire() -> Result<Self, AppError> {
        EXPORTING
            .compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
            .map_err(|_| {
                AppError::new(
                    "export-preparation-report",
                    "busy",
                    "A preparation report export is already in progress.",
                )
            })?;
        Ok(Self)
    }
}
impl Drop for ExportGuard {
    fn drop(&mut self) {
        EXPORTING.store(false, Ordering::Release);
    }
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct HistoryResult {
    pub request_id: String,
    pub reports: Vec<ReportSummary>,
    pub examples: Vec<PreparationExample>,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ReportResult {
    pub request_id: String,
    pub report_id: String,
    pub sha256: String,
    pub report: ReportView,
    pub retained_example_id: Option<String>,
    pub retained_example_diagnostic: Option<String>,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ExportResult {
    pub request_id: String,
    pub report_id: String,
    pub source_sha256: String,
    pub file: Option<FileProof>,
}
fn metadata_error(error: impl ToString) -> AppError {
    AppError::new("preparation-history", "metadata", error.to_string())
}
fn load(root: &Path, kind: ReportKind) -> Result<(Vec<u8>, InspectedReport), AppError> {
    let bytes = resources::catalog_bytes(root, kind.filename())?;
    let inspected = preparation::inspect(kind, &bytes).map_err(metadata_error)?;
    Ok((bytes, inspected))
}
pub fn history(root: &Path, request_id: String) -> Result<HistoryResult, AppError> {
    let reports = ReportKind::ALL
        .into_iter()
        .map(|kind| load(root, kind).map(|(_, r)| r.summary))
        .collect::<Result<Vec<_>, _>>()?;
    let examples = preparation::examples(&resources::catalog_bytes(root, "examples-index.json")?)
        .map_err(metadata_error)?;
    Ok(HistoryResult {
        request_id,
        reports,
        examples,
    })
}
pub fn report(
    root: &Path,
    request_id: String,
    report_id: String,
) -> Result<ReportResult, AppError> {
    let kind = ReportKind::from_id(&report_id).map_err(metadata_error)?;
    let (_, inspected) = load(root, kind)?;
    let (retained_example_id, retained_example_diagnostic) =
        retry_binding(root, kind, &inspected.view);
    Ok(ReportResult {
        request_id,
        report_id,
        sha256: inspected.summary.sha256,
        report: inspected.view,
        retained_example_id,
        retained_example_diagnostic,
    })
}
fn retry_binding(
    root: &Path,
    kind: ReportKind,
    view: &ReportView,
) -> (Option<String>, Option<String>) {
    if kind != ReportKind::Retry {
        return (None, None);
    }
    // Only this independently compiled example may be linked. The receipt's
    // filename is compared as text and is never used to construct a path.
    const NAME: &str = "example-model-observation-active.json";
    let matched = view.attempts.len() == 1 && view.attempts[0].record.as_deref() == Some(NAME);
    if !matched {
        return (
            None,
            Some("No bundled retry recording matched the retained report identity.".into()),
        );
    }
    match resources::catalog_bytes(root, NAME) {
        Ok(bytes) if view.attempts[0].sha256.as_deref() == Some(files::digest(&bytes).as_str()) => (Some("example-model-observation-active".into()), None),
        Ok(_) => (None, Some("The bundled retry recording hash differs from this report’s retained SHA-256. No link was accepted.".into())),
        Err(error) => (None, Some(format!("The retained report is readable, but its bundled retry recording is unavailable: {}", error.message))),
    }
}
fn export_snapshot(
    root: &Path,
    report_id: &str,
    expected_sha256: &str,
) -> Result<(ReportKind, Vec<u8>, String), AppError> {
    let kind = ReportKind::from_id(report_id).map_err(metadata_error)?;
    let (bytes, inspected) = load(root, kind)?;
    if inspected.summary.sha256 != expected_sha256 {
        return Err(AppError::new("export-preparation-report","identity","The report identity differs from the selected history entry. Refresh before exporting."));
    }
    Ok((kind, bytes, inspected.summary.sha256))
}
#[tauri::command]
pub async fn list_preparation_history(
    app: tauri::AppHandle,
    request_id: String,
) -> Result<HistoryResult, AppError> {
    let root = crate::resource_root(&app, "preparation-history")?;
    tauri::async_runtime::spawn_blocking(move || history(&root, request_id))
        .await
        .map_err(|e| AppError::new("preparation-history", "worker", e.to_string()))?
}
#[tauri::command]
pub async fn get_preparation_report(
    app: tauri::AppHandle,
    request_id: String,
    report_id: String,
) -> Result<ReportResult, AppError> {
    let root = crate::resource_root(&app, "preparation-report")?;
    tauri::async_runtime::spawn_blocking(move || report(&root, request_id, report_id))
        .await
        .map_err(|e| AppError::new("preparation-report", "worker", e.to_string()))?
}
#[tauri::command]
pub async fn export_preparation_report(
    app: tauri::AppHandle,
    request_id: String,
    report_id: String,
    expected_sha256: String,
) -> Result<ExportResult, AppError> {
    let guard = ExportGuard::acquire()?;
    let root = crate::resource_root(&app, "export-preparation-report")?;
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = guard;
        // Fixed catalog identity and expected byte hash are checked before the dialog.
        // Neither source-receipt filenames nor endpoints can select a file or action.
        let (kind, bytes, source_sha256) = export_snapshot(&root, &report_id, &expected_sha256)?;
        let file = if let Some(file) = app
            .dialog()
            .file()
            .set_title("Export original preparation report bytes")
            .set_file_name(kind.export_filename())
            .add_filter("JSON", &["json"])
            .blocking_save_file()
        {
            let path = file.into_path().map_err(|e| {
                AppError::new("export-preparation-report", "local-file", e.to_string())
            })?;
            Some(files::atomic_export(&path, &bytes, &root)?)
        } else {
            None
        };
        Ok(ExportResult {
            request_id,
            report_id,
            source_sha256,
            file,
        })
    })
    .await
    .map_err(|e| AppError::new("export-preparation-report", "worker", e.to_string()))?
}

#[cfg(test)]
mod tests {
    use super::*;
    fn root() -> std::path::PathBuf {
        Path::new(env!("CARGO_MANIFEST_DIR")).join("resources")
    }
    #[test]
    fn report_views_preserve_failed_outcome_and_historical_verification() {
        let h = history(&root(), "list".into()).unwrap();
        assert_eq!(h.reports.len(), 3);
        assert_eq!(h.examples.len(), 4);
        let v = report(&root(), "detail".into(), "retry".into()).unwrap();
        assert_eq!(v.sha256, h.reports[2].sha256);
        assert_eq!(v.report.status, "failed");
        assert_eq!(v.report.attempts[0].verified, Some(true));
        assert_eq!(
            v.retained_example_id.as_deref(),
            Some("example-model-observation-active")
        );
        assert!(v.retained_example_diagnostic.is_none());
    }
    #[test]
    fn export_snapshot_is_exact_and_rejects_stale_or_path_identities() {
        for kind in ReportKind::ALL {
            let original = std::fs::read(root().join(kind.filename())).unwrap();
            let (_, bytes, hash) =
                export_snapshot(&root(), kind.id(), &files::digest(&original)).unwrap();
            assert_eq!(original, bytes);
            let dir = tempfile::tempdir().unwrap();
            let destination = dir.path().join("保留された報告.json");
            let proof = files::atomic_export(&destination, &bytes, &root()).unwrap();
            assert_eq!(proof.sha256, hash);
            assert_eq!(std::fs::read(destination).unwrap(), original);
            assert!(export_snapshot(&root(), kind.id(), &"0".repeat(64)).is_err());
        }
        assert!(export_snapshot(&root(), "../../anything.json", "").is_err());
    }
    #[test]
    fn altered_package_report_is_rejected_before_display_or_export() {
        let dir = tempfile::tempdir().unwrap();
        let mut bytes = std::fs::read(root().join(ReportKind::Original.filename())).unwrap();
        bytes.push(b'\n');
        std::fs::write(dir.path().join(ReportKind::Original.filename()), &bytes).unwrap();
        assert!(report(dir.path(), "changed".into(), "original".into()).is_err());
        assert!(export_snapshot(dir.path(), "original", &files::digest(&bytes)).is_err());
    }
    #[test]
    fn retry_binding_requires_fixed_name_and_matching_bytes_without_following_paths() {
        let mut view = report(&root(), "test".into(), "retry".into())
            .unwrap()
            .report;
        view.attempts[0].record = Some("../../example-model-observation-active.json".into());
        assert!(retry_binding(&root(), ReportKind::Retry, &view).0.is_none());
        view.attempts[0].record = Some("example-model-observation-active.json".into());
        view.attempts[0].sha256 = Some("0".repeat(64));
        let missing = retry_binding(&root(), ReportKind::Retry, &view);
        assert!(missing.0.is_none());
        assert!(missing.1.unwrap().contains("differs"));
        let dir = tempfile::tempdir().unwrap();
        assert!(retry_binding(dir.path(), ReportKind::Retry, &view)
            .1
            .unwrap()
            .contains("unavailable"));
        assert_eq!(
            retry_binding(&root(), ReportKind::Original, &view),
            (None, None)
        );
    }
}
