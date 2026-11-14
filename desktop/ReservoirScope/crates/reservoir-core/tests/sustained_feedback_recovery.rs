//! Completed writing is durable evidence before embedding, and encoding retries
//! never regenerate it, consume another writing attempt, or apply actions early.
use reservoir_core::{codec, session::LanguageResponse, sustained::*};
use sha2::{Digest, Sha256};

fn spec() -> SustainedSpecification {
    SustainedSpecification {
        turn_every: 3,
        maximum_steps: 100,
        maximum_turns: 1,
        codec: SustainedCodec::Embedding {
            model: "nomic-embed-text:latest".into(),
            projection_seed: 99,
        },
        action_mode: Some(SustainedActionMode::AuthoredV2),
        prompt_version: SustainedPromptVersion::ActionJournalV2,
        ..Default::default()
    }
}
fn response(text: &str) -> LanguageResponse {
    LanguageResponse {
        text: text.into(),
        provider_model: None,
        stop_reason: Some("stop".into()),
        token_count: Some(20),
        complete: true,
        provider_prompt_evaluation: None,
    }
}
fn external() -> ExternalFeedback {
    let source: Vec<_> = (0..768).map(|i| (i as f64 * 0.37).sin()).collect();
    ExternalFeedback {
        vector: codec::project_embedding(&source, 99).unwrap(),
        provenance: FeedbackProvenance {
            kind: "embedding".into(),
            model: "nomic-embed-text:latest".into(),
            digest: None,
            dimensions: 768,
            embedding_sha256: format!("{:x}", Sha256::digest(b"fixture embedding")),
            projection_seed: 99,
        },
    }
}
fn reach(s: &mut SustainedSession) -> u64 {
    for _ in 0..3 {
        s.advance().unwrap();
    }
    let id = s.pending_language().unwrap().attempt_id;
    s.start_language(id).unwrap();
    id
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
fn save(s: &mut SustainedSession) -> SustainedPendingJournal {
    let j = s.pending_journal().unwrap().clone();
    s.confirm_saved(
        &SustainedSaveReceipt {
            entry_id: j.entry.id.clone(),
            sha256: j.entry.sha256.clone(),
            relative_path: format!("journals/{}.json", j.entry.id),
        },
        &j.entry,
    )
    .unwrap();
    j
}
fn rehash(checkpoint: &mut SustainedCheckpoint) {
    checkpoint.sha256 = format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&checkpoint.state).unwrap())
    );
}

#[test]
fn completed_reply_survives_failure_restore_retry_and_applies_once_at_writer_cap() {
    let mut s = SustainedSession::new(spec()).unwrap();
    let mut base = s.checkpoint();
    let id = reach(&mut s);
    let reply = response("Keep this exact writing.\n\nNEXT: TUNE leak 0.35");
    let prompt = s.pending_language().unwrap().prompt.clone();
    assert!(s.response_needs_feedback(&reply).unwrap());
    s.retain_language_for_feedback(id, &reply).unwrap();
    assert!(s.budget_reached());
    assert!(s.advance().is_err());
    assert!(s.retry_language().is_err());
    assert!(s.retry_feedback().is_err());
    assert!(s.confirm_feedback(id, 0, &external()).is_err());
    assert_eq!(
        s.feedback_text_for_response(&reply.text).unwrap(),
        "Keep this exact writing."
    );
    assert!(s.feedback_text_for_response("different writing").is_err());
    assert_eq!(flush(&mut s, &mut base).checked_turns(), 1);
    let first_request = s.start_feedback(id).unwrap();
    assert_eq!(first_request, 1);
    assert!(s.start_feedback(id).is_err());
    s.fail_feedback(id, first_request, "embedding service unavailable")
        .unwrap();
    assert!(s.pending_journal().is_none());
    assert_eq!(s.action_state().unwrap().controls.leak, spec().leak);
    assert_eq!(flush(&mut s, &mut base).checked_turns(), 0);
    let checkpoint: SustainedCheckpoint =
        serde_json::from_slice(&serde_json::to_vec(&base).unwrap()).unwrap();
    s = SustainedSession::restore(checkpoint).unwrap();
    assert!(s.events().is_empty());
    let held = s.pending_feedback().unwrap();
    assert_eq!(held.response.text, reply.text);
    assert_eq!(held.pending.prompt, prompt);
    assert_eq!(held.pending.attempt_id, id);
    s.retry_feedback().unwrap();
    let next_request = s.start_feedback(id).unwrap();
    assert_eq!(next_request, 2);
    assert!(s.confirm_feedback(id, first_request, &external()).is_err());
    assert!(s.fail_feedback(id, first_request, "late failure").is_err());
    assert!(s
        .confirm_feedback(id + 1, next_request, &external())
        .is_err());
    s.confirm_feedback(id, next_request, &external()).unwrap();
    assert!(s.confirm_feedback(id, next_request, &external()).is_err());
    let j = save(&mut s);
    assert_eq!(j.response.text, reply.text);
    assert_eq!(j.entry.attempt_id, id);
    assert!(s.advance().is_err());
    flush(&mut s, &mut base);
    s.authorize_application(id).unwrap();
    let frame = s.advance().unwrap();
    assert!(frame.application.is_some());
    assert_eq!(s.action_state().unwrap().controls.leak, 0.35);
    assert_eq!(s.action_state().unwrap().recent_receipts.len(), 1);
    assert!(s.advance().is_err());
    flush(&mut s, &mut base);
}

#[test]
fn recovery_before_or_during_embedding_requires_explicit_retry_of_retained_text() {
    for started in [false, true] {
        let mut s = SustainedSession::new(spec()).unwrap();
        let mut base = s.checkpoint();
        let id = reach(&mut s);
        let reply = response("The same completed response.\n\nNEXT: NONE");
        s.retain_language_for_feedback(id, &reply).unwrap();
        if started {
            s.start_feedback(id).unwrap();
        }
        flush(&mut s, &mut base);
        s = SustainedSession::restore(base.clone()).unwrap();
        let held = s.pending_feedback().unwrap();
        assert!(!held.request_started);
        assert!(held.failure.as_ref().unwrap().contains("Recovery retained"));
        assert_eq!(held.response.text, reply.text);
        assert!(s.start_feedback(id).is_err());
        assert_eq!(flush(&mut s, &mut base).checked_turns(), 0);
        s.retry_feedback().unwrap();
        assert_eq!(s.start_feedback(id).unwrap(), if started { 2 } else { 1 });
        flush(&mut s, &mut base);
    }
}

#[test]
fn malformed_feedback_and_checkpoint_tampering_never_replace_retained_writing() {
    let mut s = SustainedSession::new(spec()).unwrap();
    let mut base = s.checkpoint();
    let id = reach(&mut s);
    let reply = response("Preserve me through bad encoding.\n\nNEXT: NONE");
    s.retain_language_for_feedback(id, &reply).unwrap();
    let request_id = s.start_feedback(id).unwrap();
    let mut wrong = external();
    wrong.provenance.model = "wrong-model".into();
    assert!(s.confirm_feedback(id, request_id, &wrong).is_err());
    assert_eq!(s.pending_feedback().unwrap().response.text, reply.text);
    assert!(s.pending_feedback().unwrap().request_started);
    s.fail_feedback(id, request_id, "feedback validation failed")
        .unwrap();
    let segment = flush(&mut s, &mut base);
    let mut altered = segment.clone();
    for event in &mut altered.events {
        if let SustainedEventKind::LanguageRetainedForFeedback { response, .. } = &mut event.kind {
            response.text.push_str(" altered");
        }
    }
    assert!(altered.verify().is_err());
    for mutation in 0..3 {
        let mut altered = base.clone();
        if let SustainedPhase::Feedback(p) = &mut altered.state.phase {
            match mutation {
                0 => p.response.complete = false,
                1 => {
                    p.request_started = true;
                    p.request_id = 0;
                    p.failure = None;
                }
                _ => p.pending.prompt.push_str(" tampered"),
            }
        }
        rehash(&mut altered);
        assert!(altered.validate().is_err());
    }
}

#[test]
fn incomplete_and_withheld_replies_keep_their_existing_paths() {
    for text in [
        "Keep words in memory.\n\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: TUNE leak 0.35",
        "NEXT: NONE",
    ] {
        let mut s = SustainedSession::new(spec()).unwrap();
        let base = s.checkpoint();
        let id = reach(&mut s);
        let reply = response(text);
        assert!(!s.response_needs_feedback(&reply).unwrap());
        assert!(s.retain_language_for_feedback(id, &reply).is_err());
        s.confirm_language(id, &reply).unwrap();
        let j = s.pending_journal().unwrap();
        assert!(j.feedback_provenance.is_none());
        assert_eq!(j.semantic_vector, vec![0.0; 48]);
        let segment = SustainedSegment {
            format: FORMAT.into(),
            initial_checkpoint: base,
            events: s.events().iter().cloned().collect(),
            final_checkpoint: s.checkpoint(),
        };
        segment.verify().unwrap();
    }
    let mut s = SustainedSession::new(spec()).unwrap();
    let id = reach(&mut s);
    let mut incomplete = response("Partial output.");
    incomplete.complete = false;
    assert!(s.response_needs_feedback(&incomplete).is_err());
    assert!(s.retain_language_for_feedback(id, &incomplete).is_err());
    s.confirm_language(id, &incomplete).unwrap();
    assert!(s.blocked().unwrap().reason.contains("Incomplete"));
    assert!(matches!(
        s.events().back().unwrap().kind,
        SustainedEventKind::LanguageReceived { .. }
    ));
}

#[test]
fn check_in_directives_remain_passive_through_embedding_recovery_and_final_application() {
    let mut cfg = spec();
    cfg.check_in_schedule = Some(SustainedCheckInSchedule {
        interval_seconds: 10,
        end_after_seconds: 10,
        prompt: "Tell me what comes to mind.".into(),
        include_telemetry: false,
    });
    let mut s = SustainedSession::new(cfg).unwrap();
    let mut base = s.checkpoint();
    s.advance().unwrap();
    assert!(s.admit_due_check_in(10_000).unwrap());
    let id = s.pending_language().unwrap().attempt_id;
    s.start_language(id).unwrap();
    let reply =
        response("A passive check-in.\n\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: TUNE leak 0.35");
    assert!(s.response_needs_feedback(&reply).unwrap());
    s.retain_language_for_feedback(id, &reply).unwrap();
    let request_id = s.start_feedback(id).unwrap();
    s.interrupt("App stopped during embedding").unwrap();
    assert!(!s.check_in_complete());
    assert_eq!(
        s.check_in_state().unwrap().outcomes[0].status,
        SustainedCheckInStatus::Pending
    );
    flush(&mut s, &mut base);
    s.retry_feedback().unwrap();
    let next = s.start_feedback(id).unwrap();
    assert!(s.confirm_feedback(id, request_id, &external()).is_err());
    s.confirm_feedback(id, next, &external()).unwrap();
    let journal = save(&mut s);
    assert!(journal.action.is_none());
    assert_eq!(journal.entry.text, reply.text);
    assert!(!s.check_in_complete());
    s.authorize_application(id).unwrap();
    s.advance().unwrap();
    assert!(s.check_in_complete());
    assert_eq!(s.action_state().unwrap().controls.leak, spec().leak);
    assert!(s.action_state().unwrap().recent_receipts.is_empty());
    flush(&mut s, &mut base);
}

#[test]
fn explicit_skip_retains_generated_response_event_without_applying_it() {
    let mut s = SustainedSession::new(spec()).unwrap();
    let mut base = s.checkpoint();
    let id = reach(&mut s);
    let reply = response("Keep this as evidence only.\n\nNEXT: TUNE leak 0.35");
    s.retain_language_for_feedback(id, &reply).unwrap();
    s.interrupt("Stopped before encoding").unwrap();
    s.skip_pending("User explicitly skipped numerical feedback")
        .unwrap();
    assert!(matches!(s.phase(), SustainedPhase::Ready));
    assert!(s.latest_memory().is_none());
    assert!(s.action_state().unwrap().recent_receipts.is_empty());
    let segment = flush(&mut s, &mut base);
    assert_eq!(segment.checked_turns(), 1);
    assert!(segment.events.iter().any(|e| matches!(&e.kind,
        SustainedEventKind::LanguageRetainedForFeedback { response, .. } if response.text == reply.text)));
}
