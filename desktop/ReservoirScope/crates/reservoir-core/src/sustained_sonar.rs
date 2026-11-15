//! Read-only recurrent response scans. No model calls, filesystem or ambient RNG.
use super::*;
use nalgebra::{linalg::SVD, DMatrix};
#[path = "sustained_sonar_compact.rs"]
mod compact;
pub use compact::*;

pub const SONAR_HORIZON: usize = 64;
pub const SONAR_HISTORY: usize = 128;
pub const SONAR_EPSILON: f64 = 0.01;
pub const SONAR_STATE_BOUND: f64 = 0.05;
pub const SONAR_HORIZONS: [usize; 7] = [1, 2, 4, 8, 16, 32, 64];
const RESOLUTION: f64 = 1e-9;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum SustainedSonarVersion {
    #[serde(rename = "response-scan-v1")]
    ResponseScanV1,
    #[serde(rename = "compact-scan-v2")]
    CompactScanV2,
}
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedSonarConfig {
    pub version: SustainedSonarVersion,
    pub allow_live_probe: bool,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum SustainedSonarDirection {
    Strongest,
    Weakest,
    Persistent,
    Question,
}
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedSonarPoint {
    pub step: u64,
    pub state: Vec<f64>,
}
#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedSonarState {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub latest_compact_scan: Option<Box<SustainedCompactSonarReport>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub latest_question: Option<Box<SustainedSonarQuestionReport>>,
    pub history: Vec<SustainedSonarPoint>,
    pub latest_scan: Option<Box<SustainedSonarReport>>,
}
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedSonarOrigin {
    pub step: u64,
    pub seed: String,
    pub rng_state: String,
    pub model_sha256: String,
    pub state: Vec<f64>,
    pub held_vector: Vec<f64>,
    pub held_journal_id: Option<String>,
    pub controls: SustainedActionControls,
    pub noise_amplitude: f64,
    pub dt: f64,
    pub history_sha256: String,
}
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedSonarMirror {
    pub first_step: u64,
    pub last_step: u64,
    pub sample_count: usize,
    pub mean: Vec<f64>,
    pub covariance_eigenvalues: Vec<f64>,
    pub principal_axes: Vec<Vec<f64>>,
    pub explained_shares: Vec<f64>,
    pub projected_history: Vec<Vec<f64>>,
    pub current_rms: f64,
    pub current_boundary_coordinates: usize,
}
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedSonarCandidate {
    pub direction: SustainedSonarDirection,
    pub unit_input: Vec<f64>,
    pub positive_response_l2: Vec<f64>,
    pub negative_response_l2: Vec<f64>,
    pub positive_return_step: Option<usize>,
    pub negative_return_step: Option<usize>,
}
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedSonarReport {
    pub version: SustainedSonarVersion,
    pub id: String,
    pub origin: SustainedSonarOrigin,
    pub mirror: SustainedSonarMirror,
    pub history: Vec<SustainedSonarPoint>,
    pub horizon: usize,
    pub horizons: Vec<usize>,
    pub epsilon: f64,
    /// Rows are recurrent coordinates; columns are the 48 authored input slots.
    pub immediate_response_matrix: Vec<Vec<f64>>,
    /// Input-coordinate-major; horizon-major norms of the signed responses.
    pub positive_response_l2: Vec<Vec<f64>>,
    pub negative_response_l2: Vec<Vec<f64>>,
    pub singular_values: Vec<Vec<f64>>,
    pub candidates: Vec<SustainedSonarCandidate>,
    pub input_frobenius_bound: f64,
    pub maximum_live_input_l2: f64,
    pub maximum_live_state_l2: f64,
    pub baseline: Vec<SustainedSonarPoint>,
}

fn norm(v: &[f64]) -> f64 {
    v.iter().map(|x| x * x).sum::<f64>().sqrt()
}
fn distance(a: &[f64], b: &[f64]) -> f64 {
    a.iter()
        .zip(b)
        .map(|(a, b)| (a - b) * (a - b))
        .sum::<f64>()
        .sqrt()
}
fn origin(s: &SustainedContinuation, history: &[SustainedSonarPoint]) -> SustainedSonarOrigin {
    SustainedSonarOrigin {
        step: s.step,
        seed: s.specification.seed.to_string(),
        rng_state: s.rng_state.to_string(),
        model_sha256: s.model_sha256.clone(),
        state: s.reservoir_state.clone(),
        held_vector: s.held_vector.clone(),
        held_journal_id: s.held_journal_id.clone(),
        controls: s
            .action_state
            .as_ref()
            .map(|a| a.controls.clone())
            .unwrap_or_else(|| SustainedActionControls::initial(&s.specification)),
        noise_amplitude: s.specification.noise_amplitude,
        dt: s.specification.dt,
        history_sha256: typed_hash(&history),
    }
}
fn model_for(origin: &SustainedSonarOrigin) -> Result<ReservoirModel> {
    let seed = origin
        .seed
        .parse()
        .map_err(|_| invalid("Invalid sonar model seed"))?;
    let base = ReservoirModel::seeded(seed);
    ensure(
        typed_hash(&base) == origin.model_sha256,
        "Sonar model identity differs",
    )?;
    Ok(actions::model_for_controls(&base, &origin.controls))
}

/// Identical copied input/forcing/noise on every branch; only the first input
/// carries the requested impulse. Does not simulate future writing or actions.
pub fn sustained_sonar_continuation(
    origin: &SustainedSonarOrigin,
    impulse: &[f64],
) -> Result<Vec<SustainedSonarPoint>> {
    continuation_for(origin, impulse, SONAR_HORIZON)
}
fn continuation_for(
    origin: &SustainedSonarOrigin,
    impulse: &[f64],
    horizon: usize,
) -> Result<Vec<SustainedSonarPoint>> {
    ensure(
        (1..=SONAR_HORIZON).contains(&horizon),
        "Invalid copied horizon",
    )?;
    validate_origin(origin)?;
    vector(impulse, 48, "sonar impulse")?;
    ensure(
        norm(impulse) <= SONAR_EPSILON * (1.0 + 1e-12),
        "Sonar impulse exceeds its fixed bound",
    )?;
    let mut engine = ReservoirEngine::new(
        model_for(origin)?,
        origin.controls.leak,
        Some(origin.state.clone()),
    )?;
    let mut rng = SplitMix64::new(
        origin
            .rng_state
            .parse()
            .map_err(|_| invalid("Invalid sonar RNG state"))?,
    );
    let mut path = Vec::with_capacity(horizon);
    for offset in 1..=horizon {
        let step = origin.step + offset as u64;
        let mut input = forcing(step as usize, origin.dt);
        input[18..].copy_from_slice(&scaled_feedback(
            &origin.held_vector,
            origin.controls.feedback_scale,
        ));
        if offset == 1 {
            for (slot, kick) in input[18..].iter_mut().zip(impulse) {
                *slot += kick;
            }
        }
        let noise: Vec<_> = (0..32)
            .map(|_| rng.signed() * origin.noise_amplitude)
            .collect();
        path.push(SustainedSonarPoint {
            step,
            state: engine.step(&input, &noise)?,
        });
    }
    Ok(path)
}

pub fn sustained_sonar_mirror(history: &[SustainedSonarPoint]) -> Result<SustainedSonarMirror> {
    validate_history(history)?;
    let n = history.len();
    let mut mean = vec![0.0; 32];
    for point in history {
        for (m, x) in mean.iter_mut().zip(&point.state) {
            *m += x / n as f64;
        }
    }
    let mut covariance = vec![0.0; 1024];
    if n > 1 {
        for point in history {
            for i in 0..32 {
                for j in 0..32 {
                    covariance[i * 32 + j] +=
                        (point.state[i] - mean[i]) * (point.state[j] - mean[j]) / (n - 1) as f64;
                }
            }
        }
    }
    let (values, vectors) = eigensystem(&covariance, 32)?;
    let total = values.iter().sum::<f64>();
    let axes: Vec<Vec<f64>> = if total > 1e-20 {
        vectors.chunks(32).take(3).map(|v| v.to_vec()).collect()
    } else {
        vec![]
    };
    let shares = if axes.is_empty() {
        vec![]
    } else {
        values.iter().take(3).map(|v| v / total).collect()
    };
    let projected = history
        .iter()
        .map(|point| {
            axes.iter()
                .map(|axis| {
                    axis.iter()
                        .zip(point.state.iter().zip(&mean))
                        .map(|(v, (x, m))| v * (x - m))
                        .sum()
                })
                .collect()
        })
        .collect();
    let latest = history.last().expect("validated history");
    Ok(SustainedSonarMirror {
        first_step: history[0].step,
        last_step: latest.step,
        sample_count: n,
        mean,
        covariance_eigenvalues: values,
        principal_axes: axes,
        explained_shares: shares,
        projected_history: projected,
        current_rms: norm(&latest.state) / 32.0_f64.sqrt(),
        current_boundary_coordinates: latest.state.iter().filter(|x| x.abs() >= 1.0).count(),
    })
}

fn validate_history(history: &[SustainedSonarPoint]) -> Result<()> {
    ensure(
        !history.is_empty() && history.len() <= SONAR_HISTORY,
        "Invalid sonar history length",
    )?;
    for p in history {
        vector(&p.state, 32, "sonar state")?;
        ensure(
            p.step <= MAX_STEPS + SONAR_HORIZON as u64 && p.state.iter().all(|x| x.abs() <= 1.0),
            "Invalid sonar state boundary",
        )?;
    }
    ensure(
        history.windows(2).all(|w| w[0].step + 1 == w[1].step),
        "Sonar history is not ordered",
    )
}
fn validate_origin(o: &SustainedSonarOrigin) -> Result<()> {
    vector(&o.state, 32, "sonar origin state")?;
    vector(&o.held_vector, 48, "sonar held input")?;
    o.controls.validate()?;
    ensure(
        o.step <= MAX_STEPS
            && o.state.iter().all(|x| x.abs() <= 1.0)
            && o.held_vector.iter().all(|x| x.abs() <= 5.0)
            && o.noise_amplitude.is_finite()
            && (0.0..=0.2).contains(&o.noise_amplitude)
            && o.dt == 1.0 / 3.0
            && valid_hash(&o.model_sha256)
            && valid_hash(&o.history_sha256),
        "Invalid sonar origin",
    )?;
    o.seed
        .parse::<u64>()
        .map_err(|_| invalid("Invalid sonar seed"))?;
    o.rng_state
        .parse::<u64>()
        .map_err(|_| invalid("Invalid sonar RNG"))?;
    Ok(())
}
fn decomposition(matrix: &[Vec<f64>]) -> Result<(Vec<f64>, Vec<Vec<f64>>)> {
    let flat: Vec<_> = matrix.iter().flatten().copied().collect();
    let svd = SVD::try_new(
        DMatrix::from_row_slice(32, 48, &flat),
        false,
        true,
        1e-14,
        10_000,
    )
    .ok_or_else(|| invalid("Bounded sonar SVD did not converge"))?;
    let right = svd
        .v_t
        .ok_or_else(|| invalid("Sonar SVD has no directions"))?;
    let rows = (0..32)
        .map(|r| {
            let mut row: Vec<_> = (0..48).map(|c| right[(r, c)]).collect();
            let largest = (0..48)
                .max_by(|a, b| row[*a].abs().total_cmp(&row[*b].abs()))
                .unwrap();
            if row[largest] < 0.0 {
                for x in &mut row {
                    *x = -*x;
                }
            }
            let length = norm(&row);
            for x in &mut row {
                *x /= length;
            }
            row
        })
        .collect();
    Ok((svd.singular_values.iter().copied().collect(), rows))
}
fn return_step(curve: &[f64]) -> Option<usize> {
    if curve[0] <= RESOLUTION {
        return None;
    }
    curve
        .windows(5)
        .enumerate()
        .skip(1)
        .find(|(_, w)| w.iter().all(|x| *x <= curve[0] * 0.1))
        .map(|(i, _)| i + 1)
}

pub fn scan_sustained_checkpoint(checkpoint: &SustainedCheckpoint) -> Result<SustainedSonarReport> {
    checkpoint.validate()?;
    scan_state(&checkpoint.state)
}
pub(super) fn scan_state(s: &SustainedContinuation) -> Result<SustainedSonarReport> {
    ensure(s.specification.difference_gain==0.0,"Response scanning v1 requires the difference channel off; no active channel is silently omitted")?;
    let history = s
        .sonar_state
        .as_ref()
        .map(|v| v.history.clone())
        .filter(|h| !h.is_empty())
        .unwrap_or_else(|| {
            vec![SustainedSonarPoint {
                step: s.step,
                state: s.reservoir_state.clone(),
            }]
        });
    let origin = origin(s, &history);
    let baseline = sustained_sonar_continuation(&origin, &[0.0; 48])?;
    let mut matrices = vec![vec![vec![0.0; 48]; 32]; SONAR_HORIZONS.len()];
    let mut positive = Vec::new();
    let mut negative = Vec::new();
    for coordinate in 0..48 {
        let mut impulse = vec![0.0; 48];
        impulse[coordinate] = SONAR_EPSILON;
        let plus = sustained_sonar_continuation(&origin, &impulse)?;
        impulse[coordinate] = -SONAR_EPSILON;
        let minus = sustained_sonar_continuation(&origin, &impulse)?;
        positive.push(
            SONAR_HORIZONS
                .iter()
                .map(|h| distance(&plus[h - 1].state, &baseline[h - 1].state))
                .collect(),
        );
        negative.push(
            SONAR_HORIZONS
                .iter()
                .map(|h| distance(&minus[h - 1].state, &baseline[h - 1].state))
                .collect(),
        );
        for (index, horizon) in SONAR_HORIZONS.iter().enumerate() {
            for (row, response) in matrices[index].iter_mut().enumerate() {
                response[coordinate] = (plus[horizon - 1].state[row]
                    - minus[horizon - 1].state[row])
                    / (2.0 * SONAR_EPSILON);
            }
        }
    }
    let mut singular_values = Vec::new();
    let mut selections = Vec::new();
    for (index, matrix) in matrices.iter().enumerate() {
        let (values, right) = decomposition(matrix)?;
        if index == 0 && values[0] > RESOLUTION {
            selections.push((SustainedSonarDirection::Strongest, right[0].clone()));
            let weakest = values.iter().rposition(|v| *v > RESOLUTION).unwrap();
            selections.push((SustainedSonarDirection::Weakest, right[weakest].clone()));
        }
        if SONAR_HORIZONS[index] == 16 && values[0] > RESOLUTION {
            selections.push((SustainedSonarDirection::Persistent, right[0].clone()));
        }
        singular_values.push(values);
    }
    let mut candidates = Vec::new();
    for (direction, unit) in selections {
        let impulse: Vec<_> = unit.iter().map(|v| v * SONAR_EPSILON).collect();
        let plus = sustained_sonar_continuation(&origin, &impulse)?;
        let minus =
            sustained_sonar_continuation(&origin, &impulse.iter().map(|v| -v).collect::<Vec<_>>())?;
        let pc: Vec<_> = plus
            .iter()
            .zip(&baseline)
            .map(|(a, b)| distance(&a.state, &b.state))
            .collect();
        let nc: Vec<_> = minus
            .iter()
            .zip(&baseline)
            .map(|(a, b)| distance(&a.state, &b.state))
            .collect();
        candidates.push(SustainedSonarCandidate {
            direction,
            unit_input: unit,
            positive_return_step: return_step(&pc),
            negative_return_step: return_step(&nc),
            positive_response_l2: pc,
            negative_response_l2: nc,
        });
    }
    let bound = input_bound(&origin)?;
    let max_input =
        SONAR_EPSILON.min(SONAR_STATE_BOUND / (origin.controls.leak * bound).max(1e-12));
    let mut report = SustainedSonarReport {
        version: SustainedSonarVersion::ResponseScanV1,
        id: String::new(),
        mirror: sustained_sonar_mirror(&history)?,
        history,
        origin,
        horizon: SONAR_HORIZON,
        horizons: SONAR_HORIZONS.to_vec(),
        epsilon: SONAR_EPSILON,
        immediate_response_matrix: matrices.remove(0),
        positive_response_l2: positive,
        negative_response_l2: negative,
        singular_values,
        candidates,
        input_frobenius_bound: bound,
        maximum_live_input_l2: max_input,
        maximum_live_state_l2: SONAR_STATE_BOUND,
        baseline,
    };
    report.id = typed_hash(&report);
    Ok(report)
}

pub(super) fn remember(s: &mut SustainedContinuation) {
    if let Some(state) = &mut s.sonar_state {
        state.history.push(SustainedSonarPoint {
            step: s.step,
            state: s.reservoir_state.clone(),
        });
        let limit = if compact::enabled(&s.specification) {
            32
        } else {
            SONAR_HISTORY
        };
        if state.history.len() > limit {
            state.history.remove(0);
        }
    }
}

pub(super) fn validate_state(s: &SustainedContinuation) -> Result<()> {
    ensure(
        s.sonar_state.is_some() == s.specification.sonar.is_some(),
        "Sonar state differs from its saved capability",
    )?;
    if let Some(state) = &s.sonar_state {
        validate_history(&state.history)?;
        compact::validate_cached_state(s, state)?;
        let last = state.history.last().expect("validated history");
        ensure(
            last.step == s.step && last.state == s.reservoir_state,
            "Sonar history does not end at its saved state",
        )?;
        if let Some(report) = &state.latest_scan {
            validate_report(report)?;
            ensure(
                report.origin.step <= s.step,
                "Sonar report is from the future",
            )?;
        }
    }
    Ok(())
}

pub fn validate_report(report: &SustainedSonarReport) -> Result<()> {
    validate_origin(&report.origin)?;
    validate_history(&report.history)?;
    ensure(
        typed_hash(&report.history) == report.origin.history_sha256
            && report
                .history
                .last()
                .is_some_and(|p| p.step == report.origin.step && p.state == report.origin.state)
            && sustained_sonar_mirror(&report.history)? == report.mirror,
        "Sonar mirror/history differs",
    )?;
    ensure(
        input_bound(&report.origin)? == report.input_frobenius_bound
            && dose(&report.origin)? == report.maximum_live_input_l2,
        "Sonar bound differs from its model/controls",
    )?;
    let mut canonical = report.clone();
    canonical.id.clear();
    ensure(
        valid_hash(&report.id) && typed_hash(&canonical) == report.id,
        "Sonar report hash differs",
    )?;
    ensure(
        report.version == SustainedSonarVersion::ResponseScanV1
            && report.horizon == SONAR_HORIZON
            && report.horizons == SONAR_HORIZONS
            && report.epsilon == SONAR_EPSILON,
        "Sonar scan settings differ from version 1",
    )?;
    ensure(
        report.immediate_response_matrix.len() == 32
            && report.positive_response_l2.len() == 48
            && report.negative_response_l2.len() == 48
            && report.singular_values.len() == 7
            && report.candidates.len() <= 3,
        "Invalid sonar array dimensions",
    )?;
    for row in &report.immediate_response_matrix {
        vector(row, 48, "sonar response row")?;
    }
    for row in report
        .positive_response_l2
        .iter()
        .chain(&report.negative_response_l2)
    {
        vector(row, 7, "sonar signed response")?;
        ensure(
            row.iter().all(|v| *v >= 0.0 && *v <= 12.0),
            "Invalid sonar separation",
        )?;
    }
    for row in &report.singular_values {
        vector(row, 32, "sonar singular values")?;
        ensure(
            row.iter().all(|v| *v >= 0.0) && row.windows(2).all(|p| p[0] >= p[1]),
            "Invalid sonar spectrum",
        )?;
    }
    for (i, candidate) in report.candidates.iter().enumerate() {
        ensure(
            report.candidates[..i]
                .iter()
                .all(|c| c.direction != candidate.direction),
            "Duplicate sonar direction",
        )?;
        vector(&candidate.unit_input, 48, "sonar input direction")?;
        ensure(
            (norm(&candidate.unit_input) - 1.0).abs() < 1e-10,
            "Sonar direction is not unit length",
        )?;
        for curve in [
            &candidate.positive_response_l2,
            &candidate.negative_response_l2,
        ] {
            vector(curve, 64, "sonar candidate response")?;
            ensure(
                curve.iter().all(|v| *v >= 0.0 && *v <= 12.0),
                "Invalid sonar candidate separation",
            )?;
        }
        ensure(
            return_step(&candidate.positive_response_l2) == candidate.positive_return_step
                && return_step(&candidate.negative_response_l2) == candidate.negative_return_step,
            "Sonar return time differs",
        )?;
    }
    validate_history(&report.baseline)?;
    ensure(
        report.baseline.len() == 64
            && report.baseline[0].step == report.origin.step + 1
            && report.baseline.last().unwrap().step == report.origin.step + 64,
        "Invalid sonar continuation span",
    )?;
    ensure(
        report.input_frobenius_bound.is_finite()
            && report.input_frobenius_bound > 0.0
            && report.maximum_live_input_l2.is_finite()
            && report.maximum_live_input_l2 > 0.0
            && report.maximum_live_input_l2 <= SONAR_EPSILON
            && report.maximum_live_state_l2 == SONAR_STATE_BOUND,
        "Invalid sonar probe bounds",
    )?;
    Ok(())
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum SustainedSonarSign {
    Positive,
    Negative,
}
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedSonarScanRef {
    pub id: String,
    pub step: u64,
}
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedSonarProbeReceipt {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub question_forecast: Option<SustainedSonarQuestionForecast>,
    pub direction: SustainedSonarDirection,
    pub sign: SustainedSonarSign,
    pub source_scan: Option<SustainedSonarScanRef>,
    pub rejection: Option<String>,
    pub applied_vector: Vec<f64>,
    pub maximum_state_l2: f64,
    /// Refreshed at application with newly held text. Future writing is not simulated.
    pub forecast_origin: Option<SustainedSonarOrigin>,
    pub forecast_response_l2: Vec<f64>,
}

pub(super) fn parse_decision(
    spec: &SustainedSpecification,
    text: &str,
    d: &mut SustainedActionDecision,
) {
    if spec.sonar.is_none() {
        return;
    }
    let (fresh, _) = actions::fresh_control_lines(text);
    if fresh
        .iter()
        .filter(|(_, line)| line.starts_with("NEXT:"))
        .count()
        != 1
    {
        return;
    }
    let Some(tail) = d.raw_tail.as_deref().and_then(|t| t.strip_prefix("NEXT:")) else {
        return;
    };
    let words: Vec<_> = tail.split_whitespace().collect();
    let parsed = match words.as_slice() {
        ["SCAN"] => Some(SustainedActionRequest::Scan),
        ["SCAN_QUESTION", question] if compact::enabled(spec) => match *question {
            "state" => Some(SustainedSonarQuestion::State),
            "input" => Some(SustainedSonarQuestion::Input),
            "recurrence" => Some(SustainedSonarQuestion::Recurrence),
            _ => None,
        }
        .map(|question| SustainedActionRequest::ScanQuestion { question }),
        ["PROBE_SCAN", direction, sign] => {
            let direction = match *direction {
                "strongest" => Some(SustainedSonarDirection::Strongest),
                "weakest" => Some(SustainedSonarDirection::Weakest),
                "persistent" => Some(SustainedSonarDirection::Persistent),
                "question" if compact::enabled(spec) => Some(SustainedSonarDirection::Question),
                _ => None,
            };
            let sign = match *sign {
                "positive" => Some(SustainedSonarSign::Positive),
                "negative" => Some(SustainedSonarSign::Negative),
                _ => None,
            };
            direction
                .zip(sign)
                .map(|(direction, sign)| SustainedActionRequest::ProbeScan { direction, sign })
        }
        _ => None,
    };
    if let Some(request) = parsed {
        d.request = Some(request);
        d.rejection = None;
    } else if compact::enabled(spec)
        && matches!(
            words.first(),
            Some(&"SCAN" | &"PROBE_SCAN" | &"SCAN_QUESTION")
        )
    {
        d.request = None;
        d.rejection = Some("Use NEXT: SCAN, NEXT: SCAN_QUESTION <state|input|recurrence>, or NEXT: PROBE_SCAN <strongest|weakest|question> <positive|negative>. Real probes require saved permission and a resolved model-selected direction.".into());
    } else if matches!(words.first(), Some(&"SCAN" | &"PROBE_SCAN")) {
        d.request = None;
        d.rejection=Some("Use NEXT: SCAN without arguments, or NEXT: PROBE_SCAN <strongest|weakest|persistent> <positive|negative>. A real probe also requires saved opt-in and a prior scan.".into());
    }
}
fn input_bound(o: &SustainedSonarOrigin) -> Result<f64> {
    Ok(model_for(o)?
        .input_weights
        .chunks(67)
        .flat_map(|r| r[18..66].iter())
        .map(|x| x * x)
        .sum::<f64>()
        .sqrt())
}
fn dose(o: &SustainedSonarOrigin) -> Result<f64> {
    Ok(SONAR_EPSILON.min(SONAR_STATE_BOUND / (o.controls.leak * input_bound(o)?).max(1e-12)))
}
const NO_AUTHORITY: &str = "Real scan probes are disabled in this saved session; no probe applied.";
const NO_SCAN: &str =
    "No model-selected scan is available. Choose NEXT: SCAN first; no probe applied.";
const NO_DIRECTION: &str="That direction was unresolved in the cached scan; choose an available direction or scan again. No probe applied.";

pub(super) fn resolve_probe(
    s: &SustainedContinuation,
    request: Option<&SustainedActionRequest>,
) -> Result<Option<SustainedSonarProbeReceipt>> {
    if compact::enabled(&s.specification) {
        return compact::resolve_compact_probe(s, request);
    }
    let Some(SustainedActionRequest::ProbeScan { direction, sign }) = request else {
        return Ok(None);
    };
    let scan = s
        .sonar_state
        .as_ref()
        .and_then(|v| v.latest_scan.as_deref());
    let candidate = scan.and_then(|v| v.candidates.iter().find(|c| c.direction == *direction));
    let rejection = if !s
        .specification
        .sonar
        .as_ref()
        .is_some_and(|c| c.allow_live_probe)
    {
        Some(NO_AUTHORITY)
    } else if scan.is_none() {
        Some(NO_SCAN)
    } else if candidate.is_none() {
        Some(NO_DIRECTION)
    } else {
        None
    };
    let mut receipt = SustainedSonarProbeReceipt {
        question_forecast: None,
        direction: *direction,
        sign: *sign,
        source_scan: scan.map(|r| SustainedSonarScanRef {
            id: r.id.clone(),
            step: r.origin.step,
        }),
        rejection: rejection.map(str::to_owned),
        applied_vector: vec![0.0; 48],
        maximum_state_l2: SONAR_STATE_BOUND,
        forecast_origin: None,
        forecast_response_l2: vec![],
    };
    if let Some(candidate) = candidate.filter(|_| rejection.is_none()) {
        let history = &s.sonar_state.as_ref().expect("enabled sonar").history;
        let origin = origin(s, history);
        let signed = dose(&origin)?
            * if *sign == SustainedSonarSign::Positive {
                1.0
            } else {
                -1.0
            };
        receipt.applied_vector = candidate.unit_input.iter().map(|v| v * signed).collect();
        let baseline = sustained_sonar_continuation(&origin, &[0.0; 48])?;
        let actual = sustained_sonar_continuation(&origin, &receipt.applied_vector)?;
        receipt.forecast_response_l2 = actual
            .iter()
            .zip(&baseline)
            .map(|(a, b)| distance(&a.state, &b.state))
            .collect();
        receipt.forecast_origin = Some(origin);
    }
    Ok(Some(receipt))
}
pub(super) fn add_probe(input: &mut [f64], receipt: Option<&SustainedSonarProbeReceipt>) {
    if let Some(r) = receipt {
        for (slot, v) in input[18..66].iter_mut().zip(&r.applied_vector) {
            *slot += v;
        }
    }
}
fn sync_receipt(s: &mut SustainedContinuation, r: &SustainedActionReceipt) {
    let a = s.action_state.as_mut().expect("authored state");
    a.latest_receipt = Some(r.clone());
    if let Some(recent) = a
        .recent_receipts
        .iter_mut()
        .find(|p| p.journal_id == r.journal_id)
    {
        *recent = r.clone();
    }
    if let Some(c) = &mut a.continuity {
        if let Some(retained) = c
            .meaningful_receipts
            .iter_mut()
            .find(|p| p.journal_id == r.journal_id)
        {
            *retained = r.clone();
        }
    }
}
pub(super) fn attach_probe(
    s: &mut SustainedContinuation,
    r: &mut Option<SustainedActionReceipt>,
    probe: Option<SustainedSonarProbeReceipt>,
) {
    if let (Some(r), Some(probe)) = (r, probe) {
        if let Some(reason) = &probe.rejection {
            r.status = SustainedActionStatus::Rejected;
            r.rejection = Some(reason.clone());
            let a = s.action_state.as_mut().unwrap();
            a.applied_count -= 1;
            a.rejected_count += 1;
        }
        r.sonar_probe = Some(Box::new(probe));
        sync_receipt(s, r);
    }
}
pub(super) fn apply_scan(
    s: &mut SustainedContinuation,
    receipt: &mut Option<Box<SustainedActionReceipt>>,
) -> Result<()> {
    if compact::enabled(&s.specification) {
        return compact::apply_compact_scan(s, receipt);
    }
    if let Some(r) = receipt
        .as_mut()
        .filter(|r| matches!(r.request, Some(SustainedActionRequest::Scan)))
    {
        let report = scan_state(s)?;
        r.sonar_scan = Some(SustainedSonarScanRef {
            id: report.id.clone(),
            step: report.origin.step,
        });
        s.sonar_state.as_mut().expect("scan capability").latest_scan = Some(Box::new(report));
        sync_receipt(s, r);
    }
    Ok(())
}
pub(super) fn validate_receipt(
    r: &SustainedActionReceipt,
    s: &SustainedContinuation,
) -> Result<()> {
    compact::validate_question_receipt(r, s)?;
    match (&r.request, &r.sonar_scan) {
        (Some(SustainedActionRequest::Scan), Some(scan)) => ensure(
            s.specification.sonar.is_some()
                && valid_hash(&scan.id)
                && scan.step == r.applied_step
                && r.state_delta_l2 == 0.0,
            "Invalid scan application receipt",
        )?,
        (Some(SustainedActionRequest::Scan), None) | (_, Some(_)) => {
            return Err(invalid("Scan receipt/request mismatch"))
        }
        _ => {}
    }
    match (&r.request, &r.sonar_probe) {
        (Some(SustainedActionRequest::ProbeScan { direction, sign }), Some(p)) => {
            ensure(
                s.specification.sonar.is_some()
                    && *direction == p.direction
                    && *sign == p.sign
                    && p.maximum_state_l2 == SONAR_STATE_BOUND,
                "Invalid scan probe authority/request",
            )?;
            vector(&p.applied_vector, 48, "applied scan probe")?;
            if let Some(source) = &p.source_scan {
                ensure(
                    valid_hash(&source.id) && source.step <= r.observed_step,
                    "Invalid source scan reference",
                )?;
            }
            let parsed = actions::decision_for(
                &s.specification,
                None,
                &format!("body\n{}", r.raw_tail.as_deref().unwrap_or("")),
            )
            .unwrap();
            ensure(
                parsed.request == r.request,
                "Scan probe raw directive differs",
            )?;
            if let Some(reason) = &p.rejection {
                ensure(
                    [NO_AUTHORITY, NO_SCAN, NO_DIRECTION, compact::NO_QUESTION]
                        .contains(&reason.as_str())
                        && r.rejection.as_ref() == Some(reason)
                        && r.status == SustainedActionStatus::Rejected
                        && norm(&p.applied_vector) == 0.0
                        && r.state_delta_l2 == 0.0
                        && p.forecast_origin.is_none()
                        && p.forecast_response_l2.is_empty(),
                    "Invalid rejected scan probe",
                )?;
            } else {
                let o = p
                    .forecast_origin
                    .as_ref()
                    .ok_or_else(|| invalid("Applied scan probe lacks forecast origin"))?;
                validate_origin(o)?;
                vector(&p.forecast_response_l2, 64, "scan probe forecast")?;
                ensure(
                    s.specification.sonar.as_ref().unwrap().allow_live_probe
                        && p.source_scan.is_some()
                        && r.status == SustainedActionStatus::Applied
                        && r.rejection.is_none()
                        && o.step == r.observed_step
                        && o.controls == r.controls_after
                        && (norm(&p.applied_vector) - dose(o)?).abs() < 1e-12
                        && p.forecast_response_l2
                            .iter()
                            .all(|v| *v >= 0.0 && *v <= 12.0)
                        && r.state_delta_l2 <= SONAR_STATE_BOUND + 1e-12
                        && (p.forecast_response_l2[0] - r.state_delta_l2).abs() < 1e-12,
                    "Invalid applied scan probe or bound",
                )?;
            }
            compact::validate_question_forecast(p)?;
        }
        (Some(SustainedActionRequest::ProbeScan { .. }), None) | (_, Some(_)) => {
            return Err(invalid("Scan probe receipt/request mismatch"))
        }
        _ => {}
    }
    Ok(())
}
pub(super) fn render_context(s: &SustainedContinuation) -> String {
    if compact::enabled(&s.specification) {
        return compact::render_compact_context(s);
    }
    let config = s
        .specification
        .sonar
        .as_ref()
        .expect("sonar context enabled");
    let observation = if let Some(scan) =
        s.sonar_state.as_ref().and_then(|v| v.latest_scan.as_ref())
    {
        let candidates:Vec<_>=scan.candidates.iter().map(|c|serde_json::json!({"direction":c.direction,
            "positiveResponseL2At1_4_16_64":[c.positive_response_l2[0],c.positive_response_l2[3],c.positive_response_l2[15],c.positive_response_l2[63]],
            "negativeResponseL2At1_4_16_64":[c.negative_response_l2[0],c.negative_response_l2[3],c.negative_response_l2[15],c.negative_response_l2[63]],
            "positiveReturnStep":c.positive_return_step,"negativeReturnStep":c.negative_return_step})).collect();
        serde_json::json!({"scanId":scan.id,"originStep":scan.origin.step,"currentStep":s.step,"controlsAtScan":scan.origin.controls,
            "heldJournalAtScan":scan.origin.held_journal_id,"epsilon":scan.epsilon,"horizons":scan.horizons,
            "leadingGains":scan.singular_values.iter().map(|v|v[0]).collect::<Vec<_>>(),"candidates":candidates,
            "recentStateSamples":scan.mirror.sample_count,"principalVarianceShares":scan.mirror.explained_shares}).to_string()
    } else {
        "No scan requested yet. Operator-only scans are not supplied here.".into()
    };
    let receipts:Vec<_>=s.action_state.as_ref().map(|a|a.recent_receipts.iter().filter_map(|r|r.sonar_probe.as_ref().map(|p|serde_json::json!({
        "appliedStep":r.applied_step,"status":r.status,"sourceScan":p.source_scan,"direction":p.direction,"sign":p.sign,
        "rejection":p.rejection,"actualImmediateL2":r.state_delta_l2,"maximumImmediateL2":p.maximum_state_l2,
        "inputL2":norm(&p.applied_vector),"conditionalForecastAt1_4_16_64":if p.forecast_response_l2.is_empty(){vec![]}else{[0,3,15,63].iter().map(|i|p.forecast_response_l2[*i]).collect::<Vec<_>>()}
    }))).collect()).unwrap_or_default();
    let observation=format!("{observation}\nRECENT SCAN-PROBE RECEIPTS (later forecast points are conditional, not observed)\n{}",serde_json::to_string(&receipts).unwrap());
    format!("COPIED RECURRENT RESPONSE SCANNER response-scan-v1\nNEXT: SCAN runs signed 0.01-L2 probes along all 48 authored input coordinates on copies of the post-application state. It changes no numerical input itself; your journal SEND/WITHHOLD still applies. Results return on later ordinary turns. Branches share held text, fixed controls, future forcing and copied noise for 64 steps. Future writing, actions and sensory evolution are not simulated. This is a local conditional response map, not established global topology.\nNEXT: PROBE_SCAN <strongest|weakest|persistent> <positive|negative> selects a cached measured input direction. Real probes enabled: {}. Without saved authority, a prior scan and a resolved direction, the request is explicitly rejected. Strongest/weakest refer to immediate resolved singular directions; persistent maximizes 16-step response when resolved. These names make no claim about long-term memory. Real probes add one bounded impulse to recurrence AND the separate sensory field; they are not passive. Input L2 <=0.01 and additional immediate recurrent L2 <=0.05. Dose is recalculated with current leak. The receipt records actual immediate effect plus a fresh copied forecast; later forecast values are conditional, not observed live consequences. Old scans need not describe the current state. Return step means below 10% of first response for five consecutive boundaries; null means unresolved or no observed return within 64.\nMODEL-SELECTED SCAN\n{observation}",config.allow_live_probe)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn session() -> SustainedSession {
        SustainedSession::new(SustainedSpecification {
            sonar: Some(SustainedSonarConfig {
                version: SustainedSonarVersion::ResponseScanV1,
                allow_live_probe: false,
            }),
            action_mode: Some(SustainedActionMode::AuthoredV3),
            control_feedback: Some(SustainedControlFeedback::DiagnosticV1),
            prompt_version: SustainedPromptVersion::ActionJournalV3,
            turn_every: 1800,
            maximum_steps: 2000,
            maximum_turns: 8,
            ..SustainedSpecification::default()
        })
        .unwrap()
    }
    #[test]
    fn scan_is_read_only_deterministic_and_uses_native_continuation() {
        let mut source = session();
        for _ in 0..40 {
            source.advance().unwrap();
        }
        let checkpoint = source.checkpoint();
        let before = serde_json::to_vec(&checkpoint).unwrap();
        let a = scan_sustained_checkpoint(&checkpoint).unwrap();
        let b = scan_sustained_checkpoint(&checkpoint).unwrap();
        assert_eq!(a, b);
        validate_report(&a).unwrap();
        assert_eq!(before, serde_json::to_vec(&source.checkpoint()).unwrap());
        for expected in &a.baseline {
            let actual = source.advance().unwrap();
            assert_eq!(actual.step, expected.step);
            assert_eq!(actual.state, expected.state);
        }
        assert_eq!(a.mirror.sample_count, 41);
        assert_eq!(a.horizon, 64);
        assert_eq!(a.immediate_response_matrix.len(), 32);
        assert_eq!(a.candidates.len(), 3);
    }
    #[test]
    fn coordinate_probes_match_local_derivative_away_from_clipping() {
        let mut source = session();
        for _ in 0..19 {
            source.advance().unwrap();
        }
        let report = scan_sustained_checkpoint(&source.checkpoint()).unwrap();
        let o = &report.origin;
        let model = model_for(o).unwrap();
        let mut input = forcing(o.step as usize + 1, o.dt);
        input[18..].copy_from_slice(&scaled_feedback(&o.held_vector, o.controls.feedback_scale));
        let mut rng = SplitMix64::new(o.rng_state.parse().unwrap());
        let mut compared = 0;
        for row in 0..32 {
            let mut drive = model.input_weights[row * 67 + 66];
            for (column, x) in input.iter().enumerate() {
                drive += model.input_weights[row * 67 + column] * x;
            }
            for column in 0..32 {
                drive += model.recurrent_weights[row * 32 + column] * o.state[column];
            }
            let t = drive.tanh();
            let before = (1.0 - o.controls.leak) * o.state[row]
                + o.controls.leak * t
                + rng.signed() * o.noise_amplitude;
            if before.abs() > 0.98 {
                continue;
            }
            for column in 0..48 {
                let expected =
                    o.controls.leak * (1.0 - t * t) * model.input_weights[row * 67 + 18 + column];
                assert!((report.immediate_response_matrix[row][column] - expected).abs() < 1e-4);
                compared += 1;
            }
        }
        assert!(compared > 500);
    }
    #[test]
    fn equal_spectra_do_not_make_equal_state_geometry() {
        let points = |axis| {
            [-0.5, 0.0, 0.5]
                .iter()
                .enumerate()
                .map(|(i, x)| {
                    let mut state = vec![0.0; 32];
                    state[axis] = *x;
                    SustainedSonarPoint {
                        step: i as u64,
                        state,
                    }
                })
                .collect::<Vec<_>>()
        };
        let a = sustained_sonar_mirror(&points(0)).unwrap();
        let b = sustained_sonar_mirror(&points(1)).unwrap();
        assert_eq!(a.covariance_eigenvalues, b.covariance_eigenvalues);
        assert_ne!(a.principal_axes[0], b.principal_axes[0]);
        assert_eq!(a.explained_shares[0], 1.0);
    }
    #[test]
    fn candidate_inputs_obey_a_global_one_step_displacement_bound() {
        let mut source = session();
        for _ in 0..22 {
            source.advance().unwrap();
        }
        let report = scan_sustained_checkpoint(&source.checkpoint()).unwrap();
        for leak in [0.05, 0.65, 1.0] {
            for gain in [0.0, 2.0] {
                let mut o = report.origin.clone();
                o.controls.leak = leak;
                o.controls.recurrent_gain = gain;
                let max_input =
                    SONAR_EPSILON.min(SONAR_STATE_BOUND / (leak * report.input_frobenius_bound));
                let baseline = sustained_sonar_continuation(&o, &[0.0; 48]).unwrap();
                for c in &report.candidates {
                    for sign in [-1.0, 1.0] {
                        let impulse: Vec<_> =
                            c.unit_input.iter().map(|v| v * sign * max_input).collect();
                        let path = sustained_sonar_continuation(&o, &impulse).unwrap();
                        assert!(
                            distance(&path[0].state, &baseline[0].state)
                                <= SONAR_STATE_BOUND + 1e-12
                        );
                    }
                }
            }
        }
    }
    #[test]
    fn old_checkpoint_observation_is_passive_and_unsupported_channel_is_explicit() {
        let old = SustainedSession::new(SustainedSpecification {
            turn_every: 1800,
            ..SustainedSpecification::default()
        })
        .unwrap();
        let cp = old.checkpoint();
        let bytes = serde_json::to_vec(&cp).unwrap();
        let report = scan_sustained_checkpoint(&cp).unwrap();
        assert_eq!(report.mirror.sample_count, 1);
        assert!(report.mirror.principal_axes.is_empty());
        assert_eq!(serde_json::to_vec(&old.checkpoint()).unwrap(), bytes);
        let different = SustainedSession::new(SustainedSpecification {
            difference_gain: 0.1,
            ..SustainedSpecification::default()
        })
        .unwrap();
        assert!(scan_sustained_checkpoint(&different.checkpoint())
            .unwrap_err()
            .to_string()
            .contains("difference channel off"));
    }
    #[test]
    fn history_is_bounded_and_report_tampering_is_rejected() {
        let mut source = session();
        for _ in 0..150 {
            source.advance().unwrap();
            let last = source.events().back().unwrap().id;
            source.acknowledge_events(last).unwrap();
        }
        let cp = source.checkpoint();
        assert_eq!(cp.state.sonar_state.as_ref().unwrap().history.len(), 128);
        let mut report = scan_sustained_checkpoint(&cp).unwrap();
        assert_eq!(report.mirror.first_step, 23);
        report.immediate_response_matrix[0][0] += 1.0;
        assert!(validate_report(&report).is_err());
    }
    #[test]
    fn sonar_footer_requires_fresh_final_unambiguous_syntax() {
        let spec = session().specification().clone();
        for raw in [
            "body\nNEXT: SCAN",
            "body\nNEXT: PROBE_SCAN strongest positive",
            "body\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: SCAN",
        ] {
            assert!(actions::decision_for(&spec, None, raw)
                .unwrap()
                .request
                .is_some());
        }
        for raw in [
            "body\nNEXT: SCAN now",
            "body\nNEXT: SCAN\nmore prose",
            "> NEXT: SCAN",
            "```\nNEXT: SCAN\n```",
            "body\nNEXT: NONE\nNEXT: SCAN",
            "body\nNEXT: PROBE_SCAN strongest 1",
        ] {
            assert!(
                actions::decision_for(&spec, None, raw)
                    .unwrap()
                    .request
                    .is_none(),
                "{raw}"
            );
        }
        let mut historical = spec;
        historical.sonar = None;
        assert!(actions::decision_for(&historical, None, "body\nNEXT: SCAN")
            .unwrap()
            .request
            .is_none());
    }
}
