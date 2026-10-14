//! Fixed field-only controller teaching record. This does not run a reservoir,
//! language backend, journal loop, or sustained session. Fresh incremental frames
//! and verified complete records expose only the requested prefix's evidence.
use crate::{ensure, math::*, stage::verify_spectral, Result};
use serde::{Deserialize, Serialize};

pub const FORMAT: &str = "essentials-regulation-v1";
pub const SCOPE: &str = "essentials-regulation-v1: 600 paired field-only controller steps, seed-derived common inputs/projection, reduced fill, next-step retention and fixed 301–600 target-error window; no reservoir recurrence, journal, provider authentication, live-system or experience claim";
pub const STEPS: usize = 600;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase", from = "SpecificationWire")]
pub struct RegulationExampleSpecification {
    pub fixture: String,
    pub field_seed: u64,
    pub input_seed: u64,
    pub steps: usize,
    pub dt: f64,
    pub initial_retention: f64,
    pub target_fill_percent: f64,
    pub evaluation_first_step: usize,
    pub evaluation_last_step: usize,
    pub question: String,
    pub expected_difference: String,
    pub alternative_explanation: String,
    pub stopping_point: String,
}
impl Default for RegulationExampleSpecification {
    fn default() -> Self {
        Self {
            fixture: "uniform66-seed42-field98-v1".into(),
            field_seed: 98,
            input_seed: 42,
            steps: STEPS,
            dt: 1.0 / 3.0,
            initial_retention: 0.955,
            target_fill_percent: 68.0,
            evaluation_first_step: 301,
            evaluation_last_step: 600,
            question: "Can sensory retention control reduce target error under this richer input?".into(),
            expected_difference: "Reproduce the known lower mean absolute target error in the controlled field over steps 301–600.".into(),
            alternative_explanation: "The result depends on the declared synthetic input and reduced fill measure; it does not promise target attainment under other inputs.".into(),
            stopping_point: "600 steps, one fixed paired mechanism example; evaluate steps 301–600 without selecting a different window.".into(),
        }
    }
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct SpecificationWire {
    fixture: Option<String>,
    field_seed: Option<u64>,
    input_seed: Option<u64>,
    steps: Option<usize>,
    dt: Option<f64>,
    initial_retention: Option<f64>,
    target_fill_percent: Option<f64>,
    evaluation_first_step: Option<usize>,
    evaluation_last_step: Option<usize>,
    question: Option<String>,
    expected_difference: Option<String>,
    alternative_explanation: Option<String>,
    stopping_point: Option<String>,
}
impl From<SpecificationWire> for RegulationExampleSpecification {
    fn from(w: SpecificationWire) -> Self {
        let d = Self::default();
        Self {
            fixture: w.fixture.unwrap_or(d.fixture),
            field_seed: w.field_seed.unwrap_or(d.field_seed),
            input_seed: w.input_seed.unwrap_or(d.input_seed),
            steps: w.steps.unwrap_or(d.steps),
            dt: w.dt.unwrap_or(d.dt),
            initial_retention: w.initial_retention.unwrap_or(d.initial_retention),
            target_fill_percent: w.target_fill_percent.unwrap_or(d.target_fill_percent),
            evaluation_first_step: w.evaluation_first_step.unwrap_or(d.evaluation_first_step),
            evaluation_last_step: w.evaluation_last_step.unwrap_or(d.evaluation_last_step),
            question: w.question.unwrap_or(d.question),
            expected_difference: w.expected_difference.unwrap_or(d.expected_difference),
            alternative_explanation: w
                .alternative_explanation
                .unwrap_or(d.alternative_explanation),
            stopping_point: w.stopping_point.unwrap_or(d.stopping_point),
        }
    }
}
impl RegulationExampleSpecification {
    pub fn validate(&self) -> Result<()> {
        let d = Self::default();
        ensure(self.fixture==d.fixture && self.field_seed==d.field_seed && self.input_seed==d.input_seed
            && self.steps==d.steps && self.dt==d.dt && self.initial_retention==d.initial_retention
            && self.target_fill_percent==d.target_fill_percent && self.evaluation_first_step==d.evaluation_first_step
            && self.evaluation_last_step==d.evaluation_last_step,
            "Controller example requires its qualified fixture, seeds, 600 steps, controller and 301–600 evaluation window")?;
        ensure(
            [
                &self.question,
                &self.expected_difference,
                &self.alternative_explanation,
                &self.stopping_point,
            ]
            .iter()
            .all(|s| !s.is_empty() && s.len() <= 4096),
            "Controller study notes must be nonempty and at most 4096 UTF-8 bytes each",
        )
    }
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RegulationArmFrame {
    pub spectral: SpectralMeasurement,
    pub fill_percent: f64,
    pub retention_used: f64,
    /// Recorded next-step output, present only for the regulated field.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub control: Option<ControlMeasurement>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RegulationExampleFrame {
    pub step: usize,
    pub time: f64,
    /// Common 66-dimensional synthetic forcing, with no journal-return lane.
    pub input: Vec<f64>,
    pub baseline: RegulationArmFrame,
    pub regulated: RegulationArmFrame,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RegulationExampleSummary {
    pub evaluation_first_step: usize,
    pub evaluation_last_step: usize,
    pub evaluation_count: usize,
    pub baseline_mean_absolute_error: f64,
    pub regulated_mean_absolute_error: f64,
    pub baseline_mean_fill_percent: f64,
    pub regulated_mean_fill_percent: f64,
    pub regulated_minimum_retention: f64,
    pub regulated_maximum_retention: f64,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RegulationExampleRecord {
    pub format: String,
    pub specification: RegulationExampleSpecification,
    pub projection_weights: Vec<f64>,
    pub frames: Vec<RegulationExampleFrame>,
    /// Whole-window retained summary. Do not send this to a prefix reader before
    /// step 600; use window_evidence for cursor-bound evidence instead.
    pub summary: RegulationExampleSummary,
}
impl RegulationExampleRecord {
    pub fn checked_steps(&self) -> usize {
        self.frames.len() * 2
    }
    pub fn validate_structure(&self) -> Result<()> {
        self.specification.validate()?;
        ensure(self.format == FORMAT, "Unknown controller example format")?;
        ensure(
            self.frames.len() == self.specification.steps,
            "Controller example must retain all 600 paired observations",
        )?;
        vector(&self.projection_weights, 2112, "controller projection")?;
        for (index, frame) in self.frames.iter().enumerate() {
            ensure(
                frame.step == index + 1,
                "Controller steps are not contiguous",
            )?;
            controller_near(
                frame.time,
                frame.step as f64 * self.specification.dt,
                "clock",
            )?;
            vector(&frame.input, 66, "controller common input")?;
            ensure(
                frame.baseline.control.is_none() && frame.regulated.control.is_some(),
                "Only the regulated field may contain controller outputs",
            )?;
            for arm in [&frame.baseline, &frame.regulated] {
                spectral_structure(&arm.spectral)?;
                ensure(
                    arm.fill_percent.is_finite()
                        && (0.0..=100.0).contains(&arm.fill_percent)
                        && arm.retention_used.is_finite()
                        && (0.82..=0.995).contains(&arm.retention_used),
                    "Controller fill or retention is invalid",
                )?;
            }
        }
        Ok(())
    }
    pub fn generate(specification: RegulationExampleSpecification) -> Result<Self> {
        let mut session = RegulationSession::new(specification)?;
        while !session.is_complete() {
            session.advance()?;
        }
        session.into_completed_record()
    }
    pub fn verify(&self) -> Result<()> {
        self.validate_structure()?;
        let mut fields = Fields::new(&self.specification)?;
        ensure(
            self.projection_weights == fields.baseline.projection,
            "Controller field projection differs from its seed",
        )?;
        for frame in &self.frames {
            let expected = fields.step(frame.step, &self.specification)?;
            controller_near_vec(&frame.input, &expected.input, "common input")?;
            for (actual, expected) in [
                (&frame.baseline, &expected.baseline),
                (&frame.regulated, &expected.regulated),
            ] {
                // Native RegulationExample delegates spectral checks to the action
                // verifier's 2e-7 tolerance. Its own scalar checks remain 1e-8.
                verify_spectral(&actual.spectral, &expected.spectral)?;
                controller_near(actual.fill_percent, expected.fill_percent, "fill")?;
                controller_near(
                    actual.retention_used,
                    expected.retention_used,
                    "retention used",
                )?;
                if let (Some(a), Some(e)) = (&actual.control, &expected.control) {
                    controller_near(a.error, e.error, "control error")?;
                    controller_near(a.integral, e.integral, "control integral")?;
                    controller_near(
                        a.requested_retention,
                        e.requested_retention,
                        "requested retention",
                    )?;
                    controller_near(
                        a.applied_retention,
                        e.applied_retention,
                        "next-step retention",
                    )?;
                }
            }
        }
        // Swift derives this comparison from the retained, verified frames,
        // rather than replacing the retained values with regenerated values.
        let expected = summarize(&self.frames, &self.specification);
        let actual = &self.summary;
        ensure(
            actual.evaluation_first_step == expected.evaluation_first_step
                && actual.evaluation_last_step == expected.evaluation_last_step
                && actual.evaluation_count == expected.evaluation_count,
            "Controller evaluation window differs",
        )?;
        for (label, a, e) in [
            (
                "baseline target error",
                actual.baseline_mean_absolute_error,
                expected.baseline_mean_absolute_error,
            ),
            (
                "regulated target error",
                actual.regulated_mean_absolute_error,
                expected.regulated_mean_absolute_error,
            ),
            (
                "baseline mean fill",
                actual.baseline_mean_fill_percent,
                expected.baseline_mean_fill_percent,
            ),
            (
                "regulated mean fill",
                actual.regulated_mean_fill_percent,
                expected.regulated_mean_fill_percent,
            ),
            (
                "minimum retention",
                actual.regulated_minimum_retention,
                expected.regulated_minimum_retention,
            ),
            (
                "maximum retention",
                actual.regulated_maximum_retention,
                expected.regulated_maximum_retention,
            ),
        ] {
            controller_near(a, e, label)?;
        }
        Ok(())
    }
    /// Invoke on a verified complete record. This does not reverify or cache a
    /// future result; rewinding recomputes only the newly visible prefix.
    pub fn window_evidence(&self, cursor_step: usize) -> Option<RegulationWindowEvidence> {
        RegulationWindowEvidence::evaluate(self, cursor_step)
    }
}

/// Fixed finite field-only execution. The backend owns pacing, pause, stop and
/// durable storage; this engine has no clock, provider, filesystem or reservoir.
/// A prefix deliberately has no `essentials-regulation-v1` record or summary.
pub struct RegulationSession {
    specification: RegulationExampleSpecification,
    fields: Fields,
    frames: Vec<RegulationExampleFrame>,
}
impl RegulationSession {
    pub fn new(specification: RegulationExampleSpecification) -> Result<Self> {
        specification.validate()?;
        let fields = Fields::new(&specification)?;
        Ok(Self {
            frames: Vec::with_capacity(specification.steps),
            specification,
            fields,
        })
    }
    pub fn specification(&self) -> &RegulationExampleSpecification {
        &self.specification
    }
    pub fn frames(&self) -> &[RegulationExampleFrame] {
        &self.frames
    }
    /// Static seed-derived row-major 32×66 input projection. This is distinct
    /// from each frame's activated, RMS-normalized 32-dimensional field vector.
    pub fn projection_weights(&self) -> &[f64] {
        &self.fields.baseline.projection
    }
    pub fn is_complete(&self) -> bool {
        self.frames.len() == self.specification.steps
    }
    /// Prepare both fields, the shared RNG, fill and controller on local current
    /// state before publishing either observation. Retained history is not cloned.
    pub fn advance(&mut self) -> Result<RegulationExampleFrame> {
        ensure(
            !self.is_complete(),
            "The fixed 600-step controller session is complete",
        )?;
        let mut next = self.fields.copy()?;
        let frame = next.step(self.frames.len() + 1, &self.specification)?;
        self.fields = next;
        self.frames.push(frame.clone());
        Ok(frame)
    }
    /// Only explicit complete-record snapshots clone the retained frame history.
    pub fn completed_record(&self) -> Result<RegulationExampleRecord> {
        ensure(self.is_complete(), "Controller portable export requires all 600 paired observations; a partial session has no record in this format")?;
        Ok(RegulationExampleRecord {
            format: FORMAT.into(),
            specification: self.specification.clone(),
            projection_weights: self.fields.baseline.projection.clone(),
            frames: self.frames.clone(),
            summary: summarize(&self.frames, &self.specification),
        })
    }
    fn into_completed_record(self) -> Result<RegulationExampleRecord> {
        ensure(
            self.is_complete(),
            "Controller portable export requires all 600 paired observations",
        )?;
        let summary = summarize(&self.frames, &self.specification);
        Ok(RegulationExampleRecord {
            format: FORMAT.into(),
            specification: self.specification,
            projection_weights: self.fields.baseline.projection,
            frames: self.frames,
            summary,
        })
    }
    /// A future cursor cannot reveal frames that have not actually been stepped.
    /// Rewinding recomputes only the requested retained prefix.
    pub fn window_evidence(&self, cursor_step: usize) -> Option<RegulationWindowEvidence> {
        RegulationWindowEvidence::from_frames(&self.specification, &self.frames, cursor_step)
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct RegulationWindowEvidence {
    pub count: usize,
    pub first_step: usize,
    pub last_step: usize,
    pub is_complete: bool,
    pub baseline_mean_absolute_error: f64,
    pub regulated_mean_absolute_error: f64,
}
impl RegulationWindowEvidence {
    pub fn evaluate(record: &RegulationExampleRecord, cursor_step: usize) -> Option<Self> {
        Self::from_frames(&record.specification, &record.frames, cursor_step)
    }
    fn from_frames(
        spec: &RegulationExampleSpecification,
        frames: &[RegulationExampleFrame],
        cursor_step: usize,
    ) -> Option<Self> {
        let visible: Vec<_> = frames
            .iter()
            .filter(|f| {
                f.step >= spec.evaluation_first_step
                    && f.step <= cursor_step.min(spec.evaluation_last_step)
            })
            .collect();
        let first = *visible.first()?;
        let last = *visible.last()?;
        let n = visible.len() as f64;
        Some(Self {
            count: visible.len(),
            first_step: first.step,
            last_step: last.step,
            is_complete: last.step == spec.evaluation_last_step,
            baseline_mean_absolute_error: visible.iter().fold(0.0, |sum, f| {
                sum + (f.baseline.fill_percent - spec.target_fill_percent).abs()
            }) / n,
            regulated_mean_absolute_error: visible.iter().fold(0.0, |sum, f| {
                sum + (f.regulated.fill_percent - spec.target_fill_percent).abs()
            }) / n,
        })
    }
}
struct Fields {
    baseline: SensoryField,
    regulated: SensoryField,
    baseline_fill: ReducedFill,
    regulated_fill: ReducedFill,
    controller: RetentionController,
    random: SplitMix64,
}
impl Fields {
    fn new(spec: &RegulationExampleSpecification) -> Result<Self> {
        Ok(Self {
            baseline: SensoryField::seeded(spec.field_seed),
            regulated: SensoryField::seeded(spec.field_seed),
            baseline_fill: ReducedFill::default(),
            regulated_fill: ReducedFill::default(),
            controller: RetentionController::new(spec.initial_retention)?,
            random: SplitMix64::new(spec.input_seed),
        })
    }
    fn copy(&self) -> Result<Self> {
        let field = |f: &SensoryField| {
            SensoryField::new(
                f.dimension,
                f.input_count,
                f.projection.clone(),
                Some(f.covariance.clone()),
            )
        };
        Ok(Self {
            baseline: field(&self.baseline)?,
            regulated: field(&self.regulated)?,
            baseline_fill: ReducedFill {
                fill: self.baseline_fill.fill,
            },
            regulated_fill: ReducedFill {
                fill: self.regulated_fill.fill,
            },
            controller: RetentionController {
                current_retention: self.controller.current_retention,
                integral: self.controller.integral,
            },
            random: self.random.clone(),
        })
    }
    fn step(
        &mut self,
        step: usize,
        spec: &RegulationExampleSpecification,
    ) -> Result<RegulationExampleFrame> {
        let input: Vec<f64> = (0..66).map(|_| self.random.signed()).collect();
        let retention = self.controller.current_retention;
        let a = self.baseline.step(&input, spec.initial_retention)?;
        let b = self.regulated.step(&input, retention)?;
        let af = 100.0 * self.baseline_fill.update(&a.eigenvalues, spec.dt);
        let bf = 100.0 * self.regulated_fill.update(&b.eigenvalues, spec.dt);
        let control = self.controller.update(bf);
        Ok(RegulationExampleFrame {
            step,
            time: step as f64 * spec.dt,
            input,
            baseline: RegulationArmFrame {
                spectral: a,
                fill_percent: af,
                retention_used: spec.initial_retention,
                control: None,
            },
            regulated: RegulationArmFrame {
                spectral: b,
                fill_percent: bf,
                retention_used: retention,
                control: Some(control),
            },
        })
    }
}
fn summarize(
    frames: &[RegulationExampleFrame],
    spec: &RegulationExampleSpecification,
) -> RegulationExampleSummary {
    let sample: Vec<_> = frames
        .iter()
        .filter(|f| (spec.evaluation_first_step..=spec.evaluation_last_step).contains(&f.step))
        .collect();
    let n = sample.len() as f64;
    RegulationExampleSummary {
        evaluation_first_step: spec.evaluation_first_step,
        evaluation_last_step: spec.evaluation_last_step,
        evaluation_count: sample.len(),
        baseline_mean_absolute_error: sample.iter().fold(0.0, |sum, f| {
            sum + (f.baseline.fill_percent - spec.target_fill_percent).abs()
        }) / n,
        regulated_mean_absolute_error: sample.iter().fold(0.0, |sum, f| {
            sum + (f.regulated.fill_percent - spec.target_fill_percent).abs()
        }) / n,
        baseline_mean_fill_percent: sample
            .iter()
            .fold(0.0, |sum, f| sum + f.baseline.fill_percent)
            / n,
        regulated_mean_fill_percent: sample
            .iter()
            .fold(0.0, |sum, f| sum + f.regulated.fill_percent)
            / n,
        regulated_minimum_retention: sample
            .iter()
            .map(|f| f.regulated.retention_used)
            .fold(f64::INFINITY, f64::min),
        regulated_maximum_retention: sample
            .iter()
            .map(|f| f.regulated.retention_used)
            .fold(f64::NEG_INFINITY, f64::max),
    }
}
fn spectral_structure(s: &SpectralMeasurement) -> Result<()> {
    ensure(s.dimension == 32, "Controller sensory dimension must be 32")?;
    vector(&s.eigenvalues, 32, "controller eigenvalues")?;
    vector(&s.eigenvectors, 1024, "controller eigenvectors")?;
    vector(&s.covariance, 1024, "controller covariance")?;
    vector(&s.field_vector, 32, "controller field vector")?;
    ensure(
        s.eigenvalues.iter().all(|x| *x >= 0.0)
            && s.eigenvalues.windows(2).all(|v| v[1] <= v[0] + 1e-8),
        "Controller spectrum is invalid or unordered",
    )
}
fn controller_near(a: f64, e: f64, label: &str) -> Result<()> {
    ensure(
        a.is_finite() && e.is_finite() && (a - e).abs() <= 1e-8 * e.abs().max(1.0),
        &format!("Controller {label} differs ({a}, expected {e})"),
    )
}
fn controller_near_vec(a: &[f64], e: &[f64], label: &str) -> Result<()> {
    ensure(
        a.len() == e.len(),
        &format!("Controller {label} dimensions differ"),
    )?;
    for (a, e) in a.iter().zip(e) {
        controller_near(*a, *e, label)?;
    }
    Ok(())
}

#[cfg(test)]
mod session_tests {
    use super::*;

    #[test]
    fn second_field_failure_does_not_publish_or_consume_any_current_state() {
        let mut session =
            RegulationSession::new(RegulationExampleSpecification::default()).unwrap();
        session.advance().unwrap();
        let original_retention = session.fields.controller.current_retention;
        let rng = session.fields.random.state;
        let baseline = session.fields.baseline.covariance.clone();
        let regulated = session.fields.regulated.covariance.clone();
        let fills = (
            session.fields.baseline_fill.fill,
            session.fields.regulated_fill.fill,
        );
        let integral = session.fields.controller.integral;
        let retained = serde_json::to_vec(session.frames()).unwrap();

        // Baseline computation succeeds on the candidate before regulated.step
        // rejects this injected internal error. Nothing from that candidate may
        // replace the accepted current state or consume its shared input RNG.
        session.fields.controller.current_retention = f64::NAN;
        assert!(session
            .advance()
            .unwrap_err()
            .to_string()
            .contains("retention"));
        assert_eq!(session.fields.random.state, rng);
        assert_eq!(session.fields.baseline.covariance, baseline);
        assert_eq!(session.fields.regulated.covariance, regulated);
        assert_eq!(
            (
                session.fields.baseline_fill.fill,
                session.fields.regulated_fill.fill
            ),
            fills
        );
        assert_eq!(session.fields.controller.integral, integral);
        assert!(session.fields.controller.current_retention.is_nan());
        assert_eq!(serde_json::to_vec(session.frames()).unwrap(), retained);

        session.fields.controller.current_retention = original_retention;
        let resumed = session.advance().unwrap();
        let mut reference =
            RegulationSession::new(RegulationExampleSpecification::default()).unwrap();
        reference.advance().unwrap();
        let expected = reference.advance().unwrap();
        assert_eq!(
            serde_json::to_vec(&resumed).unwrap(),
            serde_json::to_vec(&expected).unwrap()
        );
    }
}
