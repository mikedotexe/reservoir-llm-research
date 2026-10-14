//! One in-memory accepted packet. No historical source path is resolved.
use crate::files::{self, AppError};
use reservoir_core::geometry::{GeometryEntry, GeometryPacket, GeometrySnapshot};
use serde::Serialize;
use std::sync::{
    atomic::{AtomicBool, AtomicU64, Ordering},
    Arc, Mutex,
};

#[derive(Clone, Default)]
pub struct GeometryState {
    inner: Arc<Inner>,
}
#[derive(Default)]
struct Inner {
    accepted: Mutex<Option<Accepted>>,
    sequence: AtomicU64,
    busy: AtomicBool,
}
struct Accepted {
    id: String,
    filename: String,
    bytes: Arc<Vec<u8>>,
}
pub struct GeometryGuard {
    inner: Arc<Inner>,
}
impl Drop for GeometryGuard {
    fn drop(&mut self) {
        self.inner.busy.store(false, Ordering::Release);
    }
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PacketView {
    pub packet_id: String,
    pub filename: String,
    pub origin: String,
    pub sha256: String,
    pub body_sha256: String,
    pub size_bytes: usize,
    pub owner: String,
    pub question_id: String,
    pub question: String,
    pub limits: String,
    pub verification_scope: &'static str,
    pub records: Vec<EntryView>,
}
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct EntryView {
    id: String,
    request_id: String,
    request_sha256: String,
    kind: &'static str,
    authored_text: Option<String>,
    snapshot: Option<SnapshotView>,
    baseline: Option<String>,
    maximum_rms_distance: Option<f64>,
    prediction: Option<String>,
    observation: Option<String>,
    recipe: Option<String>,
    rms_distance: Option<f64>,
    threshold_met: Option<bool>,
    target: Option<String>,
}
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SnapshotView {
    source_sha256: String,
    captured_at_unix_ms: String,
    requested_seconds: u64,
    source: String,
    scope: String,
    identity: String,
    duration_ms: u64,
    gaps: Vec<[String; 2]>,
    frames: Vec<FrameView>,
}
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct FrameView {
    t_ms: String,
    wall_clock_unix_ms: String,
    activations: Vec<f64>,
    rms: f64,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct GeometryOpenResult {
    pub request_id: String,
    pub cancelled: bool,
    pub packet: Option<PacketView>,
}
impl GeometryOpenResult {
    pub fn cancelled(request_id: String) -> Self {
        Self {
            request_id,
            cancelled: true,
            packet: None,
        }
    }
}
impl GeometryState {
    pub fn begin_operation(&self) -> Result<GeometryGuard, AppError> {
        self.inner
            .busy
            .compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
            .map_err(|_| {
                AppError::new(
                    "geometry",
                    "busy",
                    "Another geometry open or export is still running.",
                )
            })?;
        Ok(GeometryGuard {
            inner: self.inner.clone(),
        })
    }
    pub fn open(
        &self,
        request_id: String,
        filename: String,
        origin: &str,
        bytes: Vec<u8>,
    ) -> Result<GeometryOpenResult, AppError> {
        if !matches!(origin, "syntheticExample" | "openedFile") {
            return Err(AppError::new(
                "open-geometry",
                "origin",
                "Unknown packet origin.",
            ));
        }
        let packet = GeometryPacket::decode(&bytes)
            .map_err(|e| AppError::new("open-geometry", "invalid-packet", e.to_string()))?;
        let sha256 = files::digest(&bytes);
        let id = format!(
            "geometry-{}-{sha256}",
            self.inner.sequence.fetch_add(1, Ordering::Relaxed)
        );
        let records = packet
            .body
            .history
            .records
            .iter()
            .zip(&packet.records)
            .map(|(r, e)| {
                let mut v = EntryView {
                    id: r.id.clone(),
                    request_id: r.request_id.clone(),
                    request_sha256: r.request_sha256.clone(),
                    kind: e.kind(),
                    authored_text: e.authored_text().map(String::from),
                    snapshot: None,
                    baseline: None,
                    maximum_rms_distance: None,
                    prediction: None,
                    observation: None,
                    recipe: None,
                    rms_distance: None,
                    threshold_met: None,
                    target: None,
                };
                match e {
                    GeometryEntry::Capture { snapshot, .. } => {
                        v.snapshot = Some(snapshot_view(snapshot)?)
                    }
                    GeometryEntry::Prediction {
                        baseline,
                        maximum_rms_distance,
                        ..
                    } => {
                        v.baseline = Some(baseline.clone());
                        v.maximum_rms_distance = Some(*maximum_rms_distance);
                    }
                    GeometryEntry::Comparison {
                        prediction,
                        observation,
                        recipe,
                        rms_distance,
                        threshold_met,
                    } => {
                        v.prediction = Some(prediction.clone());
                        v.observation = Some(observation.clone());
                        v.recipe = Some(recipe.clone());
                        v.rms_distance = Some(*rms_distance);
                        v.threshold_met = Some(*threshold_met);
                    }
                    GeometryEntry::Revision { target, .. } => v.target = Some(target.clone()),
                }
                Ok(v)
            })
            .collect::<Result<Vec<_>, AppError>>()?;
        let view = PacketView {
            packet_id: id.clone(),
            filename: filename.clone(),
            origin: origin.into(),
            sha256,
            body_sha256: packet.digest,
            size_bytes: bytes.len(),
            owner: packet.body.owner,
            question_id: packet.body.question_id,
            question: packet.body.question,
            limits: packet.body.limits,
            verification_scope: reservoir_core::geometry::SCOPE,
            records,
        };
        *self.inner.accepted.lock().map_err(|_| {
            AppError::new("open-geometry", "state", "Geometry state unavailable.")
        })? = Some(Accepted {
            id,
            filename,
            bytes: Arc::new(bytes),
        });
        Ok(GeometryOpenResult {
            request_id,
            cancelled: false,
            packet: Some(view),
        })
    }
    pub fn snapshot(&self, packet_id: &str) -> Result<(String, Arc<Vec<u8>>), AppError> {
        let guard = self.inner.accepted.lock().map_err(|_| {
            AppError::new("export-geometry", "state", "Geometry state unavailable.")
        })?;
        let packet = guard
            .as_ref()
            .filter(|p| p.id == packet_id)
            .ok_or_else(|| {
                AppError::new(
                    "export-geometry",
                    "stale-packet",
                    "The requested packet is no longer accepted.",
                )
            })?;
        Ok((packet.filename.clone(), packet.bytes.clone()))
    }
}
fn snapshot_view(s: &GeometrySnapshot) -> Result<SnapshotView, AppError> {
    Ok(SnapshotView {
        source_sha256: s.source_sha256.clone(),
        captured_at_unix_ms: s.captured_at_unix_ms.to_string(),
        requested_seconds: s.requested_seconds,
        source: s.source.clone(),
        scope: s.scope.clone(),
        identity: s.identity.clone(),
        duration_ms: s.duration_ms(),
        gaps: s
            .gaps()
            .iter()
            .map(|(a, b)| [a.to_string(), b.to_string()])
            .collect(),
        frames: s
            .frames
            .iter()
            .map(|f| {
                Ok(FrameView {
                    t_ms: f.t_ms.to_string(),
                    wall_clock_unix_ms: f.wall_clock_unix_ms.to_string(),
                    activations: f.activations.clone(),
                    rms: f
                        .rms()
                        .map_err(|e| AppError::new("open-geometry", "vector", e.to_string()))?,
                })
            })
            .collect::<Result<Vec<_>, AppError>>()?,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    fn bytes() -> Vec<u8> {
        include_bytes!("../../../../native/ReservoirScope/Tests/Fixtures/geometry-bookmarks/minime-synthetic-geometry.json").to_vec()
    }
    #[test]
    fn failed_replacement_preserves_exact_accepted_bytes_and_origin() {
        let state = GeometryState::default();
        let p = state
            .open(
                "one".into(),
                "synthetic.json".into(),
                "syntheticExample",
                bytes(),
            )
            .unwrap()
            .packet
            .unwrap();
        assert_eq!(p.origin, "syntheticExample");
        assert_eq!(p.records.len(), 5);
        assert!(state
            .open(
                "two".into(),
                "broken.json".into(),
                "openedFile",
                b"{}".to_vec()
            )
            .is_err());
        let (filename, retained) = state.snapshot(&p.packet_id).unwrap();
        assert_eq!(filename, "synthetic.json");
        assert_eq!(*retained, bytes());
        let p2 = state
            .open(
                "three".into(),
                "same-bytes.json".into(),
                "openedFile",
                bytes(),
            )
            .unwrap()
            .packet
            .unwrap();
        assert_eq!(p2.origin, "openedFile");
        assert_ne!(p.packet_id, p2.packet_id);
        assert!(state.snapshot(&p.packet_id).is_err());
    }
    #[test]
    fn operation_guard_serializes_dialogs_and_snapshot_exports_original_bytes() {
        let state = GeometryState::default();
        let guard = state.begin_operation().unwrap();
        assert!(state.begin_operation().is_err());
        drop(guard);
        assert!(state.begin_operation().is_ok());
        let p = state
            .open(
                "one".into(),
                "référence-宇宙.json".into(),
                "openedFile",
                bytes(),
            )
            .unwrap()
            .packet
            .unwrap();
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("copy.json");
        let (_, original) = state.snapshot(&p.packet_id).unwrap();
        let proof = files::atomic_export(&path, &original, &dir.path().join("resources")).unwrap();
        assert_eq!(std::fs::read(path).unwrap(), bytes());
        assert_eq!(proof.sha256, p.sha256);
        let value = serde_json::to_value(&p).unwrap();
        assert_eq!(value["records"][0]["snapshot"]["frames"][0]["tMs"], "10000");
        assert_eq!(value["records"][0]["snapshot"]["gaps"][0][1], "13000");
        assert!(value["records"][3]["authoredText"].is_null());
    }
}
