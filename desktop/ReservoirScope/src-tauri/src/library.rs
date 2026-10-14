//! Application-owned Library. Records are immutable, content-addressed bytes;
//! SQLite is a disposable metadata projection, never numerical evidence.
use crate::{
    files::{self, AppError},
    records::{OpenResult, RecordState},
    resources,
};
use reservoir_core::{verify_bytes, VerificationReport, VerificationStatus, MAX_RECORD_BYTES};
use rusqlite::{params, Connection, OpenFlags, OptionalExtension};
use serde::{Deserialize, Serialize};
use std::{
    collections::HashSet,
    fs,
    io::Write,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    time::{Duration, SystemTime, UNIX_EPOCH},
};

const OWNER: &[u8] =
    b"{\"schema\":\"reservoir-scope-library-v1\",\"app\":\"research.reservoir.scope.tauri\"}\n";
const META_LIMIT: u64 = 64 * 1024;
pub const PAGE_LIMIT: usize = 100;
#[derive(Deserialize)]
struct CatalogItem {
    id: String,
    title: String,
    file: String,
    group: Option<String>,
    order: Option<usize>,
}
fn error(category: &str, message: impl Into<String>) -> AppError {
    AppError::new("library", category, message)
}
fn db_error(e: rusqlite::Error) -> AppError {
    error(
        "index",
        format!("Library index unavailable: {e}. Records remain intact; rebuild the index."),
    )
}
fn io_error(e: std::io::Error) -> AppError {
    error("storage", e.to_string())
}
fn now() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis()
        .min(i64::MAX as u128) as i64
}
fn hash_id(id: &str) -> Option<&str> {
    id.strip_prefix("sha256:").filter(|s| {
        s.len() == 64
            && s.bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    })
}
fn unknown_source() -> String {
    "unknown".into()
}
fn managed_origin() -> String {
    "managed".into()
}
fn diagnostic_file_id(name: &std::ffi::OsStr) -> String {
    format!("file:{}", files::digest(name.as_encoded_bytes()))
}
fn bounded(text: &str) -> String {
    text.chars().take(4096).collect()
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LibraryEntry {
    pub id: String,
    pub title: String,
    pub filename: String,
    pub origin: String,
    pub family: String,
    pub format: String,
    pub stage: Option<String>,
    pub backend: String,
    #[serde(default = "unknown_source")]
    pub source: String,
    pub model: String,
    pub seed: Option<String>,
    pub embedded_id: Option<String>,
    pub outcome: String,
    pub health: String,
    pub diagnostic: Option<String>,
    pub sha256: Option<String>,
    pub saved_at_ms: Option<i64>,
    pub last_opened_at_ms: Option<i64>,
    pub catalog_order: Option<usize>,
}
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LibraryQuery {
    #[serde(default)]
    pub text: String,
    pub origin: Option<String>,
    pub family: Option<String>,
    pub source: Option<String>,
    pub outcome: Option<String>,
    #[serde(default)]
    pub recent_only: bool,
    #[serde(default)]
    pub diagnostics_only: bool,
    #[serde(default)]
    pub offset: usize,
    pub limit: Option<usize>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ScanStatus {
    pub phase: String,
    pub complete: bool,
    pub examined: usize,
    pub indexed: usize,
    pub diagnostic_count: usize,
    pub message: String,
    pub finished_at_ms: Option<i64>,
}
impl Default for ScanStatus {
    fn default() -> Self {
        Self {
            phase: "notScanned".into(),
            complete: false,
            examined: 0,
            indexed: 0,
            diagnostic_count: 0,
            message: "Managed files have not been scanned. Refresh to establish coverage.".into(),
            finished_at_ms: None,
        }
    }
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct LibraryPage {
    pub entries: Vec<LibraryEntry>,
    pub total: usize,
    pub offset: usize,
    pub limit: usize,
    pub has_more: bool,
    pub coverage: ScanStatus,
    pub diagnostics: Vec<String>,
    pub storage_path: String,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct LibraryImportResult {
    pub request_id: String,
    pub cancelled: bool,
    pub published: bool,
    pub duplicate: bool,
    pub entry_id: Option<String>,
    pub report: Option<VerificationReport>,
    pub diagnostics: Vec<String>,
}
impl LibraryImportResult {
    pub fn cancelled(request_id: String) -> Self {
        Self {
            request_id,
            cancelled: true,
            published: false,
            duplicate: false,
            entry_id: None,
            report: None,
            diagnostics: vec![],
        }
    }
}
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct LocalMetadata {
    schema: String,
    sha256: String,
    filename: String,
    saved_at_ms: i64,
    #[serde(default = "managed_origin")]
    origin: String,
}

#[derive(Clone)]
pub struct LibraryState {
    root: PathBuf,
    resources: PathBuf,
    mutation: Arc<Mutex<()>>,
    initialization: Arc<Mutex<()>>,
    index_gate: Arc<Mutex<()>>,
    status: Arc<Mutex<ScanStatus>>,
    cancel: Arc<AtomicBool>,
}
impl LibraryState {
    /// Root must be this app's data directory + `library-v1`, never a sibling store.
    /// Construction is lazy so index damage cannot prevent desktop startup.
    pub fn new(root: PathBuf, resources: PathBuf) -> Self {
        Self {
            root,
            resources,
            mutation: Arc::new(Mutex::new(())),
            initialization: Arc::new(Mutex::new(())),
            index_gate: Arc::new(Mutex::new(())),
            status: Arc::new(Mutex::new(ScanStatus::default())),
            cancel: Arc::new(AtomicBool::new(false)),
        }
    }
    fn owned(&self) -> Result<(), AppError> {
        let _setup = self
            .initialization
            .lock()
            .map_err(|_| error("ownership", "Library initialization lock unavailable."))?;
        if !self.root.is_absolute() {
            return Err(error("ownership", "Library root must be absolute."));
        }
        if let Ok(m) = fs::symlink_metadata(&self.root) {
            if !m.file_type().is_dir() {
                return Err(error(
                    "ownership",
                    "Library root must be an ordinary directory, not a link.",
                ));
            }
        }
        fs::create_dir_all(&self.root).map_err(io_error)?;
        let marker = self.root.join("owner.json");
        if marker.try_exists().map_err(io_error)? {
            if files::read_bounded(&marker, META_LIMIT, "library-owner")? != OWNER {
                return Err(error(
                    "ownership",
                    "This directory is not this application's Library.",
                ));
            }
        } else {
            if fs::read_dir(&self.root).map_err(io_error)?.next().is_some() {
                return Err(error(
                    "ownership",
                    "Refusing to adopt an existing unmarked directory as a Library.",
                ));
            }
            publish_new(&marker, OWNER)?;
        }
        for name in ["records", "metadata"] {
            let path = self.root.join(name);
            if let Ok(m) = fs::symlink_metadata(&path) {
                if !m.file_type().is_dir() {
                    return Err(error(
                        "ownership",
                        format!("Library {name} must be an ordinary directory."),
                    ));
                }
            }
            fs::create_dir_all(path).map_err(io_error)?;
        }
        Ok(())
    }
    fn connection(&self) -> Result<Connection, AppError> {
        self.owned()?;
        // SQLite NOFOLLOW checks every path component; macOS /var is an OS alias.
        // Validate our root/leaf first, then use its canonical directory for SQLite.
        let path = fs::canonicalize(&self.root)
            .map_err(io_error)?
            .join("index.sqlite3");
        if let Ok(m) = fs::symlink_metadata(&path) {
            if !m.file_type().is_file() {
                return Err(error(
                    "index",
                    "Library index is not a regular file. Rebuild the index.",
                ));
            }
        }
        let c = Connection::open_with_flags(
            path,
            OpenFlags::SQLITE_OPEN_READ_WRITE
                | OpenFlags::SQLITE_OPEN_CREATE
                | OpenFlags::SQLITE_OPEN_NOFOLLOW
                | OpenFlags::SQLITE_OPEN_NO_MUTEX,
        )
        .map_err(db_error)?;
        c.busy_timeout(Duration::from_secs(2)).map_err(db_error)?;
        c.execute_batch("PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;
            CREATE TABLE IF NOT EXISTS entries(id TEXT PRIMARY KEY, origin TEXT NOT NULL, family TEXT NOT NULL, source TEXT NOT NULL, outcome TEXT NOT NULL, health TEXT NOT NULL, search TEXT NOT NULL, saved INTEGER NOT NULL, ordinal INTEGER NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS recents(id TEXT PRIMARY KEY, opened INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS entry_order ON entries(origin, saved DESC, ordinal, id);").map_err(db_error)?;
        Ok(c)
    }
    pub fn scan_status(&self) -> ScanStatus {
        self.status
            .lock()
            .map(|s| s.clone())
            .unwrap_or_else(|_| ScanStatus {
                phase: "failed".into(),
                message: "Scan status is unavailable; restart the app.".into(),
                ..Default::default()
            })
    }
    pub fn cancel_scan(&self) -> ScanStatus {
        self.cancel.store(true, Ordering::Release);
        self.scan_status()
    }
    fn set_status(&self, value: ScanStatus) {
        if let Ok(mut status) = self.status.lock() {
            *status = value;
        }
    }
    pub fn query(&self, query: LibraryQuery) -> Result<LibraryPage, AppError> {
        let _guard = self
            .index_gate
            .lock()
            .map_err(|_| error("index", "Index lock unavailable."))?;
        let c = self.connection()?;
        // Catalog remains available before the first managed scan. These are metadata
        // rows only; opening an example always verifies its bounded original snapshot.
        let catalog_count: i64 = c
            .query_row(
                "SELECT COUNT(*) FROM entries WHERE origin='bundled'",
                [],
                |r| r.get(0),
            )
            .map_err(db_error)?;
        let catalog_identity: Option<String> = c
            .query_row(
                "SELECT value FROM settings WHERE key='catalog-build'",
                [],
                |row| row.get(0),
            )
            .optional()
            .map_err(db_error)?;
        if catalog_count == 0 || catalog_identity.as_deref() != Some(&Self::catalog_identity()) {
            self.index_catalog(&c)?;
        }
        let limit = query.limit.unwrap_or(50).clamp(1, PAGE_LIMIT);
        if query.text.chars().count() > 4096 || query.offset > i64::MAX as usize {
            return Err(error("query", "Library query is outside its bounds."));
        }
        let text = query.text.to_lowercase();
        let origin = filter(query.origin, &["managed", "created", "bundled"])?;
        let family = filter(
            query.family,
            &["stage", "exploration", "actions", "regulation", "unknown"],
        )?;
        let source = filter(
            query.source,
            &["scripted", "model", "fixedReplay", "numerical", "unknown"],
        )?;
        let outcome = query
            .outcome
            .filter(|s| !s.is_empty() && s != "all")
            .unwrap_or_default();
        if outcome.len() > 128 {
            return Err(error("query", "Outcome filter is too long."));
        }
        let conditions = "FROM entries e LEFT JOIN recents r ON r.id=e.id WHERE (?1='' OR instr(e.search,?1)>0) AND (?2='' OR e.origin=?2) AND (?3='' OR e.family=?3) AND (?4='' OR COALESCE(json_extract(e.payload,'$.source'),'unknown')=?4) AND (?5='' OR e.outcome=?5) AND (?6=0 OR r.opened IS NOT NULL) AND (?7=0 OR e.health NOT IN ('ready','unverified'))";
        let count_sql = format!("SELECT COUNT(*) {conditions}");
        let total: i64 = c
            .query_row(
                &count_sql,
                params![
                    text,
                    origin,
                    family,
                    source,
                    outcome,
                    query.recent_only,
                    query.diagnostics_only
                ],
                |r| r.get(0),
            )
            .map_err(db_error)?;
        let order = if query.recent_only {
            "r.opened DESC,e.id"
        } else {
            "CASE e.origin WHEN 'bundled' THEN 0 ELSE 1 END,e.ordinal,e.saved DESC,e.id"
        };
        let sql =
            format!("SELECT e.payload,r.opened {conditions} ORDER BY {order} LIMIT ?8 OFFSET ?9");
        let mut statement = c.prepare(&sql).map_err(db_error)?;
        let rows = statement
            .query_map(
                params![
                    text,
                    origin,
                    family,
                    source,
                    outcome,
                    query.recent_only,
                    query.diagnostics_only,
                    limit as i64,
                    query.offset as i64
                ],
                |r| Ok((r.get::<_, String>(0)?, r.get::<_, Option<i64>>(1)?)),
            )
            .map_err(db_error)?;
        let mut entries = Vec::new();
        for row in rows {
            let (payload, recent) = row.map_err(db_error)?;
            let mut entry: LibraryEntry = serde_json::from_str(&payload).map_err(|e| {
                error(
                    "index",
                    format!("Damaged index metadata: {e}. Rebuild the index."),
                )
            })?;
            entry.last_opened_at_ms = recent;
            entries.push(entry);
        }
        let mut coverage = self.scan_status();
        if coverage.phase == "notScanned" {
            if let Some(saved) = c
                .query_row("SELECT value FROM settings WHERE key='coverage'", [], |r| {
                    r.get::<_, String>(0)
                })
                .optional()
                .map_err(db_error)?
            {
                coverage = serde_json::from_str(&saved)
                    .map_err(|_| error("index", "Damaged coverage metadata; rebuild the index."))?;
                if coverage.phase == "running" {
                    coverage.phase = "interrupted".into();
                    coverage.complete = false;
                    coverage.message =
                        "The previous scan did not finish. Refresh to establish complete coverage."
                            .into();
                }
            }
        }
        let diagnostics = if coverage.complete {
            vec![]
        } else {
            vec![coverage.message.clone()]
        };
        Ok(LibraryPage {
            entries,
            total: total as usize,
            offset: query.offset,
            limit,
            has_more: query.offset.saturating_add(limit) < total as usize,
            coverage,
            diagnostics,
            storage_path: self.root.to_string_lossy().into(),
        })
    }
    pub fn import_path(
        &self,
        request_id: String,
        source: &Path,
    ) -> Result<LibraryImportResult, AppError> {
        let bytes = files::read_bounded(source, MAX_RECORD_BYTES as u64, "library-import")?;
        let name = source.file_name().unwrap_or_default().to_string_lossy();
        self.import_bytes(request_id, &name, &bytes)
    }
    pub fn import_bytes(
        &self,
        request_id: String,
        filename: &str,
        bytes: &[u8],
    ) -> Result<LibraryImportResult, AppError> {
        self.publish_bytes(request_id, filename, bytes, "managed")
    }
    /// Publish an explicitly created, independently verified session snapshot.
    /// Existing content-addressed records keep their original provenance.
    pub fn publish_created(
        &self,
        request_id: String,
        filename: &str,
        bytes: &[u8],
    ) -> Result<LibraryImportResult, AppError> {
        self.publish_bytes(request_id, filename, bytes, "created")
    }
    fn publish_bytes(
        &self,
        request_id: String,
        filename: &str,
        bytes: &[u8],
        origin: &str,
    ) -> Result<LibraryImportResult, AppError> {
        let _write = self
            .mutation
            .try_lock()
            .map_err(|_| error("busy", "A Library import or scan is already running."))?;
        self.owned()?;
        // A successful case/geometry verification has a different scope. Those
        // packets stay temporary and must never become managed experiments here.
        #[derive(Deserialize)]
        #[serde(rename_all = "camelCase")]
        struct ImportHeader {
            format: Option<String>,
            recipe_version: Option<String>,
        }
        let allowed = bytes.len() <= MAX_RECORD_BYTES
            && serde_json::from_slice::<ImportHeader>(bytes).is_ok_and(|h| {
                match h.format.as_deref() {
                    Some(
                        "essentials-exploration-v1"
                        | "essentials-actions-v1"
                        | "essentials-actions-v2"
                        | "essentials-actions-v3"
                        | "essentials-regulation-v1",
                    ) => true,
                    None => h.recipe_version.as_deref() == Some("essentials-v1"),
                    _ => false,
                }
            });
        if !allowed {
            return Ok(LibraryImportResult { request_id, cancelled: false, published: false, duplicate: false, entry_id: None, report: None,
                diagnostics: vec!["Only supported stage, exploration, action-comparison and controller recordings can be imported. Cases and geometry remain temporary views; unreadable or unsupported records stay at their original source.".into()] });
        }
        let report = verify_bytes(bytes);
        let mut result = LibraryImportResult {
            request_id,
            cancelled: false,
            published: false,
            duplicate: false,
            entry_id: None,
            report: Some(report.clone()),
            diagnostics: vec![],
        };
        if report.status != VerificationStatus::Passed {
            return Ok(result);
        }
        let sha = files::digest(bytes);
        let id = format!("sha256:{sha}");
        let path = self.root.join("records").join(format!("{sha}.json"));
        if path.try_exists().map_err(io_error)? {
            if files::read_bounded(&path, MAX_RECORD_BYTES as u64, "library-duplicate")? != bytes {
                return Err(error("identity", "An existing content-addressed file has different bytes. Nothing was overwritten; inspect Library diagnostics."));
            }
            result.duplicate = true;
        } else {
            publish_new(&path, bytes)?;
        }
        // Read back the final publication; no index row is visible before this gate.
        if files::read_bounded(&path, MAX_RECORD_BYTES as u64, "library-readback")? != bytes {
            return Err(error("readback", "Published record could not be confirmed. It remains on disk; refresh before retrying."));
        }
        result.published = true;
        result.entry_id = Some(id.clone());
        let meta_path = self.root.join("metadata").join(format!("{sha}.json"));
        if !meta_path.try_exists().map_err(io_error)? {
            let meta = LocalMetadata {
                schema: "library-local-v1".into(),
                sha256: sha.clone(),
                filename: bounded(filename),
                saved_at_ms: now(),
                origin: origin.into(),
            };
            let encoded =
                serde_json::to_vec(&meta).map_err(|e| error("metadata", e.to_string()))?;
            if let Err(e) = publish_new(&meta_path, &encoded) {
                result.diagnostics.push(format!("Record saved; local metadata was not saved: {}. Refresh can recover the record.",e.message));
            }
        }
        let mut entry = self.entry_for(&path, &sha);
        if entry.health == "unverified" {
            entry.health = "ready".into();
        }
        let indexed = (|| {
            let _g = self
                .index_gate
                .lock()
                .map_err(|_| error("index", "Index lock unavailable."))?;
            upsert(&self.connection()?, &entry)
        })();
        if let Err(e) = indexed {
            result.diagnostics.push(format!(
                "Record saved as {id}; index update failed: {}",
                e.message
            ));
        }
        Ok(result)
    }
    /// Safe only for opaque IDs, never a frontend path. Recents are recorded after
    /// verified opening; failure to update the index does not invalidate the handle.
    pub fn open(
        &self,
        records: &RecordState,
        request_id: String,
        id: &str,
    ) -> Result<OpenResult, AppError> {
        self.owned()?;
        let (filename, bytes, origin) = if let Some(catalog) = id.strip_prefix("catalog:") {
            let item = self
                .catalog()?
                .into_iter()
                .find(|item| item.id == catalog)
                .ok_or_else(|| error("identity", "Unknown bundled Library identity."))?;
            let bytes = resources::catalog_bytes(&self.resources, &item.file)?;
            (item.file, bytes, "bundled")
        } else if let Some(sha) = hash_id(id) {
            let path = self.root.join("records").join(format!("{sha}.json"));
            let bytes = files::read_bounded(&path, MAX_RECORD_BYTES as u64, "library-open")?;
            if files::digest(&bytes) != sha {
                return Err(error("identity", "Managed record content no longer matches its Library identity. Refresh for diagnostics."));
            }
            let metadata = self.local_metadata(sha).ok();
            let name = metadata
                .as_ref()
                .map(|m| m.filename.clone())
                .unwrap_or_else(|| format!("{sha}.json"));
            let origin = if metadata.as_ref().is_some_and(|m| m.origin == "created") {
                "created"
            } else {
                "managed"
            };
            (name, bytes, origin)
        } else {
            return Err(error("identity", "Unknown Library identity."));
        };
        let mut opened = records.open(request_id, filename, origin, bytes)?;
        if opened.record.is_some() {
            let recent = (|| {
                let _g = self
                    .index_gate
                    .lock()
                    .map_err(|_| error("index", "Index lock unavailable."))?;
                self.connection()?.execute("INSERT INTO recents(id,opened) VALUES(?1,?2) ON CONFLICT(id) DO UPDATE SET opened=excluded.opened",params![id,now()]).map_err(db_error)?;
                Ok::<_, AppError>(())
            })();
            if let Err(e) = recent {
                let warning = format!(
                    "Opened successfully; recent-access update failed: {}",
                    e.message
                );
                if let Some(report) = &mut opened.report {
                    report.diagnostics.push(warning.clone());
                }
                if let Some(record) = &mut opened.record {
                    record.verification.diagnostics.push(warning);
                }
            }
        }
        Ok(opened)
    }
    pub fn scan(&self, rebuild: bool) -> Result<ScanStatus, AppError> {
        let _write = self
            .mutation
            .try_lock()
            .map_err(|_| error("busy", "A Library import or scan is already running."))?;
        self.cancel.store(false, Ordering::Release);
        self.set_status(ScanStatus { phase:"running".into(),message:"Reading this application's managed Library; opening records performs numerical verification.".into(),..Default::default() });
        let result = self.scan_inner(rebuild);
        if let Err(e) = &result {
            let mut s = self.scan_status();
            s.phase = "failed".into();
            s.complete = false;
            s.message = e.message.clone();
            s.finished_at_ms = Some(now());
            self.set_status(s.clone());
            if let Ok(c) = self.connection() {
                let _ = save_coverage(&c, &s);
            }
        }
        result
    }
    fn scan_inner(&self, rebuild: bool) -> Result<ScanStatus, AppError> {
        self.owned()?;
        let mut recovery_warning = None;
        let c = {
            let _g = self
                .index_gate
                .lock()
                .map_err(|_| error("index", "Index lock unavailable."))?;
            if rebuild {
                // Preserve recents outside the rebuilt DB; scientific files are never moved.
                let recent_backup = self.connection().ok().and_then(|c| read_recents(&c).ok());
                if recent_backup.is_none() {
                    recovery_warning =
                        Some("Prior recents could not be recovered from the damaged index.");
                }
                let stamp = format!("{}-{}", now(), std::process::id());
                for suffix in ["", "-wal", "-shm"] {
                    let from = self.root.join(format!("index.sqlite3{suffix}"));
                    if from.try_exists().map_err(io_error)? {
                        if !fs::symlink_metadata(&from)
                            .map_err(io_error)?
                            .file_type()
                            .is_file()
                        {
                            return Err(error(
                                "index",
                                "Index is not a regular file; it was not moved.",
                            ));
                        }
                        let backup = self
                            .root
                            .join(format!("index-backup-{stamp}{suffix}.sqlite3"));
                        if backup.try_exists().map_err(io_error)? {
                            return Err(error(
                                "index",
                                "An index backup already exists; retry rebuild.",
                            ));
                        }
                        fs::rename(&from, backup).map_err(io_error)?;
                    }
                }
                let c = self.connection()?;
                if let Some(recents) = recent_backup {
                    for (id, time) in recents {
                        c.execute(
                            "INSERT OR REPLACE INTO recents VALUES(?1,?2)",
                            params![id, time],
                        )
                        .map_err(db_error)?;
                    }
                }
                c
            } else {
                self.connection()?
            }
        };
        save_coverage(&c, &self.scan_status())?;
        {
            let _g = self
                .index_gate
                .lock()
                .map_err(|_| error("index", "Index lock unavailable."))?;
            self.index_catalog(&c)?;
        }
        // One metadata transaction avoids a filesystem sync per row. WAL readers
        // retain the previous projection until this scan (or cancellation) commits.
        c.execute_batch("BEGIN IMMEDIATE").map_err(db_error)?;
        let mut seen = HashSet::new();
        let mut seen_ids = HashSet::new();
        for item in fs::read_dir(self.root.join("records")).map_err(io_error)? {
            if self.cancel.load(Ordering::Acquire) {
                break;
            }
            let item = item.map_err(io_error)?;
            let path = item.path();
            let file_identity = diagnostic_file_id(&item.file_name());
            let filename = item.file_name().to_string_lossy().into_owned();
            let mut status = self.scan_status();
            status.examined += 1;
            self.set_status(status);
            let stem = path
                .file_stem()
                .and_then(|n| n.to_str())
                .unwrap_or_default();
            let candidate = format!("sha256:{stem}");
            let entry = if path.extension().and_then(|n| n.to_str()) == Some("json")
                && hash_id(&candidate).is_some()
            {
                seen.insert(stem.to_owned());
                self.entry_for(&path, stem)
            } else {
                let mut e = empty_entry(file_identity, filename, "managed");
                e.health = "damaged".into();
                e.diagnostic=Some("Unexpected file in owned records directory; not treated as an experiment or followed.".into());
                e
            };
            seen_ids.insert(entry.id.clone());
            upsert(&c, &entry)?;
            self.count_entry(&entry);
        }
        // Metadata survives removal of a record, allowing missing entries to remain
        // visible after a rebuild. Do not follow paths embedded in that metadata.
        if !self.cancel.load(Ordering::Acquire) {
            for item in fs::read_dir(self.root.join("metadata")).map_err(io_error)? {
                if self.cancel.load(Ordering::Acquire) {
                    break;
                }
                let path = item.map_err(io_error)?.path();
                let stem = path
                    .file_stem()
                    .and_then(|s| s.to_str())
                    .unwrap_or_default();
                if path.extension().and_then(|s| s.to_str()) != Some("json")
                    || hash_id(&format!("sha256:{stem}")).is_none()
                    || seen.contains(stem)
                {
                    continue;
                }
                let mut e =
                    empty_entry(format!("sha256:{stem}"), format!("{stem}.json"), "managed");
                e.sha256 = Some(stem.into());
                e.health = "missing".into();
                e.diagnostic =
                    Some("Managed recording is missing; its local import metadata remains.".into());
                if let Ok(m) = self.local_metadata(stem) {
                    e.filename = m.filename;
                    e.saved_at_ms = Some(m.saved_at_ms);
                    e.origin = m.origin;
                }
                seen_ids.insert(e.id.clone());
                upsert(&c, &e)?;
                self.count_entry(&e);
            }
        }
        if !self.cancel.load(Ordering::Acquire) {
            let mut q = c
                .prepare("SELECT payload FROM entries WHERE origin IN ('managed','created')")
                .map_err(db_error)?;
            let rows = q
                .query_map([], |r| r.get::<_, String>(0))
                .map_err(db_error)?;
            let mut missing = Vec::new();
            for row in rows {
                let mut entry: LibraryEntry = serde_json::from_str(&row.map_err(db_error)?)
                    .map_err(|e| error("index", e.to_string()))?;
                if !seen_ids.contains(&entry.id) {
                    entry.health = "missing".into();
                    entry.diagnostic = Some(
                        "Previously indexed file is no longer present in this managed Library."
                            .into(),
                    );
                    missing.push(entry);
                }
            }
            drop(q);
            for entry in missing {
                upsert(&c, &entry)?;
                self.count_entry(&entry);
            }
        }
        c.execute_batch("COMMIT").map_err(db_error)?;
        let mut s = self.scan_status();
        s.complete = !self.cancel.load(Ordering::Acquire);
        s.phase = if s.complete {
            "complete"
        } else {
            "interrupted"
        }
        .into();
        s.message = if s.complete {
            format!("Scanned all {} managed directory entries; {} indexed rows, {} diagnostics. Numerical verification runs when opening.",s.examined,s.indexed,s.diagnostic_count)
        } else {
            "Scan interrupted. Indexed results are partial; refresh to complete coverage.".into()
        };
        if let Some(warning) = recovery_warning {
            s.message.push(' ');
            s.message.push_str(warning);
        }
        s.finished_at_ms = Some(now());
        save_coverage(&c, &s)?;
        self.set_status(s.clone());
        Ok(s)
    }
    fn count_entry(&self, e: &LibraryEntry) {
        let mut s = self.scan_status();
        s.indexed += 1;
        if !matches!(e.health.as_str(), "ready" | "unverified") {
            s.diagnostic_count += 1;
        }
        self.set_status(s);
    }
    fn local_metadata(&self, sha: &str) -> Result<LocalMetadata, AppError> {
        let data = files::read_bounded(
            &self.root.join("metadata").join(format!("{sha}.json")),
            META_LIMIT,
            "library-metadata",
        )?;
        let m: LocalMetadata =
            serde_json::from_slice(&data).map_err(|e| error("metadata", e.to_string()))?;
        if m.schema != "library-local-v1"
            || m.sha256 != sha
            || m.saved_at_ms < 0
            || !matches!(m.origin.as_str(), "managed" | "created")
        {
            return Err(error("metadata", "Local metadata identity is invalid."));
        }
        Ok(m)
    }
    fn entry_for(&self, path: &Path, sha: &str) -> LibraryEntry {
        let mut e = empty_entry(format!("sha256:{sha}"), format!("{sha}.json"), "managed");
        e.sha256 = Some(sha.into());
        match self.local_metadata(sha) {
            Ok(m) => {
                e.filename = m.filename;
                e.saved_at_ms = Some(m.saved_at_ms);
                e.origin = m.origin;
            }
            Err(_) => {
                e.health = "metadataIssue".into();
                e.diagnostic=Some("Local import metadata is missing or damaged; original bytes remain available. Local save time is unknown.".into());
            }
        }
        match files::read_bounded(path, MAX_RECORD_BYTES as u64, "library-scan") {
            Ok(bytes) => {
                if files::digest(&bytes) != sha {
                    e.health = "damaged".into();
                    e.diagnostic =
                        Some("File bytes do not match their content-addressed identity.".into());
                } else {
                    match metadata(&bytes, &e.filename) {
                        Ok(m) => apply_metadata(&mut e, m),
                        Err(message) => {
                            e.health = "damaged".into();
                            e.diagnostic = Some(message);
                        }
                    }
                }
            }
            Err(err) => {
                e.health = "unreadable".into();
                e.diagnostic = Some(err.message);
            }
        }
        e
    }
    fn catalog(&self) -> Result<Vec<CatalogItem>, AppError> {
        let bytes = resources::catalog_bytes(&self.resources, "examples-index.json")?;
        let mut items: Vec<CatalogItem> =
            serde_json::from_slice(&bytes).map_err(|e| error("catalog", e.to_string()))?;
        let mut seen = HashSet::new();
        for item in &items {
            if item.id.is_empty()
                || item.id.len() > 128
                || !seen.insert(item.id.clone())
                || Path::new(&item.file).file_name().and_then(|p| p.to_str()) != Some(&item.file)
                || item.file.contains(['/', '\\'])
            {
                return Err(error("catalog", "Bundled catalog identities are invalid."));
            }
        }
        let rank = |group: Option<&str>| match group {
            Some("guided") => 0,
            Some("model") => 1,
            Some("comparison") => 2,
            Some("preparation") => 3,
            _ => 4,
        };
        items.sort_by(|a, b| {
            (rank(a.group.as_deref()), a.order.unwrap_or(0), &a.id).cmp(&(
                rank(b.group.as_deref()),
                b.order.unwrap_or(0),
                &b.id,
            ))
        });
        Ok(items)
    }
    fn catalog_identity() -> String {
        format!(
            "metadata-v2:{}:{}",
            env!("CARGO_PKG_VERSION"),
            resources::index_identity()
        )
    }
    fn index_catalog(&self, c: &Connection) -> Result<(), AppError> {
        let items = self.catalog()?;
        // Publish the bundled projection as one transaction on build/resource
        // changes. Managed bytes and separately stored recents stay untouched.
        let transaction = c.unchecked_transaction().map_err(db_error)?;
        transaction
            .execute("DELETE FROM entries WHERE origin='bundled'", [])
            .map_err(db_error)?;
        for (order, item) in items.into_iter().enumerate() {
            if self.cancel.load(Ordering::Acquire) && self.scan_status().phase == "running" {
                return Ok(()); // Drop rolls back a partial catalog, including its build marker.
            }
            let mut e = empty_entry(format!("catalog:{}", item.id), item.file.clone(), "bundled");
            e.title = item.title.clone();
            e.catalog_order = Some(order);
            match resources::catalog_bytes(&self.resources, &item.file) {
                Ok(bytes) => {
                    e.sha256 = Some(files::digest(&bytes));
                    match metadata(&bytes, &e.filename) {
                        Ok(m) => {
                            apply_metadata(&mut e, m);
                            e.title = item.title;
                        }
                        Err(msg) => {
                            e.health = "damaged".into();
                            e.diagnostic = Some(msg);
                        }
                    }
                }
                Err(err) => {
                    e.health = if err.category == "resource" {
                        "notBundled"
                    } else {
                        "unreadable"
                    }
                    .into();
                    e.diagnostic = Some(if err.category == "resource" {
                        "This authored catalog entry is not included in this build. It has no verifier or resource coverage here.".into()
                    } else {
                        err.message
                    });
                }
            }
            upsert(&transaction, &e)?;
        }
        transaction.execute("INSERT INTO settings(key,value) VALUES('catalog-build',?1) ON CONFLICT(key) DO UPDATE SET value=excluded.value", [Self::catalog_identity()]).map_err(db_error)?;
        transaction.commit().map_err(db_error)?;
        Ok(())
    }
}

fn filter(value: Option<String>, allowed: &[&str]) -> Result<String, AppError> {
    let value = value.unwrap_or_default();
    if value.is_empty() || value == "all" {
        Ok(String::new())
    } else if allowed.contains(&value.as_str()) {
        Ok(value)
    } else {
        Err(error("query", "Unknown Library filter."))
    }
}
fn empty_entry(id: String, filename: String, origin: &str) -> LibraryEntry {
    LibraryEntry {
        id,
        title: filename.clone(),
        filename,
        origin: origin.into(),
        family: "unknown".into(),
        format: "unknown".into(),
        stage: None,
        backend: "unknown".into(),
        source: "unknown".into(),
        model: "unknown".into(),
        seed: None,
        embedded_id: None,
        outcome: "unknown".into(),
        health: "unverified".into(),
        diagnostic: None,
        sha256: None,
        saved_at_ms: None,
        last_opened_at_ms: None,
        catalog_order: None,
    }
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct Header {
    format: Option<String>,
    recipe_version: Option<String>,
    id: Option<serde_json::Value>,
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct Specification {
    mode: Option<String>,
    stage: Option<u8>,
    seed: Option<u64>,
    language: Option<Language>,
}
#[derive(Deserialize)]
struct StageSpecification {
    stage: Option<u8>,
    seed: Option<u64>,
    language: Option<Language>,
}
#[derive(Deserialize)]
struct Language {
    backend: Option<String>,
    model: Option<String>,
}
#[derive(Deserialize)]
struct StageTurnHeader {
    backend: Option<String>,
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct ActionTurnHeader {
    request_started: Option<bool>,
}
#[derive(Deserialize)]
struct ArmHeader {
    #[serde(default)]
    actions: Vec<ActionTurnHeader>,
}
#[derive(Deserialize)]
struct StageHeader {
    specification: Option<StageSpecification>,
    status: Option<String>,
    #[serde(default)]
    turns: Vec<StageTurnHeader>,
}
#[derive(Deserialize)]
struct ActionHeader {
    specification: Option<Specification>,
    status: Option<String>,
    left: Option<ArmHeader>,
    right: Option<ArmHeader>,
}
#[derive(Deserialize)]
struct ExplorationHeader {
    seed: Option<u64>,
}
#[derive(Deserialize)]
struct RegulationHeader {
    specification: RegulationMetadata,
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct RegulationMetadata {
    field_seed: Option<u64>,
}
fn decode_header<T: serde::de::DeserializeOwned>(bytes: &[u8]) -> Result<T, String> {
    serde_json::from_slice(bytes).map_err(|e| format!("Record header cannot be read: {e}"))
}
struct Metadata {
    source: String,
    format: String,
    family: String,
    stage: Option<String>,
    seed: Option<String>,
    backend: String,
    model: String,
    outcome: String,
    embedded_id: Option<String>,
}
fn metadata(bytes: &[u8], _filename: &str) -> Result<Metadata, String> {
    let h: Header = decode_header(bytes)?;
    let format = h
        .format
        .clone()
        .or(h.recipe_version.clone())
        .unwrap_or_else(|| "unknown".into());
    let family = match (h.format.as_deref(), h.recipe_version.as_deref()) {
        (None, Some("essentials-v1")) => "stage",
        (Some("essentials-exploration-v1"), _) => "exploration",
        (Some("essentials-regulation-v1"), _) => "regulation",
        (Some("essentials-actions-v1" | "essentials-actions-v2" | "essentials-actions-v3"), _) => {
            "actions"
        }
        _ => "unknown",
    };
    // Project only fields belonging to the dispatched family. Unknown extras
    // preserved in the original bytes cannot promote or break index metadata.
    let (spec, raw_seed, status, turns, started) = match family {
        "stage" => {
            let v: StageHeader = decode_header(bytes)?;
            (
                v.specification.map(|s| Specification {
                    mode: None,
                    stage: s.stage,
                    seed: s.seed,
                    language: s.language,
                }),
                None,
                v.status,
                v.turns,
                false,
            )
        }
        "actions" => {
            let v: ActionHeader = decode_header(bytes)?;
            let started = v
                .left
                .iter()
                .chain(v.right.iter())
                .flat_map(|arm| &arm.actions)
                .any(|a| a.request_started == Some(true));
            (v.specification, None, v.status, vec![], started)
        }
        "exploration" => {
            let v: ExplorationHeader = decode_header(bytes)?;
            (None, v.seed, None, vec![], false)
        }
        "regulation" => {
            let v: RegulationHeader = decode_header(bytes)?;
            (
                None,
                Some(v.specification.field_seed.unwrap_or(98)),
                Some("snapshot".into()),
                vec![],
                false,
            )
        }
        _ => (None, None, None, vec![], false),
    };
    let seed = spec
        .as_ref()
        .and_then(|s| s.seed)
        .or(raw_seed)
        .or(if family == "stage" || family == "actions" {
            Some(20_260_909)
        } else {
            None
        })
        .map(|v| v.to_string());
    let stage = spec
        .as_ref()
        .and_then(|s| s.stage)
        .or(match family {
            "stage" => Some(1),
            "actions" => Some(5),
            _ => None,
        })
        .map(|s| s.to_string());
    let mode = spec
        .as_ref()
        .and_then(|s| s.mode.as_deref())
        .unwrap_or("fixedReplay");
    let fixed_replay = family == "actions" && mode == "fixedReplay";
    let language = spec.and_then(|s| s.language);
    let backend = language
        .as_ref()
        .and_then(|l| l.backend.clone())
        .unwrap_or_else(|| {
            if family == "stage" || family == "actions" {
                "scripted"
            } else {
                "unknown"
            }
            .into()
        });
    let model = language
        .and_then(|l| l.model)
        .map(|s| bounded(&s))
        .unwrap_or_else(|| "unknown".into());
    let embedded_id = h.id.and_then(|v| match v {
        serde_json::Value::String(s) => Some(bounded(&s)),
        serde_json::Value::Number(n) => Some(n.to_string()),
        _ => None,
    });
    // Metadata records a declared route, not an authenticated provider call.
    // A fixed tape takes precedence over an unused configured model backend.
    let source = if family == "regulation" {
        "numerical"
    } else if fixed_replay {
        "fixedReplay"
    } else if family == "actions" {
        match (started, backend.as_str()) {
            (true, "ollama") => "model",
            (true, "scripted") => "scripted",
            _ => "unknown",
        }
    } else if family == "stage" && !turns.is_empty() {
        if turns.iter().all(|t| t.backend.as_deref() == Some("ollama")) {
            "model"
        } else if turns
            .iter()
            .all(|t| t.backend.as_deref() == Some("scripted"))
        {
            "scripted"
        } else {
            "unknown"
        }
    } else {
        "unknown"
    };
    Ok(Metadata {
        source: source.into(),
        format: bounded(&format),
        family: family.into(),
        stage,
        seed,
        backend: bounded(&backend),
        model,
        outcome: status
            .map(|s| bounded(&s))
            .unwrap_or_else(|| "snapshot".into()),
        embedded_id,
    })
}
fn apply_metadata(e: &mut LibraryEntry, m: Metadata) {
    e.family = m.family;
    e.format = m.format;
    e.stage = m.stage;
    e.seed = m.seed;
    e.backend = m.backend;
    e.source = m.source;
    e.model = m.model;
    e.outcome = m.outcome;
    e.embedded_id = m.embedded_id;
    if e.family == "unknown" {
        e.health = "unsupported".into();
        e.diagnostic=Some("This file's format is not supported by the current verifier. Original bytes remain intact.".into());
    } else {
        e.title = match e.family.as_str() {
            "stage" => format!(
                "Stage {} experiment",
                e.stage.as_deref().unwrap_or("unknown")
            ),
            "actions" => format!(
                "Action comparison · component {}",
                e.stage.as_deref().unwrap_or("unknown")
            ),
            "regulation" => "Controller mechanism · sensory fields".into(),
            _ => "Reservoir exploration".into(),
        };
    }
}
fn upsert(c: &Connection, e: &LibraryEntry) -> Result<(), AppError> {
    let search = format!(
        "{} {} {} {} {} {} {} {} {} {}",
        e.title,
        e.filename,
        e.family,
        e.format,
        e.stage.as_deref().unwrap_or(""),
        e.backend,
        e.model,
        e.seed.as_deref().unwrap_or(""),
        e.id,
        e.embedded_id.as_deref().unwrap_or("")
    )
    .to_lowercase();
    let json = serde_json::to_string(e).map_err(|x| error("index", x.to_string()))?;
    c.execute("INSERT INTO entries VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10) ON CONFLICT(id) DO UPDATE SET origin=excluded.origin,family=excluded.family,source=excluded.source,outcome=excluded.outcome,health=excluded.health,search=excluded.search,saved=excluded.saved,ordinal=excluded.ordinal,payload=excluded.payload",params![e.id,e.origin,e.family,e.source,e.outcome,e.health,search,e.saved_at_ms.unwrap_or(0),e.catalog_order.unwrap_or(0) as i64,json]).map_err(db_error)?;
    Ok(())
}
fn save_coverage(c: &Connection, s: &ScanStatus) -> Result<(), AppError> {
    let json = serde_json::to_string(s).map_err(|e| error("index", e.to_string()))?;
    c.execute("INSERT INTO settings VALUES('coverage',?1) ON CONFLICT(key) DO UPDATE SET value=excluded.value",params![json]).map_err(db_error)?;
    Ok(())
}
fn read_recents(c: &Connection) -> rusqlite::Result<Vec<(String, i64)>> {
    let mut q = c.prepare("SELECT id,opened FROM recents")?;
    let rows = q.query_map([], |r| Ok((r.get(0)?, r.get(1)?)))?;
    rows.collect()
}
fn publish_new(path: &Path, bytes: &[u8]) -> Result<(), AppError> {
    let parent = path
        .parent()
        .ok_or_else(|| error("storage", "Missing publication directory."))?;
    let mut temp = tempfile::NamedTempFile::new_in(parent).map_err(io_error)?;
    temp.write_all(bytes)
        .and_then(|_| temp.as_file().sync_all())
        .map_err(io_error)?;
    if files::read_bounded(
        temp.path(),
        MAX_RECORD_BYTES as u64,
        "library-staged-readback",
    )? != bytes
    {
        return Err(error("readback", "Staged bytes did not read back exactly."));
    }
    temp.persist_noclobber(path)
        .map_err(|e| error("publication", e.to_string()))?;
    #[cfg(unix)]
    fs::File::open(parent)
        .and_then(|f| f.sync_all())
        .map_err(io_error)?;
    Ok(())
}

#[cfg(test)]
#[path = "library_tests.rs"]
mod tests;
