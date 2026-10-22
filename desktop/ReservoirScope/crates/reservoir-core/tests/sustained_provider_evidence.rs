use reservoir_core::{
    session::{LanguageResponse, ProviderPromptEvaluation, ProviderPromptEvaluationIssue},
    sustained::*,
};
use serde_json::json;
use sha2::{Digest, Sha256};

fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn response(evidence: Option<ProviderPromptEvaluation>) -> LanguageResponse {
    LanguageResponse {
        text: "Rain gathers at the edge of an imagined room. I can leave this image open.".into(),
        provider_model: None,
        stop_reason: Some("stop".into()),
        token_count: Some(22),
        complete: true,
        provider_prompt_evaluation: evidence,
    }
}
fn session(version: SustainedPromptVersion) -> SustainedSession {
    SustainedSession::new(SustainedSpecification {
        seed: u64::MAX,
        turn_every: 3,
        maximum_steps: 7,
        maximum_turns: 2,
        prompt_version: version,
        ..Default::default()
    })
    .unwrap()
}
fn advance(s: &mut SustainedSession, count: usize) {
    for _ in 0..count {
        s.advance().unwrap();
    }
}
fn segment(s: &SustainedSession, initial: SustainedCheckpoint) -> SustainedSegment {
    SustainedSegment {
        format: FORMAT.into(),
        initial_checkpoint: initial,
        events: s.events().iter().cloned().collect(),
        final_checkpoint: s.checkpoint(),
    }
}
fn rehash(c: &mut SustainedCheckpoint) {
    c.sha256 = hash(&serde_json::to_vec(&c.state).unwrap());
}
fn variants() -> Vec<Option<ProviderPromptEvaluation>> {
    let mut out = vec![None];
    out.extend(
        [0, 9_007_199_254_740_993, u64::MAX]
            .map(|count| Some(ProviderPromptEvaluation::Reported { count })),
    );
    out.extend(
        [
            ProviderPromptEvaluationIssue::WrongType,
            ProviderPromptEvaluationIssue::Negative,
            ProviderPromptEvaluationIssue::NonInteger,
            ProviderPromptEvaluationIssue::OutOfRange,
            ProviderPromptEvaluationIssue::DuplicateField,
        ]
        .map(|reason| Some(ProviderPromptEvaluation::Unusable { reason })),
    );
    out
}

#[test]
fn absent_or_null_evidence_keeps_historical_response_bytes() {
    let old = br#"{"text":"old prose","providerModel":null,"stopReason":"stop","tokenCount":7,"complete":true}"#;
    let old_response: LanguageResponse = serde_json::from_slice(old).unwrap();
    assert!(old_response.provider_prompt_evaluation.is_none());
    assert_eq!(serde_json::to_vec(&old_response).unwrap(), old);
    let mut explicit_null: serde_json::Value = serde_json::from_slice(old).unwrap();
    explicit_null["providerPromptEvaluation"] = serde_json::Value::Null;
    let decoded: LanguageResponse = serde_json::from_value(explicit_null).unwrap();
    assert_eq!(serde_json::to_vec(&decoded).unwrap(), old);

    let frozen = include_bytes!("fixtures/sustained-prompts/v3-legacy-budget-segment.json");
    assert_eq!(
        hash(frozen),
        "eef2a09b2c1e4e150aac8560f210997742203b78aa709829078657e86af0c6b0"
    );
    let old_segment: SustainedSegment = serde_json::from_slice(frozen).unwrap();
    assert_eq!(serde_json::to_vec(&old_segment).unwrap(), frozen);
    // Exact historical replay has a separate host qualification boundary in
    // sustained_generation_budget::historical_macos_arm64_v3_budget_segment_replays_exactly.
}

#[test]
fn reported_zero_and_wide_integer_values_and_unusable_reasons_roundtrip_exactly() {
    for evidence in variants().into_iter().flatten() {
        let r = response(Some(evidence.clone()));
        let raw = serde_json::to_vec(&r).unwrap();
        let decoded: LanguageResponse = serde_json::from_slice(&raw).unwrap();
        assert_eq!(decoded.provider_prompt_evaluation, Some(evidence));
        assert_eq!(serde_json::to_vec(&decoded).unwrap(), raw);
    }
    let raw = serde_json::to_string(&response(Some(ProviderPromptEvaluation::Reported {
        count: u64::MAX,
    })))
    .unwrap();
    assert!(raw.contains(r#""count":18446744073709551615"#));
}

#[test]
fn typed_evidence_rejects_ambiguous_or_unbounded_schema_but_transport_issues_are_data() {
    // These are malformed *retained evidence objects*, not raw provider fields.
    // The transport maps optional malformed provider values to Unusable.
    for invalid in [
        json!({"status":"reported","count":-1}),
        json!({"status":"reported","count":1.0}),
        json!({"status":"reported","count":"1"}),
        json!({"status":"reported","count":null}),
        json!({"status":"reported","count":true}),
        json!({"status":"reported","count":1,"reason":"negative"}),
        json!({"status":"unusable","reason":"invented"}),
        json!({"status":"unusable","reason":"wrongType","count":1}),
        json!({"status":"future","count":1}),
    ] {
        assert!(serde_json::from_value::<ProviderPromptEvaluation>(invalid).is_err());
    }
    assert!(serde_json::from_str::<ProviderPromptEvaluation>(
        r#"{"status":"reported","count":18446744073709551616}"#
    )
    .is_err());
    assert!(serde_json::from_str::<ProviderPromptEvaluation>(
        r#"{"status":"reported","count":1,"count":2}"#
    )
    .is_err());
}

#[test]
fn input_evidence_never_changes_prompts_save_gate_application_or_numerical_state() {
    for version in [
        SustainedPromptVersion::LegacyV1,
        SustainedPromptVersion::GroundedV2,
        SustainedPromptVersion::OpenJournalV3,
        SustainedPromptVersion::OpenJournalV4,
        SustainedPromptVersion::ContinuingJournalV5,
        SustainedPromptVersion::ActionScopeJournalV6,
        SustainedPromptVersion::WritingBoundaryJournalV7,
        SustainedPromptVersion::MeasurementMeaningJournalV8,
    ] {
        let mut baseline = None;
        for evidence in variants() {
            let mut s = session(version);
            let initial = s.checkpoint();
            advance(&mut s, 3);
            let first_prompt = s.pending_language().unwrap().prompt.clone();
            s.start_language(1).unwrap();
            s.confirm_language(1, &response(evidence.clone())).unwrap();
            let journal = s.pending_journal().unwrap().clone();
            assert_eq!(journal.response.provider_prompt_evaluation, evidence);
            assert!(s.advance().is_err());
            s.confirm_saved(
                &SustainedSaveReceipt {
                    entry_id: journal.entry.id.clone(),
                    sha256: journal.entry.sha256.clone(),
                    relative_path: format!("journals/{}.json", journal.entry.id),
                },
                &journal.entry,
            )
            .unwrap();
            assert!(s.advance().is_err());
            let serialized = serde_json::to_vec(&s.checkpoint()).unwrap();
            let mut restored =
                SustainedSession::restore(serde_json::from_slice(&serialized).unwrap()).unwrap();
            restored.authorize_application(1).unwrap();
            s.authorize_application(1).unwrap();
            let frame = s.advance().unwrap();
            assert_eq!(frame.application.as_ref().unwrap().applied_step, 4);
            assert_eq!(
                serde_json::to_vec(&frame).unwrap(),
                serde_json::to_vec(&restored.advance().unwrap()).unwrap()
            );
            advance(&mut s, 2);
            assert_eq!(
                s.pending_memory().unwrap().entry.as_ref().unwrap().text,
                journal.entry.text
            );
            s.confirm_memory(&journal.entry).unwrap();
            let comparable = (
                first_prompt,
                serde_json::to_vec(&frame).unwrap(),
                serde_json::to_vec(&s.checkpoint()).unwrap(),
            );
            if let Some(expected) = &baseline {
                assert_eq!(&comparable, expected);
            } else {
                baseline = Some(comparable);
            }
            let record = segment(&s, initial);
            record.verify().unwrap();
            assert_eq!(
                record.journal_evidence().unwrap()[0]
                    .response
                    .provider_prompt_evaluation,
                evidence
            );
        }
    }
}

#[test]
fn incomplete_response_keeps_input_evidence_without_journal_or_feedback() {
    for evidence in variants() {
        let mut s = session(CURRENT_PROMPT_VERSION);
        let initial = s.checkpoint();
        advance(&mut s, 3);
        s.start_language(1).unwrap();
        let mut r = response(evidence.clone());
        r.complete = false;
        r.stop_reason = Some("length".into());
        s.confirm_language(1, &r).unwrap();
        assert!(s.blocked().is_some());
        assert!(s.pending_journal().is_none());
        assert!(s.prepared_application().is_none());
        assert!(s.advance().is_err());
        let record = segment(&s, initial);
        let raw = serde_json::to_vec(&record).unwrap();
        let restored: SustainedSegment = serde_json::from_slice(&raw).unwrap();
        restored.verify().unwrap();
        assert!(restored.events.iter().any(|e| matches!(&e.kind,
            SustainedEventKind::LanguageReceived { response, .. }
            if response.provider_prompt_evaluation == evidence)));
    }
}

#[test]
fn inconsistent_event_and_candidate_evidence_fails_replay_even_with_valid_checkpoint_hash() {
    let mut s = session(CURRENT_PROMPT_VERSION);
    let initial = s.checkpoint();
    advance(&mut s, 3);
    s.start_language(1).unwrap();
    s.confirm_language(
        1,
        &response(Some(ProviderPromptEvaluation::Reported { count: 1700 })),
    )
    .unwrap();
    let record = segment(&s, initial);
    record.verify().unwrap();
    for value in [
        None,
        Some(ProviderPromptEvaluation::Reported { count: 1701 }),
        Some(ProviderPromptEvaluation::Unusable {
            reason: ProviderPromptEvaluationIssue::WrongType,
        }),
    ] {
        let mut changed = record.clone();
        if let SustainedPhase::Journal(j) = &mut changed.final_checkpoint.state.phase {
            j.response.provider_prompt_evaluation = value;
        } else {
            panic!("expected journal");
        }
        rehash(&mut changed.final_checkpoint);
        changed.final_checkpoint.validate().unwrap();
        assert!(changed.verify().is_err());
    }
}

#[test]
fn replay_does_not_authenticate_a_self_consistently_changed_provider_assertion() {
    let mut s = session(CURRENT_PROMPT_VERSION);
    let initial = s.checkpoint();
    advance(&mut s, 3);
    s.start_language(1).unwrap();
    s.confirm_language(
        1,
        &response(Some(ProviderPromptEvaluation::Reported { count: 1700 })),
    )
    .unwrap();
    let mut record = segment(&s, initial);
    for event in &mut record.events {
        if let SustainedEventKind::LanguageReceived { response, .. } = &mut event.kind {
            response.provider_prompt_evaluation =
                Some(ProviderPromptEvaluation::Reported { count: 1701 });
        }
    }
    if let SustainedPhase::Journal(j) = &mut record.final_checkpoint.state.phase {
        j.response.provider_prompt_evaluation =
            Some(ProviderPromptEvaluation::Reported { count: 1701 });
    }
    rehash(&mut record.final_checkpoint);
    record.verify().unwrap();
    // This external assertion is accepted as replay input, not independently
    // recomputed tokenization or evidence that a provider was ever contacted.
}
