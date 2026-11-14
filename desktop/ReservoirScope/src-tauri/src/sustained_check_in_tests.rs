use super::*;
use reservoir_core::sustained::{SustainedCheckInSchedule, SustainedCheckInStatus};

fn scheduled(
    interval: u64,
    end: u64,
    telemetry: bool,
) -> (tempfile::TempDir, SustainedState, String, String) {
    let d = tempfile::tempdir().unwrap();
    let s = SustainedState::new(d.path().join("store"));
    let cfg = SustainedConfig {
        check_in_schedule: Some(SustainedCheckInSchedule {
            interval_seconds: interval,
            end_after_seconds: end,
            prompt: "tell me, friend, about your idle thoughts or curiosities".into(),
            include_telemetry: telemetry,
        }),
        maximum_duration_seconds: end,
        maximum_steps: 100_000,
        maximum_turns: 10_000,
        turn_every: 30,
        pace_ms: 1000,
        ..Default::default()
    };
    let created = s.create("create".into(), cfg).unwrap().summary.unwrap();
    (d, s, created.session_id, created.generation)
}
fn elapsed(s: &SustainedState, millis: u64) {
    let mut g = s.lock().unwrap();
    let a = g.active.as_mut().unwrap();
    a.manifest.elapsed_millis = millis;
    a.last_accounted = Instant::now();
}
fn complete(s: &SustainedState) -> bool {
    s.lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .check_in_complete()
}
fn check_in_applied(a: &Active, ordinal: u64) -> bool {
    a.engine
        .check_in_state()
        .unwrap()
        .outcomes
        .iter()
        .any(|o| o.ordinal == ordinal && o.status == SustainedCheckInStatus::Applied)
}

#[test]
fn six_hour_schedule_dispatches_each_once_and_saves_applies_final_then_stops() {
    let (d, s, id, generation) = scheduled(3600, 21600, false);
    let epoch = arm(&s);
    assert!(drive(&s, epoch));
    elapsed(&s, 3_599_000);
    assert!(drive(&s, epoch));
    assert!(s
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .check_in_state()
        .unwrap()
        .outcomes
        .is_empty());
    for ordinal in 1..=6 {
        elapsed(&s, ordinal * 3_600_000);
        for _ in 0..20 {
            if check_in_applied(s.lock().unwrap().active.as_ref().unwrap(), ordinal) {
                break;
            }
            let running = drive(&s, epoch);
            if !running {
                assert_eq!(ordinal, 6);
            }
        }
        assert!(check_in_applied(
            s.lock().unwrap().active.as_ref().unwrap(),
            ordinal
        ));
    }
    assert!(complete(&s));
    let summary = s.get("get".into(), None).unwrap().summary.unwrap();
    assert_eq!(summary.phase, "scheduleComplete");
    assert_eq!(summary.journal_count, 6);
    assert!(!summary.can_start);
    assert!(!s.is_busy());
    assert!(!drive(&s, epoch));
    assert_eq!(
        s.shared.store.verify(&id).unwrap().manifest.journal_count,
        6
    );
    let check_ins = summary.check_ins.unwrap();
    assert_eq!(check_ins.slots.len(), 6);
    assert!(check_ins.slots.iter().all(|slot| slot.status == "applied"));
    let last = check_ins.slots.last().unwrap();
    let detail = s
        .journal(
            "last".into(),
            &id,
            &generation,
            last.entry_id.as_ref().unwrap(),
        )
        .unwrap();
    assert_eq!(detail.journal["checkIn"]["ordinal"], 6);
    assert_eq!(detail.journal["observationSupplied"], false);
    assert!(detail.journal["application"].is_object());
    let exports = d.path().join("exports");
    fs::create_dir(&exports).unwrap();
    s.export(&id, &generation, None, &exports, &[]).unwrap();
    s.stop("stop".into(), &id, &generation).unwrap();
    let saved = s.shared.store.verify(&id).unwrap();
    let restored = s
        .resume(
            "restore".into(),
            &id,
            &saved.manifest.generation,
            &saved.manifest.revision,
        )
        .unwrap()
        .summary
        .unwrap();
    assert!(restored.check_ins.unwrap().complete);
    assert_eq!(restored.phase, "scheduleComplete");
    assert!(!restored.can_start && !restored.can_extend_limits);
    assert!(!s.is_busy());
}

#[test]
fn missed_slots_are_visible_and_nonmultiple_end_is_final() {
    let (_d, s, id, _) = scheduled(2, 7, true);
    let epoch = arm(&s);
    assert!(drive(&s, epoch));
    elapsed(&s, 7000);
    for _ in 0..20 {
        if !drive(&s, epoch) {
            break;
        }
    }
    assert!(complete(&s));
    let summary = s.get("get".into(), None).unwrap().summary.unwrap();
    let slots = summary.check_ins.unwrap().slots;
    assert_eq!(
        slots
            .iter()
            .map(|s| s.scheduled_seconds)
            .collect::<Vec<_>>(),
        vec![2, 4, 6, 7]
    );
    assert_eq!(
        slots.iter().map(|s| s.status.as_str()).collect::<Vec<_>>(),
        vec!["missed", "missed", "missed", "applied"]
    );
    assert_eq!(
        s.shared.store.verify(&id).unwrap().manifest.journal_count,
        1
    );
}

#[test]
fn paused_edit_preserves_prepared_prompt_and_survives_recovery() {
    let (_d, s, id, generation) = scheduled(2, 4, false);
    let epoch = arm(&s);
    assert!(drive(&s, epoch));
    elapsed(&s, 2000);
    {
        let mut g = s.lock().unwrap();
        let a = g.active.as_mut().unwrap();
        assert!(a.engine.admit_due_check_in(2000).unwrap());
        s.persist(a).unwrap();
    }
    let paused = s
        .pause("pause".into(), &id, &generation)
        .unwrap()
        .summary
        .unwrap();
    assert!(paused.check_ins.unwrap().can_edit);
    let edited = s
        .update_check_in_settings(
            "edit".into(),
            &id,
            &generation,
            &paused.revision,
            "What are you curious about now?".into(),
            true,
        )
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(edited.check_ins.unwrap().settings.revision, 1);
    assert!(s
        .update_check_in_settings(
            "stale".into(),
            &id,
            &generation,
            &paused.revision,
            "stale".into(),
            false
        )
        .is_err());
    let epoch = arm(&s);
    match s.worker_boundary(epoch).unwrap() {
        Work::Provider(p, sampling) => {
            assert_eq!(
                p.prompt,
                "tell me, friend, about your idle thoughts or curiosities"
            );
            assert!(sampling.system.is_none());
            assert!(p.memory.is_none());
            assert_eq!(p.check_in.as_ref().unwrap().settings_revision, 0);
            s.settle(epoch, p.attempt_id, Ok(answer()), None, 1)
                .unwrap();
        }
        _ => panic!("expected frozen first check-in"),
    }
    until(&s, epoch, |a| check_in_applied(a, 1));
    elapsed(&s, 4000);
    match s.worker_boundary(epoch).unwrap() {
        Work::Provider(p, _) => {
            assert!(p.prompt.contains("What are you curious about now?"));
            assert!(p.prompt.contains("Current local runtime readout:"));
            assert!(p.memory.is_some());
            assert_eq!(p.check_in.as_ref().unwrap().settings_revision, 1);
            s.settle(epoch, p.attempt_id, Ok(answer()), None, 1)
                .unwrap();
        }
        _ => panic!("expected edited final check-in"),
    }
    while drive(&s, epoch) {}
    let verified = s.shared.store.verify(&id).unwrap();
    assert_eq!(
        verified
            .checkpoint
            .state
            .check_in_state
            .as_ref()
            .unwrap()
            .settings_revisions
            .len(),
        1
    );
    s.stop("stop".into(), &id, &generation).unwrap();
    let saved = s.shared.store.verify(&id).unwrap();
    let restored = s
        .resume(
            "restore".into(),
            &id,
            &saved.manifest.generation,
            &saved.manifest.revision,
        )
        .unwrap()
        .summary
        .unwrap();
    let ci = restored.check_ins.unwrap();
    assert_eq!(ci.settings_history.len(), 2);
    assert!(ci.settings.include_telemetry);
    assert_eq!(ci.slots[0].settings_revision, Some(0));
    assert_eq!(ci.slots[1].settings_revision, Some(1));
}

#[test]
fn schedule_validation_requires_headroom_and_matching_original_duration() {
    let schedule = SustainedCheckInSchedule {
        interval_seconds: 3600,
        end_after_seconds: 21600,
        prompt: "Hello".into(),
        include_telemetry: true,
    };
    let mut cfg = SustainedConfig {
        check_in_schedule: Some(schedule),
        ..Default::default()
    };
    assert!(cfg.validate().is_err()); // Earlier defaults can end the run too soon.
    cfg.maximum_steps = 21607;
    cfg.maximum_turns = 727;
    cfg.validate().unwrap();
    cfg.maximum_duration_seconds = 21601;
    assert!(cfg.validate().is_err());
}

#[test]
fn sleep_gap_does_not_advance_schedule_and_editing_never_resumes() {
    let (_d, s, id, generation) = scheduled(3600, 21600, false);
    let epoch = arm(&s);
    assert!(drive(&s, epoch));
    elapsed(&s, 1000);
    {
        let mut g = s.lock().unwrap();
        g.active.as_mut().unwrap().last_accounted = Instant::now() - Duration::from_secs(7200);
    }
    s.interrupt("test sleep");
    assert!(!drive(&s, epoch));
    let interrupted = s.get("get".into(), None).unwrap().summary.unwrap();
    assert_eq!(interrupted.elapsed_seconds, 1.0);
    assert!(interrupted
        .check_ins
        .as_ref()
        .unwrap()
        .slots
        .iter()
        .all(|s| s.status == "pending"));
    s.update_check_in_settings(
        "edit".into(),
        &id,
        &generation,
        &interrupted.revision,
        "After the pause".into(),
        true,
    )
    .unwrap();
    let g = s.lock().unwrap();
    let a = g.active.as_ref().unwrap();
    assert!(!a.run_requested && !a.worker_active);
    assert_eq!(a.manifest.elapsed_millis, 1000);
}

#[test]
fn check_in_command_has_narrow_permission() {
    assert!(include_str!("../build.rs").contains("\"update_sustained_check_in_settings\""));
    assert!(include_str!("../capabilities/main.json")
        .contains("allow-update-sustained-check-in-settings"));
}

#[test]
fn final_failure_holds_and_plain_retry_keeps_frozen_settings() {
    let (_d, s, id, generation) = scheduled(2, 4, false);
    let epoch = arm(&s);
    assert!(drive(&s, epoch));
    elapsed(&s, 4000);
    let original = match s.worker_boundary(epoch).unwrap() {
        Work::Provider(p, sampling) => {
            assert!(sampling.system.is_none());
            p
        }
        _ => panic!("final check-in request expected"),
    };
    s.settle(
        epoch,
        original.attempt_id,
        Err("test provider failure".into()),
        None,
        1,
    )
    .unwrap();
    assert!(!drive(&s, epoch));
    let failed = s.get("get".into(), None).unwrap().summary.unwrap();
    assert!(!failed.check_ins.as_ref().unwrap().complete);
    assert_eq!(failed.check_ins.as_ref().unwrap().slots[1].status, "failed");
    s.update_check_in_settings(
        "edit".into(),
        &id,
        &generation,
        &failed.revision,
        "Future wording".into(),
        true,
    )
    .unwrap();
    {
        let mut g = s.lock().unwrap();
        let a = g.active.as_mut().unwrap();
        a.engine.retry_language().unwrap();
        s.persist(a).unwrap();
    }
    let epoch = arm(&s);
    match s.worker_boundary(epoch).unwrap() {
        Work::Provider(p, sampling) => {
            assert_eq!(p.prompt, original.prompt);
            assert_eq!(p.check_in, original.check_in);
            assert!(p.memory.is_none() && p.latest_shown.is_none() && p.memory_choice.is_none());
            assert!(sampling.system.is_none());
            assert!(p.attempt_id > original.attempt_id);
            s.settle(epoch, p.attempt_id, Ok(answer()), None, 1)
                .unwrap();
        }
        _ => panic!("plain retry expected"),
    }
    while drive(&s, epoch) {}
    assert!(complete(&s));
    assert_eq!(
        s.shared.store.verify(&id).unwrap().manifest.journal_count,
        1
    );
}

#[test]
fn deadline_during_ordinary_request_applies_that_reply_before_final_check_in() {
    let (_d, s, id, generation) = scheduled(2, 2, false);
    let epoch = arm(&s);
    // Prepare an ordinary step-triggered opportunity before the deadline.
    until(&s, epoch, |a| a.engine.pending_language().is_some());
    let ordinary = match s.worker_boundary(epoch).unwrap() {
        Work::Provider(p, _) => p,
        _ => panic!("ordinary"),
    };
    assert!(ordinary.check_in.is_none());
    elapsed(&s, 2000);
    s.settle(epoch, ordinary.attempt_id, Ok(answer()), None, 1)
        .unwrap();
    assert!(drive(&s, epoch));
    let first = s
        .journal_page("page".into(), &id, &generation, 0, 10)
        .unwrap();
    assert_eq!(first.entries.len(), 1);
    assert_eq!(first.entries[0].status, "applied");
    let scheduled = match s.worker_boundary(epoch).unwrap() {
        Work::Provider(p, _) => p,
        _ => panic!("check-in"),
    };
    assert!(scheduled.check_in.as_ref().unwrap().final_check_in);
    assert_eq!(
        scheduled.observed_step,
        first.entries[0].first_applied_step.unwrap()
    );
    s.settle(epoch, scheduled.attempt_id, Ok(answer()), None, 1)
        .unwrap();
    while drive(&s, epoch) {}
    assert_eq!(
        s.shared.store.verify(&id).unwrap().manifest.journal_count,
        2
    );
}

#[test]
fn explicit_final_skip_completes_with_a_visible_gap() {
    let (_d, s, id, generation) = scheduled(2, 2, false);
    let epoch = arm(&s);
    assert!(drive(&s, epoch));
    elapsed(&s, 2000);
    let p = match s.worker_boundary(epoch).unwrap() {
        Work::Provider(p, _) => p,
        _ => panic!("check-in"),
    };
    s.settle(epoch, p.attempt_id, Err("test error".into()), None, 1)
        .unwrap();
    assert!(!drive(&s, epoch));
    let result = s
        .skip("skip".into(), &id, &generation, None, Some(p.attempt_id))
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(result.phase, "scheduleComplete");
    assert_eq!(result.journal_count, 0);
    assert_eq!(result.check_ins.unwrap().slots[0].status, "skipped");
    assert!(!result.can_start);
    s.shared.store.verify(&id).unwrap();
}

#[test]
fn retry_excludes_the_paused_gap_from_running_time() {
    let (_d, s, id, generation) = scheduled(3600, 21600, false);
    let epoch = arm(&s);
    assert!(drive(&s, epoch));
    elapsed(&s, 3_600_000);
    let p = match s.worker_boundary(epoch).unwrap() {
        Work::Provider(p, _) => p,
        _ => panic!("check-in"),
    };
    s.settle(epoch, p.attempt_id, Err("test error".into()), None, 1)
        .unwrap();
    assert!(!drive(&s, epoch));
    {
        let mut g = s.lock().unwrap();
        g.active.as_mut().unwrap().last_accounted = Instant::now() - Duration::from_secs(7200);
    }
    s.retry_language("retry".into(), &id, &generation).unwrap();
    wait_for(|| !s.lock().unwrap().active.as_ref().unwrap().worker_active);
    let summary = s.get("get".into(), None).unwrap().summary.unwrap();
    assert!(
        summary.elapsed_seconds < 3660.0,
        "paused retry gap was charged: {}",
        summary.elapsed_seconds
    );
    let slots = summary.check_ins.unwrap().slots;
    assert_eq!(slots[0].status, "saved");
    assert!(slots[1..].iter().all(|slot| slot.status == "pending"));
    s.stop("stop".into(), &id, &generation).unwrap();
}

#[test]
fn recovery_holds_an_uncertain_check_in_and_rejects_forged_elapsed_time() {
    let (d, s, id, generation) = scheduled(2, 4, false);
    let epoch = arm(&s);
    assert!(drive(&s, epoch));
    elapsed(&s, 2000);
    let p = match s.worker_boundary(epoch).unwrap() {
        Work::Provider(p, _) => p,
        _ => panic!("check-in"),
    };
    let saved = s.shared.store.verify(&id).unwrap();
    drop(s);
    let restored_state = SustainedState::new(d.path().join("store"));
    let restored = restored_state
        .resume("restore".into(), &id, &generation, &saved.manifest.revision)
        .unwrap()
        .summary
        .unwrap();
    assert!(!restored.can_start);
    assert!(restored.can_retry_provider);
    let slot = &restored.check_ins.as_ref().unwrap().slots[0];
    assert_eq!(slot.status, "failed");
    assert_eq!(slot.attempt_id, Some(p.attempt_id));
    assert_eq!(slot.prompt.as_deref(), Some(p.prompt.as_str()));
    assert_eq!(restored.journal_count, 0);
    let path = d.path().join("store").join(&id).join("manifest.json");
    let mut manifest: serde_json::Value =
        serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
    manifest["elapsedMillis"] = 0.into();
    fs::write(&path, serde_json::to_vec(&manifest).unwrap()).unwrap();
    assert!(restored_state.shared.store.verify(&id).is_err());
}

#[test]
fn failed_final_application_commit_can_retry_to_durable_completed_state_once() {
    let (_d, s, id, generation) = scheduled(2, 2, false);
    let epoch = arm(&s);
    assert!(drive(&s, epoch));
    elapsed(&s, 2000);
    let p = match s.worker_boundary(epoch).unwrap() {
        Work::Provider(p, _) => p,
        _ => panic!("check-in"),
    };
    s.settle(epoch, p.attempt_id, Ok(answer()), None, 1)
        .unwrap();
    s.pause("pause".into(), &id, &generation).unwrap();
    assert!(!drive(&s, epoch));
    assert!(s
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .engine
        .prepared_application()
        .is_some());
    let epoch = arm(&s);
    s.shared.store.fail_next(3);
    assert!(s.worker_boundary(epoch).is_err());
    let held = s.get("held".into(), None).unwrap().summary.unwrap();
    assert_eq!(held.phase, "storageBlocked");
    assert!(!held.check_ins.as_ref().unwrap().complete);
    assert_eq!(held.check_ins.as_ref().unwrap().slots[0].status, "saved");
    assert_eq!(held.step, p.observed_step + 1);
    assert!(held.can_retry_save);
    let retried = s
        .retry_save("retry".into(), &id, &generation)
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(retried.phase, "scheduleComplete");
    assert_eq!(retried.step, p.observed_step + 1);
    assert_eq!(retried.durable_step, retried.step);
    assert!(retried.check_ins.unwrap().complete);
    assert!(!s.is_busy());
    let verified = s.shared.store.verify(&id).unwrap();
    assert_eq!(verified.manifest.journal_count, 1);
    assert_eq!(
        verified.checkpoint.state.check_in_state.unwrap().outcomes[0].applied_step,
        Some(p.observed_step + 1)
    );
}
