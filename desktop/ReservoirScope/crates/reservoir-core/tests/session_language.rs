use reservoir_core::{
    actions::*, comparison::ActionComparisonSession, session::*, stage::*, CoreError,
};

fn language() -> LanguageConfiguration {
    LanguageConfiguration {
        backend: LanguageKind::Ollama,
        endpoint: Some("http://127.0.0.1:11499".into()),
        model: Some("fixture-provider-not-contacted".into()),
        context_tokens: Some(2048),
        response_format: None,
    }
}
fn response(text: &str) -> LanguageResponse {
    LanguageResponse {
        text: text.into(),
        provider_model: Some("fixture-provider-not-contacted".into()),
        stop_reason: Some("stop".into()),
        token_count: Some(20),
        complete: true,
        provider_prompt_evaluation: None,
    }
}
fn action_spec(stage: u8, paired: bool) -> ActionSpecification {
    let mut spec: ActionSpecification = serde_json::from_value(serde_json::json!({"stage":stage,"steps":11,"turnEvery":3,"seed":18446744073709551615u64,"comparePrevious":paired,"mode":"independentGeneration","promptVersion":2,"noiseAmplitude":0.013})).unwrap();
    spec.language = language();
    spec.language.response_format = Some("json".into());
    spec
}
fn action_response(stage: u8, id: usize) -> LanguageResponse {
    response(if stage >= 7 && id == 3 {
        r#"{"action":"WAIT","text":""}"#
    } else {
        r#"{"action":"WRITE_JOURNAL","text":"I notice the retained field and remember a quiet pattern."}"#
    })
}
fn save_receipt(p: &PendingJournal) -> JournalSaveReceipt {
    JournalSaveReceipt {
        status: SaveStatus::Saved,
        entry_id: p.entry.id.clone(),
        sha256: p.entry.sha256.clone(),
        relative_path: Some(p.relative_path.clone()),
        failure: None,
    }
}
fn resolve(s: &mut JournalSession) {
    loop {
        if let Some(p) = s.pending_memory().cloned() {
            assert!(s.pending_language().is_none());
            s.confirm_memory(&p.entry).unwrap();
        } else if let Some(p) = s.pending_language().cloned() {
            assert!(!p.request_started);
            s.start_language(p.turn_id, p.observed_step).unwrap();
            s.confirm_language(
                p.turn_id,
                p.observed_step,
                &action_response(s.run().stage, p.turn_id),
            )
            .unwrap();
        } else if let Some(p) = s.pending_journal().cloned() {
            s.confirm_saved(&save_receipt(&p), &p.entry).unwrap();
        } else {
            break;
        }
    }
}
fn pair_resolve(s: &mut ActionComparisonSession) {
    loop {
        if let Some((arm, p)) = s.pending_memory().map(|(a, p)| (a, p.clone())) {
            assert!(s.pending_language().is_none());
            s.confirm_memory(arm, &p.entry).unwrap();
        } else if let Some((arm, p)) = s.pending_language().map(|(a, p)| (a, p.clone())) {
            s.start_language(arm, p.turn_id, p.observed_step).unwrap();
            s.confirm_language(
                arm,
                p.turn_id,
                p.observed_step,
                &action_response(s.run(arm).stage, p.turn_id),
            )
            .unwrap();
        } else if let Some((arm, p)) = s.pending_journal().map(|(a, p)| (a, p.clone())) {
            s.confirm_saved(arm, &save_receipt(&p), &p.entry).unwrap();
        } else {
            break;
        }
    }
}
fn stage_session(stage: u8) -> StageSession {
    StageSession::new(RunSpecification {
        stage,
        steps: 32,
        turn_every: 30,
        seed: u64::MAX,
        language: language(),
        ..Default::default()
    })
    .unwrap()
}

#[test]
fn stage_thirty_holds_until_dispatch_and_valid_reply_then_applies_at_thirty_one() {
    for stage in [3, 4] {
        let mut s = stage_session(stage);
        for _ in 0..30 {
            s.advance().unwrap();
        }
        let p = s.pending_language().unwrap().clone();
        assert_eq!(
            (
                p.turn_id,
                p.observed_step,
                p.request_started,
                p.request_order
            ),
            (1, 30, false, None)
        );
        assert_eq!(
            p.prompt,
            reservoir_core::stage::prompt(&s.record().specification, &s.record().frames[29])
                .unwrap()
        );
        assert!(s.portable_record().is_err());
        assert!(s.advance().is_err());
        assert!(s
            .confirm_language(1, 30, &response("I notice this pattern."))
            .is_err());
        assert!(s.start_language(2, 30).is_err());
        s.start_language(1, 30).unwrap();
        assert!(s.start_language(1, 30).is_err());
        s.confirm_language(1, 30, &response("I notice this pattern."))
            .unwrap();
        assert!(s.pending_language().is_none());
        assert_eq!(s.record().turns[0].application_step, None);
        s.portable_record().unwrap().verify().unwrap();
        assert_eq!(s.advance().unwrap().semantic_turn_id, Some(1));
        assert_eq!(s.record().turns[0].application_step, Some(31));
        assert!(s.confirm_language(1, 30, &response("Late text")).is_err());
        s.advance().unwrap();
        s.portable_record().unwrap().verify().unwrap();
    }
}

#[test]
fn stage_failed_incomplete_empty_oversized_and_cancelled_replies_never_feed() {
    for kind in [
        "incomplete",
        "length",
        "tokens",
        "empty",
        "oversized",
        "transport",
        "cancel-prepared",
        "cancel-started",
    ] {
        let mut s = stage_session(3);
        for _ in 0..30 {
            s.advance().unwrap();
        }
        if kind != "cancel-prepared" {
            s.start_language(1, 30).unwrap();
        }
        match kind {
            "transport" => s
                .fail_language(1, 30, "Fixture timeout without provider response")
                .unwrap(),
            "cancel-prepared" | "cancel-started" => s
                .cancel_language(1, 30, "Explicit fixture cancellation")
                .unwrap(),
            _ => {
                let mut r = response("I notice this pattern.");
                match kind {
                    "incomplete" => r.complete = false,
                    "length" => r.stop_reason = Some("length".into()),
                    "tokens" => r.token_count = Some(257),
                    "empty" => r.text = " \n\t".into(),
                    "oversized" => r.text = "x".repeat(65_537),
                    _ => unreachable!(),
                }
                s.confirm_language(1, 30, &r).unwrap();
            }
        }
        assert!(s.advance().is_err());
        let turn = &s.record().turns[0];
        assert!(
            turn.reply.is_none()
                && turn.semantic_vector.is_none()
                && turn.application_step.is_none()
        );
        assert_eq!(s.is_failed(), !kind.starts_with("cancel"));
        s.portable_record().unwrap().verify().unwrap();
        assert!(s
            .confirm_language(1, 30, &response("A late reply."))
            .is_err());
    }
}

#[test]
fn all_independent_action_stages_gate_provider_then_save_and_reread_memory() {
    for stage in 4..=8 {
        let mut s = JournalSession::new(action_spec(stage, false)).unwrap();
        for step in 1..=11 {
            s.advance().unwrap();
            if let Some(p) = s.pending_language().cloned() {
                assert!(
                    s.pending_journal().is_none() && s.record().is_err() && s.advance().is_err()
                );
                assert!(s
                    .confirm_language(
                        p.turn_id,
                        p.observed_step,
                        &action_response(stage, p.turn_id)
                    )
                    .is_err());
                s.start_language(p.turn_id, p.observed_step).unwrap();
                s.confirm_language(
                    p.turn_id,
                    p.observed_step,
                    &action_response(stage, p.turn_id),
                )
                .unwrap();
                if let Some(j) = s.pending_journal() {
                    assert_eq!(j.observed_step, step);
                    assert!(s.record().is_err());
                }
            }
            resolve(&mut s);
        }
        let r = s.record().unwrap();
        r.verify().unwrap();
        assert_eq!(r.right.actions.len(), 3);
        assert_eq!(r.right.journals.len(), if stage >= 7 { 2 } else { 3 });
        assert!(r
            .right
            .actions
            .iter()
            .all(|a| a.request_started && a.request_order == Some(1)));
        assert_eq!(
            r.right.actions[0].application_step,
            if stage >= 5 { Some(4) } else { None }
        );
        if stage >= 6 {
            assert_eq!(
                r.right.actions[1].memory_text.as_ref(),
                Some(&r.right.journals[0].text)
            );
        }
        if stage >= 7 {
            assert_eq!(r.right.actions[2].chosen_action, Some(JournalAction::Wait));
            assert!(r.right.actions[2].save_receipt.is_none());
            assert_eq!(r.right.frames[10].semantic_action_id, Some(2));
        }
    }
}

#[test]
fn invalid_provider_action_outcomes_have_no_save_or_feedback_and_replay() {
    for kind in [
        "incomplete",
        "length",
        "negative-tokens",
        "too-many-tokens",
        "malformed",
        "forced-wait",
        "empty-write",
        "oversized",
        "transport",
        "cancel-prepared",
        "cancel-started",
    ] {
        let mut s = JournalSession::new(action_spec(5, false)).unwrap();
        for _ in 0..3 {
            s.advance().unwrap();
        }
        if kind != "cancel-prepared" {
            s.start_language(1, 3).unwrap();
        }
        match kind {
            "transport" => s.fail_language(1, 3, "Fixture transport failure").unwrap(),
            "cancel-prepared" | "cancel-started" => {
                s.cancel_language(1, 3, "Fixture stop").unwrap()
            }
            _ => {
                let mut r = action_response(5, 1);
                match kind {
                    "incomplete" => r.complete = false,
                    "length" => r.stop_reason = Some("length".into()),
                    "negative-tokens" => r.token_count = Some(-1),
                    "too-many-tokens" => r.token_count = Some(257),
                    "malformed" => r.text = "not JSON".into(),
                    "forced-wait" => r = action_response(8, 3),
                    "empty-write" => r.text = r#"{"action":"WRITE_JOURNAL","text":""}"#.into(),
                    "oversized" => r.text = "x".repeat(65_537),
                    _ => unreachable!(),
                }
                s.confirm_language(1, 3, &r).unwrap();
            }
        }
        assert!(s.pending_journal().is_none() && s.journals().is_empty());
        assert!(s.actions()[0].semantic_vector.is_none());
        assert_eq!(s.actions()[0].request_started, kind != "cancel-prepared");
        s.record().unwrap().verify().unwrap();
        assert!(s.advance().is_err());
        assert!(s.confirm_language(1, 3, &action_response(5, 1)).is_err());
    }
}

#[test]
fn compatibility_unsupported_retains_pending_without_mislabeling_native_rejection() {
    for text in [
        r#"{"action":"WAIT","text":"",}"#,
        r#"{"action":"WRITE_JOURNAL","text":"\udbff\udfff"}"#,
    ] {
        let mut s = JournalSession::new(action_spec(8, false)).unwrap();
        for _ in 0..3 {
            s.advance().unwrap();
        }
        s.start_language(1, 3).unwrap();
        assert!(matches!(
            s.confirm_language(1, 3, &response(text)),
            Err(CoreError::Unsupported(_))
        ));
        assert!(
            s.pending_language().is_some()
                && s.actions().is_empty()
                && s.pending_journal().is_none()
        );
        assert!(s.record().is_err() && s.advance().is_err());
        assert!(s.confirm_language(1, 3, &action_response(8, 1)).is_err());
        assert!(s
            .fail_language(
                1,
                3,
                "Cannot relabel a received response as transport failure"
            )
            .is_err());
        s.cancel_language(1, 3, "Explicitly stop unsupported response boundary")
            .unwrap();
        s.record().unwrap().verify().unwrap();
    }
    let mut stage = stage_session(3);
    for _ in 0..30 {
        stage.advance().unwrap();
    }
    stage.start_language(1, 30).unwrap();
    assert!(matches!(
        stage.confirm_language(1, 30, &response("\u{10ffff}")),
        Err(CoreError::Unsupported(_))
    ));
    assert!(stage.pending_language().is_some() && stage.record().turns.is_empty());
    assert!(stage
        .confirm_language(1, 30, &response("Late replacement text"))
        .is_err());
    assert!(stage.fail_language(1, 30, "Cannot relabel").is_err());
    stage.stop();
    stage.portable_record().unwrap().verify().unwrap();
}

#[test]
fn provider_pairs_preserve_arm_ordinals_wait_memory_and_observation_alternation() {
    for stage in 4..=8 {
        let mut s = ActionComparisonSession::new(action_spec(stage, true)).unwrap();
        for _ in 0..11 {
            s.advance().unwrap();
            pair_resolve(&mut s);
        }
        let r = s.record().unwrap();
        r.verify().unwrap();
        assert!(r
            .right
            .actions
            .iter()
            .all(|a| a.request_order == Some(if stage == 4 { 1 } else { 2 })));
        assert!(r
            .left
            .as_ref()
            .unwrap()
            .actions
            .iter()
            .all(|a| a.request_order == Some(1)));
    }
    let mut spec = action_spec(4, true);
    spec.comparison_kind = ComparisonKind::Observation;
    let mut s = ActionComparisonSession::new(spec).unwrap();
    for _ in 0..11 {
        s.advance().unwrap();
        pair_resolve(&mut s);
    }
    let r = s.record().unwrap();
    r.verify().unwrap();
    assert_eq!(
        r.left
            .unwrap()
            .actions
            .iter()
            .map(|a| a.request_order.unwrap())
            .collect::<Vec<_>>(),
        [1, 2, 1]
    );
    assert_eq!(
        r.right
            .actions
            .iter()
            .map(|a| a.request_order.unwrap())
            .collect::<Vec<_>>(),
        [2, 1, 2]
    );
}

#[test]
fn pair_failure_and_stop_retain_native_partner_policy_and_reject_wrong_arm() {
    for observation in [false, true] {
        let mut spec = action_spec(if observation { 4 } else { 5 }, true);
        if observation {
            spec.comparison_kind = ComparisonKind::Observation;
        }
        let mut s = ActionComparisonSession::new(spec).unwrap();
        for _ in 0..3 {
            s.advance().unwrap();
        }
        assert!(s.start_language(Arm::Right, 1, 3).is_err());
        s.start_language(Arm::Left, 1, 3).unwrap();
        s.fail_language(Arm::Left, 1, 3, "First provider attempt failed")
            .unwrap();
        assert_eq!(s.pending_language().is_some(), observation);
        pair_resolve(&mut s);
        let r = s.record().unwrap();
        r.verify().unwrap();
        assert_eq!(r.right.actions[0].request_started, observation);
        assert_eq!(
            r.right.actions[0].status,
            if observation {
                TurnStatus::Completed
            } else {
                TurnStatus::Cancelled
            }
        );
    }
    let mut spec = action_spec(4, true);
    spec.comparison_kind = ComparisonKind::Observation;
    let mut s = ActionComparisonSession::new(spec).unwrap();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    s.start_language(Arm::Left, 1, 3).unwrap();
    s.cancel_language(Arm::Left, 1, 3, "Stop both arms")
        .unwrap();
    let r = s.record().unwrap();
    r.verify().unwrap();
    assert!(r.left.unwrap().actions[0].request_started);
    assert!(!r.right.actions[0].request_started);
    assert!(s
        .confirm_language(Arm::Left, 1, 3, &action_response(4, 1))
        .is_err());
}

#[test]
fn memory_read_and_failed_save_remain_real_gates_after_valid_language() {
    let mut s = JournalSession::new(action_spec(6, false)).unwrap();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    resolve(&mut s);
    for _ in 0..3 {
        s.advance().unwrap();
    }
    assert!(s.pending_memory().is_some() && s.pending_language().is_none());
    let mut wrong = s.pending_memory().unwrap().entry.clone();
    wrong.text.push('x');
    assert!(s.confirm_memory(&wrong).is_err());
    s.fail_memory("Actual saved entry was unavailable").unwrap();
    s.record().unwrap().verify().unwrap();
    let mut s = JournalSession::new(action_spec(5, false)).unwrap();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    s.start_language(1, 3).unwrap();
    s.confirm_language(1, 3, &action_response(5, 1)).unwrap();
    assert!(s.advance().is_err());
    s.fail_pending("Actual publication did not complete")
        .unwrap();
    let r = s.record().unwrap();
    r.verify().unwrap();
    assert!(r.right.journals.is_empty() && r.right.actions[0].semantic_vector.is_none());
}
