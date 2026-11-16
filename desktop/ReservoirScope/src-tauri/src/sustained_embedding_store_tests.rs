//! Store-level encoding recovery: no provider or embedder is contacted.
use super::*;
use reservoir_core::{
    codec,
    session::LanguageResponse,
    stage::LanguageConfiguration,
    sustained::{ExternalFeedback, FeedbackProvenance, SustainedPhase},
};

fn setup(
    embedding: bool,
) -> (
    tempfile::TempDir,
    SustainedStore,
    Manifest,
    SustainedSession,
    SustainedCheckpoint,
) {
    let directory = tempfile::tempdir().unwrap();
    let store = SustainedStore::new(directory.path().join("store"));
    let config = SustainedConfig {
        turn_every: 3,
        maximum_steps: 8,
        maximum_turns: 1,
        storage_budget_bytes: 16 * 1024 * 1024,
        language: LanguageConfiguration {
            backend: LanguageKind::Ollama,
            endpoint: Some("http://127.0.0.1:1".into()),
            model: Some("fixture-writer".into()),
            context_tokens: Some(4096),
            response_format: None,
            temperature: None,
            thinking: None,
        },
        embedding_model: embedding.then(|| "fixture-embedding".into()),
        embedding_projection_seed: embedding.then(|| "99".into()),
        ..Default::default()
    };
    let engine = SustainedSession::new(config.specification().unwrap()).unwrap();
    let mut manifest = Manifest {
        configuration_changes: vec![],
        format: "reservoir-sustained-bundle-v1".into(),
        session_id: "embedding-store-test".into(),
        generation: "1".into(),
        revision: "1".into(),
        config,
        limit_extensions: vec![],
        phase: "ready".into(),
        step: 0,
        durable_step: 0,
        elapsed_millis: 0,
        journal_count: 0,
        segment_count: 0,
        last_segment_sha256: None,
        checkpoint_sha256: String::new(),
        previous_checkpoint_sha256: None,
        diagnostics: vec![],
        attempt_timing: None,
    };
    let committed = engine.checkpoint();
    store.initialize(&mut manifest, &committed).unwrap();
    (directory, store, manifest, engine, committed)
}

fn persist(
    store: &SustainedStore,
    manifest: &mut Manifest,
    engine: &mut SustainedSession,
    committed: &mut SustainedCheckpoint,
    phase: &str,
    admission: Admission,
) {
    manifest.phase = phase.into();
    manifest.revision = (manifest.revision.parse::<u64>().unwrap() + 1).to_string();
    *committed = store
        .persist(manifest, committed, engine, admission)
        .unwrap();
}

fn response(text: String) -> LanguageResponse {
    LanguageResponse {
        text,
        provider_model: Some("fixture-writer".into()),
        stop_reason: Some("stop".into()),
        token_count: Some(42),
        provider_prompt_evaluation: None,
        complete: true,
    }
}

fn feedback() -> ExternalFeedback {
    let raw: Vec<f64> = (0..768).map(|i| (i as f64 * 0.37).sin()).collect();
    ExternalFeedback {
        vector: codec::project_embedding(&raw, 99).unwrap(),
        provenance: FeedbackProvenance {
            kind: "embedding".into(),
            model: "fixture-embedding".into(),
            digest: None,
            dimensions: 768,
            embedding_sha256: files::digest(&json(&raw).unwrap()),
            projection_seed: 99,
        },
    }
}

fn dispatch(engine: &mut SustainedSession) -> u64 {
    for _ in 0..3 {
        engine.advance().unwrap();
    }
    let attempt = engine.pending_language().unwrap().attempt_id;
    engine.start_language(attempt).unwrap();
    attempt
}

#[test]
fn encoding_failure_export_and_retry_preserve_one_generated_response() {
    let (directory, store, mut manifest, mut engine, mut committed) = setup(true);
    let attempt = dispatch(&mut engine);
    // The byte cap lands inside the four-byte moon, so a byte slice would panic
    // or lose UTF-8 validity. Full text must remain in retained evidence.
    let raw = format!(
        "{}🌙\n  <script>inert journal text</script>\n",
        "x".repeat(16_383)
    );
    let reply = response(raw.clone());
    engine
        .retain_language_for_feedback(attempt, &reply)
        .unwrap();
    persist(
        &store,
        &mut manifest,
        &mut engine,
        &mut committed,
        "waitingForEmbedding",
        Admission::Ordinary,
    );
    let waiting = store.verify(&manifest.session_id).unwrap();
    assert_eq!(waiting.received_responses.total, 1);
    assert_eq!(
        waiting.received_responses.entries[0].response_text,
        "x".repeat(16_383)
    );
    assert!(waiting.received_responses.entries[0].response_text_truncated);
    assert_eq!(waiting.report.journal_count, 0);

    let request = engine.start_feedback(attempt).unwrap();
    engine
        .fail_feedback(attempt, request, "Fixture embedding failure")
        .unwrap();
    persist(
        &store,
        &mut manifest,
        &mut engine,
        &mut committed,
        "embeddingBlocked",
        Admission::Ordinary,
    );
    let failed = store.verify(&manifest.session_id).unwrap();
    let SustainedPhase::Feedback(pending) = &failed.checkpoint.state.phase else {
        panic!("completed writing was not retained")
    };
    assert_eq!(pending.response.text, raw);
    assert_eq!(pending.pending.attempt_id, attempt);
    assert_eq!(failed.received_responses.total, 1);
    assert!(failed.received_responses.entries[0].complete);

    let exports = directory.path().join("exports");
    fs::create_dir(&exports).unwrap();
    let report = store.export(&manifest.session_id, &exports, &[]).unwrap();
    let exported = exports.join(format!(
        "{}-{}-{}",
        manifest.session_id, manifest.generation, manifest.revision
    ));
    let exported = verify(&exported).unwrap();
    assert_eq!(exported.report.manifest_sha256, report.manifest_sha256);
    assert_eq!(
        json(&exported.checkpoint).unwrap(),
        json(&failed.checkpoint).unwrap()
    );
    assert_eq!(exported.received_responses.total, 1);

    // Restore and encode again without another generation or turn identity.
    engine = SustainedSession::restore(failed.checkpoint).unwrap();
    engine.retry_feedback().unwrap();
    let request = engine.start_feedback(attempt).unwrap();
    engine
        .fail_feedback(attempt, request, "Second fixture failure")
        .unwrap();
    persist(
        &store,
        &mut manifest,
        &mut engine,
        &mut committed,
        "embeddingBlocked",
        Admission::Ordinary,
    );
    assert_eq!(
        store
            .verify(&manifest.session_id)
            .unwrap()
            .received_responses
            .total,
        1
    );
    engine.retry_feedback().unwrap();
    let request = engine.start_feedback(attempt).unwrap();
    engine
        .confirm_feedback(attempt, request, &feedback())
        .unwrap();
    persist(
        &store,
        &mut manifest,
        &mut engine,
        &mut committed,
        "savingJournal",
        Admission::Ordinary,
    );
    let journal = engine.pending_journal().unwrap().clone();
    let (receipt, readback) = store
        .commit_journal(&manifest.session_id, &journal, &manifest.config, None)
        .unwrap();
    engine.confirm_saved(&receipt, &readback).unwrap();
    manifest.journal_count = 1;
    persist(
        &store,
        &mut manifest,
        &mut engine,
        &mut committed,
        "paused",
        Admission::Ordinary,
    );
    engine.authorize_application(attempt).unwrap();
    let frame = engine.advance().unwrap();
    assert!(frame.application.is_some());
    persist(
        &store,
        &mut manifest,
        &mut engine,
        &mut committed,
        "budgetReached",
        Admission::Ordinary,
    );
    let applied = store.verify(&manifest.session_id).unwrap();
    assert_eq!(applied.received_responses.total, 1);
    assert_eq!(applied.report.journal_count, 1);
    assert_eq!(applied.checkpoint.state.attempt_cursor, 1);
    assert_eq!(
        store
            .read_journal(&manifest.session_id, &journal.entry.id)
            .unwrap()
            .pending
            .response
            .text,
        raw
    );
}

#[test]
fn legacy_received_response_preview_does_not_change_saved_event_bytes() {
    let (_directory, store, mut manifest, mut engine, mut committed) = setup(false);
    let attempt = dispatch(&mut engine);
    let mut reply = response("  An unfinished reply remains evidence. 🌙\n".into());
    reply.complete = false;
    engine.confirm_language(attempt, &reply).unwrap();
    let received = engine.events().back().unwrap().clone();
    assert!(matches!(
        received.kind,
        SustainedEventKind::LanguageReceived { .. }
    ));
    persist(
        &store,
        &mut manifest,
        &mut engine,
        &mut committed,
        "attemptBlocked",
        Admission::Ordinary,
    );
    let verified = store.verify(&manifest.session_id).unwrap();
    let row = &verified.received_responses.entries[0];
    assert_eq!(verified.received_responses.total, 1);
    assert_eq!(row.response_text, reply.text);
    assert!(!row.response_text_truncated);
    assert!(!row.complete);
    assert_eq!(verified.report.journal_count, 0);
    let (link, _) = read_link(
        &store.path(&manifest.session_id).unwrap(),
        manifest.segment_count,
    )
    .unwrap();
    assert_eq!(
        json(link.segment.events.last().unwrap()).unwrap(),
        json(&received).unwrap()
    );
}

#[test]
fn retained_feedback_terminal_reserve_covers_stop_skip_and_close_under_quota() {
    let (_directory, store, mut manifest, mut engine, mut committed) = setup(true);
    let attempt = dispatch(&mut engine);
    engine
        .retain_language_for_feedback(attempt, &response("Retained encoding text. ".repeat(1000)))
        .unwrap();
    engine.start_feedback(attempt).unwrap();
    persist(
        &store,
        &mut manifest,
        &mut engine,
        &mut committed,
        "waitingForEmbedding",
        Admission::Ordinary,
    );
    let before = json(&engine.checkpoint()).unwrap();
    let (reserve, links) = terminal_reserve(&engine, Admission::Ordinary).unwrap();
    assert_eq!(links, 2);
    assert_eq!(json(&engine.checkpoint()).unwrap(), before);
    assert!(engine.events().is_empty());
    let root = store.path(&manifest.session_id).unwrap();
    let padding = fs::File::create(root.join("quota-pressure.bin")).unwrap();
    let used = disk_bytes(&root).unwrap();
    padding
        .set_len(manifest.config.storage_budget_bytes - used - reserve - 8192)
        .unwrap();
    persist(
        &store,
        &mut manifest,
        &mut engine,
        &mut committed,
        "waitingForEmbedding",
        Admission::Ordinary,
    );
    assert!(storage_held(&manifest));
    engine.interrupt("Explicit Stop during encoding").unwrap();
    persist(
        &store,
        &mut manifest,
        &mut engine,
        &mut committed,
        "stopped",
        Admission::Stop,
    );
    assert!(engine.pending_feedback().is_some());
    assert_eq!(terminal_reserve(&engine, Admission::Stop).unwrap().1, 1);
    engine
        .skip_pending("Explicit Skip retained encoding")
        .unwrap();
    persist(
        &store,
        &mut manifest,
        &mut engine,
        &mut committed,
        "stopped",
        Admission::Skip,
    );
    persist(
        &store,
        &mut manifest,
        &mut engine,
        &mut committed,
        "stopped",
        Admission::Close,
    );
    let verified = store.verify(&manifest.session_id).unwrap();
    assert!(matches!(
        verified.checkpoint.state.phase,
        SustainedPhase::Ready
    ));
    assert_eq!(verified.received_responses.total, 1);
    assert!(verified.report.size_bytes <= manifest.config.storage_budget_bytes);
}
