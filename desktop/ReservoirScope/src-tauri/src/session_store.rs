//! App-owned finite-session checkpoints and journal commits. Never follows a
//! path contained in a record, checkpoint, or journal receipt.
use crate::files::{self, AppError};
use reservoir_core::actions::{ActionReceipt, Arm, JournalEntry, JournalSaveReceipt, SaveStatus};
use serde::{Deserialize, Serialize};
use std::{
    fs,
    io::Write,
    path::{Path, PathBuf},
    sync::{Arc, Mutex},
};
const OWNER: &[u8] = b"reservoir-scope-sessions-v1\n";
const META_LIMIT: u64 = 2 * 1024 * 1024;
const JOURNAL_LIMIT: u64 = 256 * 1024;
fn error(kind: &str, message: impl Into<String>) -> AppError {
    AppError::new("session-storage", kind, message)
}
fn io(e: std::io::Error) -> AppError {
    error("storage", e.to_string())
}
pub fn now_ms() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis()
        .min(u64::MAX as u128) as u64
}
fn valid_id(id: &str) -> bool {
    !id.is_empty() && id.len() <= 96 && id.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-')
}
fn valid_hash(id: &str) -> bool {
    id.len() == 64
        && id
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn directory(path: &Path) -> Result<(), AppError> {
    match fs::symlink_metadata(path) {
        Ok(m) if !m.file_type().is_dir() => {
            return Err(error(
                "ownership",
                "Session storage directories cannot be links or other files.",
            ))
        }
        Err(e) if e.kind() != std::io::ErrorKind::NotFound => return Err(io(e)),
        _ => {}
    }
    let mut missing = Vec::new();
    let mut at = path;
    while !at.try_exists().map_err(io)? {
        missing.push(at.to_path_buf());
        let Some(parent) = at.parent() else { break };
        at = parent;
    }
    fs::create_dir_all(path).map_err(io)?;
    for created in missing.iter().rev() {
        sync_parent(created)?;
    }
    sync_parent(path)?;
    Ok(())
}
fn sync_parent(path: &Path) -> Result<(), AppError> {
    #[cfg(unix)]
    if let Some(parent) = path.parent() {
        fs::File::open(parent)
            .and_then(|f| f.sync_all())
            .map_err(io)?;
    }
    #[cfg(not(unix))]
    let _ = path;
    Ok(())
}
fn sync_existing(path: &Path) -> Result<(), AppError> {
    let mut options = fs::OpenOptions::new();
    options.read(true).write(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK);
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt;
        options.custom_flags(0x0020_0000);
    }
    let file = options.open(path).map_err(io)?;
    if !file.metadata().map_err(io)?.is_file() {
        return Err(error("ownership", "Journal is no longer an ordinary file."));
    }
    file.sync_all().map_err(io)?;
    sync_parent(path)
}
fn ordinary(path: &Path) -> Result<(), AppError> {
    if !fs::symlink_metadata(path).map_err(io)?.file_type().is_dir() {
        return Err(error(
            "ownership",
            "Recovery directories must be ordinary directories, never links.",
        ));
    }
    Ok(())
}
fn publish(path: &Path, bytes: &[u8], replace: bool) -> Result<(), AppError> {
    let parent = path
        .parent()
        .ok_or_else(|| error("path", "Missing owned parent."))?;
    if let Ok(m) = fs::symlink_metadata(path) {
        if !m.file_type().is_file() {
            return Err(error(
                "ownership",
                "Publication destination is not an ordinary file.",
            ));
        }
    }
    let mut tmp = tempfile::Builder::new()
        .prefix(".incomplete-")
        .tempfile_in(parent)
        .map_err(io)?;
    tmp.write_all(bytes)
        .and_then(|_| tmp.as_file().sync_all())
        .map_err(io)?;
    if files::read_bounded(
        tmp.path(),
        reservoir_core::MAX_RECORD_BYTES as u64,
        "session-stage-readback",
    )? != bytes
    {
        return Err(error("readback", "Staged bytes differ."));
    }
    if replace {
        tmp.persist(path)
            .map_err(|e| error("publish", e.to_string()))?;
    } else {
        tmp.persist_noclobber(path)
            .map_err(|e| error("publish", e.to_string()))?;
    }
    #[cfg(unix)]
    fs::File::open(parent)
        .and_then(|f| f.sync_all())
        .map_err(io)?;
    if files::read_bounded(
        path,
        reservoir_core::MAX_RECORD_BYTES as u64,
        "session-readback",
    )? != bytes
    {
        return Err(error(
            "readback",
            "Published bytes differ; retained files require inspection.",
        ));
    }
    Ok(())
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SaveAttempt {
    #[serde(default = "right_arm")]
    pub arm: Arm,
    pub number: usize,
    pub at_ms: String,
    pub entry_id: String,
    pub status: String,
    pub diagnostic: Option<String>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Checkpoint {
    pub schema: String,
    pub session_id: String,
    pub generation: String,
    pub revision: String,
    pub config: serde_json::Value,
    pub phase: String,
    pub step: usize,
    pub durable_step: usize,
    pub record_sha256: Option<String>,
    pub pending_journal: Option<serde_json::Value>,
    #[serde(default)]
    pub pending_language: Option<PendingLanguageCheckpoint>,
    #[serde(default)]
    pub rejected_language: Option<PendingLanguageCheckpoint>,
    #[serde(default)]
    pub paired_boundary: Option<PairedBoundary>,
    #[serde(default)]
    pub regulation_progress: Option<RegulationProgress>,
    pub attempts: Vec<SaveAttempt>,
    pub updated_at_ms: String,
    pub discarded: bool,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct PendingLanguageCheckpoint {
    #[serde(flatten)]
    pub operation: crate::sessions::PendingLanguageView,
    pub session_id: String,
    pub generation: String,
    pub prompt: String,
    pub configuration: reservoir_core::stage::LanguageConfiguration,
    pub request_started: bool,
    #[serde(default)]
    pub received_response: Option<RetainedLanguageResponse>,
    #[serde(default)]
    pub diagnostic: Option<String>,
}
/// Inert evidence of a response rejected by the qualified codec/parser gate.
/// Explicit prefix markers prevent truncated text from masquerading as exact bytes.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RetainedLanguageResponse {
    pub text: String,
    pub text_byte_count: usize,
    pub text_sha256: String,
    pub text_truncated: bool,
    pub provider_model: Option<String>,
    pub stop_reason: Option<String>,
    pub metadata_truncated: bool,
    pub token_count: Option<i64>,
    pub complete: bool,
}
fn prefix(text: &str, limit: usize) -> String {
    let mut end = text.len().min(limit);
    while !text.is_char_boundary(end) {
        end -= 1;
    }
    text[..end].into()
}
impl RetainedLanguageResponse {
    pub fn capture(r: &reservoir_core::session::LanguageResponse) -> Self {
        Self {
            text: prefix(&r.text, 65_536),
            text_byte_count: r.text.len(),
            text_sha256: files::digest(r.text.as_bytes()),
            text_truncated: r.text.len() > 65_536,
            provider_model: r.provider_model.as_deref().map(|v| prefix(v, 1024)),
            stop_reason: r.stop_reason.as_deref().map(|v| prefix(v, 1024)),
            metadata_truncated: r.provider_model.as_ref().is_some_and(|v| v.len() > 1024)
                || r.stop_reason.as_ref().is_some_and(|v| v.len() > 1024),
            token_count: r.token_count,
            complete: r.complete,
        }
    }
    fn valid(&self) -> bool {
        self.text.len() <= 65_536
            && self.text_byte_count <= 1_048_576
            && self.text_byte_count >= self.text.len()
            && valid_hash(&self.text_sha256)
            && self.provider_model.as_ref().is_none_or(|s| s.len() <= 1024)
            && self.stop_reason.as_ref().is_none_or(|s| s.len() <= 1024)
            && if self.text_truncated {
                self.text_byte_count > 65_536 && self.text.len() >= 65_533
            } else {
                self.text.len() == self.text_byte_count
                    && files::digest(self.text.as_bytes()) == self.text_sha256
            }
    }
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RegulationProgress {
    pub retained_step: usize,
    pub portable_complete: bool,
    pub specification: reservoir_core::regulation::RegulationExampleSpecification,
}
fn right_arm() -> Arm {
    Arm::Right
}
fn arm_path(arm: Arm) -> &'static str {
    if arm == Arm::Left {
        "left"
    } else {
        "right"
    }
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PairedBoundary {
    pub step: usize,
    pub arms: Vec<BoundaryArm>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct BoundaryArm {
    pub arm: Arm,
    pub stage: u8,
    pub receipt: Option<ActionReceipt>,
    pub journal: Option<JournalEntry>,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RecoveryEntry {
    pub session_id: String,
    pub phase: String,
    pub step: usize,
    pub durable_step: usize,
    pub revision: String,
    pub record_sha256: Option<String>,
    pub pending_journal: bool,
    pub pending_language: bool,
    pub discarded: bool,
    pub diagnostic: Option<String>,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RecoveryPage {
    pub entries: Vec<RecoveryEntry>,
    pub incomplete_writes: Vec<String>,
    pub examined: usize,
    pub truncated: bool,
}
#[derive(Clone)]
pub struct SessionStore {
    root: PathBuf,
    gate: Arc<Mutex<()>>,
    #[cfg(test)]
    pub fail_committed_checkpoint: Arc<std::sync::atomic::AtomicBool>,
}
impl SessionStore {
    pub fn new(root: PathBuf) -> Self {
        Self {
            root,
            gate: Arc::new(Mutex::new(())),
            #[cfg(test)]
            fail_committed_checkpoint: Arc::new(std::sync::atomic::AtomicBool::new(false)),
        }
    }
    fn owned(&self) -> Result<(), AppError> {
        if !self.root.is_absolute() {
            return Err(error("ownership", "Session root must be absolute."));
        }
        directory(&self.root)?;
        let marker = self.root.join("owner.txt");
        if marker.try_exists().map_err(io)? {
            if files::read_bounded(&marker, 128, "session-owner")? != OWNER {
                return Err(error("ownership", "Directory belongs to another store."));
            }
        } else {
            if fs::read_dir(&self.root).map_err(io)?.next().is_some() {
                return Err(error(
                    "ownership",
                    "Refusing an existing unmarked session directory.",
                ));
            }
            publish(&marker, OWNER, false)?;
        }
        Ok(())
    }
    fn session_dir(&self, id: &str, create: bool) -> Result<PathBuf, AppError> {
        if !valid_id(id) {
            return Err(error("identity", "Invalid session identity."));
        }
        let p = self.root.join(id);
        if create {
            directory(&p)?;
        } else if !fs::symlink_metadata(&p).map_err(io)?.file_type().is_dir() {
            return Err(error("ownership", "Session must be an ordinary directory."));
        }
        Ok(p)
    }
    pub fn checkpoint(
        &self,
        mut checkpoint: Checkpoint,
        record: Option<&[u8]>,
    ) -> Result<(), AppError> {
        let _gate = self
            .gate
            .lock()
            .map_err(|_| error("lock", "Storage lock unavailable."))?;
        self.owned()?;
        #[cfg(test)]
        if checkpoint
            .attempts
            .last()
            .is_some_and(|a| a.status == "committed")
            && self
                .fail_committed_checkpoint
                .swap(false, std::sync::atomic::Ordering::AcqRel)
        {
            return Err(error(
                "injected-checkpoint-failure",
                "Injected publication failure after durable journal readback.",
            ));
        }
        let dir = self.session_dir(&checkpoint.session_id, true)?;
        directory(&dir.join("records"))?;
        directory(&dir.join("right"))?;
        if checkpoint.config["actionComparePrevious"] == true {
            directory(&dir.join("left"))?;
        }
        if let Some(bytes) = record {
            if bytes.len() > reservoir_core::MAX_RECORD_BYTES {
                return Err(error("bounds", "Session snapshot exceeds record bound."));
            }
            let hash = files::digest(bytes);
            let path = dir.join("records").join(format!("{hash}.json"));
            if path.try_exists().map_err(io)? {
                if files::read_bounded(
                    &path,
                    reservoir_core::MAX_RECORD_BYTES as u64,
                    "session-existing",
                )? != bytes
                {
                    return Err(error(
                        "identity",
                        "Snapshot identity collision or changed content.",
                    ));
                }
            } else {
                publish(&path, bytes, false)?;
            }
            sync_existing(&path)?;
            checkpoint.record_sha256 = Some(hash);
        }
        let previous = if dir.join("checkpoint.json").try_exists().map_err(io)? {
            self.read_checkpoint(&checkpoint.session_id)?.record_sha256
        } else {
            None
        };
        checkpoint.updated_at_ms = now_ms().to_string();
        let bytes = serde_json::to_vec(&checkpoint).map_err(|e| error("encode", e.to_string()))?;
        if bytes.len() as u64 > META_LIMIT {
            return Err(error(
                "bounds",
                "Session checkpoint exceeds metadata bound.",
            ));
        }
        publish(&dir.join("checkpoint.json"), &bytes, true)?;
        // Only after the pointer is durable: retain current plus prior portable snapshot.
        for item in fs::read_dir(dir.join("records")).map_err(io)? {
            let item = item.map_err(io)?;
            let name = item.file_name();
            let name = name.to_string_lossy();
            if let Some(hash) = name.strip_suffix(".json").filter(|h| valid_hash(h)) {
                if Some(hash) != checkpoint.record_sha256.as_deref()
                    && Some(hash) != previous.as_deref()
                    && item.file_type().map_err(io)?.is_file()
                {
                    fs::remove_file(item.path()).map_err(io)?;
                }
            }
        }
        Ok(())
    }
    #[cfg(test)]
    pub fn commit_journal(
        &self,
        id: &str,
        entry: &JournalEntry,
    ) -> Result<(JournalSaveReceipt, JournalEntry), AppError> {
        self.commit_journal_for(id, Arm::Right, entry)
    }
    pub fn commit_journal_for(
        &self,
        id: &str,
        arm: Arm,
        entry: &JournalEntry,
    ) -> Result<(JournalSaveReceipt, JournalEntry), AppError> {
        let _gate = self
            .gate
            .lock()
            .map_err(|_| error("lock", "Storage lock unavailable."))?;
        self.owned()?;
        let dir = self.session_dir(id, false)?;
        directory(&dir.join(arm_path(arm)))?;
        if !valid_id(&entry.id)
            || entry.text.len() > 65_536
            || files::digest(entry.text.as_bytes()) != entry.sha256
        {
            return Err(error("journal", "Journal text or identity is invalid."));
        }
        let relative = format!("{}/{}.json", arm_path(arm), entry.id);
        let path = dir.join(arm_path(arm)).join(format!("{}.json", entry.id));
        let bytes = serde_json::to_vec(entry).map_err(|e| error("journal", e.to_string()))?;
        if path.try_exists().map_err(io)? {
            if files::read_bounded(&path, JOURNAL_LIMIT, "journal-retry")? != bytes {
                return Err(error(
                    "journal",
                    "Existing journal differs; no replacement or feedback was allowed.",
                ));
            }
        } else {
            publish(&path, &bytes, false)?;
        }
        // Retry the durability operation even if an earlier publish installed the
        // bytes but failed while syncing its directory entry.
        sync_existing(&path)?;
        let readback = files::read_bounded(&path, JOURNAL_LIMIT, "journal-readback")?;
        let decoded: JournalEntry = serde_json::from_slice(&readback)
            .map_err(|e| error("journal-readback", e.to_string()))?;
        if decoded != *entry || readback != bytes {
            return Err(error(
                "journal-readback",
                "Journal identity did not read back exactly.",
            ));
        }
        Ok((
            JournalSaveReceipt {
                status: SaveStatus::Saved,
                entry_id: entry.id.clone(),
                sha256: entry.sha256.clone(),
                relative_path: Some(relative),
                failure: None,
            },
            decoded,
        ))
    }
    /// Re-read a previously committed entry for a new F/G/H prompt opportunity.
    /// Expected text is never substituted for a missing or changed file.
    pub fn read_journal_for(
        &self,
        id: &str,
        arm: Arm,
        expected: &JournalEntry,
    ) -> Result<JournalEntry, AppError> {
        let _gate = self
            .gate
            .lock()
            .map_err(|_| error("lock", "Storage lock unavailable."))?;
        ordinary(&self.root)?;
        if files::read_bounded(&self.root.join("owner.txt"), 128, "session-owner")? != OWNER {
            return Err(error("ownership", "Directory belongs to another store."));
        }
        let dir = self.session_dir(id, false)?;
        ordinary(&dir.join(arm_path(arm)))?;
        if !valid_id(&expected.id) {
            return Err(error("identity", "Invalid journal identity."));
        }
        let bytes = files::read_bounded(
            &dir.join(arm_path(arm))
                .join(format!("{}.json", expected.id)),
            JOURNAL_LIMIT,
            "session-memory-read",
        )?;
        let entry: JournalEntry =
            serde_json::from_slice(&bytes).map_err(|e| error("memory-read", e.to_string()))?;
        if entry != *expected
            || entry.text.len() > 65_536
            || files::digest(entry.text.as_bytes()) != entry.sha256
            || entry.id
                != format!(
                    "journal-{}-{}-{}",
                    entry.observed_step, entry.action_id, entry.sha256
                )
        {
            return Err(error(
                "memory-read",
                "Saved journal identity, text or hash differs from its committed entry.",
            ));
        }
        Ok(entry)
    }
    pub fn recovery(&self) -> Result<RecoveryPage, AppError> {
        let _gate = self
            .gate
            .lock()
            .map_err(|_| error("lock", "Storage lock unavailable."))?;
        self.owned()?;
        let mut result = RecoveryPage {
            entries: vec![],
            incomplete_writes: vec![],
            examined: 0,
            truncated: false,
        };
        for item in fs::read_dir(&self.root).map_err(io)? {
            if result.examined == 5000 || result.entries.len() == 100 {
                result.truncated = true;
                break;
            }
            result.examined += 1;
            let item = item.map_err(io)?;
            let name = item.file_name().to_string_lossy().to_string();
            if name == "owner.txt" {
                continue;
            }
            if !valid_id(&name) || !item.file_type().map_err(io)?.is_dir() {
                recovery_diagnostic(&mut result, name);
                continue;
            }
            match self.read_checkpoint(&name) {
                Ok(c) => {
                    let diagnostic = if let Some(hash) = c.record_sha256.as_deref() {
                        self.read_record(&name, hash).err().map(|e| e.message)
                    } else {
                        Some("No portable snapshot yet; pending candidate may require explicit discard or inspection.".into())
                    };
                    result.entries.push(RecoveryEntry {
                        session_id: name.clone(),
                        phase: c.phase,
                        step: c.step,
                        durable_step: c.durable_step,
                        revision: c.revision,
                        record_sha256: c.record_sha256,
                        pending_journal: c.pending_journal.is_some(),
                        pending_language: c.pending_language.is_some(),
                        discarded: c.discarded,
                        diagnostic,
                    });
                    let mut subdirectories = vec![
                        item.path(),
                        item.path().join("right"),
                        item.path().join("records"),
                    ];
                    if c.config["actionComparePrevious"] == true {
                        subdirectories.push(item.path().join("left"));
                    }
                    for sub in subdirectories {
                        if let Err(e) = ordinary(&sub) {
                            recovery_diagnostic(&mut result, format!("{name}: {}", e.message));
                            continue;
                        }
                        if let Ok(items) = fs::read_dir(sub) {
                            for (index, f) in items.enumerate() {
                                if index >= 1000 {
                                    result.truncated = true;
                                    break;
                                }
                                if let Ok(f) = f {
                                    if f.file_name().to_string_lossy().starts_with(".incomplete-") {
                                        recovery_diagnostic(
                                            &mut result,
                                            format!("{name}/{}", f.file_name().to_string_lossy()),
                                        );
                                    }
                                }
                            }
                        }
                    }
                }
                Err(e) => result.entries.push(RecoveryEntry {
                    session_id: name,
                    phase: "incomplete".into(),
                    step: 0,
                    durable_step: 0,
                    revision: "0".into(),
                    record_sha256: None,
                    pending_journal: false,
                    pending_language: false,
                    discarded: false,
                    diagnostic: Some(e.message),
                }),
            }
        }
        result
            .entries
            .sort_by(|a, b| a.session_id.cmp(&b.session_id));
        Ok(result)
    }
    pub fn read_checkpoint(&self, id: &str) -> Result<Checkpoint, AppError> {
        ordinary(&self.root)?;
        if files::read_bounded(&self.root.join("owner.txt"), 128, "session-owner")? != OWNER {
            return Err(error("ownership", "Session owner differs."));
        }
        let dir = self.session_dir(id, false)?;
        let bytes =
            files::read_bounded(&dir.join("checkpoint.json"), META_LIMIT, "session-recovery")?;
        let c: Checkpoint =
            serde_json::from_slice(&bytes).map_err(|e| error("checkpoint", e.to_string()))?;
        if [
            c.generation.as_str(),
            c.revision.as_str(),
            c.updated_at_ms.as_str(),
        ]
        .iter()
        .any(|s| {
            s.is_empty() || !s.bytes().all(|b| b.is_ascii_digit()) || s.parse::<u64>().is_err()
        }) || c.schema != "reservoir-scope-finite-session-v1"
            || c.session_id != id
            || c.generation.parse::<u64>().is_err()
            || c.revision.parse::<u64>().is_err()
            || c.record_sha256.as_deref().is_some_and(|h| !valid_hash(h))
        {
            return Err(error("checkpoint", "Checkpoint identity is invalid."));
        }
        let record = c
            .record_sha256
            .as_deref()
            .map(|h| self.read_record(id, h))
            .transpose()?;
        validate_checkpoint(&c, record.as_deref())?;
        Ok(c)
    }
    pub fn read_record(&self, id: &str, hash: &str) -> Result<Vec<u8>, AppError> {
        if !valid_hash(hash) {
            return Err(error("identity", "Invalid snapshot hash."));
        }
        ordinary(&self.root)?;
        let dir = self.session_dir(id, false)?;
        ordinary(&dir.join("records"))?;
        let bytes = files::read_bounded(
            &dir.join("records").join(format!("{hash}.json")),
            reservoir_core::MAX_RECORD_BYTES as u64,
            "session-recovery-record",
        )?;
        if files::digest(&bytes) != hash {
            return Err(error("identity", "Recovered snapshot hash differs."));
        }
        Ok(bytes)
    }
}

fn validate_checkpoint(c: &Checkpoint, record: Option<&[u8]>) -> Result<(), AppError> {
    let bad = || {
        error(
            "checkpoint",
            "Recovered checkpoint fields disagree with bounded retained evidence.",
        )
    };
    let config: crate::sessions::SessionConfig =
        serde_json::from_value(c.config.clone()).map_err(|_| bad())?;
    crate::sessions::validate_session_language(&config).map_err(|_| bad())?;
    let seed = config.seed.parse::<u64>().map_err(|_| bad())?;
    let cap = match config.recipe.as_str() {
        "exploration" => 1800,
        "regulation" => 600,
        "stage1" | "stage2" | "stage3" | "stage4" => 3000,
        recipe if crate::sessions::action_stage(recipe).is_some() => 600,
        _ => return Err(bad()),
    };
    if config.seed.is_empty()
        || !config.seed.bytes().all(|b| b.is_ascii_digit())
        || !config.leak.is_finite()
        || !(0.0..=1.0).contains(&config.leak)
        || !config.noise_amplitude.is_finite()
        || !(0.0..=0.2).contains(&config.noise_amplitude)
        || !config.retention.is_finite()
        || !(0.82..=0.995).contains(&config.retention)
        || !config.action_input_strength.is_finite()
        || !(0.0..=1.0).contains(&config.action_input_strength)
        || config
            .exploration_controls
            .as_ref()
            .is_some_and(|x| x.validate().is_err())
        || config.steps == 0
        || config.steps > cap
        || config.turn_every == 0
        || config.turn_every > cap
        || c.durable_step > c.step
        || c.step > config.steps
        || c.attempts.len() > 512
        || !matches!(
            c.phase.as_str(),
            "ready"
                | "running"
                | "paused"
                | "awaitingJournalSave"
                | "awaitingLanguage"
                | "completed"
                | "stopped"
                | "failed"
                | "storageBlocked"
        )
    {
        return Err(bad());
    }
    if config.recipe == "regulation" {
        crate::sessions::validate_regulation_config(&config).map_err(|_| bad())?;
        let progress = c.regulation_progress.as_ref().ok_or_else(bad)?;
        progress.specification.validate().map_err(|_| bad())?;
        if progress.retained_step != c.step
            || progress.portable_complete != (c.step == 600)
            || c.pending_journal.is_some()
            || matches!(c.phase.as_str(), "awaitingJournalSave" | "awaitingLanguage")
            || c.pending_language.is_some()
            || c.rejected_language.is_some()
            || c.paired_boundary.is_some()
            || !c.attempts.is_empty()
            || (c.step < 600 && (record.is_some() || c.durable_step != 0 || c.phase == "completed"))
            || (c.step == 600 && (record.is_none() || c.durable_step != 600))
        {
            return Err(bad());
        }
    } else if c.regulation_progress.is_some() {
        return Err(bad());
    }
    let mut retained_actions = None;
    let mut retained_stage = None;
    if let Some(bytes) = record {
        let count = match config.recipe.as_str() {
            "regulation" => {
                let r: reservoir_core::regulation::RegulationExampleRecord =
                    serde_json::from_slice(bytes).map_err(|_| bad())?;
                r.validate_structure().map_err(|_| bad())?;
                if r.specification
                    != c.regulation_progress
                        .as_ref()
                        .ok_or_else(bad)?
                        .specification
                {
                    return Err(bad());
                }
                r.frames.len()
            }
            "exploration" => {
                let r: reservoir_core::exploration::ExplorationRecord =
                    serde_json::from_slice(bytes).map_err(|_| bad())?;
                r.validate_structure().map_err(|_| bad())?;
                if r.seed != seed {
                    return Err(bad());
                }
                r.frames.len()
            }
            "stage1" | "stage2" | "stage3" | "stage4" => {
                let r: reservoir_core::stage::StageRecord =
                    serde_json::from_slice(bytes).map_err(|_| bad())?;
                r.validate_structure().map_err(|_| bad())?;
                let x = &r.specification;
                if x.stage != config.recipe.as_bytes()[5] - b'0'
                    || x.seed != seed
                    || x.steps != config.steps
                    || x.turn_every != config.turn_every
                    || x.leak != config.leak
                    || x.noise_amplitude != config.noise_amplitude
                    || x.initial_retention != config.retention
                    || serde_json::to_value(&x.language).unwrap()
                        != serde_json::to_value(&config.language).unwrap()
                {
                    return Err(bad());
                }
                let count = r.frames.len();
                retained_stage = Some(r);
                count
            }
            _ => {
                let r: reservoir_core::actions::ActionComparisonRecord =
                    serde_json::from_slice(bytes).map_err(|_| bad())?;
                r.validate_structure().map_err(|_| bad())?;
                let x = &r.specification;
                if Some(x.stage) != crate::sessions::action_stage(&config.recipe)
                    || x.seed != seed
                    || x.steps != config.steps
                    || x.turn_every != config.turn_every
                    || x.leak != config.leak
                    || x.noise_amplitude != config.noise_amplitude
                    || x.initial_retention != config.retention
                    || x.input_strength != config.action_input_strength
                    || x.bias_enabled != config.action_bias_enabled
                    || x.mode != config.action_mode
                    || x.compare_previous != config.action_compare_previous
                    || x.comparison_kind != config.action_comparison_kind
                    || x.forcing_profile != config.action_forcing_profile
                    || serde_json::to_value(&x.language).unwrap()
                        != serde_json::to_value(&config.language).unwrap()
                    || r.left.is_some() != config.action_compare_previous
                {
                    return Err(bad());
                }
                let count = r.right.frames.len();
                retained_actions = Some(r);
                count
            }
        };
        if count != c.durable_step {
            return Err(bad());
        }
    } else if c.durable_step != 0 {
        return Err(bad());
    }
    let mut pending_arm = None;
    let mut pending_turn = None;
    for (p, rejected) in c
        .pending_language
        .as_ref()
        .map(|p| (p, false))
        .into_iter()
        .chain(c.rejected_language.as_ref().map(|p| (p, true)))
    {
        let v = &p.operation;
        let seq = v
            .operation_id
            .strip_prefix(&format!("language-{}-", c.generation));
        if config.language.backend != reservoir_core::stage::LanguageKind::Ollama
            || p.session_id != c.session_id
            || p.generation != c.generation
            || seq.is_none_or(|s| {
                s.is_empty()
                    || !s.bytes().all(|b| b.is_ascii_digit())
                    || s.parse::<u64>().is_err()
                    || s == "0"
            })
            || v.turn_id == 0
            || v.turn_id
                > if config.recipe.starts_with("stage") {
                    3000
                } else {
                    128
                }
            || v.observed_step != c.step
            || c.step == 0
            || c.step >= config.steps
            || !matches!(
                v.state.as_str(),
                "prepared" | "requesting" | "compatibilityBlocked"
            )
            || p.request_started != (v.state != "prepared")
            || if rejected {
                !matches!(c.phase.as_str(), "stopped" | "failed" | "storageBlocked")
                    || c.pending_language.is_some()
                    || v.state != "compatibilityBlocked"
            } else {
                !matches!(c.phase.as_str(), "awaitingLanguage" | "storageBlocked")
            }
            || c.pending_journal.is_some()
            || v.endpoint != config.language.endpoint.as_deref().unwrap_or("")
            || v.model != config.language.model.as_deref().unwrap_or("")
            || serde_json::to_value(&p.configuration).unwrap()
                != serde_json::to_value(&config.language).unwrap()
            || p.prompt.is_empty()
            || p.prompt.len() > 131_072
            || p.diagnostic
                .as_ref()
                .is_some_and(|s| s.is_empty() || s.len() > 4096)
            || p.received_response.as_ref().is_some_and(|r| !r.valid())
            || (v.state == "compatibilityBlocked")
                != (p.received_response.is_some() && p.diagnostic.is_some())
            || (v.arm == Arm::Left && !config.action_compare_previous)
        {
            return Err(bad());
        }
        if config.recipe.starts_with("stage") {
            let r = retained_stage.as_ref().ok_or_else(bad)?;
            if v.arm != Arm::Right || !c.step.is_multiple_of(config.turn_every) {
                return Err(bad());
            }
            if rejected {
                let t = r.turns.get(v.turn_id - 1).ok_or_else(bad)?;
                if t.id != v.turn_id
                    || t.observed_step != v.observed_step
                    || t.status != reservoir_core::stage::TurnStatus::Cancelled
                    || t.prompt != p.prompt
                {
                    return Err(bad());
                }
            } else if v.turn_id != r.turns.len() + 1 {
                return Err(bad());
            }
        } else {
            let prior = retained_actions
                .as_ref()
                .and_then(|r| {
                    if v.arm == Arm::Left {
                        r.left.as_ref()
                    } else {
                        Some(&r.right)
                    }
                })
                .ok_or_else(bad)?;
            if prior.stage < 4 {
                return Err(bad());
            }
            if rejected {
                let t = prior.actions.get(v.turn_id - 1).ok_or_else(bad)?;
                if t.id != v.turn_id
                    || t.observed_step != v.observed_step
                    || t.status != reservoir_core::stage::TurnStatus::Cancelled
                    || !t.request_started
                    || t.prompt != p.prompt
                {
                    return Err(bad());
                }
            } else if v.turn_id != prior.actions.len() + 1 {
                return Err(bad());
            }
        }
        if !rejected {
            pending_arm = Some(v.arm);
            pending_turn = Some(v.turn_id);
        }
    }
    if c.pending_language.is_none() && c.phase == "awaitingLanguage" {
        return Err(bad());
    }

    if let Some(v) = &c.pending_journal {
        if crate::sessions::action_stage(&config.recipe).is_none_or(|stage| stage < 4)
            || c.step == 0
            || c.step >= config.steps
        {
            return Err(bad());
        }
        let arm: Arm = v
            .get("arm")
            .cloned()
            .map(serde_json::from_value)
            .transpose()
            .map_err(|_| bad())?
            .unwrap_or(Arm::Right);
        if arm == Arm::Left && !config.action_compare_previous {
            return Err(bad());
        }
        pending_arm = Some(arm);
        pending_turn = v["actionId"].as_u64().map(|n| n as usize);
        let entry: JournalEntry = serde_json::from_value(v["entry"].clone()).map_err(|_| bad())?;
        let action = v["actionId"].as_u64().ok_or_else(bad)? as usize;
        let observed = v["observedStep"].as_u64().ok_or_else(bad)? as usize;
        let hash = files::digest(entry.text.as_bytes());
        let expected = format!("journal-{observed}-{action}-{hash}");
        if action == 0
            || action > 128
            || observed != c.step
            || entry.action_id != action
            || entry.observed_step != observed
            || entry.id != expected
            || entry.sha256 != hash
            || entry.text.is_empty()
            || entry.text.len() > 65536
            || v["relativePath"].as_str()
                != Some(format!("{}/{expected}.json", arm_path(arm)).as_str())
            || !matches!(v["trigger"].as_str(), Some("scheduled" | "manual"))
        {
            return Err(bad());
        }
        for key in ["prompt", "rawReply"] {
            if v[key].as_str().is_none_or(|s| {
                s.is_empty() || s.len() > if key == "prompt" { 131_072 } else { 65_536 }
            }) {
                return Err(bad());
            }
        }
        let reply: serde_json::Value =
            serde_json::from_str(v["rawReply"].as_str().unwrap()).map_err(|_| bad())?;
        if reply["action"] != "WRITE_JOURNAL" || reply["text"].as_str() != Some(entry.text.as_str())
        {
            return Err(bad());
        }
    }
    match (&c.paired_boundary, pending_arm) {
        (Some(boundary), Some(pending)) if config.action_compare_previous => {
            let retained = retained_actions.as_ref().ok_or_else(bad)?;
            if boundary.step != c.step || boundary.arms.len() != 2 || c.durable_step > c.step {
                return Err(bad());
            }
            for (index, arm) in [Arm::Left, Arm::Right].into_iter().enumerate() {
                let part = &boundary.arms[index];
                let prior = if arm == Arm::Left {
                    retained.left.as_ref().ok_or_else(bad)?
                } else {
                    &retained.right
                };
                if part.arm != arm
                    || part.stage != prior.stage
                    || (arm == pending && part.receipt.is_some())
                {
                    return Err(bad());
                }
                match (&part.receipt, &part.journal) {
                    (None, None) => {}
                    (Some(receipt), journal) => {
                        validate_boundary_receipt(
                            receipt,
                            journal.as_ref(),
                            arm,
                            c.step,
                            prior.actions.len() + 1,
                            config.turn_every,
                        )?;
                    }
                    _ => return Err(bad()),
                }
            }
            let prior = if pending == Arm::Left {
                retained.left.as_ref().ok_or_else(bad)?
            } else {
                &retained.right
            };
            if prior.stage < 4 || pending_turn != Some(prior.actions.len() + 1) {
                return Err(bad());
            }
            for attempt in c.attempts.iter().filter(|a| {
                a.status == "committed" && a.entry_id.starts_with(&format!("journal-{}-", c.step))
            }) {
                if !boundary.arms.iter().any(|p| {
                    p.arm == attempt.arm
                        && p.journal.as_ref().is_some_and(|j| j.id == attempt.entry_id)
                }) {
                    return Err(bad());
                }
            }
            for part in &boundary.arms {
                if let Some(journal) = &part.journal {
                    if !c.attempts.iter().any(|a| {
                        a.status == "committed" && a.arm == part.arm && a.entry_id == journal.id
                    }) {
                        return Err(bad());
                    }
                }
            }
        }
        (None, _) if !config.action_compare_previous || pending_arm.is_none() => {}
        _ => return Err(bad()),
    }
    for (index, a) in c.attempts.iter().enumerate() {
        if (a.arm == Arm::Left && !config.action_compare_previous)
            || a.number != index + 1
            || !valid_id(&a.entry_id)
            || a.at_ms.parse::<u64>().is_err()
            || !matches!(a.status.as_str(), "prepared" | "failed" | "committed")
            || a.diagnostic.as_ref().is_some_and(|s| s.len() > 4096)
        {
            return Err(bad());
        }
    }
    Ok(())
}

fn recovery_diagnostic(page: &mut RecoveryPage, message: String) {
    if page.incomplete_writes.len() < 100 {
        page.incomplete_writes.push(message);
    } else {
        page.truncated = true;
    }
}

// This authenticates bounded checkpoint consistency, not numerical regeneration.
fn validate_boundary_receipt(
    r: &ActionReceipt,
    journal: Option<&JournalEntry>,
    arm: Arm,
    step: usize,
    id: usize,
    interval: usize,
) -> Result<(), AppError> {
    use reservoir_core::{
        actions::{JournalAction, Trigger},
        stage::TurnStatus,
    };
    let bad = || {
        error(
            "checkpoint",
            "Partial paired-boundary receipt or journal is inconsistent.",
        )
    };
    if r.id != id
        || id > 128
        || r.observed_step != step
        || r.application_step.is_some()
        || (r.trigger == Trigger::Scheduled) != step.is_multiple_of(interval)
        || r.prompt.len() > 131_072
        || r.raw_reply.as_ref().is_some_and(|s| s.len() > 65_536)
        || r.memory_text.as_ref().is_some_and(|s| s.len() > 65_536)
        || [&r.failure, &r.provider_model, &r.stop_reason]
            .into_iter()
            .flatten()
            .any(|s| s.len() > 4096)
        || [&r.encoded_features, &r.semantic_vector]
            .into_iter()
            .flatten()
            .any(|v| {
                v.len() != 48
                    || v.iter().any(|x| !x.is_finite())
                    || v[32..].iter().any(|x| *x != 0.0)
            })
        || match (r.raw_reply_byte_count, r.raw_reply.as_ref()) {
            (None, None) => false,
            (Some(n), Some(raw)) => n < raw.len() || n > 1_048_576,
            _ => true,
        }
    {
        return Err(bad());
    }
    if let Some(entry) = journal {
        let hash = files::digest(entry.text.as_bytes());
        let expected = format!("journal-{step}-{id}-{hash}");
        let save = r.save_receipt.as_ref().ok_or_else(bad)?;
        if r.status != TurnStatus::Completed
            || r.chosen_action != Some(JournalAction::WriteJournal)
            || entry.id != expected
            || entry.action_id != id
            || entry.observed_step != step
            || entry.text.is_empty()
            || entry.text.len() > 65_536
            || entry.sha256 != hash
            || r.journal_entry_id.as_deref() != Some(entry.id.as_str())
            || save.status != SaveStatus::Saved
            || save.entry_id != entry.id
            || save.sha256 != entry.sha256
            || save.failure.is_some()
            || save.relative_path.as_deref()
                != Some(format!("{}/{expected}.json", arm_path(arm)).as_str())
        {
            return Err(bad());
        }
        let raw: serde_json::Value =
            serde_json::from_str(r.raw_reply.as_deref().ok_or_else(bad)?).map_err(|_| bad())?;
        if raw["action"] != "WRITE_JOURNAL" || raw["text"].as_str() != Some(entry.text.as_str()) {
            return Err(bad());
        }
    } else if r
        .save_receipt
        .as_ref()
        .is_some_and(|s| s.status == SaveStatus::Saved)
        || (r.status == TurnStatus::Completed
            && r.chosen_action == Some(JournalAction::WriteJournal))
    {
        return Err(bad());
    }
    Ok(())
}
