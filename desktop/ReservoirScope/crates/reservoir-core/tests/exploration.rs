use reservoir_core::{exploration::*, inspect_bytes, math::*, CoreError, VerificationStatus};
use serde_json::Value;
use std::path::PathBuf;

fn fixture_path(name: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests/fixtures/exploration")
        .join(format!("{name}.json"))
}
fn fixture(name: &str) -> ExplorationRecord {
    serde_json::from_slice(&std::fs::read(fixture_path(name)).unwrap()).unwrap()
}
fn transitions() -> ExplorationRecord {
    fixture("control-transitions-u64-max")
}
fn near(a: f64, b: f64) {
    assert!((a - b).abs() < 1e-12, "{a} != {b}");
}
fn rejected(record: &ExplorationRecord) {
    assert!(matches!(record.verify(), Err(CoreError::Invalid(_))));
}

#[test]
fn retained_swift_exploration_oracles_replay_all_controls_and_spectra() {
    for (name, count, seed) in [
        ("empty-u64-max", 0, u64::MAX),
        ("quiet-defaults", 8, DEFAULT_SEED),
        ("pulsed-forcing", 32, 99),
        ("control-transitions-u64-max", 18, u64::MAX),
        ("sensory-restarts-u64-large", 6, 9_007_199_254_740_993),
    ] {
        let record = fixture(name);
        record.verify().unwrap_or_else(|e| panic!("{name}: {e}"));
        assert_eq!(record.frames.len(), count);
        assert_eq!(record.seed, seed);
        let restored = ExplorationEngine::from_record(&record).unwrap();
        assert_eq!(
            serde_json::to_value(restored.record()).unwrap(),
            serde_json::to_value(record).unwrap()
        );
    }
}

#[test]
fn exploration_inspection_preserves_exact_bytes_and_full_seed_without_codec_restrictions() {
    let original = std::fs::read(fixture_path("control-transitions-u64-max")).unwrap();
    let mut bytes = original;
    // Unknown text is not a journal reply and must not trigger codec qualification.
    bytes.splice(
        1..1,
        "\n  \"futureNote\":\"日本語\", ".as_bytes().iter().copied(),
    );
    let inspection = inspect_bytes(bytes.clone());
    assert_eq!(inspection.original_bytes, bytes);
    assert_eq!(inspection.report.status, VerificationStatus::Passed);
    assert_eq!(inspection.report.checked_steps, 18);
    assert_eq!(inspection.report.checked_turns, 0);
    assert_eq!(inspection.report.format.as_deref(), Some(FORMAT));
    assert!(!inspection.report.models_contacted);
    let record: ExplorationRecord = serde_json::from_slice(&inspection.original_bytes).unwrap();
    assert_eq!(record.seed, u64::MAX);
    assert_eq!(record.model, ReservoirModel::seeded(u64::MAX));
}

#[test]
fn constructor_defaults_are_quiet_but_missing_record_controls_are_not_defaulted() {
    let record = fixture("quiet-defaults");
    let mut engine = ExplorationEngine::default();
    for expected in &record.frames {
        assert_eq!(expected.controls, ExplorationControls::default());
        let frame = engine
            .advance(ExplorationControls::default(), false)
            .unwrap();
        assert_eq!(frame.state, vec![0.0; 32]);
        assert_eq!(frame.input, vec![0.0; 66]);
        assert!(frame.spectral.is_none());
        assert_eq!(frame.input_drive, vec![0.0; 32]);
        assert_eq!(frame.recurrent_drive, vec![0.0; 32]);
        assert_eq!(frame.bias_drive, vec![0.0; 32]);
        near(frame.time, expected.time);
    }
    let encoded = serde_json::to_value(record).unwrap();
    for key in [
        "leak",
        "recurrenceEnabled",
        "recurrenceStrength",
        "repeatInput",
        "inputStrength",
        "noiseAmplitude",
        "biasEnabled",
        "sensoryEnabled",
        "retention",
    ] {
        let mut missing = encoded.clone();
        missing["frames"][0]["controls"]
            .as_object_mut()
            .unwrap()
            .remove(key);
        assert!(
            serde_json::from_value::<ExplorationRecord>(missing).is_err(),
            "missing {key}"
        );
        let mut null = encoded.clone();
        null["frames"][0]["controls"][key] = Value::Null;
        assert!(
            serde_json::from_value::<ExplorationRecord>(null).is_err(),
            "null {key}"
        );
    }
    // Swift Optional spectral accepts an omitted field or explicit null.
    let mut explicit_null = encoded;
    explicit_null["frames"][0]["spectral"] = Value::Null;
    serde_json::from_value::<ExplorationRecord>(explicit_null)
        .unwrap()
        .verify()
        .unwrap();
}

#[test]
fn controls_reconstruct_raw_contributions_without_rewriting_source_weights() {
    let mut engine = ExplorationEngine::new(111);
    engine
        .advance(ExplorationControls::default(), true)
        .unwrap();
    let controls = ExplorationControls {
        leak: 0.4,
        recurrence_enabled: true,
        recurrence_strength: 0.7,
        input_strength: 0.6,
        noise_amplitude: 0.13,
        bias_enabled: true,
        ..Default::default()
    };
    let frame = engine.advance(controls, true).unwrap();
    let source = ReservoirModel::seeded(111);
    assert_eq!(engine.record().model, source);
    for row in 0..32 {
        let input = (0..66).fold(0.0, |sum, col| {
            sum + source.input_weights[row * 67 + col] * frame.input[col]
        });
        let recurrent = (0..32).fold(0.0, |sum, col| {
            sum + source.recurrent_weights[row * 32 + col] * 0.7 * frame.previous_state[col]
        });
        let bias = source.input_weights[row * 67 + 66];
        near(frame.input_drive[row], input);
        near(frame.recurrent_drive[row], recurrent);
        near(frame.bias_drive[row], bias);
        near(frame.proposal[row], (input + recurrent + bias).tanh());
        near(
            frame.state[row],
            (0.6 * frame.previous_state[row] + 0.4 * frame.proposal[row] + frame.noise[row])
                .clamp(-1.0, 1.0),
        );
        assert!(frame.noise[row].abs() <= 0.13);
    }
    engine.record().verify().unwrap();
}

#[test]
fn pulse_overrides_repeating_input_and_quiet_windows_follow_recorded_clock() {
    let record = fixture("pulsed-forcing");
    for frame in &record.frames {
        let expected = if frame.pulse {
            forcing(1, DT)
        } else {
            forcing(frame.step, DT)
        };
        for (actual, expected) in frame.input.iter().zip(expected) {
            near(*actual, expected * frame.controls.input_strength);
        }
        assert!(frame.input[16..].iter().all(|x| *x == 0.0));
        if (13..=30).contains(&frame.step) {
            assert!(frame.input.iter().all(|x| *x == 0.0));
        }
    }
    assert_ne!(record.frames[0].input, record.frames[1].input);
    assert!(record.frames[30].input.iter().any(|x| *x != 0.0));
    for coordinate in 0..66 {
        near(
            record.frames[31].input[coordinate],
            record.frames[0].input[coordinate] * 0.25,
        );
    }
}

#[test]
fn recurrence_enabled_and_strength_change_only_the_current_drive() {
    let mut off = ExplorationEngine::new(42);
    let mut on = ExplorationEngine::new(42);
    let quiet = ExplorationControls::default();
    let recurrent = ExplorationControls {
        recurrence_enabled: true,
        ..Default::default()
    };
    let initial = off.advance(quiet.clone(), true).unwrap();
    assert_eq!(
        initial.state,
        on.advance(recurrent.clone(), true).unwrap().state
    );
    let a = off.advance(quiet, false).unwrap();
    let b = on.advance(recurrent, false).unwrap();
    assert!(a.recurrent_drive.iter().all(|x| *x == 0.0));
    assert!(b.recurrent_drive.iter().any(|x| x.abs() > 1e-12));
    for (state, previous) in a.state.iter().zip(initial.state) {
        near(*state, 0.35 * previous);
    }
    assert_ne!(a.state, b.state);
    let disabled = on
        .advance(
            ExplorationControls {
                recurrence_enabled: true,
                recurrence_strength: 0.0,
                ..Default::default()
            },
            false,
        )
        .unwrap();
    assert!(disabled.recurrent_drive.iter().all(|x| *x == 0.0));
}

#[test]
fn zero_amplitude_consumes_rng_and_invalid_controls_never_advance_it() {
    let mut quiet = ExplorationEngine::new(8);
    let mut noisy = ExplorationEngine::new(8);
    quiet
        .advance(ExplorationControls::default(), false)
        .unwrap();
    noisy
        .advance(
            ExplorationControls {
                noise_amplitude: 0.2,
                ..Default::default()
            },
            false,
        )
        .unwrap();
    let controls = ExplorationControls {
        leak: 0.0,
        noise_amplitude: 0.1,
        ..Default::default()
    };
    let mut bad = controls.clone();
    bad.input_strength = f64::NAN;
    assert!(quiet.advance(bad, true).is_err());
    assert_eq!(quiet.frames().len(), 1);
    let a = quiet.advance(controls.clone(), true).unwrap();
    let b = noisy.advance(controls, false).unwrap();
    assert_eq!(a.noise, b.noise);
    assert_eq!(a.state, a.noise);
    let full = quiet
        .advance(
            ExplorationControls {
                leak: 1.0,
                ..Default::default()
            },
            true,
        )
        .unwrap();
    assert_eq!(full.state, full.proposal);
}

#[test]
fn field_restarts_and_valid_degenerate_bases_remain_valid_evidence() {
    let mut record = fixture("sensory-restarts-u64-large");
    assert!(record.frames[3].spectral.is_none());
    // First observed frame is silent identity decay; all eigenvalues coincide.
    let s = record.frames[0].spectral.as_mut().unwrap();
    s.eigenvectors.fill(0.0);
    for mode in 0..32 {
        s.eigenvectors[mode * 32 + mode] = 1.0;
    }
    let c = std::f64::consts::FRAC_1_SQRT_2;
    s.eigenvectors[0] = c;
    s.eigenvectors[1] = c;
    s.eigenvectors[32] = -c;
    s.eigenvectors[33] = c;
    record.verify().unwrap();
    let restored = ExplorationEngine::from_record(&record).unwrap();
    assert_eq!(
        restored.frames()[0].spectral.as_ref().unwrap().eigenvectors,
        s_vectors(&record, 0)
    );
    let mut fresh = ExplorationEngine::new(record.seed);
    let reset = fresh
        .advance(record.frames[4].controls.clone(), record.frames[4].pulse)
        .unwrap();
    let reset_covariance = reset.spectral.unwrap().covariance;
    let retained_covariance = &record.frames[4].spectral.as_ref().unwrap().covariance;
    // This retained Swift fixture is cross-language evidence, not a bitwise
    // oracle for platform libm operations. Use the existing test tolerance;
    // production verifier tolerances and original fixture bytes are unchanged.
    assert_eq!(retained_covariance.len(), reset_covariance.len());
    for (&retained, &computed) in retained_covariance.iter().zip(&reset_covariance) {
        near(retained, computed);
    }

    // Keep a stricter reset invariant within one runtime: once an off step has
    // cleared the sensory field, its next pulse must match a fresh field exactly.
    let mut restarted = ExplorationEngine::new(record.seed);
    for frame in &record.frames[..4] {
        restarted
            .advance(frame.controls.clone(), frame.pulse)
            .unwrap();
    }
    assert!(restarted.frames().last().unwrap().spectral.is_none());
    let restarted_frame = restarted
        .advance(record.frames[4].controls.clone(), record.frames[4].pulse)
        .unwrap();
    assert_eq!(restarted_frame.input, reset.input);
    assert_eq!(
        restarted_frame.spectral.unwrap().covariance,
        reset_covariance
    );
    // Arbitrary sign changes are valid even without a repeated eigenvalue.
    let vector = &mut record.frames[4].spectral.as_mut().unwrap().eigenvectors;
    for value in &mut vector[..32] {
        *value = -*value;
    }
    record.verify().unwrap();
}
fn s_vectors(record: &ExplorationRecord, index: usize) -> Vec<f64> {
    record.frames[index]
        .spectral
        .as_ref()
        .unwrap()
        .eigenvectors
        .clone()
}

#[test]
fn every_exploration_link_rejects_independent_mutations() {
    type Mutation = Box<dyn Fn(&mut ExplorationRecord)>;
    let original = transitions();
    let mutations: Vec<(&str, Mutation)> = vec![
        ("seed", Box::new(|r| r.seed -= 1)),
        (
            "source weight exactness",
            Box::new(|r| {
                r.model.input_weights[0] = f64::from_bits(r.model.input_weights[0].to_bits() ^ 1)
            }),
        ),
        (
            "recurrent weight",
            Box::new(|r| r.model.recurrent_weights[0] += 0.1),
        ),
        (
            "projection exactness",
            Box::new(|r| {
                r.projection_weights[0] = f64::from_bits(r.projection_weights[0].to_bits() ^ 1)
            }),
        ),
        ("step", Box::new(|r| r.frames[0].step = 0)),
        ("clock", Box::new(|r| r.frames[0].time += 0.01)),
        ("input", Box::new(|r| r.frames[0].input[0] += 0.1)),
        (
            "previous state",
            Box::new(|r| r.frames[0].previous_state[0] += 0.1),
        ),
        (
            "input drive",
            Box::new(|r| r.frames[0].input_drive[0] += 0.1),
        ),
        (
            "recurrent drive",
            Box::new(|r| r.frames[4].recurrent_drive[0] += 0.1),
        ),
        ("bias", Box::new(|r| r.frames[4].bias_drive[0] += 0.1)),
        ("proposal", Box::new(|r| r.frames[0].proposal[0] += 0.1)),
        ("state", Box::new(|r| r.frames[0].state[0] += 0.1)),
        (
            "state clip",
            Box::new(|r| r.frames[0].state[0] = 1.00000001),
        ),
        ("noise", Box::new(|r| r.frames[9].noise[0] += 0.1)),
        ("leak", Box::new(|r| r.frames[0].controls.leak = 0.65)),
        (
            "recurrence enabled",
            Box::new(|r| r.frames[4].controls.recurrence_enabled = false),
        ),
        (
            "recurrence strength",
            Box::new(|r| r.frames[4].controls.recurrence_strength = 0.3),
        ),
        (
            "repeat input",
            Box::new(|r| r.frames[0].controls.repeat_input = false),
        ),
        (
            "input strength",
            Box::new(|r| r.frames[0].controls.input_strength = 0.8),
        ),
        (
            "noise amplitude",
            Box::new(|r| r.frames[9].controls.noise_amplitude = 0.01),
        ),
        (
            "bias enabled",
            Box::new(|r| r.frames[4].controls.bias_enabled = false),
        ),
        ("pulse", Box::new(|r| r.frames[7].pulse = false)),
        (
            "sensory enabled",
            Box::new(|r| r.frames[1].controls.sensory_enabled = false),
        ),
        (
            "retention",
            Box::new(|r| r.frames[1].controls.retention = 0.9),
        ),
        (
            "field vector",
            Box::new(|r| r.frames[1].spectral.as_mut().unwrap().field_vector[0] += 0.1),
        ),
        (
            "covariance",
            Box::new(|r| r.frames[1].spectral.as_mut().unwrap().covariance[0] += 0.1),
        ),
        (
            "eigenvalues",
            Box::new(|r| r.frames[1].spectral.as_mut().unwrap().eigenvalues[0] += 0.1),
        ),
        (
            "eigenbasis",
            Box::new(|r| r.frames[1].spectral.as_mut().unwrap().eigenvectors[0] += 0.1),
        ),
        (
            "entropy",
            Box::new(|r| r.frames[1].spectral.as_mut().unwrap().entropy += 0.1),
        ),
        (
            "head",
            Box::new(|r| r.frames[1].spectral.as_mut().unwrap().head_share += 0.1),
        ),
        (
            "shoulder",
            Box::new(|r| r.frames[1].spectral.as_mut().unwrap().shoulder_share += 0.1),
        ),
        (
            "tail",
            Box::new(|r| r.frames[1].spectral.as_mut().unwrap().tail_share += 0.1),
        ),
        (
            "negative eigenvalue",
            Box::new(|r| r.frames[1].spectral.as_mut().unwrap().eigenvalues[31] = -1e-15),
        ),
        (
            "field dimension",
            Box::new(|r| r.frames[1].spectral.as_mut().unwrap().dimension = 31),
        ),
        (
            "noise shape",
            Box::new(|r| {
                r.frames[0].noise.pop();
            }),
        ),
        (
            "spectral absence",
            Box::new(|r| r.frames[1].spectral = None),
        ),
    ];
    for (label, mutation) in mutations {
        let mut record = original.clone();
        mutation(&mut record);
        assert!(
            matches!(record.verify(), Err(CoreError::Invalid(_))),
            "{label} unexpectedly verified"
        );
    }
}

#[test]
fn inactive_controls_still_validate_without_inventing_a_causal_effect() {
    let mut quiet = fixture("quiet-defaults");
    quiet.frames[0].controls.recurrence_strength = 0.5;
    quiet.frames[0].controls.input_strength = 0.25;
    quiet.frames[0].controls.retention = 0.82;
    quiet.verify().unwrap();
    for value in [f64::NAN, f64::INFINITY, -0.01, 1.01] {
        let mut record = quiet.clone();
        record.frames[0].controls.recurrence_strength = value;
        rejected(&record);
    }
    let mut record = quiet.clone();
    record.frames[0].controls.retention = 0.8;
    rejected(&record);
    let mut record = quiet;
    record.frames[0].controls.noise_amplitude = 0.201;
    rejected(&record);
}

#[test]
fn tiny_negative_eigenvalues_fail_even_inside_numerical_tolerance() {
    let mut engine = ExplorationEngine::new(10);
    for _ in 0..100 {
        engine
            .advance(
                ExplorationControls {
                    sensory_enabled: true,
                    retention: 0.82,
                    ..Default::default()
                },
                false,
            )
            .unwrap();
    }
    let mut record = engine.record();
    record.verify().unwrap();
    let spectrum = record.frames.last_mut().unwrap().spectral.as_mut().unwrap();
    assert!(spectrum.eigenvalues[31] < 2e-7);
    spectrum.eigenvalues[31] = -1e-15;
    rejected(&record);
}

#[test]
fn final_retained_covariance_must_also_satisfy_swift_resume_symmetry() {
    let mut record = fixture("sensory-restarts-u64-large");
    // Intermediate measurements use the numerical tolerance. Swift recreates the
    // final field from retained covariance and additionally enforces 1e-10 symmetry.
    record.frames[1].spectral.as_mut().unwrap().covariance[1] += 1e-8;
    record.verify().unwrap();
    record
        .frames
        .last_mut()
        .unwrap()
        .spectral
        .as_mut()
        .unwrap()
        .covariance[1] += 1e-8;
    rejected(&record);
}

#[test]
fn verified_resume_retains_history_state_field_and_rng() {
    let imported = transitions();
    let mut uninterrupted = ExplorationEngine::new(imported.seed);
    for frame in &imported.frames {
        uninterrupted
            .advance(frame.controls.clone(), frame.pulse)
            .unwrap();
    }
    let mut restored = ExplorationEngine::from_record(&imported).unwrap();
    for step in 0..8 {
        let controls = ExplorationControls {
            recurrence_enabled: true,
            repeat_input: true,
            noise_amplitude: 0.03,
            sensory_enabled: step < 4,
            retention: 0.96,
            ..Default::default()
        };
        let a = uninterrupted.advance(controls.clone(), step == 3).unwrap();
        let b = restored.advance(controls, step == 3).unwrap();
        assert_eq!(a.input, b.input);
        assert_eq!(a.noise, b.noise);
        for (a, b) in a.state.iter().zip(&b.state) {
            near(*a, *b);
        }
        if let (Some(a), Some(b)) = (a.spectral, b.spectral) {
            for (a, b) in a.covariance.iter().zip(&b.covariance) {
                near(*a, *b);
            }
        }
    }
    restored.record().verify().unwrap();
    let mut close = imported;
    let last = close.frames.last_mut().unwrap();
    last.state[0] += 1e-8;
    close.verify().unwrap();
    let retained_state = last_state(&close);
    let mut resumed = ExplorationEngine::from_record(&close).unwrap();
    assert_eq!(
        resumed
            .advance(ExplorationControls::default(), false)
            .unwrap()
            .previous_state,
        retained_state
    );
}
fn last_state(record: &ExplorationRecord) -> Vec<f64> {
    record.frames.last().unwrap().state.clone()
}

#[test]
fn exploration_is_bounded_empty_valid_and_unknown_family_is_incomplete() {
    let mut engine = ExplorationEngine::new(1);
    engine.record().verify().unwrap();
    for _ in 0..MAXIMUM_STEPS {
        engine
            .advance(ExplorationControls::default(), false)
            .unwrap();
    }
    engine.record().verify().unwrap();
    assert!(engine
        .advance(ExplorationControls::default(), true)
        .is_err());
    assert_eq!(engine.frames().len(), MAXIMUM_STEPS);
    let mut too_long = engine.record();
    too_long.frames.push(too_long.frames[0].clone());
    rejected(&too_long);
    let mut unknown = fixture("empty-u64-max");
    unknown.format = "essentials-exploration-v9".into();
    assert!(matches!(unknown.verify(), Err(CoreError::Unsupported(_))));
}
