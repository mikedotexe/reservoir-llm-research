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

fn near(a: f64, b: f64) {
    assert!((a - b).abs() <= 1e-12, "{a:.17} != {b:.17}");
}
fn compare_native(actual: &Value, expected: &Value) {
    match (actual, expected) {
        (Value::Number(a), Value::Number(b)) => near(a.as_f64().unwrap(), b.as_f64().unwrap()),
        (Value::Array(a), Value::Array(b)) => {
            assert_eq!(a.len(), b.len());
            for (a, b) in a.iter().zip(b) {
                compare_native(a, b);
            }
        }
        (Value::Object(a), Value::Object(b)) => {
            assert_eq!(a.len(), b.len());
            for (key, value) in a {
                compare_native(value, &b[key]);
            }
        }
        _ => assert_eq!(actual, expected),
    }
}

#[test]
fn derived_fields_match_unchanged_native_swift_for_all_eight_subsets() {
    // Generated by compiling the unchanged native StateSurface.swift. Four real
    // Float32 capture rows plus offset, signed/out-of-scale and sign-flip fixtures.
    let oracle: Value =
        serde_json::from_str(include_str!("fixtures/swift-state-fields-v1.json")).unwrap();
    let (m, raw, g) = state_bytes();
    let replay = StateReplay::from_bytes(&m, raw, &g).unwrap();
    let cases = oracle["cases"].as_array().unwrap();
    assert_eq!(cases.len(), 7);
    for case in cases {
        let activations: Vec<f64> = serde_json::from_value(case["activations"].clone()).unwrap();
        let mean: Vec<f64> = serde_json::from_value(case["mean"].clone()).unwrap();
        let components: Vec<Vec<f64>> = serde_json::from_value(case["components"].clone()).unwrap();
        let selections: Vec<Vec<usize>> =
            serde_json::from_value(case["selections"].clone()).unwrap();
        assert_eq!(selections.len(), 8);
        if let Some(row) = case["name"].as_str().unwrap().strip_prefix("bundled-row-") {
            assert_eq!(
                activations,
                replay.activations(row.parse().unwrap()).unwrap()
            );
            assert_eq!(mean, replay.geometry.pca.mean);
            assert_eq!(components, replay.geometry.pca.components);
        }
        let fields = derive_state_fields(&activations, &mean, &components, &selections).unwrap();
        compare_native(&serde_json::to_value(&fields).unwrap(), &case["expected"]);
        for selection in &fields.selections {
            for ((centered, reconstructed), residual) in fields
                .deviation
                .iter()
                .zip(&selection.reconstruction)
                .zip(&selection.residual)
            {
                near(*centered, reconstructed + residual);
            }
            near(
                fields.centered_energy,
                selection.reconstructed_energy + selection.residual_energy,
            );
        }
        assert_eq!(fields.selections[0].residual, fields.deviation);
        assert_eq!(fields.selections[0].reconstructed_energy, 0.0);
    }
}

#[test]
fn reference_fields_preserve_centering_sign_invariance_and_out_of_scale_values() {
    let observed = [-3.0, 2.0, 0.7, -0.4];
    let mean = [0.2; 4];
    let basis = vec![vec![1.0, 0.0, 0.0, 0.0], vec![0.0, 1.0, 0.0, 0.0]];
    let fields = derive_state_fields(&observed, &mean, &basis, &[vec![1, 0, 1]]).unwrap();
    assert_eq!(fields.magnitude, vec![3.0, 2.0, 0.7, 0.4]);
    assert_eq!(fields.magnitude_out_of_range_count, 2);
    assert_eq!(fields.deviation_out_of_range_count, 1);
    let selected = &fields.selections[0];
    assert_eq!(selected.selected_modes, vec![0, 1]);
    assert_eq!(selected.reconstruction[0], -3.2);
    assert_eq!(selected.reconstruction_out_of_range_count, 1);
    assert_eq!(selected.reconstruction[2], 0.0); // No mean addition.
    assert_eq!(selected.residual[0], 0.0);
    let flipped: Vec<Vec<f64>> = basis
        .iter()
        .map(|c| c.iter().map(|v| -v).collect())
        .collect();
    let reverse = derive_state_fields(&observed, &mean, &flipped, &[vec![0, 1]]).unwrap();
    assert_eq!(
        selected.reconstruction,
        reverse.selections[0].reconstruction
    );
    assert_eq!(selected.residual, reverse.selections[0].residual);
    assert_eq!(
        fields.scores,
        reverse.scores.iter().map(|v| -v).collect::<Vec<_>>()
    );
}

#[test]
fn invalid_field_reference_selection_and_overflow_fail_before_presentation() {
    let basis = vec![vec![1.0, 0.0], vec![0.0, 1.0]];
    assert!(derive_state_fields(&[], &[], &basis, &[]).is_err());
    assert!(derive_state_fields(&[f64::NAN, 0.0], &[0.0; 2], &basis, &[]).is_err());
    assert!(derive_state_fields(&[f64::MAX, 0.0], &[0.0; 2], &basis, &[]).is_err());
    assert!(derive_state_fields(&[0.0; 2], &[0.0], &basis, &[]).is_err());
    assert!(derive_state_fields(&[0.0; 2], &[f64::NAN; 2], &basis, &[]).is_err());
    assert!(derive_state_fields(&[0.0; 2], &[0.0; 2], &[], &[]).is_err());
    assert!(derive_state_fields(
        &[0.0; 2],
        &[0.0; 2],
        &[basis[0].clone(), basis[0].clone()],
        &[]
    )
    .is_err());
    assert!(derive_state_fields(&[0.0; 2], &[0.0; 2], &basis, &[vec![2]]).is_err());
    assert!(derive_state_fields(&[0.0; 2], &[0.0; 2], &basis, &vec![vec![]; 9]).is_err());
    assert!(derive_state_fields(&[0.0; 2], &[f64::MAX; 2], &basis, &[vec![0]]).is_err());
    assert!(derive_state_fields(&vec![0.0; 129], &vec![0.0; 129], &[vec![0.0; 129]], &[]).is_err());
}

#[test]
fn spectrum_and_reference_semantics_reject_reanchored_malformed_metadata() {
    for (key, value) in [
        ("covariance_denominator", json!(1024)),
        ("total_sample_variance", json!(0.0)),
        ("retained_fraction", json!(0.5)),
        ("omitted_fraction", json!(0.5)),
    ] {
        assert!(
            mutated_states(|_, _, g| g["pca"][key] = value).is_err(),
            "{key}"
        );
    }
    assert!(mutated_states(|_, _, g| g["pca"]["eigenvalues"][0] = json!(-0.1)).is_err());
    assert!(mutated_states(|_, _, g| {
        g["pca"]["eigenvalues"].as_array_mut().unwrap().swap(0, 1);
        g["pca"]["explained_variance_ratio"]
            .as_array_mut()
            .unwrap()
            .swap(0, 1);
    })
    .is_err());
    assert!(
        mutated_states(|_, _, g| g["pca"]["explained_variance_ratio"][0] = json!(0.9)).is_err()
    );
    assert!(
        mutated_states(|_, _, g| g["pca"]["components"][1] = g["pca"]["components"][0].clone())
            .is_err()
    );
}

#[test]
fn capture_fields_are_bounded_and_reference_spectrum_is_independent_of_cursor() {
    let (m, raw, g) = state_bytes();
    let replay = StateReplay::from_bytes(&m, raw, &g).unwrap();
    let pca = &replay.geometry.pca;
    assert_eq!(pca.eigenvalues.len(), 128);
    assert_eq!(pca.explained_variance_ratio.len(), 128);
    assert_eq!(pca.covariance_denominator, 1023);
    near(pca.total_sample_variance, pca.eigenvalues.iter().sum());
    near(
        pca.retained_fraction,
        pca.explained_variance_ratio[..3].iter().sum(),
    );
    near(
        pca.omitted_fraction,
        pca.explained_variance_ratio[3..].iter().sum(),
    );
    let spectrum = pca.eigenvalues.clone();
    for row in [0, 1, 511, 1023] {
        let fields = replay.fields(row).unwrap();
        assert_eq!(fields.magnitude.len(), 128);
        assert_eq!(fields.deviation.len(), 128);
        assert_eq!(fields.scores.len(), 3);
        assert_eq!(
            fields
                .selections
                .iter()
                .map(|s| s.selected_modes.clone())
                .collect::<Vec<_>>(),
            vec![vec![0], vec![1], vec![2], vec![0, 1, 2]]
        );
        for s in &fields.selections {
            assert_eq!(s.reconstruction.len(), 128);
            assert_eq!(s.residual.len(), 128);
        }
        let stored = &replay.geometry.samples[row];
        for (score, retained) in fields.scores.iter().zip(&stored.pc) {
            near(*score, *retained);
        }
        near(fields.centered_energy.sqrt(), stored.centered_norm);
        near(
            fields.selections[3].residual_energy.sqrt(),
            stored.residual_norm,
        );
        assert_eq!(pca.eigenvalues, spectrum);
    }
    assert!(replay.fields(1024).is_err());
}
