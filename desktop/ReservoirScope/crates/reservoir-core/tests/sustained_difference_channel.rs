//! S-011 M5: the difference-signal channel. Gain 0 is byte for byte the 0.34.0 mechanism;
//! a nonzero gain adds a recorded, recomputable contribution to the 48 feedback slots,
//! carries a v4 identity, and is guarded by a watchdog that drops the gain for the rest
//! of the session.
use reservoir_core::{session::LanguageResponse, sustained::*};
use serde::Serialize;
use sha2::{Digest, Sha256};

const V2: &str = "essentials32-splitmix64-codec48-scaled-feedback-field-noise-v2";
const V3: &str = "essentials32-splitmix64-embedding32-scaled-feedback-field-noise-v3";
const V4: &str = "essentials32-splitmix64-codec48-scaled-feedback-field-noise-difference-v4";
const V4_EMBEDDING: &str =
    "essentials32-splitmix64-embedding32-scaled-feedback-field-noise-difference-v4";

fn bytes<T: Serialize>(v: &T) -> Vec<u8> {
    serde_json::to_vec(v).unwrap()
}
fn text<T: Serialize>(v: &T) -> String {
    String::from_utf8(bytes(v)).unwrap()
}
fn hash(data: &[u8]) -> String {
    format!("{:x}", Sha256::digest(data))
}
fn v2() -> SustainedSpecification {
    SustainedSpecification {
        seed: 7,
        turn_every: 3,
        maximum_steps: 1000,
        maximum_turns: 400,
        sensory_noise_amplitude: DEFAULT_SENSORY_NOISE_AMPLITUDE,
        feedback_scale: DEFAULT_FEEDBACK_SCALE,
        ..Default::default()
    }
}
fn with_gain(gain: f64) -> SustainedSpecification {
    SustainedSpecification {
        difference_gain: gain,
        ..v2()
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
    c.sha256 = hash(&bytes(&c.state));
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
fn acknowledge(s: &mut SustainedSession) {
    if let Some(last) = s.events().back().map(|e| e.id) {
        s.acknowledge_events(last).unwrap();
    }
}
/// Runs `steps` settled steps without acknowledging events (bounded outbox: keep short).
fn run(spec: SustainedSpecification, steps: usize) -> (SustainedSession, Vec<SustainedFrame>) {
    let mut s = SustainedSession::new(spec).unwrap();
    let frames = (0..steps).map(|_| step(&mut s)).collect();
    (s, frames)
}

#[test]
fn gain_zero_is_byte_for_byte_the_earlier_mechanism() {
    for (spec, mechanism) in [
        (v2(), V2),
        (
            SustainedSpecification {
                codec: SustainedCodec::Embedding {
                    model: "nomic-embed-text".into(),
                    projection_seed: 1,
                },
                ..v2()
            },
            V3,
        ),
    ] {
        assert!(!text(&spec).contains("difference"), "{}", text(&spec));
        assert_eq!(spec.mechanism(), mechanism);
        let decoded: SustainedSpecification = serde_json::from_slice(&bytes(&spec)).unwrap();
        assert_eq!(decoded.difference_gain, 0.0);
        assert_eq!(decoded.difference_tau, default_difference_tau());
        assert_eq!(decoded.difference_clip, default_difference_clip());
        assert!(decoded.difference_watchdog);
    }
    let base = checkpoint(&SustainedSession::new(v2()).unwrap());
    let (s, frames) = run(v2(), 40);
    for f in &frames {
        assert!(f.difference_input.is_empty() && f.difference_gain_used == 0.0);
        assert!(!text(f).contains("difference"));
    }
    assert!(!text(&s.checkpoint()).contains("difference"));
    assert!(!text(&s.events().iter().cloned().collect::<Vec<_>>()).contains("difference"));
    segment(&base, &s).verify().unwrap();

    // A segment recorded by the 0.34.0 binary before this channel existed re-serialises
    // byte for byte and validates under the new code.
    let frozen = include_bytes!("fixtures/sustained-prompts/v34-gain-zero-segment.json");
    assert_eq!(
        hash(frozen),
        "bbc3487aff4bb28cf7153b3490eeada210a3b7a99bea7f8897143c5c4e06f33b"
    );
    let witness: SustainedSegment = serde_json::from_slice(frozen).unwrap();
    assert_eq!(bytes(&witness), frozen.to_vec());
    witness.initial_checkpoint.validate().unwrap();
    witness.final_checkpoint.validate().unwrap();
    assert_eq!(witness.initial_checkpoint.state.mechanism, V2);
    assert_eq!(witness.final_checkpoint.state.step, 4);
}

#[test]
#[cfg_attr(not(all(target_os = "macos", target_arch = "aarch64")), ignore)]
fn the_0_34_0_witness_segment_replays_exactly_on_the_recording_host() {
    let frozen = include_bytes!("fixtures/sustained-prompts/v34-gain-zero-segment.json");
    let witness: SustainedSegment = serde_json::from_slice(frozen).unwrap();
    witness.verify().unwrap();
}

#[test]
fn a_nonzero_gain_alters_only_the_feedback_slots_and_is_recorded_and_guarded() {
    for (spec, mechanism) in [
        (with_gain(0.05), V4),
        (
            SustainedSpecification {
                codec: SustainedCodec::Embedding {
                    model: "nomic-embed-text".into(),
                    projection_seed: 1,
                },
                ..with_gain(0.05)
            },
            V4_EMBEDDING,
        ),
    ] {
        assert_eq!(spec.mechanism(), mechanism);
        assert!(
            text(&spec).contains("\"differenceGain\":0.05")
                && !text(&spec).contains("differenceTau")
        );
    }
    let (twin, plain) = run(v2(), 24);
    let base = checkpoint(&SustainedSession::new(with_gain(0.05)).unwrap());
    let (s, frames) = run(with_gain(0.05), 24);
    assert_eq!(s.checkpoint().state.mechanism, V4);
    let mut nonzero = 0;
    for (f, p) in frames.iter().zip(&plain) {
        assert_eq!(f.input[..18], p.input[..18]);
        assert_eq!(f.noise, p.noise);
        assert_eq!(f.sensory_noise, p.sensory_noise);
        assert_eq!(f.difference_gain_used, 0.05);
        assert_eq!(f.difference_input.len(), 48);
        assert!(f
            .difference_input
            .iter()
            .all(|u| u.is_finite() && u.abs() <= default_difference_clip()));
        if f.difference_input.iter().any(|u| *u != 0.0) {
            nonzero += 1;
        }
        assert!(f.difference_gain_dropped.is_none());
    }
    assert!(
        frames[0].difference_input.iter().all(|u| *u == 0.0),
        "no reference before the first observation"
    );
    assert!(nonzero > 0, "the channel contributed on some step");
    let c = checkpoint(&s);
    assert_eq!(
        c.state.difference_reference_step, 24,
        "the last observation step at turn 3"
    );
    assert_eq!(c.state.difference_filtered.len(), 32);
    assert!(text(&c).contains("differenceFiltered"));
    let f = c.state.latest_frame.as_ref().unwrap();
    let mut expected: Vec<f64> = c
        .state
        .held_vector
        .iter()
        .map(|x| x * DEFAULT_FEEDBACK_SCALE)
        .collect();
    for (e, u) in expected.iter_mut().zip(&f.difference_input) {
        *e += u;
    }
    assert_eq!(f.input[18..], expected[..]);
    assert_eq!(
        f.difference_input,
        difference_contribution(
            &c.state.difference_filtered,
            &difference_matrix(7 ^ 0x0044_4946_4645_5245),
            0.05,
            default_difference_dead_band(),
            default_difference_clip()
        )
    );
    c.validate().unwrap();
    segment(&base, &s).verify().unwrap();
    drop(twin);

    // Tampering with the recorded channel, its reference, the identity or the gain is caught.
    let tamper = |edit: &dyn Fn(&mut SustainedCheckpoint)| {
        let mut t = checkpoint(&s);
        edit(&mut t);
        rehash(&mut t);
        assert!(t.validate().is_err());
    };
    tamper(&|t| t.state.latest_frame.as_mut().unwrap().difference_input[0] += 1e-9);
    tamper(&|t| {
        t.state
            .latest_frame
            .as_mut()
            .unwrap()
            .difference_input
            .clear()
    });
    tamper(&|t| t.state.difference_reference_step += 1);
    tamper(&|t| t.state.mechanism = V2.into());
    tamper(&|t| t.state.specification.difference_gain = 0.0);
    tamper(&|t| t.state.difference_filtered[3] += 1.0);
    let mut edited = segment(&base, &s);
    let target = edited
        .events
        .iter()
        .position(|e| matches!(&e.kind, SustainedEventKind::Advanced(f) if f.difference_input.iter().any(|u| *u != 0.0)))
        .expect("an advanced event with a nonzero contribution");
    if let SustainedEventKind::Advanced(f) = &mut edited.events[target].kind {
        f.difference_input[0] += 1e-9;
    }
    assert!(edited.verify().is_err());
}

#[test]
fn dead_band_clip_sign_and_matrix_behave() {
    let m = difference_matrix(1);
    assert_eq!(m.len(), 48 * 32);
    assert_eq!(m, difference_matrix(1));
    assert_ne!(m, difference_matrix(2));
    let mean = m.iter().sum::<f64>() / m.len() as f64;
    let variance = m.iter().map(|w| (w - mean) * (w - mean)).sum::<f64>() / m.len() as f64;
    assert!(mean.abs() < 0.01, "{mean}");
    assert!((variance - 1.0 / 32.0).abs() < 0.006, "{variance}");

    let small = vec![0.015; 32];
    let silent = difference_contribution(&small, &m, -0.1, 0.02, 0.2);
    assert_eq!(silent.len(), 48);
    assert!(
        silent.iter().all(|u| u.to_bits() == 0.0f64.to_bits()),
        "+0.0, never -0.0"
    );

    let big = vec![5.0; 32];
    let clipped = difference_contribution(&big, &m, 1.0, 0.02, 0.3);
    assert!(clipped.iter().all(|u| u.abs() <= 0.3));
    assert!(clipped.iter().any(|u| u.abs() == 0.3));

    let d: Vec<f64> = (0..32).map(|i| 0.05 * (i as f64 - 15.5)).collect();
    let plus = difference_contribution(&d, &m, 0.05, 0.02, 5.0);
    let minus = difference_contribution(&d, &m, -0.05, 0.02, 5.0);
    let double = difference_contribution(&d, &m, 0.1, 0.02, 5.0);
    for k in 0..48 {
        assert!((plus[k] + minus[k]).abs() < 1e-12);
        assert!((double[k] - 2.0 * plus[k]).abs() < 1e-12);
    }
}

#[test]
fn watchdog_rules_and_a_forced_excursion_drop_the_gain() {
    let mut window = Vec::new();
    let (mut oob, mut sat) = (0, 0);
    let quiet = vec![0.1; 32];
    for i in 0..89 {
        difference_watchdog_update(
            &mut window,
            &mut oob,
            &mut sat,
            60.0 + (i % 2) as f64 * 30.0,
            &quiet,
        );
    }
    assert_eq!(
        difference_watchdog_verdict(&window, oob, sat, 10.0),
        None,
        "window not full"
    );
    difference_watchdog_update(&mut window, &mut oob, &mut sat, 90.0, &quiet);
    assert_eq!(window.len(), 90);
    assert_eq!(
        difference_watchdog_verdict(&window, oob, sat, 10.0),
        Some(DIFFERENCE_DROP_FILL_STD)
    );
    assert_eq!(difference_watchdog_verdict(&window, oob, sat, 20.0), None);
    let mut w2 = Vec::new();
    let (mut oob2, mut sat2) = (0, 0);
    for _ in 0..59 {
        difference_watchdog_update(&mut w2, &mut oob2, &mut sat2, 5.0, &quiet);
    }
    assert_eq!(oob2, 59);
    assert_eq!(difference_watchdog_verdict(&w2, oob2, sat2, 10.0), None);
    difference_watchdog_update(&mut w2, &mut oob2, &mut sat2, 5.0, &quiet);
    assert_eq!(
        difference_watchdog_verdict(&w2, oob2, sat2, 10.0),
        Some(DIFFERENCE_DROP_FILL_BAND)
    );
    difference_watchdog_update(&mut w2, &mut oob2, &mut sat2, 50.0, &quiet);
    assert_eq!(oob2, 0, "a fill back in band resets the count");
    let hot = vec![0.99; 32];
    let mut w3 = Vec::new();
    let (mut oob3, mut sat3) = (0, 0);
    for _ in 0..30 {
        difference_watchdog_update(&mut w3, &mut oob3, &mut sat3, 60.0, &hot);
    }
    assert_eq!(
        difference_watchdog_verdict(&w3, oob3, sat3, 10.0),
        Some(DIFFERENCE_DROP_SATURATION)
    );

    // Integration: a fill-std bound of 0 trips rule (a) at the 90th active step.
    let spec = SustainedSpecification {
        difference_watchdog_fill_std: 0.0,
        turn_every: 30,
        ..with_gain(0.1)
    };
    let mut s = SustainedSession::new(spec).unwrap();
    let mut frames = Vec::new();
    for i in 1..=60 {
        frames.push(step(&mut s));
        if i % 30 == 0 {
            acknowledge(&mut s);
        }
    }
    let base = checkpoint(&s);
    for _ in 61..=120 {
        frames.push(step(&mut s));
    }
    let dropped = frames
        .iter()
        .find(|f| f.difference_gain_dropped.is_some())
        .unwrap();
    assert_eq!(dropped.step, 90);
    assert_eq!(dropped.difference_gain_used, 0.1);
    assert_eq!(dropped.difference_input.len(), 48);
    assert_eq!(
        dropped.difference_gain_dropped.as_ref().unwrap().reason,
        DIFFERENCE_DROP_FILL_STD
    );
    for f in frames.iter().filter(|f| f.step > 90) {
        assert!(f.difference_input.is_empty() && f.difference_gain_used == 0.0);
        assert!(!text(f).contains("difference"));
    }
    let c = checkpoint(&s);
    assert_eq!(
        c.state.difference_gain_dropped.as_ref().map(|d| d.step),
        Some(90)
    );
    assert!(c.state.difference_filtered.is_empty() && c.state.difference_fill_window.is_empty());
    assert_eq!(
        c.state.mechanism, V4,
        "the identity records the configured channel"
    );
    c.validate().unwrap();
    segment(&base, &s).verify().unwrap();
    let mut t = checkpoint(&s);
    t.state.difference_gain_dropped = None;
    rehash(&mut t);
    assert!(t.validate().is_err());
    let mut t = checkpoint(&s);
    t.state.difference_gain_dropped.as_mut().unwrap().reason = "other".into();
    rehash(&mut t);
    assert!(t.validate().is_err());
}

#[test]
fn restored_continuations_match_uninterrupted_runs_across_the_drop() {
    let spec = SustainedSpecification {
        difference_watchdog_fill_std: 0.0,
        turn_every: 30,
        ..with_gain(0.1)
    };
    let mut straight = SustainedSession::new(spec.clone()).unwrap();
    let mut restored = SustainedSession::new(spec).unwrap();
    for i in 0..120 {
        if i % 30 == 0 {
            acknowledge(&mut straight);
        }
        let a = step(&mut straight);
        if i % 4 == 0 {
            restored = SustainedSession::restore(checkpoint(&restored)).unwrap();
        }
        let b = step(&mut restored);
        assert_eq!(bytes(&a), bytes(&b), "step {}", i + 1);
    }
    assert_eq!(bytes(&straight.checkpoint()), bytes(&restored.checkpoint()));
}

#[test]
fn the_entry_effect_still_isolates_the_entry_under_the_channel() {
    use reservoir_core::math::{forcing, ReservoirEngine, ReservoirModel};
    let spec = SustainedSpecification {
        prompt_version: SustainedPromptVersion::InertEffectV1,
        ..with_gain(0.1)
    };
    let (s, frames) = run(spec.clone(), 12);
    let application = frames.iter().find(|f| f.application.is_some()).unwrap();
    let effect = application.entry_effect.clone().unwrap();
    let prior = frames
        .iter()
        .find(|f| f.step + 1 == application.step)
        .map(|f| f.state.clone())
        .unwrap();
    let model = ReservoirModel::seeded(spec.seed);
    let mut with = ReservoirEngine::new(model.clone(), spec.leak, Some(prior.clone())).unwrap();
    let mut without = ReservoirEngine::new(model, spec.leak, Some(prior)).unwrap();
    let with_state = with.step(&application.input, &application.noise).unwrap();
    let mut silent_input = forcing(application.step as usize, spec.dt);
    for (slot, u) in silent_input[18..]
        .iter_mut()
        .zip(&application.difference_input)
    {
        *slot += u;
    }
    let without_state = without.step(&silent_input, &application.noise).unwrap();
    let shift: f64 = with_state
        .iter()
        .zip(&without_state)
        .map(|(a, b)| (a - b) * (a - b))
        .sum::<f64>()
        .sqrt();
    assert_eq!(effect.shift, shift);
    assert_eq!(with_state, application.state);
    drop(s);
}
