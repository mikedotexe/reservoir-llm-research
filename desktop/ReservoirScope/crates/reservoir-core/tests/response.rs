use reservoir_core::response::*;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::path::PathBuf;
fn repo() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../..")
}
fn native_bytes() -> Vec<u8> {
    std::fs::read(repo().join("research/examples/native-action-response.json")).unwrap()
}
fn simulation_bytes() -> Vec<u8> {
    std::fs::read(
        repo().join("native/ReservoirScope/Sources/ReservoirScope/Resources/state-response.json"),
    )
    .unwrap()
}
fn changed_native(f: impl FnOnce(&mut Value)) -> Vec<u8> {
    let mut v = serde_json::from_slice(&native_bytes()).unwrap();
    f(&mut v);
    serde_json::to_vec(&v).unwrap()
}
fn reject(f: impl FnOnce(&mut Value)) {
    assert!(NativeResponse::decode(&changed_native(f)).is_err());
}
fn simulation(f: impl FnOnce(&mut Value)) -> reservoir_core::Result<SimulationResponse> {
    let mut v = serde_json::from_slice(&simulation_bytes()).unwrap();
    f(&mut v);
    let b = serde_json::to_vec(&v).unwrap();
    SimulationResponse::decode_with_hash(&b, &format!("{:x}", Sha256::digest(&b)))
}
#[test]
fn canonical_native_boundaries_preserve_float32_difference_and_measurements() {
    let n = NativeResponse::decode(&native_bytes()).unwrap();
    assert_eq!(n.receipts.len(), 10);
    assert_eq!(n.frame_indices.len(), 8);
    assert_eq!(n.boundary_indices.len(), 8);
    assert!(n.delta_scale() > 0.0);
    for &i in &n.frame_indices {
        let r = &n.receipts[i];
        assert_eq!(r.direction.len(), 128);
        for ((a, b), d) in r
            .after
            .as_ref()
            .unwrap()
            .iter()
            .zip(r.before.as_ref().unwrap())
            .zip(r.delta.as_ref().unwrap())
        {
            assert_eq!((a - b).to_bits(), d.to_bits());
        }
    }
    n.validate_replacement(&n).unwrap();
}
#[test]
fn native_provenance_unknown_fields_dimensions_and_boundaries_are_strict() {
    for (key, value) in [
        ("fill", json!(68)),
        ("reference_basis", json!("PCA")),
        ("clock", json!("measured seconds")),
        ("subject", json!("live Minime")),
        ("extra", json!(true)),
        ("source_hashes", json!({})),
        ("receipts", json!([])),
    ] {
        reject(|v| v[key] = value);
    }
    for (key, value) in [
        ("after", json!([0])),
        ("actual_l2", json!(9)),
        ("max_abs_delta", json!(9)),
        ("effective_leak", json!(null)),
        ("realized_noise", json!(null)),
        ("successful_step_id", json!(0)),
        ("pulse_index", json!(-1)),
        ("success_offset", json!(4294967296_u64)),
        ("fill", json!(68)),
        ("status", json!("no_op")),
        ("status", json!("step_failed")),
    ] {
        reject(|v| v["receipts"][1][key] = value);
    }
    reject(|v| v["receipts"][1]["identity"]["hidden"] = json!(1));
    reject(|v| {
        let pulse = v["receipts"][1].clone();
        v["receipts"].as_array_mut().unwrap().insert(2, pulse);
    });
    reject(|v| v["receipts"][2]["identity"]["engine_session_id"] = json!("spliced"));
    reject(|v| v["receipts"][1]["after"][0] = json!(1.1));
    reject(|v| v["receipts"][1]["delta"][127] = json!(0.123));
    assert!(NativeResponse::decode(&vec![b' '; NATIVE_MAX_BYTES + 1]).is_err());
}
#[test]
fn native_zero_boundaries_signed_zero_and_headroom_semantics() {
    let zero = changed_native(|v| {
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
    let n = NativeResponse::decode(&zero).unwrap();
    assert!(n.frame_indices.is_empty());
    assert_eq!(n.boundary_indices.len(), 1);
    assert_eq!(n.delta_scale(), 1e-9);
    let mut v: Value = serde_json::from_slice(&zero).unwrap();
    v["receipts"][0]["delta"][0] = json!(-0.0);
    assert!(NativeResponse::decode(&serde_json::to_vec(&v).unwrap()).is_err());
    v["receipts"][0]["delta"][0] = json!(0.0);
    v["receipts"][0]["clipped"] = json!(true);
    assert!(NativeResponse::decode(&serde_json::to_vec(&v).unwrap()).is_err());
    let events = changed_native(|v| {
        v["receipts"] = json!([v["receipts"][0].clone(), v["receipts"][9].clone()]);
    });
    let e = NativeResponse::decode(&events).unwrap();
    assert!(e.frame_indices.is_empty());
    assert!(e.boundary_indices.is_empty());
}
#[test]
fn native_replacement_keeps_overlapping_boundaries_and_source_identity_immutable() {
    let old = NativeResponse::decode(&native_bytes()).unwrap();
    for bytes in [
        changed_native(|v| v["receipts"][1]["observed_at_unix_ms"] = json!(0)),
        changed_native(|v| v["source_hashes"]["executable"] = json!("a".repeat(64))),
        changed_native(|v| v["receipts"].as_array_mut().unwrap().truncate(2)),
    ] {
        NativeResponse::decode(&bytes)
            .unwrap()
            .validate_replacement(&old)
            .unwrap_err();
    }
    let new = changed_native(|v| {
        for r in v["receipts"].as_array_mut().unwrap() {
            r["identity"]["engine_session_id"] = json!("new independent session");
        }
    });
    NativeResponse::decode(&new)
        .unwrap()
        .validate_replacement(&old)
        .unwrap();
}
#[test]
fn exact_wide_native_integer_lexemes_do_not_pass_through_float64() {
    let bytes = changed_native(|v| {
        v["receipts"] = json!([v["receipts"][1].clone()]);
        v["receipts"][0]["successful_step_id"] = json!(u64::MAX);
        v["receipts"][0]["observed_at_unix_ms"] = json!(u64::MAX);
    });
    let n = NativeResponse::decode(&bytes).unwrap();
    assert_eq!(n.receipts[0].successful_step_id, Some(u64::MAX));
    for (token, expected) in [
        ("9007199254740993.0", 9007199254740993_u64),
        ("9007199254740993e0", 9007199254740993),
        ("18446744073709549568.0", 18446744073709549568),
        ("1e3", 1000),
    ] {
        let bytes = String::from_utf8(bytes.clone())
            .unwrap()
            .replace("18446744073709551615", token)
            .into_bytes();
        let n = NativeResponse::decode(&bytes).unwrap();
        assert_eq!(n.receipts[0].successful_step_id, Some(expected));
        assert_eq!(n.receipts[0].observed_at_unix_ms, expected);
    }
    for token in [
        "18446744073709551615.0",
        "18446744073709551615e0",
        "1.8446744073709551615e19",
        "18446744073709551616",
        "18446744073709551615.1",
        "-1",
        "1e100",
    ] {
        let b = String::from_utf8(bytes.clone())
            .unwrap()
            .replace("18446744073709551615", token)
            .into_bytes();
        assert!(NativeResponse::decode(&b).is_err(), "{token}");
    }
    reject(|v| v["receipts"][0]["requested_amount"] = json!(1e40));
    reject(|v| v["receipts"][0]["realized_noise"] = json!([1e40]));
}
#[test]
fn retained_simulation_rechecks_all_vectors_and_summary_without_running_a_simulation() {
    let s = SimulationResponse::decode(&simulation_bytes()).unwrap();
    assert_eq!(s.frames.len(), 65);
    assert_eq!(s.frames[0].original_boundary_step, 200);
    assert_eq!(s.frames[64].original_boundary_step, 264);
    assert_eq!(s.result_summary.return_boundary, Some(2));
    assert_eq!(s.result_summary.peak_gain_over_initial, 1.0);
    assert_eq!(s.fixed_delta_scale(), 0.001);
    assert_eq!(s.frames[64].separation_l2, 0.0);
    let mut b = simulation_bytes();
    b.push(b' ');
    assert!(SimulationResponse::decode(&b).is_err());
    assert!(SimulationResponse::decode(&vec![b' '; SIMULATION_MAX_BYTES + 1]).is_err());
}
#[test]
fn rebound_simulation_mutations_cannot_relabel_scope_time_or_displacement() {
    for (key, value) in [
        ("fill", json!(68)),
        ("reference_basis", json!("native")),
        ("subject", json!("live Minime")),
        ("clock", json!("seconds")),
        ("node_count", json!(127)),
        ("extra", json!(1)),
    ] {
        assert!(simulation(|v| v[key] = value).is_err(), "{key}");
    }
    for (key, value) in [
        ("delta", json!([0])),
        ("separation_l2", json!(2)),
        ("original_boundary_step", json!(201)),
        ("sample_index", json!(2)),
        ("seconds", json!(0)),
    ] {
        assert!(
            simulation(|v| v["frames"][0][key] = value).is_err(),
            "{key}"
        );
    }
    assert!(simulation(|v| v["result_summary"]["return_boundary"] = json!(3)).is_err());
    assert!(simulation(|v| v["result_summary"]["peak_gain_over_initial"] = json!(9)).is_err());
    assert!(simulation(|v| v["frames"][0]["control"][1] = json!(1.01)).is_err());
}
#[test]
fn swift_canonical_string_equality_cannot_bypass_native_replacement_identity() {
    let make = |session: &str, command: &str, reason: &str, source_key: &str| {
        changed_native(|v| {
            v["source_hashes"] = json!({source_key:"a".repeat(64)});
            for r in v["receipts"].as_array_mut().unwrap() {
                r["identity"]["engine_session_id"] = json!(session);
                r["command_id"] = json!(command);
                r["reason"] = json!(reason);
            }
        })
    };
    let old_bytes = make("session-é", "command-é", "réason", "sourcé");
    let old = NativeResponse::decode(&old_bytes).unwrap();
    let same_bytes = make(
        "session-e\u{301}",
        "command-e\u{301}",
        "re\u{301}ason",
        "source\u{301}",
    );
    let same = NativeResponse::decode(&same_bytes).unwrap();
    same.validate_replacement(&old).unwrap();
    assert_eq!(same.receipts[1], old.receipts[1]);
    assert_ne!(
        same.receipts[1].command_id.as_bytes(),
        old.receipts[1].command_id.as_bytes()
    );
    let mut changed: Value = serde_json::from_slice(&same_bytes).unwrap();
    changed["source_hashes"] = json!({"source\u{301}":"b".repeat(64)});
    NativeResponse::decode(&serde_json::to_vec(&changed).unwrap())
        .unwrap()
        .validate_replacement(&old)
        .unwrap_err();
    let mut changed: Value = serde_json::from_slice(&same_bytes).unwrap();
    changed["receipts"][1]["reason"] = json!("altered boundary");
    NativeResponse::decode(&serde_json::to_vec(&changed).unwrap())
        .unwrap()
        .validate_replacement(&old)
        .unwrap_err();
    let ambiguous = changed_native(|v| {
        v["source_hashes"] = json!({"é":"a".repeat(64),"e\u{301}":"b".repeat(64)})
    });
    assert!(NativeResponse::decode(&ambiguous).is_err());
}
