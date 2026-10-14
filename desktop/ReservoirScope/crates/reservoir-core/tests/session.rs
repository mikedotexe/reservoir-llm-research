use reservoir_core::{actions::*, session::*, stage::*};

fn spec(stage: u8, steps: usize) -> ActionSpecification {
    serde_json::from_value(serde_json::json!({
        "stage":stage,"steps":steps,"turnEvery":30,"seed":18446744073709551615u64,
        "mode":"independentGeneration","comparePrevious":false,
        "noiseAmplitude":0.01,"promptVersion":2
    }))
    .unwrap()
}
fn saved(p: &PendingJournal) -> JournalSaveReceipt {
    JournalSaveReceipt {
        status: SaveStatus::Saved,
        entry_id: p.entry.id.clone(),
        sha256: p.entry.sha256.clone(),
        relative_path: Some(p.relative_path.clone()),
        failure: None,
    }
}
fn confirm(s: &mut JournalSession) {
    let p = s.pending_journal().unwrap().clone();
    s.confirm_saved(&saved(&p), &p.entry).unwrap();
}

#[test]
fn incremental_stages_match_existing_batch_exactly() {
    for stage in 1..=4 {
        let s = RunSpecification {
            stage,
            steps: 32,
            turn_every: 30,
            noise_amplitude: 0.013,
            seed: u64::MAX,
            ..Default::default()
        };
        let batch = run_scripted(s.clone()).unwrap();
        let mut incremental = StageSession::new(s).unwrap();
        incremental.record().verify().unwrap();
        for _ in 0..32 {
            incremental.advance().unwrap();
        }
        assert!(incremental.is_complete());
        assert!(incremental.advance().is_err());
        assert_eq!(
            serde_json::to_value(batch).unwrap(),
            serde_json::to_value(incremental.record()).unwrap()
        );
        incremental.record().verify().unwrap();
    }
}

#[test]
fn stage_thirty_prepares_and_thirty_one_applies_and_stop_is_terminal() {
    let mut s = StageSession::new(RunSpecification {
        stage: 3,
        steps: 32,
        turn_every: 30,
        ..Default::default()
    })
    .unwrap();
    for _ in 0..30 {
        s.advance().unwrap();
    }
    assert_eq!(s.record().turns[0].application_step, None);
    assert_eq!(s.record().frames[29].semantic_turn_id, None);
    s.record().verify().unwrap();
    let boundary = s.advance().unwrap();
    assert_eq!(boundary.semantic_turn_id, Some(1));
    assert_eq!(s.record().turns[0].application_step, Some(31));
    s.stop();
    assert!(s.advance().is_err());
    s.record().verify().unwrap();
}

#[test]
fn pending_and_bad_save_proof_cannot_feed_or_create_portable_saved_claims() {
    let mut s = JournalSession::new(spec(5, 32)).unwrap();
    for _ in 0..30 {
        s.advance().unwrap();
    }
    let p = s.pending_journal().unwrap().clone();
    assert!(s.record().is_err());
    assert!(s.stop().is_err());
    assert!(s.advance().is_err());
    assert!(s.journals().is_empty());
    assert!(s.actions().is_empty());
    let mut proof = saved(&p);
    proof.relative_path = Some("left/wrong.json".into());
    assert!(s.confirm_saved(&proof, &p.entry).is_err());
    let mut other = p.entry.clone();
    other.text.push('!');
    assert!(s.confirm_saved(&saved(&p), &other).is_err());
    proof = saved(&p);
    proof.status = SaveStatus::Failed;
    assert!(s.confirm_saved(&proof, &p.entry).is_err());
    assert_eq!(s.pending_journal().unwrap().entry, p.entry);
    assert_eq!(s.frames().len(), 30);
    confirm(&mut s);
    assert_eq!(s.actions()[0].application_step, None);
    s.record().unwrap().verify().unwrap();
    let f = s.advance().unwrap();
    assert_eq!(f.semantic_action_id, Some(1));
    assert!(f.semantic_input.iter().any(|v| *v != 0.0));
    assert_eq!(s.actions()[0].application_step, Some(31));
    s.record().unwrap().verify().unwrap();
}

#[test]
fn d_records_saved_preparation_but_never_applies_feedback() {
    let mut s = JournalSession::new(spec(4, 32)).unwrap();
    for _ in 0..30 {
        s.advance().unwrap();
    }
    confirm(&mut s);
    assert!(s.actions()[0]
        .semantic_vector
        .as_ref()
        .unwrap()
        .iter()
        .any(|v| *v != 0.0));
    let f = s.advance().unwrap();
    assert_eq!(f.semantic_action_id, None);
    assert!(f.semantic_input.iter().all(|v| *v == 0.0));
    assert_eq!(s.actions()[0].application_step, None);
    s.advance().unwrap();
    s.record().unwrap().verify().unwrap();
}

#[test]
fn explicit_failed_save_is_terminal_and_preserves_raw_candidate() {
    let mut s = JournalSession::new(spec(5, 32)).unwrap();
    for _ in 0..30 {
        s.advance().unwrap();
    }
    let p = s.pending_journal().unwrap().clone();
    assert!(s.fail_pending("").is_err());
    assert!(s.pending_journal().is_some());
    s.fail_pending("Test storage failure retained on explicit stop")
        .unwrap();
    assert!(s.is_failed());
    assert!(s.advance().is_err());
    assert!(s.request_journal().is_err());
    assert!(s.confirm_saved(&saved(&p), &p.entry).is_err());
    assert!(s.journals().is_empty());
    let a = &s.actions()[0];
    assert_eq!(a.raw_reply.as_deref(), Some(p.raw_reply.as_str()));
    assert_eq!(a.failure_phase, Some(FailurePhase::JournalSave));
    assert!(
        a.encoded_features.is_none() && a.semantic_vector.is_none() && a.application_step.is_none()
    );
    let r = s.record().unwrap();
    r.verify().unwrap();
    let mut mutant = r.clone();
    mutant.right.actions[0].application_step = Some(31);
    assert!(mutant.verify().is_err());
}

#[test]
fn manual_and_scheduled_journals_use_distinct_boundaries_and_monotonic_ids() {
    let mut s = JournalSession::new(spec(5, 32)).unwrap();
    assert!(s.request_journal().is_err());
    s.advance().unwrap();
    let first = s.request_journal().unwrap();
    assert_eq!(first.trigger, Trigger::Manual);
    confirm(&mut s);
    assert!(s.request_journal().is_err());
    while s.frames().len() < 30 {
        s.advance().unwrap();
    }
    assert_eq!(s.actions()[0].application_step, Some(2));
    assert_eq!(s.pending_journal().unwrap().action_id, 2);
    assert_eq!(s.pending_journal().unwrap().trigger, Trigger::Scheduled);
    assert!(s.request_journal().is_err());
    confirm(&mut s);
    s.advance().unwrap();
    s.advance().unwrap();
    assert!(s.is_complete());
    assert!(s.request_journal().is_err());
    assert!(s
        .actions()
        .iter()
        .all(|a| a.memory_text.is_none() && a.memory_entry_id.is_none()));
    s.record().unwrap().verify().unwrap();
}

#[test]
fn manual_budget_reserves_required_scheduled_actions() {
    // 128 scheduled opportunities leave no space for manual actions.
    let mut bounded = spec(5, 257);
    bounded.turn_every = 2;
    let mut s = JournalSession::new(bounded).unwrap();
    s.advance().unwrap();
    assert!(s.request_journal().is_err());
    s.stop().unwrap();
    s.record().unwrap().verify().unwrap();
}

#[test]
fn unsupported_recipes_and_invalid_bounds_do_not_start() {
    let mut s = spec(9, 32);
    assert!(JournalSession::new(s.clone()).is_err());
    s.stage = 5;
    s.compare_previous = true;
    assert!(JournalSession::new(s.clone()).is_err());
    s.compare_previous = false;
    s.mode = ComparisonMode::FixedReplay;
    assert!(JournalSession::new(s.clone()).is_ok());
    s.mode = ComparisonMode::IndependentGeneration;
    s.steps = 601;
    assert!(JournalSession::new(s.clone()).is_err());
    let mut r = RunSpecification {
        steps: 3001,
        ..Default::default()
    };
    assert!(StageSession::new(r.clone()).is_err());
    r.steps = 32;
    r.language.backend = LanguageKind::Ollama;
    r.language.model = Some("test".into());
    assert!(StageSession::new(r).is_err());
}

#[test]
fn stopped_journal_prefixes_remain_valid_and_immutable() {
    for stage in [4, 5] {
        let mut s = JournalSession::new(spec(stage, 32)).unwrap();
        s.record().unwrap().verify().unwrap();
        for _ in 0..30 {
            s.advance().unwrap();
        }
        confirm(&mut s);
        let old = s.record().unwrap();
        s.stop().unwrap();
        assert!(s.advance().is_err());
        assert!(s.request_journal().is_err());
        assert_eq!(
            serde_json::to_value(old).unwrap(),
            serde_json::to_value(s.record().unwrap()).unwrap()
        );
        s.record().unwrap().verify().unwrap();
    }
}

#[test]
fn complete_fresh_journal_mutations_are_rejected() {
    let mut s = JournalSession::new(spec(5, 32)).unwrap();
    while !s.is_complete() {
        s.advance().unwrap();
        if s.pending_journal().is_some() {
            confirm(&mut s);
        }
    }
    let record = s.record().unwrap();
    record.verify().unwrap();
    let mut x = record.clone();
    x.right.frames[30].semantic_action_id = None;
    assert!(x.verify().is_err());
    let mut x = record.clone();
    x.right.journals[0].text.push('x');
    assert!(x.verify().is_err());
    let mut x = record.clone();
    x.right.actions[0].save_receipt.as_mut().unwrap().status = SaveStatus::Failed;
    assert!(x.verify().is_err());
    let mut x = record;
    x.right.actions[0].application_step = Some(30);
    assert!(x.verify().is_err());
}
