use reservoir_core::{
    actions::*,
    session::*,
    stage::{RunStatus, TurnStatus},
};

fn spec(stage: u8, mode: ComparisonMode) -> ActionSpecification {
    let mut s: ActionSpecification = serde_json::from_value(serde_json::json!({
        "stage":stage,"steps":11,"turnEvery":3,"seed":18446744073709551615u64,
        "mode":"independentGeneration","comparePrevious":false,"promptVersion":2,
        "noiseAmplitude":0.013,"inputStrength":0.8,"biasEnabled":true
    }))
    .unwrap();
    s.mode = mode;
    s
}
// These unit tests supply evidence directly to exercise the core protocol.
// The separate fixture generator/backend tests perform real filesystem reads.
fn resolve(s: &mut ActionSession) {
    if let Some(p) = s.pending_memory().cloned() {
        s.confirm_memory(&p.entry).unwrap();
    }
    if let Some(p) = s.pending_journal().cloned() {
        s.confirm_saved(
            &JournalSaveReceipt {
                status: SaveStatus::Saved,
                entry_id: p.entry.id.clone(),
                sha256: p.entry.sha256.clone(),
                relative_path: Some(p.relative_path),
                failure: None,
            },
            &p.entry,
        )
        .unwrap();
    }
}
fn to(s: &mut ActionSession, step: usize) {
    while s.frames().len() < step {
        s.advance().unwrap();
        resolve(s);
    }
}

#[test]
fn all_standalone_stages_both_modes_complete_with_exact_native_shapes() {
    for mode in [
        ComparisonMode::IndependentGeneration,
        ComparisonMode::FixedReplay,
    ] {
        for stage in 1..=8 {
            let mut s = ActionSession::new(spec(stage, mode)).unwrap();
            s.record().unwrap().verify().unwrap();
            assert_eq!(s.tape().is_some(), mode == ComparisonMode::FixedReplay);
            to(&mut s, 11);
            assert!(s.is_complete());
            assert!(!s.can_request_action());
            let r = s.record().unwrap();
            r.verify().unwrap();
            assert_eq!(r.status, RunStatus::Completed);
            for f in &r.right.frames {
                assert_eq!(f.spectral.is_some(), stage >= 3);
                assert_eq!(f.fill_percent.is_some(), stage >= 3);
                assert_eq!(f.retention_used.is_some(), stage >= 3);
                assert_eq!(f.control.is_some(), stage == 8);
                if stage < 5 {
                    assert!(f.semantic_input.iter().all(|v| *v == 0.0));
                }
            }
            assert_eq!(r.right.actions.len(), if stage >= 4 { 3 } else { 0 });
            if stage >= 7 {
                assert_eq!(r.right.actions[2].chosen_action, Some(JournalAction::Wait));
            }
        }
    }
}

#[test]
fn observer_and_output_are_passive_until_feedback_gate_opens() {
    let mut a = ActionSession::new(spec(1, ComparisonMode::IndependentGeneration)).unwrap();
    let mut b = ActionSession::new(spec(2, ComparisonMode::IndependentGeneration)).unwrap();
    let mut c = ActionSession::new(spec(3, ComparisonMode::IndependentGeneration)).unwrap();
    let mut d = ActionSession::new(spec(4, ComparisonMode::IndependentGeneration)).unwrap();
    let mut e = ActionSession::new(spec(5, ComparisonMode::IndependentGeneration)).unwrap();
    for s in [&mut a, &mut b, &mut c, &mut d, &mut e] {
        to(s, 11);
    }
    assert_ne!(a.frames()[10].state, b.frames()[10].state);
    for step in 0..11 {
        assert_eq!(b.frames()[step].state, c.frames()[step].state);
        assert_eq!(c.frames()[step].state, d.frames()[step].state);
    }
    assert_ne!(d.frames()[3].state, e.frames()[3].state);
}

#[test]
fn memory_requires_matching_readback_before_prompt_or_reply() {
    for mode in [
        ComparisonMode::IndependentGeneration,
        ComparisonMode::FixedReplay,
    ] {
        let mut s = ActionSession::new(spec(6, mode)).unwrap();
        to(&mut s, 5);
        s.advance().unwrap();
        let p = s.pending_memory().unwrap().clone();
        assert_eq!(p.action_id, 2);
        assert_eq!(p.observed_step, 6);
        assert_eq!(p.entry, s.journals()[0]);
        assert!(s.pending_journal().is_none());
        assert_eq!(s.actions().len(), 1);
        assert!(s.record().is_err());
        assert!(s.advance().is_err());
        assert!(s.stop().is_err());
        let mut wrong = p.entry.clone();
        wrong.text.push('!');
        assert!(s.confirm_memory(&wrong).is_err());
        assert_eq!(s.pending_memory().unwrap().entry, p.entry);
        s.confirm_memory(&p.entry).unwrap();
        assert!(s.pending_memory().is_none());
        assert!(s
            .pending_journal()
            .unwrap()
            .prompt
            .contains(&format!("<journal>\n{}\n</journal>", p.entry.text)));
        resolve(&mut s);
        let r = s.record().unwrap();
        r.verify().unwrap();
        let receipt = &r.right.actions[1];
        assert_eq!(
            receipt.memory_entry_id.as_deref(),
            Some(p.entry.id.as_str())
        );
        assert_eq!(receipt.memory_text.as_deref(), Some(p.entry.text.as_str()));
        assert_eq!(
            receipt.request_started,
            mode == ComparisonMode::IndependentGeneration
        );
        assert_eq!(
            receipt.tape_packet_id,
            if mode == ComparisonMode::FixedReplay {
                Some(6)
            } else {
                None
            }
        );
    }
}

#[test]
fn wait_still_rereads_memory_but_does_not_clear_or_reapply_feedback() {
    for mode in [
        ComparisonMode::IndependentGeneration,
        ComparisonMode::FixedReplay,
    ] {
        let mut s = ActionSession::new(spec(7, mode)).unwrap();
        to(&mut s, 8);
        let held = s.frames()[7].semantic_input.clone();
        let latest = s.journals().last().unwrap().clone();
        s.advance().unwrap();
        assert!(s.pending_memory().is_some());
        assert_eq!(s.actions().len(), 2);
        s.confirm_memory(&latest).unwrap();
        assert!(s.pending_memory().is_none() && s.pending_journal().is_none());
        let wait = &s.actions()[2];
        assert_eq!(wait.chosen_action, Some(JournalAction::Wait));
        assert_eq!(wait.memory_text.as_deref(), Some(latest.text.as_str()));
        assert!(
            wait.save_receipt.is_none()
                && wait.semantic_vector.is_none()
                && wait.application_step.is_none()
        );
        let next = s.advance().unwrap();
        assert_eq!(next.semantic_input, held);
        assert_eq!(next.semantic_action_id, Some(2));
        assert_eq!(s.journals().len(), 2);
        s.record().unwrap().verify().unwrap();
    }
}

#[test]
fn fixed_tape_is_boundary_indexed_and_manual_forces_write_over_wait() {
    let mut s = ActionSession::new(spec(7, ComparisonMode::FixedReplay)).unwrap();
    assert_eq!(s.tape().unwrap().packets.len(), 10);
    to(&mut s, 1);
    assert!(s.can_request_action());
    s.request_action().unwrap();
    resolve(&mut s);
    assert!(!s.can_request_action());
    to(&mut s, 3);
    // Second action at3 uses tape3 (first text), not second action's scripted text.
    assert_eq!(s.journals()[0].text, s.journals()[1].text);
    to(&mut s, 8);
    assert!(s.can_request_action());
    assert_eq!(s.tape().unwrap().packets[7].choice, JournalAction::Wait);
    s.request_action().unwrap();
    resolve(&mut s);
    let manual = s.actions().last().unwrap();
    assert_eq!(manual.trigger, Trigger::Manual);
    assert_eq!(manual.chosen_action, Some(JournalAction::WriteJournal));
    assert_eq!(manual.tape_packet_id, Some(8));
    assert_eq!(
        manual.semantic_vector.as_ref().unwrap(),
        &s.tape().unwrap().packets[7].semantic_vector
    );
    to(&mut s, 11);
    s.record().unwrap().verify().unwrap();
}

#[test]
fn h_control_is_next_step_and_fixed_tape_keeps_g_h_full_inputs_identical() {
    let mut g = ActionSession::new(spec(7, ComparisonMode::FixedReplay)).unwrap();
    let mut h = ActionSession::new(spec(8, ComparisonMode::FixedReplay)).unwrap();
    to(&mut g, 11);
    to(&mut h, 11);
    assert_eq!(
        serde_json::to_value(g.tape()).unwrap(),
        serde_json::to_value(h.tape()).unwrap()
    );
    for index in 0..11 {
        assert_eq!(g.frames()[index].input, h.frames()[index].input);
        assert_eq!(g.frames()[index].state, h.frames()[index].state);
        if index > 0 {
            assert_eq!(
                h.frames()[index].retention_used,
                Some(
                    h.frames()[index - 1]
                        .control
                        .as_ref()
                        .unwrap()
                        .applied_retention
                )
            );
        }
    }
    assert_ne!(g.frames()[1].retention_used, h.frames()[1].retention_used);
    assert_ne!(
        g.frames()[1].spectral.as_ref().unwrap().covariance,
        h.frames()[1].spectral.as_ref().unwrap().covariance
    );
    h.record().unwrap().verify().unwrap();
}

#[test]
fn failed_memory_is_terminal_without_exposure_and_cancel_is_distinct() {
    for mode in [
        ComparisonMode::IndependentGeneration,
        ComparisonMode::FixedReplay,
    ] {
        for cancel in [false, true] {
            let mut s = ActionSession::new(spec(6, mode)).unwrap();
            to(&mut s, 5);
            s.advance().unwrap();
            let p = s.pending_memory().unwrap().clone();
            if cancel {
                s.cancel_memory("Explicit stop before memory read").unwrap();
            } else {
                s.fail_memory("Required saved journal could not be read")
                    .unwrap();
            }
            assert!(s.advance().is_err());
            assert!(s.confirm_memory(&p.entry).is_err());
            let r = s.record().unwrap();
            r.verify().unwrap();
            let a = &r.right.actions[1];
            assert_eq!(
                a.status,
                if cancel {
                    TurnStatus::Cancelled
                } else {
                    TurnStatus::Failed
                }
            );
            assert_eq!(
                a.failure_phase,
                Some(if cancel {
                    FailurePhase::Cancelled
                } else {
                    FailurePhase::MemoryRead
                })
            );
            assert_eq!(a.memory_entry_id, Some(p.entry.id));
            assert!(!a.request_started);
            assert!(a.memory_text.is_none() && a.raw_reply.is_none() && a.save_receipt.is_none());
            assert!(
                a.encoded_features.is_none()
                    && a.semantic_vector.is_none()
                    && a.application_step.is_none()
            );
            assert_eq!(
                r.status,
                if cancel {
                    RunStatus::Stopped
                } else {
                    RunStatus::Failed
                }
            );
        }
    }
}

#[test]
fn new_memory_choice_tape_and_controller_mutations_are_rejected() {
    let mut s = ActionSession::new(spec(8, ComparisonMode::FixedReplay)).unwrap();
    to(&mut s, 11);
    let r = s.record().unwrap();
    r.verify().unwrap();
    let mut x = r.clone();
    x.right.actions[1].memory_text = Some("not the latest saved text".into());
    assert!(x.verify().is_err());
    let mut x = r.clone();
    x.right.actions[2].chosen_action = Some(JournalAction::WriteJournal);
    assert!(x.verify().is_err());
    let mut x = r.clone();
    x.right.actions[0].tape_packet_id = Some(1);
    assert!(x.verify().is_err());
    let mut x = r.clone();
    x.tape.as_mut().unwrap().packets[2].semantic_vector[0] += 0.01;
    assert!(x.verify().is_err());
    let mut x = r.clone();
    x.right.frames[1].retention_used = Some(x.specification.initial_retention);
    assert!(x.verify().is_err());
    let mut x = r;
    x.right.actions[2].application_step = Some(10);
    assert!(x.verify().is_err());
}

#[test]
fn comparisons_remain_explicitly_unsupported_and_manual_availability_is_exact() {
    let mut compared = spec(8, ComparisonMode::FixedReplay);
    compared.compare_previous = true;
    assert!(ActionSession::new(compared).is_err());
    for stage in 1..=8 {
        let mut s = ActionSession::new(spec(stage, ComparisonMode::IndependentGeneration)).unwrap();
        assert!(!s.can_request_action());
        s.advance().unwrap();
        assert_eq!(s.can_request_action(), stage >= 4);
        if stage < 4 {
            assert!(s.request_action().is_err());
        } else {
            s.request_action().unwrap();
            assert!(!s.can_request_action());
            resolve(&mut s);
            assert!(!s.can_request_action());
        }
        s.stop().unwrap();
        assert!(!s.can_request_action());
        s.record().unwrap().verify().unwrap();
    }
}
