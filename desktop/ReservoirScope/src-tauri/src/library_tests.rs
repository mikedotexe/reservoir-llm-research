use super::*;
use reservoir_core::exploration::ExplorationEngine;
use std::time::Instant;

fn fixture() -> (tempfile::TempDir, LibraryState) {
    let dir = tempfile::tempdir().unwrap();
    let resources = Path::new(env!("CARGO_MANIFEST_DIR")).join("resources");
    let state = LibraryState::new(dir.path().join("library-v1"), resources);
    (dir, state)
}
fn recording(label: &str) -> Vec<u8> {
    let record = ExplorationEngine::new(u64::MAX).record();
    let mut value = serde_json::to_value(record).unwrap();
    value["id"] = label.into();
    let mut bytes = serde_json::to_vec_pretty(&value).unwrap();
    bytes.extend_from_slice(b"\n \n");
    bytes
}
fn managed() -> LibraryQuery {
    LibraryQuery {
        origin: Some("managed".into()),
        limit: Some(100),
        ..Default::default()
    }
}
fn record_path(state: &LibraryState, bytes: &[u8]) -> PathBuf {
    state
        .root
        .join("records")
        .join(format!("{}.json", files::digest(bytes)))
}
fn place_header(state: &LibraryState, index: usize) {
    let bytes = format!(
        "{{\"format\":\"future-record-v7\",\"seed\":18446744073709551615,\"id\":\"row-{index}\"}}"
    )
    .into_bytes();
    fs::write(record_path(state, &bytes), bytes).unwrap();
}
#[test]
fn catalog_is_authored_order_read_only_and_coverage_is_honest() {
    let (_dir, state) = fixture();
    let page = state.query(LibraryQuery::default()).unwrap();
    assert_eq!(page.total, 22);
    assert_eq!(page.entries[0].id, "catalog:component-1");
    assert_eq!(page.entries[8].id, "catalog:example-model-4");
    assert!(page
        .entries
        .iter()
        .enumerate()
        .all(|(i, e)| e.catalog_order == Some(i) && e.origin == "bundled"));
    assert!(page.entries.iter().all(|e| e.health == "unverified"));
    let controller = page
        .entries
        .iter()
        .find(|e| e.id == "catalog:regulation-controller")
        .unwrap();
    assert_eq!(controller.family, "regulation");
    assert_eq!(controller.source, "numerical");
    assert!(!page.coverage.complete);
    assert_eq!(fs::read_dir(state.root.join("records")).unwrap().count(), 0);
    let attention = state
        .query(LibraryQuery {
            diagnostics_only: true,
            ..Default::default()
        })
        .unwrap();
    assert_eq!(attention.total, 0);
    assert!(state
        .open(
            &RecordState::default(),
            "unknown".into(),
            "catalog:../other"
        )
        .is_err());
}
#[test]
fn build_change_refreshes_catalog_without_touching_managed_bytes_or_recents() {
    let (_dir, state) = fixture();
    let mut old = state.query(LibraryQuery::default()).unwrap().entries;
    let controller = old
        .iter_mut()
        .find(|e| e.id == "catalog:regulation-controller")
        .unwrap();
    controller.family = "unknown".into();
    controller.health = "notBundled".into();
    let c = state.connection().unwrap();
    upsert(&c, controller).unwrap();
    upsert(
        &c,
        &empty_entry(
            "catalog:retired-example".into(),
            "old.json".into(),
            "bundled",
        ),
    )
    .unwrap();
    c.execute(
        "UPDATE settings SET value='previous-build' WHERE key='catalog-build'",
        [],
    )
    .unwrap();
    c.execute(
        "INSERT INTO recents(id,opened) VALUES('catalog:regulation-controller',1234)",
        [],
    )
    .unwrap();
    let bytes = recording("preserved-import");
    let saved = state
        .import_bytes("import".into(), "saved.json", &bytes)
        .unwrap();
    let restarted = LibraryState::new(state.root.clone(), state.resources.clone());
    let page = restarted.query(LibraryQuery::default()).unwrap();
    assert_eq!(page.total, 23);
    let controller = page
        .entries
        .iter()
        .find(|e| e.id == "catalog:regulation-controller")
        .unwrap();
    assert_eq!(controller.family, "regulation");
    assert_eq!(controller.health, "unverified");
    assert_eq!(controller.last_opened_at_ms, Some(1234));
    assert!(page
        .entries
        .iter()
        .any(|e| Some(&e.id) == saved.entry_id.as_ref()));
    assert!(!page
        .entries
        .iter()
        .any(|e| e.id == "catalog:retired-example"));
    assert_eq!(fs::read(record_path(&state, &bytes)).unwrap(), bytes);
}

#[test]
fn controller_import_filters_and_reopens_original_bytes() {
    let (_dir, state) = fixture();
    let (_, bytes) = resources::record_example(&state.resources, "regulation-controller").unwrap();
    // Native decodeIfPresent treats explicit null exactly like an omitted seed.
    // The metadata projection must not label a verifier-accepted import damaged.
    let mut value: serde_json::Value = serde_json::from_slice(&bytes).unwrap();
    value["specification"]["fieldSeed"] = serde_json::Value::Null;
    let bytes = serde_json::to_vec(&value).unwrap();
    let saved = state
        .import_bytes("controller".into(), "controller.json", &bytes)
        .unwrap();
    assert!(saved.published && saved.diagnostics.is_empty());
    let page = state
        .query(LibraryQuery {
            family: Some("regulation".into()),
            source: Some("numerical".into()),
            text: "98".into(),
            ..managed()
        })
        .unwrap();
    assert_eq!(page.total, 1);
    assert_eq!(page.entries[0].seed.as_deref(), Some("98"));
    assert_eq!(page.entries[0].health, "ready");
    let records = RecordState::default();
    let opened = state
        .open(&records, "open-controller".into(), &page.entries[0].id)
        .unwrap();
    let record = opened.record.unwrap();
    assert_eq!(record.family, "regulation");
    assert!(record.study.is_some());
    assert_eq!(
        records.snapshot(&record.record_id).unwrap().1.as_ref(),
        &bytes
    );
}

#[test]
fn exact_bytes_duplicates_embedded_ids_and_wide_seed_survive_restart() {
    let (_dir, state) = fixture();
    let a = recording("same-id");
    let first = state
        .import_bytes("first".into(), "Éclair %_ '\".json", &a)
        .unwrap();
    assert!(first.published && !first.duplicate && first.diagnostics.is_empty());
    assert_eq!(fs::read(record_path(&state, &a)).unwrap(), a);
    let first_entry = state.query(managed()).unwrap().entries.remove(0);
    assert_eq!(first_entry.seed.as_deref(), Some("18446744073709551615"));
    assert_eq!(first_entry.embedded_id.as_deref(), Some("same-id"));
    let duplicate = state
        .import_bytes("again".into(), "rename.json", &a)
        .unwrap();
    assert!(duplicate.published && duplicate.duplicate);
    assert_eq!(duplicate.entry_id, first.entry_id);
    let mut b = a.clone();
    b.push(b' ');
    let second = state
        .import_bytes("different".into(), "other.json", &b)
        .unwrap();
    assert!(second.published && !second.duplicate);
    assert_ne!(second.entry_id, first.entry_id);
    let reopened = LibraryState::new(state.root.clone(), state.resources.clone());
    let page = reopened.query(managed()).unwrap();
    assert_eq!(page.total, 2);
    let retained = page
        .entries
        .iter()
        .find(|e| e.id == first_entry.id)
        .unwrap();
    assert_eq!(retained.filename, first_entry.filename);
    assert_eq!(retained.saved_at_ms, first_entry.saved_at_ms);
    assert_eq!(
        reopened
            .query(LibraryQuery {
                text: "éCLAIR %_ '".into(),
                ..managed()
            })
            .unwrap()
            .total,
        1
    );
    assert_eq!(
        reopened
            .query(LibraryQuery {
                text: "' OR 1=1".into(),
                ..managed()
            })
            .unwrap()
            .total,
        0
    );
}
#[test]
fn numerical_failure_and_other_verified_scopes_never_publish() {
    let (_dir, state) = fixture();
    let mut invalid: serde_json::Value = serde_json::from_slice(&recording("invalid")).unwrap();
    invalid["model"]["recurrentWeights"][0] = 999.0.into();
    let bytes = serde_json::to_vec(&invalid).unwrap();
    let result = state
        .import_bytes("bad".into(), "bad.json", &bytes)
        .unwrap();
    assert!(!result.published);
    assert_ne!(result.report.unwrap().status, VerificationStatus::Passed);
    for bytes in [
        br#"{"format":"reservoir-research-case-v1","seed":[],"recipeVersion":"essentials-v1"}"#
            .as_slice(),
        br#"{"format":"reservoir-geometry-v1","seed":[],"recipeVersion":"essentials-v1"}"#,
        br#"{"format":"future","recipeVersion":"essentials-v1"}"#,
        br#"{"format":"essentials-v1","recipeVersion":"essentials-v1"}"#,
        br#"not-json"#,
    ] {
        let rejected = state
            .import_bytes("scope".into(), "scope.json", bytes)
            .unwrap();
        assert!(!rejected.published && rejected.report.is_none());
        assert!(!rejected.diagnostics.is_empty());
    }
    // These are genuinely valid packets for other verifier scopes, even with a
    // malformed experiment-only extra field. They must still not be imported.
    for name in ["research-cases-v1.json", "synthetic-geometry-example.json"] {
        let original = fs::read(state.resources.join(name)).unwrap();
        let mut value: serde_json::Value = serde_json::from_slice(&original).unwrap();
        value["seed"] = serde_json::json!([]);
        let packet = serde_json::to_vec(&value).unwrap();
        assert_eq!(
            verify_bytes(&packet).status,
            VerificationStatus::Passed,
            "{name}"
        );
        let rejected = state
            .import_bytes("other-scope".into(), name, &packet)
            .unwrap();
        assert!(!rejected.published && rejected.report.is_none());
    }
    assert_eq!(fs::read_dir(state.root.join("records")).unwrap().count(), 0);
}
#[test]
fn corrupt_index_cannot_erase_published_record_and_rebuild_recovers() {
    let (_dir, state) = fixture();
    state.owned().unwrap();
    fs::write(state.root.join("index.sqlite3"), b"damaged index").unwrap();
    let bytes = recording("recovery");
    let saved = state
        .import_bytes("save".into(), "recover.json", &bytes)
        .unwrap();
    assert!(saved.published && !saved.diagnostics.is_empty());
    assert_eq!(fs::read(record_path(&state, &bytes)).unwrap(), bytes);
    assert!(state.query(managed()).is_err());
    let scan = state.scan(true).unwrap();
    assert!(scan.complete && scan.message.contains("recents could not be recovered"));
    assert_eq!(state.query(managed()).unwrap().total, 1);
    assert_eq!(fs::read(record_path(&state, &bytes)).unwrap(), bytes);
    assert!(fs::read_dir(&state.root).unwrap().any(|p| p
        .unwrap()
        .file_name()
        .to_string_lossy()
        .starts_with("index-backup-")));
}
#[test]
fn publication_refuses_collision_and_index_directory_and_preserves_records() {
    let (_dir, state) = fixture();
    state.owned().unwrap();
    let bytes = recording("one");
    let path = record_path(&state, &bytes);
    fs::write(&path, b"different damaged bytes").unwrap();
    assert!(state
        .import_bytes("collision".into(), "one.json", &bytes)
        .is_err());
    assert_eq!(fs::read(&path).unwrap(), b"different damaged bytes");
    fs::remove_file(&path).unwrap();
    fs::create_dir(state.root.join("index.sqlite3")).unwrap();
    let saved = state
        .import_bytes("blocked-index".into(), "one.json", &bytes)
        .unwrap();
    assert!(saved.published && !saved.diagnostics.is_empty());
    assert!(state.scan(true).is_err());
    assert!(!state.scan_status().complete);
    assert_eq!(fs::read(&path).unwrap(), bytes);
}
#[test]
fn missing_damaged_unsupported_unreadable_rows_remain_visible() {
    let (_dir, state) = fixture();
    let bytes = recording("missing");
    let saved = state
        .import_bytes("a".into(), "missing.json", &bytes)
        .unwrap();
    fs::remove_file(record_path(&state, &bytes)).unwrap();
    let damaged = "a".repeat(64);
    fs::write(
        state.root.join("records").join(format!("{damaged}.json")),
        b"different",
    )
    .unwrap();
    let unreadable = "b".repeat(64);
    fs::create_dir(
        state
            .root
            .join("records")
            .join(format!("{unreadable}.json")),
    )
    .unwrap();
    place_header(&state, 1);
    let scan = state.scan(true).unwrap();
    assert!(scan.complete);
    assert_eq!(scan.examined, 3);
    assert_eq!(scan.indexed, 4);
    let rows = state.query(managed()).unwrap().entries;
    for health in ["missing", "damaged", "unreadable", "unsupported"] {
        assert!(rows.iter().any(|e| e.health == health), "{health}");
    }
    assert_eq!(
        rows.iter()
            .find(|e| e.id == saved.entry_id.as_ref().unwrap().as_str())
            .unwrap()
            .filename,
        "missing.json"
    );
    assert_eq!(
        state
            .query(LibraryQuery {
                diagnostics_only: true,
                ..managed()
            })
            .unwrap()
            .total,
        4
    );
}
#[test]
fn refresh_detects_removed_record_even_when_local_metadata_is_also_missing() {
    let (_dir, state) = fixture();
    let bytes = recording("gone");
    state.import_bytes("a".into(), "gone.json", &bytes).unwrap();
    fs::remove_file(record_path(&state, &bytes)).unwrap();
    fs::remove_file(
        state
            .root
            .join("metadata")
            .join(format!("{}.json", files::digest(&bytes))),
    )
    .unwrap();
    state.scan(false).unwrap();
    assert_eq!(state.query(managed()).unwrap().entries[0].health, "missing");
}
#[test]
fn opening_reverifies_exact_bytes_and_recents_persist_through_rebuild() {
    let (_dir, state) = fixture();
    let bytes = recording("recent");
    let saved = state
        .import_bytes("a".into(), "recent.json", &bytes)
        .unwrap();
    let id = saved.entry_id.unwrap();
    let records = RecordState::default();
    let opened = state.open(&records, "open".into(), &id).unwrap();
    let summary = opened.record.unwrap();
    assert_eq!(summary.origin, "managed");
    assert_eq!(
        records.snapshot(&summary.record_id).unwrap().1.as_ref(),
        &bytes
    );
    let time = state
        .query(LibraryQuery {
            recent_only: true,
            ..managed()
        })
        .unwrap()
        .entries[0]
        .last_opened_at_ms;
    state.scan(true).unwrap();
    let restarted = LibraryState::new(state.root.clone(), state.resources.clone());
    assert_eq!(
        restarted
            .query(LibraryQuery {
                recent_only: true,
                ..managed()
            })
            .unwrap()
            .entries[0]
            .last_opened_at_ms,
        time
    );
    fs::write(record_path(&state, &bytes), b"changed").unwrap();
    assert!(state.open(&records, "again".into(), &id).is_err());
    assert!(state
        .open(&records, "escape".into(), "sha256:../../outside")
        .is_err());
}
#[test]
fn more_than_old_scan_limits_is_fully_pageable_and_interruptions_are_explicit() {
    let (_dir, state) = fixture();
    state.owned().unwrap();
    for i in 0..5001 {
        place_header(&state, i);
    }
    let worker = state.clone();
    let join = std::thread::spawn(move || worker.scan(false));
    let start = Instant::now();
    while state.scan_status().examined < 10
        && !join.is_finished()
        && start.elapsed() < Duration::from_secs(20)
    {
        std::thread::sleep(Duration::from_millis(1));
    }
    assert!(
        !join.is_finished(),
        "fixture scan completed before cancellation was exercised"
    );
    state.cancel_scan();
    let interrupted = join.join().unwrap().unwrap();
    assert_eq!(interrupted.phase, "interrupted");
    assert!(!interrupted.complete);
    let restarted = LibraryState::new(state.root.clone(), state.resources.clone());
    assert!(!restarted.query(managed()).unwrap().coverage.complete);
    let completed = state.scan(false).unwrap();
    assert!(completed.complete);
    assert_eq!(completed.examined, 5001);
    assert_eq!(completed.indexed, 5001);
    let mut ids = HashSet::new();
    let mut offset = 0;
    let mut previous = String::new();
    loop {
        let page = state
            .query(LibraryQuery {
                offset,
                ..managed()
            })
            .unwrap();
        assert_eq!(page.total, 5001);
        assert!(page.entries.len() <= 100);
        for entry in page.entries {
            assert!(entry.id > previous);
            previous = entry.id.clone();
            assert!(ids.insert(entry.id));
        }
        if !page.has_more {
            break;
        }
        offset += page.limit;
    }
    assert_eq!(ids.len(), 5001);
    assert_eq!(
        state
            .query(LibraryQuery {
                text: "row-5000".into(),
                ..managed()
            })
            .unwrap()
            .total,
        1
    );
}
#[test]
fn interrupted_persisted_scan_and_corrupt_payload_are_not_reported_as_empty() {
    let (_dir, state) = fixture();
    let c = state.connection().unwrap();
    save_coverage(
        &c,
        &ScanStatus {
            phase: "running".into(),
            ..Default::default()
        },
    )
    .unwrap();
    let page = state.query(managed()).unwrap();
    assert_eq!(page.coverage.phase, "interrupted");
    assert!(!page.coverage.complete);
    let mut entry = empty_entry("test".into(), "broken".into(), "managed");
    entry.health = "damaged".into();
    upsert(&c, &entry).unwrap();
    c.execute("UPDATE entries SET payload='broken' WHERE id='test'", [])
        .unwrap();
    assert!(state.query(managed()).is_err());
}
#[test]
fn query_and_scan_initialization_can_race_without_adopting_foreign_store() {
    let (_dir, state) = fixture();
    let other = state.clone();
    let thread = std::thread::spawn(move || other.query(LibraryQuery::default()));
    state.scan(false).unwrap();
    assert_eq!(thread.join().unwrap().unwrap().total, 22);
    let foreign = tempfile::tempdir().unwrap();
    fs::write(foreign.path().join("existing.json"), b"private").unwrap();
    let rejected = LibraryState::new(foreign.path().into(), state.resources.clone());
    assert!(rejected.query(managed()).is_err());
    assert!(!foreign.path().join("owner.json").exists());
}
#[cfg(unix)]
#[test]
fn symlink_roots_records_and_metadata_are_not_followed() {
    use std::os::unix::fs::symlink;
    let (dir, state) = fixture();
    let outside = dir.path().join("outside");
    fs::create_dir(&outside).unwrap();
    symlink(&outside, &state.root).unwrap();
    assert!(state.query(managed()).is_err());
    fs::remove_file(&state.root).unwrap();
    state.owned().unwrap();
    let bytes = recording("link");
    let source = outside.join("source.json");
    fs::write(&source, &bytes).unwrap();
    symlink(&source, record_path(&state, &bytes)).unwrap();
    assert!(state
        .import_path("source-link".into(), &record_path(&state, &bytes))
        .is_err());
    state.scan(false).unwrap();
    assert_eq!(
        state.query(managed()).unwrap().entries[0].health,
        "unreadable"
    );
    assert!(state
        .open(
            &RecordState::default(),
            "link".into(),
            &format!("sha256:{}", files::digest(&bytes))
        )
        .is_err());
    assert_eq!(fs::read(source).unwrap(), bytes);
}

#[test]
fn fixed_tape_route_never_becomes_model_source_from_unused_configuration() {
    let (_dir, state) = fixture();
    let mut value: serde_json::Value = serde_json::from_slice(
        &fs::read(state.resources.join("example-component-8.json")).unwrap(),
    )
    .unwrap();
    value["specification"]["language"] = serde_json::json!({"backend":"ollama","endpoint":"http://localhost:11434","model":"declared-unused-model"});
    let bytes = serde_json::to_vec(&value).unwrap();
    assert_eq!(verify_bytes(&bytes).status, VerificationStatus::Passed);
    let parsed = metadata(&bytes, "tape.json").unwrap();
    assert_eq!(parsed.source, "fixedReplay");
    assert_eq!(parsed.backend, "ollama");
    let c = state.connection().unwrap();
    let mut entry = empty_entry("tape".into(), "tape.json".into(), "managed");
    apply_metadata(&mut entry, parsed);
    upsert(&c, &entry).unwrap();
    assert_eq!(
        state
            .query(LibraryQuery {
                source: Some("model".into()),
                ..managed()
            })
            .unwrap()
            .total,
        0
    );
    assert_eq!(
        state
            .query(LibraryQuery {
                source: Some("fixedReplay".into()),
                ..managed()
            })
            .unwrap()
            .total,
        1
    );
    value["specification"]
        .as_object_mut()
        .unwrap()
        .remove("mode");
    assert_eq!(
        metadata(&serde_json::to_vec(&value).unwrap(), "historical.json")
            .unwrap()
            .source,
        "fixedReplay"
    );
    let bytes = fs::read(state.resources.join("example-model-4.json")).unwrap();
    assert_eq!(metadata(&bytes, "model.json").unwrap().source, "model");
    assert_eq!(
        metadata(&recording("empty"), "no-turns.json")
            .unwrap()
            .source,
        "unknown"
    );
}
#[cfg(unix)]
#[test]
fn diagnostic_identity_uses_filename_bytes_not_lossy_display_text() {
    use std::{ffi::OsStr, os::unix::ffi::OsStrExt};
    // APFS rejects these names on creation; test the exact scanner identity
    // function without claiming a non-UTF-8 filesystem roundtrip on macOS.
    let a = OsStr::from_bytes(b"bad-\xff");
    let b = OsStr::from_bytes(b"bad-\xfe");
    assert_eq!(a.to_string_lossy(), b.to_string_lossy());
    assert_ne!(diagnostic_file_id(a), diagnostic_file_id(b));
}

#[test]
fn ignored_cross_family_fields_cannot_break_or_promote_library_metadata() {
    let (_dir, state) = fixture();
    let mut value: serde_json::Value =
        serde_json::from_slice(&recording("ignored-fields")).unwrap();
    value["specification"] = serde_json::json!({"language":{"backend":"ollama","model":"ignored-model"},"stage":8,"mode":"fixedReplay"});
    value["turns"] = serde_json::json!([{"backend":[]}]);
    value["left"] = serde_json::json!("ignored");
    value["status"] = serde_json::json!([]);
    let bytes = serde_json::to_vec(&value).unwrap();
    let result = state
        .import_bytes("cross-family".into(), "ignored.json", &bytes)
        .unwrap();
    assert!(result.published);
    let row = state.query(managed()).unwrap().entries.remove(0);
    assert_eq!(row.health, "ready");
    assert_eq!(row.source, "unknown");
    assert_eq!(row.backend, "unknown");
    assert_eq!(row.model, "unknown");
    assert_eq!(row.stage, None);
    assert_eq!(row.outcome, "snapshot");
    assert_eq!(fs::read(record_path(&state, &bytes)).unwrap(), bytes);
    assert!(state
        .open(
            &RecordState::default(),
            "open".into(),
            result.entry_id.as_ref().unwrap()
        )
        .unwrap()
        .record
        .is_some());
    value["specification"] = serde_json::json!([]);
    assert_eq!(
        metadata(&serde_json::to_vec(&value).unwrap(), "ignored-spec.json")
            .unwrap()
            .family,
        "exploration"
    );
    assert_eq!(
        metadata(
            br#"{"format":"future","seed":[],"specification":[],"turns":[]}"#,
            "future.json"
        )
        .unwrap()
        .family,
        "unknown"
    );
    assert_eq!(
        metadata(
            br#"{"format":"essentials-v1","recipeVersion":"essentials-v1"}"#,
            "priority.json"
        )
        .unwrap()
        .family,
        "unknown"
    );
}
