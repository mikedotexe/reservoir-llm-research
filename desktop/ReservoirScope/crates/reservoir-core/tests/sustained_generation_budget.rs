use reservoir_core::{session::LanguageResponse, sustained::*};
use sha2::{Digest, Sha256};
fn spec() -> SustainedSpecification {
    SustainedSpecification {
        seed: u64::MAX,
        turn_every: 3,
        maximum_steps: 15,
        maximum_turns: 4,
        ..Default::default()
    }
}
fn pending(spec: SustainedSpecification) -> SustainedSession {
    let mut s = SustainedSession::new(spec).unwrap();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    s
}
fn reply(tokens: i64) -> LanguageResponse {
    LanguageResponse { text: "A passage can unfold without being reduced to a heading. I leave room for another image, then reconsider the thread.\n\n".repeat(20), provider_model: None, stop_reason: Some("stop".into()), token_count: Some(tokens), complete: true, provider_prompt_evaluation: None }
}
fn rehash(c: &mut SustainedCheckpoint) {
    c.sha256 = format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&c.state).unwrap())
    );
}
#[test]
fn historical_v3_budget_omission_preserves_exact_segment_bytes_hashes_and_replay() {
    let raw = include_bytes!("fixtures/sustained-prompts/v3-legacy-budget-segment.json");
    assert_eq!(
        format!("{:x}", Sha256::digest(raw)),
        "eef2a09b2c1e4e150aac8560f210997742203b78aa709829078657e86af0c6b0"
    );
    let segment: SustainedSegment = serde_json::from_slice(raw).unwrap();
    assert_eq!(serde_json::to_vec(&segment).unwrap(), raw);
    segment.verify().unwrap();
    for c in [&segment.initial_checkpoint, &segment.final_checkpoint] {
        assert_eq!(c.state.specification.output_tokens, 256);
        assert_eq!(c.state.specification.request_deadline_seconds, 60);
        c.validate().unwrap();
    }
}
#[test]
fn new_defaults_and_legacy_deserialization_are_distinct_and_budget_bounds_fail_closed() {
    let fresh = spec();
    assert_eq!(
        (fresh.output_tokens, fresh.request_deadline_seconds),
        (1024, 180)
    );
    let mut value = serde_json::to_value(&fresh).unwrap();
    value.as_object_mut().unwrap().remove("outputTokens");
    value
        .as_object_mut()
        .unwrap()
        .remove("requestDeadlineSeconds");
    let old: SustainedSpecification = serde_json::from_value(value.clone()).unwrap();
    assert_eq!((old.output_tokens, old.request_deadline_seconds), (256, 60));
    assert_eq!(serde_json::to_value(old).unwrap(), value);
    for (key, bad) in [
        ("outputTokens", serde_json::json!(255)),
        ("outputTokens", serde_json::json!(2049)),
        ("requestDeadlineSeconds", serde_json::json!(59)),
        ("requestDeadlineSeconds", serde_json::json!(181)),
        ("outputTokens", serde_json::Value::Null),
        ("requestDeadlineSeconds", serde_json::json!(60.5)),
    ] {
        let mut changed = value.clone();
        changed[key] = bad;
        assert!(serde_json::from_value::<SustainedSpecification>(changed)
            .map(|s| s.validate().is_err())
            .unwrap_or(true));
    }
    assert!(validate_generation_budget(256, 60, Some(512)).is_ok());
    assert!(validate_generation_budget(1024, 180, Some(1024)).is_err());
    assert!(validate_generation_budget(2048, 180, Some(8192)).is_ok());
}
#[test]
fn request_budget_does_not_reword_prompt_and_cannot_be_mutated_with_a_new_hash() {
    let legacy = pending(SustainedSpecification {
        output_tokens: 256,
        request_deadline_seconds: 60,
        ..spec()
    });
    let current = pending(spec());
    assert_eq!(
        legacy.pending_language().unwrap().prompt,
        current.pending_language().unwrap().prompt
    );
    assert_eq!(current.pending_language().unwrap().output_tokens, 1024);
    assert_eq!(
        current.pending_language().unwrap().request_deadline_seconds,
        180
    );
    for member in 0..4 {
        let mut c = current.checkpoint();
        match member {
            0 => c.state.specification.output_tokens = 512,
            1 => c.state.specification.request_deadline_seconds = 90,
            2 => {
                if let SustainedPhase::Language(p) = &mut c.state.phase {
                    p.output_tokens = 512;
                }
            }
            _ => {
                if let SustainedPhase::Language(p) = &mut c.state.phase {
                    p.request_deadline_seconds = 90;
                }
            }
        }
        rehash(&mut c);
        assert!(c.validate().is_err());
    }
}
#[test]
fn long_complete_journal_survives_save_prepared_restore_application_memory_and_replay() {
    let mut s = SustainedSession::new(spec()).unwrap();
    let initial = s.checkpoint();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    s.start_language(1).unwrap();
    let r = reply(900);
    s.confirm_language(1, &r).unwrap();
    let candidate = s.pending_journal().unwrap().clone();
    assert_eq!(candidate.entry.text, r.text);
    assert!(s.advance().is_err());
    s.confirm_saved(
        &SustainedSaveReceipt {
            entry_id: candidate.entry.id.clone(),
            sha256: candidate.entry.sha256.clone(),
            relative_path: format!("journals/{}.json", candidate.entry.id),
        },
        &candidate.entry,
    )
    .unwrap();
    let prepared = s.checkpoint();
    let mut restored = SustainedSession::restore(
        serde_json::from_slice(&serde_json::to_vec(&prepared).unwrap()).unwrap(),
    )
    .unwrap();
    assert!(restored.advance().is_err());
    for engine in [&mut s, &mut restored] {
        engine.authorize_application(1).unwrap();
        let f = engine.advance().unwrap();
        assert_eq!(f.application.unwrap().applied_step, 4);
    }
    assert_eq!(s.checkpoint().sha256, restored.checkpoint().sha256);
    for _ in 0..2 {
        s.advance().unwrap();
    }
    assert_eq!(s.pending_memory().unwrap().entry.text, r.text);
    s.confirm_memory(&candidate.entry).unwrap();
    let p = s.pending_language().unwrap();
    assert_eq!((p.output_tokens, p.request_deadline_seconds), (1024, 180));
    assert_eq!(p.memory.as_ref().unwrap().entry.text, r.text);
    let encoded = p
        .prompt
        .split('\n')
        .find_map(|line| line.strip_prefix("Full previous text as one JSON string: "))
        .unwrap();
    assert_eq!(serde_json::from_str::<String>(encoded).unwrap(), r.text);
    let segment = SustainedSegment {
        format: FORMAT.into(),
        initial_checkpoint: initial,
        events: s.events().iter().cloned().collect(),
        final_checkpoint: s.checkpoint(),
    };
    segment.verify().unwrap();
    let mut changed = segment;
    changed.final_checkpoint.state.specification.output_tokens = 2048;
    if let SustainedPhase::Language(p) = &mut changed.final_checkpoint.state.phase {
        p.output_tokens = 2048;
    }
    rehash(&mut changed.final_checkpoint);
    changed.final_checkpoint.validate().unwrap();
    assert!(changed.verify().is_err());
}
#[test]
fn selected_token_bound_and_completeness_each_independently_gate_feedback() {
    for (budget, tokens, complete, stop, accepted) in [
        (256, 257, true, "stop", false),
        (1024, 900, true, "stop", true),
        (2048, 2048, true, "stop", true),
        (2048, 2049, true, "stop", false),
        (1024, 900, false, "stop", false),
        (1024, 1024, true, "length", false),
    ] {
        let mut s = pending(SustainedSpecification {
            output_tokens: budget,
            ..spec()
        });
        s.start_language(1).unwrap();
        let mut r = reply(tokens);
        r.complete = complete;
        r.stop_reason = Some(stop.into());
        s.confirm_language(1, &r).unwrap();
        assert_eq!(s.pending_journal().is_some(), accepted);
        assert_eq!(s.blocked().is_some(), !accepted);
        assert!(s.prepared_application().is_none());
        assert!(s.advance().is_err());
        s.checkpoint().validate().unwrap();
    }
}
