//! Backend-owned frozen evidence sessions. No source path in evidence is opened.
use crate::{files::AppError, resources};
use reservoir_core::observatory::{
    self as evidence, HistoricalEvidence, ReferenceBands, StateReplay,
};
use serde::Serialize;
use std::{
    collections::BTreeMap,
    path::Path,
    sync::{
        atomic::{AtomicBool, AtomicU64, Ordering},
        Arc, Mutex,
    },
};

const MAX_HANDLES: usize = 4;
pub const MAX_TIMELINE_PAGE: usize = 256;

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Identity {
    pub name: String,
    pub sha256: String,
}
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Diagnostic {
    pub track_id: String,
    pub category: String,
    pub message: String,
}
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TrackSummary {
    pub id: String,
    pub title: String,
    pub axis: String,
    pub frame_count: usize,
    pub node_count: Option<usize>,
    pub first_position: f64,
    pub last_position: f64,
    pub first_utc: Option<String>,
    pub last_utc: Option<String>,
    pub captured_at_utc: Option<String>,
    pub identities: Vec<Identity>,
    pub provenance: Vec<String>,
    pub missingness: Vec<String>,
    pub definitions: BTreeMap<String, String>,
    pub bands: Option<ReferenceBands>,
}
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ObservatorySummary {
    pub observatory_id: String,
    pub tracks: Vec<TrackSummary>,
    pub diagnostics: Vec<Diagnostic>,
    pub max_timeline_page: usize,
}
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ObservatoryOpenResult {
    pub request_id: String,
    pub observatory: ObservatorySummary,
}
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct HistoryFrame {
    pub t_utc: String,
    pub t_seconds: f64,
    pub session_id: String,
    pub fill_pct: f64,
    pub fill_rate_pct_per_s: Option<f64>,
    pub cascade: Vec<f64>,
    pub esn_cov_lambda1: Option<f64>,
    pub geom_radius: Option<f64>,
    pub geom_rel: Option<f64>,
    pub esn_leak: Option<f64>,
    pub esn_lambda: Option<f64>,
    pub source_ids: Option<Vec<Option<String>>>,
    pub interval_seconds: Option<f64>,
    pub break_before: bool,
}
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct StateFrame {
    pub activations: Vec<f64>,
    pub pc: Vec<f64>,
    pub state_rms: f64,
    pub centered_rms: f64,
    pub projected_rms: f64,
    pub reconstruction_rmse: f64,
    pub source_identity: String,
}
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ObservatoryFrame {
    pub track_id: String,
    pub index: usize,
    pub position: f64,
    pub history: Option<HistoryFrame>,
    pub state: Option<StateFrame>,
}
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ObservatoryFrameResult {
    pub request_id: String,
    pub observatory_id: String,
    pub frame: ObservatoryFrame,
}
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TimelinePoint {
    pub index: usize,
    pub position: f64,
    pub t_utc: Option<String>,
    pub session_id: Option<String>,
    pub fill_pct: Option<f64>,
    pub fill_rate_pct_per_s: Option<f64>,
    pub cascade: Option<Vec<f64>>,
    pub interval_seconds: Option<f64>,
    pub break_before: bool,
    pub state_rms: Option<f64>,
    pub pc: Option<Vec<f64>>,
    pub node_value: Option<f64>,
}
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ObservatoryTimelineResult {
    pub request_id: String,
    pub observatory_id: String,
    pub track_id: String,
    pub start: usize,
    pub total: usize,
    pub has_more: bool,
    pub node_index: Option<usize>,
    pub points: Vec<TimelinePoint>,
}
struct Capture {
    history: Option<HistoricalEvidence>,
    states: Option<StateReplay>,
}
#[derive(Clone, Default)]
pub struct ObservatoryState {
    captures: Arc<Mutex<BTreeMap<String, Arc<Capture>>>>,
    sequence: Arc<AtomicU64>,
    opening: Arc<AtomicBool>,
}
struct OpeningGuard<'a>(&'a AtomicBool);
impl Drop for OpeningGuard<'_> {
    fn drop(&mut self) {
        self.0.store(false, Ordering::Release);
    }
}
fn error(category: &str, message: impl Into<String>) -> AppError {
    AppError::new("observatory", category, message)
}
fn core_error(e: reservoir_core::CoreError) -> AppError {
    let category = match &e {
        reservoir_core::CoreError::Invalid(_) => "invalid-evidence",
        reservoir_core::CoreError::Unsupported(_) => "unsupported-evidence",
    };
    error(category, e.to_string())
}
fn identity(name: &str, bytes: &[u8]) -> Identity {
    Identity {
        name: name.into(),
        sha256: evidence::digest(bytes),
    }
}
fn diagnostic(track: &str, e: AppError) -> Diagnostic {
    Diagnostic {
        track_id: track.into(),
        category: e.category,
        message: e.message,
    }
}

impl ObservatoryState {
    /// Only the fixed bundle allowlist is read; a broken track does not disable
    /// independent evidence. A session with no available tracks retains diagnostics.
    pub fn open(&self, root: &Path, request_id: String) -> Result<ObservatoryOpenResult, AppError> {
        self.opening
            .compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
            .map_err(|_| error("busy", "An Observatory bundle read is already in progress."))?;
        let _guard = OpeningGuard(&self.opening);
        if self
            .captures
            .lock()
            .map_err(|_| error("state", "Observatory state is unavailable."))?
            .len()
            >= MAX_HANDLES
        {
            return Err(error(
                "handle-limit",
                "Close an Observatory session before opening another.",
            ));
        }
        let mut tracks = Vec::new();
        let mut diagnostics = Vec::new();
        let history = match load_history(root) {
            Ok((history, summary)) => {
                tracks.push(summary);
                Some(history)
            }
            Err(e) => {
                diagnostics.push(diagnostic("history", e));
                None
            }
        };
        let states = match load_states(root) {
            Ok((states, summary)) => {
                tracks.push(summary);
                Some(states)
            }
            Err(e) => {
                diagnostics.push(diagnostic("states", e));
                None
            }
        };
        let id = format!(
            "observatory-{}",
            self.sequence.fetch_add(1, Ordering::Relaxed)
        );
        self.captures
            .lock()
            .map_err(|_| error("state", "Observatory state is unavailable."))?
            .insert(id.clone(), Arc::new(Capture { history, states }));
        Ok(ObservatoryOpenResult {
            request_id,
            observatory: ObservatorySummary {
                observatory_id: id,
                tracks,
                diagnostics,
                max_timeline_page: MAX_TIMELINE_PAGE,
            },
        })
    }
    fn capture(&self, id: &str) -> Result<Arc<Capture>, AppError> {
        self.captures
            .lock()
            .map_err(|_| error("state", "Observatory state is unavailable."))?
            .get(id)
            .cloned()
            .ok_or_else(|| {
                error(
                    "unknown-handle",
                    "This Observatory session is closed or unknown.",
                )
            })
    }
    pub fn close(&self, observatory_id: &str) -> Result<(), AppError> {
        self.captures
            .lock()
            .map_err(|_| error("state", "Observatory state is unavailable."))?
            .remove(observatory_id);
        Ok(())
    }
    pub fn frame(
        &self,
        request_id: String,
        observatory_id: &str,
        track_id: &str,
        index: usize,
    ) -> Result<ObservatoryFrameResult, AppError> {
        let capture = self.capture(observatory_id)?;
        let frame = frame(&capture, track_id, index)?;
        Ok(ObservatoryFrameResult {
            request_id,
            observatory_id: observatory_id.into(),
            frame,
        })
    }
    pub fn seek(
        &self,
        request_id: String,
        observatory_id: &str,
        track_id: &str,
        position: f64,
        mode: &str,
    ) -> Result<ObservatoryFrameResult, AppError> {
        let nearest = match mode {
            "floor" => false,
            "nearest" => true,
            _ => return Err(error("seek-mode", "Seek mode must be floor or nearest.")),
        };
        let capture = self.capture(observatory_id)?;
        let index = match track_id {
            "history" => history(&capture)?.seek(position, nearest),
            "states" => states(&capture)?.seek(position, nearest),
            _ => return Err(error("unknown-track", "Unknown Observatory track.")),
        }
        .map_err(core_error)?;
        let frame = frame(&capture, track_id, index)?;
        Ok(ObservatoryFrameResult {
            request_id,
            observatory_id: observatory_id.into(),
            frame,
        })
    }
    #[allow(clippy::too_many_arguments)]
    pub fn timeline(
        &self,
        request_id: String,
        observatory_id: &str,
        track_id: &str,
        start: usize,
        limit: usize,
        node_index: Option<usize>,
    ) -> Result<ObservatoryTimelineResult, AppError> {
        if !(1..=MAX_TIMELINE_PAGE).contains(&limit) {
            return Err(error(
                "page-bound",
                format!("Timeline page size must be 1–{MAX_TIMELINE_PAGE}."),
            ));
        }
        let capture = self.capture(observatory_id)?;
        let total = match track_id {
            "history" => {
                if node_index.is_some() {
                    return Err(error(
                        "coordinate",
                        "Historical sensory evidence has no per-node activation coordinates.",
                    ));
                }
                history(&capture)?.samples.len()
            }
            "states" => {
                if node_index.is_some_and(|i| i >= evidence::STATE_DIMENSIONS) {
                    return Err(error(
                        "coordinate",
                        "Retained coordinate index must be 0–127.",
                    ));
                }
                states(&capture)?.manifest.rows
            }
            _ => return Err(error("unknown-track", "Unknown Observatory track.")),
        };
        if start > total {
            return Err(error(
                "page-bound",
                "Timeline start is outside retained coverage.",
            ));
        }
        let end = start.saturating_add(limit).min(total);
        let points = (start..end)
            .map(|index| match track_id {
                "history" => {
                    let h = history(&capture)?;
                    let s = &h.samples[index];
                    Ok(TimelinePoint {
                        index,
                        position: s.t_s,
                        t_utc: Some(s.t_utc.clone()),
                        session_id: Some(s.session_id.to_string()),
                        fill_pct: Some(s.fill_pct),
                        fill_rate_pct_per_s: s.fill_rate_pct_per_s,
                        cascade: Some(s.cascade.clone()),
                        interval_seconds: h.interval_seconds(index),
                        break_before: h.break_before(index),
                        state_rms: None,
                        pc: None,
                        node_value: None,
                    })
                }
                _ => {
                    let r = states(&capture)?;
                    let s = &r.geometry.samples[index];
                    Ok(TimelinePoint {
                        index,
                        position: index as f64,
                        t_utc: None,
                        session_id: None,
                        fill_pct: None,
                        fill_rate_pct_per_s: None,
                        cascade: None,
                        interval_seconds: None,
                        break_before: false,
                        state_rms: Some(s.state_rms),
                        pc: Some(s.pc.clone()),
                        node_value: node_index
                            .map(|node| r.node(index, node).map_err(core_error))
                            .transpose()?,
                    })
                }
            })
            .collect::<Result<Vec<_>, AppError>>()?;
        Ok(ObservatoryTimelineResult {
            request_id,
            observatory_id: observatory_id.into(),
            track_id: track_id.into(),
            start,
            total,
            has_more: end < total,
            node_index,
            points,
        })
    }
}
fn history(capture: &Capture) -> Result<&HistoricalEvidence, AppError> {
    capture.history.as_ref().ok_or_else(|| {
        error(
            "unavailable-track",
            "Historical evidence is unavailable; inspect this session’s diagnostic.",
        )
    })
}
fn states(capture: &Capture) -> Result<&StateReplay, AppError> {
    capture.states.as_ref().ok_or_else(|| {
        error(
            "unavailable-track",
            "Retained activations are unavailable; inspect this session’s diagnostic.",
        )
    })
}
fn frame(capture: &Capture, track: &str, index: usize) -> Result<ObservatoryFrame, AppError> {
    match track {
        "history" => {
            let h = history(capture)?;
            let s = h.samples.get(index).ok_or_else(|| {
                error(
                    "frame-bound",
                    "Historical frame is outside retained coverage.",
                )
            })?;
            Ok(ObservatoryFrame {
                track_id: track.into(),
                index,
                position: s.t_s,
                state: None,
                history: Some(HistoryFrame {
                    t_utc: s.t_utc.clone(),
                    t_seconds: s.t_s,
                    session_id: s.session_id.to_string(),
                    fill_pct: s.fill_pct,
                    fill_rate_pct_per_s: s.fill_rate_pct_per_s,
                    cascade: s.cascade.clone(),
                    esn_cov_lambda1: s.esn_cov_lambda1,
                    geom_radius: s.geom_radius,
                    geom_rel: s.geom_rel,
                    esn_leak: s.esn_leak,
                    esn_lambda: s.esn_lambda,
                    source_ids: s
                        .source_ids
                        .as_ref()
                        .map(|ids| ids.iter().map(|id| id.map(|v| v.to_string())).collect()),
                    interval_seconds: h.interval_seconds(index),
                    break_before: h.break_before(index),
                }),
            })
        }
        "states" => {
            let r = states(capture)?;
            let s =
                r.geometry.samples.get(index).ok_or_else(|| {
                    error("frame-bound", "State frame is outside retained coverage.")
                })?;
            Ok(ObservatoryFrame {
                track_id: track.into(),
                index,
                position: index as f64,
                history: None,
                state: Some(StateFrame {
                    activations: r.activations(index).map_err(core_error)?,
                    pc: s.pc.clone(),
                    state_rms: s.state_rms,
                    centered_rms: s.centered_rms,
                    projected_rms: s.projected_rms,
                    reconstruction_rmse: s.reconstruction_rmse,
                    source_identity: format!("capture:{}:row:{index}", r.manifest.source_sha256),
                }),
            })
        }
        _ => Err(error("unknown-track", "Unknown Observatory track.")),
    }
}

fn load_history(root: &Path) -> Result<(HistoricalEvidence, TrackSummary), AppError> {
    let bytes = resources::catalog_bytes(root, "data.json")?;
    let h = HistoricalEvidence::from_bytes(&bytes).map_err(core_error)?;
    let first = &h.samples[0];
    let last = h.samples.last().unwrap();
    let mut provenance=vec![
        "Frozen September 2026 steward-side telemetry; no live connection and no language-model activation measurement.".into(),
        "Elapsed seconds preserve retained sample spacing. UTC is the historical session-start conversion, with an unrecorded baseline offset and later clock/logging uncertainty (TRACE.md §5).".into(),
        "Fill rate is the retained backward difference between saved fills, not the engine’s smoothed dfill_dt. Null measurements remain absent.".into(),
        "Replay holds the last observation; nearest seeking chooses an actual retained sample. No intermediate measurements are synthesized.".into(),
        "Reference bands are retained configuration, not measured subjective comfort or a historical per-tick controller mode.".into(),
    ];
    if let Some(note) = h.subject.as_ref().and_then(|s| s.note.clone()) {
        provenance.push(note);
    }
    let mut missingness=vec![
        "No timed-gap annotations are retained. Elapsed intervals are exposed exactly; only session changes create automatic breaks. Absence of a break does not prove continuous coverage.".into(),
        "Sensory cascade contains three recorded direction estimates in stored slot order; the other five slots, all direction vectors and a certified sorted eigenspectrum are absent.".into(),
        "No join to the separately captured 128-coordinate state replay is available.".into(),
    ];
    if let Some(status) = h.controller.historical_status.clone() {
        missingness.push(status);
    }
    let summary = TrackSummary {
        id: "history".into(),
        title: "Recorded fill and sensory directions".into(),
        axis: "elapsedSeconds".into(),
        frame_count: h.samples.len(),
        node_count: None,
        first_position: first.t_s,
        last_position: last.t_s,
        first_utc: Some(first.t_utc.clone()),
        last_utc: Some(last.t_utc.clone()),
        captured_at_utc: h.capture.as_ref().and_then(|c| c.captured_at_utc.clone()),
        identities: vec![identity("data.json", &bytes)],
        provenance,
        missingness,
        definitions: h.definitions.clone().unwrap_or_default(),
        bands: Some(h.bands.clone()),
    };
    Ok((h, summary))
}
fn load_states(root: &Path) -> Result<(StateReplay, TrackSummary), AppError> {
    let manifest = resources::catalog_bytes(root, "state-replay.json")?;
    let raw = resources::catalog_bytes(root, "state-replay.bin")?;
    let geometry = resources::catalog_bytes(root, "state-geometry.json")?;
    let identities = vec![
        identity("state-replay.json", &manifest),
        identity("state-replay.bin", &raw),
        identity("state-geometry.json", &geometry),
    ];
    let r = StateReplay::from_bytes(&manifest, raw, &geometry).map_err(core_error)?;
    let mut provenance=vec![
        "Frozen Minime native ESN retained activation coordinates, decoded exactly from little-endian Float32 bytes into Float64 display values.".into(),
        "1024-row capture limit; oldest-to-newest retained row order. Capture time observes the file and is not a timestamp for any row.".into(),
        "Coordinate indices preserve recorded order. Any drawn node positions are a display arrangement, not authenticated neuron locations.".into(),
        "PCA coordinates and distances are retained derived geometry bound to these exact activation bytes. The frozen basis was fitted retrospectively to the full capture; this reader does not refit it or infer online availability.".into(),
        "Validation checks resource identity, binary/schema bounds, finite values and internal hash bindings. It does not regenerate the live recurrent engine or establish causal effects.".into(),
    ];
    if let Some(limitation) = r
        .geometry
        .source
        .consistency
        .as_ref()
        .and_then(|c| c.limitation.clone())
    {
        provenance.push(limitation);
    }
    if let Some(notes) = r.geometry.timing.cadence_notes.clone() {
        provenance.push(notes);
    }
    let mut missingness = r.geometry.missing_fields.clone().unwrap_or_default();
    missingness.extend([
        "No per-row time, measured cadence or timed-gap sequence. Playback speed in rows/second is presentation only.".into(),
        "No paired fill, controller sequence, authenticated node-layout, boot/session or successful-step identifier.".into(),
        "No alignment with the separate historical fill/sensory track. A replay cursor cannot establish such a join.".into(),
    ]);
    let definitions=BTreeMap::from([
        ("activation".into(),"Retained native ESN state coordinate in −1…1; no language-model activation or neuron location is inferred.".into()),
        ("pc".into(),"Three retained projection coordinates in the retrospective frozen PCA basis, not three observed physical axes.".into()),
        ("state_rms".into(),"Retained RMS of the original 128-coordinate row; distinct from sensory fill.".into()),
    ]);
    let summary = TrackSummary {
        id: "states".into(),
        title: "Retained 128-coordinate ESN states".into(),
        axis: "ordinal".into(),
        frame_count: r.manifest.rows,
        node_count: Some(r.manifest.dimensions),
        first_position: 0.0,
        last_position: (r.manifest.rows - 1) as f64,
        first_utc: None,
        last_utc: None,
        captured_at_utc: r.manifest.captured_at_utc.clone(),
        identities,
        provenance,
        missingness,
        definitions,
        bands: None,
    };
    Ok((r, summary))
}

#[cfg(test)]
#[path = "observatory_tests.rs"]
mod tests;
