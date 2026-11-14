use super::*;
use reservoir_core::sustained::{SustainedActionMode, SustainedCheckInSchedule};

fn action_config(steps: u64, turn: u64) -> SustainedConfig {
    SustainedConfig {
        action_mode: Some(SustainedActionMode::AuthoredV1),
        prompt_version: SustainedPromptVersion::ActionJournalV1,
        ..config(steps, turn)
    }
}
fn action_setup(steps: u64, turn: u64) -> (tempfile::TempDir, SustainedState, String, String) {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    let m = s
        .create("create".into(), action_config(steps, turn))
        .unwrap()
        .summary
        .unwrap();
    (d, s, m.session_id, m.generation)
}
fn reply(text: &str) -> LanguageResponse {
    LanguageResponse {
        text: text.into(),
        ..answer()
    }
}
fn dispatch(s: &SustainedState, epoch: u64, text: &str) {
    until(s, epoch, |a| a.engine.pending_language().is_some());
    let Work::Provider(p, _) = s.worker_boundary(epoch).unwrap() else {
        panic!("provider boundary")
    };
    s.settle(epoch, p.attempt_id, Ok(reply(text)), None, 1)
        .unwrap();
}
fn action_state(s: &SustainedState) -> serde_json::Value {
    serde_json::to_value(
        s.get("view".into(), None)
            .unwrap()
            .summary
            .unwrap()
            .actions
            .unwrap(),
    )
    .unwrap()
}

#[test]
fn authored_action_config_requires_both_capability_and_new_prompt() {
    let old = config(8, 3);
    assert!(serde_json::to_value(&old)
        .unwrap()
        .get("actionMode")
        .is_none());
    let (_d, s, _, _) = setup(8, 3);
    assert!(
        serde_json::to_value(s.get("view".into(), None).unwrap().summary.unwrap())
            .unwrap()
            .get("actions")
            .is_none()
    );
    let mut changed = old.clone();
    changed.action_mode = Some(SustainedActionMode::AuthoredV1);
    assert!(changed.validate().is_err());
    changed.prompt_version = SustainedPromptVersion::ActionJournalV1;
    changed.validate().unwrap();
    assert_eq!(
        serde_json::to_value(&changed).unwrap()["actionMode"],
        "authored-v1"
    );
    changed.action_mode = None;
    assert!(changed.validate().is_err());
}

#[test]
fn authored_action_waits_for_saved_preparation_and_retry_applies_exactly_once() {
    let (d, s, id, generation) = action_setup(8, 3);
    let epoch = arm(&s);
    let raw = "I will adjust how strongly new state replaces old state.\nNEXT: TUNE leak 0.35";
    dispatch(&s, epoch, raw);
    let view = action_state(&s);
    assert_eq!(view["state"]["controls"]["leak"], 0.65);
    assert_eq!(view["pending"]["phase"], "saving");
    assert!(view["state"]["latestReceipt"].is_null());
    s.shared.store.fail_next(3);
    assert!(s.worker_boundary(epoch).is_err());
    let view = action_state(&s);
    assert_eq!(view["state"]["controls"]["leak"], 0.65);
    assert_eq!(view["pending"]["phase"], "prepared");
    assert_eq!(view["pending"]["durablePrepared"], false);
    s.retry_save("retry".into(), &id, &generation).unwrap();
    assert_eq!(action_state(&s)["pending"]["durablePrepared"], true);
    let epoch = arm(&s);
    assert!(drive(&s, epoch));
    s.pause("pause".into(), &id, &generation).unwrap();
    drive(&s, epoch);
    let saved = s.shared.store.verify(&id).unwrap();
    assert_eq!(saved.checkpoint.state.step, 4);
    let state = action_state(&s);
    assert_eq!(state["state"]["controls"]["leak"], 0.35);
    assert_eq!(state["state"]["decisionCount"], 1);
    assert_eq!(state["state"]["latestReceipt"]["appliedStep"], 4);
    let page = s
        .journal_page("page".into(), &id, &generation, 0, 10)
        .unwrap();
    assert_eq!(page.entries.len(), 1);
    assert!(!page.entries[0].text_preview.contains("NEXT:"));
    let journal = s
        .journal(
            "journal".into(),
            &id,
            &generation,
            &page.entries[0].entry_id,
        )
        .unwrap()
        .journal;
    assert_eq!(journal["rawReply"], raw);
    assert_eq!(journal["text"], raw);
    let body = journal["action"]["body"].as_str().unwrap();
    assert!(!body.contains("NEXT:"));
    assert_eq!(journal["bodySha256"], crate::files::digest(body.as_bytes()));
    assert_eq!(journal["sha256"], crate::files::digest(raw.as_bytes()));
    assert_eq!(
        journal["encodedFeatures"],
        serde_json::to_value(reservoir_core::codec::encode(body).unwrap()).unwrap()
    );
    assert_eq!(journal["actionReceipt"]["status"], "applied");
    let exports = d.path().join("exports");
    fs::create_dir(&exports).unwrap();
    s.export(&id, &generation, None, &exports, &[]).unwrap();
    s.stop("stop".into(), &id, &generation).unwrap();
    let saved = s.shared.store.verify(&id).unwrap();
    let restored = s
        .resume(
            "resume".into(),
            &id,
            &saved.manifest.generation,
            &saved.manifest.revision,
        )
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(
        serde_json::to_value(restored.actions.unwrap()).unwrap()["state"]["decisionCount"],
        1
    );
    let epoch = arm(&s);
    drive(&s, epoch);
    assert_eq!(action_state(&s)["state"]["decisionCount"], 1);
}

#[test]
fn authored_action_application_receipt_is_not_published_before_its_commit() {
    let (_d, s, id, generation) = action_setup(8, 3);
    let epoch = arm(&s);
    dispatch(
        &s,
        epoch,
        "A single pulse, with a receipt to inspect.\nNEXT: PULSE alternating 0.5",
    );
    s.pause("pause-before-application".into(), &id, &generation)
        .unwrap();
    s.worker_boundary(epoch).unwrap();
    let epoch = arm(&s);
    s.shared.store.fail_next(3);
    assert!(s.worker_boundary(epoch).is_err());
    let unpublished = action_state(&s);
    assert_eq!(unpublished["durableStep"], 3);
    assert_eq!(unpublished["state"]["decisionCount"], 0);
    assert!(unpublished["state"]["latestReceipt"].is_null());
    s.retry_save("retry-commit".into(), &id, &generation)
        .unwrap();
    let published = action_state(&s);
    assert_eq!(published["durableStep"], 4);
    assert_eq!(published["state"]["decisionCount"], 1);
    assert_eq!(published["state"]["latestReceipt"]["status"], "applied");
    let saved = s.shared.store.verify(&id).unwrap();
    assert_eq!(saved.checkpoint.state.step, 4);
    let before = saved.checkpoint.state.reservoir_state;
    s.retry_save("idempotent".into(), &id, &generation).unwrap();
    let saved = s.shared.store.verify(&id).unwrap();
    assert_eq!(saved.checkpoint.state.reservoir_state, before);
    assert_eq!(action_state(&s)["state"]["decisionCount"], 1);
}

#[test]
fn authored_action_scripted_cycle_is_persistent_and_recoverable_with_historical_receipts() {
    let (_d, s, id, generation) = action_setup(13, 3);
    s.start("start".into(), &id, &generation).unwrap();
    wait_long(|| !s.is_busy());
    let m = s.get("done".into(), None).unwrap().summary.unwrap();
    assert_eq!(m.step, 13);
    assert_eq!(m.journal_count, 4);
    let state = serde_json::to_value(m.actions.unwrap()).unwrap();
    assert_eq!(state["state"]["decisionCount"], 4);
    assert_eq!(state["state"]["controls"]["leak"], 0.65);
    let page = s
        .journal_page("page".into(), &id, &generation, 0, 10)
        .unwrap();
    let mut statuses = Vec::new();
    for index in page.entries.iter().rev() {
        let detail = s
            .journal("detail".into(), &id, &generation, &index.entry_id)
            .unwrap()
            .journal;
        statuses.push(
            detail["actionReceipt"]["status"]
                .as_str()
                .unwrap()
                .to_owned(),
        );
        assert_eq!(detail["actionReceipt"]["journalId"], index.entry_id);
        assert!(detail["action"]["body"]
            .as_str()
            .unwrap()
            .starts_with("Example writing:"));
        if detail["memory"].is_object() {
            let memory = &detail["memory"];
            let supplied = memory["suppliedText"].as_str().unwrap();
            assert!(!supplied.contains("NEXT:"));
            assert!(memory["text"].as_str().unwrap().contains("NEXT:"));
            assert_eq!(
                memory["suppliedTextSha256"],
                crate::files::digest(supplied.as_bytes())
            );
            assert_eq!(
                memory["sha256"],
                crate::files::digest(memory["text"].as_str().unwrap().as_bytes())
            );
        }
    }
    assert_eq!(statuses, ["applied", "applied", "unchanged", "applied"]);
    let before = s.shared.store.verify(&id).unwrap();
    s.stop("stop".into(), &id, &generation).unwrap();
    let saved = s.shared.store.verify(&id).unwrap();
    let restored = s
        .resume(
            "resume".into(),
            &id,
            &saved.manifest.generation,
            &saved.manifest.revision,
        )
        .unwrap()
        .summary
        .unwrap();
    let restored_page = s
        .journal_page("restored-page".into(), &id, &restored.generation, 0, 10)
        .unwrap();
    assert_eq!(
        serde_json::to_value(restored_page.entries).unwrap(),
        serde_json::to_value(page.entries).unwrap()
    );
    assert_eq!(
        before.checkpoint.state.action_state.unwrap(),
        saved.checkpoint.state.action_state.unwrap()
    );
}

#[test]
fn authored_action_plain_and_telemetry_checkins_keep_next_text_inert() {
    for telemetry in [false, true] {
        let d = tempfile::tempdir().unwrap();
        let s = SustainedState::new(d.path().join("store"));
        let cfg = SustainedConfig {
            check_in_schedule: Some(SustainedCheckInSchedule {
                interval_seconds: 1,
                end_after_seconds: 1,
                prompt: "What are you curious about?".into(),
                include_telemetry: telemetry,
            }),
            maximum_duration_seconds: 1,
            ..action_config(100, 3)
        };
        let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
        let epoch = arm(&s);
        dispatch(
            &s,
            epoch,
            "A lasting adjustment before the conversational probe.\nNEXT: TUNE leak 0.35",
        );
        drive(&s, epoch);
        {
            let mut g = s.lock().unwrap();
            let a = g.active.as_mut().unwrap();
            assert_eq!(a.engine.step(), 4);
            a.manifest.elapsed_millis = 1000;
            a.last_accounted = Instant::now();
        }
        let raw =
            "This conversational reply mentions a control but does not execute it.\nNEXT: RELEASE";
        let mut received = false;
        for _ in 0..10 {
            match s.worker_boundary(epoch).unwrap() {
                Work::Provider(p, sampling) => {
                    assert!(p.check_in.is_some());
                    assert_eq!(s.feedback_text_for(epoch, p.attempt_id, raw).unwrap(), raw);
                    assert!(!s.scripted_reply_for(epoch, &p).contains("NEXT:"));
                    if !telemetry {
                        assert_eq!(p.prompt, "What are you curious about?");
                        assert!(sampling.system.is_none());
                    }
                    s.settle(epoch, p.attempt_id, Ok(reply(raw)), None, 1)
                        .unwrap();
                    received = true;
                }
                Work::Continue(_) => {}
                Work::Done => break,
            }
        }
        assert!(received);
        let final_state = action_state(&s);
        assert_eq!(final_state["state"]["decisionCount"], 1);
        assert_eq!(final_state["state"]["controls"]["leak"], 0.35);
        let page = s
            .journal_page("page".into(), &m.session_id, &m.generation, 0, 10)
            .unwrap();
        let checkin = s
            .journal(
                "detail".into(),
                &m.session_id,
                &m.generation,
                &page.entries[0].entry_id,
            )
            .unwrap()
            .journal;
        assert!(checkin.get("action").is_none());
        assert!(checkin.get("actionReceipt").is_none());
        assert_eq!(checkin["text"], raw);
        s.shared.store.verify(&m.session_id).unwrap();
    }
}

#[test]
fn authored_action_embedding_receives_body_but_saved_reply_retains_tail() {
    let d = tempfile::tempdir().unwrap();
    let inputs = Arc::new(Mutex::new(Vec::new()));
    let seen = inputs.clone();
    let raw =
        "The embedding should contain these words without a control tail.\nNEXT: PULSE uniform 0.1";
    let s = SustainedState::with_provider_and_embedder(
        d.path().join("store"),
        Arc::new(move |_, _, _, _, _, _| Ok(reply(raw))),
        Arc::new(move |_, model, text, _, _| {
            seen.lock().unwrap().push(text.to_owned());
            Ok(crate::model_transport::EmbeddingReceipt {
                vector: (0..64).map(|i| (i as f64 * 0.1).sin()).collect(),
                model: model.into(),
                digest: None,
            })
        }),
    );
    let mut cfg = action_config(4, 3);
    cfg.language = model_config().language;
    cfg.embedding_model = Some("owned-fake-embed".into());
    let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_long(|| !s.is_busy());
    let inputs = inputs.lock().unwrap();
    assert_eq!(inputs.len(), 1);
    assert!(!inputs[0].contains("NEXT:"));
    let page = s
        .journal_page("page".into(), &m.session_id, &m.generation, 0, 10)
        .unwrap();
    assert_eq!(page.entries.len(), 1);
    let detail = s
        .journal(
            "detail".into(),
            &m.session_id,
            &m.generation,
            &page.entries[0].entry_id,
        )
        .unwrap()
        .journal;
    assert_eq!(detail["rawReply"], raw);
    assert_eq!(detail["action"]["body"], inputs[0]);
    assert_eq!(detail["actionReceipt"]["status"], "applied");
    s.shared.store.verify(&m.session_id).unwrap();
}

#[test]
fn authored_action_skipped_saved_decision_never_changes_controls() {
    let (_d, s, id, generation) = action_setup(8, 3);
    let epoch = arm(&s);
    dispatch(
        &s,
        epoch,
        "This saved adjustment will be explicitly skipped.\nNEXT: TUNE leak 0.35",
    );
    s.pause("pause".into(), &id, &generation).unwrap();
    s.worker_boundary(epoch).unwrap();
    let prepared = s
        .get("pending".into(), None)
        .unwrap()
        .summary
        .unwrap()
        .pending_application
        .unwrap();
    s.skip(
        "skip".into(),
        &id,
        &generation,
        Some(prepared.entry_id),
        Some(prepared.attempt_id),
    )
    .unwrap();
    let state = action_state(&s);
    assert_eq!(state["state"]["controls"]["leak"], 0.65);
    assert_eq!(state["state"]["decisionCount"], 0);
    let page = s
        .journal_page("page".into(), &id, &generation, 0, 10)
        .unwrap();
    assert_eq!(page.entries[0].status, "skipped");
    assert!(page.entries[0].action_receipt.is_none());
    s.shared.store.verify(&id).unwrap();
}

#[test]
fn authored_action_rejection_is_visible_without_losing_saved_writing() {
    let (_d, s, id, generation) = action_setup(4, 3);
    let epoch = arm(&s);
    dispatch(&s, epoch, "This prose is still feedback even though its requested action is invalid.\nNEXT: TUNE leak 9");
    assert!(action_state(&s)["pending"]["decision"]["rejection"].is_string());
    drive(&s, epoch);
    drive(&s, epoch);
    let state = action_state(&s);
    assert_eq!(state["state"]["controls"]["leak"], 0.65);
    assert_eq!(state["state"]["rejectedCount"], 1);
    let page = s
        .journal_page("page".into(), &id, &generation, 0, 10)
        .unwrap();
    assert_eq!(page.entries[0].status, "applied");
    let detail = s
        .journal("detail".into(), &id, &generation, &page.entries[0].entry_id)
        .unwrap()
        .journal;
    assert_eq!(detail["actionReceipt"]["status"], "rejected");
    assert!(detail["actionReceipt"]["rejection"].is_string());
    s.shared.store.verify(&id).unwrap();
}

#[test]
fn authored_action_only_reply_skips_embedding_and_applies_zero_text_feedback() {
    let d = tempfile::tempdir().unwrap();
    let calls = Arc::new(AtomicU64::new(0));
    let seen = calls.clone();
    let raw = "NEXT: TUNE leak 0.35";
    let s = SustainedState::with_provider_and_embedder(
        d.path().join("store"),
        Arc::new(move |_, _, _, _, _, _| Ok(reply(raw))),
        Arc::new(move |_, _, _, _, _| {
            seen.fetch_add(1, Ordering::SeqCst);
            Err("An action-only reply must not request an embedding".into())
        }),
    );
    let mut cfg = action_config(4, 3);
    cfg.language = model_config().language;
    cfg.embedding_model = Some("owned-fake-embed".into());
    let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_long(|| !s.is_busy());
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    let state = action_state(&s);
    assert_eq!(state["state"]["controls"]["leak"], 0.35);
    let page = s
        .journal_page("page".into(), &m.session_id, &m.generation, 0, 10)
        .unwrap();
    assert_eq!(page.entries.len(), 1);
    let detail = s
        .journal(
            "detail".into(),
            &m.session_id,
            &m.generation,
            &page.entries[0].entry_id,
        )
        .unwrap()
        .journal;
    assert_eq!(detail["rawReply"], raw);
    assert_eq!(detail["action"]["body"], "");
    assert_eq!(detail["semanticVector"], serde_json::json!(vec![0.0; 48]));
    assert!(detail["feedbackProvenance"].is_null());
    assert_eq!(detail["actionReceipt"]["status"], "applied");
    s.shared.store.verify(&m.session_id).unwrap();
}

#[test]
fn authored_action_stopped_before_application_remains_visibly_unapplied() {
    let (_d, s, id, generation) = action_setup(8, 3);
    let epoch = arm(&s);
    dispatch(&s, epoch, "This pulse will be saved, then the session stopped before application.\nNEXT: PULSE uniform 1");
    s.pause("pause".into(), &id, &generation).unwrap();
    s.worker_boundary(epoch).unwrap();
    s.stop("stop".into(), &id, &generation).unwrap();
    let summary = s.get("stopped".into(), None).unwrap().summary.unwrap();
    assert_eq!(summary.phase, "stopped");
    assert!(!summary.can_start);
    let actions = serde_json::to_value(summary.actions.unwrap()).unwrap();
    assert_eq!(actions["state"]["decisionCount"], 0);
    assert!(actions["state"]["latestReceipt"].is_null());
    assert_eq!(actions["pending"]["phase"], "prepared");
    assert!(!drive(&s, epoch));
    let page = s
        .journal_page("page".into(), &id, &generation, 0, 10)
        .unwrap();
    assert_eq!(page.entries[0].status, "savedPendingApplication");
    assert!(page.entries[0].first_applied_step.is_none());
    assert!(page.entries[0].action_receipt.is_none());
    let detail = s
        .journal("detail".into(), &id, &generation, &page.entries[0].entry_id)
        .unwrap()
        .journal;
    assert!(detail["action"]["request"].is_object());
    assert!(detail.get("actionReceipt").is_none());
    s.shared.store.verify(&id).unwrap();
}
