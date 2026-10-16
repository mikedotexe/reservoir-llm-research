//! Inert, portable derivatives for reading activation writing without model setup.
use crate::files::{self, digest, AppError, FileProof};
use serde::{Deserialize, Serialize};
use std::{
    collections::{HashMap, HashSet},
    sync::{
        atomic::{AtomicBool, AtomicU64, Ordering},
        Arc, Mutex,
    },
};
use tauri::Manager;
use tauri_plugin_dialog::DialogExt;

const LIMIT: u64 = 4 * 1024 * 1024;
const FORMAT: &str = "activation-reading-collection-v1";
fn error(message: impl Into<String>) -> AppError {
    AppError::new("activation-reading", "verification", message)
}
fn hash(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
}
fn text(value: &str) -> bool {
    !value.trim().is_empty() && value.len() <= 65536
}

#[derive(Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ReadingCollection {
    pub format: String,
    pub title: String,
    pub scope: String,
    pub questions: Vec<String>,
    pub readings: Vec<Reading>,
}
#[derive(Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Reading {
    pub id: String,
    pub entries: Vec<Entry>,
    pub events: Vec<ReadingEvent>,
    pub disclosure: Disclosure,
}
#[derive(Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Entry {
    pub id: String,
    pub status: String,
    pub text: String,
    pub sha256: String,
    pub observed_step: u64,
    pub saved_step: Option<u64>,
    pub applied_step: Option<u64>,
    pub request_id: String,
    pub prompt: String,
    pub prompt_sha256: String,
    pub stop_reason: String,
    pub content_tokens: usize,
    pub source_response_sha256: String,
    pub event_ids: Vec<String>,
}
#[derive(Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ReadingEvent {
    pub id: String,
    pub kind: String,
    pub step: u64,
    pub observation: Option<String>,
}
#[derive(Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Disclosure {
    pub arm: String,
    pub source_attempt: String,
    pub source_session: String,
    pub source_format: String,
    pub record_sha256: String,
    pub model_manifest_sha256: String,
    pub calibration_sha256: String,
    pub model_id: String,
    pub model_revision: String,
    pub protocol: Protocol,
    pub notes: Vec<ReadingNote>,
}
#[derive(Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Protocol {
    pub seed: u64,
    pub steps_between: u64,
    pub journal_every: u64,
    pub max_journal_tokens: usize,
    pub gain: f64,
}
#[derive(Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ReadingNote {
    pub title: String,
    pub text: String,
    pub sha256: String,
    pub source_sha256: String,
    pub attribution: String,
}

impl ReadingCollection {
    pub fn decode(bytes: &[u8]) -> Result<Self, AppError> {
        if bytes.len() > LIMIT as usize {
            return Err(error("Reading collection exceeds the 4 MiB limit"));
        }
        let value: Self = serde_json::from_slice(bytes).map_err(|e| error(e.to_string()))?;
        value.validate()?;
        Ok(value)
    }
    fn validate(&self) -> Result<(), AppError> {
        if self.format != FORMAT
            || !text(&self.title)
            || !text(&self.scope)
            || !(1..=3).contains(&self.readings.len())
            || self.questions.len() > 12
            || self.questions.iter().any(|q| !text(q))
        {
            return Err(error("Unsupported collection format or reading bounds"));
        }
        let mut readings = HashSet::new();
        for reading in &self.readings {
            if !text(&reading.id)
                || !readings.insert(&reading.id)
                || reading.entries.is_empty()
                || reading.entries.len() > 100
                || reading.events.len() > 10000
            {
                return Err(error("Invalid reading identities or bounds"));
            }
            let mut event_ids = HashSet::new();
            let mut last_step = 0;
            for event in &reading.events {
                if !text(&event.id)
                    || !event_ids.insert(&event.id)
                    || event.step < last_step
                    || event.step > 1_000_000_000
                    || !matches!(
                        event.kind.as_str(),
                        "requestStarted"
                            | "quietReceived"
                            | "journalReceived"
                            | "journalSaved"
                            | "journalApplied"
                            | "failed"
                    )
                    || event.observation.as_ref().is_some_and(|v| !text(v))
                {
                    return Err(error("Invalid chronological event boundary"));
                }
                last_step = event.step;
            }
            let mut entries = HashSet::new();
            let mut requests = HashSet::new();
            let mut writing_events = HashSet::new();
            let mut prior_step = None;
            let mut incomplete = false;
            for entry in &reading.entries {
                if incomplete
                    || !text(&entry.id)
                    || !entries.insert(&entry.id)
                    || !text(&entry.text)
                    || !text(&entry.prompt)
                    || digest(entry.text.as_bytes()) != entry.sha256
                    || digest(entry.prompt.as_bytes()) != entry.prompt_sha256
                    || !hash(&entry.source_response_sha256)
                    || prior_step.is_some_and(|prior| entry.observed_step <= prior)
                    || entry.observed_step > last_step
                    || !text(&entry.request_id)
                    || !requests.insert(&entry.request_id)
                    || !text(&entry.stop_reason)
                    || entry.content_tokens > 1024
                    || entry.event_ids.is_empty()
                    || entry.event_ids.iter().collect::<HashSet<_>>().len() != entry.event_ids.len()
                    || entry.event_ids.iter().any(|id| !event_ids.contains(id))
                    || entry.event_ids.iter().any(|id| !writing_events.insert(id))
                {
                    return Err(error(
                        "Writing content hash, chronology or event reference differs",
                    ));
                }
                match entry.status.as_str() {
                    "complete"
                        if entry.saved_step == Some(entry.observed_step)
                            && entry.applied_step
                                == entry.saved_step.and_then(|v| v.checked_add(1)) => {}
                    "incomplete" if entry.saved_step.is_none() && entry.applied_step.is_none() => {
                        incomplete = true;
                    }
                    _ => return Err(error("Invalid completion, save or feedback boundary")),
                }
                let linked: Vec<_> = reading
                    .events
                    .iter()
                    .filter(|e| entry.event_ids.contains(&e.id))
                    .collect();
                let boundary = |kind: &str, step: u64| {
                    linked
                        .iter()
                        .filter(|e| e.kind == kind && e.step == step)
                        .count()
                        == 1
                };
                let ordered_kinds: &[&str] = if entry.status == "complete" {
                    &[
                        "requestStarted",
                        "journalReceived",
                        "journalSaved",
                        "journalApplied",
                    ]
                } else {
                    &["requestStarted", "failed"]
                };
                if linked
                    .iter()
                    .map(|event| event.kind.as_str())
                    .ne(ordered_kinds.iter().copied())
                    || !boundary("requestStarted", entry.observed_step)
                    || linked.iter().any(|e| e.observation.is_some())
                    || (entry.status == "complete"
                        && (linked.len() != 4
                            || !boundary("journalReceived", entry.observed_step)
                            || !boundary("journalSaved", entry.observed_step)
                            || !boundary("journalApplied", entry.applied_step.unwrap())))
                    || (entry.status == "incomplete"
                        && (linked.len() != 2 || !boundary("failed", entry.observed_step)))
                {
                    return Err(error(
                        "Writing references do not identify its request and completion boundaries",
                    ));
                }
                prior_step = Some(entry.observed_step);
            }
            let d = &reading.disclosure;
            if !matches!(
                d.arm.as_str(),
                "no_steering" | "decaying_trace" | "recurrent"
            ) || !matches!(
                d.source_format.as_str(),
                "activation-session-v1" | "activation-cohort-session-v1"
            ) || [
                &d.source_attempt,
                &d.source_session,
                &d.model_id,
                &d.model_revision,
            ]
            .iter()
            .any(|v| !text(v))
                || [
                    &d.record_sha256,
                    &d.model_manifest_sha256,
                    &d.calibration_sha256,
                ]
                .iter()
                .any(|v| !hash(v))
                || d.protocol.steps_between == 0
                || d.protocol.journal_every == 0
                || d.protocol.max_journal_tokens != 1024
                || !d.protocol.gain.is_finite()
                || !(0.0..=0.01).contains(&d.protocol.gain)
                || d.notes.len() > 20
            {
                return Err(error("Invalid disclosed provenance or protocol"));
            }
            for note in &d.notes {
                if !text(&note.title)
                    || !text(&note.text)
                    || !text(&note.attribution)
                    || !hash(&note.source_sha256)
                    || digest(note.text.as_bytes()) != note.sha256
                {
                    return Err(error("Reading-note content hash differs"));
                }
            }
        }
        Ok(())
    }
}

#[derive(Clone, Default)]
pub struct ReadingCollectionState {
    inner: Arc<Mutex<HashMap<String, Arc<Vec<u8>>>>>,
    serial: Arc<AtomicU64>,
    busy: Arc<AtomicBool>,
}
struct ReadingGuard(Arc<AtomicBool>);
impl Drop for ReadingGuard {
    fn drop(&mut self) {
        self.0.store(false, Ordering::Release);
    }
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct OpenedReadingCollection {
    pub collection_id: String,
    pub sha256: String,
    pub collection: ReadingCollection,
}
impl ReadingCollectionState {
    fn begin(&self) -> Result<ReadingGuard, AppError> {
        self.busy
            .compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
            .map_err(|_| error("A reading-file operation is already in progress"))?;
        Ok(ReadingGuard(self.busy.clone()))
    }
    pub fn open(&self, bytes: Vec<u8>) -> Result<OpenedReadingCollection, AppError> {
        let collection = ReadingCollection::decode(&bytes)?;
        let mut state = self
            .inner
            .lock()
            .map_err(|_| error("Reading state unavailable"))?;
        if state.len() >= 4 {
            return Err(error("Close an open collection before opening another"));
        }
        let collection_id = format!(
            "activation-reading-{}",
            self.serial.fetch_add(1, Ordering::Relaxed)
        );
        let sha256 = digest(&bytes);
        state.insert(collection_id.clone(), Arc::new(bytes));
        Ok(OpenedReadingCollection {
            collection_id,
            sha256,
            collection,
        })
    }
    fn snapshot(&self, id: &str) -> Result<Arc<Vec<u8>>, AppError> {
        self.inner
            .lock()
            .map_err(|_| error("Reading state unavailable"))?
            .get(id)
            .cloned()
            .ok_or_else(|| error("This collection is no longer open"))
    }
    fn close(&self, id: &str) -> Result<(), AppError> {
        self.inner
            .lock()
            .map_err(|_| error("Reading state unavailable"))?
            .remove(id);
        Ok(())
    }
}

#[tauri::command]
pub async fn activation_reading_open(
    app: tauri::AppHandle,
    state: tauri::State<'_, ReadingCollectionState>,
    bundled: bool,
) -> Result<Option<OpenedReadingCollection>, AppError> {
    let guard = state.begin()?;
    let state = state.inner().clone();
    let root = app
        .path()
        .resource_dir()
        .map_err(|e| error(e.to_string()))?;
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = guard;
        let path = if bundled {
            root.join("examples/activation-preview-v1.json")
        } else {
            let Some(file) = app
                .dialog()
                .file()
                .set_title("Open activation reading collection")
                .add_filter("Reading collection", &["json"])
                .blocking_pick_file()
            else {
                return Ok(None);
            };
            file.into_path().map_err(|e| error(e.to_string()))?
        };
        state
            .open(files::read_bounded(&path, LIMIT, "activation-reading")?)
            .map(Some)
    })
    .await
    .map_err(|e| error(e.to_string()))?
}

#[tauri::command]
pub async fn activation_reading_export(
    app: tauri::AppHandle,
    state: tauri::State<'_, ReadingCollectionState>,
    collection_id: String,
) -> Result<Option<FileProof>, AppError> {
    let guard = state.begin()?;
    let bytes = state.snapshot(&collection_id)?;
    let root = app
        .path()
        .resource_dir()
        .map_err(|e| error(e.to_string()))?;
    tauri::async_runtime::spawn_blocking(move || {
        let _guard = guard;
        let Some(file) = app
            .dialog()
            .file()
            .set_title("Export portable activation reading collection")
            .set_file_name("activation-reading.json")
            .add_filter("Reading collection", &["json"])
            .blocking_save_file()
        else {
            return Ok(None);
        };
        let path = file.into_path().map_err(|e| error(e.to_string()))?;
        files::atomic_export(&path, &bytes, &root).map(Some)
    })
    .await
    .map_err(|e| error(e.to_string()))?
}

#[tauri::command]
pub fn activation_reading_close(
    state: tauri::State<'_, ReadingCollectionState>,
    collection_id: String,
) -> Result<(), AppError> {
    state.close(&collection_id)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::{json, Value};
    fn fixture() -> Value {
        json!({"format":FORMAT,"title":"Synthetic reading","scope":"Synthetic fixture, no model output","questions":["What changes?"],"readings":[{"id":"reading-a","entries":[{"id":"entry-1","status":"complete","text":"Complete synthetic writing.","sha256":digest(b"Complete synthetic writing."),"observedStep":20,"savedStep":20,"appliedStep":21,"requestId":"request-1","prompt":"Synthetic invitation","promptSha256":digest(b"Synthetic invitation"),"stopReason":"eos","contentTokens":4,"sourceResponseSha256":"a".repeat(64),"eventIds":["event-1","event-2","event-3","event-4"]}],"events":[{"id":"event-1","kind":"requestStarted","step":20,"observation":null},{"id":"event-2","kind":"journalReceived","step":20,"observation":null},{"id":"event-3","kind":"journalSaved","step":20,"observation":null},{"id":"event-4","kind":"journalApplied","step":21,"observation":null}],"disclosure":{"arm":"no_steering","sourceAttempt":"Synthetic","sourceSession":"synthetic","sourceFormat":"activation-session-v1","recordSha256":"a".repeat(64),"modelManifestSha256":"b".repeat(64),"calibrationSha256":"c".repeat(64),"modelId":"synthetic","modelRevision":"synthetic","protocol":{"seed":1,"stepsBetween":10,"journalEvery":2,"maxJournalTokens":1024,"gain":0.01},"notes":[]}}]})
    }
    fn bytes(value: &Value) -> Vec<u8> {
        serde_json::to_vec(value).unwrap()
    }
    #[test]
    fn reading_roundtrip_preserves_exact_bytes_and_cannot_replace_on_failure() {
        let mut raw = bytes(&fixture());
        raw.extend_from_slice(b"\n  ");
        let state = ReadingCollectionState::default();
        let opened = state.open(raw.clone()).unwrap();
        assert!(state.open(b"{}".to_vec()).is_err());
        assert_eq!(
            state.snapshot(&opened.collection_id).unwrap().as_slice(),
            raw
        );
        let folder = tempfile::tempdir().unwrap();
        let path = folder.path().join("reading.json");
        files::atomic_export(&path, &raw, &folder.path().join("resources")).unwrap();
        let again = state.open(std::fs::read(path).unwrap()).unwrap();
        assert_eq!(opened.sha256, again.sha256);
        state.close(&opened.collection_id).unwrap();
        assert!(state.snapshot(&opened.collection_id).is_err());
    }
    #[test]
    fn rejects_changed_text_prompt_dangling_references_and_executable_fields() {
        for pointer in [
            "/readings/0/entries/0/text",
            "/readings/0/entries/0/prompt",
            "/readings/0/entries/0/eventIds/0",
            "/readings/0/disclosure/recordSha256",
        ] {
            let mut value = fixture();
            *value.pointer_mut(pointer).unwrap() = json!("changed");
            assert!(
                ReadingCollection::decode(&bytes(&value)).is_err(),
                "{pointer}"
            );
        }
        let mut value = fixture();
        value["readings"][0]["config"] = json!({"pythonPath":"/untrusted/python"});
        assert!(ReadingCollection::decode(&bytes(&value)).is_err());
    }
    #[test]
    fn incomplete_is_visible_but_never_a_saved_or_applied_journal() {
        let mut value = fixture();
        let entry = &mut value["readings"][0]["entries"][0];
        entry["status"] = json!("incomplete");
        entry["savedStep"] = Value::Null;
        entry["appliedStep"] = Value::Null;
        entry["eventIds"] = json!(["event-1", "event-2"]);
        value["readings"][0]["events"] = json!([{"id":"event-1","kind":"requestStarted","step":20,"observation":null},{"id":"event-2","kind":"failed","step":20,"observation":null}]);
        assert!(ReadingCollection::decode(&bytes(&value)).is_ok());
        value["readings"][0]["entries"][0]["appliedStep"] = json!(21);
        assert!(ReadingCollection::decode(&bytes(&value)).is_err());
    }
    #[test]
    fn one_writing_boundary_cannot_be_counted_twice() {
        let mut value = fixture();
        let mut duplicate = value["readings"][0]["entries"][0].clone();
        duplicate["id"] = json!("another-entry");
        value["readings"][0]["entries"]
            .as_array_mut()
            .unwrap()
            .push(duplicate);
        assert!(ReadingCollection::decode(&bytes(&value)).is_err());
    }
    #[test]
    fn same_step_boundaries_must_preserve_request_receive_save_order() {
        for (left, right) in [(0, 1), (1, 2), (0, 2)] {
            let mut value = fixture();
            value["readings"][0]["events"]
                .as_array_mut()
                .unwrap()
                .swap(left, right);
            assert!(
                ReadingCollection::decode(&bytes(&value)).is_err(),
                "reversed {left}/{right}"
            );
        }
        let mut value = fixture();
        let entry = &mut value["readings"][0]["entries"][0];
        entry["status"] = json!("incomplete");
        entry["savedStep"] = Value::Null;
        entry["appliedStep"] = Value::Null;
        entry["eventIds"] = json!(["event-1", "event-2"]);
        value["readings"][0]["events"] = json!([
            {"id":"event-2","kind":"failed","step":20,"observation":null},
            {"id":"event-1","kind":"requestStarted","step":20,"observation":null}
        ]);
        assert!(ReadingCollection::decode(&bytes(&value)).is_err());
    }
    #[test]
    fn reading_dialog_operations_are_bounded_and_serialized() {
        let state = ReadingCollectionState::default();
        let guard = state.begin().unwrap();
        assert!(state.begin().is_err());
        drop(guard);
        assert!(state.begin().is_ok());
        for _ in 0..4 {
            state.open(bytes(&fixture())).unwrap();
        }
        assert!(state.open(bytes(&fixture())).is_err());
        assert!(ReadingCollection::decode(&vec![b' '; LIMIT as usize + 1]).is_err());
    }
}
