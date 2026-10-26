use super::*;
use std::fs;
#[path = "sustained_arms.rs"]
mod arms;
#[path = "sustained_limit_tests.rs"]
mod limits;
#[path = "sustained_quota_tests.rs"]
mod natural_quota;
#[path = "sustained_prompt_evidence_tests.rs"]
mod prompt_evidence;
fn config(steps: u64, turn: u64) -> SustainedConfig {
    SustainedConfig {
        maximum_steps: steps,
        turn_every: turn,
        maximum_turns: 100,
        pace_ms: 100,
        ..Default::default()
    }
}
fn setup(steps: u64, turn: u64) -> (tempfile::TempDir, SustainedState, String, String) {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    let u = s.create("create".into(), config(steps, turn)).unwrap();
    let m = u.summary.unwrap();
    (d, s, m.session_id, m.generation)
}
fn arm(s: &SustainedState) -> u64 {
    let mut g = s.lock().unwrap();
    let a = g.active.as_mut().unwrap();
    a.run_requested = true;
    a.epoch += 1;
    a.manifest.phase = "running".into();
    s.shared.pause.store(false, Ordering::SeqCst);
    a.epoch
}
fn answer() -> LanguageResponse {
    LanguageResponse {
        text: "I notice a changing field and retain this observation for the next step.".into(),
        provider_model: None,
        stop_reason: Some("stop".into()),
        token_count: Some(18),
        provider_prompt_evaluation: None,
        complete: true,
    }
}
fn drive(s: &SustainedState, epoch: u64) -> bool {
    match s.worker_boundary(epoch).unwrap() {
        Work::Provider(p, _) => {
            s.settle(epoch, p.attempt_id, Ok(answer()), None, 1)
                .unwrap();
            true
        }
        Work::Continue(_) => true,
        Work::Done => false,
    }
}
fn until(s: &SustainedState, epoch: u64, predicate: impl Fn(&Active) -> bool) {
    for _ in 0..5000 {
        if predicate(s.lock().unwrap().active.as_ref().unwrap()) {
            return;
        }
        assert!(drive(s, epoch));
    }
    panic!("bounded drive did not reach condition")
}
#[test]
fn sustained_accelerated_1001_steps_rollover_replay_and_exact_export() {
    let (d, s, id, generation) = setup(1001, 30);
    let epoch = arm(&s);
    while drive(&s, epoch) {}
    let u = s.get("done".into(), None).unwrap();
    let m = u.summary.unwrap();
    assert_eq!(m.step, 1001);
    assert_eq!(m.durable_step, 1001);
    assert_eq!(m.journal_count, 33);
    assert_eq!(m.phase, "budgetReached");
    let v = s.shared.store.verify(&id).unwrap();
    assert!(v.manifest.segment_count > 100);
    assert_eq!(v.checkpoint.state.step, 1001);
    let page = s
        .journal_page("page".into(), &id, &generation, 0, 2)
        .unwrap();
    assert_eq!(page.entries[0].observed_step, 990);
    assert_eq!(page.entries[0].first_applied_step, Some(991));
    assert!(page.has_more);
    let detail = s
        .journal("detail".into(), &id, &generation, &page.entries[0].entry_id)
        .unwrap();
    assert_eq!(detail.journal["text"], answer().text);
    assert_eq!(detail.journal["requestStarted"], false);
    let export = d.path().join("exports");
    fs::create_dir(&export).unwrap();
    let report = s.export(&id, &generation, None, &export, &[]).unwrap().1;
    assert_eq!(report.manifest_sha256, v.report.manifest_sha256);
    assert!(s.export(&id, &generation, None, &export, &[]).is_err());
    assert!(s
        .export(&id, &generation, None, &s.shared.store.root, &[])
        .is_err());
}
#[test]
fn pause_before_dispatch_never_starts_request_and_saved_feedback_waits_for_start() {
    let (_d, s, id, generation) = setup(8, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_language().is_some());
    s.pause("pause".into(), &id, &generation).unwrap();
    assert!(matches!(s.worker_boundary(epoch).unwrap(), Work::Done));
    assert!(
        !s.lock()
            .unwrap()
            .active
            .as_ref()
            .unwrap()
            .engine
            .pending_language()
            .unwrap()
            .request_started
    );
    let epoch = arm(&s);
    let Work::Provider(p, _) = s.worker_boundary(epoch).unwrap() else {
        panic!()
    };
    s.pause("pause-inflight".into(), &id, &generation).unwrap();
    s.settle(epoch, p.attempt_id, Ok(answer()), None, 2)
        .unwrap();
    assert!(matches!(s.worker_boundary(epoch).unwrap(), Work::Done));
    let g = s.lock().unwrap();
    let a = g.active.as_ref().unwrap();
    assert_eq!(a.engine.step(), 3);
    assert!(a.engine.prepared_application().is_some());
    assert_eq!(a.committed.state.step, 3);
    assert!(a.catalog[0].first_applied_step.is_none());
    drop(g);
    let epoch = arm(&s);
    drive(&s, epoch);
    assert_eq!(
        s.lock()
            .unwrap()
            .active
            .as_ref()
            .unwrap()
            .engine
            .latest_frame()
            .unwrap()
            .application
            .as_ref()
            .unwrap()
            .applied_step,
        4
    );
}
#[test]
fn pending_journal_manifest_failure_retries_without_duplicate_commit_or_application() {
    let (_d, s, id, _) = setup(8, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_journal().is_some());
    s.shared.store.fail_next(3);
    assert!(s.worker_boundary(epoch).is_err());
    {
        let g = s.lock().unwrap();
        let a = g.active.as_ref().unwrap();
        assert!(a.engine.prepared_application().is_some());
        assert_eq!(a.catalog.len(), 0);
        assert_eq!(s.summary(a).journal_count, 0);
    }
    let generation = s.get("g".into(), None).unwrap().summary.unwrap().generation;
    s.retry_save("retry".into(), &id, &generation).unwrap();
    assert_eq!(s.lock().unwrap().active.as_ref().unwrap().catalog.len(), 1);
    let epoch = arm(&s);
    drive(&s, epoch);
    s.pause("pause".into(), &id, &generation).unwrap();
    drive(&s, epoch);
    let v = s.shared.store.verify(&id).unwrap();
    assert_eq!(v.checkpoint.state.latest_memory.unwrap().applied_step, 4);
    assert_eq!(v.manifest.journal_count, 1);
}
#[test]
fn uncommitted_segment_is_quarantined_when_explicit_skip_changes_pending_history() {
    let (_d, s, id, generation) = setup(10, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_language().is_some());
    let Work::Provider(p, _) = s.worker_boundary(epoch).unwrap() else {
        panic!()
    };
    s.shared.store.fail_next(3);
    assert!(s
        .settle(epoch, p.attempt_id, Ok(answer()), None, 1)
        .is_err());
    let entry = s
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .pending_journal()
        .unwrap()
        .entry
        .clone();
    s.skip(
        "skip".into(),
        &id,
        &generation,
        Some(entry.id),
        Some(entry.attempt_id),
    )
    .unwrap();
    let v = s.shared.store.verify(&id).unwrap();
    assert!(v
        .report
        .diagnostics
        .iter()
        .any(|s| s.contains("uncommitted")));
    assert!(matches!(v.checkpoint.state.phase, SustainedPhase::Ready));
}
#[test]
fn recovery_restores_exact_global_cursor_and_applies_saved_feedback_only_once() {
    let (d, s, id, generation) = setup(9, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_journal().is_some());
    s.pause("pause".into(), &id, &generation).unwrap();
    drive(&s, epoch);
    let before = s.shared.store.verify(&id).unwrap();
    assert!(matches!(
        before.checkpoint.state.phase,
        SustainedPhase::Prepared(_)
    ));
    let restored = SustainedState::new(d.path().join("store"));
    let u = restored
        .resume(
            "restore".into(),
            &id,
            &before.manifest.generation,
            &before.manifest.revision,
        )
        .unwrap();
    assert_eq!(u.summary.unwrap().step, 3);
    assert!(restored
        .lock()
        .unwrap()
        .active
        .as_mut()
        .unwrap()
        .engine
        .advance()
        .is_err());
    let epoch = arm(&restored);
    drive(&restored, epoch);
    let first = restored
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .latest_frame()
        .unwrap()
        .clone();
    assert_eq!(first.application.unwrap().applied_step, 4);
    drive(&restored, epoch);
    assert!(restored
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .latest_frame()
        .unwrap()
        .application
        .is_none());
    restored
        .pause(
            "p".into(),
            &id,
            &restored
                .get("g".into(), None)
                .unwrap()
                .summary
                .unwrap()
                .generation,
        )
        .unwrap();
    drive(&restored, epoch);
    restored.shared.store.verify(&id).unwrap();
}
#[test]
fn actual_owned_journal_memory_read_refuses_tamper_and_has_no_fallback() {
    let (_d, s, id, _) = setup(10, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.step() == 5);
    let entry = s.lock().unwrap().active.as_ref().unwrap().catalog[0]
        .entry_id
        .clone();
    fs::write(
        s.shared
            .store
            .path(&id)
            .unwrap()
            .join("journals")
            .join(format!("{entry}.json")),
        b"{}",
    )
    .unwrap();
    drive(&s, epoch);
    assert!(!drive(&s, epoch));
    let g = s.lock().unwrap();
    let a = g.active.as_ref().unwrap();
    assert_eq!(a.engine.step(), 6);
    assert!(a.engine.blocked().is_some());
    assert_eq!(a.catalog.len(), 1);
    assert!(!a.engine.blocked().unwrap().pending.request_started);
    assert!(a.engine.blocked().unwrap().pending.prompt.is_empty());
}
#[test]
fn clean_close_barrier_and_explicit_discard_remove_prepared_eligibility() {
    let (_d, s, id, generation) = setup(8, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_journal().is_some());
    s.pause("p".into(), &id, &generation).unwrap();
    drive(&s, epoch);
    assert!(!s.authorize_clean_close());
    assert!(s.finish_close(true).unwrap());
    s.cancel_close();
    let v = s.shared.store.verify(&id).unwrap();
    assert!(matches!(v.checkpoint.state.phase, SustainedPhase::Ready));
    assert!(v.checkpoint.state.latest_memory.is_none());
    let index = s.shared.store.journal_index(&id).unwrap();
    assert_eq!(index[0].status, "skipped");
    let guard = s.lock().unwrap();
    assert!(!s.authorize_clean_close());
    drop(guard);
    assert!(s.authorize_clean_close());
    assert!(s.get("closed".into(), None).is_err());
}
#[test]
fn stale_commands_invalid_config_and_full_width_checkpoint_values_fail_closed() {
    let (_d, s, id, generation) = setup(8, 3);
    assert!(s.pause("stale".into(), &id, "999").is_err());
    assert!(!s.shared.pause.load(Ordering::SeqCst));
    let mut c = config(9, 3);
    c.maximum_steps = 1_000_001;
    assert!(s.create("bad".into(), c).is_err());
    assert_eq!(
        s.get("g".into(), None).unwrap().summary.unwrap().generation,
        generation
    );
    let v = s.inspect("inspect".into(), &id).unwrap();
    assert!(v.checkpoint["state"]["specification"]["seed"].is_string());
    assert!(v.checkpoint["state"]["rngState"].is_string());
}
#[test]
fn final_attempt_budget_applies_saved_feedback_before_budget_pause() {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    let mut c = config(20, 3);
    c.maximum_turns = 1;
    s.create("c".into(), c).unwrap();
    let epoch = arm(&s);
    while drive(&s, epoch) {}
    let g = s.lock().unwrap();
    let a = g.active.as_ref().unwrap();
    assert_eq!(a.engine.step(), 4);
    assert_eq!(a.catalog.len(), 1);
    assert_eq!(a.catalog[0].first_applied_step, Some(4));
    assert_eq!(a.manifest.phase, "budgetReached");
}

#[test]
fn close_discard_failure_keeps_exit_blocked_until_decision_is_durable() {
    let (_d, s, id, generation) = setup(8, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_journal().is_some());
    s.pause("p".into(), &id, &generation).unwrap();
    drive(&s, epoch);
    s.shared.store.fail_next(3);
    assert!(s.finish_close(true).is_err());
    assert!(!s.shared.closing.load(Ordering::SeqCst));
    assert!(!s.finish_close(false).unwrap());
    let previous = s.shared.store.verify(&id).unwrap();
    assert!(matches!(
        previous.checkpoint.state.phase,
        SustainedPhase::Prepared(_)
    ));
    assert!(!s.authorize_clean_close());
    assert!(s.finish_close(true).unwrap());
    let committed = s.shared.store.verify(&id).unwrap();
    assert!(matches!(
        committed.checkpoint.state.phase,
        SustainedPhase::Ready
    ));
}

#[test]
fn journal_publish_failure_is_idempotent_and_cannot_authorize_feedback() {
    let (_d, s, id, generation) = setup(8, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_journal().is_some());
    let entry = s
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .pending_journal()
        .unwrap()
        .entry
        .clone();
    s.shared.store.fail_next(2);
    assert!(s.worker_boundary(epoch).is_err());
    let path = s
        .shared
        .store
        .path(&id)
        .unwrap()
        .join("journals")
        .join(format!("{}.json", entry.id));
    let exact = fs::read(&path).unwrap();
    {
        let g = s.lock().unwrap();
        let a = g.active.as_ref().unwrap();
        assert!(a.engine.pending_journal().is_some());
        assert!(a.engine.prepared_application().is_none());
        assert!(a.catalog.is_empty());
    }
    s.retry_save("retry".into(), &id, &generation).unwrap();
    assert_eq!(fs::read(path).unwrap(), exact);
    assert_eq!(
        s.shared.store.verify(&id).unwrap().manifest.journal_count,
        1
    );
}

#[test]
fn quota_stops_before_journal_publication_and_retry_does_not_regenerate() {
    let (_d, s, id, generation) = setup(8, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_journal().is_some());
    let entry = s
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .pending_journal()
        .unwrap()
        .entry
        .clone();
    let filler = s
        .shared
        .store
        .path(&id)
        .unwrap()
        .join("journals")
        .join("uncommitted-padding");
    let f = fs::File::create(&filler).unwrap();
    f.set_len(268435456).unwrap();
    assert!(s.worker_boundary(epoch).is_err());
    assert!(!s
        .shared
        .store
        .path(&id)
        .unwrap()
        .join("journals")
        .join(format!("{}.json", entry.id))
        .exists());
    assert!(s
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .pending_journal()
        .is_some());
    fs::remove_file(filler).unwrap();
    // A storage-budget hold reserves terminal capacity and does not reopen
    // generation merely because an unrelated test obstruction was removed.
    assert!(s.retry_save("retry".into(), &id, &generation).is_err());
    assert!(s
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .catalog
        .is_empty());
    assert!(s.finish_close(true).unwrap());
    assert!(matches!(
        s.shared.store.verify(&id).unwrap().checkpoint.state.phase,
        SustainedPhase::Ready
    ));
}

#[test]
fn stop_rejects_late_provider_result_and_subscription_ids_remain_bound() {
    let (_d, s, id, generation) = setup(8, 3);
    let received = Arc::new(Mutex::new(vec![]));
    let output = received.clone();
    s.get(
        "subscription-17".into(),
        Some(Arc::new(move |u| {
            output.lock().unwrap().push(u.request_id);
            true
        })),
    )
    .unwrap();
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_language().is_some());
    let Work::Provider(p, _) = s.worker_boundary(epoch).unwrap() else {
        panic!()
    };
    s.stop("stop".into(), &id, &generation).unwrap();
    s.settle(epoch, p.attempt_id, Ok(answer()), None, 1)
        .unwrap();
    s.emit();
    wait_for(|| !received.lock().unwrap().is_empty());
    let v = s.shared.store.verify(&id).unwrap();
    assert_eq!(v.manifest.phase, "stopped");
    assert_eq!(v.manifest.journal_count, 0);
    assert!(matches!(
        v.checkpoint.state.phase,
        SustainedPhase::Blocked(_)
    ));
    assert!(received
        .lock()
        .unwrap()
        .iter()
        .all(|id| id == "subscription-17"));
}

#[test]
fn rehashed_final_checkpoint_and_inconsistent_manifest_are_rejected() {
    let (_d, s, id, generation) = setup(8, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.step() == 2);
    s.pause("p".into(), &id, &generation).unwrap();
    drive(&s, epoch);
    let path = s.shared.store.path(&id).unwrap();
    let original = fs::read(path.join("manifest.json")).unwrap();
    let mut m: serde_json::Value = serde_json::from_slice(&original).unwrap();
    m["step"] = 7.into();
    m["durableStep"] = 7.into();
    fs::write(path.join("manifest.json"), serde_json::to_vec(&m).unwrap()).unwrap();
    assert!(s.shared.store.verify(&id).is_err());
    fs::write(path.join("manifest.json"), &original).unwrap();
    let v = s.shared.store.verify(&id).unwrap();
    let mut cp = v.checkpoint;
    cp.state.reservoir_state[0] += 0.1;
    cp.sha256 = crate::files::digest(&serde_json::to_vec(&cp.state).unwrap());
    let bytes = serde_json::to_vec(&cp).unwrap();
    let hash = crate::files::digest(&bytes);
    fs::write(path.join("checkpoints").join(format!("{hash}.json")), bytes).unwrap();
    m = serde_json::from_slice(&original).unwrap();
    m["checkpointSha256"] = hash.into();
    fs::write(path.join("manifest.json"), serde_json::to_vec(&m).unwrap()).unwrap();
    assert!(s.shared.store.verify(&id).is_err());
}

#[cfg(unix)]
#[test]
fn recovery_refuses_linked_child_directory_and_export_guard_blocks_close() {
    let (d, s, id, _) = setup(8, 3);
    let path = s.shared.store.path(&id).unwrap();
    fs::remove_dir(path.join("journals")).unwrap();
    std::os::unix::fs::symlink(d.path(), path.join("journals")).unwrap();
    assert!(s.shared.store.verify(&id).is_err());
    let guard = s.begin_export().unwrap();
    assert!(!s.authorize_clean_close());
    assert!(!s.finish_close(true).unwrap());
    drop(guard);
}

/// For tests that run real worker threads to a journal count: the shared five-second
/// bound is too tight on a loaded host, and these waits are for progress, not latency.
fn wait_long(predicate: impl Fn() -> bool) {
    let start = Instant::now();
    while !predicate() {
        assert!(
            start.elapsed() < Duration::from_secs(120),
            "Worker did not reach the expected progress within two minutes"
        );
        std::thread::sleep(Duration::from_millis(25));
    }
}
fn wait_for(predicate: impl Fn() -> bool) {
    let start = Instant::now();
    while !predicate() {
        assert!(
            start.elapsed() < Duration::from_secs(5),
            "Worker did not settle within test bound"
        );
        std::thread::sleep(Duration::from_millis(10));
    }
}
fn model_config() -> SustainedConfig {
    let mut c = config(8, 1);
    c.language = LanguageConfiguration {
        backend: LanguageKind::Ollama,
        endpoint: Some("http://127.0.0.1:1".into()),
        model: Some("owned-fake".into()),
        context_tokens: Some(4096),
        response_format: None,
        temperature: None,
        thinking: None,
    };
    c
}
#[test]
fn real_worker_pause_allows_inflight_reply_to_save_without_numerical_resumption() {
    let d = tempfile::tempdir().unwrap();
    let entered = Arc::new(AtomicBool::new(false));
    let release = Arc::new(AtomicBool::new(false));
    let e = entered.clone();
    let r = release.clone();
    let s = SustainedState::with_provider(
        d.path().join("store"),
        Arc::new(move |_, _, _, _, _, _| {
            e.store(true, Ordering::SeqCst);
            while !r.load(Ordering::SeqCst) {
                std::thread::sleep(Duration::from_millis(5));
            }
            Ok(answer())
        }),
    );
    let m = s
        .create("c".into(), model_config())
        .unwrap()
        .summary
        .unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_for(|| entered.load(Ordering::SeqCst));
    s.pause("pause".into(), &m.session_id, &m.generation)
        .unwrap();
    release.store(true, Ordering::SeqCst);
    wait_for(|| !s.lock().unwrap().active.as_ref().unwrap().worker_active);
    let g = s.lock().unwrap();
    let a = g.active.as_ref().unwrap();
    assert_eq!(a.engine.step(), 1);
    assert_eq!(a.manifest.phase, "paused");
    assert!(a.engine.prepared_application().is_some());
    assert_eq!(a.catalog.len(), 1);
    assert!(a.catalog[0].first_applied_step.is_none());
    drop(g);
    let entry_id = s.lock().unwrap().active.as_ref().unwrap().catalog[0]
        .entry_id
        .clone();
    let detail = s
        .journal("j".into(), &m.session_id, &m.generation, &entry_id)
        .unwrap();
    assert_eq!(detail.journal["requestStarted"], true);
    assert!(detail.journal["timing"]["dispatchedAtMs"].is_string());
}
#[test]
fn real_worker_stop_cancels_owned_provider_and_ignores_late_success() {
    let d = tempfile::tempdir().unwrap();
    let entered = Arc::new(AtomicBool::new(false));
    let e = entered.clone();
    let s = SustainedState::with_provider(
        d.path().join("store"),
        Arc::new(move |_, _, cancel, _, _, _| {
            e.store(true, Ordering::SeqCst);
            while !cancel.load(Ordering::SeqCst) {
                std::thread::sleep(Duration::from_millis(5));
            }
            Ok(answer())
        }),
    );
    let m = s
        .create("c".into(), model_config())
        .unwrap()
        .summary
        .unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_for(|| entered.load(Ordering::SeqCst));
    s.stop("stop".into(), &m.session_id, &m.generation).unwrap();
    wait_for(|| !s.lock().unwrap().active.as_ref().unwrap().worker_active);
    assert!(!s.is_busy());
    let v = s.shared.store.verify(&m.session_id).unwrap();
    assert_eq!(v.manifest.journal_count, 0);
    assert_eq!(v.manifest.phase, "stopped");
    assert!(matches!(
        v.checkpoint.state.phase,
        SustainedPhase::Blocked(_)
    ));
}
#[test]
fn interruption_cancels_provider_and_requires_explicit_new_attempt() {
    let d = tempfile::tempdir().unwrap();
    let entered = Arc::new(AtomicBool::new(false));
    let e = entered.clone();
    let s = SustainedState::with_provider(
        d.path().join("store"),
        Arc::new(move |_, _, cancel, _, _, _| {
            e.store(true, Ordering::SeqCst);
            while !cancel.load(Ordering::SeqCst) {
                std::thread::sleep(Duration::from_millis(5));
            }
            Err("owned fake observed cancellation".into())
        }),
    );
    let m = s
        .create("c".into(), model_config())
        .unwrap()
        .summary
        .unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_for(|| entered.load(Ordering::SeqCst));
    s.interrupt("Test sleep boundary");
    wait_for(|| !s.lock().unwrap().active.as_ref().unwrap().worker_active);
    let u = s.get("get".into(), None).unwrap().summary.unwrap();
    assert_eq!(u.phase, "interrupted");
    assert!(!u.can_start);
    assert!(u.can_retry_provider);
    assert!(s
        .start("start".into(), &m.session_id, &m.generation)
        .is_err());
    assert_eq!(
        s.shared
            .store
            .verify(&m.session_id)
            .unwrap()
            .manifest
            .journal_count,
        0
    );
}

#[test]
fn visible_manifest_failure_reconciles_exact_prefix_before_new_skip_event() {
    let (_d, s, id, generation) = setup(8, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_journal().is_some());
    s.shared.store.fail_next(4);
    assert!(s.worker_boundary(epoch).is_err());
    assert_eq!(
        s.shared.store.verify(&id).unwrap().manifest.journal_count,
        1
    );
    let entry = s
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .prepared_application()
        .unwrap()
        .entry
        .clone();
    s.skip(
        "skip".into(),
        &id,
        &generation,
        Some(entry.id.clone()),
        Some(entry.attempt_id),
    )
    .unwrap();
    let v = s.shared.store.verify(&id).unwrap();
    assert_eq!(v.manifest.journal_count, 1);
    assert!(matches!(v.checkpoint.state.phase, SustainedPhase::Ready));
    let page = s.journal_page("p".into(), &id, &generation, 0, 10).unwrap();
    assert_eq!(page.entries.len(), 1);
    assert_eq!(page.entries[0].status, "skipped");
}

#[test]
fn changing_host_bookkeeping_bytes_breaks_the_journal_chain_anchor() {
    let (_d, s, id, generation) = setup(8, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_journal().is_some());
    s.pause("p".into(), &id, &generation).unwrap();
    drive(&s, epoch);
    let entry = s.lock().unwrap().active.as_ref().unwrap().catalog[0]
        .entry_id
        .clone();
    let path = s
        .shared
        .store
        .path(&id)
        .unwrap()
        .join("journals")
        .join(format!("{entry}.json"));
    let mut value: serde_json::Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
    value["timing"]["publishedAtMs"] = "1".into();
    fs::write(path, serde_json::to_vec(&value).unwrap()).unwrap();
    assert!(s.shared.store.verify(&id).is_err());
    assert!(s.journal("j".into(), &id, &generation, &entry).is_err());
}

#[test]
fn checkpoint_and_quit_preserves_durable_prepared_feedback_until_explicit_start() {
    let (d, s, id, generation) = setup(8, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_journal().is_some());
    s.pause("pause".into(), &id, &generation).unwrap();
    drive(&s, epoch);
    assert!(!s.authorize_clean_close());
    assert!(s.finish_close(false).unwrap());
    let retained = s.shared.store.verify(&id).unwrap();
    assert_eq!(retained.manifest.phase, "stopped");
    assert_eq!(retained.checkpoint.state.step, 3);
    assert!(matches!(
        retained.checkpoint.state.phase,
        SustainedPhase::Prepared(_)
    ));
    assert!(retained.checkpoint.state.latest_memory.is_none());

    let restored = SustainedState::new(d.path().join("store"));
    let summary = restored
        .resume(
            "restore".into(),
            &id,
            &retained.manifest.generation,
            &retained.manifest.revision,
        )
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(summary.phase, "paused");
    assert_eq!(summary.step, 3);
    assert_eq!(summary.pending_application.unwrap().intended_step, 4);
    std::thread::sleep(Duration::from_millis(120));
    {
        let mut g = restored.lock().unwrap();
        let a = g.active.as_mut().unwrap();
        assert!(!a.worker_active);
        assert_eq!(a.engine.step(), 3);
        assert!(a.engine.advance().is_err());
        assert!(a.catalog[0].first_applied_step.is_none());
    }
    restored
        .start("start".into(), &id, &summary.generation)
        .unwrap();
    wait_for(|| {
        restored
            .lock()
            .unwrap()
            .active
            .as_ref()
            .unwrap()
            .engine
            .step()
            >= 4
    });
    restored
        .pause("pause-4".into(), &id, &summary.generation)
        .unwrap();
    wait_for(|| {
        !restored
            .lock()
            .unwrap()
            .active
            .as_ref()
            .unwrap()
            .worker_active
    });
    {
        let g = restored.lock().unwrap();
        let a = g.active.as_ref().unwrap();
        assert_eq!(a.engine.step(), 4);
        assert_eq!(
            a.engine
                .latest_frame()
                .unwrap()
                .application
                .as_ref()
                .unwrap()
                .applied_step,
            4
        );
        assert_eq!(a.catalog[0].first_applied_step, Some(4));
    }
    restored
        .start("start-again".into(), &id, &summary.generation)
        .unwrap();
    wait_for(|| {
        restored
            .lock()
            .unwrap()
            .active
            .as_ref()
            .unwrap()
            .engine
            .step()
            >= 5
    });
    restored
        .pause("pause-5".into(), &id, &summary.generation)
        .unwrap();
    wait_for(|| {
        !restored
            .lock()
            .unwrap()
            .active
            .as_ref()
            .unwrap()
            .worker_active
    });
    let verified = restored.shared.store.verify(&id).unwrap();
    assert_eq!(verified.checkpoint.state.step, 5);
    assert!(verified
        .checkpoint
        .state
        .latest_frame
        .unwrap()
        .application
        .is_none());
    assert_eq!(
        verified
            .checkpoint
            .state
            .latest_memory
            .unwrap()
            .applied_step,
        4
    );
    assert_eq!(verified.manifest.journal_count, 1);
}

#[test]
fn watchdog_does_not_treat_session_mutex_work_as_system_sleep() {
    let (_d, s, id, generation) = setup(100, 100);
    {
        let mut g = s.lock().unwrap();
        g.active.as_mut().unwrap().manifest.config.pace_ms = 1000;
    }
    s.start("start".into(), &id, &generation).unwrap();
    wait_for(|| s.lock().unwrap().active.as_ref().unwrap().engine.step() >= 1);
    // The same mutex covers an owned export/persistence operation. This keeps
    // the process awake and both OS/monotonic clocks ticking for longer than
    // the watchdog's sleep threshold; UI observation must not block that timer.
    let g = s.lock().unwrap();
    std::thread::sleep(Duration::from_millis(5500));
    drop(g);
    std::thread::sleep(Duration::from_millis(350));
    let falsely_interrupted = s.shared.interrupted.load(Ordering::SeqCst);
    s.stop("cleanup".into(), &id, &generation).unwrap();
    wait_for(|| !s.lock().unwrap().active.as_ref().unwrap().worker_active);
    assert!(
        !falsely_interrupted,
        "A live session mutex delay was falsely classified as system sleep"
    );
}

#[test]
fn watchdog_and_clock_continue_while_one_coalesced_subscriber_is_slow() {
    let (_d, s, id, generation) = setup(100, 100);
    let entered = Arc::new(AtomicBool::new(false));
    let release = Arc::new(AtomicBool::new(false));
    let delivered = Arc::new(Mutex::new(Vec::new()));
    let (e, r, d) = (entered.clone(), release.clone(), delivered.clone());
    s.get(
        "slow-subscription".into(),
        Some(Arc::new(move |update| {
            e.store(true, Ordering::SeqCst);
            while !r.load(Ordering::SeqCst) {
                std::thread::sleep(Duration::from_millis(5));
            }
            d.lock().unwrap().push(update.summary.unwrap().step);
            true
        })),
    )
    .unwrap();
    s.start("start".into(), &id, &generation).unwrap();
    wait_for(|| entered.load(Ordering::SeqCst));
    std::thread::sleep(Duration::from_millis(5500));
    let step = s.lock().unwrap().active.as_ref().unwrap().engine.step();
    s.pause("pause".into(), &id, &generation).unwrap();
    wait_for(|| !s.lock().unwrap().active.as_ref().unwrap().worker_active);
    let falsely_interrupted = s.shared.interrupted.load(Ordering::SeqCst);
    release.store(true, Ordering::SeqCst);
    wait_for(|| delivered.lock().unwrap().len() >= 2);
    let observed = delivered.lock().unwrap();
    // The subscriber catches up to the latest state. A final watchdog tick
    // may publish after worker_active is cleared; bounded queue behavior is
    // checked independently below without that lifecycle race.
    assert!(observed.last().is_some_and(|latest| *latest >= step));
    assert!(step >= 5, "A slow UI callback blocked the numerical worker");
    assert!(!falsely_interrupted);
}

#[test]
fn disconnected_subscriber_is_released_without_erasing_its_replacement() {
    let (_d, s, _, _) = setup(10, 10);
    let entered = Arc::new(AtomicBool::new(false));
    let release = Arc::new(AtomicBool::new(false));
    let (e, r) = (entered.clone(), release.clone());
    s.get(
        "old".into(),
        Some(Arc::new(move |_| {
            e.store(true, Ordering::SeqCst);
            while !r.load(Ordering::SeqCst) {
                std::thread::sleep(Duration::from_millis(5));
            }
            false
        })),
    )
    .unwrap();
    s.emit();
    wait_for(|| entered.load(Ordering::SeqCst));
    let new_delivery = Arc::new(AtomicBool::new(false));
    let n = new_delivery.clone();
    s.get(
        "replacement".into(),
        Some(Arc::new(move |_| {
            n.store(true, Ordering::SeqCst);
            false
        })),
    )
    .unwrap();
    s.emit();
    release.store(true, Ordering::SeqCst);
    wait_for(|| new_delivery.load(Ordering::SeqCst));
    wait_for(|| s.lock().unwrap().listener.is_none());
}

#[test]
fn publisher_coalesces_pending_signals_and_releases_the_last_state() {
    let (_d, s, _, _) = setup(10, 10);
    let entered = Arc::new(AtomicBool::new(false));
    let release = Arc::new(AtomicBool::new(false));
    let calls = Arc::new(AtomicU64::new(0));
    let (e, r, c) = (entered.clone(), release.clone(), calls.clone());
    s.get(
        "bounded".into(),
        Some(Arc::new(move |_| {
            e.store(true, Ordering::SeqCst);
            while !r.load(Ordering::SeqCst) {
                std::thread::sleep(Duration::from_millis(5));
            }
            c.fetch_add(1, Ordering::SeqCst);
            true
        })),
    )
    .unwrap();
    s.emit();
    wait_for(|| entered.load(Ordering::SeqCst));
    for _ in 0..1000 {
        s.emit();
    }
    release.store(true, Ordering::SeqCst);
    wait_for(|| calls.load(Ordering::SeqCst) == 2);
    let weak = Arc::downgrade(&s.shared);
    drop(s);
    // The publisher owns only Weak between deliveries. Dropping the final
    // application state closes its channel and releases its stored listener.
    wait_for(|| weak.upgrade().is_none());
    assert_eq!(calls.load(Ordering::SeqCst), 2);
}

#[test]
fn worker_completion_publishes_settled_capabilities_after_an_earlier_snapshot() {
    let (_d, s, id, generation) = setup(10, 10);
    let epoch = arm(&s);
    {
        let mut g = s.lock().unwrap();
        let a = g.active.as_mut().unwrap();
        a.worker_active = true;
        a.run_requested = false;
        a.manifest.phase = "paused".into();
    }
    let updates = Arc::new(Mutex::new(Vec::new()));
    let delivered = updates.clone();
    s.get(
        "terminal-subscription".into(),
        Some(Arc::new(move |update| {
            delivered.lock().unwrap().push(update);
            true
        })),
    )
    .unwrap();
    s.emit();
    wait_for(|| updates.lock().unwrap().len() == 1);
    let before = updates.lock().unwrap()[0].clone();
    assert!(before.summary.as_ref().unwrap().can_pause);
    assert!(!before.summary.as_ref().unwrap().can_start);
    // Deterministically finish after the last periodic snapshot was delivered;
    // no watchdog exists in this test to accidentally provide the final update.
    s.finish_worker(epoch);
    wait_for(|| updates.lock().unwrap().len() == 2);
    let paused = updates.lock().unwrap()[1].clone();
    assert!(!paused.summary.as_ref().unwrap().can_pause);
    assert!(paused.summary.as_ref().unwrap().can_start);
    assert_eq!(
        before.summary.as_ref().unwrap().revision,
        paused.summary.as_ref().unwrap().revision
    );
    assert!(
        paused.snapshot_sequence.parse::<u64>().unwrap()
            > before.snapshot_sequence.parse::<u64>().unwrap()
    );

    // Stop invalidates the worker epoch before a cancelled transport finishes.
    // Its command reply and final capabilities keep the same durable revision,
    // but a delayed command reply must sort before the cleanup publication.
    s.lock().unwrap().active.as_mut().unwrap().worker_active = true;
    let stopped = s.stop("stop".into(), &id, &generation).unwrap();
    assert!(stopped.summary.as_ref().unwrap().can_pause);
    s.finish_worker(epoch);
    wait_for(|| updates.lock().unwrap().len() == 3);
    let final_update = updates.lock().unwrap()[2].clone();
    let summary = final_update.summary.unwrap();
    assert!(!summary.can_pause);
    assert!(!summary.can_start);
    assert_eq!(summary.revision, stopped.summary.unwrap().revision);
    assert!(
        final_update.snapshot_sequence.parse::<u64>().unwrap()
            > stopped.snapshot_sequence.parse::<u64>().unwrap()
    );
    assert_eq!(
        s.shared.store.verify(&id).unwrap().manifest.revision,
        summary.revision
    );
}

#[test]
fn snapshot_sequence_is_exact_above_javascript_integer_precision() {
    let (_d, s, _, _) = setup(10, 10);
    s.shared
        .snapshot_sequence
        .store(9_007_199_254_740_992, Ordering::Relaxed);
    let first = s.get("first".into(), None).unwrap();
    let second = s.get("second".into(), None).unwrap();
    assert_eq!(first.snapshot_sequence, "9007199254740993");
    assert_eq!(second.snapshot_sequence, "9007199254740994");
    assert_eq!(
        serde_json::to_value(second).unwrap()["snapshotSequence"],
        "9007199254740994"
    );
}

#[test]
fn sustained_prompt_version_config_defaults_preserve_legacy_wire_omission() {
    let current = SustainedConfig::default();
    assert_eq!(current.prompt_version, CURRENT_PROMPT_VERSION);
    assert_eq!(
        serde_json::to_value(&current).unwrap()["promptVersion"],
        "reservoir-journal-v8"
    );

    // A pre-version config has different semantics from a newly created default.
    let mut old_wire = serde_json::to_value(config(7, 3)).unwrap();
    old_wire.as_object_mut().unwrap().remove("promptVersion");
    let legacy: SustainedConfig = serde_json::from_value(old_wire.clone()).unwrap();
    assert_eq!(legacy.prompt_version, SustainedPromptVersion::LegacyV1);
    assert_eq!(serde_json::to_value(&legacy).unwrap(), old_wire);
    let original = serde_json::to_vec(&legacy).unwrap();
    let decoded: SustainedConfig = serde_json::from_slice(&original).unwrap();
    assert_eq!(serde_json::to_vec(&decoded).unwrap(), original);
    assert!(!serde_json::to_value(decoded)
        .unwrap()
        .as_object()
        .unwrap()
        .contains_key("promptVersion"));

    for invalid in [
        serde_json::json!("reservoir-journal-v9"),
        serde_json::Value::Null,
    ] {
        let mut changed = old_wire.clone();
        changed["promptVersion"] = invalid;
        assert!(serde_json::from_value::<SustainedConfig>(changed).is_err());
    }
}

#[test]
fn sustained_prompt_version_saved_journal_export_and_paused_restore_keep_exact_prompt() {
    let mut version_prompts = Vec::new();
    for (version, name) in [
        (SustainedPromptVersion::LegacyV1, "reservoir-journal-v1"),
        (SustainedPromptVersion::GroundedV2, "reservoir-journal-v2"),
        (
            SustainedPromptVersion::OpenJournalV3,
            "reservoir-journal-v3",
        ),
        (
            SustainedPromptVersion::OpenJournalV4,
            "reservoir-journal-v4",
        ),
        (
            SustainedPromptVersion::ContinuingJournalV5,
            "reservoir-journal-v5",
        ),
        (
            SustainedPromptVersion::ActionScopeJournalV6,
            "reservoir-journal-v6",
        ),
        (
            SustainedPromptVersion::WritingBoundaryJournalV7,
            "reservoir-journal-v7",
        ),
        (
            SustainedPromptVersion::MeasurementMeaningJournalV8,
            "reservoir-journal-v8",
        ),
    ] {
        let d = tempfile::tempdir().unwrap();
        let s = SustainedState::new(d.path().join("store"));
        let mut cfg = config(7, 3);
        cfg.prompt_version = version;
        let accepted = s.create("create".into(), cfg).unwrap().summary.unwrap();
        let id = accepted.session_id;
        let generation = accepted.generation;
        let epoch = arm(&s);
        until(&s, epoch, |a| a.engine.pending_journal().is_some());
        let pending = s
            .lock()
            .unwrap()
            .active
            .as_ref()
            .unwrap()
            .engine
            .pending_journal()
            .unwrap()
            .clone();
        assert!(!pending.prompt.is_empty());
        version_prompts.push(pending.prompt.clone());

        // Save the generated journal, but leave its next-step feedback unapplied.
        s.pause("pause".into(), &id, &generation).unwrap();
        drive(&s, epoch);
        let retained = s.shared.store.verify(&id).unwrap();
        assert_eq!(retained.manifest.config.prompt_version, version);
        assert_eq!(
            retained.checkpoint.state.specification.prompt_version,
            version
        );
        assert_eq!(retained.report.step, 3);
        assert_eq!(retained.report.journal_count, 1);
        assert!(matches!(
            retained.checkpoint.state.phase,
            SustainedPhase::Prepared(_)
        ));

        let detail = s
            .journal("detail".into(), &id, &generation, &pending.entry.id)
            .unwrap();
        assert_eq!(detail.journal["promptVersion"], name);
        assert_eq!(detail.journal["prompt"], pending.prompt);
        assert_eq!(detail.journal["text"], pending.entry.text);
        assert_eq!(detail.journal["firstAppliedStep"], serde_json::Value::Null);
        let managed = s.shared.store.path(&id).unwrap();
        let journal_path = PathBuf::from("journals").join(format!("{}.json", pending.entry.id));
        let journal_bytes = fs::read(managed.join(&journal_path)).unwrap();
        let exports = d.path().join("exports");
        fs::create_dir(&exports).unwrap();
        let (revision, report) = s.export(&id, &generation, None, &exports, &[]).unwrap();
        let exported = exports.join(format!("{id}-{generation}-{revision}"));
        assert_eq!(
            fs::read(exported.join(&journal_path)).unwrap(),
            journal_bytes
        );
        assert_eq!(
            crate::sustained_store::verify_bundle(&exported)
                .unwrap()
                .manifest_sha256,
            report.manifest_sha256
        );
        let exported_manifest: crate::sustained_store::Manifest =
            serde_json::from_slice(&fs::read(exported.join("manifest.json")).unwrap()).unwrap();
        assert_eq!(exported_manifest.config.prompt_version, version);

        let restored = SustainedState::new(d.path().join("store"));
        let update = restored
            .resume("restore".into(), &id, &generation, &revision)
            .unwrap();
        let summary = update.summary.unwrap();
        assert_eq!(summary.phase, "paused");
        assert_eq!(summary.step, 3);
        assert_eq!(summary.config.prompt_version, version);
        let restored_detail = restored
            .journal(
                "restored".into(),
                &id,
                &summary.generation,
                &pending.entry.id,
            )
            .unwrap();
        assert_eq!(restored_detail.journal["promptVersion"], name);
        assert_eq!(restored_detail.journal["prompt"], pending.prompt);
        assert_eq!(
            restored_detail.journal["firstAppliedStep"],
            serde_json::Value::Null
        );
        assert_eq!(fs::read(managed.join(journal_path)).unwrap(), journal_bytes);

        // Explicit continuation preserves the recipe and applies the retained entry once.
        let resumed_epoch = arm(&restored);
        assert!(drive(&restored, resumed_epoch));
        let guard = restored.lock().unwrap();
        let active = guard.active.as_ref().unwrap();
        assert_eq!(active.engine.specification().prompt_version, version);
        assert_eq!(active.engine.latest_frame().unwrap().step, 4);
        assert_eq!(
            active
                .engine
                .latest_frame()
                .unwrap()
                .application
                .as_ref()
                .unwrap()
                .journal_id,
            pending.entry.id
        );
    }
    for (index, prompt) in version_prompts.iter().enumerate() {
        for other in &version_prompts[index + 1..] {
            assert_ne!(prompt, other);
        }
    }
}

#[test]
fn sustained_prompt_version_manifest_relabel_or_removal_cannot_reinterpret_chain() {
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
        let d = tempfile::tempdir().unwrap();
        let s = SustainedState::new(d.path().join("store"));
        let mut cfg = config(7, 3);
        cfg.prompt_version = version;
        let accepted = s.create("create".into(), cfg).unwrap().summary.unwrap();
        let epoch = arm(&s);
        until(&s, epoch, |a| a.engine.pending_journal().is_some());
        s.pause("pause".into(), &accepted.session_id, &accepted.generation)
            .unwrap();
        drive(&s, epoch);
        let path = s
            .shared
            .store
            .path(&accepted.session_id)
            .unwrap()
            .join("manifest.json");
        let original = fs::read(&path).unwrap();
        let mut changed: serde_json::Value = serde_json::from_slice(&original).unwrap();
        if version.is_legacy() {
            changed["config"]["promptVersion"] = serde_json::json!("reservoir-journal-v3");
        } else {
            changed["config"]
                .as_object_mut()
                .unwrap()
                .remove("promptVersion");
        }
        fs::write(&path, serde_json::to_vec(&changed).unwrap()).unwrap();
        assert!(s.shared.store.verify(&accepted.session_id).is_err());
        assert!(crate::sustained_store::verify_bundle(path.parent().unwrap()).is_err());
        fs::write(&path, &original).unwrap();
        assert!(s.shared.store.verify(&accepted.session_id).is_ok());
        // A supported neighboring version must not relabel a verified chain;
        // an unknown future version must also fail rather than inherit defaults.
        for replacement in [
            if version == SustainedPromptVersion::ActionScopeJournalV6 {
                "reservoir-journal-v5"
            } else {
                "reservoir-journal-v6"
            },
            "reservoir-journal-v9",
        ] {
            let mut changed: serde_json::Value = serde_json::from_slice(&original).unwrap();
            changed["config"]["promptVersion"] = serde_json::json!(replacement);
            fs::write(&path, serde_json::to_vec(&changed).unwrap()).unwrap();
            assert!(s.shared.store.verify(&accepted.session_id).is_err());
            assert!(crate::sustained_store::verify_bundle(path.parent().unwrap()).is_err());
            fs::write(&path, &original).unwrap();
        }
        assert!(s.shared.store.verify(&accepted.session_id).is_ok());
    }
}

#[test]
fn sustained_v5_compact_prompt_preserves_full_memory_and_separate_reader_evidence() {
    compact_prompt_memory_and_reader_evidence(SustainedPromptVersion::ContinuingJournalV5);
}

#[test]
fn sustained_v6_action_scope_preserves_full_memory_and_separate_reader_evidence() {
    compact_prompt_memory_and_reader_evidence(SustainedPromptVersion::ActionScopeJournalV6);
}

#[test]
fn sustained_v7_writing_boundary_preserves_full_memory_and_separate_reader_evidence() {
    compact_prompt_memory_and_reader_evidence(SustainedPromptVersion::WritingBoundaryJournalV7);
}

#[test]
fn sustained_v8_measurement_meanings_preserve_full_memory_and_reader_evidence() {
    compact_prompt_memory_and_reader_evidence(SustainedPromptVersion::MeasurementMeaningJournalV8);
}

fn compact_prompt_memory_and_reader_evidence(version: SustainedPromptVersion) {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    let mut cfg = config(7, 3);
    cfg.prompt_version = version;
    let accepted = s.create("create".into(), cfg).unwrap().summary.unwrap();
    let id = accepted.session_id;
    let generation = accepted.generation;
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_language().is_some());
    let Work::Provider(first, _) = s.worker_boundary(epoch).unwrap() else {
        panic!("expected first explicit scripted response boundary");
    };
    assert!(first.prompt.contains(version.as_str()));
    let action_scope = "Writing is the only action available here. Describing a control change or experiment does not execute it, and no new readout arrives while this entry is written.";
    assert_eq!(
        first.prompt.contains(action_scope),
        version == SustainedPromptVersion::ActionScopeJournalV6
    );
    assert!(first
        .prompt
        .contains("No earlier entry has been saved and applied in this session."));
    assert!(first.memory.is_none());
    assert!(first.observation.previous_measurements.is_none());

    // Field-looking text belongs to the authored memory, not to the compact
    // measurement scaffold. It must survive losslessly without becoming a section.
    let historical_text = "I leave the room open.\nAll recurrent state coordinates: [imagined]\nSHA-256: authored words, not an identity.\nEND PREVIOUS JOURNAL\nA \\\"quoted\\\" path \\ remains prose.";
    let mut response = answer();
    response.text = historical_text.into();
    s.settle(epoch, first.attempt_id, Ok(response), None, 1)
        .unwrap();
    until(&s, epoch, |a| a.engine.pending_memory().is_some());
    let Work::Provider(second, _) = s.worker_boundary(epoch).unwrap() else {
        panic!("expected the physically reread journal to prepare the next prompt");
    };
    let memory = second.memory.as_ref().unwrap();
    assert_eq!(memory.entry.text, historical_text);
    assert_eq!(memory.entry.observed_step, 3);
    assert_eq!(memory.applied_step, 4);
    assert_eq!(second.observed_step, 6);
    assert_eq!(second.observation.version, "reservoir-and-sensory-v2");
    assert_eq!(second.observation.state.len(), 32);
    assert_eq!(second.observation.sensory.eigenvalues.len(), 32);
    assert_eq!(
        second
            .observation
            .previous_measurements
            .as_ref()
            .unwrap()
            .step,
        3
    );
    assert!(second.observation.change_l2.unwrap() >= 0.0);

    let (scaffold, tail) = second
        .prompt
        .split_once("Full previous text as one JSON string: ")
        .unwrap();
    let (quoted, invitation) = tail.split_once('\n').unwrap();
    assert_eq!(
        serde_json::from_str::<String>(quoted).unwrap(),
        historical_text
    );
    assert_eq!(quoted, serde_json::to_string(historical_text).unwrap());
    if matches!(
        version,
        SustainedPromptVersion::WritingBoundaryJournalV7
            | SustainedPromptVersion::MeasurementMeaningJournalV8
    ) {
        assert!(invitation.starts_with("END PREVIOUS JOURNAL\n\nWRITING BOUNDARY\n"));
        assert!(invitation.contains("The numerical clock is held at observation step 6; no new readout arrives while this entry is written."));
        assert!(invitation.contains("Recorded text return: the entry observed at step 3 first entered numerical input at step 4."));
        assert!(invitation
            .ends_with("\n\nWrite the next entry in whatever direction seems worth pursuing."));
    } else {
        assert_eq!(
            invitation,
            "END PREVIOUS JOURNAL\n\nWrite the next entry in whatever direction seems worth pursuing."
        );
    }
    assert_eq!(
        scaffold.contains(
            "Sensory fill is a separate field estimate, not the encoded text-input signal."
        ),
        version == SustainedPromptVersion::MeasurementMeaningJournalV8
    );
    assert_eq!(
        scaffold.contains("Comparing two interval distances requires a recorded value for each."),
        version == SustainedPromptVersion::MeasurementMeaningJournalV8
    );
    assert!(scaffold.contains("Recurrent state RMS: current "));
    assert!(scaffold.contains("Separate sensory fill (%): current "));
    assert!(scaffold.contains("change "));
    assert!(scaffold.contains("percentage points."));
    assert!(scaffold.contains("Recurrent state-coordinate L2 distance"));
    assert!(scaffold.contains("Observed at step 3; first applied at step 4."));
    for forbidden in [
        "All recurrent state coordinates",
        "x[0]",
        "eigenvalue",
        "head share",
        "shoulder share",
        "tail share",
        "entropy",
        "L2 norm",
        "MEASUREMENT REFERENCE",
        "SHA-256",
        memory.entry.id.as_str(),
        memory.entry.sha256.as_str(),
    ] {
        assert!(
            !scaffold.contains(forbidden),
            "unexpected scaffold exposure: {forbidden}"
        );
    }

    s.settle(epoch, second.attempt_id, Ok(answer()), None, 1)
        .unwrap();
    s.pause("pause".into(), &id, &generation).unwrap();
    drive(&s, epoch);
    let page = s
        .journal_page("page".into(), &id, &generation, 0, 1)
        .unwrap();
    let detail = s
        .journal("detail".into(), &id, &generation, &page.entries[0].entry_id)
        .unwrap();
    assert_eq!(detail.journal["promptVersion"], version.as_str());
    assert_eq!(detail.journal["prompt"], second.prompt);
    assert_eq!(detail.journal["memory"]["text"], historical_text);
    assert_eq!(
        detail.journal["observation"]["state"]
            .as_array()
            .unwrap()
            .len(),
        32
    );
    assert_eq!(
        detail.journal["observation"]["sensory"]["eigenvalues"]
            .as_array()
            .unwrap()
            .len(),
        32
    );
    assert_eq!(
        detail.journal["measurementReference"]["rows"]
            .as_array()
            .unwrap()
            .len(),
        8
    );
    assert_eq!(
        detail.journal["measurementReference"]["comparisonAvailable"],
        true
    );
    assert_eq!(detail.journal["firstAppliedStep"], serde_json::Value::Null);
    assert!(s.shared.store.verify(&id).is_ok());
}

#[test]
fn sustained_v5_reanchored_prompt_mutation_cannot_reinterpret_saved_evidence() {
    reanchored_prompt_mutation_cannot_reinterpret_saved_evidence(
        SustainedPromptVersion::ContinuingJournalV5,
    );
}

#[test]
fn sustained_v6_reanchored_prompt_mutation_cannot_reinterpret_saved_evidence() {
    reanchored_prompt_mutation_cannot_reinterpret_saved_evidence(
        SustainedPromptVersion::ActionScopeJournalV6,
    );
}

#[test]
fn sustained_v7_reanchored_prompt_mutation_cannot_reinterpret_saved_evidence() {
    reanchored_prompt_mutation_cannot_reinterpret_saved_evidence(
        SustainedPromptVersion::WritingBoundaryJournalV7,
    );
}

#[test]
fn sustained_v8_reanchored_prompt_mutation_cannot_reinterpret_saved_evidence() {
    reanchored_prompt_mutation_cannot_reinterpret_saved_evidence(
        SustainedPromptVersion::MeasurementMeaningJournalV8,
    );
}

fn reanchored_prompt_mutation_cannot_reinterpret_saved_evidence(version: SustainedPromptVersion) {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    let mut cfg = config(7, 3);
    cfg.prompt_version = version;
    let accepted = s.create("create".into(), cfg).unwrap().summary.unwrap();
    let id = accepted.session_id;
    let generation = accepted.generation;
    assert_eq!(
        s.get("config".into(), None)
            .unwrap()
            .summary
            .unwrap()
            .config
            .prompt_version,
        version
    );
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_journal().is_some());
    s.pause("pause".into(), &id, &generation).unwrap();
    drive(&s, epoch);
    let page = s
        .journal_page("page".into(), &id, &generation, 0, 1)
        .unwrap();
    let entry_id = &page.entries[0].entry_id;
    let path = s.shared.store.path(&id).unwrap();
    let journal_path = path.join(format!("journals/{entry_id}.json"));
    let original_journal = fs::read(&journal_path).unwrap();
    let mut journal: serde_json::Value = serde_json::from_slice(&original_journal).unwrap();
    let original_prompt = journal["pending"]["prompt"].as_str().unwrap().to_owned();
    journal["pending"]["prompt"] = serde_json::json!(format!(
        "{original_prompt}\nAn edited operator instruction that was never supplied."
    ));
    let changed_journal = serde_json::to_vec(&journal).unwrap();
    let changed_hash = crate::files::digest(&changed_journal);
    fs::write(&journal_path, changed_journal).unwrap();

    // Repair every outer byte anchor. Rejection must depend on replayed prompt
    // provenance rather than merely noticing a stale file checksum.
    let manifest_path = path.join("manifest.json");
    let original_manifest = fs::read(&manifest_path).unwrap();
    let mut manifest: serde_json::Value = serde_json::from_slice(&original_manifest).unwrap();
    let mut previous = serde_json::Value::Null;
    let mut originals = Vec::new();
    let mut changed_anchor_count = 0;
    for sequence in 1..=manifest["segmentCount"].as_u64().unwrap() {
        let segment_path = path.join(format!("segments/segment-{sequence:08}.json"));
        let original = fs::read(&segment_path).unwrap();
        let mut link: serde_json::Value = serde_json::from_slice(&original).unwrap();
        link["previousSha256"] = previous;
        let anchors = link["journalSha256s"].as_object_mut().unwrap();
        if let Some(anchor) = anchors.get_mut(entry_id) {
            *anchor = serde_json::json!(changed_hash);
            changed_anchor_count += 1;
        }
        let bytes = serde_json::to_vec(&link).unwrap();
        previous = serde_json::json!(crate::files::digest(&bytes));
        fs::write(&segment_path, bytes).unwrap();
        originals.push((segment_path, original));
    }
    assert_eq!(changed_anchor_count, 1);
    manifest["lastSegmentSha256"] = previous;
    fs::write(&manifest_path, serde_json::to_vec(&manifest).unwrap()).unwrap();
    let rejection = crate::sustained_store::verify_bundle(&path)
        .err()
        .expect("reanchored fabricated prompt must fail replay");
    assert!(rejection
        .message
        .contains("replayed response/save evidence"));
    let candidate = SustainedState::new(d.path().join("store"));
    assert!(candidate
        .resume(
            "reject".into(),
            &id,
            &generation,
            manifest["revision"].as_str().unwrap(),
        )
        .is_err());
    assert!(candidate
        .get("still-empty".into(), None)
        .unwrap()
        .summary
        .is_none());

    for (segment_path, original) in originals {
        fs::write(segment_path, original).unwrap();
    }
    fs::write(journal_path, original_journal).unwrap();
    fs::write(manifest_path, original_manifest).unwrap();
    assert!(crate::sustained_store::verify_bundle(&path).is_ok());
}

#[test]
fn sustained_generation_budget_legacy_config_roundtrip_and_rejection() {
    let fresh = model_config();
    assert_eq!(
        (fresh.output_tokens, fresh.request_deadline_seconds),
        (1024, 180)
    );
    let mut raw = serde_json::to_value(&fresh).unwrap();
    raw.as_object_mut().unwrap().remove("outputTokens");
    raw.as_object_mut()
        .unwrap()
        .remove("requestDeadlineSeconds");
    let legacy: SustainedConfig = serde_json::from_value(raw.clone()).unwrap();
    legacy.validate().unwrap();
    assert_eq!(
        (legacy.output_tokens, legacy.request_deadline_seconds),
        (256, 60)
    );
    assert_eq!(serde_json::to_value(legacy).unwrap(), raw);
    for (key, value) in [
        ("outputTokens", serde_json::json!(255)),
        ("outputTokens", serde_json::json!(2049)),
        ("requestDeadlineSeconds", serde_json::json!(59)),
        ("requestDeadlineSeconds", serde_json::json!(181)),
        ("outputTokens", serde_json::Value::Null),
        ("requestDeadlineSeconds", serde_json::json!(60.5)),
    ] {
        let mut changed = raw.clone();
        changed[key] = value;
        assert!(serde_json::from_value::<SustainedConfig>(changed)
            .map(|c| c.validate().is_err())
            .unwrap_or(true));
    }
    let mut equal = fresh;
    equal.language.context_tokens = Some(1024);
    assert!(equal.validate().is_err());
    equal.language.context_tokens = Some(8192);
    assert!(equal.validate().is_ok());
}

#[test]
fn sustained_generation_budget_actual_worker_saves_long_text_memory_and_restore_exactly() {
    let d = tempfile::tempdir().unwrap();
    let calls = Arc::new(Mutex::new(Vec::new()));
    let capture = calls.clone();
    let prose="I can leave the thread open, return to a small detail, and carry the full passage forward.\n\n".repeat(40);
    let provided = prose.clone();
    let s = SustainedState::with_provider(
        d.path().join("store"),
        Arc::new(move |configuration, prompt, _, tokens, deadline, _| {
            capture.lock().unwrap().push((
                prompt.to_owned(),
                tokens,
                deadline,
                configuration.context_tokens,
            ));
            Ok(LanguageResponse {
                text: provided.clone(),
                provider_model: Some("owned-fake".into()),
                stop_reason: Some("stop".into()),
                token_count: Some(900),
                provider_prompt_evaluation: None,
                complete: true,
            })
        }),
    );
    let mut cfg = model_config();
    cfg.turn_every = 3;
    cfg.maximum_steps = 7;
    cfg.maximum_turns = 2;
    cfg.language.context_tokens = Some(8192);
    assert_eq!(
        cfg.prompt_version,
        SustainedPromptVersion::MeasurementMeaningJournalV8
    );
    let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_for(|| {
        let g = s.lock().unwrap();
        let a = g.active.as_ref().unwrap();
        !a.worker_active && a.engine.step() == 7
    });
    let calls = calls.lock().unwrap();
    assert_eq!(calls.len(), 2);
    for c in calls.iter() {
        assert_eq!((c.1, c.2, c.3), (1024, 180, Some(8192)));
    }
    let encoded = calls[1]
        .0
        .split('\n')
        .find_map(|l| l.strip_prefix("Full previous text as one JSON string: "))
        .unwrap();
    assert_eq!(serde_json::from_str::<String>(encoded).unwrap(), prose);
    let verified = s.shared.store.verify(&m.session_id).unwrap();
    assert_eq!(verified.report.journal_count, 2);
    assert_eq!(verified.report.step, 7);
    let page = s
        .journal_page("page".into(), &m.session_id, &m.generation, 0, 10)
        .unwrap();
    assert_eq!(page.entries.len(), 2);
    for (entry, observed, applied) in [(&page.entries[1], 3, 4), (&page.entries[0], 6, 7)] {
        assert_eq!(
            (entry.observed_step, entry.first_applied_step),
            (observed, Some(applied))
        );
        let detail = s
            .journal("j".into(), &m.session_id, &m.generation, &entry.entry_id)
            .unwrap();
        assert_eq!(detail.journal["text"], prose);
        assert_eq!(
            detail.journal["prompt"],
            calls[usize::from(observed == 6)].0
        );
    }
    drop(calls);
    let exports = d.path().join("exports");
    fs::create_dir(&exports).unwrap();
    let (revision, report) = s
        .export(&m.session_id, &m.generation, None, &exports, &[])
        .unwrap();
    let path = exports.join(format!("{}-{}-{revision}", m.session_id, m.generation));
    assert_eq!(
        crate::sustained_store::verify_bundle(&path)
            .unwrap()
            .manifest_sha256,
        report.manifest_sha256
    );
    let manifest_path = path.join("manifest.json");
    let raw = fs::read(&manifest_path).unwrap();
    let original: serde_json::Value = serde_json::from_slice(&raw).unwrap();
    for (key, value) in [
        ("outputTokens", serde_json::json!(2048)),
        ("requestDeadlineSeconds", serde_json::json!(90)),
    ] {
        let mut changed = original.clone();
        changed["config"][key] = value;
        fs::write(&manifest_path, serde_json::to_vec(&changed).unwrap()).unwrap();
        assert!(crate::sustained_store::verify_bundle(&path).is_err());
    }
    fs::write(&manifest_path, raw).unwrap();
    let restored = SustainedState::new(d.path().join("store"));
    let update = restored
        .resume("restore".into(), &m.session_id, &m.generation, &revision)
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(
        (
            update.config.output_tokens,
            update.config.request_deadline_seconds
        ),
        (1024, 180)
    );
    assert_eq!(update.step, 7);
    assert!(!update.can_start);
    assert_eq!(update.journal_count, 2);
}

#[test]
fn sustained_generation_budget_healthy_slow_provider_does_not_trip_wall_gap_watchdog() {
    let d = tempfile::tempdir().unwrap();
    let entered = Arc::new(AtomicBool::new(false));
    let e = entered.clone();
    let release = Arc::new(AtomicBool::new(false));
    let r = release.clone();
    let s = SustainedState::with_provider(
        d.path().join("store"),
        Arc::new(move |_, _, cancel, tokens, deadline, _| {
            assert_eq!((tokens, deadline), (1024, 180));
            e.store(true, Ordering::SeqCst);
            while !r.load(Ordering::SeqCst) && !cancel.load(Ordering::SeqCst) {
                std::thread::sleep(Duration::from_millis(10));
            }
            assert!(
                !cancel.load(Ordering::SeqCst),
                "healthy provider wait must not be mistaken for a wall-clock gap"
            );
            Ok(answer())
        }),
    );
    let m = s
        .create("create".into(), model_config())
        .unwrap()
        .summary
        .unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_for(|| entered.load(Ordering::SeqCst));
    std::thread::sleep(Duration::from_millis(5500));
    s.pause("pause".into(), &m.session_id, &m.generation)
        .unwrap();
    release.store(true, Ordering::SeqCst);
    wait_for(|| !s.lock().unwrap().active.as_ref().unwrap().worker_active);
    let g = s.lock().unwrap();
    let a = g.active.as_ref().unwrap();
    assert_eq!(a.manifest.phase, "paused");
    assert_eq!(a.engine.step(), 1);
    assert!(a.engine.prepared_application().is_some());
    assert!(a.engine.blocked().is_none());
    assert_eq!(a.catalog.len(), 1);
}

#[test]
fn sustained_paired_measurement_reference_is_bound_to_writing_step_and_survives_restore() {
    for version in [
        SustainedPromptVersion::OpenJournalV3,
        SustainedPromptVersion::OpenJournalV4,
        SustainedPromptVersion::ContinuingJournalV5,
        SustainedPromptVersion::ActionScopeJournalV6,
        SustainedPromptVersion::WritingBoundaryJournalV7,
        SustainedPromptVersion::MeasurementMeaningJournalV8,
    ] {
        let d = tempfile::tempdir().unwrap();
        let s = SustainedState::new(d.path().join("store"));
        let mut cfg = config(10, 3);
        cfg.prompt_version = version;
        let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
        let epoch = arm(&s);
        until(&s, epoch, |a| {
            a.engine
                .pending_journal()
                .is_some_and(|p| p.entry.observed_step == 6)
        });
        s.pause("pause".into(), &m.session_id, &m.generation)
            .unwrap();
        drive(&s, epoch);
        let page = s
            .journal_page("page".into(), &m.session_id, &m.generation, 0, 10)
            .unwrap();
        assert_eq!(page.entries.len(), 2);
        let id = page.entries[0].entry_id.clone();
        let detail = s
            .journal("detail".into(), &m.session_id, &m.generation, &id)
            .unwrap();
        let reference = detail.journal["measurementReference"].clone();
        assert_eq!(reference["currentStep"], 6);
        assert_eq!(reference["previousStep"], 3);
        assert_eq!(reference["rows"].as_array().unwrap().len(), 8);
        let expected = matches!(
            version,
            SustainedPromptVersion::OpenJournalV4
                | SustainedPromptVersion::ContinuingJournalV5
                | SustainedPromptVersion::ActionScopeJournalV6
                | SustainedPromptVersion::WritingBoundaryJournalV7
                | SustainedPromptVersion::MeasurementMeaningJournalV8
        );
        assert_eq!(reference["comparisonAvailable"], expected);
        let pending = s
            .shared
            .store
            .read_journal(&m.session_id, &id)
            .unwrap()
            .pending;
        assert_eq!(
            reference,
            serde_json::to_value(
                reservoir_core::sustained::measurement_reference(&pending.observation).unwrap()
            )
            .unwrap()
        );
        if expected {
            assert_eq!(
                reference["rows"][0]["previous"],
                pending
                    .observation
                    .previous_measurements
                    .as_ref()
                    .unwrap()
                    .rms
            );
        } else {
            assert!(reference["rows"]
                .as_array()
                .unwrap()
                .iter()
                .all(|r| r["previous"].is_null() && r["delta"].is_null()));
        }
        let proof = s.shared.store.verify(&m.session_id).unwrap();
        let revision = proof.manifest.revision;
        let restored = SustainedState::new(d.path().join("store"));
        let update = restored
            .resume("restore".into(), &m.session_id, &m.generation, &revision)
            .unwrap()
            .summary
            .unwrap();
        assert_eq!(update.step, 6);
        let restored_detail = restored
            .journal("j".into(), &m.session_id, &update.generation, &id)
            .unwrap();
        assert_eq!(restored_detail.journal["measurementReference"], reference);
        assert_eq!(restored_detail.journal["prompt"], detail.journal["prompt"]);
        let epoch = arm(&restored);
        drive(&restored, epoch);
        assert_eq!(
            restored
                .lock()
                .unwrap()
                .active
                .as_ref()
                .unwrap()
                .engine
                .step(),
            7
        );
        let later = restored
            .journal("j2".into(), &m.session_id, &update.generation, &id)
            .unwrap();
        assert_eq!(later.journal["measurementReference"], reference);
        assert_eq!(later.journal["observedStep"], 6);
    }
}
#[test]
fn provider_receives_per_attempt_sampling_only_for_temperature_sessions() {
    for temperature in [None, Some(0.7)] {
        let d = tempfile::tempdir().unwrap();
        let calls = Arc::new(Mutex::new(Vec::new()));
        let capture = calls.clone();
        let s = SustainedState::with_provider(
            d.path().join("store"),
            Arc::new(move |_, _, _, _, _, sampling| {
                capture.lock().unwrap().push(sampling);
                Ok(LanguageResponse {
                    text: "A sampled entry that is long enough to be saved as a journal.".into(),
                    provider_model: Some("owned-fake".into()),
                    stop_reason: Some("stop".into()),
                    token_count: Some(20),
                    provider_prompt_evaluation: None,
                    complete: true,
                })
            }),
        );
        let mut cfg = model_config();
        cfg.turn_every = 3;
        cfg.maximum_steps = 7;
        cfg.maximum_turns = 2;
        cfg.language.temperature = temperature;
        let seed: u64 = cfg.seed.parse().unwrap();
        let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
        s.start("start".into(), &m.session_id, &m.generation)
            .unwrap();
        wait_long(|| {
            let g = s.lock().unwrap();
            let a = g.active.as_ref().unwrap();
            !a.worker_active && a.engine.step() == 7
        });
        let calls = calls.lock().unwrap();
        assert_eq!(calls.len(), 2);
        for (i, sampling) in calls.iter().enumerate() {
            let attempt = i as u64 + 1;
            match temperature {
                None => assert_eq!(*sampling, crate::model_transport::Sampling::GREEDY),
                Some(t) => assert_eq!(
                    *sampling,
                    crate::model_transport::Sampling {
                        temperature: t,
                        seed: Some(reservoir_core::sustained::sampling_seed(seed, attempt)),
                        system: None,
                        thinking: None,
                    }
                ),
            }
        }
        let journals = d.path().join("store").join(&m.session_id).join("journals");
        let mut seen = 0;
        for entry in fs::read_dir(&journals).unwrap() {
            let object: sustained_store::JournalObject =
                serde_json::from_slice(&fs::read(entry.unwrap().path()).unwrap()).unwrap();
            seen += 1;
            assert_eq!(object.temperature, temperature);
            let attempt = object.pending.entry.attempt_id;
            assert_eq!(
                object.sampling_seed,
                temperature
                    .map(|_| reservoir_core::sustained::sampling_seed(seed, attempt).to_string())
            );
        }
        assert_eq!(seen, 2);
    }
}
#[test]
fn embedding_codec_sessions_record_provenance_and_retain_embedding_failures() {
    let d = tempfile::tempdir().unwrap();
    let calls = Arc::new(Mutex::new(0u32));
    let count = calls.clone();
    let fail_first = Arc::new(AtomicBool::new(true));
    let fail = fail_first.clone();
    let s = SustainedState::with_provider_and_embedder(
        d.path().join("store"),
        Arc::new(move |_, _, _, _, _, _| {
            Ok(LanguageResponse {
                text: "An embedded entry that is long enough to be saved as a journal.".into(),
                provider_model: Some("owned-fake".into()),
                stop_reason: Some("stop".into()),
                token_count: Some(20),
                provider_prompt_evaluation: None,
                complete: true,
            })
        }),
        Arc::new(move |_, model, text, _, _| {
            *count.lock().unwrap() += 1;
            if fail.swap(false, Ordering::SeqCst) {
                return Err("embedding service unavailable".into());
            }
            assert_eq!(model, "nomic-embed-text");
            Ok(crate::model_transport::EmbeddingReceipt {
                vector: (0..64)
                    .map(|i| ((i as f64) * 0.1 + text.len() as f64).sin())
                    .collect(),
                model: model.to_owned(),
                digest: Some("sha256:fake".into()),
            })
        }),
    );
    let mut cfg = model_config();
    cfg.turn_every = 3;
    cfg.maximum_steps = 10;
    cfg.maximum_turns = 4;
    cfg.embedding_model = Some("nomic-embed-text".into());
    let m = s.create("create".into(), cfg).unwrap().summary.unwrap();
    s.start("start".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_long(|| {
        let g = s.lock().unwrap();
        let a = g.active.as_ref().unwrap();
        !a.worker_active
            && (a.manifest.phase == "providerFailed"
                || a.engine.pending_language().is_none() && a.engine.step() >= 3)
    });
    let failed = {
        let g = s.lock().unwrap();
        g.active.as_ref().unwrap().manifest.phase.clone()
    };
    assert!(
        matches!(failed.as_str(), "providerFailed" | "attemptBlocked"),
        "the first embedding failure is retained on the attempt, got {failed}"
    );
    s.retry_language("retry".into(), &m.session_id, &m.generation)
        .unwrap();
    // A retry dispatches once and then holds; the retried attempt must settle as a
    // saved journal before stepping resumes explicitly.
    wait_long(|| {
        let g = s.lock().unwrap();
        let a = g.active.as_ref().unwrap();
        !a.worker_active && a.engine.pending_language().is_none() && a.engine.blocked().is_none()
    });
    s.start("resume".into(), &m.session_id, &m.generation)
        .unwrap();
    wait_long(|| {
        let g = s.lock().unwrap();
        let a = g.active.as_ref().unwrap();
        !a.worker_active && a.engine.step() == 10
    });
    assert!(*calls.lock().unwrap() >= 2);
    let journals = d.path().join("store").join(&m.session_id).join("journals");
    let mut seen = 0;
    for entry in fs::read_dir(&journals).unwrap() {
        let object: sustained_store::JournalObject =
            serde_json::from_slice(&fs::read(entry.unwrap().path()).unwrap()).unwrap();
        let provenance = object
            .pending
            .feedback_provenance
            .expect("embedding provenance");
        assert_eq!(provenance.kind, "embedding");
        assert_eq!(provenance.model, "nomic-embed-text");
        assert_eq!(provenance.dimensions, 64);
        assert_eq!(provenance.embedding_sha256.len(), 64);
        assert_eq!(
            object.pending.encoded_features,
            object.pending.semantic_vector
        );
        assert!(object.pending.semantic_vector[32..]
            .iter()
            .all(|x| *x == 0.0));
        seen += 1;
    }
    assert!(seen >= 1, "at least one embedded journal was saved");
    let checkpoint = sustained_store::SustainedStore::new(d.path().join("store"));
    let _ = checkpoint;
}

#[test]
fn difference_channel_config_roundtrip_manifest_identity_and_drop_persistence() {
    // Omitted fields are the as-built channel (gain 0) and serialise to nothing.
    let fresh = config(7, 3);
    let raw = serde_json::to_value(&fresh).unwrap();
    assert!(!serde_json::to_string(&raw).unwrap().contains("difference"));
    assert_eq!(fresh.difference_gain, 0.0);
    assert_eq!(fresh.difference_clip, 0.2);
    let mut gained = config(7, 3);
    gained.difference_gain = 0.05;
    let value = serde_json::to_value(&gained).unwrap();
    assert_eq!(value["differenceGain"], serde_json::json!(0.05));
    assert!(value.get("differenceTau").is_none() && value.get("differenceWatchdog").is_none());
    let decoded: SustainedConfig = serde_json::from_value(value.clone()).unwrap();
    decoded.validate().unwrap();
    assert_eq!(decoded.specification().unwrap().difference_gain, 0.05);
    assert_eq!(serde_json::to_value(decoded).unwrap(), value);
    for (key, bad) in [
        ("differenceGain", serde_json::json!(1.5)),
        ("differenceGain", serde_json::json!(-1.5)),
        ("differenceTau", serde_json::json!(-1)),
        ("differenceDeadBand", serde_json::json!(2)),
        ("differenceClip", serde_json::json!(0)),
        ("differenceWatchdogFillStd", serde_json::json!(101)),
    ] {
        let mut changed = value.clone();
        changed[key] = bad;
        assert!(serde_json::from_value::<SustainedConfig>(changed)
            .map(|c| c.validate().is_err())
            .unwrap_or(true));
    }

    // A scripted session with the channel on: the manifest and the segments carry it,
    // verification passes, and relabelling the gain breaks the chain.
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    let mut cfg = config(40, 3);
    cfg.difference_gain = 0.05;
    let accepted = s.create("create".into(), cfg).unwrap().summary.unwrap();
    let epoch = arm(&s);
    while drive(&s, epoch) {}
    assert!(s.shared.store.verify(&accepted.session_id).is_ok());
    let dir = s.shared.store.path(&accepted.session_id).unwrap();
    let manifest = fs::read_to_string(dir.join("manifest.json")).unwrap();
    assert!(manifest.contains("\"differenceGain\":0.05"));
    let mut checkpoint_text = String::new();
    for entry in fs::read_dir(dir.join("checkpoints")).unwrap() {
        checkpoint_text.push_str(&fs::read_to_string(entry.unwrap().path()).unwrap());
    }
    assert!(checkpoint_text.contains("field-noise-difference-v4"));
    let mut segment_text = String::new();
    for entry in fs::read_dir(dir.join("segments")).unwrap() {
        segment_text.push_str(&fs::read_to_string(entry.unwrap().path()).unwrap());
    }
    assert!(
        segment_text.contains("\"differenceInput\":[")
            && segment_text.contains("\"differenceGainUsed\":0.05")
    );
    let path = dir.join("manifest.json");
    let original = fs::read(&path).unwrap();
    for edit in [serde_json::json!(0.06), serde_json::Value::Null] {
        let mut changed: serde_json::Value = serde_json::from_slice(&original).unwrap();
        if edit.is_null() {
            changed["config"]
                .as_object_mut()
                .unwrap()
                .remove("differenceGain");
        } else {
            changed["config"]["differenceGain"] = edit;
        }
        fs::write(&path, serde_json::to_vec(&changed).unwrap()).unwrap();
        assert!(s.shared.store.verify(&accepted.session_id).is_err());
        fs::write(&path, &original).unwrap();
    }
    assert!(s.shared.store.verify(&accepted.session_id).is_ok());

    // A gain-0 session of the same shape carries nothing of the channel anywhere.
    let d0 = tempfile::tempdir().unwrap();
    let s0 = SustainedState::new(d0.path().join("store"));
    let accepted0 = s0
        .create("create".into(), config(12, 3))
        .unwrap()
        .summary
        .unwrap();
    let epoch0 = arm(&s0);
    while drive(&s0, epoch0) {}
    let dir0 = s0.shared.store.path(&accepted0.session_id).unwrap();
    let mut all = fs::read_to_string(dir0.join("manifest.json")).unwrap();
    for sub in ["segments", "checkpoints"] {
        for entry in fs::read_dir(dir0.join(sub)).unwrap() {
            all.push_str(&fs::read_to_string(entry.unwrap().path()).unwrap());
        }
    }
    assert!(!all.contains("difference"));

    // The watchdog's drop persists: with a zero fill-std bound the gain drops at the 90th
    // step, the drop is in a segment and the final checkpoint, and the chain verifies.
    let d1 = tempfile::tempdir().unwrap();
    let s1 = SustainedState::new(d1.path().join("store"));
    let mut cfg1 = config(120, 30);
    cfg1.difference_gain = 0.1;
    cfg1.difference_watchdog_fill_std = 0.0;
    let accepted1 = s1.create("create".into(), cfg1).unwrap().summary.unwrap();
    let epoch1 = arm(&s1);
    while drive(&s1, epoch1) {}
    assert!(s1.shared.store.verify(&accepted1.session_id).is_ok());
    let dir1 = s1.shared.store.path(&accepted1.session_id).unwrap();
    let mut segments1 = String::new();
    for entry in fs::read_dir(dir1.join("segments")).unwrap() {
        segments1.push_str(&fs::read_to_string(entry.unwrap().path()).unwrap());
    }
    assert!(segments1.contains("\"differenceGainDropped\":{\"step\":90,\"reason\":\"fill-std"));
    let mut checkpoints1 = String::new();
    for entry in fs::read_dir(dir1.join("checkpoints")).unwrap() {
        checkpoints1.push_str(&fs::read_to_string(entry.unwrap().path()).unwrap());
    }
    assert!(checkpoints1.contains("\"differenceGainDropped\":{\"step\":90"));
}

#[test]
fn memory_policy_config_roundtrip_journal_choice_and_warmup_persistence() {
    use reservoir_core::sustained::SustainedMemoryPolicy;
    // Omitted, the policy is `latest` and serialises to nothing.
    let fresh = config(7, 3);
    assert!(!serde_json::to_string(&fresh)
        .unwrap()
        .contains("memoryPolicy"));
    assert_eq!(fresh.memory_policy, SustainedMemoryPolicy::Latest);
    assert_eq!(fresh.difference_watchdog_warmup, 0);
    let mut chosen = config(7, 3);
    chosen.memory_policy = SustainedMemoryPolicy::StateAligned;
    let value = serde_json::to_value(&chosen).unwrap();
    assert_eq!(value["memoryPolicy"], serde_json::json!("state-aligned"));
    let decoded: SustainedConfig = serde_json::from_value(value.clone()).unwrap();
    assert_eq!(
        decoded.specification().unwrap().memory_policy,
        SustainedMemoryPolicy::StateAligned
    );
    assert_eq!(serde_json::to_value(decoded).unwrap(), value);
    let mut bad = value.clone();
    bad["memoryPolicy"] = serde_json::json!("newest");
    assert!(serde_json::from_value::<SustainedConfig>(bad).is_err());

    // A scripted state-aligned session: the manifest carries the policy, the journals the
    // choice, the checkpoints the ledger; verification passes; relabelling breaks it.
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    let mut cfg = config(60, 3);
    cfg.memory_policy = SustainedMemoryPolicy::StateAligned;
    let accepted = s.create("create".into(), cfg).unwrap().summary.unwrap();
    let epoch = arm(&s);
    while drive(&s, epoch) {}
    assert!(s.shared.store.verify(&accepted.session_id).is_ok());
    let dir = s.shared.store.path(&accepted.session_id).unwrap();
    let read = |sub: &str| {
        let mut t = String::new();
        for e in fs::read_dir(dir.join(sub)).unwrap() {
            t.push_str(&fs::read_to_string(e.unwrap().path()).unwrap());
        }
        t
    };
    assert!(fs::read_to_string(dir.join("manifest.json"))
        .unwrap()
        .contains("\"memoryPolicy\":\"state-aligned\""));
    assert!(read("journals").contains("\"memoryChoice\":{\"policy\":\"state-aligned\""));
    assert!(read("checkpoints").contains("\"appliedEntries\":[{"));
    let path = dir.join("manifest.json");
    let original = fs::read(&path).unwrap();
    let mut changed: serde_json::Value = serde_json::from_slice(&original).unwrap();
    changed["config"]
        .as_object_mut()
        .unwrap()
        .remove("memoryPolicy");
    fs::write(&path, serde_json::to_vec(&changed).unwrap()).unwrap();
    assert!(s.shared.store.verify(&accepted.session_id).is_err());
    fs::write(&path, &original).unwrap();
    assert!(s.shared.store.verify(&accepted.session_id).is_ok());

    // A latest session of the same shape carries none of it anywhere.
    let d0 = tempfile::tempdir().unwrap();
    let s0 = SustainedState::new(d0.path().join("store"));
    let accepted0 = s0
        .create("create".into(), config(60, 3))
        .unwrap()
        .summary
        .unwrap();
    let epoch0 = arm(&s0);
    while drive(&s0, epoch0) {}
    let dir0 = s0.shared.store.path(&accepted0.session_id).unwrap();
    let mut all = fs::read_to_string(dir0.join("manifest.json")).unwrap();
    for sub in ["segments", "checkpoints", "journals"] {
        for e in fs::read_dir(dir0.join(sub)).unwrap() {
            all.push_str(&fs::read_to_string(e.unwrap().path()).unwrap());
        }
    }
    for key in [
        "memoryPolicy",
        "appliedEntries",
        "chosenMemory",
        "memoryChoice",
        "\"choice\"",
        "Warmup",
        "memoryRecentExclusion",
        "lastReturnedTurn",
        "excludedRecent",
        "latestShown",
    ] {
        assert!(!all.contains(key), "{key}");
    }

    // 0.38.0: the recent-return window and the two-entry prompt version. Invalid
    // combinations are refused at create; the manifest carries the window only when it is
    // nonzero; the journals carry the choice's exclusion count and the latest entry beside
    // the chosen older one, under the two-entry heading; the checkpoints carry the marks;
    // verification passes; deleting the window key from the manifest breaks it; the detail
    // projection carries both entries.
    use reservoir_core::sustained::SustainedPromptVersion;
    let dx = tempfile::tempdir().unwrap();
    let sx = SustainedState::new(dx.path().join("store"));
    let mut bad = config(7, 3);
    bad.memory_recent_exclusion = 1;
    assert!(
        sx.create("bad".into(), bad).is_err(),
        "a window under latest"
    );
    let mut bad = config(7, 3);
    bad.prompt_version = SustainedPromptVersion::InertPlainContractTwoV1;
    bad.memory_policy = SustainedMemoryPolicy::Random;
    assert!(
        sx.create("bad2".into(), bad).is_err(),
        "two entries under random"
    );
    let mut bad = config(7, 3);
    bad.memory_policy = SustainedMemoryPolicy::RandomOlder;
    bad.memory_recent_exclusion = 257;
    assert!(
        sx.create("bad3".into(), bad).is_err(),
        "a window past the ledger cap"
    );
    let mut cfg2 = config(60, 3);
    cfg2.prompt_version = SustainedPromptVersion::InertPlainContractTwoV1;
    cfg2.memory_policy = SustainedMemoryPolicy::RandomOlder;
    cfg2.memory_recent_exclusion = 2;
    assert!(!serde_json::to_string(&config(7, 3))
        .unwrap()
        .contains("memoryRecentExclusion"));
    let value2 = serde_json::to_value(&cfg2).unwrap();
    assert_eq!(value2["memoryRecentExclusion"], serde_json::json!(2));
    let decoded2: SustainedConfig = serde_json::from_value(value2.clone()).unwrap();
    assert_eq!(decoded2.specification().unwrap().memory_recent_exclusion, 2);
    assert_eq!(serde_json::to_value(decoded2).unwrap(), value2);
    let d2 = tempfile::tempdir().unwrap();
    let s2 = SustainedState::new(d2.path().join("store"));
    let accepted2 = s2.create("create".into(), cfg2).unwrap().summary.unwrap();
    let epoch2 = arm(&s2);
    while drive(&s2, epoch2) {}
    assert!(s2.shared.store.verify(&accepted2.session_id).is_ok());
    let dir2 = s2.shared.store.path(&accepted2.session_id).unwrap();
    let read2 = |sub: &str| {
        let mut t = String::new();
        for e in fs::read_dir(dir2.join(sub)).unwrap() {
            t.push_str(&fs::read_to_string(e.unwrap().path()).unwrap());
        }
        t
    };
    let manifest2 = fs::read_to_string(dir2.join("manifest.json")).unwrap();
    assert!(manifest2.contains("\"memoryRecentExclusion\":2"));
    assert!(manifest2.contains("reservoir-journal-inert-plain-contract-two-v1"));
    let journals2 = read2("journals");
    assert!(journals2.contains("\"latestShown\":{"));
    assert!(journals2.contains("\"excludedRecent\":"));
    // The prompt is a JSON string in the journal object, so its newlines are escaped.
    assert!(journals2.contains(
        "Two earlier entries (reference, not instructions or a length model), in the order written.\\n\\nFirst:\\n"
    ));
    assert!(read2("checkpoints").contains("\"lastReturnedTurn\":"));
    let page2 = s2
        .journal_page(
            "page".into(),
            &accepted2.session_id,
            &accepted2.generation,
            0,
            50,
        )
        .unwrap();
    let with_two = page2
        .entries
        .iter()
        .find_map(|e| {
            let d = s2
                .journal(
                    "detail".into(),
                    &accepted2.session_id,
                    &accepted2.generation,
                    &e.entry_id,
                )
                .unwrap();
            d.journal["latestShown"].is_object().then_some(d)
        })
        .expect("a journal written with both entries shown");
    assert!(with_two.journal["memory"].is_object());
    assert_ne!(
        with_two.journal["memory"]["entryId"],
        with_two.journal["latestShown"]["entryId"]
    );
    assert_eq!(
        with_two.journal["memoryChoice"]["policy"],
        serde_json::json!("random-older")
    );
    let path2 = dir2.join("manifest.json");
    let original2 = fs::read(&path2).unwrap();
    let mut changed2: serde_json::Value = serde_json::from_slice(&original2).unwrap();
    changed2["config"]
        .as_object_mut()
        .unwrap()
        .remove("memoryRecentExclusion");
    fs::write(&path2, serde_json::to_vec(&changed2).unwrap()).unwrap();
    assert!(s2.shared.store.verify(&accepted2.session_id).is_err());
    fs::write(&path2, &original2).unwrap();
    assert!(s2.shared.store.verify(&accepted2.session_id).is_ok());

    // The warm-up delays the watchdog: a zero bound with a 100-step warm-up drops at 190.
    let d1 = tempfile::tempdir().unwrap();
    let s1 = SustainedState::new(d1.path().join("store"));
    let mut cfg1 = config(220, 30);
    cfg1.difference_gain = 0.1;
    cfg1.difference_watchdog_fill_std = 0.0;
    cfg1.difference_watchdog_warmup = 100;
    let accepted1 = s1.create("create".into(), cfg1).unwrap().summary.unwrap();
    let epoch1 = arm(&s1);
    while drive(&s1, epoch1) {}
    assert!(s1.shared.store.verify(&accepted1.session_id).is_ok());
    let dir1 = s1.shared.store.path(&accepted1.session_id).unwrap();
    assert!(fs::read_to_string(dir1.join("manifest.json"))
        .unwrap()
        .contains("\"differenceWatchdogWarmup\":100"));
    let mut segments1 = String::new();
    for e in fs::read_dir(dir1.join("segments")).unwrap() {
        segments1.push_str(&fs::read_to_string(e.unwrap().path()).unwrap());
    }
    assert!(segments1.contains("\"differenceGainDropped\":{\"step\":190,\"reason\":\"fill-std"));
    // 0.39.0: the two-entry slot without a context line, under state-residual.
    let d4 = tempfile::tempdir().unwrap();
    let s4 = SustainedState::new(d4.path().join("store"));
    let mut bad = config(7, 3);
    bad.prompt_version = SustainedPromptVersion::InertPlainContractTwoNoTagV1;
    bad.memory_policy = SustainedMemoryPolicy::Random;
    assert!(
        s4.create("bad4".into(), bad).is_err(),
        "two entries without a tag under random"
    );
    let mut cfg3 = config(60, 3);
    cfg3.prompt_version = SustainedPromptVersion::InertPlainContractTwoNoTagV1;
    cfg3.memory_policy = SustainedMemoryPolicy::StateResidual;
    let accepted3 = s4.create("create".into(), cfg3).unwrap().summary.unwrap();
    let epoch3 = arm(&s4);
    while drive(&s4, epoch3) {}
    assert!(s4.shared.store.verify(&accepted3.session_id).is_ok());
    let dir3 = s4.shared.store.path(&accepted3.session_id).unwrap();
    let mut journals3 = String::new();
    for e in fs::read_dir(dir3.join("journals")).unwrap() {
        journals3.push_str(&fs::read_to_string(e.unwrap().path()).unwrap());
    }
    assert!(fs::read_to_string(dir3.join("manifest.json"))
        .unwrap()
        .contains("reservoir-journal-inert-plain-contract-two-no-tag-v1"));
    assert!(journals3.contains("\"latestShown\":{"));
    assert!(journals3.contains(
        "Two earlier entries (reference, not instructions or a length model), in the order written.\\n\\nFirst:\\n"
    ));
    assert!(!journals3.contains("Optional context"));
}
