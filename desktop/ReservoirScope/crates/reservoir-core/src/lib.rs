//! Offline, explicitly scoped record verification. This crate never contacts a
//! model, follows embedded source paths, or modifies imported record bytes.
pub mod actions;
pub mod cases;
pub mod codec;
pub mod comparison;
pub mod exploration;
pub mod geometry;
pub mod guided_evidence;
pub mod math;
pub mod observatory;
pub mod preparation;
mod prompt_number;
pub mod regulation;
pub mod response;
pub mod session;
pub mod stage;
pub mod sustained;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{fmt, fs::File, io::Read, path::Path};

pub const MAX_RECORD_BYTES: usize = 256 * 1024 * 1024;
pub const VERIFICATION_SCOPE: &str = "Supported family structure and numerical replay; retained prompts and bounded qualified Unicode text codec where applicable. Unqualified scalars/graphemes and parser cases remain incomplete; not full desktop or M1 parity.";

#[derive(Debug)]
pub enum CoreError {
    Invalid(String),
    Unsupported(String),
}
impl fmt::Display for CoreError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Invalid(s) | Self::Unsupported(s) => f.write_str(s),
        }
    }
}
impl std::error::Error for CoreError {}
pub type Result<T> = std::result::Result<T, CoreError>;
pub(crate) fn ensure(condition: bool, message: &str) -> Result<()> {
    if condition {
        Ok(())
    } else {
        Err(CoreError::Invalid(message.into()))
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum VerificationStatus {
    Passed,
    Failed,
    Incomplete,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct VerificationReport {
    pub schema: String,
    pub status: VerificationStatus,
    pub format: Option<String>,
    pub scope: String,
    pub checked_steps: usize,
    pub checked_turns: usize,
    pub sha256: Option<String>,
    pub models_contacted: bool,
    pub diagnostics: Vec<String>,
}
impl VerificationReport {
    fn initial(bytes: Option<&[u8]>) -> Self {
        Self {
            schema: "reservoir-core-verification-v1".into(),
            status: VerificationStatus::Incomplete,
            format: None,
            scope: VERIFICATION_SCOPE.into(),
            checked_steps: 0,
            checked_turns: 0,
            sha256: bytes.map(|v| format!("{:x}", Sha256::digest(v))),
            models_contacted: false,
            diagnostics: vec![],
        }
    }
    pub fn exit_code(&self) -> i32 {
        match self.status {
            VerificationStatus::Passed => 0,
            VerificationStatus::Failed => 1,
            VerificationStatus::Incomplete => 2,
        }
    }
}

/// Original bytes are authoritative for copying/exporting an imported record.
/// A decoded StageRecord is only an inspection view; serializing it is not a
/// substitute for preserving the imported file (unknown fields/whitespace matter).
pub struct RecordInspection {
    pub original_bytes: Vec<u8>,
    pub report: VerificationReport,
    pub stage_record: Option<stage::StageRecord>,
}

pub fn inspect_bytes(original_bytes: Vec<u8>) -> RecordInspection {
    let mut report = VerificationReport::initial(Some(&original_bytes));
    let mut stage_record = None;
    let result: Result<()> = (|| {
        ensure(
            original_bytes.len() <= MAX_RECORD_BYTES,
            "Record exceeds 256 MiB limit",
        )?;
        #[derive(Deserialize)]
        #[serde(rename_all = "camelCase")]
        struct Header {
            format: Option<String>,
            recipe_version: Option<String>,
        }
        let header: Header = serde_json::from_slice(&original_bytes)
            .map_err(|e| CoreError::Invalid(format!("Invalid JSON header: {e}")))?;
        report.format = header.format.clone().or(header.recipe_version.clone());
        if header.format.as_deref() == Some(sustained::FORMAT) {
            report.scope = sustained::SCOPE.into();
            let segment: sustained::SustainedSegment = serde_json::from_slice(&original_bytes)
                .map_err(|e| CoreError::Invalid(format!("Invalid sustained segment: {e}")))?;
            segment.verify()?;
            report.checked_steps = segment.checked_steps();
            report.checked_turns = segment.checked_turns();
            return Ok(());
        }
        if header.format.as_deref() == Some(cases::FORMAT) {
            report.scope = cases::SCOPE.into();
            cases::CaseCatalog::decode(&original_bytes)?;
            return Ok(());
        }
        if header.format.as_deref() == Some(geometry::FORMAT) {
            report.scope = geometry::SCOPE.into();
            geometry::GeometryPacket::decode(&original_bytes)?;
            return Ok(());
        }
        if header.format.as_deref() == Some(regulation::FORMAT) {
            report.scope = regulation::SCOPE.into();
            let record: regulation::RegulationExampleRecord =
                serde_json::from_slice(&original_bytes)
                    .map_err(|e| CoreError::Invalid(format!("Invalid controller record: {e}")))?;
            record.verify()?;
            report.checked_steps = record.checked_steps();
            return Ok(());
        }
        if header
            .format
            .as_deref()
            .is_some_and(|format| actions::FORMATS.contains(&format))
        {
            let record: actions::ActionComparisonRecord =
                serde_json::from_slice(&original_bytes)
                    .map_err(|e| CoreError::Invalid(format!("Invalid actions record: {e}")))?;
            record.verify()?;
            report.checked_steps = record.checked_steps();
            report.checked_turns = record.checked_turns();
            return Ok(());
        }
        // Match the native runner's family dispatch: a nonempty `format` takes
        // precedence. A stage recipeVersion is not an action-format escape hatch.
        if header.format.as_deref() == Some(exploration::FORMAT) {
            let record: exploration::ExplorationRecord = serde_json::from_slice(&original_bytes)
                .map_err(|e| CoreError::Invalid(format!("Invalid exploration record: {e}")))?;
            record.verify()?;
            report.checked_steps = record.frames.len();
            return Ok(());
        }
        if header.format.is_some() || header.recipe_version.as_deref() != Some(stage::FORMAT) {
            return Err(CoreError::Unsupported(format!(
                "Record family {} is not numerically supported by this tranche",
                report.format.as_deref().unwrap_or("unidentified")
            )));
        }
        let record: stage::StageRecord = serde_json::from_slice(&original_bytes)
            .map_err(|e| CoreError::Invalid(format!("Invalid stage record: {e}")))?;
        let outcome = record.verify();
        if outcome.is_ok() {
            report.checked_steps = record.frames.len();
            report.checked_turns = record.turns.len();
        }
        stage_record = Some(record);
        outcome
    })();
    match result {
        Ok(()) => {
            report.status = VerificationStatus::Passed;
            report.diagnostics.push(match report.format.as_deref() {
                Some(sustained::FORMAT) => "Sustained segment reproduces its bounded event and numerical chain from its declared starting checkpoint. Verify the complete ordered bundle for genesis continuity. No provider calls were made.",
                Some(cases::FORMAT) => "Embedded case evidence passes integrity and reference checks. Authored interpretations remain distinct from verification.",
                Some(geometry::FORMAT) => "Geometry packet hashes, references, clocks and frozen-vector comparisons pass. No historical source paths were accessed.",
                _ => "Record reproduces its retained numerical chain and supported text contract. No provider calls were made.",
            }.into());
        }
        Err(CoreError::Invalid(message)) => {
            report.status = VerificationStatus::Failed;
            report.diagnostics.push(message);
        }
        Err(CoreError::Unsupported(message)) => {
            report.status = VerificationStatus::Incomplete;
            report.diagnostics.push(message);
        }
    }
    RecordInspection {
        original_bytes,
        report,
        stage_record,
    }
}

pub fn verify_bytes(bytes: &[u8]) -> VerificationReport {
    inspect_bytes(bytes.to_vec()).report
}

pub fn read_record_bytes(path: &Path) -> Result<Vec<u8>> {
    let file =
        File::open(path).map_err(|e| CoreError::Invalid(format!("Cannot open record: {e}")))?;
    let metadata = file
        .metadata()
        .map_err(|e| CoreError::Invalid(format!("Cannot inspect record: {e}")))?;
    ensure(
        metadata.is_file() && metadata.len() <= MAX_RECORD_BYTES as u64,
        "Record must be a regular file no larger than 256 MiB",
    )?;
    let mut bytes = Vec::new();
    file.take(MAX_RECORD_BYTES as u64 + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| CoreError::Invalid(format!("Cannot read record: {e}")))?;
    ensure(
        bytes.len() <= MAX_RECORD_BYTES,
        "Record grew beyond 256 MiB while reading",
    )?;
    Ok(bytes)
}
pub fn verify_file(path: &Path) -> VerificationReport {
    match read_record_bytes(path) {
        Ok(bytes) => inspect_bytes(bytes).report,
        Err(error) => {
            let mut report = VerificationReport::initial(None);
            report.status = VerificationStatus::Failed;
            report.diagnostics.push(error.to_string());
            report
        }
    }
}
