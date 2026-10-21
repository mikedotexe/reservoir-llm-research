//! Writing temperature on the shared language configuration and the per-attempt sampler
//! seed. Omitted temperature keeps greedy decoding and historical serialization.
use reservoir_core::{
    stage::{LanguageConfiguration, LanguageKind},
    sustained::*,
};

fn ollama(temperature: Option<f64>) -> LanguageConfiguration {
    LanguageConfiguration {
        backend: LanguageKind::Ollama,
        endpoint: Some("http://127.0.0.1:11499".into()),
        model: Some("fixture-provider-not-contacted".into()),
        context_tokens: Some(8192),
        response_format: None,
        temperature,
    }
}

#[test]
fn omitted_temperature_serializes_unchanged_and_values_are_bounded() {
    let json = serde_json::to_string(&ollama(None)).unwrap();
    assert!(!json.contains("temperature"));
    let parsed: LanguageConfiguration = serde_json::from_str(&json).unwrap();
    assert_eq!(parsed.temperature, None);
    assert_eq!(LanguageConfiguration::default().temperature, None);
    let json = serde_json::to_string(&ollama(Some(DEFAULT_WRITING_TEMPERATURE))).unwrap();
    assert!(json.contains("\"temperature\":0.7"));
    let parsed: LanguageConfiguration = serde_json::from_str(&json).unwrap();
    assert_eq!(parsed.temperature, Some(0.7));
    for ok in [0.0, 0.7, 2.0] {
        ollama(Some(ok)).validate().unwrap();
    }
    for bad in [-0.1, 2.5, f64::NAN, f64::INFINITY] {
        assert!(ollama(Some(bad)).validate().is_err(), "{bad}");
    }
}

#[test]
fn sampling_seed_is_deterministic_distinct_per_attempt_and_fits_a_signed_integer() {
    let seed = 20_260_909;
    assert_eq!(sampling_seed(seed, 1), sampling_seed(seed, 1));
    let seeds: Vec<u64> = (1..=6).map(|a| sampling_seed(seed, a)).collect();
    for (i, a) in seeds.iter().enumerate() {
        assert!(*a < (1u64 << 63));
        for b in &seeds[i + 1..] {
            assert_ne!(a, b);
        }
    }
    assert_ne!(sampling_seed(seed, 1), sampling_seed(seed + 1, 1));
    assert!(sampling_seed(u64::MAX, u64::MAX) < (1u64 << 63));
}

#[test]
fn pending_language_carries_the_configured_temperature_and_guards_it() {
    let spec = SustainedSpecification {
        seed: 7,
        turn_every: 3,
        maximum_steps: 100,
        maximum_turns: 30,
        language: ollama(Some(0.7)),
        ..Default::default()
    };
    let mut s = SustainedSession::new(spec).unwrap();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    let pending = s.pending_language().unwrap().clone();
    assert_eq!(pending.configuration.temperature, Some(0.7));
    let checkpoint: SustainedCheckpoint =
        serde_json::from_slice(&serde_json::to_vec(&s.checkpoint()).unwrap()).unwrap();
    checkpoint.validate().unwrap();
    let mut altered = checkpoint.clone();
    if let SustainedPhase::Language(p) = &mut altered.state.phase {
        p.configuration.temperature = None;
    }
    altered.sha256 = {
        use sha2::{Digest, Sha256};
        format!(
            "{:x}",
            Sha256::digest(serde_json::to_vec(&altered.state).unwrap())
        )
    };
    assert!(altered.validate().is_err());
    let legacy = SustainedSession::new(SustainedSpecification {
        seed: 7,
        turn_every: 3,
        language: ollama(None),
        ..Default::default()
    })
    .unwrap();
    let json = serde_json::to_string(&legacy.checkpoint()).unwrap();
    assert!(!json.contains("temperature"));
}
