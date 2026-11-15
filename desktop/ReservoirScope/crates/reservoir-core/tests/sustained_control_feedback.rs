//! New admission and explanations are explicit session policies, not parser repairs.
use reservoir_core::{codec, session::LanguageResponse, sustained::*};
use sha2::{Digest, Sha256};

fn spec(semantic: bool) -> SustainedSpecification {
    SustainedSpecification {
        action_mode: Some(SustainedActionMode::AuthoredV3),
        prompt_version: SustainedPromptVersion::ActionJournalV3,
        control_feedback: Some(SustainedControlFeedback::DiagnosticV1),
        text_admission: semantic.then_some(SustainedTextAdmission::Utf8V1),
        codec: if semantic {
            SustainedCodec::Embedding {
                model: "fixture".into(),
                projection_seed: 99,
            }
        } else {
            SustainedCodec::Surface
        },
        turn_every: 3,
        maximum_steps: 100,
        maximum_turns: 20,
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
fn external() -> ExternalFeedback {
    let source: Vec<_> = (0..768).map(|i| (i as f64 * 0.37).sin()).collect();
    ExternalFeedback {
        vector: codec::project_embedding(&source, 99).unwrap(),
        provenance: FeedbackProvenance {
            kind: "embedding".into(),
            model: "fixture".into(),
            digest: None,
            dimensions: 768,
            embedding_sha256: format!("{:x}", Sha256::digest(b"fixture embedding")),
            projection_seed: 99,
        },
    }
}
struct Run {
    s: SustainedSession,
    base: SustainedCheckpoint,
}
impl Run {
    fn new(spec: SustainedSpecification) -> Self {
        let s = SustainedSession::new(spec).unwrap();
        Self {
            base: s.checkpoint(),
            s,
        }
    }
    fn reach(&mut self) -> u64 {
        while matches!(self.s.phase(), SustainedPhase::Ready) {
            self.s.advance().unwrap();
        }
        if let Some(m) = self.s.pending_memory().cloned() {
            self.s.confirm_memory(m.entry.as_ref().unwrap()).unwrap();
        }
        self.s.pending_language().unwrap().attempt_id
    }
    fn receive(&mut self, text: &str) {
        let id = self.reach();
        self.s.start_language(id).unwrap();
        let r = reply(text);
        if self.s.response_needs_feedback(&r).unwrap() {
            self.s.retain_language_for_feedback(id, &r).unwrap();
            let request = self.s.start_feedback(id).unwrap();
            self.s.confirm_feedback(id, request, &external()).unwrap();
        } else {
            self.s.confirm_language(id, &r).unwrap();
        }
    }
    fn apply(&mut self) -> SustainedFrame {
        let p = self.s.pending_journal().unwrap().clone();
        self.s
            .confirm_saved(
                &SustainedSaveReceipt {
                    entry_id: p.entry.id.clone(),
                    sha256: p.entry.sha256.clone(),
                    relative_path: format!("journals/{}.json", p.entry.id),
                },
                &p.entry,
            )
            .unwrap();
        self.s.authorize_application(p.entry.attempt_id).unwrap();
        self.s.advance().unwrap()
    }
    fn verify(&mut self) {
        let segment = SustainedSegment {
            format: FORMAT.into(),
            initial_checkpoint: self.base.clone(),
            events: self.s.events().iter().cloned().collect(),
            final_checkpoint: self.s.checkpoint(),
        };
        segment.verify().unwrap();
        if let Some(e) = segment.events.last() {
            self.s.acknowledge_events(e.id).unwrap();
        }
        self.base = segment.final_checkpoint;
    }
}

#[test]
fn formatted_candidates_explain_rejection_without_becoming_commands() {
    for tail in [
        "**NEXT: TUNE leak 0.7**",
        "`NEXT: TUNE leak 0.7`",
        "```\nNEXT: TUNE leak 0.7\n```",
        "> NEXT: TUNE leak 0.7",
        "- NEXT: TUNE leak 0.7",
        "NEXT: TUNE leak 0.7\nMore prose.",
    ] {
        let mut r = Run::new(spec(false));
        let text = format!("An observation.\n\n{tail}");
        r.receive(&text);
        let decision = r.s.pending_journal().unwrap().action.as_ref().unwrap();
        assert!(decision.request.is_none(), "{tail}");
        assert_eq!(decision.body, text);
        let d = decision.diagnostics.as_ref().unwrap();
        assert_eq!(d.next.candidate_count, 1);
        assert!(d.next.explanation.contains("plain, unformatted"));
        let d = d.clone();
        let frame = r.apply();
        let receipt = frame.action_receipt.unwrap();
        assert_eq!(receipt.status, SustainedActionStatus::Rejected);
        assert_eq!(receipt.controls_before, receipt.controls_after);
        assert_eq!(receipt.diagnostics, Some(d));
        r.verify();
        r.reach();
        let prompt = &r.s.pending_language().unwrap().prompt;
        assert!(prompt.contains("quoted, non-executable data"));
        assert!(prompt.contains("NEXT outcome: Rejected"));
        r.verify();
    }
}

#[test]
fn numerical_probe_errors_are_specific_without_repairing_vectors() {
    for (tail, expected) in [
        (
            "PROBE [0,0]".to_owned(),
            "received 2 coordinates; exactly 48",
        ),
        ("PROBE [0,...]".to_owned(), "no ellipsis"),
        ("PROBE {}".to_owned(), "not an object"),
        (
            format!("PROBE {}", serde_json::to_string(&vec![0.5; 48]).unwrap()),
            "L2 norm exceeds 2",
        ),
        (
            format!("PROBE {}", serde_json::to_string(&vec![2.0; 48]).unwrap()),
            "coordinate 0 (zero-based) is outside [-1,1]",
        ),
        ("PROBE [true]".to_owned(), "not a finite JSON number"),
        ("PULSE uniform 0.3".to_owned(), "strength"),
    ] {
        let mut r = Run::new(spec(false));
        r.receive(&format!("I can leave text aside.\nINQUIRY: OPEN both \"A question.\"\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: {tail}"));
        let p = r.s.pending_journal().unwrap();
        let d = p.action.as_ref().unwrap();
        assert!(d.request.is_none());
        assert!(d.withholds_reservoir_input());
        assert!(
            d.diagnostics
                .as_ref()
                .unwrap()
                .next
                .explanation
                .contains(expected),
            "{}",
            d.diagnostics.as_ref().unwrap().next.explanation
        );
        let f = r.apply();
        assert_eq!(
            f.action_receipt.unwrap().status,
            SustainedActionStatus::Rejected
        );
        assert!(r
            .s
            .action_state()
            .unwrap()
            .continuity
            .as_ref()
            .unwrap()
            .active_inquiry
            .is_some());
        r.verify();
        r.reach();
        let prompt = &r.s.pending_language().unwrap().prompt;
        assert!(prompt.contains("input outcome: Some(Withhold)"));
        assert!(prompt.contains("inquiry outcome: Opened"));
        r.verify();
    }
}

#[test]
fn valid_probe_example_and_absent_controls_have_truthful_diagnostics() {
    let mut r = Run::new(spec(false));
    r.reach();
    let prompt = &r.s.pending_language().unwrap().prompt;
    let vector = prompt
        .split("single line NEXT: PROBE ")
        .nth(1)
        .unwrap()
        .split(']')
        .next()
        .unwrap();
    let raw = format!("A zero control.\nNEXT: PROBE {vector}]");
    r.receive(&raw);
    let f = r.apply();
    let receipt = f.action_receipt.unwrap();
    assert_eq!(receipt.status, SustainedActionStatus::Applied);
    assert_eq!(receipt.probe.unwrap().requested_vector, vec![0.0; 48]);
    assert!(receipt
        .diagnostics
        .unwrap()
        .next
        .explanation
        .contains("syntax accepted"));
    r.verify();
    r.receive("There is no control footer here.");
    let d =
        r.s.pending_journal()
            .unwrap()
            .action
            .as_ref()
            .unwrap()
            .diagnostics
            .as_ref()
            .unwrap();
    assert_eq!(d.next.candidate_count, 0);
    assert!(d.next.candidate.is_none());
    assert!(d.next.explanation.contains("Missing final NEXT"));
    r.apply();
    r.verify();
}

#[test]
fn independent_formatting_and_malformed_input_get_distinct_feedback() {
    let mut r = Run::new(spec(false));
    r.receive("Body.\n\n**INQUIRY: CONTINUE**\n**WITHHOLD_RESERVOIR_INPUT=true**\n**NEXT: NONE**");
    let d =
        r.s.pending_journal()
            .unwrap()
            .action
            .as_ref()
            .unwrap()
            .diagnostics
            .as_ref()
            .unwrap();
    assert!(d
        .reservoir_input
        .explanation
        .contains("not recognized; text input is SEND"));
    assert!(d
        .inquiry
        .explanation
        .contains("not recognized; the inquiry is unchanged"));
    r.apply();
    r.verify();
    r.receive("Body.\nWITHHOLD_RESERVOIR_INPUT=maybe\nNEXT: NONE");
    let a = r.s.pending_journal().unwrap().action.as_ref().unwrap();
    assert!(a.request.is_some());
    assert!(a.withholds_reservoir_input());
    assert!(a.reservoir_input.as_ref().unwrap().rejection.is_some());
    r.apply();
    r.verify();
}

#[test]
fn unicode_survives_embedding_failure_restore_retry_save_memory_and_replay() {
    let mut r = Run::new(spec(true));
    let raw = "≤ ≈ 🪨 e\u{301} 日本語 العربية\nINQUIRY: OPEN both \"Does ≤ mean ≈?\"\nNEXT: NONE";
    let id = r.reach();
    r.s.start_language(id).unwrap();
    assert!(r.s.response_needs_feedback(&reply(raw)).unwrap());
    r.s.retain_language_for_feedback(id, &reply(raw)).unwrap();
    let req = r.s.start_feedback(id).unwrap();
    r.s.fail_feedback(id, req, "fixture interruption").unwrap();
    r.verify();
    r.s = SustainedSession::restore(
        serde_json::from_slice(&serde_json::to_vec(&r.base).unwrap()).unwrap(),
    )
    .unwrap();
    assert_eq!(r.s.pending_feedback().unwrap().response.text, raw);
    r.s.retry_feedback().unwrap();
    let req2 = r.s.start_feedback(id).unwrap();
    assert!(req2 > req);
    r.s.confirm_feedback(id, req2, &external()).unwrap();
    let j = r.s.pending_journal().unwrap();
    assert_eq!(j.entry.text, raw);
    assert_eq!(
        j.entry.sha256,
        format!("{:x}", Sha256::digest(raw.as_bytes()))
    );
    r.apply();
    r.verify();
    r.reach();
    assert!(r
        .s
        .pending_language()
        .unwrap()
        .prompt
        .contains("≤ ≈ 🪨 e\u{301} 日本語 العربية"));
    r.verify();
    r.s = SustainedSession::restore(r.base.clone()).unwrap();
}

#[test]
fn unicode_withholding_and_passive_checkins_keep_their_distinct_paths() {
    for telemetry in [false, true] {
        let mut c = spec(true);
        c.check_in_schedule = Some(SustainedCheckInSchedule {
            interval_seconds: 10,
            end_after_seconds: 30,
            prompt: " Tell me, friend.\n".into(),
            include_telemetry: telemetry,
        });
        let mut r = Run::new(c);
        r.receive("≤ ≈\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: TUNE leak 0.7");
        assert!(r.s.pending_journal().unwrap().feedback_provenance.is_none());
        r.apply();
        r.verify();
        let before = r.s.action_state().unwrap().controls.clone();
        assert!(r.s.admit_due_check_in(10000).unwrap());
        r.reach();
        if !telemetry {
            assert_eq!(
                r.s.pending_language().unwrap().prompt,
                " Tell me, friend.\n"
            );
        }
        r.receive("≈\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: TUNE leak 0.9");
        assert!(r.s.pending_journal().unwrap().action.is_none());
        assert!(r.s.pending_journal().unwrap().feedback_provenance.is_some());
        assert!(r.apply().action_receipt.is_none());
        assert_eq!(r.s.action_state().unwrap().controls, before);
        r.verify();
    }
}

#[test]
fn policies_are_explicit_and_legacy_admission_remains_frozen() {
    let mut legacy = spec(true);
    legacy.text_admission = None;
    legacy.control_feedback = None;
    let encoded = serde_json::to_string(&legacy).unwrap();
    assert!(!encoded.contains("textAdmission"));
    assert!(!encoded.contains("controlFeedback"));
    let mut r = Run::new(legacy);
    let id = r.reach();
    r.s.start_language(id).unwrap();
    assert!(!r
        .s
        .pending_language()
        .unwrap()
        .prompt
        .contains("CONTROL FORMAT"));
    for text in ["≤", "≈"] {
        assert!(r.s.response_needs_feedback(&reply(text)).is_err());
    }
    let mut c = spec(false);
    c.text_admission = Some(SustainedTextAdmission::Utf8V1);
    assert!(SustainedSession::new(c).is_err());
    let mut c = spec(true);
    c.action_mode = Some(SustainedActionMode::AuthoredV2);
    c.prompt_version = SustainedPromptVersion::ActionJournalV2;
    assert!(SustainedSession::new(c).is_err());
    let mut r = Run::new(spec(true));
    let id = r.reach();
    r.s.start_language(id).unwrap();
    for text in ["", " \t\n\u{00a0}\u{2000}\u{2028}\u{3000}"] {
        assert!(r.s.response_needs_feedback(&reply(text)).is_err());
    }
    let mut incomplete = reply("≤");
    incomplete.complete = false;
    assert!(r.s.response_needs_feedback(&incomplete).is_err());
}

#[test]
fn candidate_excerpts_are_utf8_bounded_and_checkpoint_tampering_is_detected() {
    let mut r = Run::new(spec(true));
    r.receive(&format!(
        "Body.\n**NEXT: {}**\n**NEXT: {}**",
        "🪨".repeat(100),
        "🪨".repeat(100)
    ));
    let d =
        r.s.pending_journal()
            .unwrap()
            .action
            .as_ref()
            .unwrap()
            .diagnostics
            .as_ref()
            .unwrap();
    assert_eq!(d.next.candidate_count, 2);
    let c = d.next.candidate.as_ref().unwrap();
    assert!(c.truncated);
    assert!(c.excerpt.len() <= 256);
    assert_eq!(c.line, 3);
    r.apply();
    r.verify();
    let mut corrupted = r.base.clone();
    corrupted
        .state
        .action_state
        .as_mut()
        .unwrap()
        .latest_receipt
        .as_mut()
        .unwrap()
        .diagnostics
        .as_mut()
        .unwrap()
        .next
        .explanation = "invented outcome".into();
    corrupted.sha256 = format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&corrupted.state).unwrap())
    );
    assert!(SustainedSession::restore(corrupted).is_err());
}
