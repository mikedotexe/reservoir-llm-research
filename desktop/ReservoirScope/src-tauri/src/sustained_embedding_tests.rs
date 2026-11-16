use super::*;
use reservoir_core::sustained::{SustainedActionMode, SustainedCheckInSchedule};

const RAW: &str = "Retain this exact reply, even if encoding fails.\nNEXT: TUNE leak 0.75";
fn semantic_config() -> SustainedConfig {
    SustainedConfig {
        action_mode: Some(SustainedActionMode::AuthoredV2),
        prompt_version: SustainedPromptVersion::ActionJournalV2,
        embedding_model: Some("owned-test-embedding".into()),
        maximum_turns: 1,
        maximum_steps: 4,
        turn_every: 1,
        ..model_config()
    }
}
fn response(text: &str) -> LanguageResponse {
    LanguageResponse {
        text: text.into(),
        ..answer()
    }
}
fn embedding(model: &str) -> crate::model_transport::EmbeddingReceipt {
    crate::model_transport::EmbeddingReceipt {
        vector: (0..64).map(|i| (i as f64 * 0.17).sin()).collect(),
        model: model.into(),
        digest: None,
    }
}
fn settled(s: &SustainedState) {
    wait_long(|| !s.lock().unwrap().active.as_ref().unwrap().worker_active);
}
fn prepare_reply(s: &SustainedState, epoch: u64, text: &str) -> u64 {
    loop {
        match s.worker_boundary(epoch).unwrap() {
            Work::Provider(p, _, _permit) => {
                s.settle(epoch, p.attempt_id, Ok(response(text)), None, 25)
                    .unwrap();
                return p.attempt_id;
            }
            Work::Continue(_) => {}
            _ => panic!("expected generation boundary"),
        }
    }
}

#[test]
fn embedding_failure_restart_retry_preserves_one_generation_and_one_action() {
    encoding_recovery_case(
        semantic_config(),
        RAW,
        "Retain this exact reply, even if encoding fails.",
    );
}

#[test]
fn unicode_admission_and_control_diagnostics_survive_host_retry_and_export() {
    use reservoir_core::sustained::{SustainedControlFeedback, SustainedTextAdmission};
    let config = SustainedConfig {
        action_mode: Some(SustainedActionMode::AuthoredV3),
        prompt_version: SustainedPromptVersion::ActionJournalV3,
        text_admission: Some(SustainedTextAdmission::Utf8V1),
        control_feedback: Some(SustainedControlFeedback::DiagnosticV1),
        ..semantic_config()
    };
    encoding_recovery_case(
        config,
        "≤ ≈ 🪨 e\u{301} 日本語\nNEXT: TUNE leak 0.75",
        "≤ ≈ 🪨 e\u{301} 日本語",
    );
}

fn encoding_recovery_case(config: SustainedConfig, raw: &'static str, body: &'static str) {
    let feedback_policy = config.control_feedback;
    let admission_policy = config.text_admission;
    let d = tempfile::tempdir().unwrap();
    let root = d.path().join("store");
    let writers = Arc::new(AtomicU64::new(0));
    let calls = writers.clone();
    let s = SustainedState::with_provider_and_embedder(
        root.clone(),
        Arc::new(move |_, _, _, _, _, _| {
            calls.fetch_add(1, Ordering::SeqCst);
            Ok(response(raw))
        }),
        Arc::new(move |_, _, text, _, _| {
            assert_eq!(text, body);
            Err("owned embedding failure".into())
        }),
    );
    let m = s.create("create".into(), config).unwrap().summary.unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    settled(&s);
    let before = s.get("view".into(), None).unwrap().summary.unwrap();
    assert_eq!(before.phase, "embeddingBlocked");
    assert_eq!(before.turn_count, 1);
    assert_eq!(before.journal_count, 0);
    assert!(!before.can_start && !before.can_retry_provider && before.can_retry_embedding);
    assert_eq!(before.pending_embedding.unwrap().response_text, raw);
    assert!(s.start("bad".into(), &m.session_id, &m.generation).is_err());
    let original = s.shared.store.verify(&m.session_id).unwrap();
    assert_eq!(original.received_responses.total, 1);
    let timing = serde_json::to_value(&original.manifest.attempt_timing).unwrap();
    let embeddings = Arc::new(AtomicU64::new(0));
    let encoded = embeddings.clone();
    let resumed = SustainedState::with_provider_and_embedder(
        root,
        Arc::new(|_, _, _, _, _, _| panic!("encoding retry must never regenerate writing")),
        Arc::new(move |_, model, text, _, _| {
            encoded.fetch_add(1, Ordering::SeqCst);
            assert_eq!(text, body);
            Ok(embedding(model))
        }),
    );
    let restored = resumed
        .resume(
            "restore".into(),
            &m.session_id,
            &original.manifest.generation,
            &original.manifest.revision,
        )
        .unwrap()
        .summary
        .unwrap();
    assert!(restored.can_retry_embedding && !restored.can_start);
    assert_eq!(embeddings.load(Ordering::SeqCst), 0);
    resumed
        .retry_embedding("retry".into(), &m.session_id, &restored.generation)
        .unwrap();
    settled(&resumed);
    let held = resumed.get("held".into(), None).unwrap().summary.unwrap();
    assert_eq!(held.journal_count, 1);
    assert!(held.pending_application.is_some());
    assert_eq!(held.actions.unwrap().state.decision_count, 0);
    assert_eq!(writers.load(Ordering::SeqCst), 1);
    assert_eq!(embeddings.load(Ordering::SeqCst), 1);
    assert!(resumed
        .retry_embedding("again".into(), &m.session_id, &restored.generation)
        .is_err());
    let after = resumed.shared.store.verify(&m.session_id).unwrap();
    assert_eq!(after.received_responses.total, 1);
    assert_eq!(
        serde_json::to_value(&after.manifest.attempt_timing).unwrap(),
        timing
    );
    resumed
        .start("apply".into(), &m.session_id, &restored.generation)
        .unwrap();
    settled(&resumed);
    let end = resumed.get("done".into(), None).unwrap().summary.unwrap();
    assert_eq!(end.phase, "budgetReached");
    assert_eq!(end.step, 2);
    assert_eq!(end.actions.unwrap().state.decision_count, 1);
    let verified = resumed.shared.store.verify(&m.session_id).unwrap();
    assert_eq!(verified.checkpoint.state.attempt_cursor, 1);
    assert_eq!(verified.manifest.config.text_admission, admission_policy);
    assert_eq!(verified.manifest.config.control_feedback, feedback_policy);
    let latest = verified
        .checkpoint
        .state
        .action_state
        .as_ref()
        .unwrap()
        .latest_receipt
        .as_ref()
        .unwrap();
    assert_eq!(latest.diagnostics.is_some(), feedback_policy.is_some());
    assert_eq!(
        verified
            .checkpoint
            .state
            .action_state
            .unwrap()
            .controls
            .leak,
        0.75
    );
    let export = d.path().join("exports");
    fs::create_dir(&export).unwrap();
    let report = resumed
        .export(&m.session_id, &restored.generation, None, &export, &[])
        .unwrap()
        .1;
    assert_eq!(report.journal_count, 1);
}

#[test]
fn failed_retention_save_never_dispatches_embedding_and_retry_save_keeps_reply() {
    for stage in [1, 3, 4] {
        let (_d, s, id, generation) = {
            let d = tempfile::tempdir().unwrap();
            let s = SustainedState::with_provider_and_embedder(
                d.path().join("store"),
                Arc::new(|_, _, _, _, _, _| panic!("manual generation")),
                Arc::new(|_, _, _, _, _| panic!("not admitted")),
            );
            let m = s
                .create("create".into(), semantic_config())
                .unwrap()
                .summary
                .unwrap();
            (d, s, m.session_id, m.generation)
        };
        let epoch = arm(&s);
        assert!(matches!(
            s.worker_boundary(epoch).unwrap(),
            Work::Continue(_)
        ));
        let Work::Provider(p, _, _permit) = s.worker_boundary(epoch).unwrap() else {
            panic!()
        };
        s.shared.store.fail_next(stage);
        assert!(s
            .settle(epoch, p.attempt_id, Ok(response(RAW)), None, 25)
            .is_err());
        assert_eq!(
            s.get("view".into(), None).unwrap().summary.unwrap().phase,
            "storageBlocked"
        );
        assert!(s
            .retry_embedding("not-yet".into(), &id, &generation)
            .is_err());
        assert_eq!(
            s.lock()
                .unwrap()
                .active
                .as_ref()
                .unwrap()
                .engine
                .pending_feedback()
                .unwrap()
                .response
                .text,
            RAW
        );
        s.retry_save("save".into(), &id, &generation).unwrap();
        let saved = s.shared.store.verify(&id).unwrap();
        assert_eq!(saved.checkpoint.state.attempt_cursor, 1);
        assert_eq!(saved.received_responses.total, 1);
        assert!(
            s.get("view".into(), None)
                .unwrap()
                .summary
                .unwrap()
                .can_retry_embedding
        );
    }
}

#[test]
fn failed_embedding_dispatch_save_is_retryable_without_a_network_request() {
    for stage in [1, 3, 4] {
        let d = tempfile::tempdir().unwrap();
        let s = SustainedState::new(d.path().join("store"));
        let m = s
            .create("create".into(), semantic_config())
            .unwrap()
            .summary
            .unwrap();
        let epoch = arm(&s);
        prepare_reply(&s, epoch, RAW);
        s.shared.store.fail_next(stage);
        assert!(s.worker_boundary(epoch).is_err());
        let g = s.lock().unwrap();
        let p = g
            .active
            .as_ref()
            .unwrap()
            .engine
            .pending_feedback()
            .unwrap();
        assert!(!p.request_started && p.failure.is_some());
        assert_eq!(p.response.text, RAW);
        drop(g);
        s.retry_save("save".into(), &m.session_id, &m.generation)
            .unwrap();
        assert!(
            s.get("view".into(), None)
                .unwrap()
                .summary
                .unwrap()
                .can_retry_embedding
        );
        s.shared.store.verify(&m.session_id).unwrap();
    }
}

#[test]
fn stop_during_embedding_retains_reply_and_ignores_late_result() {
    let d = tempfile::tempdir().unwrap();
    let entered = Arc::new(AtomicBool::new(false));
    let release = Arc::new(AtomicBool::new(false));
    let e = entered.clone();
    let r = release.clone();
    let s = SustainedState::with_provider_and_embedder(
        d.path().join("store"),
        Arc::new(|_, _, _, _, _, _| Ok(response(RAW))),
        Arc::new(move |_, model, _, _, _| {
            e.store(true, Ordering::SeqCst);
            while !r.load(Ordering::SeqCst) {
                std::thread::sleep(Duration::from_millis(5));
            }
            Ok(embedding(model))
        }),
    );
    let m = s
        .create("create".into(), semantic_config())
        .unwrap()
        .summary
        .unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_long(|| entered.load(Ordering::SeqCst));
    let before = s.shared.store.verify(&m.session_id).unwrap();
    assert_eq!(before.received_responses.total, 1);
    s.stop("stop".into(), &m.session_id, &m.generation).unwrap();
    release.store(true, Ordering::SeqCst);
    settled(&s);
    let after = s.shared.store.verify(&m.session_id).unwrap();
    assert_eq!(after.manifest.phase, "stopped");
    assert_eq!(after.report.journal_count, 0);
    let p = match after.checkpoint.state.phase {
        SustainedPhase::Feedback(p) => p,
        _ => panic!(),
    };
    assert_eq!(p.response.text, RAW);
    assert!(p.failure.is_some());
    assert!(!p.request_started);
    assert!(
        s.get("view".into(), None)
            .unwrap()
            .summary
            .unwrap()
            .can_retry_embedding
    );
}

#[test]
fn final_checkin_encoding_retry_keeps_schedule_and_applies_once() {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::with_provider_and_embedder(
        d.path().join("store"),
        Arc::new(|_, _, _, _, _, _| panic!("no second generation")),
        Arc::new(|_, model, _, _, _| Ok(embedding(model))),
    );
    let cfg = SustainedConfig {
        maximum_duration_seconds: 1,
        maximum_turns: 20,
        maximum_steps: 20,
        turn_every: 30,
        check_in_schedule: Some(SustainedCheckInSchedule {
            interval_seconds: 1,
            end_after_seconds: 1,
            prompt: "Hello".into(),
            include_telemetry: false,
        }),
        ..semantic_config()
    };
    let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
    let epoch = arm(&s);
    {
        let mut g = s.lock().unwrap();
        g.active.as_mut().unwrap().manifest.elapsed_millis = 1000;
    }
    let attempt = prepare_reply(
        &s,
        epoch,
        "Conversational body.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: TUNE leak 0.75",
    );
    let Work::Embedding(p, _, _, _permit) = s.worker_boundary(epoch).unwrap() else {
        panic!()
    };
    s.settle_embedding(epoch, attempt, p.request_id, Err("retry me".into()))
        .unwrap();
    assert!(matches!(s.worker_boundary(epoch).unwrap(), Work::Done));
    s.retry_embedding("retry".into(), &m.session_id, &m.generation)
        .unwrap();
    settled(&s);
    // Final conversations settle their application boundary before declaring completion.
    let summary = s.get("done".into(), None).unwrap().summary.unwrap();
    if summary.phase != "scheduleComplete" {
        s.start("apply".into(), &m.session_id, &m.generation)
            .unwrap();
        settled(&s);
    }
    let saved = s.shared.store.verify(&m.session_id).unwrap();
    assert_eq!(saved.manifest.phase, "scheduleComplete");
    assert_eq!(saved.report.journal_count, 1);
    assert_eq!(
        saved.checkpoint.state.action_state.unwrap().decision_count,
        0
    );
    assert_eq!(saved.received_responses.total, 1);
}

#[test]
fn new_scripted_embedding_configuration_is_rejected_without_rejecting_historical_validation() {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    let mut cfg = semantic_config();
    cfg.language = SustainedConfig::default().language;
    cfg.validate().unwrap();
    assert!(s.create("create".into(), cfg).is_err());
}
