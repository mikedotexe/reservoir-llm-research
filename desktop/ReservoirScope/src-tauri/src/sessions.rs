//! One backend-owned finite numerical session. The WebView is a reader/controller,
//! never the numerical clock. Recovery exposes durable snapshots, never auto-runs.
use crate::{
    files::{self, AppError},
    library::LibraryState,
    records::{FrameView, TurnView},
    session_store::{
        BoundaryArm, Checkpoint, PairedBoundary, PendingLanguageCheckpoint, RegulationProgress,
        RetainedLanguageResponse, SaveAttempt, SessionStore,
    },
};
use reservoir_core::{
    actions::*,
    comparison::ActionComparisonSession,
    exploration::{ExplorationControls, ExplorationEngine},
    regulation::{
        RegulationExampleFrame, RegulationExampleSpecification, RegulationSession,
        RegulationWindowEvidence,
    },
    session::{JournalSession, LanguageResponse, PendingLanguage, StageSession},
    stage::{LanguageConfiguration, LanguageKind, RunSpecification, RunStatus},
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicBool, AtomicUsize, Ordering},
        Arc, Mutex,
    },
    time::{Duration, Instant},
};
fn error(kind: &str, message: impl Into<String>) -> AppError {
    AppError::new("session", kind, message)
}
fn core(e: reservoir_core::CoreError) -> AppError {
    error("numerical", e.to_string())
}
fn encode<T: Serialize>(v: &T) -> Result<Vec<u8>, AppError> {
    serde_json::to_vec(v).map_err(|e| error("encode", e.to_string()))
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SessionConfig {
    pub recipe: String,
    pub seed: String,
    pub steps: usize,
    pub turn_every: usize,
    pub leak: f64,
    pub noise_amplitude: f64,
    pub retention: f64,
    pub exploration_controls: Option<ExplorationControls>,
    #[serde(default = "independent_action_mode")]
    pub action_mode: ComparisonMode,
    #[serde(default = "full_action_input")]
    pub action_input_strength: f64,
    #[serde(default)]
    pub action_bias_enabled: bool,
    #[serde(default)]
    pub action_compare_previous: bool,
    #[serde(default = "component_comparison")]
    pub action_comparison_kind: ComparisonKind,
    #[serde(default = "pulsed_forcing")]
    pub action_forcing_profile: ForcingProfile,
    #[serde(default)]
    pub language: LanguageConfiguration,
}
pub(crate) fn validate_session_language(c: &SessionConfig) -> Result<(), AppError> {
    c.language.validate().map_err(core)?;
    if c.language.backend == LanguageKind::Ollama {
        let eligible = matches!(c.recipe.as_str(), "stage3" | "stage4")
            || (action_stage(&c.recipe).is_some_and(|s| s >= 4)
                && c.action_mode == ComparisonMode::IndependentGeneration);
        if !eligible {
            return Err(error("config", "Local models require stage 3/4 or independent action D–H; fixed replay never calls a provider."));
        }
        if action_stage(&c.recipe).is_some()
            && c.language.response_format.as_deref() != Some("json")
        {
            return Err(error(
                "config",
                "Local action responses require JSON format.",
            ));
        }
        if c.recipe.starts_with("stage") && c.language.response_format.is_some() {
            return Err(error(
                "config",
                "Stage 3/4 local responses use prose, not the action JSON format.",
            ));
        }
        crate::model_transport::validate_configuration(&c.language)
            .map_err(|e| error("config", e.to_string()))?;
    }
    Ok(())
}
fn component_comparison() -> ComparisonKind {
    ComparisonKind::Components
}
fn pulsed_forcing() -> ForcingProfile {
    ForcingProfile::PulsedSensoryV1
}
fn independent_action_mode() -> ComparisonMode {
    ComparisonMode::IndependentGeneration
}
fn full_action_input() -> f64 {
    1.0
}
pub(crate) fn action_stage(recipe: &str) -> Option<u8> {
    match recipe {
        "journalD" => Some(4),
        "journalE" => Some(5),
        s if s.len() == 7
            && s.starts_with("action")
            && (b'A'..=b'H').contains(&s.as_bytes()[6]) =>
        {
            Some(s.as_bytes()[6] - b'A' + 1)
        }
        _ => None,
    }
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ReplyTapeSummary {
    pub format: String,
    pub origin: String,
    pub packet_count: usize,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ActionSessionSummary {
    pub stage: u8,
    pub mode: ComparisonMode,
    pub has_journal: bool,
    pub has_feedback: bool,
    pub has_memory: bool,
    pub has_choice: bool,
    pub has_controller: bool,
    pub latest_journal_entry_id: Option<String>,
    pub reply_tape: Option<ReplyTapeSummary>,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PendingJournalView {
    pub arm: Arm,
    pub id: String,
    pub action_id: usize,
    pub observed_step: usize,
    pub prompt: String,
    pub text: String,
    pub sha256: String,
    pub relative_path: String,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PendingLanguageView {
    pub operation_id: String,
    pub arm: Arm,
    pub turn_id: usize,
    pub observed_step: usize,
    pub endpoint: String,
    pub model: String,
    pub state: String,
}
struct LanguageOperation {
    view: PendingLanguageView,
    cancel: Arc<AtomicBool>,
    received_response: Option<RetainedLanguageResponse>,
    diagnostic: Option<String>,
}
type LanguageGenerator = Arc<
    dyn Fn(
            &LanguageConfiguration,
            &str,
            &AtomicBool,
        ) -> Result<LanguageResponse, crate::model_transport::TransportError>
        + Send
        + Sync,
>;

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SessionSummary {
    pub session_id: String,
    pub generation: String,
    pub revision: String,
    pub config: SessionConfig,
    pub phase: String,
    pub step: usize,
    pub step_limit: usize,
    pub durable_step: usize,
    pub frame_count: usize,
    pub turn_count: usize,
    pub journal_count: usize,
    pub unsaved_record: bool,
    pub pending_writes: bool,
    pub can_step: bool,
    pub can_run: bool,
    pub can_export: bool,
    pub can_request_journal: bool,
    pub action: Option<ActionSessionSummary>,
    pub tracks: Vec<SessionTrackSummary>,
    pub regulation_spec: Option<Value>,
    pub exploration_controls: Option<ExplorationControls>,
    pub save_error: Option<String>,
    pub library_entry_id: Option<String>,
    pub diagnostics: Vec<String>,
    pub pending_language: Option<PendingLanguageView>,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SessionUpdate {
    pub request_id: String,
    pub summary: Option<SessionSummary>,
    pub frame: Option<SessionFrame>,
    pub frames: Option<SessionFrames>,
    pub regulation_frames: Option<RegulationFieldFrames>,
    pub pending_journal: Option<PendingJournalView>,
    pub close_requested: bool,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SessionTrackSummary {
    pub id: String,
    pub label: String,
    pub stage: Option<u8>,
    pub frame_count: usize,
    pub turn_count: usize,
    pub journal_count: usize,
    pub status: String,
    pub failure: Option<String>,
    pub observation_channel: Option<ObservationChannel>,
    pub action: Option<ActionSessionSummary>,
}
#[derive(Clone, Serialize)]
pub struct SessionFrames {
    pub left: Option<SessionFrame>,
    pub right: SessionFrame,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SessionFrame {
    #[serde(flatten)]
    pub frame: FrameView,
    pub exploration_controls: Option<ExplorationControls>,
    pub control: Option<reservoir_core::math::ControlMeasurement>,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SessionTurn {
    #[serde(flatten)]
    pub turn: TurnView,
    pub memory_text: Option<String>,
    pub memory_entry_sha256: Option<String>,
    pub journal_entry_id: Option<String>,
    pub journal_sha256: Option<String>,
    pub request_order: Option<usize>,
}
impl std::ops::Deref for SessionTurn {
    type Target = TurnView;
    fn deref(&self) -> &Self::Target {
        &self.turn
    }
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SessionFrameResult {
    pub request_id: String,
    pub session_id: String,
    pub generation: String,
    pub revision: String,
    pub track_id: String,
    pub frame: Option<SessionFrame>,
    pub regulation_frame: Option<RegulationFieldFrame>,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SessionTurnResult {
    pub request_id: String,
    pub session_id: String,
    pub generation: String,
    pub revision: String,
    pub track_id: String,
    pub turn: SessionTurn,
}

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RegulationFieldFrame {
    pub index: usize,
    pub step: String,
    pub time: f64,
    pub input: Vec<f64>,
    pub field_vector: Vec<f64>,
    pub eigenvalues: Vec<f64>,
    pub fill_percent: f64,
    pub retention_used: f64,
    pub next_retention: Option<f64>,
    pub control: Option<reservoir_core::math::ControlMeasurement>,
    pub regulation_evidence: Option<RegulationWindowEvidence>,
}
#[derive(Clone, Serialize)]
pub struct RegulationFieldFrames {
    pub left: RegulationFieldFrame,
    pub right: RegulationFieldFrame,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RegulationTimelinePoint {
    pub step: String,
    pub baseline_fill: f64,
    pub regulated_fill: f64,
    pub baseline_retention: f64,
    pub regulated_retention: f64,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RegulationDetails {
    pub request_id: String,
    pub session_id: String,
    pub generation: String,
    pub revision: String,
    pub cursor_step: usize,
    pub projection_weights: Vec<f64>,
    pub timeline: Vec<RegulationTimelinePoint>,
}
// These values lock the generic form to the native field-only recipe. Other
// SessionConfig knobs are inert defaults, not scientific parameters of this run.
pub(crate) fn validate_regulation_config(c: &SessionConfig) -> Result<(), AppError> {
    if c.seed != "98"
        || c.steps != 600
        || c.retention != 0.955
        || c.leak != 0.65
        || c.noise_amplitude != 0.0
        || c.turn_every != 30
        || c.exploration_controls.is_some()
        || c.action_mode != ComparisonMode::IndependentGeneration
        || c.action_input_strength != 1.0
        || c.action_bias_enabled
        || c.action_compare_previous
        || c.action_comparison_kind != ComparisonKind::Components
        || c.action_forcing_profile != ForcingProfile::PulsedSensoryV1
    {
        return Err(error("config","The field-only controller recipe requires field seed 98, input seed 42, 600 steps, retention 0.955 and its fixed configuration."));
    }
    Ok(())
}
fn regulation_spec_view(spec: &RegulationExampleSpecification) -> Value {
    let mut v = serde_json::to_value(spec).unwrap();
    v["fieldSeed"] = json!(spec.field_seed.to_string());
    v["inputSeed"] = json!(spec.input_seed.to_string());
    v
}
fn regulation_frame_view(
    f: &RegulationExampleFrame,
    arm: Arm,
    evidence: Option<RegulationWindowEvidence>,
) -> RegulationFieldFrame {
    let a = if arm == Arm::Left {
        &f.baseline
    } else {
        &f.regulated
    };
    RegulationFieldFrame {
        index: f.step - 1,
        step: f.step.to_string(),
        time: f.time,
        input: f.input.clone(),
        field_vector: a.spectral.field_vector.clone(),
        eigenvalues: a.spectral.eigenvalues.clone(),
        fill_percent: a.fill_percent,
        retention_used: a.retention_used,
        next_retention: a.control.as_ref().map(|c| c.applied_retention),
        control: a.control.clone(),
        regulation_evidence: evidence,
    }
}

type Listener = Arc<dyn Fn(SessionUpdate) -> bool + Send + Sync>;
struct Subscription {
    request_id: String,
    listener: Listener,
}
enum Engine {
    Explore(ExplorationEngine),
    Regulation(Box<RegulationSession>),
    Stage(Box<StageSession>),
    Journal(Box<ActionEngine>),
}
enum ActionEngine {
    Single(Box<JournalSession>),
    Paired(Box<ActionComparisonSession>),
}
impl ActionEngine {
    fn new(spec: ActionSpecification) -> reservoir_core::Result<Self> {
        if spec.compare_previous {
            ActionComparisonSession::new(spec).map(|j| Self::Paired(Box::new(j)))
        } else {
            JournalSession::new(spec).map(|j| Self::Single(Box::new(j)))
        }
    }
    fn specification(&self) -> &ActionSpecification {
        match self {
            Self::Single(j) => j.specification(),
            Self::Paired(j) => j.specification(),
        }
    }
    fn is_paired(&self) -> bool {
        matches!(self, Self::Paired(_))
    }
    fn run(&self, arm: Arm) -> Option<&ActionRunRecord> {
        match self {
            Self::Single(j) => (arm == Arm::Right).then(|| j.run()),
            Self::Paired(j) => Some(j.run(arm)),
        }
    }
    fn actions(&self) -> &[ActionReceipt] {
        &self.run(Arm::Right).unwrap().actions
    }
    fn journals(&self) -> &[JournalEntry] {
        &self.run(Arm::Right).unwrap().journals
    }
    fn pending_journal(&self) -> Option<&reservoir_core::session::PendingJournal> {
        match self {
            Self::Single(j) => j.pending_journal(),
            Self::Paired(j) => j.pending_journal().map(|(_, p)| p),
        }
    }
    fn pending_journal_arm(&self) -> Option<Arm> {
        match self {
            Self::Single(j) => j.pending_journal().map(|_| Arm::Right),
            Self::Paired(j) => j.pending_journal().map(|(a, _)| a),
        }
    }
    fn pending_memory(&self) -> Option<(Arm, &reservoir_core::session::PendingMemory)> {
        match self {
            Self::Single(j) => j.pending_memory().map(|p| (Arm::Right, p)),
            Self::Paired(j) => j.pending_memory(),
        }
    }
    fn pending_language(&self) -> Option<(Arm, &PendingLanguage)> {
        match self {
            Self::Single(j) => j.pending_language().map(|p| (Arm::Right, p)),
            Self::Paired(j) => j.pending_language(),
        }
    }
    fn start_language(&mut self, arm: Arm, id: usize, step: usize) -> reservoir_core::Result<()> {
        match self {
            Self::Single(j) => j.start_language(id, step),
            Self::Paired(j) => j.start_language(arm, id, step),
        }
    }
    fn confirm_language(
        &mut self,
        arm: Arm,
        id: usize,
        step: usize,
        r: &LanguageResponse,
    ) -> reservoir_core::Result<()> {
        match self {
            Self::Single(j) => j.confirm_language(id, step, r),
            Self::Paired(j) => j.confirm_language(arm, id, step, r),
        }
    }
    fn fail_language(
        &mut self,
        arm: Arm,
        id: usize,
        step: usize,
        reason: &str,
    ) -> reservoir_core::Result<()> {
        match self {
            Self::Single(j) => j.fail_language(id, step, reason),
            Self::Paired(j) => j.fail_language(arm, id, step, reason),
        }
    }
    fn tape(&self) -> Option<&ActionReplyTape> {
        match self {
            Self::Single(j) => j.tape(),
            Self::Paired(j) => j.tape(),
        }
    }
    fn can_request_action(&self) -> bool {
        match self {
            Self::Single(j) => j.can_request_action(),
            Self::Paired(j) => j.can_request_action(),
        }
    }
    fn request_action(&mut self) -> reservoir_core::Result<()> {
        match self {
            Self::Single(j) => j.request_action(),
            Self::Paired(j) => j.request_action(),
        }
    }
    fn advance(&mut self) -> reservoir_core::Result<ActionFrame> {
        match self {
            Self::Single(j) => j.advance(),
            Self::Paired(j) => j.advance().map(|f| f.right),
        }
    }
    fn is_failed(&self) -> bool {
        match self {
            Self::Single(j) => j.is_failed(),
            Self::Paired(j) => j.is_failed(),
        }
    }
    fn record(&self) -> reservoir_core::Result<ActionComparisonRecord> {
        match self {
            Self::Single(j) => j.record(),
            Self::Paired(j) => j.record(),
        }
    }
    fn confirm_saved(
        &mut self,
        r: &JournalSaveReceipt,
        e: &JournalEntry,
    ) -> reservoir_core::Result<()> {
        match self {
            Self::Single(j) => j.confirm_saved(r, e),
            Self::Paired(j) => j.confirm_saved(j.pending_journal().unwrap().0, r, e),
        }
    }
    fn confirm_memory(&mut self, arm: Arm, e: &JournalEntry) -> reservoir_core::Result<()> {
        match self {
            Self::Single(j) => j.confirm_memory(e),
            Self::Paired(j) => j.confirm_memory(arm, e),
        }
    }
    fn fail_memory(&mut self, arm: Arm, reason: &str) -> reservoir_core::Result<()> {
        match self {
            Self::Single(j) => j.fail_memory(reason),
            Self::Paired(j) => j.fail_memory(arm, reason),
        }
    }
    fn stop(&mut self, reason: &str) -> reservoir_core::Result<()> {
        match self {
            Self::Paired(j) => j.stop(reason),
            Self::Single(j) => {
                if let Some(p) = j.pending_language().cloned() {
                    j.cancel_language(p.turn_id, p.observed_step, reason)?;
                    j.stop()
                } else if j.pending_journal().is_some() {
                    j.fail_pending(reason)
                } else if j.pending_memory().is_some() {
                    j.cancel_memory(reason)
                } else {
                    j.stop()
                }
            }
        }
    }
}
fn arm_label(arm: Arm) -> &'static str {
    if arm == Arm::Left {
        "left"
    } else {
        "right"
    }
}
fn read_arm(track: Option<&str>) -> Result<Arm, AppError> {
    match track.unwrap_or("right") {
        "left" => Ok(Arm::Left),
        "right" => Ok(Arm::Right),
        _ => Err(error("track", "Unknown session track.")),
    }
}
struct Active {
    id: String,
    generation: u64,
    revision: u64,
    worker_epoch: u64,
    language_sequence: u64,
    language_operation: Option<LanguageOperation>,
    rejected_language: Option<PendingLanguageCheckpoint>,
    config: SessionConfig,
    engine: Engine,
    phase: String,
    frames: Vec<SessionFrame>,
    controls: Option<ExplorationControls>,
    durable_step: usize,
    durable_hash: Option<String>,
    dirty: bool,
    save_error: Option<String>,
    blocked_phase: Option<String>,
    library_id: Option<String>,
    attempts: Vec<SaveAttempt>,
    diagnostics: Vec<String>,
}
struct Inner {
    active: Option<Active>,
    next: u64,
    subscription: Option<Subscription>,
}
#[derive(Clone)]
pub struct SessionState {
    inner: Arc<Mutex<Inner>>,
    pub store: SessionStore,
    library: LibraryState,
    running: Arc<AtomicBool>,
    writing: Arc<AtomicUsize>,
    dirty: Arc<AtomicBool>,
    pause_requested: Arc<AtomicBool>,
    closing: Arc<AtomicBool>,
    close_requested: Arc<AtomicBool>,
    generate_language: LanguageGenerator,
}
pub struct WriteFlag(Arc<AtomicUsize>);
impl Drop for WriteFlag {
    fn drop(&mut self) {
        self.0.fetch_sub(1, Ordering::AcqRel);
    }
}
impl Engine {
    fn new(c: &SessionConfig) -> Result<Self, AppError> {
        validate_session_language(c)?;
        if c.seed.is_empty() || c.seed.len() > 20 || !c.seed.bytes().all(|b| b.is_ascii_digit()) {
            return Err(error(
                "config",
                "Seed must be an unsigned 64-bit decimal string.",
            ));
        }
        let seed = c
            .seed
            .parse::<u64>()
            .map_err(|_| error("config", "Seed exceeds UInt64."))?;
        if !c.leak.is_finite()
            || !(0.0..=1.0).contains(&c.leak)
            || !c.noise_amplitude.is_finite()
            || !(0.0..=0.2).contains(&c.noise_amplitude)
            || !c.retention.is_finite()
            || !(0.82..=0.995).contains(&c.retention)
            || c.turn_every == 0
            || !c.action_input_strength.is_finite()
            || !(0.0..=1.0).contains(&c.action_input_strength)
        {
            return Err(error(
                "config",
                "Numerical controls are outside their finite bounds.",
            ));
        }
        match c.recipe.as_str() {
            "regulation" => {
                validate_regulation_config(c)?;
                Ok(Self::Regulation(Box::new(
                    RegulationSession::new(RegulationExampleSpecification::default())
                        .map_err(core)?,
                )))
            }
            "exploration" => {
                if !(1..=1800).contains(&c.steps) || c.turn_every > 1800 {
                    return Err(error(
                        "config",
                        "Exploration step and interval bounds are 1–1800.",
                    ));
                }
                c.exploration_controls
                    .clone()
                    .unwrap_or_default()
                    .validate()
                    .map_err(core)?;
                Ok(Self::Explore(ExplorationEngine::new(seed)))
            }
            "stage1" | "stage2" | "stage3" | "stage4" => Ok(Self::Stage(Box::new(
                StageSession::new(RunSpecification {
                    stage: c.recipe.as_bytes()[5] - b'0',
                    seed,
                    steps: c.steps,
                    turn_every: c.turn_every,
                    leak: c.leak,
                    noise_amplitude: c.noise_amplitude,
                    initial_retention: c.retention,
                    language: c.language.clone(),
                    ..RunSpecification::default()
                })
                .map_err(core)?,
            ))),
            recipe if action_stage(recipe).is_some() => {
                let mut spec: ActionSpecification = serde_json::from_value(json!({}))
                    .map_err(|e| error("config", e.to_string()))?;
                spec.stage = action_stage(recipe).unwrap();
                spec.seed = seed;
                spec.steps = c.steps;
                spec.turn_every = c.turn_every;
                spec.leak = c.leak;
                spec.noise_amplitude = c.noise_amplitude;
                spec.initial_retention = c.retention;
                spec.mode = c.action_mode;
                spec.input_strength = c.action_input_strength;
                spec.bias_enabled = c.action_bias_enabled;
                spec.compare_previous = c.action_compare_previous;
                spec.comparison_kind = c.action_comparison_kind;
                spec.forcing_profile = c.action_forcing_profile;
                spec.language = c.language.clone();
                Ok(Self::Journal(Box::new(
                    ActionEngine::new(spec).map_err(core)?,
                )))
            }
            _ => Err(error("config", "Choose a supported finite offline recipe.")),
        }
    }
    fn pending(&self) -> Option<PendingJournalView> {
        if let Self::Journal(j) = self {
            j.pending_journal().map(|p| PendingJournalView {
                arm: j.pending_journal_arm().unwrap(),
                id: p.entry.id.clone(),
                action_id: p.action_id,
                observed_step: p.observed_step,
                prompt: p.prompt.clone(),
                text: p.entry.text.clone(),
                sha256: p.entry.sha256.clone(),
                relative_path: p.relative_path.clone(),
            })
        } else {
            None
        }
    }
    fn record(&self) -> Result<Vec<u8>, AppError> {
        match self {
            Self::Explore(x) => encode(&x.record()),
            Self::Regulation(x) => encode(&x.completed_record().map_err(core)?),
            Self::Stage(x) => encode(x.portable_record().map_err(core)?),
            Self::Journal(x) => encode(&x.record().map_err(core)?),
        }
    }
    fn turn_count(&self) -> usize {
        match self {
            Self::Explore(_) | Self::Regulation(_) => 0,
            Self::Stage(s) => s.record().turns.len(),
            Self::Journal(j) => j.actions().len(),
        }
    }
    fn journal_count(&self) -> usize {
        if let Self::Journal(j) = self {
            j.journals().len()
        } else {
            0
        }
    }
    fn unresolved(&self) -> bool {
        self.pending_language().is_some()
            || matches!(self, Self::Journal(j) if j.pending_journal().is_some() || j.pending_memory().is_some())
    }
    fn pending_language(&self) -> Option<(Arm, &PendingLanguage)> {
        match self {
            Self::Stage(s) => s.pending_language().map(|p| (Arm::Right, p)),
            Self::Journal(j) => j.pending_language(),
            _ => None,
        }
    }
    fn start_language(&mut self, arm: Arm, id: usize, step: usize) -> Result<(), AppError> {
        match self {
            Self::Stage(s) => s.start_language(id, step),
            Self::Journal(j) => j.start_language(arm, id, step),
            _ => unreachable!(),
        }
        .map_err(core)
    }
    fn confirm_language(
        &mut self,
        arm: Arm,
        id: usize,
        step: usize,
        r: &LanguageResponse,
    ) -> Result<(), AppError> {
        match self {
            Self::Stage(s) => s.confirm_language(id, step, r),
            Self::Journal(j) => j.confirm_language(arm, id, step, r),
            _ => unreachable!(),
        }
        .map_err(core)
    }
    fn fail_language(
        &mut self,
        arm: Arm,
        id: usize,
        step: usize,
        reason: &str,
    ) -> Result<(), AppError> {
        match self {
            Self::Stage(s) => s.fail_language(id, step, reason),
            Self::Journal(j) => j.fail_language(arm, id, step, reason),
            _ => unreachable!(),
        }
        .map_err(core)
    }
    fn action_summary(&self, config: &SessionConfig, arm: Arm) -> Option<ActionSessionSummary> {
        let Self::Journal(j) = self else {
            return None;
        };
        let run = j.run(arm)?;
        let stage = run.stage;
        Some(ActionSessionSummary {
            stage,
            mode: config.action_mode,
            has_journal: stage >= 4,
            has_feedback: stage >= 5,
            has_memory: stage >= 6,
            has_choice: stage >= 7,
            has_controller: stage == 8,
            latest_journal_entry_id: run.journals.last().map(|e| e.id.clone()),
            reply_tape: j.tape().map(|t| ReplyTapeSummary {
                format: t.format.clone(),
                origin: t.origin.clone(),
                packet_count: t.packets.len(),
            }),
        })
    }
    fn turn(&self, index: usize, arm: Arm) -> Result<SessionTurn, AppError> {
        if arm == Arm::Left && !matches!(self,Self::Journal(j) if j.is_paired()) {
            return Err(error("track", "This session has no left comparison arm."));
        }
        let v = match self {
            Self::Explore(_) | Self::Regulation(_) => None,
            Self::Stage(s) => s
                .record()
                .turns
                .get(index)
                .map(|t| serde_json::to_value(t).unwrap()),
            Self::Journal(j) => j.run(arm).and_then(|r| r.actions.get(index)).map(|t| {
                let mut value = serde_json::to_value(t).unwrap();
                // Read the committed entry named by this exact receipt.
                // Keep rawReply untouched as the action envelope; a failed
                // save without an entry retains its existing raw fallback.
                if let Some(entry) = t.journal_entry_id.as_ref().and_then(|id| {
                    j.run(arm)
                        .unwrap()
                        .journals
                        .iter()
                        .find(|entry| entry.id == *id)
                }) {
                    value["reply"] = Value::String(entry.text.clone());
                }
                value
            }),
        }
        .ok_or_else(|| error("range", "No such committed turn."))?;
        let memory_text = opt_text(&v, "memoryText");
        let memory_entry_sha256 = if memory_text.is_some() {
            if let Self::Journal(j) = self {
                j.run(arm)
                    .unwrap()
                    .journals
                    .iter()
                    .find(|entry| Some(entry.id.as_str()) == v["memoryEntryID"].as_str())
                    .map(|e| e.sha256.clone())
            } else {
                None
            }
        } else {
            None
        };
        let mut turn = turn_view(index, &v);
        if matches!(self, Self::Stage(_)) {
            turn.configured_model = turn.model.clone();
        }
        if let Self::Journal(j) = self {
            let config = &j.specification().language;
            if v["tapePacketID"].is_null() {
                turn.backend = Some(
                    if config.backend == LanguageKind::Ollama {
                        "ollama"
                    } else {
                        "scripted"
                    }
                    .into(),
                );
                turn.configured_model = config.model.clone();
                turn.model = config.model.clone();
            }
        }
        if v["chosenAction"] == "WAIT" {
            turn.reply = None;
        }
        Ok(SessionTurn {
            turn,
            memory_text,
            memory_entry_sha256,
            journal_entry_id: opt_text(&v, "journalEntryID"),
            journal_sha256: opt_text(&v["saveReceipt"], "sha256"),
            request_order: v["requestOrder"].as_u64().map(|n| n as usize),
        })
    }
    fn advance(
        &mut self,
        c: &SessionConfig,
        controls: Option<&ExplorationControls>,
        pulse: bool,
    ) -> Result<Option<SessionFrame>, AppError> {
        if let Self::Regulation(r) = self {
            r.advance().map_err(core)?;
            return Ok(None);
        }
        let v = match self {
            Self::Regulation(_) => unreachable!(),
            Self::Explore(e) => serde_json::to_value(
                e.advance(
                    controls
                        .cloned()
                        .or_else(|| c.exploration_controls.clone())
                        .unwrap_or_default(),
                    pulse,
                )
                .map_err(core)?,
            ),
            Self::Stage(e) => serde_json::to_value(e.advance().map_err(core)?),
            Self::Journal(e) => serde_json::to_value(e.advance().map_err(core)?),
        }
        .map_err(|e| error("view", e.to_string()))?;
        let control = v
            .get("control")
            .filter(|v| !v.is_null())
            .map(|v| serde_json::from_value(v.clone()).map_err(|e| error("view", e.to_string())))
            .transpose()?;
        Ok(Some(SessionFrame {
            frame: frame_view(&v),
            exploration_controls: controls.cloned(),
            control,
        }))
    }
    fn stop(&mut self, reason: &str) -> Result<(), AppError> {
        match self {
            Self::Explore(_) | Self::Regulation(_) => {}
            Self::Stage(e) => {
                if let Some(p) = e.pending_language().cloned() {
                    e.cancel_language(p.turn_id, p.observed_step, reason)
                        .map_err(core)?;
                }
                e.stop();
            }
            Self::Journal(e) => e.stop(reason).map_err(core)?,
        }
        Ok(())
    }
    fn portable_available(&self) -> bool {
        !self.unresolved() && !matches!(self,Self::Regulation(r) if !r.is_complete())
    }
    fn failed(&self) -> bool {
        matches!(self,Self::Journal(j) if j.is_failed())
            || matches!(self,Self::Stage(s) if s.record().status == RunStatus::Failed)
    }
}
fn array(v: &Value, key: &str) -> Vec<f64> {
    v[key]
        .as_array()
        .map(|a| a.iter().filter_map(Value::as_f64).collect())
        .unwrap_or_default()
}
fn opt_text(v: &Value, key: &str) -> Option<String> {
    v[key].as_str().map(str::to_owned)
}
fn ordinal(v: &Value) -> Option<String> {
    v.as_u64()
        .map(|x| x.to_string())
        .or_else(|| v.as_str().map(str::to_owned))
}
fn frame_view(v: &Value) -> FrameView {
    let step = v["step"].as_u64().unwrap_or(0);
    FrameView {
        index: step.saturating_sub(1) as usize,
        step: step.to_string(),
        time: v["time"].as_f64(),
        state: array(v, "state"),
        input: array(v, "input"),
        noise: array(v, "noise"),
        fill_percent: v["fillPercent"].as_f64(),
        eigenvalues: v["spectral"]["eigenvalues"]
            .as_array()
            .map(|_| array(&v["spectral"], "eigenvalues")),
        retention_used: v["retentionUsed"].as_f64(),
        semantic_turn_id: ordinal(&v["semanticTurnID"]).or_else(|| ordinal(&v["semanticActionID"])),
        next_retention: v["control"]["appliedRetention"].as_f64(),
        lesson_evidence: None,
        regulation_evidence: None,
    }
}
fn action_frame_view(f: &ActionFrame) -> SessionFrame {
    SessionFrame {
        frame: frame_view(&serde_json::to_value(f).unwrap()),
        exploration_controls: None,
        control: f.control.clone(),
    }
}
fn turn_view(index: usize, v: &Value) -> TurnView {
    TurnView {
        index,
        id: ordinal(&v["id"]).unwrap_or_else(|| index.to_string()),
        observed_step: ordinal(&v["observedStep"]),
        application_step: ordinal(&v["applicationStep"]),
        status: opt_text(v, "status").unwrap_or_default(),
        backend: opt_text(v, "backend").or_else(|| {
            Some(
                if v["tapePacketID"].is_null() {
                    "scripted"
                } else {
                    "fixedReplay"
                }
                .into(),
            )
        }),
        model: opt_text(v, "model"),
        prompt: opt_text(v, "prompt").unwrap_or_default(),
        reply: opt_text(v, "reply").or_else(|| opt_text(v, "rawReply")),
        encoded_features: v["encodedFeatures"]
            .as_array()
            .map(|_| array(v, "encodedFeatures")),
        semantic_vector: v["semanticVector"]
            .as_array()
            .map(|_| array(v, "semanticVector")),
        failure: opt_text(v, "failure"),
        journal_saved: v
            .get("saveReceipt")
            .filter(|x| !x.is_null())
            .map(|x| x["status"] == "saved"),
        raw_reply: opt_text(v, "rawReply"),
        requested_action: opt_text(v, "requestedAction"),
        chosen_action: opt_text(v, "chosenAction"),
        context_kind: opt_text(v, "contextKind"),
        memory_entry_ids: v["memoryEntryID"]
            .as_str()
            .map(|s| vec![s.into()])
            .unwrap_or_default(),
        journal_relative_path: opt_text(&v["saveReceipt"], "relativePath"),
        configured_model: None,
        provider_model: opt_text(v, "providerModel"),
        request_started: v["requestStarted"].as_bool(),
        tape_packet_id: ordinal(&v["tapePacketID"]),
        failure_phase: opt_text(v, "failurePhase"),
    }
}
impl Active {
    fn step_count(&self) -> usize {
        if let Engine::Regulation(r) = &self.engine {
            r.frames().len()
        } else {
            self.frames.len()
        }
    }
    fn regulation_frame(&self, index: usize, arm: Arm) -> Option<RegulationFieldFrame> {
        let Engine::Regulation(r) = &self.engine else {
            return None;
        };
        r.frames()
            .get(index)
            .map(|f| regulation_frame_view(f, arm, r.window_evidence(index + 1)))
    }
    fn tracks(&self) -> Vec<SessionTrackSummary> {
        if let Engine::Regulation(r) = &self.engine {
            [Arm::Left, Arm::Right]
                .into_iter()
                .map(|arm| SessionTrackSummary {
                    id: arm_label(arm).into(),
                    label: if arm == Arm::Left {
                        "Baseline field"
                    } else {
                        "Regulated field"
                    }
                    .into(),
                    stage: None,
                    frame_count: r.frames().len(),
                    turn_count: 0,
                    journal_count: 0,
                    status: if r.is_complete() {
                        "completed"
                    } else {
                        "incomplete"
                    }
                    .into(),
                    failure: None,
                    observation_channel: None,
                    action: None,
                })
                .collect()
        } else if let Engine::Journal(j) = &self.engine {
            [Arm::Left, Arm::Right]
                .into_iter()
                .filter_map(|arm| {
                    j.run(arm).map(|r| SessionTrackSummary {
                        id: arm_label(arm).into(),
                        label: format!(
                            "{} · Action {}",
                            arm_label(arm),
                            (b'A' + r.stage - 1) as char
                        ),
                        stage: Some(r.stage),
                        frame_count: r.frames.len(),
                        turn_count: r.actions.len(),
                        journal_count: r.journals.len(),
                        status: serde_json::to_value(&r.status)
                            .unwrap()
                            .as_str()
                            .unwrap()
                            .into(),
                        failure: r.failure.clone(),
                        observation_channel: r.observation_channel,
                        action: self.engine.action_summary(&self.config, arm),
                    })
                })
                .collect()
        } else {
            vec![SessionTrackSummary {
                id: "right".into(),
                label: self.config.recipe.clone(),
                stage: None,
                frame_count: self.step_count(),
                turn_count: self.engine.turn_count(),
                journal_count: 0,
                status: if self.phase == "completed" {
                    "completed"
                } else if self.phase == "failed" {
                    "failed"
                } else {
                    "stopped"
                }
                .into(),
                failure: self.save_error.clone(),
                observation_channel: None,
                action: None,
            }]
        }
    }
    fn left_frame(&self, index: usize) -> Option<SessionFrame> {
        let Engine::Journal(j) = &self.engine else {
            return None;
        };
        j.run(Arm::Left)?.frames.get(index).map(action_frame_view)
    }
    fn summary(&self, writing: bool) -> SessionSummary {
        let ready = matches!(self.phase.as_str(), "ready" | "paused");
        SessionSummary {
            session_id: self.id.clone(),
            generation: self.generation.to_string(),
            revision: self.revision.to_string(),
            config: self.config.clone(),
            phase: self.phase.clone(),
            step: self.step_count(),
            step_limit: self.config.steps,
            durable_step: self.durable_step,
            frame_count: self.step_count(),
            turn_count: self.engine.turn_count(),
            journal_count: self.engine.journal_count(),
            unsaved_record: self.dirty,
            pending_writes: writing,
            can_step: ready && !writing,
            can_run: ready && !writing,
            can_export: self.phase != "running" && self.engine.portable_available(),
            can_request_journal: ready
                && !writing
                && matches!(&self.engine, Engine::Journal(j) if j.can_request_action()),
            action: self.engine.action_summary(&self.config, Arm::Right),
            tracks: self.tracks(),
            regulation_spec: if let Engine::Regulation(r) = &self.engine {
                Some(regulation_spec_view(r.specification()))
            } else {
                None
            },
            exploration_controls: self.controls.clone(),
            save_error: self.save_error.clone(),
            library_entry_id: self.library_id.clone(),
            diagnostics: self.diagnostics.clone(),
            pending_language: self.language_operation.as_ref().map(|o| o.view.clone()),
        }
    }
    fn pending_language_checkpoint(&self) -> Option<PendingLanguageCheckpoint> {
        self.language_operation.as_ref().and_then(|o| {
            self.engine
                .pending_language()
                .map(|(_, p)| PendingLanguageCheckpoint {
                    operation: o.view.clone(),
                    session_id: self.id.clone(),
                    generation: self.generation.to_string(),
                    prompt: p.prompt.clone(),
                    configuration: p.configuration.clone(),
                    request_started: p.request_started,
                    received_response: o.received_response.clone(),
                    diagnostic: o.diagnostic.clone(),
                })
        })
    }
    fn checkpoint(&self, discarded: bool) -> Checkpoint {
        Checkpoint {
            schema: "reservoir-scope-finite-session-v1".into(),
            session_id: self.id.clone(),
            generation: self.generation.to_string(),
            revision: self.revision.to_string(),
            config: serde_json::to_value(&self.config).unwrap(),
            phase: self.phase.clone(),
            step: self.step_count(),
            durable_step: self.durable_step,
            record_sha256: self.durable_hash.clone(),
            pending_journal: if let Engine::Journal(j) = &self.engine {
                j.pending_journal().map(|p| {
                    let mut v = serde_json::to_value(p).unwrap();
                    v["arm"] = serde_json::to_value(j.pending_journal_arm().unwrap()).unwrap();
                    v
                })
            } else {
                None
            },
            pending_language: self.pending_language_checkpoint(),
            rejected_language: self.rejected_language.clone(),
            paired_boundary: if let Engine::Journal(j) = &self.engine {
                if j.is_paired() && self.engine.unresolved() {
                    Some(PairedBoundary {
                        step: self.step_count(),
                        arms: [Arm::Left, Arm::Right]
                            .into_iter()
                            .map(|arm| {
                                let run = j.run(arm).unwrap();
                                let receipt = run
                                    .actions
                                    .last()
                                    .filter(|r| r.observed_step == self.step_count())
                                    .cloned();
                                let journal = receipt
                                    .as_ref()
                                    .and_then(|r| r.journal_entry_id.as_ref())
                                    .and_then(|id| run.journals.iter().find(|j| j.id == *id))
                                    .cloned();
                                BoundaryArm {
                                    arm,
                                    stage: run.stage,
                                    receipt,
                                    journal,
                                }
                            })
                            .collect(),
                    })
                } else {
                    None
                }
            } else {
                None
            },
            regulation_progress: if let Engine::Regulation(r) = &self.engine {
                Some(RegulationProgress {
                    retained_step: r.frames().len(),
                    portable_complete: r.is_complete(),
                    specification: r.specification().clone(),
                })
            } else {
                None
            },
            attempts: self.attempts.clone(),
            updated_at_ms: String::new(),
            discarded,
        }
    }
}
impl SessionState {
    pub fn new(root: PathBuf, library: LibraryState) -> Self {
        Self {
            inner: Arc::new(Mutex::new(Inner {
                active: None,
                next: 0,
                subscription: None,
            })),
            store: SessionStore::new(root),
            library,
            running: Arc::new(AtomicBool::new(false)),
            writing: Arc::new(AtomicUsize::new(0)),
            dirty: Arc::new(AtomicBool::new(false)),
            pause_requested: Arc::new(AtomicBool::new(false)),
            closing: Arc::new(AtomicBool::new(false)),
            close_requested: Arc::new(AtomicBool::new(false)),
            generate_language: Arc::new(crate::model_transport::generate),
        }
    }
    fn lock(&self) -> Result<std::sync::MutexGuard<'_, Inner>, AppError> {
        if self.closing.load(Ordering::Acquire) {
            return Err(error("closing", "Application is closing."));
        }
        let guard = self
            .inner
            .lock()
            .map_err(|_| error("lock", "Session lock unavailable."))?;
        if self.closing.load(Ordering::Acquire) {
            return Err(error("closing", "Application is closing."));
        }
        Ok(guard)
    }
    fn active<'a>(
        inner: &'a mut Inner,
        id: &str,
        generation: &str,
    ) -> Result<&'a mut Active, AppError> {
        inner
            .active
            .as_mut()
            .filter(|a| a.id == id && a.generation.to_string() == generation)
            .ok_or_else(|| {
                error(
                    "stale",
                    "This command targets a replaced session generation.",
                )
            })
    }
    fn update(&self, inner: &Inner, request_id: String, writing: bool) -> SessionUpdate {
        SessionUpdate {
            request_id,
            summary: inner.active.as_ref().map(|a| a.summary(writing)),
            frame: inner.active.as_ref().and_then(|a| a.frames.last().cloned()),
            frames: inner.active.as_ref().and_then(|a| {
                a.frames.last().map(|right| SessionFrames {
                    left: a.left_frame(a.frames.len() - 1),
                    right: right.clone(),
                })
            }),
            regulation_frames: inner.active.as_ref().and_then(|a| {
                a.step_count().checked_sub(1).and_then(|index| {
                    Some(RegulationFieldFrames {
                        left: a.regulation_frame(index, Arm::Left)?,
                        right: a.regulation_frame(index, Arm::Right)?,
                    })
                })
            }),
            pending_journal: inner.active.as_ref().and_then(|a| a.engine.pending()),
            close_requested: self.close_requested.load(Ordering::Acquire),
        }
    }
    fn write_flag(&self) -> WriteFlag {
        self.writing.fetch_add(1, Ordering::AcqRel);
        WriteFlag(self.writing.clone())
    }
    fn persist(&self, a: &mut Active, discarded: bool) -> Result<(), AppError> {
        let _writing = self.write_flag();
        let bytes = if !a.engine.portable_available() {
            None
        } else {
            Some(a.engine.record()?)
        };
        let mut checkpoint = a.checkpoint(discarded);
        if bytes.is_some() {
            checkpoint.durable_step = a.step_count();
        }
        self.store.checkpoint(checkpoint, bytes.as_deref())?;
        if let Some(b) = bytes {
            a.durable_step = a.step_count();
            a.durable_hash = Some(files::digest(&b));
        }
        Ok(())
    }
    fn persist_checked(&self, a: &mut Active) -> Result<(), AppError> {
        let was_blocked = a.phase == "storageBlocked";
        if was_blocked {
            a.phase = a.blocked_phase.clone().unwrap_or_else(|| "paused".into());
        }
        match self.persist(a, false) {
            Ok(()) => {
                a.blocked_phase = None;
                if was_blocked {
                    a.save_error = None;
                }
                Ok(())
            }
            Err(e) => {
                a.blocked_phase = Some(if a.phase == "running" {
                    "paused".into()
                } else {
                    a.phase.clone()
                });
                a.phase = "storageBlocked".into();
                a.save_error = Some(e.message.clone());
                self.running.store(false, Ordering::Release);
                Err(e)
            }
        }
    }
    fn persist_or_block(&self, a: &mut Active) {
        let _ = self.persist_checked(a);
    }
    pub fn get(
        &self,
        request_id: String,
        listener: Option<Listener>,
    ) -> Result<SessionUpdate, AppError> {
        let mut i = self.lock()?;
        if let Some(listener) = listener {
            i.subscription = Some(Subscription {
                request_id: request_id.clone(),
                listener,
            });
        }
        Ok(self.update(&i, request_id, self.writing.load(Ordering::Acquire) > 0))
    }
    pub fn create(
        &self,
        request_id: String,
        config: SessionConfig,
    ) -> Result<SessionUpdate, AppError> {
        let engine = Engine::new(&config)?;
        let mut i = self.lock()?;
        self.create_locked(&mut i, request_id, config, engine)
    }
    fn create_locked(
        &self,
        i: &mut Inner,
        request_id: String,
        config: SessionConfig,
        engine: Engine,
    ) -> Result<SessionUpdate, AppError> {
        if i.active
            .as_ref()
            .is_some_and(|a| a.dirty || a.phase == "running" || a.engine.unresolved())
        {
            return Err(error(
                "unsaved",
                "Save or explicitly discard the current session first.",
            ));
        }
        i.next = i
            .next
            .checked_add(1)
            .ok_or_else(|| error("identity", "Session generation exhausted."))?;
        let id = format!(
            "session-{}-{}-{}",
            crate::session_store::now_ms(),
            std::process::id(),
            i.next
        );
        let controls = if config.recipe == "exploration" {
            Some(config.exploration_controls.clone().unwrap_or_default())
        } else {
            None
        };
        let mut a = Active {
            id,
            generation: i.next,
            revision: 1,
            worker_epoch: 0,
            language_sequence: 0,
            language_operation: None,
            rejected_language: None,
            config,
            engine,
            controls,
            phase: "ready".into(),
            frames: vec![],
            durable_step: 0,
            durable_hash: None,
            dirty: true,
            save_error: None,
            blocked_phase: None,
            library_id: None,
            attempts: vec![],
            diagnostics: vec![],
        };
        self.persist_or_block(&mut a);
        i.active = Some(a);
        self.dirty.store(true, Ordering::Release);
        self.pause_requested.store(false, Ordering::Release);
        Ok(self.update(i, request_id, false))
    }
    fn advance(&self, a: &mut Active, pulse: bool) -> Result<(), AppError> {
        let old_turn_count = a.engine.turn_count();
        let f = a.engine.advance(&a.config, a.controls.as_ref(), pulse)?;
        if let Some(f) = f {
            a.frames.push(f);
        }
        a.revision += 1;
        a.dirty = true;
        self.dirty.store(true, Ordering::Release);
        self.resolve_memory(a)?;
        if self.schedule_language(a)? {
            return Ok(());
        }
        if a.engine.pending().is_some() {
            a.phase = "awaitingJournalSave".into();
            self.running.store(false, Ordering::Release);
        } else if a.engine.failed() {
            a.phase = "failed".into();
            self.running.store(false, Ordering::Release);
        } else if a.step_count() >= a.config.steps {
            a.phase = "completed".into();
            self.running.store(false, Ordering::Release);
        }
        if a.step_count().is_multiple_of(30)
            || old_turn_count != a.engine.turn_count()
            || matches!(
                a.phase.as_str(),
                "awaitingJournalSave" | "completed" | "failed"
            )
        {
            self.persist_or_block(a);
        }
        Ok(())
    }
    fn cancel_operation(a: &mut Active) {
        if a.language_operation
            .as_ref()
            .is_some_and(|o| o.received_response.is_some())
        {
            a.rejected_language = a.pending_language_checkpoint();
        }
        if let Some(op) = a.language_operation.take() {
            op.cancel.store(true, Ordering::Release);
        }
    }
    /// Publish bounded intent before dispatch. The worker acquires the lock only
    /// to mark dispatch and accept the one matching result, never during HTTP.
    fn schedule_language(&self, a: &mut Active) -> Result<bool, AppError> {
        let Some((arm, p)) = a.engine.pending_language().map(|(arm, p)| (arm, p.clone())) else {
            return Ok(false);
        };
        if a.language_operation.is_some() {
            return Ok(true);
        }
        a.language_sequence += 1;
        let operation_id = format!("language-{}-{}", a.generation, a.language_sequence);
        a.language_operation = Some(LanguageOperation {
            view: PendingLanguageView {
                operation_id: operation_id.clone(),
                arm,
                turn_id: p.turn_id,
                observed_step: p.observed_step,
                endpoint: p.configuration.endpoint.clone().unwrap_or_default(),
                model: p.configuration.model.clone().unwrap_or_default(),
                state: "prepared".into(),
            },
            cancel: Arc::new(AtomicBool::new(false)),
            received_response: None,
            diagnostic: None,
        });
        a.phase = "awaitingLanguage".into();
        a.revision += 1;
        self.running.store(false, Ordering::Release);
        if let Err(e) = self.persist_checked(a) {
            Self::cancel_operation(a);
            a.engine.stop(
                "Provider preparation was cancelled because its checkpoint could not be saved.",
            )?;
            a.phase = "storageBlocked".into();
            a.blocked_phase = Some("stopped".into());
            a.save_error = Some(e.message);
            a.revision += 1;
            return Ok(true);
        }
        let this = self.clone();
        let token = (a.id.clone(), a.generation, operation_id);
        std::thread::spawn(move || this.language_worker(token));
        Ok(true)
    }
    fn language_worker(&self, token: (String, u64, String)) {
        let prepared = (|| -> Result<Option<(PendingLanguageView, PendingLanguage, Arc<AtomicBool>)>,AppError> {
            let mut i=self.lock()?;
            let Some(a)=i.active.as_mut().filter(|a|a.id==token.0 && a.generation==token.1) else {return Ok(None)};
            let Some(op)=a.language_operation.as_ref().filter(|o|o.view.operation_id==token.2 && o.view.state=="prepared" && !o.cancel.load(Ordering::Acquire)) else {return Ok(None)};
            let view=op.view.clone(); let cancel=op.cancel.clone();
            let p=a.engine.pending_language().ok_or_else(||error("state","Provider intent lost its pending boundary."))?.1.clone();
            a.engine.start_language(view.arm,view.turn_id,view.observed_step)?;
            a.language_operation.as_mut().unwrap().view.state="requesting".into();
            a.revision+=1;
            // Prepared intent is already durable. There is no fallible disk
            // operation between this dispatch marker and transport handoff.
            // A crash may leave the older prepared snapshot; recovery must
            // neither infer that dispatch was absent nor repeat the request.
            Ok(Some((view,p,cancel)))
        })();
        self.notify();
        let Ok(Some((view, p, cancel))) = prepared else {
            return;
        };
        let response = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            (self.generate_language)(&p.configuration, &p.prompt, &cancel)
        }))
        .unwrap_or_else(|_| {
            Err(crate::model_transport::TransportError {
                category: "worker",
                message: "Provider worker failed before producing an accepted response.".into(),
            })
        });
        let completion = (|| -> Result<(), AppError> {
            let mut i = self.lock()?;
            let Some(a) = i
                .active
                .as_mut()
                .filter(|a| a.id == token.0 && a.generation == token.1)
            else {
                return Ok(());
            };
            if a.language_operation
                .as_ref()
                .is_none_or(|o| o.view.operation_id != token.2)
                || cancel.load(Ordering::Acquire)
            {
                return Ok(());
            }
            let result = match &response {
                Ok(r) => a
                    .engine
                    .confirm_language(view.arm, view.turn_id, view.observed_step, r),
                Err(e) => {
                    let reason: String = e.message.chars().take(1000).collect();
                    a.engine.fail_language(
                        view.arm,
                        view.turn_id,
                        view.observed_step,
                        if reason.is_empty() {
                            "Local model request failed."
                        } else {
                            &reason
                        },
                    )
                }
            };
            a.revision += 1;
            a.dirty = true;
            self.dirty.store(true, Ordering::Release);
            if let Err(e) = result {
                // Qualified codec/parser support is a scientific gate, not a
                // transient HTTP error. Keep the boundary until explicit Stop.
                let operation = a.language_operation.as_mut().unwrap();
                operation.view.state = "compatibilityBlocked".into();
                operation.received_response = response
                    .as_ref()
                    .ok()
                    .map(RetainedLanguageResponse::capture);
                operation.diagnostic = Some(e.message.clone());
                a.phase = "awaitingLanguage".into();
                a.diagnostics.push(format!("Provider response was not accepted: {}. Stop to retain cancellation; no request will be retried.",e.message));
            } else {
                a.language_operation = None;
                self.resolve_memory(a)?;
                a.phase = if a.engine.pending_language().is_some() {
                    "awaitingLanguage"
                } else if a.engine.pending().is_some() {
                    "awaitingJournalSave"
                } else if a.engine.failed() {
                    "failed"
                } else {
                    "paused"
                }
                .into();
            }
            self.running.store(false, Ordering::Release);
            // Schedule a required peer only after the previous arm settled. A
            // completed provider boundary never resumes numerical time itself.
            if a.engine.pending_language().is_some() && a.language_operation.is_none() {
                self.schedule_language(a)?;
            } else {
                self.persist_or_block(a);
            }
            Ok(())
        })();
        if let Err(e) = completion {
            if let Ok(mut i) = self.inner.lock() {
                if let Some(a) = i
                    .active
                    .as_mut()
                    .filter(|a| a.id == token.0 && a.generation == token.1)
                {
                    a.diagnostics.push(format!(
                        "Provider completion could not be committed: {}",
                        e.message
                    ));
                }
            }
        }
        self.notify();
    }
    fn resolve_memory(&self, a: &mut Active) -> Result<(), AppError> {
        let Engine::Journal(j) = &mut a.engine else {
            return Ok(());
        };
        while let Some((arm, pending)) = j.pending_memory().map(|(arm, p)| (arm, p.clone())) {
            // Resolve within the numerical-boundary mutex, on a backend worker. The
            // store reads only its own fixed journal namespace, never a receipt path.
            // This is a new physical read even when the earlier save was confirmed.
            let result = self
                .store
                .read_journal_for(&a.id, arm, &pending.entry)
                .and_then(|entry| j.confirm_memory(arm, &entry).map_err(core));
            if let Err(e) = result {
                let reason: String = e.message.chars().take(1000).collect();
                j.fail_memory(arm, &reason).map_err(core)?;
                let diagnostic = format!(
                    "Saved journal memory read failed ({}): {reason}",
                    arm_label(arm)
                );
                a.save_error = Some(diagnostic.clone());
                a.diagnostics.push(diagnostic);
            }
        }
        Ok(())
    }
    pub fn step(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
        pulse: bool,
    ) -> Result<SessionUpdate, AppError> {
        let mut i = self.lock()?;
        let a = Self::active(&mut i, id, generation)?;
        if !a.summary(false).can_step {
            return Err(error(
                "state",
                "Pause, resolve pending save, or reset before stepping.",
            ));
        }
        self.advance(a, pulse)?;
        Ok(self.update(&i, request_id, false))
    }
    pub fn run(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
        listener: Listener,
    ) -> Result<SessionUpdate, AppError> {
        let mut i = self.lock()?;
        let a = Self::active(&mut i, id, generation)?;
        if !a.summary(false).can_run {
            return Err(error("state", "Session is not ready to run."));
        }
        a.phase = "running".into();
        a.revision += 1;
        a.worker_epoch += 1;
        let token = (a.id.clone(), a.generation, a.worker_epoch);
        i.subscription = Some(Subscription {
            request_id: request_id.clone(),
            listener,
        });
        self.pause_requested.store(false, Ordering::Release);
        self.running.store(true, Ordering::Release);
        let result = self.update(&i, request_id, false);
        let this = self.clone();
        std::thread::spawn(move || this.worker(token));
        Ok(result)
    }
    fn notify(&self) {
        let message = if let Ok(i) = self.inner.lock() {
            i.subscription.as_ref().map(|s| {
                (
                    s.listener.clone(),
                    self.update(
                        &i,
                        s.request_id.clone(),
                        self.writing.load(Ordering::Acquire) > 0,
                    ),
                )
            })
        } else {
            None
        };
        if let Some((listener, message)) = message {
            if !listener(message) {
                if let Ok(mut i) = self.inner.lock() {
                    if i.subscription
                        .as_ref()
                        .is_some_and(|s| Arc::ptr_eq(&s.listener, &listener))
                    {
                        i.subscription = None;
                    }
                }
            }
        }
    }
    fn worker(&self, token: (String, u64, u64)) {
        let mut last = Instant::now() - Duration::from_secs(1);
        loop {
            let running = {
                let Ok(mut i) = self.inner.lock() else { return };
                let Some(a) = i.active.as_mut().filter(|a| {
                    a.id == token.0 && a.generation == token.1 && a.worker_epoch == token.2
                }) else {
                    return;
                };
                if a.phase != "running" {
                    return;
                }
                if self.pause_requested.swap(false, Ordering::AcqRel) {
                    a.phase = "paused".into();
                    a.revision += 1;
                    self.running.store(false, Ordering::Release);
                    self.persist_or_block(a);
                } else if let Err(e) = self.advance(a, false) {
                    a.phase = "failed".into();
                    a.save_error = Some(e.message);
                    a.revision += 1;
                    self.running.store(false, Ordering::Release);
                    self.persist_or_block(a);
                }
                a.phase == "running"
            };
            if !running || last.elapsed() >= Duration::from_millis(100) {
                self.notify();
                last = Instant::now();
            }
            if !running {
                return;
            }
            std::thread::sleep(Duration::from_millis(20));
        }
    }
    pub fn pause(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
    ) -> Result<SessionUpdate, AppError> {
        let mut i = self.lock()?;
        let a = Self::active(&mut i, id, generation)?;
        self.pause_requested.store(true, Ordering::Release);
        a.worker_epoch += 1;
        if a.phase == "running" {
            a.phase = "paused".into();
            a.revision += 1;
        }
        self.running.store(false, Ordering::Release);
        self.persist_or_block(a);
        Ok(self.update(&i, request_id, false))
    }
    pub fn stop(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
    ) -> Result<SessionUpdate, AppError> {
        let mut i = self.lock()?;
        let a = Self::active(&mut i, id, generation)?;
        a.worker_epoch += 1;
        let reason = if a.engine.pending_language().is_some() {
            "Explicit stop while the language request remained unresolved."
        } else if a.engine.pending().is_some() {
            "Explicit stop while journal save remained unresolved."
        } else {
            "Explicit stop of the finite experiment."
        };
        Self::cancel_operation(a);
        a.engine.stop(reason)?;
        a.phase = if a.engine.failed() {
            "failed"
        } else {
            "stopped"
        }
        .into();
        a.revision += 1;
        a.dirty = true;
        self.dirty.store(true, Ordering::Release);
        self.running.store(false, Ordering::Release);
        self.persist_or_block(a);
        Ok(self.update(&i, request_id, false))
    }
    pub fn reset(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
        discard: bool,
    ) -> Result<SessionUpdate, AppError> {
        let mut i = self.lock()?;
        let a = Self::active(&mut i, id, generation)?;
        if a.dirty && !discard {
            return Err(error(
                "unsaved",
                "Reset requires saving or explicit discard.",
            ));
        }
        let config = a.config.clone();
        let engine = Engine::new(&config)?;
        self.running.store(false, Ordering::Release);
        a.worker_epoch += 1;
        Self::cancel_operation(a);
        a.engine
            .stop("Explicit reset discarded unresolved journal save.")?;
        a.phase = if a.engine.failed() {
            "failed"
        } else {
            "stopped"
        }
        .into();
        a.revision += 1;
        if let Err(e) = self.persist(a, discard) {
            a.blocked_phase = Some(a.phase.clone());
            a.phase = "storageBlocked".into();
            a.save_error = Some(e.message);
            return Ok(self.update(&i, request_id, false));
        }
        a.dirty = false;
        self.create_locked(&mut i, request_id, config, engine)
    }

    pub fn request_journal(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
    ) -> Result<SessionUpdate, AppError> {
        let mut i = self.lock()?;
        let a = Self::active(&mut i, id, generation)?;
        if !a.summary(false).can_step {
            return Err(error("state", "Pause before requesting a journal."));
        }
        let Engine::Journal(j) = &mut a.engine else {
            return Err(error(
                "recipe",
                "Manual journal requests require an action D–H recipe.",
            ));
        };
        j.request_action().map_err(core)?;
        self.resolve_memory(a)?;
        a.phase = if a.engine.pending_language().is_some() {
            "awaitingLanguage"
        } else if a.engine.pending().is_some() {
            "awaitingJournalSave"
        } else if a.engine.failed() {
            "failed"
        } else {
            "paused"
        }
        .into();
        a.revision += 1;
        a.dirty = true;
        self.dirty.store(true, Ordering::Release);
        if !self.schedule_language(a)? {
            self.persist_or_block(a);
        }
        Ok(self.update(&i, request_id, false))
    }
    #[cfg(test)]
    pub fn save_journal(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
    ) -> Result<SessionUpdate, AppError> {
        let candidate = {
            let mut i = self.lock()?;
            Self::active(&mut i, id, generation)?
                .engine
                .pending()
                .ok_or_else(|| error("state", "No unresolved journal candidate."))?
        };
        self.save_journal_for(
            request_id,
            id,
            generation,
            arm_label(candidate.arm),
            &candidate.id,
        )
    }
    pub fn save_journal_for(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
        arm: &str,
        entry_id: &str,
    ) -> Result<SessionUpdate, AppError> {
        let arm = read_arm(Some(arm))?;
        let mut i = self.lock()?;
        let a = Self::active(&mut i, id, generation)?;
        let Engine::Journal(j) = &a.engine else {
            return Err(error("recipe", "No journal candidate in this recipe."));
        };
        let pending = j
            .pending_journal()
            .cloned()
            .ok_or_else(|| error("state", "No unresolved journal candidate."))?;
        if j.pending_journal_arm() != Some(arm) || pending.entry.id != entry_id {
            return Err(error(
                "stale",
                "This save targets a different arm or journal candidate.",
            ));
        }
        if a.attempts.len() >= 512 {
            return Err(error(
                "bound",
                "Save-attempt limit reached; stop and retain the failure.",
            ));
        }
        a.attempts.push(SaveAttempt {
            arm,
            number: a.attempts.len() + 1,
            at_ms: crate::session_store::now_ms().to_string(),
            entry_id: pending.entry.id.clone(),
            status: "prepared".into(),
            diagnostic: None,
        });
        a.revision += 1;
        if let Err(e) = self.persist_checked(a) {
            let attempt = a.attempts.last_mut().unwrap();
            attempt.status = "failed".into();
            attempt.diagnostic = Some(e.message.clone());
            a.save_error = Some(e.message);
            a.phase = "storageBlocked".into();
            return Ok(self.update(&i, request_id, false));
        }
        let _writing = self.write_flag();
        let result = self.store.commit_journal_for(&a.id, arm, &pending.entry);
        match result {
            Ok((receipt, entry)) => {
                let Engine::Journal(j) = &mut a.engine else {
                    unreachable!()
                };
                match j.confirm_saved(&receipt, &entry) {
                    Ok(()) => {
                        a.attempts.last_mut().unwrap().status = "committed".into();
                        a.phase = "paused".into();
                        a.save_error = None;
                    }
                    Err(e) => {
                        let attempt = a.attempts.last_mut().unwrap();
                        attempt.status = "failed".into();
                        attempt.diagnostic = Some(e.to_string());
                        a.save_error = Some(e.to_string());
                        a.phase = "awaitingJournalSave".into();
                    }
                }
            }
            Err(e) => {
                let attempt = a.attempts.last_mut().unwrap();
                attempt.status = "failed".into();
                attempt.diagnostic = Some(e.message.clone());
                a.save_error = Some(e.message);
                a.phase = "awaitingJournalSave".into();
            }
        }
        drop(_writing);
        self.resolve_memory(a)?;
        a.phase = if a.engine.pending_language().is_some() {
            "awaitingLanguage"
        } else if a.engine.pending().is_some() {
            "awaitingJournalSave"
        } else if a.engine.failed() {
            "failed"
        } else {
            "paused"
        }
        .into();
        a.revision += 1;
        if !self.schedule_language(a)? {
            self.persist_or_block(a);
        }
        Ok(self.update(&i, request_id, false))
    }
    pub fn save_record(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
    ) -> Result<SessionUpdate, AppError> {
        let mut i = self.lock()?;
        let a = Self::active(&mut i, id, generation)?;
        if !a.summary(false).can_export {
            if matches!(a.engine, Engine::Regulation(_)) {
                return Err(error("incomplete","A portable field-only controller record requires all 600 steps. Export partial progress metadata through recovery."));
            }
            return Err(error("pending","Pause and save the journal, or explicitly stop and retain failed save before exporting."));
        }
        if let Err(e) = self.persist_checked(a) {
            a.save_error = Some(e.message);
            a.phase = "storageBlocked".into();
            a.revision += 1;
            return Ok(self.update(&i, request_id, false));
        }
        let bytes = a.engine.record()?;
        let _writing = self.write_flag();
        let result =
            self.library
                .publish_created(request_id.clone(), &format!("{}.json", a.id), &bytes);
        match result {
            Ok(result) => {
                if result.published {
                    a.dirty = false;
                    self.dirty.store(false, Ordering::Release);
                    a.library_id = result.entry_id;
                    a.save_error = None;
                } else {
                    a.save_error = Some(
                        "Snapshot did not pass record verification; session remains available."
                            .into(),
                    );
                }
                a.diagnostics = result.diagnostics;
            }
            Err(e) => a.save_error = Some(e.message),
        }
        a.revision += 1;
        drop(_writing);
        Ok(self.update(&i, request_id, false))
    }
    pub fn snapshot(
        &self,
        id: &str,
        generation: &str,
    ) -> Result<(String, Vec<u8>, String), AppError> {
        let mut i = self.lock()?;
        let a = Self::active(&mut i, id, generation)?;
        if !a.summary(false).can_export {
            if matches!(a.engine, Engine::Regulation(_)) {
                return Err(error("incomplete","A portable field-only controller record requires all 600 steps. Export partial progress metadata through recovery."));
            }
            return Err(error(
                "pending",
                "Pause and resolve pending journal save before exporting.",
            ));
        }
        Ok((
            format!("{}.json", a.id),
            a.engine.record()?,
            a.revision.to_string(),
        ))
    }
    #[cfg(test)]
    pub fn frame(
        &self,
        request_id: String,
        id: String,
        generation: String,
        index: usize,
    ) -> Result<SessionFrameResult, AppError> {
        self.frame_for(request_id, id, generation, index, None)
    }
    pub fn frame_for(
        &self,
        request_id: String,
        id: String,
        generation: String,
        index: usize,
        track_id: Option<String>,
    ) -> Result<SessionFrameResult, AppError> {
        let arm = read_arm(track_id.as_deref())?;
        let mut i = self.lock()?;
        let a = Self::active(&mut i, &id, &generation)?;
        let frame = if arm == Arm::Left {
            a.left_frame(index)
        } else {
            a.frames.get(index).cloned()
        };
        let regulation_frame = a.regulation_frame(index, arm);
        if frame.is_none() && regulation_frame.is_none() {
            return Err(error(
                "range",
                "Track or frame is outside retained boundaries.",
            ));
        }
        Ok(SessionFrameResult {
            request_id,
            session_id: id,
            generation,
            revision: a.revision.to_string(),
            track_id: arm_label(arm).into(),
            frame,
            regulation_frame,
        })
    }
    #[cfg(test)]
    pub fn turn(
        &self,
        request_id: String,
        id: String,
        generation: String,
        index: usize,
    ) -> Result<SessionTurnResult, AppError> {
        self.turn_for(request_id, id, generation, index, None)
    }
    pub fn turn_for(
        &self,
        request_id: String,
        id: String,
        generation: String,
        index: usize,
        track_id: Option<String>,
    ) -> Result<SessionTurnResult, AppError> {
        let arm = read_arm(track_id.as_deref())?;
        let mut i = self.lock()?;
        let a = Self::active(&mut i, &id, &generation)?;
        Ok(SessionTurnResult {
            request_id,
            session_id: id,
            generation,
            revision: a.revision.to_string(),
            track_id: arm_label(arm).into(),
            turn: a.engine.turn(index, arm)?,
        })
    }
    pub fn regulation_details(
        &self,
        request_id: String,
        id: String,
        generation: String,
        cursor_step: usize,
    ) -> Result<RegulationDetails, AppError> {
        let mut i = self.lock()?;
        let a = Self::active(&mut i, &id, &generation)?;
        let Engine::Regulation(r) = &a.engine else {
            return Err(error(
                "recipe",
                "This session has no field-only controller details.",
            ));
        };
        if cursor_step == 0 || cursor_step > r.frames().len() {
            return Err(error(
                "range",
                "Choose an actually retained controller step.",
            ));
        }
        Ok(RegulationDetails {
            request_id,
            session_id: id,
            generation,
            revision: a.revision.to_string(),
            cursor_step,
            projection_weights: r.projection_weights().to_vec(),
            timeline: r.frames()[..cursor_step]
                .iter()
                .map(|f| RegulationTimelinePoint {
                    step: f.step.to_string(),
                    baseline_fill: f.baseline.fill_percent,
                    regulated_fill: f.regulated.fill_percent,
                    baseline_retention: f.baseline.retention_used,
                    regulated_retention: f.regulated.retention_used,
                })
                .collect(),
        })
    }
    pub fn begin_export(&self) -> Result<WriteFlag, AppError> {
        let _guard = self.lock()?;
        Ok(self.write_flag())
    }
    /// Cross-workspace admission is conservative while a boundary is unsettled.
    /// A saved paused finite record may coexist with a running sustained session.
    pub fn execution_busy(&self) -> bool {
        if self.running.load(Ordering::Acquire) || self.writing.load(Ordering::Acquire) > 0 {
            return true;
        }
        let Ok(i) = self.inner.try_lock() else {
            return true;
        };
        i.active
            .as_ref()
            .is_some_and(|a| a.dirty || a.phase == "running" || a.engine.unresolved())
    }
    /// Nonblocking authorization for a cooperative close without a review dialog.
    /// The atomics alone are insufficient: a manual step can hold `inner` while
    /// computing from a saved state, before it sets dirty. Acquire the same gate
    /// used by every command, inspect accepted state, then permanently close it.
    pub fn authorize_clean_close(&self) -> bool {
        if self.closing.load(Ordering::Acquire) {
            return true;
        }
        if self.writing.load(Ordering::Acquire) > 0 {
            return false;
        }
        let Ok(i) = self.inner.try_lock() else {
            return false;
        };
        if self.closing.load(Ordering::Acquire) {
            return true;
        }
        if self.writing.load(Ordering::Acquire) > 0
            || i.active
                .as_ref()
                .is_some_and(|a| a.dirty || a.phase == "running" || a.engine.unresolved())
        {
            return false;
        }
        // A command already waiting for this mutex rechecks closing in lock().
        // New create/step/run/export operations therefore cannot be accepted
        // between this authorization and AppKit/Tauri's eventual process exit.
        self.closing.store(true, Ordering::Release);
        true
    }
    #[cfg(test)]
    pub fn needs_review(&self) -> bool {
        !self.closing.load(Ordering::Acquire)
            && (self.running.load(Ordering::Acquire)
                || self.writing.load(Ordering::Acquire) > 0
                || self.dirty.load(Ordering::Acquire))
    }
    pub fn request_close_pause(&self) {
        self.close_requested.store(true, Ordering::Release);
        self.pause_requested.store(true, Ordering::Release);
    }
    pub fn cancel_close(&self) {
        self.close_requested.store(false, Ordering::Release);
        // Another owned lab can require review after this lab was clean. Returning
        // to the app must reopen both command gates, never strand the clean owner.
        self.closing.store(false, Ordering::Release);
    }
    pub fn reopen_after_stale_close(&self) {
        // A cancelled finish may complete after another quit request. Reopen
        // its command gate without erasing the newer review or pause request.
        self.closing.store(false, Ordering::Release);
    }
    pub fn update_controls(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
        controls: ExplorationControls,
    ) -> Result<SessionUpdate, AppError> {
        controls.validate().map_err(core)?;
        let mut i = self.lock()?;
        let a = Self::active(&mut i, id, generation)?;
        if a.controls.is_none() || !matches!(a.phase.as_str(), "ready" | "paused" | "running") {
            return Err(error(
                "controls",
                "Exploration controls require an active exploration session.",
            ));
        }
        a.controls = Some(controls);
        a.revision += 1;
        Ok(self.update(&i, request_id, false))
    }
    pub fn finish_close(&self, allow_discard: bool) -> Result<bool, AppError> {
        if self.writing.load(Ordering::Acquire) > 0 {
            return Ok(false);
        }
        let Ok(mut i) = self.inner.try_lock() else {
            return Ok(false);
        };
        if self.writing.load(Ordering::Acquire) > 0 {
            return Ok(false);
        }
        if let Some(a) = i.active.as_mut() {
            if (a.dirty || a.phase == "running" || a.engine.unresolved()) && !allow_discard {
                return Ok(false);
            }
            Self::cancel_operation(a);
            a.engine
                .stop("Explicit close discarded unresolved journal save.")?;
            a.phase = "stopped".into();
            a.revision += 1;
            if allow_discard {
                let _ = self.persist(a, true);
            }
        }
        self.running.store(false, Ordering::Release);
        self.closing.store(true, Ordering::Release);
        Ok(true)
    }
}

#[cfg(test)]
#[path = "sessions_tests.rs"]
mod tests;
