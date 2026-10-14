//! Bounded inspection of retained preparation reports. These are historical
//! receipts, not numerical records; parsing never changes their outcome or
//! follows a recorded file, endpoint, or command.
use crate::{ensure, CoreError, Result};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, HashSet};

pub const MAX_REPORT_BYTES: usize = 128 * 1024;
pub const INSPECTION_SCOPE: &str = "Bundled report identity and supported metadata structure only. Historical verification receipts are not a new numerical replay, a successful generation, or current model availability.";

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum ReportKind {
    Original,
    Correction,
    Retry,
}
impl ReportKind {
    pub const ALL: [Self; 3] = [Self::Original, Self::Correction, Self::Retry];
    pub fn id(self) -> &'static str {
        match self {
            Self::Original => "original",
            Self::Correction => "correction",
            Self::Retry => "retry",
        }
    }
    pub fn from_id(id: &str) -> Result<Self> {
        Self::ALL
            .into_iter()
            .find(|kind| kind.id() == id)
            .ok_or_else(|| CoreError::Invalid("Unknown preparation report identity.".into()))
    }
    pub fn filename(self) -> &'static str {
        match self {
            Self::Original => "guided-observation-recording.json",
            Self::Correction => "guided-observation-amendment.json",
            Self::Retry => "guided-observation-retry-20260916.json",
        }
    }
    pub fn export_filename(self) -> &'static str {
        match self {
            Self::Original => "active-state-preparation.json",
            Self::Correction => "active-state-protocol-correction.json",
            Self::Retry => "active-state-retry-20260916.json",
        }
    }
    pub fn title(self) -> &'static str {
        match self {
            Self::Original => "Original active-state preparation",
            Self::Correction => "Protocol correction · not executed",
            Self::Retry => "Separate active-state retry · September 16, 2026",
        }
    }
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ReportSummary {
    pub id: String,
    pub title: String,
    pub kind: ReportKind,
    pub status: String,
    pub filename: String,
    pub sha256: String,
    pub size_bytes: usize,
    pub summary: String,
}
#[derive(Clone, Debug, Serialize)]
pub struct ReportField {
    pub label: String,
    pub value: String,
}
#[derive(Clone, Debug, Serialize)]
pub struct ReportSection {
    pub title: String,
    pub fields: Vec<ReportField>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all(serialize = "camelCase"))]
pub struct Attempt {
    pub started_at_utc: Option<String>,
    pub finished_at_utc: Option<String>,
    pub exit_code: Option<i32>,
    pub record: Option<String>,
    pub verified: Option<bool>,
    pub verification: Option<String>,
    pub sha256: Option<String>,
    pub status: Option<String>,
    pub steps: Option<u32>,
    pub journal_counts: Option<BTreeMap<String, u32>>,
    pub request_count: Option<u32>,
}
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ReportView {
    pub schema: String,
    pub status: String,
    pub scope: Option<String>,
    pub inspection_scope: String,
    pub sections: Vec<ReportSection>,
    pub attempts: Vec<Attempt>,
}
pub struct InspectedReport {
    pub summary: ReportSummary,
    pub view: ReportView,
}

#[derive(Deserialize)]
struct Recording {
    schema: String,
    status: String,
    registered_at_utc: Option<String>,
    finished_at_utc: Option<String>,
    model_name: Option<String>,
    expected_model_digest: Option<String>,
    cli_sha256: Option<String>,
    fixture_sha256: Option<String>,
    specification: Option<Specification>,
    prompt_version: Option<u32>,
    word_instruction: Option<u32>,
    maximum_model_requests: Option<u32>,
    request_order: Option<Vec<String>>,
    scope: Option<String>,
    error: Option<String>,
    attempts: Vec<Attempt>,
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct Specification {
    prompt_version: Option<u32>,
    steps: Option<u32>,
    stopping_point: Option<String>,
    question: Option<String>,
    expected_difference: Option<String>,
    alternative_explanation: Option<String>,
    language: Option<Language>,
}
#[derive(Deserialize)]
struct Language {
    backend: Option<String>,
    endpoint: Option<String>,
    model: Option<String>,
}
#[derive(Deserialize)]
struct Reference {
    file: Option<String>,
    sha256: Option<String>,
    status: Option<String>,
    preserved_byte_for_byte: Option<bool>,
}
#[derive(Deserialize)]
struct Outcome {
    status: Option<String>,
    generation_attempts: Option<u32>,
    model_calls: Option<u32>,
    error: Option<String>,
}
#[derive(Deserialize)]
struct Execution {
    inventory_rechecked: Option<bool>,
    retries: Option<u32>,
    actual_network_requests: Option<u32>,
    actual_model_calls: Option<u32>,
    note: Option<String>,
}
#[derive(Deserialize)]
struct Qualification {
    status: Option<String>,
    tests: Option<u32>,
    cases: Option<Vec<String>>,
    actual_network_requests: Option<u32>,
    actual_model_calls: Option<u32>,
    actual_cli_executions: Option<u32>,
    checks: Option<Vec<String>>,
    scope: Option<String>,
}
#[derive(Deserialize)]
struct ManifestContract {
    prompt_version: Option<u32>,
    word_instruction: Option<u32>,
    temperature: Option<f64>,
    output_tokens: Option<u32>,
    context_tokens: Option<u32>,
    response_format: Option<String>,
}
#[derive(Deserialize)]
struct Amendment {
    schema: String,
    status: String,
    recorded_at_utc: Option<String>,
    original_receipt: Option<Reference>,
    original_recipe: Option<Reference>,
    discrepancy: Option<String>,
    correction: Option<String>,
    corrected_specification: Option<Specification>,
    corrected_manifest_contract: Option<ManifestContract>,
    original_outcome: Option<Outcome>,
    amendment_execution: Option<Execution>,
    qualification: Option<Qualification>,
    scope: Option<String>,
}
fn text<T: ToString>(value: Option<T>) -> String {
    value
        .map(|v| v.to_string())
        .unwrap_or_else(|| "Not retained".into())
}
fn field(label: &str, value: impl Into<String>) -> ReportField {
    ReportField {
        label: label.into(),
        value: value.into(),
    }
}
fn section(title: &str, fields: Vec<ReportField>) -> ReportSection {
    ReportSection {
        title: title.into(),
        fields,
    }
}
fn spec_fields(spec: Option<&Specification>) -> Vec<ReportField> {
    let language = spec.and_then(|s| s.language.as_ref());
    vec![
        field("Prompt version", text(spec.and_then(|s| s.prompt_version))),
        field("Planned steps", text(spec.and_then(|s| s.steps))),
        field(
            "Recorded source",
            text(language.and_then(|v| v.backend.as_deref())),
        ),
        field(
            "Configured model",
            text(language.and_then(|v| v.model.as_deref())),
        ),
        field(
            "Historical endpoint · text only",
            text(language.and_then(|v| v.endpoint.as_deref())),
        ),
        field("Question", text(spec.and_then(|s| s.question.as_deref()))),
        field(
            "Expected difference",
            text(spec.and_then(|s| s.expected_difference.as_deref())),
        ),
        field(
            "Alternative explanation",
            text(spec.and_then(|s| s.alternative_explanation.as_deref())),
        ),
        field(
            "Frozen stopping point",
            text(spec.and_then(|s| s.stopping_point.as_deref())),
        ),
    ]
}
fn decode<T: for<'a> Deserialize<'a>>(bytes: &[u8]) -> Result<T> {
    ensure(
        bytes.len() <= MAX_REPORT_BYTES,
        "Preparation report exceeds 128 KiB inspection limit.",
    )?;
    serde_json::from_slice(bytes)
        .map_err(|e| CoreError::Invalid(format!("Invalid preparation metadata: {e}")))
}

pub fn inspect(kind: ReportKind, bytes: &[u8]) -> Result<InspectedReport> {
    let (view, summary) = if kind == ReportKind::Correction {
        let v: Amendment = decode(bytes)?;
        ensure(
            v.schema == "reservoir-scope.guided-observation-protocol-amendment.v1",
            "Unsupported preparation correction schema.",
        )?;
        let mut sections = vec![
            section(
                "Correction retained separately",
                vec![
                    field("Recorded at UTC", text(v.recorded_at_utc)),
                    field("Discrepancy", text(v.discrepancy)),
                    field("Correction", text(v.correction)),
                ],
            ),
            section(
                "Corrected specification",
                spec_fields(v.corrected_specification.as_ref()),
            ),
        ];
        if let Some(c) = v.corrected_manifest_contract {
            sections.push(section(
                "Corrected manifest contract",
                vec![
                    field("Manifest prompt version", text(c.prompt_version)),
                    field("Word instruction", text(c.word_instruction)),
                    field("Temperature", text(c.temperature)),
                    field("Output tokens", text(c.output_tokens)),
                    field("Context tokens", text(c.context_tokens)),
                    field("Response format", text(c.response_format)),
                ],
            ));
        }
        for (title, reference) in [
            ("Original receipt reference", v.original_receipt),
            ("Original recipe reference", v.original_recipe),
        ] {
            if let Some(r) = reference {
                sections.push(section(
                    title,
                    vec![
                        field("Historical filename · not followed", text(r.file)),
                        field("SHA-256 recorded in correction", text(r.sha256)),
                        field("Recorded status", text(r.status)),
                        field(
                            "Preserved byte for byte · historical claim",
                            text(r.preserved_byte_for_byte),
                        ),
                    ],
                ));
            }
        }
        if let Some(o) = v.original_outcome {
            sections.push(section(
                "Original outcome retained by correction",
                vec![
                    field("Recorded status", text(o.status)),
                    field("Generation attempts", text(o.generation_attempts)),
                    field("Model calls", text(o.model_calls)),
                    field("Error", text(o.error)),
                ],
            ));
        }
        if let Some(e) = v.amendment_execution {
            sections.push(section(
                "Correction execution receipt",
                vec![
                    field("Inventory rechecked", text(e.inventory_rechecked)),
                    field("Retries", text(e.retries)),
                    field("Actual network requests", text(e.actual_network_requests)),
                    field("Actual model calls", text(e.actual_model_calls)),
                    field("Note", text(e.note)),
                ],
            ));
        }
        if let Some(q) = v.qualification {
            sections.push(section(
                "Historical protocol preparation qualification",
                vec![
                    field("Recorded qualification status", text(q.status)),
                    field("Tests", text(q.tests)),
                    field("Cases", text(q.cases.map(|v| v.join("\n")))),
                    field("Checks", text(q.checks.map(|v| v.join("\n")))),
                    field("Actual network requests", text(q.actual_network_requests)),
                    field("Actual model calls", text(q.actual_model_calls)),
                    field("Actual CLI executions", text(q.actual_cli_executions)),
                    field("Qualification scope", text(q.scope)),
                ],
            ));
        }
        (ReportView {schema:v.schema,status:v.status,scope:v.scope,inspection_scope:INSPECTION_SCOPE.into(),sections,attempts:vec![]},"The protocol correction is a separate retained receipt. Its preparation qualification does not supply a model-written example.".into())
    } else {
        let v: Recording = decode(bytes)?;
        ensure(
            v.schema == "reservoir-scope.guided-observation-recording.v1",
            "Unsupported preparation report schema.",
        )?;
        ensure(
            v.attempts.len() <= 64,
            "Preparation report exceeds 64 retained attempts.",
        )?;
        for a in &v.attempts {
            ensure(
                a.journal_counts.as_ref().is_none_or(|v| v.len() <= 16),
                "Preparation attempt exceeds 16 journal-count groups.",
            )?;
        }
        let summary = v.error.clone().unwrap_or_else(|| if v.status == "failed" { "Partial recording retained. Its verification receipt does not change the failed run outcome.".into() } else { "One bounded attempt; all recorded outcomes retained.".into() });
        let sections = vec![
            section(
                "Preparation receipt",
                vec![
                    field("Registered at UTC", text(v.registered_at_utc)),
                    field("Finished at UTC", text(v.finished_at_utc)),
                    field("Recorded model name", text(v.model_name)),
                    field("Expected model digest", text(v.expected_model_digest)),
                    field("CLI SHA-256", text(v.cli_sha256)),
                    field("Fixture SHA-256", text(v.fixture_sha256)),
                    field("Error", text(v.error)),
                    field("Maximum model requests", text(v.maximum_model_requests)),
                    field(
                        "Request order",
                        text(v.request_order.map(|v| v.join(" → "))),
                    ),
                    field("Manifest prompt version", text(v.prompt_version)),
                    field("Word instruction", text(v.word_instruction)),
                ],
            ),
            section(
                "Frozen specification",
                spec_fields(v.specification.as_ref()),
            ),
        ];
        (
            ReportView {
                schema: v.schema,
                status: v.status,
                scope: v.scope,
                inspection_scope: INSPECTION_SCOPE.into(),
                sections,
                attempts: v.attempts,
            },
            summary,
        )
    };
    ensure(
        !view.status.is_empty(),
        "Preparation report status is empty.",
    )?;
    let summary = ReportSummary {
        id: kind.id().into(),
        title: kind.title().into(),
        kind,
        status: view.status.clone(),
        filename: kind.filename().into(),
        sha256: format!("{:x}", Sha256::digest(bytes)),
        size_bytes: bytes.len(),
        summary,
    };
    Ok(InspectedReport { summary, view })
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct PreparationExample {
    pub id: String,
    pub title: String,
    pub provenance: String,
    pub format: String,
}
#[derive(Deserialize)]
struct CatalogEntry {
    id: String,
    title: String,
    provenance: String,
    format: String,
    file: String,
    group: Option<String>,
    order: Option<i32>,
}
pub fn examples(bytes: &[u8]) -> Result<Vec<PreparationExample>> {
    let catalog: Vec<CatalogEntry> = decode(bytes)?;
    ensure(catalog.len() <= 128, "Example catalog exceeds 128 entries.")?;
    let mut selected: Vec<_> = catalog
        .into_iter()
        .filter(|e| e.group.as_deref() == Some("preparation"))
        .collect();
    let mut ids = HashSet::new();
    for e in &selected {
        let ordinal =
            e.id.strip_prefix("example-preparation-")
                .and_then(|v| v.parse::<u8>().ok());
        ensure(
            matches!(ordinal, Some(1..=4))
                && e.file == format!("{}.json", e.id)
                && ids.insert(e.id.clone()),
            "Unrecognized or duplicate preparation example identity.",
        )?;
    }
    selected.sort_by(|a, b| {
        a.order
            .unwrap_or(0)
            .cmp(&b.order.unwrap_or(0))
            .then(a.id.cmp(&b.id))
    });
    Ok(selected
        .into_iter()
        .map(|e| PreparationExample {
            id: e.id,
            title: e.title,
            provenance: e.provenance,
            format: e.format,
        })
        .collect())
}

#[cfg(test)]
mod tests {
    use super::*;
    fn source(kind: ReportKind) -> Vec<u8> {
        std::fs::read(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("../../../../essentials/examples/portable")
                .join(kind.filename()),
        )
        .unwrap()
    }
    #[test]
    fn retained_outcomes_and_native_summary_remain_distinct() {
        let original = inspect(ReportKind::Original, &source(ReportKind::Original)).unwrap();
        assert_eq!(original.view.status, "unavailable");
        assert!(original.view.attempts.is_empty());
        assert!(original.summary.summary.contains("Connection refused"));
        let correction = inspect(ReportKind::Correction, &source(ReportKind::Correction)).unwrap();
        assert_eq!(
            correction.view.status,
            "corrected_protocol_frozen_not_executed"
        );
        assert!(correction.view.attempts.is_empty());
        assert!(correction
            .view
            .sections
            .iter()
            .flat_map(|s| &s.fields)
            .any(|f| f.label == "Actual model calls" && f.value == "0"));
        assert!(correction
            .view
            .sections
            .iter()
            .any(|s| s.title == "Corrected manifest contract"
                && s.fields
                    .iter()
                    .any(|f| f.label == "Manifest prompt version" && f.value == "2")));
        let retry = inspect(ReportKind::Retry, &source(ReportKind::Retry)).unwrap();
        let a = &retry.view.attempts[0];
        assert_eq!(retry.view.status, "failed");
        assert_eq!(a.status.as_deref(), Some("failed"));
        assert_eq!(a.verified, Some(true));
        assert_eq!(a.steps, Some(60));
        assert_eq!(a.request_count, Some(4));
        assert_eq!(a.journal_counts.as_ref().unwrap().values().sum::<u32>(), 3);
        assert!(retry.summary.summary.contains("Partial recording retained"));
    }
    #[test]
    fn exact_byte_identity_includes_whitespace_and_does_not_rewrite_original() {
        let mut b = source(ReportKind::Original);
        let before = b.clone();
        let first = inspect(ReportKind::Original, &b).unwrap();
        assert_eq!(b, before);
        b.push(b'\n');
        let next = inspect(ReportKind::Original, &b).unwrap();
        assert_ne!(first.summary.sha256, next.summary.sha256);
        assert_eq!(next.summary.size_bytes, first.summary.size_bytes + 1);
    }
    #[test]
    fn missing_receipts_are_unknown_not_zero_or_success() {
        let report=inspect(ReportKind::Retry,br#"{"schema":"reservoir-scope.guided-observation-recording.v1","status":"failed","attempts":[{}]}"#).unwrap();
        let a = &report.view.attempts[0];
        assert!(a.verified.is_none());
        assert!(a.steps.is_none());
        assert!(a.request_count.is_none());
        assert!(a.journal_counts.is_none());
    }
    #[test]
    fn unknown_fields_cannot_promote_outcome_and_historical_paths_are_inert() {
        let mut v: serde_json::Value = serde_json::from_slice(&source(ReportKind::Retry)).unwrap();
        v["verified"] = true.into();
        v["url"] = "http://untrusted.invalid".into();
        v["attempts"][0]["record"] = "../../not-followed.json".into();
        let report = inspect(ReportKind::Retry, &serde_json::to_vec(&v).unwrap()).unwrap();
        assert_eq!(report.view.status, "failed");
        assert_eq!(
            report.view.attempts[0].record.as_deref(),
            Some("../../not-followed.json")
        );
        assert!(!serde_json::to_string(&report.view)
            .unwrap()
            .contains("untrusted.invalid"));
    }
    #[test]
    fn invalid_schema_type_and_bounds_are_visible_errors() {
        assert!(inspect(ReportKind::Original, &source(ReportKind::Correction)).is_err());
        assert!(inspect(ReportKind::Original, &vec![b' '; MAX_REPORT_BYTES + 1]).is_err());
        let mut v: serde_json::Value = serde_json::from_slice(&source(ReportKind::Retry)).unwrap();
        v["attempts"][0]["verified"] = "true".into();
        assert!(inspect(ReportKind::Retry, &serde_json::to_vec(&v).unwrap()).is_err());
        v["attempts"] = serde_json::Value::Array(vec![serde_json::json!({}); 65]);
        assert!(inspect(ReportKind::Retry, &serde_json::to_vec(&v).unwrap()).is_err());
        assert!(ReportKind::from_id("../../report").is_err());
    }
    #[test]
    fn catalog_keeps_all_four_attempts_in_order_without_following_files() {
        let bytes = std::fs::read(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("../../../../essentials/examples/portable/examples-index.json"),
        )
        .unwrap();
        let found = examples(&bytes).unwrap();
        assert_eq!(found.len(), 4);
        assert_eq!(found[0].id, "example-preparation-1");
        assert!(found[2].provenance.contains("failed"));
        assert!(found[3].provenance.contains("completed"));
        let mut v: Vec<serde_json::Value> = serde_json::from_slice(&bytes).unwrap();
        let item = v
            .iter_mut()
            .find(|e| e["id"] == "example-preparation-1")
            .unwrap();
        item["file"] = "../secret.json".into();
        assert!(examples(&serde_json::to_vec(&v).unwrap()).is_err());
    }
}
