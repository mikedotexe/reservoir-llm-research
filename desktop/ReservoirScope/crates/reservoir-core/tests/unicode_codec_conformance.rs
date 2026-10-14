use reservoir_core::{codec, CoreError};
use serde_json::Value;

#[test]
fn retained_native_unicode_vectors_match_without_relaxing_tolerance() {
    let oracle: Value =
        serde_json::from_str(include_str!("fixtures/unicode-codec-v1.json")).unwrap();
    let mut accepted = 0;
    let mut incomplete = 0;
    let mut mismatches = Vec::new();
    for (case, row) in oracle["vectors"].as_array().unwrap().iter().enumerate() {
        let text = row["text"].as_str().unwrap();
        match codec::encode(text) {
            Ok(actual) => {
                accepted += 1;
                let native_nonempty = row["features"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .any(|v| v.as_f64().unwrap() != 0.0);
                assert_eq!(codec::has_non_whitespace(text).unwrap(), native_nonempty);
                for (index, expected) in row["features"].as_array().unwrap().iter().enumerate() {
                    let difference = (actual[index] - expected.as_f64().unwrap()).abs();
                    if difference > 1e-12 {
                        mismatches.push(format!(
                            "case {case} feature {index} difference {difference}: {text:?}"
                        ));
                    }
                }
                assert!(actual[32..].iter().all(|v| *v == 0.0));
            }
            Err(CoreError::Unsupported(_)) => incomplete += 1,
            Err(e) => panic!("unexpected codec error {e}"),
        }
    }
    println!(
        "native Unicode corpus: {accepted} matched/admitted, {incomplete} explicitly incomplete"
    );
    assert!(
        mismatches.is_empty(),
        "{}",
        mismatches
            .iter()
            .take(25)
            .cloned()
            .collect::<Vec<_>>()
            .join("\n")
    );
    assert_eq!(
        accepted, 1124,
        "Unicode admission boundary changed; requalify it explicitly"
    );
    assert_eq!(
        incomplete, 23,
        "corpus deliberately includes unqualified combining sequences"
    );
}

#[test]
fn unicode_boundary_and_foundation_whitespace_remain_explicit() {
    for text in [
        "é e\u{301}",
        "İ I i ı i\u{307}",
        "ΟΣ ΟΣΑ",
        "Привет",
        "中文 日本語",
        "한글",
        "👩🏽‍💻",
        "🇺🇸",
        "1️⃣",
        "क्ष",
    ] {
        assert!(codec::encode(text).is_ok(), "{text:?}");
    }
    for text in ["\u{10ffff}", "a\u{301}\u{308}\u{30b}", "🧑‍🚀"] {
        assert!(
            matches!(codec::encode(text), Err(CoreError::Unsupported(_))),
            "{text:?}"
        );
    }
    for text in ["\u{200b}", "\u{0085}\u{00a0}", "\r\n"] {
        assert_eq!(codec::encode(text).unwrap(), vec![0.0; 48]);
        assert!(!codec::has_non_whitespace(text).unwrap());
    }
    assert!(codec::has_non_whitespace("\u{001c}").unwrap());
    assert!(codec::has_non_whitespace("\u{00ad}").unwrap());
}

#[test]
fn unicode_oracle_is_bound_to_unchanged_native_source() {
    use sha2::{Digest, Sha256};
    let oracle: Value =
        serde_json::from_str(include_str!("fixtures/unicode-codec-v1.json")).unwrap();
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../..");
    let source = root.join(oracle["source"]["path"].as_str().unwrap());
    assert_eq!(
        format!("{:x}", Sha256::digest(std::fs::read(source).unwrap())),
        oracle["source"]["sha256"]
    );
    assert_eq!(oracle["scalarCount"], 44206);
    assert_eq!(oracle["clusters"].as_array().unwrap().len(), 21);
}
