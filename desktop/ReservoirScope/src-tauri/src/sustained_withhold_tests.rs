use super::*;
use reservoir_core::sustained::{SustainedActionMode, SustainedCheckInSchedule};

fn withholding_config(steps: u64, turn: u64) -> SustainedConfig {
    SustainedConfig {
        action_mode: Some(SustainedActionMode::AuthoredV2),
        prompt_version: SustainedPromptVersion::ActionJournalV2,
        ..config(steps, turn)
    }
}
fn setup_withholding(steps: u64, turn: u64) -> (tempfile::TempDir, SustainedState, String, String) {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    let m = s
        .create("create".into(), withholding_config(steps, turn))
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
    let p = next_provider(s, epoch);
    s.settle(epoch, p.attempt_id, Ok(reply(text)), None, 1)
        .unwrap();
}
fn next_provider(
    s: &SustainedState,
    epoch: u64,
) -> Box<reservoir_core::sustained::SustainedPendingLanguage> {
    for _ in 0..5000 {
        match s.worker_boundary(epoch).unwrap() {
            Work::Provider(p, _) => return p,
            Work::Continue(_) => {}
            Work::Done => panic!("session held before the next provider boundary"),
        }
    }
    panic!("bounded drive did not reach provider boundary")
}
fn state(s: &SustainedState) -> serde_json::Value {
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
fn authored_v2_requires_matching_prompt_without_changing_v1_identity() {
    let mut cfg = withholding_config(8, 3);
    cfg.validate().unwrap();
    assert_eq!(
        serde_json::to_value(&cfg).unwrap()["actionMode"],
        "authored-v2"
    );
    cfg.prompt_version = SustainedPromptVersion::ActionJournalV1;
    assert!(cfg.validate().is_err());
    cfg.action_mode = Some(SustainedActionMode::AuthoredV1);
    cfg.validate().unwrap();
    assert_eq!(
        serde_json::to_value(&cfg).unwrap()["actionMode"],
        "authored-v1"
    );
    cfg.prompt_version = SustainedPromptVersion::ActionJournalV2;
    assert!(cfg.validate().is_err());
}

#[test]
fn withholding_replaces_previous_input_only_after_durable_preparation_and_recovers_once() {
    let (d, s, id, generation) = setup_withholding(12, 3);
    let epoch = arm(&s);
    dispatch(
        &s,
        epoch,
        "The first entry supplies numerical text feedback.\nNEXT: NONE",
    );
    until(&s, epoch, |a| a.engine.step() == 4);
    let before = s
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .checkpoint()
        .state
        .held_vector
        .clone();
    assert!(before.iter().any(|x| *x != 0.0));
    let raw = "Keep this entry as writing without numerical text input.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: PULSE alternating 0.5";
    dispatch(&s, epoch, raw);
    let pending = state(&s);
    assert_eq!(pending["pending"]["phase"], "saving");
    assert_eq!(
        pending["pending"]["decision"]["reservoirInput"]["disposition"],
        "withhold"
    );
    s.shared.store.fail_next(3);
    assert!(s.worker_boundary(epoch).is_err());
    assert_eq!(state(&s)["pending"]["durablePrepared"], false);
    assert_eq!(
        s.lock()
            .unwrap()
            .active
            .as_ref()
            .unwrap()
            .engine
            .checkpoint()
            .state
            .held_vector,
        before
    );
    s.retry_save("retry".into(), &id, &generation).unwrap();
    let prepared = state(&s);
    assert_eq!(prepared["pending"]["durablePrepared"], true);
    assert_eq!(prepared["state"]["decisionCount"], 1);
    let epoch = arm(&s);
    assert!(drive(&s, epoch));
    s.pause("pause".into(), &id, &generation).unwrap();
    drive(&s, epoch);
    let verified = s.shared.store.verify(&id).unwrap();
    assert_eq!(verified.checkpoint.state.step, 7);
    assert!(verified
        .checkpoint
        .state
        .held_vector
        .iter()
        .all(|x| *x == 0.0));
    let received = state(&s);
    assert_eq!(received["state"]["decisionCount"], 2);
    assert_eq!(received["state"]["latestReceipt"]["status"], "applied");
    assert_eq!(
        received["state"]["latestReceipt"]["reservoirInput"]["disposition"],
        "withhold"
    );
    let page = s
        .journal_page("page".into(), &id, &generation, 0, 10)
        .unwrap();
    let detail = s
        .journal("detail".into(), &id, &generation, &page.entries[0].entry_id)
        .unwrap()
        .journal;
    assert_eq!(detail["rawReply"], raw);
    assert_eq!(
        detail["action"]["body"],
        "Keep this entry as writing without numerical text input."
    );
    assert_eq!(detail["semanticVector"], serde_json::json!(vec![0.0; 48]));
    assert_eq!(detail["actionReceipt"]["appliedStep"], 7);
    let exports = d.path().join("exports");
    fs::create_dir(&exports).unwrap();
    let (_, exported) = s.export(&id, &generation, None, &exports, &[]).unwrap();
    assert_eq!(
        exported.checkpoint_sha256,
        verified.report.checkpoint_sha256
    );
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
        serde_json::to_value(restored.actions.unwrap()).unwrap()["state"],
        received["state"]
    );
    let epoch = arm(&s);
    let p = next_provider(&s, epoch);
    assert!(p
        .prompt
        .contains("Keep this entry as writing without numerical text input."));
    assert!(p.prompt.contains("withhold"));
    assert_eq!(state(&s)["state"]["decisionCount"], 2);
    s.settle(
        epoch,
        p.attempt_id,
        Ok(reply(
            "Send numerical input again.\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: NONE",
        )),
        None,
        1,
    )
    .unwrap();
    until(&s, epoch, |a| a.engine.step() == 10);
    s.pause("last-pause".into(), &id, &restored.generation)
        .unwrap();
    drive(&s, epoch);
    let saved = s.shared.store.verify(&id).unwrap();
    assert!(saved.checkpoint.state.held_vector.iter().any(|x| *x != 0.0));
    assert_eq!(state(&s)["state"]["decisionCount"], 3);
    assert_eq!(
        state(&s)["state"]["latestReceipt"]["reservoirInput"]["disposition"],
        "send"
    );
}

#[test]
fn withheld_nonempty_body_skips_embedding_and_keeps_memory_and_control_action() {
    let d = tempfile::tempdir().unwrap();
    let calls = Arc::new(AtomicU64::new(0));
    let seen = calls.clone();
    let raw = "These retained words are deliberately withheld from numerical input.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: TUNE leak 0.35";
    let s = SustainedState::with_provider_and_embedder(
        d.path().join("store"),
        Arc::new(move |_, _, _, _, _, _| Ok(reply(raw))),
        Arc::new(move |_, _, _, _, _| {
            seen.fetch_add(1, Ordering::SeqCst);
            Err("Withheld input must not call the embedding provider".into())
        }),
    );
    let mut cfg = withholding_config(4, 3);
    cfg.language = model_config().language;
    cfg.embedding_model = Some("owned-fake-embed".into());
    let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_long(|| !s.is_busy());
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    assert_eq!(state(&s)["state"]["controls"]["leak"], 0.35);
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
    assert_eq!(
        detail["action"]["body"],
        "These retained words are deliberately withheld from numerical input."
    );
    assert_eq!(detail["semanticVector"], serde_json::json!(vec![0.0; 48]));
    assert!(detail["feedbackProvenance"].is_null());
    assert_eq!(detail["actionReceipt"]["status"], "applied");
    assert_eq!(
        detail["actionReceipt"]["reservoirInput"]["disposition"],
        "withhold"
    );
    s.shared.store.verify(&m.session_id).unwrap();
}

#[test]
fn rejected_input_directive_withholds_without_suppressing_valid_next_action() {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::with_provider_and_embedder(
        d.path().join("store"),
        Arc::new(move |_, _, _, _, _, _| {
            Ok(reply("The input flag is malformed.\nWITHHOLD_RESERVOIR_INPUT=perhaps\nNEXT: TUNE leak 0.35"))
        }),
        Arc::new(move |_, _, _, _, _| panic!("Rejected input directive must not call embedder")),
    );
    let mut cfg = withholding_config(4, 3);
    cfg.language = model_config().language;
    cfg.embedding_model = Some("owned-fake-embed".into());
    let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_long(|| !s.is_busy());
    let receipt = state(&s)["state"]["latestReceipt"].clone();
    assert_eq!(receipt["status"], "applied");
    assert_eq!(receipt["reservoirInput"]["disposition"], "rejected");
    assert!(receipt["reservoirInput"]["rejection"].is_string());
    assert_eq!(state(&s)["state"]["controls"]["leak"], 0.35);
    let saved = s.shared.store.verify(&m.session_id).unwrap();
    assert!(saved.checkpoint.state.held_vector.iter().all(|x| *x == 0.0));
}

#[test]
fn embedding_resumes_on_next_send_and_withheld_body_still_returns_as_memory() {
    let d = tempfile::tempdir().unwrap();
    let attempts = Arc::new(AtomicU64::new(0));
    let prompts = Arc::new(Mutex::new(Vec::new()));
    let seen_prompts = prompts.clone();
    let inputs = Arc::new(Mutex::new(Vec::new()));
    let seen_inputs = inputs.clone();
    let s = SustainedState::with_provider_and_embedder(
        d.path().join("store"),
        Arc::new(move |_, prompt, _, _, _, _| {
            seen_prompts.lock().unwrap().push(prompt.to_owned());
            Ok(reply(match attempts.fetch_add(1, Ordering::SeqCst) {
                0 => "First numerical input.\nNEXT: NONE",
                1 => "Retained words without numerical input.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE",
                _ => "Numerical input resumes.\nNEXT: NONE",
            }))
        }),
        Arc::new(move |_, model, text, _, _| {
            seen_inputs.lock().unwrap().push(text.to_owned());
            Ok(crate::model_transport::EmbeddingReceipt {
                vector: (0..64).map(|i| (i as f64 * 0.1).sin()).collect(),
                model: model.into(),
                digest: None,
            })
        }),
    );
    let mut cfg = withholding_config(10, 3);
    cfg.language = model_config().language;
    cfg.embedding_model = Some("owned-fake-embed".into());
    let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_long(|| !s.is_busy());
    assert_eq!(
        *inputs.lock().unwrap(),
        ["First numerical input.", "Numerical input resumes."]
    );
    let prompts = prompts.lock().unwrap();
    assert_eq!(prompts.len(), 3);
    assert!(prompts[2].contains("Retained words without numerical input."));
    let saved = s.shared.store.verify(&m.session_id).unwrap();
    assert!(saved.checkpoint.state.held_vector.iter().any(|x| *x != 0.0));
    assert_eq!(
        state(&s)["state"]["latestReceipt"]["reservoirInput"]["disposition"],
        "send"
    );
}

#[test]
fn v2_scripted_cycle_withholds_once_then_sends_and_restores_controls() {
    let (_d, s, id, generation) = setup_withholding(13, 3);
    s.start("start".into(), &id, &generation).unwrap();
    wait_long(|| !s.is_busy());
    assert_eq!(state(&s)["state"]["decisionCount"], 4);
    assert_eq!(state(&s)["state"]["controls"]["leak"], 0.65);
    let page = s
        .journal_page("page".into(), &id, &generation, 0, 10)
        .unwrap();
    let mut dispositions = Vec::new();
    for index in page.entries.iter().rev() {
        let detail = s
            .journal("detail".into(), &id, &generation, &index.entry_id)
            .unwrap()
            .journal;
        let disposition = detail["actionReceipt"]["reservoirInput"]["disposition"]
            .as_str()
            .unwrap();
        dispositions.push(disposition.to_owned());
        assert!(!detail["action"]["body"]
            .as_str()
            .unwrap()
            .contains("WITHHOLD_RESERVOIR_INPUT"));
        if disposition == "withhold" {
            assert_eq!(detail["semanticVector"], serde_json::json!(vec![0.0; 48]));
        } else {
            assert!(detail["semanticVector"]
                .as_array()
                .unwrap()
                .iter()
                .any(|v| v.as_f64().unwrap() != 0.0));
        }
        if detail["memory"].is_object() {
            assert!(!detail["memory"]["suppliedText"]
                .as_str()
                .unwrap()
                .contains("WITHHOLD_RESERVOIR_INPUT"));
        }
    }
    assert_eq!(dispositions, ["send", "withhold", "send", "send"]);
    s.shared.store.verify(&id).unwrap();
}

#[test]
fn checkin_withholding_text_is_inert_and_replaces_held_zero_with_ordinary_feedback() {
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
            ..withholding_config(100, 3)
        };
        let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
        let epoch = arm(&s);
        dispatch(
            &s,
            epoch,
            "The ordinary entry is withheld.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: TUNE leak 0.35",
        );
        until(&s, epoch, |a| a.engine.step() == 4);
        {
            let mut g = s.lock().unwrap();
            let a = g.active.as_mut().unwrap();
            assert!(a
                .engine
                .checkpoint()
                .state
                .held_vector
                .iter()
                .all(|x| *x == 0.0));
            a.manifest.elapsed_millis = 1000;
            a.last_accounted = Instant::now();
        }
        let raw = "This conversational text remains numerical feedback.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: RELEASE";
        let mut received = false;
        for _ in 0..10 {
            match s.worker_boundary(epoch).unwrap() {
                Work::Provider(p, sampling) => {
                    assert!(p.check_in.is_some());
                    assert_eq!(s.feedback_text_for(epoch, p.attempt_id, raw).unwrap(), raw);
                    assert!(!s
                        .scripted_reply_for(epoch, &p)
                        .contains("WITHHOLD_RESERVOIR_INPUT"));
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
        assert_eq!(state(&s)["state"]["decisionCount"], 1);
        assert_eq!(state(&s)["state"]["controls"]["leak"], 0.35);
        let saved = s.shared.store.verify(&m.session_id).unwrap();
        assert!(saved.checkpoint.state.held_vector.iter().any(|x| *x != 0.0));
        let page = s
            .journal_page("page".into(), &m.session_id, &m.generation, 0, 10)
            .unwrap();
        let detail = s
            .journal(
                "detail".into(),
                &m.session_id,
                &m.generation,
                &page.entries[0].entry_id,
            )
            .unwrap()
            .journal;
        assert!(detail.get("action").is_none());
        assert!(detail.get("actionReceipt").is_none());
        assert_eq!(detail["text"], raw);
    }
}

#[test]
fn authored_v1_keeps_withholding_directive_as_ordinary_body_text() {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    let cfg = SustainedConfig {
        action_mode: Some(SustainedActionMode::AuthoredV1),
        prompt_version: SustainedPromptVersion::ActionJournalV1,
        ..config(4, 3)
    };
    let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
    let epoch = arm(&s);
    let body =
        "Historical mode still encodes this literal directive.\nWITHHOLD_RESERVOIR_INPUT=true";
    dispatch(&s, epoch, &format!("{body}\nNEXT: NONE"));
    assert!(state(&s)["pending"]["decision"]
        .get("reservoirInput")
        .is_none());
    while drive(&s, epoch) {}
    let page = s
        .journal_page("page".into(), &m.session_id, &m.generation, 0, 10)
        .unwrap();
    let detail = s
        .journal(
            "detail".into(),
            &m.session_id,
            &m.generation,
            &page.entries[0].entry_id,
        )
        .unwrap()
        .journal;
    assert_eq!(detail["action"]["body"], body);
    assert!(detail["action"].get("reservoirInput").is_none());
    assert!(detail["actionReceipt"].get("reservoirInput").is_none());
    let saved = s.shared.store.verify(&m.session_id).unwrap();
    assert!(saved.checkpoint.state.held_vector.iter().any(|x| *x != 0.0));
}
