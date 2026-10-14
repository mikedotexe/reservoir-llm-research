//! Explicit opt-in investigation: real generated records, no filler or provider.
use super::*;
use crate::files;
use serde_json::{json, Value};

fn save(path: &Path, value: &impl serde::Serialize) {
    use std::io::Write;
    let mut file = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .unwrap();
    file.write_all(&serde_json::to_vec_pretty(value).unwrap())
        .unwrap();
}
fn copy_tree(source: &Path, destination: &Path) {
    fs::create_dir(destination).unwrap();
    for entry in fs::read_dir(source).unwrap() {
        let entry = entry.unwrap();
        if entry.file_type().unwrap().is_dir() {
            copy_tree(&entry.path(), &destination.join(entry.file_name()));
        } else {
            assert!(entry.file_type().unwrap().is_file());
            fs::copy(entry.path(), destination.join(entry.file_name())).unwrap();
        }
    }
}
fn outcome<T>(result: Result<T, AppError>) -> Value {
    match result {
        Ok(_) => json!({"ok":true}),
        Err(error) => json!({"ok":false,"error":error}),
    }
}
fn snapshot(s: &SustainedState, id: &str) -> Value {
    let g = s.lock().unwrap();
    let a = g.active.as_ref().unwrap();
    let bytes = fs::read(s.shared.store.path(id).unwrap().join("manifest.json")).unwrap();
    let disk: Value = serde_json::from_slice(&bytes).unwrap();
    json!({
        "summary":s.summary(a),"uncommittedEvents":a.engine.events().len(),
        "enginePhase":a.engine.phase(),"diskManifest":disk,
        "manifestSha256":crate::files::digest(&bytes),
        "actualOwnedBytes":s.shared.store.used_bytes(id).unwrap(),
        "busy":s.is_busy(),
    })
}

fn investigate(label: &str, cadence: u64) {
    let parent = PathBuf::from(
        std::env::var_os("RESERVOIR_QUOTA_EVIDENCE")
            .expect("Set a new isolated evidence directory"),
    );
    let evidence = parent.join(label);
    fs::create_dir(&evidence).unwrap();
    let store = tempfile::Builder::new()
        .prefix("owned-temp-store-")
        .tempdir_in(&evidence)
        .unwrap()
        .keep();
    let s = SustainedState::new(store.clone());
    let c = SustainedConfig {
        turn_every: cadence,
        maximum_steps: 100_000,
        maximum_turns: 10_000,
        maximum_duration_seconds: 86_400,
        storage_budget_bytes: 16 * 1024 * 1024,
        pace_ms: 100,
        ..Default::default()
    };
    assert_eq!(c.language.backend, LanguageKind::Scripted);
    let created = s
        .create("create".into(), c.clone())
        .unwrap()
        .summary
        .unwrap();
    let (id, generation) = (created.session_id, created.generation);
    let epoch = arm(&s);
    let started = Instant::now();
    let mut responses = 0u64;
    loop {
        match s.worker_boundary(epoch) {
            Ok(Work::Provider(p)) => {
                responses += 1;
                s.settle(epoch, p.attempt_id, Ok(answer()), 0).unwrap();
            }
            Ok(Work::Continue(_)) => {}
            Ok(Work::Done) => break,
            Err(error) => panic!(
                "Natural quota must hold durably before failure: {}",
                error.message
            ),
        }
        assert!(s.lock().unwrap().active.as_ref().unwrap().engine.step() < 100_000);
    }
    let before = snapshot(&s, &id);
    assert_eq!(before["summary"]["phase"], "budgetReached");
    assert_eq!(before["summary"]["step"], before["summary"]["durableStep"]);
    assert_eq!(before["uncommittedEvents"], 0);
    assert!(s.start("no-new-work".into(), &id, &generation).is_err());
    assert!(s
        .retry_language("no-new-provider".into(), &id, &generation)
        .is_err());
    assert!(before["actualOwnedBytes"].as_u64().unwrap() <= 16 * 1024 * 1024);
    copy_tree(
        &s.shared.store.path(&id).unwrap(),
        &evidence.join("first-budget-hold-bundle"),
    );
    {
        let g = s.lock().unwrap();
        let a = g.active.as_ref().unwrap();
        save(
            &evidence.join("first-budget-hold-checkpoint.json"),
            &a.engine.checkpoint(),
        );
        save(
            &evidence.join("first-budget-hold-events.json"),
            a.engine.events(),
        );
    }
    let mut operations = Vec::new();
    let retry = outcome(s.retry_save("checkpoint-retry".into(), &id, &generation));
    operations
        .push(json!({"operation":"retry_save_checkpoint","result":retry,"after":snapshot(&s,&id)}));
    let stop = outcome(s.stop("stop".into(), &id, &generation));
    assert_eq!(stop["ok"], true);
    operations.push(json!({"operation":"stop","result":stop,"after":snapshot(&s,&id)}));
    let (entry, attempt) = {
        let g = s.lock().unwrap();
        let a = g.active.as_ref().unwrap();
        (
            a.engine
                .pending_journal()
                .map(|p| p.entry.id.clone())
                .or_else(|| a.engine.prepared_application().map(|p| p.entry.id.clone())),
            a.engine
                .pending_journal()
                .map(|p| p.entry.attempt_id)
                .or_else(|| a.engine.prepared_application().map(|p| p.entry.attempt_id))
                .or_else(|| a.engine.blocked().map(|p| p.pending.attempt_id)),
        )
    };
    if entry.is_some() || attempt.is_some() {
        let skipped = outcome(s.skip("skip".into(), &id, &generation, entry, attempt));
        assert_eq!(skipped["ok"], true);
        operations
            .push(json!({"operation":"explicit_skip","result":skipped,"after":snapshot(&s,&id)}));
    } else {
        operations.push(json!({"operation":"explicit_skip","notApplicable":"No pending opportunity exists; numeric events are not a language opportunity."}));
    }
    let close = match s.finish_close(true) {
        Ok(accepted) => json!({"ok":true,"accepted":accepted}),
        Err(e) => json!({"ok":false,"error":e}),
    };
    assert_eq!(close["accepted"], true);
    // Successful close closes the command gate; reopen only that gate for this
    // inspection harness, without altering run/engine/manifest state or bytes.
    s.reopen_after_stale_close();
    operations.push(
        json!({"operation":"explicit_discard_close","result":close,"after":snapshot(&s,&id)}),
    );
    let revision = s
        .get("current".into(), None)
        .unwrap()
        .summary
        .unwrap()
        .revision;
    let export_to = evidence.join("current-export");
    fs::create_dir(&export_to).unwrap();
    let current_export = outcome(s.export(&id, &generation, Some(&revision), &export_to, &[]));
    assert_eq!(current_export["ok"], true);
    operations.push(json!({"operation":"current_revision_export","result":current_export}));
    let clean_close = s.authorize_clean_close();
    s.reopen_after_stale_close();
    let final_snapshot = snapshot(&s, &id);
    drop(s);
    let recovered = SustainedState::new(store.clone());
    let inspected = recovered
        .inspect("inspect-committed-prefix".into(), &id)
        .unwrap();
    let recovery_export_to = evidence.join("recovery-export");
    fs::create_dir(&recovery_export_to).unwrap();
    let recovery_export = outcome(recovered.export(
        &id,
        &inspected.manifest.generation,
        Some(&inspected.manifest.revision),
        &recovery_export_to,
        &[],
    ));
    assert_eq!(recovery_export["ok"], true);
    let restored = outcome(recovered.resume(
        "restore".into(),
        &id,
        &inspected.manifest.generation,
        &inspected.manifest.revision,
    ));
    assert_eq!(restored["ok"], true);
    let restored_summary = recovered
        .get("restored".into(), None)
        .unwrap()
        .summary
        .unwrap();
    assert!(!restored_summary.can_start);
    assert_eq!(restored_summary.phase, "budgetReached");
    let result = json!({"profile":label,"config":c,"providersContacted":false,"actualPacedDurationClaimed":false,
        "generationResponsesSimulated":responses,"elapsedSeconds":started.elapsed().as_secs_f64(),"gracefulBudgetHold":true,
        "firstHold":before,"operationsInOrder":operations,"authorizeCleanCloseAfterOperations":clean_close,
        "finalInMemory":final_snapshot,"committedPrefixAfterDroppingProcessState":inspected,
        "recoveryExport":recovery_export,"explicitRestore":restored,"retainedTempStore":store,
        "scope":"Genuine generated records; no filler files or quota edits. Sequential operations are stated in order; this does not simulate physical power loss."});
    save(&evidence.join("result.json"), &result);
    println!("NATURAL_QUOTA_RESULT {}",serde_json::to_string(&json!({"path":evidence.join("result.json"),"profile":label,"heldStep":before["summary"]["step"],"durableStep":before["summary"]["durableStep"],"ownedBytes":before["actualOwnedBytes"],"journalCount":before["summary"]["journalCount"],"stop":stop,"close":close,"currentExport":current_export,"recoveryExport":recovery_export,"restore":restored})).unwrap());
}

#[test]
#[ignore = "Opt-in isolated16MiB natural quota investigation; retains own temporary evidence"]
fn natural_quota_repaired_frequent_journals() {
    investigate("frequent-journals-cadence3", 3);
}

#[test]
#[ignore = "Opt-in isolated16MiB natural quota investigation; retains own temporary evidence"]
fn natural_quota_repaired_sparse_observations() {
    investigate("sparse-observations-cadence1800", 1800);
}

// These are fault-injection tests, separate from the opt-in naturally generated
// profiles above. Padding is explicit and never represented as session evidence.
fn pressure(s: &SustainedState, id: &str, remaining: u64) {
    let p = s.shared.store.path(id).unwrap();
    let budget = s
        .lock()
        .unwrap()
        .active
        .as_ref()
        .unwrap()
        .manifest
        .config
        .storage_budget_bytes;
    let used = s.shared.store.used_bytes(id).unwrap();
    let f = fs::File::create(p.join("quota-test-pressure.bin")).unwrap();
    f.set_len(budget.checked_sub(used + remaining).unwrap())
        .unwrap();
}

#[test]
fn quota_held_marker_survives_diagnostics_and_terminal_revision_changes() {
    let (_d, s, id, generation) = setup(100, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_journal().is_some());
    let before = s.inspect("before".into(), &id).unwrap();
    pressure(&s, &id, sustained_store::RUN_HEADROOM - 1);
    {
        let mut g = s.lock().unwrap();
        let a = g.active.as_mut().unwrap();
        s.save_journal(a).unwrap();
        assert!(sustained_store::storage_held(&a.manifest));
        assert_eq!(a.catalog.len(), 0);
        for i in 0..100 {
            diagnostic(a, &format!("bounded test diagnostic {i}"));
        }
        assert!(sustained_store::storage_held(&a.manifest));
        assert_eq!(a.manifest.diagnostics.len(), 32);
    }
    let after = s.inspect("after".into(), &id).unwrap();
    assert_ne!(before.manifest.revision, after.manifest.revision);
    assert_eq!(after.manifest.phase, "budgetReached");
    assert!(s.start("start".into(), &id, &generation).is_err());
    assert!(s.retry_save("retry".into(), &id, &generation).is_err());
    assert!(s
        .retry_language("provider".into(), &id, &generation)
        .is_err());
    assert!(matches!(s.worker_boundary(epoch).unwrap(), Work::Done));
    s.stop("stop".into(), &id, &generation).unwrap();
    assert!(s.finish_close(true).unwrap());
    assert!(matches!(
        s.shared.store.verify(&id).unwrap().checkpoint.state.phase,
        SustainedPhase::Ready
    ));
}

#[test]
fn quota_duration_pending_boundary_has_new_durable_revision() {
    let (_d, s, id, _) = setup(100, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_language().is_some());
    let before = s.inspect("before".into(), &id).unwrap();
    {
        let mut g = s.lock().unwrap();
        let a = g.active.as_mut().unwrap();
        a.manifest.elapsed_millis = a.manifest.config.maximum_duration_seconds * 1000;
    }
    assert!(matches!(s.worker_boundary(epoch).unwrap(), Work::Done));
    let after = s.inspect("after".into(), &id).unwrap();
    assert_eq!(after.manifest.phase, "budgetReached");
    assert_ne!(before.manifest.revision, after.manifest.revision);
}

#[test]
fn quota_old_ready_prefix_exports_and_discards_only_volatile_tail() {
    let (d, s, id, generation) = setup(1800, 1800);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.step() == 30);
    let inspected = s.inspect("before".into(), &id).unwrap();
    until(&s, epoch, |a| a.engine.step() == 59);
    pressure(&s, &id, 100);
    let before = fs::read(s.shared.store.path(&id).unwrap().join("manifest.json")).unwrap();
    assert!(s.stop("stop".into(), &id, &generation).is_err());
    let live_revision = s
        .get("live".into(), None)
        .unwrap()
        .summary
        .unwrap()
        .revision;
    let out = d.path().join("exports");
    fs::create_dir(&out).unwrap();
    assert!(s
        .export(&id, &generation, Some(&live_revision), &out, &[])
        .is_err());
    let (_, report) = s
        .export(
            &id,
            &generation,
            Some(&inspected.manifest.revision),
            &out,
            &[],
        )
        .unwrap();
    assert_eq!(report.step, 30);
    assert_eq!(report.manifest_sha256, files::digest(&before));
    assert!(s.finish_close(true).unwrap());
    assert_eq!(
        fs::read(s.shared.store.path(&id).unwrap().join("manifest.json")).unwrap(),
        before
    );
    s.reopen_after_stale_close();
    let summary = s.get("done".into(), None).unwrap().summary.unwrap();
    assert_eq!(summary.step, 30);
    assert_eq!(summary.durable_step, 30);
    assert_eq!(summary.phase, "stopped");
    assert!(summary
        .diagnostics
        .iter()
        .any(|d| d.contains("live step was 59")));
}

#[test]
fn quota_old_retained_intent_never_uses_ready_discard_fallback() {
    for phase in ["language", "journal", "prepared"] {
        let (_d, s, id, generation) = setup(100, 3);
        let epoch = arm(&s);
        until(&s, epoch, |a| {
            if phase == "language" {
                a.engine.pending_language().is_some()
            } else {
                a.engine.pending_journal().is_some()
            }
        });
        if phase == "prepared" {
            s.pause("hold".into(), &id, &generation).unwrap();
            assert!(matches!(s.worker_boundary(epoch).unwrap(), Work::Done));
            assert!(s
                .lock()
                .unwrap()
                .active
                .as_ref()
                .unwrap()
                .engine
                .prepared_application()
                .is_some());
        }
        let before = fs::read(s.shared.store.path(&id).unwrap().join("manifest.json")).unwrap();
        pressure(&s, &id, 100);
        assert!(s.finish_close(true).is_err(), "{phase}");
        assert!(!s.shared.closing.load(Ordering::SeqCst));
        assert_eq!(
            fs::read(s.shared.store.path(&id).unwrap().join("manifest.json")).unwrap(),
            before
        );
        assert!(!matches!(
            s.shared.store.verify(&id).unwrap().checkpoint.state.phase,
            SustainedPhase::Ready
        ));
    }
}

#[test]
fn quota_escaped_rejected_response_cannot_publish_or_claim_discard_of_retained_language() {
    let (_d, s, id, _) = setup(100, 3);
    let epoch = arm(&s);
    until(&s, epoch, |a| a.engine.pending_language().is_some());
    let Work::Provider(p) = s.worker_boundary(epoch).unwrap() else {
        panic!()
    };
    let before = fs::read(s.shared.store.path(&id).unwrap().join("manifest.json")).unwrap();
    let mut response = answer();
    response.text = "\0".repeat(1_048_576);
    let error = s.settle(epoch, p.attempt_id, Ok(response), 0).unwrap_err();
    assert_eq!(error.category, "budget");
    assert!(error.message.contains("Segment exceeds object limit"));
    assert_eq!(
        fs::read(s.shared.store.path(&id).unwrap().join("manifest.json")).unwrap(),
        before
    );
    assert!(s.finish_close(true).is_err());
    assert!(!s.shared.closing.load(Ordering::SeqCst));
    let retained = s.shared.store.verify(&id).unwrap();
    assert_eq!(retained.manifest.journal_count, 0);
    assert!(matches!(
        retained.checkpoint.state.phase,
        SustainedPhase::Language(_)
    ));
}

#[test]
fn quota_transport_sized_escaped_responses_retain_exact_terminal_path() {
    for length in [65_536usize, 170_000] {
        let (_d, s, id, generation) = setup(100, 3);
        let epoch = arm(&s);
        until(&s, epoch, |a| a.engine.pending_language().is_some());
        let Work::Provider(first) = s.worker_boundary(epoch).unwrap() else {
            panic!()
        };
        let mut previous = answer();
        previous.text = "\0".repeat(65_536);
        s.settle(epoch, first.attempt_id, Ok(previous), 0).unwrap();
        assert!(s
            .lock()
            .unwrap()
            .active
            .as_ref()
            .unwrap()
            .engine
            .pending_journal()
            .is_some());
        until(&s, epoch, |a| a.engine.pending_memory().is_some());
        let Work::Provider(p) = s.worker_boundary(epoch).unwrap() else {
            panic!()
        };
        assert_eq!(p.memory.as_ref().unwrap().entry.text.len(), 65_536);
        let mut response = answer();
        response.text = "\0".repeat(length);
        let transport = serde_json::json!({"response":response.text,"done":true,"done_reason":"stop","eval_count":18,"model":"owned-fixture"});
        assert!(serde_json::to_vec(&transport).unwrap().len() <= 1_048_576);
        s.pause("pause-in-flight".into(), &id, &generation).unwrap();
        s.settle(epoch, p.attempt_id, Ok(response), 0).unwrap();
        s.shared.store.verify(&id).unwrap();
        s.stop("stop".into(), &id, &generation).unwrap();
        assert!(s.finish_close(true).unwrap());
        let retained = s.shared.store.verify(&id).unwrap();
        assert!(matches!(
            retained.checkpoint.state.phase,
            SustainedPhase::Ready
        ));
        assert_eq!(retained.manifest.journal_count, 1);
    }
}

#[test]
fn quota_legacy_retry_that_newly_reaches_low_water_does_not_publish_journal() {
    let (_d, s, id, generation) = setup(100, 3);
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
        .id
        .clone();
    pressure(&s, &id, sustained_store::RUN_HEADROOM - 1);
    {
        let mut g = s.lock().unwrap();
        let a = g.active.as_mut().unwrap();
        a.manifest.phase = "storageBlocked".into();
        a.run_requested = false;
    }
    let result = s
        .retry_save("retry-at-low-water".into(), &id, &generation)
        .unwrap();
    assert_eq!(result.summary.unwrap().phase, "budgetReached");
    assert!(!s
        .shared
        .store
        .path(&id)
        .unwrap()
        .join("journals")
        .join(format!("{entry}.json"))
        .exists());
    let retained = s.shared.store.verify(&id).unwrap();
    assert_eq!(retained.manifest.journal_count, 0);
    assert!(matches!(
        retained.checkpoint.state.phase,
        SustainedPhase::Journal(_)
    ));
}
