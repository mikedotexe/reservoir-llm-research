//! Operator observations are read-only and never enter model-selected scan state.
use super::*;
use reservoir_core::sustained::{
    compact_sonar_matrix, question_sustained_checkpoint, scan_compact_sustained_checkpoint,
    scan_sustained_checkpoint, sustained_sonar_mirror, SustainedCompactSonarReport,
    SustainedSonarMirror, SustainedSonarPoint, SustainedSonarQuestion,
    SustainedSonarQuestionReport, SustainedSonarReport, SustainedSonarVersion,
};
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CompactSonarView {
    pub report: SustainedCompactSonarReport,
    pub immediate_response_matrix: Vec<Vec<f64>>,
}
impl CompactSonarView {
    fn new(report: SustainedCompactSonarReport) -> Result<Self, AppError> {
        let immediate_response_matrix = compact_sonar_matrix(&report).map_err(ce)?;
        Ok(Self {
            report,
            immediate_response_matrix,
        })
    }
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SonarView {
    pub model_experiments: Vec<reservoir_core::sustained::SustainedExperimentReport>,
    pub model_compact: Option<CompactSonarView>,
    pub operator_compact: Option<CompactSonarView>,
    pub model_question: Option<Box<SustainedSonarQuestionReport>>,
    pub operator_question: Option<SustainedSonarQuestionReport>,
    pub session_id: String,
    pub generation: String,
    pub checkpoint_sha256: String,
    pub step: u64,
    pub state: Vec<f64>,
    pub held_input: Vec<f64>,
    pub mirror: SustainedSonarMirror,
    pub model_scan: Option<Box<SustainedSonarReport>>,
    pub operator_scan: Option<SustainedSonarReport>,
}
impl SustainedState {
    pub fn sonar_view(
        &self,
        id: &str,
        generation: &str,
        scan: bool,
    ) -> Result<SonarView, AppError> {
        self.sonar_question_view(id, generation, scan, None)
    }
    pub fn sonar_question_view(
        &self,
        id: &str,
        generation: &str,
        scan: bool,
        question: Option<SustainedSonarQuestion>,
    ) -> Result<SonarView, AppError> {
        let checkpoint = {
            let mut g = self.lock()?;
            active(&mut g, id, generation)?.committed.clone()
        };
        let history = checkpoint
            .state
            .sonar_state
            .as_ref()
            .map(|v| v.history.clone())
            .unwrap_or_else(|| {
                vec![SustainedSonarPoint {
                    step: checkpoint.state.step,
                    state: checkpoint.state.reservoir_state.clone(),
                }]
            });
        let mirror = sustained_sonar_mirror(&history).map_err(ce)?;
        let compact = checkpoint
            .state
            .specification
            .sonar
            .as_ref()
            .is_some_and(|c| {
                matches!(
                    c.version,
                    SustainedSonarVersion::CompactScanV2 | SustainedSonarVersion::ExperimentsV3
                )
            });
        let operator_scan = (scan && !compact)
            .then(|| scan_sustained_checkpoint(&checkpoint))
            .transpose()
            .map_err(ce)?;
        let operator_compact = (scan && compact)
            .then(|| scan_compact_sustained_checkpoint(&checkpoint))
            .transpose()
            .map_err(ce)?
            .map(CompactSonarView::new)
            .transpose()?;
        let operator_question = question
            .map(|q| question_sustained_checkpoint(&checkpoint, q))
            .transpose()
            .map_err(ce)?;
        let model_compact = checkpoint
            .state
            .sonar_state
            .as_ref()
            .and_then(|s| s.latest_compact_scan.as_deref())
            .cloned()
            .map(CompactSonarView::new)
            .transpose()?;
        let model_question = checkpoint
            .state
            .sonar_state
            .as_ref()
            .and_then(|s| s.latest_question.clone());
        Ok(SonarView {
            model_experiments: checkpoint
                .state
                .sonar_state
                .as_ref()
                .map(|s| s.experiments.clone())
                .unwrap_or_default(),
            model_compact,
            operator_compact,
            model_question,
            operator_question,
            session_id: id.into(),
            generation: generation.into(),
            checkpoint_sha256: checkpoint.sha256,
            step: checkpoint.state.step,
            state: checkpoint.state.reservoir_state,
            held_input: checkpoint.state.held_vector,
            mirror,
            model_scan: checkpoint.state.sonar_state.and_then(|s| s.latest_scan),
            operator_scan,
        })
    }
}
