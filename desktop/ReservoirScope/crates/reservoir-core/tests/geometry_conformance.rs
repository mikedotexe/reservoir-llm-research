//! Synthetic packets only. Mutations reseal the entire chain and references so
//! semantic failures cannot hide behind a trivial outer hash mismatch.
use reservoir_core::geometry::{hash, GeometryEntry, GeometryPacket, MAX_PACKET_BYTES};
use serde_json::{json, Value};
use std::{collections::HashMap, path::PathBuf};

fn fixture(owner: &str) -> Vec<u8> {
    std::fs::read(PathBuf::from(env!("CARGO_MANIFEST_DIR")).join(format!("../../../../native/ReservoirScope/Tests/Fixtures/geometry-bookmarks/{owner}-synthetic-geometry.json"))).unwrap()
}
fn body(owner: &str) -> Value {
    let e: Value = serde_json::from_slice(&fixture(owner)).unwrap();
    serde_json::from_str(e["body_json"].as_str().unwrap()).unwrap()
}
fn entry(b: &mut Value, index: usize, change: impl FnOnce(&mut Value)) {
    let r = &mut b["history"]["records"][index];
    let mut e = serde_json::from_str(r["body_json"].as_str().unwrap()).unwrap();
    change(&mut e);
    r["body_json"] = json!(serde_json::to_string(&e).unwrap());
}
fn snapshot(b: &mut Value, change: impl FnOnce(&mut Value)) {
    entry(b, 0, |e| change(&mut e["snapshot"]));
}
fn seal(mut b: Value) -> Vec<u8> {
    let mut replacements: HashMap<String, String> = HashMap::new();
    let mut previous = "empty".to_owned();
    for r in b["history"]["records"].as_array_mut().unwrap() {
        let old = r["id"].as_str().unwrap().to_owned();
        let mut e: Value = serde_json::from_str(r["body_json"].as_str().unwrap()).unwrap();
        for key in ["baseline", "prediction", "observation", "target"] {
            if let Some(replacement) = e[key].as_str().and_then(|id| replacements.get(id)) {
                e[key] = json!(replacement);
            }
        }
        let text = serde_json::to_string(&e).unwrap();
        let id = hash(
            &[
                previous.clone(),
                hash(r["request_id"].as_str().unwrap()),
                r["request_sha256"].as_str().unwrap().into(),
                hash(&text),
            ]
            .join("\n"),
        );
        r["previous"] = json!(previous);
        r["body_json"] = json!(text);
        r["id"] = json!(id);
        replacements.insert(old, id.clone());
        previous = id;
    }
    let text = serde_json::to_string(&b).unwrap();
    serde_json::to_vec(
        &json!({"format":"question-geometry-v1","body_sha256":hash(&text),"body_json":text}),
    )
    .unwrap()
}
fn rejects(change: impl FnOnce(&mut Value), expected: &str) {
    let mut b = body("minime");
    change(&mut b);
    let error = GeometryPacket::decode(&seal(b)).unwrap_err().to_string();
    assert!(error.contains(expected), "Expected {expected}, got {error}");
}

#[test]
fn both_canonical_synthetic_packets_and_resealed_controls_verify() {
    for owner in ["astrid", "minime"] {
        let p = GeometryPacket::decode(&fixture(owner)).unwrap();
        assert_eq!(p.records.len(), 5);
        assert_eq!(p.body.owner, owner);
        let GeometryEntry::Capture { snapshot, .. } = &p.records[0] else {
            panic!()
        };
        assert_eq!(snapshot.gaps(), vec![(11000, 13000)]);
        assert_eq!(snapshot.duration_ms(), 3000);
        let GeometryEntry::Comparison {
            rms_distance,
            threshold_met,
            ..
        } = p.records[3]
        else {
            panic!()
        };
        assert!((rms_distance - 0.1).abs() < 1e-12);
        assert!(!threshold_met);
        assert!(p.records[3].authored_text().is_none());
        for i in [0, 1, 4] {
            assert!(p.records[i]
                .authored_text()
                .unwrap()
                .starts_with("Synthetic"));
        }
        let mut b = body(owner);
        entry(&mut b, 0, |e| {
            e["note"] = json!("Resealed synthetic control. Café and 宇宙 are authored data.")
        });
        let q = GeometryPacket::decode(&seal(b)).unwrap();
        assert_ne!(p.body.history.records[0].id, q.body.history.records[0].id);
        let mut b = body(owner);
        entry(&mut b, 1, |e| e["maximum_rms_distance"] = json!(0.2));
        entry(&mut b, 3, |e| e["threshold_met"] = json!(true));
        assert!(GeometryPacket::decode(&seal(b)).is_ok());
        let mut b = body(owner);
        b["history"] = json!({"records":[]});
        assert!(GeometryPacket::decode(&seal(b)).unwrap().records.is_empty());
    }
}
#[test]
fn body_chain_and_operation_identity_are_checked() {
    assert!(GeometryPacket::decode(&[]).is_err());
    assert!(GeometryPacket::decode(&vec![b' '; MAX_PACKET_BYTES + 1]).is_err());
    let mut e: Value = serde_json::from_slice(&fixture("minime")).unwrap();
    e["body_json"] = json!(format!("{} ", e["body_json"].as_str().unwrap()));
    assert!(GeometryPacket::decode(&serde_json::to_vec(&e).unwrap()).is_err());
    rejects(
        |b| b["history"]["owner"] = json!("astrid"),
        "Question owner mismatch",
    );
    rejects(
        |b| {
            b["history"].as_object_mut().unwrap().remove("owner");
        },
        "Missing history owner",
    );
    rejects(
        |b| b["question_id"] = json!("q9223372036854775808"),
        "Invalid question identity",
    );
    rejects(
        |b| {
            b["history"]["records"][1]["request_id"] =
                b["history"]["records"][0]["request_id"].clone()
        },
        "operation identity",
    );
    rejects(
        |b| b["history"]["records"][0]["request_sha256"] = json!("x".repeat(64)),
        "operation identity",
    );
    rejects(
        |b| {
            b["history"]["records"][0]["request_id"] = json!("caf\u{00e9}");
            b["history"]["records"][1]["request_id"] = json!("cafe\u{0301}");
        },
        "operation identity",
    );
    let mut b = body("minime");
    b["history"]["records"][0]["id"] = json!("bad");
    let text = serde_json::to_string(&b).unwrap();
    assert!(GeometryPacket::decode(
        &serde_json::to_vec(
            &json!({"format":"question-geometry-v1","body_json":text,"body_sha256":hash(&text)})
        )
        .unwrap()
    )
    .is_err());
}
#[test]
fn source_vectors_clocks_and_bounds_reject_resealed_mutations() {
    for (key, value) in [
        ("scope", "recurrent_matrix_eigenvectors"),
        ("source", "/private/secret"),
        ("identity", "known-layout"),
        ("source_sha256", "invalid"),
    ] {
        rejects(
            |b| snapshot(b, |s| s[key] = json!(value)),
            "Unsupported source identity",
        );
    }
    rejects(
        |b| snapshot(b, |s| s["frames"] = json!([])),
        "Invalid interval limits",
    );
    rejects(
        |b| snapshot(b, |s| s["requested_seconds"] = json!(0)),
        "Invalid interval limits",
    );
    rejects(
        |b| snapshot(b, |s| s["frames"][0]["activations"] = json!(vec![0; 127])),
        "Invalid activation vector",
    );
    rejects(
        |b| snapshot(b, |s| s["frames"][0]["activations"] = json!(vec![2; 128])),
        "Invalid activation vector",
    );
    for key in ["t_ms", "wall_clock_unix_ms"] {
        rejects(
            |b| snapshot(b, |s| s["frames"][1][key] = s["frames"][0][key].clone()),
            "Duplicate or reversed recorder clock",
        );
    }
    rejects(
        |b| snapshot(b, |s| s["frames"][1]["t_ms"] = json!(10999)),
        "Duplicate or reversed recorder clock",
    );
    rejects(
        |b| snapshot(b, |s| s["requested_seconds"] = json!(1)),
        "Invalid capture clock or interval",
    );
    rejects(
        |b| snapshot(b, |s| s["captured_at_unix_ms"] = json!(0)),
        "Invalid capture clock or interval",
    );
    rejects(
        |b| {
            snapshot(b, |s| {
                s["captured_at_unix_ms"] = json!(1790000013000_u64 + 12001)
            })
        },
        "Invalid capture clock or interval",
    );
    rejects(
        |b| {
            snapshot(b, |s| {
                s["frames"].as_array_mut().unwrap().truncate(1);
            })
        },
        "Insufficient observations",
    );
    rejects(
        |b| {
            let first: Value =
                serde_json::from_str(b["history"]["records"][0]["body_json"].as_str().unwrap())
                    .unwrap();
            entry(b, 2, |e| e["snapshot"] = first["snapshot"].clone());
        },
        "Overlapping intervals or recorder restart",
    );
}
#[test]
fn references_rms_authored_text_and_extraneous_fields_are_checked() {
    rejects(
        |b| {
            b["history"]["records"].as_array_mut().unwrap().swap(1, 2);
        },
        "missing or misordered",
    );
    rejects(
        |b| entry(b, 1, |e| e["maximum_rms_distance"] = json!(3)),
        "Invalid prediction bound",
    );
    rejects(
        |b| entry(b, 1, |e| e["baseline"] = json!("unavailable")),
        "earlier baseline",
    );
    for (index, key, value) in [
        (1, "expectation", " \u{200b}".to_owned()),
        (0, "note", "x".repeat(2001)),
        (4, "text", String::new()),
    ] {
        rejects(
            |b| entry(b, index, |e| e[key] = json!(value)),
            "Invalid authored text length",
        );
    }
    for (key, value) in [
        ("rms_distance", json!(0)),
        ("threshold_met", json!(true)),
        ("recipe", json!("unverified")),
    ] {
        rejects(
            |b| entry(b, 3, |e| e[key] = value),
            "Comparison does not match",
        );
    }
    rejects(
        |b| entry(b, 3, |e| e["observation"] = e["prediction"].clone()),
        "missing or misordered",
    );
    rejects(
        |b| entry(b, 4, |e| e["target"] = json!("unavailable")),
        "Revision needs an earlier record",
    );
    for (index, key) in [
        (0, "text"),
        (1, "note"),
        (3, "note"),
        (4, "note"),
        (4, "future_field"),
        (1, "snapshot"),
        (3, "snapshot"),
        (4, "snapshot"),
    ] {
        rejects(
            |b| entry(b, index, |e| e[key] = Value::Null),
            "Invalid geometry JSON",
        );
    }
    rejects(
        |b| entry(b, 4, |e| e["kind"] = json!("unknown")),
        "Invalid geometry JSON",
    );
}
#[test]
fn upper_clock_and_packet_count_limits_are_exact() {
    let mut b = body("minime");
    b["history"]["records"].as_array_mut().unwrap().truncate(1);
    snapshot(&mut b, |s| {
        s["requested_seconds"] = json!(1);
        s["captured_at_unix_ms"] = json!(u64::MAX);
        s["frames"] = json!([
            {"t_ms":u64::MAX-1000,"wall_clock_unix_ms":u64::MAX-1000,"activations":vec![0.0;128]},
            {"t_ms":u64::MAX,"wall_clock_unix_ms":u64::MAX,"activations":vec![0.0;128]}
        ]);
    });
    let p = GeometryPacket::decode(&seal(b.clone())).unwrap();
    let GeometryEntry::Capture { snapshot, .. } = &p.records[0] else {
        panic!()
    };
    assert_eq!(snapshot.duration_ms(), 1000);
    assert!(snapshot.gaps().is_empty());
    let first = b["history"]["records"][0].clone();
    b["history"]["records"] = json!((0..5)
        .map(|i| {
            let mut r = first.clone();
            r["request_id"] = json!(format!("capture-{i}"));
            r
        })
        .collect::<Vec<_>>());
    assert!(GeometryPacket::decode(&seal(b))
        .unwrap_err()
        .to_string()
        .contains("Four frozen intervals"));
    rejects(
        |b| {
            let first = b["history"]["records"][0].clone();
            b["history"]["records"] = json!(vec![first; 65]);
        },
        "exceeds 64 records",
    );
}
