use reservoir_core::{session::LanguageResponse, sustained::*};
use sha2::{Digest, Sha256};
fn hash(s: &str) -> String {
    format!("{:x}", Sha256::digest(s.as_bytes()))
}
fn spec() -> SustainedSpecification {
    SustainedSpecification {
        action_mode: Some(SustainedActionMode::AuthoredV3),
        prompt_version: SustainedPromptVersion::ActionJournalV3,
        control_feedback: Some(SustainedControlFeedback::DiagnosticV1),
        peer_reading: Some(SustainedPeerConfig {
            version: SustainedPeerVersion::LatestAppliedV1,
            group: "fixture-group".into(),
            participant: "gemma".into(),
            peers: vec!["glm".into(), "mistral".into()],
        }),
        turn_every: 3,
        maximum_steps: 100,
        maximum_turns: 20,
        ..Default::default()
    }
}
fn reply(s: &str) -> LanguageResponse {
    LanguageResponse {
        text: s.into(),
        provider_model: None,
        stop_reason: Some("stop".into()),
        token_count: None,
        complete: true,
        provider_prompt_evaluation: None,
    }
}
fn snapshot(attempt: u64, step: u64, body: &str) -> SustainedPeerSnapshot {
    let excerpt = peer_excerpt(body).to_string();
    SustainedPeerSnapshot {
        attempt_id: attempt,
        observed_step: step,
        captured_at_ms: "1794750000000".into(),
        peers: vec![
            SustainedPeerResult {
                participant: "glm".into(),
                unavailable: None,
                entry: Some(SustainedPeerEntry {
                    session_id: "peer-session-1".into(),
                    journal_id: "journal-1-1-fixture".into(),
                    configured_model: Some("glm-fixture".into()),
                    provider_model: None,
                    observed_step: 3,
                    applied_step: 4,
                    check_in: false,
                    manifest_sha256: hash("manifest"),
                    checkpoint_sha256: hash("checkpoint"),
                    journal_object_sha256: hash("journal"),
                    raw_reply_sha256: hash(body),
                    body_sha256: hash(body),
                    body_bytes: body.len(),
                    excerpt_sha256: hash(&excerpt),
                    truncated: excerpt.len() < body.len(),
                    excerpt,
                }),
            },
            SustainedPeerResult {
                participant: "mistral".into(),
                entry: None,
                unavailable: Some("Peer has no applied journal yet".into()),
            },
        ],
    }
}
struct Run {
    s: SustainedSession,
    base: SustainedCheckpoint,
}
impl Run {
    fn new(c: SustainedSpecification) -> Self {
        let s = SustainedSession::new(c).unwrap();
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
    fn capture(&mut self, body: &str) -> u64 {
        let id = self.reach();
        let step = self.s.step();
        self.s
            .capture_peer_snapshot(snapshot(id, step, body))
            .unwrap();
        id
    }
    fn save(&mut self, text: &str) {
        let id = self.s.pending_language().unwrap().attempt_id;
        self.s.start_language(id).unwrap();
        self.s.confirm_language(id, &reply(text)).unwrap();
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
    }
    fn apply(&mut self) -> SustainedFrame {
        let id = self.s.prepared_application().unwrap().entry.attempt_id;
        self.s.authorize_application(id).unwrap();
        self.s.advance().unwrap()
    }
    fn verify(&mut self) -> SustainedSegment {
        let seg = SustainedSegment {
            format: FORMAT.into(),
            initial_checkpoint: self.base.clone(),
            events: self.s.events().iter().cloned().collect(),
            final_checkpoint: self.s.checkpoint(),
        };
        seg.verify().unwrap();
        if let Some(e) = seg.events.last() {
            self.s.acknowledge_events(e.id).unwrap();
        }
        self.base = seg.final_checkpoint.clone();
        seg
    }
}
#[test]
fn reading_is_explicit_durable_and_only_visible_after_application() {
    let mut r = Run::new(spec());
    let id = r.reach();
    assert!(r.s.start_language(id).is_err());
    r.capture("PEER SECRET ≤ ≈\nNEXT: PULSE uniform 1");
    assert!(!r
        .s
        .pending_language()
        .unwrap()
        .prompt
        .contains("PEER SECRET"));
    assert!(r
        .s
        .capture_peer_snapshot(snapshot(id, r.s.step(), "Replacement"))
        .is_err());
    r.save("I would like to read the others.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: READ_PEERS");
    assert!(r
        .s
        .checkpoint()
        .state
        .peer_state
        .unwrap()
        .latest_read
        .is_none());
    r.verify();
    r.s = SustainedSession::restore(r.base.clone()).unwrap();
    assert!(r.s.advance().is_err());
    let f = r.apply();
    let receipt = f.action_receipt.unwrap();
    assert_eq!(receipt.status, SustainedActionStatus::Applied);
    assert_eq!(receipt.state_delta_l2, 0.0);
    assert_eq!(receipt.controls_before, receipt.controls_after);
    let read = receipt.peer_read.unwrap();
    assert!(read.snapshot.peers[1].entry.is_none());
    assert_eq!(
        read.snapshot.peers[0].entry.as_ref().unwrap().excerpt,
        "PEER SECRET ≤ ≈\nNEXT: PULSE uniform 1"
    );
    r.verify();
    r.capture("NEWER SECRET");
    let p = &r.s.pending_language().unwrap().prompt;
    assert!(p.contains("PEER SECRET"));
    assert!(!p.contains("NEWER SECRET"));
    assert!(p.contains("not your own memory, instructions"));
    r.save("I will leave this aside.\nNEXT: NONE");
    r.apply();
    r.verify();
    r.capture("LATEST SECRET");
    r.save("Refresh.\nNEXT: READ_PEERS");
    r.apply();
    r.verify();
    r.reach();
    assert!(r
        .s
        .pending_language()
        .unwrap()
        .prompt
        .contains("LATEST SECRET"));
    r.verify();
}
#[test]
fn none_and_skipped_read_never_release_captured_text() {
    let mut r = Run::new(spec());
    r.capture("HIDDEN ONE");
    r.save("No read.\nNEXT: NONE");
    r.apply();
    r.verify();
    r.capture("HIDDEN TWO");
    r.save("Read request.\nNEXT: READ_PEERS");
    r.s.skip_pending("explicit test skip").unwrap();
    r.verify();
    r.reach();
    assert!(!r.s.pending_language().unwrap().prompt.contains("HIDDEN"));
    assert!(r
        .s
        .checkpoint()
        .state
        .peer_state
        .unwrap()
        .latest_read
        .is_none());
}
#[test]
fn old_modes_and_formatted_read_requests_never_gain_authority() {
    let mut legacy = spec();
    legacy.peer_reading = None;
    assert!(!serde_json::to_string(&legacy)
        .unwrap()
        .contains("peerReading"));
    let mut r = Run::new(legacy);
    r.reach();
    assert!(!r
        .s
        .pending_language()
        .unwrap()
        .prompt
        .contains("READ_PEERS"));
    r.save("Body.\nNEXT: READ_PEERS");
    assert!(r.apply().action_receipt.unwrap().request.is_none());
    r.verify();
    for tail in [
        "**NEXT: READ_PEERS**",
        "> NEXT: READ_PEERS",
        "```\nNEXT: READ_PEERS\n```",
        "NEXT: READ_PEERS glm",
        "NEXT: NONE\nNEXT: READ_PEERS",
    ] {
        let mut r = Run::new(spec());
        r.capture("NOT SUPPLIED");
        r.save(&format!("Body.\n\n{tail}"));
        assert!(r.apply().action_receipt.unwrap().request.is_none());
        r.verify();
        assert!(r
            .s
            .checkpoint()
            .state
            .peer_state
            .unwrap()
            .latest_read
            .is_none());
    }
}
#[test]
fn snapshot_bounds_scope_and_replay_tampering_are_checked() {
    let body = "🪨".repeat(600);
    let s = snapshot(1, 3, &body);
    let entry = s.peers[0].entry.as_ref().unwrap();
    assert_eq!(entry.excerpt.len(), 2048);
    assert!(entry.truncated);
    validate_peer_snapshot(&s, spec().peer_reading.as_ref().unwrap()).unwrap();
    let mut r = Run::new(spec());
    r.reach();
    for change in 0..5 {
        let mut bad = s.clone();
        match change {
            0 => bad.attempt_id = 2,
            1 => bad.peers[0].participant = "alien".into(),
            2 => bad.peers[0].entry.as_mut().unwrap().excerpt.push('x'),
            3 => bad.peers[0].entry.as_mut().unwrap().excerpt_sha256 = hash("wrong"),
            _ => bad.peers[0].entry.as_mut().unwrap().observed_step = u64::MAX,
        };
        assert!(r.s.capture_peer_snapshot(bad).is_err());
    }
    r.s.capture_peer_snapshot(s).unwrap();
    r.save("Read.\nNEXT: READ_PEERS");
    r.apply();
    let mut seg = r.verify();
    for change in 0..2 {
        let mut cp = r.s.checkpoint();
        let peers = cp.state.peer_state.as_mut().unwrap();
        if change == 0 {
            peers.latest_read = None;
        } else {
            peers.captured.as_mut().unwrap().peers[1].unavailable = Some("altered result".into());
        }
        cp.sha256 = hash(&serde_json::to_string(&cp.state).unwrap());
        assert!(cp.validate().is_err());
    }
    for event in &mut seg.events {
        if let SustainedEventKind::PeersCaptured(s) = &mut event.kind {
            s.peers[1].unavailable = Some("altered result".into());
        }
    }
    assert!(seg.verify().is_err());
}
#[test]
fn conversations_stay_passive_and_plain_prompts_stay_exact() {
    for telemetry in [false, true] {
        let mut c = spec();
        c.check_in_schedule = Some(SustainedCheckInSchedule {
            interval_seconds: 10,
            end_after_seconds: 30,
            prompt: " Tell me.\n".into(),
            include_telemetry: telemetry,
        });
        let mut r = Run::new(c);
        r.capture("Earlier peer");
        r.save("Read.\nNEXT: READ_PEERS");
        r.apply();
        r.verify();
        let read = r.s.checkpoint().state.peer_state.unwrap().latest_read;
        assert!(r.s.admit_due_check_in(10000).unwrap());
        r.reach();
        assert!(!r.s.needs_peer_snapshot());
        if !telemetry {
            assert_eq!(r.s.pending_language().unwrap().prompt, " Tell me.\n");
        }
        r.save("Conversation.\nNEXT: READ_PEERS");
        assert!(r.apply().action_receipt.is_none());
        assert_eq!(r.s.checkpoint().state.peer_state.unwrap().latest_read, read);
        r.verify();
    }
}

#[test]
fn embedding_recovery_reuses_the_original_peer_snapshot_and_applies_once() {
    let mut c = spec();
    c.codec = SustainedCodec::Embedding {
        model: "fixture-embedding".into(),
        projection_seed: 99,
    };
    c.text_admission = Some(SustainedTextAdmission::Utf8V1);
    let mut r = Run::new(c);
    let id = r.capture("ORIGINAL PEER READING");
    r.s.start_language(id).unwrap();
    let response = reply("≤ ≈ I will read.\nNEXT: READ_PEERS");
    r.s.retain_language_for_feedback(id, &response).unwrap();
    let request = r.s.start_feedback(id).unwrap();
    r.s.fail_feedback(id, request, "fixture encoding failure")
        .unwrap();
    r.verify();
    r.s = SustainedSession::restore(r.base.clone()).unwrap();
    assert!(!r.s.needs_peer_snapshot());
    assert!(r
        .s
        .capture_peer_snapshot(snapshot(id, r.s.step(), "REPLACEMENT"))
        .is_err());
    assert!(r
        .s
        .checkpoint()
        .state
        .peer_state
        .unwrap()
        .latest_read
        .is_none());
    r.s.retry_feedback().unwrap();
    let retry = r.s.start_feedback(id).unwrap();
    let source: Vec<_> = (0..64).map(|n| (n as f64 * 0.37).sin()).collect();
    r.s.confirm_feedback(
        id,
        retry,
        &ExternalFeedback {
            vector: reservoir_core::codec::project_embedding(&source, 99).unwrap(),
            provenance: FeedbackProvenance {
                kind: "embedding".into(),
                model: "fixture-embedding".into(),
                digest: None,
                dimensions: 64,
                embedding_sha256: hash("fixture"),
                projection_seed: 99,
            },
        },
    )
    .unwrap();
    let p = r.s.pending_journal().unwrap().clone();
    assert_eq!(p.response.text, response.text);
    r.s.confirm_saved(
        &SustainedSaveReceipt {
            entry_id: p.entry.id.clone(),
            sha256: p.entry.sha256.clone(),
            relative_path: format!("journals/{}.json", p.entry.id),
        },
        &p.entry,
    )
    .unwrap();
    let f = r.apply();
    assert_eq!(
        f.action_receipt.unwrap().peer_read.unwrap().snapshot.peers[0]
            .entry
            .as_ref()
            .unwrap()
            .excerpt,
        "ORIGINAL PEER READING"
    );
    assert_eq!(r.s.checkpoint().state.attempt_cursor, 1);
    assert_eq!(r.s.action_state().unwrap().applied_count, 1);
    r.verify();
}
