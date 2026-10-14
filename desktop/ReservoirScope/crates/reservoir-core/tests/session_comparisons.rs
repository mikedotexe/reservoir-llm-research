use reservoir_core::{
    actions::*,
    comparison::ActionComparisonSession,
    stage::{RunStatus, TurnStatus},
};

fn spec(stage: u8, mode: ComparisonMode) -> ActionSpecification {
    let mut spec: ActionSpecification = serde_json::from_value(serde_json::json!({
        "stage":stage,"steps":11,"turnEvery":3,"seed":18446744073709551615u64,
        "comparePrevious":true,"promptVersion":2,"inputStrength":0.8,"noiseAmplitude":0.013,"biasEnabled":true
    })).unwrap();
    spec.mode = mode;
    spec
}
fn observation(quiet: bool) -> ActionSpecification {
    let mut s = spec(4, ComparisonMode::IndependentGeneration);
    s.comparison_kind = ComparisonKind::Observation;
    s.forcing_profile = ForcingProfile::ContinuousSensoryV1;
    if quiet {
        s.input_strength = 0.0;
        s.bias_enabled = false;
        s.noise_amplitude = 0.0;
    }
    s
}
fn save(s: &mut ActionComparisonSession) {
    let (arm, p) = s.pending_journal().map(|(a, p)| (a, p.clone())).unwrap();
    let receipt = JournalSaveReceipt {
        status: SaveStatus::Saved,
        entry_id: p.entry.id.clone(),
        sha256: p.entry.sha256.clone(),
        relative_path: Some(p.relative_path),
        failure: None,
    };
    s.confirm_saved(arm, &receipt, &p.entry).unwrap();
}
fn resolve(s: &mut ActionComparisonSession) {
    loop {
        if let Some((arm, p)) = s.pending_memory().map(|(a, p)| (a, p.clone())) {
            s.confirm_memory(arm, &p.entry).unwrap();
        } else if s.pending_journal().is_some() {
            save(s);
        } else {
            break;
        }
    }
}
fn to(s: &mut ActionComparisonSession, step: usize) {
    while s.frames(Arm::Right).len() < step {
        s.advance().unwrap();
        resolve(s);
    }
}

#[test]
fn all_fourteen_component_pairs_preserve_native_tracks_ordinals_and_tapes() {
    for mode in [
        ComparisonMode::IndependentGeneration,
        ComparisonMode::FixedReplay,
    ] {
        for stage in 2..=8 {
            let mut s = ActionComparisonSession::new(spec(stage, mode)).unwrap();
            to(&mut s, 11);
            let r = s.record().unwrap();
            r.verify().unwrap();
            let left = r.left.as_ref().unwrap();
            assert_eq!((left.stage, r.right.stage), (stage - 1, stage));
            assert_eq!(r.status, RunStatus::Completed);
            assert_eq!(left.frames.len(), r.right.frames.len());
            if stage < 4 {
                assert!(left.actions.is_empty() && r.right.actions.is_empty());
            }
            if stage == 4 {
                assert!(left.actions.is_empty());
            }
            for a in &r.right.actions {
                assert_eq!(
                    a.request_order,
                    if mode == ComparisonMode::FixedReplay {
                        None
                    } else {
                        Some(if stage == 4 { 1 } else { 2 })
                    }
                );
            }
            for a in &left.actions {
                assert_eq!(
                    a.request_order,
                    if mode == ComparisonMode::FixedReplay {
                        None
                    } else {
                        Some(1)
                    }
                );
                if let Some(receipt) = &a.save_receipt {
                    assert!(receipt.relative_path.as_ref().unwrap().starts_with("left/"));
                }
            }
            if stage == 8 && mode == ComparisonMode::FixedReplay {
                for (a, b) in left.frames.iter().zip(&r.right.frames) {
                    assert_eq!(a.input, b.input);
                    assert_eq!(a.state, b.state);
                }
                assert_ne!(
                    left.frames[1].retention_used,
                    r.right.frames[1].retention_used
                );
            }
        }
    }
}

#[test]
fn observation_matches_numerics_changes_exposure_and_alternates_real_order() {
    for quiet in [false, true] {
        let mut s = ActionComparisonSession::new(observation(quiet)).unwrap();
        to(&mut s, 2);
        s.advance().unwrap();
        assert_eq!(s.pending_journal().unwrap().0, Arm::Left);
        save(&mut s);
        assert_eq!(s.pending_journal().unwrap().0, Arm::Right);
        save(&mut s);
        to(&mut s, 5);
        s.advance().unwrap();
        assert_eq!(s.pending_journal().unwrap().0, Arm::Right);
        save(&mut s);
        assert_eq!(s.pending_journal().unwrap().0, Arm::Left);
        save(&mut s);
        to(&mut s, 11);
        let r = s.record().unwrap();
        r.verify().unwrap();
        let l = r.left.unwrap();
        for (a, b) in l.frames.iter().zip(&r.right.frames) {
            assert_eq!(a.input, b.input);
            assert_eq!(a.state, b.state);
            assert_eq!(
                a.spectral.as_ref().unwrap().covariance,
                b.spectral.as_ref().unwrap().covariance
            );
            assert!(a.semantic_action_id.is_none() && b.semantic_action_id.is_none());
            if quiet {
                assert!(a.input.iter().all(|x| *x == 0.0));
                assert!(a.state.iter().all(|x| *x == 0.0));
            }
        }
        assert_eq!(
            l.actions
                .iter()
                .map(|a| a.request_order)
                .collect::<Vec<_>>(),
            vec![Some(1), Some(2), Some(1)]
        );
        assert_eq!(
            r.right
                .actions
                .iter()
                .map(|a| a.request_order)
                .collect::<Vec<_>>(),
            vec![Some(2), Some(1), Some(2)]
        );
        assert!(!l.actions[0].prompt.contains("x[0]="));
        assert!(r.right.actions[0].prompt.contains("x[0]="));
    }
}

#[test]
fn ordered_save_gate_rejects_wrong_arm_path_and_blocks_both_clocks() {
    let mut s =
        ActionComparisonSession::new(spec(5, ComparisonMode::IndependentGeneration)).unwrap();
    to(&mut s, 2);
    let f = s.advance().unwrap();
    assert_eq!((f.left.step, f.right.step), (3, 3));
    let (arm, p) = s.pending_journal().map(|(a, p)| (a, p.clone())).unwrap();
    assert_eq!(arm, Arm::Left);
    assert!(s.record().is_err() && s.advance().is_err() && !s.can_request_action());
    let mut receipt = JournalSaveReceipt {
        status: SaveStatus::Saved,
        entry_id: p.entry.id.clone(),
        sha256: p.entry.sha256.clone(),
        relative_path: Some(p.relative_path),
        failure: None,
    };
    assert!(s.confirm_saved(Arm::Right, &receipt, &p.entry).is_err());
    receipt.relative_path = Some(format!("right/{}.json", p.entry.id));
    assert!(s.confirm_saved(Arm::Left, &receipt, &p.entry).is_err());
    assert!(s.actions(Arm::Left).is_empty() && s.actions(Arm::Right).is_empty());
    save(&mut s);
    assert_eq!(s.journals(Arm::Left).len(), 1);
    assert!(s.journals(Arm::Right).is_empty());
    assert!(s.record().is_err() && s.advance().is_err());
    save(&mut s);
    let r = s.record().unwrap();
    r.verify().unwrap();
    assert_eq!(r.left.unwrap().actions[0].application_step, None);
    assert_eq!(r.right.actions[0].application_step, None);
    s.advance().unwrap();
    assert_eq!(s.actions(Arm::Right)[0].application_step, Some(4));
    assert_eq!(s.actions(Arm::Left)[0].application_step, None);
}

#[test]
fn component_failure_cancels_unstarted_peer_or_retains_successful_first_arm() {
    for mode in [
        ComparisonMode::IndependentGeneration,
        ComparisonMode::FixedReplay,
    ] {
        for fail_arm in [Arm::Left, Arm::Right] {
            let mut s = ActionComparisonSession::new(spec(5, mode)).unwrap();
            to(&mut s, 2);
            s.advance().unwrap();
            if fail_arm == Arm::Right {
                save(&mut s);
            }
            s.fail_pending(fail_arm, "Actual save failure finalized")
                .unwrap();
            assert!(s.is_failed() && s.pending_journal().is_none() && s.advance().is_err());
            let r = s.record().unwrap();
            r.verify().unwrap();
            let l = r.left.unwrap();
            assert_eq!(r.status, RunStatus::Failed);
            if fail_arm == Arm::Left {
                assert_eq!(r.right.actions[0].status, TurnStatus::Cancelled);
                assert!(!r.right.actions[0].request_started);
                assert!(r.right.actions[0].raw_reply.is_none());
                assert!(l.journals.is_empty() && r.right.journals.is_empty());
            } else {
                assert_eq!(l.journals.len(), 1);
                assert!(r.right.journals.is_empty());
            }
        }
    }
}

#[test]
fn observation_failure_still_attempts_partner_in_both_orders() {
    for step in [3, 6] {
        let mut s = ActionComparisonSession::new(observation(false)).unwrap();
        to(&mut s, step - 1);
        s.advance().unwrap();
        let first = if step == 3 { Arm::Left } else { Arm::Right };
        let second = if first == Arm::Left {
            Arm::Right
        } else {
            Arm::Left
        };
        s.fail_pending(first, "Actual first-arm save failure")
            .unwrap();
        assert!(s.is_failed());
        assert_eq!(s.pending_journal().unwrap().0, second);
        assert!(s.record().is_err());
        save(&mut s);
        let r = s.record().unwrap();
        r.verify().unwrap();
        assert_eq!(s.actions(second).last().unwrap().request_order, Some(2));
        assert!(s.actions(second).last().unwrap().failure.is_none());
        assert!(s.advance().is_err());
    }
}

#[test]
fn per_arm_memory_read_failure_and_explicit_stop_never_expose_missing_text() {
    for mode in [
        ComparisonMode::IndependentGeneration,
        ComparisonMode::FixedReplay,
    ] {
        for stop in [false, true] {
            let mut s = ActionComparisonSession::new(spec(7, mode)).unwrap();
            to(&mut s, 5);
            s.advance().unwrap();
            assert_eq!(s.pending_memory().unwrap().0, Arm::Left);
            if stop {
                s.stop("Explicit stop before memory read").unwrap();
            } else {
                s.fail_memory(Arm::Left, "Actual left file missing")
                    .unwrap();
            }
            let r = s.record().unwrap();
            r.verify().unwrap();
            assert!(s.advance().is_err());
            for arm in [Arm::Left, Arm::Right] {
                let a = s.actions(arm).last().unwrap();
                assert!(a.memory_entry_id.is_some());
                assert!(
                    a.memory_text.is_none()
                        && a.raw_reply.is_none()
                        && !a.request_started
                        && a.save_receipt.is_none()
                );
            }
            assert_eq!(
                r.status,
                if stop {
                    RunStatus::Stopped
                } else {
                    RunStatus::Failed
                }
            );
        }
    }
}

#[test]
fn manual_tape_wait_forces_both_writes_and_shared_reference_is_preserved() {
    let mut s = ActionComparisonSession::new(spec(8, ComparisonMode::FixedReplay)).unwrap();
    to(&mut s, 8);
    assert_eq!(s.tape().unwrap().packets[7].choice, JournalAction::Wait);
    s.request_action().unwrap();
    resolve(&mut s);
    for arm in [Arm::Left, Arm::Right] {
        let a = s.actions(arm).last().unwrap();
        assert_eq!(a.chosen_action, Some(JournalAction::WriteJournal));
        assert_eq!(a.tape_packet_id, Some(8));
        assert_eq!(
            a.semantic_vector.as_ref().unwrap(),
            &s.tape().unwrap().packets[7].semantic_vector
        );
    }
    to(&mut s, 11);
    s.record().unwrap().verify().unwrap();
}

#[test]
fn stop_during_partner_save_preserves_first_save_and_historical_failure() {
    for obs in [false, true] {
        let mut s = ActionComparisonSession::new(if obs {
            observation(false)
        } else {
            spec(6, ComparisonMode::IndependentGeneration)
        })
        .unwrap();
        to(&mut s, 2);
        s.advance().unwrap();
        save(&mut s);
        s.stop("Explicit stop retaining unresolved save failure")
            .unwrap();
        let r = s.record().unwrap();
        r.verify().unwrap();
        assert_eq!(r.left.unwrap().journals.len(), 1);
        assert_eq!(
            r.right.actions[0].failure_phase,
            Some(FailurePhase::JournalSave)
        );
        assert!(s.advance().is_err() && s.request_action().is_err());
    }
}

#[test]
fn rejects_unavailable_pairs_and_mutated_order_exposure_paths_and_controller() {
    assert!(ActionComparisonSession::new(spec(1, ComparisonMode::FixedReplay)).is_err());
    let mut invalid = observation(false);
    invalid.mode = ComparisonMode::FixedReplay;
    assert!(ActionComparisonSession::new(invalid).is_err());
    let mut s = ActionComparisonSession::new(observation(false)).unwrap();
    to(&mut s, 11);
    let r = s.record().unwrap();
    let mut changed = r.clone();
    changed.right.actions[1].request_order = Some(2);
    assert!(changed.verify().is_err());
    let mut changed = r.clone();
    changed.right.observation_channel = Some(ObservationChannel::Sensory);
    assert!(changed.verify().is_err());
    let mut changed = r;
    changed.left.as_mut().unwrap().actions[0]
        .save_receipt
        .as_mut()
        .unwrap()
        .relative_path = changed.right.actions[0]
        .save_receipt
        .as_ref()
        .unwrap()
        .relative_path
        .clone();
    assert!(changed.verify().is_err());
    let mut h = ActionComparisonSession::new(spec(8, ComparisonMode::FixedReplay)).unwrap();
    to(&mut h, 11);
    let mut r = h.record().unwrap();
    r.right.frames[0]
        .control
        .as_mut()
        .unwrap()
        .applied_retention += 0.0005;
    assert!(r.verify().is_err());
}

#[test]
fn manual_admission_reserves_both_arms_scheduled_capacity() {
    let mut config = spec(6, ComparisonMode::IndependentGeneration);
    config.steps = 258;
    config.turn_every = 2;
    let mut s = ActionComparisonSession::new(config).unwrap();
    s.advance().unwrap();
    assert!(!s.can_request_action());
    assert!(s.request_action().is_err());
    assert_eq!(
        (s.frames(Arm::Left).len(), s.frames(Arm::Right).len()),
        (1, 1)
    );
    assert!(s.actions(Arm::Left).is_empty() && s.actions(Arm::Right).is_empty());
    s.advance().unwrap();
    resolve(&mut s);
    s.record().unwrap().verify().unwrap();
}

#[test]
fn quiet_decimal_tie_uses_native_locale_format_in_both_prompt_families() {
    let mut s = ActionComparisonSession::new(observation(true)).unwrap();
    to(&mut s, 2);
    s.advance().unwrap();
    // Exact same bits are below the binary half, but the native locale-aware
    // formatter rounds the shortest decimal 0.870983875 as a decimal tie.
    let f = &s.frames(Arm::Right)[2];
    assert_eq!(
        f.spectral.as_ref().unwrap().eigenvalues[0].to_bits(),
        0x3febdf19934efcbd
    );
    assert!(s
        .pending_journal()
        .unwrap()
        .1
        .prompt
        .contains("[0.87098388, 0.87098388"));
    let stage_frame = reservoir_core::stage::EssentialsFrame {
        step: f.step,
        time: f.time,
        input: f.input.clone(),
        state: f.state.clone(),
        noise: f.noise.clone(),
        spectral: f.spectral.clone(),
        fill_percent: f.fill_percent,
        retention_used: f.retention_used,
        control: f.control.clone(),
        semantic_turn_id: None,
    };
    let stage_spec = serde_json::from_value(serde_json::json!({"stage":2})).unwrap();
    assert!(reservoir_core::stage::prompt(&stage_spec, &stage_frame)
        .unwrap()
        .contains("[0.87098388, 0.87098388"));
    resolve(&mut s);
    let bytes = serde_json::to_vec(&s.record().unwrap()).unwrap();
    let decoded: ActionComparisonRecord = serde_json::from_slice(&bytes).unwrap();
    decoded.verify().unwrap();
    for run in [decoded.left.as_ref().unwrap(), &decoded.right] {
        assert!(run.actions[0].prompt.contains("[0.87098388, 0.87098388"));
        let mut wrong = decoded.clone();
        wrong.right.actions[0].prompt = wrong.right.actions[0]
            .prompt
            .replace("0.87098388", "0.87098387");
        assert!(wrong.verify().is_err());
    }
}
