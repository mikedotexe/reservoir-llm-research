use super::*;
fn setup(slow: bool) -> (tempfile::TempDir, ActivationState, Config) {
    let root = tempfile::tempdir().unwrap();
    let worker = root.path().join("worker.py");
    let source = format!(
        r#"import json,sys,time
for line in sys.stdin:
 r=json.loads(line); c=r['command']
 if c=='inspect': x={{'loaded':False}}
 elif c=='initialize': x={{'manifest':{{'sha256':'fake-model'}},'calibration':{{'sha256':'fixed','modelManifestSha256':'fake-model','mean':[0]*32,'scales':[1]*32}}}}
 else:
  if {slow} and c=='quiet_capture': time.sleep(30)
  receipt={{'sampledTokenCount':0,'freshCache':True,'cacheDiscarded':True,'modelManifestSha256':'fake-model','calibrationSha256':'fixed','chatTemplateApplied':False}}
  x={{'projection':[0.2]*32,'promptTokenIds':[1,2],'generatedTokenIds':[],'sampledTokenIds':[],'receipt':receipt,'complete':True,'stopReason':'stop','text':'Synthetic fixture; no model generated this writing. An open question remains.'}}
  if c=='generate_journal':
   x['generatedTokenIds']=[3]; x['sampledTokenIds']=[3,4]
   receipt.update(steeringHeld=True,steeringState=r['steeringState'],requestedGain=r['gain'],arm=r['arm'],seed=r['seed'],temperature=r['temperature'],maxTokens=r['maxTokens'],feedbackEligible=True,capturedTokenId=3)
 print(json.dumps({{'id':r['id'],'type':'result','command':c,'result':x}}),flush=True)
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
