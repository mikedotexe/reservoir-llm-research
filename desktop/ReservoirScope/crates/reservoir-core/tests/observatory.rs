use reservoir_core::{observatory::*, CoreError};
use serde_json::{json, Value};
use std::path::PathBuf;
fn repo() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../..")
}
fn history_bytes() -> Vec<u8> {
    std::fs::read(repo().join("visualizations/reservoir-3d/data.json")).unwrap()
}
fn state_bytes() -> (Vec<u8>, Vec<u8>, Vec<u8>) {
    let native = repo().join("native/ReservoirScope/Sources/ReservoirScope/Resources");
    (
        std::fs::read(native.join("state-replay.json")).unwrap(),
        std::fs::read(native.join("state-replay.bin")).unwrap(),
        std::fs::read(repo().join("visualizations/reservoir-3d/state-geometry.json")).unwrap(),
    )
}
fn mutated_history(change: impl FnOnce(&mut Value)) -> reservoir_core::Result<HistoricalEvidence> {
    let mut value: Value = serde_json::from_slice(&history_bytes()).unwrap();
    change(&mut value);
    HistoricalEvidence::from_bytes(&serde_json::to_vec(&value).unwrap())
}
fn mutated_states(
    change: impl FnOnce(&mut Value, &mut Vec<u8>, &mut Value),
) -> reservoir_core::Result<StateReplay> {
    let (manifest, mut raw, geometry) = state_bytes();
    let mut m: Value = serde_json::from_slice(&manifest).unwrap();
    let mut g: Value = serde_json::from_slice(&geometry).unwrap();
    change(&mut m, &mut raw, &mut g);
    // Rebind mutations deliberately: failures below exercise semantic validation,
    // rather than merely rejecting the first stale hash.
    m["source_sha256"] = json!(digest(&raw));
    g["source"]["files"]["states"]["sha256"] = json!(digest(&raw));
    let geometry = serde_json::to_vec(&g).unwrap();
    m["geometry_sha256"] = json!(digest(&geometry));
    StateReplay::from_bytes(&serde_json::to_vec(&m).unwrap(), raw, &geometry)
}
#[test]
fn canonical_history_preserves_all_samples_and_distinct_measurements() {
    let h = HistoricalEvidence::from_bytes(&history_bytes()).unwrap();
    assert_eq!(h.samples.len(), 507);
    assert_eq!(h.samples[0].t_s, 0.0);
    assert_eq!(h.samples[506].t_s, 1198.51497746);
    assert_eq!(
        h.samples[0].cascade,
        vec![4.72739172, 3.07596111, 1.20072341]
    );
    assert_eq!(h.samples[0].esn_cov_lambda1, Some(19.45121193));
    assert_eq!(h.samples[0].fill_rate_pct_per_s, None);
    assert_eq!(h.samples[506].fill_rate_pct_per_s, Some(-1.56934016));
    assert_eq!(h.bands.target_pct, 68.0);
    assert_eq!(h.bands.shelf_min_pct, 58.0);
    assert_eq!(h.bands.force_rail_pct, 78.0);
    assert!(h
        .samples
        .iter()
        .enumerate()
        .all(|(i, _)| !h.break_before(i)));
}
#[test]
fn history_seek_holds_previous_observation_and_nearest_ties_choose_earlier() {
    let mut h = HistoricalEvidence::from_bytes(&history_bytes()).unwrap();
    h.samples.truncate(3);
    h.samples[0].t_s = 0.0;
    h.samples[1].t_s = 10.0;
    h.samples[2].t_s = 100.0;
    assert_eq!(h.seek(9.0, false).unwrap(), 0);
    assert_eq!(h.seek(9.0, true).unwrap(), 1);
    assert_eq!(h.seek(55.0, true).unwrap(), 1);
    assert_eq!(h.seek(55.01, true).unwrap(), 2);
    assert_eq!(h.seek(-100.0, false).unwrap(), 0);
    assert_eq!(h.seek(1e9, false).unwrap(), 2);
    assert!(h.seek(f64::NAN, false).is_err());
    assert_eq!(h.interval_seconds(2), Some(90.0));
    assert!(!h.break_before(2));
    h.samples[2].session_id += 1;
    assert!(h.break_before(2));
}
#[test]
fn history_rejects_schema_shape_time_and_bounds_without_sorting_spectral_slots() {
    assert!(matches!(
        mutated_history(|v| v["schema_version"] = json!(2)),
        Err(CoreError::Unsupported(_))
    ));
    for (path, value) in [
        ("fill_pct", json!(101)),
        ("cascade", json!([1, 2])),
        ("t_utc", json!("2026-02-30T16:09:01Z")),
        ("t_utc", json!("2026-09-06T24:09:01Z")),
        ("t_utc", json!("2026-09-06T16:09:01.000+25:00")),
        ("t_s", json!(2)),
    ] {
        assert!(
            mutated_history(|v| {
                v["samples"][0][path] = value;
                if path == "t_s" {
                    v["samples"][1][path] = json!(1);
                }
            })
            .is_err(),
            "{path}"
        );
    }
    assert!(mutated_history(|v| v["bands"]["target_pct"] = json!(99)).is_err());
    let h = mutated_history(|v| v["samples"][0]["cascade"] = json!([1, 8, 3])).unwrap();
    assert_eq!(h.samples[0].cascade, vec![1.0, 8.0, 3.0]);
    let mut h = h;
    h.samples[0].esn_cov_lambda1 = Some(f64::INFINITY);
    assert!(h.validate().is_err());
    assert!(HistoricalEvidence::from_bytes(&vec![b' '; MAX_JSON_BYTES + 1]).is_err());
}
#[test]
fn history_missingness_and_signed_identifiers_are_preserved() {
    let h = mutated_history(|v| {
        v["samples"][0]["session_id"] = json!(i64::MAX);
        v["samples"][0]["source_ids"] = json!([i64::MAX, null, -1]);
        for key in [
            "esn_cov_lambda1",
            "geom_radius",
            "geom_rel",
            "esn_leak",
            "esn_lambda",
        ] {
            v["samples"][0].as_object_mut().unwrap().remove(key);
        }
    })
    .unwrap();
    assert_eq!(h.samples[0].session_id, i64::MAX);
    assert_eq!(
        h.samples[0].source_ids,
        Some(vec![Some(i64::MAX), None, Some(-1)])
    );
    assert_eq!(h.samples[0].geom_radius, None);
}
#[test]
fn canonical_state_decodes_every_retained_coordinate_without_a_clock_or_fill_join() {
    let (m, raw, g) = state_bytes();
    let r = StateReplay::from_bytes(&m, raw.clone(), &g).unwrap();
    assert_eq!(r.manifest.rows, 1024);
    assert_eq!(r.manifest.dimensions, 128);
    assert!(!r.manifest.per_row_timestamps_available);
    assert!(!r.manifest.paired_fill_available);
    assert_eq!(r.manifest.node_layout_id, None);
    for row in 0..1024 {
        let values = r.activations(row).unwrap();
        assert_eq!(values.len(), 128);
        for (node, value) in values.iter().enumerate() {
            let offset = (row * 128 + node) * 4;
            assert_eq!(
                value.to_bits(),
                f64::from(f32::from_le_bytes(
                    raw[offset..offset + 4].try_into().unwrap()
                ))
                .to_bits()
            );
            assert_eq!(*value, r.node(row, node).unwrap());
        }
    }
    assert_eq!(r.seek(500.5, true).unwrap(), 500);
    assert_eq!(r.seek(500.51, true).unwrap(), 501);
    assert_eq!(r.seek(-1.0, false).unwrap(), 0);
    assert_eq!(r.seek(9999.0, false).unwrap(), 1023);
    assert!(r.activations(1024).is_err());
    assert!(r.node(0, 128).is_err());
    assert!(r.seek(f64::INFINITY, false).is_err());
}
#[test]
fn state_rejects_byte_and_hash_corruption_before_presentation() {
    let (m, raw, g) = state_bytes();
    let mut damaged = raw.clone();
    damaged[19] ^= 1;
    assert!(StateReplay::from_bytes(&m, damaged, &g).is_err());
    assert!(StateReplay::from_bytes(&m, raw[..raw.len() - 1].to_vec(), &g).is_err());
    let mut geometry = g.clone();
    geometry.push(b' ');
    assert!(StateReplay::from_bytes(&m, raw, &geometry).is_err());
    assert!(mutated_states(|m, _, _| m["byte_count"] = json!(1)).is_err());
}
#[test]
fn rebound_state_mutations_reject_finite_range_dimension_order_and_identity_claim_errors() {
    for bad in [f32::NAN, f32::INFINITY, 1.01, -1.01] {
        assert!(mutated_states(|_, raw, _| raw[0..4].copy_from_slice(&bad.to_le_bytes())).is_err());
    }
    for (key, value) in [
        ("rows", json!(1025)),
        ("dimensions", json!(127)),
        ("binary_file", json!("../state-replay.bin")),
        ("dtype", json!(">f4")),
        ("row_order", json!("newest_to_oldest")),
        ("per_row_timestamps_available", json!(true)),
        ("paired_fill_available", json!(true)),
        ("node_layout_id", json!("invented")),
    ] {
        assert!(mutated_states(|m, _, _| m[key] = value).is_err(), "{key}");
    }
    assert!(mutated_states(|_, _, g| g["samples"][1]["index"] = json!(0)).is_err());
    assert!(mutated_states(|_, _, g| g["samples"][0]["state_rms"] = json!(-1)).is_err());
    assert!(mutated_states(|_, _, g| g["pca"]["components"][0] = json!([1, 2])).is_err());
    assert!(mutated_states(|m, _, _| m["captured_at_utc"] = json!("unrelated capture")).is_err());
}
