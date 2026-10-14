//! Bounded, incremental offline execution. No disk or provider access occurs here.
//! Journal candidates stay outside portable history until a storage owner confirms
//! exact save/readback, or explicitly finalizes an irreversible failed outcome.
use crate::{
    actions::*,
    codec, ensure,
    math::*,
    stage::{
        ContextKind, EssentialsFrame, LanguageConfiguration, LanguageKind, LanguageTurn,
        RunSpecification, RunStatus, StageRecord, TurnStatus, EXAMPLE_TEXTS, SCRIPTED_REPLIES,
    },
    CoreError, Result,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::sync::Arc;
use unicode_segmentation::UnicodeSegmentation;

/// A numerical boundary waiting for its caller's provider operation. This is
/// preparation, not evidence that a request has been dispatched.
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PendingLanguage {
    pub turn_id: usize,
    pub observed_step: usize,
    pub configuration: LanguageConfiguration,
    pub prompt: String,
    pub request_started: bool,
    pub request_order: Option<usize>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LanguageResponse {
    pub text: String,
    pub provider_model: Option<String>,
    pub stop_reason: Option<String>,
    pub token_count: Option<i64>,
    pub complete: bool,
    /// Optional provider assertion, not a context-coverage or completeness gate.
    /// Omission preserves historical typed serialization and checkpoint hashes.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub provider_prompt_evaluation: Option<ProviderPromptEvaluation>,
}

/// Evidence from the provider's optional `prompt_eval_count` response member.
/// A reported count is not independently tokenized or authenticated here.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "status", rename_all = "camelCase", deny_unknown_fields)]
pub enum ProviderPromptEvaluation {
    Reported {
        count: u64,
    },
    Unusable {
        reason: ProviderPromptEvaluationIssue,
    },
}

/// Why the optional field could not be read as an unsigned JSON integer.
/// These diagnostics never determine whether journal text can be accepted.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum ProviderPromptEvaluationIssue {
    WrongType,
    Negative,
    NonInteger,
    OutOfRange,
    DuplicateField,
}
impl PendingLanguage {
    fn matches(&self, id: usize, step: usize) -> Result<()> {
        ensure(
            self.turn_id == id && self.observed_step == step,
            "Language outcome belongs to a different opportunity",
        )
    }
    fn start(&mut self, id: usize, step: usize, order: Option<usize>) -> Result<()> {
        self.matches(id, step)?;
        ensure(
            !self.request_started,
            "Language request was already dispatched",
        )?;
        self.request_started = true;
        self.request_order = order;
        Ok(())
    }
    fn dispatched(&self, id: usize, step: usize) -> Result<()> {
        self.matches(id, step)?;
        ensure(
            self.request_started,
            "Language request has not been dispatched",
        )
    }
}
fn language_reason(reason: &str) -> Result<()> {
    ensure(
        !reason.is_empty() && reason.len() <= 4096,
        "Language outcome diagnostic must contain 1–4096 UTF-8 bytes",
    )
}
fn retained_raw(text: &str) -> Result<String> {
    let raw = if text.len() <= 65_536 {
        text.to_owned()
    } else {
        text.graphemes(true).take(16_000).collect()
    };
    if raw.len() > 65_536 {
        return Err(CoreError::Unsupported("Native grapheme-prefix response exceeds the portable byte bound; retain the pending boundary without feedback".into()));
    }
    Ok(raw)
}

struct StageLanguage {
    public: PendingLanguage,
    turn: LanguageTurn,
    response_received: bool,
}

pub struct StageSession {
    record: StageRecord,
    engine: ReservoirEngine,
    field: SensoryField,
    fill: ReducedFill,
    controller: RetentionController,
    retention: f64,
    rng: SplitMix64,
    semantic: Vec<f64>,
    semantic_id: Option<usize>,
    stopped: bool,
    pending_language: Option<StageLanguage>,
}

impl StageSession {
    pub fn new(spec: RunSpecification) -> Result<Self> {
        spec.validate()?;
        ensure(
            spec.language.backend == LanguageKind::Scripted || spec.stage >= 3,
            "A provider-backed fresh stage requires stage 3 or 4",
        )?;
        let model = ReservoirModel::seeded(spec.seed);
        let engine = ReservoirEngine::new(model.clone(), spec.leak, None)?;
        let field = SensoryField::seeded(spec.seed ^ FIELD_SEED);
        Ok(Self {
            record: StageRecord {
                recipe_version: crate::stage::FORMAT.into(),
                specification: spec.clone(),
                model,
                projection_weights: if spec.stage == 1 {
                    vec![]
                } else {
                    field.projection.clone()
                },
                frames: vec![],
                turns: vec![],
                status: RunStatus::Stopped,
                failure: None,
            },
            engine,
            field,
            fill: ReducedFill::default(),
            controller: RetentionController::new(spec.initial_retention)?,
            retention: spec.initial_retention,
            rng: SplitMix64::new(spec.seed ^ NOISE_SEED),
            semantic: vec![0.0; 48],
            semantic_id: None,
            stopped: false,
            pending_language: None,
        })
    }
    pub fn record(&self) -> &StageRecord {
        &self.record
    }
    pub fn is_complete(&self) -> bool {
        self.record.status == RunStatus::Completed
    }
    pub fn is_failed(&self) -> bool {
        self.record.status == RunStatus::Failed
    }
    pub fn pending_language(&self) -> Option<&PendingLanguage> {
        self.pending_language.as_ref().map(|p| &p.public)
    }
    pub fn portable_record(&self) -> Result<&StageRecord> {
        ensure(self.pending_language.is_none(), "Language opportunity remains unresolved; finish it or explicitly stop before exporting")?;
        Ok(&self.record)
    }
    pub fn stop(&mut self) {
        if let Some(p) = self.pending_language() {
            let (id, step) = (p.turn_id, p.observed_step);
            self.cancel_language(
                id,
                step,
                "Explicit stop cancelled the pending language opportunity.",
            )
            .expect("bounded current cancellation");
        }
        self.stopped = true;
    }
    pub fn advance(&mut self) -> Result<EssentialsFrame> {
        ensure(
            !self.stopped
                && !self.is_complete()
                && !self.is_failed()
                && self.pending_language.is_none(),
            "Stage session is stopped or complete",
        )?;
        let spec = &self.record.specification;
        let step = self.record.frames.len() + 1;
        // Work on local numerical state so an error cannot consume a noise draw,
        // controller update or recurrence without recording its boundary.
        let mut rng = self.rng.clone();
        let mut engine = copy_engine(&self.engine)?;
        let mut field = copy_field(&self.field)?;
        let mut fill = ReducedFill {
            fill: self.fill.fill,
        };
        let mut controller = RetentionController {
            current_retention: self.controller.current_retention,
            integral: self.controller.integral,
        };
        let mut input = forcing(step, spec.dt);
        input[18..].copy_from_slice(&self.semantic);
        let noise: Vec<_> = (0..32)
            .map(|_| rng.signed() * spec.noise_amplitude)
            .collect();
        let state = engine.step(&input, &noise)?;
        let spectral = if spec.stage == 1 {
            None
        } else {
            Some(field.step(&input, self.retention)?)
        };
        let fill_percent = if spec.stage == 4 {
            Some(100.0 * fill.update(&spectral.as_ref().unwrap().eigenvalues, spec.dt))
        } else {
            None
        };
        let control = if spec.stage == 4 && spec.regulation_enabled {
            Some(controller.update(fill_percent.unwrap()))
        } else {
            None
        };
        let frame = EssentialsFrame {
            step,
            time: step as f64 * spec.dt,
            input,
            state,
            noise,
            retention_used: spectral.as_ref().map(|_| self.retention),
            spectral,
            fill_percent,
            control,
            semantic_turn_id: self.semantic_id,
        };
        let due = spec.stage != 1 && step.is_multiple_of(spec.turn_every) && step < spec.steps;
        let pending_language =
            if due && spec.stage >= 3 && spec.language.backend == LanguageKind::Ollama {
                let id = self.record.turns.len() + 1;
                let prompt = crate::stage::prompt(spec, &frame)?;
                Some(StageLanguage {
                    response_received: false,
                    public: PendingLanguage {
                        turn_id: id,
                        observed_step: step,
                        configuration: spec.language.clone(),
                        prompt: prompt.clone(),
                        request_started: false,
                        request_order: None,
                    },
                    turn: LanguageTurn {
                        id,
                        observed_step: step,
                        application_step: None,
                        prompt,
                        context_kind: ContextKind::LanguageRequest,
                        reply: None,
                        raw_reply: None,
                        provider_model: None,
                        stop_reason: None,
                        token_count: None,
                        encoded_features: None,
                        semantic_vector: None,
                        status: TurnStatus::Cancelled,
                        failure: None,
                        backend: spec.language.backend.as_str().into(),
                        model: spec.language.model.clone(),
                    },
                })
            } else {
                None
            };
        let turn = if due && pending_language.is_none() {
            let id = self.record.turns.len() + 1;
            let reply = if spec.stage == 2 {
                EXAMPLE_TEXTS[(id - 1) % EXAMPLE_TEXTS.len()]
            } else {
                SCRIPTED_REPLIES[(id - 1) % SCRIPTED_REPLIES.len()]
            };
            let features = codec::encode(reply)?;
            let semantic = codec::feedback(&features, frame.spectral.as_ref().unwrap());
            Some(LanguageTurn {
                id,
                observed_step: step,
                application_step: None,
                prompt: crate::stage::prompt(spec, &frame)?,
                context_kind: if spec.stage == 2 {
                    ContextKind::PreparedExampleContext
                } else {
                    ContextKind::LanguageRequest
                },
                reply: Some(reply.into()),
                raw_reply: Some(reply.into()),
                provider_model: Some(
                    if spec.stage == 2 {
                        "essentials-examples-v1"
                    } else {
                        "essentials-script-v1"
                    }
                    .into(),
                ),
                stop_reason: Some(
                    if spec.stage == 2 {
                        "example"
                    } else {
                        "scripted"
                    }
                    .into(),
                ),
                token_count: None,
                encoded_features: Some(features),
                semantic_vector: Some(semantic),
                status: TurnStatus::Completed,
                failure: None,
                backend: if spec.stage == 2 {
                    "example"
                } else {
                    "scripted"
                }
                .into(),
                model: if spec.stage >= 3 {
                    spec.language.model.clone()
                } else {
                    None
                },
            })
        } else {
            None
        };
        self.rng = rng;
        self.engine = engine;
        self.field = field;
        self.fill = fill;
        self.controller = controller;
        if let Some(control) = &frame.control {
            self.retention = control.applied_retention;
        }
        if let Some(id) = self.semantic_id {
            self.record.turns[id - 1]
                .application_step
                .get_or_insert(step);
        }
        if let Some(turn) = turn {
            self.semantic = turn.semantic_vector.clone().unwrap();
            self.semantic_id = Some(turn.id);
            self.record.turns.push(turn);
        }
        self.record.frames.push(frame.clone());
        self.pending_language = pending_language;
        if step == spec.steps {
            self.record.status = RunStatus::Completed;
        }
        Ok(frame)
    }
    pub fn start_language(&mut self, id: usize, step: usize) -> Result<()> {
        self.pending_language
            .as_mut()
            .ok_or_else(|| CoreError::Invalid("No pending language opportunity".into()))?
            .public
            .start(id, step, None)
    }
    pub fn confirm_language(
        &mut self,
        id: usize,
        step: usize,
        response: &LanguageResponse,
    ) -> Result<()> {
        let pending = self
            .pending_language
            .as_mut()
            .ok_or_else(|| CoreError::Invalid("No pending language opportunity".into()))?;
        pending.public.dispatched(id, step)?;
        ensure(!pending.response_received, "A response already settled or blocked this opportunity; only explicit cancellation remains")?;
        pending.response_received = true;
        ensure(
            response
                .provider_model
                .as_ref()
                .is_none_or(|v| v.len() <= 1024)
                && response
                    .stop_reason
                    .as_ref()
                    .is_none_or(|v| v.len() <= 1024),
            "Stage provider metadata exceeds its retained byte bound",
        )?;
        let mut turn = pending.turn.clone();
        turn.raw_reply = Some(retained_raw(&response.text)?);
        turn.provider_model = response.provider_model.clone();
        turn.stop_reason = response.stop_reason.clone();
        turn.token_count = response.token_count;
        let failure = if !response.complete
            || response.stop_reason.as_deref() == Some("length")
            || response
                .token_count
                .is_some_and(|n| !(0..=256).contains(&n))
        {
            Some("Language response was incomplete or exceeded its 256-token limit.")
        } else if response.text.len() > 65_536 || !codec::has_non_whitespace(&response.text)? {
            Some("Reply was empty or exceeded the text limit.")
        } else {
            None
        };
        if let Some(reason) = failure {
            turn.status = TurnStatus::Failed;
            turn.failure = Some(reason.into());
            self.record.status = RunStatus::Failed;
            self.record.failure = Some(reason.into());
            self.stopped = true;
        } else {
            let features = codec::encode(&response.text)?;
            let semantic = codec::feedback(
                &features,
                self.record
                    .frames
                    .last()
                    .unwrap()
                    .spectral
                    .as_ref()
                    .unwrap(),
            );
            turn.reply = Some(response.text.clone());
            turn.encoded_features = Some(features);
            turn.semantic_vector = Some(semantic.clone());
            turn.status = TurnStatus::Completed;
            self.semantic = semantic;
            self.semantic_id = Some(id);
        }
        self.pending_language = None;
        self.record.turns.push(turn);
        Ok(())
    }
    pub fn fail_language(&mut self, id: usize, step: usize, reason: &str) -> Result<()> {
        self.finish_language(id, step, reason, false)
    }
    pub fn cancel_language(&mut self, id: usize, step: usize, reason: &str) -> Result<()> {
        self.finish_language(id, step, reason, true)
    }
    fn finish_language(
        &mut self,
        id: usize,
        step: usize,
        reason: &str,
        cancelled: bool,
    ) -> Result<()> {
        language_reason(reason)?;
        let pending = self
            .pending_language
            .as_ref()
            .ok_or_else(|| CoreError::Invalid("No pending language opportunity".into()))?;
        if cancelled {
            pending.public.matches(id, step)?;
        } else {
            pending.public.dispatched(id, step)?;
            ensure(
                !pending.response_received,
                "A received response cannot be rewritten as a provider-free language failure",
            )?;
        }
        let mut pending = self.pending_language.take().unwrap();
        pending.turn.status = if cancelled {
            TurnStatus::Cancelled
        } else {
            TurnStatus::Failed
        };
        pending.turn.failure = Some(reason.into());
        self.record.turns.push(pending.turn);
        if !cancelled {
            self.record.status = RunStatus::Failed;
            self.record.failure = Some(reason.into());
        }
        self.stopped = true;
        Ok(())
    }
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PendingJournal {
    pub action_id: usize,
    pub observed_step: usize,
    pub trigger: Trigger,
    pub entry: JournalEntry,
    pub relative_path: String,
    pub prompt: String,
    pub raw_reply: String,
}
struct Candidate {
    public: PendingJournal,
    receipt: ActionReceipt,
}
struct ActionLanguage {
    public: PendingLanguage,
    receipt: ActionReceipt,
    response_received: bool,
}

/// A required physical read, before text is exposed in a fresh prompt. `entry`
/// is the expected immutable value, not proof that storage was actually read.
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PendingMemory {
    pub action_id: usize,
    pub observed_step: usize,
    pub trigger: Trigger,
    pub entry: JournalEntry,
    pub relative_path: String,
}
enum Opportunity {
    Memory(PendingMemory),
    Language(ActionLanguage),
    Journal(Candidate),
    Wait(ActionReceipt),
}

/// The historical name remains source-compatible with the 0.7 D/E API.
pub type ActionSession = JournalSession;

pub struct JournalSession {
    record: ActionComparisonRecord,
    tape: Option<Arc<ActionReplyTape>>,
    request_order: usize,
    engine: ReservoirEngine,
    field: SensoryField,
    fill: ReducedFill,
    controller: RetentionController,
    retention: f64,
    rng: SplitMix64,
    semantic: Vec<f64>,
    semantic_id: Option<usize>,
    pending: Option<Candidate>,
    pending_memory: Option<PendingMemory>,
    pending_language: Option<ActionLanguage>,
    stopped: bool,
}

pub(crate) struct PreparedActionFrame {
    frame: ActionFrame,
    engine: ReservoirEngine,
    field: SensoryField,
    fill: ReducedFill,
    controller: RetentionController,
    rng: SplitMix64,
}

impl JournalSession {
    pub fn new(spec: ActionSpecification) -> Result<Self> {
        spec.validate()?;
        ensure_action_language(&spec)?;
        ensure(
            spec.comparison_kind == ComparisonKind::Components && !spec.compare_previous,
            "Fresh action sessions support standalone component A–H only; matched/observation comparisons are not available",
        )?;
        let tape = if spec.mode == ComparisonMode::FixedReplay {
            Some(Arc::new(ActionReplyTape::make(&spec)?))
        } else {
            None
        };
        let stage = spec.stage;
        Self::new_arm(spec, stage, Arm::Right, tape)
    }
    pub(crate) fn new_arm(
        spec: ActionSpecification,
        stage: u8,
        arm: Arm,
        tape: Option<Arc<ActionReplyTape>>,
    ) -> Result<Self> {
        let model = ReservoirModel::seeded(spec.seed);
        let mut controlled = model.clone();
        if !spec.bias_enabled {
            for row in 0..32 {
                controlled.input_weights[row * 67 + 66] = 0.0;
            }
        }
        if stage == 1 {
            controlled.recurrent_weights.fill(0.0);
        }
        let engine = ReservoirEngine::new(controlled, spec.leak, None)?;
        let field = SensoryField::seeded(spec.seed ^ FIELD_SEED);
        let right = ActionRunRecord {
            arm,
            observation_channel: Some(
                if spec.comparison_kind == ComparisonKind::Observation && arm == Arm::Right {
                    ObservationChannel::SensoryAndReservoir
                } else {
                    ObservationChannel::Sensory
                },
            ),
            stage,
            model,
            projection_weights: if stage >= 3 {
                field.projection.clone()
            } else {
                vec![]
            },
            frames: vec![],
            actions: vec![],
            journals: vec![],
            status: RunStatus::Stopped,
            failure: None,
        };
        let rng = SplitMix64::new(spec.seed ^ NOISE_SEED);
        let retention = spec.initial_retention;
        Ok(Self {
            record: ActionComparisonRecord {
                format: FORMATS[2].into(),
                specification: spec,
                tape: None,
                left: None,
                right,
                status: RunStatus::Stopped,
                failure: None,
            },
            tape,
            request_order: 1,
            engine,
            field,
            fill: ReducedFill::default(),
            controller: RetentionController::new(retention)?,
            retention,
            rng,
            semantic: vec![0.0; 48],
            semantic_id: None,
            pending: None,
            pending_memory: None,
            pending_language: None,
            stopped: false,
        })
    }
    pub fn frames(&self) -> &[ActionFrame] {
        &self.record.right.frames
    }
    pub fn actions(&self) -> &[ActionReceipt] {
        &self.record.right.actions
    }
    pub fn journals(&self) -> &[JournalEntry] {
        &self.record.right.journals
    }
    pub fn is_complete(&self) -> bool {
        self.record.status == RunStatus::Completed
    }
    pub fn is_failed(&self) -> bool {
        self.record.status == RunStatus::Failed
    }
    pub fn pending_journal(&self) -> Option<&PendingJournal> {
        self.pending.as_ref().map(|c| &c.public)
    }
    pub fn pending_memory(&self) -> Option<&PendingMemory> {
        self.pending_memory.as_ref()
    }
    pub fn pending_language(&self) -> Option<&PendingLanguage> {
        self.pending_language.as_ref().map(|p| &p.public)
    }
    pub fn tape(&self) -> Option<&ActionReplyTape> {
        self.tape.as_deref()
    }
    /// Portable snapshots cannot silently omit an unresolved journal candidate.
    pub fn record(&self) -> Result<ActionComparisonRecord> {
        ensure(self.pending.is_none() && self.pending_memory.is_none() && self.pending_language.is_none(), "Journal save, memory read or language opportunity is pending; resolve it, explicitly retain terminal failure/cancellation, or discard before snapshot")?;
        let mut record = self.record.clone();
        record.tape = self.tape.as_deref().cloned();
        Ok(record)
    }
    pub fn run(&self) -> &ActionRunRecord {
        &self.record.right
    }
    pub fn specification(&self) -> &ActionSpecification {
        &self.record.specification
    }
    pub fn stop(&mut self) -> Result<()> {
        ensure(
            self.pending.is_none() && self.pending_memory.is_none() && self.pending_language.is_none(),
            "Cannot stop with unresolved journal save/memory read; finalize the accurate outcome or discard",
        )?;
        self.stopped = true;
        Ok(())
    }
    fn ready(&self) -> Result<()> {
        ensure(
            !self.stopped && !self.is_complete() && !self.is_failed(),
            "Journal session is stopped, complete or failed",
        )?;
        ensure(
            self.pending.is_none()
                && self.pending_memory.is_none()
                && self.pending_language.is_none(),
            "Journal save/readback or memory read must finish before advancing",
        )
    }
    pub fn advance(&mut self) -> Result<ActionFrame> {
        let prepared = self.prepare_frame()?;
        let spec = &self.record.specification;
        let step = prepared.frame.step;
        let candidate = if self.record.right.stage >= 4
            && step.is_multiple_of(spec.turn_every)
            && step < spec.steps
        {
            Some(self.opportunity(&prepared.frame, Trigger::Scheduled)?)
        } else {
            None
        };
        let frame = self.commit_frame(prepared);
        if let Some(candidate) = candidate {
            self.accept_opportunity(candidate);
        }
        Ok(frame)
    }
    pub(crate) fn prepare_frame(&self) -> Result<PreparedActionFrame> {
        self.ready()?;
        let spec = &self.record.specification;
        let stage = self.record.right.stage;
        let step = self.frames().len() + 1;
        // Check the next opportunity before either member of a pair can commit.
        // Manual admission also reserves capacity for every remaining schedule.
        if stage >= 4 && step < spec.steps && step.is_multiple_of(spec.turn_every) {
            ensure(self.actions().len() < 128, "Native action limit reached")?;
        }
        let mut rng = self.rng.clone();
        let mut engine = copy_engine(&self.engine)?;
        let mut field = copy_field(&self.field)?;
        let mut fill = ReducedFill {
            fill: self.fill.fill,
        };
        let mut controller = RetentionController {
            current_retention: self.controller.current_retention,
            integral: self.controller.integral,
        };
        let external_input = crate::actions::external(spec, step);
        let mut input = external_input.clone();
        input[18..].copy_from_slice(&self.semantic);
        let noise: Vec<_> = (0..32)
            .map(|_| rng.signed() * spec.noise_amplitude)
            .collect();
        let previous_state = engine.state.clone();
        let state = engine.step(&input, &noise)?;
        let spectral = if stage >= 3 {
            Some(field.step(&input, self.retention)?)
        } else {
            None
        };
        let fill_percent = spectral
            .as_ref()
            .map(|m| 100.0 * fill.update(&m.eigenvalues, 1.0 / 3.0));
        let control = if stage == 8 {
            Some(controller.update(fill_percent.unwrap()))
        } else {
            None
        };
        let frame = ActionFrame {
            step,
            time: step as f64 * (1.0 / 3.0),
            input,
            external_input,
            semantic_input: self.semantic.clone(),
            previous_state,
            state,
            noise,
            retention_used: spectral.as_ref().map(|_| self.retention),
            spectral,
            fill_percent,
            control,
            semantic_action_id: self.semantic_id,
        };
        Ok(PreparedActionFrame {
            frame,
            rng,
            engine,
            field,
            fill,
            controller,
        })
    }
    pub(crate) fn commit_frame(&mut self, prepared: PreparedActionFrame) -> ActionFrame {
        let PreparedActionFrame {
            frame,
            rng,
            engine,
            field,
            fill,
            controller,
        } = prepared;
        let step = frame.step;
        self.rng = rng;
        self.engine = engine;
        self.field = field;
        self.fill = fill;
        self.controller = controller;
        if let Some(c) = &frame.control {
            self.retention = c.applied_retention;
        }
        if let Some(id) = self.semantic_id {
            self.record.right.actions[id - 1]
                .application_step
                .get_or_insert(step);
        }
        self.record.right.frames.push(frame.clone());
        if step == self.record.specification.steps {
            self.record.right.status = RunStatus::Completed;
            self.record.status = RunStatus::Completed;
        }
        frame
    }
    pub(crate) fn begin_opportunity(
        &mut self,
        trigger: Trigger,
        request_order: usize,
    ) -> Result<()> {
        self.request_order = request_order;
        let frame = self
            .frames()
            .last()
            .ok_or_else(|| CoreError::Invalid("No observed frame".into()))?;
        let candidate = self.opportunity(frame, trigger)?;
        self.accept_opportunity(candidate);
        Ok(())
    }
    pub(crate) fn cancel_before_action(&mut self, trigger: Trigger, reason: &str) -> Result<()> {
        ensure(
            !reason.is_empty() && reason.len() <= 4096,
            "Cancellation diagnostic must contain 1–4096 UTF-8 bytes",
        )?;
        let frame = self
            .frames()
            .last()
            .ok_or_else(|| CoreError::Invalid("No observed frame".into()))?;
        let mut receipt = self.receipt(frame, trigger, None);
        receipt.memory_entry_id = if self.record.right.stage >= 6 {
            self.journals().last().map(|j| j.id.clone())
        } else {
            None
        };
        receipt.failure_phase = Some(FailurePhase::Cancelled);
        receipt.failure = Some(reason.into());
        self.record.right.actions.push(receipt);
        self.stopped = true;
        Ok(())
    }
    pub fn request_journal(&mut self) -> Result<PendingJournal> {
        ensure(matches!(self.record.right.stage, 4 | 5), "Use request_action for stages with memory/choice; request_journal is the compatible D/E API")?;
        ensure(self.record.specification.language.backend == LanguageKind::Scripted || self.tape.is_some(), "Use request_action and settle pending language before requesting a provider-backed journal candidate")?;
        self.request_action()?;
        Ok(self.pending_journal().unwrap().clone())
    }
    pub fn can_request_action(&self) -> bool {
        if self.stopped
            || self.is_complete()
            || self.is_failed()
            || self.pending.is_some()
            || self.pending_memory.is_some()
            || self.pending_language.is_some()
            || self.record.right.stage < 4
        {
            return false;
        }
        let Some(frame) = self.frames().last() else {
            return false;
        };
        let spec = &self.record.specification;
        !frame.step.is_multiple_of(spec.turn_every)
            && self
                .actions()
                .last()
                .is_none_or(|a| a.observed_step != frame.step)
            && self.actions().len() + (spec.steps - 1) / spec.turn_every
                - frame.step / spec.turn_every
                < 128
    }
    /// Manual opportunities force WRITE even in G/H; memory must still be read.
    pub fn request_action(&mut self) -> Result<()> {
        self.ready()?;
        ensure(
            self.record.right.stage >= 4,
            "Stages A–C have no journal action",
        )?;
        let frame = self
            .frames()
            .last()
            .ok_or_else(|| CoreError::Invalid("Advance before requesting a journal".into()))?;
        ensure(
            !frame
                .step
                .is_multiple_of(self.record.specification.turn_every),
            "Scheduled boundaries already own their journal opportunity",
        )?;
        ensure(
            self.actions()
                .last()
                .is_none_or(|a| a.observed_step != frame.step),
            "Boundary already has an action",
        )?;
        // Reserve enough of the native 128-action budget for all remaining
        // scheduled opportunities, so manual journals cannot break a later run.
        let spec = &self.record.specification;
        let remaining = (spec.steps - 1) / spec.turn_every - frame.step / spec.turn_every;
        ensure(
            self.actions().len() + remaining < 128,
            "Manual action would exhaust remaining scheduled action capacity",
        )?;
        let candidate = self.opportunity(frame, Trigger::Manual)?;
        self.accept_opportunity(candidate);
        Ok(())
    }
    fn opportunity(&self, frame: &ActionFrame, trigger: Trigger) -> Result<Opportunity> {
        ensure(self.actions().len() < 128, "Native action limit reached")?;
        if self.record.right.stage >= 6 {
            if let Some(entry) = self.journals().last() {
                return Ok(Opportunity::Memory(PendingMemory {
                    action_id: self.actions().len() + 1,
                    observed_step: frame.step,
                    trigger,
                    relative_path: format!("{}/{}.json", self.record.right.arm.label(), entry.id),
                    entry: entry.clone(),
                }));
            }
        }
        self.response(frame, trigger, None)
    }
    fn accept_opportunity(&mut self, candidate: Opportunity) {
        match candidate {
            Opportunity::Memory(memory) => self.pending_memory = Some(memory),
            Opportunity::Language(language) => self.pending_language = Some(language),
            Opportunity::Journal(journal) => self.pending = Some(journal),
            Opportunity::Wait(receipt) => self.record.right.actions.push(receipt),
        }
    }
    fn receipt(
        &self,
        frame: &ActionFrame,
        trigger: Trigger,
        memory: Option<&JournalEntry>,
    ) -> ActionReceipt {
        ActionReceipt {
            id: self.actions().len() + 1,
            observed_step: frame.step,
            trigger,
            prompt: crate::actions::prompt(
                self.record.right.stage,
                frame,
                memory,
                trigger == Trigger::Manual,
                self.record
                    .right
                    .observation_channel
                    .unwrap_or(ObservationChannel::Sensory),
                &self.record.specification,
            ),
            requested_action: if self.record.right.stage >= 7 && trigger != Trigger::Manual {
                None
            } else {
                Some(JournalAction::WriteJournal)
            },
            raw_reply: None,
            raw_reply_byte_count: None,
            chosen_action: None,
            status: TurnStatus::Cancelled,
            failure: None,
            provider_model: None,
            stop_reason: None,
            token_count: None,
            provider_complete: None,
            request_started: false,
            failure_phase: None,
            journal_entry_id: None,
            save_receipt: None,
            memory_entry_id: memory.map(|m| m.id.clone()),
            memory_text: memory.map(|m| m.text.clone()),
            encoded_features: None,
            semantic_vector: None,
            application_step: None,
            tape_packet_id: self.tape.as_deref().map(|_| frame.step),
            request_order: None,
        }
    }
    fn response(
        &self,
        frame: &ActionFrame,
        trigger: Trigger,
        memory: Option<&JournalEntry>,
    ) -> Result<Opportunity> {
        if self.record.specification.language.backend == LanguageKind::Ollama && self.tape.is_none()
        {
            let receipt = self.receipt(frame, trigger, memory);
            return Ok(Opportunity::Language(ActionLanguage {
                response_received: false,
                public: PendingLanguage {
                    turn_id: receipt.id,
                    observed_step: frame.step,
                    configuration: self.record.specification.language.clone(),
                    prompt: receipt.prompt.clone(),
                    request_started: false,
                    request_order: None,
                },
                receipt,
            }));
        }
        let id = self.actions().len() + 1;
        let packet = self.tape.as_ref().map(|t| &t.packets[frame.step - 1]);
        let choice = if self.record.right.stage >= 7 && trigger != Trigger::Manual {
            packet.map(|p| p.choice).unwrap_or(if id.is_multiple_of(3) {
                JournalAction::Wait
            } else {
                JournalAction::WriteJournal
            })
        } else {
            JournalAction::WriteJournal
        };
        let text = if choice == JournalAction::Wait {
            String::new()
        } else {
            packet
                .map(|p| p.text.as_str())
                .unwrap_or(SCRIPTED_REPLIES[(id - 1) % SCRIPTED_REPLIES.len()])
                .to_string()
        };
        let raw_reply = serde_json::to_string(&serde_json::json!({"action":choice,"text":text}))
            .map_err(|e| CoreError::Invalid(e.to_string()))?;
        let mut receipt = self.receipt(frame, trigger, memory);
        receipt.raw_reply = Some(raw_reply.clone());
        receipt.raw_reply_byte_count = Some(raw_reply.len());
        receipt.chosen_action = Some(choice);
        receipt.status = TurnStatus::Completed;
        receipt.provider_model = Some(
            if packet.is_some() {
                "essentials-action-tape-v1"
            } else {
                "essentials-action-script-v1"
            }
            .into(),
        );
        receipt.stop_reason = Some(
            if packet.is_some() {
                "replayed"
            } else {
                "scripted"
            }
            .into(),
        );
        receipt.provider_complete = Some(true);
        receipt.request_started = packet.is_none();
        receipt.request_order = if packet.is_none() {
            Some(self.request_order)
        } else {
            None
        };
        if choice == JournalAction::Wait {
            return Ok(Opportunity::Wait(receipt));
        }
        let sha256 = format!("{:x}", Sha256::digest(text.as_bytes()));
        let entry = JournalEntry {
            id: format!("journal-{}-{}-{}", frame.step, id, sha256),
            action_id: id,
            observed_step: frame.step,
            text,
            sha256,
        };
        receipt.journal_entry_id = Some(entry.id.clone());
        Ok(Opportunity::Journal(Candidate {
            public: PendingJournal {
                action_id: id,
                observed_step: frame.step,
                trigger,
                relative_path: format!("{}/{}.json", self.record.right.arm.label(), entry.id),
                entry,
                prompt: receipt.prompt.clone(),
                raw_reply,
            },
            receipt,
        }))
    }
    pub fn start_language(&mut self, id: usize, step: usize) -> Result<()> {
        let pending = self
            .pending_language
            .as_mut()
            .ok_or_else(|| CoreError::Invalid("No pending language opportunity".into()))?;
        pending.public.start(id, step, Some(self.request_order))?;
        pending.receipt.request_started = true;
        pending.receipt.request_order = Some(self.request_order);
        Ok(())
    }
    pub fn confirm_language(
        &mut self,
        id: usize,
        step: usize,
        response: &LanguageResponse,
    ) -> Result<()> {
        let pending = self
            .pending_language
            .as_mut()
            .ok_or_else(|| CoreError::Invalid("No pending language opportunity".into()))?;
        pending.public.dispatched(id, step)?;
        ensure(!pending.response_received, "A response already settled or blocked this opportunity; only explicit cancellation remains")?;
        pending.response_received = true;
        let mut receipt = pending.receipt.clone();
        // Validation observes the complete response; only the retained failed
        // outcome may use native's bounded 16,000-grapheme prefix.
        receipt.raw_reply = Some(response.text.clone());
        receipt.raw_reply_byte_count = Some(response.text.len());
        receipt.provider_model = response
            .provider_model
            .as_ref()
            .map(|v| v.graphemes(true).take(256).collect::<String>());
        receipt.stop_reason = response
            .stop_reason
            .as_ref()
            .map(|v| v.graphemes(true).take(256).collect::<String>());
        ensure(
            [&receipt.provider_model, &receipt.stop_reason]
                .iter()
                .all(|v| v.as_ref().is_none_or(|v| v.len() <= 4096)),
            "Provider metadata exceeds the retained action byte bound",
        )?;
        receipt.token_count = response.token_count;
        receipt.provider_complete = Some(response.complete);
        let parsed = crate::actions::parse_reply(
            &receipt,
            self.record.right.stage,
            receipt.trigger == Trigger::Manual,
        );
        receipt.raw_reply = Some(retained_raw(&response.text)?);
        let (choice, text) = match parsed {
            Ok(value) => value,
            Err(CoreError::Invalid(_)) => {
                let reason = "Language response was incomplete or invalid under the action envelope and output limits.".to_string();
                receipt.status = TurnStatus::Failed;
                receipt.failure_phase = Some(FailurePhase::ResponseValidation);
                receipt.failure = Some(reason.clone());
                self.pending_language = None;
                self.record.right.actions.push(receipt);
                self.mark_failed(&reason);
                return Ok(());
            }
            Err(error) => return Err(error),
        };
        // Qualify feedback text before storage is invited. Unsupported text
        // remains an unresolved boundary; no durable journal is manufactured.
        if choice == JournalAction::WriteJournal {
            codec::encode(&text)?;
        }
        receipt.chosen_action = Some(choice);
        receipt.status = TurnStatus::Completed;
        if choice == JournalAction::Wait {
            self.pending_language = None;
            self.record.right.actions.push(receipt);
            return Ok(());
        }
        let sha256 = format!("{:x}", Sha256::digest(text.as_bytes()));
        let entry = JournalEntry {
            id: format!("journal-{step}-{id}-{sha256}"),
            action_id: id,
            observed_step: step,
            text,
            sha256,
        };
        receipt.journal_entry_id = Some(entry.id.clone());
        self.pending = Some(Candidate {
            public: PendingJournal {
                action_id: id,
                observed_step: step,
                trigger: receipt.trigger,
                relative_path: format!("{}/{}.json", self.record.right.arm.label(), entry.id),
                entry,
                prompt: receipt.prompt.clone(),
                raw_reply: response.text.clone(),
            },
            receipt,
        });
        self.pending_language = None;
        Ok(())
    }
    pub fn fail_language(&mut self, id: usize, step: usize, reason: &str) -> Result<()> {
        self.finish_language(id, step, reason, false)
    }
    pub fn cancel_language(&mut self, id: usize, step: usize, reason: &str) -> Result<()> {
        self.finish_language(id, step, reason, true)
    }
    fn finish_language(
        &mut self,
        id: usize,
        step: usize,
        reason: &str,
        cancelled: bool,
    ) -> Result<()> {
        language_reason(reason)?;
        let pending = self
            .pending_language
            .as_ref()
            .ok_or_else(|| CoreError::Invalid("No pending language opportunity".into()))?;
        if cancelled {
            pending.public.matches(id, step)?;
        } else {
            pending.public.dispatched(id, step)?;
            ensure(
                !pending.response_received,
                "A received response cannot be rewritten as a provider-free language failure",
            )?;
        }
        let mut pending = self.pending_language.take().unwrap();
        pending.receipt.status = if cancelled {
            TurnStatus::Cancelled
        } else {
            TurnStatus::Failed
        };
        pending.receipt.failure_phase = Some(if cancelled {
            FailurePhase::Cancelled
        } else {
            FailurePhase::Language
        });
        pending.receipt.failure = Some(reason.into());
        self.record.right.actions.push(pending.receipt);
        if cancelled {
            self.stopped = true;
        } else {
            self.mark_failed(reason);
        }
        Ok(())
    }
    /// Backend supplies an actual fresh disk read. Mismatch leaves this boundary
    /// unresolved; caller can retain the read failure through fail_memory.
    pub fn confirm_memory(&mut self, readback: &JournalEntry) -> Result<()> {
        let pending = self
            .pending_memory
            .as_ref()
            .ok_or_else(|| CoreError::Invalid("No pending memory read".into()))?;
        ensure(
            readback == &pending.entry,
            "Memory readback differs from the latest saved journal",
        )?;
        let response = self.response(
            self.frames().last().unwrap(),
            pending.trigger,
            Some(readback),
        )?;
        self.pending_memory = None;
        self.accept_opportunity(response);
        Ok(())
    }
    pub fn fail_memory(&mut self, reason: &str) -> Result<()> {
        self.finish_memory(reason, false)
    }
    pub fn cancel_memory(&mut self, reason: &str) -> Result<()> {
        self.finish_memory(reason, true)
    }
    fn finish_memory(&mut self, reason: &str, cancelled: bool) -> Result<()> {
        ensure(
            !reason.is_empty() && reason.len() <= 4096,
            "Memory outcome diagnostic must contain 1–4096 UTF-8 bytes",
        )?;
        let pending = self
            .pending_memory
            .as_ref()
            .ok_or_else(|| CoreError::Invalid("No pending memory read".into()))?;
        let mut receipt = self.receipt(self.frames().last().unwrap(), pending.trigger, None);
        receipt.memory_entry_id = Some(pending.entry.id.clone());
        receipt.status = if cancelled {
            TurnStatus::Cancelled
        } else {
            TurnStatus::Failed
        };
        receipt.failure_phase = Some(if cancelled {
            FailurePhase::Cancelled
        } else {
            FailurePhase::MemoryRead
        });
        receipt.failure = Some(reason.into());
        self.pending_memory = None;
        self.record.right.actions.push(receipt);
        if !cancelled {
            self.mark_failed(reason);
        } else {
            self.stopped = true;
        }
        Ok(())
    }
    /// Caller owns real atomic publication, durability, and a fresh disk read.
    /// This method validates supplied evidence; it does not authenticate a disk.
    pub fn confirm_saved(
        &mut self,
        saved: &JournalSaveReceipt,
        readback: &JournalEntry,
    ) -> Result<()> {
        let candidate = self
            .pending
            .as_ref()
            .ok_or_else(|| CoreError::Invalid("No pending journal".into()))?;
        let p = &candidate.public;
        ensure(
            saved.status == SaveStatus::Saved
                && saved.failure.is_none()
                && saved.entry_id == p.entry.id
                && saved.sha256 == p.entry.sha256
                && saved.relative_path.as_deref() == Some(p.relative_path.as_str())
                && readback == &p.entry,
            "Save/readback receipt does not match the pending journal",
        )?;
        let features = codec::encode(&p.entry.text)?;
        let vector = if let Some(tape) = &self.tape {
            tape.packets[p.observed_step - 1].semantic_vector.clone()
        } else {
            codec::feedback(
                &features,
                self.frames().last().unwrap().spectral.as_ref().unwrap(),
            )
        };
        let mut candidate = self.pending.take().unwrap();
        candidate.receipt.save_receipt = Some(saved.clone());
        candidate.receipt.encoded_features = Some(features);
        candidate.receipt.semantic_vector = Some(vector.clone());
        if self.record.right.stage >= 5 {
            self.semantic = vector;
            self.semantic_id = Some(candidate.receipt.id);
        }
        self.record.right.journals.push(candidate.public.entry);
        self.record.right.actions.push(candidate.receipt);
        Ok(())
    }
    /// Explicit terminal outcome. This historical failure can never be retried
    /// into success; only unresolved candidates may be retried by the backend.
    pub fn fail_pending(&mut self, reason: &str) -> Result<()> {
        ensure(
            !reason.is_empty() && reason.len() <= 4096,
            "Failure diagnostic must contain 1–4096 UTF-8 bytes",
        )?;
        let mut candidate = self
            .pending
            .take()
            .ok_or_else(|| CoreError::Invalid("No pending journal".into()))?;
        candidate.receipt.failure_phase = Some(FailurePhase::JournalSave);
        candidate.receipt.failure = Some(reason.into());
        candidate.receipt.save_receipt = Some(JournalSaveReceipt {
            status: SaveStatus::Failed,
            entry_id: candidate.public.entry.id,
            sha256: candidate.public.entry.sha256,
            relative_path: None,
            failure: Some(reason.into()),
        });
        self.record.right.actions.push(candidate.receipt);
        self.mark_failed(reason);
        Ok(())
    }
    fn mark_failed(&mut self, reason: &str) {
        self.record.right.status = RunStatus::Failed;
        self.record.status = RunStatus::Failed;
        self.record.right.failure = Some(reason.into());
        self.record.failure = Some(reason.into());
        self.stopped = true;
    }
}

pub(crate) fn ensure_action_language(spec: &ActionSpecification) -> Result<()> {
    if spec.language.backend != LanguageKind::Scripted
        && (spec.stage < 4 || spec.mode != ComparisonMode::IndependentGeneration)
    {
        Err(CoreError::Unsupported(
            "Provider-backed fresh actions require independent D–H; fixed tapes and A–C remain scripted"
                .into(),
        ))
    } else {
        Ok(())
    }
}
fn copy_engine(e: &ReservoirEngine) -> Result<ReservoirEngine> {
    ReservoirEngine::new(e.model.clone(), e.leak, Some(e.state.clone()))
}
fn copy_field(f: &SensoryField) -> Result<SensoryField> {
    SensoryField::new(
        f.dimension,
        f.input_count,
        f.projection.clone(),
        Some(f.covariance.clone()),
    )
}
