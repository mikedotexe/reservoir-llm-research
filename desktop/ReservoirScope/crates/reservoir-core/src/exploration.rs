//! Bounded `essentials-exploration-v1` replay. Controls apply at the recorded
//! step, noise consumes 32 samples even at zero amplitude, and enabling the
//! separate sensory field after an off step starts from identity covariance.
//! No model, journal, filesystem, wall clock, or live input is involved.
use crate::{ensure, math::*, stage::verify_spectral, CoreError, Result};
use serde::{Deserialize, Serialize};

pub const FORMAT: &str = "essentials-exploration-v1";
pub const MAXIMUM_STEPS: usize = 1_800;
pub const DT: f64 = 1.0 / 3.0;
pub const DEFAULT_SEED: u64 = 20_260_909;

/// Constructor defaults match Swift. Decoding deliberately requires every field:
/// Swift's synthesized Codable does not supply constructor defaults on import.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ExplorationControls {
    pub leak: f64,
    pub recurrence_enabled: bool,
    pub recurrence_strength: f64,
    pub repeat_input: bool,
    pub input_strength: f64,
    pub noise_amplitude: f64,
    pub bias_enabled: bool,
    pub sensory_enabled: bool,
    pub retention: f64,
}
impl Default for ExplorationControls {
    fn default() -> Self {
        Self {
            leak: 0.65,
            recurrence_enabled: false,
            recurrence_strength: 1.0,
            repeat_input: false,
            input_strength: 1.0,
            noise_amplitude: 0.0,
            bias_enabled: false,
            sensory_enabled: false,
            retention: 0.955,
        }
    }
}
impl ExplorationControls {
    pub fn validate(&self) -> Result<()> {
        ensure(
            [self.leak, self.recurrence_strength, self.input_strength]
                .iter()
                .all(|x| x.is_finite() && (0.0..=1.0).contains(x))
                && self.noise_amplitude.is_finite()
                && (0.0..=0.2).contains(&self.noise_amplitude)
                && self.retention.is_finite()
                && (0.82..=0.995).contains(&self.retention),
            "Exploration controls require leak/strengths 0–1, noise 0–0.2, and retention 0.82–0.995",
        )
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ExplorationFrame {
    pub step: usize,
    pub time: f64,
    pub controls: ExplorationControls,
    pub pulse: bool,
    pub input: Vec<f64>,
    pub previous_state: Vec<f64>,
    /// Raw pre-tanh drives, not leaky state increments or clipped display values.
    pub input_drive: Vec<f64>,
    pub recurrent_drive: Vec<f64>,
    pub bias_drive: Vec<f64>,
    /// Tanh of the total drive, before leak and explicit noise.
    pub proposal: Vec<f64>,
    pub state: Vec<f64>,
    pub noise: Vec<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub spectral: Option<SpectralMeasurement>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ExplorationRecord {
    pub format: String,
    pub seed: u64,
    pub model: ReservoirModel,
    pub projection_weights: Vec<f64>,
    pub frames: Vec<ExplorationFrame>,
}
impl ExplorationRecord {
    /// Shape checks alone never establish numerical conformance.
    pub fn validate_structure(&self) -> Result<()> {
        if self.format != FORMAT {
            return Err(CoreError::Unsupported(format!(
                "Unknown exploration format {}",
                self.format
            )));
        }
        ensure(
            self.frames.len() <= MAXIMUM_STEPS,
            "Exploration exceeds 1,800 steps",
        )?;
        ensure(
            self.model.node_count == 32 && self.model.input_count == 66,
            "Exploration model must be 32 nodes and 66 inputs",
        )?;
        self.model.validate()?;
        vector(&self.projection_weights, 2112, "exploration projection")?;
        for (index, frame) in self.frames.iter().enumerate() {
            frame.controls.validate()?;
            ensure(
                frame.step == index + 1 && frame.time.is_finite(),
                "Invalid exploration step or clock",
            )?;
            vector(&frame.input, 66, "exploration input")?;
            for (label, values) in [
                ("previous state", &frame.previous_state),
                ("input drive", &frame.input_drive),
                ("recurrent drive", &frame.recurrent_drive),
                ("bias drive", &frame.bias_drive),
                ("proposal", &frame.proposal),
                ("state", &frame.state),
                ("noise", &frame.noise),
            ] {
                vector(values, 32, label)?;
            }
            ensure(
                frame.controls.sensory_enabled == frame.spectral.is_some(),
                "Exploration sensory measurement presence disagrees with its control",
            )?;
            if let Some(spectral) = &frame.spectral {
                ensure(
                    spectral.dimension == 32,
                    "Exploration sensory dimension must be 32",
                )?;
                vector(&spectral.field_vector, 32, "sensory vector")?;
                vector(&spectral.eigenvalues, 32, "sensory eigenvalues")?;
                vector(&spectral.covariance, 1024, "sensory covariance")?;
                vector(&spectral.eigenvectors, 1024, "sensory eigenvectors")?;
                ensure(
                    [
                        spectral.entropy,
                        spectral.head_share,
                        spectral.shoulder_share,
                        spectral.tail_share,
                    ]
                    .iter()
                    .all(|x| x.is_finite()),
                    "Nonfinite exploration spectral summary",
                )?;
            }
        }
        Ok(())
    }

    /// Replay all controls, contributions, noise, states and optional spectra.
    /// Report counts only after success: `frames.len()` steps and zero turns.
    /// Original imported bytes remain the caller's authoritative export source.
    pub fn verify(&self) -> Result<()> {
        self.reconstructed_engine().map(|_| ())
    }

    fn reconstructed_engine(&self) -> Result<ExplorationEngine> {
        self.validate_structure()?;
        let mut replay = ExplorationEngine::new(self.seed);
        ensure(
            self.model == replay.model,
            "Exploration weights do not match their seed",
        )?;
        ensure(
            self.projection_weights == replay.projection_weights,
            "Exploration projection does not match its seed",
        )?;
        for frame in &self.frames {
            ensure(
                frame.state.iter().all(|x| x.abs() <= 1.0),
                "Exploration state exceeds the clip bounds",
            )?;
            let expected = replay.advance(frame.controls.clone(), frame.pulse)?;
            near(frame.time, expected.time, "Exploration simulated time")?;
            for (label, actual, expected) in [
                ("actual input", &frame.input, &expected.input),
                (
                    "previous state",
                    &frame.previous_state,
                    &expected.previous_state,
                ),
                ("input drive", &frame.input_drive, &expected.input_drive),
                (
                    "recurrent drive",
                    &frame.recurrent_drive,
                    &expected.recurrent_drive,
                ),
                ("bias drive", &frame.bias_drive, &expected.bias_drive),
                ("proposal", &frame.proposal, &expected.proposal),
                ("realized noise", &frame.noise, &expected.noise),
                ("resulting state", &frame.state, &expected.state),
            ] {
                near_vec(actual, expected, label)?;
            }
            match (&frame.spectral, &expected.spectral) {
                (None, None) => {}
                (Some(actual), Some(expected)) => {
                    ensure(
                        actual.eigenvalues.iter().all(|x| *x >= 0.0),
                        "Negative exploration sensory eigenvalue",
                    )?;
                    // Residual/norm/orthogonality checks allow valid alternate
                    // signs and repeated-eigenvalue bases, just as Swift does.
                    verify_spectral(actual, expected)?;
                }
                _ => {
                    return Err(CoreError::Invalid(
                        "Exploration spectral presence differs".into(),
                    ))
                }
            }
        }
        // Resume from retained (verified-within-tolerance) state/covariance, not
        // their recomputed approximations. Keep valid imported bases unchanged.
        replay.frames = self.frames.clone();
        replay.state = self
            .frames
            .last()
            .map(|f| f.state.clone())
            .unwrap_or_else(|| vec![0.0; 32]);
        replay.sensory_covariance = self
            .frames
            .last()
            .and_then(|f| f.spectral.as_ref())
            .map(|s| {
                SensoryField::new(
                    32,
                    66,
                    self.projection_weights.clone(),
                    Some(s.covariance.clone()),
                )
                .map(|field| field.covariance)
            })
            .transpose()?;
        Ok(replay)
    }
}

/// Finite deterministic exploration. This is not a sustained-session runtime.
pub struct ExplorationEngine {
    seed: u64,
    model: ReservoirModel,
    projection_weights: Vec<f64>,
    frames: Vec<ExplorationFrame>,
    state: Vec<f64>,
    noise_generator: SplitMix64,
    sensory_covariance: Option<Vec<f64>>,
}
impl Default for ExplorationEngine {
    fn default() -> Self {
        Self::new(DEFAULT_SEED)
    }
}
impl ExplorationEngine {
    pub fn new(seed: u64) -> Self {
        Self {
            seed,
            model: ReservoirModel::seeded(seed),
            projection_weights: SensoryField::seeded(seed ^ FIELD_SEED).projection,
            frames: Vec::new(),
            state: vec![0.0; 32],
            noise_generator: SplitMix64::new(seed ^ NOISE_SEED),
            sensory_covariance: None,
        }
    }
    pub fn from_record(record: &ExplorationRecord) -> Result<Self> {
        record.reconstructed_engine()
    }
    pub fn frames(&self) -> &[ExplorationFrame] {
        &self.frames
    }
    pub fn record(&self) -> ExplorationRecord {
        ExplorationRecord {
            format: FORMAT.into(),
            seed: self.seed,
            model: self.model.clone(),
            projection_weights: self.projection_weights.clone(),
            frames: self.frames.clone(),
        }
    }
    pub fn advance(
        &mut self,
        controls: ExplorationControls,
        pulse: bool,
    ) -> Result<ExplorationFrame> {
        controls.validate()?;
        ensure(
            self.frames.len() < MAXIMUM_STEPS,
            "Exploration reached 1,800 steps",
        )?;
        let step = self.frames.len() + 1;
        let mut input = if pulse {
            forcing(1, DT)
        } else if controls.repeat_input {
            forcing(step, DT)
        } else {
            vec![0.0; 66]
        };
        for value in &mut input {
            *value *= controls.input_strength;
        }
        let strength = if controls.recurrence_enabled {
            controls.recurrence_strength
        } else {
            0.0
        };
        let mut controlled = self.model.clone();
        for weight in &mut controlled.recurrent_weights {
            *weight *= strength;
        }
        if !controls.bias_enabled {
            for row in 0..32 {
                controlled.input_weights[row * 67 + 66] = 0.0;
            }
        }
        let mut reservoir =
            ReservoirEngine::new(controlled, controls.leak, Some(self.state.clone()))?;
        let mut generator = self.noise_generator.clone();
        let noise: Vec<f64> = (0..32)
            .map(|_| generator.signed() * controls.noise_amplitude)
            .collect();
        let next_state = reservoir.step(&input, &noise)?;
        let mut input_drive = vec![0.0; 32];
        let mut recurrent_drive = vec![0.0; 32];
        let mut bias_drive = vec![0.0; 32];
        let mut proposal = vec![0.0; 32];
        for row in 0..32 {
            bias_drive[row] = reservoir.model.input_weights[row * 67 + 66];
            // Keep total-drive accumulation in the recurrence's exact order;
            // summing the three displayed totals changes floating-point order.
            let mut drive = bias_drive[row];
            for (column, value) in input.iter().enumerate() {
                let contribution = reservoir.model.input_weights[row * 67 + column] * value;
                input_drive[row] += contribution;
                drive += contribution;
            }
            for column in 0..32 {
                let contribution =
                    reservoir.model.recurrent_weights[row * 32 + column] * self.state[column];
                recurrent_drive[row] += contribution;
                drive += contribution;
            }
            proposal[row] = drive.tanh();
        }
        let spectral = if controls.sensory_enabled {
            let mut field = SensoryField::new(
                32,
                66,
                self.projection_weights.clone(),
                self.sensory_covariance.clone(),
            )?;
            Some(field.step(&input, controls.retention)?)
        } else {
            None
        };
        let frame = ExplorationFrame {
            step,
            time: step as f64 * DT,
            controls,
            pulse,
            input,
            previous_state: self.state.clone(),
            input_drive,
            recurrent_drive,
            bias_drive,
            proposal,
            state: next_state.clone(),
            noise,
            spectral,
        };
        // Validation/eigensolver failure cannot consume RNG or partially commit.
        self.sensory_covariance = frame.spectral.as_ref().map(|s| s.covariance.clone());
        self.state = next_state;
        self.noise_generator = generator;
        self.frames.push(frame.clone());
        Ok(frame)
    }
}
