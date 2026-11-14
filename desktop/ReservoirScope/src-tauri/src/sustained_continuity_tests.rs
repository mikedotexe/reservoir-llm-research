use super::*;
use reservoir_core::sustained::{SustainedActionMode, SustainedCheckInSchedule};

const QUESTION: &str = "How does the probe change the next observation?";
fn inquiry_config(steps: u64, turn: u64) -> SustainedConfig {
    SustainedConfig {
        action_mode: Some(SustainedActionMode::AuthoredV3),
        prompt_version: SustainedPromptVersion::ActionJournalV3,
        ..config(steps, turn)
    }
}
fn probe_reply(withhold: bool) -> String {
    let mut vector = vec![0.0; 48];
    vector[0] = 0.5;
    format!(
        "I will keep a question available for later observations.\nINQUIRY: OPEN both {}\nWITHHOLD_RESERVOIR_INPUT={withhold}\nNEXT: PROBE {}",
        serde_json::to_string(QUESTION).unwrap(), serde_json::to_string(&vector).unwrap()
    )
}
fn response(text: &str) -> LanguageResponse {
    LanguageResponse {
        text: text.into(),
        ..answer()
    }
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
fn next_provider(
    s: &SustainedState,
    epoch: u64,
) -> Box<reservoir_core::sustained::SustainedPendingLanguage> {
    for _ in 0..5000 {
        match s.worker_boundary(epoch).unwrap() {
            Work::Provider(p, _) => return p,
            Work::Continue(_) => {}
            _ => panic!("expected a surface-fixture writing boundary"),
        }
    }
    panic!("writing boundary not reached")
}
fn dispatch(s: &SustainedState, epoch: u64, text: &str) {
    let p = next_provider(s, epoch);
    s.settle(epoch, p.attempt_id, Ok(response(text)), None, 1)
        .unwrap();
}

#[test]
fn v3_host_configuration_keeps_exact_version_pair_and_empty_continuity() {
    let cfg = inquiry_config(13, 3);
    let serialized = serde_json::to_value(&cfg).unwrap();
    assert_eq!(serialized["actionMode"], "authored-v3");
    assert_eq!(serialized["promptVersion"], "reservoir-journal-actions-v3");
    let roundtrip: SustainedConfig = serde_json::from_value(serialized).unwrap();
    roundtrip.validate().unwrap();
    for prompt in [
        SustainedPromptVersion::ActionJournalV1,
        SustainedPromptVersion::ActionJournalV2,
    ] {
        assert!(SustainedConfig {
            prompt_version: prompt,
            ..cfg.clone()
        }
        .validate()
        .is_err());
    }
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    s.create("create".into(), cfg).unwrap();
    let initial = state(&s);
    assert_eq!(
        initial["state"]["continuity"]["meaningfulReceipts"],
        serde_json::json!([])
    );
    assert!(initial["state"]["continuity"]["activeInquiry"].is_null());
}

#[test]
fn inquiry_and_probe_wait_for_save_then_recover_and_export_once() {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    let m = s
        .create("create".into(), inquiry_config(12, 3))
        .unwrap()
        .summary
        .unwrap();
    let epoch = arm(&s);
    dispatch(
        &s,
        epoch,
        "The earlier journal entry supplies local evidence.\nNEXT: NONE",
    );
    until(&s, epoch, |a| a.engine.step() == 4);
    let raw = probe_reply(true);
    dispatch(&s, epoch, &raw);
    let pending = state(&s);
    assert_eq!(
        pending["pending"]["decision"]["inquiry"]["request"]["question"],
        QUESTION
    );
    assert_eq!(pending["pending"]["decision"]["request"]["kind"], "probe");
    assert!(pending["state"]["continuity"]["activeInquiry"].is_null());
    s.shared.store.fail_next(3);
    assert!(s.worker_boundary(epoch).is_err());
    assert_eq!(state(&s)["pending"]["durablePrepared"], false);
    assert!(state(&s)["state"]["continuity"]["activeInquiry"].is_null());
    s.retry_save("save".into(), &m.session_id, &m.generation)
        .unwrap();
    assert_eq!(state(&s)["pending"]["durablePrepared"], true);
    let epoch = arm(&s);
    assert!(drive(&s, epoch));
    s.pause("pause".into(), &m.session_id, &m.generation)
        .unwrap();
    drive(&s, epoch);
    let applied = state(&s);
    let c = &applied["state"]["continuity"];
    assert_eq!(applied["state"]["decisionCount"], 2);
    assert_eq!(c["activeInquiry"]["question"], QUESTION);
    assert_eq!(
        c["activeInquiry"]["history"][0]["excerpt"],
        "The earlier journal entry supplies local evidence."
    );
    assert_eq!(c["meaningfulReceipts"].as_array().unwrap().len(), 1);
    let receipt = &applied["state"]["latestReceipt"];
    assert_eq!(receipt["inquiry"]["status"], "opened");
    assert_eq!(
        receipt["probe"]["requestedVector"],
        receipt["probe"]["appliedVector"]
    );
    assert_eq!(
        receipt["probe"]["stateDeltaVector"]
            .as_array()
            .unwrap()
            .len(),
        32
    );
    let saved = s.shared.store.verify(&m.session_id).unwrap();
    assert_eq!(saved.checkpoint.state.step, 7);
    assert!(saved.checkpoint.state.held_vector.iter().all(|x| *x == 0.0));
    let export = d.path().join("exports");
    fs::create_dir(&export).unwrap();
    let report = s
        .export(&m.session_id, &m.generation, None, &export, &[])
        .unwrap()
        .1;
    assert_eq!(report.checkpoint_sha256, saved.report.checkpoint_sha256);
    s.stop("stop".into(), &m.session_id, &m.generation).unwrap();
    let saved = s.shared.store.verify(&m.session_id).unwrap();
    let restored = s
        .resume(
            "resume".into(),
            &m.session_id,
            &saved.manifest.generation,
            &saved.manifest.revision,
        )
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(
        serde_json::to_value(restored.actions.unwrap()).unwrap()["state"],
        applied["state"]
    );
    let epoch = arm(&s);
    let p = next_provider(&s, epoch);
    assert!(p.prompt.contains(QUESTION));
    assert!(p
        .prompt
        .contains("The earlier journal entry supplies local evidence."));
    assert!(p.prompt.contains("MEANINGFUL INTERVENTIONS"));
    assert_eq!(state(&s)["state"]["decisionCount"], 2);
    s.settle(
        epoch,
        p.attempt_id,
        Ok(response(
            "Continue with newer journal evidence.\nINQUIRY: CONTINUE\nNEXT: NONE",
        )),
        None,
        1,
    )
    .unwrap();
    until(&s, epoch, |a| a.engine.step() == 10);
    let refreshed = state(&s);
    assert_eq!(
        refreshed["state"]["continuity"]["activeInquiry"]["continuationCount"],
        1
    );
    assert_eq!(
        refreshed["state"]["continuity"]["activeInquiry"]["baseline"],
        c["activeInquiry"]["baseline"]
    );
    assert_eq!(
        refreshed["state"]["continuity"]["activeInquiry"]["history"]
            .as_array()
            .unwrap()
            .len(),
        2
    );
}

#[test]
fn v3_scripted_cycle_keeps_omitted_inquiry_then_closes_and_preserves_interventions() {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    let m = s
        .create("create".into(), inquiry_config(13, 3))
        .unwrap()
        .summary
        .unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_long(|| !s.is_busy());
    let final_state = state(&s);
    let c = &final_state["state"]["continuity"];
    assert_eq!(final_state["state"]["decisionCount"], 4);
    assert_eq!(final_state["state"]["controls"]["leak"], 0.65);
    assert!(c["activeInquiry"].is_null());
    assert_eq!(c["latestInquiryReceipt"]["status"], "closed");
    assert_eq!(c["meaningfulReceipts"].as_array().unwrap().len(), 3);
    let page = s
        .journal_page("page".into(), &m.session_id, &m.generation, 0, 10)
        .unwrap();
    let mut statuses = Vec::new();
    for entry in page.entries.iter().rev() {
        let detail = s
            .journal(
                "detail".into(),
                &m.session_id,
                &m.generation,
                &entry.entry_id,
            )
            .unwrap()
            .journal;
        statuses.push(
            detail["actionReceipt"]["inquiry"]["status"]
                .as_str()
                .map(str::to_owned),
        );
        assert!(!detail["action"]["body"]
            .as_str()
            .unwrap()
            .contains("INQUIRY:"));
    }
    assert_eq!(
        statuses,
        [
            Some("opened".into()),
            Some("continued".into()),
            None,
            Some("closed".into())
        ]
    );
    s.shared.store.verify(&m.session_id).unwrap();
}

#[test]
fn passive_checkin_neither_closes_inquiry_nor_applies_probe() {
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
            ..inquiry_config(100, 3)
        };
        let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
        let epoch = arm(&s);
        dispatch(&s, epoch, &probe_reply(true));
        until(&s, epoch, |a| a.engine.step() == 4);
        let before = state(&s)["state"]["continuity"]["activeInquiry"].clone();
        {
            let mut g = s.lock().unwrap();
            let a = g.active.as_mut().unwrap();
            a.manifest.elapsed_millis = 1000;
            a.last_accounted = Instant::now();
        }
        let p = next_provider(&s, epoch);
        assert!(p.check_in.is_some());
        let raw = format!(
            "This is ordinary check-in prose.\nINQUIRY: CLOSE\nNEXT: PROBE {}",
            serde_json::to_string(&vec![0.0; 48]).unwrap()
        );
        assert_eq!(s.feedback_text_for(epoch, p.attempt_id, &raw).unwrap(), raw);
        s.settle(epoch, p.attempt_id, Ok(response(&raw)), None, 1)
            .unwrap();
        while drive(&s, epoch) {}
        let after = state(&s);
        assert_eq!(after["state"]["decisionCount"], 1);
        assert_eq!(after["state"]["continuity"]["activeInquiry"], before);
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
        assert_eq!(detail["text"], raw);
        s.shared.store.verify(&m.session_id).unwrap();
    }
}

#[test]
fn supplied_memory_evidence_matches_v3_prefix_for_ordinary_and_telemetry_prompts() {
    let body = format!("{}é retained suffix outside the prefix", "a".repeat(2047));
    let raw = format!("{body}\nNEXT: NONE");
    for (mode, version) in [
        (
            SustainedActionMode::AuthoredV1,
            SustainedPromptVersion::ActionJournalV1,
        ),
        (
            SustainedActionMode::AuthoredV2,
            SustainedPromptVersion::ActionJournalV2,
        ),
        (
            SustainedActionMode::AuthoredV3,
            SustainedPromptVersion::ActionJournalV3,
        ),
    ] {
        let d = tempfile::tempdir().unwrap();
        let s = SustainedState::new(d.path().join("store"));
        let cfg = SustainedConfig {
            action_mode: Some(mode),
            prompt_version: version,
            check_in_schedule: Some(SustainedCheckInSchedule {
                interval_seconds: 60,
                end_after_seconds: 60,
                prompt: "Continue our conversation.".into(),
                include_telemetry: true,
            }),
            maximum_duration_seconds: 60,
            maximum_turns: 1000,
            ..config(1000, 3)
        };
        let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
        let epoch = arm(&s);
        dispatch(&s, epoch, &raw);
        until(&s, epoch, |a| a.engine.step() == 4);
        let p = next_provider(&s, epoch);
        let earlier = p.memory.as_ref().unwrap();
        let projection = crate::sustained::actions::memory_evidence(earlier, version);
        let expected = if mode == SustainedActionMode::AuthoredV3 {
            "a".repeat(2047)
        } else {
            body.clone()
        };
        assert_eq!(projection["suppliedText"], expected);
        assert_eq!(
            projection["suppliedTextSha256"],
            crate::files::digest(expected.as_bytes())
        );
        assert_eq!(projection["text"], raw);
        if mode == SustainedActionMode::AuthoredV3 {
            assert!(p
                .prompt
                .contains(&serde_json::to_string(&expected).unwrap()));
            assert!(!p.prompt.contains("retained suffix outside the prefix"));
            assert_eq!(projection["suppliedTextTruncated"], true);
            assert_eq!(
                projection["fullBodySha256"],
                crate::files::digest(body.as_bytes())
            );
            assert_eq!(projection["fullBodyBytes"], body.len());
            let mut conversational_memory = earlier.clone();
            conversational_memory.entry.body = None;
            let fallback =
                crate::sustained::actions::memory_evidence(&conversational_memory, version);
            assert_eq!(fallback["suppliedText"], expected);
            assert_eq!(
                fallback["fullBodySha256"],
                crate::files::digest(raw.as_bytes())
            );
        } else {
            assert!(p.prompt.contains(&body));
            assert!(projection.get("suppliedTextTruncated").is_none());
            assert!(projection.get("fullBodySha256").is_none());
        }
        s.settle(epoch, p.attempt_id, Ok(response(&raw)), None, 1)
            .unwrap();
        until(&s, epoch, |a| a.engine.step() == 7);
        {
            let mut g = s.lock().unwrap();
            let a = g.active.as_mut().unwrap();
            a.manifest.elapsed_millis = 60_000;
            a.last_accounted = Instant::now();
        }
        let check_in = next_provider(&s, epoch);
        assert!(check_in.check_in.is_some());
        s.settle(
            epoch,
            check_in.attempt_id,
            Ok(response("A passive conversation.")),
            None,
            1,
        )
        .unwrap();
        while drive(&s, epoch) {}
        let page = s
            .journal_page("page".into(), &m.session_id, &m.generation, 0, 10)
            .unwrap();
        for entry in page.entries.iter().take(2) {
            let detail = s
                .journal(
                    "detail".into(),
                    &m.session_id,
                    &m.generation,
                    &entry.entry_id,
                )
                .unwrap()
                .journal;
            assert_eq!(detail["memory"]["suppliedText"], expected);
            assert_eq!(
                detail["memory"]["suppliedTextSha256"],
                crate::files::digest(expected.as_bytes())
            );
            let prompt = detail["prompt"].as_str().unwrap();
            if mode == SustainedActionMode::AuthoredV3 {
                assert!(prompt.contains(&serde_json::to_string(&expected).unwrap()));
                assert!(!prompt.contains("retained suffix outside the prefix"));
            } else {
                assert!(prompt.contains(&body));
            }
        }
        s.shared.store.verify(&m.session_id).unwrap();
    }
}

#[test]
fn withheld_probe_and_inquiry_skip_encoding_but_keep_both_applied_choices() {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::with_provider_and_embedder(
        d.path().join("store"),
        Arc::new(|_, _, _, _, _, _| Ok(response(&probe_reply(true)))),
        Arc::new(|_, _, _, _, _| panic!("withheld input must not call the embedder")),
    );
    let cfg = SustainedConfig {
        language: model_config().language,
        embedding_model: Some("owned-fake-embedding".into()),
        ..inquiry_config(4, 3)
    };
    let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_long(|| !s.is_busy());
    let applied = state(&s);
    assert_eq!(
        applied["state"]["latestReceipt"]["request"]["kind"],
        "probe"
    );
    assert_eq!(
        applied["state"]["continuity"]["activeInquiry"]["question"],
        QUESTION
    );
    let saved = s.shared.store.verify(&m.session_id).unwrap();
    assert!(saved.checkpoint.state.held_vector.iter().all(|x| *x == 0.0));
}

#[test]
fn encoding_retry_retains_inquiry_and_probe_without_regenerating_or_reapplying() {
    let d = tempfile::tempdir().unwrap();
    let root = d.path().join("store");
    let writers = Arc::new(AtomicU64::new(0));
    let calls = writers.clone();
    let raw = probe_reply(false);
    let received = raw.clone();
    let s = SustainedState::with_provider_and_embedder(
        root.clone(),
        Arc::new(move |_, _, _, _, _, _| {
            calls.fetch_add(1, Ordering::SeqCst);
            Ok(response(&received))
        }),
        Arc::new(|_, _, text, _, _| {
            assert_eq!(
                text,
                "I will keep a question available for later observations."
            );
            Err("owned encoding failure".into())
        }),
    );
    let cfg = SustainedConfig {
        language: model_config().language,
        embedding_model: Some("owned-fake-embedding".into()),
        maximum_turns: 1,
        ..inquiry_config(4, 1)
    };
    let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_long(|| !s.lock().unwrap().active.as_ref().unwrap().worker_active);
    let blocked = s.get("blocked".into(), None).unwrap().summary.unwrap();
    assert_eq!(blocked.phase, "embeddingBlocked");
    assert_eq!(blocked.pending_embedding.unwrap().response_text, raw);
    assert!(state(&s)["state"]["continuity"]["activeInquiry"].is_null());
    let saved = s.shared.store.verify(&m.session_id).unwrap();
    let resumed = SustainedState::with_provider_and_embedder(
        root,
        Arc::new(|_, _, _, _, _, _| panic!("retry must not regenerate")),
        Arc::new(|_, model, text, _, _| {
            assert_eq!(
                text,
                "I will keep a question available for later observations."
            );
            Ok(crate::model_transport::EmbeddingReceipt {
                vector: (0..64).map(|i| (i as f64 * 0.17).sin()).collect(),
                model: model.into(),
                digest: None,
            })
        }),
    );
    let restored = resumed
        .resume(
            "restore".into(),
            &m.session_id,
            &saved.manifest.generation,
            &saved.manifest.revision,
        )
        .unwrap()
        .summary
        .unwrap();
    resumed
        .retry_embedding("retry".into(), &m.session_id, &restored.generation)
        .unwrap();
    wait_long(|| {
        !resumed
            .lock()
            .unwrap()
            .active
            .as_ref()
            .unwrap()
            .worker_active
    });
    let pending = state(&resumed);
    assert_eq!(
        pending["pending"]["decision"]["inquiry"]["request"]["question"],
        QUESTION
    );
    assert_eq!(pending["state"]["decisionCount"], 0);
    assert!(resumed
        .retry_embedding("duplicate".into(), &m.session_id, &restored.generation)
        .is_err());
    resumed
        .start("apply".into(), &m.session_id, &restored.generation)
        .unwrap();
    wait_long(|| {
        !resumed
            .lock()
            .unwrap()
            .active
            .as_ref()
            .unwrap()
            .worker_active
    });
    assert_eq!(writers.load(Ordering::SeqCst), 1);
    let applied = state(&resumed);
    assert_eq!(applied["state"]["decisionCount"], 1);
    assert_eq!(
        applied["state"]["continuity"]["activeInquiry"]["question"],
        QUESTION
    );
    assert_eq!(
        applied["state"]["continuity"]["meaningfulReceipts"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
    resumed.shared.store.verify(&m.session_id).unwrap();
}
