//! Shared operator service for native UI, HTTP and the research CLI.
//! Only owns this application's stores; it never discovers or controls live beings.
#[path = "research_validation.rs"]
mod validation;
use crate::{
    files::{self, AppError},
    provider_scheduler::ProviderScheduler,
    sustained::{SustainedConfig, SustainedState},
    sustained_store::{JournalIndex, Manifest, SustainedStore},
};
use rusqlite::{params, Connection, OptionalExtension};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, VecDeque},
    fs,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering},
        Arc, Mutex,
    },
    time::Duration,
};

pub fn error(code: &str, message: impl Into<String>) -> AppError {
    AppError::new("research-api", code, message)
}
fn internal(e: impl std::fmt::Display) -> AppError {
    error("storage", e.to_string())
}
pub fn id(prefix: &str) -> String {
    format!("{prefix}-{}", uuid::Uuid::new_v4().simple())
}
pub fn value<T: Serialize>(v: T) -> Result<Value, AppError> {
    serde_json::to_value(v).map_err(internal)
}
pub fn merge(target: &mut Value, patch: &Value) {
    if let (Some(to), Some(from)) = (target.as_object_mut(), patch.as_object()) {
        for (key, val) in from {
            if val.is_object() {
                merge(to.entry(key).or_insert(json!({})), val);
            } else {
                to.insert(key.clone(), val.clone());
            }
        }
    } else {
        *target = patch.clone();
    }
}
fn configuration(v: &Value) -> Result<SustainedConfig, AppError> {
    let c: SustainedConfig =
        serde_json::from_value(v.clone()).map_err(|e| error("configuration", e.to_string()))?;
    c.validate()?;
    Ok(c)
}
fn identifier(v: &str) -> Result<(), AppError> {
    if !crate::sustained_store::valid_id(v) {
        return Err(error(
            "invalid-id",
            "Use an opaque identifier returned by this app",
        ));
    }
    Ok(())
}

fn validate_intervention(b: &Value) -> Result<(), AppError> {
    let at = &b["at"];
    let valid = at.as_object().is_some_and(|o| {
        o.len() == 1
            && (at["step"]
                .as_u64()
                .is_some_and(|s| (1..=10_000_000).contains(&s))
                || at["activeSeconds"]
                    .as_u64()
                    .is_some_and(|s| (1..=604800).contains(&s)))
    });
    if !valid {
        return Err(error(
            "configuration",
            "at requires one positive step or activeSeconds",
        ));
    }
    match b["kind"].as_str() {
        Some("configuration") if b["patch"].is_object() => Ok(()),
        Some("prompt")
            if b["prompt"]
                .as_str()
                .is_some_and(|p| !p.trim().is_empty() && p.len() <= 16384)
                && b["includeTelemetry"].is_boolean() =>
        {
            Ok(())
        }
        _ => Err(error(
            "configuration",
            "Supply a configuration patch or a prompt with includeTelemetry",
        )),
    }
}

#[derive(Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Operation {
    pub id: String,
    pub status: String,
    pub method: String,
    pub path: String,
    pub request: Value,
    pub result: Option<Value>,
    pub error: Option<Value>,
}
struct Page {
    run_id: String,
    manifest: Manifest,
    entries: Vec<JournalIndex>,
}
struct Control {
    gate: Mutex<()>,
    epoch: AtomicU64,
    // A boundary can become due after Pause requests its drain. Its remembered
    // running state must never override the operator's newer lifecycle intent.
    resume_suppressed: AtomicBool,
}
struct Shared {
    _ownership: fs::File,
    root: PathBuf,
    store: SustainedStore,
    owners: Mutex<BTreeMap<String, SustainedState>>,
    primary: SustainedState,
    db: Mutex<Connection>,
    scheduler: ProviderScheduler,
    pages: Mutex<BTreeMap<String, Page>>,
    page_order: Mutex<VecDeque<String>>,
    active_operations: AtomicUsize,
    closing: AtomicBool,
    pending: Mutex<BTreeMap<String, String>>,
    controls: Mutex<BTreeMap<String, Arc<Control>>>,
    app: Mutex<Option<tauri::AppHandle>>,
}
#[derive(Clone)]
pub struct ResearchService(Arc<Shared>);

impl ResearchService {
    pub fn new(data: PathBuf, primary: SustainedState) -> Result<Self, AppError> {
        let root = data.join("automation-v1");
        fs::create_dir_all(&root).map_err(internal)?;
        crate::sustained_store::ordinary(&root)?;
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            fs::set_permissions(&root, fs::Permissions::from_mode(0o700)).map_err(internal)?;
        }
        let lock_path = root.join("owner.lock");
        if lock_path.exists()
            && !fs::symlink_metadata(&lock_path)
                .map_err(internal)?
                .file_type()
                .is_file()
        {
            return Err(error(
                "ownership",
                "Research ownership lock must be an ordinary file",
            ));
        }
        let ownership = fs::OpenOptions::new()
            .create(true)
            .truncate(false)
            .read(true)
            .write(true)
            .open(lock_path)
            .map_err(internal)?;
        #[cfg(unix)]
        {
            use std::os::fd::AsRawFd;
            if unsafe { libc::flock(ownership.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } != 0 {
                return Err(error(
                    "conflict",
                    "Another process owns this research data directory",
                ));
            }
        }
        let db = Connection::open(root.join("operations.sqlite")).map_err(internal)?;
        db.execute_batch("PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;
            CREATE TABLE IF NOT EXISTS operations (id TEXT PRIMARY KEY, key TEXT UNIQUE NOT NULL, digest TEXT NOT NULL, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS documents (kind TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY(kind,id));").map_err(internal)?;
        let scheduler = ProviderScheduler::default();
        primary.set_scheduler(scheduler.clone());
        let service = Self(Arc::new(Shared {
            _ownership: ownership,
            root,
            store: SustainedStore::new(data.join("sustained-v1")),
            owners: Mutex::new(BTreeMap::new()),
            primary,
            db: Mutex::new(db),
            scheduler,
            pages: Mutex::new(BTreeMap::new()),
            page_order: Mutex::new(VecDeque::new()),
            active_operations: AtomicUsize::new(0),
            closing: AtomicBool::new(false),
            pending: Mutex::new(BTreeMap::new()),
            controls: Mutex::new(BTreeMap::new()),
            app: Mutex::new(None),
        }));
        if let Ok(settings) = service.document("settings", "application") {
            if let Some(n) = settings["maxConcurrentRequests"].as_u64() {
                service
                    .0
                    .scheduler
                    .set_limit(n as usize)
                    .map_err(internal)?;
            }
        }
        // An uncertain operation is never automatically dispatched after restart.
        for mut op in service.unfinished_operations()? {
            if matches!(op.status.as_str(), "queued" | "running" | "scheduled") {
                op.status = "needsAttention".into();
                op.error = Some(
                    json!({"code":"interrupted","message":"App restarted; inspect the retained run before explicitly continuing."}),
                );
                if let Some(run) = op.path.strip_prefix("/v1/runs/").and_then(|p| {
                    p.strip_suffix("/settings")
                        .or_else(|| p.strip_suffix("/interventions"))
                }) {
                    if let Ok(m) = service.0.store.manifest(run) {
                        if let Some(c) = m
                            .configuration_changes
                            .iter()
                            .find(|c| c.operation_id == op.id)
                        {
                            op.status = "completed".into();
                            op.error = None;
                            op.result = Some(if op.path.ends_with("/interventions") {
                                json!({"requestedBoundary":op.request["at"],"applied":c})
                            } else {
                                value(c)?
                            });
                        }
                    }
                }
                service.save_operation(&op)?;
            }
        }
        Ok(service)
    }
    pub fn set_app(&self, app: tauri::AppHandle) {
        *self.0.app.lock().unwrap() = Some(app);
    }
    fn admit<T>(&self, action: impl FnOnce() -> Result<T, AppError>) -> Result<T, AppError> {
        let app = self.0.app.lock().map_err(internal)?.clone();
        if let Some(app) = app {
            crate::execution_admission::start_sustained(&app, action)
        } else {
            action()
        }
    }
    fn control(&self, run: &str) -> Arc<Control> {
        self.0
            .controls
            .lock()
            .unwrap()
            .entry(run.into())
            .or_insert_with(|| {
                Arc::new(Control {
                    gate: Mutex::new(()),
                    epoch: AtomicU64::new(0),
                    resume_suppressed: AtomicBool::new(false),
                })
            })
            .clone()
    }
    pub fn discovery_directory(&self) -> &Path {
        &self.0.root
    }
    fn adopt_primary(&self) {
        if let Ok(m) = self.0.primary.stored_manifest() {
            let mut owners = self.0.owners.lock().unwrap();
            owners.retain(|id, s| s.stored_manifest().is_ok_and(|m| m.session_id == *id));
            owners
                .entry(m.session_id)
                .or_insert_with(|| self.0.primary.clone());
        }
    }
    fn owner(&self, run: &str, restore: bool) -> Result<SustainedState, AppError> {
        identifier(run)?;
        self.adopt_primary();
        let mut owners = self.0.owners.lock().map_err(internal)?;
        if let Some(s) = owners.get(run) {
            if !s.requires_reload() {
                return Ok(s.clone());
            }
        }
        if !restore {
            return Err(error("not-loaded", "Run is retained on disk"));
        }
        let m = self.0.store.manifest(run)?;
        let s = SustainedState::new(self.0.store.root.clone());
        s.set_scheduler(self.0.scheduler.clone());
        s.resume("api-restore".into(), run, &m.generation, &m.revision)?;
        owners.insert(run.into(), s.clone());
        Ok(s)
    }
    pub fn list_runs(&self) -> Result<Value, AppError> {
        self.adopt_primary();
        let mut ids = BTreeMap::new();
        if self.0.store.root.exists() {
            crate::sustained_store::ordinary(&self.0.store.root)?;
            for entry in fs::read_dir(&self.0.store.root)
                .map_err(internal)?
                .take(10001)
            {
                let e = entry.map_err(internal)?;
                if e.file_type().map_err(internal)?.is_dir() {
                    let name = e.file_name().to_string_lossy().to_string();
                    if identifier(&name).is_ok() {
                        ids.insert(name, ());
                    }
                }
            }
        }
        if ids.len() > 10000 {
            return Err(error("limit", "Run catalog exceeds 10,000 records"));
        }
        let mut runs = Vec::new();
        for run in ids.keys() {
            match self.run(run) {
                Ok(v) => runs.push(v),
                Err(e) => runs.push(json!({"runId":run,"error":e})),
            }
        }
        Ok(json!({"runs":runs,"scheduler":self.0.scheduler.snapshot()}))
    }
    pub fn run(&self, run: &str) -> Result<Value, AppError> {
        identifier(run)?;
        let (m, summary) = match self.owner(run, false) {
            Ok(s) => (
                s.stored_manifest()?,
                value(s.get("api-read".into(), None)?)?["summary"].clone(),
            ),
            Err(_) => (self.0.store.manifest(run)?, Value::Null),
        };
        Ok(
            json!({"runId":run,"generation":m.generation,"revision":m.revision,"loaded":!summary.is_null(),
            "phase":if summary.is_null(){"retained"}else{m.phase.as_str()},"savedPhase":m.phase,"step":m.step,"journalCount":m.journal_count,
            "configurationRevision":m.configuration_changes.last().map_or(0,|c|c.revision),"configuration":m.current_config(),
            "snapshot":m.checkpoint_sha256,"summary":summary,"metadata":self.document("runs",run).unwrap_or(json!({}))}),
        )
    }
    pub fn settings(&self, run: &str) -> Result<Value, AppError> {
        if let Ok(s) = self.owner(run, false) {
            return s.settings();
        }
        let verified = self.0.store.verify(run)?;
        let mut effective = value(verified.manifest.current_config())?;
        let limits = verified.manifest.effective_limits();
        effective["maximumSteps"] = json!(limits.maximum_steps);
        effective["maximumTurns"] = json!(limits.maximum_turns);
        effective["maximumDurationSeconds"] = json!(limits.maximum_duration_seconds);
        if let Some(settings) = verified
            .checkpoint
            .state
            .check_in_state
            .as_ref()
            .and_then(|c| c.settings_revisions.last())
        {
            effective["checkInSchedule"]["prompt"] = json!(settings.prompt);
            effective["checkInSchedule"]["includeTelemetry"] = json!(settings.include_telemetry);
        }
        if let Some(actions) = &verified.checkpoint.state.action_state {
            effective["leak"] = json!(actions.controls.leak);
            effective["feedbackScale"] = json!(actions.controls.feedback_scale);
            effective["recurrentGain"] = json!(actions.controls.recurrent_gain);
        }
        Ok(
            json!({"original":verified.manifest.config,"configured":verified.manifest.current_config(),"effective":effective,
            "configurationRevision":verified.checkpoint.state.configuration_phase.as_ref().map_or(0,|p|p.revision),"history":verified.manifest.configuration_changes}),
        )
    }
    pub fn entries(
        &self,
        run: &str,
        cursor: Option<&str>,
        limit: usize,
    ) -> Result<Value, AppError> {
        identifier(run)?;
        if !(1..=50).contains(&limit) {
            return Err(error("page", "Page size must be 1–50"));
        }
        let (token, offset) = if let Some(cursor) = cursor {
            let (token, offset) = cursor
                .rsplit_once('.')
                .ok_or_else(|| error("cursor", "Invalid cursor"))?;
            (
                token.to_owned(),
                offset
                    .parse::<usize>()
                    .map_err(|_| error("cursor", "Invalid cursor offset"))?,
            )
        } else {
            let (manifest, mut entries) = if let Ok(s) = self.owner(run, false) {
                s.catalog_snapshot()?
            } else {
                let v = self.0.store.verify(run)?;
                let entries = self.0.store.journal_index_at(&v.manifest)?;
                (v.manifest, entries)
            };
            entries.sort_by_key(|e| std::cmp::Reverse(e.attempt_id));
            let token = id("page");
            self.0.pages.lock().map_err(internal)?.insert(
                token.clone(),
                Page {
                    run_id: run.into(),
                    manifest,
                    entries,
                },
            );
            let mut order = self.0.page_order.lock().map_err(internal)?;
            order.push_back(token.clone());
            while order.len() > 128 {
                if let Some(old) = order.pop_front() {
                    self.0.pages.lock().map_err(internal)?.remove(&old);
                }
            }
            (token, 0)
        };
        let pages = self.0.pages.lock().map_err(internal)?;
        let p = pages.get(&token).ok_or_else(|| {
            error(
                "cursor-expired",
                "Restart pagination; this snapshot cursor expired",
            )
        })?;
        if p.run_id != run || offset > p.entries.len() {
            return Err(error(
                "cursor",
                "Cursor belongs to another run or exceeds its prefix",
            ));
        }
        let end = offset.saturating_add(limit).min(p.entries.len());
        Ok(
            json!({"runId":run,"snapshot":p.manifest.checkpoint_sha256,"total":p.entries.len(),"entries":p.entries[offset..end],
            "nextCursor":(end < p.entries.len()).then(||format!("{token}.{end}"))}),
        )
    }
    pub fn entry(&self, run: &str, entry: &str) -> Result<Value, AppError> {
        identifier(run)?;
        identifier(entry)?;
        let (manifest, rows) = if let Ok(s) = self.owner(run, false) {
            s.catalog_snapshot()?
        } else {
            let v = self.0.store.verify(run)?;
            let rows = self.0.store.journal_index_at(&v.manifest)?;
            (v.manifest, rows)
        };
        let row = rows
            .iter()
            .find(|r| r.entry_id == entry)
            .ok_or_else(|| error("not-found", "Entry is not in the committed prefix"))?;
        let (object, hash) = self.0.store.read_journal_proof(run, entry)?;
        if hash != row.object_sha256 {
            return Err(error(
                "verification",
                "Journal differs from committed evidence",
            ));
        }
        let phase = manifest
            .configuration_changes
            .iter()
            .rev()
            .find(|c| c.step < row.observed_step);
        let evidence = value(&object)?;
        let mut detail =
            SustainedState::project_journal(String::new(), &manifest, row, object, &hash)?;
        detail.journal["configurationRevision"] = json!(phase.map_or(0, |c| c.revision));
        detail.journal["configuration"] = value(phase.map_or(&manifest.config, |c| &c.config))?;
        detail.journal["evidence"] = evidence;
        // Keep the API's nullable receipt field stable for entries without actions.
        if detail.journal.get("actionReceipt").is_none() {
            detail.journal["actionReceipt"] = Value::Null;
        }
        Ok(json!({"runId":run,"snapshot":manifest.checkpoint_sha256,
            "generation":manifest.generation,"revision":manifest.revision,"journal":detail.journal}))
    }

    pub fn events(&self, run: &str, after: u64, limit: usize) -> Result<Value, AppError> {
        identifier(run)?;
        let m = if let Ok(s) = self.owner(run, false) {
            s.stored_manifest()?
        } else {
            self.0.store.verify(run)?.manifest
        };
        self.0.store.events(&m, after, limit)
    }
    pub fn sonar(&self, run: &str) -> Result<Value, AppError> {
        if let Ok(s) = self.owner(run, false) {
            let m = s.stored_manifest()?;
            return value(s.sonar_view(run, &m.generation, false)?);
        }
        let v = self.0.store.verify(run)?;
        value(SustainedState::sonar_checkpoint(
            run,
            &v.manifest.generation,
            v.checkpoint,
            false,
            None,
        )?)
    }
    pub fn documents(&self, kind: &str) -> Result<Value, AppError> {
        let db = self.0.db.lock().map_err(internal)?;
        let mut stmt = db
            .prepare("SELECT data FROM documents WHERE kind=? ORDER BY id")
            .map_err(internal)?;
        let raw: Vec<String> = stmt
            .query_map([kind], |r| r.get(0))
            .map_err(internal)?
            .collect::<Result<_, _>>()
            .map_err(internal)?;
        let docs: Vec<Value> = raw
            .into_iter()
            .map(|s| serde_json::from_str(&s))
            .collect::<Result<_, _>>()
            .map_err(internal)?;
        Ok(json!({"items":docs}))
    }
    pub fn document(&self, kind: &str, doc: &str) -> Result<Value, AppError> {
        identifier(doc)?;
        let raw: Option<String> = self
            .0
            .db
            .lock()
            .map_err(internal)?
            .query_row(
                "SELECT data FROM documents WHERE kind=? AND id=?",
                params![kind, doc],
                |r| r.get(0),
            )
            .optional()
            .map_err(internal)?;
        serde_json::from_str(&raw.ok_or_else(|| error("not-found", "Document not found"))?)
            .map_err(internal)
    }
    fn save_document(&self, kind: &str, doc: &str, data: &Value) -> Result<(), AppError> {
        self.0.db.lock().map_err(internal)?.execute("INSERT INTO documents VALUES (?,?,?) ON CONFLICT(kind,id) DO UPDATE SET data=excluded.data",params![kind,doc,data.to_string()]).map_err(internal)?;
        Ok(())
    }
    pub fn operation(&self, op: &str) -> Result<Operation, AppError> {
        identifier(op)?;
        let raw: Option<String> = self
            .0
            .db
            .lock()
            .map_err(internal)?
            .query_row("SELECT data FROM operations WHERE id=?", [op], |r| r.get(0))
            .optional()
            .map_err(internal)?;
        serde_json::from_str(&raw.ok_or_else(|| error("not-found", "Operation not found"))?)
            .map_err(internal)
    }
    fn unfinished_operations(&self) -> Result<Vec<Operation>, AppError> {
        let db = self.0.db.lock().map_err(internal)?;
        let mut stmt=db.prepare("SELECT data FROM operations WHERE json_extract(data, '$.status') IN ('queued','running','scheduled')").map_err(internal)?;
        let raw: Vec<String> = stmt
            .query_map([], |r| r.get(0))
            .map_err(internal)?
            .collect::<Result<_, _>>()
            .map_err(internal)?;
        raw.into_iter()
            .map(|v| serde_json::from_str(&v).map_err(internal))
            .collect()
    }
    pub fn operations(&self) -> Result<Vec<Operation>, AppError> {
        let db = self.0.db.lock().map_err(internal)?;
        let mut stmt = db.prepare("SELECT data FROM operations WHERE rowid IN (SELECT rowid FROM operations ORDER BY rowid DESC LIMIT 1000) OR json_extract(data, '$.status') IN ('queued','running','scheduled') ORDER BY rowid DESC").map_err(internal)?;
        let raw: Vec<String> = stmt
            .query_map([], |r| r.get(0))
            .map_err(internal)?
            .collect::<Result<_, _>>()
            .map_err(internal)?;
        raw.into_iter()
            .map(|s| serde_json::from_str(&s).map_err(internal))
            .collect()
    }
    fn save_operation(&self, op: &Operation) -> Result<(), AppError> {
        self.0
            .db
            .lock()
            .map_err(internal)?
            .execute(
                "UPDATE operations SET data=? WHERE id=?",
                params![serde_json::to_string(op).map_err(internal)?, op.id],
            )
            .map_err(internal)?;
        Ok(())
    }
    pub fn submit(
        &self,
        method: &str,
        path: &str,
        key: &str,
        request: Value,
    ) -> Result<Operation, AppError> {
        let close_recovery = method == "POST"
            && path.starts_with("/v1/runs/")
            && path.ends_with("/actions/retry-save");
        if self.0.closing.load(Ordering::SeqCst) && !close_recovery {
            return Err(error(
                "closing",
                "App is settling its runs; retained save work may still be retried",
            ));
        }
        if key.is_empty() || key.len() > 128 {
            return Err(error(
                "idempotency-key",
                "Supply a nonempty Idempotency-Key of at most 128 bytes",
            ));
        }
        let digest = files::digest(json!([method, path, request]).to_string().as_bytes());
        let op = Operation {
            id: id("op"),
            status: "queued".into(),
            method: method.into(),
            path: path.into(),
            request,
            result: None,
            error: None,
        };
        {
            let db = self.0.db.lock().map_err(internal)?;
            let existing: Option<(String, String)> = db
                .query_row(
                    "SELECT digest,data FROM operations WHERE key=?",
                    [key],
                    |r| Ok((r.get(0)?, r.get(1)?)),
                )
                .optional()
                .map_err(internal)?;
            if let Some((prior, raw)) = existing {
                if prior != digest {
                    return Err(error(
                        "idempotency-conflict",
                        "This key was used with a different request",
                    ));
                }
                return serde_json::from_str(&raw).map_err(internal);
            }
            if self
                .0
                .active_operations
                .fetch_update(Ordering::SeqCst, Ordering::SeqCst, |n| {
                    (n < 64).then_some(n + 1)
                })
                .is_err()
            {
                return Err(error("busy", "At most 64 operations may be outstanding"));
            }
            if let Err(e) = db.execute(
                "INSERT INTO operations VALUES (?,?,?,?)",
                params![
                    op.id,
                    key,
                    digest,
                    serde_json::to_string(&op).map_err(internal)?
                ],
            ) {
                self.0.active_operations.fetch_sub(1, Ordering::SeqCst);
                return Err(internal(e));
            }
        }
        let this = self.clone();
        let task = op.clone();
        std::thread::spawn(move || {
            this.execute(task);
            this.0.active_operations.fetch_sub(1, Ordering::SeqCst);
        });
        Ok(op)
    }
    fn execute(&self, mut op: Operation) {
        {
            let control = op
                .path
                .strip_prefix("/v1/runs/")
                .and_then(|p| {
                    p.strip_suffix("/settings")
                        .or_else(|| p.strip_suffix("/interventions"))
                })
                .map(|run| self.control(run));
            let _gate = control.as_ref().map(|c| c.gate.lock().unwrap());
            if self
                .operation(&op.id)
                .is_ok_and(|o| o.status == "cancelled")
            {
                return;
            }
            op.status = "running".into();
            if self.save_operation(&op).is_err() {
                return;
            }
        }
        let result = self.mutate(&op);
        match result {
            Ok(result) => {
                op.status = "completed".into();
                op.result = Some(result)
            }
            Err(e) => {
                op.status = if matches!(e.category.as_str(), "needs-attention" | "interrupted") {
                    "needsAttention"
                } else if e.category == "cancelled" {
                    "cancelled"
                } else {
                    "failed"
                }
                .into();
                op.error = Some(json!({"code":e.category,"message":e.message}));
            }
        }
        let _ = self.save_operation(&op);
    }
    fn create_run(
        &self,
        run: &str,
        config: SustainedConfig,
        metadata: Value,
    ) -> Result<Value, AppError> {
        let s = SustainedState::new(self.0.store.root.clone());
        s.set_scheduler(self.0.scheduler.clone());
        s.create_named("api-create".into(), config, Some(run.into()))?;
        self.0
            .owners
            .lock()
            .map_err(internal)?
            .insert(run.into(), s);
        self.save_document("runs", run, &metadata)?;
        self.run(run)
    }
    fn mutate(&self, op: &Operation) -> Result<Value, AppError> {
        let b = &op.request;
        let path: Vec<&str> = op.path.trim_matches('/').split('/').collect();
        match (op.method.as_str(), path.as_slice()) {
            ("POST", ["v1", "operations", target, "cancel"]) => self.cancel_operation(target),
            ("POST", ["v1", "runs"]) => {
                let mut cfg = value(SustainedConfig::default())?;
                merge(&mut cfg, b.get("config").unwrap_or(b));
                self.create_run(
                    &format!("run-{}", op.id.trim_start_matches("op-")),
                    configuration(&cfg)?,
                    b.get("metadata").cloned().unwrap_or(json!({})),
                )
            }
            ("POST", ["v1", "runs", run, "clone"]) => {
                let mut cfg = self.settings(run)?["effective"].clone();
                if let Some(p) = b.get("overrides") {
                    merge(&mut cfg, p);
                }
                self.create_run(
                    &format!("run-{}", op.id.trim_start_matches("op-")),
                    configuration(&cfg)?,
                    json!({"clonedFrom":run}),
                )
            }
            ("POST", ["v1", "runs", run, "interventions"]) => self.intervention(op, run),
            ("PATCH", ["v1", "runs", run, "settings"]) => self.change_settings(op, run, None),
            ("POST", ["v1", "runs", run, "actions", action]) => self.action(op, run, action),
            ("POST", ["v1", "runs", run, "exports"]) => {
                identifier(run)?;
                let dir = self.0.root.join("exports").join(&op.id);
                fs::create_dir_all(&dir).map_err(internal)?;
                let report = self
                    .0
                    .store
                    .export(run, &dir, &[self.0.store.root.clone()])?;
                let bundle = fs::read_dir(&dir)
                    .map_err(internal)?
                    .next()
                    .ok_or_else(|| error("export", "No export"))?
                    .map_err(internal)?
                    .path();
                let files = self.scan_export(&op.id)?;
                self.save_document("exports", &op.id, &files)?;
                Ok(
                    json!({"exportId":op.id,"bundleName":bundle.file_name().unwrap().to_string_lossy(),"report":report,"downloadUrl":format!("/v1/exports/{}/files",op.id)}),
                )
            }
            ("PATCH", ["v1", "settings"]) => {
                let n = b["maxConcurrentRequests"]
                    .as_u64()
                    .ok_or_else(|| error("configuration", "maxConcurrentRequests is required"))?;
                if n > 16 {
                    return Err(error("configuration", "Concurrency must be 1–16"));
                }
                self.0
                    .scheduler
                    .set_limit(n as usize)
                    .map_err(|m| error("configuration", m))?;
                self.save_document(
                    "settings",
                    "application",
                    &json!({"maxConcurrentRequests":n}),
                )?;
                Ok(self.0.scheduler.snapshot())
            }
            ("POST", ["v1", "models", "check"]) => {
                let config: reservoir_core::stage::LanguageConfiguration =
                    serde_json::from_value(b.clone())
                        .map_err(|e| error("configuration", e.to_string()))?;
                crate::model_transport::validate_configuration(&config)
                    .map_err(|e| error(e.category, e.message))?;
                let found = crate::model_transport::inventory(&config, &AtomicBool::new(false))
                    .map_err(|e| error(e.category, e.message))?;
                Ok(json!({"status":"found","model":found.name,"digest":found.digest}))
            }
            ("POST", ["v1", "recipes"]) => {
                self.expand_recipe(b, &op.id)?;
                let doc = id("recipe");
                let mut recipe = b.clone();
                recipe["id"] = json!(doc);
                self.save_document("recipes", &doc, &recipe)?;
                Ok(recipe)
            }
            ("POST", ["v1", "experiments"]) => self.prepare_experiment(op),
            ("POST", ["v1", "experiments", experiment, "actions", action]) => {
                let e = self.document("experiments", experiment)?;
                if e["status"] != "prepared" {
                    return Err(error(
                        "needs-attention",
                        "Experiment preparation did not complete; inspect its member runs",
                    ));
                }
                let runs = e["runIds"]
                    .as_array()
                    .ok_or_else(|| error("experiment", "Missing members"))?;
                if matches!(*action, "start" | "resume") {
                    if let Some(n) = e["recipe"]["maxConcurrentRequests"].as_u64() {
                        self.0.scheduler.set_limit(n as usize).map_err(internal)?;
                        self.save_document(
                            "settings",
                            "application",
                            &json!({"maxConcurrentRequests":n,"sourceExperiment":experiment}),
                        )?;
                    }
                }
                let mut results = Vec::new();
                for run in runs {
                    let run = run
                        .as_str()
                        .ok_or_else(|| error("experiment", "Invalid member"))?;
                    results.push(match self.action(op, run, action) {
                        Ok(result) => json!({"runId":run,"result":result}),
                        Err(e) => json!({"runId":run,"error":e}),
                    });
                }
                Ok(
                    json!({"experimentId":experiment,"partial":results.iter().any(|r|r.get("error").is_some()),"results":results}),
                )
            }
            _ => Err(error("not-found", "Unknown mutation route")),
        }
    }
    fn action(&self, op: &Operation, run: &str, action: &str) -> Result<Value, AppError> {
        let control = self.control(run);
        let gate = control.gate.lock().map_err(internal)?;
        let s = self.owner(run, true)?;
        let m = s.stored_manifest()?;
        if let Some(g) = op.request.get("generation").and_then(Value::as_str) {
            if g != m.generation {
                return Err(error("stale", "Run generation changed"));
            }
        }
        match action {
            "start" | "resume" => {
                if self.0.pending.lock().map_err(internal)?.contains_key(run) {
                    return Err(error("conflict", "A configuration transition is pending"));
                }
                control.epoch.fetch_add(1, Ordering::SeqCst);
                control.resume_suppressed.store(false, Ordering::SeqCst);
                s.cancel_boundary_pause();
                self.admit(|| value(s.start(op.id.clone(), run, &m.generation)?))
            }
            "pause" => {
                if m.phase == "stopped" {
                    return Err(error("phase", "The run is already stopped"));
                }
                control.epoch.fetch_add(1, Ordering::SeqCst);
                control.resume_suppressed.store(true, Ordering::SeqCst);
                self.cancel_pending(run)?;
                s.disable_target_resume();
                s.request_boundary_pause();
                drop(gate);
                if !s.get("pause".into(), None)?.summary.unwrap().can_pause {
                    return value(s.pause(op.id.clone(), run, &m.generation)?);
                }
                self.wait_boundary(&s, op)?;
                self.run(run)
            }
            "stop" => {
                control.epoch.fetch_add(1, Ordering::SeqCst);
                control.resume_suppressed.store(true, Ordering::SeqCst);
                self.cancel_pending(run)?;
                s.cancel_boundary_pause();
                value(s.stop(op.id.clone(), run, &m.generation)?)
            }
            "extend-limits" => {
                let limits = serde_json::from_value(op.request.clone())
                    .map_err(|e| error("configuration", e.to_string()))?;
                value(s.extend_limits(op.id.clone(), run, &m.generation, &m.revision, limits)?)
            }
            "retry-save" => value(s.retry_save(op.id.clone(), run, &m.generation)?),
            "retry-writing" => {
                self.admit(|| value(s.retry_language(op.id.clone(), run, &m.generation)?))
            }
            "retry-encoding" => {
                self.admit(|| value(s.retry_embedding(op.id.clone(), run, &m.generation)?))
            }
            "skip-feedback" => value(s.skip(
                op.id.clone(),
                run,
                &m.generation,
                op.request["entryId"].as_str().map(str::to_owned),
                op.request["attemptId"].as_u64(),
            )?),
            _ => Err(error("not-found", "Unknown run action")),
        }
    }
    fn wait_boundary(&self, s: &SustainedState, op: &Operation) -> Result<(), AppError> {
        loop {
            if self.0.closing.load(Ordering::SeqCst) {
                return Err(error("interrupted", "App is closing"));
            }
            if self.operation(&op.id)?.status == "cancelled" {
                return Err(error("cancelled", "Operation cancelled"));
            }
            if s.settled_boundary() {
                return Ok(());
            }
            let u = s
                .get("boundary".into(), None)?
                .summary
                .ok_or_else(|| error("missing", "Run disappeared"))?;
            if !u.can_pause
                && (!s.is_busy()
                    || u.can_retry_save
                    || u.can_retry_provider
                    || u.can_retry_embedding
                    || u.can_skip_feedback
                    || u.phase == "stopped")
            {
                return Err(error(
                    "needs-attention",
                    "Resolve the retained turn before applying the configuration",
                ));
            }
            std::thread::sleep(Duration::from_millis(50));
        }
    }
    fn cancel_pending(&self, run: &str) -> Result<(), AppError> {
        if let Some(id) = self.0.pending.lock().map_err(internal)?.get(run).cloned() {
            let mut op = self.operation(&id)?;
            op.status = "cancelled".into();
            self.save_operation(&op)?;
        }
        Ok(())
    }
    pub fn cancel_operation(&self, op: &str) -> Result<Value, AppError> {
        let mut o = self.operation(op)?;
        let run = o
            .path
            .strip_prefix("/v1/runs/")
            .and_then(|p| {
                p.strip_suffix("/settings")
                    .or_else(|| p.strip_suffix("/interventions"))
            })
            .ok_or_else(|| {
                error(
                    "conflict",
                    "Only pending run settings or interventions can be cancelled",
                )
            })?
            .to_owned();
        let control = self.control(&run);
        let _gate = control.gate.lock().map_err(internal)?;
        o = self.operation(op)?;
        if self
            .0
            .store
            .manifest(&run)?
            .configuration_changes
            .iter()
            .any(|c| c.operation_id == op)
        {
            return Err(error("conflict", "Configuration already applied"));
        }
        if !matches!(o.status.as_str(), "queued" | "running" | "scheduled") {
            return Err(error(
                "conflict",
                "Only an unapplied intervention can be cancelled",
            ));
        }
        o.status = "cancelled".into();
        self.save_operation(&o)?;
        value(o)
    }
    fn change_settings(
        &self,
        op: &Operation,
        run: &str,
        resume: Option<bool>,
    ) -> Result<Value, AppError> {
        let s = self.owner(run, true)?;
        let control = self.control(run);
        let initial_gate = control.gate.lock().map_err(internal)?;
        let epoch = control.epoch.load(Ordering::SeqCst);
        let was_running = resume
            .unwrap_or(s.get("change".into(), None)?.summary.unwrap().can_pause)
            && !control.resume_suppressed.load(Ordering::SeqCst);
        {
            let mut pending = self.0.pending.lock().map_err(internal)?;
            if pending.contains_key(run) {
                return Err(error("conflict", "A settings change is already pending"));
            }
            pending.insert(run.into(), op.id.clone());
        }
        drop(initial_gate);
        let mut applying = false;
        let result = (|| {
            let expected = op.request["expectedConfigurationRevision"]
                .as_u64()
                .ok_or_else(|| {
                    error("configuration", "expectedConfigurationRevision is required")
                })?;
            let settings = s.settings()?;
            if settings["configurationRevision"] != expected {
                return Err(error("stale", "Configuration revision changed"));
            }
            let mut cfg = settings["effective"].clone();
            let patch = op
                .request
                .get("patch")
                .filter(|p| p.is_object())
                .ok_or_else(|| error("configuration", "patch must be an object"))?;
            merge(&mut cfg, patch);
            let cfg = configuration(&cfg)?;
            if cfg.seed != s.stored_manifest()?.config.seed {
                return Err(error("configuration", "Seed requires a fresh linked run"));
            }
            s.request_boundary_pause();
            self.wait_boundary(&s, op)?;
            if self.operation(&op.id)?.status == "cancelled" {
                return Err(error("cancelled", "Operation cancelled"));
            }
            let _gate = control.gate.lock().map_err(internal)?;
            if control.epoch.load(Ordering::SeqCst) != epoch
                || self.operation(&op.id)?.status == "cancelled"
            {
                return Err(error(
                    "cancelled",
                    "A later lifecycle request superseded this change",
                ));
            }
            // Untargeted authored controls may have changed while the old turn drained.
            let mut effective = s.settings()?["effective"].clone();
            merge(&mut effective, patch);
            applying = true;
            let mut result = s.apply_configuration(&op.id, expected, configuration(&effective)?)?;
            if resume.is_some() {
                s.disarm_boundary(&op.id);
            }
            if was_running
                && !self.0.closing.load(Ordering::SeqCst)
                && self.operation(&op.id)?.status != "cancelled"
            {
                let m = s.stored_manifest()?;
                if let Err(e) = self.admit(|| s.start(op.id.clone(), run, &m.generation)) {
                    result["resumeError"] = json!({"code":e.category,"message":e.message});
                }
            }
            Ok(result)
        })();
        self.0.pending.lock().map_err(internal)?.remove(run);
        if result.is_err() && !applying {
            let _gate = control.gate.lock().map_err(internal)?;
            if control.epoch.load(Ordering::SeqCst) == epoch {
                s.cancel_boundary_pause();
                if was_running && s.settled_boundary() && !self.0.closing.load(Ordering::SeqCst) {
                    let m = s.stored_manifest()?;
                    let _ = self.admit(|| s.start(op.id.clone(), run, &m.generation));
                }
            }
        }
        result
    }
    fn intervention(&self, op: &Operation, run: &str) -> Result<Value, AppError> {
        let b = &op.request;
        validate_intervention(b)?;
        let at = &b["at"];
        let step = at.get("step").and_then(Value::as_u64);
        let seconds = at.get("activeSeconds").and_then(Value::as_u64);
        if !at.is_object()
            || at.as_object().unwrap().len() != 1
            || step.is_some() == seconds.is_some()
            || step.is_some_and(|n| n == 0 || n > 10_000_000)
            || seconds.is_some_and(|n| n == 0 || n > 604800)
        {
            return Err(error(
                "configuration",
                "at requires exactly one positive step or activeSeconds",
            ));
        }
        let s = self.owner(run, true)?;
        let kind = b["kind"].as_str().unwrap_or("");
        match kind {
            "configuration" => {
                let patch = b.get("patch").filter(|p| p.is_object()).ok_or_else(|| {
                    error(
                        "configuration",
                        "A configuration intervention needs a patch object",
                    )
                })?;
                let mut config = s.settings()?["effective"].clone();
                merge(&mut config, patch);
                configuration(&config)?;
            }
            "prompt" => {
                let p = b["prompt"]
                    .as_str()
                    .ok_or_else(|| error("configuration", "prompt is required"))?;
                if p.trim().is_empty() || p.len() > 16384 || !b["includeTelemetry"].is_boolean() {
                    return Err(error(
                        "configuration",
                        "Prompt requires 1–16,384 UTF-8 bytes and includeTelemetry boolean",
                    ));
                }
            }
            _ => {
                return Err(error(
                    "configuration",
                    "Intervention kind must be configuration or prompt",
                ))
            }
        }
        let control = self.control(run);
        {
            let _gate = control.gate.lock().map_err(internal)?;
            if self.operation(&op.id)?.status == "cancelled" {
                return Err(error("cancelled", "Intervention cancelled"));
            }
            s.arm_boundary(&op.id, step, seconds.map(|t| t * 1000))?;
            let mut scheduled = op.clone();
            scheduled.status = "scheduled".into();
            self.save_operation(&scheduled)?;
        }
        let result = (|| {
            loop {
                if self.0.closing.load(Ordering::SeqCst) {
                    return Err(error(
                        "interrupted",
                        "App closed before intervention; explicit resubmission is required",
                    ));
                }
                if self.operation(&op.id)?.status == "cancelled" {
                    return Err(error("cancelled", "Intervention cancelled"));
                }
                let state = s
                    .get("intervention".into(), None)?
                    .summary
                    .ok_or_else(|| error("missing", "Run disappeared"))?;
                if matches!(
                    state.phase.as_str(),
                    "stopped" | "interrupted" | "budgetReached" | "scheduleComplete"
                ) {
                    return Err(error("needs-attention","Run stopped, was interrupted, or reached its budget before the intervention"));
                }
                if s.boundary_reached(&op.id).is_some() {
                    break;
                }
                std::thread::sleep(Duration::from_millis(25));
            }
            self.wait_boundary(&s, op)?;
            let resume = s.boundary_reached(&op.id).unwrap_or(false);
            let result = if kind == "configuration" {
                let mut change = op.clone();
                change.request = json!({"patch":b["patch"],"expectedConfigurationRevision":b.get("expectedConfigurationRevision").cloned().unwrap_or(s.settings()?["configurationRevision"].clone())});
                self.change_settings(&change, run, Some(resume))?
            } else {
                let _gate = control.gate.lock().map_err(internal)?;
                if self.operation(&op.id)?.status == "cancelled" {
                    return Err(error("cancelled", "Intervention cancelled"));
                }
                if control.resume_suppressed.load(Ordering::SeqCst) {
                    return Err(error("needs-attention", "Run was paused before scheduled prompt admission; explicitly resubmit after resume"));
                }
                let admitted = self.admit(|| {
                    s.custom_prompt(
                        &op.id,
                        b["prompt"].as_str().unwrap().into(),
                        b["includeTelemetry"].as_bool().unwrap(),
                        resume,
                    )
                })?;
                let mut committed = op.clone();
                committed.status = "completed".into();
                committed.result = Some(json!({"requestedBoundary":at,"applied":admitted}));
                self.save_operation(&committed)?;
                admitted
            };
            Ok(json!({"requestedBoundary":at,"applied":result}))
        })();
        let _gate = control.gate.lock().map_err(internal)?;
        let resume = s.boundary_reached(&op.id) == Some(true)
            && !control.resume_suppressed.load(Ordering::SeqCst);
        s.disarm_boundary(&op.id);
        if result.as_ref().is_err_and(|e| e.category == "cancelled")
            && resume
            && !self.0.closing.load(Ordering::SeqCst)
        {
            if s.settled_boundary()
                && s.get("cancel-intervention".into(), None)?
                    .summary
                    .is_some_and(|s| s.phase == "paused")
            {
                let m = s.stored_manifest()?;
                let _ = self.admit(|| s.start(op.id.clone(), run, &m.generation));
            }
        }
        result
    }
    pub fn interventions(&self, run: &str) -> Result<Value, AppError> {
        identifier(run)?;
        let path = format!("/v1/runs/{run}/interventions");
        Ok(
            json!({"operations":self.operations()?.into_iter().filter(|o|o.path==path).collect::<Vec<_>>()}),
        )
    }
    pub fn expand_recipe(
        &self,
        recipe: &Value,
        group: &str,
    ) -> Result<Vec<(String, SustainedConfig)>, AppError> {
        if recipe["version"] != 1 {
            return Err(error("recipe", "Recipe version must be 1"));
        }
        if recipe
            .get("maxConcurrentRequests")
            .is_some_and(|n| n.as_u64().is_none_or(|n| !(1..=16).contains(&n)))
        {
            return Err(error("recipe", "maxConcurrentRequests must be 1–16"));
        }
        let arms = recipe["arms"]
            .as_array()
            .filter(|a| !a.is_empty() && a.len() <= 32)
            .ok_or_else(|| error("recipe", "Supply 1–32 named arms"))?;
        let mut configs = Vec::new();
        let mut intervention_count = 0;
        let mut names = std::collections::BTreeSet::new();
        for arm in arms {
            let name = arm["name"]
                .as_str()
                .ok_or_else(|| error("recipe", "Each arm needs a name"))?;
            identifier(name)?;
            if !names.insert(name) {
                return Err(error("recipe", "Arm names must be unique"));
            }
            let mut cfg = value(SustainedConfig::default())?;
            if let Some(base) = recipe.get("baseConfig") {
                merge(&mut cfg, base);
            }
            if let Some(patch) = arm.get("overrides") {
                merge(&mut cfg, patch);
            }
            for definitions in [recipe.get("interventions"), arm.get("interventions")]
                .into_iter()
                .flatten()
            {
                let definitions = definitions
                    .as_array()
                    .ok_or_else(|| error("recipe", "interventions must be an array"))?;
                intervention_count += definitions.len();
                for definition in definitions {
                    validate_intervention(definition)?;
                }
            }
            if intervention_count > 48 {
                return Err(error(
                    "recipe",
                    "A recipe may schedule at most 48 interventions across its arms",
                ));
            }
            configs.push((name.to_owned(), configuration(&cfg)?));
        }
        if recipe["peerReading"].as_bool() == Some(true) {
            if !(2..=4).contains(&configs.len()) {
                return Err(error("recipe", "Reciprocal peer groups require 2–4 arms"));
            }
            let names: Vec<_> = configs.iter().map(|(n, _)| n.clone()).collect();
            for (name, cfg) in &mut configs {
                cfg.peer_reading = Some(reservoir_core::sustained::SustainedPeerConfig {
                    version: reservoir_core::sustained::SustainedPeerVersion::LatestAppliedV1,
                    group: group.into(),
                    participant: name.clone(),
                    peers: names.iter().filter(|n| *n != name).cloned().collect(),
                });
                cfg.validate()?;
            }
        }
        Ok(configs)
    }
    fn prepare_experiment(&self, op: &Operation) -> Result<Value, AppError> {
        let recipe = if let Some(id) = op.request["recipeId"].as_str() {
            self.document("recipes", id)?
        } else {
            op.request
                .get("recipe")
                .cloned()
                .unwrap_or(op.request.clone())
        };
        let experiment = format!("experiment-{}", op.id.trim_start_matches("op-"));
        let expanded = self.expand_recipe(&recipe, &experiment)?;
        let planned: Vec<_> = (0..expanded.len())
            .map(|i| format!("{}-{i}", experiment.replace("experiment-", "run-")))
            .collect();
        self.save_document(
            "experiments",
            &experiment,
            &json!({"id":experiment,"recipe":recipe,"runIds":planned,"status":"preparing"}),
        )?;
        let mut runs = Vec::new();
        for (i, (name, config)) in expanded.iter().enumerate() {
            let run = format!("{}-{i}", experiment.replace("experiment-", "run-"));
            self.create_run(
                &run,
                config.clone(),
                json!({"experimentId":experiment,"name":name}),
            )?;
            let arm = &recipe["arms"][i];
            for (j, definition) in [recipe.get("interventions"), arm.get("interventions")]
                .into_iter()
                .flatten()
                .flat_map(|v| v.as_array().unwrap())
                .enumerate()
            {
                let child = self.submit(
                    "POST",
                    &format!("/v1/runs/{run}/interventions"),
                    &format!("{}-{i}-{j}", op.id),
                    definition.clone(),
                )?;
                let deadline = std::time::Instant::now() + Duration::from_secs(10);
                loop {
                    let state = self.operation(&child.id)?;
                    if state.status == "scheduled" {
                        break;
                    }
                    if state.status != "queued" && state.status != "running" {
                        return Err(error(
                            "recipe",
                            format!(
                                "Intervention {} could not be armed: {:?}",
                                child.id, state.error
                            ),
                        ));
                    }
                    if std::time::Instant::now() > deadline {
                        return Err(error(
                            "needs-attention",
                            "Intervention arming did not finish",
                        ));
                    }
                    std::thread::sleep(Duration::from_millis(10));
                }
            }
            runs.push(run);
        }
        let doc = json!({"id":experiment,"recipe":recipe,"runIds":runs,"resolved":expanded.iter().map(|(name,config)|json!({"name":name,"config":config})).collect::<Vec<_>>(),"status":"prepared"});
        self.save_document("experiments", &experiment, &doc)?;
        Ok(doc)
    }
    pub fn scheduler(&self) -> Value {
        self.0.scheduler.snapshot()
    }
    pub fn interrupt(&self, reason: &str) {
        self.adopt_primary();
        for s in self.0.owners.lock().unwrap().values() {
            s.interrupt(reason);
        }
    }
    pub fn busy(&self) -> bool {
        self.adopt_primary();
        self.0.owners.lock().unwrap().values().any(|s| s.is_busy())
    }
    pub fn close(&self) -> bool {
        self.0.closing.store(true, Ordering::SeqCst);
        self.adopt_primary();
        self.0
            .owners
            .lock()
            .unwrap()
            .values()
            .fold(true, |ready, s| {
                s.retain_shutdown().unwrap_or(false) && ready
            })
            && self.0.active_operations.load(Ordering::SeqCst) == 0
    }
    pub fn reopen(&self) {
        self.0.closing.store(false, Ordering::SeqCst);
        for s in self.0.owners.lock().unwrap().values() {
            s.cancel_close();
        }
    }
    pub fn export_files(&self, export: &str) -> Result<Value, AppError> {
        identifier(export)?;
        let op = self.operation(export)?;
        if op.status != "completed" || !op.path.ends_with("/exports") {
            return Err(error("not-found", "Export is not complete"));
        }
        if let Ok(index) = self.document("exports", export) {
            return Ok(index);
        }
        let index = self.scan_export(export)?;
        self.save_document("exports", export, &index)?;
        Ok(index)
    }
    fn scan_export(&self, export: &str) -> Result<Value, AppError> {
        let root = self.0.root.join("exports").join(export);
        let bundle = fs::read_dir(&root)
            .map_err(internal)?
            .next()
            .ok_or_else(|| error("not-found", "Export missing"))?
            .map_err(internal)?
            .path();
        fn walk(root: &Path, p: &Path, rows: &mut Vec<Value>) -> Result<(), AppError> {
            for item in fs::read_dir(p).map_err(internal)? {
                let e = item.map_err(internal)?;
                let t = e.file_type().map_err(internal)?;
                if t.is_dir() {
                    walk(root, &e.path(), rows)?;
                } else if t.is_file() {
                    let data = files::read_bounded(&e.path(), 64 * 1024 * 1024, "api-export")?;
                    rows.push(json!({"path":e.path().strip_prefix(root).map_err(internal)?.to_string_lossy(),"sha256":files::digest(&data),"bytes":data.len()}));
                } else {
                    return Err(error("ownership", "Export contains a nonordinary file"));
                }
            }
            Ok(())
        }
        let mut rows = Vec::new();
        walk(&bundle, &bundle, &mut rows)?;
        Ok(json!({"bundleName":bundle.file_name().unwrap().to_string_lossy(),"files":rows}))
    }
    pub fn export_file(&self, export: &str, relative: &str) -> Result<Vec<u8>, AppError> {
        let index = self.export_files(export)?;
        if !index["files"]
            .as_array()
            .unwrap()
            .iter()
            .any(|f| f["path"] == relative)
        {
            return Err(error("not-found", "File is not in the exported snapshot"));
        }
        let root = self.0.root.join("exports").join(export);
        let bundle = fs::read_dir(root)
            .map_err(internal)?
            .next()
            .ok_or_else(|| error("not-found", "Export missing"))?
            .map_err(internal)?
            .path();
        let bytes = files::read_bounded(&bundle.join(relative), 64 * 1024 * 1024, "api-export")?;
        let record = index["files"]
            .as_array()
            .unwrap()
            .iter()
            .find(|f| f["path"] == relative)
            .unwrap();
        if record["bytes"] != bytes.len() || record["sha256"] != files::digest(&bytes) {
            return Err(error(
                "verification",
                "Export file differs from its frozen snapshot",
            ));
        }
        Ok(bytes)
    }
}

#[cfg(test)]
#[path = "research_tests.rs"]
mod tests;
