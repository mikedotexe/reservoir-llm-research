use reservoir_core::{math::SplitMix64, regulation::*, CoreError};
use std::{path::PathBuf, sync::OnceLock};
fn canonical_path() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../../../essentials/examples/portable/example-regulation-controller.json")
}
fn canonical() -> &'static RegulationExampleRecord {
    static RECORD: OnceLock<RegulationExampleRecord> = OnceLock::new();
    RECORD
        .get_or_init(|| serde_json::from_slice(&std::fs::read(canonical_path()).unwrap()).unwrap())
}
fn rejected(record: &RegulationExampleRecord) {
    assert!(matches!(record.verify(), Err(CoreError::Invalid(_))));
}
#[test]
fn retained_swift_controller_replays_all_1200_arm_observations() {
    let r = canonical();
    r.verify().unwrap();
    assert_eq!(r.checked_steps(), 1200);
    assert_eq!(r.frames.len(), 600);
    let mut rng = SplitMix64::new(42);
    for frame in &r.frames {
        for x in &frame.input {
            assert_eq!(*x, rng.signed());
        }
    }
    for pair in r.frames.windows(2) {
        assert_eq!(
            pair[1].regulated.retention_used,
            pair[0]
                .regulated
                .control
                .as_ref()
                .unwrap()
                .applied_retention
        );
    }
    assert!(r
        .frames
        .iter()
        .all(|f| f.baseline.retention_used == 0.955 && f.baseline.control.is_none()));
    assert!(r.summary.regulated_mean_absolute_error < r.summary.baseline_mean_absolute_error);
}
#[test]
fn specification_missing_and_null_fields_keep_native_defaults_and_notes_are_utf8_bounded() {
    let default = RegulationExampleSpecification::default();
    for value in [
        serde_json::json!({}),
        serde_json::json!({"fixture":null,"fieldSeed":null,"inputSeed":null,"steps":null,"dt":null,"initialRetention":null,"targetFillPercent":null,"evaluationFirstStep":null,"evaluationLastStep":null,"question":null,"expectedDifference":null,"alternativeExplanation":null,"stoppingPoint":null}),
    ] {
        let spec: RegulationExampleSpecification = serde_json::from_value(value).unwrap();
        assert_eq!(spec, default);
        spec.validate().unwrap();
    }
    let mut spec = default.clone();
    spec.question = " ".into();
    spec.validate().unwrap();
    spec.question = "é".repeat(2048);
    spec.validate().unwrap();
    spec.question.push('x');
    assert!(spec.validate().is_err());
    spec.question = String::new();
    assert!(spec.validate().is_err());
    for key in [
        "fieldSeed",
        "inputSeed",
        "steps",
        "evaluationFirstStep",
        "evaluationLastStep",
    ] {
        let mut value = serde_json::to_value(&default).unwrap();
        value[key] = serde_json::json!(u64::MAX);
        let changed: RegulationExampleSpecification = serde_json::from_value(value).unwrap();
        assert!(changed.validate().is_err(), "{key}");
    }
    for key in ["dt", "initialRetention", "targetFillPercent"] {
        let mut value = serde_json::to_value(&default).unwrap();
        value[key] = serde_json::json!(0.1);
        let changed: RegulationExampleSpecification = serde_json::from_value(value).unwrap();
        assert!(changed.validate().is_err(), "{key}");
    }
}
#[test]
fn prefix_window_has_no_early_final_result_and_rewinds_without_future_state() {
    let record = canonical();
    for cursor in [0, 1, 299, 300] {
        assert!(record.window_evidence(cursor).is_none());
    }
    for (cursor, count, last, complete) in [
        (301, 1, 301, false),
        (450, 150, 450, false),
        (599, 299, 599, false),
        (600, 300, 600, true),
        (usize::MAX, 300, 600, true),
    ] {
        let evidence = record.window_evidence(cursor).unwrap();
        assert_eq!(
            (
                evidence.count,
                evidence.first_step,
                evidence.last_step,
                evidence.is_complete
            ),
            (count, 301, last, complete)
        );
        let selected = &record.frames[300..last];
        let n = selected.len() as f64;
        let baseline = selected
            .iter()
            .fold(0.0, |sum, f| sum + (f.baseline.fill_percent - 68.0).abs())
            / n;
        let regulated = selected
            .iter()
            .fold(0.0, |sum, f| sum + (f.regulated.fill_percent - 68.0).abs())
            / n;
        assert_eq!(evidence.baseline_mean_absolute_error, baseline);
        assert_eq!(evidence.regulated_mean_absolute_error, regulated);
    }
    let complete = record.window_evidence(600).unwrap();
    assert_eq!(
        complete.baseline_mean_absolute_error,
        record.summary.baseline_mean_absolute_error
    );
    assert_eq!(
        complete.regulated_mean_absolute_error,
        record.summary.regulated_mean_absolute_error
    );
    let first = record.window_evidence(301).unwrap();
    assert_eq!(first.count, 1);
    assert!(!first.is_complete);
    assert!(record.window_evidence(300).is_none());
    // Poison only future values and the whole-window summary: visible prefix
    // evaluation must read neither. This copy is intentionally not a valid record.
    let mut poisoned = record.clone();
    poisoned.summary.baseline_mean_absolute_error = 1e30;
    for frame in &mut poisoned.frames[301..] {
        frame.baseline.fill_percent = 1e20;
        frame.regulated.fill_percent = -1e20;
    }
    assert_eq!(poisoned.window_evidence(301), Some(first));
}
#[test]
fn complete_record_and_control_presence_are_required_not_partial_record_success() {
    let mut r = canonical().clone();
    r.frames.truncate(599);
    assert!(r.validate_structure().is_err());
    let mut r = canonical().clone();
    r.frames[599].step = 599;
    assert!(r.validate_structure().is_err());
    let mut r = canonical().clone();
    r.frames[0].regulated.control = None;
    assert!(r.validate_structure().is_err());
    let mut r = canonical().clone();
    r.frames[0].baseline.control = r.frames[0].regulated.control.clone();
    assert!(r.validate_structure().is_err());
    let mut r = canonical().clone();
    r.frames[0].input.pop();
    assert!(r.validate_structure().is_err());
    let mut r = canonical().clone();
    r.frames[0].baseline.spectral.eigenvalues[31] = -1e-15;
    assert!(r.validate_structure().is_err());
}
#[test]
fn seeded_projection_is_exact_and_input_draws_cannot_be_swapped() {
    let mut r = canonical().clone();
    let old = r.projection_weights[0];
    r.projection_weights[0] = f64::from_bits(old.to_bits() + 1);
    rejected(&r);
    let mut r = canonical().clone();
    r.frames[0].input.swap(0, 1);
    rejected(&r);
    let mut r = canonical().clone();
    r.specification.input_seed = 43;
    rejected(&r);
    let mut r = canonical().clone();
    r.specification.fixture = "other-input".into();
    rejected(&r);
}
#[test]
fn controller_scalar_tolerance_is_one_e_minus_eight_not_spectral_tolerance() {
    let mut r = canonical().clone();
    r.frames[0].time += 5e-9;
    r.validate_structure().unwrap();
    r.frames[0].time += 5e-8;
    assert!(r.validate_structure().is_err());
    let mut r = canonical().clone();
    r.frames[0].regulated.retention_used += 5e-8;
    rejected(&r);
    let mut r = canonical().clone();
    r.frames[0]
        .regulated
        .control
        .as_mut()
        .unwrap()
        .applied_retention += 5e-8;
    rejected(&r);
    let mut r = canonical().clone();
    r.frames[0].regulated.control.as_mut().unwrap().integral = f64::NAN;
    rejected(&r);
}
#[test]
fn next_step_timing_fill_and_controller_state_mutations_fail() {
    let mut r = canonical().clone();
    r.frames[0].regulated.retention_used = r.frames[0]
        .regulated
        .control
        .as_ref()
        .unwrap()
        .applied_retention;
    rejected(&r);
    let mut r = canonical().clone();
    r.frames[1].regulated.retention_used = 0.955;
    rejected(&r);
    let mut r = canonical().clone();
    r.frames[0].regulated.fill_percent += 0.01;
    rejected(&r);
    let mut r = canonical().clone();
    r.frames[0].regulated.control.as_mut().unwrap().error += 0.01;
    rejected(&r);
    let mut r = canonical().clone();
    r.frames[0]
        .regulated
        .control
        .as_mut()
        .unwrap()
        .requested_retention -= 0.01;
    rejected(&r);
}
#[test]
fn spectral_geometry_rejects_corruption_but_allows_basis_sign_gauge() {
    let mut r = canonical().clone();
    r.frames[0].baseline.spectral.field_vector[0] += 0.01;
    rejected(&r);
    let mut r = canonical().clone();
    r.frames[0].regulated.spectral.covariance[0] += 0.01;
    rejected(&r);
    let mut r = canonical().clone();
    r.frames[0].regulated.spectral.eigenvectors[0] += 0.01;
    rejected(&r);
    let mut r = canonical().clone();
    for x in &mut r.frames[0].regulated.spectral.eigenvectors[0..32] {
        *x = -*x;
    }
    r.verify().unwrap();
}
#[test]
fn summary_window_and_retained_aggregate_mutations_fail() {
    let mut r = canonical().clone();
    r.summary.evaluation_count = 299;
    rejected(&r);
    let mut r = canonical().clone();
    r.summary.evaluation_first_step = 300;
    rejected(&r);
    let mut r = canonical().clone();
    r.summary.regulated_mean_absolute_error += 0.01;
    rejected(&r);
    let mut r = canonical().clone();
    r.summary.regulated_minimum_retention = 0.9;
    rejected(&r);
}
