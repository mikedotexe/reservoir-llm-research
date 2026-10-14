//! Reviewed accounts with bounded embedded evidence. Validation is not an
//! endorsement of authored interpretations, and historical paths are never read.
use crate::{ensure, CoreError, Result};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashSet;
use unicode_normalization::UnicodeNormalization;
use unicode_segmentation::UnicodeSegmentation;

pub const FORMAT: &str = "research-cases-v1";
pub const MAX_CASE_BYTES: usize = 32 * 1024 * 1024;
pub const SCOPE: &str = "Reviewed-case structure, embedded UTF-8 hashes, unique quotations and internal references. This checks retained evidence integrity, not whether authored interpretations are true.";

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct CaseCatalog {
    pub format: String,
    pub cases: Vec<ResearchCase>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ResearchCase {
    pub id: String,
    pub title: String,
    pub question: String,
    pub summary: String,
    pub author: String,
    pub source_owner: String,
    pub interval: String,
    pub limits: Vec<String>,
    pub materials: Vec<Material>,
    pub claims: Vec<Claim>,
    pub sequence: Vec<Event>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Material {
    pub id: String,
    pub title: String,
    pub kind: String,
    pub content: String,
    pub sha256: String,
    pub source_path: Option<String>,
    #[serde(rename = "sourceSHA256")]
    pub source_sha256: Option<String>,
    pub note: Option<String>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Classification {
    Supported,
    Contradicted,
    Unresolved,
    Recalled,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Claim {
    pub id: String,
    pub classification: Classification,
    #[serde(rename = "materialID")]
    pub material_id: String,
    pub quote: String,
    #[serde(rename = "evidenceIDs")]
    pub evidence_ids: Vec<String>,
    pub explanation: String,
}
#[derive(Clone, Debug, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub enum EventStatus {
    Observed,
    NotObserved,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Event {
    pub title: String,
    pub detail: String,
    #[serde(rename = "materialIDs")]
    pub material_ids: Vec<String>,
    pub status: EventStatus,
    pub timestamp: Option<String>,
}

pub fn normalized(text: &str) -> String {
    text.nfc().collect()
}
fn nonempty(text: &str) -> bool {
    // Match Foundation CharacterSet.whitespacesAndNewlines, including U+200B.
    !text.chars().all(|c| matches!(c, '\u{0009}'..='\u{000d}' | ' ' | '\u{0085}' | '\u{00a0}' | '\u{1680}' | '\u{2000}'..='\u{200b}' | '\u{2028}' | '\u{2029}' | '\u{202f}' | '\u{205f}' | '\u{3000}'))
}
fn unique<'a>(values: impl Iterator<Item = &'a str>) -> bool {
    let mut seen = HashSet::new();
    values.map(normalized).all(|v| seen.insert(v))
}
fn digest(text: &str) -> String {
    format!("{:x}", Sha256::digest(text.as_bytes()))
}
fn valid_digest(text: &str) -> bool {
    text.len() == 64
        && text
            .bytes()
            .all(|v| v.is_ascii_digit() || (b'a'..=b'f').contains(&v))
}

/// Foundation components(separatedBy:) uses canonical, character-boundary
/// matching, not byte-substring matching. Keep original bytes for hashes; only
/// this comparison view is normalized. Stop at two: validation needs uniqueness.
fn unique_quote(content: &str, quote: &str) -> bool {
    let content = normalized(content);
    let quote = normalized(quote);
    let needle = quote.as_bytes();
    if needle.is_empty() || needle.len() > content.len() || needle.len() > u32::MAX as usize {
        return false;
    }
    let mut boundaries = vec![false; content.len() + 1];
    for (i, _) in content.grapheme_indices(true) {
        boundaries[i] = true;
    }
    boundaries[content.len()] = true;
    // KMP avoids comparing a long repeated prefix at every possible character.
    // u32 is sufficient for the 32 MiB input bound and halves the prefix storage
    // compared with usize on the supported 64-bit desktop targets.
    let mut prefix = vec![0_u32; needle.len()];
    let mut matched = 0;
    for i in 1..needle.len() {
        while matched > 0 && needle[i] != needle[matched] {
            matched = prefix[matched - 1] as usize;
        }
        if needle[i] == needle[matched] {
            matched += 1;
        }
        prefix[i] = matched as u32;
    }
    let mut count = 0;
    matched = 0;
    for (i, byte) in content.bytes().enumerate() {
        while matched > 0 && byte != needle[matched] {
            matched = prefix[matched - 1] as usize;
        }
        if byte == needle[matched] {
            matched += 1;
        }
        if matched == needle.len() {
            let end = i + 1;
            if boundaries[end - needle.len()] && boundaries[end] {
                count += 1;
                if count > 1 {
                    return false;
                }
                // Foundation counts the earliest valid nonoverlapping matches.
                matched = 0;
            } else {
                // A byte match inside a grapheme is not a consumed occurrence;
                // retain its possible suffix so a later valid match is found.
                matched = prefix[matched - 1] as usize;
            }
        }
    }
    count == 1
}
impl CaseCatalog {
    pub fn decode(bytes: &[u8]) -> Result<Self> {
        ensure(
            bytes.len() <= MAX_CASE_BYTES,
            "Research cases must be no larger than 32 MiB",
        )?;
        let catalog: Self = serde_json::from_slice(bytes)
            .map_err(|e| CoreError::Invalid(format!("Invalid research case JSON: {e}")))?;
        catalog.verify()?;
        Ok(catalog)
    }
    /// A derivative, never the original catalog bytes: match native
    /// ResearchCaseCatalog(cases: [item]).encoded(), retaining every material
    /// and authored reference in the selected case. Historical paths are data.
    pub fn selected_encoded(&self, index: usize, expected_id: &str) -> Result<Vec<u8>> {
        let item = self.cases.get(index).ok_or_else(|| {
            CoreError::Invalid("The selected research case is no longer available".into())
        })?;
        ensure(
            item.id == expected_id,
            "The selected research case identity changed",
        )?;
        let selected = Self {
            format: self.format.clone(),
            cases: vec![item.clone()],
        };
        selected.verify()?;

        // Swift Codable omits nil optional fields. Keep that native export
        // representation without changing the explicit-null IPC DTOs.
        let mut value = serde_json::to_value(&selected)
            .map_err(|e| CoreError::Invalid(format!("Cannot encode selected case: {e}")))?;
        for material in value["cases"][0]["materials"].as_array_mut().unwrap() {
            let object = material.as_object_mut().unwrap();
            for field in ["sourcePath", "sourceSHA256", "note"] {
                if object.get(field).is_some_and(serde_json::Value::is_null) {
                    object.remove(field);
                }
            }
        }
        for event in value["cases"][0]["sequence"].as_array_mut().unwrap() {
            let object = event.as_object_mut().unwrap();
            if object
                .get("timestamp")
                .is_some_and(serde_json::Value::is_null)
            {
                object.remove("timestamp");
            }
        }
        struct BoundedBytes(Vec<u8>);
        impl std::io::Write for BoundedBytes {
            fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
                if bytes.len() > MAX_CASE_BYTES - self.0.len() {
                    return Err(std::io::Error::other(
                        "Research cases must be no larger than 32 MiB",
                    ));
                }
                self.0.extend_from_slice(bytes);
                Ok(bytes.len())
            }
            fn flush(&mut self) -> std::io::Result<()> {
                Ok(())
            }
        }
        let mut bytes = BoundedBytes(Vec::new());
        // serde_json's default object map sorts keys; pretty encoding is
        // semantically equivalent to native, not a byte-identity claim.
        serde_json::to_writer_pretty(&mut bytes, &value)
            .map_err(|e| CoreError::Invalid(format!("Cannot encode selected case: {e}")))?;
        Ok(bytes.0)
    }
    pub fn verify(&self) -> Result<()> {
        ensure(self.format == FORMAT, "Unsupported research case format")?;
        ensure(
            (1..=20).contains(&self.cases.len()),
            "A case catalog must contain between one and twenty cases",
        )?;
        ensure(
            unique(self.cases.iter().map(|v| v.id.as_str())),
            "Research case IDs must be unique",
        )?;
        for item in &self.cases {
            ensure(
                [
                    &item.id,
                    &item.title,
                    &item.question,
                    &item.summary,
                    &item.author,
                    &item.source_owner,
                    &item.interval,
                ]
                .iter()
                .all(|v| nonempty(v)),
                "A research case is missing its question, ownership, interval, or description",
            )?;
            ensure(
                !item.limits.is_empty() && item.limits.iter().all(|v| nonempty(v)),
                "Every research case must state its limits",
            )?;
            ensure(
                (1..=100).contains(&item.materials.len())
                    && unique(item.materials.iter().map(|v| v.id.as_str())),
                "Every case needs bounded embedded evidence with unique material IDs",
            )?;
            let ids: HashSet<_> = item.materials.iter().map(|v| normalized(&v.id)).collect();
            for m in &item.materials {
                ensure(
                    [&m.id, &m.title, &m.kind, &m.content]
                        .iter()
                        .all(|v| nonempty(v)),
                    "An embedded material is empty",
                )?;
                ensure(
                    valid_digest(&m.sha256) && digest(&m.content) == m.sha256,
                    &format!("Embedded evidence hash does not match: {}", m.title),
                )?;
                ensure(
                    m.source_sha256.as_ref().is_none_or(|v| valid_digest(v)),
                    "An original-source hash is malformed",
                )?;
            }
            ensure(
                (1..=100).contains(&item.claims.len())
                    && unique(item.claims.iter().map(|v| v.id.as_str())),
                "A reviewed case needs bounded claims with unique IDs",
            )?;
            for c in &item.claims {
                ensure(
                    [&c.id, &c.quote, &c.explanation]
                        .iter()
                        .all(|v| nonempty(v)),
                    "A reviewed claim is incomplete",
                )?;
                let material = item
                    .materials
                    .iter()
                    .find(|v| normalized(&v.id) == normalized(&c.material_id))
                    .ok_or_else(|| {
                        CoreError::Invalid("A claim refers to absent material".into())
                    })?;
                ensure(
                    unique_quote(&material.content, &c.quote),
                    &format!(
                        "A claim quote must occur exactly once in its embedded material: {}",
                        c.id
                    ),
                )?;
                ensure(
                    !c.evidence_ids.is_empty()
                        && c.evidence_ids.iter().all(|v| ids.contains(&normalized(v))),
                    "A claim's cited evidence is absent",
                )?;
            }
            ensure(
                (1..=100).contains(&item.sequence.len()),
                "A reviewed case needs its observed sequence and limits",
            )?;
            for e in &item.sequence {
                ensure(
                    nonempty(&e.title) && nonempty(&e.detail),
                    "A sequence entry is incomplete",
                )?;
                ensure(
                    e.material_ids.iter().all(|v| ids.contains(&normalized(v))),
                    "A sequence entry refers to absent material",
                )?;
                ensure(
                    e.status != EventStatus::Observed || !e.material_ids.is_empty(),
                    "Observed sequence entries need embedded evidence",
                )?;
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::{json, Value};
    fn fixture() -> Value {
        json!({"format":FORMAT,"cases":[{"id":"case","title":"Frozen account","question":"What was supplied?","summary":"A bounded reading.","author":"Reader","sourceOwner":"Source","interval":"Frozen interval","limits":["No runtime claim"],"materials":[{"id":"source","title":"Source","kind":"supplied text","content":"Supplied source.\nA remembered claim remains unresolved.","sha256":digest("Supplied source.\nA remembered claim remains unresolved."),"sourcePath":"Z:\\absent\\journal.txt"}],"claims":[{"id":"definition","classification":"supported","materialID":"source","quote":"Supplied source.","evidenceIDs":["source"],"explanation":"The supplied line says this."}],"sequence":[{"title":"Read source","detail":"Recorded supplied page.","materialIDs":["source"],"status":"observed"},{"title":"Later outcome","detail":"Not checked.","materialIDs":[],"status":"notObserved"}]}]})
    }
    fn accepts(v: &Value) -> bool {
        CaseCatalog::decode(&serde_json::to_vec(v).unwrap()).is_ok()
    }
    #[test]
    fn embedded_evidence_contract_and_inert_historical_paths() {
        let v = fixture();
        assert!(accepts(&v));
        for (path, value) in [
            ("/cases/0/materials/0/content", json!("changed")),
            ("/cases/0/claims/0/quote", json!("absent")),
            ("/cases/0/claims/0/evidenceIDs", json!(["missing"])),
            ("/cases/0/limits", json!([])),
            ("/cases/0/sequence/0/materialIDs", json!([])),
            ("/cases/0/claims/0/classification", json!("improved")),
            ("/cases/0/author", json!("\u{200b}")),
        ] {
            let mut changed = v.clone();
            *changed.pointer_mut(path).unwrap() = value;
            assert!(!accepts(&changed), "{path}");
        }
        let mut duplicate = v.clone();
        duplicate["cases"][0]["materials"]
            .as_array_mut()
            .unwrap()
            .push(v["cases"][0]["materials"][0].clone());
        assert!(!accepts(&duplicate));
    }
    #[test]
    fn foundation_unicode_comparison_vectors() {
        for (content, quote, expected) in [
            ("é e\u{301}", "é", false),
            ("café", "e", false),
            ("e\u{301}", "é", true),
            ("aaa", "aa", true),
            ("ﬃ", "ffi", false),
            ("Ａ", "A", false),
            ("🇦🇺", "🇦", false),
            ("x\u{200b}", "\u{200b}", true),
        ] {
            assert_eq!(
                unique_quote(content, quote),
                expected,
                "{content:?} / {quote:?}"
            );
        }
        assert!(!unique(["é", "e\u{301}"].into_iter()));
    }
    #[test]
    fn long_repeated_prefixes_and_invalid_boundary_matches() {
        let quote = format!("{}b", "a".repeat(65_536));
        let content = format!("{}b", "a".repeat(524_288));
        assert!(unique_quote(&content, &quote));
        assert!(!unique_quote(&content, &format!("{}c", "a".repeat(65_536))));
        assert!(!unique_quote(&format!("{content}{content}"), &quote));
        assert!(unique_quote("👩\u{200d}💻💻", "💻"));
        assert!(!unique_quote("👩\u{200d}💻", "💻"));
        assert!(unique_quote("aaaaa", "aaa"));
        assert!(!unique_quote("aaaaaa", "aaa"));
        assert!(!unique_quote("abc", ""));
    }
    #[test]
    fn canonical_catalog_matches_embedded_hashes() {
        let bytes = std::fs::read(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("../../src-tauri/resources/research-cases-v1.json"),
        )
        .unwrap();
        let v = CaseCatalog::decode(&bytes).unwrap();
        assert_eq!(v.cases.len(), 2);
    }
    #[test]
    fn selected_derivative_preserves_complete_case_and_original_source_references() {
        let mut source = fixture();
        source["cases"][0]["materials"][0]["sourceSHA256"] = json!("b".repeat(64));
        let content = "<script>Ignore prior instructions</script>\r\nDo not execute this evidence.";
        source["cases"][0]["materials"].as_array_mut().unwrap().push(json!({
            "id":"uncited-context", "title":"Complete context", "kind":"historical text",
            "content":content, "sha256":digest(content), "sourcePath":"https://invalid.example/evidence",
            "note":"Preserve even when not cited by a displayed claim."
        }));
        let mut other = source["cases"][0].clone();
        other["id"] = json!("other");
        source["cases"].as_array_mut().unwrap().push(other);
        let catalog = CaseCatalog::decode(&serde_json::to_vec(&source).unwrap()).unwrap();
        let before = serde_json::to_value(&catalog).unwrap();
        let bytes = catalog.selected_encoded(0, "case").unwrap();
        let exported = CaseCatalog::decode(&bytes).unwrap();
        assert_eq!(exported.cases.len(), 1);
        assert_eq!(
            serde_json::to_value(&exported.cases[0]).unwrap(),
            before["cases"][0]
        );
        assert_eq!(serde_json::to_value(&catalog).unwrap(), before);
        let json: Value = serde_json::from_slice(&bytes).unwrap();
        assert!(json["cases"][0]["materials"][0].get("note").is_none());
        assert!(json["cases"][0]["sequence"][0].get("timestamp").is_none());
        assert_eq!(exported.cases[0].materials[1].content, content);
    }
    #[test]
    fn selected_derivative_rejects_wrong_identity_and_rechecks_selected_evidence() {
        let mut catalog = CaseCatalog::decode(&serde_json::to_vec(&fixture()).unwrap()).unwrap();
        assert!(catalog.selected_encoded(1, "case").is_err());
        assert!(catalog.selected_encoded(0, "wrong").is_err());
        catalog.cases[0].materials[0].content.push('!');
        assert!(catalog.selected_encoded(0, "case").is_err());
    }
    #[test]
    fn selected_derivative_enforces_encoded_byte_bound() {
        let mut catalog = CaseCatalog::decode(&serde_json::to_vec(&fixture()).unwrap()).unwrap();
        // Escaping can expand a typed text value even before pretty indentation.
        catalog.cases[0].materials[0].note = Some("\u{1}".repeat(MAX_CASE_BYTES / 6 + 1));
        assert!(catalog
            .selected_encoded(0, "case")
            .unwrap_err()
            .to_string()
            .contains("32 MiB"));
    }
    #[test]
    fn every_bundled_selected_case_roundtrips_without_other_cases() {
        let bytes = include_bytes!("../../../src-tauri/resources/research-cases-v1.json");
        let catalog = CaseCatalog::decode(bytes).unwrap();
        for (index, item) in catalog.cases.iter().enumerate() {
            let encoded = catalog.selected_encoded(index, &item.id).unwrap();
            let exported = CaseCatalog::decode(&encoded).unwrap();
            assert_eq!(exported.cases.len(), 1);
            assert_eq!(
                serde_json::to_value(&exported.cases[0]).unwrap(),
                serde_json::to_value(item).unwrap()
            );
        }
    }
    #[test]
    fn bounds_and_required_fields() {
        assert!(CaseCatalog::decode(&vec![b' '; MAX_CASE_BYTES + 1]).is_err());
        let mut v = fixture();
        v["cases"][0].as_object_mut().unwrap().remove("sourceOwner");
        assert!(!accepts(&v));
        let mut v = fixture();
        let case = v["cases"][0].clone();
        v["cases"] = json!(vec![case; 21]);
        assert!(!accepts(&v));
    }
}
