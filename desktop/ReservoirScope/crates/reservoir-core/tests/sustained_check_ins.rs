use reservoir_core::{session::LanguageResponse, sustained::*};
use sha2::{Digest, Sha256};
use std::collections::HashMap;

fn schedule(telemetry: bool) -> SustainedCheckInSchedule {
    SustainedCheckInSchedule {
        interval_seconds: 10,
        end_after_seconds: 30,
        prompt: " Tell me, friend, about your idle curiosities.\n".into(),
        include_telemetry: telemetry,
    }
}
fn spec(telemetry: bool) -> SustainedSpecification {
    SustainedSpecification {
        check_in_schedule: Some(schedule(telemetry)),
        turn_every: 3,
        maximum_steps: 100,
        maximum_turns: 40,
        prompt_version: SustainedPromptVersion::InertPlainContractNoTagV1,
        ..Default::default()
    }
}
fn response(text: &str) -> LanguageResponse {
    LanguageResponse {
        text: text.into(),
        provider_model: None,
        stop_reason: Some("stop".into()),
        token_count: Some(12),
        complete: true,
        provider_prompt_evaluation: None,
    }
}
fn read_memory(s: &mut SustainedSession, entries: &HashMap<String, SustainedJournal>) {
    if let Some(p) = s.pending_memory().cloned() {
        let entry = p
            .entry
            .as_ref()
            .unwrap_or_else(|| entries.get(p.entry_id().unwrap()).unwrap());
        s.confirm_memory(entry).unwrap();
    }
}
fn save(
    s: &mut SustainedSession,
    entries: &mut HashMap<String, SustainedJournal>,
    text: &str,
) -> SustainedPendingJournal {
    read_memory(s, entries);
    let p = s.pending_language().unwrap().clone();
    s.start_language(p.attempt_id).unwrap();
    s.confirm_language(p.attempt_id, &response(text)).unwrap();
    let j = s.pending_journal().unwrap().clone();
    let receipt = SustainedSaveReceipt {
        entry_id: j.entry.id.clone(),
        sha256: j.entry.sha256.clone(),
        relative_path: format!("journals/{}.json", j.entry.id),
    };
    s.confirm_saved(&receipt, &j.entry).unwrap();
    entries.insert(j.entry.id.clone(), j.entry.clone());
    j
}
fn apply(s: &mut SustainedSession) -> SustainedFrame {
    let id = s.prepared_application().unwrap().entry.attempt_id;
    s.authorize_application(id).unwrap();
    s.advance().unwrap()
}
fn flush(s: &mut SustainedSession, base: &mut SustainedCheckpoint) -> SustainedSegment {
    let segment = SustainedSegment {
        format: FORMAT.into(),
        initial_checkpoint: base.clone(),
        events: s.events().iter().cloned().collect(),
        final_checkpoint: s.checkpoint(),
    };
    segment.verify().unwrap();
    s.acknowledge_events(segment.events.last().unwrap().id)
        .unwrap();
    *base = segment.final_checkpoint.clone();
    segment
}
fn initial_entry(s: &mut SustainedSession, entries: &mut HashMap<String, SustainedJournal>) {
    for _ in 0..3 {
        s.advance().unwrap();
    }
    save(s, entries, "ordinary memory marker");
    apply(s);
}

#[test]
fn plain_is_exact_and_bypasses_memory_but_response_still_flows_back() {
    let mut s = SustainedSession::new(spec(false)).unwrap();
    let mut base = s.checkpoint();
    let mut entries = HashMap::new();
    initial_entry(&mut s, &mut entries);
    assert!(!s.admit_due_check_in(9999).unwrap());
    assert!(s.admit_due_check_in(10000).unwrap());
    let p = s.pending_language().unwrap();
    assert_eq!(p.prompt, schedule(false).prompt);
    assert!(p.memory.is_none() && p.memory_choice.is_none() && p.latest_shown.is_none());
    assert!(s.pending_system_contract().is_none());
    let journal = save(&mut s, &mut entries, "check-in response marker");
    assert!(journal.check_in.is_some());
    assert_eq!(
        s.check_in_state().unwrap().outcomes[0].status,
        SustainedCheckInStatus::Pending
    );
    let frame = apply(&mut s);
    assert_eq!(frame.application.unwrap().journal_id, journal.entry.id);
    assert_eq!(
        s.check_in_state().unwrap().outcomes[0].status,
        SustainedCheckInStatus::Applied
    );
    s.advance().unwrap(); // next ordinary opportunity
    read_memory(&mut s, &entries);
    assert!(s
        .pending_language()
        .unwrap()
        .prompt
        .contains("check-in response marker"));
    assert!(s.pending_language().unwrap().check_in.is_none());
    assert!(s.pending_system_contract().is_some());
    flush(&mut s, &mut base);
}

#[test]
fn telemetry_uses_actual_readout_and_policy_memory_for_every_invitation() {
    for version in [
        SustainedPromptVersion::InertPlainContractNoTagV1,
        SustainedPromptVersion::InertPlainContractScrambledTagV1,
        SustainedPromptVersion::InertPlainContractTwoNoTagV1,
    ] {
        let mut cfg = spec(true);
        cfg.prompt_version = version;
        if version.returns_two_entries() {
            cfg.memory_policy = SustainedMemoryPolicy::StateResidual;
        }
        let mut s = SustainedSession::new(cfg).unwrap();
        let mut base = s.checkpoint();
        let mut entries = HashMap::new();
        initial_entry(&mut s, &mut entries);
        assert!(s.admit_due_check_in(10000).unwrap());
        assert!(s.pending_memory().is_some());
        read_memory(&mut s, &entries);
        let p = s.pending_language().unwrap();
        assert!(p.prompt.contains("ordinary memory marker"));
        assert!(p.prompt.contains(&format!(
            "Separate sensory fill (%): {:.8}.",
            p.observation.sensory.fill_percent
        )));
        assert!(p.prompt.contains("Recurrent state RMS:"));
        assert!(p.prompt.ends_with(&schedule(true).prompt));
        assert_eq!(s.pending_system_contract(), version.system_contract());
        save(&mut s, &mut entries, "readout response");
        apply(&mut s);
        flush(&mut s, &mut base);
    }
}

#[test]
fn converting_ordinary_language_preserves_reserved_attempt_even_with_memory_reread() {
    for telemetry in [false, true] {
        let mut s = SustainedSession::new(spec(telemetry)).unwrap();
        let mut entries = HashMap::new();
        let mut base = s.checkpoint();
        initial_entry(&mut s, &mut entries);
        s.advance().unwrap();
        s.advance().unwrap();
        read_memory(&mut s, &entries);
        let ordinary = s.pending_language().unwrap().clone();
        assert!(s.admit_due_check_in(10000).unwrap());
        read_memory(&mut s, &entries);
        let scheduled = s.pending_language().unwrap();
        assert_eq!(scheduled.attempt_id, ordinary.attempt_id);
        assert_eq!(scheduled.turn_id, ordinary.turn_id);
        assert!(!s.admit_due_check_in(20000).unwrap());
        save(&mut s, &mut entries, "converted response");
        apply(&mut s);
        flush(&mut s, &mut base);
    }
}

#[test]
fn converting_pending_memory_to_plain_does_not_read_or_return_that_memory() {
    let mut cfg = spec(false);
    cfg.memory_policy = SustainedMemoryPolicy::StateResidual;
    cfg.memory_recent_exclusion = 3;
    let mut s = SustainedSession::new(cfg).unwrap();
    let mut entries = HashMap::new();
    let mut base = s.checkpoint();
    initial_entry(&mut s, &mut entries);
    s.advance().unwrap();
    s.advance().unwrap();
    assert!(s.pending_memory().is_some());
    assert!(s.admit_due_check_in(10000).unwrap());
    assert!(s.pending_memory().is_none());
    save(&mut s, &mut entries, "plain reply");
    apply(&mut s);
    assert!(s.checkpoint().state.applied_entries[0]
        .last_returned_turn
        .is_none());
    flush(&mut s, &mut base);
}

#[test]
fn paused_edits_leave_prepared_and_retried_plain_prompts_frozen() {
    let mut s = SustainedSession::new(spec(false)).unwrap();
    let mut entries = HashMap::new();
    let mut base = s.checkpoint();
    initial_entry(&mut s, &mut entries);
    s.admit_due_check_in(10000).unwrap();
    let original = s.pending_language().unwrap().clone();
    s.update_check_in_settings("A revised question".into(), true, 10001)
        .unwrap();
    assert_eq!(s.pending_language().unwrap().prompt, original.prompt);
    s.start_language(original.attempt_id).unwrap();
    assert!(s
        .update_check_in_settings("no in-flight edits".into(), true, 10002)
        .is_err());
    s.fail_language(original.attempt_id, "provider unavailable")
        .unwrap();
    s.retry_language().unwrap();
    let retry = s.pending_language().unwrap();
    assert!(retry.attempt_id > original.attempt_id);
    assert_eq!(retry.prompt, original.prompt);
    assert!(retry.memory.is_none());
    assert!(s.pending_system_contract().is_none());
    save(&mut s, &mut entries, "retry response");
    apply(&mut s);
    assert!(s.admit_due_check_in(20000).unwrap());
    read_memory(&mut s, &entries);
    let next = s.pending_language().unwrap();
    assert_eq!(next.check_in.as_ref().unwrap().settings_revision, 1);
    assert!(next.prompt.ends_with("A revised question"));
    assert!(next.memory.is_some());
    flush(&mut s, &mut base);
}

#[test]
fn missed_deadlines_do_not_burst_and_nondivisible_end_gets_final_slot() {
    let mut cfg = spec(false);
    cfg.check_in_schedule.as_mut().unwrap().end_after_seconds = 25;
    let schedule = cfg.check_in_schedule.as_ref().unwrap();
    assert_eq!(schedule.opportunity_count(), 3);
    assert_eq!(
        (
            schedule.deadline_seconds(0),
            schedule.deadline_seconds(1),
            schedule.deadline_seconds(2),
            schedule.deadline_seconds(3),
            schedule.deadline_seconds(4)
        ),
        (None, Some(10), Some(20), Some(25), None)
    );
    let mut s = SustainedSession::new(cfg).unwrap();
    let mut base = s.checkpoint();
    s.advance().unwrap();
    assert!(s.admit_due_check_in(26000).unwrap());
    let outcomes = &s.check_in_state().unwrap().outcomes;
    assert_eq!(
        outcomes.iter().map(|o| o.status).collect::<Vec<_>>(),
        [
            SustainedCheckInStatus::Missed,
            SustainedCheckInStatus::Missed,
            SustainedCheckInStatus::Pending
        ]
    );
    assert!(
        s.pending_language()
            .unwrap()
            .check_in
            .as_ref()
            .unwrap()
            .final_check_in
    );
    s.skip_pending("explicitly skip final opportunity").unwrap();
    assert!(s.check_in_complete());
    assert!(s.advance().is_err());
    flush(&mut s, &mut base);
}

#[test]
fn final_reply_applies_once_and_suppresses_an_ordinary_opportunity_at_same_step() {
    let mut cfg = spec(false);
    cfg.check_in_schedule.as_mut().unwrap().end_after_seconds = 10;
    let mut s = SustainedSession::new(cfg).unwrap();
    let mut base = s.checkpoint();
    let mut entries = HashMap::new();
    s.advance().unwrap();
    s.advance().unwrap();
    s.admit_due_check_in(10000).unwrap();
    save(&mut s, &mut entries, "final reply");
    assert!(!s.check_in_complete());
    let before_application = s.checkpoint();
    let mut restored = SustainedSession::restore(before_application).unwrap();
    assert!(restored.advance().is_err()); // restore grants no application authority
    let frame = apply(&mut s);
    assert_eq!(frame.step, 3); // ordinary opportunity would otherwise open here
    assert!(s.check_in_complete());
    assert!(matches!(s.phase(), SustainedPhase::Ready));
    assert!(s.advance().is_err());
    assert!(!s.admit_due_check_in(20000).unwrap());
    let restored_frame = apply(&mut restored);
    assert_eq!(
        serde_json::to_value(frame).unwrap(),
        serde_json::to_value(restored_frame).unwrap()
    );
    flush(&mut s, &mut base);
}

#[test]
fn recovery_keeps_check_in_context_and_requires_explicit_retry() {
    let mut s = SustainedSession::new(spec(false)).unwrap();
    s.advance().unwrap();
    s.admit_due_check_in(10000).unwrap();
    let prompt = s.pending_language().unwrap().prompt.clone();
    let mut recovered = SustainedSession::restore(s.checkpoint()).unwrap();
    assert!(recovered.blocked().is_some());
    assert!(!recovered.admit_due_check_in(20000).unwrap());
    recovered.retry_language().unwrap();
    assert_eq!(recovered.pending_language().unwrap().prompt, prompt);
    assert_eq!(
        recovered
            .pending_language()
            .unwrap()
            .check_in
            .as_ref()
            .unwrap()
            .ordinal,
        1
    );
    assert!(recovered.pending_system_contract().is_none());
    recovered.checkpoint().validate().unwrap();
}

#[test]
fn skip_then_admit_later_slot_at_same_step_preserves_valid_observation() {
    let mut s = SustainedSession::new(spec(false)).unwrap();
    let mut base = s.checkpoint();
    s.advance().unwrap();
    s.admit_due_check_in(10000).unwrap();
    s.skip_pending("skip first").unwrap();
    s.admit_due_check_in(20000).unwrap();
    flush(&mut s, &mut base);
}

#[test]
fn prepared_and_inflight_ordinary_work_cannot_be_replaced() {
    let mut s = SustainedSession::new(spec(false)).unwrap();
    let mut entries = HashMap::new();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    let attempt = s.pending_language().unwrap().attempt_id;
    s.start_language(attempt).unwrap();
    assert!(!s.admit_due_check_in(10000).unwrap());
    s.confirm_language(attempt, &response("in-flight reply"))
        .unwrap();
    assert!(!s.admit_due_check_in(10000).unwrap());
    let journal = s.pending_journal().unwrap().clone();
    s.confirm_saved(
        &SustainedSaveReceipt {
            entry_id: journal.entry.id.clone(),
            sha256: journal.entry.sha256.clone(),
            relative_path: format!("journals/{}.json", journal.entry.id),
        },
        &journal.entry,
    )
    .unwrap();
    entries.insert(journal.entry.id.clone(), journal.entry);
    assert!(!s.admit_due_check_in(10000).unwrap());
    apply(&mut s);
    assert!(s.admit_due_check_in(10000).unwrap());
}

#[test]
fn invalid_schedule_and_forged_context_are_rejected() {
    for bad in [
        "".into(),
        " \n\t".into(),
        "é".repeat(MAX_CHECK_IN_PROMPT_BYTES / 2 + 1),
    ] {
        let mut cfg = spec(false);
        cfg.check_in_schedule.as_mut().unwrap().prompt = bad;
        assert!(SustainedSession::new(cfg).is_err());
    }
    let mut cfg = schedule(false);
    cfg.interval_seconds = 0;
    assert!(cfg.validate().is_err());
    let mut s = SustainedSession::new(spec(false)).unwrap();
    let mut base = s.checkpoint();
    s.advance().unwrap();
    s.admit_due_check_in(10000).unwrap();
    let segment = flush(&mut s, &mut base);
    let mut forged = segment.clone();
    if let SustainedEventKind::CheckInAdmitted { elapsed_millis } =
        &mut forged.events.last_mut().unwrap().kind
    {
        *elapsed_millis = 9999;
    }
    assert!(forged.verify().is_err());
    let mut checkpoint = s.checkpoint();
    if let SustainedPhase::Language(p) = &mut checkpoint.state.phase {
        p.check_in.as_mut().unwrap().include_telemetry = true;
    }
    checkpoint.sha256 = format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&checkpoint.state).unwrap())
    );
    assert!(checkpoint.validate().is_err());
}

#[test]
fn absent_schedule_has_no_new_serialized_fields() {
    let s = SustainedSession::new(SustainedSpecification::default()).unwrap();
    let serialized = serde_json::to_string(&s.checkpoint()).unwrap();
    assert!(!serialized.contains("checkIn"));
    assert!(!serialized.contains("reservedAttempt"));
}

#[test]
fn scheduled_observations_update_difference_reference_between_ordinary_boundaries() {
    for telemetry in [false, true] {
        let mut cfg = spec(telemetry);
        cfg.difference_gain = 0.1;
        cfg.difference_watchdog = false;
        let mut s = SustainedSession::new(cfg).unwrap();
        let mut base = s.checkpoint();
        let mut entries = HashMap::new();
        s.advance().unwrap();
        assert!(s.admit_due_check_in(10000).unwrap());
        assert_eq!(s.checkpoint().state.difference_reference_step, 1);
        s.checkpoint().validate().unwrap();
        save(
            &mut s,
            &mut entries,
            "a thought between ordinary observations",
        );
        apply(&mut s);
        flush(&mut s, &mut base);
    }
}
