use super::*;
use std::time::{Duration, Instant};

fn setup() -> (tempfile::TempDir, ResearchService) {
    let dir = tempfile::tempdir().unwrap();
    let primary = SustainedState::new(dir.path().join("sustained-v1"));
    let s = ResearchService::new(dir.path().to_owned(), primary).unwrap();
    (dir, s)
}
fn wait(s: &ResearchService, id: &str) -> Operation {
    let until = Instant::now() + Duration::from_secs(30);
    loop {
        let op = s.operation(id).unwrap();
        if !matches!(op.status.as_str(), "queued" | "running" | "scheduled") {
            return op;
        }
        assert!(Instant::now() < until, "operation timed out: {}", id);
        std::thread::sleep(Duration::from_millis(20));
    }
}
fn call(s: &ResearchService, method: &str, path: &str, body: Value) -> Value {
    let op = s.submit(method, path, &id("key"), body).unwrap();
    let op = wait(s, &op.id);
    assert_eq!(op.status, "completed", "{:?}", op.error);
    op.result.unwrap()
}
fn create(s: &ResearchService) -> String {
    call(
        s,
        "POST",
        "/v1/runs",
        json!({"config":{"turnEvery":3,"paceMs":100,"maximumSteps":90,"maximumTurns":30}}),
    )["runId"]
        .as_str()
        .unwrap()
        .into()
}
fn entries(s: &ResearchService, run: &str, n: u64) {
    let until = Instant::now() + Duration::from_secs(20);
    loop {
        let r = s.run(run).unwrap();
        if r["journalCount"].as_u64().unwrap() >= n {
            return;
        }
        assert!(Instant::now() < until, "run stalled: {r}");
        std::thread::sleep(Duration::from_millis(30));
    }
}

#[test]
fn three_runs_cursor_changes_and_verified_export() {
    let (_dir, s) = setup();
    let runs: Vec<_> = (0..3).map(|_| create(&s)).collect();
    for run in &runs {
        call(
            &s,
            "POST",
            &format!("/v1/runs/{run}/actions/start"),
            json!({}),
        );
    }
    for run in &runs {
        entries(&s, run, 2);
    }
    let run = &runs[0];
    let page = s.entries(run, None, 1).unwrap();
    let first = page["entries"][0]["entryId"].clone();
    entries(&s, run, 3);
    let next = s.entries(run, page["nextCursor"].as_str(), 1).unwrap();
    assert_ne!(first, next["entries"][0]["entryId"]);
    assert_eq!(page["snapshot"], next["snapshot"]);
    let changed = call(
        &s,
        "PATCH",
        &format!("/v1/runs/{run}/settings"),
        json!({"expectedConfigurationRevision":0,"patch":{"leak":0.4,"turnEvery":4}}),
    );
    assert_eq!(changed["revision"], 1);
    entries(&s, run, 4);
    let changed = call(
        &s,
        "PATCH",
        &format!("/v1/runs/{run}/settings"),
        json!({"expectedConfigurationRevision":1,"patch":{"promptVersion":"reservoir-journal-inert-plain-contract-v1","memoryPolicy":"random"}}),
    );
    assert_eq!(changed["revision"], 2);
    entries(&s, run, 5);
    for run in &runs {
        call(
            &s,
            "POST",
            &format!("/v1/runs/{run}/actions/pause"),
            json!({}),
        );
    }
    let report = call(&s, "POST", &format!("/v1/runs/{run}/exports"), json!({}));
    assert_eq!(
        report["report"]["journalCount"],
        s.run(run).unwrap()["journalCount"]
    );
    assert!(!s
        .export_files(report["exportId"].as_str().unwrap())
        .unwrap()["files"]
        .as_array()
        .unwrap()
        .is_empty());
    for run in &runs {
        s.0.store.verify(run).unwrap();
    }
    let entry = first.as_str().unwrap();
    let loaded = s.entry(run, entry).unwrap();
    s.0.owners.lock().unwrap().remove(run);
    assert_eq!(
        loaded,
        s.entry(run, entry).unwrap(),
        "Retained and loaded journal contracts must agree"
    );
}
#[test]
fn idempotency_conflicts_and_restart_do_not_dispatch() {
    let (dir, s) = setup();
    let body = json!({"config":{"turnEvery":3,"paceMs":100}});
    let a = s.submit("POST", "/v1/runs", "same", body.clone()).unwrap();
    let b = s.submit("POST", "/v1/runs", "same", body).unwrap();
    assert_eq!(a.id, b.id);
    assert!(s
        .submit(
            "POST",
            "/v1/runs",
            "same",
            json!({"config":{"turnEvery":4}})
        )
        .is_err());
    let result = wait(&s, &a.id);
    assert_eq!(result.status, "completed");
    let run = result.result.unwrap()["runId"].as_str().unwrap().to_owned();
    drop(s);
    let primary = SustainedState::new(dir.path().join("sustained-v1"));
    let restored = ResearchService::new(dir.path().to_owned(), primary).unwrap();
    assert_eq!(restored.run(&run).unwrap()["phase"], "retained");
    assert_eq!(restored.run(&run).unwrap()["step"], 0);
    assert_eq!(restored.operations().unwrap().len(), 1);
}
#[test]
fn recipes_prepare_every_arm_before_dispatch() {
    let (_dir, s) = setup();
    let recipe = json!({"version":1,"baseConfig":{"turnEvery":3,"paceMs":100},"arms":[{"name":"a","overrides":{}},{"name":"b","overrides":{}},{"name":"c","overrides":{}}]});
    let experiment = call(&s, "POST", "/v1/experiments", recipe);
    let runs = experiment["runIds"].as_array().unwrap();
    assert_eq!(runs.len(), 3);
    for run in runs {
        assert_eq!(s.run(run.as_str().unwrap()).unwrap()["step"], 0);
    }
    let group = experiment["id"].as_str().unwrap();
    let result = call(
        &s,
        "POST",
        &format!("/v1/experiments/{group}/actions/start"),
        json!({}),
    );
    assert_eq!(result["partial"], false);
    call(
        &s,
        "POST",
        &format!("/v1/experiments/{group}/actions/pause"),
        json!({}),
    );
}

#[test]
fn planned_resize_and_custom_prompt_are_durable_and_replayable() {
    let (_dir, s) = setup();
    let run = create(&s);
    let resize = s
        .submit(
            "POST",
            &format!("/v1/runs/{run}/interventions"),
            "resize-at-seven",
            json!({"at":{"step":7},"kind":"configuration","patch":{"reservoirNodes":48}}),
        )
        .unwrap();
    // Wait until the target is actually armed before allowing the run to move.
    let until = Instant::now() + Duration::from_secs(5);
    while s.operation(&resize.id).unwrap().status != "scheduled" {
        assert!(Instant::now() < until);
        std::thread::sleep(Duration::from_millis(10));
    }
    call(
        &s,
        "POST",
        &format!("/v1/runs/{run}/actions/start"),
        json!({}),
    );
    let resized = wait(&s, &resize.id);
    assert_eq!(resized.status, "completed", "{:?}", resized.error);
    assert_eq!(resized.result.unwrap()["applied"]["step"], 7);
    let prompt=s.submit("POST",&format!("/v1/runs/{run}/interventions"),"future-prompt",json!({"at":{"step":12},"kind":"prompt","prompt":"What changed after the extra nodes arrived?","includeTelemetry":false})).unwrap();
    let outcome = wait(&s, &prompt.id);
    assert_eq!(outcome.status, "completed", "{:?}", outcome.error);
    entries(&s, &run, 4);
    call(
        &s,
        "POST",
        &format!("/v1/runs/{run}/actions/pause"),
        json!({}),
    );
    let v = s.0.store.verify(&run).unwrap();
    assert_eq!(v.checkpoint.state.reservoir_state.len(), 48);
    assert_eq!(v.checkpoint.state.custom_prompt_count, 1);
    let rows = s.0.store.journal_index_at(&v.manifest).unwrap();
    assert!(rows.iter().any(|row| s
        .0
        .store
        .read_journal_proof(&run, &row.entry_id)
        .unwrap()
        .0
        .pending
        .prompt
        == "What changed after the extra nodes arrived?"));
}

#[test]
fn cancelling_scheduled_work_and_restart_never_dispatches_it() {
    let (dir, s) = setup();
    let run = create(&s);
    let op = s
        .submit(
            "POST",
            &format!("/v1/runs/{run}/interventions"),
            "future",
            json!({"at":{"step":30},"kind":"configuration","patch":{"leak":0.2}}),
        )
        .unwrap();
    let until = Instant::now() + Duration::from_secs(5);
    while s.operation(&op.id).unwrap().status != "scheduled" {
        assert!(Instant::now() < until);
        std::thread::sleep(Duration::from_millis(10));
    }
    call(
        &s,
        "POST",
        &format!("/v1/operations/{}/cancel", op.id),
        json!({}),
    );
    assert_eq!(wait(&s, &op.id).status, "cancelled");
    assert_eq!(s.run(&run).unwrap()["step"], 0);
    let op=s.submit("POST",&format!("/v1/runs/{run}/interventions"),"future-two",json!({"at":{"activeSeconds":10},"kind":"prompt","prompt":"Later","includeTelemetry":false})).unwrap();
    s.0.closing.store(true, Ordering::SeqCst);
    assert_eq!(wait(&s, &op.id).status, "needsAttention");
    drop(s);
    let restored = ResearchService::new(
        dir.path().into(),
        SustainedState::new(dir.path().join("sustained-v1")),
    )
    .unwrap();
    assert_eq!(restored.run(&run).unwrap()["step"], 0);
    assert_eq!(restored.operation(&op.id).unwrap().status, "needsAttention");
}

#[test]
fn effective_limits_survive_changes_cloning_and_retained_reads() {
    let (dir, s) = setup();
    let run = create(&s);
    call(
        &s,
        "POST",
        &format!("/v1/runs/{run}/actions/extend-limits"),
        json!({
            "maximumSteps":120,"maximumTurns":40,"maximumDurationSeconds":43200
        }),
    );
    assert_eq!(s.settings(&run).unwrap()["effective"]["maximumSteps"], 120);
    call(
        &s,
        "PATCH",
        &format!("/v1/runs/{run}/settings"),
        json!({
            "expectedConfigurationRevision":0,"patch":{"leak":0.4}
        }),
    );
    let cloned = call(&s, "POST", &format!("/v1/runs/{run}/clone"), json!({}));
    assert_eq!(cloned["configuration"]["maximumSteps"], 120);
    assert_eq!(cloned["configuration"]["leak"], 0.4);
    assert_eq!(cloned["step"], 0);
    drop(s);
    let restored = ResearchService::new(
        dir.path().into(),
        SustainedState::new(dir.path().join("sustained-v1")),
    )
    .unwrap();
    assert_eq!(
        restored.settings(&run).unwrap()["effective"]["maximumSteps"],
        120
    );
}

#[test]
fn checked_in_recipes_validate_without_model_requests() {
    let (_dir, s) = setup();
    for source in [
        include_str!("../../../../research/recipes/three-model-sonar-v1.json"),
        include_str!("../../../../research/recipes/growth-and-conversation-v1.json"),
    ] {
        let recipe: Value = serde_json::from_str(source).unwrap();
        let saved = call(&s, "POST", "/v1/recipes", recipe);
        assert!(saved["id"].is_string());
    }
    assert!(s.list_runs().unwrap()["runs"]
        .as_array()
        .unwrap()
        .is_empty());
}
