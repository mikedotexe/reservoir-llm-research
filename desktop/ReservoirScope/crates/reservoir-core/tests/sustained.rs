use reservoir_core::{
    session::LanguageResponse,
    stage::{LanguageConfiguration, LanguageKind},
    sustained::*,
};
use serde::Serialize;
use sha2::{Digest, Sha256};
fn bytes<T: Serialize>(v: &T) -> Vec<u8> {
    serde_json::to_vec(v).unwrap()
}
fn same<T: Serialize>(a: &T, b: &T) {
    assert_eq!(bytes(a), bytes(b));
}
fn spec() -> SustainedSpecification {
    SustainedSpecification {
        seed: u64::MAX,
        turn_every: 3,
        maximum_steps: 100,
        maximum_turns: 30,
        ..Default::default()
    }
}
fn response() -> LanguageResponse {
    LanguageResponse {
        text: "I notice the changing pattern and remember what came before.".into(),
        provider_model: None,
        stop_reason: Some("stop".into()),
        token_count: Some(18),
        complete: true,
        provider_prompt_evaluation: None,
    }
}
fn checkpoint(s: &SustainedSession) -> SustainedCheckpoint {
    serde_json::from_slice(&bytes(&s.checkpoint())).unwrap()
}
fn receipt(j: &SustainedPendingJournal) -> SustainedSaveReceipt {
    SustainedSaveReceipt {
        entry_id: j.entry.id.clone(),
        sha256: j.entry.sha256.clone(),
        relative_path: format!("journals/{}.json", j.entry.id),
    }
}
fn flush(s: &mut SustainedSession, base: &mut SustainedCheckpoint) -> SustainedSegment {
    let segment = SustainedSegment {
        format: FORMAT.into(),
        initial_checkpoint: base.clone(),
        events: s.events().iter().cloned().collect(),
        final_checkpoint: checkpoint(s),
    };
    segment.verify().unwrap();
    s.acknowledge_events(segment.events.last().unwrap().id)
        .unwrap();
    *base = segment.final_checkpoint.clone();
    segment
}
fn settle(s: &mut SustainedSession) {
    if let Some(m) = s.pending_memory().cloned() {
        s.confirm_memory(m.entry.as_ref().unwrap()).unwrap();
    }
    if let Some(p) = s.pending_language().cloned() {
        s.start_language(p.attempt_id).unwrap();
        s.confirm_language(p.attempt_id, &response()).unwrap();
    }
    if let Some(j) = s.pending_journal().cloned() {
        s.confirm_saved(&receipt(&j), &j.entry).unwrap();
    }
    if let Some(p) = s.prepared_application() {
        let id = p.entry.attempt_id;
        s.authorize_application(id).unwrap();
    }
}
fn rehash(c: &mut SustainedCheckpoint) {
    c.sha256 = format!("{:x}", Sha256::digest(bytes(&c.state)));
}
#[test]
fn save_then_persist_authorization_then_exactly_one_next_step_application() {
    let mut s = SustainedSession::new(spec()).unwrap();
    let mut base = s.checkpoint();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    let p = s.pending_language().unwrap().clone();
    assert_eq!(p.observation.state, s.latest_frame().unwrap().state);
    assert_eq!(p.observation.previous_observation_step, None);
    assert_eq!(p.observation.change_l2, None);
    assert_eq!(p.observation.state.len(), 32);
    assert_eq!(p.observation.sensory.eigenvalues.len(), 32);
    assert!(p.prompt.contains("Recurrent state RMS: current "));
    assert!(!p.prompt.contains("All recurrent state coordinates"));
    assert!(!p.prompt.contains("Separate sensory field eigenvalues"));
    assert!(s.advance().is_err());
    assert!(s.confirm_language(p.attempt_id, &response()).is_err());
    s.start_language(p.attempt_id).unwrap();
    assert!(s.start_language(p.attempt_id).is_err());
    assert!(s.confirm_language(p.attempt_id + 1, &response()).is_err());
    s.confirm_language(p.attempt_id, &response()).unwrap();
    let j = s.pending_journal().unwrap().clone();
    assert!(s.advance().is_err());
    let before = bytes(&s.checkpoint());
    let mut bad = receipt(&j);
    bad.sha256 = "0".repeat(64);
    assert!(s.confirm_saved(&bad, &j.entry).is_err());
    assert_eq!(before, bytes(&s.checkpoint()));
    s.confirm_saved(&receipt(&j), &j.entry).unwrap();
    assert!(s.advance().is_err());
    assert!(s.latest_memory().is_none());
    let segment = flush(&mut s, &mut base);
    let evidence = segment.journal_evidence().unwrap();
    assert_eq!(evidence.len(), 1);
    same(&evidence[0], &j);
    s.authorize_application(p.attempt_id).unwrap();
    let f = s.advance().unwrap();
    assert_eq!(f.step, 4);
    assert_eq!(f.application.as_ref().unwrap().applied_step, 4);
    assert_eq!(f.input[18..], j.semantic_vector);
    assert_eq!(s.latest_memory().unwrap().entry.id, j.entry.id);
    let f = s.advance().unwrap();
    assert!(f.application.is_none());
    assert_eq!(f.input[18..], j.semantic_vector);
    flush(&mut s, &mut base);
}
#[test]
fn segmented_and_serialized_continuation_matches_uninterrupted_across_all_saved_gates() {
    let mut a = SustainedSession::new(spec()).unwrap();
    let mut b = SustainedSession::new(spec()).unwrap();
    let mut base = b.checkpoint();
    for _ in 0..70 {
        a.advance().unwrap();
        b.advance().unwrap();
        if let Some(m) = a.pending_memory().cloned() {
            a.confirm_memory(m.entry.as_ref().unwrap()).unwrap();
            flush(&mut b, &mut base);
            b = SustainedSession::restore(checkpoint(&b)).unwrap();
            b.confirm_memory(m.entry.as_ref().unwrap()).unwrap();
        }
        if let Some(p) = a.pending_language().cloned() {
            a.start_language(p.attempt_id).unwrap();
            a.confirm_language(p.attempt_id, &response()).unwrap();
            b.start_language(p.attempt_id).unwrap();
            b.confirm_language(p.attempt_id, &response()).unwrap();
        }
        if let Some(j) = a.pending_journal().cloned() {
            flush(&mut b, &mut base);
            b = SustainedSession::restore(checkpoint(&b)).unwrap();
            a.confirm_saved(&receipt(&j), &j.entry).unwrap();
            b.confirm_saved(&receipt(&j), &j.entry).unwrap();
            flush(&mut b, &mut base);
            b = SustainedSession::restore(checkpoint(&b)).unwrap();
        }
        if let Some(p) = a.prepared_application() {
            let id = p.entry.attempt_id;
            a.authorize_application(id).unwrap();
            assert!(b.advance().is_err());
            b.authorize_application(id).unwrap();
        } else if b.events().len() >= 7 {
            flush(&mut b, &mut base);
            b = SustainedSession::restore(checkpoint(&b)).unwrap();
        }
        same(&a.checkpoint(), &b.checkpoint());
        if let Some(e) = a.events().back() {
            let id = e.id;
            a.acknowledge_events(id).unwrap();
        }
    }
    if !b.events().is_empty() {
        flush(&mut b, &mut base);
    }
    assert_eq!(a.step(), 70);
    assert_ne!(a.checkpoint().state.rng_state, u64::MAX);
    assert!(a.latest_memory().is_some());
}
#[test]
fn prepared_or_started_recovery_never_resends_and_retry_allocates_new_attempt() {
    for started in [false, true] {
        let mut s = SustainedSession::new(spec()).unwrap();
        let mut base = s.checkpoint();
        for _ in 0..3 {
            s.advance().unwrap();
        }
        if started {
            s.start_language(1).unwrap();
        }
        flush(&mut s, &mut base);
        let original = checkpoint(&s);
        let mut resumed = SustainedSession::restore(original.clone()).unwrap();
        assert!(resumed.blocked().is_some());
        assert!(resumed.pending_language().is_none());
        assert!(resumed.advance().is_err());
        assert!(resumed.confirm_language(1, &response()).is_err());
        resumed.retry_language().unwrap();
        assert_eq!(resumed.pending_language().unwrap().attempt_id, 2);
        assert!(!resumed.pending_language().unwrap().request_started);
        resumed.start_language(2).unwrap();
        resumed.confirm_language(2, &response()).unwrap();
        let j = resumed.pending_journal().unwrap().clone();
        resumed.confirm_saved(&receipt(&j), &j.entry).unwrap();
        resumed.authorize_application(2).unwrap();
        let f = resumed.advance().unwrap();
        assert_eq!(f.application.unwrap().attempt_id, 2);
        let mut base = original;
        flush(&mut resumed, &mut base);
    }
}
#[test]
fn failed_incomplete_mismatched_and_unqualified_responses_never_gain_feedback() {
    let mut cfg = spec();
    cfg.language = LanguageConfiguration {
        backend: LanguageKind::Ollama,
        endpoint: Some("http://127.0.0.1:11499".into()),
        model: Some("selected-model".into()),
        context_tokens: Some(2048),
        response_format: None,
        temperature: None,
        thinking: None,
    };
    for mode in 0..8 {
        let mut s = SustainedSession::new(cfg.clone()).unwrap();
        let mut base = s.checkpoint();
        for _ in 0..3 {
            s.advance().unwrap();
        }
        s.start_language(1).unwrap();
        let mut r = response();
        r.provider_model = Some("selected-model".into());
        match mode {
            0 => r.complete = false,
            1 => r.stop_reason = Some("length".into()),
            2 => r.token_count = Some(-1),
            3 => r.text = " \n".into(),
            4 => r.text = "x".repeat(65537),
            5 => r.provider_model = Some("substitute".into()),
            6 => r.text = "\u{10ffff}".into(),
            _ => r.token_count = Some(i64::from(cfg.output_tokens) + 1),
        };
        s.confirm_language(1, &r).unwrap();
        assert!(s.blocked().is_some());
        assert!(s.pending_journal().is_none());
        assert!(s.prepared_application().is_none());
        assert!(s.advance().is_err());
        assert!(s.confirm_language(1, &response()).is_err());
        s.skip_pending("Explicitly skip this failed writing opportunity")
            .unwrap();
        let f = s.advance().unwrap();
        assert!(f.application.is_none());
        assert!(f.input[18..].iter().all(|x| *x == 0.0));
        flush(&mut s, &mut base);
    }
}
#[test]
fn memory_must_be_reread_and_skipped_saved_journal_never_enters_memory() {
    let mut s = SustainedSession::new(spec()).unwrap();
    let mut base = s.checkpoint();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    settle(&mut s);
    for _ in 0..3 {
        s.advance().unwrap();
    }
    let m = s.pending_memory().unwrap().clone();
    assert_eq!(m.observed_step, 6);
    let first = m.entry.clone().unwrap();
    let mut bad = first.clone();
    bad.text.push('!');
    assert!(s.confirm_memory(&bad).is_err());
    assert!(s.pending_language().is_none());
    s.fail_memory("Fresh readback was not available").unwrap();
    assert_eq!(s.blocked().unwrap().pending.attempt_id, 0);
    s.retry_language().unwrap();
    assert!(s.pending_memory().is_some());
    s.confirm_memory(&first).unwrap();
    let p = s.pending_language().unwrap().clone();
    assert_eq!(p.attempt_id, 2);
    assert_eq!(p.memory.as_ref().unwrap().entry.sha256, first.sha256);
    assert!(!p.prompt.contains(&first.sha256));
    let quoted = p
        .prompt
        .split('\n')
        .find_map(|line| line.strip_prefix("Full previous text as one JSON string: "))
        .unwrap();
    assert_eq!(serde_json::from_str::<String>(quoted).unwrap(), first.text);
    assert_eq!(p.observation.previous_observation_step, Some(3));
    s.start_language(2).unwrap();
    s.confirm_language(2, &response()).unwrap();
    let j = s.pending_journal().unwrap().clone();
    s.confirm_saved(&receipt(&j), &j.entry).unwrap();
    s.skip_pending("Keep this saved journal readable but do not apply or expose it as memory")
        .unwrap();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    assert_eq!(
        s.pending_memory().unwrap().entry.as_ref().unwrap().id,
        first.id
    );
    assert_ne!(
        s.pending_memory().unwrap().entry.as_ref().unwrap().id,
        j.entry.id
    );
    flush(&mut s, &mut base);
}
#[test]
fn bounded_outbox_backpressure_and_step_attempt_budget_extension_preserve_rng() {
    let mut cfg = spec();
    cfg.maximum_steps = 1000;
    cfg.turn_every = 1800;
    let mut s = SustainedSession::new(cfg).unwrap();
    let mut base = s.checkpoint();
    for _ in 0..MAX_EVENTS {
        s.advance().unwrap();
    }
    let before = bytes(&s.checkpoint());
    assert!(s.advance().is_err());
    assert_eq!(before, bytes(&s.checkpoint()));
    assert_eq!(s.events().len(), MAX_EVENTS);
    assert!(s.acknowledge_events(999).is_err());
    flush(&mut s, &mut base);
    assert_eq!(s.events().len(), 0);
    s.advance().unwrap();
    assert_eq!(s.step(), 129);
    let mut cfg = spec();
    cfg.maximum_turns = 1;
    let mut s = SustainedSession::new(cfg).unwrap();
    let mut base = s.checkpoint();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    assert!(s.budget_reached());
    settle(&mut s);
    s.advance().unwrap();
    assert_eq!(s.step(), 4);
    assert!(s.advance().is_err());
    let rng = s.checkpoint().state.rng_state;
    s.extend_budgets(101, 2).unwrap();
    s.advance().unwrap();
    assert_ne!(rng, s.checkpoint().state.rng_state);
    assert_eq!(s.step(), 5);
    flush(&mut s, &mut base);
}
#[test]
fn checkpoint_integrity_deep_prompt_vector_guards_and_segment_replay_reject_tampering() {
    let mut s = SustainedSession::new(spec()).unwrap();
    let base = s.checkpoint();
    let mut altered_genesis = base.clone();
    altered_genesis.state.reservoir_state[0] = 0.1;
    rehash(&mut altered_genesis);
    assert!(altered_genesis.validate().is_err());
    for _ in 0..3 {
        s.advance().unwrap();
    }
    let mut c = checkpoint(&s);
    c.state.rng_state ^= 1;
    assert!(c.validate().is_err());
    rehash(&mut c);
    assert!(c.validate().is_err());
    let mut c = checkpoint(&s);
    if let SustainedPhase::Language(p) = &mut c.state.phase {
        p.prompt.push_str("changed");
    }
    rehash(&mut c);
    assert!(c.validate().is_err());
    settle(&mut s);
    let mut c = checkpoint(&s);
    if let SustainedPhase::Prepared(p) = &mut c.state.phase {
        p.semantic_vector[0] += 0.1;
    }
    rehash(&mut c);
    assert!(c.validate().is_err());
    s.advance().unwrap();
    let seg = SustainedSegment {
        format: FORMAT.into(),
        initial_checkpoint: base,
        events: s.events().iter().cloned().collect(),
        final_checkpoint: checkpoint(&s),
    };
    seg.verify().unwrap();
    let mut altered = seg.clone();
    if let SustainedEventKind::Advanced(f) = &mut altered.events[0].kind {
        f.state[0] += 0.0001;
    }
    assert!(altered.verify().is_err());
    let mut altered = seg.clone();
    altered.final_checkpoint.state.sensory_covariance[0] += 0.01;
    rehash(&mut altered.final_checkpoint);
    assert!(altered.verify().is_err());
    let mut altered = seg.clone();
    altered.events.swap(3, 4);
    assert!(altered.verify().is_err());
    let mut altered = seg.clone();
    if let SustainedEventKind::JournalSaved { entry, .. } = &mut altered
        .events
        .iter_mut()
        .find(|e| matches!(e.kind, SustainedEventKind::JournalSaved { .. }))
        .unwrap()
        .kind
    {
        entry.text.push('!');
    }
    assert!(altered.verify().is_err());
}
#[test]
fn cancellation_is_terminal_for_attempt_and_all_failure_events_replay() {
    for started in [false, true] {
        let mut s = SustainedSession::new(spec()).unwrap();
        let mut base = s.checkpoint();
        for _ in 0..3 {
            s.advance().unwrap();
        }
        if started {
            s.start_language(1).unwrap();
            s.fail_language(1, "Transport failed").unwrap();
        } else {
            s.cancel_language(1, "Cancelled before dispatch").unwrap();
        }
        assert!(s.confirm_language(1, &response()).is_err());
        s.retry_language().unwrap();
        s.start_language(2).unwrap();
        s.cancel_language(2, "Explicit cancellation after dispatch")
            .unwrap();
        s.skip_pending("Skip this opportunity").unwrap();
        s.advance().unwrap();
        flush(&mut s, &mut base);
    }
}

#[test]
fn stream_passes_historical_caps_with_bounded_outbox_and_no_rng_restart() {
    let mut cfg = spec();
    cfg.maximum_steps = 3605;
    cfg.maximum_turns = 200;
    cfg.turn_every = 30;
    let mut s = SustainedSession::new(cfg).unwrap();
    let mut base = s.checkpoint();
    let mut segments = 0;
    let mut max_outbox = 0;
    let mut max_checkpoint_bytes = 0;
    for expected in 1..=3605 {
        s.advance().unwrap();
        settle(&mut s);
        assert_eq!(s.step(), expected);
        max_outbox = max_outbox.max(s.events().len());
        max_checkpoint_bytes = max_checkpoint_bytes.max(bytes(&s.checkpoint()).len());
        assert!(max_checkpoint_bytes < 100_000);
        if s.events().len() >= 48 {
            // Flush only at ready or saved/prepared boundaries; restoring a model
            // request would correctly require an explicit interruption/retry.
            flush(&mut s, &mut base);
            segments += 1;
            s = SustainedSession::restore(checkpoint(&s)).unwrap();
            if let Some(p) = s.prepared_application() {
                let id = p.entry.attempt_id;
                s.authorize_application(id).unwrap();
            }
        }
    }
    if !s.events().is_empty() {
        flush(&mut s, &mut base);
        segments += 1;
    }
    assert!(max_outbox <= 53);
    assert!(segments > 70);
    assert_eq!(s.step(), 3605);
    assert_eq!(s.checkpoint().state.attempt_cursor, 120);
    assert!(s.advance().is_err());
    assert!(s.events().is_empty());
    println!(
        "{}",
        serde_json::json!({"qualification":"accelerated-core-stream-not-wall-time-soak","steps":s.step(),"attempts":s.checkpoint().state.attempt_cursor,"verifiedSegments":segments,"maximumRetainedEvents":max_outbox,"maximumCheckpointBytes":max_checkpoint_bytes,"modelsContacted":false})
    );
}

#[test]
fn skipped_memory_failures_count_opportunities_without_fabricating_provider_attempts() {
    let mut s = SustainedSession::new(spec()).unwrap();
    let mut base = s.checkpoint();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    settle(&mut s);
    for _ in 0..2 {
        for _ in 0..3 {
            s.advance().unwrap();
        }
        s.fail_memory("The saved object could not be read").unwrap();
        s.skip_pending("Skip this observation without a model request")
            .unwrap();
        s.checkpoint().validate().unwrap();
    }
    for _ in 0..3 {
        s.advance().unwrap();
    }
    let m = s.pending_memory().unwrap().clone();
    s.confirm_memory(m.entry.as_ref().unwrap()).unwrap();
    assert_eq!(s.pending_language().unwrap().turn_id, 4);
    assert_eq!(s.pending_language().unwrap().attempt_id, 2);
    settle(&mut s);
    s.advance().unwrap();
    flush(&mut s, &mut base);
}
