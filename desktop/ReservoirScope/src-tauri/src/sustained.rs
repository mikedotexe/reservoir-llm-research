//! One backend-owned sustained clock. Provider calls happen outside the state
//! mutex, and only a durable prepared checkpoint can authorize feedback.
#[path = "sustained_peers.rs"]
mod peers;
use crate::{
    files::AppError,
    records::FrameView,
    sessions::SessionFrame,
    sustained_store::{self, JournalIndex, Manifest, SustainedStore},
};
use reservoir_core::{
    session::LanguageResponse,
    stage::{LanguageConfiguration, LanguageKind, SCRIPTED_REPLIES},
    sustained::{
        default_difference_clip, default_difference_dead_band, default_difference_tau,
        default_difference_watchdog, default_difference_watchdog_fill_std,
        is_default_difference_clip, is_default_difference_dead_band, is_default_difference_tau,
        is_default_difference_watchdog, is_default_difference_watchdog_fill_std,
        is_legacy_feedback_scale, is_legacy_output_tokens, is_legacy_request_deadline_seconds,
        is_legacy_sensory_noise_amplitude, is_zero, legacy_feedback_scale, legacy_output_tokens,
        legacy_request_deadline_seconds, legacy_sensory_noise_amplitude, SustainedCheckpoint,
        SustainedEventKind, SustainedPhase, SustainedPromptVersion, SustainedRunLimitContext,
        SustainedSession, SustainedSpecification, CURRENT_PROMPT_VERSION, DEFAULT_FEEDBACK_SCALE,
        DEFAULT_OUTPUT_TOKENS, DEFAULT_REQUEST_DEADLINE_SECONDS, DEFAULT_SENSORY_NOISE_AMPLITUDE,
    },
};
use serde::{Deserialize, Serialize};
use std::{
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, AtomicU64, Ordering},
        mpsc::{sync_channel, SyncSender},
        Arc, Mutex, MutexGuard,
    },
    time::{Duration, Instant, SystemTime},
};

use reservoir_core::sustained::{is_zero_u64, SustainedMemoryPolicy};
#[path = "sustained_check_ins.rs"]
mod check_ins;
use check_ins::CheckInSummary;
#[path = "sustained_actions.rs"]
mod actions;
use actions::ActionsSummary;

#[path = "sustained_sonar.rs"]
mod sonar;
#[path = "sustained_configuration.rs"]
mod configuration;
pub use configuration::{ConfigurationRecord, BoundaryTarget};
pub use sonar::SonarView;

static NEXT_SESSION_ID: AtomicU64 = AtomicU64::new(1);

fn err(kind: &str, message: impl Into<String>) -> AppError {
    AppError::new("sustained", kind, message)
}
fn ce(e: impl std::fmt::Display) -> AppError {
    err("engine", e.to_string())
}
#[derive(Clone, Serialize, Deserialize, schemars::JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedConfig {
    #[serde(default = "reservoir_core::sustained::default_reservoir_nodes", skip_serializing_if = "reservoir_core::sustained::is_default_reservoir_nodes")]
    pub reservoir_nodes: usize,
    #[serde(default = "reservoir_core::sustained::default_recurrent_gain", skip_serializing_if = "reservoir_core::sustained::is_default_recurrent_gain")]
    pub recurrent_gain: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sonar: Option<reservoir_core::sustained::SustainedSonarConfig>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub peer_reading: Option<reservoir_core::sustained::SustainedPeerConfig>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub text_admission: Option<reservoir_core::sustained::SustainedTextAdmission>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub control_feedback: Option<reservoir_core::sustained::SustainedControlFeedback>,
    /// Immutable, opt-in authority for fresh ordinary writing turns only.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub action_mode: Option<reservoir_core::sustained::SustainedActionMode>,
    /// Optional elapsed-running-time conversation schedule; absent in historical sessions.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub check_in_schedule: Option<reservoir_core::sustained::SustainedCheckInSchedule>,
    pub seed: String,
    pub turn_every: u64,
    pub maximum_steps: u64,
    pub maximum_turns: u64,
    pub maximum_duration_seconds: u64,
    pub storage_budget_bytes: u64,
    pub pace_ms: u64,
    pub leak: f64,
    pub noise_amplitude: f64,
    pub initial_retention: f64,
    pub regulation_enabled: bool,
    pub language: LanguageConfiguration,
    #[serde(default, skip_serializing_if = "SustainedPromptVersion::is_legacy")]
    pub prompt_version: SustainedPromptVersion,
    #[serde(
        default = "legacy_output_tokens",
        skip_serializing_if = "is_legacy_output_tokens"
    )]
    pub output_tokens: u32,
    #[serde(
        default = "legacy_request_deadline_seconds",
        skip_serializing_if = "is_legacy_request_deadline_seconds"
    )]
    pub request_deadline_seconds: u64,
    /// Omitted historical configuration keeps mechanism v1 (no field noise, feedback ×1).
    #[serde(
        default = "legacy_sensory_noise_amplitude",
        skip_serializing_if = "is_legacy_sensory_noise_amplitude"
    )]
    pub sensory_noise_amplitude: f64,
    #[serde(
        default = "legacy_feedback_scale",
        skip_serializing_if = "is_legacy_feedback_scale"
    )]
    pub feedback_scale: f64,
    /// Embedding codec (S-010 Part B): the local embedding model; omitted keeps the
    /// surface codec. The projection seed defaults to the session seed.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub embedding_model: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub embedding_projection_seed: Option<String>,
    /// Difference-signal channel (S-011 M5); gain 0 keeps every earlier mechanism identity.
    #[serde(default, skip_serializing_if = "is_zero")]
    pub difference_gain: f64,
    #[serde(
        default = "default_difference_tau",
        skip_serializing_if = "is_default_difference_tau"
    )]
    pub difference_tau: f64,
    #[serde(
        default = "default_difference_dead_band",
        skip_serializing_if = "is_default_difference_dead_band"
    )]
    pub difference_dead_band: f64,
    #[serde(
        default = "default_difference_clip",
        skip_serializing_if = "is_default_difference_clip"
    )]
    pub difference_clip: f64,
    #[serde(
        default = "default_difference_watchdog",
        skip_serializing_if = "is_default_difference_watchdog"
    )]
    pub difference_watchdog: bool,
    #[serde(
        default = "default_difference_watchdog_fill_std",
        skip_serializing_if = "is_default_difference_watchdog_fill_std"
    )]
    pub difference_watchdog_fill_std: f64,
    /// Steps before the watchdog's fill ring counts (0.36.0); 0 is as built.
    #[serde(default, skip_serializing_if = "is_zero_u64")]
    pub difference_watchdog_warmup: u64,
    /// Which earlier entry a turn returns as memory (0.36.0); `latest` is as built.
    #[serde(default, skip_serializing_if = "SustainedMemoryPolicy::is_latest")]
    pub memory_policy: SustainedMemoryPolicy,
    /// Turns during which a returned entry stays out of the older-entry policies'
    /// candidates (0.38.0); 0 is as built.
    #[serde(default, skip_serializing_if = "is_zero_u64")]
    pub memory_recent_exclusion: u64,
}
impl Default for SustainedConfig {
    fn default() -> Self {
        Self {
            reservoir_nodes: 32,
            recurrent_gain: 1.0,
            sonar: None,
            peer_reading: None,
            text_admission: None,
            control_feedback: None,
            action_mode: None,
            check_in_schedule: None,
            seed: "20260909".into(),
            turn_every: 30,
            maximum_steps: 10800,
            maximum_turns: 360,
            maximum_duration_seconds: 21600,
            storage_budget_bytes: 268435456,
            pace_ms: 1000,
            leak: 0.65,
            noise_amplitude: 0.02,
            initial_retention: 0.955,
            regulation_enabled: true,
            language: LanguageConfiguration::default(),
            prompt_version: CURRENT_PROMPT_VERSION,
            output_tokens: DEFAULT_OUTPUT_TOKENS,
            request_deadline_seconds: DEFAULT_REQUEST_DEADLINE_SECONDS,
            sensory_noise_amplitude: DEFAULT_SENSORY_NOISE_AMPLITUDE,
            feedback_scale: DEFAULT_FEEDBACK_SCALE,
            embedding_model: None,
            embedding_projection_seed: None,
            difference_gain: 0.0,
            difference_tau: default_difference_tau(),
            difference_dead_band: default_difference_dead_band(),
            difference_clip: default_difference_clip(),
            difference_watchdog: default_difference_watchdog(),
            difference_watchdog_fill_std: default_difference_watchdog_fill_std(),
            difference_watchdog_warmup: 0,
            memory_policy: SustainedMemoryPolicy::Latest,
            memory_recent_exclusion: 0,
        }
    }
}
impl SustainedConfig {
    pub fn validate(&self) -> Result<(), AppError> {
        if !(1..=1_000_000).contains(&self.maximum_steps)
            || !(1..=10_000).contains(&self.maximum_turns)
            || !(1..=86_400).contains(&self.maximum_duration_seconds)
            || !(16 * 1024 * 1024..=512 * 1024 * 1024).contains(&self.storage_budget_bytes)
            || !(100..=10_000).contains(&self.pace_ms)
        {
            return Err(err("configuration","Sustained budgets: 1–1,000,000 steps, 1–10,000 attempts, 1–86,400 seconds, 16–512 MiB and 100–10,000 ms pacing."));
        }
        self.specification()?.validate().map_err(ce)?;
        if let Some(schedule) = &self.check_in_schedule {
            if schedule.end_after_seconds != self.maximum_duration_seconds {
                return Err(err(
                    "configuration",
                    "The conversation schedule must end at the session's original duration.",
                ));
            }
            let slots = schedule
                .end_after_seconds
                .div_ceil(schedule.interval_seconds);
            let steps = (schedule.end_after_seconds * 1000).div_ceil(self.pace_ms) + slots + 1;
            let turns = steps.div_ceil(self.turn_every) + slots;
            if self.maximum_steps < steps || self.maximum_turns < turns {
                return Err(err("configuration", format!("This schedule needs at least {steps} steps and {turns} writing attempts; increase the run limits before creating it.")));
            }
        }
        if self.language.backend == LanguageKind::Ollama {
            crate::model_transport::validate_configuration(&self.language).map_err(ce)?;
        }
        Ok(())
    }
    pub fn specification(&self) -> Result<SustainedSpecification, AppError> {
        let seed = self
            .seed
            .parse::<u64>()
            .map_err(|_| err("seed", "Use an unsigned decimal 64-bit seed"))?;
        if self.seed != seed.to_string() {
            return Err(err("seed", "Seed must be canonical unsigned decimal"));
        }
        Ok(SustainedSpecification {
            reservoir_nodes: self.reservoir_nodes,
            recurrent_gain: self.recurrent_gain,
            sonar: self.sonar.clone(),
            peer_reading: self.peer_reading.clone(),
            text_admission: self.text_admission,
            control_feedback: self.control_feedback,
            action_mode: self.action_mode,
            check_in_schedule: self.check_in_schedule.clone(),
            seed,
            dt: 1.0 / 3.0,
            leak: self.leak,
            noise_amplitude: self.noise_amplitude,
            initial_retention: self.initial_retention,
            regulation_enabled: self.regulation_enabled,
            turn_every: self.turn_every,
            maximum_steps: self.maximum_steps,
            maximum_turns: self.maximum_turns,
            language: self.language.clone(),
            prompt_version: self.prompt_version,
            output_tokens: self.output_tokens,
            request_deadline_seconds: self.request_deadline_seconds,
            sensory_noise_amplitude: self.sensory_noise_amplitude,
            feedback_scale: self.feedback_scale,
            difference_gain: self.difference_gain,
            difference_tau: self.difference_tau,
            difference_dead_band: self.difference_dead_band,
            difference_clip: self.difference_clip,
            difference_watchdog: self.difference_watchdog,
            difference_watchdog_fill_std: self.difference_watchdog_fill_std,
            difference_watchdog_warmup: self.difference_watchdog_warmup,
            memory_policy: self.memory_policy,
            memory_recent_exclusion: self.memory_recent_exclusion,
            codec: match &self.embedding_model {
                None => reservoir_core::sustained::SustainedCodec::Surface,
                Some(model) => {
                    let projection_seed = match &self.embedding_projection_seed {
                        None => seed,
                        Some(text) => {
                            let value = text.parse::<u64>().map_err(|_| {
                                err("seed", "Use an unsigned decimal projection seed")
                            })?;
                            if *text != value.to_string() {
                                return Err(err(
                                    "seed",
                                    "Projection seed must be canonical unsigned decimal",
                                ));
                            }
                            value
                        }
                    };
                    reservoir_core::sustained::SustainedCodec::Embedding {
                        model: model.clone(),
                        projection_seed,
                    }
                }
            },
        })
    }
}
pub const MAX_LIMIT_EXTENSIONS: usize = 256;
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedRunLimits {
    pub maximum_steps: u64,
    pub maximum_turns: u64,
    pub maximum_duration_seconds: u64,
}
impl SustainedRunLimits {
    pub fn from_config(config: &SustainedConfig) -> Self {
        Self {
            maximum_steps: config.maximum_steps,
            maximum_turns: config.maximum_turns,
            maximum_duration_seconds: config.maximum_duration_seconds,
        }
    }
    pub fn validate_extension(&self, previous: &Self) -> Result<(), AppError> {
        if !(1..=1_000_000).contains(&self.maximum_steps)
            || !(1..=10_000).contains(&self.maximum_turns)
            || !(1..=86_400).contains(&self.maximum_duration_seconds)
            || self.maximum_steps < previous.maximum_steps
            || self.maximum_turns < previous.maximum_turns
            || self.maximum_duration_seconds < previous.maximum_duration_seconds
            || self == previous
        {
            return Err(err("limits", "Increase at least one limit without lowering another; maximum totals are 1,000,000 steps, 10,000 attempts and 24 hours."));
        }
        Ok(())
    }
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedLimitExtension {
    pub event_id: u64,
    pub step: u64,
    pub elapsed_millis: u64,
    pub limits: SustainedRunLimits,
}
/// Embeds one entry for the embedding codec: the real transport in the app, a fake in tests.
type Embedder = Arc<
    dyn Fn(
            &LanguageConfiguration,
            &str,
            &str,
            &AtomicBool,
            u64,
        ) -> Result<crate::model_transport::EmbeddingReceipt, String>
        + Send
        + Sync,
>;
fn transport_embedder() -> Embedder {
    Arc::new(|c, model, text, cancel, deadline| {
        crate::model_transport::embed(c, model, text, cancel, deadline).map_err(|e| e.to_string())
    })
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PendingLanguage {
    pub operation_id: String,
    pub turn_id: u64,
    pub attempt_id: u64,
    pub observed_step: u64,
    pub endpoint: String,
    pub model: String,
    pub state: String,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PendingEmbedding {
    pub attempt_id: u64,
    pub observed_step: u64,
    pub response_text: String,
    pub reason: Option<String>,
    pub state: &'static str,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PendingSave {
    pub attempt_id: u64,
    pub entry_id: String,
    pub observed_step: u64,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PendingApplication {
    pub attempt_id: u64,
    pub entry_id: String,
    pub observed_step: u64,
    pub intended_step: u64,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SustainedSummary {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub actions: Option<ActionsSummary>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub check_ins: Option<CheckInSummary>,
    pub effective_limits: SustainedRunLimits,
    pub can_extend_limits: bool,
    pub limit_extension_count: usize,
    pub session_id: String,
    pub generation: String,
    pub revision: String,
    pub config: SustainedConfig,
    pub original_config: SustainedConfig,
    pub configuration_revision: u64,
    pub configuration_history: Vec<ConfigurationRecord>,
    pub phase: String,
    pub step: u64,
    pub durable_step: u64,
    pub simulated_time: f64,
    pub elapsed_seconds: f64,
    pub used_bytes: u64,
    pub journal_count: u64,
    pub turn_count: u64,
    pub can_start: bool,
    pub can_pause: bool,
    pub can_stop: bool,
    pub can_retry_save: bool,
    pub can_retry_provider: bool,
    pub can_retry_embedding: bool,
    pub can_skip_feedback: bool,
    pub pending_language: Option<PendingLanguage>,
    pub pending_embedding: Option<PendingEmbedding>,
    pub pending_save: Option<PendingSave>,
    pub pending_application: Option<PendingApplication>,
    pub diagnostics: Vec<String>,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SustainedUpdate {
    pub request_id: String,
    pub snapshot_sequence: String,
    pub summary: Option<SustainedSummary>,
    pub frame: Option<SessionFrame>,
    pub close_requested: bool,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct JournalPage {
    pub request_id: String,
    pub session_id: String,
    pub generation: String,
    pub revision: String,
    pub total: usize,
    pub offset: usize,
    pub has_more: bool,
    pub entries: Vec<JournalIndex>,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct JournalDetail {
    pub request_id: String,
    pub session_id: String,
    pub generation: String,
    pub revision: String,
    pub journal: serde_json::Value,
}
type Listener = Arc<dyn Fn(SustainedUpdate) -> bool + Send + Sync>;
type Provider = Arc<
    dyn Fn(
            &LanguageConfiguration,
            &str,
            &AtomicBool,
            u32,
            u64,
            crate::model_transport::Sampling,
        ) -> Result<LanguageResponse, String>
        + Send
        + Sync,
>;
struct Active {
    engine: SustainedSession,
    manifest: Manifest,
    committed: SustainedCheckpoint,
    used_bytes: u64,
    catalog: Vec<JournalIndex>,
    epoch: u64,
    worker_active: bool,
    run_requested: bool,
    dispatch_once: bool,
    last_accounted: Instant,
}
struct Inner {
    active: Option<Active>,
    listener: Option<Listener>,
    generation: u64,
}
struct Shared {
    inner: Mutex<Inner>,
    store: SustainedStore,
    provider: Provider,
    embedder: Embedder,
    closing: AtomicBool,
    close_requested: AtomicBool,
    busy: AtomicBool,
    pause: AtomicBool,
    cancel: AtomicBool,
    interrupted: AtomicBool,
    epoch: AtomicU64,
    exports: AtomicU64,
    snapshot_sequence: AtomicU64,
    updates: SyncSender<()>,
    configuration_pause: AtomicBool,
    configuration_uncertain: AtomicBool,
    boundary_targets: Mutex<std::collections::BTreeMap<String, BoundaryTarget>>,
    scheduler: Mutex<Option<crate::provider_scheduler::ProviderScheduler>>,
}
#[derive(Clone)]
pub struct SustainedState {
    shared: Arc<Shared>,
}
impl SustainedState {
    pub fn new(root: PathBuf) -> Self {
        Self::with_provider(
            root,
            Arc::new(|c, p, x, tokens, deadline, sampling| {
                crate::model_transport::generate_sustained(c, p, x, tokens, deadline, sampling)
                    .map_err(|e| e.to_string())
            }),
        )
    }
    fn with_provider(root: PathBuf, provider: Provider) -> Self {
        Self::with_provider_and_embedder(root, provider, transport_embedder())
    }
    fn with_provider_and_embedder(root: PathBuf, provider: Provider, embedder: Embedder) -> Self {
        // A single coalescing publisher serves this state, including across
        // successive runs. Slow state reads or WebView callbacks cannot block
        // the clock/watchdog or allocate an unbounded queue of old snapshots.
        let (updates, receiver) = sync_channel(1);
        let state = Self {
            shared: Arc::new(Shared {
                inner: Mutex::new(Inner {
                    active: None,
                    listener: None,
                    generation: 0,
                }),
                store: SustainedStore::new(root),
                provider,
                embedder,
                closing: AtomicBool::new(false),
                close_requested: AtomicBool::new(false),
                busy: AtomicBool::new(false),
                pause: AtomicBool::new(false),
                cancel: AtomicBool::new(false),
                interrupted: AtomicBool::new(false),
                epoch: AtomicU64::new(0),
                exports: AtomicU64::new(0),
                snapshot_sequence: AtomicU64::new(0),
                updates,
                configuration_pause: AtomicBool::new(false),
                configuration_uncertain: AtomicBool::new(false),
                boundary_targets: Mutex::new(std::collections::BTreeMap::new()),
                scheduler: Mutex::new(None),
            }),
        };
        let weak = Arc::downgrade(&state.shared);
        std::thread::spawn(move || {
            while receiver.recv().is_ok() {
                let Some(shared) = weak.upgrade() else { break };
                Self { shared }.deliver_update();
            }
        });
        state
    }
    fn lock(&self) -> Result<MutexGuard<'_, Inner>, AppError> {
        let g = self
            .shared
            .inner
            .lock()
            .map_err(|_| err("lock", "Sustained state unavailable"))?;
        if self.shared.configuration_uncertain.load(Ordering::SeqCst) { return Err(err("needs-attention", "Configuration publication is uncertain; reload the verified run before another mutation")); }
        if self.shared.closing.load(Ordering::SeqCst) {
            return Err(err("closing", "Application close has been authorized"));
        }
        Ok(g)
    }
    pub fn requires_reload(&self) -> bool { self.shared.configuration_uncertain.load(Ordering::SeqCst) }
    pub fn set_scheduler(&self, scheduler: crate::provider_scheduler::ProviderScheduler) {
        *self.shared.scheduler.lock().unwrap() = Some(scheduler);
    }
    fn scheduler_permit(&self, a: &Active) -> Result<Option<crate::provider_scheduler::Permit>, ()> {
        if a.manifest.current_config().language.backend == LanguageKind::Scripted { return Ok(None); }
        let scheduler = self.shared.scheduler.lock().map_err(|_| ())?;
        match scheduler.as_ref() {
            None => Ok(None),
            Some(s) => s.try_acquire(a.manifest.current_config().language.endpoint.as_deref().unwrap_or(""), &a.manifest.session_id).map(Some).ok_or(()),
        }
    }
    pub fn begin_export(&self) -> Result<ExportGuard, AppError> {
        let _g = self.lock()?;
        self.shared.exports.fetch_add(1, Ordering::SeqCst);
        Ok(ExportGuard(self.shared.clone()))
    }
    pub fn is_busy(&self) -> bool {
        self.shared.busy.load(Ordering::SeqCst)
    }
    pub fn request_close_pause(&self) {
        self.shared.close_requested.store(true, Ordering::SeqCst);
        self.shared.pause.store(true, Ordering::SeqCst);
    }
    pub fn interrupt(&self, _reason: &str) {
        self.shared.interrupted.store(true, Ordering::SeqCst);
        self.shared.pause.store(true, Ordering::SeqCst);
        self.shared.cancel.store(true, Ordering::SeqCst);
    }
    pub fn reopen_after_stale_close(&self) {
        self.shared.closing.store(false, Ordering::SeqCst);
    }
    pub fn cancel_close(&self) {
        self.shared.closing.store(false, Ordering::SeqCst);
        self.shared.close_requested.store(false, Ordering::SeqCst);
    }
    pub fn authorize_clean_close(&self) -> bool {
        if self.shared.closing.load(Ordering::SeqCst) {
            return true;
        }
        let Ok(g) = self.shared.inner.try_lock() else {
            return false;
        };
        let clean = self.shared.exports.load(Ordering::SeqCst) == 0
            && g.active.as_ref().is_none_or(|a| {
                !a.worker_active
                    && !a.run_requested
                    && a.engine.events().is_empty()
                    && a.engine.pending_journal().is_none()
                    && a.engine.pending_language().is_none()
                    && a.engine.prepared_application().is_none()
            });
        if clean {
            self.shared.closing.store(true, Ordering::SeqCst);
        }
        clean
    }
    pub fn finish_close(&self, allow_discard: bool) -> Result<bool, AppError> {
        let mut g = self.lock()?;
        if self.shared.exports.load(Ordering::SeqCst) > 0 {
            return Ok(false);
        }
        if let Some(a) = g.active.as_mut() {
            if a.worker_active {
                return Ok(false);
            }
            if !allow_discard
                && (a.engine.pending_language().is_some()
                    || a.engine.pending_journal().is_some()
                    || !a.engine.events().is_empty())
            {
                return Ok(false);
            }
            // Explicit checkpoint-and-quit may retain an already committed
            // Prepared boundary. Recovery clears ephemeral application permission
            // and restores paused; only a later explicit Start can apply it.
            a.run_requested = false;
            if allow_discard && !matches!(a.engine.phase(), SustainedPhase::Ready) {
                a.engine.skip_pending("User explicitly discarded the held opportunity when closing; it cannot become future memory or feedback.").map_err(ce)?;
            }
            a.manifest.phase = "stopped".into();
            a.manifest.revision = next(&a.manifest.revision);
            if let Err(error) = self.persist_mode(a, sustained_store::Admission::Close) {
                if !allow_discard || error.category != "budget" {
                    return Err(error);
                }
                self.discard_volatile_ready_prefix(a)?;
            }
        }
        self.shared.busy.store(false, Ordering::SeqCst);
        self.shared.closing.store(true, Ordering::SeqCst);
        Ok(true)
    }
    fn discard_volatile_ready_prefix(&self, a: &mut Active) -> Result<(), AppError> {
        // Explicit close only. Never choose an older Ready checkpoint when the
        // current committed prefix still contains a pending opportunity.
        let retained = self.shared.store.verify(&a.manifest.session_id)?;
        if retained.manifest.generation != a.manifest.generation
            || retained.checkpoint.sha256 != a.committed.sha256
            || !matches!(retained.checkpoint.state.phase, SustainedPhase::Ready)
        {
            return Err(err("budget", "The current committed boundary has retained intent or changed identity. A durable Skip is required before discard; no committed opportunity was erased."));
        }
        let live_step = a.engine.step();
        let old_revision = a.manifest.revision.clone();
        let engine = SustainedSession::restore(retained.checkpoint.clone()).map_err(ce)?;
        let mut catalog = self.shared.store.journal_index(&a.manifest.session_id)?;
        catalog.sort_by_key(|row| row.attempt_id);
        a.engine = engine;
        a.committed = retained.checkpoint;
        a.manifest = retained.manifest;
        a.manifest.revision = next(&old_revision);
        a.manifest.phase = "stopped".into();
        a.run_requested = false;
        a.dispatch_once = false;
        a.catalog = catalog;
        a.used_bytes = retained.report.size_bytes;
        diagnostic(a, &format!("Explicit discard released unsaved progress after durable step {} (live step was {}). The verified Ready prefix and all committed files are unchanged; this stopped decision is process-local, not a saved terminal manifest.", a.engine.step(), live_step));
        Ok(())
    }
    pub fn create(
        &self,
        request_id: String,
        config: SustainedConfig,
    ) -> Result<SustainedUpdate, AppError> {
        self.create_named(request_id, config, None)
    }
    pub fn create_named(&self, request_id: String, config: SustainedConfig, selected_id: Option<String>) -> Result<SustainedUpdate, AppError> {
        config.validate()?;
        if config.embedding_model.is_some() && config.language.backend != LanguageKind::Ollama {
            return Err(err(
                "configuration",
                "Semantic text encoding requires a local Ollama writing source.",
            ));
        }
        let engine = SustainedSession::new(config.specification()?).map_err(ce)?;
        let mut g = self.lock()?;
        if g.active.as_ref().is_some_and(|a| {
            a.worker_active
                || !matches!(a.manifest.phase.as_str(), "stopped" | "budgetReached")
                || !a.engine.events().is_empty()
        }) {
            return Err(err(
                "active",
                "Stop and durably retain the existing sustained session first",
            ));
        }
        g.generation += 1;
        let id = format!(
            "sustained-{}-{}",
            crate::session_store::now_ms(),
            NEXT_SESSION_ID.fetch_add(1, Ordering::SeqCst)
        );
        let id = selected_id.unwrap_or(id);
        let committed = engine.checkpoint();
        let mut manifest = Manifest {
            configuration_changes: vec![],
            format: "reservoir-sustained-bundle-v1".into(),
            session_id: id.clone(),
            generation: g.generation.to_string(),
            revision: "1".into(),
            config,
            limit_extensions: vec![],
            phase: "ready".into(),
            step: 0,
            durable_step: 0,
            elapsed_millis: 0,
            journal_count: 0,
            segment_count: 0,
            last_segment_sha256: None,
            checkpoint_sha256: String::new(),
            previous_checkpoint_sha256: None,
            diagnostics: vec![],
            attempt_timing: None,
        };
        self.shared.store.initialize(&mut manifest, &committed)?;
        let used_bytes = self.shared.store.used_bytes(&id)?;
        g.active = Some(Active {
            engine,
            manifest,
            committed,
            used_bytes,
            catalog: vec![],
            epoch: 0,
            worker_active: false,
            run_requested: false,
            dispatch_once: false,
            last_accounted: Instant::now(),
        });
        self.shared.busy.store(true, Ordering::SeqCst);
        self.shared.pause.store(false, Ordering::SeqCst);
        self.shared.interrupted.store(false, Ordering::SeqCst);
        Ok(self.update(&g, request_id))
    }
    pub fn get(
        &self,
        request_id: String,
        listener: Option<Listener>,
    ) -> Result<SustainedUpdate, AppError> {
        let mut g = self.lock()?;
        if let Some(l) = listener {
            let subscription_id = request_id.clone();
            g.listener = Some(Arc::new(move |mut u| {
                u.request_id = subscription_id.clone();
                l(u)
            }));
        }
        Ok(self.update(&g, request_id))
    }
    pub fn start(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
    ) -> Result<SustainedUpdate, AppError> {
        let mut g = self.lock()?;
        let a = active(&mut g, id, generation)?;
        if a.worker_active
            || sustained_store::storage_held(&a.manifest)
            || a.engine.blocked().is_some()
            || a.engine.pending_feedback().is_some()
            || matches!(
                a.manifest.phase.as_str(),
                "stopped"
                    | "storageBlocked"
                    | "providerFailed"
                    | "compatibilityBlocked"
                    | "budgetReached"
            )
        {
            return Err(err(
                "phase",
                "Resolve the held outcome before explicitly starting",
            ));
        }
        if a.engine.check_in_complete() || self.duration_reached(a) || self.step_budget_reached(a) {
            return Err(err("budget", "A configured sustained budget is exhausted"));
        }
        a.run_requested = true;
        a.manifest.phase = "running".into();
        a.manifest.revision = next(&a.manifest.revision);
        self.shared.pause.store(false, Ordering::SeqCst);
        self.shared.cancel.store(false, Ordering::SeqCst);
        self.shared.interrupted.store(false, Ordering::SeqCst);
        a.last_accounted = Instant::now();
        self.persist(a)?;
        if a.manifest.phase == "budgetReached" {
            return Ok(self.update(&g, request_id));
        }
        self.launch(a);
        let update = self.update(&g, request_id);
        drop(g);
        self.emit();
        Ok(update)
    }
    fn can_extend_limits(&self, a: &Active) -> bool {
        !a.engine.check_in_complete()
            && !a.worker_active
            && !a.run_requested
            && !a.dispatch_once
            && matches!(
                a.manifest.phase.as_str(),
                "ready" | "paused" | "budgetReached"
            )
            && !sustained_store::storage_held(&a.manifest)
            && a.engine.blocked().is_none()
            && a.engine.pending_journal().is_none()
            && a.engine.pending_feedback().is_none()
            && !a
                .engine
                .pending_language()
                .is_some_and(|pending| pending.request_started)
            && a.engine.events().is_empty()
            && a.engine.checkpoint().sha256 == a.committed.sha256
            && a.manifest.limit_extensions.len() < MAX_LIMIT_EXTENSIONS
    }
    pub fn extend_limits(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
        expected_revision: &str,
        limits: SustainedRunLimits,
    ) -> Result<SustainedUpdate, AppError> {
        let mut g = self.lock()?;
        let a = active(&mut g, id, generation)?;
        if a.manifest.revision != expected_revision {
            return Err(err(
                "stale",
                "Session changed before the limit extension was saved",
            ));
        }
        if !self.can_extend_limits(a) {
            return Err(err("phase", "Pause at a saved boundary before extending run limits; resolve pending errors or storage holds first"));
        }
        let previous = a.manifest.effective_limits();
        limits.validate_extension(&previous)?;
        // Prepare the entire transaction separately. Unpublished changes never
        // grant the active worker a larger budget.
        let mut engine = a.engine.clone();
        engine
            .extend_run_budgets(
                limits.maximum_steps,
                limits.maximum_turns,
                Some(SustainedRunLimitContext {
                    previous_duration_seconds: previous.maximum_duration_seconds,
                    maximum_duration_seconds: limits.maximum_duration_seconds,
                    elapsed_millis: a.manifest.elapsed_millis,
                }),
            )
            .map_err(ce)?;
        let event_id = engine.events().back().expect("extension event").id;
        let mut manifest = a.manifest.clone();
        manifest.limit_extensions.push(SustainedLimitExtension {
            event_id,
            step: engine.step(),
            elapsed_millis: manifest.elapsed_millis,
            limits,
        });
        manifest.phase = "paused".into();
        manifest.revision = next(&manifest.revision);
        let committed = match self.shared.store.persist(
            &mut manifest,
            &a.committed,
            &mut engine,
            sustained_store::Admission::Ordinary,
        ) {
            Ok(checkpoint) => checkpoint,
            Err(error) => {
                // Publication can finish before a final sync/readback reports an
                // error. Accept only the exact proposed, independently verified
                // commit; otherwise retain the original active limits.
                let recovered = self.shared.store.verify(id).ok().filter(|saved| {
                    saved.manifest.generation == manifest.generation
                        && saved.manifest.revision == manifest.revision
                        && saved.manifest.limit_extensions == manifest.limit_extensions
                        && saved.checkpoint.sha256 == engine.checkpoint().sha256
                });
                let Some(saved) = recovered else {
                    return Err(error);
                };
                manifest = saved.manifest;
                engine.acknowledge_events(event_id).map_err(ce)?;
                saved.checkpoint
            }
        };
        a.engine = engine;
        a.manifest = manifest;
        a.committed = committed;
        a.used_bytes = self.shared.store.used_bytes(id).unwrap_or(a.used_bytes);
        self.shared.busy.store(true, Ordering::SeqCst);
        a.run_requested = false;
        a.dispatch_once = false;
        self.shared.pause.store(true, Ordering::SeqCst);
        let update = self.update(&g, request_id);
        drop(g);
        self.emit();
        Ok(update)
    }
    pub fn pause(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
    ) -> Result<SustainedUpdate, AppError> {
        let mut g = self.lock()?;
        let a = active(&mut g, id, generation)?;
        a.run_requested = false;
        a.dispatch_once = false;
        self.shared.pause.store(true, Ordering::SeqCst);
        a.manifest.revision = next(&a.manifest.revision);
        if !a.worker_active {
            a.manifest.phase = if a.engine.check_in_complete() {
                "scheduleComplete"
            } else {
                "paused"
            }
            .into();
            self.persist(a)?;
        }
        Ok(self.update(&g, request_id))
    }
    pub fn stop(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
    ) -> Result<SustainedUpdate, AppError> {
        let mut g = self.lock()?;
        let a = active(&mut g, id, generation)?;
        a.run_requested = false;
        a.dispatch_once = false;
        self.shared.pause.store(true, Ordering::SeqCst);
        self.shared.cancel.store(true, Ordering::SeqCst);
        a.epoch = self.shared.epoch.fetch_add(1, Ordering::SeqCst) + 1;
        if let Some(p) = a.engine.pending_language().cloned() {
            a.engine
                .cancel_language(
                    p.attempt_id,
                    "Explicit Stop cancelled the pending sustained language request.",
                )
                .map_err(ce)?;
        }
        if a.engine.pending_feedback().is_some() {
            a.engine
                .interrupt(
                    "Explicit Stop interrupted encoding; completed writing remains retained.",
                )
                .map_err(ce)?;
        }
        a.manifest.phase = "stopped".into();
        a.manifest.revision = next(&a.manifest.revision);
        self.persist_mode(a, sustained_store::Admission::Stop)?;
        if !a.worker_active {
            self.shared.busy.store(false, Ordering::SeqCst);
        }
        Ok(self.update(&g, request_id))
    }
    pub fn retry_save(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
    ) -> Result<SustainedUpdate, AppError> {
        let mut g = self.lock()?;
        let a = active(&mut g, id, generation)?;
        if a.manifest.phase == "budgetReached" || sustained_store::storage_held(&a.manifest) {
            return Err(err("budget", "Budget headroom is reserved for terminal handling; explicitly skip retained feedback rather than retrying its save."));
        }
        if a.worker_active {
            return Err(err("busy", "Wait for the active write/request to settle"));
        }
        a.run_requested = false;
        a.dispatch_once = false;
        a.manifest.phase = if a.engine.check_in_complete() {
            "scheduleComplete"
        } else {
            "paused"
        }
        .into();
        a.manifest.revision = next(&a.manifest.revision);
        self.persist(a)?;
        if a.manifest.phase == "budgetReached" {
            return Ok(self.update(&g, request_id));
        }
        if a.engine.pending_journal().is_some() {
            self.save_journal(a)?;
        }
        if a.engine.check_in_complete() {
            self.shared.busy.store(false, Ordering::SeqCst);
        }
        Ok(self.update(&g, request_id))
    }
    pub fn retry_language(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
    ) -> Result<SustainedUpdate, AppError> {
        let mut g = self.lock()?;
        let a = active(&mut g, id, generation)?;
        if a.manifest.phase == "budgetReached"
            || sustained_store::storage_held(&a.manifest)
            || a.used_bytes.saturating_add(sustained_store::RUN_HEADROOM)
                > a.manifest.current_config().storage_budget_bytes
        {
            return Err(err("budget", "Storage headroom is reserved for terminal handling; no new provider attempt was admitted."));
        }
        if a.worker_active {
            return Err(err("busy", "Previous request has not settled"));
        }
        a.engine.retry_language().map_err(ce)?;
        a.dispatch_once = true;
        a.run_requested = false;
        a.manifest.phase = "awaitingLanguage".into();
        a.manifest.revision = next(&a.manifest.revision);
        self.shared.cancel.store(false, Ordering::SeqCst);
        self.shared.interrupted.store(false, Ordering::SeqCst);
        self.shared.pause.store(true, Ordering::SeqCst);
        self.persist(a)?;
        if a.manifest.phase == "budgetReached" {
            return Ok(self.update(&g, request_id));
        }
        // A retry starts a new active interval; exclude the preceding pause.
        if a.engine.check_in_state().is_some() {
            a.last_accounted = Instant::now();
        }
        self.launch(a);
        Ok(self.update(&g, request_id))
    }
    /// Retry only encoding of an already retained reply. No writer request,
    /// sampling seed, attempt identity or memory selection changes.
    pub fn retry_embedding(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
    ) -> Result<SustainedUpdate, AppError> {
        let mut g = self.lock()?;
        let a = active(&mut g, id, generation)?;
        if a.worker_active {
            return Err(err(
                "busy",
                "Wait for the active encoding request to settle",
            ));
        }
        if a.manifest.phase == "storageBlocked"
            || sustained_store::storage_held(&a.manifest)
            || a.used_bytes.saturating_add(sustained_store::RUN_HEADROOM)
                > a.manifest.current_config().storage_budget_bytes
        {
            return Err(err(
                "budget",
                "Save the retained writing and resolve storage headroom before retrying encoding.",
            ));
        }
        let pending = a
            .engine
            .pending_feedback()
            .ok_or_else(|| err("phase", "No retained writing awaits encoding"))?;
        if pending.request_started {
            return Err(err(
                "phase",
                "The prior encoding outcome is uncertain; restore the saved session first",
            ));
        }
        if pending.failure.is_some() {
            a.engine.retry_feedback().map_err(ce)?;
        }
        a.dispatch_once = true;
        a.run_requested = false;
        a.manifest.phase = "waitingForEmbedding".into();
        a.manifest.revision = next(&a.manifest.revision);
        self.shared.cancel.store(false, Ordering::SeqCst);
        self.shared.interrupted.store(false, Ordering::SeqCst);
        self.shared.pause.store(true, Ordering::SeqCst);
        self.persist(a)?;
        if a.manifest.phase == "budgetReached" {
            return Ok(self.update(&g, request_id));
        }
        a.last_accounted = Instant::now();
        self.launch(a);
        Ok(self.update(&g, request_id))
    }
    pub fn skip(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
        entry_id: Option<String>,
        attempt_id: Option<u64>,
    ) -> Result<SustainedUpdate, AppError> {
        let mut g = self.lock()?;
        let a = active(&mut g, id, generation)?;
        if a.worker_active {
            return Err(err(
                "busy",
                "Pause and settle the active request before skipping",
            ));
        }
        let expected_entry = a
            .engine
            .pending_journal()
            .map(|p| p.entry.id.clone())
            .or_else(|| a.engine.prepared_application().map(|p| p.entry.id.clone()));
        let expected_attempt = a
            .engine
            .pending_language()
            .map(|p| p.attempt_id)
            .or_else(|| a.engine.blocked().map(|p| p.pending.attempt_id))
            .or_else(|| a.engine.pending_feedback().map(|p| p.pending.attempt_id))
            .or_else(|| a.engine.pending_journal().map(|p| p.entry.attempt_id))
            .or_else(|| a.engine.prepared_application().map(|p| p.entry.attempt_id));
        if expected_entry != entry_id || expected_attempt != attempt_id {
            return Err(err(
                "stale",
                "Pending opportunity changed before explicit skip",
            ));
        }
        a.engine
            .skip_pending(
                "User explicitly skipped this opportunity; previous applied feedback remains held.",
            )
            .map_err(ce)?;
        a.manifest.phase = if a.engine.check_in_complete() {
            "scheduleComplete"
        } else {
            "paused"
        }
        .into();
        a.manifest.revision = next(&a.manifest.revision);
        self.persist_mode(a, sustained_store::Admission::Skip)?;
        if a.engine.check_in_complete() {
            self.shared.busy.store(false, Ordering::SeqCst);
        }
        Ok(self.update(&g, request_id))
    }
    fn duration_reached(&self, a: &Active) -> bool {
        // A scheduled run closes only after its final check-in is resolved.
        // Resource and provider failure holds still apply throughout settlement.
        a.engine.check_in_state().is_none()
            && a.manifest.elapsed_millis
                >= a.manifest.effective_limits().maximum_duration_seconds * 1000
    }
    fn step_budget_reached(&self, a: &Active) -> bool {
        a.engine.step() >= a.manifest.effective_limits().maximum_steps
            || (a.engine.budget_reached()
                && a.engine.prepared_application().is_none()
                && a.engine.pending_language().is_none()
                && a.engine.pending_journal().is_none()
                && a.engine.pending_feedback().is_none()
                && a.engine.pending_memory().is_none())
    }
    fn persist(&self, a: &mut Active) -> Result<(), AppError> {
        self.persist_mode(a, sustained_store::Admission::Ordinary)
    }
    fn persist_mode(
        &self,
        a: &mut Active,
        admission: sustained_store::Admission,
    ) -> Result<(), AppError> {
        let events: Vec<_> = a.engine.events().iter().cloned().collect();
        match self
            .shared
            .store
            .persist(&mut a.manifest, &a.committed, &mut a.engine, admission)
        {
            Ok(cp) => {
                a.committed = cp;
                if a.manifest.phase == "budgetReached" {
                    a.run_requested = false;
                    a.dispatch_once = false;
                    self.shared.pause.store(true, Ordering::SeqCst);
                }
                apply_catalog(&mut a.catalog, &events);
                for row in a.catalog.iter_mut().filter(|j| j.object_sha256.is_empty()) {
                    if let Ok((_, hash)) = self
                        .shared
                        .store
                        .read_journal_proof(&a.manifest.session_id, &row.entry_id)
                    {
                        row.object_sha256 = hash;
                    }
                }
                a.used_bytes = self
                    .shared
                    .store
                    .used_bytes(&a.manifest.session_id)
                    .unwrap_or(a.used_bytes);
                Ok(())
            }
            Err(e) => {
                a.run_requested = false;
                a.manifest.phase = "storageBlocked".into();
                diagnostic(a, &e.message);
                Err(e)
            }
        }
    }
    fn save_journal(&self, a: &mut Active) -> Result<(), AppError> {
        let pending = a
            .engine
            .pending_journal()
            .cloned()
            .ok_or_else(|| err("phase", "No pending journal save"))?;
        a.manifest.phase = "savingJournal".into();
        let (receipt, readback) = match self.shared.store.commit_journal(
            &a.manifest.session_id,
            &pending,
            a.manifest.current_config(),
            a.manifest.attempt_timing.as_ref(),
        ) {
            Ok(v) => v,
            Err(e) => {
                a.run_requested = false;
                if e.category == "budget" {
                    sustained_store::hold_storage(&mut a.manifest);
                    diagnostic(a, &e.message);
                    a.manifest.revision = next(&a.manifest.revision);
                    self.persist(a)?;
                    return Ok(());
                }
                a.manifest.phase = "storageBlocked".into();
                diagnostic(a, &e.message);
                return Err(e);
            }
        };
        a.engine.confirm_saved(&receipt, &readback).map_err(ce)?;
        a.manifest.journal_count += 1;
        a.manifest.phase = if a.run_requested { "running" } else { "paused" }.into();
        a.manifest.revision = next(&a.manifest.revision);
        self.persist(a)?;
        Ok(())
    }
    fn launch(&self, a: &mut Active) {
        a.epoch = self.shared.epoch.fetch_add(1, Ordering::SeqCst) + 1;
        a.worker_active = true;
        let epoch = a.epoch;
        let state = self.clone();
        std::thread::spawn(move || state.worker(epoch));
    }
    fn worker(&self, epoch: u64) {
        let activity = crate::run_activity::RunActivity::begin();
        if let Err(e) = activity {
            self.worker_failure(epoch, &e.message);
            if let Ok(mut g) = self.shared.inner.lock() {
                if let Some(a) = g.active.as_mut() {
                    if a.epoch == epoch {
                        a.worker_active = false;
                    }
                }
            }
            self.emit();
            return;
        }
        let _activity = activity.ok();
        let done = Arc::new(AtomicBool::new(false));
        let watch_done = done.clone();
        let watch = self.clone();
        let watchdog = std::thread::spawn(move || {
            let mut last = SystemTime::now();
            while !watch_done.load(Ordering::SeqCst) {
                std::thread::sleep(Duration::from_millis(100));
                let now = SystemTime::now();
                if now
                    .duration_since(last)
                    .is_ok_and(|d| d > Duration::from_secs(5))
                {
                    watch.interrupt("Wall-clock interruption requires explicit resume");
                }
                last = now;
                watch.emit();
            }
        });
        loop {
            let outcome = self.worker_boundary(epoch);
            match outcome {
                Ok(Work::Provider(p, sampling, _permit)) => {
                    let transport_start = Instant::now();
                    let response = if p.configuration.backend == LanguageKind::Scripted {
                        Ok(LanguageResponse {
                            text: self.scripted_reply_for(epoch, &p),
                            provider_model: None,
                            stop_reason: Some("stop".into()),
                            token_count: None,
                            provider_prompt_evaluation: None,
                            complete: true,
                        })
                    } else {
                        (self.shared.provider)(
                            &p.configuration,
                            &p.prompt,
                            &self.shared.cancel,
                            p.output_tokens,
                            p.request_deadline_seconds,
                            sampling,
                        )
                    };
                    if let Err(e) = self.settle(
                        epoch,
                        p.attempt_id,
                        response,
                        None,
                        transport_start.elapsed().as_millis() as u64,
                    ) {
                        self.worker_failure(epoch, &e.message);
                        break;
                    }
                }
                Ok(Work::Embedding(p, model, projection_seed, _permit)) => {
                    let result = self
                        .external_feedback_for(
                            epoch,
                            &p.pending,
                            &p.response.text,
                            &model,
                            projection_seed,
                        )
                        .and_then(|value| {
                            value.ok_or_else(|| {
                                "Retained reply unexpectedly needs no encoding".into()
                            })
                        });
                    if let Err(e) =
                        self.settle_embedding(epoch, p.pending.attempt_id, p.request_id, result)
                    {
                        self.worker_failure(epoch, &e.message);
                        break;
                    }
                }
                Ok(Work::Continue(pace)) => {
                    let start = Instant::now();
                    while start.elapsed() < Duration::from_millis(pace) {
                        if self.shared.pause.load(Ordering::SeqCst)
                            || self.shared.cancel.load(Ordering::SeqCst)
                        {
                            break;
                        }
                        std::thread::sleep(Duration::from_millis(20));
                    }
                }
                Ok(Work::Done) => break,
                Err(e) => {
                    self.worker_failure(epoch, &e.message);
                    break;
                }
            }
        }
        done.store(true, Ordering::SeqCst);
        let _ = watchdog.join();
        self.finish_worker(epoch);
    }
    fn finish_worker(&self, epoch: u64) {
        if let Ok(mut g) = self.shared.inner.lock() {
            if let Some(a) = g.active.as_mut() {
                // Old worker completion may release its in-flight flag, but never mutate a replacement run.
                if a.epoch == epoch || a.manifest.phase == "stopped" {
                    if let Ok(s) = self.shared.scheduler.lock() { if let Some(s) = s.as_ref() { s.cancel(&a.manifest.session_id); } }
                    a.worker_active = false;
                    if a.manifest.phase == "stopped" {
                        self.shared.busy.store(false, Ordering::SeqCst);
                    }
                }
            }
        }
        // No periodic tick is guaranteed after worker_active changes. Publish
        // settled capabilities explicitly, including after Stop invalidates the
        // worker epoch while it is still waiting for a cancelled provider.
        self.emit();
    }
    fn worker_boundary(&self, epoch: u64) -> Result<Work, AppError> {
        let mut g = self.lock()?;
        let a = g
            .active
            .as_mut()
            .ok_or_else(|| err("missing", "No sustained session"))?;
        if a.epoch != epoch {
            return Ok(Work::Done);
        }
        if a.manifest.phase == "budgetReached" {
            a.run_requested = false;
            return Ok(Work::Done);
        }
        let elapsed = a.last_accounted.elapsed();
        a.last_accounted = Instant::now();
        // A sleep/long-gap interruption does not advance a conversation schedule.
        // Historical unscheduled elapsed-time accounting remains unchanged.
        if a.engine.check_in_state().is_none() || !self.shared.interrupted.load(Ordering::SeqCst) {
            a.manifest.elapsed_millis = a
                .manifest
                .elapsed_millis
                .saturating_add(elapsed.as_millis().min(u64::MAX as u128) as u64);
        }
        if self.shared.interrupted.load(Ordering::SeqCst) {
            if a.engine.pending_language().is_some() || a.engine.pending_feedback().is_some() {
                a.engine.interrupt("System sleep/wake or a long wall-clock interruption; explicit recovery choice is required.").map_err(ce)?;
            }
            a.run_requested = false;
            a.manifest.phase = "interrupted".into();
            a.manifest.revision = next(&a.manifest.revision);
            self.persist(a)?;
            return Ok(Work::Done);
        }
        if (self.target_due(a) || self.shared.configuration_pause.load(Ordering::SeqCst)) && a.engine.configuration_ready() {
            a.run_requested = false;
            a.manifest.phase = "paused".into();
            a.manifest.revision = next(&a.manifest.revision);
            self.persist(a)?;
            return Ok(Work::Done);
        }
        if self.shared.pause.load(Ordering::SeqCst) {
            a.run_requested = false;
        }
        if !a.run_requested
            && !a.dispatch_once
            && (a.engine.pending_memory().is_some() || a.engine.pending_language().is_some())
        {
            a.manifest.phase = "paused".into();
            a.manifest.revision = next(&a.manifest.revision);
            self.persist(a)?;
            return Ok(Work::Done);
        }
        if a.engine.check_in_state().is_some() && a.run_requested && self.step_budget_reached(a) {
            a.run_requested = false;
            a.manifest.phase = "budgetReached".into();
            a.manifest.revision = next(&a.manifest.revision);
            self.persist(a)?;
            self.shared.busy.store(false, Ordering::SeqCst);
            return Ok(Work::Done);
        }
        if a.run_requested
            && !a.dispatch_once
            && a.engine
                .admit_due_check_in(a.engine.schedule_elapsed(a.manifest.elapsed_millis))
                .map_err(ce)?
        {
            a.manifest.revision = next(&a.manifest.revision);
            self.persist(a)?;
            if a.manifest.phase == "budgetReached" {
                return Ok(Work::Done);
            }
        }
        if a.engine.check_in_complete() {
            return self.finish_check_ins(a);
        }
        if self.duration_reached(a)
            && (a.engine.pending_memory().is_some() || a.engine.pending_language().is_some())
        {
            a.run_requested = false;
            a.manifest.phase = "budgetReached".into();
            a.manifest.revision = next(&a.manifest.revision);
            self.persist(a)?;
            return Ok(Work::Done);
        }
        if let Some(p) = a.engine.pending_memory().cloned() {
            let read = match p.entry_id() {
                Some(id) => self.shared.store.read_journal(&a.manifest.session_id, id),
                None => Err(err("engine", "Pending memory read names no entry")),
            };
            match read {
                Ok(j) => {
                    if let Err(e) = a.engine.confirm_memory(&j.pending.entry) {
                        a.engine.fail_memory(&e.to_string()).map_err(ce)?;
                    }
                }
                Err(e) => a.engine.fail_memory(&e.message).map_err(ce)?,
            }
            a.manifest.revision = next(&a.manifest.revision);
            self.persist(a)?;
            if a.manifest.phase == "budgetReached" {
                return Ok(Work::Done);
            }
        }
        if a.engine.needs_peer_snapshot() {
            let snapshot = peers::capture(
                &self.shared.store,
                &a.manifest,
                a.engine.pending_language().expect("snapshot due"),
            );
            a.engine.capture_peer_snapshot(snapshot).map_err(ce)?;
            a.manifest.revision = next(&a.manifest.revision);
            self.persist(a)?;
            if a.manifest.phase == "budgetReached" {
                return Ok(Work::Done);
            }
        }
        if let Some(p) = a.engine.pending_language().cloned() {
            if p.request_started {
                return Err(err(
                    "request",
                    "An uncertain dispatched request cannot be sent again",
                ));
            }
            let permit = match self.scheduler_permit(a) { Ok(p) => p, Err(()) => return Ok(Work::Continue(20)) };
            a.manifest.phase = "awaitingLanguage".into();
            a.manifest.revision = next(&a.manifest.revision);
            self.persist(a)?;
            if a.manifest.phase == "budgetReached" {
                return Ok(Work::Done);
            }
            a.engine.start_language(p.attempt_id).map_err(ce)?;
            a.manifest.revision = next(&a.manifest.revision);
            a.dispatch_once = false;
            a.manifest.attempt_timing = Some(sustained_store::AttemptTiming {
                queue_wait_ms: permit.as_ref().map(|p|p.queued_millis),
                attempt_id: p.attempt_id,
                dispatched_at_ms: if p.configuration.backend == LanguageKind::Ollama {
                    Some(crate::session_store::now_ms().to_string())
                } else {
                    None
                },
                ..Default::default()
            });
            let temperature = p.configuration.temperature.unwrap_or(0.0);
            let sampling = crate::model_transport::Sampling {
                temperature,
                seed: (temperature > 0.0).then(|| {
                    reservoir_core::sustained::sampling_seed(
                        a.engine.specification().seed,
                        p.attempt_id,
                    )
                }),
                system: a.engine.pending_system_contract(),
                thinking: p.configuration.thinking,
            };
            return Ok(Work::Provider(Box::new(p), sampling, permit));
        }
        if let Some(p) = a.engine.pending_feedback().cloned() {
            if let Some(reason) = &p.failure {
                a.run_requested = false;
                a.dispatch_once = false;
                a.manifest.phase = "embeddingBlocked".into();
                diagnostic(a, reason);
                a.manifest.revision = next(&a.manifest.revision);
                self.persist(a)?;
                return Ok(Work::Done);
            }
            if !a.run_requested && !a.dispatch_once {
                a.manifest.phase = "paused".into();
                a.manifest.revision = next(&a.manifest.revision);
                self.persist(a)?;
                return Ok(Work::Done);
            }
            if p.request_started {
                return Err(err(
                    "request",
                    "An uncertain encoding request requires explicit recovery",
                ));
            }
            let (model, projection_seed) = match &a.engine.specification().codec {
                reservoir_core::sustained::SustainedCodec::Embedding {
                    model,
                    projection_seed,
                } => (model.clone(), *projection_seed),
                _ => {
                    return Err(err(
                        "encoding",
                        "Retained encoding requires a semantic codec",
                    ))
                }
            };
            let permit = match self.scheduler_permit(a) { Ok(p) => p, Err(()) => return Ok(Work::Continue(20)) };
            if let Some(t)=&mut a.manifest.attempt_timing { t.embedding_queue_wait_ms=permit.as_ref().map(|p|p.queued_millis); }
            a.engine.start_feedback(p.pending.attempt_id).map_err(ce)?;
            a.dispatch_once = false;
            a.manifest.phase = "waitingForEmbedding".into();
            a.manifest.revision = next(&a.manifest.revision);
            // Both the full reply and dispatch state are durable before network work.
            if let Err(error) = self.persist(a) {
                // No network request was sent. Retain a retryable interruption
                // in memory alongside the unsaved events; Retry save publishes it.
                a.engine
                    .interrupt(
                        "Encoding dispatch was not durably saved; no encoding request was sent.",
                    )
                    .map_err(ce)?;
                return Err(error);
            }
            if a.manifest.phase == "budgetReached" {
                a.engine.interrupt("Storage budget held encoding before dispatch; completed writing remains retained.").map_err(ce)?;
                a.manifest.revision = next(&a.manifest.revision);
                self.persist_mode(a, sustained_store::Admission::Stop)?;
                return Ok(Work::Done);
            }
            return Ok(Work::Embedding(
                Box::new(
                    a.engine
                        .pending_feedback()
                        .expect("started feedback")
                        .clone(),
                ),
                model,
                projection_seed,
                permit,
            ));
        }
        if a.engine.pending_journal().is_some() {
            self.save_journal(a)?;
            if a.manifest.phase == "budgetReached" {
                return Ok(Work::Done);
            }
        }
        if let Some(b) = a.engine.blocked() {
            let reason = b.reason.clone();
            a.run_requested = false;
            a.manifest.phase = "attemptBlocked".into();
            a.manifest.revision = next(&a.manifest.revision);
            diagnostic(a, &reason);
            self.persist(a)?;
            return Ok(Work::Done);
        }
        if !a.run_requested {
            a.manifest.phase = "paused".into();
            a.manifest.revision = next(&a.manifest.revision);
            self.persist(a)?;
            return Ok(Work::Done);
        }
        if self.duration_reached(a) || self.step_budget_reached(a) {
            a.run_requested = false;
            a.manifest.phase = "budgetReached".into();
            a.manifest.revision = next(&a.manifest.revision);
            self.persist(a)?;
            self.shared.busy.store(false, Ordering::SeqCst);
            return Ok(Work::Done);
        }
        if let Some(p) = a.engine.prepared_application() {
            a.engine
                .authorize_application(p.entry.attempt_id)
                .map_err(ce)?;
        }
        let f = a.engine.advance().map_err(ce)?;
        if a.engine.check_in_complete() {
            return self.finish_check_ins(a);
        }
        a.manifest.phase = "running".into();
        a.manifest.revision = next(&a.manifest.revision);
        if f.application.is_some()
            || f.step.is_multiple_of(30)
            || a.engine.pending_memory().is_some()
            || a.engine.pending_language().is_some()
        {
            self.persist(a)?;
        }
        Ok(Work::Continue(a.manifest.current_config().pace_ms))
    }
    fn settle(
        &self,
        epoch: u64,
        attempt: u64,
        response: Result<LanguageResponse, String>,
        external: Option<reservoir_core::sustained::ExternalFeedback>,
        duration_ms: u64,
    ) -> Result<(), AppError> {
        let mut g = self.lock()?;
        let Some(a) = g.active.as_mut() else {
            return Ok(());
        };
        if a.epoch != epoch
            || a.engine
                .pending_language()
                .is_none_or(|p| p.attempt_id != attempt)
        {
            return Ok(());
        }
        if let Some(t) = a.manifest.attempt_timing.as_mut() {
            t.received_at_ms = Some(crate::session_store::now_ms().to_string());
            t.transport_duration_ms = Some(duration_ms);
        }
        if self.shared.interrupted.load(Ordering::SeqCst) {
            a.engine.interrupt("Provider operation interrupted by sleep/wake or a long wall-clock gap; no automatic resend.").map_err(ce)?;
            a.run_requested = false;
            a.manifest.phase = "interrupted".into();
        } else {
            match response {
                Ok(r) => {
                    if external.is_none() && a.engine.response_needs_feedback(&r).unwrap_or(false) {
                        a.engine
                            .retain_language_for_feedback(attempt, &r)
                            .map_err(ce)?;
                        a.manifest.phase = "waitingForEmbedding".into();
                        // Finish encoding this explicitly admitted generation even if
                        // numerical pacing was paused while the writer was busy.
                        a.dispatch_once = true;
                    } else {
                        a.engine
                            .confirm_language_with_feedback(attempt, &r, external.as_ref())
                            .map_err(ce)?;
                    }
                }
                Err(message) => a
                    .engine
                    .fail_language(attempt, &message.chars().take(4096).collect::<String>())
                    .map_err(ce)?,
            }
        }
        a.manifest.revision = next(&a.manifest.revision);
        self.persist(a)?;
        Ok(())
    }
    fn settle_embedding(
        &self,
        epoch: u64,
        attempt: u64,
        request: u64,
        result: Result<reservoir_core::sustained::ExternalFeedback, String>,
    ) -> Result<(), AppError> {
        let mut g = self.lock()?;
        let Some(a) = g.active.as_mut() else {
            return Ok(());
        };
        if a.epoch != epoch
            || a.engine.pending_feedback().is_none_or(|p| {
                p.pending.attempt_id != attempt || p.request_id != request || !p.request_started
            })
        {
            return Ok(());
        }
        if self.shared.interrupted.load(Ordering::SeqCst) {
            a.engine
                .interrupt(
                    "Encoding interrupted; completed writing is retained for explicit retry.",
                )
                .map_err(ce)?;
            a.run_requested = false;
            a.manifest.phase = "interrupted".into();
        } else {
            let result = result.and_then(|feedback| {
                a.engine
                    .confirm_feedback(attempt, request, &feedback)
                    .map_err(|e| e.to_string())
            });
            if let Err(message) = result {
                let message = message.chars().take(4096).collect::<String>();
                a.engine
                    .fail_feedback(attempt, request, &message)
                    .map_err(ce)?;
                a.run_requested = false;
                a.manifest.phase = "embeddingBlocked".into();
                diagnostic(a, &message);
            }
        }
        a.manifest.revision = next(&a.manifest.revision);
        // Preserve generation timing; this operation did not generate new writing.
        self.persist(a)?;
        Ok(())
    }
    fn worker_failure(&self, epoch: u64, message: &str) {
        if let Ok(mut g) = self.shared.inner.lock() {
            if let Some(a) = g.active.as_mut() {
                if a.epoch == epoch {
                    a.run_requested = false;
                    if !matches!(
                        a.manifest.phase.as_str(),
                        "storageBlocked" | "budgetReached"
                    ) {
                        a.manifest.phase = "paused".into();
                    }
                    diagnostic(a, message);
                    a.manifest.revision = next(&a.manifest.revision);
                }
            }
        }
    }
    fn update(&self, g: &Inner, request_id: String) -> SustainedUpdate {
        // Called only while the state lock is held. This process-local sequence
        // orders transient capabilities too, without changing durable revision.
        // Exhaustion fails closed instead of wrapping to an apparently old update.
        let previous = self
            .shared
            .snapshot_sequence
            .fetch_update(Ordering::Relaxed, Ordering::Relaxed, |n| n.checked_add(1))
            .expect("Sustained snapshot sequence exhausted; restart the application");
        SustainedUpdate {
            request_id,
            snapshot_sequence: (previous + 1).to_string(),
            summary: g.active.as_ref().map(|a| self.summary(a)),
            frame: g
                .active
                .as_ref()
                .and_then(|a| a.engine.latest_frame())
                .map(frame),
            close_requested: self.shared.close_requested.load(Ordering::SeqCst),
        }
    }
    fn summary(&self, a: &Active) -> SustainedSummary {
        let language = a
            .engine
            .pending_language()
            .map(|p| (p, "prepared"))
            .or_else(|| a.engine.blocked().map(|p| (&p.pending, "blocked")));
        let pending_language = language.map(|(p, state)| PendingLanguage {
            operation_id: format!("{}:{}:{}", a.manifest.generation, a.epoch, p.attempt_id),
            turn_id: p.turn_id,
            attempt_id: p.attempt_id,
            observed_step: p.observed_step,
            endpoint: p.configuration.endpoint.clone().unwrap_or_default(),
            model: p.configuration.model.clone().unwrap_or_default(),
            state: if p.request_started && state == "prepared" {
                "requesting"
            } else {
                state
            }
            .into(),
        });
        let cp = &a.committed.state;
        SustainedSummary {
            actions: self.actions_summary(a),
            check_ins: self.check_in_summary(a),
            effective_limits: a.manifest.effective_limits(),
            can_extend_limits: self.can_extend_limits(a),
            limit_extension_count: a.manifest.limit_extensions.len(),
            session_id: a.manifest.session_id.clone(),
            generation: a.manifest.generation.clone(),
            revision: a.manifest.revision.clone(),
            config: a.manifest.current_config().clone(),
            original_config: a.manifest.config.clone(),
            configuration_revision: a.engine.configuration_revision(),
            configuration_history: a.manifest.configuration_changes.clone(),
            phase: a.manifest.phase.clone(),
            step: a.engine.step(),
            durable_step: a.committed.state.step,
            simulated_time: a.engine.step() as f64 / 3.0,
            elapsed_seconds: a.manifest.elapsed_millis as f64 / 1000.0,
            used_bytes: a.used_bytes,
            journal_count: a.catalog.len() as u64,
            turn_count: cp.attempt_cursor,
            can_start: !a.worker_active
                && !a.engine.check_in_complete()
                && !a.run_requested
                && !sustained_store::storage_held(&a.manifest)
                && a.engine.blocked().is_none()
                && a.engine.pending_feedback().is_none()
                && !matches!(
                    a.manifest.phase.as_str(),
                    "stopped" | "storageBlocked" | "budgetReached"
                )
                && !self.duration_reached(a)
                && !self.step_budget_reached(a),
            can_pause: a.worker_active || a.run_requested,
            can_stop: a.manifest.phase != "stopped",
            can_retry_save: !a.worker_active
                && !sustained_store::storage_held(&a.manifest)
                && (a.engine.pending_journal().is_some() || a.manifest.phase == "storageBlocked"),
            can_retry_provider: !a.worker_active
                && !sustained_store::storage_held(&a.manifest)
                && a.engine.blocked().is_some()
                && cp.attempt_cursor < a.manifest.effective_limits().maximum_turns,
            can_retry_embedding: !a.worker_active
                && a.manifest.phase != "storageBlocked"
                && !sustained_store::storage_held(&a.manifest)
                && a.used_bytes.saturating_add(sustained_store::RUN_HEADROOM)
                    <= a.manifest.current_config().storage_budget_bytes
                && a.engine
                    .pending_feedback()
                    .is_some_and(|p| !p.request_started),
            can_skip_feedback: !a.worker_active
                && !matches!(a.engine.phase(), SustainedPhase::Ready),
            pending_language,
            pending_embedding: a.engine.pending_feedback().map(|p| PendingEmbedding {
                attempt_id: p.pending.attempt_id,
                observed_step: p.pending.observed_step,
                response_text: p.response.text.clone(),
                reason: p.failure.clone(),
                state: if p.failure.is_some() {
                    "blocked"
                } else if p.request_started {
                    "requesting"
                } else {
                    "prepared"
                },
            }),
            pending_save: a.engine.pending_journal().map(|p| PendingSave {
                attempt_id: p.entry.attempt_id,
                entry_id: p.entry.id.clone(),
                observed_step: p.entry.observed_step,
            }),
            pending_application: a.engine.prepared_application().map(|p| PendingApplication {
                attempt_id: p.entry.attempt_id,
                entry_id: p.entry.id.clone(),
                observed_step: p.entry.observed_step,
                intended_step: p.application_step,
            }),
            diagnostics: a.manifest.diagnostics.clone(),
        }
    }
    fn emit(&self) {
        // Full means one newer snapshot is already requested. Never wait for
        // delivery from the watchdog or numerical/provider worker.
        let _ = self.shared.updates.try_send(());
    }
    fn deliver_update(&self) {
        let pair = if let Ok(g) = self.shared.inner.lock() {
            g.listener
                .as_ref()
                .map(|l| (l.clone(), self.update(&g, String::new())))
        } else {
            None
        };
        if let Some((l, u)) = pair {
            if !l(u) {
                // A disconnected WebView should not retain its channel forever.
                // Do not remove a newer subscription installed during delivery.
                if let Ok(mut g) = self.shared.inner.lock() {
                    if g.listener
                        .as_ref()
                        .is_some_and(|current| Arc::ptr_eq(current, &l))
                    {
                        g.listener = None;
                    }
                }
            }
        }
    }
    pub fn journal_directory(&self, id: &str, generation: &str) -> Result<PathBuf, AppError> {
        let mut g = self.lock()?;
        active(&mut g, id, generation)?;
        self.shared.store.journal_directory(id)
    }
    pub fn journal_page(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
        offset: usize,
        limit: usize,
    ) -> Result<JournalPage, AppError> {
        if !(1..=50).contains(&limit) {
            return Err(err("page", "Page size must be 1–50"));
        }
        let mut g = self.lock()?;
        let a = active(&mut g, id, generation)?;
        let total = a.catalog.len();
        if offset > total {
            return Err(err("page", "Offset exceeds journal count"));
        }
        Ok(JournalPage {
            request_id,
            session_id: id.into(),
            generation: generation.into(),
            revision: a.manifest.revision.clone(),
            total,
            offset,
            has_more: offset.saturating_add(limit) < total,
            entries: a
                .catalog
                .iter()
                .rev()
                .skip(offset)
                .take(limit)
                .cloned()
                .collect(),
        })
    }
    pub fn journal(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
        entry_id: &str,
    ) -> Result<JournalDetail, AppError> {
        let mut g = self.lock()?;
        let a = active(&mut g, id, generation)?;
        let index = a
            .catalog
            .iter()
            .find(|j| j.entry_id == entry_id)
            .ok_or_else(|| err("journal", "Journal is not in the committed prefix"))?;
        let (j, object_hash) = self.shared.store.read_journal_proof(id, entry_id)?;
        if object_hash != index.object_sha256 {
            return Err(err(
                "journal",
                "Journal object changed since its committed chain anchor",
            ));
        }
        let config = a.manifest.configuration_changes.iter().rev().find(|c| c.step < index.observed_step).map_or(&a.manifest.config, |c| &c.config);
        let p = j.pending;
        // This optional display projection must not hide an otherwise readable,
        // verified historical journal. Raw evidence remains available on failure.
        let measurement_reference =
            reservoir_core::sustained::measurement_reference(&p.observation).ok();
        let memory = p
            .memory
            .map(|m| actions::memory_evidence(&m, config.prompt_version));
        let latest_shown = p
            .latest_shown
            .map(|m| actions::memory_evidence(&m, config.prompt_version));
        let application=index.first_applied_step.map(|s|serde_json::json!({"journalId":entry_id,"observedStep":index.observed_step,"appliedStep":s,"attemptId":index.attempt_id}));
        let provider_prompt_evaluation = p
            .response
            .provider_prompt_evaluation
            .as_ref()
            .map(sustained_store::ProviderPromptEvaluationView::from);
        let mut detail = JournalDetail {
            request_id,
            session_id: id.into(),
            generation: generation.into(),
            revision: a.manifest.revision.clone(),
            journal: serde_json::json!({"entryId":p.entry.id,"turnId":p.entry.turn_id,"attemptId":p.entry.attempt_id,"observedStep":p.entry.observed_step,"firstAppliedStep":index.first_applied_step,"text":p.entry.text,"sha256":p.entry.sha256,"prompt":p.prompt,"promptVersion":config.prompt_version,"rawReply":p.response.text,"observation":p.observation,"measurementReference":measurement_reference,"memory":memory,"memoryChoice":p.memory_choice,"latestShown":latest_shown,"encodedFeatures":p.encoded_features,"semanticVector":p.semantic_vector,"saveReceipt":{"entryId":entry_id,"sha256":index.sha256,"relativePath":format!("journals/{entry_id}.json")},"providerModel":p.response.provider_model,"stopReason":p.response.stop_reason,"tokenCount":p.response.token_count,"providerComplete":p.response.complete,"configuredModel":j.configured_model,"temperature":j.temperature,"samplingSeed":j.sampling_seed,"thinking":j.thinking,"feedbackProvenance":p.feedback_provenance,"objectSha256":object_hash,"requestStarted":j.request_started,"timing":j.timing,"status":index.status,"application":application}),
        };
        if let Some(action) = &p.action {
            detail.journal["action"] = serde_json::to_value(action).map_err(ce)?;
            detail.journal["bodySha256"] = crate::files::digest(action.body.as_bytes()).into();
        }
        if let Some(receipt) = &index.action_receipt {
            detail.journal["actionReceipt"] = serde_json::to_value(receipt).map_err(ce)?;
        }
        if let Some(check_in) = &p.check_in {
            detail.journal["checkIn"] = serde_json::to_value(check_in).map_err(ce)?;
            detail.journal["observationSupplied"] = check_in.include_telemetry.into();
            detail.journal["systemContract"] = if check_in.include_telemetry {
                config.prompt_version
                    .system_contract()
                    .map(serde_json::Value::from)
                    .unwrap_or(serde_json::Value::Null)
            } else {
                serde_json::Value::Null
            };
        }
        if let Some(value) = provider_prompt_evaluation {
            detail.journal["providerPromptEvaluation"] = serde_json::to_value(value).map_err(ce)?;
        }
        Ok(detail)
    }
    pub fn recovery(&self, request_id: String) -> Result<sustained_store::RecoveryPage, AppError> {
        self.shared.store.recovery(request_id)
    }
    pub fn inspect(
        &self,
        request_id: String,
        id: &str,
    ) -> Result<sustained_store::RecoveryDetail, AppError> {
        let v = self.shared.store.verify(id)?;
        Ok(sustained_store::RecoveryDetail {
            request_id,
            manifest: v.manifest,
            checkpoint: checkpoint_view(&v.checkpoint)?,
            report: v.report,
            received_responses: v.received_responses,
        })
    }
    pub fn resume(
        &self,
        request_id: String,
        id: &str,
        expected_generation: &str,
        expected_revision: &str,
    ) -> Result<SustainedUpdate, AppError> {
        let mut g = self.lock()?;
        if g.active.as_ref().is_some_and(|a| {
            a.worker_active
                || a.run_requested
                || !a.engine.events().is_empty()
                || a.manifest.phase != "stopped"
        }) {
            return Err(err(
                "active",
                "Stop the current sustained session before restoring a retained one",
            ));
        }
        let v = self.shared.store.verify(id)?;
        if v.manifest.generation != expected_generation || v.manifest.revision != expected_revision
        {
            return Err(err("stale", "Recovery selection changed"));
        }
        let mut engine = SustainedSession::restore(v.checkpoint.clone()).map_err(ce)?;
        let mut manifest = v.manifest;
        g.generation = g.generation.max(manifest.generation.parse().unwrap_or(0)) + 1;
        manifest.generation = g.generation.to_string();
        manifest.revision = next(&manifest.revision);
        let schedule_complete = engine.check_in_complete();
        manifest.phase = if schedule_complete {
            "scheduleComplete"
        } else {
            "paused"
        }
        .into();
        let committed = self.shared.store.persist(
            &mut manifest,
            &v.checkpoint,
            &mut engine,
            sustained_store::Admission::Ordinary,
        )?;
        let mut catalog = self.shared.store.journal_index(id)?;
        catalog.sort_by_key(|e| e.attempt_id);
        g.active = Some(Active {
            engine,
            manifest,
            committed,
            used_bytes: v.report.size_bytes,
            catalog,
            epoch: 0,
            worker_active: false,
            run_requested: false,
            dispatch_once: false,
            last_accounted: Instant::now(),
        });
        self.shared.busy.store(!schedule_complete, Ordering::SeqCst);
        self.shared.pause.store(true, Ordering::SeqCst);
        self.shared.interrupted.store(false, Ordering::SeqCst);
        self.shared.cancel.store(false, Ordering::SeqCst);
        Ok(self.update(&g, request_id))
    }
    pub fn export(
        &self,
        id: &str,
        generation: &str,
        revision: Option<&str>,
        destination: &Path,
        forbidden: &[PathBuf],
    ) -> Result<(String, sustained_store::BundleReport), AppError> {
        let g = self.lock()?;
        if let Some(a) = &g.active {
            if a.manifest.session_id == id && a.manifest.generation != generation {
                return Err(err(
                    "stale",
                    "Selected session snapshot changed before export",
                ));
            }
        }
        let v = self.shared.store.verify(id)?;
        if v.manifest.generation != generation || revision.is_some_and(|r| r != v.manifest.revision)
        {
            return Err(err("stale", "Retained snapshot changed"));
        }
        let report = self.shared.store.export(id, destination, forbidden)?;
        Ok((v.manifest.revision, report))
    }
}
fn active<'a>(g: &'a mut Inner, id: &str, generation: &str) -> Result<&'a mut Active, AppError> {
    let a = g
        .active
        .as_mut()
        .ok_or_else(|| err("missing", "No accepted sustained session"))?;
    if a.manifest.session_id != id || a.manifest.generation != generation {
        return Err(err("stale", "Session identity or generation changed"));
    }
    Ok(a)
}
fn next(s: &str) -> String {
    s.parse::<u64>().unwrap_or(0).saturating_add(1).to_string()
}
fn diagnostic(a: &mut Active, s: &str) {
    let s: String = s.chars().take(1024).collect();
    if a.manifest.diagnostics.last() != Some(&s) {
        a.manifest.diagnostics.push(s);
        sustained_store::trim_diagnostics(&mut a.manifest);
    }
}
fn frame(f: &reservoir_core::sustained::SustainedFrame) -> SessionFrame {
    SessionFrame {
        frame: FrameView {
            index: (f.step - 1) as usize,
            step: f.step.to_string(),
            time: Some(f.simulated_time),
            state: f.state.clone(),
            input: f.input.clone(),
            noise: f.noise.clone(),
            fill_percent: Some(f.sensory.fill_percent),
            eigenvalues: Some(f.sensory.eigenvalues.clone()),
            retention_used: Some(f.retention_used),
            semantic_turn_id: f.semantic_journal_id.clone(),
            next_retention: Some(f.next_retention),
            lesson_evidence: None,
            regulation_evidence: None,
        },
        exploration_controls: None,
        control: None,
    }
}
fn apply_catalog(
    catalog: &mut Vec<JournalIndex>,
    events: &[reservoir_core::sustained::SustainedEvent],
) {
    for event in events {
        match &event.kind {
            SustainedEventKind::JournalSaved { entry, .. } => catalog.push(JournalIndex {
                entry_id: entry.id.clone(),
                turn_id: entry.turn_id,
                attempt_id: entry.attempt_id,
                observed_step: entry.observed_step,
                first_applied_step: None,
                status: "savedPendingApplication".into(),
                text_preview: entry
                    .body
                    .as_deref()
                    .unwrap_or(&entry.text)
                    .chars()
                    .take(160)
                    .collect(),
                action_receipt: None,
                sha256: entry.sha256.clone(),
                object_sha256: String::new(),
            }),
            SustainedEventKind::Advanced(f) => {
                if let Some(applied) = &f.application {
                    if let Some(j) = catalog
                        .iter_mut()
                        .find(|j| j.entry_id == applied.journal_id)
                    {
                        j.first_applied_step = Some(applied.applied_step);
                        j.status = "applied".into();
                        j.action_receipt = f.action_receipt.as_deref().cloned();
                    }
                }
            }
            SustainedEventKind::Skipped { .. } => {
                if let Some(j) = catalog.last_mut() {
                    if j.status == "savedPendingApplication" {
                        j.status = "skipped".into();
                    }
                }
            }
            _ => {}
        }
    }
}
enum Work {
    Provider(
        Box<reservoir_core::sustained::SustainedPendingLanguage>,
        crate::model_transport::Sampling,
        Option<crate::provider_scheduler::Permit>,
    ),
    Embedding(
        Box<reservoir_core::sustained::SustainedPendingFeedback>,
        String,
        u64,
        Option<crate::provider_scheduler::Permit>,
    ),
    Continue(u64),
    Done,
}
#[cfg(test)]
#[path = "sustained_tests.rs"]
mod tests;

fn checkpoint_view(cp: &SustainedCheckpoint) -> Result<serde_json::Value, AppError> {
    let mut v = serde_json::to_value(cp).map_err(ce)?;
    v["state"]["specification"]["seed"] = cp.state.specification.seed.to_string().into();
    v["state"]["rngState"] = cp.state.rng_state.to_string().into();
    project_prompt_evaluation_counts(&mut v);
    // This is an inert IPC inspection view, never original-byte serialization.
    Ok(v)
}

/// Only typed checkpoint data reaches this display projection. Original bytes,
/// event metadata and hashes are untouched; JS receives exact decimal strings.
fn project_prompt_evaluation_counts(value: &mut serde_json::Value) {
    match value {
        serde_json::Value::Object(map) => {
            if let Some(field) = map.get_mut("providerPromptEvaluation") {
                if field["status"] == "reported" {
                    if let Some(count) = field["count"].as_u64() {
                        field["count"] = count.to_string().into();
                    }
                }
            }
            for child in map.values_mut() {
                project_prompt_evaluation_counts(child);
            }
        }
        serde_json::Value::Array(values) => {
            for child in values {
                project_prompt_evaluation_counts(child);
            }
        }
        _ => {}
    }
}

pub struct ExportGuard(Arc<Shared>);
impl Drop for ExportGuard {
    fn drop(&mut self) {
        self.0.exports.fetch_sub(1, Ordering::SeqCst);
    }
}
