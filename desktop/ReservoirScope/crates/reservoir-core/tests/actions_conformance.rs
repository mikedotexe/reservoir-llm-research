//! Canonical retained Swift evidence and adversarial action-chain mutations.
//! Never starts a provider, follows a recorded path or writes canonical data.
use reservoir_core::{
    actions::{ActionComparisonRecord, JournalAction},
    CoreError,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::path::PathBuf;

fn example(name: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../../../essentials/examples")
        .join(name)
}
fn value(name: &str) -> Value {
    serde_json::from_slice(&std::fs::read(example(name)).unwrap()).unwrap()
}
fn record(value: Value) -> ActionComparisonRecord {
    serde_json::from_value(value).unwrap()
}
const CANONICAL: [&str; 22] = [
    "essentials-actions-feedback.json",
    "portable/example-component-1.json",
    "portable/example-component-2.json",
    "portable/example-component-3.json",
    "portable/example-component-4.json",
    "portable/example-component-5.json",
    "portable/example-component-6.json",
    "portable/example-component-7.json",
    "portable/example-component-8.json",
    "portable/example-model-4.json",
    "portable/example-model-5.json",
    "portable/example-model-6.json",
    "portable/example-model-7.json",
    "portable/example-model-8.json",
    "portable/example-model-observation.json",
    "portable/example-model-observation-active.json",
    "portable/example-observation-scripted.json",
    "portable/example-observation-active-scripted.json",
    "portable/example-preparation-1.json",
    "portable/example-preparation-2.json",
    "portable/example-preparation-3.json",
    "portable/example-preparation-4.json",
];
#[test]
fn all_22_retained_swift_action_records_verify() {
    for name in CANONICAL {
        let r = record(value(name));
        r.verify().unwrap_or_else(|error| panic!("{name}: {error}"));
        assert_eq!(
            r.checked_steps(),
            r.right.frames.len() + r.left.as_ref().map_or(0, |r| r.frames.len())
        );
        assert_eq!(
            r.checked_turns(),
            r.right.actions.len() + r.left.as_ref().map_or(0, |r| r.actions.len())
        );
    }
}
fn must_fail(name: &str, change: impl FnOnce(&mut Value)) {
    let mut v = value(name);
    change(&mut v);
    match serde_json::from_value::<ActionComparisonRecord>(v) {
        Err(_) => (),
        Ok(r) => assert!(
            matches!(r.verify(), Err(CoreError::Invalid(_))),
            "mutation accepted or misclassified: {name}"
        ),
    }
}
#[test]
fn action_numerical_and_saved_evidence_chain_rejects_tampering() {
    let name = "portable/example-model-6.json";
    must_fail(name, |v| {
        v["right"]["model"]["inputWeights"][0] = json!(9.0)
    });
    must_fail(name, |v| {
        v["right"]["frames"][0]["previousState"][0] = json!(0.4)
    });
    must_fail(name, |v| v["right"]["frames"][0]["state"][0] = json!(0.5));
    must_fail(name, |v| v["right"]["frames"][0]["noise"][0] = json!(0.1));
    must_fail(name, |v| {
        v["right"]["frames"][0]["spectral"]["eigenvectors"][0] = json!(2.0)
    });
    must_fail(name, |v| {
        v["right"]["frames"][30]["semanticActionID"] = json!(999)
    });
    must_fail(name, |v| {
        v["right"]["actions"][0]["prompt"] = json!("Invented observation")
    });
    must_fail(name, |v| {
        v["right"]["actions"][0]["applicationStep"] = json!(32)
    });
    must_fail(name, |v| {
        v["right"]["actions"][0]["encodedFeatures"][0] = json!(4.2)
    });
    must_fail(name, |v| {
        v["right"]["actions"][0]["semanticVector"][0] = json!(4.2)
    });
    must_fail(name, |v| {
        v["right"]["actions"][0]["saveReceipt"]["sha256"] = json!("wrong")
    });
    must_fail(name, |v| {
        v["right"]["actions"][0]["saveReceipt"]["relativePath"] = json!("../../private-file")
    });
    must_fail(name, |v| {
        v["right"]["journals"][0]["text"] = json!("Different saved words")
    });
    must_fail(name, |v| {
        v["right"]["actions"][1]["memoryText"] = json!("Not the saved journal")
    });
    must_fail(name, |v| {
        v["right"]["actions"][0]["rawReplyByteCount"] = json!(0)
    });
    must_fail(name, |v| {
        v["right"]["actions"][0]["providerComplete"] = json!(false)
    });
    must_fail(name, |v| {
        v["right"]["actions"][0]["stopReason"] = json!("length")
    });
    must_fail(name, |v| {
        v["right"]["actions"][0]["requestStarted"] = json!(false)
    });
    must_fail(name, |v| {
        v["right"]["actions"][0]
            .as_object_mut()
            .unwrap()
            .remove("rawReply");
    });
    must_fail("portable/example-model-8.json", |v| {
        v["right"]["frames"][0]["control"]["appliedRetention"] = json!(0.85)
    });
}
#[test]
fn comparison_tape_and_wait_constraints_reject_tampering() {
    must_fail("portable/example-component-8.json", |v| {
        v["tape"]["packets"][0]["text"] = json!("Changed tape text")
    });
    must_fail("portable/example-component-8.json", |v| {
        v["tape"]["packets"][0]["referenceEigenvalues"][0] = json!(5.0)
    });
    must_fail("portable/example-component-8.json", |v| {
        v["right"]["actions"][0]["tapePacketID"] = json!(1)
    });
    must_fail("portable/example-component-7.json", |v| {
        v["right"]["actions"][2]["applicationStep"] = json!(91)
    });
    must_fail("portable/example-model-observation.json", |v| {
        v["right"]["observationChannel"] = json!("sensory")
    });
    must_fail("portable/example-model-observation.json", |v| {
        v["right"]["actions"][1]["requestOrder"] = json!(2)
    });
    must_fail("portable/example-model-observation-active.json", |v| {
        v["format"] = json!("essentials-actions-v2")
    });
    must_fail("essentials-actions-feedback.json", |v| {
        v["right"]["observationChannel"] = json!("sensory")
    });
}
#[test]
fn required_structure_failure_gates_and_defaults_are_checked() {
    must_fail("portable/example-model-4.json", |v| {
        v["right"].as_object_mut().unwrap().remove("journals");
    });
    must_fail("portable/example-model-4.json", |v| {
        v["right"]["frames"][0]["spectral"] = Value::Null
    });
    must_fail("portable/example-model-4.json", |v| {
        v["specification"]["turnEvery"] = json!(0)
    });
    must_fail("portable/example-model-4.json", |v| {
        v["specification"]["seed"] = json!(18446744073709551615_u64)
    });
    must_fail("portable/example-preparation-3.json", |v| {
        v["right"]["actions"][0]["applicationStep"] = json!(31)
    });
    let mut legacy = value("essentials-actions-feedback.json");
    legacy["specification"]["forcingProfile"] = Value::Null;
    legacy["specification"]["comparisonKind"] = Value::Null;
    legacy["specification"]["promptVersion"] = Value::Null;
    record(legacy).verify().unwrap();
}
#[test]
fn unqualified_unicode_action_text_is_explicitly_incomplete() {
    let mut v = value("portable/example-preparation-4.json");
    let body = "A saved journal with \u{10ffff}.";
    let sha = format!("{:x}", Sha256::digest(body.as_bytes()));
    let step = v["right"]["actions"][0]["observedStep"].as_u64().unwrap();
    let id = format!("journal-{step}-1-{sha}");
    let raw =
        serde_json::to_string(&json!({"action":JournalAction::WriteJournal,"text":body})).unwrap();
    let a = &mut v["right"]["actions"][0];
    a["rawReply"] = json!(raw);
    a["rawReplyByteCount"] = json!(raw.len());
    a["journalEntryID"] = json!(id);
    a["saveReceipt"]["entryID"] = json!(id);
    a["saveReceipt"]["sha256"] = json!(sha);
    a["saveReceipt"]["relativePath"] = json!(format!("right/{id}.json"));
    let j = &mut v["right"]["journals"][0];
    j["id"] = json!(id);
    j["text"] = json!(body);
    j["sha256"] = json!(sha);
    assert!(matches!(record(v).verify(), Err(CoreError::Unsupported(_))));
}

#[test]
fn native_parser_differences_cannot_certify_a_false_response_failure() {
    // Observed with the local Foundation JSONDecoder: duplicate fields use the
    // first value, and trailing commas and a UTF-8 BOM are accepted. The portable
    // verifier keeps these forms incomplete rather than accepting a claimed
    // responseValidation failure merely because serde rejects them.
    for raw in [
        r#"{"action":"WRITE_JOURNAL","action":"WAIT","text":"words"}"#,
        r#"{"action":"WRITE_JOURNAL","text":"words",}"#,
        "\u{feff}{\"action\":\"WRITE_JOURNAL\",\"text\":\"words\"}",
    ] {
        let mut v = value("portable/example-preparation-2.json");
        v["right"]["actions"][0]["rawReply"] = json!(raw);
        v["right"]["actions"][0]["rawReplyByteCount"] = json!(raw.len());
        assert!(
            matches!(record(v).verify(), Err(CoreError::Unsupported(_))),
            "Unqualified parser case received a verdict: {raw}"
        );
    }
    // The retained native Foundation whitespace table now qualifies these
    // invalid WRITE_JOURNAL envelopes; a recorded response failure is truthful.
    for text in ["\u{0085}", "\u{200b}", "\u{00a0}"] {
        let raw = serde_json::to_string(&json!({"action":"WRITE_JOURNAL", "text":text})).unwrap();
        let mut v = value("portable/example-preparation-2.json");
        v["right"]["actions"][0]["rawReply"] = json!(raw);
        v["right"]["actions"][0]["rawReplyByteCount"] = json!(raw.len());
        record(v).verify().unwrap();
    }
    must_fail("portable/example-preparation-2.json", |v| {
        let raw = r#"{"action":"WRITE_JOURNAL","text":"words"}"#;
        v["right"]["actions"][0]["rawReply"] = json!(raw);
        v["right"]["actions"][0]["rawReplyByteCount"] = json!(raw.len());
    });
}

#[test]
fn terminal_cancellation_manual_actions_and_language_defaults_are_explicit() {
    let mut cancelled = value("portable/example-preparation-1.json");
    cancelled["status"] = json!("stopped");
    cancelled["failure"] = Value::Null;
    cancelled["right"]["status"] = json!("stopped");
    cancelled["right"]["failure"] = Value::Null;
    let a = &mut cancelled["right"]["actions"][0];
    a["status"] = json!("cancelled");
    a["failurePhase"] = json!("cancelled");
    a["requestStarted"] = json!(false);
    a["requestOrder"] = Value::Null;
    record(cancelled.clone()).verify().unwrap();
    cancelled["right"]["actions"][0]["rawReply"] = json!("late reply");
    assert!(matches!(
        record(cancelled).verify(),
        Err(CoreError::Invalid(_))
    ));

    // Derive a finite stopped single-arm record from canonical numerical
    // evidence. A manual G action must force a journal even though scheduled G
    // actions can choose WAIT. This is a verifier test, not a runner export.
    let mut manual = value("portable/example-model-7.json");
    manual["left"] = Value::Null;
    manual["specification"]["comparePrevious"] = json!(false);
    manual["specification"]["turnEvery"] = json!(31);
    manual["status"] = json!("stopped");
    manual["right"]["status"] = json!("stopped");
    manual["right"]["frames"]
        .as_array_mut()
        .unwrap()
        .truncate(31);
    manual["right"]["journals"]
        .as_array_mut()
        .unwrap()
        .truncate(1);
    manual["right"]["actions"]
        .as_array_mut()
        .unwrap()
        .truncate(1);
    let a = &mut manual["right"]["actions"][0];
    a["trigger"] = json!("manual");
    a["requestOrder"] = json!(1);
    a["requestedAction"] = json!("WRITE_JOURNAL");
    a["prompt"] = json!(a["prompt"].as_str().unwrap().replace(
        "Choose WRITE_JOURNAL or WAIT.",
        "The requested action is WRITE_JOURNAL."
    ));
    record(manual.clone()).verify().unwrap();
    manual["right"]["actions"][0]["requestedAction"] = Value::Null;
    assert!(matches!(
        record(manual).verify(),
        Err(CoreError::Invalid(_))
    ));

    let mut legacy = value("essentials-actions-feedback.json");
    legacy["specification"]
        .as_object_mut()
        .unwrap()
        .remove("language");
    record(legacy.clone()).verify().unwrap();
    legacy["specification"]["language"] = Value::Null;
    record(legacy.clone()).verify().unwrap();
    legacy["specification"]["language"] = json!({});
    assert!(serde_json::from_value::<ActionComparisonRecord>(legacy).is_err());
}

#[test]
fn failed_save_has_no_feedback_and_prevents_the_paired_action() {
    let mut v = value("portable/example-component-5.json");
    for arm in ["left", "right"] {
        v[arm]["frames"].as_array_mut().unwrap().truncate(30);
        v[arm]["actions"].as_array_mut().unwrap().truncate(1);
        v[arm]["journals"].as_array_mut().unwrap().clear();
    }
    v["status"] = json!("failed");
    v["failure"] = json!("Offline test: save failed");
    v["left"]["status"] = json!("failed");
    v["left"]["failure"] = v["failure"].clone();
    v["right"]["status"] = json!("stopped");
    let a = &mut v["left"]["actions"][0];
    a["failure"] = json!("Offline test: save failed");
    a["failurePhase"] = json!("journalSave");
    a["saveReceipt"]["status"] = json!("failed");
    a["saveReceipt"]["failure"] = a["failure"].clone();
    a["saveReceipt"]["relativePath"] = Value::Null;
    a["encodedFeatures"] = Value::Null;
    a["semanticVector"] = Value::Null;
    a["applicationStep"] = Value::Null;
    let a = &mut v["right"]["actions"][0];
    a["status"] = json!("cancelled");
    a["failure"] = json!("Paired action stopped before this request started.");
    a["failurePhase"] = json!("cancelled");
    for key in [
        "rawReply",
        "rawReplyByteCount",
        "chosenAction",
        "providerModel",
        "stopReason",
        "tokenCount",
        "providerComplete",
        "journalEntryID",
        "saveReceipt",
        "encodedFeatures",
        "semanticVector",
        "applicationStep",
    ] {
        a[key] = Value::Null;
    }
    record(v.clone()).verify().unwrap();
    let mut applied = v.clone();
    applied["left"]["actions"][0]["applicationStep"] = json!(31);
    assert!(matches!(
        record(applied).verify(),
        Err(CoreError::Invalid(_))
    ));

    // Individually valid right-side completion cannot hide the preceding left
    // save failure. Both arms must retain the same interrupted opportunity.
    let original = value("portable/example-component-5.json");
    v["right"]["actions"][0] = original["right"]["actions"][0].clone();
    v["right"]["actions"][0]["applicationStep"] = Value::Null;
    v["right"]["journals"] = json!([original["right"]["journals"][0].clone()]);
    assert!(matches!(record(v).verify(), Err(CoreError::Invalid(_))));
}
