use reservoir_core::{
    codec, inspect_bytes, math::*, stage::*, verify_bytes, CoreError, VerificationStatus,
};
use std::path::PathBuf;

fn repository() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../..")
}
fn small(stage: u8) -> StageRecord {
    run_scripted(RunSpecification {
        stage,
        steps: 10,
        turn_every: 3,
        noise_amplitude: 0.012,
        ..Default::default()
    })
    .unwrap()
}
fn assert_near(a: f64, b: f64) {
    assert!((a - b).abs() < 1e-12, "{a} != {b}");
}

#[test]
fn swift_known_rng_and_hand_recurrence_vectors() {
    let mut rng = SplitMix64::new(0);
    assert_eq!(rng.next_u64(), 0xE220A8397B1DCDAF);
    assert_eq!(rng.next_u64(), 0x6E789E6AA1B965F4);
    let weights = ReservoirModel::seeded(42);
    assert_eq!(weights, ReservoirModel::seeded(42));
    assert!(weights.recurrent_weights.chunks(32).all(|row| row
        .iter()
        .map(|x| x.abs())
        .sum::<f64>()
        <= 0.9 + 1e-12));
    let model = ReservoirModel {
        node_count: 2,
        input_count: 1,
        recurrent_weights: vec![0.0, 0.5, -0.25, 0.0],
        input_weights: vec![0.8, 0.1, -0.3, 0.2],
    };
    let mut engine = ReservoirEngine::new(model, 0.4, Some(vec![0.2, -0.4])).unwrap();
    let state = engine.step(&[0.5], &[0.01, -0.02]).unwrap();
    assert_near(state[0], 0.6 * 0.2 + 0.4 * 0.3_f64.tanh() + 0.01);
    assert_near(state[1], 0.6 * -0.4 + 0.4 * 0.0_f64.tanh() - 0.02);
    let before = engine.state.clone();
    assert!(engine.step(&[f64::NAN], &[]).is_err());
    assert_eq!(before, engine.state);
    assert_eq!(engine.step(&[0.0], &[10.0, -10.0]).unwrap(), [1.0, -1.0]);
}

#[test]
fn rank_one_silence_degeneracy_and_eigenvector_meaning() {
    let mut field = SensoryField::new(2, 2, vec![1.0, 0.0, 0.0, 1.0], None).unwrap();
    let measured = field.step(&[1.0, 0.0], 0.5).unwrap();
    assert_near(measured.field_vector[0], 2.0_f64.sqrt());
    assert_near(measured.covariance[0], 1.5);
    assert_near(measured.covariance[3], 0.5);
    assert_near(measured.eigenvalues[0], 1.5);
    verify_eigenvectors(&measured).unwrap();
    let quiet = field.step(&[0.0, 0.0], 0.5).unwrap();
    assert_near(quiet.covariance[0], 0.75);
    assert_eq!(quiet.field_vector, [0.0, 0.0]);
    let mut identity = SensoryField::seeded(1);
    let mut degenerate = identity.step(&[0.0; 66], 0.95).unwrap();
    verify_eigenvectors(&degenerate).unwrap();
    // A valid sign change in retained evidence remains valid.
    for x in &mut degenerate.eigenvectors[..32] {
        *x = -*x;
    }
    verify_eigenvectors(&degenerate).unwrap();
    degenerate.eigenvectors[0] += 0.1;
    assert!(verify_eigenvectors(&degenerate).is_err());
}

#[test]
fn fill_and_controller_swift_vectors() {
    let flat = spectral_summary(&[1.0; 32]);
    assert_near(flat.0, 1.0);
    assert_near(flat.1, 0.125);
    assert_near(flat.2, 0.25);
    assert_near(flat.3, 0.625);
    let mut spectrum = [0.0; 32];
    spectrum[..16].fill(1.0);
    assert_near(ReducedFill::default().update(&spectrum, 1.0 / 3.0), 0.05);
    spectrum.fill(0.0);
    spectrum[0] = 32.0;
    assert_near(ReducedFill::default().update(&spectrum, 1.0 / 3.0), 0.004);
    assert_near(
        RetentionController::new(0.955)
            .unwrap()
            .update(90.0)
            .applied_retention,
        0.945,
    );
    assert_near(
        RetentionController::new(0.955)
            .unwrap()
            .update(20.0)
            .applied_retention,
        0.965,
    );
    assert_near(
        RetentionController::new(0.955)
            .unwrap()
            .update(69.0)
            .applied_retention,
        0.955,
    );
    assert!(RetentionController::new(f64::NAN).is_err());
}

#[test]
fn retained_swift_ascii_codec_oracle_vectors_match() {
    let fixture: serde_json::Value =
        serde_json::from_str(include_str!("fixtures/ascii-codec-vectors.json")).unwrap();
    for vector in fixture["vectors"].as_array().unwrap() {
        let text = vector["text"].as_str().unwrap();
        let actual = codec::encode(text).unwrap();
        for (index, expected) in vector["features"].as_array().unwrap().iter().enumerate() {
            assert!(
                (actual[index] - expected.as_f64().unwrap()).abs() < 1e-12,
                "ASCII codec mismatch in feature {index} for {text:?}: {} vs {expected}",
                actual[index]
            );
        }
    }
}

#[test]
fn all_tracked_swift_stage_records_pass_independent_rust_verification() {
    for stage in 1..=4 {
        let path = repository().join(format!("essentials/examples/essentials-stage-{stage}.json"));
        let bytes = std::fs::read(&path).unwrap();
        let result = inspect_bytes(bytes.clone());
        assert_eq!(
            result.report.status,
            VerificationStatus::Passed,
            "{}: {:?}",
            path.display(),
            result.report.diagnostics
        );
        assert_eq!(result.report.checked_steps, 300);
        assert_eq!(result.report.checked_turns, if stage == 1 { 0 } else { 9 });
        assert!(!result.report.models_contacted);
        assert_eq!(result.original_bytes, bytes);
    }
}

#[test]
fn each_scientific_link_rejects_independent_mutations() {
    let original = small(4);
    type Mutation = Box<dyn Fn(&mut StageRecord)>;
    let mutations: Vec<Mutation> = vec![
        Box::new(|r| r.model.recurrent_weights[0] += 0.1),
        Box::new(|r| r.model.input_weights[0] += 0.1),
        Box::new(|r| r.projection_weights[0] += 0.1),
        Box::new(|r| r.frames[0].input[0] += 0.1),
        Box::new(|r| r.frames[0].state[0] += 0.1),
        Box::new(|r| r.frames[0].noise[0] += 0.1),
        Box::new(|r| r.frames[0].spectral.as_mut().unwrap().covariance[0] += 0.1),
        Box::new(|r| r.frames[0].spectral.as_mut().unwrap().eigenvalues[0] += 0.1),
        Box::new(|r| r.frames[0].spectral.as_mut().unwrap().eigenvectors[0] += 0.1),
        Box::new(|r| r.frames[0].control.as_mut().unwrap().applied_retention += 0.01),
        Box::new(|r| r.frames[0].fill_percent = None),
        Box::new(|r| r.turns[0].prompt.push('!')),
        Box::new(|r| r.turns[0].application_step = Some(3)),
        Box::new(|r| r.turns[0].encoded_features.as_mut().unwrap()[0] += 0.1),
        Box::new(|r| r.turns[0].semantic_vector.as_mut().unwrap()[0] += 0.1),
        Box::new(|r| {
            r.turns.remove(0);
        }),
    ];
    for (index, change) in mutations.into_iter().enumerate() {
        let mut mutated = original.clone();
        change(&mut mutated);
        assert!(
            matches!(mutated.verify(), Err(CoreError::Invalid(_))),
            "Mutation {index} unexpectedly verified"
        );
    }
}

#[test]
fn full_u64_seed_and_unknown_bytes_roundtrip_without_javascript() {
    for seed in [9_007_199_254_740_993, u64::MAX] {
        let record = run_scripted(RunSpecification {
            seed,
            steps: 2,
            ..Default::default()
        })
        .unwrap();
        let mut bytes = serde_json::to_vec(&record).unwrap();
        bytes.insert(1, b' ');
        bytes.insert(2, b'\n');
        bytes.splice(
            1..1,
            br#""futureNote":{"text":"retained exactly"},"#.iter().copied(),
        );
        let inspection = inspect_bytes(bytes.clone());
        assert_eq!(inspection.report.status, VerificationStatus::Passed);
        assert_eq!(inspection.stage_record.unwrap().specification.seed, seed);
        assert_eq!(inspection.original_bytes, bytes);
    }
}

#[test]
fn unsupported_family_and_unicode_are_incomplete_not_passed() {
    for bytes in [
        br#"{"format":"future-actions-v4"}"#.as_slice(),
        br#"{"format":"future-family"}"#,
    ] {
        assert_eq!(verify_bytes(bytes).status, VerificationStatus::Incomplete);
    }
    assert_eq!(verify_bytes(b"not json").status, VerificationStatus::Failed);
    let mut record = small(3);
    record.turns[0].reply = Some("A retained thought \u{10ffff}".into());
    record.turns[0].raw_reply = record.turns[0].reply.clone();
    let bytes = serde_json::to_vec(&record).unwrap();
    assert_eq!(verify_bytes(&bytes).status, VerificationStatus::Incomplete);
    assert_eq!(inspect_bytes(bytes.clone()).original_bytes, bytes);
    assert!(matches!(
        codec::encode("a\u{301}\u{308}\u{30b}"),
        Err(CoreError::Unsupported(_))
    ));
}

#[test]
fn stopped_failed_and_provider_records_are_verified_offline() {
    let mut provider = small(3);
    provider.specification.language = LanguageConfiguration {
        backend: LanguageKind::Ollama,
        endpoint: Some("http://127.0.0.1:1".into()),
        model: Some("retained-only".into()),
        context_tokens: Some(4096),
        response_format: None,
        temperature: None,
        thinking: None,
    };
    for turn in &mut provider.turns {
        turn.backend = "ollama".into();
        turn.model = Some("retained-only".into());
    }
    provider.verify().unwrap();
    assert!(matches!(
        run_scripted(provider.specification.clone()),
        Err(CoreError::Unsupported(_))
    ));
    provider.frames.truncate(3);
    provider.turns.truncate(1);
    provider.status = RunStatus::Stopped;
    let turn = &mut provider.turns[0];
    turn.status = TurnStatus::Cancelled;
    turn.reply = None;
    turn.raw_reply = None;
    turn.encoded_features = None;
    turn.semantic_vector = None;
    turn.application_step = None;
    turn.failure = Some("Cancelled by user".into());
    provider.verify().unwrap();
    provider.status = RunStatus::Failed;
    provider.failure = Some("Recorded timeout".into());
    provider.turns[0].status = TurnStatus::Failed;
    provider.turns[0].failure = provider.failure.clone();
    provider.verify().unwrap();
    provider.turns[0].application_step = Some(4);
    assert!(provider.verify().is_err());
}

#[test]
fn recipe_and_endpoint_bounds_fail_closed() {
    let mut spec = RunSpecification {
        steps: 3001,
        ..Default::default()
    };
    assert!(spec.validate().is_err());
    spec.steps = 1;
    for endpoint in [
        "http://example.com:11434",
        "http://localhost",
        "http://127.0.0.1:80/path",
        "http://user@localhost:80",
        "http://localhost:80?x=1",
        "http://127.1:1234",
        "http://2130706433:1234",
        "http://@localhost:1234",
        "http://local%68ost:1234",
        "http://localhost:1234/.",
        "http://localhost:1234/%2e",
        "http://localhost:1234/a/../",
        "http://localhost:1234/%5c",
    ] {
        spec.language = LanguageConfiguration {
            backend: LanguageKind::Ollama,
            endpoint: Some(endpoint.into()),
            model: Some("model".into()),
            context_tokens: None,
            response_format: None,
            temperature: None,
            thinking: None,
        };
        assert!(spec.validate().is_err(), "accepted {endpoint}");
    }
    for endpoint in [
        "http://localhost:80",
        "http://127.0.0.1:11434/",
        "http://[::1]:1234",
        "http://localhost:1234///",
        "http://localhost:1234/%2F",
        "http://localhost:65536",
        "http://localhost:9999999999",
    ] {
        spec.language.endpoint = Some(endpoint.into());
        spec.validate().unwrap();
    }
}

#[test]
fn swift_decode_if_present_defaults_include_explicit_null() {
    let missing: RunSpecification = serde_json::from_str(r#"{"stage":1}"#).unwrap();
    let nulls: RunSpecification = serde_json::from_str(r#"{"stage":1,"seed":null,"steps":null,"dt":null,"turnEvery":null,"noiseAmplitude":null,"leak":null,"initialRetention":null,"regulationEnabled":null,"language":null}"#).unwrap();
    assert_eq!(
        serde_json::to_value(missing).unwrap(),
        serde_json::to_value(nulls).unwrap()
    );
    assert!(serde_json::from_str::<RunSpecification>(r#"{"stage":null}"#).is_err());
}

#[test]
fn cli_reports_passed_failed_and_incomplete_with_distinct_exit_codes() {
    let binary = env!("CARGO_BIN_EXE_reservoir-core");
    let pass = std::process::Command::new(binary)
        .args([
            "verify",
            repository()
                .join("essentials/examples/essentials-stage-1.json")
                .to_str()
                .unwrap(),
            "--json",
        ])
        .output()
        .unwrap();
    assert_eq!(pass.status.code(), Some(0));
    let pass: serde_json::Value = serde_json::from_slice(&pass.stdout).unwrap();
    assert_eq!(pass["status"], "passed");
    assert_eq!(pass["modelsContacted"], false);
    let future = std::env::temp_dir().join(format!(
        "reservoir-future-format-{}.json",
        std::process::id()
    ));
    std::fs::write(&future, br#"{"format":"future-record-v99"}"#).unwrap();
    let incomplete = std::process::Command::new(binary)
        .args(["verify", future.to_str().unwrap(), "--json"])
        .output()
        .unwrap();
    std::fs::remove_file(future).unwrap();
    assert_eq!(incomplete.status.code(), Some(2));
    let incomplete: serde_json::Value = serde_json::from_slice(&incomplete.stdout).unwrap();
    assert_eq!(incomplete["status"], "incomplete");
    let fail = std::process::Command::new(binary)
        .args(["verify", "this-record-does-not-exist.json", "--json"])
        .output()
        .unwrap();
    assert_eq!(fail.status.code(), Some(1));
    let fail: serde_json::Value = serde_json::from_slice(&fail.stdout).unwrap();
    assert_eq!(fail["status"], "failed");
}
