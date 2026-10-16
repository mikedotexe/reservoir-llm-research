use super::*;
fn root() -> std::path::PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("resources")
}
fn open(state: &ObservatoryState) -> ObservatorySummary {
    state.open(&root(), "open-1".into()).unwrap().observatory
}
fn copy_bundle() -> tempfile::TempDir {
    let dir = tempfile::tempdir().unwrap();
    for name in [
        "data.json",
        "state-replay.json",
        "state-replay.bin",
        "state-geometry.json",
    ] {
        std::fs::copy(root().join(name), dir.path().join(name)).unwrap();
    }
    dir
}
#[test]
fn independent_tracks_disclose_coverage_sources_and_meaning() {
    let state = ObservatoryState::default();
    let summary = open(&state);
    assert!(summary.diagnostics.is_empty());
    assert_eq!(summary.tracks.len(), 2);
    let h = &summary.tracks[0];
    assert_eq!(h.frame_count, 507);
    assert_eq!(h.axis, "elapsedSeconds");
    assert_eq!(h.node_count, None);
    assert_eq!(h.bands.as_ref().unwrap().target_pct, 68.0);
    assert_eq!(h.identities.len(), 1);
    let s = &summary.tracks[1];
    assert_eq!(s.frame_count, 1024);
    assert_eq!(s.node_count, Some(128));
    assert_eq!(s.axis, "ordinal");
    assert_eq!(s.first_utc, None);
    assert!(s.bands.is_none());
    assert_eq!(s.identities.len(), 3);
    let f = state
        .frame("f1".into(), &summary.observatory_id, "states", 1023)
        .unwrap();
    assert!(f.frame.history.is_none());
    assert_eq!(f.frame.state.unwrap().activations.len(), 128);
    let f = state
        .frame("f2".into(), &summary.observatory_id, "history", 0)
        .unwrap();
    assert!(f.frame.state.is_none());
    assert_eq!(f.frame.history.unwrap().fill_rate_pct_per_s, None);
}
#[test]
fn paged_timelines_cover_every_row_and_one_chosen_node_without_silent_truncation() {
    let state = ObservatoryState::default();
    let summary = open(&state);
    let id = &summary.observatory_id;
    for (track, total, node) in [("history", 507, None), ("states", 1024, Some(127))] {
        let mut indices = Vec::new();
        let mut start = 0;
        loop {
            let page = state
                .timeline("page".into(), id, track, start, 256, node)
                .unwrap();
            assert_eq!(page.total, total);
            assert!(page.points.len() <= 256);
            for point in &page.points {
                indices.push(point.index);
                if track == "states" {
                    assert_eq!(point.t_utc, None);
                    assert_eq!(point.interval_seconds, None);
                    assert_eq!(point.fill_pct, None);
                    let frame = state
                        .frame("frame".into(), id, track, point.index)
                        .unwrap()
                        .frame
                        .state
                        .unwrap();
                    assert_eq!(point.node_value, Some(frame.activations[127]));
                } else {
                    assert_eq!(point.node_value, None);
                }
            }
            start += page.points.len();
            if !page.has_more {
                break;
            }
        }
        assert_eq!(indices, (0..total).collect::<Vec<_>>());
        assert!(state
            .timeline("end".into(), id, track, total, 1, node)
            .unwrap()
            .points
            .is_empty());
    }
    assert!(state
        .timeline("bad".into(), id, "states", 0, 257, None)
        .is_err());
    assert!(state
        .timeline("bad".into(), id, "states", usize::MAX, 1, None)
        .is_err());
    assert!(state
        .timeline("bad".into(), id, "states", 0, 1, Some(128))
        .is_err());
    assert!(state
        .timeline("bad".into(), id, "history", 0, 1, Some(0))
        .is_err());
    assert!(state.frame("bad".into(), id, "history", 507).is_err());
}
#[test]
fn seek_replies_keep_request_identity_and_never_join_clocks() {
    let state = ObservatoryState::default();
    let s = open(&state);
    let id = &s.observatory_id;
    let result = state
        .seek("seek-8".into(), id, "states", 333.9, "floor")
        .unwrap();
    assert_eq!(result.request_id, "seek-8");
    assert_eq!(result.observatory_id, *id);
    assert_eq!(result.frame.index, 333);
    assert_eq!(
        state
            .seek("seek".into(), id, "states", 333.9, "nearest")
            .unwrap()
            .frame
            .index,
        334
    );
    assert_eq!(
        state
            .seek("seek".into(), id, "history", 1.0, "floor")
            .unwrap()
            .frame
            .index,
        0
    );
    assert!(state
        .seek("seek".into(), id, "states", 1.0, "seconds")
        .is_err());
    assert!(state
        .seek("seek".into(), id, "states", f64::NAN, "floor")
        .is_err());
    assert!(state.frame("bad".into(), id, "../data.json", 0).is_err());
}
#[test]
fn corrupt_or_missing_track_leaves_independent_track_available_with_diagnostic() {
    let dir = copy_bundle();
    std::fs::write(dir.path().join("data.json"), b"{}").unwrap();
    let state = ObservatoryState::default();
    let result = state.open(dir.path(), "broken-history".into()).unwrap();
    let s = result.observatory;
    assert_eq!(s.tracks.len(), 1);
    assert_eq!(s.tracks[0].id, "states");
    assert_eq!(s.diagnostics[0].track_id, "history");
    assert_eq!(s.diagnostics[0].category, "hash-mismatch");
    assert!(state
        .frame("frame".into(), &s.observatory_id, "history", 0)
        .is_err());
    std::fs::remove_file(dir.path().join("state-replay.bin")).unwrap();
    let empty = state
        .open(dir.path(), "both-broken".into())
        .unwrap()
        .observatory;
    assert!(empty.tracks.is_empty());
    assert_eq!(empty.diagnostics.len(), 2);
    let dir = copy_bundle();
    std::fs::write(dir.path().join("state-geometry.json"), b"{}").unwrap();
    let s = state
        .open(dir.path(), "broken-state".into())
        .unwrap()
        .observatory;
    assert_eq!(s.tracks.len(), 1);
    assert_eq!(s.tracks[0].id, "history");
    assert_eq!(s.diagnostics[0].track_id, "states");
}
#[test]
fn lifecycle_closes_idempotently_rejects_old_handles_and_bounds_sessions() {
    let state = ObservatoryState::default();
    let first = open(&state);
    let second = open(&state);
    state.close(&first.observatory_id).unwrap();
    state.close(&first.observatory_id).unwrap();
    assert!(state
        .frame("old".into(), &first.observatory_id, "history", 0)
        .is_err());
    assert!(state
        .frame("kept".into(), &second.observatory_id, "history", 0)
        .is_ok());
    let third = open(&state);
    assert_ne!(third.observatory_id, first.observatory_id);
    open(&state);
    open(&state);
    assert_eq!(
        state.open(&root(), "over".into()).unwrap_err().category,
        "handle-limit"
    );
    state.opening.store(true, Ordering::Release);
    assert_eq!(
        state.open(&root(), "busy".into()).unwrap_err().category,
        "busy"
    );
    state.opening.store(false, Ordering::Release);
}
#[test]
fn integer_identities_cross_ipc_as_strings_and_optional_values_remain_null() {
    let state = ObservatoryState::default();
    let mut h =
        HistoricalEvidence::from_bytes(&std::fs::read(root().join("data.json")).unwrap()).unwrap();
    h.samples[0].session_id = i64::MAX;
    h.samples[0].source_ids = Some(vec![Some(i64::MAX), None]);
    h.samples[0].geom_radius = None;
    state.captures.lock().unwrap().insert(
        "test".into(),
        Arc::new(Capture {
            history: Some(h),
            states: None,
        }),
    );
    let f = state.frame("req".into(), "test", "history", 0).unwrap();
    let json = serde_json::to_value(f).unwrap();
    assert_eq!(json["frame"]["history"]["sessionId"], i64::MAX.to_string());
    assert_eq!(
        json["frame"]["history"]["sourceIds"][0],
        i64::MAX.to_string()
    );
    assert!(json["frame"]["history"]["sourceIds"][1].is_null());
    assert!(json["frame"]["history"]["geomRadius"].is_null());
}

#[test]
fn reference_summary_is_static_and_fields_are_bounded_authoritative_vectors() {
    let state = ObservatoryState::default();
    let summary = open(&state);
    assert!(summary.tracks[0].state_reference.is_none());
    let reference = summary.tracks[1].state_reference.as_ref().unwrap();
    assert_eq!(reference.rows, 1024);
    assert_eq!(reference.dimensions, 128);
    assert_eq!(reference.retained_mode_count, 3);
    assert_eq!(reference.covariance_denominator, 1023);
    assert_eq!(reference.eigenvalues.len(), 128);
    assert_eq!(reference.explained_variance_ratio.len(), 128);
    assert_eq!(
        reference.fit_scope.as_deref(),
        Some("entire_captured_window_retrospective")
    );
    assert_eq!(reference.frozen, Some(true));
    assert_eq!(
        reference.source_identity,
        summary.tracks[1].identities[2].sha256
    );
    let static_json = serde_json::to_value(reference).unwrap();
    let capture = state.capture(&summary.observatory_id).unwrap();
    for row in [0, 511, 1023] {
        let result = state
            .frame("fields".into(), &summary.observatory_id, "states", row)
            .unwrap();
        let payload = serde_json::to_vec(&result).unwrap();
        assert!(payload.len() < 40 * 1024); // No basis or full matrix crosses per-frame IPC.
        let frame = result.frame.state.unwrap();
        let expected = states(&capture).unwrap().fields(row).unwrap();
        assert_eq!(
            serde_json::to_value(&frame.fields).unwrap(),
            serde_json::to_value(expected).unwrap()
        );
        assert_eq!(frame.fields.magnitude.len(), 128);
        assert_eq!(frame.fields.selections.len(), 4);
        let json = serde_json::to_value(&frame).unwrap();
        assert!(json.get("components").is_none());
        assert!(json.get("eigenvalues").is_none());
        assert_eq!(
            json["fields"]["selections"][3]["selectedModes"],
            serde_json::json!([0, 1, 2])
        );
        assert!(json["fields"]["centeredEnergy"].is_number());
    }
    assert_eq!(serde_json::to_value(reference).unwrap(), static_json);
    state.close(&summary.observatory_id).unwrap();
    assert!(state
        .frame("closed".into(), &summary.observatory_id, "states", 0)
        .is_err());
}
