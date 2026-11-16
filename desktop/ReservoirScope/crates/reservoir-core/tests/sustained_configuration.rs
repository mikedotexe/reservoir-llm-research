use reservoir_core::sustained::*;
use serde_json::json;

fn commit(s: &mut SustainedSession, base: &mut SustainedCheckpoint) {
    let segment = SustainedSegment {
        format: FORMAT.into(),
        initial_checkpoint: base.clone(),
        events: s.events().iter().cloned().collect(),
        final_checkpoint: s.checkpoint(),
    };
    segment.verify().unwrap();
    s.acknowledge_events(segment.events.last().unwrap().id)
        .unwrap();
    *base = segment.final_checkpoint;
}
fn change(s: &SustainedSession, spec: SustainedSpecification) -> ConfigurationChange {
    ConfigurationChange {
        version: 1,
        operation_id: "operation-test".into(),
        expected_revision: s.configuration_revision(),
        predecessor_sha256: s.checkpoint().sha256,
        specification: spec,
        host_configuration: json!({}),
        elapsed_millis: 1000,
    }
}
#[test]
fn changes_preserve_numerical_state_and_replay_at_new_cadence() {
    let mut s = SustainedSession::new(SustainedSpecification::default()).unwrap();
    let mut base = s.checkpoint();
    for _ in 0..5 {
        s.advance().unwrap();
    }
    commit(&mut s, &mut base);
    let before = s.checkpoint();
    let mut spec = s.specification().clone();
    spec.leak = 0.4;
    spec.turn_every = 7;
    spec.noise_amplitude = 0.03;
    s.reconfigure(change(&s, spec)).unwrap();
    assert_eq!(
        s.checkpoint().state.reservoir_state,
        before.state.reservoir_state
    );
    assert_eq!(
        s.checkpoint().state.sensory_covariance,
        before.state.sensory_covariance
    );
    commit(&mut s, &mut base);
    assert_eq!(s.configuration_revision(), 1);
    for _ in 0..6 {
        s.advance().unwrap();
    }
    assert!(s.pending_language().is_none());
    commit(&mut s, &mut base);
    s.advance().unwrap();
    assert!(s.pending_language().is_some());
    commit(&mut s, &mut base);
}
#[test]
fn transition_rejects_pending_work_stale_identity_and_reseeding() {
    let mut s = SustainedSession::new(SustainedSpecification::default()).unwrap();
    let mut c = change(&s, s.specification().clone());
    c.specification.seed += 1;
    assert!(s.reconfigure(c).is_err());
    let mut c = change(&s, s.specification().clone());
    c.expected_revision = 4;
    assert!(s.reconfigure(c).is_err());
    let mut base = s.checkpoint();
    for _ in 0..30 {
        s.advance().unwrap();
    }
    commit(&mut s, &mut base);
    assert!(s
        .reconfigure(change(&s, s.specification().clone()))
        .is_err());
}
#[test]
fn enabling_and_disabling_scanner_and_actions_preserves_the_trajectory_prefix() {
    let mut s = SustainedSession::new(SustainedSpecification::default()).unwrap();
    let mut base = s.checkpoint();
    for _ in 0..4 {
        s.advance().unwrap();
    }
    commit(&mut s, &mut base);
    let mut v = serde_json::to_value(s.specification()).unwrap();
    v["promptVersion"] = json!("reservoir-journal-actions-v3");
    v["actionMode"] = json!("authored-v3");
    v["controlFeedback"] = json!("diagnostic-v1");
    v["sonar"] = json!({"version":"compact-scan-v2","allowLiveProbe":true});
    let spec = serde_json::from_value(v).unwrap();
    s.reconfigure(change(&s, spec)).unwrap();
    commit(&mut s, &mut base);
    s.advance().unwrap();
    commit(&mut s, &mut base);
    let mut spec = SustainedSpecification::default();
    spec.recurrent_gain = 0.7;
    s.reconfigure(change(&s, spec)).unwrap();
    commit(&mut s, &mut base);
    s.advance().unwrap();
    commit(&mut s, &mut base);
}

#[test]
fn growing_preserves_every_old_connection_coordinate_and_random_stream() {
    let original = reservoir_model(42, 32);
    let larger = reservoir_model(42, 48);
    let largest = reservoir_model(42, 64);
    for row in 0..32 {
        for col in 0..32 {
            assert_eq!(
                original.recurrent_weights[row * 32 + col],
                larger.recurrent_weights[row * 48 + col]
            );
        }
    }
    for row in 0..48 {
        for col in 0..48 {
            assert_eq!(
                larger.recurrent_weights[row * 48 + col],
                largest.recurrent_weights[row * 64 + col]
            );
        }
    }
    assert_eq!(&larger.input_weights[..32 * 67], &original.input_weights);
    let mut s = SustainedSession::new(SustainedSpecification::default()).unwrap();
    let mut base = s.checkpoint();
    for _ in 0..5 {
        s.advance().unwrap();
    }
    commit(&mut s, &mut base);
    let before = s.checkpoint();
    let mut spec = s.specification().clone();
    spec.reservoir_nodes = 48;
    s.reconfigure(change(&s, spec)).unwrap();
    let after = s.checkpoint();
    assert_eq!(
        before.state.reservoir_state,
        after.state.reservoir_state[..32]
    );
    assert!(after.state.reservoir_state[32..].iter().all(|n| *n == 0.0));
    assert_eq!(before.state.rng_state, after.state.rng_state);
    assert_eq!(
        before.state.sensory_covariance,
        after.state.sensory_covariance
    );
    commit(&mut s, &mut base);
    for _ in 0..4 {
        s.advance().unwrap();
    }
    commit(&mut s, &mut base);
    assert_eq!(base.state.reservoir_state.len(), 48);
    let mut spec = s.specification().clone();
    spec.reservoir_nodes = 32;
    assert!(s.reconfigure(change(&s, spec)).is_err());
}

#[test]
fn resized_compact_scans_and_custom_prompts_replay() {
    let mut spec = SustainedSpecification::default();
    spec.reservoir_nodes = 48;
    spec.prompt_version = SustainedPromptVersion::ActionJournalV3;
    spec.action_mode = Some(SustainedActionMode::AuthoredV3);
    spec.control_feedback = Some(SustainedControlFeedback::DiagnosticV1);
    spec.sonar = Some(SustainedSonarConfig {
        version: SustainedSonarVersion::CompactScanV2,
        allow_live_probe: true,
    });
    let mut s = SustainedSession::new(spec).unwrap();
    let mut base = s.checkpoint();
    s.advance().unwrap();
    commit(&mut s, &mut base);
    let scan = scan_compact_sustained_checkpoint(&base).unwrap();
    validate_compact_sonar_report(&scan).unwrap();
    assert_eq!(compact_sonar_matrix(&scan).unwrap().len(), 48);
    s.admit_custom_prompt(
        "prompt-op".into(),
        "A custom future question".into(),
        false,
        1000,
    )
    .unwrap();
    assert_eq!(
        s.pending_language().unwrap().prompt,
        "A custom future question"
    );
    commit(&mut s, &mut base);
    s.skip_pending("test skip").unwrap();
    commit(&mut s, &mut base);
}

#[test]
fn changing_conversation_text_preserves_due_slots_but_cadence_changes_rebase() {
    let mut spec = SustainedSpecification::default();
    spec.check_in_schedule = Some(SustainedCheckInSchedule {
        interval_seconds: 10,
        end_after_seconds: 30,
        prompt: "old".into(),
        include_telemetry: false,
    });
    let mut s = SustainedSession::new(spec).unwrap();
    let mut base = s.checkpoint();
    s.advance().unwrap();
    commit(&mut s, &mut base);
    assert!(s.admit_due_check_in(10000).unwrap());
    s.skip_pending("test skip").unwrap();
    commit(&mut s, &mut base);
    let mut spec = s.specification().clone();
    spec.check_in_schedule.as_mut().unwrap().prompt = "new".into();
    let mut c = change(&s, spec);
    c.elapsed_millis = 15000;
    s.reconfigure(c).unwrap();
    commit(&mut s, &mut base);
    assert_eq!(s.check_in_state().unwrap().outcomes.len(), 1);
    assert_eq!(s.schedule_elapsed(20000), 20000);
    s.advance().unwrap();
    assert!(s.admit_due_check_in(20000).unwrap());
    assert_eq!(s.pending_language().unwrap().prompt, "new");
    s.skip_pending("test skip").unwrap();
    commit(&mut s, &mut base);
    let mut spec = s.specification().clone();
    spec.check_in_schedule.as_mut().unwrap().interval_seconds = 5;
    let mut c = change(&s, spec);
    c.elapsed_millis = 22000;
    s.reconfigure(c).unwrap();
    commit(&mut s, &mut base);
    assert_eq!(s.schedule_elapsed(27000), 5000);
    assert!(s.check_in_state().unwrap().outcomes.is_empty());
}

#[test]
fn unrelated_configuration_changes_do_not_shift_the_writing_cadence() {
    let mut spec = SustainedSpecification::default();
    spec.turn_every = 7;
    let mut s = SustainedSession::new(spec).unwrap();
    let mut base = s.checkpoint();
    for _ in 0..5 {
        s.advance().unwrap();
    }
    commit(&mut s, &mut base);
    let mut spec = s.specification().clone();
    spec.reservoir_nodes = 48;
    s.reconfigure(change(&s, spec)).unwrap();
    commit(&mut s, &mut base);
    s.advance().unwrap();
    assert!(s.pending_language().is_none());
    s.advance().unwrap();
    assert!(s.pending_language().is_some());
    commit(&mut s, &mut base);
}
