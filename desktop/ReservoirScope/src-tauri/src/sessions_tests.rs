use super::*;
use std::{fs, thread};
fn fixture() -> (tempfile::TempDir, SessionState) {
    let d = tempfile::tempdir().unwrap();
    let lib = LibraryState::new(
        d.path().join("library-v1"),
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources"),
    );
    let s = SessionState::new(d.path().join("sessions-v1"), lib);
    (d, s)
}
fn config(recipe: &str, steps: usize) -> SessionConfig {
    SessionConfig {
        recipe: recipe.into(),
        seed: u64::MAX.to_string(),
        steps,
        turn_every: 2,
        leak: 0.65,
        noise_amplitude: 0.0,
        retention: 0.955,
        exploration_controls: None,
        action_mode: ComparisonMode::IndependentGeneration,
        action_input_strength: 1.0,
        action_bias_enabled: false,
        action_compare_previous: false,
        action_comparison_kind: ComparisonKind::Components,
        action_forcing_profile: ForcingProfile::PulsedSensoryV1,
        language: LanguageConfiguration::default(),
    }
}
fn create(s: &SessionState, recipe: &str, steps: usize) -> SessionSummary {
    s.create("create".into(), config(recipe, steps))
        .unwrap()
        .summary
        .unwrap()
}
fn step(s: &SessionState, a: &SessionSummary) -> SessionUpdate {
    s.step("step".into(), &a.session_id, &a.generation, false)
        .unwrap()
}
fn summary(s: &SessionState) -> SessionSummary {
    s.get("get".into(), None).unwrap().summary.unwrap()
}
#[test]
fn every_recipe_has_finite_steps_and_verified_existing_format() {
    for recipe in [
        "exploration",
        "stage1",
        "stage2",
        "stage3",
        "stage4",
        "journalD",
        "journalE",
    ] {
        let (_d, s) = fixture();
        let a = create(&s, recipe, 4);
        for _ in 0..4 {
            let u = step(&s, &a);
            if u.pending_journal.is_some() {
                s.save_journal("save".into(), &a.session_id, &a.generation)
                    .unwrap();
            }
        }
        assert_eq!(summary(&s).phase, "completed", "{recipe}");
        let (_, b, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
        let report = reservoir_core::verify_bytes(&b);
        assert_eq!(
            report.status,
            reservoir_core::VerificationStatus::Passed,
            "{recipe}: {:?}",
            report.diagnostics
        );
        assert!(s
            .step("beyond".into(), &a.session_id, &a.generation, false)
            .is_err());
    }
}
#[test]
fn pending_save_failure_retry_and_application_are_distinct() {
    let (d, s) = fixture();
    let a = create(&s, "journalE", 5);
    step(&s, &a);
    let u = step(&s, &a);
    let pending = u.pending_journal.unwrap();
    assert_eq!(u.summary.unwrap().durable_step, 0);
    assert!(s.snapshot(&a.session_id, &a.generation).is_err());
    assert!(s
        .step("blocked".into(), &a.session_id, &a.generation, false)
        .is_err());
    let obstruction = d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join(&pending.relative_path);
    fs::create_dir(&obstruction).unwrap();
    let failed = s
        .save_journal("save".into(), &a.session_id, &a.generation)
        .unwrap();
    assert!(failed.pending_journal.is_some());
    assert_eq!(failed.summary.unwrap().journal_count, 0);
    assert!(s
        .step("blocked".into(), &a.session_id, &a.generation, false)
        .is_err());
    fs::remove_dir(obstruction).unwrap();
    let saved = s
        .save_journal("retry".into(), &a.session_id, &a.generation)
        .unwrap();
    assert!(saved.pending_journal.is_none());
    assert_eq!(saved.summary.unwrap().journal_count, 1);
    let c = s.store.read_checkpoint(&a.session_id).unwrap();
    assert_eq!(
        c.attempts
            .iter()
            .map(|a| a.status.as_str())
            .collect::<Vec<_>>(),
        vec!["failed", "committed"]
    );
    let turn = s
        .turn("turn".into(), a.session_id.clone(), a.generation.clone(), 0)
        .unwrap()
        .turn;
    assert_eq!(turn.journal_saved, Some(true));
    assert_eq!(turn.application_step, None);
    let applied = step(&s, &a).frame.unwrap();
    assert_eq!(applied.frame.semantic_turn_id, Some("1".into()));
    assert_eq!(
        s.turn("t".into(), a.session_id, a.generation, 0)
            .unwrap()
            .turn
            .application_step,
        Some("3".into())
    );
}
#[test]
fn committed_journal_turn_reads_entry_text_and_preserves_raw_reply_and_prompt() {
    let (_d, s) = fixture();
    let a = create(&s, "journalE", 7);
    let mut expected = Vec::new();
    for _ in 0..2 {
        step(&s, &a);
        let pending = step(&s, &a).pending_journal.unwrap();
        let raw = {
            let i = s.lock().unwrap();
            let Engine::Journal(j) = &i.active.as_ref().unwrap().engine else {
                unreachable!()
            };
            j.pending_journal().unwrap().raw_reply.clone()
        };
        s.save_journal("save".into(), &a.session_id, &a.generation)
            .unwrap();
        expected.push((pending, raw));
    }
    assert_ne!(expected[0].0.id, expected[1].0.id);
    for (index, (pending, raw)) in expected.iter().enumerate() {
        let t = s
            .turn(
                "read".into(),
                a.session_id.clone(),
                a.generation.clone(),
                index,
            )
            .unwrap()
            .turn;
        assert_eq!(t.journal_saved, Some(true));
        assert_eq!(t.reply.as_deref(), Some(pending.text.as_str()));
        assert_eq!(t.raw_reply.as_deref(), Some(raw.as_str()));
        assert_ne!(t.reply, t.raw_reply);
        assert_eq!(t.prompt.as_bytes(), pending.prompt.as_bytes());
        assert_eq!(
            t.journal_relative_path.as_deref(),
            Some(pending.relative_path.as_str())
        );
    }
    // The saved portable record also retains the exact original action reply;
    // changing the reader DTO must not rewrite recorded evidence.
    let (_, bytes, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
    let record: ActionComparisonRecord = serde_json::from_slice(&bytes).unwrap();
    for (index, (pending, raw)) in expected.iter().enumerate() {
        let action = &record.right.actions[index];
        assert_eq!(action.prompt.as_bytes(), pending.prompt.as_bytes());
        assert_eq!(action.raw_reply.as_deref(), Some(raw.as_str()));
    }
}
#[test]
fn standalone_action_stages_and_modes_preserve_existing_record_contracts() {
    for stage in 1..=8 {
        for mode in [
            ComparisonMode::IndependentGeneration,
            ComparisonMode::FixedReplay,
        ] {
            let (_d, s) = fixture();
            let mut c = config(&format!("action{}", (b'A' + stage - 1) as char), 7);
            c.action_mode = mode;
            let a = s.create("create".into(), c).unwrap().summary.unwrap();
            let action = a.action.as_ref().unwrap();
            assert_eq!(action.stage, stage);
            assert_eq!(action.mode, mode);
            assert_eq!(
                action.reply_tape.as_ref().map(|t| t.packet_count),
                (mode == ComparisonMode::FixedReplay).then_some(6)
            );
            assert!(!a.can_request_journal);
            for _ in 0..7 {
                let u = step(&s, &a);
                let frame = u.frame.unwrap();
                assert_eq!(frame.frame.fill_percent.is_some(), stage >= 3);
                assert_eq!(frame.control.is_some(), stage == 8);
                if u.pending_journal.is_some() {
                    s.save_journal("save".into(), &a.session_id, &a.generation)
                        .unwrap();
                }
            }
            assert_eq!(summary(&s).phase, "completed");
            let (_, bytes, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
            let report = reservoir_core::verify_bytes(&bytes);
            assert_eq!(
                report.status,
                reservoir_core::VerificationStatus::Passed,
                "stage {stage} {mode:?}: {:?}",
                report.diagnostics
            );
            let record: ActionComparisonRecord = serde_json::from_slice(&bytes).unwrap();
            assert!(record.left.is_none());
            assert_eq!(record.right.stage, stage);
            assert_eq!(record.tape.is_some(), mode == ComparisonMode::FixedReplay);
            assert_eq!(record.right.actions.len(), if stage >= 4 { 3 } else { 0 });
            assert!(s.store.read_checkpoint(&a.session_id).is_ok());
        }
    }
}

#[test]
fn memory_requires_new_physical_read_and_failure_is_retained_without_exposure() {
    for recipe in ["actionF", "actionG", "actionH"] {
        for mode in [
            ComparisonMode::IndependentGeneration,
            ComparisonMode::FixedReplay,
        ] {
            let (d, s) = fixture();
            let mut c = config(recipe, 7);
            c.action_mode = mode;
            let a = s.create("create".into(), c).unwrap().summary.unwrap();
            step(&s, &a);
            let p = step(&s, &a).pending_journal.unwrap();
            s.save_journal("save".into(), &a.session_id, &a.generation)
                .unwrap();
            // Remove a once-durable file. A cached in-memory entry must not make
            // the next prompt succeed, in either independent or tape mode.
            fs::remove_file(
                d.path()
                    .join("sessions-v1")
                    .join(&a.session_id)
                    .join(&p.relative_path),
            )
            .unwrap();
            step(&s, &a);
            let u = step(&s, &a);
            let failed = u.summary.unwrap();
            assert_eq!(failed.phase, "failed");
            assert!(failed
                .save_error
                .as_ref()
                .unwrap()
                .contains("memory read failed"));
            assert!(u.pending_journal.is_none());
            let t = s
                .turn(
                    "failed".into(),
                    a.session_id.clone(),
                    a.generation.clone(),
                    1,
                )
                .unwrap()
                .turn;
            assert_eq!(t.failure_phase.as_deref(), Some("memoryRead"));
            assert_eq!(t.request_started, Some(false));
            assert_eq!(t.memory_entry_ids, vec![p.id]);
            assert!(t.memory_text.is_none());
            assert!(t.memory_entry_sha256.is_none());
            assert!(t.raw_reply.is_none());
            assert!(t.chosen_action.is_none());
            assert!(t.journal_saved.is_none());
            assert!(t.application_step.is_none());
            assert!(!t.prompt.contains(&p.text));
            assert!(s
                .step("late".into(), &a.session_id, &a.generation, false)
                .is_err());
            let (_, bytes, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
            let report = reservoir_core::verify_bytes(&bytes);
            assert_eq!(
                report.status,
                reservoir_core::VerificationStatus::Passed,
                "{recipe} {mode:?}: {:?}",
                report.diagnostics
            );
            assert_eq!(
                s.store.read_checkpoint(&a.session_id).unwrap().durable_step,
                4
            );
        }
    }
}

#[test]
fn manual_memory_read_rejects_tampered_journal_without_repair_or_cached_text() {
    let (d, s) = fixture();
    let a = create(&s, "actionF", 7);
    step(&s, &a);
    let p = step(&s, &a).pending_journal.unwrap();
    s.save_journal("save".into(), &a.session_id, &a.generation)
        .unwrap();
    step(&s, &a);
    let path = d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join(&p.relative_path);
    let mut changed: JournalEntry = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
    changed.text = "Different retained text".into();
    changed.sha256 = files::digest(changed.text.as_bytes());
    let corrupt = serde_json::to_vec(&changed).unwrap();
    fs::write(&path, &corrupt).unwrap();
    assert!(summary(&s).can_request_journal);
    let result = s
        .request_journal("manual".into(), &a.session_id, &a.generation)
        .unwrap();
    assert_eq!(result.summary.unwrap().phase, "failed");
    assert!(result.pending_journal.is_none());
    assert_eq!(fs::read(&path).unwrap(), corrupt);
    let t = s
        .turn(
            "inspect".into(),
            a.session_id.clone(),
            a.generation.clone(),
            1,
        )
        .unwrap()
        .turn;
    assert_eq!(t.failure_phase.as_deref(), Some("memoryRead"));
    assert_eq!(t.request_started, Some(false));
    assert!(t.raw_reply.is_none());
    assert!(t.memory_text.is_none());
    assert!(t.semantic_vector.is_none());
    assert_eq!(summary(&s).journal_count, 1);
    let (_, bytes, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
    assert_eq!(
        reservoir_core::verify_bytes(&bytes).status,
        reservoir_core::VerificationStatus::Passed
    );
}

#[cfg(unix)]
#[test]
fn memory_read_refuses_symlink_file_and_symlink_owned_journal_directory() {
    use std::os::unix::fs::symlink;
    for link_directory in [false, true] {
        let (d, s) = fixture();
        let a = create(&s, "actionH", 7);
        step(&s, &a);
        let p = step(&s, &a).pending_journal.unwrap();
        s.save_journal("save".into(), &a.session_id, &a.generation)
            .unwrap();
        let dir = d
            .path()
            .join("sessions-v1")
            .join(&a.session_id)
            .join("right");
        if link_directory {
            let outside = d.path().join("outside-right");
            fs::rename(&dir, &outside).unwrap();
            symlink(outside, &dir).unwrap();
        } else {
            let path = dir.join(format!("{}.json", p.id));
            let outside = d.path().join("outside-entry.json");
            fs::rename(&path, &outside).unwrap();
            symlink(outside, path).unwrap();
        }
        step(&s, &a);
        let u = step(&s, &a);
        // A checkpoint can itself be storageBlocked by the changed directory;
        // the underlying portable outcome must still be the terminal read failure.
        assert!(matches!(
            u.summary.unwrap().phase.as_str(),
            "failed" | "storageBlocked"
        ));
        let t = s
            .turn("read".into(), a.session_id.clone(), a.generation.clone(), 1)
            .unwrap()
            .turn;
        assert_eq!(t.failure_phase.as_deref(), Some("memoryRead"));
        assert_eq!(t.request_started, Some(false));
        assert!(t.memory_text.is_none());
        assert!(t.raw_reply.is_none());
        assert!(t.application_step.is_none());
        let (_, bytes, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
        let r: ActionComparisonRecord = serde_json::from_slice(&bytes).unwrap();
        assert_eq!(r.right.journals.len(), 1);
        assert_eq!(r.right.frames.last().unwrap().semantic_action_id, Some(1));
        assert_eq!(
            reservoir_core::verify_bytes(&bytes).status,
            reservoir_core::VerificationStatus::Passed
        );
    }
}

#[test]
fn wait_preserves_held_feedback_and_latest_saved_memory_and_is_checkpointed() {
    for mode in [
        ComparisonMode::IndependentGeneration,
        ComparisonMode::FixedReplay,
    ] {
        let (_d, s) = fixture();
        let mut c = config("actionG", 8);
        c.action_mode = mode;
        let a = s.create("create".into(), c).unwrap().summary.unwrap();
        let mut last = None;
        for _ in 0..6 {
            let u = step(&s, &a);
            if let Some(p) = u.pending_journal {
                s.save_journal("save".into(), &a.session_id, &a.generation)
                    .unwrap();
                last = Some(p);
            }
        }
        let p = last.unwrap();
        let t = s
            .turn("wait".into(), a.session_id.clone(), a.generation.clone(), 2)
            .unwrap()
            .turn;
        assert_eq!(t.chosen_action.as_deref(), Some("WAIT"));
        assert_eq!(t.memory_entry_ids, vec![p.id.clone()]);
        assert_eq!(t.memory_text.as_deref(), Some(p.text.as_str()));
        assert_eq!(t.memory_entry_sha256.as_deref(), Some(p.sha256.as_str()));
        assert!(t.prompt.contains(&p.text));
        assert!(t.reply.is_none());
        assert!(t.raw_reply.as_ref().unwrap().contains("WAIT"));
        assert!(t.journal_saved.is_none());
        assert!(t.journal_entry_id.is_none());
        assert!(t.journal_sha256.is_none());
        assert!(t.application_step.is_none());
        assert_eq!(
            t.request_started,
            Some(mode == ComparisonMode::IndependentGeneration)
        );
        assert_eq!(
            t.tape_packet_id.as_deref(),
            (mode == ComparisonMode::FixedReplay).then_some("6")
        );
        assert_eq!(summary(&s).journal_count, 2);
        assert_eq!(
            s.store.read_checkpoint(&a.session_id).unwrap().durable_step,
            6
        );
        let before = s
            .frame(
                "before".into(),
                a.session_id.clone(),
                a.generation.clone(),
                5,
            )
            .unwrap()
            .frame
            .unwrap();
        let after = step(&s, &a).frame.unwrap();
        assert_eq!(before.frame.semantic_turn_id, Some("2".into()));
        assert_eq!(after.frame.semantic_turn_id, Some("2".into()));
        assert_eq!(before.frame.input[18..], after.frame.input[18..]);
        // Manual action remains forced WRITE even when choice is otherwise open.
        assert!(summary(&s).can_request_journal);
        let forced = s
            .request_journal("manual".into(), &a.session_id, &a.generation)
            .unwrap();
        assert!(forced.pending_journal.is_some());
        assert!(!forced.summary.unwrap().can_request_journal);
    }
}

#[test]
fn action_controller_receipt_distinguishes_used_and_next_retention() {
    let (_d, s) = fixture();
    let mut c = config("actionH", 3);
    c.turn_every = 30;
    c.action_input_strength = 0.0;
    let a = s.create("quiet".into(), c).unwrap().summary.unwrap();
    let first = step(&s, &a).frame.unwrap();
    let second = step(&s, &a).frame.unwrap();
    assert!(first.frame.state.iter().all(|v| *v == 0.0));
    assert_eq!(first.frame.retention_used, Some(a.config.retention));
    assert_eq!(
        second.frame.retention_used,
        Some(first.control.as_ref().unwrap().applied_retention)
    );
    assert_eq!(
        first.frame.next_retention,
        Some(first.control.as_ref().unwrap().applied_retention)
    );
    assert_ne!(first.frame.retention_used, first.frame.next_retention);
    assert!(first.control.unwrap().error.is_finite());
    assert_eq!(summary(&s).turn_count, 0);
    let (_, bytes, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
    let record: ActionComparisonRecord = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(record.specification.input_strength, 0.0);
    assert!(!record.specification.bias_enabled);
}

#[test]
fn legacy_journal_checkpoints_default_mode_and_new_action_fields_are_bound() {
    let (d, s) = fixture();
    let a = create(&s, "journalE", 3);
    step(&s, &a);
    s.pause("pause".into(), &a.session_id, &a.generation)
        .unwrap();
    let path = d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join("checkpoint.json");
    let mut metadata: Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
    for name in [
        "actionMode",
        "actionInputStrength",
        "actionBiasEnabled",
        "actionComparePrevious",
        "actionComparisonKind",
        "actionForcingProfile",
    ] {
        metadata["config"].as_object_mut().unwrap().remove(name);
    }
    fs::write(&path, serde_json::to_vec(&metadata).unwrap()).unwrap();
    assert!(s.store.read_checkpoint(&a.session_id).is_ok());
    for (key, value) in [
        ("actionMode", json!("fixedReplay")),
        ("actionInputStrength", json!(0.5)),
        ("actionBiasEnabled", json!(true)),
        ("recipe", json!("actionH")),
    ] {
        let mut changed = metadata.clone();
        changed["config"][key] = value;
        fs::write(&path, serde_json::to_vec(&changed).unwrap()).unwrap();
        assert!(s.store.read_checkpoint(&a.session_id).is_err(), "{key}");
    }
}
#[test]
fn committed_journal_checkpoint_failure_recovers_without_double_feedback() {
    let (_d, s) = fixture();
    let a = create(&s, "journalE", 5);
    step(&s, &a);
    step(&s, &a);
    s.store
        .fail_committed_checkpoint
        .store(true, Ordering::Release);
    let failed = s
        .save_journal("save".into(), &a.session_id, &a.generation)
        .unwrap();
    assert!(failed.pending_journal.is_none());
    assert_eq!(failed.summary.unwrap().phase, "storageBlocked");
    assert!(s
        .step("blocked".into(), &a.session_id, &a.generation, false)
        .is_err());
    let retried = s
        .save_record("retry".into(), &a.session_id, &a.generation)
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(retried.phase, "paused");
    assert!(retried.can_step);
    assert_eq!(retried.journal_count, 1);
    step(&s, &a);
    let checkpoint = s.store.read_checkpoint(&a.session_id).unwrap();
    assert_eq!(checkpoint.attempts.len(), 1);
    assert_eq!(checkpoint.attempts[0].status, "committed");
    assert_eq!(summary(&s).journal_count, 1);
}
#[test]
fn explicit_failed_save_is_terminal_and_exportable() {
    let (_d, s) = fixture();
    let a = create(&s, "journalE", 5);
    step(&s, &a);
    step(&s, &a);
    let stopped = s.stop("stop".into(), &a.session_id, &a.generation).unwrap();
    assert_eq!(stopped.summary.unwrap().phase, "failed");
    assert!(stopped.pending_journal.is_none());
    assert!(s
        .save_journal("retry".into(), &a.session_id, &a.generation)
        .is_err());
    let (_, bytes, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
    assert_eq!(
        reservoir_core::verify_bytes(&bytes).status,
        reservoir_core::VerificationStatus::Passed
    );
    let t = s
        .turn("turn".into(), a.session_id, a.generation, 0)
        .unwrap()
        .turn;
    assert_eq!(t.journal_saved, Some(false));
    assert!(t.raw_reply.is_some());
    assert!(t.application_step.is_none());
}
#[test]
fn stale_controls_pause_reset_and_old_worker_cannot_mutate_replacement() {
    let (_d, s) = fixture();
    let a = create(&s, "exploration", 10);
    step(&s, &a);
    assert!(s
        .reset("reset".into(), &a.session_id, &a.generation, false)
        .is_err());
    let b = s
        .reset("reset".into(), &a.session_id, &a.generation, true)
        .unwrap()
        .summary
        .unwrap();
    assert_ne!(a.session_id, b.session_id);
    assert!(s.pause("old".into(), &a.session_id, &a.generation).is_err());
    assert!(!s.pause_requested.load(Ordering::Acquire));
    assert!(s
        .update_controls(
            "old".into(),
            &a.session_id,
            &a.generation,
            ExplorationControls::default()
        )
        .is_err());
    {
        let mut i = s.inner.lock().unwrap();
        let a = i.active.as_mut().unwrap();
        a.phase = "running".into();
        a.worker_epoch = 2;
    }
    s.worker((b.session_id.clone(), b.generation.parse().unwrap(), 1));
    assert_eq!(summary(&s).step, 0);
    s.stop("stop".into(), &b.session_id, &b.generation).unwrap();
}
#[test]
fn scheduler_runs_without_ui_and_close_flag_pauses_without_resuming() {
    let (_d, s) = fixture();
    let a = create(&s, "exploration", 100);
    s.run(
        "run".into(),
        &a.session_id,
        &a.generation,
        Arc::new(|_| true),
    )
    .unwrap();
    let deadline = Instant::now() + Duration::from_secs(2);
    while summary(&s).step < 2 && Instant::now() < deadline {
        thread::sleep(Duration::from_millis(5));
    }
    assert!(summary(&s).step >= 2);
    s.request_close_pause();
    while summary(&s).phase == "running" && Instant::now() < deadline {
        thread::sleep(Duration::from_millis(5));
    }
    let paused = s.get("get".into(), None).unwrap();
    assert!(paused.close_requested);
    assert_eq!(paused.summary.as_ref().unwrap().phase, "paused");
    let count = paused.summary.unwrap().step;
    s.cancel_close();
    thread::sleep(Duration::from_millis(50));
    assert_eq!(summary(&s).step, count);
    assert!(!s.get("get".into(), None).unwrap().close_requested);
}
#[test]
fn persistence_cadence_and_controls_are_bound_to_actual_frames() {
    let (d, s) = fixture();
    let a = create(&s, "exploration", 100);
    for _ in 0..29 {
        step(&s, &a);
    }
    assert_eq!(summary(&s).durable_step, 0);
    let controls = ExplorationControls {
        repeat_input: true,
        leak: 0.2,
        ..ExplorationControls::default()
    };
    s.update_controls(
        "controls".into(),
        &a.session_id,
        &a.generation,
        controls.clone(),
    )
    .unwrap();
    let frame = step(&s, &a).frame.unwrap();
    assert_eq!(frame.exploration_controls, Some(controls));
    assert_eq!(summary(&s).durable_step, 30);
    assert_eq!(
        s.frame("old".into(), a.session_id.clone(), a.generation.clone(), 0)
            .unwrap()
            .frame
            .unwrap()
            .exploration_controls
            .unwrap()
            .leak,
        0.65
    );
    for _ in 0..60 {
        step(&s, &a);
    }
    let records = d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join("records");
    assert_eq!(fs::read_dir(records).unwrap().count(), 2);
    assert_eq!(summary(&s).durable_step, 90);
}
#[test]
fn stage_context_provenance_is_not_promoted_to_a_model_or_journal() {
    let (_d, s) = fixture();
    let a = create(&s, "stage2", 4);
    step(&s, &a);
    step(&s, &a);
    let t = s
        .turn("turn".into(), a.session_id, a.generation, 0)
        .unwrap()
        .turn;
    assert_eq!(t.backend, Some("example".into()));
    assert_eq!(t.context_kind, Some("preparedExampleContext".into()));
    assert_eq!(t.journal_saved, None);
}
#[test]
fn close_refuses_writes_and_unsaved_then_closing_rejects_commands() {
    let (_d, s) = fixture();
    let a = create(&s, "exploration", 2);
    let export = s.begin_export().unwrap();
    assert!(!s.finish_close(true).unwrap());
    drop(export);
    assert!(!s.finish_close(false).unwrap());
    assert!(s.finish_close(true).unwrap());
    assert!(!s.needs_review());
    assert!(s.get("closed".into(), None).is_err());
    assert!(s
        .step("closed".into(), &a.session_id, &a.generation, false)
        .is_err());
    assert!(s.begin_export().is_err());
}
#[test]
fn clean_close_refuses_inflight_mutation_even_when_atomics_still_look_clean() {
    let (_d, s) = fixture();
    let a = create(&s, "exploration", 4);
    step(&s, &a);
    s.save_record("save".into(), &a.session_id, &a.generation)
        .unwrap();
    assert!(!s.needs_review());
    // This is the same protected interval used by step(): its computation has
    // started but its completed frame has not yet changed the dirty atomic.
    let mut in_flight = s.lock().unwrap();
    assert!(!s.needs_review());
    assert!(!s.authorize_clean_close());
    s.advance(in_flight.active.as_mut().unwrap(), false)
        .unwrap();
    drop(in_flight);
    assert!(s.needs_review());
    assert!(!s.authorize_clean_close());
    s.save_record("save-again".into(), &a.session_id, &a.generation)
        .unwrap();
    assert!(s.authorize_clean_close());
    assert!(s.authorize_clean_close());
    assert!(s
        .step("too-late".into(), &a.session_id, &a.generation, false)
        .is_err());
    assert!(s.begin_export().is_err());
}

#[test]
fn clean_close_serializes_with_first_creation_and_export_without_blocking() {
    let (_d, s) = fixture();
    let mut creating = s.lock().unwrap();
    assert!(!s.needs_review());
    assert!(!s.authorize_clean_close());
    let c = config("exploration", 2);
    s.create_locked(
        &mut creating,
        "create".into(),
        c.clone(),
        Engine::new(&c).unwrap(),
    )
    .unwrap();
    drop(creating);
    assert!(!s.authorize_clean_close());

    let (_d, empty) = fixture();
    let export = empty.begin_export().unwrap();
    assert!(!empty.authorize_clean_close());
    drop(export);
    assert!(empty.authorize_clean_close());
    assert!(empty.authorize_clean_close());
    assert!(empty.create("too-late".into(), c).is_err());
    assert!(empty.get("too-late".into(), None).is_err());
    assert!(empty.begin_export().is_err());
}

#[test]
fn returning_from_other_labs_close_review_reopens_finite_owner() {
    let (_d, s) = fixture();
    assert!(s.authorize_clean_close());
    assert!(s.create("closed".into(), config("exploration", 3)).is_err());
    s.cancel_close();
    let a = create(&s, "exploration", 3);
    assert!(s.execution_busy()); // Unsaved genesis must be retained first.
    s.save_record("save".into(), &a.session_id, &a.generation)
        .unwrap();
    assert!(!s.execution_busy());
    let write = s.begin_export().unwrap();
    assert!(s.execution_busy());
    drop(write);
    step(&s, &a);
    assert!(s.execution_busy());
}
#[test]
fn stale_close_completion_reopens_gate_without_erasing_new_review() {
    let (_d, s) = fixture();
    assert!(s.authorize_clean_close());
    s.request_close_pause();
    s.reopen_after_stale_close();
    assert!(s.get("new-review".into(), None).unwrap().close_requested);
    assert!(s.pause_requested.load(Ordering::Acquire));
    assert!(!s.closing.load(Ordering::Acquire));
}
#[test]
fn created_library_origin_survives_scan_and_index_failure_keeps_files() {
    let (d, s) = fixture();
    let a = create(&s, "exploration", 2);
    step(&s, &a);
    step(&s, &a);
    let saved = s
        .save_record("save".into(), &a.session_id, &a.generation)
        .unwrap()
        .summary
        .unwrap();
    assert!(!saved.unsaved_record);
    let page = s
        .library
        .query(crate::library::LibraryQuery {
            origin: Some("created".into()),
            ..Default::default()
        })
        .unwrap();
    assert_eq!(page.entries.len(), 1);
    assert_eq!(page.entries[0].origin, "created");
    s.library.scan(false).unwrap();
    assert_eq!(
        s.library
            .query(crate::library::LibraryQuery {
                origin: Some("created".into()),
                ..Default::default()
            })
            .unwrap()
            .entries
            .len(),
        1
    );
    let b = s
        .reset("reset".into(), &a.session_id, &a.generation, false)
        .unwrap()
        .summary
        .unwrap();
    s.step("pulse".into(), &b.session_id, &b.generation, true)
        .unwrap();
    let index = d.path().join("library-v1/index.sqlite3");
    fs::remove_file(&index).unwrap();
    fs::create_dir(&index).unwrap();
    let result = s
        .save_record("save".into(), &b.session_id, &b.generation)
        .unwrap()
        .summary
        .unwrap();
    assert!(!result.unsaved_record);
    assert!(result
        .diagnostics
        .iter()
        .any(|x| x.contains("index update failed")));
    let hash = result.library_entry_id.unwrap().replace("sha256:", "");
    assert!(d
        .path()
        .join("library-v1/records")
        .join(format!("{hash}.json"))
        .is_file());
}

#[test]
fn stopped_checkpoint_retry_never_resumes_a_terminal_engine() {
    for recipe in ["exploration", "stage1", "journalD"] {
        let (d, s) = fixture();
        let a = create(&s, recipe, 5);
        step(&s, &a);
        let cp = d
            .path()
            .join("sessions-v1")
            .join(&a.session_id)
            .join("checkpoint.json");
        let original = fs::read(&cp).unwrap();
        fs::remove_file(&cp).unwrap();
        fs::create_dir(&cp).unwrap();
        let stopped = s
            .stop("stop".into(), &a.session_id, &a.generation)
            .unwrap()
            .summary
            .unwrap();
        assert_eq!(stopped.phase, "storageBlocked");
        fs::remove_dir(&cp).unwrap();
        fs::write(&cp, original).unwrap();
        let saved = s
            .save_record("retry".into(), &a.session_id, &a.generation)
            .unwrap()
            .summary
            .unwrap();
        assert_eq!(saved.phase, "stopped", "{recipe}");
        assert!(!saved.can_step);
        assert!(!saved.can_run);
        assert!(s
            .step("forbidden".into(), &a.session_id, &a.generation, false)
            .is_err());
    }
}
#[test]
fn recovered_checkpoint_metadata_must_agree_with_retained_record_and_pending_text() {
    let (d, s) = fixture();
    let a = create(&s, "journalE", 5);
    step(&s, &a);
    step(&s, &a);
    let cp = d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join("checkpoint.json");
    let original = fs::read(&cp).unwrap();
    let base: Value = serde_json::from_slice(&original).unwrap();
    for mutation in 0..6 {
        let mut v = base.clone();
        match mutation {
            0 => v["durableStep"] = json!(2),
            1 => v["pendingJournal"]["entry"]["text"] = json!("changed"),
            2 => v["pendingJournal"]["relativePath"] = json!("../../outside"),
            3 => v["pendingJournal"]["observedStep"] = json!(1),
            4 => v["config"]["seed"] = json!("1"),
            _ => v["step"] = json!(601),
        }
        fs::write(&cp, serde_json::to_vec(&v).unwrap()).unwrap();
        assert!(
            s.store.read_checkpoint(&a.session_id).is_err(),
            "mutation {mutation}"
        );
    }
    fs::write(&cp, original).unwrap();
    let c = s.store.read_checkpoint(&a.session_id).unwrap();
    assert_eq!(c.step, 2);
    assert_eq!(c.durable_step, 0);
    assert!(c.pending_journal.is_some());
    let page = s.store.recovery().unwrap();
    assert_eq!(page.entries[0].durable_step, 0);
    assert_eq!(page.entries[0].step, 2);
}
#[cfg(unix)]
#[test]
fn recovery_refuses_nested_symlink_directories_and_reports_incomplete_files() {
    let (d, s) = fixture();
    let a = create(&s, "exploration", 2);
    let root = d.path().join("sessions-v1").join(&a.session_id);
    let c = s.store.read_checkpoint(&a.session_id).unwrap();
    let hash = c.record_sha256.unwrap();
    let records = root.join("records");
    let moved = d.path().join("moved-records");
    fs::rename(&records, &moved).unwrap();
    std::os::unix::fs::symlink(&moved, &records).unwrap();
    assert!(s.store.read_record(&a.session_id, &hash).is_err());
    assert!(s.store.read_checkpoint(&a.session_id).is_err());
    assert_eq!(s.store.recovery().unwrap().entries[0].phase, "incomplete");
    fs::remove_file(&records).unwrap();
    fs::rename(&moved, &records).unwrap();
    fs::write(root.join("right/.incomplete-journal"), b"partial").unwrap();
    assert!(s
        .store
        .recovery()
        .unwrap()
        .incomplete_writes
        .iter()
        .any(|x| x.contains(".incomplete-journal")));
}
#[test]
fn recovery_cutoff_is_explicit_and_existing_journal_retry_preserves_exact_bytes() {
    let (d, s) = fixture();
    let a = create(&s, "journalD", 5);
    step(&s, &a);
    let p = step(&s, &a).pending_journal.unwrap();
    let entry = {
        let i = s.inner.lock().unwrap();
        let Engine::Journal(j) = &i.active.as_ref().unwrap().engine else {
            panic!()
        };
        j.pending_journal().unwrap().entry.clone()
    };
    let first = s.store.commit_journal(&a.session_id, &entry).unwrap();
    let second = s.store.commit_journal(&a.session_id, &entry).unwrap();
    assert_eq!(first.1, second.1);
    let path = d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join(p.relative_path);
    let bytes = fs::read(&path).unwrap();
    fs::write(&path, b"changed").unwrap();
    assert!(s.store.commit_journal(&a.session_id, &entry).is_err());
    fs::write(path, bytes).unwrap();
    let right = d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join("right");
    for n in 0..1001 {
        fs::write(right.join(format!("extra-{n}")), []).unwrap();
    }
    assert!(s.store.recovery().unwrap().truncated);
}
#[test]
fn invalid_seed_provider_recipe_and_unmarked_store_are_rejected() {
    let (d, s) = fixture();
    let mut c = config("exploration", 3);
    c.seed = "18446744073709551616".into();
    assert!(s.create("bad".into(), c).is_err());
    assert!(s.create("bad".into(), config("ollama", 3)).is_err());
    let root = d.path().join("sessions-v1");
    fs::create_dir(&root).unwrap();
    fs::write(root.join("foreign"), b"untouched").unwrap();
    let a = create(&s, "exploration", 3);
    assert_eq!(a.phase, "storageBlocked");
    assert_eq!(fs::read(root.join("foreign")).unwrap(), b"untouched");
    assert!(!root.join("owner.txt").exists());
}

#[test]
fn reset_storage_failure_returns_retained_terminal_state_instead_of_stale_candidate() {
    let (d, s) = fixture();
    let a = create(&s, "journalE", 5);
    step(&s, &a);
    step(&s, &a);
    let cp = d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join("checkpoint.json");
    let old = fs::read(&cp).unwrap();
    fs::remove_file(&cp).unwrap();
    fs::create_dir(&cp).unwrap();
    let failed = s
        .reset("reset".into(), &a.session_id, &a.generation, true)
        .unwrap();
    assert!(failed.pending_journal.is_none());
    let summary = failed.summary.unwrap();
    assert_eq!(summary.session_id, a.session_id);
    assert_eq!(summary.phase, "storageBlocked");
    assert!(!summary.can_run);
    fs::remove_dir(&cp).unwrap();
    fs::write(cp, old).unwrap();
    let retry = s
        .save_record("retain".into(), &a.session_id, &a.generation)
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(retry.phase, "failed");
    assert!(!retry.can_run);
}

fn paired_config(recipe: &str, mode: ComparisonMode) -> SessionConfig {
    let mut c = config(recipe, 7);
    c.action_compare_previous = true;
    c.action_mode = mode;
    c
}
fn save_current(s: &SessionState, a: &SessionSummary) -> SessionUpdate {
    let p = s
        .get("candidate".into(), None)
        .unwrap()
        .pending_journal
        .unwrap();
    let u = s
        .save_journal_for(
            "save".into(),
            &a.session_id,
            &a.generation,
            arm_label(p.arm),
            &p.id,
        )
        .unwrap();
    assert_ne!(
        u.pending_journal.as_ref().map(|x| (x.arm, x.id.as_str())),
        Some((p.arm, p.id.as_str())),
        "{:?}",
        u.summary.as_ref().unwrap().save_error
    );
    u
}
#[test]
fn matched_component_pairs_b_through_h_keep_atomic_frames_and_verify_both_modes() {
    for recipe in [
        "actionB", "actionC", "actionD", "actionE", "actionF", "actionG", "actionH",
    ] {
        for mode in [
            ComparisonMode::IndependentGeneration,
            ComparisonMode::FixedReplay,
        ] {
            let (_d, s) = fixture();
            let a = s
                .create("pair".into(), paired_config(recipe, mode))
                .unwrap()
                .summary
                .unwrap();
            for index in 0..7 {
                let u = step(&s, &a);
                let frames = u.frames.unwrap();
                assert_eq!(frames.left.as_ref().unwrap().frame.index, index);
                assert_eq!(frames.right.frame.index, index);
                while s
                    .get("pending".into(), None)
                    .unwrap()
                    .pending_journal
                    .is_some()
                {
                    save_current(&s, &a);
                }
                assert_ne!(summary(&s).phase, "storageBlocked", "{recipe} {mode:?}");
            }
            let u = s.get("final".into(), None).unwrap();
            let summary = u.summary.unwrap();
            assert_eq!(summary.phase, "completed");
            assert_eq!(summary.tracks.len(), 2);
            assert_eq!(summary.turn_count, summary.tracks[1].turn_count);
            let (_, bytes, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
            let report = reservoir_core::verify_bytes(&bytes);
            assert_eq!(
                report.status,
                reservoir_core::VerificationStatus::Passed,
                "{recipe} {mode:?}: {:?}",
                report.diagnostics
            );
            let record: ActionComparisonRecord = serde_json::from_slice(&bytes).unwrap();
            let left = s
                .frame_for(
                    "left".into(),
                    a.session_id.clone(),
                    a.generation.clone(),
                    6,
                    Some("left".into()),
                )
                .unwrap();
            assert_eq!(left.track_id, "left");
            assert_eq!(
                left.frame.unwrap().frame.state,
                record.left.as_ref().unwrap().frames[6].state
            );
            assert_eq!(u.frame.unwrap().frame.state, record.right.frames[6].state);
            assert!(s
                .store
                .read_checkpoint(&a.session_id)
                .unwrap()
                .paired_boundary
                .is_none());
        }
    }
}
#[test]
fn paired_half_boundary_recovers_saved_peer_and_rejects_stale_arm_save_and_metadata_tampering() {
    let (d, s) = fixture();
    let a = s
        .create(
            "pair".into(),
            paired_config("actionH", ComparisonMode::FixedReplay),
        )
        .unwrap()
        .summary
        .unwrap();
    step(&s, &a);
    let first = step(&s, &a).pending_journal.unwrap();
    assert_eq!(first.arm, Arm::Left);
    assert!(s
        .save_journal_for(
            "wrong".into(),
            &a.session_id,
            &a.generation,
            "right",
            &first.id
        )
        .is_err());
    let second = save_current(&s, &a).pending_journal.unwrap();
    assert_eq!(second.arm, Arm::Right);
    assert_eq!(
        first.id, second.id,
        "shared fixed tape can produce same ID in both namespaces"
    );
    assert!(s
        .save_journal_for(
            "stale".into(),
            &a.session_id,
            &a.generation,
            "left",
            &first.id
        )
        .is_err());
    assert!(s.snapshot(&a.session_id, &a.generation).is_err());
    assert!(!s.authorize_clean_close());
    let recovered = SessionState::new(
        d.path().join("sessions-v1"),
        LibraryState::new(
            d.path().join("library-v1"),
            PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources"),
        ),
    );
    assert!(recovered
        .get("read".into(), None)
        .unwrap()
        .summary
        .is_none());
    let c = recovered.store.read_checkpoint(&a.session_id).unwrap();
    assert_eq!((c.step, c.durable_step), (2, 0));
    assert_eq!(c.pending_journal.as_ref().unwrap()["arm"], "right");
    let b = c.paired_boundary.unwrap();
    assert!(b.arms[0].journal.is_some());
    assert!(b.arms[1].receipt.is_none());
    assert_eq!(
        b.arms[0]
            .receipt
            .as_ref()
            .unwrap()
            .save_receipt
            .as_ref()
            .unwrap()
            .relative_path
            .as_deref(),
        Some(first.relative_path.as_str())
    );
    let path = d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join("checkpoint.json");
    let original = fs::read(&path).unwrap();
    let v: Value = serde_json::from_slice(&original).unwrap();
    for pointer in [
        "/pairedBoundary/step",
        "/pairedBoundary/arms/0/stage",
        "/pairedBoundary/arms/0/receipt/id",
        "/pairedBoundary/arms/0/journal/actionID",
        "/pendingJournal/arm",
    ] {
        let mut changed = v.clone();
        *changed.pointer_mut(pointer).unwrap() = if pointer.ends_with("/arm") {
            json!("left")
        } else {
            json!(99)
        };
        fs::write(&path, serde_json::to_vec(&changed).unwrap()).unwrap();
        assert!(s.store.read_checkpoint(&a.session_id).is_err(), "{pointer}");
    }
    fs::write(&path, original).unwrap();
    save_current(&s, &a);
    let c = s.store.read_checkpoint(&a.session_id).unwrap();
    assert_eq!(c.durable_step, 2);
    assert!(c.paired_boundary.is_none());
    assert_eq!(
        c.attempts.iter().map(|a| a.arm).collect::<Vec<_>>(),
        vec![Arm::Left, Arm::Right]
    );
    assert!(d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join(first.relative_path)
        .is_file());
    assert!(d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join(second.relative_path)
        .is_file());
}
#[test]
fn paired_first_save_checkpoint_failure_preserves_file_and_retry_then_stop_keeps_peer_history() {
    let (d, s) = fixture();
    let a = s
        .create(
            "pair".into(),
            paired_config("actionH", ComparisonMode::FixedReplay),
        )
        .unwrap()
        .summary
        .unwrap();
    step(&s, &a);
    let left = step(&s, &a).pending_journal.unwrap();
    s.store
        .fail_committed_checkpoint
        .store(true, Ordering::Release);
    let u = save_current(&s, &a);
    assert_eq!(u.summary.unwrap().phase, "storageBlocked");
    assert_eq!(u.pending_journal.as_ref().unwrap().arm, Arm::Right);
    assert!(d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join(left.relative_path)
        .is_file());
    assert!(s
        .store
        .read_checkpoint(&a.session_id)
        .unwrap()
        .paired_boundary
        .unwrap()
        .arms[0]
        .receipt
        .is_none());
    s.pause("retrycheckpoint".into(), &a.session_id, &a.generation)
        .unwrap();
    let c = s.store.read_checkpoint(&a.session_id).unwrap();
    assert!(c.paired_boundary.unwrap().arms[0].journal.is_some());
    s.stop("stop".into(), &a.session_id, &a.generation).unwrap();
    let (_, bytes, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
    assert_eq!(
        reservoir_core::verify_bytes(&bytes).status,
        reservoir_core::VerificationStatus::Passed
    );
    let r: ActionComparisonRecord = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(r.left.unwrap().journals.len(), 1);
    assert!(r.right.journals.is_empty());
    assert_eq!(
        r.right.actions[0].failure_phase,
        Some(FailurePhase::JournalSave)
    );
}
#[test]
fn observation_pairs_alternate_order_and_keep_explicit_forcing_and_quiet_controls() {
    for quiet in [false, true] {
        for forcing in [
            ForcingProfile::PulsedSensoryV1,
            ForcingProfile::ContinuousSensoryV1,
        ] {
            let (_d, s) = fixture();
            let mut c = paired_config("actionD", ComparisonMode::IndependentGeneration);
            c.action_comparison_kind = ComparisonKind::Observation;
            c.action_forcing_profile = forcing;
            if quiet {
                c.action_input_strength = 0.0;
            }
            let a = s.create("observation".into(), c).unwrap().summary.unwrap();
            let mut order = vec![];
            for _ in 0..7 {
                step(&s, &a);
                while let Some(p) = s.get("pending".into(), None).unwrap().pending_journal {
                    order.push((p.observed_step, p.arm));
                    save_current(&s, &a);
                }
            }
            assert_eq!(
                order,
                vec![
                    (2, Arm::Left),
                    (2, Arm::Right),
                    (4, Arm::Right),
                    (4, Arm::Left),
                    (6, Arm::Left),
                    (6, Arm::Right)
                ]
            );
            let (_, bytes, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
            let report = reservoir_core::verify_bytes(&bytes);
            assert_eq!(
                report.status,
                reservoir_core::VerificationStatus::Passed,
                "{:?}",
                report.diagnostics
            );
            let r: ActionComparisonRecord = serde_json::from_slice(&bytes).unwrap();
            let left = r.left.unwrap();
            assert_eq!(left.stage, 4);
            assert_ne!(left.observation_channel, r.right.observation_channel);
            assert_eq!(r.specification.forcing_profile, forcing);
            if quiet {
                assert!(left
                    .frames
                    .iter()
                    .all(|f| f.input.iter().all(|x| *x == 0.0)));
            }
        }
    }
}
#[test]
fn paired_memory_reads_never_substitute_peer_file_and_failed_left_cancels_components_peer() {
    let (d, s) = fixture();
    let a = s
        .create(
            "pair".into(),
            paired_config("actionH", ComparisonMode::FixedReplay),
        )
        .unwrap()
        .summary
        .unwrap();
    step(&s, &a);
    let left = step(&s, &a).pending_journal.unwrap();
    save_current(&s, &a);
    save_current(&s, &a);
    fs::remove_file(
        d.path()
            .join("sessions-v1")
            .join(&a.session_id)
            .join(left.relative_path),
    )
    .unwrap();
    step(&s, &a);
    let u = step(&s, &a);
    assert_eq!(u.summary.unwrap().phase, "failed");
    assert!(u.pending_journal.is_none());
    let (_, bytes, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
    let r: ActionComparisonRecord = serde_json::from_slice(&bytes).unwrap();
    let left = r.left.unwrap();
    assert_eq!(
        left.actions[1].failure_phase,
        Some(FailurePhase::MemoryRead)
    );
    assert!(!left.actions[1].request_started);
    assert!(left.actions[1].raw_reply.is_none());
    assert!(left.actions[1].memory_text.is_none());
    assert_eq!(
        r.right.actions[1].failure_phase,
        Some(FailurePhase::Cancelled)
    );
    assert_eq!(
        reservoir_core::verify_bytes(&bytes).status,
        reservoir_core::VerificationStatus::Passed
    );
}
#[test]
fn unsupported_pairs_fail_without_replacing_the_accepted_session() {
    for (recipe, kind, mode) in [
        (
            "actionA",
            ComparisonKind::Components,
            ComparisonMode::IndependentGeneration,
        ),
        (
            "actionH",
            ComparisonKind::Observation,
            ComparisonMode::IndependentGeneration,
        ),
        (
            "actionD",
            ComparisonKind::Observation,
            ComparisonMode::FixedReplay,
        ),
    ] {
        let (_d, s) = fixture();
        let mut c = paired_config(recipe, mode);
        c.action_comparison_kind = kind;
        assert!(s.create("invalid".into(), c).is_err());
        assert!(s.get("read".into(), None).unwrap().summary.is_none());
    }
}

#[test]
fn manual_paired_boundary_at_durable_step_retains_prior_snapshot_and_legacy_arm_defaults() {
    let (d, s) = fixture();
    let a = s
        .create(
            "pair".into(),
            paired_config("actionE", ComparisonMode::IndependentGeneration),
        )
        .unwrap()
        .summary
        .unwrap();
    step(&s, &a);
    s.pause("checkpoint".into(), &a.session_id, &a.generation)
        .unwrap();
    let u = s
        .request_journal("manual".into(), &a.session_id, &a.generation)
        .unwrap();
    assert_eq!(u.pending_journal.unwrap().arm, Arm::Left);
    save_current(&s, &a);
    let c = s.store.read_checkpoint(&a.session_id).unwrap();
    assert_eq!((c.durable_step, c.step), (1, 1));
    save_current(&s, &a);
    let (_, bytes, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
    assert_eq!(
        reservoir_core::verify_bytes(&bytes).status,
        reservoir_core::VerificationStatus::Passed
    );
    let right = s
        .turn_for(
            "right".into(),
            a.session_id.clone(),
            a.generation.clone(),
            0,
            None,
        )
        .unwrap();
    let left = s
        .turn_for(
            "left".into(),
            a.session_id.clone(),
            a.generation.clone(),
            0,
            Some("left".into()),
        )
        .unwrap();
    assert_eq!(left.track_id, "left");
    assert_eq!(right.track_id, "right");
    assert!(left
        .turn
        .journal_relative_path
        .as_deref()
        .unwrap()
        .starts_with("left/"));
    assert!(right
        .turn
        .journal_relative_path
        .as_deref()
        .unwrap()
        .starts_with("right/"));
    assert!(s
        .frame_for(
            "bad".into(),
            a.session_id.clone(),
            a.generation.clone(),
            0,
            Some("unknown".into())
        )
        .is_err());
    // Older standalone metadata omitted the arm, comparison and partial-boundary fields.
    drop(s);
    let s = SessionState::new(
        d.path().join("other-sessions"),
        LibraryState::new(
            d.path().join("other-library"),
            PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources"),
        ),
    );
    let a = create(&s, "journalE", 5);
    step(&s, &a);
    step(&s, &a);
    save_current(&s, &a);
    step(&s, &a);
    step(&s, &a);
    let path = d
        .path()
        .join("other-sessions")
        .join(&a.session_id)
        .join("checkpoint.json");
    let mut v: Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
    v.as_object_mut().unwrap().remove("pairedBoundary");
    v["pendingJournal"].as_object_mut().unwrap().remove("arm");
    for a in v["attempts"].as_array_mut().unwrap() {
        a.as_object_mut().unwrap().remove("arm");
    }
    fs::write(path, serde_json::to_vec(&v).unwrap()).unwrap();
    let c = s.store.read_checkpoint(&a.session_id).unwrap();
    assert_eq!(c.attempts[0].arm, Arm::Right);
    assert!(c.paired_boundary.is_none());
}

fn regulation_config() -> SessionConfig {
    let mut c = config("regulation", 600);
    c.seed = "98".into();
    c.turn_every = 30;
    c
}
#[test]
fn regulation_completes_exact_native_record_and_library_recovery_without_future_summary() {
    let (d, s) = fixture();
    let u = s.create("regulation".into(), regulation_config()).unwrap();
    assert!(u.frame.is_none() && u.frames.is_none() && u.regulation_frames.is_none());
    let a = u.summary.unwrap();
    assert!(!a.can_export);
    assert_eq!(a.regulation_spec.as_ref().unwrap()["fieldSeed"], "98");
    assert_eq!(a.regulation_spec.as_ref().unwrap()["inputSeed"], "42");
    assert!(s
        .frame_for(
            "zero".into(),
            a.session_id.clone(),
            a.generation.clone(),
            0,
            None
        )
        .is_err());
    let mut previous_next = None;
    for n in 1..=600 {
        let u = step(&s, &a);
        assert!(u.frame.is_none() && u.frames.is_none());
        assert!(u.pending_journal.is_none());
        let pair = u.regulation_frames.unwrap();
        assert_eq!(pair.left.step, n.to_string());
        assert_eq!(pair.left.input.len(), 66);
        assert_eq!(pair.left.field_vector.len(), 32);
        assert_eq!(pair.left.eigenvalues.len(), 32);
        assert_eq!(pair.left.input, pair.right.input);
        assert_eq!(pair.left.field_vector, pair.right.field_vector);
        assert!(pair.left.control.is_none());
        assert_eq!(pair.left.retention_used, 0.955);
        if let Some(retention) = previous_next {
            assert_eq!(pair.right.retention_used, retention);
        }
        previous_next = pair.right.next_retention;
        let summary = u.summary.unwrap();
        assert_eq!(summary.step, n);
        assert_eq!(summary.turn_count, 0);
        assert_eq!(summary.journal_count, 0);
        assert!(summary.action.is_none());
        assert!(!summary.can_request_journal);
        if n <= 300 {
            assert!(pair.right.regulation_evidence.is_none());
        } else {
            let e = pair.right.regulation_evidence.unwrap();
            assert_eq!(e.count, n - 300);
            assert_eq!(e.last_step, n);
            assert_eq!(e.is_complete, n == 600);
        }
        if n == 30 || n == 300 || n == 599 {
            assert!(s.snapshot(&a.session_id, &a.generation).is_err());
            assert!(s
                .save_record("partial".into(), &a.session_id, &a.generation)
                .is_err());
            assert!(!summary.can_export);
            let c = s.store.read_checkpoint(&a.session_id).unwrap();
            assert_eq!(c.durable_step, 0);
            assert!(c.record_sha256.is_none());
            assert!(!c.regulation_progress.unwrap().portable_complete);
        }
    }
    let summary = summary(&s);
    assert_eq!(summary.phase, "completed");
    assert_eq!(summary.durable_step, 600);
    assert!(summary.can_export);
    assert!(!summary.can_run);
    let old = s
        .frame_for(
            "old".into(),
            a.session_id.clone(),
            a.generation.clone(),
            299,
            Some("left".into()),
        )
        .unwrap();
    assert!(old.frame.is_none());
    assert!(old.regulation_frame.unwrap().regulation_evidence.is_none());
    let first = s
        .frame_for(
            "first".into(),
            a.session_id.clone(),
            a.generation.clone(),
            300,
            Some("right".into()),
        )
        .unwrap();
    assert_eq!(
        first
            .regulation_frame
            .unwrap()
            .regulation_evidence
            .unwrap()
            .count,
        1
    );
    let details = s
        .regulation_details(
            "details".into(),
            a.session_id.clone(),
            a.generation.clone(),
            301,
        )
        .unwrap();
    assert_eq!(details.projection_weights.len(), 2112);
    assert_eq!(details.timeline.len(), 301);
    assert_eq!(details.timeline.last().unwrap().step, "301");
    assert!(s
        .regulation_details(
            "future".into(),
            a.session_id.clone(),
            a.generation.clone(),
            601
        )
        .is_err());
    let (_, bytes, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
    let record: reservoir_core::regulation::RegulationExampleRecord =
        serde_json::from_slice(&bytes).unwrap();
    assert_eq!(record.frames.len(), 600);
    assert_eq!(record.projection_weights, details.projection_weights);
    assert_eq!(
        reservoir_core::verify_bytes(&bytes).status,
        reservoir_core::VerificationStatus::Passed
    );
    let saved = s
        .save_record("save".into(), &a.session_id, &a.generation)
        .unwrap()
        .summary
        .unwrap();
    assert!(!saved.unsaved_record);
    assert!(saved.library_entry_id.is_some());
    let reopened = SessionState::new(d.path().join("sessions-v1"), s.library.clone());
    assert!(reopened.get("read".into(), None).unwrap().summary.is_none());
    let c = reopened.store.read_checkpoint(&a.session_id).unwrap();
    assert_eq!(c.step, 600);
    assert_eq!(c.durable_step, 600);
    assert!(c.regulation_progress.unwrap().portable_complete);
    assert_eq!(
        reopened
            .store
            .read_record(&a.session_id, c.record_sha256.as_deref().unwrap())
            .unwrap(),
        bytes
    );
}
#[test]
fn regulation_partial_stop_reset_and_checkpoint_reopen_preserve_metadata_only_limits() {
    let (d, s) = fixture();
    let a = s
        .create("create".into(), regulation_config())
        .unwrap()
        .summary
        .unwrap();
    for _ in 0..3 {
        step(&s, &a);
    }
    s.pause("pause".into(), &a.session_id, &a.generation)
        .unwrap();
    assert!(!s.authorize_clean_close());
    assert!(!s.finish_close(false).unwrap());
    let c = s.store.read_checkpoint(&a.session_id).unwrap();
    assert_eq!(c.step, 3);
    assert_eq!(c.durable_step, 0);
    assert!(c.record_sha256.is_none());
    assert_eq!(c.regulation_progress.as_ref().unwrap().retained_step, 3);
    let path = d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join("checkpoint.json");
    let original = fs::read(&path).unwrap();
    let v: Value = serde_json::from_slice(&original).unwrap();
    for (pointer, value) in [
        ("/regulationProgress/retainedStep", json!(4)),
        ("/regulationProgress/portableComplete", json!(true)),
        ("/regulationProgress/specification/inputSeed", json!(43)),
        ("/durableStep", json!(3)),
        ("/phase", json!("completed")),
        ("/phase", json!("awaitingJournalSave")),
    ] {
        let mut changed = v.clone();
        *changed.pointer_mut(pointer).unwrap() = value;
        fs::write(&path, serde_json::to_vec(&changed).unwrap()).unwrap();
        assert!(s.store.read_checkpoint(&a.session_id).is_err(), "{pointer}");
    }
    fs::write(&path, original).unwrap();
    let u = s.stop("stop".into(), &a.session_id, &a.generation).unwrap();
    assert_eq!(u.summary.unwrap().phase, "stopped");
    assert!(s
        .step("late".into(), &a.session_id, &a.generation, false)
        .is_err());
    assert!(s.snapshot(&a.session_id, &a.generation).is_err());
    assert!(s
        .reset("reset".into(), &a.session_id, &a.generation, false)
        .is_err());
    let b = s
        .reset("discard-reset".into(), &a.session_id, &a.generation, true)
        .unwrap()
        .summary
        .unwrap();
    assert_ne!(a.session_id, b.session_id);
    assert_eq!(b.step, 0);
    assert!(s
        .step("old".into(), &a.session_id, &a.generation, false)
        .is_err());
    assert!(s
        .regulation_details("old".into(), a.session_id.clone(), a.generation.clone(), 1)
        .is_err());
    assert!(s.store.read_checkpoint(&a.session_id).unwrap().discarded);
    assert!(s.finish_close(true).unwrap());
    let reopened = SessionState::new(d.path().join("sessions-v1"), s.library.clone());
    assert!(reopened.get("read".into(), None).unwrap().summary.is_none());
    assert!(reopened
        .store
        .read_checkpoint(&a.session_id)
        .unwrap()
        .record_sha256
        .is_none());
}
#[test]
fn regulation_fixed_configuration_rejects_changes_without_replacing_accepted_generation() {
    let (_d, s) = fixture();
    let a = s
        .create("create".into(), regulation_config())
        .unwrap()
        .summary
        .unwrap();
    let v = serde_json::to_value(regulation_config()).unwrap();
    for (key, value) in [
        ("seed", json!("42")),
        ("steps", json!(599)),
        ("retention", json!(0.96)),
        ("noiseAmplitude", json!(0.01)),
        ("leak", json!(0.5)),
        ("turnEvery", json!(3)),
        ("actionComparePrevious", json!(true)),
        ("actionMode", json!("fixedReplay")),
        ("actionForcingProfile", json!("continuousSensoryV1")),
    ] {
        let mut changed = v.clone();
        changed[key] = value;
        let config = serde_json::from_value(changed).unwrap();
        assert!(s.create("invalid".into(), config).is_err(), "{key}");
        assert_eq!(summary(&s).session_id, a.session_id);
        assert_eq!(summary(&s).step, 0);
    }
    assert!(s
        .request_journal("journal".into(), &a.session_id, &a.generation)
        .is_err());
    assert!(s
        .turn_for(
            "turn".into(),
            a.session_id.clone(),
            a.generation.clone(),
            0,
            None
        )
        .is_err());
    assert!(s
        .update_controls(
            "controls".into(),
            &a.session_id,
            &a.generation,
            ExplorationControls::default()
        )
        .is_err());
}
#[test]
fn regulation_scheduler_pause_and_replaced_worker_never_advance_new_generation() {
    let (_d, s) = fixture();
    let a = s
        .create("create".into(), regulation_config())
        .unwrap()
        .summary
        .unwrap();
    s.run(
        "run".into(),
        &a.session_id,
        &a.generation,
        Arc::new(|u| {
            assert!(u.frame.is_none());
            true
        }),
    )
    .unwrap();
    let start = Instant::now();
    while summary(&s).step == 0 && start.elapsed() < Duration::from_secs(5) {
        thread::sleep(Duration::from_millis(5));
    }
    let u = s
        .pause("pause".into(), &a.session_id, &a.generation)
        .unwrap();
    let count = u.summary.unwrap().step;
    assert!(count > 0);
    thread::sleep(Duration::from_millis(70));
    assert_eq!(summary(&s).step, count);
    s.run(
        "rerun".into(),
        &a.session_id,
        &a.generation,
        Arc::new(|_| true),
    )
    .unwrap();
    let b = s
        .reset("replace".into(), &a.session_id, &a.generation, true)
        .unwrap()
        .summary
        .unwrap();
    thread::sleep(Duration::from_millis(70));
    assert_eq!(summary(&s).session_id, b.session_id);
    assert_eq!(summary(&s).step, 0);
}
#[test]
fn request_order_is_only_the_actual_receipt_and_observation_can_reverse_it() {
    let (_d, s) = fixture();
    let mut c = paired_config("actionD", ComparisonMode::IndependentGeneration);
    c.action_comparison_kind = ComparisonKind::Observation;
    let a = s.create("pair".into(), c).unwrap().summary.unwrap();
    for _ in 0..4 {
        step(&s, &a);
        while s
            .get("read".into(), None)
            .unwrap()
            .pending_journal
            .is_some()
        {
            save_current(&s, &a);
        }
    }
    for (index, left_order, right_order) in [(0, 1, 2), (1, 2, 1)] {
        assert_eq!(
            s.turn_for(
                "left".into(),
                a.session_id.clone(),
                a.generation.clone(),
                index,
                Some("left".into())
            )
            .unwrap()
            .turn
            .request_order,
            Some(left_order)
        );
        assert_eq!(
            s.turn_for(
                "right".into(),
                a.session_id.clone(),
                a.generation.clone(),
                index,
                None
            )
            .unwrap()
            .turn
            .request_order,
            Some(right_order)
        );
    }
    let (_d, s) = fixture();
    let a = create(&s, "stage2", 3);
    step(&s, &a);
    step(&s, &a);
    assert!(s
        .turn("stage".into(), a.session_id, a.generation, 0)
        .unwrap()
        .turn
        .request_order
        .is_none());
}

#[test]
fn regulation_stopped_progress_checkpoint_retry_cannot_restart_the_terminal_engine() {
    let (d, s) = fixture();
    let a = s
        .create("create".into(), regulation_config())
        .unwrap()
        .summary
        .unwrap();
    step(&s, &a);
    let path = d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join("checkpoint.json");
    let original = fs::read(&path).unwrap();
    fs::remove_file(&path).unwrap();
    fs::create_dir(&path).unwrap();
    let blocked = s
        .stop("stop".into(), &a.session_id, &a.generation)
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(blocked.phase, "storageBlocked");
    assert!(!blocked.can_export);
    fs::remove_dir(&path).unwrap();
    fs::write(&path, original).unwrap();
    let retried = s
        .pause("retry-progress".into(), &a.session_id, &a.generation)
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(retried.phase, "stopped");
    assert!(!retried.can_run && !retried.can_step && !retried.can_export);
    assert!(s
        .run(
            "late".into(),
            &a.session_id,
            &a.generation,
            Arc::new(|_| true)
        )
        .is_err());
    let c = s.store.read_checkpoint(&a.session_id).unwrap();
    assert_eq!(c.step, 1);
    assert_eq!(c.durable_step, 0);
    assert!(c.record_sha256.is_none());
    assert_eq!(c.regulation_progress.unwrap().retained_step, 1);
}

fn model_config(recipe: &str, steps: usize) -> SessionConfig {
    let mut c = config(recipe, steps);
    c.language = LanguageConfiguration {
        backend: LanguageKind::Ollama,
        endpoint: Some("http://127.0.0.1:23456".into()),
        model: Some("isolated-test-model".into()),
        context_tokens: Some(4096),
        response_format: action_stage(recipe).map(|_| "json".into()),
    };
    c
}
fn model_response(text: &str) -> LanguageResponse {
    LanguageResponse {
        text: text.into(),
        provider_model: Some("reported-test-model".into()),
        stop_reason: Some("stop".into()),
        token_count: Some(12),
        provider_prompt_evaluation: None,
        complete: true,
    }
}
fn wait_session(s: &SessionState, predicate: impl Fn(&SessionSummary) -> bool) -> SessionSummary {
    let until = Instant::now() + Duration::from_secs(15);
    loop {
        let u = summary(s);
        if predicate(&u) {
            return u;
        };
        assert!(
            Instant::now() < until,
            "timed out in {}: {:?}",
            u.phase,
            u.diagnostics
        );
        thread::sleep(Duration::from_millis(10));
    }
}
fn assert_portable(s: &SessionState, a: &SessionSummary) -> serde_json::Value {
    let (_, b, _) = s.snapshot(&a.session_id, &a.generation).unwrap();
    let report = reservoir_core::verify_bytes(&b);
    assert_eq!(
        report.status,
        reservoir_core::VerificationStatus::Passed,
        "{:?}",
        report.diagnostics
    );
    serde_json::from_slice(&b).unwrap()
}
#[test]
fn model_config_rejects_ineligible_recipes_without_replacing_or_contacting() {
    let (_d, mut s) = fixture();
    let called = Arc::new(AtomicUsize::new(0));
    let copy = called.clone();
    s.generate_language = Arc::new(move |_, _, _| {
        copy.fetch_add(1, Ordering::SeqCst);
        Ok(model_response("Bounded reply."))
    });
    let a = s
        .create("create".into(), model_config("stage3", 5))
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(called.load(Ordering::SeqCst), 0);
    for recipe in [
        "stage1",
        "stage2",
        "exploration",
        "regulation",
        "actionA",
        "actionB",
        "actionC",
    ] {
        assert!(s.create("bad".into(), model_config(recipe, 5)).is_err());
        assert_eq!(summary(&s).session_id, a.session_id);
    }
    let mut c = model_config("actionH", 5);
    c.action_mode = ComparisonMode::FixedReplay;
    assert!(s.create("tape".into(), c).is_err());
    let mut c = model_config("stage3", 5);
    c.language.endpoint = Some("http://127.1:23456".into());
    assert!(s.create("alias".into(), c).is_err());
    assert_eq!(called.load(Ordering::SeqCst), 0);
}
#[test]
fn model_stage_manual_step_subscription_pause_and_next_step_feedback() {
    let (_d, mut s) = fixture();
    let (started_tx, started_rx) = std::sync::mpsc::channel();
    let (release_tx, release_rx) = std::sync::mpsc::channel();
    let release = Mutex::new(release_rx);
    s.generate_language = Arc::new(move |c, p, _| {
        started_tx.send((c.model.clone(), p.to_string())).unwrap();
        release
            .lock()
            .unwrap()
            .recv_timeout(Duration::from_secs(10))
            .unwrap();
        Ok(model_response("A quiet bounded journal."))
    });
    let a = s
        .create("create".into(), model_config("stage3", 5))
        .unwrap()
        .summary
        .unwrap();
    let updates = Arc::new(Mutex::new(Vec::new()));
    let observed = updates.clone();
    s.get(
        "subscribe".into(),
        Some(Arc::new(move |u| {
            observed.lock().unwrap().push(u);
            true
        })),
    )
    .unwrap();
    step(&s, &a);
    let u = step(&s, &a);
    assert_eq!(u.summary.unwrap().phase, "awaitingLanguage");
    let (model, prompt) = started_rx.recv_timeout(Duration::from_secs(10)).unwrap();
    assert_eq!(model.as_deref(), Some("isolated-test-model"));
    let check = s.store.read_checkpoint(&a.session_id).unwrap();
    let pending = check.pending_language.unwrap();
    assert_eq!(pending.prompt, prompt);
    assert!(!pending.request_started);
    assert_eq!(pending.operation.state, "prepared");
    assert_eq!(check.durable_step, 0);
    assert!(s.snapshot(&a.session_id, &a.generation).is_err());
    assert!(!s.authorize_clean_close());
    let paused = s
        .pause("pause".into(), &a.session_id, &a.generation)
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(paused.phase, "awaitingLanguage");
    assert_eq!(paused.step, 2);
    release_tx.send(()).unwrap();
    let ready = wait_session(&s, |u| u.phase == "paused");
    assert_eq!(ready.step, 2);
    assert_eq!(ready.turn_count, 1);
    let until = Instant::now() + Duration::from_secs(5);
    while !updates.lock().unwrap().iter().any(|u| {
        u.summary
            .as_ref()
            .is_some_and(|s| s.phase == "paused" && s.turn_count == 1)
    }) {
        assert!(Instant::now() < until);
        thread::sleep(Duration::from_millis(5));
    }
    let frame = step(&s, &a).frame.unwrap();
    assert_eq!(frame.frame.semantic_turn_id.as_deref(), Some("1"));
    let r = assert_portable(&s, &a);
    assert_eq!(r["turns"][0]["prompt"], prompt);
    assert_eq!(r["turns"][0]["providerModel"], "reported-test-model");
    assert_eq!(r["turns"][0]["applicationStep"], 3);
    assert!(updates.lock().unwrap().iter().any(|u| u
        .summary
        .as_ref()
        .is_some_and(|s| s.phase == "paused" && s.turn_count == 1)));
}
#[test]
fn model_action_write_requires_real_save_before_feedback_and_reports_sources() {
    let (_d, mut s) = fixture();
    s.generate_language = Arc::new(|_, _, _| {
        Ok(model_response(
            r#"{"action":"WRITE_JOURNAL","text":"A saved bounded thought."}"#,
        ))
    });
    let a = s
        .create("create".into(), model_config("actionE", 5))
        .unwrap()
        .summary
        .unwrap();
    step(&s, &a);
    step(&s, &a);
    let waiting = wait_session(&s, |u| u.phase == "awaitingJournalSave");
    assert_eq!(waiting.turn_count, 0);
    assert_eq!(waiting.journal_count, 0);
    let pending = s.get("get".into(), None).unwrap().pending_journal.unwrap();
    assert_eq!(pending.text, "A saved bounded thought.");
    assert!(s
        .step("blocked".into(), &a.session_id, &a.generation, false)
        .is_err());
    s.save_journal("save".into(), &a.session_id, &a.generation)
        .unwrap();
    let committed = summary(&s);
    assert_eq!(committed.journal_count, 1);
    let t = s
        .turn_for(
            "turn".into(),
            a.session_id.clone(),
            a.generation.clone(),
            0,
            None,
        )
        .unwrap()
        .turn;
    assert_eq!(t.backend.as_deref(), Some("ollama"));
    assert_eq!(t.configured_model.as_deref(), Some("isolated-test-model"));
    assert_eq!(t.provider_model.as_deref(), Some("reported-test-model"));
    assert_eq!(t.request_order, Some(1));
    assert_eq!(t.reply.as_deref(), Some("A saved bounded thought."));
    assert_eq!(
        step(&s, &a)
            .frame
            .unwrap()
            .frame
            .semantic_turn_id
            .as_deref(),
        Some("1")
    );
    assert_portable(&s, &a);
}
#[test]
fn model_stop_reset_and_close_reject_late_provider_result() {
    let (_d, mut s) = fixture();
    let cancelled = Arc::new(AtomicBool::new(false));
    let seen = cancelled.clone();
    let (started_tx, started_rx) = std::sync::mpsc::channel();
    let (release_tx, release_rx) = std::sync::mpsc::channel();
    let release = Mutex::new(release_rx);
    s.generate_language = Arc::new(move |_, _, cancel| {
        started_tx.send(()).unwrap();
        release
            .lock()
            .unwrap()
            .recv_timeout(Duration::from_secs(10))
            .unwrap();
        seen.store(cancel.load(Ordering::Acquire), Ordering::Release);
        Ok(model_response("Late reply must not enter feedback."))
    });
    let a = s
        .create("create".into(), model_config("stage3", 5))
        .unwrap()
        .summary
        .unwrap();
    step(&s, &a);
    step(&s, &a);
    started_rx.recv_timeout(Duration::from_secs(10)).unwrap();
    let stopped = s
        .stop("stop".into(), &a.session_id, &a.generation)
        .unwrap()
        .summary
        .unwrap();
    assert_eq!(stopped.phase, "stopped");
    let record = assert_portable(&s, &a);
    assert_eq!(record["turns"][0]["status"], "cancelled");
    assert_eq!(
        record["turns"][0]["failure"],
        "Explicit stop while the language request remained unresolved."
    );
    assert!(record["turns"][0]["rawReply"].is_null());
    let replacement = s
        .reset("reset".into(), &a.session_id, &a.generation, true)
        .unwrap()
        .summary
        .unwrap();
    assert_ne!(replacement.session_id, a.session_id);
    release_tx.send(()).unwrap();
    let until = Instant::now() + Duration::from_secs(5);
    while !cancelled.load(Ordering::Acquire) {
        assert!(Instant::now() < until);
        thread::sleep(Duration::from_millis(10));
    }
    assert_eq!(summary(&s).session_id, replacement.session_id);
    assert_eq!(summary(&s).step, 0);
    assert_eq!(summary(&s).turn_count, 0);
    assert!(s.finish_close(true).unwrap());
    assert!(s.get("closed".into(), None).is_err());
}
#[test]
fn model_unqualified_reply_is_blocked_without_retry_until_explicit_stop() {
    let (_d, mut s) = fixture();
    let calls = Arc::new(AtomicUsize::new(0));
    let n = calls.clone();
    s.generate_language = Arc::new(move |_, _, _| {
        n.fetch_add(1, Ordering::SeqCst);
        Ok(model_response("\u{10ffff}"))
    });
    let a = s
        .create("create".into(), model_config("stage3", 5))
        .unwrap()
        .summary
        .unwrap();
    step(&s, &a);
    step(&s, &a);
    let blocked = wait_session(&s, |u| {
        u.pending_language
            .as_ref()
            .is_some_and(|p| p.state == "compatibilityBlocked")
    });
    assert_eq!(blocked.turn_count, 0);
    assert!(!blocked.can_export);
    assert!(!blocked.can_step);
    assert_eq!(calls.load(Ordering::SeqCst), 1);
    let checkpoint = s.store.read_checkpoint(&a.session_id).unwrap();
    let pending = checkpoint.pending_language.unwrap();
    assert_eq!(pending.operation.state, "compatibilityBlocked");
    assert_eq!(
        pending.received_response.as_ref().unwrap().text,
        "\u{10ffff}"
    );
    assert!(!pending.received_response.as_ref().unwrap().text_truncated);
    s.stop("stop".into(), &a.session_id, &a.generation).unwrap();
    assert_portable(&s, &a);
    let stopped = s.store.read_checkpoint(&a.session_id).unwrap();
    assert!(stopped.pending_language.is_none());
    let retained = stopped.rejected_language.unwrap();
    assert_eq!(retained.received_response.unwrap().text, "\u{10ffff}");
    assert!(retained.diagnostic.is_some());
}
#[test]
fn model_observation_failure_attempts_peer_and_components_cancel_peer() {
    for observation in [true, false] {
        let (_d, mut s) = fixture();
        let calls = Arc::new(AtomicUsize::new(0));
        let n = calls.clone();
        s.generate_language = Arc::new(move |_, _, _| {
            if n.fetch_add(1, Ordering::SeqCst) == 0 {
                Err(crate::model_transport::TransportError {
                    category: "test",
                    message: "Isolated fake provider failed.".into(),
                })
            } else {
                Ok(model_response(
                    r#"{"action":"WRITE_JOURNAL","text":"Peer reply."}"#,
                ))
            }
        });
        let mut c = model_config(if observation { "actionD" } else { "actionE" }, 5);
        c.action_compare_previous = true;
        if observation {
            c.action_comparison_kind = ComparisonKind::Observation;
        }
        let a = s.create("create".into(), c).unwrap().summary.unwrap();
        step(&s, &a);
        step(&s, &a);
        if observation {
            wait_session(&s, |u| u.phase == "awaitingJournalSave");
            assert_eq!(calls.load(Ordering::SeqCst), 2);
            let c = s.store.read_checkpoint(&a.session_id).unwrap();
            assert_eq!(
                c.paired_boundary.unwrap().arms[0]
                    .receipt
                    .as_ref()
                    .unwrap()
                    .failure_phase,
                Some(FailurePhase::Language)
            );
            s.save_journal("save".into(), &a.session_id, &a.generation)
                .unwrap();
        } else {
            wait_session(&s, |u| u.phase == "failed");
            assert_eq!(calls.load(Ordering::SeqCst), 1);
        }
        let r = assert_portable(&s, &a);
        assert_eq!(r["left"]["actions"][0]["requestOrder"], 1);
        assert_eq!(r["right"]["actions"][0]["requestStarted"], observation);
        assert_eq!(
            r["right"]["actions"][0]["status"],
            if observation {
                "completed"
            } else {
                "cancelled"
            }
        );
    }
}
#[test]
fn model_pending_recovery_binds_identity_and_failed_intent_does_not_dispatch() {
    let (d, mut s) = fixture();
    let calls = Arc::new(AtomicUsize::new(0));
    let n = calls.clone();
    s.generate_language = Arc::new(move |_, _, _| {
        n.fetch_add(1, Ordering::SeqCst);
        Ok(model_response("Should not dispatch."))
    });
    let a = s
        .create("create".into(), model_config("actionE", 5))
        .unwrap()
        .summary
        .unwrap();
    step(&s, &a);
    let path = d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join("checkpoint.json");
    let prior = fs::read(&path).unwrap();
    fs::remove_file(&path).unwrap();
    fs::create_dir(&path).unwrap();
    let u = step(&s, &a).summary.unwrap();
    assert_eq!(u.phase, "storageBlocked");
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    assert!(u.pending_language.is_none());
    fs::remove_dir(&path).unwrap();
    fs::write(&path, prior).unwrap();
    s.save_record("retry".into(), &a.session_id, &a.generation)
        .unwrap();
    assert_eq!(summary(&s).phase, "stopped");
    let r = assert_portable(&s, &a);
    assert_eq!(r["right"]["actions"][0]["requestStarted"], false);
    assert_eq!(r["right"]["actions"][0]["status"], "cancelled");
}
#[test]
fn model_real_loopback_http_bridge_sends_exact_prompt_and_retains_native_response() {
    use std::io::{Read, Write};
    let listener = std::net::TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let (body_tx, body_rx) = std::sync::mpsc::channel();
    let server = thread::spawn(move || {
        let (mut socket, _) = listener.accept().unwrap();
        socket
            .set_read_timeout(Some(Duration::from_secs(10)))
            .unwrap();
        let mut bytes = Vec::new();
        let mut block = [0u8; 4096];
        let header_end = loop {
            let n = socket.read(&mut block).unwrap();
            assert!(n > 0);
            bytes.extend_from_slice(&block[..n]);
            if let Some(at) = bytes.windows(4).position(|v| v == b"\r\n\r\n") {
                break at + 4;
            }
        };
        let header = String::from_utf8(bytes[..header_end].to_vec()).unwrap();
        assert!(header.starts_with("POST /api/chat HTTP/1.1"));
        let length = header
            .lines()
            .find_map(|l| {
                l.to_ascii_lowercase()
                    .strip_prefix("content-length: ")
                    .map(|v| v.parse::<usize>().unwrap())
            })
            .unwrap();
        while bytes.len() < header_end + length {
            let n = socket.read(&mut block).unwrap();
            assert!(n > 0);
            bytes.extend_from_slice(&block[..n]);
        }
        let body: Value = serde_json::from_slice(&bytes[header_end..header_end + length]).unwrap();
        body_tx.send(body).unwrap();
        let response=br#"{"model":"isolated-test-model","done":true,"done_reason":"stop","eval_count":9,"message":{"content":"An isolated test response."}}"#;
        write!(socket,"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",response.len()).unwrap();
        socket.write_all(response).unwrap();
    });
    let (_d, s) = fixture();
    let mut c = model_config("stage3", 5);
    c.language.endpoint = Some(format!("http://127.0.0.1:{port}"));
    let a = s.create("create".into(), c).unwrap().summary.unwrap();
    step(&s, &a);
    step(&s, &a);
    let body = body_rx.recv_timeout(Duration::from_secs(10)).unwrap();
    wait_session(&s, |u| u.phase == "paused");
    server.join().unwrap();
    assert_eq!(body["model"], "isolated-test-model");
    assert_eq!(body["stream"], false);
    assert_eq!(body["options"]["num_predict"], 256);
    assert_eq!(body["options"]["num_ctx"], 4096);
    assert_eq!(body["options"]["temperature"], 0);
    let r = assert_portable(&s, &a);
    assert_eq!(r["turns"][0]["prompt"], body["messages"][0]["content"]);
    assert_eq!(r["turns"][0]["providerModel"], "isolated-test-model");
}

#[test]
fn model_memory_read_failure_prevents_dispatch_and_retains_terminal_native_receipt() {
    let (d, mut s) = fixture();
    let calls = Arc::new(AtomicUsize::new(0));
    let n = calls.clone();
    s.generate_language = Arc::new(move |_, _, _| {
        n.fetch_add(1, Ordering::SeqCst);
        Ok(model_response(
            r#"{"action":"WRITE_JOURNAL","text":"Saved memory must really be read."}"#,
        ))
    });
    let a = s
        .create("create".into(), model_config("actionF", 6))
        .unwrap()
        .summary
        .unwrap();
    step(&s, &a);
    step(&s, &a);
    wait_session(&s, |u| u.phase == "awaitingJournalSave");
    let p = s
        .get("pending".into(), None)
        .unwrap()
        .pending_journal
        .unwrap();
    s.save_journal("save".into(), &a.session_id, &a.generation)
        .unwrap();
    fs::remove_file(
        d.path()
            .join("sessions-v1")
            .join(&a.session_id)
            .join(p.relative_path),
    )
    .unwrap();
    step(&s, &a);
    let failed = step(&s, &a).summary.unwrap();
    assert_eq!(failed.phase, "failed");
    assert_eq!(calls.load(Ordering::SeqCst), 1);
    let r = assert_portable(&s, &a);
    assert_eq!(r["right"]["actions"][1]["failurePhase"], "memoryRead");
    assert_eq!(r["right"]["actions"][1]["requestStarted"], false);
    assert!(r["right"]["actions"][1]["rawReply"].is_null());
    assert!(r["right"]["actions"][1]["memoryText"].is_null());
}
#[test]
fn model_pending_checkpoint_rejects_identity_and_response_corruption() {
    let (d, mut s) = fixture();
    s.generate_language = Arc::new(|_, _, _| Ok(model_response("\u{10ffff}")));
    let a = s
        .create("create".into(), model_config("stage3", 5))
        .unwrap()
        .summary
        .unwrap();
    step(&s, &a);
    step(&s, &a);
    wait_session(&s, |u| {
        u.pending_language
            .as_ref()
            .is_some_and(|p| p.state == "compatibilityBlocked")
    });
    let path = d
        .path()
        .join("sessions-v1")
        .join(&a.session_id)
        .join("checkpoint.json");
    let original: Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
    for (key, value) in [
        ("generation", json!("900")),
        ("operationId", json!("different")),
        ("observedStep", json!(1)),
        ("model", json!("substitute")),
        ("state", json!("prepared")),
    ] {
        let mut changed = original.clone();
        changed["pendingLanguage"][key] = value;
        fs::write(&path, serde_json::to_vec(&changed).unwrap()).unwrap();
        assert!(s.store.read_checkpoint(&a.session_id).is_err(), "{key}");
    }
    let mut changed = original.clone();
    changed["pendingLanguage"]["receivedResponse"]["text"] = json!("altered");
    fs::write(&path, serde_json::to_vec(&changed).unwrap()).unwrap();
    assert!(s.store.read_checkpoint(&a.session_id).is_err());
    fs::write(&path, serde_json::to_vec(&original).unwrap()).unwrap();
    assert!(s.store.read_checkpoint(&a.session_id).is_ok());
    s.stop("stop".into(), &a.session_id, &a.generation).unwrap();
}
