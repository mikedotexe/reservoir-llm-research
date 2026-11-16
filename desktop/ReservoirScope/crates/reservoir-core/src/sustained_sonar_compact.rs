//! Versioned compact first-step identification, independent checks and questions.
use super::*;

pub const COMPACT_EPSILON: f64 = 0.001;
pub const COMPACT_ERROR_LIMIT: f64 = 0.01;
pub const COMPACT_VALIDATION_DIRECTIONS: usize = 16;
const CALIBRATION_SEED: u64 = 20_261_117;
const VALIDATION_SEED: u64 = 20_261_118;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum SustainedSonarQuestion {
    State,
    Input,
    Recurrence,
}
impl SustainedSonarQuestion {
    pub fn name(self) -> &'static str {
        match self {
            Self::State => "state",
            Self::Input => "input",
            Self::Recurrence => "recurrence",
        }
    }
    pub fn description(self) -> &'static str {
        match self {
            Self::State => "Current starting state versus zero starting state; same held input, controls, forcing and noise.",
            Self::Input => "Current held input versus zero held input; same starting state, controls, forcing and noise.",
            Self::Recurrence => "Current recurrent gain versus zero recurrent gain; same starting state, held input, forcing and noise.",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedSonarValidation {
    pub seed: String,
    pub signed_probes: usize,
    pub resolved_probes: usize,
    pub aggregate_relative_error: Option<f64>,
    pub maximum_relative_error: Option<f64>,
    pub absolute_error_l2: f64,
    pub response_l2: f64,
    pub passed: bool,
}
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedSonarSignedFallback {
    pub reason: String,
    /// Coordinate-major measured state differences, not predictions.
    pub positive: Vec<Vec<f64>>,
    pub negative: Vec<Vec<f64>>,
}
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedCompactSonarReport {
    pub version: SustainedSonarVersion,
    pub id: String,
    pub origin: SustainedSonarOrigin,
    pub epsilon: f64,
    pub calibration_direction: Vec<f64>,
    pub calibration_positive: Vec<f64>,
    pub calibration_negative: Vec<f64>,
    pub row_gains: Vec<f64>,
    pub minimum_normalized_drive: f64,
    pub validation: SustainedSonarValidation,
    pub fallback: Option<SustainedSonarSignedFallback>,
    pub candidates: Vec<SustainedSonarCandidate>,
    pub maximum_live_input_l2: f64,
    pub maximum_live_state_l2: f64,
}
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedSonarQuestionReport {
    pub version: SustainedSonarVersion,
    pub id: String,
    pub question: SustainedSonarQuestion,
    pub origin: SustainedSonarOrigin,
    pub alternative_origin: SustainedSonarOrigin,
    pub epsilon: f64,
    pub actual_map_id: String,
    pub alternative_map_id: String,
    pub actual_validation: SustainedSonarValidation,
    pub alternative_validation: SustainedSonarValidation,
    pub used_signed_fallback: bool,
    pub unit_input: Option<Vec<f64>>,
    /// Positive then negative; differences of baseline-subtracted responses.
    pub predicted_gap: Vec<Vec<f64>>,
    pub measured_gap: Vec<Vec<f64>>,
    pub actual_response_l2: Vec<f64>,
    pub alternative_response_l2: Vec<f64>,
    pub prediction_relative_error: Option<f64>,
    pub linear_prediction_valid: bool,
    pub random_median_gap_l2: f64,
    pub gain_over_random: Option<f64>,
}
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedSonarQuestionForecast {
    pub question: SustainedSonarQuestion,
    pub alternative_origin: SustainedSonarOrigin,
    pub actual_delta: Vec<f64>,
    pub alternative_delta: Vec<f64>,
    pub difference_l2: f64,
}

pub(super) fn enabled(s: &SustainedSpecification) -> bool {
    s.sonar
        .as_ref()
        .is_some_and(|c| c.version == SustainedSonarVersion::CompactScanV2)
}
fn unit(rng: &mut SplitMix64) -> Vec<f64> {
    let mut v: Vec<_> = (0..48).map(|_| rng.signed()).collect();
    let n = norm(&v);
    for x in &mut v {
        *x /= n;
    }
    v
}
fn validation_directions() -> Vec<Vec<f64>> {
    let mut rng = SplitMix64::new(VALIDATION_SEED);
    (0..COMPACT_VALIDATION_DIRECTIONS)
        .map(|_| unit(&mut rng))
        .collect()
}
fn wiring(o: &SustainedSonarOrigin) -> Result<Vec<Vec<f64>>> {
    Ok(model_for(o)?
        .input_weights
        .chunks(67)
        .map(|r| r[18..66].to_vec())
        .collect())
}
fn multiply(m: &[Vec<f64>], v: &[f64]) -> Vec<f64> {
    m.iter()
        .map(|r| r.iter().zip(v).map(|(a, b)| a * b).sum())
        .collect()
}
fn subtract(a: &[f64], b: &[f64]) -> Vec<f64> {
    a.iter().zip(b).map(|(a, b)| a - b).collect()
}
fn first(o: &SustainedSonarOrigin, impulse: &[f64]) -> Result<Vec<f64>> {
    Ok(continuation_for(o, impulse, 1)?.remove(0).state)
}
fn response(
    o: &SustainedSonarOrigin,
    baseline: &[f64],
    unit: &[f64],
    amount: f64,
) -> Result<Vec<f64>> {
    let impulse: Vec<_> = unit.iter().map(|v| v * amount).collect();
    Ok(subtract(&first(o, &impulse)?, baseline))
}
fn validate_prediction(
    o: &SustainedSonarOrigin,
    matrix: &[Vec<f64>],
    baseline: &[f64],
) -> Result<SustainedSonarValidation> {
    let mut error2 = 0.0;
    let mut response2 = 0.0;
    let mut worst: f64 = 0.0;
    let mut resolved = 0;
    for direction in validation_directions() {
        let p = multiply(matrix, &direction);
        for sign in [-1.0, 1.0] {
            let actual = response(o, baseline, &direction, sign * COMPACT_EPSILON)?;
            let predicted: Vec<_> = p.iter().map(|v| v * sign * COMPACT_EPSILON).collect();
            let n = norm(&actual);
            let e = distance(&actual, &predicted);
            error2 += e * e;
            response2 += n * n;
            if n > RESOLUTION {
                resolved += 1;
            }
            // False predicted signal also fails, even when measurement is unresolved.
            worst = worst.max(e / n.max(RESOLUTION));
        }
    }
    let magnitude = response2.sqrt();
    let relative = (magnitude > RESOLUTION).then_some(error2.sqrt() / magnitude.max(RESOLUTION));
    Ok(SustainedSonarValidation {
        seed: VALIDATION_SEED.to_string(),
        signed_probes: COMPACT_VALIDATION_DIRECTIONS * 2,
        resolved_probes: resolved,
        aggregate_relative_error: relative,
        maximum_relative_error: Some(worst),
        absolute_error_l2: error2.sqrt(),
        response_l2: magnitude,
        passed: resolved > 0
            && relative.is_some_and(|e| e <= COMPACT_ERROR_LIMIT)
            && worst <= COMPACT_ERROR_LIMIT,
    })
}
fn raw_matrix(r: &SustainedCompactSonarReport) -> Result<Vec<Vec<f64>>> {
    if let Some(f) = &r.fallback {
        Ok((0..r.origin.state.len())
            .map(|row| {
                (0..48)
                    .map(|col| (f.positive[col][row] - f.negative[col][row]) / (2.0 * r.epsilon))
                    .collect()
            })
            .collect())
    } else {
        Ok(wiring(&r.origin)?
            .iter()
            .zip(&r.row_gains)
            .map(|(row, g)| row.iter().map(|v| v * g).collect())
            .collect())
    }
}
pub fn compact_sonar_matrix(r: &SustainedCompactSonarReport) -> Result<Vec<Vec<f64>>> {
    validate_compact_sonar_report(r)?;
    raw_matrix(r)
}
fn candidate(
    o: &SustainedSonarOrigin,
    kind: SustainedSonarDirection,
    unit: Vec<f64>,
    baseline: &[SustainedSonarPoint],
) -> Result<SustainedSonarCandidate> {
    let curves: Result<Vec<Vec<f64>>> = [1.0, -1.0]
        .iter()
        .map(|sign| {
            let impulse: Vec<_> = unit.iter().map(|v| v * sign * COMPACT_EPSILON).collect();
            Ok(sustained_sonar_continuation(o, &impulse)?
                .iter()
                .zip(baseline)
                .map(|(a, b)| distance(&a.state, &b.state))
                .collect())
        })
        .collect();
    let mut curves = curves?;
    let negative = curves.pop().unwrap();
    let positive = curves.pop().unwrap();
    Ok(SustainedSonarCandidate {
        direction: kind,
        unit_input: unit,
        positive_return_step: return_step(&positive),
        negative_return_step: return_step(&negative),
        positive_response_l2: positive,
        negative_response_l2: negative,
    })
}
fn scan_origin(
    o: SustainedSonarOrigin,
    with_candidates: bool,
) -> Result<SustainedCompactSonarReport> {
    validate_origin(&o)?;
    let b = wiring(&o)?;
    let row_norms: Vec<_> = b.iter().map(|r| norm(r)).collect();
    let mut rng = SplitMix64::new(CALIBRATION_SEED);
    let mut best = vec![0.0; 48];
    let mut conditioning = 0.0;
    for _ in 0..256 {
        let v = unit(&mut rng);
        let drive = multiply(&b, &v);
        let score = drive
            .iter()
            .zip(&row_norms)
            .map(|(d, n)| d.abs() / n.max(1e-12))
            .fold(f64::INFINITY, f64::min);
        if score > conditioning {
            conditioning = score;
            best = v;
        }
    }
    let baseline = first(&o, &[0.0; 48])?;
    let positive = response(&o, &baseline, &best, COMPACT_EPSILON)?;
    let negative = response(&o, &baseline, &best, -COMPACT_EPSILON)?;
    let drive = multiply(&b, &best);
    let gains: Vec<_> = positive
        .iter()
        .zip(&negative)
        .zip(&drive)
        .map(|((p, n), d)| {
            if d.abs() > 1e-12 {
                ((p - n) / (2.0 * COMPACT_EPSILON * d)).clamp(0.0, o.controls.leak)
            } else {
                0.0
            }
        })
        .collect();
    let matrix: Vec<Vec<f64>> = b
        .iter()
        .zip(&gains)
        .map(|(row, g)| row.iter().map(|v| v * g).collect())
        .collect();
    let validation = validate_prediction(&o, &matrix, &baseline)?;
    let fallback = if conditioning <= 1e-9 || !validation.passed {
        let reason = if conditioning <= 1e-9 {
            "Calibration drive is unresolved"
        } else if validation.resolved_probes == 0 {
            "Fresh probes found no resolved response"
        } else {
            "Fresh-probe prediction error exceeded 1%"
        };
        let mut p = Vec::new();
        let mut n = Vec::new();
        for i in 0..48 {
            let mut v = vec![0.0; 48];
            v[i] = 1.0;
            p.push(response(&o, &baseline, &v, COMPACT_EPSILON)?);
            n.push(response(&o, &baseline, &v, -COMPACT_EPSILON)?);
        }
        Some(SustainedSonarSignedFallback {
            reason: reason.into(),
            positive: p,
            negative: n,
        })
    } else {
        None
    };
    let cap = dose(&o)?;
    let mut report = SustainedCompactSonarReport {
        version: SustainedSonarVersion::CompactScanV2,
        id: String::new(),
        origin: o,
        epsilon: COMPACT_EPSILON,
        calibration_direction: best,
        calibration_positive: positive,
        calibration_negative: negative,
        row_gains: gains,
        minimum_normalized_drive: conditioning,
        validation,
        fallback,
        candidates: Vec::new(),
        maximum_live_input_l2: cap,
        maximum_live_state_l2: SONAR_STATE_BOUND,
    };
    if with_candidates {
        let (values, right) = decomposition(&raw_matrix(&report)?)?;
        if values[0] > RESOLUTION {
            let weakest = values.iter().rposition(|v| *v > RESOLUTION).unwrap();
            let baseline = sustained_sonar_continuation(&report.origin, &[0.0; 48])?;
            report.candidates.push(candidate(
                &report.origin,
                SustainedSonarDirection::Strongest,
                right[0].clone(),
                &baseline,
            )?);
            report.candidates.push(candidate(
                &report.origin,
                SustainedSonarDirection::Weakest,
                right[weakest].clone(),
                &baseline,
            )?);
        }
    }
    report.id = typed_hash(&report);
    Ok(report)
}
pub fn scan_compact_sustained_checkpoint(
    cp: &SustainedCheckpoint,
) -> Result<SustainedCompactSonarReport> {
    cp.validate()?;
    scan_compact_state(&cp.state)
}
pub(super) fn scan_compact_state(s: &SustainedContinuation) -> Result<SustainedCompactSonarReport> {
    ensure(
        s.specification.difference_gain == 0.0,
        "Compact scans require the difference channel off",
    )?;
    let history = s
        .sonar_state
        .as_ref()
        .map(|v| v.history.clone())
        .unwrap_or_else(|| {
            vec![SustainedSonarPoint {
                step: s.step,
                state: s.reservoir_state.clone(),
            }]
        });
    scan_origin(origin(s, &history), true)
}
fn alternative(o: &SustainedSonarOrigin, question: SustainedSonarQuestion) -> SustainedSonarOrigin {
    let mut alt = o.clone();
    match question {
        SustainedSonarQuestion::State => alt.state.fill(0.0),
        SustainedSonarQuestion::Input => alt.held_vector.fill(0.0),
        SustainedSonarQuestion::Recurrence => alt.controls.recurrent_gain = 0.0,
    }
    alt
}
pub fn question_sustained_checkpoint(
    cp: &SustainedCheckpoint,
    question: SustainedSonarQuestion,
) -> Result<SustainedSonarQuestionReport> {
    cp.validate()?;
    question_state(&cp.state, question)
}
pub(super) fn question_state(
    s: &SustainedContinuation,
    question: SustainedSonarQuestion,
) -> Result<SustainedSonarQuestionReport> {
    ensure(
        enabled(&s.specification),
        "Question scans require compact-scan-v2",
    )?;
    let history = &s
        .sonar_state
        .as_ref()
        .ok_or_else(|| invalid("Missing scanner history"))?
        .history;
    question_origin(origin(s, history), question)
}
fn question_origin(
    o: SustainedSonarOrigin,
    question: SustainedSonarQuestion,
) -> Result<SustainedSonarQuestionReport> {
    let alt = alternative(&o, question);
    let a = scan_origin(o.clone(), false)?;
    let b = scan_origin(alt.clone(), false)?;
    let ma = raw_matrix(&a)?;
    let mb = raw_matrix(&b)?;
    let delta: Vec<_> = ma.iter().zip(&mb).map(|(a, b)| subtract(a, b)).collect();
    let (values, right) = decomposition(&delta)?;
    let baseline = first(&o, &[0.0; 48])?;
    let alt_baseline = first(&alt, &[0.0; 48])?;
    let mut measured = Vec::new();
    let mut predicted = Vec::new();
    let mut actual_norm = Vec::new();
    let mut alt_norm = Vec::new();
    let mut direction = (values[0] > RESOLUTION).then(|| right[0].clone());
    if let Some(v) = &direction {
        let p = multiply(&delta, v);
        for sign in [1.0, -1.0] {
            let actual = response(&o, &baseline, v, sign * COMPACT_EPSILON)?;
            let alternative = response(&alt, &alt_baseline, v, sign * COMPACT_EPSILON)?;
            measured.push(subtract(&actual, &alternative));
            predicted.push(
                p.iter()
                    .map(|x| x * sign * COMPACT_EPSILON)
                    .collect::<Vec<_>>(),
            );
            actual_norm.push(norm(&actual));
            alt_norm.push(norm(&alternative));
        }
        if measured.iter().all(|v| norm(v) <= RESOLUTION) {
            direction = None;
        }
    }
    let mut random = Vec::new();
    for v in validation_directions() {
        for sign in [1.0, -1.0] {
            let a = response(&o, &baseline, &v, sign * COMPACT_EPSILON)?;
            let b = response(&alt, &alt_baseline, &v, sign * COMPACT_EPSILON)?;
            random.push(distance(&a, &b));
        }
    }
    random.sort_by(f64::total_cmp);
    let median = (random[15] + random[16]) / 2.0;
    let measured_norm = measured.iter().map(|v| norm(v).powi(2)).sum::<f64>().sqrt();
    let error = measured
        .iter()
        .zip(&predicted)
        .map(|(a, b)| distance(a, b).powi(2))
        .sum::<f64>()
        .sqrt();
    let relative = (measured_norm > RESOLUTION).then_some(error / measured_norm.max(RESOLUTION));
    let gain = (direction.is_some() && median > RESOLUTION)
        .then(|| measured.iter().map(|v| norm(v)).sum::<f64>() / 2.0 / median);
    let valid = direction.is_some()
        && a.fallback.is_none()
        && b.fallback.is_none()
        && relative.is_some_and(|e| e <= COMPACT_ERROR_LIMIT);
    let mut report = SustainedSonarQuestionReport {
        version: SustainedSonarVersion::CompactScanV2,
        id: String::new(),
        question,
        origin: o,
        alternative_origin: alt,
        epsilon: COMPACT_EPSILON,
        actual_map_id: a.id,
        alternative_map_id: b.id,
        actual_validation: a.validation,
        alternative_validation: b.validation,
        used_signed_fallback: a.fallback.is_some() || b.fallback.is_some(),
        unit_input: direction,
        predicted_gap: predicted,
        measured_gap: measured,
        actual_response_l2: actual_norm,
        alternative_response_l2: alt_norm,
        prediction_relative_error: relative,
        linear_prediction_valid: valid,
        random_median_gap_l2: median,
        gain_over_random: gain,
    };
    report.id = typed_hash(&report);
    Ok(report)
}

fn validate_check(v: &SustainedSonarValidation) -> Result<()> {
    ensure(
        v.seed == VALIDATION_SEED.to_string()
            && v.signed_probes == 32
            && v.resolved_probes <= 32
            && v.absolute_error_l2.is_finite()
            && v.absolute_error_l2 >= 0.0
            && v.response_l2.is_finite()
            && v.response_l2 >= 0.0
            && [v.aggregate_relative_error, v.maximum_relative_error]
                .into_iter()
                .flatten()
                .all(|e| e.is_finite() && e >= 0.0)
            && v.aggregate_relative_error.is_some() == (v.response_l2 > RESOLUTION)
            && v.maximum_relative_error.is_some()
            && v.passed
                == (v.resolved_probes > 0
                    && v.aggregate_relative_error
                        .is_some_and(|e| e <= COMPACT_ERROR_LIMIT)
                    && v.maximum_relative_error
                        .is_some_and(|e| e <= COMPACT_ERROR_LIMIT)),
        "Invalid fresh-probe validation",
    )?;
    if let Some(e) = v.aggregate_relative_error {
        ensure(
            (e - v.absolute_error_l2 / v.response_l2).abs() < 1e-12,
            "Validation error ratio differs",
        )?;
    }
    Ok(())
}
fn unit_vector(v: &[f64]) -> Result<()> {
    vector(v, 48, "compact probe direction")?;
    ensure((norm(v) - 1.0).abs() < 1e-10, "Nonunit compact direction")
}
pub fn validate_compact_sonar_report(r: &SustainedCompactSonarReport) -> Result<()> {
    validate_origin(&r.origin)?;
    validate_check(&r.validation)?;
    ensure(
        r.version == SustainedSonarVersion::CompactScanV2 && r.epsilon == COMPACT_EPSILON,
        "Invalid compact report version/settings",
    )?;
    unit_vector(&r.calibration_direction)?;
    for v in [
        &r.calibration_positive,
        &r.calibration_negative,
        &r.row_gains,
    ] {
        vector(v, r.origin.state.len(), "compact calibration")?;
    }
    ensure(
        r.row_gains
            .iter()
            .all(|v| *v >= 0.0 && *v <= r.origin.controls.leak)
            && r.minimum_normalized_drive.is_finite()
            && r.minimum_normalized_drive >= 0.0
            && r.minimum_normalized_drive <= 1.0,
        "Invalid calibrated gains/conditioning",
    )?;
    ensure(
        r.fallback.is_some() == (!r.validation.passed || r.minimum_normalized_drive <= 1e-9),
        "Compact fallback omitted or spurious",
    )?;
    if let Some(f) = &r.fallback {
        let reason = if r.minimum_normalized_drive <= 1e-9 {
            "Calibration drive is unresolved"
        } else if r.validation.resolved_probes == 0 {
            "Fresh probes found no resolved response"
        } else {
            "Fresh-probe prediction error exceeded 1%"
        };
        ensure(
            f.reason == reason && f.positive.len() == 48 && f.negative.len() == 48,
            "Invalid signed fallback",
        )?;
        for v in f.positive.iter().chain(&f.negative) {
            vector(v, r.origin.state.len(), "signed fallback response")?;
            ensure(
                v.iter().all(|x| x.abs() <= 2.0),
                "Fallback response out of bounds",
            )?;
        }
    }
    ensure(r.candidates.len() <= 2, "Too many compact candidates")?;
    for (i, c) in r.candidates.iter().enumerate() {
        ensure(
            matches!(
                c.direction,
                SustainedSonarDirection::Strongest | SustainedSonarDirection::Weakest
            ) && r.candidates[..i].iter().all(|p| p.direction != c.direction),
            "Invalid compact candidate",
        )?;
        unit_vector(&c.unit_input)?;
        for v in [&c.positive_response_l2, &c.negative_response_l2] {
            vector(v, 64, "compact candidate curve")?;
            ensure(
                v.iter().all(|x| *x >= 0.0 && *x <= 12.0),
                "Invalid candidate separation",
            )?;
        }
        ensure(
            c.positive_return_step == return_step(&c.positive_response_l2)
                && c.negative_return_step == return_step(&c.negative_response_l2),
            "Candidate return differs",
        )?;
    }
    ensure(
        r.maximum_live_input_l2 == dose(&r.origin)? && r.maximum_live_state_l2 == SONAR_STATE_BOUND,
        "Compact bound differs",
    )?;
    let mut copy = r.clone();
    copy.id.clear();
    ensure(
        valid_hash(&r.id) && r.id == typed_hash(&copy),
        "Compact report hash differs",
    )
}
pub fn validate_sonar_question_report(r: &SustainedSonarQuestionReport) -> Result<()> {
    validate_origin(&r.origin)?;
    validate_origin(&r.alternative_origin)?;
    validate_check(&r.actual_validation)?;
    validate_check(&r.alternative_validation)?;
    ensure(
        r.version == SustainedSonarVersion::CompactScanV2
            && r.epsilon == COMPACT_EPSILON
            && r.alternative_origin == alternative(&r.origin, r.question)
            && valid_hash(&r.actual_map_id)
            && valid_hash(&r.alternative_map_id),
        "Invalid question alternatives",
    )?;
    if let Some(v) = &r.unit_input {
        unit_vector(v)?;
    }
    let n = r.measured_gap.len();
    ensure(
        [0, 2].contains(&n)
            && r.predicted_gap.len() == n
            && r.actual_response_l2.len() == n
            && r.alternative_response_l2.len() == n,
        "Invalid question outcome dimensions",
    )?;
    for v in r.measured_gap.iter().chain(&r.predicted_gap) {
        vector(v, r.origin.state.len(), "question gap")?;
    }
    let magnitude = r
        .measured_gap
        .iter()
        .map(|v| norm(v).powi(2))
        .sum::<f64>()
        .sqrt();
    let error = r
        .measured_gap
        .iter()
        .zip(&r.predicted_gap)
        .map(|(a, b)| distance(a, b).powi(2))
        .sum::<f64>()
        .sqrt();
    let relative = (magnitude > RESOLUTION).then_some(error / magnitude.max(RESOLUTION));
    ensure(
        (r.actual_validation.passed && r.alternative_validation.passed || r.used_signed_fallback)
            && r.prediction_relative_error == relative
            && r.unit_input.is_some() == r.measured_gap.iter().any(|v| norm(v) > RESOLUTION)
            && r.actual_response_l2
                .iter()
                .chain(&r.alternative_response_l2)
                .all(|v| v.is_finite() && *v >= 0.0 && *v <= 12.0)
            && r.random_median_gap_l2.is_finite()
            && r.random_median_gap_l2 >= 0.0
            && r.random_median_gap_l2 <= 24.0
            && r.linear_prediction_valid
                == (r.unit_input.is_some()
                    && !r.used_signed_fallback
                    && relative.is_some_and(|e| e <= COMPACT_ERROR_LIMIT)),
        "Invalid measured question evidence",
    )?;
    let gain = (r.unit_input.is_some() && r.random_median_gap_l2 > RESOLUTION).then(|| {
        r.measured_gap.iter().map(|v| norm(v)).sum::<f64>() / 2.0 / r.random_median_gap_l2
    });
    ensure(
        r.gain_over_random == gain,
        "Question random-control ratio differs",
    )?;
    let mut copy = r.clone();
    copy.id.clear();
    ensure(
        valid_hash(&r.id) && r.id == typed_hash(&copy),
        "Question report hash differs",
    )
}
pub(super) fn question_forecast(
    o: &SustainedSonarOrigin,
    question: SustainedSonarQuestion,
    impulse: &[f64],
) -> Result<SustainedSonarQuestionForecast> {
    let alt = alternative(o, question);
    let actual = subtract(&first(o, impulse)?, &first(o, &[0.0; 48])?);
    let alternative_delta = subtract(&first(&alt, impulse)?, &first(&alt, &[0.0; 48])?);
    Ok(SustainedSonarQuestionForecast {
        question,
        alternative_origin: alt,
        difference_l2: distance(&actual, &alternative_delta),
        actual_delta: actual,
        alternative_delta,
    })
}
pub(super) fn validate_question_forecast(p: &SustainedSonarProbeReceipt) -> Result<()> {
    if let Some(q) = &p.question_forecast {
        ensure(
            p.direction == SustainedSonarDirection::Question && p.rejection.is_none(),
            "Unexpected question forecast",
        )?;
        let o = p
            .forecast_origin
            .as_ref()
            .ok_or_else(|| invalid("Missing question application origin"))?;
        validate_origin(&q.alternative_origin)?;
        vector(&q.actual_delta, o.state.len(), "question actual delta")?;
        vector(&q.alternative_delta, o.state.len(), "question alternative delta")?;
        ensure(
            q.alternative_origin == alternative(o, q.question)
                && q.difference_l2 == distance(&q.actual_delta, &q.alternative_delta)
                && (norm(&q.actual_delta) - p.forecast_response_l2[0]).abs() < 1e-12,
            "Question forecast differs",
        )?;
    } else {
        ensure(
            p.direction != SustainedSonarDirection::Question || p.rejection.is_some(),
            "Missing question probe evidence",
        )?;
    }
    Ok(())
}
pub(super) fn validate_cached_state(
    s: &SustainedContinuation,
    state: &SustainedSonarState,
) -> Result<()> {
    if !enabled(&s.specification) {
        return ensure(
            state.latest_compact_scan.is_none() && state.latest_question.is_none(),
            "Compact cache in historical session",
        );
    }
    ensure(
        state.latest_scan.is_none() && state.history.len() <= 32,
        "Invalid compact history/cache",
    )?;
    let check = |o: &SustainedSonarOrigin| {
        ensure(
            o.step <= s.step
                && o.seed == s.specification.seed.to_string()
                && o.model_sha256 == s.model_sha256,
            "Compact cache source differs",
        )
    };
    if let Some(r) = &state.latest_compact_scan {
        validate_compact_sonar_report(r)?;
        check(&r.origin)?;
    }
    if let Some(r) = &state.latest_question {
        validate_sonar_question_report(r)?;
        check(&r.origin)?;
    }
    Ok(())
}
pub(super) fn apply_compact_scan(
    s: &mut SustainedContinuation,
    receipt: &mut Option<Box<SustainedActionReceipt>>,
) -> Result<()> {
    let Some(r) = receipt else {
        return Ok(());
    };
    match r.request {
        Some(SustainedActionRequest::Scan) => {
            let report = scan_compact_state(s)?;
            r.sonar_scan = Some(SustainedSonarScanRef {
                id: report.id.clone(),
                step: report.origin.step,
            });
            s.sonar_state.as_mut().unwrap().latest_compact_scan = Some(Box::new(report));
            sync_receipt(s, r);
        }
        Some(SustainedActionRequest::ScanQuestion { question }) => {
            let report = question_state(s, question)?;
            r.sonar_question = Some(SustainedSonarScanRef {
                id: report.id.clone(),
                step: report.origin.step,
            });
            s.sonar_state.as_mut().unwrap().latest_question = Some(Box::new(report));
            sync_receipt(s, r);
        }
        _ => {}
    }
    Ok(())
}
pub(super) fn validate_question_receipt(
    r: &SustainedActionReceipt,
    s: &SustainedContinuation,
) -> Result<()> {
    match (&r.request, &r.sonar_question) {
        (Some(SustainedActionRequest::ScanQuestion { .. }), Some(q)) => ensure(
            enabled(&s.specification)
                && valid_hash(&q.id)
                && q.step == r.applied_step
                && r.state_delta_l2 == 0.0
                && r.status == SustainedActionStatus::Applied,
            "Invalid copied question receipt",
        ),
        (Some(SustainedActionRequest::ScanQuestion { .. }), None) | (_, Some(_)) => {
            Err(invalid("Question receipt/request mismatch"))
        }
        _ => Ok(()),
    }
}
pub(super) fn resolve_compact_probe(
    s: &SustainedContinuation,
    request: Option<&SustainedActionRequest>,
) -> Result<Option<SustainedSonarProbeReceipt>> {
    let Some(SustainedActionRequest::ProbeScan { direction, sign }) = request else {
        return Ok(None);
    };
    let state = s
        .sonar_state
        .as_ref()
        .ok_or_else(|| invalid("Missing compact scanner"))?;
    let is_question = *direction == SustainedSonarDirection::Question;
    let (source, unit, question) = if is_question {
        (
            state
                .latest_question
                .as_ref()
                .map(|q| SustainedSonarScanRef {
                    id: q.id.clone(),
                    step: q.origin.step,
                }),
            state
                .latest_question
                .as_ref()
                .and_then(|q| q.unit_input.as_ref()),
            state.latest_question.as_ref().map(|q| q.question),
        )
    } else {
        (
            state
                .latest_compact_scan
                .as_ref()
                .map(|q| SustainedSonarScanRef {
                    id: q.id.clone(),
                    step: q.origin.step,
                }),
            state
                .latest_compact_scan
                .as_ref()
                .and_then(|q| q.candidates.iter().find(|c| c.direction == *direction))
                .map(|c| &c.unit_input),
            None,
        )
    };
    let rejection = if !s.specification.sonar.as_ref().unwrap().allow_live_probe {
        Some(NO_AUTHORITY)
    } else if source.is_none() {
        Some(if is_question { NO_QUESTION } else { NO_SCAN })
    } else if unit.is_none() {
        Some(NO_DIRECTION)
    } else {
        None
    };
    let mut r = SustainedSonarProbeReceipt {
        question_forecast: None,
        direction: *direction,
        sign: *sign,
        source_scan: source,
        rejection: rejection.map(str::to_owned),
        applied_vector: vec![0.0; 48],
        maximum_state_l2: SONAR_STATE_BOUND,
        forecast_origin: None,
        forecast_response_l2: Vec::new(),
    };
    if let Some(unit) = unit.filter(|_| rejection.is_none()) {
        let o = origin(s, &state.history);
        let amount = dose(&o)?
            * if *sign == SustainedSonarSign::Positive {
                1.0
            } else {
                -1.0
            };
        r.applied_vector = unit.iter().map(|v| v * amount).collect();
        let baseline = sustained_sonar_continuation(&o, &[0.0; 48])?;
        let actual = sustained_sonar_continuation(&o, &r.applied_vector)?;
        r.forecast_response_l2 = actual
            .iter()
            .zip(&baseline)
            .map(|(a, b)| distance(&a.state, &b.state))
            .collect();
        if let Some(q) = question {
            r.question_forecast = Some(question_forecast(&o, q, &r.applied_vector)?);
        }
        r.forecast_origin = Some(o);
    }
    Ok(Some(r))
}
pub(super) const NO_QUESTION:&str="No model-selected question scan is available. Choose NEXT: SCAN_QUESTION state, input or recurrence first; no probe applied.";
pub(super) fn render_compact_context(s: &SustainedContinuation) -> String {
    let state = s.sonar_state.as_ref().expect("compact capability");
    let scan=state.latest_compact_scan.as_ref().map(|r|serde_json::json!({
        "scanId":r.id,"originStep":r.origin.step,"currentStep":s.step,"epsilon":r.epsilon,
        "validation":r.validation,"signedFallback":r.fallback.as_ref().map(|f|&f.reason),
        "candidates":r.candidates.iter().map(|c|serde_json::json!({"direction":c.direction,"positiveL2At1_4_16_64":[c.positive_response_l2[0],c.positive_response_l2[3],c.positive_response_l2[15],c.positive_response_l2[63]],"negativeL2At1_4_16_64":[c.negative_response_l2[0],c.negative_response_l2[3],c.negative_response_l2[15],c.negative_response_l2[63]]})).collect::<Vec<_>>()
    }));
    let question=state.latest_question.as_ref().map(|q|serde_json::json!({
        "questionId":q.id,"question":q.question,"alternatives":q.question.description(),"originStep":q.origin.step,
        "currentStep":s.step,"epsilon":q.epsilon,"directionResolved":q.unit_input.is_some(),
        "actualValidation":q.actual_validation,"alternativeValidation":q.alternative_validation,"usedSignedFallback":q.used_signed_fallback,
        "linearPredictionValid":q.linear_prediction_valid,"predictionRelativeError":q.prediction_relative_error,
        "positiveNegativeMeasuredGapL2":q.measured_gap.iter().map(|v|norm(v)).collect::<Vec<_>>(),
        "actualResponseL2":q.actual_response_l2,"alternativeResponseL2":q.alternative_response_l2,
        "randomMedianGapL2":q.random_median_gap_l2,"gainOverRandom":q.gain_over_random
    }));
    let receipts:Vec<_>=s.action_state.as_ref().map(|a|a.recent_receipts.iter().filter_map(|r|r.sonar_probe.as_ref().map(|p|serde_json::json!({
        "appliedStep":r.applied_step,"status":r.status,"direction":p.direction,"sign":p.sign,"sourceScan":p.source_scan,"rejection":p.rejection,
        "observedImmediateL2":r.state_delta_l2,"maximumImmediateL2":p.maximum_state_l2,
        "freshCopiedFirstPrediction":p.forecast_response_l2.first(),
        "questionForecast":p.question_forecast.as_ref().map(|q|serde_json::json!({"question":q.question,"alternatives":q.question.description(),"copiedAlternativeResponseL2":norm(&q.alternative_delta),"copiedContrastL2":q.difference_l2}))
    }))).collect()).unwrap_or_default();
    format!("COPIED RECURRENT RESPONSE SCANNER compact-scan-v2\nNEXT: SCAN calibrates known-wiring first-step sensitivity with two signed 0.001-L2 inputs. Sixteen independent directions tested with both signs validate the map; both pooled and worst relative errors must be <=1%. Failed/unresolved calibration falls back to 96 measured signed coordinate responses; that fallback is not a validated linear map. Strongest and weakest select immediate resolved directions, with actual copied 64-step curves; persistent is unavailable in v2.\nNEXT: SCAN_QUESTION <state|input|recurrence> chooses a numerical question. state compares current starting state to zero state; input removes the held text vector; recurrence sets recurrent gain to zero. Each comparison keeps other conditions, forcing and copied noise fixed. A numerical tool selects the vector distinguishing the two local response maps, then measures both signs against paired baselines and equal-energy random controls. Missing signal is reported unresolved. This is a copied counterfactual experiment, not evidence of global topology or an unknown state. You choose the question; the tool chooses its vector.\nNEXT: PROBE_SCAN <strongest|weakest|question> <positive|negative> applies the cached model-selected vector only if real probes are authorized ({}). The question choice uses the most recent resolved SCAN_QUESTION result. Without authority/source/direction the request is rejected. A real impulse reaches recurrence AND the sensory field; input L2 <=0.01 and additional immediate recurrent L2 <=0.05. Current leak sets dose and the application origin refreshes the forecast. Only the actual immediate paired effect is observed; the alternative and later trajectory remain copied predictions.\nSCAN and SCAN_QUESTION themselves add no numerical input; ordinary SEND/WITHHOLD still applies. Future writing/actions and sensory evolution are not simulated. Operator-only observations never populate these model caches. Old maps may be stale.\nMODEL-SELECTED COMPACT SCAN\n{}\nMODEL-SELECTED QUESTION\n{}\nRECENT REAL-PROBE RECEIPTS\n{}",
        s.specification.sonar.as_ref().unwrap().allow_live_probe,serde_json::to_string(&scan).unwrap(),serde_json::to_string(&question).unwrap(),serde_json::to_string(&receipts).unwrap())
}

#[cfg(test)]
mod tests {
    use super::*;
    fn session() -> SustainedSession {
        SustainedSession::new(SustainedSpecification {
            sonar: Some(SustainedSonarConfig {
                version: SustainedSonarVersion::CompactScanV2,
                allow_live_probe: true,
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
    fn compact_native_map_is_validated_passive_and_smaller_than_v1() {
        let mut s = session();
        for _ in 0..19 {
            s.advance().unwrap();
        }
        let cp = s.checkpoint();
        let before = serde_json::to_vec(&cp).unwrap();
        let compact = scan_compact_sustained_checkpoint(&cp).unwrap();
        assert!(compact.validation.passed);
        assert!(compact.fallback.is_none());
        assert_eq!(compact, scan_compact_sustained_checkpoint(&cp).unwrap());
        validate_compact_sonar_report(&compact).unwrap();
        let old = scan_sustained_checkpoint(&cp).unwrap();
        let matrix = compact_sonar_matrix(&compact).unwrap();
        let max = matrix
            .iter()
            .flatten()
            .zip(old.immediate_response_matrix.iter().flatten())
            .map(|(a, b)| (a - b).abs())
            .fold(0.0, f64::max);
        assert!(max < 1e-4, "{max}");
        let new_bytes = serde_json::to_vec(&compact).unwrap().len();
        let old_bytes = serde_json::to_vec(&old).unwrap().len();
        assert!(
            new_bytes * 4 < old_bytes,
            "compact {new_bytes} / old {old_bytes}"
        );
        assert_eq!(before, serde_json::to_vec(&s.checkpoint()).unwrap());
        for v in validation_directions() {
            assert!(distance(&v, &compact.calibration_direction) > 1e-3);
        }
    }
    #[test]
    fn clipping_boundary_triggers_measured_signed_fallback() {
        let cp = session().checkpoint();
        let mut o = origin(&cp.state, &cp.state.sonar_state.as_ref().unwrap().history);
        o.noise_amplitude = 0.2;
        o.controls.leak = 1.0;
        o.controls.feedback_scale = 1.0;
        let m = model_for(&o).unwrap();
        let mut rng = SplitMix64::new(o.rng_state.parse().unwrap());
        let noises: Vec<_> = (0..32).map(|_| rng.signed() * o.noise_amplitude).collect();
        let input = forcing(o.step as usize + 1, o.dt);
        let mut found = false;
        for (row, noise) in noises.iter().enumerate().filter(|(_, n)| **n > 0.05) {
            let drive = m.input_weights[row * 67 + 66]
                + input
                    .iter()
                    .enumerate()
                    .map(|(c, x)| m.input_weights[row * 67 + c] * x)
                    .sum::<f64>();
            let target = (1.0 - noise).atanh();
            let held = (target - drive) / m.input_weights[row * 67 + 18];
            if held.abs() > 5.0 {
                continue;
            }
            let mut at = o.clone();
            at.held_vector[0] = held;
            let report = scan_origin(at.clone(), true).unwrap();
            if report.fallback.is_none() {
                continue;
            }
            assert!(!report.validation.passed);
            validate_compact_sonar_report(&report).unwrap();
            let f = report.fallback.as_ref().unwrap();
            let base = first(&at, &[0.0; 48]).unwrap();
            let mut axis = vec![0.0; 48];
            axis[0] = 1.0;
            assert_eq!(
                f.positive[0],
                response(&at, &base, &axis, COMPACT_EPSILON).unwrap()
            );
            assert_eq!(
                f.negative[0],
                response(&at, &base, &axis, -COMPACT_EPSILON).unwrap()
            );
            assert!((f.positive[0][row] + f.negative[0][row]).abs() > 1e-6);
            found = true;
            break;
        }
        assert!(
            found,
            "Expected at least one exact clipping boundary to fail fresh validation"
        );
    }
    #[test]
    fn question_comparisons_measure_a_specific_counterfactual_and_unresolved_signal() {
        let mut s = session();
        for _ in 0..19 {
            s.advance().unwrap();
        }
        let cp = s.checkpoint();
        let before = serde_json::to_vec(&cp).unwrap();
        let report = question_sustained_checkpoint(&cp, SustainedSonarQuestion::State).unwrap();
        validate_sonar_question_report(&report).unwrap();
        assert!(report.unit_input.is_some());
        assert!(report.prediction_relative_error.unwrap() < 0.01);
        assert!(report.gain_over_random.unwrap() > 1.0);
        assert_eq!(
            report.origin.held_vector,
            report.alternative_origin.held_vector
        );
        assert_eq!(report.origin.rng_state, report.alternative_origin.rng_state);
        assert!(report.alternative_origin.state.iter().all(|x| *x == 0.0));
        let empty = question_sustained_checkpoint(&cp, SustainedSonarQuestion::Input).unwrap();
        assert!(empty.unit_input.is_none());
        assert!(empty.gain_over_random.is_none());
        validate_sonar_question_report(&empty).unwrap();
        assert_eq!(before, serde_json::to_vec(&s.checkpoint()).unwrap());
    }
    #[test]
    fn compact_history_and_version_specific_question_admission() {
        let mut s = session();
        for _ in 0..45 {
            s.advance().unwrap();
        }
        let cp = s.checkpoint();
        assert_eq!(cp.state.sonar_state.as_ref().unwrap().history.len(), 32);
        cp.validate().unwrap();
        for raw in [
            "body\nNEXT: SCAN_QUESTION state",
            "body\nNEXT: SCAN_QUESTION input",
            "body\nNEXT: SCAN_QUESTION recurrence",
            "body\nNEXT: PROBE_SCAN question negative",
        ] {
            assert!(actions::decision_for(s.specification(), None, raw)
                .unwrap()
                .request
                .is_some());
            let mut legacy = s.specification().clone();
            legacy.sonar.as_mut().unwrap().version = SustainedSonarVersion::ResponseScanV1;
            assert!(actions::decision_for(&legacy, None, raw)
                .unwrap()
                .request
                .is_none());
        }
        for raw in [
            "body\nNEXT: SCAN_QUESTION anything",
            "body\nNEXT: SCAN_QUESTION state now",
            "body\nNEXT: SCAN_QUESTION state\nmore",
            "body\nNEXT: NONE\nNEXT: SCAN_QUESTION state",
            "> NEXT: SCAN_QUESTION state",
            "```\nNEXT: SCAN_QUESTION state\n```",
        ] {
            assert!(
                actions::decision_for(s.specification(), None, raw)
                    .unwrap()
                    .request
                    .is_none(),
                "{raw}"
            );
        }
    }
    #[test]
    fn tampered_compact_and_question_reports_are_rejected() {
        let mut s = session();
        for _ in 0..19 {
            s.advance().unwrap();
        }
        let cp = s.checkpoint();
        let mut r = scan_compact_sustained_checkpoint(&cp).unwrap();
        r.validation.maximum_relative_error = Some(2.0);
        assert!(validate_compact_sonar_report(&r).is_err());
        let mut q = question_sustained_checkpoint(&cp, SustainedSonarQuestion::State).unwrap();
        q.alternative_origin.rng_state = "8".into();
        assert!(validate_sonar_question_report(&q).is_err());
    }
    #[test]
    fn question_probe_uses_current_origin_bound_and_separate_permission() {
        let mut s = session();
        for _ in 0..19 {
            s.advance().unwrap();
        }
        let mut cp = s.checkpoint();
        let req = SustainedActionRequest::ProbeScan {
            direction: SustainedSonarDirection::Question,
            sign: SustainedSonarSign::Negative,
        };
        assert_eq!(
            resolve_compact_probe(&cp.state, Some(&req))
                .unwrap()
                .unwrap()
                .rejection
                .as_deref(),
            Some(NO_QUESTION)
        );
        let q = question_state(&cp.state, SustainedSonarQuestion::State).unwrap();
        let id = q.id.clone();
        cp.state.sonar_state.as_mut().unwrap().latest_question = Some(Box::new(q));
        cp.state.action_state.as_mut().unwrap().controls.leak = 1.0;
        let p = resolve_compact_probe(&cp.state, Some(&req))
            .unwrap()
            .unwrap();
        assert!(p.rejection.is_none());
        assert_eq!(p.source_scan.as_ref().unwrap().id, id);
        assert_eq!(p.forecast_origin.as_ref().unwrap().controls.leak, 1.0);
        assert!(p.forecast_response_l2[0] <= SONAR_STATE_BOUND);
        validate_question_forecast(&p).unwrap();
        cp.state
            .specification
            .sonar
            .as_mut()
            .unwrap()
            .allow_live_probe = false;
        let p = resolve_compact_probe(&cp.state, Some(&req))
            .unwrap()
            .unwrap();
        assert_eq!(p.rejection.as_deref(), Some(NO_AUTHORITY));
        assert!(p.question_forecast.is_none());
        assert_eq!(norm(&p.applied_vector), 0.0);
    }
}
