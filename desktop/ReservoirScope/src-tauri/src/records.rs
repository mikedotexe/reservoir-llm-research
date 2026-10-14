//! Temporary, verified record handles. No Library import, path following, or
//! model transport occurs here. Portable bytes remain authoritative for export.
use crate::files::{self, AppError};
use reservoir_core::{inspect_bytes, VerificationReport, VerificationStatus, MAX_RECORD_BYTES};
use serde::Serialize;
use serde_json::Value;
use std::{
    collections::HashMap,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
};

const MAX_HANDLES: usize = 4;
const MAX_RETAINED_BYTES: usize = MAX_RECORD_BYTES;
const MAX_TIMELINE_POINTS: usize = 600;

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TimelinePoint {
    pub index: usize,
    pub step: String,
    pub time: Option<f64>,
    pub fill_percent: Option<f64>,
    pub eigenvalues: Option<Vec<f64>>,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct FrameView {
    pub index: usize,
    pub step: String,
    pub time: Option<f64>,
    pub state: Vec<f64>,
    pub input: Vec<f64>,
    pub noise: Vec<f64>,
    pub fill_percent: Option<f64>,
    pub eigenvalues: Option<Vec<f64>>,
    pub retention_used: Option<f64>,
    pub semantic_turn_id: Option<String>,
    pub next_retention: Option<f64>,
    pub lesson_evidence: Option<reservoir_core::guided_evidence::LessonEvidence>,
    pub regulation_evidence: Option<reservoir_core::regulation::RegulationWindowEvidence>,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TurnView {
    pub index: usize,
    pub id: String,
    pub observed_step: Option<String>,
    pub application_step: Option<String>,
    pub status: String,
    pub backend: Option<String>,
    pub model: Option<String>,
    pub prompt: String,
    pub reply: Option<String>,
    pub encoded_features: Option<Vec<f64>>,
    pub semantic_vector: Option<Vec<f64>>,
    pub failure: Option<String>,
    pub journal_saved: Option<bool>,
    pub raw_reply: Option<String>,
    pub requested_action: Option<String>,
    pub chosen_action: Option<String>,
    pub context_kind: Option<String>,
    pub memory_entry_ids: Vec<String>,
    pub journal_relative_path: Option<String>,
    pub configured_model: Option<String>,
    pub provider_model: Option<String>,
    pub request_started: Option<bool>,
    pub tape_packet_id: Option<String>,
    pub failure_phase: Option<String>,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TrackSummary {
    pub id: String,
    pub label: String,
    pub frame_count: usize,
    pub turn_count: usize,
    pub backend: Option<String>,
    pub model: Option<String>,
    pub timeline_stride: usize,
    pub timeline: Vec<TimelinePoint>,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct StudyNotes {
    pub question: String,
    pub expected_difference: String,
    pub alternative_explanation: String,
    pub stopping_point: String,
    pub evaluation_first_step: usize,
    pub evaluation_last_step: usize,
    pub target_fill_percent: f64,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RecordSummary {
    pub record_id: String,
    pub title: String,
    pub family: String,
    pub format: String,
    pub origin: String,
    pub filename: String,
    pub sha256: String,
    pub seed: Option<String>,
    pub outcome: String,
    pub tracks: Vec<TrackSummary>,
    pub verification: VerificationReport,
    pub study: Option<StudyNotes>,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct OpenResult {
    pub request_id: String,
    pub cancelled: bool,
    pub report: Option<VerificationReport>,
    pub record: Option<RecordSummary>,
}
impl OpenResult {
    pub fn cancelled(request_id: String) -> Self {
        Self {
            request_id,
            cancelled: true,
            report: None,
            record: None,
        }
    }
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct FrameResult {
    pub request_id: String,
    pub record_id: String,
    pub track_id: String,
    pub frame: FrameView,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TurnResult {
    pub request_id: String,
    pub record_id: String,
    pub track_id: String,
    pub turn: TurnView,
}
struct Track {
    frames: Vec<FrameView>,
    turns: Vec<TurnView>,
}
struct Entry {
    bytes: Arc<Vec<u8>>,
    filename: String,
    tracks: HashMap<String, Track>,
}
#[derive(Default)]
struct Store {
    next: u64,
    entries: HashMap<String, Entry>,
}
#[derive(Clone, Default)]
pub struct RecordState {
    store: Arc<Mutex<Store>>,
    operation: Arc<AtomicBool>,
}
pub struct OperationGuard(Arc<AtomicBool>);
impl Drop for OperationGuard {
    fn drop(&mut self) {
        self.0.store(false, Ordering::Release);
    }
}
impl RecordState {
    /// Do not accumulate reads/verifiers or native dialogs on the worker pool.
    pub fn begin_operation(&self) -> Result<OperationGuard, AppError> {
        self.operation
            .compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
            .map_err(|_| {
                AppError::new(
                    "records",
                    "busy",
                    "A file operation is already in progress. Wait for it to finish.",
                )
            })?;
        Ok(OperationGuard(self.operation.clone()))
    }
    fn lock(&self) -> Result<std::sync::MutexGuard<'_, Store>, AppError> {
        self.store.lock().map_err(|_| {
            AppError::new(
                "records",
                "store",
                "Record storage is unavailable. Reopen the application.",
            )
        })
    }
    pub fn open(
        &self,
        request_id: String,
        filename: String,
        origin: &str,
        bytes: Vec<u8>,
    ) -> Result<OpenResult, AppError> {
        {
            let store = self.lock()?;
            if store.entries.len() >= MAX_HANDLES
                || store.entries.values().map(|e| e.bytes.len()).sum::<usize>() + bytes.len()
                    > MAX_RETAINED_BYTES
            {
                return Err(AppError::new("open-record", "capacity", "Temporary record capacity is full (4 handles or 256 MiB of source bytes). Close a recording before opening another."));
            }
        }
        let inspection = inspect_bytes(bytes);
        let report = inspection.report;
        let bytes = inspection.original_bytes;
        if report.status != VerificationStatus::Passed {
            return Ok(OpenResult {
                request_id,
                cancelled: false,
                report: Some(report),
                record: None,
            });
        }
        let format = report.format.clone().unwrap_or_default();
        // Views contain only the typed fields the verifier interprets. Unknown
        // original JSON fields remain exportable, but cannot introduce "verified"
        // fill, replies or provenance from another record family.
        let mut action_record = None;
        let mut regulation_record = None;
        let value = if let Some(stage) = inspection.stage_record {
            serde_json::to_value(stage)
        } else if format == "essentials-exploration-v1" {
            serde_json::from_slice::<reservoir_core::exploration::ExplorationRecord>(&bytes)
                .and_then(serde_json::to_value)
        } else if reservoir_core::actions::FORMATS.contains(&format.as_str()) {
            serde_json::from_slice::<reservoir_core::actions::ActionComparisonRecord>(&bytes)
                .and_then(|record| {
                    let value = serde_json::to_value(&record)?;
                    action_record = Some(record);
                    Ok(value)
                })
        } else if format == reservoir_core::regulation::FORMAT {
            serde_json::from_slice::<reservoir_core::regulation::RegulationExampleRecord>(&bytes)
                .and_then(|record| {
                    let value = serde_json::to_value(&record)?;
                    regulation_record = Some(record);
                    Ok(value)
                })
        } else {
            return Err(AppError::new(
                "open-record",
                "unsupported-view",
                "This verified family has no desktop inspection view yet.",
            ));
        }
        .map_err(|e| AppError::new("open-record", "decode-view", e.to_string()))?;
        let mut tracks = HashMap::new();
        let mut summaries = vec![];
        let spec = &value["specification"];
        let (family, title) = if format == "essentials-v1" {
            let stage = spec["stage"].as_u64().unwrap_or(0);
            let label = match stage {
                1 => "Reservoir",
                2 => "Sensory field",
                3 => "Language return",
                4 => "Regulation",
                _ => "Stage",
            };
            let (summary, track) = make_track("main", label, &value, spec)?;
            summaries.push(summary);
            tracks.insert("main".into(), track);
            ("stage", format!("Stage {stage} · {label}"))
        } else if format == "essentials-exploration-v1" {
            let (summary, track) = make_track("main", "Exploration", &value, spec)?;
            summaries.push(summary);
            tracks.insert("main".into(), track);
            ("exploration", "Recorded exploration".into())
        } else if matches!(
            format.as_str(),
            "essentials-actions-v1" | "essentials-actions-v2" | "essentials-actions-v3"
        ) {
            for id in ["left", "right"] {
                if value[id].is_object() {
                    let label = format!(
                        "{} · {}",
                        if id == "left" { "Left" } else { "Right" },
                        value[id]["stage"]
                            .as_u64()
                            .map(|n| format!(
                                "component {}",
                                (b'A' + n.saturating_sub(1) as u8) as char
                            ))
                            .unwrap_or_else(|| "recorded arm".into())
                    );
                    let (summary, track) = make_track(id, &label, &value[id], spec)?;
                    summaries.push(summary);
                    tracks.insert(id.into(), track);
                }
            }
            ("actions", "Recorded action comparison".into())
        } else if let Some(record) = regulation_record.as_ref() {
            for (id, label) in [
                ("baseline", "Baseline sensory field"),
                ("regulated", "Regulated sensory field"),
            ] {
                // These fields are not reservoir activations. No synthetic state
                // surface or language-turn history is constructed for this family.
                let projected = serde_json::json!({"frames": record.frames.iter().map(|f| {
                    let arm = if id == "baseline" { &f.baseline } else { &f.regulated };
                    serde_json::json!({"step":f.step,"time":f.time,"input":f.input,
                        "spectral":arm.spectral,"fillPercent":arm.fill_percent,
                        "retentionUsed":arm.retention_used,"control":arm.control})
                }).collect::<Vec<_>>()});
                let (summary, track) = make_track(id, label, &projected, spec)?;
                summaries.push(summary);
                tracks.insert(id.into(), track);
            }
            ("regulation", "Controller mechanism · sensory fields".into())
        } else {
            return Err(AppError::new(
                "open-record",
                "unsupported-view",
                "This verified family has no desktop inspection view yet.",
            ));
        };
        // Evaluate each bounded recorded cursor from typed, verified data once.
        // Evidence travels atomically with its frame, so rewind/track changes
        // cannot retain a later conclusion or race a separate evidence request.
        if let Some(record) = action_record.as_ref() {
            let mut evidence = HashMap::new();
            for track in tracks.values_mut() {
                for frame in &mut track.frames {
                    let step = frame
                        .step
                        .parse::<usize>()
                        .map_err(|e| AppError::new("open-record", "step", e.to_string()))?;
                    frame.lesson_evidence = Some(
                        evidence
                            .entry(step)
                            .or_insert_with(|| {
                                reservoir_core::guided_evidence::evaluate(record, step)
                            })
                            .clone(),
                    );
                }
            }
        }
        if let Some(record) = regulation_record.as_ref() {
            for track in tracks.values_mut() {
                for frame in &mut track.frames {
                    frame.regulation_evidence = record.window_evidence(frame.index + 1);
                }
            }
        }
        let study = regulation_record.as_ref().map(|r| StudyNotes {
            question: r.specification.question.clone(),
            expected_difference: r.specification.expected_difference.clone(),
            alternative_explanation: r.specification.alternative_explanation.clone(),
            stopping_point: r.specification.stopping_point.clone(),
            evaluation_first_step: r.specification.evaluation_first_step,
            evaluation_last_step: r.specification.evaluation_last_step,
            target_fill_percent: r.specification.target_fill_percent,
        });
        let mut store = self.lock()?;
        // Recheck at publication so independent callers cannot exceed the bound.
        if store.entries.len() >= MAX_HANDLES
            || store.entries.values().map(|e| e.bytes.len()).sum::<usize>() + bytes.len()
                > MAX_RETAINED_BYTES
        {
            return Err(AppError::new(
                "open-record",
                "capacity",
                "Temporary record capacity was reached. Close a recording and retry.",
            ));
        }
        store.next = store.next.checked_add(1).ok_or_else(|| {
            AppError::new(
                "open-record",
                "identity",
                "Record identity exhausted. Reopen the application.",
            )
        })?;
        let record_id = format!("record-{}", store.next);
        let summary = RecordSummary {
            record_id: record_id.clone(),
            title,
            family: family.into(),
            format,
            origin: origin.into(),
            filename: filename.clone(),
            sha256: files::digest(&bytes),
            seed: integer(&spec["seed"])
                .or_else(|| integer(&value["seed"]))
                .or_else(|| integer(&spec["fieldSeed"])),
            outcome: string(&value["status"]).unwrap_or_else(|| "retained snapshot".into()),
            tracks: summaries,
            verification: report.clone(),
            study,
        };
        store.entries.insert(
            record_id,
            Entry {
                bytes: Arc::new(bytes),
                filename,
                tracks,
            },
        );
        Ok(OpenResult {
            request_id,
            cancelled: false,
            report: Some(report),
            record: Some(summary),
        })
    }
    pub fn frame(
        &self,
        request_id: String,
        record_id: String,
        track_id: String,
        index: usize,
    ) -> Result<FrameResult, AppError> {
        let store = self.lock()?;
        let frame = store
            .entries
            .get(&record_id)
            .and_then(|e| e.tracks.get(&track_id))
            .and_then(|t| t.frames.get(index))
            .ok_or_else(|| {
                AppError::new(
                    "record-frame",
                    "range",
                    "This frame or recording is no longer available.",
                )
            })?
            .clone();
        Ok(FrameResult {
            request_id,
            record_id,
            track_id,
            frame,
        })
    }
    pub fn turn(
        &self,
        request_id: String,
        record_id: String,
        track_id: String,
        index: usize,
    ) -> Result<TurnResult, AppError> {
        let store = self.lock()?;
        let turn = store
            .entries
            .get(&record_id)
            .and_then(|e| e.tracks.get(&track_id))
            .and_then(|t| t.turns.get(index))
            .ok_or_else(|| {
                AppError::new(
                    "record-turn",
                    "range",
                    "This text turn or recording is no longer available.",
                )
            })?
            .clone();
        Ok(TurnResult {
            request_id,
            record_id,
            track_id,
            turn,
        })
    }
    pub fn snapshot(&self, record_id: &str) -> Result<(String, Arc<Vec<u8>>), AppError> {
        let store = self.lock()?;
        let entry = store.entries.get(record_id).ok_or_else(|| {
            AppError::new(
                "export-record",
                "closed",
                "The recording is closed. Open it again before exporting.",
            )
        })?;
        Ok((entry.filename.clone(), entry.bytes.clone()))
    }
    pub fn close(&self, record_id: &str) -> Result<(), AppError> {
        self.lock()?.entries.remove(record_id);
        Ok(())
    }
}
fn string(value: &Value) -> Option<String> {
    value.as_str().map(str::to_owned)
}
fn integer(value: &Value) -> Option<String> {
    value.as_u64().map(|v| v.to_string())
}
fn numbers(value: &Value) -> Option<Vec<f64>> {
    value.as_array()?.iter().map(Value::as_f64).collect()
}
fn make_track(
    id: &str,
    label: &str,
    record: &Value,
    spec: &Value,
) -> Result<(TrackSummary, Track), AppError> {
    let raw_frames = record["frames"].as_array().ok_or_else(|| {
        AppError::new("open-record", "view", "Verified record has no frame array.")
    })?;
    let frames: Vec<FrameView> = raw_frames
        .iter()
        .enumerate()
        .map(|(index, f)| FrameView {
            index,
            step: integer(&f["step"]).unwrap_or_default(),
            time: f["time"].as_f64(),
            state: numbers(&f["state"]).unwrap_or_default(),
            input: numbers(&f["input"]).unwrap_or_default(),
            noise: numbers(&f["noise"]).unwrap_or_default(),
            fill_percent: f["fillPercent"].as_f64(),
            eigenvalues: numbers(&f["spectral"]["eigenvalues"]),
            retention_used: f["retentionUsed"].as_f64().or_else(|| {
                (f["controls"]["sensoryEnabled"].as_bool() == Some(true))
                    .then(|| f["controls"]["retention"].as_f64())
                    .flatten()
            }),
            semantic_turn_id: integer(&f["semanticTurnID"])
                .or_else(|| integer(&f["semanticActionID"])),
            next_retention: f["control"]["appliedRetention"].as_f64(),
            lesson_evidence: None,
            regulation_evidence: None,
        })
        .collect();
    let backend = string(&spec["language"]["backend"]);
    let model = string(&spec["language"]["model"]);
    let empty = vec![];
    let raw_turns = record["turns"]
        .as_array()
        .or_else(|| record["actions"].as_array())
        .unwrap_or(&empty);
    let journals = record["journals"].as_array().unwrap_or(&empty);
    let turns = raw_turns
        .iter()
        .enumerate()
        .map(|(index, t)| {
            let journal = journals
                .iter()
                .find(|j| j["id"].as_str().is_some() && j["id"] == t["journalEntryID"]);
            TurnView {
                index,
                id: integer(&t["id"]).unwrap_or_default(),
                observed_step: integer(&t["observedStep"]),
                application_step: integer(&t["applicationStep"]),
                status: string(&t["status"]).unwrap_or_else(|| "unknown".into()),
                backend: string(&t["backend"]).or_else(|| backend.clone()),
                model: string(&t["providerModel"])
                    .or_else(|| string(&t["model"]))
                    .or_else(|| model.clone()),
                prompt: string(&t["prompt"]).unwrap_or_default(),
                reply: string(&t["reply"]).or_else(|| journal.and_then(|j| string(&j["text"]))),
                encoded_features: numbers(&t["encodedFeatures"]),
                semantic_vector: numbers(&t["semanticVector"]),
                failure: string(&t["failure"]),
                journal_saved: t["saveReceipt"]["status"].as_str().map(|s| s == "saved"),
                raw_reply: string(&t["rawReply"]),
                requested_action: string(&t["requestedAction"]),
                chosen_action: string(&t["chosenAction"]),
                context_kind: string(&t["contextKind"]),
                memory_entry_ids: string(&t["memoryEntryID"]).into_iter().collect(),
                journal_relative_path: string(&t["saveReceipt"]["relativePath"]),
                configured_model: model.clone(),
                provider_model: string(&t["providerModel"]),
                request_started: t["requestStarted"].as_bool(),
                tape_packet_id: integer(&t["tapePacketID"]),
                failure_phase: string(&t["failurePhase"]),
            }
        })
        .collect::<Vec<_>>();
    let stride = if frames.len() > MAX_TIMELINE_POINTS {
        (frames.len() - 1).div_ceil(MAX_TIMELINE_POINTS - 1)
    } else {
        1
    };
    let mut indices: Vec<usize> = (0..frames.len()).step_by(stride).collect();
    if let Some(last) = frames.len().checked_sub(1) {
        if indices.last() != Some(&last) {
            indices.push(last);
        }
    }
    let timeline = indices
        .into_iter()
        .map(|index| {
            let f = &frames[index];
            TimelinePoint {
                index,
                step: f.step.clone(),
                time: f.time,
                fill_percent: f.fill_percent,
                eigenvalues: f.eigenvalues.clone(),
            }
        })
        .collect();
    Ok((
        TrackSummary {
            id: id.into(),
            label: label.into(),
            frame_count: frames.len(),
            turn_count: turns.len(),
            backend,
            model,
            timeline_stride: stride,
            timeline,
        },
        Track { frames, turns },
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use reservoir_core::stage::{run_scripted, RunSpecification};
    fn example(stage: u8) -> Vec<u8> {
        let value = serde_json::json!({"stage":stage,"seed":u64::MAX,"steps":31,"dt":1.0/3.0,"leak":0.65,"noiseAmplitude":0.0,"initialRetention":0.955,"regulationEnabled":true,"turnEvery":30,"language":{"backend":"scripted"}});
        let spec: RunSpecification = serde_json::from_value(value).unwrap();
        serde_json::to_vec(&run_scripted(spec).unwrap()).unwrap()
    }
    #[test]
    fn controller_view_exposes_no_reservoir_and_only_reached_evaluation() {
        let bytes = std::fs::read(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("resources/example-regulation-controller.json"),
        )
        .unwrap();
        let state = RecordState::default();
        let record = state
            .open(
                "controller".into(),
                "controller.json".into(),
                "bundled",
                bytes.clone(),
            )
            .unwrap()
            .record
            .unwrap();
        assert_eq!(record.family, "regulation");
        assert_eq!(record.tracks.len(), 2);
        assert_eq!(record.study.as_ref().unwrap().evaluation_first_step, 301);
        for track in [&record.tracks[0], &record.tracks[1]] {
            assert_eq!(track.frame_count, 600);
            assert_eq!(track.turn_count, 0);
            let frame = |index| {
                state
                    .frame(
                        format!("frame-{index}"),
                        record.record_id.clone(),
                        track.id.clone(),
                        index,
                    )
                    .unwrap()
                    .frame
            };
            let before = frame(299);
            assert!(before.state.is_empty() && before.noise.is_empty());
            assert_eq!(before.input.len(), 66);
            assert!(before.regulation_evidence.is_none());
            assert!(before.lesson_evidence.is_none());
            assert_eq!(frame(300).regulation_evidence.unwrap().count, 1);
            let complete = frame(599).regulation_evidence.unwrap();
            assert!(complete.is_complete);
            assert_eq!(complete.count, 300);
            assert!(complete.regulated_mean_absolute_error < complete.baseline_mean_absolute_error);
            assert!(frame(0).regulation_evidence.is_none());
        }
        assert_eq!(
            state.snapshot(&record.record_id).unwrap().1.as_ref(),
            &bytes
        );
    }
    #[test]
    fn guided_evidence_moves_with_frame_and_rewinds_before_feedback() {
        let bytes = std::fs::read(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("resources/example-component-5.json"),
        )
        .unwrap();
        let state = RecordState::default();
        let record = state
            .open("guide".into(), "return.json".into(), "bundled", bytes)
            .unwrap()
            .record
            .unwrap();
        let frame = |index| {
            state
                .frame(
                    format!("frame-{index}"),
                    record.record_id.clone(),
                    "right".into(),
                    index,
                )
                .unwrap()
                .frame
        };
        let saved = frame(29).lesson_evidence.unwrap();
        assert_eq!(
            saved.state,
            reservoir_core::guided_evidence::LessonEvidenceState::NotYetObserved
        );
        assert_eq!(saved.evidence_steps, vec![30]);
        let returned = frame(30).lesson_evidence.unwrap();
        assert_eq!(
            returned.state,
            reservoir_core::guided_evidence::LessonEvidenceState::Observed
        );
        assert_eq!(returned.evidence_steps, vec![30, 31]);
        let rewind = frame(28).lesson_evidence.unwrap();
        assert_eq!(
            rewind.state,
            reservoir_core::guided_evidence::LessonEvidenceState::NotYetObserved
        );
        assert!(rewind.evidence_steps.is_empty());
    }
    #[test]
    fn verified_views_keep_wide_seed_missing_fill_and_exact_bytes() {
        let state = RecordState::default();
        let bytes = example(1);
        let opened = state
            .open(
                "request-a".into(),
                "example.json".into(),
                "external",
                bytes.clone(),
            )
            .unwrap();
        let record = opened.record.unwrap();
        assert_eq!(opened.request_id, "request-a");
        assert_eq!(record.seed.unwrap(), u64::MAX.to_string());
        assert!(record.tracks[0]
            .timeline
            .iter()
            .all(|f| f.fill_percent.is_none() && f.eigenvalues.is_none()));
        assert_eq!(
            state.snapshot(&record.record_id).unwrap().1.as_ref(),
            &bytes
        );
        let f = state
            .frame("f1".into(), record.record_id.clone(), "main".into(), 0)
            .unwrap();
        assert_eq!(f.frame.step, "1");
        assert_eq!(f.frame.state.len(), 32);
        assert!(state
            .frame(
                "bad".into(),
                record.record_id.clone(),
                "main".into(),
                usize::MAX
            )
            .is_err());
        state.close(&record.record_id).unwrap();
        assert!(state.snapshot(&record.record_id).is_err());
    }
    #[test]
    fn rejection_keeps_previous_and_unique_handles_are_independent() {
        let state = RecordState::default();
        let bytes = example(1);
        let a = state
            .open("a".into(), "a.json".into(), "external", bytes.clone())
            .unwrap()
            .record
            .unwrap();
        let bad = state
            .open("bad".into(), "bad.json".into(), "external", b"{}".to_vec())
            .unwrap();
        assert!(bad.record.is_none());
        assert_eq!(bad.report.unwrap().status, VerificationStatus::Incomplete);
        let b = state
            .open("b".into(), "a.json".into(), "external", bytes)
            .unwrap()
            .record
            .unwrap();
        assert_ne!(a.record_id, b.record_id);
        state.close(&b.record_id).unwrap();
        assert!(state.snapshot(&a.record_id).is_ok());
        let guard = state.begin_operation().unwrap();
        assert!(state.begin_operation().is_err());
        drop(guard);
        assert!(state.begin_operation().is_ok());
    }
    #[test]
    fn recorded_text_boundary_and_real_fill_survive_view_adapter() {
        let state = RecordState::default();
        let opened = state
            .open("a".into(), "stage4.json".into(), "bundled", example(4))
            .unwrap();
        let r = opened.record.unwrap();
        assert_eq!(r.tracks[0].turn_count, 1);
        let turn = state
            .turn("t1".into(), r.record_id.clone(), "main".into(), 0)
            .unwrap()
            .turn;
        assert_eq!(turn.observed_step.as_deref(), Some("30"));
        assert_eq!(turn.application_step.as_deref(), Some("31"));
        assert_eq!(turn.journal_saved, None);
        assert_eq!(turn.semantic_vector.unwrap().len(), 48);
        assert!(r.tracks[0]
            .timeline
            .iter()
            .all(|p| p.fill_percent.is_some()));
        assert!(state
            .frame("f".into(), r.record_id, "main".into(), 30)
            .unwrap()
            .frame
            .fill_percent
            .is_some());
    }

    #[test]
    fn actions_preserve_saved_journal_and_next_step_identity() {
        let state = RecordState::default();
        let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("resources");
        let (name, bytes) = crate::resources::record_example(&root, "component-8").unwrap();
        let r = state
            .open("action".into(), name, "bundled", bytes)
            .unwrap()
            .record
            .unwrap();
        assert_eq!(r.tracks.len(), 2);
        let turn = state
            .turn("t".into(), r.record_id.clone(), "right".into(), 0)
            .unwrap()
            .turn;
        assert_eq!(turn.journal_saved, Some(true));
        assert_eq!(turn.chosen_action.as_deref(), Some("WRITE_JOURNAL"));
        assert_eq!(turn.observed_step.as_deref(), Some("30"));
        assert_eq!(turn.application_step.as_deref(), Some("31"));
        assert!(turn.journal_relative_path.unwrap().starts_with("right/"));
        assert!(turn.reply.is_some() && turn.raw_reply.is_some());
        let frame = state
            .frame("f".into(), r.record_id, "right".into(), 30)
            .unwrap()
            .frame;
        assert_eq!(frame.semantic_turn_id.as_deref(), Some("1"));
    }

    #[test]
    fn historical_defaults_and_bounded_timeline_are_explicit() {
        let state = RecordState::default();
        let spec = RunSpecification {
            steps: 3000,
            ..Default::default()
        };
        let mut value = serde_json::to_value(run_scripted(spec).unwrap()).unwrap();
        for key in ["seed", "language"] {
            value["specification"].as_object_mut().unwrap().remove(key);
        }
        let r = state
            .open(
                "old".into(),
                "old.json".into(),
                "external",
                serde_json::to_vec(&value).unwrap(),
            )
            .unwrap()
            .record
            .unwrap();
        assert_eq!(r.seed.as_deref(), Some("20260909"));
        assert!(r.title.starts_with("Stage 1"));
        let t = &r.tracks[0];
        assert_eq!(t.backend.as_deref(), Some("scripted"));
        assert_eq!(t.frame_count, 3000);
        assert!(t.timeline.len() <= MAX_TIMELINE_POINTS);
        assert_eq!(t.timeline.first().unwrap().index, 0);
        assert_eq!(t.timeline.last().unwrap().index, 2999);
        assert!(t.timeline_stride > 1);
    }

    #[test]
    fn handle_capacity_is_visible_and_released_by_close() {
        let state = RecordState::default();
        let bytes = example(1);
        let mut ids = vec![];
        for _ in 0..MAX_HANDLES {
            ids.push(
                state
                    .open("x".into(), "x.json".into(), "external", bytes.clone())
                    .unwrap()
                    .record
                    .unwrap()
                    .record_id,
            );
        }
        assert_eq!(
            state
                .open("x".into(), "x.json".into(), "external", bytes.clone())
                .err()
                .unwrap()
                .category,
            "capacity"
        );
        state.close(&ids[0]).unwrap();
        assert!(state
            .open("x".into(), "x.json".into(), "external", bytes)
            .unwrap()
            .record
            .is_some());
    }
    #[test]
    fn ignored_fields_are_exportable_but_never_verified_display_evidence() {
        let state = RecordState::default();
        let mut engine = reservoir_core::exploration::ExplorationEngine::new(42);
        engine.advance(Default::default(), true).unwrap();
        let mut value = serde_json::to_value(engine.record()).unwrap();
        value["frames"][0]["fillPercent"] = serde_json::json!(68);
        value["frames"][0]["lessonEvidence"] = serde_json::json!({"state":"Observed", "observation":"invented evidence", "evidenceSteps":[1]});
        value["frames"][0]["regulationEvidence"] =
            serde_json::json!({"count":300, "isComplete":true});
        value["frames"][0]["nextRetention"] = serde_json::json!(0.5);
        let bytes = serde_json::to_vec(&value).unwrap();
        let r = state
            .open("e".into(), "e.json".into(), "external", bytes.clone())
            .unwrap()
            .record
            .unwrap();
        assert!(r.tracks[0].timeline[0].fill_percent.is_none());
        let frame = state
            .frame("evidence".into(), r.record_id.clone(), "main".into(), 0)
            .unwrap()
            .frame;
        assert!(frame.lesson_evidence.is_none());
        assert!(frame.regulation_evidence.is_none());
        assert!(frame.next_retention.is_none());
        assert!(state
            .frame("f".into(), r.record_id.clone(), "main".into(), 0)
            .unwrap()
            .frame
            .fill_percent
            .is_none());
        assert_eq!(state.snapshot(&r.record_id).unwrap().1.as_ref(), &bytes);
        let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("resources");
        let (_, original) = crate::resources::record_example(&root, "component-8").unwrap();
        let mut action: Value = serde_json::from_slice(&original).unwrap();
        let original_text = action["right"]["journals"][0]["text"]
            .as_str()
            .unwrap()
            .to_owned();
        action["right"]["actions"][0]["reply"] = serde_json::json!("invented unchecked reply");
        action["right"]["actions"][0]["backend"] = serde_json::json!("invented provider");
        action["right"]["actions"][0]["contextKind"] = serde_json::json!("invented context");
        let bytes = serde_json::to_vec(&action).unwrap();
        let r = state
            .open("a".into(), "a.json".into(), "external", bytes.clone())
            .unwrap()
            .record
            .unwrap();
        let t = state
            .turn("t".into(), r.record_id.clone(), "right".into(), 0)
            .unwrap()
            .turn;
        assert_eq!(t.reply.as_deref(), Some(original_text.as_str()));
        assert_eq!(t.backend.as_deref(), Some("scripted"));
        assert!(t.context_kind.is_none());
        assert_eq!(state.snapshot(&r.record_id).unwrap().1.as_ref(), &bytes);
    }
}
