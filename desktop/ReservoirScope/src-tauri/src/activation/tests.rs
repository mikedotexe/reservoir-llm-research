use super::*;
fn setup(slow: bool) -> (tempfile::TempDir, ActivationState, Config) {
    let root = tempfile::tempdir().unwrap();
    let worker = root.path().join("worker.py");
    let source = format!(
        r#"import json,sys,time,os
for line in sys.stdin:
 r=json.loads(line); c=r['command']
 with open(sys.argv[0]+'.calls','a') as f: f.write(json.dumps(dict(r,pid=os.getpid()))+'\n')
 if c=='inspect': x={{'loaded':False}}
 elif c=='initialize': x={{'manifest':{{'sha256':'fake-model'}},'calibration':{{'sha256':'fixed','modelManifestSha256':'fake-model','mean':[0]*32,'scales':[1]*32}}}}
 else:
  if {slow} and c=='quiet_capture': time.sleep(30)
  receipt={{'sampledTokenCount':0,'freshCache':True,'cacheDiscarded':True,'modelManifestSha256':'fake-model','calibrationSha256':'fixed','chatTemplateApplied':False}}
  x={{'projection':[0.2]*32,'promptTokenIds':[1,2],'generatedTokenIds':[],'sampledTokenIds':[],'receipt':receipt,'complete':True,'stopReason':'stop','text':'Synthetic fixture; no model generated this writing. An open question remains.'}}
  if c=='generate_journal':
   x['generatedTokenIds']=[3]; x['sampledTokenIds']=[3,4]
   receipt.update(steeringHeld=True,steeringState=r['steeringState'],requestedGain=r['gain'],arm=r['arm'],seed=r['seed'],temperature=r['temperature'],maxTokens=r['maxTokens'],feedbackEligible=True,capturedTokenId=3)
 print(json.dumps({{'id':r['id'],'type':'result','command':c,'result':x,'protocolVersion':'reservoir-activation/1','workerIdentity':{{'modelManifestSha256':'fake-model','runtime':'synthetic'}}}}),flush=True)
"#,
        slow = if slow { "True" } else { "False" }
    );
    fs::write(&worker, source).unwrap();
    let config = Config {
        python_path: "/usr/bin/python3".into(),
        worker_path: worker.to_string_lossy().into(),
        model_path: root.path().join("model").to_string_lossy().into(),
        arm: Arm::Recurrent,
        seed: 42,
        observations: vec!["rain".into(), "quiet".into()],
        steps_between: 10,
        journal_every: 2,
        max_journal_tokens: 1024,
        gain: 0.01,
    };
    let state = ActivationState::new(root.path().join("sessions"), worker);
    (root, state, config)
}
fn finish(state: &ActivationState) {
    let deadline = Instant::now() + Duration::from_secs(10);
    while state.is_busy() {
        assert!(Instant::now() < deadline);
        thread::sleep(Duration::from_millis(5));
    }
}

#[test]
fn incomplete_response_over_64k_is_readable_without_becoming_a_journal_or_feedback() {
    let (_root, state, config) = setup(false);
    let source = fs::read_to_string(&config.worker_path).unwrap();
    let source = source.replace("if c=='generate_journal':", "if c=='generate_journal':\n   x['complete']=False; x['stopReason']='max_tokens'; x['text']='Retained unfinished response. ' * 3000");
    fs::write(&config.worker_path, source).unwrap();
    let prepared = state.create(config.clone()).unwrap();
    state.start(&prepared.session_id).unwrap();
    finish(&state);
    let snapshot = state.get(Some(&prepared.session_id)).unwrap().unwrap();
    assert_eq!(snapshot.journal_count, 0);
    assert_eq!(snapshot.incomplete_attempts.len(), 1);
    assert!(snapshot.incomplete_attempts[0].text.len() > 65536);
    assert_eq!(
        snapshot.incomplete_attempts[0].text,
        "Retained unfinished response. ".repeat(3000)
    );
    assert!(!snapshot.incomplete_attempts[0].feedback_eligible);
    assert_eq!(snapshot.incomplete_attempts[0].stop_reason, "max_tokens");
    assert!(!snapshot.can_start);
    let verified = verify(Path::new(&snapshot.directory)).unwrap();
    assert_eq!(verified["journals"], 0);
}

fn cohort_configs(config: &Config) -> Vec<Config> {
    [Arm::NoSteering, Arm::Recurrent, Arm::DecayingTrace]
        .into_iter()
        .map(|arm| {
            let mut config = config.clone();
            config.arm = arm;
            config
        })
        .collect()
}
fn fake_calibration(root: &Path) -> PathBuf {
    let path = root.join("frozen-calibration.json");
    fs::write(&path, encode(&json!({"sha256":"fixed","modelManifestSha256":"fake-model","mean":vec![0;32],"scales":vec![1;32]})).unwrap()).unwrap();
    path
}
fn calls(config: &Config) -> Vec<Value> {
    fs::read_to_string(format!("{}.calls", config.worker_path))
        .unwrap()
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect()
}
fn assert_reaped(result: &Value) {
    let pid = result["workerPid"].as_u64().unwrap() as libc::pid_t;
    let mut status = 0;
    assert_eq!(
        unsafe { libc::waitpid(pid, &mut status, libc::WNOHANG) },
        -1
    );
    assert_eq!(
        std::io::Error::last_os_error().raw_os_error(),
        Some(libc::ECHILD)
    );
    assert_eq!(result["workerReleased"], true);
}
#[test]
fn cohort_shares_one_initialization_preserves_single_arm_parity_and_portable_proof() {
    let (root, state, config) = setup(false);
    let configs = cohort_configs(&config);
    let cohort_root = root.path().join("cohort");
    let result = run_cohort(
        configs.clone(),
        &cohort_root,
        &fake_calibration(root.path()),
        &AtomicBool::new(false),
    )
    .unwrap();
    assert_eq!(result["status"], "completed", "{result}");
    assert_eq!(result["modelsLoaded"], 1);
    assert_eq!(result["workerStarts"], 1);
    assert_reaped(&result);
    let wire_calls = calls(&config);
    assert_eq!(wire_calls.len(), 10);
    assert_eq!(
        wire_calls
            .iter()
            .filter(|c| c["command"] == "initialize")
            .count(),
        1
    );
    assert!(wire_calls.iter().all(|c| c["pid"] == wire_calls[0]["pid"]));
    let cohort_state = ActivationState::new(cohort_root, PathBuf::from(&config.worker_path));
    for (index, expected_config) in configs.into_iter().enumerate() {
        let retained = &result["sessions"][index];
        let p = Path::new(retained["directory"].as_str().unwrap());
        verify(p).unwrap();
        let (manifest, cohort_record) = load(p).unwrap();
        assert_eq!(cohort_record.state.step, 21);
        assert!(!retained["canStart"].as_bool().unwrap());
        assert_eq!(
            manifest.cohort.as_ref().unwrap().first_operation_sequence,
            Some(2 + 3 * index as u64)
        );
        assert!(!fs::read_dir(p).unwrap().any(|e| e
            .unwrap()
            .file_name()
            .to_string_lossy()
            .starts_with("initialize-")));
        let isolated = state.create(expected_config).unwrap();
        state.start(&isolated.session_id).unwrap();
        finish(&state);
        let (_, isolated_record) = load(Path::new(&isolated.directory)).unwrap();
        assert_eq!(
            encode(&cohort_record).unwrap(),
            encode(&isolated_record).unwrap(),
            "State, prior-journal prompt, and applied feedback differ for arm {index}"
        );
        let export = root.path().join(format!("arm-{index}.json"));
        cohort_state.export(&manifest.session_id, &export).unwrap();
        let imported = state.import(&export).unwrap();
        verify(Path::new(&imported.directory)).unwrap();
        assert!(!imported.can_start);
        assert!(state.start(&imported.session_id).is_err());
    }
}
#[test]
fn cohort_configuration_identity_is_checked_before_creating_evidence_or_worker() {
    let (root, _, config) = setup(false);
    let calibration = fake_calibration(root.path());
    for change in 0..9 {
        let mut configs = cohort_configs(&config);
        match change {
            0 => configs.pop().map(|_| ()).unwrap(),
            1 => configs[1].arm = configs[0].arm,
            2 => configs[1].seed += 1,
            3 => configs[1].model_path.push('x'),
            4 => configs[1].python_path.push('x'),
            5 => configs[1].worker_path.push('x'),
            6 => configs[1].observations[0].push('x'),
            7 => configs[1].steps_between += 1,
            _ => configs[1].max_journal_tokens -= 1,
        }
        let output = root.path().join(format!("invalid-{change}"));
        assert!(run_cohort(configs, &output, &calibration, &AtomicBool::new(false)).is_err());
        assert!(!output.exists());
    }
    assert!(!Path::new(&format!("{}.calls", config.worker_path)).exists());
}
#[test]
fn cohort_first_failed_arm_retains_completed_prefix_and_never_starts_third_arm() {
    let (root, _, config) = setup(false);
    let source = fs::read_to_string(&config.worker_path).unwrap().replace(
        " if c=='inspect':",
        " if c=='generate_journal' and r['arm']=='recurrent':\n  print(json.dumps({'id':r['id'],'type':'error','command':c,'error':{'message':'synthetic second arm failure'},'protocolVersion':'reservoir-activation/1','workerIdentity':{'modelManifestSha256':'fake-model','runtime':'synthetic'}}),flush=True)\n  continue\n if c=='inspect':",
    );
    fs::write(&config.worker_path, source).unwrap();
    let result = run_cohort(
        cohort_configs(&config),
        &root.path().join("cohort"),
        &fake_calibration(root.path()),
        &AtomicBool::new(false),
    )
    .unwrap();
    assert_eq!(result["status"], "failed");
    assert_eq!(result["sessions"][0]["status"], "completed");
    assert_eq!(result["sessions"][1]["status"], "failed");
    assert_eq!(result["sessions"][2]["status"], "paused");
    assert_eq!(result["sessions"][2]["step"], 0);
    assert!(result["sessions"][2]["events"]
        .as_array()
        .unwrap()
        .is_empty());
    assert_eq!(calls(&config).len(), 7);
    assert_reaped(&result);
    for session in result["sessions"].as_array().unwrap() {
        verify(Path::new(session["directory"].as_str().unwrap())).unwrap();
        assert_eq!(session["canStart"], false);
    }
}
#[test]
fn cohort_deadline_and_cancellation_end_owned_worker_without_resend() {
    for cancellation in [false, true] {
        let (root, _, config) = setup(true);
        let cancel = Arc::new(AtomicBool::new(false));
        let flag = cancel.clone();
        let log_path = format!("{}.calls", config.worker_path);
        let cancellation_thread = cancellation.then(|| {
            thread::spawn(move || {
                let deadline = Instant::now() + Duration::from_secs(10);
                while Instant::now() < deadline {
                    if fs::read_to_string(&log_path).is_ok_and(|s| s.contains("quiet_capture")) {
                        flag.store(true, Ordering::SeqCst);
                        return;
                    }
                    thread::sleep(Duration::from_millis(10));
                }
                panic!("Synthetic worker never reached its cancellable operation");
            })
        });
        let result = run_cohort_bounded(
            cohort_configs(&config),
            &root.path().join("cohort"),
            &fake_calibration(root.path()),
            &cancel,
            if cancellation {
                Duration::from_secs(10)
            } else {
                Duration::from_millis(300)
            },
            resident_pressure,
        )
        .unwrap();
        if let Some(thread) = cancellation_thread {
            thread.join().unwrap();
        }
        assert_eq!(result["status"], "failed");
        if !cancellation {
            assert!(
                result["diagnostic"].as_str().unwrap().contains("lifetime")
                    || result["diagnostic"].as_str().unwrap().contains("deadline")
            );
        }
        assert_eq!(result["sessions"][0]["journalCount"], 0);
        assert_eq!(result["sessions"][1]["step"], 0);
        if result["workerStarts"] == 1 {
            assert_reaped(&result);
        }
        if cancellation {
            // Cancel only after the owned fake worker actually starts quiet
            // capture. Fixture creation and durable closeout are not request
            // latency; the direct Worker tests bound cancellation/reap time.
            assert_eq!(calls(&config).len(), 2);
            assert_reaped(&result);
        }
        for session in result["sessions"].as_array().unwrap() {
            verify(Path::new(session["directory"].as_str().unwrap())).unwrap();
        }
    }
}
#[test]
fn cohort_rejects_shared_initialization_and_wire_boundary_tampering() {
    let (root, _, config) = setup(false);
    let result = run_cohort(
        cohort_configs(&config),
        &root.path().join("cohort"),
        &fake_calibration(root.path()),
        &AtomicBool::new(false),
    )
    .unwrap();
    let first = Path::new(result["sessions"][0]["directory"].as_str().unwrap());
    let wire = first.join("cohort-protocol-2-request.json");
    let original = fs::read(&wire).unwrap();
    let mut value: Value = serde_json::from_slice(&original).unwrap();
    value["text"] = json!("unrecorded observation");
    fs::write(&wire, encode(&value).unwrap()).unwrap();
    assert!(verify(first).is_err());
    fs::write(wire, original).unwrap();
    let init = first.join("shared-initialize-response.json");
    let mut value: Value = decode(&init).unwrap();
    value["result"]["manifest"]["sha256"] = json!("different runtime");
    fs::write(init, encode(&value).unwrap()).unwrap();
    assert!(verify(first).is_err());
    let second = Path::new(result["sessions"][1]["directory"].as_str().unwrap());
    let boundary_path = second.join("cohort-operation-boundary.json");
    let mut boundary: OperationBoundary = decode(&boundary_path).unwrap();
    boundary.first_sequence = 2;
    fs::write(boundary_path, encode(&boundary).unwrap()).unwrap();
    assert!(verify(second).is_err());
}
#[test]
fn cohort_unknown_or_critical_resident_pressure_stops_before_model_dispatch() {
    fn refused() -> Result<Value> {
        Err(err(
            "resident-resource",
            "synthetic pressure=4 or unavailable",
        ))
    }
    let (root, _, config) = setup(false);
    let result = run_cohort_bounded(
        cohort_configs(&config),
        &root.path().join("cohort"),
        &fake_calibration(root.path()),
        &AtomicBool::new(false),
        Duration::from_secs(10),
        refused,
    )
    .unwrap();
    assert_eq!(result["status"], "failed");
    assert_eq!(result["workerStarts"], 0);
    assert_eq!(result["modelsLoaded"], 0);
    assert_eq!(result["sessions"][1]["status"], "paused");
    assert!(!Path::new(&format!("{}.calls", config.worker_path)).exists());
    assert_eq!(
        fs::read_dir(root.path().join("cohort"))
            .unwrap()
            .filter(|entry| entry
                .as_ref()
                .unwrap()
                .file_name()
                .to_string_lossy()
                .starts_with("resident-guard-"))
            .count(),
        1
    );
}
#[test]
fn cohort_warning_only_continues_a_resident_worker_and_critical_stops_at_next_arm() {
    static GUARDS: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);
    fn scripted() -> Result<Value> {
        let index = GUARDS.fetch_add(1, Ordering::SeqCst);
        match index {
            0 => Ok(json!({"allowed":true,"pressure":1,"synthetic":true})),
            1..=4 => Ok(json!({"allowed":true,"pressure":2,"synthetic":true})),
            _ => Err(err(
                "resident-resource",
                "synthetic critical pressure 4 at second arm",
            )),
        }
    }
    GUARDS.store(0, Ordering::SeqCst);
    let (root, _, config) = setup(false);
    let result = run_cohort_bounded(
        cohort_configs(&config),
        &root.path().join("cohort"),
        &fake_calibration(root.path()),
        &AtomicBool::new(false),
        Duration::from_secs(10),
        scripted,
    )
    .unwrap();
    assert_eq!(result["status"], "failed");
    assert_eq!(result["sessions"][0]["status"], "completed");
    assert_eq!(result["sessions"][1]["status"], "failed");
    assert_eq!(result["sessions"][1]["step"], 0);
    assert_eq!(calls(&config).len(), 4);
    assert_reaped(&result);
    fn warning() -> Result<Value> {
        Ok(json!({"allowed":true,"pressure":2,"synthetic":true}))
    }
    let refused = run_cohort_bounded(
        cohort_configs(&config),
        &root.path().join("warning-before-load"),
        &root.path().join("frozen-calibration.json"),
        &AtomicBool::new(false),
        Duration::from_secs(10),
        warning,
    )
    .unwrap();
    assert_eq!(refused["workerStarts"], 0);
    assert_eq!(refused["modelsLoaded"], 0);
}
#[test]
fn cohort_changed_runtime_envelope_is_retained_but_never_applied() {
    let (root, _, config) = setup(false);
    let source = fs::read_to_string(&config.worker_path).unwrap().replace(
        "'runtime':'synthetic'",
        "'runtime':('synthetic' if c=='initialize' else 'changed')",
    );
    fs::write(&config.worker_path, source).unwrap();
    let result = run_cohort(
        cohort_configs(&config),
        &root.path().join("cohort"),
        &fake_calibration(root.path()),
        &AtomicBool::new(false),
    )
    .unwrap();
    assert_eq!(result["status"], "failed");
    assert!(result["diagnostic"]
        .as_str()
        .unwrap()
        .contains("runtime identity"));
    assert_eq!(result["sessions"][0]["observationIndex"], 0);
    assert_eq!(calls(&config).len(), 2);
    let p = Path::new(result["sessions"][0]["directory"].as_str().unwrap());
    assert!(p.join("cohort-protocol-2-response.json").exists());
    verify(p).unwrap();
    assert_reaped(&result);
}
#[test]
fn received_response_cannot_cross_the_request_deadline() {
    let (root, _, config) = setup(false);
    fs::write(&config.worker_path, r#"import json,sys,time
for line in sys.stdin:
 r=json.loads(line)
 if r['command']=='late': time.sleep(0.030)
 print(json.dumps({'id':r['id'],'command':r['command'],'type':'result','result':{'complete':True}}),flush=True)
"#).unwrap();
    let mut worker = Worker::spawn(&config).unwrap();
    worker.protocol_prefix = Some(root.path().join("late-protocol"));
    let cancel = AtomicBool::new(false);
    worker
        .call("warm", json!({}), &cancel, Duration::from_secs(2))
        .unwrap();
    let error = worker
        .call("late", json!({}), &cancel, Duration::from_millis(25))
        .unwrap_err();
    assert_eq!(error.category, "timeout");
    // Whether the response reached the reader or timed out in the pipe, it
    // cannot become an accepted result, and the owned child must be reaped.
    let pid = worker.child.id() as libc::pid_t;
    let mut status = 0;
    assert_eq!(
        unsafe { libc::waitpid(pid, &mut status, libc::WNOHANG) },
        -1
    );
    assert_eq!(
        std::io::Error::last_os_error().raw_os_error(),
        Some(libc::ECHILD)
    );
}
#[test]
fn completed_arm_remains_verifiable_at_a_cancelled_or_expired_terminal_boundary() {
    let (root, _, config) = setup(false);
    let cohort_root = root.path().join("cohort");
    let result = run_cohort(
        cohort_configs(&config),
        &cohort_root,
        &fake_calibration(root.path()),
        &AtomicBool::new(false),
    )
    .unwrap();
    let path = Path::new(result["sessions"][0]["directory"].as_str().unwrap());
    let (mut manifest, mut record) = load(path).unwrap();
    let recorded_events = record.events.len();
    let recorded_hash = manifest.record_sha256.clone();
    let mut worker = Worker::spawn(&config).unwrap();
    for cancelled in [false, true] {
        manifest.status = "running".into();
        let runtime = CohortRuntime {
            deadline: Instant::now() - Duration::from_secs(1),
            root: &cohort_root,
            resident_pressure,
        };
        ActivationState::execute_operations(
            path,
            &mut manifest,
            &mut record,
            &mut worker,
            &AtomicBool::new(cancelled),
            Some(&runtime),
        )
        .unwrap();
        assert_eq!(manifest.status, "completed");
        assert_eq!(record.events.len(), recorded_events);
        assert_eq!(manifest.record_sha256, recorded_hash);
        verify(path).unwrap();
    }
    retain_failure(
        path,
        &mut manifest,
        &mut record,
        "Synthetic cohort stop after this completed arm",
    )
    .unwrap();
    assert_eq!(manifest.status, "completed");
    assert_eq!(record.events.len(), recorded_events);
    verify(path).unwrap();
    assert_eq!(worker.sequence, 0);
}
#[test]
fn optional_synthetic_reader_export() {
    let Some(path) = std::env::var_os("ACTIVATION_TEST_EXPORT_PATH") else {
        return;
    };
    let (_root, state, mut config) = setup(false);
    config.observations = (1..=12)
        .map(|n| format!("Synthetic observation {n}"))
        .collect();
    let s = state.create(config).unwrap();
    state.start(&s.session_id).unwrap();
    finish(&state);
    let s = state.get(Some(&s.session_id)).unwrap().unwrap();
    assert_eq!(s.status, "completed", "{:?}", s.diagnostic);
    assert_eq!(s.journal_count, 6);
    assert_eq!(s.step, 121);
    state.export(&s.session_id, Path::new(&path)).unwrap();
}
#[test]
fn fake_worker_full_save_apply_export_import_and_offline_replay() {
    let (root, state, config) = setup(false);
    let inspected = state.inspect(config.clone()).unwrap();
    assert_eq!(inspected["capability"]["loaded"], false);
    let s = state.create(config).unwrap();
    assert!(s.can_start);
    assert_eq!(s.step, 0);
    state.start(&s.session_id).unwrap();
    finish(&state);
    let s = state.get(Some(&s.session_id)).unwrap().unwrap();
    assert_eq!(s.status, "completed", "{:?}", s.diagnostic);
    assert_eq!(s.step, 21);
    assert_eq!(s.journal_count, 1);
    assert_eq!(s.journals[0].first_applied_step, Some(21));
    verify(Path::new(&s.directory)).unwrap();
    let output = root.path().join("export.json");
    state.export(&s.session_id, &output).unwrap();
    let original = fs::read(&output).unwrap();
    let imported = state.import(&output).unwrap();
    assert_ne!(s.session_id, imported.session_id);
    assert!(!imported.can_start);
    assert_eq!(original, fs::read(&output).unwrap());
    verify(Path::new(&imported.directory)).unwrap();
}
#[test]
fn cancellation_kills_owned_worker_without_late_application_or_resend() {
    let (_root, state, config) = setup(true);
    let s = state.create(config).unwrap();
    state.start(&s.session_id).unwrap();
    let deadline = Instant::now() + Duration::from_secs(10);
    loop {
        let x = state.get(Some(&s.session_id)).unwrap().unwrap();
        if x.active_operation.as_deref() == Some("quiet_capture") {
            break;
        }
        assert!(Instant::now() < deadline);
        thread::sleep(Duration::from_millis(10));
    }
    let start = Instant::now();
    let s = state.stop(&s.session_id).unwrap();
    assert!(start.elapsed() < Duration::from_secs(2));
    assert_eq!(s.status, "failed");
    assert_eq!(s.journal_count, 0);
    assert!(!s.can_start);
    assert!(state.start(&s.session_id).is_err());
    verify(Path::new(&s.directory)).unwrap();
}
#[test]
fn changed_saved_text_or_projection_evidence_is_rejected() {
    let (_root, state, config) = setup(false);
    let s = state.create(config).unwrap();
    state.start(&s.session_id).unwrap();
    finish(&state);
    let s = state.get(Some(&s.session_id)).unwrap().unwrap();
    fs::write(
        Path::new(&s.directory).join(format!("{}.txt", s.journals[0].id)),
        "changed",
    )
    .unwrap();
    assert!(verify(Path::new(&s.directory)).is_err());
    assert!(state.restore(&s.session_id).is_err());
}
#[test]
fn calibration_mutation_cannot_resume_or_pass_replay() {
    let (_root, state, config) = setup(false);
    let s = state.create(config).unwrap();
    state.start(&s.session_id).unwrap();
    finish(&state);
    let s = state.get(Some(&s.session_id)).unwrap().unwrap();
    let p = Path::new(&s.directory).join("calibration.json");
    let mut cal: Value = decode(&p).unwrap();
    cal["mean"][0] = json!(7.0);
    fs::write(p, encode(&cal).unwrap()).unwrap();
    assert!(verify(Path::new(&s.directory)).is_err());
    assert!(state.restore(&s.session_id).is_err());
}
#[test]
fn close_stops_and_blocks_new_starts_until_cancelled() {
    let (_root, state, config) = setup(false);
    let s = state.create(config).unwrap();
    state.request_close();
    assert!(state.start(&s.session_id).is_err());
    state.cancel_close();
    state.start(&s.session_id).unwrap();
    finish(&state);
    assert_eq!(
        state.get(Some(&s.session_id)).unwrap().unwrap().status,
        "completed"
    );
}
#[test]
fn retained_response_projection_must_match_ledger_even_when_rehashed() {
    let (_root, state, config) = setup(false);
    let s = state.create(config).unwrap();
    state.start(&s.session_id).unwrap();
    finish(&state);
    let p = Path::new(&s.directory);
    let (mut m, mut r) = load(p).unwrap();
    let (event_index, request_id) = r
        .events
        .iter()
        .enumerate()
        .find_map(|(i, e)| match e {
            Event::QuietReceived { request_id, .. } => Some((i, request_id.clone())),
            _ => None,
        })
        .unwrap();
    let response_path = p.join(format!("{request_id}-response.json"));
    let mut response: Value = decode(&response_path).unwrap();
    response["projection"][0] = json!(0.8);
    let raw = encode(&response).unwrap();
    fs::write(response_path, &raw).unwrap();
    if let Event::QuietReceived {
        evidence_sha256, ..
    } = &mut r.events[event_index]
    {
        *evidence_sha256 = core::digest(&raw);
    }
    save(p, &mut m, &r).unwrap();
    assert!(verify(p).is_err());
}

fn unread_large_request_is_bounded(cancel_request: bool) {
    let (_root, _state, config) = setup(false);
    fs::write(&config.worker_path, "import time\ntime.sleep(30)\n").unwrap();
    let mut worker = Worker::spawn(&config).unwrap();
    let pid = worker.child.id();
    let cancelled = Arc::new(AtomicBool::new(false));
    let cancel_join = cancel_request.then(|| {
        let cancelled = cancelled.clone();
        thread::spawn(move || {
            thread::sleep(Duration::from_millis(150));
            cancelled.store(true, Ordering::SeqCst);
        })
    });
    let payload = json!({"existingCalibration":{"padding":"x".repeat(2 * 1024 * 1024)}});
    let start = Instant::now();
    let failure = worker
        .call(
            "initialize",
            payload,
            &cancelled,
            if cancel_request {
                Duration::from_secs(10)
            } else {
                Duration::from_millis(150)
            },
        )
        .unwrap_err();
    assert_eq!(
        failure.category,
        if cancel_request {
            "cancelled"
        } else {
            "timeout"
        }
    );
    assert!(start.elapsed() < Duration::from_secs(2));
    assert!(worker.input.is_none());
    assert!(worker.input_join.is_none(), "Blocked writer was not joined");
    #[cfg(unix)]
    {
        // ECHILD proves call() already reaped the process, rather than leaving
        // that cleanup for the assertion's own wait or for Worker::drop.
        let mut status = 0;
        assert_eq!(
            unsafe { libc::waitpid(pid as i32, &mut status, libc::WNOHANG) },
            -1
        );
        assert_eq!(
            std::io::Error::last_os_error().raw_os_error(),
            Some(libc::ECHILD)
        );
    }
    #[cfg(not(unix))]
    assert!(
        worker.child.try_wait().unwrap().is_some(),
        "Child {pid} is alive"
    );
    if let Some(join) = cancel_join {
        join.join().unwrap();
    }
    drop(worker);
    assert!(start.elapsed() < Duration::from_secs(2));
}

#[test]
fn worker_deadline_covers_large_request_when_child_never_reads_stdin() {
    unread_large_request_is_bounded(false);
}

#[test]
fn worker_cancel_joins_writer_and_reaps_child_that_never_reads_stdin() {
    unread_large_request_is_bounded(true);
}
