use super::*;
use serde_json::{json, Value};
fn native_bytes() -> Vec<u8> {
    std::fs::read(
        Path::new(env!("CARGO_MANIFEST_DIR")).join("resources/native-action-response.json"),
    )
    .unwrap()
}
fn sim_bytes() -> Vec<u8> {
    std::fs::read(Path::new(env!("CARGO_MANIFEST_DIR")).join("resources/state-response.json"))
        .unwrap()
}
fn open(state: &ResponseState) -> ResponseSummary {
    state
        .open(
            "open".into(),
            "receipts.json".into(),
            "openedFile",
            "native",
            native_bytes(),
            None,
        )
        .unwrap()
        .response
        .unwrap()
}
fn changed(f: impl FnOnce(&mut Value)) -> Vec<u8> {
    let mut v = serde_json::from_slice(&native_bytes()).unwrap();
    f(&mut v);
    serde_json::to_vec(&v).unwrap()
}
#[test]
fn canonical_handles_keep_response_families_and_exact_values_separate() {
    let state = ResponseState::default();
    let n = open(&state);
    assert_eq!(n.frame_count, 8);
    assert_eq!(n.events.len(), 10);
    assert_eq!(n.return_threshold, None);
    assert_eq!(n.first_label, "Ordinary step");
    let f = state.frame("frame1".into(), &n.response_id, 0).unwrap();
    assert_eq!(f.frame.first.len(), 128);
    assert_eq!(f.frame.delta.len(), 128);
    assert_eq!(f.request_id, "frame1");
    let raw = NativeResponse::decode(&native_bytes()).unwrap();
    let receipt = &raw.receipts[raw.frame_indices[0]];
    for (i, value) in f.frame.first.iter().enumerate() {
        assert_eq!(
            value.to_bits(),
            f64::from(receipt.before.as_ref().unwrap()[i]).to_bits()
        );
    }
    assert_eq!(
        f.frame.position,
        receipt.successful_step_id.unwrap().to_string()
    );
    let s = state
        .open(
            "sim".into(),
            "state-response.json".into(),
            "bundled",
            "simulation",
            sim_bytes(),
            Some(&n.response_id),
        )
        .unwrap()
        .response
        .unwrap();
    assert_eq!(s.frame_count, 65);
    assert!(s.events.is_empty());
    assert_eq!(s.first_label, "Control");
    assert!(s.return_threshold.is_some());
    let f = state.frame("last".into(), &s.response_id, 64).unwrap();
    assert_eq!(f.frame.position, "264");
    assert_eq!(f.frame.l2, 0.0);
    assert!(f.frame.direction.is_none());
    assert!(state.event("event".into(), &s.response_id, 0).is_err());
    assert!(state.frame("bad".into(), &s.response_id, 65).is_err());
}
#[test]
fn events_keep_no_state_and_headroom_rejection_distinct_from_frames() {
    let state = ResponseState::default();
    let n = open(&state);
    let e = state
        .event("event".into(), &n.response_id, 0)
        .unwrap()
        .event;
    assert_eq!(e.status, "accepted");
    assert!(!e.has_state);
    assert!(!e.is_boundary);
    assert!(e.first.is_none());
    assert_eq!(e.direction.len(), 128);
    let data = changed(|v| {
        let mut r = v["receipts"][1].clone();
        r["status"] = json!("headroom_rejected");
        r["after"] = r["before"].clone();
        r["delta"] = json!([0.0; 128].to_vec());
        r["attenuation"] = json!(0);
        r["actual_l2"] = json!(0);
        r["max_abs_delta"] = json!(0);
        r["clipped"] = json!(false);
        v["receipts"] = json!([r]);
    });
    let r = state
        .open(
            "rejected".into(),
            "zero.json".into(),
            "openedFile",
            "native",
            data,
            None,
        )
        .unwrap()
        .response
        .unwrap();
    assert_eq!(r.frame_count, 0);
    assert!(r.timeline.is_empty());
    assert_eq!(r.events.len(), 1);
    let e = state
        .event("event".into(), &r.response_id, 0)
        .unwrap()
        .event;
    assert!(!e.has_state);
    assert!(e.is_boundary);
    assert_eq!(e.delta, Some(vec![0.0; 128]));
    assert!(state.frame("frame".into(), &r.response_id, 0).is_err());
}
#[test]
fn rejected_candidates_never_drop_or_change_the_previous_bytes() {
    let state = ResponseState::default();
    let n = open(&state);
    for bytes in [
        b"{}".to_vec(),
        changed(|v| v["receipts"][1]["observed_at_unix_ms"] = json!(0)),
        changed(|v| v["receipts"].as_array_mut().unwrap().truncate(2)),
        changed(|v| v["source_hashes"]["executable"] = json!("a".repeat(64))),
    ] {
        assert!(state
            .open(
                "bad".into(),
                "next.json".into(),
                "openedFile",
                "native",
                bytes,
                Some(&n.response_id)
            )
            .is_err());
        assert_eq!(*state.snapshot(&n.response_id).unwrap().1, native_bytes());
        assert!(state.frame("still".into(), &n.response_id, 7).is_ok());
    }
    assert_eq!(state.inner.stored.lock().unwrap().len(), 1);
    assert!(state
        .open(
            "unknown".into(),
            "file.json".into(),
            "openedFile",
            "native",
            native_bytes(),
            Some("closed")
        )
        .is_err());
    assert!(state
        .open(
            "badsource".into(),
            "simulation.json".into(),
            "openedFile",
            "simulation",
            sim_bytes(),
            None
        )
        .is_err());
}
#[test]
fn wide_identifiers_and_float32_promotions_survive_json_ipc() {
    let state = ResponseState::default();
    let data = changed(|v| {
        let mut r = v["receipts"][1].clone();
        r["successful_step_id"] = json!(u64::MAX);
        r["observed_at_unix_ms"] = json!(u64::MAX);
        r["boundary_wait_us"] = json!(u64::MAX);
        v["receipts"] = json!([r]);
    });
    let n = state
        .open(
            "wide".into(),
            "wide.json".into(),
            "openedFile",
            "native",
            data,
            None,
        )
        .unwrap()
        .response
        .unwrap();
    assert_eq!(n.timeline[0].position, u64::MAX.to_string());
    let f = state.frame("exact".into(), &n.response_id, 0).unwrap();
    let actual = f.frame.first[0];
    let j = serde_json::to_string(&f).unwrap();
    let round: Value = serde_json::from_str(&j).unwrap();
    assert_eq!(
        round["frame"]["first"][0].as_f64().unwrap().to_bits(),
        actual.to_bits()
    );
    assert_eq!(
        round["frame"]["metadata"]["Successful native step"],
        u64::MAX.to_string()
    );
    assert_eq!(
        round["frame"]["metadata"]["Boundary wait (µs)"],
        u64::MAX.to_string()
    );
}
#[test]
fn exports_are_original_bytes_and_snapshot_survives_close() {
    let state = ResponseState::default();
    let n = open(&state);
    let dir = tempfile::tempdir().unwrap();
    let resource = tempfile::tempdir().unwrap();
    let destination = dir.path().join("exact.json");
    let proof = state
        .export(&n.response_id, &destination, resource.path())
        .unwrap();
    assert_eq!(std::fs::read(&destination).unwrap(), native_bytes());
    assert_eq!(proof.sha256, n.sha256);
    let (_, snapshot) = state.snapshot(&n.response_id).unwrap();
    state.close(&n.response_id).unwrap();
    state.close(&n.response_id).unwrap();
    assert_eq!(*snapshot, native_bytes());
    assert!(state.snapshot(&n.response_id).is_err());
    let n = open(&state);
    assert!(state
        .export(
            &n.response_id,
            &resource.path().join("forbidden.json"),
            resource.path()
        )
        .is_err());
}
#[test]
fn lifecycle_guards_and_handle_limits_are_bounded() {
    let state = ResponseState::default();
    let guard = state.begin_operation().unwrap();
    assert!(state.begin_operation().is_err());
    drop(guard);
    assert!(state.begin_operation().is_ok());
    for _ in 0..4 {
        open(&state);
    }
    assert!(state
        .open(
            "fifth".into(),
            "file.json".into(),
            "openedFile",
            "native",
            native_bytes(),
            None
        )
        .is_err());
    let id = state
        .inner
        .stored
        .lock()
        .unwrap()
        .keys()
        .next()
        .unwrap()
        .clone();
    state.close(&id).unwrap();
    let next = open(&state);
    assert_ne!(next.response_id, id);
    assert!(state.frame("old".into(), &id, 0).is_err());
    assert!(state.event("bad".into(), &next.response_id, 10).is_err());
}
#[test]
fn canonically_equivalent_identity_does_not_allow_mutated_boundary_replacement() {
    let state = ResponseState::default();
    let bytes = changed(|v| {
        for r in v["receipts"].as_array_mut().unwrap() {
            r["identity"]["engine_session_id"] = json!("session-é");
            r["command_id"] = json!("command-é");
        }
    });
    let old = state
        .open(
            "old".into(),
            "unicode.json".into(),
            "openedFile",
            "native",
            bytes.clone(),
            None,
        )
        .unwrap()
        .response
        .unwrap();
    let mut next: Value = serde_json::from_slice(&bytes).unwrap();
    for r in next["receipts"].as_array_mut().unwrap() {
        r["identity"]["engine_session_id"] = json!("session-e\u{301}");
        r["command_id"] = json!("command-e\u{301}");
    }
    next["receipts"][1]["reason"] = json!("changed overlap");
    assert!(state
        .open(
            "new".into(),
            "candidate.json".into(),
            "openedFile",
            "native",
            serde_json::to_vec(&next).unwrap(),
            Some(&old.response_id)
        )
        .is_err());
    assert_eq!(*state.snapshot(&old.response_id).unwrap().1, bytes);
    assert!(state.frame("kept".into(), &old.response_id, 0).is_ok());
}
