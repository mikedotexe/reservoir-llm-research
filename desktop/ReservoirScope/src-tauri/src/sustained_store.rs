//! Bounded, app-owned sustained bundles. A manifest names a committed prefix;
//! leftover objects are never promoted to history merely because they exist.
use crate::files::{self, AppError};
use crate::sustained::SustainedConfig;
use reservoir_core::session::{ProviderPromptEvaluation, ProviderPromptEvaluationIssue};
use reservoir_core::stage::LanguageKind;
use reservoir_core::sustained::{
    self as core, SustainedCheckpoint, SustainedEventKind, SustainedJournal,
    SustainedPendingJournal, SustainedSaveReceipt, SustainedSegment, SustainedSession,
};
use serde::{Deserialize, Serialize};
use std::{
    collections::{BTreeMap, VecDeque},
    fs,
    io::Write,
    path::{Path, PathBuf},
};

const OWNER: &[u8] = b"reservoir-scope-sustained-v1\n";
pub const OBJECT_LIMIT: u64 = 4 * 1024 * 1024;
const MANIFEST_LIMIT: u64 = 128 * 1024;
// Low water is one maximum accepted segment/checkpoint transaction. The actual
// candidate is sized separately; this is not a second up-front transaction.
pub const RUN_HEADROOM: u64 = 2 * OBJECT_LIMIT + MANIFEST_LIMIT;
const HEADROOM_DIAGNOSTIC: &str = "Storage headroom reached; the exact current boundary is retained and further execution is held. Stop or explicitly skip pending feedback before closing.";
pub fn storage_held(manifest: &Manifest) -> bool {
    manifest
        .diagnostics
        .iter()
        .any(|d| d == HEADROOM_DIAGNOSTIC)
}
pub fn hold_storage(manifest: &mut Manifest) {
    manifest.phase = "budgetReached".into();
    if !storage_held(manifest) {
        manifest.diagnostics.push(HEADROOM_DIAGNOSTIC.into());
        trim_diagnostics(manifest);
    }
}
pub fn trim_diagnostics(manifest: &mut Manifest) {
    while manifest.diagnostics.len() > 32 {
        let removable = manifest
            .diagnostics
            .iter()
            .position(|d| d != HEADROOM_DIAGNOSTIC)
            .unwrap_or(0);
        manifest.diagnostics.remove(removable);
    }
}
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Admission {
    Ordinary,
    Stop,
    Skip,
    Close,
}
const MAX_SEGMENTS: u64 = 100_000;
const MAX_OBJECTS: u64 = MAX_SEGMENTS + 20_100;
fn err(kind: &str, message: impl Into<String>) -> AppError {
    AppError::new("sustained-storage", kind, message)
}
fn io(e: std::io::Error) -> AppError {
    err("io", e.to_string())
}
fn ce(e: impl std::fmt::Display) -> AppError {
    err("verification", e.to_string())
}
pub fn valid_id(id: &str) -> bool {
    !id.is_empty() && id.len() <= 128 && id.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-')
}
fn hash(s: &str) -> bool {
    s.len() == 64
        && s.bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn json<T: Serialize + ?Sized>(v: &T) -> Result<Vec<u8>, AppError> {
    serde_json::to_vec(v).map_err(ce)
}
fn typed<T: serde::de::DeserializeOwned>(p: &Path, limit: u64) -> Result<T, AppError> {
    serde_json::from_slice(&files::read_bounded(p, limit, "sustained-read")?).map_err(ce)
}
pub fn ordinary(path: &Path) -> Result<(), AppError> {
    if !fs::symlink_metadata(path).map_err(io)?.file_type().is_dir() {
        return Err(err(
            "ownership",
            "Storage directories must be ordinary directories, never links.",
        ));
    }
    Ok(())
}
fn sync_parent(path: &Path) -> Result<(), AppError> {
    #[cfg(unix)]
    if let Some(p) = path.parent() {
        fs::File::open(p).and_then(|f| f.sync_all()).map_err(io)?;
    }
    #[cfg(not(unix))]
    let _ = path;
    Ok(())
}
fn directory(path: &Path) -> Result<(), AppError> {
    if path.exists() {
        ordinary(path)?;
    } else {
        let parent = path.parent().ok_or_else(|| err("path", "Missing parent"))?;
        if !parent.exists() {
            directory(parent)?;
        }
        ordinary(parent)?;
        fs::create_dir(path).map_err(io)?;
    }
    sync_parent(path)
}
fn resync(path: &Path) -> Result<(), AppError> {
    let mut o = fs::OpenOptions::new();
    o.read(true).write(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        o.custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK);
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt;
        o.custom_flags(0x0020_0000);
    }
    let f = o.open(path).map_err(io)?;
    if !f.metadata().map_err(io)?.is_file() {
        return Err(err(
            "ownership",
            "Owned object ceased to be an ordinary file",
        ));
    }
    f.sync_all().map_err(io)?;
    sync_parent(path)
}
fn publish(path: &Path, bytes: &[u8], replace: bool) -> Result<(), AppError> {
    let parent = path.parent().ok_or_else(|| err("path", "Missing parent"))?;
    ordinary(parent)?;
    if let Ok(m) = fs::symlink_metadata(path) {
        if !m.file_type().is_file() {
            return Err(err("ownership", "Destination is not an ordinary file"));
        }
        if !replace {
            if files::read_bounded(path, OBJECT_LIMIT, "existing-object")? != bytes {
                return Err(err(
                    "conflict",
                    "Immutable object already exists with different bytes",
                ));
            }
            return resync(path);
        }
    }
    let mut tmp = tempfile::Builder::new()
        .prefix(".incomplete-")
        .tempfile_in(parent)
        .map_err(io)?;
    tmp.write_all(bytes)
        .and_then(|_| tmp.as_file().sync_all())
        .map_err(io)?;
    if files::read_bounded(tmp.path(), OBJECT_LIMIT, "staged-object")? != bytes {
        return Err(err("readback", "Staged object changed"));
    }
    if replace {
        tmp.persist(path)
            .map_err(|e| err("publish", e.to_string()))?;
    } else {
        tmp.persist_noclobber(path)
            .map_err(|e| err("publish", e.to_string()))?;
    }
    sync_parent(path)?;
    if files::read_bounded(path, OBJECT_LIMIT, "published-object")? != bytes {
        return Err(err("readback", "Published object changed"));
    }
    Ok(())
}

#[derive(Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Manifest {
    pub format: String,
    pub session_id: String,
    pub generation: String,
    pub revision: String,
    pub config: SustainedConfig,
    pub phase: String,
    pub step: u64,
    pub durable_step: u64,
    pub elapsed_millis: u64,
    pub journal_count: u64,
    pub segment_count: u64,
    pub last_segment_sha256: Option<String>,
    pub checkpoint_sha256: String,
    pub previous_checkpoint_sha256: Option<String>,
    pub diagnostics: Vec<String>,
    pub attempt_timing: Option<AttemptTiming>,
}
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct Envelope {
    format: String,
    sequence: u64,
    previous_sha256: Option<String>,
    segment: SustainedSegment,
    journal_sha256s: BTreeMap<String, String>,
}

/// Size the allowed Stop/cancel -> Skip -> close suffix for the actual candidate
/// state. Only a clone is changed. All three manifest replacements are reserved,
/// and old checkpoints are not subtracted before their eventual cleanup.
fn terminal_reserve(
    engine: &SustainedSession,
    admission: Admission,
) -> Result<(u64, u64), AppError> {
    let mut preview = engine.clone();
    if let Some(last) = preview.events().back() {
        preview.acknowledge_events(last.id).map_err(ce)?;
    }
    let manifests = match admission {
        Admission::Ordinary => 3,
        Admission::Stop => 2,
        Admission::Skip => 1,
        Admission::Close => 0,
    };
    let mut required = manifests * MANIFEST_LIMIT;
    let mut segments = 0;
    let reason = "\0".repeat(4096); // Maximum bounded reason and JSON escaping.
    for cancel in [true, false] {
        if (cancel && admission != Admission::Ordinary)
            || (!cancel && matches!(admission, Admission::Skip | Admission::Close))
        {
            continue;
        }
        let initial = preview.checkpoint();
        if cancel {
            if let Some(p) = preview.pending_language() {
                preview.cancel_language(p.attempt_id, &reason).map_err(ce)?;
            }
        } else if !matches!(preview.phase(), core::SustainedPhase::Ready) {
            preview.skip_pending(&reason).map_err(ce)?;
        }
        if preview.events().is_empty() {
            continue;
        }
        let final_checkpoint = preview.checkpoint();
        let cp = json(&final_checkpoint)?;
        let envelope = Envelope {
            format: "reservoir-sustained-chain-link-v1".into(),
            sequence: u64::MAX,
            previous_sha256: Some("0".repeat(64)),
            journal_sha256s: BTreeMap::new(),
            segment: SustainedSegment {
                format: core::FORMAT.into(),
                initial_checkpoint: initial,
                events: preview.events().iter().cloned().collect(),
                final_checkpoint,
            },
        };
        let segment = json(&envelope)?;
        if cp.len() as u64 > OBJECT_LIMIT || segment.len() as u64 > OBJECT_LIMIT {
            return Err(err(
                "budget",
                "Candidate's bounded terminal transition exceeds an object limit",
            ));
        }
        required += cp.len() as u64 + segment.len() as u64;
        segments += 1;
        if let Some(last) = preview.events().back() {
            preview.acknowledge_events(last.id).map_err(ce)?;
        }
    }
    Ok((required, segments))
}

/// Existing identical immutable objects need a sync/readback, not a second
/// allocation. Conflicting checkpoints never count as reusable capacity.
fn immutable_allocation(path: &Path, bytes: &[u8]) -> Result<u64, AppError> {
    match fs::symlink_metadata(path) {
        Ok(_) => {
            if files::read_bounded(path, OBJECT_LIMIT, "allocation")? != bytes {
                return Err(err(
                    "conflict",
                    "Immutable object differs during budget admission",
                ));
            }
            Ok(0)
        }
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(bytes.len() as u64),
        Err(e) => Err(io(e)),
    }
}
#[derive(Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct AttemptTiming {
    pub attempt_id: u64,
    pub dispatched_at_ms: Option<String>,
    pub received_at_ms: Option<String>,
    pub transport_duration_ms: Option<u64>,
    pub published_at_ms: Option<String>,
}
#[derive(Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct JournalObject {
    pub format: String,
    pub pending: SustainedPendingJournal,
    pub request_started: bool,
    pub configured_model: Option<String>,
    /// Sampling evidence; omitted for historical greedy journals.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub temperature: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sampling_seed: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub thinking: Option<bool>,
    pub timing: AttemptTiming,
}
/// The per-attempt sampler seed a sustained journal must carry, as a decimal string.
pub fn expected_sampling_seed(config: &SustainedConfig, attempt_id: u64) -> Option<String> {
    config
        .language
        .temperature
        .filter(|t| *t > 0.0)
        .and_then(|_| config.seed.parse::<u64>().ok())
        .map(|seed| reservoir_core::sustained::sampling_seed(seed, attempt_id).to_string())
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BundleReport {
    pub format: String,
    pub session_id: String,
    pub manifest_sha256: String,
    pub checkpoint_sha256: String,
    pub segment_count: u64,
    pub step: u64,
    pub journal_count: u64,
    pub size_bytes: u64,
    pub verification: String,
    pub diagnostics: Vec<String>,
}
pub struct Verified {
    pub manifest: Manifest,
    pub checkpoint: SustainedCheckpoint,
    pub report: BundleReport,
    pub received_responses: ReceivedResponses,
}
/// IPC projection only: stored response counts remain exact u64 JSON integers.
#[derive(Clone, Serialize)]
#[serde(tag = "status", rename_all = "camelCase")]
pub enum ProviderPromptEvaluationView {
    Reported {
        count: String,
    },
    Unusable {
        reason: ProviderPromptEvaluationIssue,
    },
}
impl From<&ProviderPromptEvaluation> for ProviderPromptEvaluationView {
    fn from(value: &ProviderPromptEvaluation) -> Self {
        match value {
            ProviderPromptEvaluation::Reported { count } => Self::Reported {
                count: count.to_string(),
            },
            ProviderPromptEvaluation::Unusable { reason } => Self::Unusable { reason: *reason },
        }
    }
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ReceivedResponseEvidence {
    pub attempt_id: String,
    pub observed_step: String,
    pub complete: bool,
    pub stop_reason: Option<String>,
    pub stop_reason_truncated: bool,
    pub token_count: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub provider_prompt_evaluation: Option<ProviderPromptEvaluationView>,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ReceivedResponses {
    pub total: usize,
    pub truncated: bool,
    pub entries: Vec<ReceivedResponseEvidence>,
}
const RECEIVED_RESPONSE_LIMIT: usize = 50;
const STOP_REASON_DISPLAY_CHARACTERS: usize = 256;

fn stop_reason_view(reason: Option<&str>) -> (Option<String>, bool) {
    let Some(reason) = reason else {
        return (None, false);
    };
    let mut chars = reason.chars();
    let text = chars
        .by_ref()
        .take(STOP_REASON_DISPLAY_CHARACTERS)
        .collect();
    (Some(text), chars.next().is_some())
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RecoveryEntry {
    pub session_id: String,
    pub generation: Option<String>,
    pub revision: Option<String>,
    pub phase: Option<String>,
    pub step: Option<u64>,
    pub durable_step: Option<u64>,
    pub journal_count: Option<u64>,
    pub diagnostic: Option<String>,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RecoveryPage {
    pub request_id: String,
    pub entries: Vec<RecoveryEntry>,
    pub complete: bool,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RecoveryDetail {
    pub request_id: String,
    pub manifest: Manifest,
    pub checkpoint: serde_json::Value,
    pub report: BundleReport,
    pub received_responses: ReceivedResponses,
}
#[derive(Clone)]
pub struct SustainedStore {
    pub root: PathBuf,
    #[cfg(test)]
    fault: std::sync::Arc<std::sync::atomic::AtomicU8>,
}
impl SustainedStore {
    pub fn new(root: PathBuf) -> Self {
        Self {
            root,
            #[cfg(test)]
            fault: std::sync::Arc::new(std::sync::atomic::AtomicU8::new(0)),
        }
    }
    #[cfg(test)]
    pub fn fail_next(&self, stage: u8) {
        self.fault.store(stage, std::sync::atomic::Ordering::SeqCst);
    }
    fn injected(&self, stage: u8) -> Result<(), AppError> {
        #[cfg(test)]
        if self
            .fault
            .compare_exchange(
                stage,
                0,
                std::sync::atomic::Ordering::SeqCst,
                std::sync::atomic::Ordering::SeqCst,
            )
            .is_ok()
        {
            return Err(err(
                "injected",
                format!("Injected durable stage {stage} failure"),
            ));
        }
        #[cfg(not(test))]
        let _ = stage;
        Ok(())
    }
    fn root(&self, create: bool) -> Result<(), AppError> {
        if create {
            directory(&self.root)?;
        } else {
            ordinary(&self.root)?;
        }
        let marker = self.root.join("owner");
        if !marker.exists() && create {
            publish(&marker, OWNER, false)?;
        }
        if files::read_bounded(&marker, 128, "owner")? != OWNER {
            return Err(err("ownership", "This is not an owned sustained store"));
        }
        Ok(())
    }
    pub fn path(&self, id: &str) -> Result<PathBuf, AppError> {
        if !valid_id(id) {
            return Err(err("identity", "Invalid session ID"));
        }
        Ok(self.root.join(id))
    }
    fn prepare(&self, id: &str) -> Result<PathBuf, AppError> {
        self.root(true)?;
        let p = self.path(id)?;
        directory(&p)?;
        for name in ["segments", "checkpoints", "journals"] {
            directory(&p.join(name))?;
        }
        Ok(p)
    }
    pub fn initialize(
        &self,
        manifest: &mut Manifest,
        checkpoint: &SustainedCheckpoint,
    ) -> Result<(), AppError> {
        let p = self.prepare(&manifest.session_id)?;
        if p.join("manifest.json").exists() {
            return Err(err("exists", "A session with that identity already exists"));
        }
        checkpoint.validate().map_err(ce)?;
        let bytes = json(checkpoint)?;
        manifest.checkpoint_sha256 = files::digest(&bytes);
        publish(
            &p.join("checkpoints")
                .join(format!("{}.json", manifest.checkpoint_sha256)),
            &bytes,
            false,
        )?;
        publish(&p.join("manifest.json"), &json(manifest)?, false)
    }
    pub fn persist(
        &self,
        manifest: &mut Manifest,
        initial: &SustainedCheckpoint,
        engine: &mut SustainedSession,
        admission: Admission,
    ) -> Result<SustainedCheckpoint, AppError> {
        let p = self.prepare(&manifest.session_id)?;
        let checkpoint = engine.checkpoint();
        let cpbytes = json(&checkpoint)?;
        if cpbytes.len() as u64 > OBJECT_LIMIT {
            return Err(err("budget", "Checkpoint exceeds object limit"));
        }
        let cphash = files::digest(&cpbytes);
        let mut events: Vec<_> = engine.events().iter().cloned().collect();
        let mut candidate = manifest.clone();
        let mut initial = initial.clone();
        // A rename may have installed the manifest before a directory sync or
        // readback failed. Reconcile only an exact prefix of this engine's
        // still-unacknowledged events; never replace it with unrelated disk data.
        let disk: Manifest = typed(&p.join("manifest.json"), MANIFEST_LIMIT)?;
        if disk.segment_count != manifest.segment_count
            || disk.checkpoint_sha256 != manifest.checkpoint_sha256
        {
            if disk.segment_count < manifest.segment_count
                || disk.session_id != manifest.session_id
                || disk.generation != manifest.generation
            {
                return Err(err("changed", "Committed manifest identity changed"));
            }
            let verified = verify(&p)?;
            let mut prefix = Vec::new();
            for n in manifest.segment_count + 1..=disk.segment_count {
                let (link, _) = read_link(&p, n)?;
                prefix.extend(link.segment.events);
            }
            if prefix.len() > events.len()
                || json(&prefix)? != json(&events[..prefix.len()])?
                || verified.checkpoint.state.event_cursor > checkpoint.state.event_cursor
            {
                return Err(err(
                    "changed",
                    "Installed manifest is not an exact unacknowledged event prefix",
                ));
            }
            resync(&p.join("manifest.json"))?;
            initial = verified.checkpoint;
            events.drain(..prefix.len());
            candidate.segment_count = disk.segment_count;
            candidate.last_segment_sha256 = disk.last_segment_sha256;
            candidate.checkpoint_sha256 = disk.checkpoint_sha256;
        }
        let base_segment_count = candidate.segment_count;
        let base_segment_hash = candidate.last_segment_sha256.clone();
        let mut segment_bytes = None;
        if !events.is_empty() {
            if candidate.segment_count >= MAX_SEGMENTS {
                return Err(err("budget", "Segment count limit reached"));
            }
            let mut journal_sha256s = BTreeMap::new();
            for event in &events {
                if let SustainedEventKind::JournalSaved { entry, .. } = &event.kind {
                    let bytes = files::read_bounded(
                        &p.join("journals").join(format!("{}.json", entry.id)),
                        OBJECT_LIMIT,
                        "journal-anchor",
                    )?;
                    journal_sha256s.insert(entry.id.clone(), files::digest(&bytes));
                }
            }
            let envelope = Envelope {
                format: "reservoir-sustained-chain-link-v1".into(),
                sequence: candidate.segment_count + 1,
                previous_sha256: candidate.last_segment_sha256.clone(),
                journal_sha256s,
                segment: SustainedSegment {
                    format: core::FORMAT.into(),
                    initial_checkpoint: initial.clone(),
                    events,
                    final_checkpoint: checkpoint.clone(),
                },
            };
            let bytes = json(&envelope)?;
            if bytes.len() as u64 > OBJECT_LIMIT {
                return Err(err("budget", "Segment exceeds object limit"));
            }
            candidate.segment_count += 1;
            candidate.last_segment_sha256 = Some(files::digest(&bytes));
            segment_bytes = Some(bytes);
        } else if initial.sha256 != checkpoint.sha256 {
            return Err(err(
                "events",
                "Checkpoint changed without a replayable event",
            ));
        }
        candidate.step = engine.step();
        candidate.durable_step = engine.step();
        candidate.previous_checkpoint_sha256 = Some(candidate.checkpoint_sha256.clone());
        candidate.checkpoint_sha256 = cphash.clone();
        let (used, objects) = disk_usage(&p)?;
        let checkpoint_allocation = immutable_allocation(
            &p.join("checkpoints").join(format!("{cphash}.json")),
            &cpbytes,
        )?;
        let mut segment_allocation = 0;
        let mut quarantine_allocation = 0;
        if let Some(bytes) = &segment_bytes {
            let next_path = p
                .join("segments")
                .join(segment_name(candidate.segment_count));
            if next_path.exists() {
                let old = files::read_bounded(&next_path, OBJECT_LIMIT, "uncommitted-link")?;
                if old != *bytes {
                    // Quarantine currently copies before removing the conflicting
                    // uncommitted sequence. Include that transient extra copy.
                    let orphan = p.join("segments").join(format!(
                        "orphan-{}-{}.json",
                        candidate.segment_count,
                        files::digest(&old)
                    ));
                    quarantine_allocation = immutable_allocation(&orphan, &old)?;
                    segment_allocation = bytes.len() as u64;
                }
            } else {
                segment_allocation = bytes.len() as u64;
            }
        }
        let allocation = segment_allocation + quarantine_allocation + checkpoint_allocation;
        let new_objects = u64::from(segment_allocation > 0)
            + u64::from(quarantine_allocation > 0)
            + u64::from(checkpoint_allocation > 0);
        let ordinary_peak = used
            .saturating_add(allocation)
            .saturating_add(json(&candidate)?.len() as u64);
        let (terminal_bytes, terminal_segments) = terminal_reserve(engine, admission)?;
        if admission == Admission::Ordinary
            && (candidate.segment_count.saturating_add(3) >= MAX_SEGMENTS
                || objects.saturating_add(new_objects).saturating_add(7) >= MAX_OBJECTS
                || storage_held(&candidate)
                || ordinary_peak.saturating_add(RUN_HEADROOM)
                    > candidate.config.storage_budget_bytes)
        {
            hold_storage(&mut candidate);
        }
        let manifest_bytes = json(&candidate)?;
        if manifest_bytes.len() as u64 > MANIFEST_LIMIT {
            return Err(err("budget", "Manifest exceeds object limit"));
        }
        let peak = used
            .saturating_add(allocation)
            .saturating_add(manifest_bytes.len() as u64);
        // Every accepted state retains its actual bounded terminal suffix, not
        // an assumption that a reply or a buffered numerical tail is small.
        if peak.saturating_add(terminal_bytes) > candidate.config.storage_budget_bytes
            || candidate.segment_count.saturating_add(terminal_segments) > MAX_SEGMENTS
            || objects
                .saturating_add(new_objects)
                .saturating_add(2 * terminal_segments + 1)
                > MAX_OBJECTS
        {
            return Err(err("budget","Owned storage budget cannot retain this candidate and its terminal transition; pending state remains unsaved."));
        }
        if let Some(bytes) = segment_bytes {
            let next_path = p
                .join("segments")
                .join(segment_name(candidate.segment_count));
            if next_path.exists() {
                let old = files::read_bounded(&next_path, OBJECT_LIMIT, "uncommitted-link")?;
                if old != bytes {
                    let committed: Manifest = typed(&p.join("manifest.json"), MANIFEST_LIMIT)?;
                    if committed.segment_count != base_segment_count
                        || committed.last_segment_sha256 != base_segment_hash
                    {
                        return Err(err(
                            "changed",
                            "Committed manifest changed; inspect before continuing",
                        ));
                    }
                    let orphan = p.join("segments").join(format!(
                        "orphan-{}-{}.json",
                        candidate.segment_count,
                        files::digest(&old)
                    ));
                    publish(&orphan, &old, false)?;
                    fs::remove_file(&next_path).map_err(io)?;
                    sync_parent(&next_path)?;
                }
            }
            publish(
                &p.join("segments")
                    .join(segment_name(candidate.segment_count)),
                &bytes,
                false,
            )?;
        }
        self.injected(1)?;
        publish(
            &p.join("checkpoints").join(format!("{cphash}.json")),
            &cpbytes,
            false,
        )?;
        self.injected(3)?;
        publish(&p.join("manifest.json"), &manifest_bytes, true)?;
        self.injected(4)?;
        if let Some(last) = engine.events().back() {
            engine.acknowledge_events(last.id).map_err(ce)?;
        }
        *manifest = candidate;
        // Publication already committed. Cleanup can never turn success into a
        // retry of acknowledged events; unused checkpoint files remain inspectable.
        if let Ok(entries) = fs::read_dir(p.join("checkpoints")) {
            for entry in entries.flatten() {
                let name = entry.file_name().to_string_lossy().into_owned();
                let keep = name == format!("{}.json", manifest.checkpoint_sha256)
                    || manifest
                        .previous_checkpoint_sha256
                        .as_ref()
                        .is_some_and(|h| name == format!("{h}.json"));
                if !keep
                    && name.ends_with(".json")
                    && hash(name.trim_end_matches(".json"))
                    && entry.file_type().is_ok_and(|t| t.is_file())
                {
                    let _ = fs::remove_file(entry.path());
                }
            }
        }
        Ok(checkpoint)
    }
    pub fn commit_journal(
        &self,
        id: &str,
        pending: &SustainedPendingJournal,
        config: &SustainedConfig,
        timing: Option<&AttemptTiming>,
    ) -> Result<(SustainedSaveReceipt, SustainedJournal), AppError> {
        let p = self.prepare(id)?;
        if !valid_id(&pending.entry.id) {
            return Err(err("identity", "Invalid journal ID"));
        }
        let mut timing = timing.cloned().unwrap_or_default();
        timing.attempt_id = pending.entry.attempt_id;
        timing.published_at_ms = Some(crate::session_store::now_ms().to_string());
        let object = JournalObject {
            format: "reservoir-sustained-journal-v1".into(),
            pending: pending.clone(),
            request_started: config.language.backend == LanguageKind::Ollama,
            configured_model: config.language.model.clone(),
            temperature: config.language.temperature,
            sampling_seed: expected_sampling_seed(config, pending.entry.attempt_id),
            thinking: config.language.thinking,
            timing,
        };
        let path = p
            .join("journals")
            .join(format!("{}.json", pending.entry.id));
        if path.exists() {
            let existing: JournalObject = typed(&path, OBJECT_LIMIT)?;
            if json(&existing.pending)? != json(pending)?
                || existing.configured_model != object.configured_model
                || existing.temperature != object.temperature
                || existing.sampling_seed != object.sampling_seed
                || existing.thinking != object.thinking
                || existing.request_started != object.request_started
            {
                return Err(err(
                    "conflict",
                    "Existing immutable journal differs from pending evidence",
                ));
            }
            resync(&path)?;
            return Ok((
                SustainedSaveReceipt {
                    entry_id: pending.entry.id.clone(),
                    sha256: pending.entry.sha256.clone(),
                    relative_path: format!("journals/{}.json", pending.entry.id),
                },
                existing.pending.entry,
            ));
        }
        let bytes = json(&object)?;
        if bytes.len() as u64 > OBJECT_LIMIT
            || disk_bytes(&p)?.saturating_add(bytes.len() as u64 + RUN_HEADROOM)
                > config.storage_budget_bytes
        {
            return Err(err(
                "budget",
                "Insufficient owned budget for journal and prepared checkpoint",
            ));
        }
        let path = p
            .join("journals")
            .join(format!("{}.json", pending.entry.id));
        publish(&path, &bytes, false)?;
        self.injected(2)?;
        let readback: JournalObject = typed(&path, OBJECT_LIMIT)?;
        if json(&readback)? != bytes {
            return Err(err("readback", "Journal readback differs"));
        }
        Ok((
            SustainedSaveReceipt {
                entry_id: pending.entry.id.clone(),
                sha256: pending.entry.sha256.clone(),
                relative_path: format!("journals/{}.json", pending.entry.id),
            },
            readback.pending.entry,
        ))
    }
    pub fn read_journal(&self, id: &str, entry_id: &str) -> Result<JournalObject, AppError> {
        Ok(self.read_journal_proof(id, entry_id)?.0)
    }
    pub fn read_journal_proof(
        &self,
        id: &str,
        entry_id: &str,
    ) -> Result<(JournalObject, String), AppError> {
        self.root(false)?;
        if !valid_id(entry_id) {
            return Err(err("identity", "Invalid journal ID"));
        }
        let p = self.path(id)?;
        ordinary(&p)?;
        ordinary(&p.join("journals"))?;
        let bytes = files::read_bounded(
            &p.join("journals").join(format!("{entry_id}.json")),
            OBJECT_LIMIT,
            "journal-read",
        )?;
        let object: JournalObject = serde_json::from_slice(&bytes).map_err(ce)?;
        if object.pending.entry.id != entry_id
            || files::digest(object.pending.entry.text.as_bytes()) != object.pending.entry.sha256
        {
            return Err(err("integrity", "Journal identity or text hash differs"));
        }
        Ok((object, files::digest(&bytes)))
    }
    pub fn verify(&self, id: &str) -> Result<Verified, AppError> {
        self.root(false)?;
        verify(&self.path(id)?)
    }
    pub fn used_bytes(&self, id: &str) -> Result<u64, AppError> {
        disk_bytes(&self.path(id)?)
    }
    pub fn recovery(&self, request_id: String) -> Result<RecoveryPage, AppError> {
        if !self.root.exists() {
            return Ok(RecoveryPage {
                request_id,
                entries: vec![],
                complete: true,
            });
        }
        self.root(false)?;
        let mut entries = vec![];
        let mut complete = true;
        for e in fs::read_dir(&self.root).map_err(io)? {
            let e = e.map_err(io)?;
            if e.file_name() == "owner" {
                continue;
            }
            if entries.len() >= 1000 {
                complete = false;
                break;
            }
            let id = e.file_name().to_string_lossy().into_owned();
            if !valid_id(&id) {
                continue;
            }
            let m = if e.file_type().map_err(io)?.is_dir() {
                typed::<Manifest>(&e.path().join("manifest.json"), MANIFEST_LIMIT)
            } else {
                Err(err("ownership", "Non-directory recovery entry"))
            };
            entries.push(match m {
                Ok(m) => RecoveryEntry {
                    session_id: id,
                    generation: Some(m.generation),
                    revision: Some(m.revision),
                    phase: Some(m.phase),
                    step: Some(m.step),
                    durable_step: Some(m.durable_step),
                    journal_count: Some(m.journal_count),
                    diagnostic: Some(
                        "Catalog metadata only; inspect verifies the complete committed chain."
                            .into(),
                    ),
                },
                Err(e) => RecoveryEntry {
                    session_id: id,
                    generation: None,
                    revision: None,
                    phase: None,
                    step: None,
                    durable_step: None,
                    journal_count: None,
                    diagnostic: Some(e.message),
                },
            });
        }
        entries.sort_by(|a, b| b.session_id.cmp(&a.session_id));
        Ok(RecoveryPage {
            request_id,
            entries,
            complete,
        })
    }
    pub fn journal_index(&self, id: &str) -> Result<Vec<JournalIndex>, AppError> {
        let v = self.verify(id)?;
        journal_index(&self.path(id)?, &v.manifest)
    }
    pub fn export(
        &self,
        id: &str,
        destination: &Path,
        forbidden: &[PathBuf],
    ) -> Result<BundleReport, AppError> {
        let source = self.path(id)?;
        let before = verify(&source)?;
        ordinary(destination)?;
        let destination = destination.canonicalize().map_err(io)?;
        for p in forbidden.iter().chain(std::iter::once(&self.root)) {
            if let Ok(p) = p.canonicalize() {
                if destination.starts_with(p) {
                    return Err(err(
                        "destination",
                        "Choose a destination outside application resources and managed stores",
                    ));
                }
            }
        }
        let name = format!(
            "{}-{}-{}",
            id, before.manifest.generation, before.manifest.revision
        );
        let final_path = destination.join(name);
        if final_path.exists() {
            return Err(err(
                "exists",
                "This exact exported snapshot directory already exists",
            ));
        }
        let temp = tempfile::Builder::new()
            .prefix(".incomplete-sustained-")
            .tempdir_in(&destination)
            .map_err(io)?;
        copy_committed(&source, temp.path(), &before.manifest)?;
        let exported = verify(temp.path())?;
        if exported.report.manifest_sha256 != before.report.manifest_sha256 {
            return Err(err("changed", "Manifest changed during export"));
        }
        let kept = temp.keep();
        rename_new_directory(&kept, &final_path)?;
        sync_parent(&final_path)?;
        Ok(exported.report)
    }
}
fn segment_name(n: u64) -> String {
    format!("segment-{n:08}.json")
}
fn disk_bytes(path: &Path) -> Result<u64, AppError> {
    Ok(disk_usage(path)?.0)
}
fn disk_usage(path: &Path) -> Result<(u64, u64), AppError> {
    ordinary(path)?;
    let mut n = 0u64;
    let mut count = 0u64;
    for e in fs::read_dir(path).map_err(io)? {
        let e = e.map_err(io)?;
        let t = e.file_type().map_err(io)?;
        let name = e.file_name();
        if t.is_dir()
            && ["segments", "checkpoints", "journals"]
                .iter()
                .any(|d| name == *d)
        {
            ordinary(&e.path())?;
            for child in fs::read_dir(e.path()).map_err(io)? {
                let child = child.map_err(io)?;
                count += 1;
                if count > MAX_OBJECTS {
                    return Err(err("bound", "Owned object count exceeds bound"));
                }
                if !child.file_type().map_err(io)?.is_file() {
                    return Err(err(
                        "ownership",
                        "Nested directory, link or special object is not allowed",
                    ));
                }
                n = n
                    .checked_add(child.metadata().map_err(io)?.len())
                    .ok_or_else(|| err("bound", "Byte count overflow"))?;
            }
        } else if t.is_file() {
            count += 1;
            if count > MAX_OBJECTS {
                return Err(err("bound", "Owned object count exceeds bound"));
            }
            n = n
                .checked_add(e.metadata().map_err(io)?.len())
                .ok_or_else(|| err("bound", "Byte count overflow"))?;
        } else {
            return Err(err(
                "ownership",
                "Unexpected directory, link or special object",
            ));
        }
    }
    Ok((n, count))
}
fn read_link(path: &Path, n: u64) -> Result<(Envelope, String), AppError> {
    let bytes = files::read_bounded(
        &path.join("segments").join(segment_name(n)),
        OBJECT_LIMIT,
        "chain-link",
    )?;
    let h = files::digest(&bytes);
    Ok((serde_json::from_slice(&bytes).map_err(ce)?, h))
}
pub fn verify_bundle(path: &Path) -> Result<BundleReport, AppError> {
    Ok(verify(path)?.report)
}
fn verify(path: &Path) -> Result<Verified, AppError> {
    ordinary(path)?;
    for d in ["segments", "checkpoints", "journals"] {
        ordinary(&path.join(d))?;
    }
    let mb = files::read_bounded(&path.join("manifest.json"), MANIFEST_LIMIT, "manifest")?;
    let manifest: Manifest = serde_json::from_slice(&mb).map_err(ce)?;
    manifest.config.validate()?;
    if ![
        "ready",
        "running",
        "awaitingLanguage",
        "savingJournal",
        "paused",
        "stopped",
        "budgetReached",
        "storageBlocked",
        "providerFailed",
        "compatibilityBlocked",
        "attemptBlocked",
        "interrupted",
    ]
    .contains(&manifest.phase.as_str())
    {
        return Err(err("manifest", "Unknown phase"));
    }
    if let Some(t) = &manifest.attempt_timing {
        validate_timing(t)?;
    }
    if manifest.format != "reservoir-sustained-bundle-v1"
        || !valid_id(&manifest.session_id)
        || manifest.segment_count > MAX_SEGMENTS
        || !hash(&manifest.checkpoint_sha256)
        || manifest.step != manifest.durable_step
        || manifest.diagnostics.len() > 32
        || manifest.diagnostics.iter().any(|s| s.len() > 4096)
        || manifest.generation.parse::<u64>().is_err()
        || manifest.revision.parse::<u64>().is_err()
    {
        return Err(err("manifest", "Invalid bounded manifest"));
    }
    let mut expected = SustainedSession::new(manifest.config.specification()?)
        .map_err(ce)?
        .checkpoint();
    let mut previous = None;
    let mut journal_count = 0;
    let mut received_response_total = 0;
    let mut received_responses = VecDeque::new();
    for n in 1..=manifest.segment_count {
        let (link, h) = read_link(path, n)?;
        if link.format != "reservoir-sustained-chain-link-v1"
            || link.sequence != n
            || link.previous_sha256 != previous
            || link.segment.initial_checkpoint.sha256 != expected.sha256
            || json(&link.segment.initial_checkpoint)? != json(&expected)?
        {
            return Err(err(
                "chain",
                "Segment chain does not begin at exact genesis or previous committed continuation",
            ));
        }
        let evidence = link.segment.journal_evidence().map_err(ce)?;
        // The existing verified-chain traversal already owns these typed events.
        // Retain only the newest bounded metadata rows, never full response text.
        for event in &link.segment.events {
            if let SustainedEventKind::LanguageReceived {
                attempt_id,
                response,
                ..
            } = &event.kind
            {
                let (stop_reason, stop_reason_truncated) =
                    stop_reason_view(response.stop_reason.as_deref());
                received_response_total += 1;
                if received_responses.len() == RECEIVED_RESPONSE_LIMIT {
                    received_responses.pop_front();
                }
                received_responses.push_back(ReceivedResponseEvidence {
                    attempt_id: attempt_id.to_string(),
                    observed_step: event.step.to_string(),
                    complete: response.complete,
                    stop_reason,
                    stop_reason_truncated,
                    token_count: response.token_count.map(|count| count.to_string()),
                    provider_prompt_evaluation: response
                        .provider_prompt_evaluation
                        .as_ref()
                        .map(Into::into),
                });
            }
        }
        if evidence.len() != link.journal_sha256s.len() {
            return Err(err(
                "journal",
                "Journal object anchors differ from replayed commits",
            ));
        }
        for pending in evidence {
            let entry = &pending.entry;
            {
                let object_bytes = files::read_bounded(
                    &path.join("journals").join(format!("{}.json", entry.id)),
                    OBJECT_LIMIT,
                    "journal-evidence",
                )?;
                if link.journal_sha256s.get(&entry.id) != Some(&files::digest(&object_bytes)) {
                    return Err(err(
                        "journal",
                        "Journal object bytes differ from immutable chain anchor",
                    ));
                }
                let object: JournalObject = serde_json::from_slice(&object_bytes).map_err(ce)?;
                validate_timing(&object.timing)?;
                if object.timing.attempt_id != entry.attempt_id {
                    return Err(err("journal", "Host timing refers to a different attempt"));
                }
                if !valid_id(&entry.id)
                    || object.format != "reservoir-sustained-journal-v1"
                    || object.request_started
                        != (manifest.config.language.backend == LanguageKind::Ollama)
                    || json(&object.pending)? != json(&pending)?
                    || json(entry)? != json(&pending.entry)?
                    || object.configured_model != manifest.config.language.model
                    || object.temperature != manifest.config.language.temperature
                    || object.sampling_seed
                        != expected_sampling_seed(&manifest.config, entry.attempt_id)
                    || object.thinking != manifest.config.language.thinking
                {
                    return Err(err(
                        "journal",
                        "Immutable journal differs from its replayed response/save evidence",
                    ));
                }
                journal_count += 1;
            }
        }
        expected = link.segment.final_checkpoint;
        previous = Some(h);
    }
    let cpbytes = files::read_bounded(
        &path
            .join("checkpoints")
            .join(format!("{}.json", manifest.checkpoint_sha256)),
        OBJECT_LIMIT,
        "checkpoint",
    )?;
    let checkpoint: SustainedCheckpoint = serde_json::from_slice(&cpbytes).map_err(ce)?;
    checkpoint.validate().map_err(ce)?;
    if files::digest(&cpbytes) != manifest.checkpoint_sha256
        || json(&checkpoint)? != json(&expected)?
        || previous != manifest.last_segment_sha256
        || manifest.step != checkpoint.state.step
        || manifest.journal_count != journal_count
    {
        return Err(err(
            "chain",
            "Final manifest/checkpoint/journal count differs from replayed committed prefix",
        ));
    }
    let size_bytes = disk_bytes(path)?;
    let mut diagnostics = manifest.diagnostics.clone();
    let committed_journals = journal_index(path, &manifest)?;
    let mut extras = 0u64;
    for dir in ["segments", "journals", "checkpoints"] {
        for e in fs::read_dir(path.join(dir)).map_err(io)? {
            let e = e.map_err(io)?;
            let name = e.file_name().to_string_lossy().into_owned();
            let committed = match dir {
                "segments" => name
                    .strip_prefix("segment-")
                    .and_then(|s| s.strip_suffix(".json"))
                    .and_then(|s| s.parse::<u64>().ok())
                    .is_some_and(|n| (1..=manifest.segment_count).contains(&n)),
                "journals" => committed_journals
                    .iter()
                    .any(|j| name == format!("{}.json", j.entry_id)),
                _ => {
                    name == format!("{}.json", manifest.checkpoint_sha256)
                        || manifest
                            .previous_checkpoint_sha256
                            .as_ref()
                            .is_some_and(|h| name == format!("{h}.json"))
                }
            };
            if !committed {
                extras += 1;
            }
        }
    }
    if extras > 0 {
        diagnostics.push(format!("{extras} uncommitted or incomplete objects retained separately; never promoted to replay history."));
    }
    if size_bytes > manifest.config.storage_budget_bytes {
        return Err(err(
            "budget",
            "Retained bundle exceeds its declared storage budget",
        ));
    }
    let report=BundleReport{format:manifest.format.clone(),session_id:manifest.session_id.clone(),manifest_sha256:files::digest(&mb),checkpoint_sha256:manifest.checkpoint_sha256.clone(),segment_count:manifest.segment_count,step:manifest.step,journal_count,size_bytes,verification:"Exact genesis and contiguous event/numerical replay; journal/save/application consistency. This does not authenticate provider execution or physical power-loss durability.".into(),diagnostics};
    Ok(Verified {
        manifest,
        checkpoint,
        report,
        received_responses: ReceivedResponses {
            total: received_response_total,
            truncated: received_response_total > RECEIVED_RESPONSE_LIMIT,
            entries: received_responses.into_iter().rev().collect(),
        },
    })
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct JournalIndex {
    pub entry_id: String,
    pub turn_id: u64,
    pub attempt_id: u64,
    pub observed_step: u64,
    pub first_applied_step: Option<u64>,
    pub status: String,
    pub text_preview: String,
    pub sha256: String,
    pub object_sha256: String,
}
fn journal_index(path: &Path, manifest: &Manifest) -> Result<Vec<JournalIndex>, AppError> {
    let mut entries = BTreeMap::new();
    let mut pending = None;
    for n in 1..=manifest.segment_count {
        let (link, _) = read_link(path, n)?;
        for e in link.segment.events {
            match e.kind {
                SustainedEventKind::JournalSaved { entry, .. } => {
                    pending = Some(entry.id.clone());
                    entries.insert(
                        entry.id.clone(),
                        JournalIndex {
                            entry_id: entry.id.clone(),
                            turn_id: entry.turn_id,
                            attempt_id: entry.attempt_id,
                            observed_step: entry.observed_step,
                            first_applied_step: None,
                            status: "savedPendingApplication".into(),
                            text_preview: entry.text.chars().take(160).collect(),
                            object_sha256: link
                                .journal_sha256s
                                .get(&entry.id)
                                .cloned()
                                .unwrap_or_default(),
                            sha256: entry.sha256,
                        },
                    );
                }
                SustainedEventKind::Advanced(f) => {
                    if let Some(a) = f.application {
                        if let Some(e) = entries.get_mut(&a.journal_id) {
                            e.first_applied_step = Some(a.applied_step);
                            e.status = "applied".into();
                        }
                        pending = None;
                    }
                }
                SustainedEventKind::Skipped { .. } => {
                    if let Some(id) = pending.take() {
                        if let Some(e) = entries.get_mut(&id) {
                            e.status = "skipped".into();
                        }
                    }
                }
                _ => {}
            }
        }
    }
    let mut rows: Vec<_> = entries.into_values().collect();
    rows.sort_by_key(|e| std::cmp::Reverse(e.attempt_id));
    Ok(rows)
}
fn copy_committed(source: &Path, target: &Path, m: &Manifest) -> Result<(), AppError> {
    for d in ["segments", "checkpoints", "journals"] {
        directory(&target.join(d))?;
    }
    let mut paths = vec![
        PathBuf::from("manifest.json"),
        PathBuf::from(format!("checkpoints/{}.json", m.checkpoint_sha256)),
    ];
    if let Some(h) = &m.previous_checkpoint_sha256 {
        if hash(h) && source.join(format!("checkpoints/{h}.json")).exists() {
            paths.push(PathBuf::from(format!("checkpoints/{h}.json")));
        }
    }
    for n in 1..=m.segment_count {
        paths.push(PathBuf::from("segments").join(segment_name(n)));
    }
    for j in journal_index(source, m)? {
        paths.push(PathBuf::from("journals").join(format!("{}.json", j.entry_id)));
    }
    for p in paths {
        let b = files::read_bounded(&source.join(&p), OBJECT_LIMIT, "export-object")?;
        publish(&target.join(p), &b, false)?;
    }
    Ok(())
}

fn rename_new_directory(source: &Path, destination: &Path) -> Result<(), AppError> {
    #[cfg(any(target_os = "macos", target_os = "linux"))]
    {
        use std::{ffi::CString, os::unix::ffi::OsStrExt};
        let a = CString::new(source.as_os_str().as_bytes()).map_err(ce)?;
        let b = CString::new(destination.as_os_str().as_bytes()).map_err(ce)?;
        // SAFETY: Both owned C strings remain valid for the syscall; no-replace
        // publication prevents a concurrent preexisting destination from removal.
        #[cfg(target_os = "macos")]
        let result = unsafe { libc::renamex_np(a.as_ptr(), b.as_ptr(), libc::RENAME_EXCL) };
        #[cfg(target_os = "linux")]
        let result = unsafe {
            libc::renameat2(
                libc::AT_FDCWD,
                a.as_ptr(),
                libc::AT_FDCWD,
                b.as_ptr(),
                libc::RENAME_NOREPLACE,
            )
        };
        if result != 0 {
            return Err(io(std::io::Error::last_os_error()));
        }
        Ok(())
    }
    #[cfg(target_os = "windows")]
    {
        fs::rename(source, destination).map_err(io)
    }
    #[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
    {
        let _ = (source, destination);
        Err(err(
            "platform",
            "Atomic no-replace directory publication is not qualified on this target",
        ))
    }
}

fn validate_timing(t: &AttemptTiming) -> Result<(), AppError> {
    if [
        t.dispatched_at_ms.as_ref(),
        t.received_at_ms.as_ref(),
        t.published_at_ms.as_ref(),
    ]
    .into_iter()
    .flatten()
    .any(|s| s.parse::<u64>().is_err() || s.len() > 20)
        || t.transport_duration_ms.is_some_and(|n| n > 86_400_000)
    {
        return Err(err(
            "timing",
            "Host timing metadata exceeds bounded representation",
        ));
    }
    Ok(())
}

#[cfg(test)]
mod quota_projection_tests {
    use super::*;
    #[test]
    fn quota_projection_is_pure_and_terminal_suffix_can_spend_reserved_capacity() {
        let directory = tempfile::tempdir().unwrap();
        let store = SustainedStore::new(directory.path().join("store"));
        let config = SustainedConfig {
            turn_every: 3,
            storage_budget_bytes: 16 * 1024 * 1024,
            ..Default::default()
        };
        let mut engine = SustainedSession::new(config.specification().unwrap()).unwrap();
        let mut manifest = Manifest {
            format: "reservoir-sustained-bundle-v1".into(),
            session_id: "quota-test".into(),
            generation: "1".into(),
            revision: "1".into(),
            config,
            phase: "ready".into(),
            step: 0,
            durable_step: 0,
            elapsed_millis: 0,
            journal_count: 0,
            segment_count: 0,
            last_segment_sha256: None,
            checkpoint_sha256: String::new(),
            previous_checkpoint_sha256: None,
            diagnostics: vec![],
            attempt_timing: None,
        };
        let mut committed = engine.checkpoint();
        store.initialize(&mut manifest, &committed).unwrap();
        for _ in 0..3 {
            engine.advance().unwrap();
        }
        committed = store
            .persist(&mut manifest, &committed, &mut engine, Admission::Ordinary)
            .unwrap();
        let before = json(&engine.checkpoint()).unwrap();
        let (reserve, links) = terminal_reserve(&engine, Admission::Ordinary).unwrap();
        assert_eq!(links, 2);
        assert_eq!(json(&engine.checkpoint()).unwrap(), before);
        assert!(engine.events().is_empty());
        let root = store.path(&manifest.session_id).unwrap();
        let padding = root.join("quota-test-pressure.bin");
        let f = fs::File::create(&padding).unwrap();
        let used = disk_bytes(&root).unwrap();
        // Exact projection plus a single small candidate publication, far less
        // than the general 8 MiB ordinary low-water threshold.
        f.set_len(manifest.config.storage_budget_bytes - used - reserve - 8192)
            .unwrap();
        committed = store
            .persist(&mut manifest, &committed, &mut engine, Admission::Ordinary)
            .unwrap();
        assert!(storage_held(&manifest));
        let attempt = engine.pending_language().unwrap().attempt_id;
        engine.cancel_language(attempt, "Explicit Stop").unwrap();
        manifest.phase = "stopped".into();
        manifest.revision = "2".into();
        committed = store
            .persist(&mut manifest, &committed, &mut engine, Admission::Stop)
            .unwrap();
        assert_eq!(terminal_reserve(&engine, Admission::Stop).unwrap().1, 1);
        engine.skip_pending("Explicit Skip").unwrap();
        manifest.revision = "3".into();
        committed = store
            .persist(&mut manifest, &committed, &mut engine, Admission::Skip)
            .unwrap();
        assert_eq!(
            terminal_reserve(&engine, Admission::Skip).unwrap(),
            (MANIFEST_LIMIT, 0)
        );
        // Leave only actual manifest replacement space: a final Close must not
        // demand another hypothetical future Stop/Skip/close reserve.
        let used = disk_bytes(&root).unwrap();
        let old = f.metadata().unwrap().len();
        let mut final_candidate = manifest.clone();
        final_candidate.previous_checkpoint_sha256 = Some(manifest.checkpoint_sha256.clone());
        let remaining = json(&final_candidate).unwrap().len() as u64 + 1;
        f.set_len(old + manifest.config.storage_budget_bytes - used - remaining)
            .unwrap();
        store
            .persist(&mut manifest, &committed, &mut engine, Admission::Close)
            .unwrap();
        let verified = store.verify(&manifest.session_id).unwrap();
        assert!(matches!(
            verified.checkpoint.state.phase,
            core::SustainedPhase::Ready
        ));
        assert!(verified.report.size_bytes <= manifest.config.storage_budget_bytes);
    }
}
