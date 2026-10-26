use super::*;

fn limits(s: &SustainedState) -> (SustainedRunLimits, String) {
    let summary = s.get("limits".into(), None).unwrap().summary.unwrap();
    (summary.effective_limits, summary.revision)
}
fn extend(
    s: &SustainedState,
    id: &str,
    generation: &str,
    new: SustainedRunLimits,
) -> SustainedSummary {
    let revision = limits(s).1;
    s.extend_limits("extend".into(), id, generation, &revision, new)
        .unwrap()
        .summary
        .unwrap()
}

#[test]
fn run_limit_extension_continues_same_journal_and_exports_restores_exact_history() {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    let mut cfg = config(20, 2);
    cfg.maximum_turns = 1;
    let original = serde_json::to_value(&cfg).unwrap();
    let initial = s.create("create".into(), cfg).unwrap().summary.unwrap();
    let (id, generation) = (initial.session_id, initial.generation);
    let epoch = arm(&s);
    while drive(&s, epoch) {}
    let before = s.shared.store.verify(&id).unwrap();
    assert_eq!(before.manifest.journal_count, 1);
    assert_eq!(before.manifest.phase, "budgetReached");
    assert!(!s.is_busy());
    let prior_entry = before.checkpoint.state.held_journal_id.clone();
    let mut new = limits(&s).0;
    new.maximum_turns = 2;
    let result = extend(&s, &id, &generation, new.clone());
    assert_eq!(result.session_id, id);
    assert_eq!(result.generation, generation);
    assert_eq!(result.phase, "paused");
    assert_eq!(result.journal_count, 1);
    assert!(result.can_start);
    assert_eq!(result.limit_extension_count, 1);
    assert!(s.is_busy());
    assert_eq!(serde_json::to_value(result.config).unwrap(), original);
    assert_eq!(
        s.shared
            .store
            .verify(&id)
            .unwrap()
            .checkpoint
            .state
            .held_journal_id,
        prior_entry
    );
    let epoch = arm(&s);
    while drive(&s, epoch) {}
    let finished = s.shared.store.verify(&id).unwrap();
    assert_eq!(finished.manifest.journal_count, 2);
    assert_eq!(finished.manifest.effective_limits(), new);
    assert_eq!(finished.checkpoint.state.attempt_cursor, 2);
    let destination = d.path().join("export");
    fs::create_dir(&destination).unwrap();
    let exported = s
        .export(&id, &generation, None, &destination, &[])
        .unwrap()
        .1;
    assert_eq!(exported.manifest_sha256, finished.report.manifest_sha256);
    s.stop("stop".into(), &id, &generation).unwrap();
    let stopped = s.shared.store.verify(&id).unwrap();
    let restored = s
        .resume(
            "restore".into(),
            &id,
            &stopped.manifest.generation,
            &stopped.manifest.revision,
        )
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(restored.effective_limits, new);
    assert_eq!(restored.limit_extension_count, 1);
    assert_eq!(restored.journal_count, 2);
    assert!(!restored.can_start); // Restoring cannot erase exhausted attempt totals.
    new.maximum_turns = 3;
    assert!(extend(&s, &id, &restored.generation, new).can_start);
}

#[test]
fn duration_only_and_repeated_extensions_preserve_elapsed_time_and_original_limits() {
    let (_d, s, id, generation) = setup(20, 10);
    {
        let mut g = s.lock().unwrap();
        let a = g.active.as_mut().unwrap();
        a.manifest.elapsed_millis = a.manifest.config.maximum_duration_seconds * 1000;
        a.manifest.phase = "budgetReached".into();
        s.persist(a).unwrap();
    }
    let original = s.shared.store.verify(&id).unwrap();
    let mut new = limits(&s).0;
    new.maximum_duration_seconds += 3600;
    let first = extend(&s, &id, &generation, new.clone());
    assert_eq!(first.phase, "paused");
    assert!(first.can_start);
    assert_eq!(
        first.elapsed_seconds,
        original.manifest.elapsed_millis as f64 / 1000.0
    );
    assert_eq!(first.config.maximum_duration_seconds, 21600);
    new.maximum_steps += 10;
    new.maximum_duration_seconds += 3600;
    let second = extend(&s, &id, &generation, new.clone());
    assert_eq!(second.limit_extension_count, 2);
    let saved = s.shared.store.verify(&id).unwrap();
    assert_eq!(saved.manifest.effective_limits(), new);
    assert_eq!(
        saved.manifest.elapsed_millis,
        original.manifest.elapsed_millis
    );
    assert_eq!(saved.checkpoint.state.step, original.checkpoint.state.step);
    assert_eq!(
        saved.checkpoint.state.rng_state,
        original.checkpoint.state.rng_state
    );
    assert_eq!(saved.manifest.limit_extensions[0].limits.maximum_steps, 20);
    assert_eq!(saved.manifest.limit_extensions[1].limits.maximum_steps, 30);
}

#[test]
fn extension_rejects_decreases_noop_caps_stale_identity_and_active_or_storage_held_states() {
    let (_d, s, id, generation) = setup(20, 10);
    let (old, revision) = limits(&s);
    let reject = |proposed: SustainedRunLimits| {
        assert!(s
            .extend_limits("bad".into(), &id, &generation, &revision, proposed)
            .is_err())
    };
    reject(old.clone());
    reject(SustainedRunLimits {
        maximum_steps: 19,
        maximum_turns: 101,
        ..old.clone()
    });
    reject(SustainedRunLimits {
        maximum_steps: 21,
        maximum_turns: 99,
        ..old.clone()
    });
    reject(SustainedRunLimits {
        maximum_steps: 21,
        maximum_duration_seconds: 21599,
        ..old.clone()
    });
    reject(SustainedRunLimits {
        maximum_steps: 1_000_001,
        ..old.clone()
    });
    reject(SustainedRunLimits {
        maximum_turns: 10_001,
        ..old.clone()
    });
    reject(SustainedRunLimits {
        maximum_duration_seconds: 86_401,
        ..old.clone()
    });
    let new = SustainedRunLimits {
        maximum_steps: 21,
        ..old.clone()
    };
    assert!(s
        .extend_limits("bad".into(), &id, "wrong", &revision, new.clone())
        .is_err());
    assert!(s
        .extend_limits("bad".into(), &id, &generation, "0", new.clone())
        .is_err());
    arm(&s);
    reject(new.clone());
    {
        let mut g = s.lock().unwrap();
        let a = g.active.as_mut().unwrap();
        a.run_requested = false;
        a.manifest.phase = "budgetReached".into();
        sustained_store::hold_storage(&mut a.manifest);
    }
    reject(new);
    assert_eq!(limits(&s).0, old);
}

#[test]
fn extension_save_failures_keep_old_runtime_budget_and_publication_readback_is_exact() {
    for stage in [1, 3, 4] {
        let (_d, s, id, generation) = setup(20, 10);
        let (old, revision) = limits(&s);
        let new = SustainedRunLimits {
            maximum_steps: 30,
            ..old.clone()
        };
        s.shared.store.fail_next(stage);
        let result = s.extend_limits("extend".into(), &id, &generation, &revision, new.clone());
        if stage == 4 {
            assert_eq!(result.unwrap().summary.unwrap().effective_limits, new);
            assert_eq!(
                s.shared
                    .store
                    .verify(&id)
                    .unwrap()
                    .manifest
                    .effective_limits(),
                new
            );
        } else {
            assert!(result.is_err());
            assert_eq!(limits(&s).0, old);
            assert_eq!(
                s.shared
                    .store
                    .verify(&id)
                    .unwrap()
                    .manifest
                    .effective_limits(),
                old
            );
            assert_eq!(
                extend(&s, &id, &generation, new.clone()).effective_limits,
                new
            );
        }
        let g = s.lock().unwrap();
        let a = g.active.as_ref().unwrap();
        assert!(!a.run_requested && !a.worker_active);
        assert_eq!(a.manifest.phase, "paused");
        assert!(a.engine.events().is_empty());
    }
}

#[test]
fn extension_retains_prepared_writing_and_rejects_forged_receipts() {
    let (_d, s, id, generation) = setup(20, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_language().is_some());
    s.pause("pause".into(), &id, &generation).unwrap();
    assert!(matches!(s.worker_boundary(epoch).unwrap(), Work::Done));
    let before = s.shared.store.verify(&id).unwrap();
    let new = SustainedRunLimits {
        maximum_steps: 30,
        ..limits(&s).0
    };
    s.shared.store.fail_next(4);
    assert!(extend(&s, &id, &generation, new).can_start);
    let after = s.shared.store.verify(&id).unwrap();
    assert_eq!(
        serde_json::to_value(before.checkpoint.state.phase).unwrap(),
        serde_json::to_value(after.checkpoint.state.phase).unwrap()
    );
    assert_eq!(after.manifest.journal_count, 0);
    let path = s.shared.store.path(&id).unwrap().join("manifest.json");
    let pristine = fs::read(&path).unwrap();
    let mut forged: serde_json::Value = serde_json::from_slice(&pristine).unwrap();
    forged["limitExtensions"][0]["limits"]["maximumDurationSeconds"] = 86400.into();
    fs::write(&path, serde_json::to_vec(&forged).unwrap()).unwrap();
    assert!(s.shared.store.verify(&id).is_err());
    fs::write(&path, &pristine).unwrap();
    let mut forged: serde_json::Value = serde_json::from_slice(&pristine).unwrap();
    forged["limitExtensions"] = serde_json::json!([]);
    fs::write(&path, serde_json::to_vec(&forged).unwrap()).unwrap();
    assert!(s.shared.store.verify(&id).is_err());
    fs::write(&path, &pristine).unwrap();
    assert!(s.shared.store.verify(&id).is_ok());
}

#[test]
fn duration_extension_does_not_clear_an_exhausted_step_limit() {
    let (_d, s, id, generation) = setup(2, 10);
    let epoch = arm(&s);
    while drive(&s, epoch) {}
    let new = SustainedRunLimits {
        maximum_duration_seconds: 25200,
        ..limits(&s).0
    };
    let result = extend(&s, &id, &generation, new);
    assert_eq!(result.phase, "paused");
    assert_eq!(result.step, 2);
    assert!(!result.can_start);
    assert!(s.start("start".into(), &id, &generation).is_err());
    assert_eq!(s.shared.store.verify(&id).unwrap().checkpoint.state.step, 2);
}

#[test]
fn limit_extension_command_is_granted_to_the_bundled_main_window() {
    let manifests: serde_json::Value =
        serde_json::from_str(include_str!("../gen/schemas/acl-manifests.json")).unwrap();
    let capabilities: serde_json::Value =
        serde_json::from_str(include_str!("../gen/schemas/capabilities.json")).unwrap();
    let main = &capabilities["main"];
    assert_eq!(main["windows"], serde_json::json!(["main"]));
    assert_eq!(main["local"], serde_json::json!(true));
    assert!(main["remote"].is_null());
    assert!(main["permissions"]
        .as_array()
        .unwrap()
        .contains(&serde_json::json!("allow-extend-sustained-limits")));
    assert_eq!(
        manifests["__app-acl__"]["permissions"]["allow-extend-sustained-limits"]["commands"]
            ["allow"],
        serde_json::json!(["extend_sustained_limits"])
    );
    assert!(include_str!("main.rs").contains("sustained_commands::extend_sustained_limits,"));
}
