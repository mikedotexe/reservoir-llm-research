//! Temporary, immutable response handles. Candidates validate before insertion;
//! failures never replace a retained handle or rewrite original bytes.
#[cfg(test)]
use crate::files::FileProof;
use crate::files::{self, AppError};
use reservoir_core::response::{
    NativeReceipt, NativeResponse, SimulationResponse, NATIVE_CLOCK, NATIVE_SCOPE, NATIVE_SUBJECT,
};
use serde::Serialize;
#[cfg(test)]
use std::path::Path;
use std::{
    collections::BTreeMap,
    sync::{
        atomic::{AtomicBool, AtomicU64, Ordering},
        Arc, Mutex,
    },
};
const MAX_HANDLES: usize = 4;
const MAX_RETAINED_BYTES: usize = 32 * 1024 * 1024;
#[derive(Clone, Default)]
pub struct ResponseState {
    inner: Arc<Inner>,
}
#[derive(Default)]
struct Inner {
    stored: Mutex<BTreeMap<String, Arc<Stored>>>,
    sequence: AtomicU64,
    busy: AtomicBool,
}
struct Stored {
    filename: String,
    bytes: Arc<Vec<u8>>,
    evidence: Evidence,
}
enum Evidence {
    Native(NativeResponse),
    Simulation(Box<SimulationResponse>),
}
pub struct ResponseGuard(Arc<Inner>);
impl Drop for ResponseGuard {
    fn drop(&mut self) {
        self.0.busy.store(false, Ordering::Release)
    }
}
fn error(category: &str, message: impl Into<String>) -> AppError {
    AppError::new("response", category, message)
}
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ResponseSummary {
    pub response_id: String,
    pub kind: String,
    pub origin: String,
    pub filename: String,
    pub sha256: String,
    pub size_bytes: usize,
    pub frame_count: usize,
    pub node_count: usize,
    pub fixed_delta_scale: f64,
    pub return_threshold: Option<f64>,
    pub first_label: String,
    pub second_label: String,
    pub provenance: Vec<String>,
    pub missingness: Vec<String>,
    pub metadata: BTreeMap<String, String>,
    pub timeline: Vec<TimelinePoint>,
    pub events: Vec<EventSummary>,
}
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TimelinePoint {
    pub index: usize,
    pub position: String,
    pub l2: f64,
    pub receipt_index: Option<usize>,
}
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct EventSummary {
    pub index: usize,
    pub status: String,
    pub frame_index: Option<usize>,
    pub is_boundary: bool,
}
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ResponseOpenResult {
    pub request_id: String,
    pub cancelled: bool,
    pub response: Option<ResponseSummary>,
}
impl ResponseOpenResult {
    pub fn cancelled(request_id: String) -> Self {
        Self {
            request_id,
            cancelled: true,
            response: None,
        }
    }
}
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ResponseFrame {
    pub index: usize,
    pub position: String,
    pub first: Vec<f64>,
    pub second: Vec<f64>,
    pub delta: Vec<f64>,
    pub l2: f64,
    pub direction: Option<Vec<f64>>,
    pub realized_noise: Option<Vec<f64>>,
    pub metadata: BTreeMap<String, String>,
}
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ResponseFrameResult {
    pub request_id: String,
    pub response_id: String,
    pub frame: ResponseFrame,
}
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ResponseEvent {
    pub index: usize,
    pub status: String,
    pub has_state: bool,
    pub is_boundary: bool,
    pub metadata: BTreeMap<String, String>,
    pub direction: Vec<f64>,
    pub realized_noise: Option<Vec<f64>>,
    pub first: Option<Vec<f64>>,
    pub second: Option<Vec<f64>>,
    pub delta: Option<Vec<f64>>,
}
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ResponseEventResult {
    pub request_id: String,
    pub response_id: String,
    pub event: ResponseEvent,
}
fn doubles(v: &[f32]) -> Vec<f64> {
    v.iter().map(|&x| f64::from(x)).collect()
}
impl ResponseState {
    pub fn begin_operation(&self) -> Result<ResponseGuard, AppError> {
        self.inner
            .busy
            .compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
            .map_err(|_| error("busy", "Another response file operation is still running."))?;
        Ok(ResponseGuard(self.inner.clone()))
    }
    pub fn open(
        &self,
        request_id: String,
        filename: String,
        origin: &str,
        kind: &str,
        bytes: Vec<u8>,
        previous_response_id: Option<&str>,
    ) -> Result<ResponseOpenResult, AppError> {
        if !matches!(origin, "bundled" | "openedFile") {
            return Err(error("origin", "Unknown response origin."));
        }
        if origin == "openedFile" && kind != "native" {
            return Err(error(
                "source",
                "Only native rehearsal receipts may be opened externally.",
            ));
        }
        let evidence = match kind {
            "native" => Evidence::Native(
                NativeResponse::decode(&bytes)
                    .map_err(|e| error("invalid-response", e.to_string()))?,
            ),
            "simulation" => Evidence::Simulation(Box::new(
                SimulationResponse::decode(&bytes)
                    .map_err(|e| error("invalid-response", e.to_string()))?,
            )),
            _ => return Err(error("source", "Unknown response family.")),
        };
        let mut store = self
            .inner
            .stored
            .lock()
            .map_err(|_| error("state", "Response state is unavailable."))?;
        if let Some(previous) = previous_response_id {
            let prior = store.get(previous).ok_or_else(|| {
                error(
                    "unknown-handle",
                    "The previous response handle is closed or unknown.",
                )
            })?;
            if let (Evidence::Native(next), Evidence::Native(old)) = (&evidence, &prior.evidence) {
                next.validate_replacement(old)
                    .map_err(|e| error("invalid-replacement", e.to_string()))?;
            }
        }
        if store.len() >= MAX_HANDLES
            || store.values().map(|s| s.bytes.len()).sum::<usize>() + bytes.len()
                > MAX_RETAINED_BYTES
        {
            return Err(error("handle-limit","Close an unused response before opening another; at most four bounded snapshots are retained."));
        }
        let sha256 = files::digest(&bytes);
        let id = format!(
            "response-{}-{sha256}",
            self.inner.sequence.fetch_add(1, Ordering::Relaxed)
        );
        let summary = summary(&id, &filename, origin, &sha256, bytes.len(), &evidence);
        store.insert(
            id,
            Arc::new(Stored {
                filename,
                bytes: Arc::new(bytes),
                evidence,
            }),
        );
        Ok(ResponseOpenResult {
            request_id,
            cancelled: false,
            response: Some(summary),
        })
    }
    fn stored(&self, id: &str) -> Result<Arc<Stored>, AppError> {
        self.inner
            .stored
            .lock()
            .map_err(|_| error("state", "Response state is unavailable."))?
            .get(id)
            .cloned()
            .ok_or_else(|| {
                error(
                    "unknown-handle",
                    "This response handle is closed or unknown.",
                )
            })
    }
    pub fn close(&self, response_id: &str) -> Result<(), AppError> {
        self.inner
            .stored
            .lock()
            .map_err(|_| error("state", "Response state is unavailable."))?
            .remove(response_id);
        Ok(())
    }
    pub fn snapshot(&self, response_id: &str) -> Result<(String, Arc<Vec<u8>>), AppError> {
        let stored = self.stored(response_id)?;
        Ok((stored.filename.clone(), stored.bytes.clone()))
    }
    #[cfg(test)]
    pub fn export(
        &self,
        response_id: &str,
        path: &Path,
        resource_root: &Path,
    ) -> Result<FileProof, AppError> {
        let (_, bytes) = self.snapshot(response_id)?;
        files::atomic_export(path, &bytes, resource_root)
    }
    pub fn frame(
        &self,
        request_id: String,
        response_id: &str,
        index: usize,
    ) -> Result<ResponseFrameResult, AppError> {
        let stored = self.stored(response_id)?;
        let frame = match &stored.evidence {
            Evidence::Native(n) => {
                let receipt = n
                    .frame_indices
                    .get(index)
                    .map(|&i| &n.receipts[i])
                    .ok_or_else(|| {
                        error(
                            "frame-bound",
                            "Native applied frame index is outside this bundle.",
                        )
                    })?;
                ResponseFrame {
                    index,
                    position: receipt.successful_step_id.unwrap().to_string(),
                    first: doubles(receipt.before.as_ref().unwrap()),
                    second: doubles(receipt.after.as_ref().unwrap()),
                    delta: doubles(receipt.delta.as_ref().unwrap()),
                    l2: receipt.actual_l2.unwrap(),
                    direction: Some(doubles(&receipt.direction)),
                    realized_noise: receipt.realized_noise.as_ref().map(|v| doubles(v)),
                    metadata: receipt_metadata(receipt),
                }
            }
            Evidence::Simulation(s) => {
                let f = s.frames.get(index).ok_or_else(|| {
                    error(
                        "frame-bound",
                        "Simulation boundary index is outside the retained fixture.",
                    )
                })?;
                ResponseFrame {
                    index,
                    position: f.original_boundary_step.to_string(),
                    first: f.control.clone(),
                    second: f.intervention.clone(),
                    delta: f.delta.clone(),
                    l2: f.separation_l2,
                    direction: None,
                    realized_noise: None,
                    metadata: BTreeMap::from([
                        ("Sample index".into(), index.to_string()),
                        (
                            "Original simulation boundary".into(),
                            f.original_boundary_step.to_string(),
                        ),
                        ("Run ID".into(), s.run_id.clone()),
                    ]),
                }
            }
        };
        Ok(ResponseFrameResult {
            request_id,
            response_id: response_id.into(),
            frame,
        })
    }
    pub fn event(
        &self,
        request_id: String,
        response_id: &str,
        index: usize,
    ) -> Result<ResponseEventResult, AppError> {
        let stored = self.stored(response_id)?;
        let Evidence::Native(n) = &stored.evidence else {
            return Err(error(
                "event-kind",
                "The retained simulation has frames, not native receipt events.",
            ));
        };
        let r = n.receipts.get(index).ok_or_else(|| {
            error(
                "event-bound",
                "Native receipt event is outside this bundle.",
            )
        })?;
        Ok(ResponseEventResult {
            request_id,
            response_id: response_id.into(),
            event: ResponseEvent {
                index,
                status: r.status.clone(),
                has_state: r.has_state(),
                is_boundary: r.is_boundary(),
                metadata: receipt_metadata(r),
                direction: doubles(&r.direction),
                realized_noise: r.realized_noise.as_ref().map(|v| doubles(v)),
                first: r.before.as_ref().map(|v| doubles(v)),
                second: r.after.as_ref().map(|v| doubles(v)),
                delta: r.delta.as_ref().map(|v| doubles(v)),
            },
        })
    }
}
fn receipt_metadata(r: &NativeReceipt) -> BTreeMap<String, String> {
    let mut m = BTreeMap::from([
        ("Command ID".into(), r.command_id.clone()),
        ("Intent ID".into(), r.intent_id.clone()),
        ("Pattern ID".into(), r.pattern_id.clone()),
        ("Pattern SHA-256".into(), r.pattern_sha256.clone()),
        (
            "Engine session ID".into(),
            r.identity.engine_session_id.clone(),
        ),
        ("Model ID".into(), r.identity.model_id.clone()),
        ("Node-layout ID".into(), r.identity.node_layout_id.clone()),
        ("Status".into(), r.status.clone()),
        (
            "Supplied rehearsal clock (not measured epoch)".into(),
            r.observed_at_unix_ms.to_string(),
        ),
        ("Clipped".into(), r.clipped.to_string()),
    ]);
    for (key, value) in [
        (
            "Successful native step",
            r.successful_step_id.map(|v| v.to_string()),
        ),
        ("Pulse index", r.pulse_index.map(|v| v.to_string())),
        ("Success offset", r.success_offset.map(|v| v.to_string())),
        (
            "Requested signed amount",
            r.requested_amount.map(|v| f64::from(v).to_string()),
        ),
        (
            "Attenuation",
            r.attenuation.map(|v| f64::from(v).to_string()),
        ),
        ("Actual L2", r.actual_l2.map(|v| v.to_string())),
        (
            "Maximum absolute delta",
            r.max_abs_delta.map(|v| f64::from(v).to_string()),
        ),
        (
            "Boundary wait (µs)",
            r.boundary_wait_us.map(|v| v.to_string()),
        ),
        (
            "Effective leak",
            r.effective_leak.map(|v| f64::from(v).to_string()),
        ),
        ("Reason", r.reason.clone()),
    ] {
        if let Some(v) = value {
            m.insert(key.into(), v);
        }
    }
    m
}
fn summary(
    id: &str,
    filename: &str,
    origin: &str,
    sha256: &str,
    size_bytes: usize,
    evidence: &Evidence,
) -> ResponseSummary {
    let (
        kind,
        frame_count,
        fixed_delta_scale,
        return_threshold,
        first_label,
        second_label,
        provenance,
        missingness,
        metadata,
        timeline,
        events,
    ) = match evidence {
        Evidence::Native(n) => {
            let mut metadata = BTreeMap::from([
                ("Subject".into(), NATIVE_SUBJECT.into()),
                ("Scope".into(), NATIVE_SCOPE.into()),
                ("Clock".into(), NATIVE_CLOCK.into()),
                ("Receipts".into(), n.receipts.len().to_string()),
                (
                    "Verified boundaries".into(),
                    n.boundary_indices.len().to_string(),
                ),
            ]);
            for (k, v) in &n.source_hashes {
                metadata.insert(format!("Source SHA-256 · {k}"), v.clone());
            }
            if let Some(identity) = n.identity() {
                metadata.insert(
                    "Engine session ID".into(),
                    identity.engine_session_id.clone(),
                );
                metadata.insert("Model ID".into(), identity.model_id.clone());
                metadata.insert("Node-layout ID".into(), identity.node_layout_id.clone());
            }
            let timeline = n
                .frame_indices
                .iter()
                .enumerate()
                .map(|(index, &i)| {
                    let r = &n.receipts[i];
                    TimelinePoint {
                        index,
                        position: r.successful_step_id.unwrap().to_string(),
                        l2: r.actual_l2.unwrap(),
                        receipt_index: Some(i),
                    }
                })
                .collect();
            let events = n
                .receipts
                .iter()
                .enumerate()
                .map(|(index, r)| EventSummary {
                    index,
                    status: r.status.clone(),
                    frame_index: n.frame_indices.iter().position(|&i| i == index),
                    is_boundary: r.is_boundary(),
                })
                .collect();
            ("native",n.frame_indices.len(),n.delta_scale(),None,"Ordinary step","Applied result",vec![
                "Minime native ESN isolated rehearsal receipts; no running being or live provider is contacted.".into(),
                "Before is the ordinary result of this same successful step, not an unperturbed counterfactual trajectory. After is the actually applied result.".into(),
                "Delta equals Float32 after minus before, checked bit for bit. L2 and maximum change are checked against all 128 coordinates; UI values are exact Float32-to-Float64 promotions.".into(),
                "The difference scale is fixed across this accepted bundle. Admission/terminal events do not create state frames; headroom rejection remains a verified zero-change event.".into(),
                "Successful-step IDs and supplied rehearsal clocks retain exact integer identities. Playback speed does not measure recovery time.".into(),
            ],vec!["No measured fill or reference PCA basis is present. Node positions are a drawing convention.".into(),"Immediate boundaries do not establish a future response, recovery duration, stability or a counterfactual effect.".into()],metadata,timeline,events)
        }
        Evidence::Simulation(s) => {
            let mut metadata = BTreeMap::from([
                ("Subject".into(), s.subject.clone()),
                ("Scope".into(), s.scope.clone()),
                ("Run ID".into(), s.run_id.clone()),
                ("Selection".into(), s.selection.clone()),
                ("Clock".into(), s.clock.clone()),
                ("Controls".into(), s.controls.clone()),
                ("Node layout".into(), s.node_layout.clone()),
                ("Results SHA-256".into(), s.source_results_sha256.clone()),
                (
                    "Requested signed L2".into(),
                    s.result_summary.requested_signed_l2.to_string(),
                ),
                (
                    "Actual initial L2".into(),
                    s.result_summary.actual_initial_l2.to_string(),
                ),
                (
                    "Peak / initial separation".into(),
                    s.result_summary.peak_gain_over_initial.to_string(),
                ),
                (
                    "Return status".into(),
                    s.result_summary.return_status.clone(),
                ),
                (
                    "Return dwell".into(),
                    "8 consecutive boundaries below or equal to 10% of initial separation".into(),
                ),
            ]);
            if let Some(boundary) = s.result_summary.return_boundary {
                metadata.insert("First return sample index".into(), boundary.to_string());
            }
            for (k, v) in &s.model_hashes {
                metadata.insert(format!("Model SHA-256 · {k}"), v.clone());
            }
            let mut provenance=vec!["Retained esn-divide simulated-parent evidence, not a fresh simulation or live Minime measurement.".into(),s.controls.clone(),"Boundary zero already includes one +0.001 coordinate-zero displacement. The entire retained path validates full-vector separation, peak and threshold/dwell return.".into(),"Fixed delta scale is ±0.001 across all 65 boundaries; state scale is ±1. Original simulation boundaries are 200–264; no easing or measured seconds are implied.".into()];
            provenance.extend(s.display_rules.clone());
            let timeline = s
                .frames
                .iter()
                .enumerate()
                .map(|(index, f)| TimelinePoint {
                    index,
                    position: f.original_boundary_step.to_string(),
                    l2: f.separation_l2,
                    receipt_index: None,
                })
                .collect();
            ("simulation",s.frames.len(),s.fixed_delta_scale(),Some(s.return_threshold()),"Control","Perturbed",provenance,vec![s.scope.clone(),"No measured fill, wall-clock time or Minime PCA join. Simulation coordinate compatibility with native node identity is unestablished.".into(),"Clipping occurs in this simulation. Unclipped derivative validation is unestablished; this conditional pair is not a stability test or evidence about either being’s experience.".into()],metadata,timeline,vec![])
        }
    };
    ResponseSummary {
        response_id: id.into(),
        kind: kind.into(),
        origin: origin.into(),
        filename: filename.into(),
        sha256: sha256.into(),
        size_bytes,
        frame_count,
        node_count: 128,
        fixed_delta_scale,
        return_threshold,
        first_label: first_label.into(),
        second_label: second_label.into(),
        provenance,
        missingness,
        metadata,
        timeline,
        events,
    }
}
#[cfg(test)]
#[path = "response_tests.rs"]
mod tests;
