//! Mechanism v2: uniform field-input noise and scaled held feedback. Legacy values keep
//! mechanism v1 byte-for-byte; non-legacy values are identified, replayable and guarded.
use reservoir_core::{session::LanguageResponse, sustained::*};
use serde::Serialize;
use sha2::{Digest, Sha256};

const V1: &str = "essentials32-splitmix64-codec48-held-feedback-v1";
const V2: &str = "essentials32-splitmix64-codec48-scaled-feedback-field-noise-v2";

fn bytes<T: Serialize>(v: &T) -> Vec<u8> {
    serde_json::to_vec(v).unwrap()
}
fn legacy() -> SustainedSpecification {
    SustainedSpecification {
        seed: 7,
        turn_every: 3,
        maximum_steps: 1000,
        maximum_turns: 400,
        ..Default::default()
    }
}
fn v2() -> SustainedSpecification {
    SustainedSpecification {
        sensory_noise_amplitude: DEFAULT_SENSORY_NOISE_AMPLITUDE,
        feedback_scale: DEFAULT_FEEDBACK_SCALE,
        ..legacy()
    }
}
fn response() -> LanguageResponse {
    LanguageResponse {
        text: "The field keeps turning while the same few words return.".into(),
        provider_model: None,
        stop_reason: Some("stop".into()),
        token_count: Some(12),
        complete: true,
        provider_prompt_evaluation: None,
    }
}
fn checkpoint(s: &SustainedSession) -> SustainedCheckpoint {
    serde_json::from_slice(&bytes(&s.checkpoint())).unwrap()
}
fn rehash(c: &mut SustainedCheckpoint) {
    c.sha256 = format!("{:x}", Sha256::digest(bytes(&c.state)));
}
fn settle(s: &mut SustainedSession) {
    if let Some(m) = s.pending_memory().cloned() {
        s.confirm_memory(&m.entry).unwrap();
    }
    if let Some(p) = s.pending_language().cloned() {
        s.start_language(p.attempt_id).unwrap();
        s.confirm_language(p.attempt_id, &response()).unwrap();
    }
    if let Some(j) = s.pending_journal().cloned() {
        let receipt = SustainedSaveReceipt {
            entry_id: j.entry.id.clone(),
            sha256: j.entry.sha256.clone(),
            relative_path: format!("journals/{}.json", j.entry.id),
        };
        s.confirm_saved(&receipt, &j.entry).unwrap();
    }
    if let Some(p) = s.prepared_application() {
        let id = p.entry.attempt_id;
        s.authorize_application(id).unwrap();
    }
}
fn step(s: &mut SustainedSession) -> SustainedFrame {
    settle(s);
    s.advance().unwrap()
}
fn segment(base: &SustainedCheckpoint, s: &SustainedSession) -> SustainedSegment {
    SustainedSegment {
        format: FORMAT.into(),
        initial_checkpoint: base.clone(),
        events: s.events().iter().cloned().collect(),
        final_checkpoint: checkpoint(s),
    }
}

#[test]
fn legacy_values_serialize_unchanged_and_keep_mechanism_v1() {
    let json = String::from_utf8(bytes(&legacy())).unwrap();
    assert!(!json.contains("sensoryNoiseAmplitude") && !json.contains("feedbackScale"));
    assert_eq!(legacy().mechanism(), V1);
    assert!(!legacy().uses_field_noise_mechanism());
    let parsed: SustainedSpecification = serde_json::from_str(&json).unwrap();
    assert_eq!(parsed.sensory_noise_amplitude, 0.0);
    assert_eq!(parsed.feedback_scale, 1.0);
    let json = String::from_utf8(bytes(&v2())).unwrap();
    assert!(
        json.contains("\"sensoryNoiseAmplitude\":0.5") && json.contains("\"feedbackScale\":0.4")
    );
    let parsed: SustainedSpecification = serde_json::from_str(&json).unwrap();
    assert_eq!(parsed.mechanism(), V2);
    for (noise, scale) in [
        (-0.1, 1.0),
        (1.5, 1.0),
        (0.4, -0.1),
        (0.4, 2.5),
        (f64::NAN, 1.0),
    ] {
        let bad = SustainedSpecification {
            sensory_noise_amplitude: noise,
            feedback_scale: scale,
            ..legacy()
        };
        assert!(bad.validate().is_err(), "{noise} {scale}");
    }
    assert_eq!(
        checkpoint(&SustainedSession::new(legacy()).unwrap())
            .state
            .mechanism,
        V1
    );
    assert_eq!(
        checkpoint(&SustainedSession::new(v2()).unwrap())
            .state
            .mechanism,
        V2
    );
    assert!(field_noise(&legacy(), 5).is_empty());
    let frame = SustainedSession::new(legacy()).unwrap().advance().unwrap();
    assert!(frame.sensory_noise.is_empty());
    assert!(!String::from_utf8(bytes(&frame))
        .unwrap()
        .contains("sensoryNoise"));
}

#[test]
fn field_noise_is_deterministic_step_indexed_bounded_and_non_overlapping() {
    let spec = v2();
    let a = field_noise(&spec, 9);
    assert_eq!(a, field_noise(&spec, 9));
    assert_eq!(a.len(), 66);
    assert!(a.iter().all(|x| x.abs() <= spec.sensory_noise_amplitude));
    let b = field_noise(&spec, 10);
    assert_ne!(a, b);
    assert_ne!(
        a[1..],
        b[..65],
        "consecutive steps must not share a shifted stream"
    );
    let other = SustainedSpecification { seed: 8, ..v2() };
    assert_ne!(a, field_noise(&other, 9));
    let half = SustainedSpecification {
        sensory_noise_amplitude: DEFAULT_SENSORY_NOISE_AMPLITUDE / 2.0,
        ..v2()
    };
    let h = field_noise(&half, 9);
    assert!(a.iter().zip(&h).all(|(x, y)| (x * 0.5 - y).abs() < 1e-15));
}

#[test]
fn scaled_feedback_and_field_noise_enter_frames_and_tampering_is_rejected() {
    let mut s = SustainedSession::new(v2()).unwrap();
    let base = s.checkpoint();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    settle(&mut s);
    let prepared = checkpoint(&s);
    let vector = match &prepared.state.phase {
        SustainedPhase::Prepared(p) => p.semantic_vector.clone(),
        other => panic!("expected prepared feedback, got {other:?}"),
    };
    let f = s.advance().unwrap();
    assert_eq!(f.step, 4);
    assert!(f.application.is_some());
    let expected: Vec<f64> = vector.iter().map(|x| x * DEFAULT_FEEDBACK_SCALE).collect();
    assert_eq!(f.input[18..], expected[..]);
    assert_eq!(f.sensory_noise, field_noise(&v2(), 4));
    assert_eq!(
        checkpoint(&s).state.held_vector,
        vector,
        "stored feedback stays unscaled"
    );
    checkpoint(&s).validate().unwrap();
    segment(&base, &s).verify().unwrap();
    let mut c = checkpoint(&s);
    c.state.latest_frame.as_mut().unwrap().sensory_noise[3] += 1e-9;
    rehash(&mut c);
    assert!(c.validate().is_err());
    let mut c = checkpoint(&s);
    c.state.latest_frame.as_mut().unwrap().sensory_noise.clear();
    rehash(&mut c);
    assert!(c.validate().is_err());
    let mut c = checkpoint(&s);
    c.state.mechanism = V1.into();
    rehash(&mut c);
    assert!(c.validate().is_err());
    let mut c = checkpoint(&s);
    c.state.specification.feedback_scale = 1.0;
    rehash(&mut c);
    assert!(c.validate().is_err());
    let mut altered = segment(&base, &s);
    if let SustainedEventKind::Advanced(frame) = &mut altered.events[0].kind {
        frame.sensory_noise[0] += 1e-9;
    }
    assert!(altered.verify().is_err());
}

#[test]
fn restored_continuation_matches_uninterrupted_under_field_noise() {
    let mut a = SustainedSession::new(v2()).unwrap();
    let mut b = SustainedSession::new(v2()).unwrap();
    let mut base = b.checkpoint();
    for i in 1..=14 {
        let fa = step(&mut a);
        settle(&mut b);
        if i % 4 == 0 {
            let seg = segment(&base, &b);
            seg.verify().unwrap();
            b.acknowledge_events(seg.events.last().unwrap().id).unwrap();
            base = seg.final_checkpoint.clone();
            // Recovery never carries application permission; the caller re-authorizes.
            b = SustainedSession::restore(checkpoint(&b)).unwrap();
            settle(&mut b);
        }
        let fb = b.advance().unwrap();
        assert_eq!(bytes(&fa), bytes(&fb), "frame {i}");
    }
    assert_eq!(bytes(&a.checkpoint().state), bytes(&b.checkpoint().state));
}

#[test]
fn defaults_let_regulation_leave_its_rail_while_legacy_stays_low() {
    let run = |spec: SustainedSpecification| {
        let mut s = SustainedSession::new(SustainedSpecification {
            turn_every: 30,
            maximum_steps: 2000,
            ..spec
        })
        .unwrap();
        let mut last = None;
        for i in 1..=420 {
            last = Some(step(&mut s));
            if i % 30 == 0 {
                let id = s.events().back().unwrap().id;
                s.acknowledge_events(id).unwrap();
            }
        }
        let f = last.unwrap();
        (f.sensory.fill_percent, f.next_retention)
    };
    let (legacy_fill, legacy_retention) = run(legacy());
    let (fill, retention) = run(v2());
    eprintln!("legacy fill {legacy_fill:.2}% retention {legacy_retention:.3}; v2 fill {fill:.2}% retention {retention:.3}");
    assert!(
        legacy_fill < 45.0 && legacy_retention >= 0.99,
        "legacy {legacy_fill} {legacy_retention}"
    );
    assert!((45.0..=80.0).contains(&fill), "v2 fill {fill}");
    assert!(retention < 0.99, "v2 retention {retention}");
}
