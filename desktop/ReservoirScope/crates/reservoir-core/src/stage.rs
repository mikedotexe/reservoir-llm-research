//! Historical `essentials-v1` record contract. Exact prompts are reconstructed
//! from retained observations; numerical replay is checked independently.
use crate::{codec, ensure, math::*, CoreError, Result};
use serde::{Deserialize, Serialize};

pub const FORMAT: &str = "essentials-v1";
pub const EXAMPLE_TEXTS: [&str; 3] = [
    "A bright movement arrives. I notice its change and wonder what will remain when it is quiet.",
    "I remember the earlier rhythm. The sound is softer now, and I can wait with this steady pattern.",
    "Several shapes move together. I feel curious and hopeful about a different possibility.",
];
pub const SCRIPTED_REPLIES: [&str; 4] = [
    "I notice a steady pattern and a quiet change. I remember the earlier signal and will watch what persists.",
    "The broad field carries several shapes together. I wonder whether another rhythm will change the balance.",
    "I feel curious about this new pattern. Let me hold the bright signal briefly and listen for what returns.",
    "A narrow pattern remains while other movements fade. I can compare this moment with the last and try a different thought.",
];

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum LanguageKind {
    Scripted,
    Ollama,
}
impl LanguageKind {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Scripted => "scripted",
            Self::Ollama => "ollama",
        }
    }
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LanguageConfiguration {
    pub backend: LanguageKind,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub endpoint: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub context_tokens: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub response_format: Option<String>,
    /// Sampling temperature for sustained writing. Omitted historical values keep greedy
    /// decoding (zero) and their exact serialized form.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub temperature: Option<f64>,
}
impl Default for LanguageConfiguration {
    fn default() -> Self {
        Self {
            backend: LanguageKind::Scripted,
            endpoint: None,
            model: None,
            context_tokens: None,
            response_format: None,
            temperature: None,
        }
    }
}
impl LanguageConfiguration {
    pub fn validate(&self) -> Result<()> {
        ensure(
            self.temperature
                .map(|t| t.is_finite() && (0.0..=2.0).contains(&t))
                .unwrap_or(true),
            "Temperature must be between 0 and 2",
        )?;
        ensure(
            self.response_format
                .as_deref()
                .map(|s| s == "json")
                .unwrap_or(true),
            "Unsupported response format",
        )?;
        ensure(
            self.context_tokens
                .map(|n| (512..=32768).contains(&n))
                .unwrap_or(true),
            "Context must be 512–32768 tokens",
        )?;
        if self.backend == LanguageKind::Ollama {
            let text = self
                .endpoint
                .as_deref()
                .ok_or_else(|| CoreError::Invalid("Missing explicit loopback endpoint".into()))?;
            // WHATWG URL parsing canonicalizes hosts such as 127.1 and strips an
            // empty userinfo marker. The native contract checks the supplied host
            // and rejects *any* userinfo, so validate the raw authority first.
            // Explicit :80 must survive the URL parser's default-port removal.
            let endpoint_rest = text.strip_prefix("http://").unwrap_or("");
            let authority = endpoint_rest.split(['/', '?', '#']).next().unwrap_or("");
            let exact_authority = authority
                .rsplit_once(':')
                .map(|(host, port)| {
                    matches!(host, "localhost" | "127.0.0.1" | "[::1]")
                        && !authority.contains('@')
                        && !port.is_empty()
                        && port.bytes().all(|c| c.is_ascii_digit())
                        // Foundation's historical record validator only requires
                        // a representable Int port, not a usable socket port.
                        // Verification never opens it; preserve that distinction.
                        && port.parse::<i64>().is_ok()
                })
                .unwrap_or(false);
            // Foundation URL.path rejects dot segments (including /%2e), while
            // the WHATWG parser removes them. Foundation does accept a path made
            // entirely of slash tokens, including percent-encoded slashes.
            let raw_path = &endpoint_rest[authority.len()..];
            let mut remaining = raw_path.as_bytes();
            while !remaining.is_empty() {
                if remaining[0] == b'/' {
                    remaining = &remaining[1..];
                } else if remaining.len() >= 3
                    && remaining[0] == b'%'
                    && remaining[1] == b'2'
                    && matches!(remaining[2], b'f' | b'F')
                {
                    remaining = &remaining[3..];
                } else {
                    break;
                }
            }
            let root_path = remaining.is_empty();
            ensure(
                exact_authority && root_path,
                "Ollama requires an explicit HTTP loopback endpoint with a port",
            )?;
            ensure(
                self.model
                    .as_ref()
                    .map(|s| !s.trim().is_empty() && s.len() <= 256)
                    .unwrap_or(false),
                "Missing or invalid model name",
            )?;
        }
        Ok(())
    }
}

fn default_seed() -> u64 {
    20260909
}
fn default_steps() -> usize {
    300
}
fn default_dt() -> f64 {
    1.0 / 3.0
}
fn default_turn_every() -> usize {
    30
}
fn default_leak() -> f64 {
    0.65
}
fn default_retention() -> f64 {
    0.955
}
fn yes() -> bool {
    true
}
// Swift decodeIfPresent uses the documented default for both a missing field and
// explicit JSON null. Serde's `default` alone only handles the missing case.
macro_rules! nullable_default {
    ($name:ident, $kind:ty, $value:expr) => {
        fn $name<'de, D: serde::Deserializer<'de>>(
            decoder: D,
        ) -> std::result::Result<$kind, D::Error> {
            Ok(Option::<$kind>::deserialize(decoder)?.unwrap_or_else(|| $value))
        }
    };
}
nullable_default!(nullable_seed, u64, default_seed());
nullable_default!(nullable_steps, usize, default_steps());
nullable_default!(nullable_dt, f64, default_dt());
nullable_default!(nullable_turn_every, usize, default_turn_every());
nullable_default!(nullable_noise, f64, 0.0);
nullable_default!(nullable_leak, f64, default_leak());
nullable_default!(nullable_retention, f64, default_retention());
nullable_default!(nullable_regulation, bool, true);
nullable_default!(
    nullable_language,
    LanguageConfiguration,
    LanguageConfiguration::default()
);
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RunSpecification {
    pub stage: u8,
    #[serde(default = "default_seed", deserialize_with = "nullable_seed")]
    pub seed: u64,
    #[serde(default = "default_steps", deserialize_with = "nullable_steps")]
    pub steps: usize,
    #[serde(default = "default_dt", deserialize_with = "nullable_dt")]
    pub dt: f64,
    #[serde(
        default = "default_turn_every",
        deserialize_with = "nullable_turn_every"
    )]
    pub turn_every: usize,
    #[serde(default, deserialize_with = "nullable_noise")]
    pub noise_amplitude: f64,
    #[serde(default = "default_leak", deserialize_with = "nullable_leak")]
    pub leak: f64,
    #[serde(default = "default_retention", deserialize_with = "nullable_retention")]
    pub initial_retention: f64,
    #[serde(default = "yes", deserialize_with = "nullable_regulation")]
    pub regulation_enabled: bool,
    #[serde(default, deserialize_with = "nullable_language")]
    pub language: LanguageConfiguration,
}
impl Default for RunSpecification {
    fn default() -> Self {
        Self {
            stage: 1,
            seed: default_seed(),
            steps: default_steps(),
            dt: default_dt(),
            turn_every: default_turn_every(),
            noise_amplitude: 0.0,
            leak: default_leak(),
            initial_retention: default_retention(),
            regulation_enabled: true,
            language: LanguageConfiguration::default(),
        }
    }
}
impl RunSpecification {
    pub fn validate(&self) -> Result<()> {
        ensure((1..=4).contains(&self.stage), "Unknown stage")?;
        ensure(
            (1..=3000).contains(&self.steps)
                && (1..=3000).contains(&self.turn_every)
                && self.dt.is_finite()
                && (0.001..=10.0).contains(&self.dt)
                && self.noise_amplitude.is_finite()
                && (0.0..=0.2).contains(&self.noise_amplitude)
                && self.leak.is_finite()
                && (0.0..=1.0).contains(&self.leak)
                && self.initial_retention.is_finite()
                && (0.82..=0.995).contains(&self.initial_retention),
            "Invalid bounded stage recipe",
        )?;
        self.language.validate()
    }
    pub fn title(&self) -> &'static str {
        match self.stage {
            1 => "1 · Reservoir",
            2 => "2 · Spectral bridge",
            3 => "3 · LLM loop",
            4 => "4 · Regulation",
            _ => "Unknown",
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum RunStatus {
    Completed,
    Stopped,
    Failed,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum TurnStatus {
    Completed,
    Failed,
    Cancelled,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub enum ContextKind {
    PreparedExampleContext,
    LanguageRequest,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LanguageTurn {
    pub id: usize,
    pub observed_step: usize,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub application_step: Option<usize>,
    pub prompt: String,
    pub context_kind: ContextKind,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reply: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub raw_reply: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub provider_model: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stop_reason: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub token_count: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub encoded_features: Option<Vec<f64>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub semantic_vector: Option<Vec<f64>>,
    pub status: TurnStatus,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub failure: Option<String>,
    pub backend: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model: Option<String>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EssentialsFrame {
    pub step: usize,
    pub time: f64,
    pub input: Vec<f64>,
    pub state: Vec<f64>,
    pub noise: Vec<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub spectral: Option<SpectralMeasurement>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub fill_percent: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub retention_used: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub control: Option<ControlMeasurement>,
    #[serde(rename = "semanticTurnID", skip_serializing_if = "Option::is_none")]
    pub semantic_turn_id: Option<usize>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct StageRecord {
    pub recipe_version: String,
    pub specification: RunSpecification,
    pub model: ReservoirModel,
    pub projection_weights: Vec<f64>,
    pub frames: Vec<EssentialsFrame>,
    pub turns: Vec<LanguageTurn>,
    pub status: RunStatus,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub failure: Option<String>,
}

impl StageRecord {
    pub fn validate_structure(&self) -> Result<()> {
        self.specification.validate()?;
        let spec = &self.specification;
        ensure(self.recipe_version == FORMAT, "Unknown recipe version")?;
        ensure(
            self.model.node_count == 32 && self.model.input_count == 66,
            "Expected a 32 × 66 reservoir",
        )?;
        self.model.validate()?;
        vector(
            &self.projection_weights,
            if spec.stage == 1 { 0 } else { 2112 },
            "projection",
        )?;
        ensure(self.frames.len() <= spec.steps, "Too many frames")?;
        if self.status == RunStatus::Completed {
            ensure(
                self.frames.len() == spec.steps,
                "Completed run is missing steps",
            )?;
        }
        if self.status == RunStatus::Failed {
            ensure(
                self.failure
                    .as_ref()
                    .map(|s| !s.is_empty())
                    .unwrap_or(false),
                "Failed run lacks diagnostic",
            )?;
        } else {
            ensure(self.failure.is_none(), "Nonfailed run has a failure")?;
        }
        ensure(
            self.turns.len() <= (spec.steps - 1) / spec.turn_every,
            "Too many turns",
        )?;
        if spec.stage == 1 {
            ensure(
                self.turns.is_empty(),
                "Reservoir-only stage has language turns",
            )?;
        }
        for (i, frame) in self.frames.iter().enumerate() {
            ensure(
                frame.step == i + 1,
                "Steps must be contiguous and one-based",
            )?;
            near(frame.time, frame.step as f64 * spec.dt, "Simulated time")?;
            vector(&frame.input, 66, "input")?;
            vector(&frame.state, 32, "state")?;
            ensure(
                frame.state.iter().all(|x| x.abs() <= 1.0),
                "State exceeds [-1,1]",
            )?;
            vector(&frame.noise, 32, "noise")?;
            if let Some(id) = frame.semantic_turn_id {
                ensure(
                    id > 0 && id <= self.turns.len(),
                    "Invalid semantic turn reference",
                )?;
            }
            if spec.stage == 1 {
                ensure(
                    frame.spectral.is_none()
                        && frame.retention_used.is_none()
                        && frame.fill_percent.is_none()
                        && frame.control.is_none()
                        && frame.semantic_turn_id.is_none(),
                    "Stage 1 contains unavailable measurements",
                )?;
            } else {
                let spectral = frame
                    .spectral
                    .as_ref()
                    .ok_or_else(|| CoreError::Invalid("Missing field measurement".into()))?;
                spectral_structure(spectral)?;
                ensure(
                    frame
                        .retention_used
                        .map(|x| x.is_finite() && (0.82..=0.995).contains(&x))
                        .unwrap_or(false),
                    "Missing or invalid retention",
                )?;
                if spec.stage == 4 {
                    ensure(
                        frame
                            .fill_percent
                            .map(|x| x.is_finite() && (0.0..=100.0).contains(&x))
                            .unwrap_or(false),
                        "Missing or invalid fill",
                    )?;
                    ensure(
                        frame.control.is_some() == spec.regulation_enabled,
                        "Controller availability differs from recipe",
                    )?;
                    if let Some(c) = &frame.control {
                        ensure(
                            [
                                c.error,
                                c.integral,
                                c.requested_retention,
                                c.applied_retention,
                            ]
                            .iter()
                            .all(|x| x.is_finite())
                                && (0.82..=0.995).contains(&c.applied_retention),
                            "Invalid controller measurement",
                        )?;
                    }
                } else {
                    ensure(
                        frame.fill_percent.is_none() && frame.control.is_none(),
                        "Fill/controller unavailable before stage 4",
                    )?;
                }
            }
        }
        for (i, turn) in self.turns.iter().enumerate() {
            ensure(
                turn.id == i + 1
                    && turn.observed_step == turn.id * spec.turn_every
                    && turn.observed_step <= self.frames.len(),
                "Invalid turn order or observation step",
            )?;
            ensure(
                !turn.prompt.is_empty() && turn.prompt.len() <= 65536,
                "Invalid retained prompt",
            )?;
            if let Some(reply) = &turn.reply {
                ensure(
                    !reply.is_empty() && reply.len() <= 65536,
                    "Invalid retained reply",
                )?;
            }
            ensure(
                turn.raw_reply
                    .as_ref()
                    .map(|s| s.len() <= 65536)
                    .unwrap_or(true),
                "Oversized raw reply",
            )?;
            ensure(
                [&turn.provider_model, &turn.stop_reason]
                    .iter()
                    .all(|s| s.as_ref().map(|v| v.len() <= 1024).unwrap_or(true)),
                "Oversized response metadata",
            )?;
            if turn.status == TurnStatus::Completed {
                ensure(
                    turn.reply.is_some()
                        && turn.encoded_features.is_some()
                        && turn.semantic_vector.is_some(),
                    "Completed turn lacks feedback evidence",
                )?;
                vector(
                    turn.encoded_features.as_ref().unwrap(),
                    48,
                    "encoded features",
                )?;
                vector(
                    turn.semantic_vector.as_ref().unwrap(),
                    48,
                    "semantic vector",
                )?;
                ensure(
                    turn.failure.is_none() && turn.raw_reply == turn.reply,
                    "Completed turn lacks complete raw response evidence",
                )?;
                ensure(
                    turn.stop_reason.as_deref() != Some("length")
                        && turn
                            .token_count
                            .map(|n| (0..=256).contains(&n))
                            .unwrap_or(true),
                    "Incomplete response used as feedback",
                )?;
                if let Some(application) = turn.application_step {
                    ensure(
                        application == turn.observed_step + 1 && application <= self.frames.len(),
                        "Feedback did not apply on the next step",
                    )?;
                } else {
                    ensure(
                        self.status == RunStatus::Stopped
                            && turn.observed_step == self.frames.len()
                            && i == self.turns.len() - 1,
                        "Completed feedback missing application step",
                    )?;
                }
            } else {
                ensure(
                    i == self.turns.len() - 1 && turn.observed_step == self.frames.len(),
                    "Unsuccessful turn must end the run",
                )?;
                ensure(
                    turn.reply.is_none()
                        && turn.encoded_features.is_none()
                        && turn.semantic_vector.is_none()
                        && turn.application_step.is_none(),
                    "Unsuccessful turn produced feedback",
                )?;
                ensure(
                    turn.failure
                        .as_ref()
                        .map(|s| !s.is_empty())
                        .unwrap_or(false),
                    "Unsuccessful turn lacks diagnostic",
                )?;
                ensure(
                    if turn.status == TurnStatus::Failed {
                        self.status == RunStatus::Failed
                    } else {
                        self.status == RunStatus::Stopped
                    },
                    "Turn/run outcomes disagree",
                )?;
            }
            let context = if spec.stage == 2 {
                ContextKind::PreparedExampleContext
            } else {
                ContextKind::LanguageRequest
            };
            ensure(
                turn.context_kind == context,
                "Turn context differs from stage",
            )?;
            ensure(
                turn.backend
                    == if spec.stage == 2 {
                        "example"
                    } else {
                        spec.language.backend.as_str()
                    },
                "Turn backend differs from recipe",
            )?;
            ensure(
                turn.model
                    == if spec.stage >= 3 {
                        spec.language.model.clone()
                    } else {
                        None
                    },
                "Turn model differs from recipe",
            )?;
        }
        if spec.stage != 1 {
            let required = self.frames.len().saturating_sub(1) / spec.turn_every;
            ensure(
                self.turns.len() >= required
                    && self
                        .turns
                        .iter()
                        .take(required)
                        .all(|t| t.status == TurnStatus::Completed && t.application_step.is_some()),
                "Run advanced past a missing/unsuccessful turn",
            )?;
            if self.status == RunStatus::Completed {
                ensure(
                    self.turns.len() == (spec.steps - 1) / spec.turn_every,
                    "Completed run is missing turns",
                )?;
            }
        }
        Ok(())
    }

    pub fn verify(&self) -> Result<()> {
        self.validate_structure()?;
        let spec = &self.specification;
        let seeded = ReservoirModel::seeded(spec.seed);
        near_vec(
            &self.model.recurrent_weights,
            &seeded.recurrent_weights,
            "Seeded recurrent weights",
        )?;
        near_vec(
            &self.model.input_weights,
            &seeded.input_weights,
            "Seeded input weights",
        )?;
        let mut engine = ReservoirEngine::new(self.model.clone(), spec.leak, None)?;
        let mut field = SensoryField::seeded(spec.seed ^ FIELD_SEED);
        if spec.stage != 1 {
            near_vec(
                &self.projection_weights,
                &field.projection,
                "Seeded sensory projection",
            )?;
        }
        let mut fill = ReducedFill::default();
        let mut controller = RetentionController::new(spec.initial_retention)?;
        let mut retention = spec.initial_retention;
        let mut rng = SplitMix64::new(spec.seed ^ NOISE_SEED);
        for frame in &self.frames {
            let mut input = forcing(frame.step, spec.dt);
            let turn = self
                .turns
                .iter()
                .rev()
                .find(|t| t.application_step.map(|n| n <= frame.step).unwrap_or(false));
            ensure(
                frame.semantic_turn_id == turn.map(|t| t.id),
                "Semantic reference is not current applied turn",
            )?;
            if let Some(semantic) = turn.and_then(|t| t.semantic_vector.as_ref()) {
                input[18..66].copy_from_slice(semantic);
            }
            near_vec(&frame.input, &input, "Actual input")?;
            let noise: Vec<f64> = (0..32)
                .map(|_| rng.signed() * spec.noise_amplitude)
                .collect();
            near_vec(&frame.noise, &noise, "Seeded noise")?;
            near_vec(
                &frame.state,
                &engine.step(&frame.input, &frame.noise)?,
                "Recurrence",
            )?;
            if let Some(stored) = &frame.spectral {
                near(
                    frame.retention_used.unwrap(),
                    retention,
                    "Applied retention",
                )?;
                let measured = field.step(&frame.input, retention)?;
                verify_spectral(stored, &measured)?;
                if spec.stage == 4 {
                    let fill_pct = 100.0 * fill.update(&measured.eigenvalues, spec.dt);
                    near(
                        frame.fill_percent.unwrap(),
                        fill_pct,
                        "Reduced active-mode fill",
                    )?;
                    if let Some(stored) = &frame.control {
                        let expected = controller.update(fill_pct);
                        near(stored.error, expected.error, "Control error")?;
                        near(stored.integral, expected.integral, "Control integral")?;
                        near(
                            stored.requested_retention,
                            expected.requested_retention,
                            "Requested retention",
                        )?;
                        near(
                            stored.applied_retention,
                            expected.applied_retention,
                            "Next-step retention",
                        )?;
                        retention = expected.applied_retention;
                    }
                }
            }
        }
        for turn in &self.turns {
            let observation = &self.frames[turn.observed_step - 1];
            ensure(
                turn.prompt == prompt(spec, observation)?,
                "Prompt differs from retained spectral observation",
            )?;
            if let Some(reply) = &turn.reply {
                let features = codec::encode(reply)?;
                near_vec(
                    turn.encoded_features.as_ref().unwrap(),
                    &features,
                    "Text codec features",
                )?;
                near_vec(
                    turn.semantic_vector.as_ref().unwrap(),
                    &codec::feedback(&features, observation.spectral.as_ref().unwrap()),
                    "Spectral feedback encoding",
                )?;
                if spec.stage == 2 {
                    ensure(
                        reply == EXAMPLE_TEXTS[(turn.id - 1) % EXAMPLE_TEXTS.len()],
                        "Example text differs from recipe",
                    )?;
                }
            }
        }
        Ok(())
    }
}

pub fn spectral_structure(s: &SpectralMeasurement) -> Result<()> {
    ensure(s.dimension == 32, "Sensory dimension must be 32")?;
    vector(&s.eigenvalues, 32, "eigenvalues")?;
    vector(&s.eigenvectors, 1024, "eigenvectors")?;
    vector(&s.covariance, 1024, "covariance")?;
    vector(&s.field_vector, 32, "field vector")?;
    ensure(
        s.eigenvalues.iter().all(|x| *x >= 0.0)
            && s.eigenvalues.windows(2).all(|v| v[1] <= v[0] + 1e-8),
        "Invalid or unsorted eigenvalues",
    )?;
    ensure(
        [s.entropy, s.head_share, s.shoulder_share, s.tail_share]
            .iter()
            .all(|x| x.is_finite() && (-1e-8..=1.0 + 1e-8).contains(x)),
        "Invalid spectral summary",
    )
}
pub fn verify_spectral(stored: &SpectralMeasurement, expected: &SpectralMeasurement) -> Result<()> {
    near_vec(&stored.field_vector, &expected.field_vector, "Field vector")?;
    near_vec(&stored.covariance, &expected.covariance, "Covariance")?;
    near_vec(&stored.eigenvalues, &expected.eigenvalues, "Eigenvalues")?;
    near(stored.entropy, expected.entropy, "Entropy")?;
    near(stored.head_share, expected.head_share, "Head share")?;
    near(
        stored.shoulder_share,
        expected.shoulder_share,
        "Shoulder share",
    )?;
    near(stored.tail_share, expected.tail_share, "Tail share")?;
    verify_eigenvectors(stored)
}
pub fn verify_eigenvectors(s: &SpectralMeasurement) -> Result<()> {
    let n = s.dimension;
    ensure((1..=4096).contains(&n), "Invalid eigenvector dimension")?;
    vector(&s.eigenvalues, n, "eigenvalues")?;
    vector(&s.eigenvectors, n * n, "eigenvectors")?;
    vector(&s.covariance, n * n, "covariance")?;
    for mode in 0..n {
        let v = &s.eigenvectors[mode * n..(mode + 1) * n];
        near(
            v.iter().fold(0.0, |sum, x| sum + x * x),
            1.0,
            "Eigenvector norm",
        )?;
        for row in 0..n {
            let product = (0..n).fold(0.0, |sum, column| {
                sum + s.covariance[row * n + column] * v[column]
            });
            near(
                product,
                s.eigenvalues[mode] * v[row],
                "Eigenvector residual",
            )?;
        }
        for previous in 0..mode {
            let dot = (0..n).fold(0.0, |sum, c| sum + v[c] * s.eigenvectors[previous * n + c]);
            near(dot, 0.0, "Eigenvector orthogonality")?;
        }
    }
    Ok(())
}

pub fn prompt(spec: &RunSpecification, frame: &EssentialsFrame) -> Result<String> {
    use crate::prompt_number::fixed8;
    let s = frame
        .spectral
        .as_ref()
        .ok_or_else(|| CoreError::Invalid("Prompt requires spectral observation".into()))?;
    let values = s
        .eigenvalues
        .iter()
        .take(8)
        .map(|x| fixed8(*x))
        .collect::<Vec<_>>()
        .join(", ");
    let fill = frame
        .fill_percent
        .map(|x| format!("{}%", fixed8(x)))
        .unwrap_or_else(|| "unavailable in this stage".into());
    Ok(format!("Essentials experimental reconstruction · {}\nThis is a standalone, synthetic 32-node reservoir and a separate 32-dimensional sensory field.\nStep {}; simulated seconds {}.\nSensory field eigenvalues (top 8 of 32; covariance trace normalization on nonzero input): [{}]\nTop-eight normalized entropy: {}.\nShares within the leading eight modes: head {}; shoulder {}; tail {}.\nReduced active-mode fill: {}.\nWrite one short observation about this pattern and what to notice next. Your complete reply will be encoded into the 48-coordinate semantic lane on the next step. Embedding features are unavailable. Do not claim that this describes Minime or Astrid.", spec.title(), frame.step, fixed8(frame.time), values, fixed8(s.entropy), fixed8(s.head_share), fixed8(s.shoulder_share), fixed8(s.tail_share), fill))
}

/// Finite synchronous synthetic run. Provider sessions/cancellation are deliberately
/// absent here; requesting an Ollama run is incomplete, never silently substituted.
pub fn run_scripted(spec: RunSpecification) -> Result<StageRecord> {
    spec.validate()?;
    if spec.language.backend != LanguageKind::Scripted {
        return Err(CoreError::Unsupported(
            "This tranche runs scripted recipes only; no provider is contacted or substituted"
                .into(),
        ));
    }
    let model = ReservoirModel::seeded(spec.seed);
    let mut engine = ReservoirEngine::new(model.clone(), spec.leak, None)?;
    let mut field = SensoryField::seeded(spec.seed ^ FIELD_SEED);
    let mut fill = ReducedFill::default();
    let mut controller = RetentionController::new(spec.initial_retention)?;
    let mut retention = spec.initial_retention;
    let mut rng = SplitMix64::new(spec.seed ^ NOISE_SEED);
    let mut semantic = vec![0.0; 48];
    let mut semantic_turn_id: Option<usize> = None;
    let mut record = StageRecord {
        recipe_version: FORMAT.into(),
        specification: spec.clone(),
        model,
        projection_weights: if spec.stage == 1 {
            vec![]
        } else {
            field.projection.clone()
        },
        frames: Vec::with_capacity(spec.steps),
        turns: vec![],
        status: RunStatus::Completed,
        failure: None,
    };
    for step in 1..=spec.steps {
        let mut input = forcing(step, spec.dt);
        input[18..66].copy_from_slice(&semantic);
        let noise: Vec<f64> = (0..32)
            .map(|_| rng.signed() * spec.noise_amplitude)
            .collect();
        let state = engine.step(&input, &noise)?;
        let spectral = if spec.stage == 1 {
            None
        } else {
            Some(field.step(&input, retention)?)
        };
        let retention_used = spectral.as_ref().map(|_| retention);
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
        if let Some(c) = &control {
            retention = c.applied_retention;
        }
        if let Some(id) = semantic_turn_id {
            if record.turns[id - 1].application_step.is_none() {
                record.turns[id - 1].application_step = Some(step);
            }
        }
        let frame = EssentialsFrame {
            step,
            time: step as f64 * spec.dt,
            input,
            state,
            noise,
            spectral,
            fill_percent,
            retention_used,
            control,
            semantic_turn_id,
        };
        if spec.stage != 1 && step % spec.turn_every == 0 && step < spec.steps {
            let id = record.turns.len() + 1;
            let reply = if spec.stage == 2 {
                EXAMPLE_TEXTS[(id - 1) % EXAMPLE_TEXTS.len()]
            } else {
                SCRIPTED_REPLIES[(id - 1) % SCRIPTED_REPLIES.len()]
            };
            let features = codec::encode(reply)?;
            semantic = codec::feedback(&features, frame.spectral.as_ref().unwrap());
            record.turns.push(LanguageTurn {
                id,
                observed_step: step,
                application_step: None,
                prompt: prompt(&spec, &frame)?,
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
                semantic_vector: Some(semantic.clone()),
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
            });
            semantic_turn_id = Some(id);
        }
        record.frames.push(frame);
    }
    record.verify()?;
    Ok(record)
}
