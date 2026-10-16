use super::*;
use serde_json::json;

const RUNTIME: &str = "synthetic-runtime-v1";
const REVISION: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

struct Fixture {
    _temporary: tempfile::TempDir,
    state: SetupState,
}

impl Fixture {
    fn new() -> Self {
        let temporary = tempfile::Builder::new()
            .prefix("activation setup ")
            .tempdir()
            .unwrap();
        let root = temporary.path().join("Application Support/owned setup");
        let resources = temporary.path().join("app resources");
        fs::create_dir_all(&root).unwrap();
        fs::create_dir_all(&resources).unwrap();
        let root = root.canonicalize().unwrap();
        let resources = resources.canonicalize().unwrap();
        publish(
            &resources.join("model-files.json"),
            &json!({"revision": REVISION}),
        )
        .unwrap();
        let model_hash = hash_file(&resources.join("model-files.json")).unwrap();
        publish(&resources.join("setup-manifest.json"), &json!({
            "schema": "activation-setup-manifest-v1", "runtimeId": RUNTIME,
            "python": {"archivePath": "synthetic.tar.gz", "archiveSha256": "not-a-real-archive", "executableRelativePath": "python/bin/python3.12"},
            "locks": {"model": {"path": "model-files.json", "sha256": model_hash}},
            "minimumFreeBytes": 1
        })).unwrap();
        let driver = resources.join("synthetic driver.py");
        let state = SetupState::new(root, resources, driver);
        Self {
            _temporary: temporary,
            state,
        }
    }

    fn install_receipt(&self) -> Value {
        // Synthetic files are never executable and never used for inference.
        let python = self
            .state
            .0
            .root
            .join("runtime")
            .join(RUNTIME)
            .join("venv/bin/python");
        let model = self.state.0.root.join("models").join(REVISION);
        fs::create_dir_all(python.parent().unwrap()).unwrap();
        fs::create_dir_all(&model).unwrap();
        fs::write(
            &python,
            "Synthetic interpreter placeholder; do not execute.\n",
        )
        .unwrap();
        publish(
            &model.join("model-provenance.json"),
            &json!({"synthetic": true}),
        )
        .unwrap();
        let receipt = json!({
            "schema": "activation-setup-ready-v1", "runtimeId": RUNTIME,
            "manifestSha256": hash_file(&self.state.0.resources.join("setup-manifest.json")).unwrap(),
            "pythonPath": python, "modelPath": model
        });
        publish(&self.state.0.root.join("ready.json"), &receipt).unwrap();
        receipt
    }

    #[cfg(unix)]
    fn command(&self, body: &str) -> Command {
        fs::write(&self.state.0.driver, body).unwrap();
        let mut command = Command::new("/usr/bin/python3");
        command
            .arg("-I")
            .arg("-B")
            .arg(&self.state.0.driver)
            .arg(&self.state.0.root);
        command
    }
}

#[cfg(unix)]
fn read_owned_pid(path: &Path) -> libc::pid_t {
    let deadline = Instant::now() + Duration::from_secs(5);
    loop {
        if let Ok(text) = fs::read_to_string(path) {
            if let Ok(pid) = text.trim().parse::<libc::pid_t>() {
                assert!(pid > 1);
                return pid;
            }
        }
        assert!(
            Instant::now() < deadline,
            "Owned synthetic child did not publish {}",
            path.display()
        );
        thread::sleep(Duration::from_millis(20));
    }
}

#[cfg(unix)]
fn assert_leader_reaped(pid: libc::pid_t) {
    let mut exit_status = 0;
    assert_eq!(
        unsafe { libc::waitpid(pid, &mut exit_status, libc::WNOHANG) },
        -1
    );
    assert_eq!(
        std::io::Error::last_os_error().raw_os_error(),
        Some(libc::ECHILD)
    );
}

#[cfg(unix)]
fn assert_descendant_stopped(pid: libc::pid_t) {
    // An orphan can briefly be a zombie pending the OS reaper. It must not keep
    // executing, writing or holding a live setup subprocess after cancellation.
    let deadline = Instant::now() + Duration::from_secs(5);
    loop {
        let output = Command::new("/bin/ps")
            .args(["-o", "stat=", "-p", &pid.to_string()])
            .output()
            .unwrap();
        let status = String::from_utf8_lossy(&output.stdout);
        let status = status.trim();
        if status.is_empty() || status.starts_with('Z') {
            return;
        }
        assert!(
            Instant::now() < deadline,
            "Owned descendant {pid} is still running: {status}"
        );
        thread::sleep(Duration::from_millis(20));
    }
}

#[test]
fn platform_floor_is_macos_26_on_apple_silicon() {
    for version in ["26", "26.0", "26.0.1\0", "27.0.1", "28.1"] {
        assert!(platform_version_supported(true, version), "{version:?}");
        assert!(!platform_version_supported(false, version), "{version:?}");
    }
    for version in ["", "25", "25.9.9", "15.7", "invalid", "macOS 27.0.1"] {
        assert!(!platform_version_supported(true, version), "{version:?}");
    }
}

#[test]
fn exact_readiness_paths_allow_spaces_and_do_not_spawn_a_driver() {
    let fixture = Fixture::new();
    let receipt = fixture.install_receipt();
    let paths = fixture.state.ready_paths().unwrap().unwrap();
    assert_eq!(paths.0, receipt["pythonPath"].as_str().unwrap());
    assert_eq!(paths.1, receipt["modelPath"].as_str().unwrap());
    assert!(paths.0.contains("Application Support/owned setup"));
    assert!(!fixture.state.0.driver.exists());
    assert!(!fixture.state.is_busy());
    assert!(fixture.state.0.join.lock().unwrap().is_none());
    if platform_supported() {
        let status = fixture.state.status();
        assert_eq!(status.state, "ready");
        assert_eq!(
            status.python_path.as_deref(),
            receipt["pythonPath"].as_str()
        );
        assert_eq!(status.model_path.as_deref(), receipt["modelPath"].as_str());
        assert!(!status.can_resume);
    }
}

#[test]
fn readiness_rejects_another_path_even_inside_the_same_owned_root() {
    let fixture = Fixture::new();
    let original = fixture.install_receipt();
    for field in ["pythonPath", "modelPath"] {
        let mut changed = original.clone();
        changed[field] = json!(fixture.state.0.root.join("different but local path"));
        publish(&fixture.state.0.root.join("ready.json"), &changed).unwrap();
        assert!(fixture
            .state
            .ready_paths()
            .unwrap_err()
            .message
            .contains("Readiness paths differ"));
    }
}

#[test]
fn readiness_rejects_a_changed_manifest_or_missing_installation() {
    let fixture = Fixture::new();
    assert!(fixture.state.ready_paths().unwrap().is_none());
    let mut receipt = fixture.install_receipt();
    receipt["manifestSha256"] = json!("a different preview");
    publish(&fixture.state.0.root.join("ready.json"), &receipt).unwrap();
    assert!(fixture
        .state
        .ready_paths()
        .unwrap_err()
        .message
        .contains("different preview"));
    let receipt = fixture.install_receipt();
    fs::remove_file(receipt["pythonPath"].as_str().unwrap()).unwrap();
    assert!(fixture.state.ready_paths().is_err());
}

#[test]
fn damaged_prepared_installation_is_preserved_and_cannot_resume() {
    let fixture = Fixture::new();
    let receipt = fixture.install_receipt();
    let ready_path = fixture.state.0.root.join("ready.json");
    let ready_bytes = fs::read(&ready_path).unwrap();
    let python_path = Path::new(receipt["pythonPath"].as_str().unwrap());
    let python_bytes = fs::read(python_path).unwrap();
    let provenance =
        Path::new(receipt["modelPath"].as_str().unwrap()).join("model-provenance.json");
    fs::remove_file(&provenance).unwrap();
    assert!(fixture.state.ready_paths().is_err());
    if platform_supported() {
        let status = fixture.state.status();
        assert_eq!(status.state, "failed");
        assert!(!status.can_resume);
        assert!(status.message.contains("not an interrupted preparation"));
        assert!(status.message.contains("preserved"));
        for resume in [false, true] {
            assert!(fixture
                .state
                .prepare(resume)
                .unwrap_err()
                .message
                .contains("Resume cannot repair"));
        }
    }
    assert_eq!(fs::read(ready_path).unwrap(), ready_bytes);
    assert_eq!(fs::read(python_path).unwrap(), python_bytes);
    assert!(!provenance.exists());
    assert!(!fixture.state.0.root.join("setup-status.json").exists());
    assert!(!fixture.state.0.driver.exists());
    assert!(!fixture.state.is_busy());
    assert!(fixture.state.0.join.lock().unwrap().is_none());
}

#[test]
fn interrupted_startup_retains_evidence_without_automatically_spawning() {
    let fixture = Fixture::new();
    let mut prior = SetupStatus::new("preparing", "model", "Synthetic interrupted download");
    prior.downloaded_bytes = Some(123);
    prior.total_bytes = Some(456);
    publish(&fixture.state.0.root.join("setup-status.json"), &prior).unwrap();
    let saved = fs::read(fixture.state.0.root.join("setup-status.json")).unwrap();
    let restored = SetupState::new(
        fixture.state.0.root.clone(),
        fixture.state.0.resources.clone(),
        fixture.state.0.driver.clone(),
    );
    let status = restored.0.status.lock().unwrap().clone();
    assert_eq!(status.state, "interrupted");
    assert!(status.can_resume);
    assert_eq!(status.downloaded_bytes, Some(123));
    assert_eq!(status.total_bytes, Some(456));
    assert!(!restored.is_busy());
    assert!(restored.0.join.lock().unwrap().is_none());
    assert!(!fixture.state.0.driver.exists());
    let _ = restored.status();
    assert_eq!(
        fs::read(fixture.state.0.root.join("setup-status.json")).unwrap(),
        saved
    );
    if platform_supported() {
        assert!(restored
            .prepare(false)
            .unwrap_err()
            .message
            .contains("Choose Resume"));
    }
}

#[test]
fn terminal_memory_status_survives_a_receipt_write_failure() {
    let fixture = Fixture::new();
    fixture
        .state
        .update(SetupStatus::new(
            "preparing",
            "verification",
            "Checking files",
        ))
        .unwrap();
    let path = fixture.state.0.root.join("setup-status.json");
    fs::remove_file(&path).unwrap();
    fs::create_dir(&path).unwrap(); // Deterministic persistence failure; no disk is filled.
    let mut failed = SetupStatus::new("failed", "verification", "Unable to finish preparation.");
    failed.can_resume = true;
    assert!(fixture.state.update(failed).is_err());
    let status = fixture.state.0.status.lock().unwrap().clone();
    assert_eq!(status.state, "failed");
    assert!(status.can_resume);
    assert!(status.message.contains("Status could not be saved"));
    assert!(status.message.contains("Unable to finish preparation"));
}

#[test]
fn busy_and_closing_states_refuse_another_preparation() {
    let fixture = Fixture::new();
    fixture.state.0.busy.store(true, Ordering::SeqCst);
    assert!(fixture
        .state
        .prepare(false)
        .unwrap_err()
        .message
        .contains("already active"));
    fixture.state.0.busy.store(false, Ordering::SeqCst);
    fixture.state.0.closing.store(true, Ordering::SeqCst);
    assert!(fixture
        .state
        .prepare(false)
        .unwrap_err()
        .message
        .contains("app is closing"));
    assert!(!fixture.state.0.driver.exists());
    assert!(fixture.state.0.join.lock().unwrap().is_none());
}

#[test]
fn relative_asset_paths_cannot_escape_the_bundle() {
    let root = Path::new("/synthetic path with spaces");
    assert_eq!(
        child_path(root, &json!({"path": "assets/uv"}), "path").unwrap(),
        root.join("assets/uv")
    );
    for path in ["../foreign", "assets/../../foreign", "/foreign"] {
        assert!(child_path(root, &json!({"path": path}), "path").is_err());
    }
}

#[test]
fn interrupted_bootstrap_ownership_resumes_before_and_after_runtime_creation() {
    for directory_was_created in [false, true] {
        let fixture = Fixture::new();
        let root = &fixture.state.0.root;
        let runtime = root.join("runtime").join(RUNTIME);
        let owners = root.join("bootstrap-owners");
        fs::create_dir_all(&owners).unwrap();
        let identity =
            json!({"schema": "activation-bootstrap-owner-v1", "manifestSha256": "synthetic"});
        publish(&owners.join(format!("{RUNTIME}.json")), &identity).unwrap();
        // Simulate either interruption immediately after the sibling marker or
        // after mkdir, before the inner ownership marker was published.
        if directory_was_created {
            fs::create_dir_all(&runtime).unwrap();
            fs::write(runtime.join("partial-extraction"), b"retained bytes").unwrap();
        }
        assert_eq!(
            bootstrap_runtime_directory(root, RUNTIME, &identity).unwrap(),
            runtime
        );
        assert_eq!(
            json_file(&runtime.join("bootstrap-owner.json")).unwrap(),
            identity
        );
        if directory_was_created {
            assert_eq!(
                fs::read(runtime.join("partial-extraction")).unwrap(),
                b"retained bytes"
            );
        }
    }
}

#[test]
fn bootstrap_ownership_never_adopts_an_unowned_directory() {
    for contains_files in [false, true] {
        let fixture = Fixture::new();
        let root = &fixture.state.0.root;
        let runtime = root.join("runtime").join(RUNTIME);
        fs::create_dir_all(&runtime).unwrap();
        if contains_files {
            fs::write(runtime.join("foreign-file"), b"untouched").unwrap();
        }
        let identity =
            json!({"schema": "activation-bootstrap-owner-v1", "manifestSha256": "synthetic"});
        assert!(bootstrap_runtime_directory(root, RUNTIME, &identity)
            .unwrap_err()
            .message
            .contains("unowned files"));
        assert!(!root
            .join("bootstrap-owners")
            .join(format!("{RUNTIME}.json"))
            .exists());
        assert!(!runtime.join("bootstrap-owner.json").exists());
        if contains_files {
            assert_eq!(
                fs::read(runtime.join("foreign-file")).unwrap(),
                b"untouched"
            );
        }
    }
}

#[test]
fn bootstrap_ownership_preserves_an_existing_qualified_environment() {
    let fixture = Fixture::new();
    let root = &fixture.state.0.root;
    let runtime = root.join("runtime").join(RUNTIME);
    fs::create_dir_all(runtime.join("venv/bin")).unwrap();
    let identity =
        json!({"schema": "activation-bootstrap-owner-v1", "manifestSha256": "synthetic"});
    publish(&runtime.join("bootstrap-owner.json"), &identity).unwrap();
    publish(&runtime.join("bootstrap-complete.json"), &identity).unwrap();
    fs::write(runtime.join("venv/bin/python"), b"qualified placeholder").unwrap();
    bootstrap_runtime_directory(root, RUNTIME, &identity).unwrap();
    assert_eq!(
        json_file(
            &root
                .join("bootstrap-owners")
                .join(format!("{RUNTIME}.json"))
        )
        .unwrap(),
        identity
    );
    assert_eq!(
        json_file(&runtime.join("bootstrap-complete.json")).unwrap(),
        identity
    );
    assert_eq!(
        fs::read(runtime.join("venv/bin/python")).unwrap(),
        b"qualified placeholder"
    );
    assert!(bootstrap_runtime_directory(root, RUNTIME, &json!({"other": "manifest"})).is_err());
    for invalid in ["", ".", "..", "../foreign", "foreign/path"] {
        assert!(bootstrap_runtime_directory(root, invalid, &identity).is_err());
    }
}

#[cfg(unix)]
#[test]
fn insufficient_storage_is_rejected_before_extracting_any_runtime() {
    let fixture = Fixture::new();
    assert!(require_disk(&fixture.state.0.root, 1).is_ok());
    let failure = require_disk(&fixture.state.0.root, u64::MAX).unwrap_err();
    assert!(failure.message.contains("free storage"));
    let mut manifest = fixture.state.manifest().unwrap();
    manifest["minimumFreeBytes"] = json!(u64::MAX);
    publish(
        &fixture.state.0.resources.join("setup-manifest.json"),
        &manifest,
    )
    .unwrap();
    if platform_supported() {
        let failure = fixture.state.prepare(false).unwrap_err();
        assert!(failure.message.contains("free storage"));
        assert!(!fixture.state.is_busy());
        assert!(fixture.state.0.join.lock().unwrap().is_none());
    }
    assert!(!fixture.state.0.root.join("runtime").exists());
    assert!(!fixture.state.0.driver.exists());
}

#[cfg(unix)]
#[test]
fn readiness_rejects_an_interpreter_symlink_outside_its_owned_root() {
    let fixture = Fixture::new();
    let receipt = fixture.install_receipt();
    let python = Path::new(receipt["pythonPath"].as_str().unwrap());
    fs::remove_file(python).unwrap();
    std::os::unix::fs::symlink("/usr/bin/python3", python).unwrap();
    assert!(fixture
        .state
        .ready_paths()
        .unwrap_err()
        .message
        .contains("leaves this app's setup directory"));
}

#[cfg(unix)]
#[test]
fn cancellation_kills_the_owned_group_and_reaps_its_leader() {
    let fixture = Fixture::new();
    let command = fixture.command(
        r#"import os, pathlib, subprocess, sys, time
root = pathlib.Path(sys.argv[1])
child = subprocess.Popen([sys.executable, '-I', '-B', '-c', 'import time; time.sleep(15)'])
(root / 'child.pid').write_text(str(child.pid))
(root / 'leader.pid').write_text(str(os.getpid()))
time.sleep(15)
"#,
    );
    let state = fixture.state.clone();
    let (sender, receiver) = mpsc::channel();
    let handle = thread::spawn(move || {
        sender
            .send(state.process(command, Instant::now() + Duration::from_secs(10), true))
            .unwrap();
    });
    let leader = read_owned_pid(&fixture.state.0.root.join("leader.pid"));
    let child = read_owned_pid(&fixture.state.0.root.join("child.pid"));
    fixture.state.0.cancel.store(true, Ordering::SeqCst);
    let failure = receiver
        .recv_timeout(Duration::from_secs(5))
        .expect("Cancellation must settle the owned process")
        .unwrap_err();
    handle.join().unwrap();
    assert!(failure.message.contains("Preparation cancelled"));
    assert_leader_reaped(leader);
    assert_descendant_stopped(child);
}

#[cfg(unix)]
#[test]
fn driver_exit_cannot_leave_a_live_installer_holding_stdout() {
    for exit_code in [0, 7] {
        let fixture = Fixture::new();
        let command = fixture.command(&format!(
            r#"import os, pathlib, subprocess, sys
root = pathlib.Path(sys.argv[1])
child = subprocess.Popen([sys.executable, '-I', '-B', '-c', 'import time; time.sleep(15)'])
(root / 'child.pid').write_text(str(child.pid))
(root / 'leader.pid').write_text(str(os.getpid()))
os._exit({exit_code})
"#
        ));
        let state = fixture.state.clone();
        let (sender, receiver) = mpsc::channel();
        let handle = thread::spawn(move || {
            sender
                .send(state.process(command, Instant::now() + Duration::from_secs(10), true))
                .unwrap();
        });
        let leader = read_owned_pid(&fixture.state.0.root.join("leader.pid"));
        let child = read_owned_pid(&fixture.state.0.root.join("child.pid"));
        let result = receiver
            .recv_timeout(Duration::from_secs(5))
            .expect("Driver exit must settle without waiting for its still-live child");
        handle.join().unwrap();
        assert_eq!(result.is_ok(), exit_code == 0);
        assert_leader_reaped(leader);
        assert_descendant_stopped(child);
    }
}

#[cfg(unix)]
#[test]
fn final_diagnostic_survives_a_process_exit_and_full_output_queue() {
    let fixture = Fixture::new();
    let command = fixture.command(r#"import json, sys
for _ in range(64): print('synthetic startup output', flush=True)
print(json.dumps({'schema': 'activation-setup-progress-v1', 'phase': 'failed', 'status': 'failed', 'diagnostic': 'Synthetic asset hash mismatch; retained partial download needs review.'}), flush=True)
sys.exit(9)
"#);
    let failure = fixture
        .state
        .process(command, Instant::now() + Duration::from_secs(5), true)
        .unwrap_err();
    assert!(failure.message.contains("Synthetic asset hash mismatch"));
    assert!(fixture
        .state
        .0
        .status
        .lock()
        .unwrap()
        .message
        .contains("retained partial download needs review"));
}

#[cfg(unix)]
#[test]
fn process_deadline_stops_an_owned_child_without_a_retry() {
    let fixture = Fixture::new();
    let command = fixture.command(
        r#"import os, pathlib, sys, time
root = pathlib.Path(sys.argv[1])
(root / 'leader.pid').write_text(str(os.getpid()))
(root / 'attempts').write_text('one attempt')
time.sleep(15)
"#,
    );
    let state = fixture.state.clone();
    let (sender, receiver) = mpsc::channel();
    let handle = thread::spawn(move || {
        sender
            .send(state.process(command, Instant::now() + Duration::from_millis(750), false))
            .unwrap();
    });
    let failure = receiver
        .recv_timeout(Duration::from_secs(5))
        .expect("The configured process deadline must be enforced")
        .unwrap_err();
    handle.join().unwrap();
    assert!(failure.message.contains("deadline"));
    assert_eq!(
        fs::read_to_string(fixture.state.0.root.join("attempts")).unwrap(),
        "one attempt"
    );
    assert_leader_reaped(read_owned_pid(&fixture.state.0.root.join("leader.pid")));
}

#[test]
fn progress_names_the_current_file_and_keeps_byte_counts_optional() {
    let fixture = Fixture::new();
    fixture.state.progress(&json!({"schema":"activation-setup-progress-v1", "phase":"model", "file":"weights.safetensors", "downloadedBytes":123, "totalBytes":456}).to_string()).unwrap();
    let status = fixture.state.0.status.lock().unwrap().clone();
    assert!(status.message.contains("Current file: weights.safetensors"));
    assert_eq!(status.downloaded_bytes, Some(123));
    assert_eq!(status.total_bytes, Some(456));
    fixture
        .state
        .progress(
            &json!({"schema":"activation-setup-progress-v1", "phase":"verification"}).to_string(),
        )
        .unwrap();
    let status = fixture.state.0.status.lock().unwrap().clone();
    assert_eq!(status.downloaded_bytes, None);
    assert_eq!(status.total_bytes, None);
}
