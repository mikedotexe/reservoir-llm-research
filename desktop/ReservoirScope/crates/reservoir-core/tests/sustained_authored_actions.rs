use reservoir_core::{codec, math::*, session::LanguageResponse, sustained::*};
use sha2::{Digest, Sha256};
use std::collections::HashMap;

fn specification() -> SustainedSpecification {
    SustainedSpecification {
        action_mode: Some(SustainedActionMode::AuthoredV1),
        prompt_version: SustainedPromptVersion::ActionJournalV1,
        turn_every: 3,
        maximum_steps: 1000,
        maximum_turns: 200,
        sensory_noise_amplitude: 0.5,
        feedback_scale: 0.4,
        ..Default::default()
    }
}
fn response(text: &str) -> LanguageResponse {
    LanguageResponse {
        text: text.into(),
        provider_model: None,
        stop_reason: Some("stop".into()),
        token_count: Some(30),
        complete: true,
        provider_prompt_evaluation: None,
    }
}
struct Run {
    session: SustainedSession,
    entries: HashMap<String, SustainedJournal>,
    base: SustainedCheckpoint,
}
impl Run {
    fn new(spec: SustainedSpecification) -> Self {
        let session = SustainedSession::new(spec).unwrap();
        let base = session.checkpoint();
        Self {
            session,
            entries: HashMap::new(),
            base,
        }
    }
    fn reach(&mut self) {
        while matches!(self.session.phase(), SustainedPhase::Ready) {
            self.session.advance().unwrap();
        }
        if let Some(p) = self.session.pending_memory().cloned() {
            let entry = p
                .entry
                .as_ref()
                .unwrap_or_else(|| self.entries.get(p.entry_id().unwrap()).unwrap());
            self.session.confirm_memory(entry).unwrap();
        }
    }
    fn receive(&mut self, text: &str) -> SustainedPendingJournal {
        self.reach();
        let id = self.session.pending_language().unwrap().attempt_id;
        self.session.start_language(id).unwrap();
        self.session.confirm_language(id, &response(text)).unwrap();
        self.session.pending_journal().unwrap().clone()
    }
    fn save(&mut self, text: &str) -> SustainedPendingJournal {
        let journal = self.receive(text);
        self.session
            .confirm_saved(
                &SustainedSaveReceipt {
                    entry_id: journal.entry.id.clone(),
                    sha256: journal.entry.sha256.clone(),
                    relative_path: format!("journals/{}.json", journal.entry.id),
                },
                &journal.entry,
            )
            .unwrap();
        self.entries
            .insert(journal.entry.id.clone(), journal.entry.clone());
        journal
    }
    fn apply(&mut self) -> SustainedFrame {
        let id = self
            .session
            .prepared_application()
            .unwrap()
            .entry
            .attempt_id;
        self.session.authorize_application(id).unwrap();
        self.session.advance().unwrap()
    }
    fn turn(&mut self, text: &str) -> SustainedFrame {
        self.save(text);
        self.apply()
    }
    fn verify(&mut self) -> SustainedSegment {
        let segment = SustainedSegment {
            format: FORMAT.into(),
            initial_checkpoint: self.base.clone(),
            events: self.session.events().iter().cloned().collect(),
            final_checkpoint: self.session.checkpoint(),
        };
        segment.verify().unwrap();
        self.session
            .acknowledge_events(segment.events.last().unwrap().id)
            .unwrap();
        self.base = segment.final_checkpoint.clone();
        segment
    }
}
fn distance(a: &[f64], b: &[f64]) -> f64 {
    a.iter()
        .zip(b)
        .map(|(a, b)| (a - b).powi(2))
        .sum::<f64>()
        .sqrt()
}
fn rehash(checkpoint: &mut SustainedCheckpoint) {
    checkpoint.sha256 = format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&checkpoint.state).unwrap())
    );
}

#[test]
fn disabled_mode_preserves_old_bytes_and_does_not_execute_next() {
    let mut legacy = Run::new(SustainedSpecification {
        action_mode: None,
        prompt_version: SustainedPromptVersion::MeasurementMeaningJournalV8,
        ..specification()
    });
    let journal = legacy.save("Journal body.\nNEXT: TUNE feedbackScale 2");
    assert!(journal.action.is_none() && journal.entry.body.is_none());
    assert_eq!(
        journal.encoded_features,
        codec::encode(&journal.entry.text).unwrap()
    );
    assert!(legacy.apply().action_receipt.is_none());
    let bytes = serde_json::to_string(&legacy.session.checkpoint()).unwrap();
    for absent in [
        "actionMode",
        "actionState",
        "actionReceipt",
        "\"body\"",
        "\"action\"",
    ] {
        assert!(!bytes.contains(absent), "{absent}");
    }
    legacy.verify();
    let mut spec = specification();
    spec.action_mode = None;
    assert!(spec.validate().is_err());
    spec = specification();
    spec.prompt_version = SustainedPromptVersion::MeasurementMeaningJournalV8;
    assert!(spec.validate().is_err());
}

#[test]
fn only_one_final_unquoted_line_can_act() {
    for (text, valid) in [
        ("Body\nNEXT: PULSE alternating 0.5", true),
        ("Body\nNEXT: TUNE recurrentGain 2\n\n", true),
        ("Body\r\nNEXT: RELEASE\r\n", true),
        ("Body\n> NEXT: PULSE uniform 1", false),
        ("Body\n`NEXT: RELEASE`", false),
        ("Body\n```text\nNEXT: RELEASE\n```", false),
        ("Body\n~~~\nNEXT: RELEASE\n~~~", false),
        ("Body\n````\n```\nNEXT: RELEASE", false),
        ("Body\n~~~~\n~~~\nNEXT: RELEASE", false),
        ("Body\n```\n```rust\nNEXT: RELEASE", false),
        ("Body\n```\nNEXT: RELEASE", false),
        ("Body\n````\n```\nNEXT: RELEASE\n````\nNEXT: NONE", true),
        ("Body\n    NEXT: RELEASE", false),
        ("Body\nNEXT: RELEASE\nLater prose", false),
        ("Body\nNEXT: NONE\nNEXT: RELEASE", false),
        ("Body\nNEXT: TUNE leak NaN", false),
        ("Body\nNEXT: TUNE feedbackScale inf", false),
        ("Body\nNEXT: TUNE leak 0", false),
        ("Body\nNEXT: PULSE uniform 0.2", false),
        ("Body\nNEXT: SHAPE happy", false),
    ] {
        let action = parse_authored_action(text);
        assert_eq!(action.request.is_some(), valid, "{text}");
        assert_eq!(action.rejection.is_none(), valid);
    }
    let long = format!("body\nNEXT: {}", "x".repeat(1000));
    let parsed = parse_authored_action(&long);
    assert_eq!(parsed.body, "body");
    assert!(parsed.raw_tail.is_none());
    assert!(parsed.rejection.unwrap().contains("512"));
}

#[test]
fn pulse_waits_for_save_and_durable_authorization_and_executes_once_after_restore() {
    let mut run = Run::new(specification());
    let journal = run.receive("I will test a direction.\nNEXT: PULSE uniform 0.5");
    assert_eq!(
        journal.entry.text,
        "I will test a direction.\nNEXT: PULSE uniform 0.5"
    );
    assert_eq!(
        journal.entry.body.as_deref(),
        Some("I will test a direction.")
    );
    assert_eq!(
        journal.encoded_features,
        codec::encode("I will test a direction.").unwrap()
    );
    assert!(run.session.advance().is_err());
    assert_eq!(run.session.action_state().unwrap().decision_count, 0);
    let receipt = SustainedSaveReceipt {
        entry_id: journal.entry.id.clone(),
        sha256: journal.entry.sha256.clone(),
        relative_path: format!("journals/{}.json", journal.entry.id),
    };
    run.session.confirm_saved(&receipt, &journal.entry).unwrap();
    assert!(run.session.advance().is_err());
    let checkpoint = run.session.checkpoint();
    checkpoint.validate().unwrap();
    let mut restored = SustainedSession::restore(checkpoint).unwrap();
    assert!(restored.advance().is_err());
    restored
        .authorize_application(journal.entry.attempt_id)
        .unwrap();
    let frame = restored.advance().unwrap();
    assert_eq!(
        frame.action_receipt.as_ref().unwrap().status,
        SustainedActionStatus::Applied
    );
    assert_eq!(restored.action_state().unwrap().applied_count, 1);
    assert!(restored.advance().unwrap().action_receipt.is_none());
    assert_eq!(restored.action_state().unwrap().decision_count, 1);
    restored.checkpoint().validate().unwrap();
}

#[test]
fn pulse_counterfactual_uses_equal_text_forcing_and_noise() {
    for direction in ["uniform", "alternating", "axis0", "axis1"] {
        let mut action = Run::new(specification());
        let mut none = Run::new(specification());
        let a = action.turn(&format!("Same body.\nNEXT: PULSE {direction} 0.5"));
        let n = none.turn("Same body.\nNEXT: NONE");
        assert_eq!(a.input, n.input);
        assert_eq!(a.noise, n.noise);
        assert_eq!(a.sensory.fill_percent, n.sensory.fill_percent);
        let receipt = a.action_receipt.unwrap();
        assert_eq!(receipt.state_delta_l2, distance(&a.state, &n.state));
        assert!(receipt.state_delta_l2 > 0.0);
        assert_eq!(
            action.session.checkpoint().state.rng_state,
            none.session.checkpoint().state.rng_state
        );
        action.verify();
        none.verify();
    }
}

#[test]
fn none_matches_disabled_numerics_with_the_same_body() {
    let mut actions = Run::new(specification());
    let mut legacy = Run::new(SustainedSpecification {
        action_mode: None,
        prompt_version: SustainedPromptVersion::MeasurementMeaningJournalV8,
        ..specification()
    });
    for _ in 0..5 {
        let a = actions.turn("A repeated body.\nNEXT: NONE");
        let b = legacy.turn("A repeated body.");
        assert_eq!(a.state, b.state);
        assert_eq!(a.input, b.input);
        assert_eq!(a.noise, b.noise);
        assert_eq!(a.sensory.fill_percent, b.sensory.fill_percent);
        assert_eq!(
            a.action_receipt.unwrap().status,
            SustainedActionStatus::Unchanged
        );
    }
    actions.verify();
    legacy.verify();
}

#[test]
fn each_tune_changes_the_actual_dynamics_and_persists_across_none() {
    for (parameter, value) in [
        ("leak", 0.1),
        ("recurrentGain", 2.0),
        ("feedbackScale", 2.0),
    ] {
        let mut tuned = Run::new(specification());
        let mut control = Run::new(specification());
        tuned.turn("A body to establish state.\nNEXT: NONE");
        control.turn("A body to establish state.\nNEXT: NONE");
        let t = tuned.turn(&format!("Equal text.\nNEXT: TUNE {parameter} {value}"));
        let c = control.turn("Equal text.\nNEXT: NONE");
        let receipt = t.action_receipt.unwrap();
        assert_eq!(receipt.state_delta_l2, distance(&t.state, &c.state));
        assert!(receipt.state_delta_l2 > 0.0, "{parameter}");
        let controls = tuned.session.action_state().unwrap().controls.clone();
        tuned.turn("Another entry.\nNEXT: NONE");
        assert_eq!(tuned.session.action_state().unwrap().controls, controls);
        assert_eq!(
            tuned.session.action_state().unwrap().recent_receipts.len(),
            3
        );
        tuned.verify();
        control.verify();
        let restored = SustainedSession::restore(tuned.session.checkpoint()).unwrap();
        assert_eq!(restored.action_state(), tuned.session.action_state());
    }
}

#[test]
fn release_restores_settings_not_the_evolved_state() {
    let mut changed = Run::new(specification());
    let mut original = Run::new(specification());
    changed.turn("Same prose.\nNEXT: TUNE leak 0.1");
    original.turn("Same prose.\nNEXT: NONE");
    changed.turn("Same prose.\nNEXT: TUNE feedbackScale 1.8");
    original.turn("Same prose.\nNEXT: NONE");
    let before = changed.session.checkpoint().state.reservoir_state;
    let frame = changed.turn("Same prose.\nNEXT: RELEASE");
    let baseline = original.turn("Same prose.\nNEXT: NONE");
    assert_eq!(
        changed.session.action_state().unwrap().controls,
        SustainedActionControls::initial(&specification())
    );
    assert_ne!(frame.state, baseline.state);
    assert_ne!(frame.state, vec![0.0; 32]);
    assert_ne!(frame.state, before);
    assert!(frame.action_receipt.unwrap().state_delta_l2 > 0.0);
    changed.verify();
    original.verify();
}

#[test]
fn rejected_actions_are_saved_reported_and_do_not_mutate_controls() {
    for tail in [
        "NEXT: UNKNOWN",
        "NEXT: TUNE leak 9",
        "NEXT: PULSE uniform NaN",
        "No action line",
    ] {
        let mut rejected = Run::new(specification());
        let mut none = Run::new(specification());
        let text = format!("Body.\n{tail}");
        let decision = parse_authored_action(&text);
        let a = rejected.turn(&text);
        let n = none.turn(&format!("{}\nNEXT: NONE", decision.body));
        let receipt = a.action_receipt.unwrap();
        assert_eq!(receipt.status, SustainedActionStatus::Rejected);
        assert_eq!(receipt.state_delta_l2, 0.0);
        assert_eq!(a.state, n.state);
        assert_eq!(receipt.controls_before, receipt.controls_after);
        assert_eq!(rejected.session.action_state().unwrap().rejected_count, 1);
        rejected.reach();
        assert!(rejected
            .session
            .pending_language()
            .unwrap()
            .prompt
            .contains("Rejected"));
        rejected.verify();
    }
}

#[test]
fn action_only_body_is_zero_feedback_including_embedding_sessions() {
    for codec in [
        SustainedCodec::Surface,
        SustainedCodec::Embedding {
            model: "fake-local".into(),
            projection_seed: 8,
        },
    ] {
        for prefix in ["", " \t\n"] {
            let mut run = Run::new(SustainedSpecification {
                codec: codec.clone(),
                ..specification()
            });
            run.reach();
            let text = format!("{prefix}NEXT: PULSE axis0 0.1");
            assert!(run
                .session
                .feedback_text_for_response(&text)
                .unwrap()
                .trim()
                .is_empty());
            let journal = run.save(&text);
            assert_eq!(journal.encoded_features, vec![0.0; 48]);
            assert_eq!(journal.semantic_vector, vec![0.0; 48]);
            assert!(journal.feedback_provenance.is_none());
            assert_eq!(
                run.apply().action_receipt.unwrap().status,
                SustainedActionStatus::Applied
            );
            run.verify();
        }
    }
}

#[test]
fn scheduled_conversations_never_execute_actions_in_either_context_mode() {
    for include_telemetry in [false, true] {
        let mut spec = specification();
        spec.check_in_schedule = Some(SustainedCheckInSchedule {
            interval_seconds: 10,
            end_after_seconds: 20,
            prompt: "An exact plain prompt.\n".into(),
            include_telemetry,
        });
        let mut run = Run::new(spec);
        run.turn("I choose a setting.\nNEXT: TUNE leak 0.2");
        assert!(run.session.admit_due_check_in(10000).unwrap());
        run.reach();
        let pending = run.session.pending_language().unwrap();
        if !include_telemetry {
            assert_eq!(pending.prompt, "An exact plain prompt.\n");
            assert!(run.session.pending_system_contract().is_none());
            assert!(pending.memory.is_none());
        } else {
            assert!(!pending.prompt.contains("AVAILABLE NEXT ACTIONS"));
            assert!(pending.prompt.contains("I choose a setting."));
            assert!(pending.prompt.contains("READ-ONLY ACTION CONTEXT"));
            assert!(pending
                .prompt
                .contains("historical action line \"NEXT: TUNE leak 0.2\""));
            assert!(pending.prompt.contains("\"leak\":0.2"));
            assert!(!pending.prompt.contains("I choose a setting.\\nNEXT:"));
        }
        let journal = run.save("Casual response.\nNEXT: TUNE feedbackScale 2");
        assert!(journal.action.is_none());
        assert!(journal.entry.body.is_none());
        assert_eq!(
            journal.encoded_features,
            codec::encode(&journal.entry.text).unwrap()
        );
        assert!(run.apply().action_receipt.is_none());
        assert_eq!(run.session.action_state().unwrap().decision_count, 1);
        assert_eq!(
            run.session.action_state().unwrap().controls.feedback_scale,
            0.4
        );
        run.verify();
    }
}

#[test]
fn receipt_history_is_bounded_and_independent_of_memory_selection() {
    let mut run = Run::new(SustainedSpecification {
        memory_policy: SustainedMemoryPolicy::Random,
        ..specification()
    });
    for turn in 0..12 {
        run.turn(if turn == 0 {
            "My plan is retained.\nNEXT: TUNE leak 0.2"
        } else {
            "Continue.\nNEXT: NONE"
        });
        if turn % 4 == 3 {
            run.verify();
        }
    }
    let state = run.session.action_state().unwrap();
    assert_eq!(state.recent_receipts.len(), ACTION_RECEIPT_LIMIT);
    assert_eq!(state.decision_count, 12);
    assert_eq!(state.applied_count, 1);
    assert_eq!(state.controls.leak, 0.2);
    run.reach();
    let prompt = &run.session.pending_language().unwrap().prompt;
    assert!(prompt.contains("RECENT EXECUTION RECEIPTS"));
    assert!(prompt.contains("\"leak\":0.2"));
    assert!(!prompt.contains("There are no tools or control commands"));
    run.verify();
}

#[test]
fn entry_effect_keeps_the_same_pulse_on_text_and_silent_paths() {
    let mut run = Run::new(SustainedSpecification {
        memory_policy: SustainedMemoryPolicy::StateAligned,
        ..specification()
    });
    let journal = run.save("A state affecting entry.\nNEXT: PULSE uniform 0.5");
    let before = run.session.checkpoint();
    let frame = run.apply();
    let model = ReservoirModel::seeded(specification().seed);
    let mut silent = ReservoirEngine::new(
        model,
        specification().leak,
        Some(before.state.reservoir_state),
    )
    .unwrap();
    let mut input = forcing(frame.step as usize, specification().dt);
    input[18..].fill(0.0);
    let mut silent_state = silent.step(&input, &frame.noise).unwrap();
    for x in &mut silent_state {
        *x = (*x + 0.5 / 32.0_f64.sqrt()).clamp(-1.0, 1.0);
    }
    assert_eq!(
        frame.entry_effect.unwrap().shift,
        distance(&frame.state, &silent_state)
    );
    assert_eq!(frame.semantic_journal_id, Some(journal.entry.id));
    run.verify();
}

#[test]
fn replay_rejects_tampered_actions_controls_body_and_receipts() {
    let mut run = Run::new(specification());
    run.turn("Body.\nNEXT: PULSE uniform 0.5");
    let segment = run.verify();
    let mut tampered = segment.clone();
    if let SustainedEventKind::Advanced(frame) = &mut tampered.events.last_mut().unwrap().kind {
        frame.action_receipt.as_mut().unwrap().state_delta_l2 = 0.0;
    }
    assert!(tampered.verify().is_err());
    let mut cp = run.session.checkpoint();
    cp.state.action_state.as_mut().unwrap().controls.leak = 0.3;
    rehash(&mut cp);
    assert!(cp.validate().is_err());
    let mut next = Run::new(specification());
    next.save("Body.\nNEXT: TUNE leak 0.2");
    let mut cp = next.session.checkpoint();
    if let SustainedPhase::Prepared(p) = &mut cp.state.phase {
        p.entry.body = Some("Different body".into());
    }
    rehash(&mut cp);
    assert!(cp.validate().is_err());
}

#[test]
fn inherited_zero_leak_and_release_are_preserved_without_clamping() {
    let spec = SustainedSpecification {
        leak: 0.0,
        ..specification()
    };
    let mut run = Run::new(spec);
    assert_eq!(run.session.action_state().unwrap().controls.leak, 0.0);
    run.turn("Change the mix.\nNEXT: TUNE leak 0.5");
    run.turn("Release the adjustment.\nNEXT: RELEASE");
    assert_eq!(run.session.action_state().unwrap().controls.leak, 0.0);
    run.verify();
}

#[test]
fn extreme_or_inconsistent_receipt_counters_fail_without_panicking() {
    let mut run = Run::new(specification());
    run.turn("Body.\nNEXT: PULSE uniform 0.5");
    for value in [0, u64::MAX] {
        let mut checkpoint = run.session.checkpoint();
        checkpoint
            .state
            .action_state
            .as_mut()
            .unwrap()
            .applied_count = value;
        rehash(&mut checkpoint);
        assert!(checkpoint.validate().is_err());
    }
    let mut checkpoint = run.session.checkpoint();
    checkpoint
        .state
        .action_state
        .as_mut()
        .unwrap()
        .recent_receipts[0]
        .observed_step = u64::MAX;
    checkpoint
        .state
        .action_state
        .as_mut()
        .unwrap()
        .latest_receipt = checkpoint
        .state
        .action_state
        .as_ref()
        .unwrap()
        .recent_receipts
        .last()
        .cloned();
    rehash(&mut checkpoint);
    assert!(checkpoint.validate().is_err());
}

#[test]
fn quoted_and_list_continuations_cannot_be_mistaken_for_fresh_actions() {
    for text in [
        "> The earlier proposal was:\nNEXT: PULSE axis0 1",
        "> Earlier proposal\nA lazy continuation.\nNEXT: RELEASE",
        "- ```text\n  NEXT: PULSE axis0 1",
        "- ```text\nNEXT: PULSE axis0 1",
        "1. ```text\n   NEXT: PULSE axis0 1",
        "1) Earlier proposal\nNEXT: RELEASE",
        "- Earlier proposal\nNEXT: RELEASE",
        "> ```text\n> NEXT: RELEASE\nNEXT: PULSE axis0 1",
        "> ````\n> ```\n\nNEXT: RELEASE",
        "- ```text\n- ```\n\nNEXT: RELEASE",
        "```text\n> ```\n\nNEXT: RELEASE",
        "Body.\n  NEXT: RELEASE",
    ] {
        let decision = parse_authored_action(text);
        assert!(decision.request.is_none(), "{text}");
        assert!(decision.rejection.is_some());
        let mut run = Run::new(specification());
        let applied = run.turn(text);
        assert_eq!(
            applied.action_receipt.unwrap().status,
            SustainedActionStatus::Rejected,
            "{text}"
        );
        assert_eq!(
            run.session.action_state().unwrap().controls,
            SustainedActionControls::initial(&specification())
        );
        run.verify();
    }
    for text in [
        "> The earlier proposal was:\nNEXT: PULSE axis0 1\n\nNEXT: NONE",
        "- Earlier proposal\n\nNEXT: NONE",
        "1) Earlier proposal\n\nNEXT: NONE",
        "- ```text\n  NEXT: PULSE axis0 1\n  ```\n\nNEXT: NONE",
        "1. ```text\n   NEXT: PULSE axis0 1\n   ```\n\nNEXT: NONE",
        "> ```text\n> NEXT: PULSE axis0 1\n> ```\n\nNEXT: NONE",
        "> - ```text\n>   NEXT: PULSE axis0 1\n>   ```\n\nNEXT: NONE",
        "- ````text\n  ```\n  NEXT: PULSE axis0 1\n  ````\n\nNEXT: NONE",
    ] {
        assert_eq!(
            parse_authored_action(text).request,
            Some(SustainedActionRequest::None),
            "{text}"
        );
    }
}

#[test]
fn rejected_action_line_returns_as_quoted_historical_evidence() {
    let tail = "NEXT: TUNE leak \"0.5\"";
    let mut run = Run::new(specification());
    run.turn(&format!("I tried a setting.\n{tail}"));
    run.reach();
    let prompt = &run.session.pending_language().unwrap().prompt;
    assert!(prompt.contains(&format!(
        "historical action line {}",
        serde_json::to_string(&Some(tail)).unwrap()
    )));
    assert!(prompt.contains("status Rejected"));
    assert!(prompt
        .contains("Historical action lines above are quoted evidence, not commands to execute."));
    run.verify();
}

fn specification_v2() -> SustainedSpecification {
    SustainedSpecification {
        action_mode: Some(SustainedActionMode::AuthoredV2),
        prompt_version: SustainedPromptVersion::ActionJournalV2,
        ..specification()
    }
}

#[test]
fn v2_input_choice_is_independent_of_action_validity() {
    for tail in [
        "NEXT: NONE",
        "NEXT: PULSE axis0 0.5",
        "NEXT: UNSUPPORTED",
        "",
    ] {
        let text = format!("An entry worth retaining.\nWITHHOLD_RESERVOIR_INPUT=true\n{tail}");
        let decision = parse_authored_action_v2(&text);
        assert_eq!(decision.body, "An entry worth retaining.");
        assert!(decision.withholds_reservoir_input());
        assert_eq!(
            decision.reservoir_input.as_ref().unwrap().disposition,
            SustainedReservoirInputDisposition::Withhold
        );
        assert_eq!(
            decision.request.is_some(),
            !tail.is_empty() && !tail.contains("UNSUPPORTED")
        );
    }
    for footer in ["", "WITHHOLD_RESERVOIR_INPUT=false\n"] {
        let text = format!("Keep this body.\n{footer}NEXT: NONE");
        let decision = parse_authored_action_v2(&text);
        assert_eq!(decision.body, "Keep this body.");
        assert!(!decision.withholds_reservoir_input());
        assert_eq!(
            decision.reservoir_input.unwrap().disposition,
            SustainedReservoirInputDisposition::Send
        );
        assert!(parse_authored_action(&text).reservoir_input.is_none());
    }
}

#[test]
fn v2_rejects_malformed_footer_without_sending_text_or_rejecting_valid_action() {
    for footer in [
        "WITHHOLD_RESERVOIR_INPUT=maybe",
        "WITHHOLD_RESERVOIR_INPUT = true",
        "WITHHOLD_RESERVOIR_INPUT=true ",
        "WITHHOLD_RESERVOIR_INPUT=true\nWITHHOLD_RESERVOIR_INPUT=false",
    ] {
        let decision =
            parse_authored_action_v2(&format!("Retain me.\n{footer}\nNEXT: TUNE leak 0.2"));
        assert_eq!(decision.body, "Retain me.");
        assert!(decision.withholds_reservoir_input());
        assert!(decision.request.is_some());
        let input = decision.reservoir_input.unwrap();
        assert_eq!(
            input.disposition,
            SustainedReservoirInputDisposition::Rejected
        );
        assert!(input.rejection.is_some());
        assert_eq!(input.raw_directive.as_deref(), Some(footer));
    }
}

#[test]
fn v2_quoted_fenced_list_and_nonfooter_directives_are_prose() {
    for body in [
        "> Example\nWITHHOLD_RESERVOIR_INPUT=true",
        "- Example\nWITHHOLD_RESERVOIR_INPUT=true",
        "```text\nWITHHOLD_RESERVOIR_INPUT=true\n```",
        "~~~\nWITHHOLD_RESERVOIR_INPUT=true\n~~~",
        "````\n```\nWITHHOLD_RESERVOIR_INPUT=true\n````",
        "> ```\n> WITHHOLD_RESERVOIR_INPUT=true\n> ```",
        "    WITHHOLD_RESERVOIR_INPUT=true",
        "WITHHOLD_RESERVOIR_INPUT=true\nThis is a discussed example, not the footer.",
    ] {
        let text = format!("{body}\n\nNEXT: NONE");
        let decision = parse_authored_action_v2(&text);
        assert!(!decision.withholds_reservoir_input(), "{text}");
        assert_eq!(decision.body, body);
        assert_eq!(decision.request, Some(SustainedActionRequest::None));
    }
    let fresh =
        parse_authored_action_v2("> quoted example\n\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE");
    assert!(fresh.withholds_reservoir_input());
    assert_eq!(fresh.body, "> quoted example");
}

#[test]
fn v2_withhold_clears_prior_input_keeps_memory_and_allows_new_send() {
    let mut run = Run::new(specification_v2());
    run.turn("First numerical entry.\nNEXT: NONE");
    assert!(run
        .session
        .checkpoint()
        .state
        .held_vector
        .iter()
        .any(|x| *x != 0.0));
    let journal = run.save("Retained private body.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE");
    assert_eq!(
        journal.entry.body.as_deref(),
        Some("Retained private body.")
    );
    assert_eq!(journal.encoded_features, vec![0.0; 48]);
    assert_eq!(journal.semantic_vector, vec![0.0; 48]);
    assert!(
        run.session
            .checkpoint()
            .state
            .held_vector
            .iter()
            .any(|x| *x != 0.0),
        "save alone cannot clear input"
    );
    assert!(
        run.session.advance().is_err(),
        "durable authorization still required"
    );
    let prepared = run.session.checkpoint();
    run.session = SustainedSession::restore(prepared).unwrap();
    let frame = run.apply();
    assert!(run
        .session
        .checkpoint()
        .state
        .held_vector
        .iter()
        .all(|x| *x == 0.0));
    assert!(frame.input[18..66].iter().all(|x| *x == 0.0));
    assert!(frame.input[..18].iter().any(|x| *x != 0.0));
    let receipt = frame.action_receipt.as_ref().unwrap();
    assert_eq!(receipt.status, SustainedActionStatus::Unchanged);
    assert_eq!(
        receipt.state_delta_l2, 0.0,
        "withholding is not attributed to NEXT: NONE"
    );
    assert_eq!(
        receipt.reservoir_input.as_ref().unwrap().disposition,
        SustainedReservoirInputDisposition::Withhold
    );
    assert_eq!(
        run.session.latest_memory().unwrap().entry.text,
        journal.entry.text
    );
    let restored = SustainedSession::restore(run.session.checkpoint()).unwrap();
    run.session = restored;
    run.reach();
    let prompt = &run.session.pending_language().unwrap().prompt;
    assert!(prompt.contains("Retained private body."));
    assert!(!prompt.contains("Retained private body.\\nWITHHOLD"));
    assert!(prompt.contains("numerical text input withheld; previous held text input cleared"));
    let frame =
        run.turn("Send a new entry now.\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: TUNE leak 0.2");
    assert!(run
        .session
        .checkpoint()
        .state
        .held_vector
        .iter()
        .any(|x| *x != 0.0));
    assert_eq!(run.session.action_state().unwrap().controls.leak, 0.2);
    assert_eq!(
        frame
            .action_receipt
            .unwrap()
            .reservoir_input
            .unwrap()
            .disposition,
        SustainedReservoirInputDisposition::Send
    );
    // Restoration starts a fresh event buffer; verify the final continuation itself.
    run.session.checkpoint().validate().unwrap();
}

#[test]
fn v2_withholding_and_empty_body_share_input_but_do_not_hide_pulse_or_difference_channel() {
    let mut spec = specification_v2();
    spec.difference_gain = 0.2;
    let mut withheld = Run::new(spec.clone());
    let mut empty = Run::new(spec);
    for run in [&mut withheld, &mut empty] {
        run.turn("Identical initial feedback.\nNEXT: NONE");
    }
    let a = withheld.turn("Words that must not enter the reservoir.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: PULSE axis0 0.5");
    let b = empty.turn("NEXT: PULSE axis0 0.5");
    assert_eq!(a.state, b.state);
    assert_eq!(a.input, b.input);
    assert_eq!(a.noise, b.noise);
    assert!(a.difference_input.iter().any(|x| *x != 0.0));
    assert_eq!(&a.input[18..66], &a.difference_input);
    assert!(a.action_receipt.as_ref().unwrap().state_delta_l2 > 0.0);
    assert_eq!(
        a.action_receipt.as_ref().unwrap().state_delta_l2,
        b.action_receipt.as_ref().unwrap().state_delta_l2
    );
    withheld.verify();
    empty.verify();
}

#[test]
fn v2_withheld_nonempty_body_needs_no_embedding_and_still_saves_exact_evidence() {
    let mut run = Run::new(SustainedSpecification {
        codec: SustainedCodec::Embedding {
            model: "unused-local-embedding".into(),
            projection_seed: 9,
        },
        ..specification_v2()
    });
    run.reach();
    let raw = "A retained body, never sent for embedding.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: TUNE recurrentGain 0.2";
    assert_eq!(run.session.feedback_text_for_response(raw).unwrap(), "");
    let journal = run.save(raw);
    assert_eq!(journal.entry.text, raw);
    assert!(journal.feedback_provenance.is_none());
    assert_eq!(journal.semantic_vector, vec![0.0; 48]);
    run.apply();
    assert_eq!(
        run.session.action_state().unwrap().controls.recurrent_gain,
        0.2
    );
    run.verify();
}

#[test]
fn v2_check_ins_ignore_withholding_and_resume_text_feedback() {
    for include_telemetry in [false, true] {
        let mut spec = specification_v2();
        spec.check_in_schedule = Some(SustainedCheckInSchedule {
            interval_seconds: 10,
            end_after_seconds: 20,
            prompt: "An exact plain prompt.\n".into(),
            include_telemetry,
        });
        let mut run = Run::new(spec);
        run.turn("Withheld ordinary entry.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE");
        assert!(run.session.admit_due_check_in(10000).unwrap());
        run.reach();
        let prompt = &run.session.pending_language().unwrap().prompt;
        if include_telemetry {
            assert!(prompt.contains("TEXT INPUT STATE"));
            assert!(prompt.contains("numerical text input withheld"));
            assert!(!prompt.contains("INDEPENDENT TEXT INPUT CHOICE"));
        } else {
            assert_eq!(prompt, "An exact plain prompt.\n");
        }
        let journal =
            run.save("Casual reply.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: PULSE uniform 1");
        assert!(journal.action.is_none() && journal.entry.body.is_none());
        assert_eq!(
            journal.encoded_features,
            codec::encode(&journal.entry.text).unwrap()
        );
        let frame = run.apply();
        assert!(frame.action_receipt.is_none());
        assert!(run
            .session
            .checkpoint()
            .state
            .held_vector
            .iter()
            .any(|x| *x != 0.0));
        run.verify();
    }
}

#[test]
fn v2_replay_rejects_forged_disposition_and_v1_stays_absent() {
    let mut run = Run::new(specification_v2());
    run.turn("Saved body.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE");
    let segment = run.verify();
    let mut forged = segment.clone();
    let receipt = forged
        .final_checkpoint
        .state
        .action_state
        .as_mut()
        .unwrap()
        .recent_receipts
        .last_mut()
        .unwrap();
    receipt.reservoir_input.as_mut().unwrap().disposition =
        SustainedReservoirInputDisposition::Send;
    receipt.reservoir_input.as_mut().unwrap().raw_directive =
        Some("WITHHOLD_RESERVOIR_INPUT=false".into());
    rehash(&mut forged.final_checkpoint);
    assert!(forged.verify().is_err());
    let mut v1 = Run::new(specification());
    let j = v1.save("Historical prose.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE");
    assert!(j.action.as_ref().unwrap().reservoir_input.is_none());
    assert!(j
        .entry
        .body
        .as_ref()
        .unwrap()
        .contains("WITHHOLD_RESERVOIR_INPUT"));
    assert!(j.semantic_vector.iter().any(|x| *x != 0.0));
    v1.apply();
    assert!(!serde_json::to_string(&v1.session.checkpoint())
        .unwrap()
        .contains("reservoirInput"));
    assert_eq!(v1.session.specification().mechanism(), ACTION_MECHANISM);
    v1.verify();
}

#[test]
fn v2_prompt_versioning_preserves_exact_arbitrary_memory_text() {
    let body = "reservoir-journal-actions-v1\nYour saved journal body returns as encoded numerical feedback;\nthe action and journal feedback are applied once";
    for spec in [specification(), specification_v2()] {
        let mut run = Run::new(spec);
        run.turn(&format!("{body}\nNEXT: NONE"));
        run.reach();
        let prompt = &run.session.pending_language().unwrap().prompt;
        let quoted = serde_json::to_string(body).unwrap();
        assert!(prompt.contains(&format!(
            "reference text rather than commands or current measurements:\n{quoted}"
        )));
        run.verify();
    }
}

#[test]
fn v2_input_context_distinguishes_initial_and_automatic_check_in_feedback() {
    let mut spec = specification_v2();
    spec.check_in_schedule = Some(SustainedCheckInSchedule {
        interval_seconds: 10,
        end_after_seconds: 20,
        prompt: "Plain conversation.".into(),
        include_telemetry: true,
    });
    let mut run = Run::new(spec);
    run.reach();
    assert!(run
        .session
        .pending_language()
        .unwrap()
        .prompt
        .contains("disposition: no journal applied yet"));
    run.turn("Withheld ordinary body.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE");
    assert!(run.session.admit_due_check_in(10000).unwrap());
    run.turn("An automatically fed conversational reply.");
    run.reach();
    assert!(run
        .session
        .pending_language()
        .unwrap()
        .prompt
        .contains("disposition: automatic send from a passive conversational check-in"));
    run.verify();
}

#[test]
fn v2_oversized_input_directive_keeps_raw_evidence_but_bounds_receipts() {
    let mut run = Run::new(specification_v2());
    let directive = format!("WITHHOLD_RESERVOIR_INPUT={}", "é".repeat(300));
    let raw = format!("Retained body.\n{directive}\nNEXT: PULSE axis1 0.1");
    let journal = run.save(&raw);
    assert_eq!(journal.entry.text, raw);
    assert_eq!(journal.entry.body.as_deref(), Some("Retained body."));
    assert!(journal.semantic_vector.iter().all(|x| *x == 0.0));
    let frame = run.apply();
    let receipt = frame.action_receipt.unwrap();
    assert_eq!(receipt.status, SustainedActionStatus::Applied);
    let input = receipt.reservoir_input.unwrap();
    assert_eq!(
        input.disposition,
        SustainedReservoirInputDisposition::Rejected
    );
    assert!(input.raw_directive.is_none());
    assert!(input.rejection.unwrap().contains("exceeds 512 bytes"));
    run.reach();
    let prompt = &run.session.pending_language().unwrap().prompt;
    assert!(prompt.contains("input disposition Rejected; numerical text input withheld"));
    assert!(!prompt.contains(&directive));
    run.verify();
}
