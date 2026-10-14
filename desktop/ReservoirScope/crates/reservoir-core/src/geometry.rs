//! Bounded, offline `question-geometry-v1` packets. Paths are labels only.
//! Hashes establish internal consistency, not producer authenticity or novelty.
use crate::{ensure, CoreError, Result};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet};
use unicode_normalization::UnicodeNormalization;

pub const FORMAT: &str = "question-geometry-v1";
pub const MAX_PACKET_BYTES: usize = 4 * 1024 * 1024;
pub const SCOPE: &str = "Geometry packet body/chain hashes, ordered references, bounded 128-coordinate snapshots, clocks and mean-state RMS comparisons; no producer authenticity, boot/layout identity, historical novelty, causality or experience claim";

#[derive(Clone, Debug, Deserialize)]
struct Envelope {
    format: String,
    body_sha256: String,
    body_json: String,
}
#[derive(Clone, Debug)]
pub struct GeometryPacket {
    pub body: GeometryBody,
    pub digest: String,
    pub records: Vec<GeometryEntry>,
}
#[derive(Clone, Debug, Deserialize)]
pub struct GeometryBody {
    pub format: String,
    pub owner: String,
    pub question_id: String,
    pub question: String,
    pub history: GeometryHistory,
    pub limits: String,
}
#[derive(Clone, Debug, Deserialize)]
pub struct GeometryHistory {
    pub owner: Option<String>,
    pub records: Vec<GeometryRecord>,
}
#[derive(Clone, Debug, Deserialize)]
pub struct GeometryRecord {
    pub id: String,
    pub previous: String,
    pub request_id: String,
    pub request_sha256: String,
    pub body_json: String,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(tag = "kind", rename_all = "lowercase", deny_unknown_fields)]
pub enum GeometryEntry {
    Capture {
        snapshot: GeometrySnapshot,
        note: String,
    },
    Prediction {
        baseline: String,
        maximum_rms_distance: f64,
        expectation: String,
    },
    Comparison {
        prediction: String,
        observation: String,
        recipe: String,
        rms_distance: f64,
        threshold_met: bool,
    },
    Revision {
        target: String,
        text: String,
    },
}
impl GeometryEntry {
    pub fn kind(&self) -> &'static str {
        match self {
            Self::Capture { .. } => "capture",
            Self::Prediction { .. } => "prediction",
            Self::Comparison { .. } => "comparison",
            Self::Revision { .. } => "revision",
        }
    }
    pub fn authored_text(&self) -> Option<&str> {
        match self {
            Self::Capture { note, .. } => Some(note),
            Self::Prediction { expectation, .. } => Some(expectation),
            Self::Revision { text, .. } => Some(text),
            Self::Comparison { .. } => None,
        }
    }
}
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct GeometryFrame {
    pub t_ms: u64,
    pub wall_clock_unix_ms: u64,
    pub activations: Vec<f64>,
}
impl GeometryFrame {
    pub fn rms(&self) -> Result<f64> {
        validate_vector(&self.activations)?;
        Ok((self.activations.iter().map(|x| x * x).sum::<f64>() / 128.0).sqrt())
    }
}
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct GeometrySnapshot {
    pub source_sha256: String,
    pub captured_at_unix_ms: u64,
    pub requested_seconds: u64,
    pub source: String,
    pub scope: String,
    pub identity: String,
    pub frames: Vec<GeometryFrame>,
}
impl GeometrySnapshot {
    pub fn duration_ms(&self) -> u64 {
        self.frames
            .first()
            .zip(self.frames.last())
            .map_or(0, |(first, last)| last.t_ms.saturating_sub(first.t_ms))
    }
    pub fn gaps(&self) -> Vec<(u64, u64)> {
        self.frames
            .windows(2)
            .filter(|p| p[1].t_ms.saturating_sub(p[0].t_ms) > 1000)
            .map(|p| (p[0].t_ms, p[1].t_ms))
            .collect()
    }
    pub fn validate(&self) -> Result<()> {
        ensure(
            self.scope == "native_esn_128_activations"
                && self.identity == "boot_and_node_layout_unverified"
                && self.source == "minime/workspace/runtime/esn_activation_trace_v1.json"
                && is_hash(&self.source_sha256),
            "Unsupported source identity",
        )?;
        ensure(
            (1..=60).contains(&self.requested_seconds) && (1..=61).contains(&self.frames.len()),
            "Invalid interval limits",
        )?;
        for f in &self.frames {
            validate_vector(&f.activations)?;
        }
        for p in self.frames.windows(2) {
            ensure(
                p[1].t_ms > p[0].t_ms
                    && p[1].t_ms - p[0].t_ms >= 1000
                    && p[1].wall_clock_unix_ms > p[0].wall_clock_unix_ms,
                "Duplicate or reversed recorder clock",
            )?;
        }
        let last = self.frames.last().expect("nonempty bounded frames checked");
        ensure(
            self.duration_ms() <= self.requested_seconds * 1000
                && self.captured_at_unix_ms >= last.wall_clock_unix_ms
                && self.captured_at_unix_ms - last.wall_clock_unix_ms <= 12_000,
            "Invalid capture clock or interval",
        )
    }
    pub fn mean(&self) -> Result<Vec<f64>> {
        self.validate()?;
        Ok((0..128)
            .map(|n| {
                self.frames.iter().map(|f| f.activations[n]).sum::<f64>() / self.frames.len() as f64
            })
            .collect())
    }
    pub fn distance(baseline: &Self, observation: &Self) -> Result<f64> {
        baseline.validate()?;
        observation.validate()?;
        ensure(
            baseline.frames.len() >= 2 && observation.frames.len() >= 2,
            "Insufficient observations",
        )?;
        let last = baseline.frames.last().expect("validated nonempty frames");
        let first = &observation.frames[0];
        ensure(
            first.wall_clock_unix_ms > last.wall_clock_unix_ms && first.t_ms > last.t_ms,
            "Overlapping intervals or recorder restart",
        )?;
        let sum = baseline
            .mean()?
            .iter()
            .zip(observation.mean()?)
            .map(|(a, b)| (a - b).powi(2))
            .sum::<f64>();
        Ok((sum / 128.0).sqrt())
    }
}
impl GeometryPacket {
    pub fn decode(bytes: &[u8]) -> Result<Self> {
        ensure(
            !bytes.is_empty() && bytes.len() <= MAX_PACKET_BYTES,
            "Packet must be at most 4 MiB",
        )?;
        let envelope: Envelope = decode(bytes)?;
        ensure(
            envelope.format == FORMAT && hash(&envelope.body_json) == envelope.body_sha256,
            "Unsupported packet or changed body bytes",
        )?;
        let body: GeometryBody = decode(envelope.body_json.as_bytes())?;
        ensure(
            body.format == FORMAT && matches!(body.owner.as_str(), "astrid" | "minime"),
            "Unknown geometry owner",
        )?;
        ensure(
            body.history.owner.as_ref().is_none_or(|o| o == &body.owner),
            "Question owner mismatch",
        )?;
        ensure(
            body.history.records.is_empty() || body.history.owner.is_some(),
            "Missing history owner",
        )?;
        ensure(
            body.question.len() <= 2000
                && body
                    .question_id
                    .strip_prefix('q')
                    .is_some_and(|s| s.parse::<i64>().is_ok()),
            "Invalid question identity",
        )?;
        ensure(
            body.history.records.len() <= 64,
            "Geometry history exceeds 64 records",
        )?;
        let mut previous = "empty";
        let mut seen = HashSet::new();
        let mut captures: HashMap<&str, &GeometrySnapshot> = HashMap::new();
        let mut predictions: HashMap<&str, (&str, f64)> = HashMap::new();
        let mut positions: HashMap<&str, usize> = HashMap::new();
        let records: Vec<GeometryEntry> = body
            .history
            .records
            .iter()
            .map(|r| decode(r.body_json.as_bytes()))
            .collect::<Result<_>>()?;
        for (index, (record, entry)) in body.history.records.iter().zip(&records).enumerate() {
            let identity = hash(
                &[
                    record.previous.clone(),
                    hash(&record.request_id),
                    record.request_sha256.clone(),
                    hash(&record.body_json),
                ]
                .join("\n"),
            );
            ensure(
                record.previous == previous
                    && record.id == identity
                    && is_hash(&record.request_sha256)
                    && !record.request_id.is_empty()
                    && record.request_id.len() <= 128
                    && seen.insert(record.request_id.nfc().collect::<String>()),
                "Broken geometry chain or conflicting operation identity",
            )?;
            match entry {
                GeometryEntry::Capture { snapshot, note } => {
                    authored(note)?;
                    snapshot.validate()?;
                    captures.insert(&record.id, snapshot);
                    ensure(captures.len() <= 4, "Four frozen intervals per question")?;
                }
                GeometryEntry::Prediction {
                    baseline,
                    maximum_rms_distance,
                    expectation,
                } => {
                    ensure(
                        captures.contains_key(baseline.as_str()),
                        "Prediction has no earlier baseline or authored expectation",
                    )?;
                    ensure(
                        maximum_rms_distance.is_finite()
                            && (0.0..=2.0).contains(maximum_rms_distance),
                        "Invalid prediction bound",
                    )?;
                    authored(expectation)?;
                    predictions.insert(&record.id, (baseline, *maximum_rms_distance));
                }
                GeometryEntry::Comparison {
                    prediction,
                    observation,
                    recipe,
                    rms_distance,
                    threshold_met,
                } => {
                    let (baseline_id, bound) =
                        predictions.get(prediction.as_str()).ok_or_else(|| {
                            invalid("Comparison references missing or misordered records")
                        })?;
                    let b = captures.get(baseline_id).ok_or_else(|| {
                        invalid("Comparison references missing or misordered records")
                    })?;
                    let o = captures.get(observation.as_str()).ok_or_else(|| {
                        invalid("Comparison references missing or misordered records")
                    })?;
                    ensure(
                        positions
                            .get(observation.as_str())
                            .zip(positions.get(prediction.as_str()))
                            .is_some_and(|(o, p)| o > p),
                        "Comparison references missing or misordered records",
                    )?;
                    let value = GeometrySnapshot::distance(b, o)?;
                    ensure(
                        recipe == "mean-state-rms-distance-v1"
                            && rms_distance.is_finite()
                            && (value - rms_distance).abs() <= 1e-12
                            && *threshold_met == (value <= *bound),
                        "Comparison does not match its frozen vectors",
                    )?;
                }
                GeometryEntry::Revision { target, text } => {
                    ensure(
                        positions.contains_key(target.as_str()),
                        "Revision needs an earlier record and authored text",
                    )?;
                    authored(text)?;
                }
            }
            positions.insert(&record.id, index);
            previous = &record.id;
        }
        Ok(Self {
            body,
            digest: envelope.body_sha256,
            records,
        })
    }
}
fn decode<T: serde::de::DeserializeOwned>(bytes: &[u8]) -> Result<T> {
    serde_json::from_slice(bytes).map_err(|e| invalid(&format!("Invalid geometry JSON: {e}")))
}
pub fn hash(text: &str) -> String {
    format!("{:x}", Sha256::digest(text.as_bytes()))
}
fn invalid(message: &str) -> CoreError {
    CoreError::Invalid(message.into())
}
fn is_hash(text: &str) -> bool {
    // Swift Character.isHexDigit includes the fullwidth ASCII forms.
    text.chars().count() == 64 && text.chars().all(|c| c.is_ascii_hexdigit() || matches!(c, '\u{ff10}'..='\u{ff19}' | '\u{ff21}'..='\u{ff26}' | '\u{ff41}'..='\u{ff46}'))
}
fn authored(text: &str) -> Result<()> {
    // Foundation .whitespacesAndNewlines includes U+200B (unlike str::trim).
    let whitespace = |c| matches!(c, '\u{0009}'..='\u{000d}' | ' ' | '\u{0085}' | '\u{00a0}' | '\u{1680}' | '\u{2000}'..='\u{200b}' | '\u{2028}' | '\u{2029}' | '\u{202f}' | '\u{205f}' | '\u{3000}');
    ensure(
        text.len() <= 2000 && !text.trim_matches(whitespace).is_empty(),
        "Invalid authored text length",
    )
}
fn validate_vector(values: &[f64]) -> Result<()> {
    ensure(
        values.len() == 128
            && values
                .iter()
                .all(|v| v.is_finite() && (-1.0..=1.0).contains(v)),
        "Invalid activation vector",
    )
}
