//! Operator observations are read-only and never enter model-selected scan state.
use super::*;
use reservoir_core::sustained::{
    scan_sustained_checkpoint, sustained_sonar_mirror, SustainedSonarMirror, SustainedSonarPoint,
    SustainedSonarReport,
};
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SonarView {
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
        let operator_scan = scan
            .then(|| scan_sustained_checkpoint(&checkpoint))
            .transpose()
            .map_err(ce)?;
        Ok(SonarView {
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
