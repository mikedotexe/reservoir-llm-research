use reservoir_core::{codec, session::LanguageResponse, sustained::*};
use sha2::{Digest, Sha256};

fn spec() -> SustainedSpecification {
    SustainedSpecification {
        action_mode: Some(SustainedActionMode::AuthoredV3),
        prompt_version: SustainedPromptVersion::ActionJournalV3,
        turn_every: 3,
        maximum_steps: 1000,
        maximum_turns: 200,
        sensory_noise_amplitude: 0.5,
        feedback_scale: 0.4,
        ..Default::default()
    }
}
fn reply(text: &str) -> LanguageResponse {
    LanguageResponse {
        text: text.into(),
        provider_model: None,
        stop_reason: Some("stop".into()),
        token_count: Some(30),
        complete: true,
        provider_prompt_evaluation: None,
    }
}
fn probe(value: f64) -> String {
    let mut v = vec![0.0; 48];
    v[0] = value;
    format!("PROBE {}", serde_json::to_string(&v).unwrap())
}
fn rehash(c: &mut SustainedCheckpoint) {
    c.sha256 = format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&c.state).unwrap())
    );
}
struct Run {
    session: SustainedSession,
    base: SustainedCheckpoint,
    entries: Vec<SustainedJournal>,
}
impl Run {
    fn new(spec: SustainedSpecification) -> Self {
        let session = SustainedSession::new(spec).unwrap();
        let base = session.checkpoint();
        Self {
            session,
            base,
            entries: Vec::new(),
        }
    }
    fn reach(&mut self) {
        while matches!(self.session.phase(), SustainedPhase::Ready) {
            self.session.advance().unwrap();
        }
        if let Some(m) = self.session.pending_memory().cloned() {
            self.session
                .confirm_memory(
                    m.entry
                        .as_ref()
                        .or_else(|| {
                            self.entries
                                .iter()
                                .find(|e| Some(e.id.as_str()) == m.entry_id())
                        })
                        .expect("saved memory"),
                )
                .unwrap();
        }
    }
    fn save(&mut self, text: &str) -> SustainedPendingJournal {
        self.reach();
        let id = self.session.pending_language().unwrap().attempt_id;
        self.session.start_language(id).unwrap();
        self.session.confirm_language(id, &reply(text)).unwrap();
        let p = self.session.pending_journal().unwrap().clone();
        self.session
            .confirm_saved(
                &SustainedSaveReceipt {
                    entry_id: p.entry.id.clone(),
                    sha256: p.entry.sha256.clone(),
                    relative_path: format!("journals/{}.json", p.entry.id),
                },
                &p.entry,
            )
            .unwrap();
        self.entries.push(p.entry.clone());
        p
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
        if let Some(e) = segment.events.last() {
            self.session.acknowledge_events(e.id).unwrap();
        }
        self.base = segment.final_checkpoint.clone();
        segment
    }
    fn continuity(&self) -> &SustainedContinuityState {
        self.session
            .action_state()
            .unwrap()
            .continuity
            .as_ref()
            .unwrap()
    }
}
fn distance(a: &[f64], b: &[f64]) -> f64 {
    a.iter()
        .zip(b)
        .map(|(a, b)| (a - b) * (a - b))
        .sum::<f64>()
        .sqrt()
}

#[test]
fn v3_is_explicit_and_legacy_serialization_omits_new_fields() {
    let mut c = spec();
    c.action_mode = Some(SustainedActionMode::AuthoredV2);
    assert!(c.validate().is_err());
    c.prompt_version = SustainedPromptVersion::ActionJournalV2;
    let mut r = Run::new(c);
    r.turn("Old body.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE");
    r.verify();
    let serialized = serde_json::to_string(&r.session.checkpoint()).unwrap();
    for absent in ["continuity", "inquiry", "probe"] {
        assert!(!serialized.contains(absent));
    }
    assert!(
        parse_authored_action_v2(&format!("Body\nNEXT: {}", probe(1.0)))
            .request
            .is_none()
    );
}

#[test]
fn inquiry_and_input_footers_are_removed_independently_of_rejected_action() {
    let d=parse_authored_action_v3("A question.\n\nINQUIRY: OPEN both \"What changed?\"\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: INVALID");
    assert_eq!(d.body, "A question.");
    assert!(d.request.is_none());
    assert!(d.withholds_reservoir_input());
    assert!(matches!(
        d.inquiry.unwrap().request,
        Some(SustainedInquiryRequest::Open {
            source: SustainedInquirySource::Both,
            ..
        })
    ));
    let d = parse_authored_action_v3(
        "Body\nINQUIRY: OPEN journal \"earlier\"\nINQUIRY: CLOSE\nNEXT: TUNE leak 0.75",
    );
    assert_eq!(d.body, "Body");
    assert!(d.request.is_some());
    assert!(d.inquiry.unwrap().rejection.is_some());
}

#[test]
fn quoted_fenced_and_nonfooter_inquiries_never_execute() {
    for text in [
        "Body\n> INQUIRY: CLOSE\n\nNEXT: NONE",
        "Body\n```\nINQUIRY: CLOSE\n```\nNEXT: NONE",
        "Body\n    INQUIRY: CLOSE\nNEXT: NONE",
        "Body\nINQUIRY: CLOSE\nFurther prose\nNEXT: NONE",
        "- quote\nINQUIRY: CLOSE\n\nNEXT: NONE",
    ] {
        assert!(parse_authored_action_v3(text).inquiry.is_none(), "{text}");
    }
    let q="Quoted.\n```\nINQUIRY: CLOSE\nNEXT: RELEASE\n```\n\nINQUIRY: OPEN dynamics \"What changes after a probe?\"\nNEXT: NONE";
    let d = parse_authored_action_v3(q);
    assert!(d.inquiry.unwrap().request.is_some());
    assert!(d.body.contains("INQUIRY: CLOSE"));
}

#[test]
fn malformed_inquiry_is_bounded_and_does_not_cancel_other_choices() {
    for directive in [
        "INQUIRY: OPEN outside \"x\"".to_string(),
        "INQUIRY: OPEN journal unquoted".into(),
        "INQUIRY: OPEN dynamics \"\"".into(),
        "INQUIRY: OPEN both \"line\\nline\"".into(),
        format!(
            "INQUIRY: OPEN both {}",
            serde_json::to_string(&"x".repeat(513)).unwrap()
        ),
        "INQUIRY: UNKNOWN".into(),
        format!("INQUIRY: {}", "x".repeat(5000)),
    ] {
        let d = parse_authored_action_v3(&format!(
            "Body\n{directive}\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: TUNE leak 0.75"
        ));
        assert_eq!(d.body, "Body");
        assert!(d.inquiry.as_ref().unwrap().rejection.is_some());
        assert!(d.request.is_some());
        assert!(!d.withholds_reservoir_input());
    }
}

#[test]
fn probe_validation_is_exact_and_preserves_independent_input_and_inquiry() {
    let mut long = vec![0.012345678901234567; 48];
    long[0] = 0.75;
    let raw=format!("Body\nINQUIRY: OPEN dynamics \"Trace response.\"\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: PROBE {}",serde_json::to_string(&long).unwrap());
    assert!(raw.lines().last().unwrap().len() > 512);
    let d = parse_authored_action_v3(&raw);
    assert!(matches!(
        d.request,
        Some(SustainedActionRequest::Probe { .. })
    ));
    assert!(d.withholds_reservoir_input());
    assert_eq!(d.body, "Body");
    assert!(d.inquiry.unwrap().request.is_some());
    for value in [
        serde_json::json!([]),
        serde_json::json!(vec![0.0; 47]),
        serde_json::json!(vec![0.0; 49]),
        serde_json::json!(vec![1.0; 48]),
        serde_json::json!(vec![1.01; 48]),
    ] {
        let d = parse_authored_action_v3(&format!("Body\nNEXT: PROBE {value}"));
        assert!(d.request.is_none());
        assert_eq!(d.body, "Body");
    }
    assert!(
        parse_authored_action_v3(&format!("Body\nNEXT: {}", probe(0.0)))
            .request
            .is_some()
    );
    for raw in ["PROBE [NaN]", "PROBE [Infinity]", "PROBE [1e400]"] {
        assert!(parse_authored_action_v3(&format!("Body\nNEXT: {raw}"))
            .request
            .is_none());
    }
}

#[test]
fn probe_is_one_step_input_and_reaches_field_without_changing_rng_or_held_text() {
    let mut actual = Run::new(spec());
    let mut control = Run::new(spec());
    let a = actual.turn(&format!(
        "Body\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: {}",
        probe(1.0)
    ));
    let b = control.turn("Body\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE");
    assert_eq!(a.noise, b.noise);
    assert_eq!(a.sensory_noise, b.sensory_noise);
    for (i, (x, y)) in a.input.iter().zip(&b.input).enumerate() {
        assert_eq!(x - y, if i == 18 { 1.0 } else { 0.0 });
    }
    assert!(distance(&a.state, &b.state) > 0.0);
    assert_ne!(a.sensory.field_vector, b.sensory.field_vector);
    let receipt = a.action_receipt.as_ref().unwrap();
    assert_eq!(receipt.state_delta_l2, distance(&a.state, &b.state));
    assert_eq!(receipt.probe.as_ref().unwrap().applied_vector[0], 1.0);
    assert!(actual
        .session
        .checkpoint()
        .state
        .held_vector
        .iter()
        .all(|x| *x == 0.0));
    let a2 = actual.session.advance().unwrap();
    let b2 = control.session.advance().unwrap();
    assert_eq!(a2.input, b2.input);
    assert!(a2.action_receipt.is_none());
    actual.verify();
    control.verify();
}

#[test]
fn zero_probe_and_none_have_same_numerical_path_and_zero_action_is_not_stasis() {
    let mut actual = Run::new(spec());
    let mut control = Run::new(spec());
    let a = actual.turn(&format!("Body\nNEXT: {}", probe(0.0)));
    let b = control.turn("Body\nNEXT: NONE");
    assert_eq!(a.state, b.state);
    assert_eq!(a.input, b.input);
    assert_eq!(a.sensory.field_vector, b.sensory.field_vector);
    assert_eq!(a.action_receipt.as_ref().unwrap().state_delta_l2, 0.0);
    actual.reach();
    let p = &actual.session.pending_language().unwrap().prompt;
    assert!(p.contains("NONE has zero additional effect even while the reservoir changes"));
    actual.verify();
}

#[test]
fn text_omission_comparison_retains_the_probe() {
    let mut c = spec();
    c.memory_policy = SustainedMemoryPolicy::StateAligned;
    let mut actual = Run::new(c.clone());
    let mut no_text = Run::new(c);
    let a = actual.turn(&format!("Body\nNEXT: {}", probe(0.75)));
    let b = no_text.turn(&format!("NEXT: {}", probe(0.75)));
    assert_eq!(
        a.entry_effect.as_ref().unwrap().shift,
        distance(&a.state, &b.state)
    );
    actual.verify();
    no_text.verify();
}

#[test]
fn inquiry_and_probe_wait_for_durable_application_and_survive_restart_once() {
    let mut r = Run::new(spec());
    r.save(&format!(
        "Body\nINQUIRY: OPEN both \"What happened?\"\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: {}",
        probe(0.5)
    ));
    assert!(r.continuity().active_inquiry.is_none());
    assert!(r.session.advance().is_err());
    r.verify();
    let checkpoint = r.session.checkpoint();
    r.session = SustainedSession::restore(checkpoint).unwrap();
    assert!(r.session.advance().is_err());
    let frame = r.apply();
    assert!(frame.action_receipt.as_ref().unwrap().probe.is_some());
    assert!(r.continuity().active_inquiry.is_some());
    let q = r.continuity().active_inquiry.as_ref().unwrap();
    assert_eq!(q.baseline.step, 3);
    assert_eq!(q.opened_applied_step, 4);
    assert!(q.history.is_empty());
    r.session.advance().unwrap();
    assert_eq!(r.session.action_state().unwrap().applied_count, 1);
    r.verify();
    r.reach();
    let prompt = &r.session.pending_language().unwrap().prompt;
    assert!(prompt.contains("Opening recurrent coordinates [0..31]"));
    assert!(prompt.contains("paired recurrent response [0..31]"));
    assert!(prompt.contains("No prior applied entry existed"));
}

#[test]
fn inquiry_survives_none_refreshes_real_history_and_can_close_or_replace() {
    let mut r = Run::new(spec());
    r.turn("First saved thought.\nNEXT: TUNE leak 0.75");
    r.verify();
    r.turn("Opening.\nINQUIRY: OPEN both \"What changed after the tuning?\"\nNEXT: NONE");
    r.verify();
    let original = r.continuity().active_inquiry.clone().unwrap();
    assert_eq!(original.history.len(), 1);
    assert_eq!(original.history[0].excerpt, "First saved thought.");
    for n in 0..10 {
        r.turn(&format!("Later {n} {}\nNEXT: NONE", "é".repeat(400)));
        r.verify();
    }
    assert_eq!(
        r.continuity().active_inquiry.as_ref().unwrap().id,
        original.id
    );
    assert_eq!(r.continuity().journal_window.len(), 8);
    assert_eq!(r.continuity().meaningful_receipts.len(), 1);
    r.turn("Revisit.\nINQUIRY: CONTINUE\nNEXT: NONE");
    r.verify();
    let q = r.continuity().active_inquiry.as_ref().unwrap();
    assert_eq!(q.baseline, original.baseline);
    assert_eq!(q.history.len(), 4);
    assert_eq!(q.continuation_count, 1);
    assert!(q
        .history
        .iter()
        .all(|h| h.excerpt_truncated && h.excerpt.len() <= 512));
    r.turn("A new question.\nINQUIRY: OPEN journal \"What was I discussing?\"\nNEXT: NONE");
    r.verify();
    assert_eq!(
        r.continuity()
            .latest_inquiry_receipt
            .as_ref()
            .unwrap()
            .status,
        SustainedInquiryStatus::Replaced
    );
    assert_ne!(
        r.continuity().active_inquiry.as_ref().unwrap().id,
        original.id
    );
    r.turn("Done for now.\nINQUIRY: CLOSE\nNEXT: NONE");
    r.verify();
    assert!(r.continuity().active_inquiry.is_none());
    assert_eq!(
        r.continuity()
            .latest_inquiry_receipt
            .as_ref()
            .unwrap()
            .status,
        SustainedInquiryStatus::Closed
    );
}

#[test]
fn malformed_inquiry_keeps_open_question_and_can_still_tune_or_withhold() {
    let mut r = Run::new(spec());
    r.turn("Question.\nINQUIRY: OPEN both \"What changes?\"\nNEXT: NONE");
    r.verify();
    let q = r.continuity().active_inquiry.clone();
    let frame = r.turn(
        "Continue prose.\nINQUIRY: WRONG\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: TUNE leak 0.8",
    );
    r.verify();
    assert_eq!(r.continuity().active_inquiry, q);
    assert_eq!(r.session.action_state().unwrap().controls.leak, 0.8);
    assert!(r
        .session
        .checkpoint()
        .state
        .held_vector
        .iter()
        .all(|x| *x == 0.0));
    assert_eq!(
        frame.action_receipt.unwrap().inquiry.unwrap().status,
        SustainedInquiryStatus::Rejected
    );
    let mut empty = Run::new(spec());
    empty.turn("No question.\nINQUIRY: CONTINUE\nNEXT: NONE");
    empty.verify();
    assert_eq!(
        empty
            .continuity()
            .latest_inquiry_receipt
            .as_ref()
            .unwrap()
            .status,
        SustainedInquiryStatus::Rejected
    );
}

#[test]
fn inquiry_evidence_tampering_is_detected_by_full_replay_even_with_rehashed_checkpoint() {
    let mut r = Run::new(spec());
    r.turn(&format!("{}\nNEXT: NONE", "a".repeat(1000)));
    r.turn("Question\nINQUIRY: OPEN journal \"Compare earlier writing.\"\nNEXT: NONE");
    let mut segment = r.verify();
    segment
        .final_checkpoint
        .state
        .action_state
        .as_mut()
        .unwrap()
        .continuity
        .as_mut()
        .unwrap()
        .active_inquiry
        .as_mut()
        .unwrap()
        .history[0]
        .excerpt
        .replace_range(..1, "b");
    rehash(&mut segment.final_checkpoint);
    assert!(
        segment.final_checkpoint.validate().is_ok(),
        "A self-hashed truncated excerpt alone cannot authenticate original text"
    );
    assert!(segment.verify().is_err());
    let mut checkpoint = r.session.checkpoint();
    checkpoint
        .state
        .action_state
        .as_mut()
        .unwrap()
        .continuity
        .as_mut()
        .unwrap()
        .active_inquiry
        .as_mut()
        .unwrap()
        .baseline
        .state[0] += 0.1;
    rehash(&mut checkpoint);
    assert!(checkpoint.validate().is_err());
}

#[test]
fn probe_vector_or_effect_tampering_is_rejected() {
    let mut r = Run::new(spec());
    r.turn(&format!("Body\nNEXT: {}", probe(0.5)));
    r.verify();
    let mut c = r.session.checkpoint();
    c.state
        .action_state
        .as_mut()
        .unwrap()
        .continuity
        .as_mut()
        .unwrap()
        .meaningful_receipts[0]
        .probe
        .as_mut()
        .unwrap()
        .applied_vector[0] = 0.75;
    rehash(&mut c);
    assert!(c.validate().is_err());
    let mut c = r.session.checkpoint();
    c.state
        .action_state
        .as_mut()
        .unwrap()
        .continuity
        .as_mut()
        .unwrap()
        .meaningful_receipts[0]
        .probe
        .as_mut()
        .unwrap()
        .state_delta_vector[0] += 0.1;
    rehash(&mut c);
    assert!(c.validate().is_err());
}

#[test]
fn ordinary_prompt_is_open_and_withholding_instructions_are_symmetric() {
    let mut r = Run::new(spec());
    r.reach();
    let p = &r.session.pending_language().unwrap().prompt;
    assert!(p.contains("Choose the subject, form and length"));
    assert!(p.contains("WITHHOLD_RESERVOIR_INPUT=true"));
    assert!(p.contains("WITHHOLD_RESERVOIR_INPUT=false"));
    assert!(!p.contains("Example footer"));
    assert!(!p.contains("Describe a pause"));
    assert!(p.contains("RELEASE restores initial controls, not state or history"));
}

#[test]
fn latest_inquiry_identity_and_retained_receipt_tampering_are_rejected() {
    let mut r = Run::new(spec());
    r.turn("Question.\nINQUIRY: OPEN both \"What changes?\"\nNEXT: TUNE leak 0.8");
    r.verify();
    let mut c = r.session.checkpoint();
    c.state
        .action_state
        .as_mut()
        .unwrap()
        .continuity
        .as_mut()
        .unwrap()
        .latest_inquiry_receipt
        .as_mut()
        .unwrap()
        .inquiry_id = None;
    rehash(&mut c);
    assert!(c.validate().is_err());
    let mut c = r.session.checkpoint();
    c.state
        .action_state
        .as_mut()
        .unwrap()
        .continuity
        .as_mut()
        .unwrap()
        .latest_inquiry_receipt
        .as_mut()
        .unwrap()
        .decision
        .raw_directive = None;
    rehash(&mut c);
    assert!(c.validate().is_err());
    let mut c = r.session.checkpoint();
    c.state
        .action_state
        .as_mut()
        .unwrap()
        .continuity
        .as_mut()
        .unwrap()
        .meaningful_receipts[0]
        .clipped_coordinates = 1;
    rehash(&mut c);
    assert!(c.validate().is_err());
}
#[test]
fn tiny_probe_coordinates_are_rendered_exactly() {
    let mut r = Run::new(spec());
    r.turn(&format!(
        "Body\nINQUIRY: OPEN dynamics \"Tiny input?\"\nNEXT: {}",
        probe(1e-12)
    ));
    r.reach();
    assert!(r
        .session
        .pending_language()
        .unwrap()
        .prompt
        .contains("[1e-12,"));
    r.verify();
}

#[test]
fn v3_none_keeps_v2_numerical_path_without_extra_rng_draws() {
    let mut v2 = spec();
    v2.action_mode = Some(SustainedActionMode::AuthoredV2);
    v2.prompt_version = SustainedPromptVersion::ActionJournalV2;
    let mut old = Run::new(v2);
    let mut new = Run::new(spec());
    for text in [
        "One.\nNEXT: NONE",
        "Two.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE",
        "Three.\nNEXT: NONE",
    ] {
        let a = old.turn(text);
        let b = new.turn(text);
        assert_eq!(a.state, b.state);
        assert_eq!(a.input, b.input);
        assert_eq!(a.sensory.field_vector, b.sensory.field_vector);
        assert_eq!(a.noise, b.noise);
        assert_eq!(a.sensory_noise, b.sensory_noise);
        old.verify();
        new.verify();
    }
}

#[test]
fn inquiry_and_probe_survive_embedding_failure_restore_and_retry_without_early_effect() {
    let mut c = spec();
    c.codec = SustainedCodec::Embedding {
        model: "fixture".into(),
        projection_seed: 99,
    };
    let mut r = Run::new(c);
    r.reach();
    let pending = r.session.pending_language().unwrap().clone();
    let id = pending.attempt_id;
    r.session.start_language(id).unwrap();
    let response=reply(&format!("Investigate this input.\nINQUIRY: OPEN both \"What changes?\"\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: {}",probe(0.5)));
    r.session
        .retain_language_for_feedback(id, &response)
        .unwrap();
    assert_eq!(
        r.session
            .feedback_text_for_response(&response.text)
            .unwrap(),
        "Investigate this input."
    );
    let first = r.session.start_feedback(id).unwrap();
    r.session
        .fail_feedback(id, first, "fixture unavailable")
        .unwrap();
    r.verify();
    assert!(r.continuity().active_inquiry.is_none());
    assert!(r.continuity().meaningful_receipts.is_empty());
    r.session = SustainedSession::restore(
        serde_json::from_slice(&serde_json::to_vec(&r.session.checkpoint()).unwrap()).unwrap(),
    )
    .unwrap();
    assert_eq!(
        r.session.pending_feedback().unwrap().pending.prompt,
        pending.prompt
    );
    assert_eq!(
        r.session.pending_feedback().unwrap().response.text,
        response.text
    );
    r.session.retry_feedback().unwrap();
    let retry = r.session.start_feedback(id).unwrap();
    let source: Vec<_> = (0..768).map(|i| (i as f64 * 0.37).sin()).collect();
    let external = ExternalFeedback {
        vector: codec::project_embedding(&source, 99).unwrap(),
        provenance: FeedbackProvenance {
            kind: "embedding".into(),
            model: "fixture".into(),
            digest: None,
            dimensions: 768,
            embedding_sha256: format!("{:x}", Sha256::digest(b"fixture")),
            projection_seed: 99,
        },
    };
    assert!(r.session.confirm_feedback(id, first, &external).is_err());
    r.session.confirm_feedback(id, retry, &external).unwrap();
    let p = r.session.pending_journal().unwrap().clone();
    r.session
        .confirm_saved(
            &SustainedSaveReceipt {
                entry_id: p.entry.id.clone(),
                sha256: p.entry.sha256.clone(),
                relative_path: format!("journals/{}.json", p.entry.id),
            },
            &p.entry,
        )
        .unwrap();
    assert!(r.continuity().active_inquiry.is_none());
    assert!(r.session.advance().is_err());
    r.verify();
    r.apply();
    assert!(r.continuity().active_inquiry.is_some());
    assert_eq!(r.continuity().meaningful_receipts.len(), 1);
    assert_eq!(r.session.checkpoint().state.attempt_cursor, id);
    r.verify();
    r.reach();
    assert!(r
        .session
        .pending_language()
        .unwrap()
        .prompt
        .contains("Investigate this input."));
    r.verify();
}

#[test]
fn plain_and_telemetry_check_ins_preserve_inquiry_and_execute_no_directives() {
    for telemetry in [false, true] {
        let mut c = spec();
        let prompt = " Tell me, friend.\n".to_string();
        c.check_in_schedule = Some(SustainedCheckInSchedule {
            interval_seconds: 10,
            end_after_seconds: 30,
            prompt: prompt.clone(),
            include_telemetry: telemetry,
        });
        let mut r = Run::new(c);
        r.turn("Opening.\nINQUIRY: OPEN both \"Carry this question.\"\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: TUNE leak 0.7");
        r.verify();
        let before = r.continuity().active_inquiry.clone();
        let controls = r.session.action_state().unwrap().controls.clone();
        let latest = r.continuity().latest_inquiry_receipt.clone();
        assert!(r.session.admit_due_check_in(10000).unwrap());
        if let Some(m) = r.session.pending_memory().cloned() {
            r.session.confirm_memory(m.entry.as_ref().unwrap()).unwrap();
        }
        let p = r.session.pending_language().unwrap();
        if telemetry {
            assert!(p
                .prompt
                .contains("Ordinary journal turns retain their control"));
            assert!(p.prompt.contains("Carry this question."));
        } else {
            assert_eq!(p.prompt, prompt);
        }
        let raw = format!(
            "Conversation.\nINQUIRY: CLOSE\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: {}",
            probe(1.0)
        );
        let j = r.save(&raw);
        assert!(j.action.is_none());
        assert!(j.entry.body.is_none());
        assert_eq!(j.entry.text, raw);
        let frame = r.apply();
        assert!(frame.action_receipt.is_none());
        assert_eq!(r.continuity().active_inquiry, before);
        assert_eq!(r.continuity().latest_inquiry_receipt, latest);
        assert_eq!(r.session.action_state().unwrap().controls, controls);
        assert!(r.continuity().journal_window.last().unwrap().check_in);
        assert_eq!(
            r.continuity().input_transitions.last().unwrap().disposition,
            SustainedReservoirInputDisposition::Send
        );
        assert!(r
            .session
            .checkpoint()
            .state
            .held_vector
            .iter()
            .any(|v| *v != 0.0));
        r.verify();
        r.reach();
        assert!(r
            .session
            .pending_language()
            .unwrap()
            .prompt
            .contains("Carry this question."));
        r.verify();
    }
}

#[test]
fn prose_about_inquiry_is_not_a_directive() {
    let d = parse_authored_action_v3("INQUIRY seems a useful word.\nNEXT: NONE");
    assert!(d.inquiry.is_none());
    assert_eq!(d.body, "INQUIRY seems a useful word.");
}

#[test]
fn prior_window_identity_and_bounded_context_survive_long_histories() {
    let mut c = spec();
    c.memory_policy = SustainedMemoryPolicy::StateAligned;
    let mut r = Run::new(c);
    for n in 0..9 {
        r.turn(&format!(
            "{}\nWITHHOLD_RESERVOIR_INPUT={}\nNEXT: TUNE feedbackScale {}",
            "a".repeat(3000),
            n % 2 == 0,
            if n % 2 == 0 { 0.5 } else { 1.0 }
        ));
        r.verify();
    }
    r.turn(&format!(
        "{}\nINQUIRY: OPEN both {}\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: {}",
        "b".repeat(3000),
        serde_json::to_string(&"q".repeat(512)).unwrap(),
        probe(0.123456789012345)
    ));
    r.verify();
    let mut bad = r.session.checkpoint();
    bad.state
        .action_state
        .as_mut()
        .unwrap()
        .continuity
        .as_mut()
        .unwrap()
        .journal_window
        .remove(0);
    rehash(&mut bad);
    assert!(bad.validate().is_err());
    r.reach();
    let prompt = &r.session.pending_language().unwrap().prompt;
    assert!(
        prompt.len() < 22000,
        "bounded prompt is {} bytes",
        prompt.len()
    );
    assert!(!prompt.contains(&"b".repeat(2049)));
    r.verify();
}

#[test]
fn final_probe_channel_and_serialized_receipts_replay_exactly() {
    let mut vector = vec![0.0; 48];
    vector[47] = 0.125;
    let mut actual = Run::new(spec());
    let mut control = Run::new(spec());
    let a = actual.turn(&format!(
        "Body\nNEXT: PROBE {}",
        serde_json::to_string(&vector).unwrap()
    ));
    let b = control.turn("Body\nNEXT: NONE");
    assert_eq!(a.input[65] - b.input[65], 0.125);
    assert_eq!(&a.input[..65], &b.input[..65]);
    assert!(distance(&a.state, &b.state) > 0.0);
    assert_ne!(a.sensory.field_vector, b.sensory.field_vector);
    let segment = actual.verify();
    let restored: SustainedSegment =
        serde_json::from_slice(&serde_json::to_vec(&segment).unwrap()).unwrap();
    restored.verify().unwrap();
    actual.session = SustainedSession::restore(restored.final_checkpoint).unwrap();
    assert_eq!(
        actual
            .session
            .action_state()
            .unwrap()
            .latest_receipt
            .as_ref()
            .unwrap()
            .probe
            .as_ref()
            .unwrap()
            .applied_vector,
        vector
    );
}

#[test]
fn exported_memory_excerpt_helper_matches_exact_utf8_bound() {
    let body = format!("{}éZ", "a".repeat(V3_MEMORY_PREFIX_BYTES - 1));
    let excerpt = sustained_v3_memory_excerpt(&body);
    assert_eq!(excerpt.len(), 2047);
    assert_eq!(excerpt, "a".repeat(2047));
    assert_eq!(sustained_v3_memory_excerpt("short"), "short");
}
