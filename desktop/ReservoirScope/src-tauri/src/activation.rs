//! Owned, serial activation worker and immutable research evidence. No Being
//! endpoints, models, or stores are contacted by this module.
use crate::files::{self, AppError};
use reservoir_core::activation::{self as core, Arm, Event, Record, Specification};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    fs,
    io::{BufRead, BufReader, Read, Write},
    path::{Path, PathBuf},
    process::{Child, ChildStdin, Command, Stdio},
    sync::{
        atomic::{AtomicBool, Ordering},
        mpsc::{self, Receiver},
        Arc, Mutex,
    },
    thread::{self, JoinHandle},
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};

type Result<T> = std::result::Result<T, AppError>;
const MAX_BYTES: u64 = 256 * 1024 * 1024;
const RESPONSE_LIMIT: u64 = 8 * 1024 * 1024;
fn err(category: &str, message: impl Into<String>) -> AppError {
    AppError::new("activation", category, message)
}
fn io(e: impl std::fmt::Display) -> AppError {
    err("evidence", e.to_string())
}
fn now() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos()
}
fn encode<T: Serialize>(v: &T) -> Result<Vec<u8>> {
    serde_json::to_vec_pretty(v).map_err(io)
}
fn decode<T: serde::de::DeserializeOwned>(p: &Path) -> Result<T> {
    serde_json::from_slice(&files::read_bounded(p, MAX_BYTES, "activation")?).map_err(io)
}
fn publish(p: &Path, bytes: &[u8]) -> Result<()> {
    publish_limit(p, bytes, MAX_BYTES - 32 * 1024 * 1024)
}
fn publish_limit(p: &Path, bytes: &[u8], limit: u64) -> Result<()> {
    if p.exists() {
        if files::read_bounded(p, MAX_BYTES, "activation")? == bytes {
            return Ok(());
        }
        return Err(err(
            "collision",
            "Immutable evidence already exists with different bytes",
        ));
    }
    if p.parent().and_then(Path::file_name).is_some_and(|n| {
        let n = n.to_string_lossy();
        n.starts_with("activation-") || n.starts_with(".activation-import-")
    }) {
        let mut used = 0u64;
        for entry in fs::read_dir(p.parent().unwrap()).map_err(io)? {
            let entry = entry.map_err(io)?;
            let metadata = entry.metadata().map_err(io)?;
            used = used.saturating_add(metadata.len());
        }
        if used.saturating_add(bytes.len() as u64) > limit {
            return Err(err("storage","Activation evidence reached its 256 MiB allowance; no further model operation is admitted"));
        }
    }
    let mut f = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(p)
        .map_err(io)?;
    f.write_all(bytes).map_err(io)?;
    f.sync_all().map_err(io)?;
    fs::File::open(p.parent().unwrap())
        .and_then(|f| f.sync_all())
        .map_err(io)
}
fn ordinary_dir(p: &Path) -> Result<()> {
    let m = fs::symlink_metadata(p).map_err(io)?;
    if !m.is_dir() || m.file_type().is_symlink() {
        return Err(err(
            "path",
            "Evidence directory must be an ordinary directory",
        ));
    }
    Ok(())
}
fn id_ok(s: &str) -> bool {
    !s.is_empty() && s.len() <= 100 && s.bytes().all(|c| c.is_ascii_alphanumeric() || c == b'-')
}
fn worker_identity(path: &Path) -> Result<String> {
    let mut items = BTreeMap::new();
    items.insert(
        "entrypoint".to_string(),
        core::digest(&files::read_bounded(path, 4 * 1024 * 1024, "activation")?),
    );
    if path.file_name().is_some_and(|n| n == "__main__.py") {
        for entry in fs::read_dir(path.parent().unwrap()).map_err(io)? {
            let entry = entry.map_err(io)?;
            if entry.path().extension().is_some_and(|e| e == "py") {
                items.insert(
                    entry.file_name().to_string_lossy().into_owned(),
                    core::digest(&files::read_bounded(
                        &entry.path(),
                        4 * 1024 * 1024,
                        "activation",
                    )?),
                );
            }
        }
    }
    Ok(core::digest(&encode(&items)?))
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Config {
    pub python_path: String,
    pub worker_path: String,
    pub model_path: String,
    pub arm: Arm,
    pub seed: u64,
    pub observations: Vec<String>,
    pub steps_between: usize,
    pub journal_every: usize,
    pub max_journal_tokens: u32,
    pub gain: f64,
}
impl Config {
    fn specification(&self) -> Specification {
        Specification {
            arm: self.arm,
            seed: self.seed,
            observations: self.observations.clone(),
            steps_between: self.steps_between,
            journal_every: self.journal_every,
            gain: self.gain,
        }
    }
    fn validate(&self) -> Result<()> {
        self.specification().validate().map_err(io)?;
        if self.max_journal_tokens != 1024 {
            return Err(err(
                "configuration",
                "First-tranche journals use the fixed 1024-token allowance",
            ));
        }
        for p in [&self.python_path, &self.worker_path, &self.model_path] {
            if !Path::new(p).is_absolute() {
                return Err(err(
                    "configuration",
                    "Select absolute local Python, worker, and model paths",
                ));
            }
        }
        Ok(())
    }
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Annotation {
    pub excerpt: String,
    pub interpretation: String,
    pub alternative: String,
    pub source_event_ids: Vec<String>,
    pub journal_id: Option<String>,
}
#[derive(Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct Manifest {
    format: String,
    session_id: String,
    revision: u64,
    status: String,
    config: Config,
    record_file: String,
    record_sha256: String,
    worker_sha256: String,
    diagnostic: Option<String>,
    active_operation: Option<String>,
    model_manifest_sha256: Option<String>,
    calibration_sha256: Option<String>,
    calibration_file_sha256: Option<String>,
    model_manifest_file_sha256: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    cohort: Option<CohortMembership>,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct JournalView {
    id: String,
    text: String,
    observed_step: u64,
    first_applied_step: Option<u64>,
    sha256: String,
    status: String,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct EventView {
    id: String,
    kind: String,
    step: u64,
    detail: String,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Snapshot {
    pub session_id: String,
    pub revision: u64,
    pub status: String,
    pub config: Config,
    pub step: u64,
    pub observation_index: usize,
    pub journal_count: usize,
    pub journals: Vec<JournalView>,
    pub events: Vec<EventView>,
    pub diagnostic: Option<String>,
    pub active_operation: Option<String>,
    pub directory: String,
    pub can_start: bool,
    pub annotations: Vec<Annotation>,
    pub calibration_sha256: Option<String>,
    pub model_manifest_sha256: Option<String>,
}
#[derive(Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct Export {
    format: String,
    files: BTreeMap<String, String>,
}

#[derive(Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct CohortMembership {
    plan_sha256: String,
    index: usize,
    origin_session_id: String,
    initialization_sha256: Option<String>,
    first_operation_sequence: Option<u64>,
    operation_boundary_sha256: Option<String>,
}
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct CohortPlan {
    format: String,
    cohort_id: String,
    configs: Vec<Config>,
    session_ids: Vec<String>,
    worker_sha256: String,
    calibration_source_sha256: String,
    lifetime_seconds: f64,
    request_timeout_seconds: u64,
}
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct SharedInitialization {
    format: String,
    cohort_id: String,
    plan_sha256: String,
    worker_pid: u32,
    sequence: u64,
    request_sha256: String,
    response_sha256: String,
}
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct OperationBoundary {
    format: String,
    initialization_sha256: String,
    origin_session_id: String,
    index: usize,
    first_sequence: u64,
    last_sequence: u64,
    record_sha256: String,
    status: String,
}
struct CohortRuntime<'a> {
    deadline: Instant,
    root: &'a Path,
    resident_pressure: fn() -> Result<Value>,
}
impl CohortRuntime<'_> {
    fn guard(&self, phase: &str, cancel: &AtomicBool) -> Result<()> {
        operation_timeout(Some(self.deadline))?;
        if cancel.load(Ordering::SeqCst) {
            return Err(err("cancelled", "Activation cohort was cancelled"));
        }
        let outcome = (self.resident_pressure)().and_then(|value| {
            if phase == "initialize" && value["pressure"] != json!(1) {
                return Err(err("admission", "Pressure changed before the new model load; initialization requires pressure 1"));
            }
            Ok(value)
        });
        let timestamp = now();
        let receipt = match &outcome {
            Ok(value) => {
                json!({"phase":phase,"observedUnixNanos":timestamp.to_string(),"resource":value})
            }
            Err(e) => {
                json!({"phase":phase,"observedUnixNanos":timestamp.to_string(),"allowed":false,"category":e.category,"message":e.message})
            }
        };
        publish(
            &self.root.join(format!("resident-guard-{timestamp}.json")),
            &encode(&receipt)?,
        )?;
        outcome?;
        operation_timeout(Some(self.deadline))?;
        Ok(())
    }
}
fn operation_timeout(deadline: Option<Instant>) -> Result<Duration> {
    let maximum = Duration::from_secs(180);
    match deadline {
        Some(deadline) => deadline
            .checked_duration_since(Instant::now())
            .filter(|remaining| !remaining.is_zero())
            .map(|remaining| remaining.min(maximum))
            .ok_or_else(|| {
                err(
                    "timeout",
                    "Activation cohort exhausted its total lifetime; no next operation is admitted",
                )
            }),
        None => Ok(maximum),
    }
}
fn validate_cohort(configs: &[Config]) -> Result<()> {
    if configs.len() != 3 {
        return Err(err(
            "configuration",
            "An activation cohort requires exactly three distinct arms",
        ));
    }
    for (index, config) in configs.iter().enumerate() {
        config.validate()?;
        let mut normalized = config.clone();
        normalized.arm = configs[0].arm;
        if normalized != configs[0] || configs[..index].iter().any(|c| c.arm == config.arm) {
            return Err(err(
                "configuration",
                "Cohort arms must differ only in arm and contain each arm exactly once",
            ));
        }
    }
    Ok(())
}

/// The cohort is a new execution contract. Existing sessions never enter this
/// path, and borrowed sessions cannot later create a replacement worker.
pub fn run_cohort(
    configs: Vec<Config>,
    root: &Path,
    calibration: &Path,
    cancel: &AtomicBool,
) -> Result<Value> {
    run_cohort_bounded(
        configs,
        root,
        calibration,
        cancel,
        Duration::from_secs(900),
        resident_pressure,
    )
}
fn run_cohort_bounded(
    configs: Vec<Config>,
    root: &Path,
    calibration: &Path,
    cancel: &AtomicBool,
    lifetime: Duration,
    guard: fn() -> Result<Value>,
) -> Result<Value> {
    validate_cohort(&configs)?;
    let source = files::read_bounded(calibration, RESPONSE_LIMIT, "activation")?;
    let calibration_value: Value = serde_json::from_slice(&source).map_err(io)?;
    if !calibration_value["sha256"].is_string()
        || !calibration_value["modelManifestSha256"].is_string()
    {
        return Err(err(
            "calibration",
            "Cohort requires an existing identified calibration",
        ));
    }
    // create_dir is deliberately exclusive: an older stopped cohort is never
    // resumed, overwritten, or interpreted as preparation for this attempt.
    fs::create_dir(root).map_err(io)?;
    let started_at = Instant::now();
    let runtime = CohortRuntime {
        deadline: started_at + lifetime,
        root,
        resident_pressure: guard,
    };
    let state = ActivationState::new(root.to_owned(), PathBuf::from(&configs[0].worker_path));
    let mut sessions = Vec::new();
    for config in &configs {
        let initial = state.create(config.clone())?;
        let path = PathBuf::from(&initial.directory);
        let (manifest, record) = load(&path)?;
        sessions.push((path, manifest, record));
    }
    let plan = CohortPlan {
        format: "activation-cohort-plan-v1".into(),
        cohort_id: format!("cohort-{}", now()),
        configs,
        session_ids: sessions
            .iter()
            .map(|(_, m, _)| m.session_id.clone())
            .collect(),
        worker_sha256: sessions[0].1.worker_sha256.clone(),
        calibration_source_sha256: core::digest(&source),
        lifetime_seconds: lifetime.as_secs_f64(),
        request_timeout_seconds: 180,
    };
    let plan_bytes = encode(&plan)?;
    let plan_sha256 = core::digest(&plan_bytes);
    publish(&root.join("cohort-plan.json"), &plan_bytes)?;
    publish(&root.join("calibration-source.json"), &source)?;
    for (index, (path, manifest, record)) in sessions.iter_mut().enumerate() {
        publish(&path.join("cohort-plan.json"), &plan_bytes)?;
        publish(&path.join("cohort-calibration-source.json"), &source)?;
        manifest.format = "activation-cohort-session-v1".into();
        manifest.status = "paused".into();
        manifest.cohort = Some(CohortMembership {
            plan_sha256: plan_sha256.clone(),
            index,
            origin_session_id: manifest.session_id.clone(),
            initialization_sha256: None,
            first_operation_sequence: None,
            operation_boundary_sha256: None,
        });
        save(path, manifest, record)?;
    }
    let mut worker = None;
    let mut models_loaded = 0;
    let mut worker_starts = 0;
    let mut active_index = 0;
    let mut outcome = (|| -> Result<()> {
        operation_timeout(Some(runtime.deadline))?;
        if cancel.load(Ordering::SeqCst) {
            return Err(err(
                "cancelled",
                "Activation cohort was cancelled before admission",
            ));
        }
        if worker_identity(Path::new(&plan.configs[0].worker_path))? != plan.worker_sha256 {
            return Err(err(
                "identity",
                "Worker sources changed before cohort admission",
            ));
        }
        #[cfg(not(test))]
        {
            let admission = admit();
            let receipt = match &admission {
                Ok(value) => value.clone(),
                Err(e) => json!({"admitted":false,"category":e.category,"message":e.message}),
            };
            publish(&root.join("admission.json"), &encode(&receipt)?)?;
            admission?;
        }
        runtime.guard("initialize", cancel)?;
        let mut owned = Worker::spawn(&plan.configs[0])?;
        worker_starts = 1;
        owned.evidence_path = Some(root.join("worker-stderr.txt"));
        owned.protocol_prefix = Some(root.join("shared-worker"));
        worker = Some(owned);
        let owned = worker.as_mut().unwrap();
        let initialized = owned.call(
            "initialize",
            json!({"modelPath":plan.configs[0].model_path,"existingCalibration":calibration_value}),
            cancel,
            operation_timeout(Some(runtime.deadline))?,
        )?;
        models_loaded = 1;
        if initialized["calibration"] != calibration_value {
            return Err(err(
                "identity",
                "Shared initialization changed the supplied frozen calibration",
            ));
        }
        let request_bytes = files::read_bounded(
            &root.join("shared-worker-1-request.json"),
            RESPONSE_LIMIT,
            "activation",
        )?;
        let response_bytes = files::read_bounded(
            &root.join("shared-worker-1-response.json"),
            RESPONSE_LIMIT,
            "activation",
        )?;
        let envelope: Value = serde_json::from_slice(&response_bytes).map_err(io)?;
        if envelope["protocolVersion"] != "reservoir-activation/1"
            || !envelope["workerIdentity"].is_object()
            || envelope["workerIdentity"]["modelManifestSha256"]
                != initialized["manifest"]["sha256"]
        {
            return Err(err(
                "identity",
                "Shared initialization omitted the pinned worker envelope identity",
            ));
        }
        owned.frozen_envelope = Some(
            json!({"protocolVersion":envelope["protocolVersion"],"workerIdentity":envelope["workerIdentity"]}),
        );
        let initialization = SharedInitialization {
            format: "activation-shared-initialization-v1".into(),
            cohort_id: plan.cohort_id.clone(),
            plan_sha256: plan_sha256.clone(),
            worker_pid: owned.child.id(),
            sequence: 1,
            request_sha256: core::digest(&request_bytes),
            response_sha256: core::digest(&response_bytes),
        };
        let initialization_bytes = encode(&initialization)?;
        let initialization_sha256 = core::digest(&initialization_bytes);
        publish(
            &root.join("shared-initialization.json"),
            &initialization_bytes,
        )?;
        for (path, manifest, record) in &mut sessions {
            publish(
                &path.join("shared-initialization.json"),
                &initialization_bytes,
            )?;
            publish(&path.join("shared-initialize-request.json"), &request_bytes)?;
            publish(
                &path.join("shared-initialize-response.json"),
                &response_bytes,
            )?;
            retain_initialization(path, manifest, &initialized)?;
            manifest.cohort.as_mut().unwrap().initialization_sha256 =
                Some(initialization_sha256.clone());
            save(path, manifest, record)?;
        }
        for (index, (path, manifest, record)) in sessions.iter_mut().enumerate() {
            active_index = index;
            runtime.guard(&format!("arm-boundary-{index}"), cancel)?;
            manifest.status = "running".into();
            manifest.cohort.as_mut().unwrap().first_operation_sequence = Some(owned.sequence + 1);
            save(path, manifest, record)?;
            owned.protocol_prefix = Some(path.join("cohort-protocol"));
            let operation = ActivationState::execute_operations(
                path,
                manifest,
                record,
                owned,
                cancel,
                Some(&runtime),
            );
            let operation = operation.and_then(|()| {
                if record.complete() {
                    Ok(())
                } else {
                    Err(err(
                        "cancelled",
                        "Cohort stopped at an operation boundary; no later arm was started",
                    ))
                }
            });
            if let Err(e) = &operation {
                retain_failure(path, manifest, record, &e.message)?;
            }
            let boundary = OperationBoundary {
                format: "activation-cohort-boundary-v1".into(),
                initialization_sha256: initialization_sha256.clone(),
                origin_session_id: manifest.cohort.as_ref().unwrap().origin_session_id.clone(),
                index,
                first_sequence: manifest
                    .cohort
                    .as_ref()
                    .unwrap()
                    .first_operation_sequence
                    .unwrap(),
                last_sequence: owned.sequence,
                record_sha256: manifest.record_sha256.clone(),
                status: manifest.status.clone(),
            };
            let boundary_bytes = encode(&boundary)?;
            publish(
                &path.join("cohort-operation-boundary.json"),
                &boundary_bytes,
            )?;
            manifest.cohort.as_mut().unwrap().operation_boundary_sha256 =
                Some(core::digest(&boundary_bytes));
            save(path, manifest, record)?;
            operation?;
            verify(path)?;
        }
        Ok(())
    })();
    // A single owner kills/reaps on every outcome, before publishing a terminal
    // result. No replacement worker or model load can occur inside a cohort.
    let worker_pid = worker.as_ref().map(|owned| owned.child.id());
    let release = worker.as_mut().map(Worker::terminate_owned).transpose();
    let worker_released = release.is_ok();
    let worker_exit_status = release
        .as_ref()
        .ok()
        .and_then(|status| status.as_ref())
        .map(ToString::to_string);
    if let Err(release_error) = release {
        let preceding = outcome
            .as_ref()
            .err()
            .map(|e| format!("{}; ", e.message))
            .unwrap_or_default();
        outcome = Err(err(
            "worker-release",
            format!(
                "{preceding}Owned worker reap failed: {}",
                release_error.message
            ),
        ));
    }
    drop(worker);
    let diagnostic = outcome
        .as_ref()
        .err()
        .map(|e| e.message.chars().take(4096).collect::<String>());
    if let Some(message) = &diagnostic {
        let (path, manifest, record) = &mut sessions[active_index];
        if !record.complete() && record.state.failed.is_none() {
            retain_failure(path, manifest, record, message)?;
        }
        for (path, manifest, record) in sessions.iter_mut().skip(active_index + 1) {
            manifest.status = "paused".into();
            manifest.diagnostic =
                Some("Cohort stopped before this arm; no automatic resume is permitted".into());
            save(path, manifest, record)?;
        }
    }
    let snapshots = sessions
        .iter()
        .map(|(path, manifest, record)| snapshot(path, manifest, record))
        .collect::<Result<Vec<_>>>()?;
    let result = json!({"schema":"activation-cohort-result-v1","status":if outcome.is_ok(){"completed"}else{"failed"},
        "cohortDirectory":root,"cohortId":plan.cohort_id,"sessions":snapshots,"diagnostic":diagnostic,
        "modelsLoaded":models_loaded,"workerStarts":worker_starts,"workerPid":worker_pid,"workerReleased":worker_released,"workerExitStatus":worker_exit_status,
        "lifetimeSeconds":lifetime.as_secs_f64(),"elapsedSeconds":started_at.elapsed().as_secs_f64()});
    publish(&root.join("cohort-result.json"), &encode(&result)?)?;
    Ok(result)
}
fn retain_failure(
    path: &Path,
    manifest: &mut Manifest,
    record: &mut Record,
    message: &str,
) -> Result<()> {
    let message = message.chars().take(4096).collect::<String>();
    if record.complete() && record.state.failed.is_none() {
        // A later cohort stop does not undo an already saved/applied arm.
        manifest.status = "completed".into();
        manifest.diagnostic = Some(message);
        manifest.active_operation = None;
        return save(path, manifest, record);
    }
    if record.state.failed.is_none() {
        record
            .append(Event::Failed {
                reason: message.clone(),
            })
            .map_err(io)?;
    }
    manifest.status = "failed".into();
    manifest.diagnostic = Some(message);
    manifest.active_operation = None;
    save(path, manifest, record)
}
fn verify_cohort_membership(p: &Path, m: &Manifest, r: &Record) -> Result<()> {
    let Some(member) = &m.cohort else {
        return Ok(());
    };
    let plan_bytes =
        files::read_bounded(&p.join("cohort-plan.json"), RESPONSE_LIMIT, "activation")?;
    let plan: CohortPlan = serde_json::from_slice(&plan_bytes).map_err(io)?;
    validate_cohort(&plan.configs)?;
    if plan.format != "activation-cohort-plan-v1"
        || core::digest(&plan_bytes) != member.plan_sha256
        || plan.session_ids.len() != 3
        || member.index >= 3
        || plan.session_ids[member.index] != member.origin_session_id
        || plan.configs[member.index] != m.config
        || plan.worker_sha256 != m.worker_sha256
        || plan.lifetime_seconds <= 0.0
        || plan.lifetime_seconds > 900.0
        || plan.request_timeout_seconds != 180
        || plan
            .session_ids
            .iter()
            .enumerate()
            .any(|(i, id)| !id_ok(id) || plan.session_ids[..i].contains(id))
    {
        return Err(err(
            "cohort",
            "Session membership differs from its immutable cohort plan",
        ));
    }
    let calibration_bytes = files::read_bounded(
        &p.join("cohort-calibration-source.json"),
        RESPONSE_LIMIT,
        "activation",
    )?;
    if core::digest(&calibration_bytes) != plan.calibration_source_sha256 {
        return Err(err("cohort", "Cohort calibration source differs"));
    }
    let started: Vec<_> = r
        .events
        .iter()
        .filter_map(|event| match event {
            Event::RequestStarted { request } => Some(request),
            _ => None,
        })
        .collect();
    let Some(initialization_sha256) = &member.initialization_sha256 else {
        if !started.is_empty()
            || m.model_manifest_sha256.is_some()
            || member.first_operation_sequence.is_some()
            || member.operation_boundary_sha256.is_some()
            || r.complete()
        {
            return Err(err(
                "cohort",
                "Cohort operation lacks shared initialization proof",
            ));
        }
        return Ok(());
    };
    let init_bytes = files::read_bounded(
        &p.join("shared-initialization.json"),
        RESPONSE_LIMIT,
        "activation",
    )?;
    let init: SharedInitialization = serde_json::from_slice(&init_bytes).map_err(io)?;
    let request_bytes = files::read_bounded(
        &p.join("shared-initialize-request.json"),
        RESPONSE_LIMIT,
        "activation",
    )?;
    let response_bytes = files::read_bounded(
        &p.join("shared-initialize-response.json"),
        RESPONSE_LIMIT,
        "activation",
    )?;
    if core::digest(&init_bytes) != *initialization_sha256
        || init.format != "activation-shared-initialization-v1"
        || init.cohort_id != plan.cohort_id
        || init.plan_sha256 != member.plan_sha256
        || init.sequence != 1
        || init.worker_pid == 0
        || core::digest(&request_bytes) != init.request_sha256
        || core::digest(&response_bytes) != init.response_sha256
    {
        return Err(err("cohort", "Shared initialization binding differs"));
    }
    let request: Value = serde_json::from_slice(&request_bytes).map_err(io)?;
    let response: Value = serde_json::from_slice(&response_bytes).map_err(io)?;
    let source: Value = serde_json::from_slice(&calibration_bytes).map_err(io)?;
    if request
        != json!({"id":"worker-1","command":"initialize","modelPath":m.config.model_path,"existingCalibration":source})
        || response["id"] != "worker-1"
        || response["command"] != "initialize"
        || response["type"] != "result"
        || response["protocolVersion"] != "reservoir-activation/1"
        || !response["workerIdentity"].is_object()
        || response["result"]["calibration"] != source
        || response["workerIdentity"]["modelManifestSha256"].as_str()
            != m.model_manifest_sha256.as_deref()
        || response["result"]["manifest"]["sha256"].as_str() != m.model_manifest_sha256.as_deref()
        || response["result"]["calibration"]["sha256"].as_str() != m.calibration_sha256.as_deref()
        || Some(core::digest(&encode(&response["result"]["manifest"])?)).as_ref()
            != m.model_manifest_file_sha256.as_ref()
        || Some(core::digest(&encode(&source)?)).as_ref() != m.calibration_file_sha256.as_ref()
    {
        return Err(err(
            "cohort",
            "Borrowed initialization does not match the actual shared request and result",
        ));
    }
    let Some(first) = member.first_operation_sequence else {
        if !started.is_empty() || member.operation_boundary_sha256.is_some() || r.complete() {
            return Err(err(
                "cohort",
                "Operation lacks its shared-worker sequence boundary",
            ));
        }
        return Ok(());
    };
    let operations_per_arm =
        m.config.observations.len() + m.config.observations.len() / m.config.journal_every;
    if first != 2 + member.index as u64 * operations_per_arm as u64 {
        return Err(err(
            "cohort",
            "Session sequence boundary overlaps or skips another cohort arm",
        ));
    }
    let boundary = if let Some(hash) = &member.operation_boundary_sha256 {
        let bytes = files::read_bounded(
            &p.join("cohort-operation-boundary.json"),
            RESPONSE_LIMIT,
            "activation",
        )?;
        let boundary: OperationBoundary = serde_json::from_slice(&bytes).map_err(io)?;
        if core::digest(&bytes) != *hash
            || boundary.format != "activation-cohort-boundary-v1"
            || boundary.initialization_sha256 != *initialization_sha256
            || boundary.origin_session_id != member.origin_session_id
            || boundary.index != member.index
            || boundary.first_sequence != first
            || boundary.last_sequence < first - 1
            || boundary.record_sha256 != m.record_sha256
            || !matches!(boundary.status.as_str(), "failed" | "completed")
            || (boundary.status == "completed") != r.complete()
        {
            return Err(err(
                "cohort",
                "Cohort operation boundary differs from the retained session",
            ));
        }
        Some(boundary)
    } else {
        if r.complete() {
            return Err(err(
                "cohort",
                "Completed cohort session lacks a closed operation boundary",
            ));
        }
        None
    };
    let mut sequences = Vec::new();
    for entry in fs::read_dir(p).map_err(io)? {
        let name = entry
            .map_err(io)?
            .file_name()
            .to_string_lossy()
            .into_owned();
        if let Some(index) = name
            .strip_prefix("cohort-protocol-")
            .and_then(|n| n.strip_suffix("-request.json"))
        {
            sequences.push(index.parse::<u64>().map_err(io)?);
        }
    }
    sequences.sort_unstable();
    if sequences.len() > started.len()
        || started.len() - sequences.len() > 1
        || sequences
            .iter()
            .enumerate()
            .any(|(i, sequence)| *sequence != first + i as u64)
        || (r.complete() && sequences.len() != started.len())
        || boundary
            .as_ref()
            .is_some_and(|b| b.last_sequence != first - 1 + sequences.len() as u64)
    {
        return Err(err(
            "cohort",
            "Shared-worker operation sequence is missing, duplicated, or outside its arm boundary",
        ));
    }
    for (index, sequence) in sequences.iter().enumerate() {
        let core_request = started[index];
        let actual: Value = decode(&p.join(format!("cohort-protocol-{sequence}-request.json")))?;
        let retained_request: Value = decode(&p.join(format!("{}-request.json", core_request.id)))?;
        let mut expected = request_payload(m, core_request);
        if retained_request != expected {
            return Err(err(
                "cohort",
                "Retained request differs from the replayed session operation",
            ));
        }
        expected["id"] = json!(format!("worker-{sequence}"));
        expected["command"] = json!(core_request.kind);
        if actual != expected {
            return Err(err(
                "cohort",
                "Actual worker request differs from its session request",
            ));
        }
        let accepted = r.events.iter().any(|event| match event {
            Event::QuietReceived { request_id, .. } | Event::JournalReceived { request_id, .. } => {
                request_id == &core_request.id
            }
            _ => false,
        });
        let wire_path = p.join(format!("cohort-protocol-{sequence}-response.json"));
        if !wire_path.exists() {
            if accepted {
                return Err(err(
                    "cohort",
                    "Accepted result lacks its actual worker response",
                ));
            }
            continue;
        }
        let wire: Value = decode(&wire_path)?;
        if wire["id"] != actual["id"] || wire["command"] != actual["command"] {
            return Err(err(
                "cohort",
                "Worker response is outside its recorded operation boundary",
            ));
        }
        if accepted {
            let retained: Value = decode(&p.join(format!("{}-response.json", core_request.id)))?;
            if wire["type"] != "result"
                || wire["result"] != retained
                || wire["workerIdentity"] != response["workerIdentity"]
                || wire["protocolVersion"] != response["protocolVersion"]
            {
                return Err(err(
                    "cohort",
                    "Accepted result differs from its shared worker identity or wire evidence",
                ));
            }
        }
    }
    Ok(())
}
struct Shared {
    root: PathBuf,
    default_worker: PathBuf,
    busy: AtomicBool,
    cancel: AtomicBool,
    active: Mutex<Option<String>>,
    join: Mutex<Option<JoinHandle<()>>>,
    lifecycle: Mutex<()>,
    closing: AtomicBool,
}
#[derive(Clone)]
pub struct ActivationState(Arc<Shared>);
impl ActivationState {
    pub fn new(root: PathBuf, default_worker: PathBuf) -> Self {
        Self(Arc::new(Shared {
            root,
            default_worker,
            busy: AtomicBool::new(false),
            cancel: AtomicBool::new(false),
            active: Mutex::new(None),
            join: Mutex::new(None),
            lifecycle: Mutex::new(()),
            closing: AtomicBool::new(false),
        }))
    }
    pub fn is_busy(&self) -> bool {
        self.0.busy.load(Ordering::SeqCst)
    }
    fn path(&self, id: &str) -> Result<PathBuf> {
        if !id_ok(id) {
            return Err(err("identity", "Invalid activation session identity"));
        }
        let p = self.0.root.join(id);
        ordinary_dir(&p)?;
        Ok(p)
    }
    pub fn resolve(&self, mut c: Config) -> Config {
        let repo = Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap();
        if c.worker_path.is_empty() {
            c.worker_path = self.0.default_worker.to_string_lossy().into();
        }
        if c.python_path.is_empty() {
            c.python_path = repo
                .join(".venv-activation/bin/python")
                .to_string_lossy()
                .into();
        }
        if c.model_path.is_empty() {
            c.model_path = repo
                .join(".activation-models/qwen3-4b")
                .to_string_lossy()
                .into();
        }
        c
    }
    pub fn inspect(&self, c: Config) -> Result<Value> {
        let c = self.resolve(c);
        c.validate()?;
        let cancel = AtomicBool::new(false);
        let mut w = Worker::spawn(&c)?;
        let result = w.call(
            "inspect",
            json!({"modelPath":c.model_path}),
            &cancel,
            Duration::from_secs(30),
        )?;
        Ok(json!({"ready":true,"config":c,"capability":result}))
    }
    pub fn create(&self, c: Config) -> Result<Snapshot> {
        let c = self.resolve(c);
        c.validate()?;
        let worker_sha = worker_identity(Path::new(&c.worker_path))?;
        fs::create_dir_all(&self.0.root).map_err(io)?;
        ordinary_dir(&self.0.root)?;
        let id = format!("activation-{}", now());
        let p = self.0.root.join(&id);
        fs::create_dir(&p).map_err(io)?;
        let record = Record::new(c.specification()).map_err(io)?;
        let mut m = Manifest {
            format: "activation-session-v1".into(),
            session_id: id,
            revision: 0,
            status: "ready".into(),
            config: c,
            record_file: String::new(),
            record_sha256: String::new(),
            worker_sha256: worker_sha,
            diagnostic: None,
            active_operation: None,
            model_manifest_sha256: None,
            calibration_sha256: None,
            calibration_file_sha256: None,
            model_manifest_file_sha256: None,
            cohort: None,
        };
        save(&p, &mut m, &record)?;
        snapshot(&p, &m, &record)
    }
    pub fn get(&self, id: Option<&str>) -> Result<Option<Snapshot>> {
        let owned = if let Some(id) = id {
            Some(id.into())
        } else {
            self.0.active.lock().unwrap().clone()
        };
        let Some(id) = owned else { return Ok(None) };
        let p = self.path(&id)?;
        let (m, r) = load(&p)?;
        Ok(Some(snapshot(&p, &m, &r)?))
    }
    pub fn seed_calibration(&self, id: &str, source: &Path) -> Result<()> {
        let p = self.path(id)?;
        let (m, r) = load(&p)?;
        if m.status != "ready" || !r.events.is_empty() {
            return Err(err(
                "calibration",
                "Calibration can only be attached to a new session",
            ));
        }
        let raw = files::read_bounded(source, RESPONSE_LIMIT, "activation")?;
        let value: Value = serde_json::from_slice(&raw).map_err(io)?;
        if value.get("sha256").and_then(Value::as_str).is_none()
            || value
                .get("modelManifestSha256")
                .and_then(Value::as_str)
                .is_none()
        {
            return Err(err("calibration", "Calibration lacks frozen identity"));
        }
        publish(&p.join("calibration.json"), &encode(&value)?)?;
        publish(
            &p.join("calibration-source.json"),
            &encode(
                &json!({"sourceFileSha256":core::digest(&raw),"calibrationSha256":value["sha256"]}),
            )?,
        )
    }
    pub fn list(&self) -> Result<Vec<Snapshot>> {
        if !self.0.root.exists() {
            return Ok(vec![]);
        }
        ordinary_dir(&self.0.root)?;
        let mut out = vec![];
        for e in fs::read_dir(&self.0.root).map_err(io)?.take(1000) {
            let e = e.map_err(io)?;
            if e.file_type().map_err(io)?.is_dir()
                && e.file_name().to_string_lossy().starts_with("activation-")
                && e.path().join("latest.json").exists()
            {
                let (m, r) = load(&e.path())?;
                out.push(snapshot(&e.path(), &m, &r)?);
            }
        }
        out.sort_by(|a, b| b.session_id.cmp(&a.session_id));
        Ok(out)
    }
    pub fn start(&self, id: &str) -> Result<Snapshot> {
        let _lifecycle = self.0.lifecycle.lock().unwrap();
        if self.0.closing.load(Ordering::SeqCst) {
            return Err(err("closing", "Application close is in progress"));
        }
        if self
            .0
            .busy
            .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
            .is_err()
        {
            return Err(err("busy", "An activation experiment is already running"));
        }
        let setup = (|| {
            let p = self.path(id)?;
            verify(&p)?;
            let (mut m, r) = load(&p)?;
            let s = snapshot(&p, &m, &r)?;
            if !s.can_start {
                return Err(err(
                    "boundary",
                    "This session cannot resume an uncertain, failed, or completed operation",
                ));
            }
            m.status = "running".into();
            m.diagnostic = None;
            save(&p, &mut m, &r)?;
            Ok((p, m, r))
        })();
        let (p, m, r) = match setup {
            Ok(x) => x,
            Err(e) => {
                self.0.busy.store(false, Ordering::SeqCst);
                return Err(e);
            }
        };
        self.0.cancel.store(false, Ordering::SeqCst);
        *self.0.active.lock().unwrap() = Some(id.into());
        let state = self.clone();
        let initial = snapshot(&p, &m, &r)?;
        let handle = thread::spawn(move || {
            state.run(p, m, r);
            state.0.busy.store(false, Ordering::SeqCst);
        });
        *self.0.join.lock().unwrap() = Some(handle);
        Ok(initial)
    }
    pub fn stop(&self, id: &str) -> Result<Snapshot> {
        let _lifecycle = self.0.lifecycle.lock().unwrap();
        if self.0.active.lock().unwrap().as_deref() == Some(id) {
            self.stop_locked();
        }
        self.get(Some(id))?
            .ok_or_else(|| err("missing", "Session not found"))
    }
    pub fn stop_owned(&self) {
        let _lifecycle = self.0.lifecycle.lock().unwrap();
        self.stop_locked();
    }
    fn stop_locked(&self) {
        self.0.cancel.store(true, Ordering::SeqCst);
        let handle = self.0.join.lock().unwrap().take();
        if let Some(h) = handle {
            let _ = h.join();
        }
    }
    pub fn request_close(&self) {
        self.0.closing.store(true, Ordering::SeqCst);
        self.stop_owned();
    }
    pub fn cancel_close(&self) {
        self.0.closing.store(false, Ordering::SeqCst);
    }
    pub fn restore(&self, id: &str) -> Result<Snapshot> {
        let _lifecycle = self.0.lifecycle.lock().unwrap();
        if self.is_busy() {
            return Err(err("busy", "Stop the active experiment before recovery"));
        }
        let p = self.path(id)?;
        verify(&p)?;
        let (mut m, mut r) = load(&p)?;
        if m.status == "running"
            || m.active_operation.is_some()
            || r.state.pending_request.is_some()
        {
            if r.state.failed.is_none() {
                r.append(Event::Failed {
                    reason: "Interrupted operation has an uncertain outcome; it will not be resent"
                        .into(),
                })
                .map_err(io)?;
            }
            m.status = "failed".into();
            m.diagnostic = r.state.failed.clone();
            m.active_operation = None;
        } else if !r.complete() && r.state.failed.is_none() {
            m.status = "paused".into();
        }
        save(&p, &mut m, &r)?;
        *self.0.active.lock().unwrap() = Some(id.into());
        snapshot(&p, &m, &r)
    }
    pub fn annotate(&self, id: &str, a: Annotation) -> Result<Snapshot> {
        let p = self.path(id)?;
        let (m, r) = load(&p)?;
        for s in [&a.excerpt, &a.interpretation, &a.alternative] {
            if s.len() > 16384 {
                return Err(err("annotation", "Annotation text exceeds 16384 bytes"));
            }
        }
        if a.source_event_ids.len() > 120
            || a.source_event_ids.iter().any(|id| {
                !id.strip_prefix("event-")
                    .and_then(|s| s.parse::<usize>().ok())
                    .is_some_and(|n| n > 0 && n <= r.events.len())
            })
        {
            return Err(err(
                "annotation",
                "Annotation references an unavailable event",
            ));
        }
        if let Some(id) = &a.journal_id {
            let j = r
                .state
                .journals
                .iter()
                .find(|j| &j.id == id)
                .ok_or_else(|| err("annotation", "Annotation journal is unavailable"))?;
            if !a.excerpt.is_empty() && !j.text.contains(&a.excerpt) {
                return Err(err(
                    "annotation",
                    "Excerpt is not present in the selected journal",
                ));
            }
        }
        publish(&p.join(format!("annotation-{}.json", now())), &encode(&a)?)?;
        snapshot(&p, &m, &r)
    }
    pub fn export(&self, id: &str, destination: &Path) -> Result<()> {
        let _lifecycle = self.0.lifecycle.lock().unwrap();
        if self.is_busy() {
            return Err(err("busy", "Stop the activation experiment before export"));
        }
        let p = self.path(id)?;
        let _ = verify(&p)?;
        let mut entries = BTreeMap::new();
        let mut total = 0;
        for e in fs::read_dir(&p).map_err(io)? {
            let e = e.map_err(io)?;
            let name = e.file_name().to_string_lossy().into_owned();
            if name.starts_with('.') {
                continue;
            }
            if !e.file_type().map_err(io)?.is_file() {
                return Err(err("export", "Unexpected evidence directory entry"));
            }
            let raw = files::read_bounded(&e.path(), MAX_BYTES, "activation")?;
            total += raw.len();
            if total > MAX_BYTES as usize {
                return Err(err("export", "Evidence exceeds export bound"));
            }
            entries.insert(name, String::from_utf8(raw).map_err(io)?);
        }
        publish(
            destination,
            &encode(&Export {
                format: "activation-export-v1".into(),
                files: entries,
            })?,
        )
    }
    pub fn import(&self, source: &Path) -> Result<Snapshot> {
        let _lifecycle = self.0.lifecycle.lock().unwrap();
        if self.is_busy() {
            return Err(err("busy", "Stop before importing an experiment"));
        }
        let export: Export = decode(source)?;
        if export.format != "activation-export-v1" || export.files.len() > 4096 {
            return Err(err("import", "Unsupported activation export"));
        }
        fs::create_dir_all(&self.0.root).map_err(io)?;
        let temp = tempfile::Builder::new()
            .prefix(".activation-import-")
            .tempdir_in(&self.0.root)
            .map_err(io)?;
        for (name, text) in &export.files {
            if name.contains('/')
                || name.contains('\\')
                || name.starts_with('.')
                || name.len() > 128
            {
                return Err(err("import", "Invalid evidence filename"));
            }
            publish(&temp.path().join(name), text.as_bytes())?;
        }
        let (mut m, r) = load(temp.path())?;
        let _ = verify(temp.path())?;
        let original = m.session_id.clone();
        m.session_id = format!("activation-{}", now());
        m.status = if r.complete() {
            "completed"
        } else if r.state.failed.is_some() || r.state.pending_request.is_some() {
            "failed"
        } else {
            "paused"
        }
        .into();
        m.active_operation = None;
        m.diagnostic = Some(format!(
            "Imported from {original}; no model request was made"
        ));
        save(temp.path(), &mut m, &r)?;
        let p = self.0.root.join(&m.session_id);
        fs::rename(temp.path(), &p).map_err(io)?;
        snapshot(&p, &m, &r)
    }
    fn run(&self, p: PathBuf, mut m: Manifest, mut r: Record) {
        let result = self.execute(&p, &mut m, &mut r);
        if let Err(e) = result {
            let message = e.message.chars().take(4096).collect::<String>();
            if r.state.failed.is_none() {
                let _ = r.append(Event::Failed {
                    reason: message.clone(),
                });
            }
            m.status = "failed".into();
            m.diagnostic = Some(message);
            m.active_operation = None;
            let _ = save(&p, &mut m, &r);
        }
    }
    fn execute(&self, p: &Path, m: &mut Manifest, r: &mut Record) -> Result<()> {
        if worker_identity(Path::new(&m.config.worker_path))? != m.worker_sha256 {
            return Err(err(
                "identity",
                "The worker entrypoint changed since session creation",
            ));
        }
        #[cfg(not(test))]
        {
            let admission = admit();
            let receipt = match &admission {
                Ok(v) => v.clone(),
                Err(e) => json!({"admitted":false,"category":e.category,"message":e.message}),
            };
            publish(
                &p.join(format!("admission-{}.json", now())),
                &encode(&receipt)?,
            )?;
            admission?;
        }
        let mut worker = Worker::spawn(&m.config)?;
        worker.evidence_path = Some(p.join(format!("worker-stderr-{}.txt", now())));
        worker.protocol_prefix = Some(p.join(format!("worker-protocol-{}", now())));
        m.active_operation = Some("initialize".into());
        save(p, m, r)?;
        let calibration = if p.join("calibration.json").exists() {
            Some(decode::<Value>(&p.join("calibration.json"))?)
        } else {
            None
        };
        let result = worker.call(
            "initialize",
            json!({"modelPath":m.config.model_path,"existingCalibration":calibration}),
            &self.0.cancel,
            Duration::from_secs(180),
        )?;
        retain_initialization(p, m, &result)?;
        publish(
            &p.join(format!("initialize-{}.json", now())),
            &encode(&result)?,
        )?;
        m.active_operation = None;
        save(p, m, r)?;
        Self::execute_operations(p, m, r, &mut worker, &self.0.cancel, None)
    }
    fn execute_operations(
        p: &Path,
        m: &mut Manifest,
        r: &mut Record,
        worker: &mut Worker,
        cancel: &AtomicBool,
        cohort: Option<&CohortRuntime<'_>>,
    ) -> Result<()> {
        loop {
            if r.next_kind() == "complete" {
                m.status = "completed".into();
                m.active_operation = None;
                save(p, m, r)?;
                return Ok(());
            }
            operation_timeout(cohort.map(|c| c.deadline))?;
            if cancel.load(Ordering::SeqCst) {
                m.status = "paused".into();
                m.active_operation = None;
                save(p, m, r)?;
                return Ok(());
            }
            match r.next_kind() {
                "save" => {
                    let j = r.state.journals.last().unwrap().clone();
                    let file = p.join(format!("{}.txt", j.id));
                    publish(&file, j.text.as_bytes())?;
                    let text = files::read_bounded(&file, 65536, "activation")?;
                    if text != j.text.as_bytes() {
                        return Err(err("save", "Journal readback differed"));
                    }
                    r.append(Event::JournalSaved {
                        journal_id: j.id,
                        sha256: core::digest(&text),
                    })
                    .map_err(io)?;
                    save(p, m, r)?;
                }
                "apply" => {
                    let j = r.state.journals.last().unwrap();
                    let bytes =
                        files::read_bounded(&p.join(format!("{}.txt", j.id)), 65536, "activation")?;
                    if core::digest(&bytes) != j.sha256 {
                        return Err(err("save", "Saved journal changed before application"));
                    }
                    r.append(Event::JournalApplied {
                        journal_id: j.id.clone(),
                    })
                    .map_err(io)?;
                    save(p, m, r)?;
                }
                "quiet_capture" | "generate_journal" => {
                    if let Some(c) = cohort {
                        c.guard(r.next_kind(), cancel)?;
                    }
                    let request = r.request().map_err(io)?;
                    r.append(Event::RequestStarted {
                        request: request.clone(),
                    })
                    .map_err(io)?;
                    m.active_operation = Some(request.kind.clone());
                    save(p, m, r)?;
                    let payload = request_payload(m, &request);
                    publish(
                        &p.join(format!("{}-request.json", request.id)),
                        &encode(&payload)?,
                    )?;
                    let response = worker.call(
                        &request.kind,
                        payload,
                        cancel,
                        operation_timeout(cohort.map(|c| c.deadline))?,
                    )?;
                    let bytes = encode(&response)?;
                    publish(&p.join(format!("{}-response.json", request.id)), &bytes)?;
                    if cancel.load(Ordering::SeqCst) {
                        return Err(err("cancelled","Received response retained after cancellation; no journal or feedback is eligible"));
                    }
                    let evidence_sha256 = core::digest(&bytes);
                    check_response_identity(m, &request, &response)?;
                    if request.kind == "generate_journal"
                        && response.get("complete") != Some(&Value::Bool(true))
                    {
                        return Err(err("incomplete","Incomplete journal response was retained; no journal feedback is eligible"));
                    }
                    let projection: Vec<f64> = serde_json::from_value(
                        response.get("projection").cloned().unwrap_or(Value::Null),
                    )
                    .map_err(|_| {
                        err(
                            "projection",
                            "Worker omitted a complete 32-coordinate projection",
                        )
                    })?;
                    if request.kind == "quiet_capture" {
                        if response["receipt"]["sampledTokenCount"] != json!(0)
                            || response["sampledTokenIds"] != json!([])
                            || response["generatedTokenIds"] != json!([])
                        {
                            return Err(err(
                                "quiet-output",
                                "Quiet capture lacks an explicit zero-sampling receipt",
                            ));
                        }
                        r.append(Event::QuietReceived {
                            request_id: request.id,
                            projection,
                            evidence_sha256,
                        })
                        .map_err(io)?;
                    } else {
                        if response.get("complete") != Some(&Value::Bool(true)) {
                            return Err(err("incomplete","Incomplete journal response was retained; no journal feedback is eligible"));
                        }
                        let text = response
                            .get("text")
                            .and_then(Value::as_str)
                            .ok_or_else(|| err("protocol", "Worker omitted journal text"))?;
                        r.append(Event::JournalReceived {
                            request_id: request.id,
                            text: text.into(),
                            projection,
                            evidence_sha256,
                        })
                        .map_err(io)?;
                    }
                    m.active_operation = None;
                    save(p, m, r)?;
                }
                _ => return Err(err("boundary", "Refusing to resend an uncertain operation")),
            }
        }
    }
}

fn retain_initialization(p: &Path, m: &mut Manifest, result: &Value) -> Result<()> {
    let cal = result
        .get("calibration")
        .ok_or_else(|| err("protocol", "Initialization omitted calibration"))?;
    publish(&p.join("calibration.json"), &encode(cal)?)?;
    let model_hash = result["manifest"]["sha256"]
        .as_str()
        .ok_or_else(|| err("identity", "Initialization omitted model/runtime identity"))?;
    let calibration_hash = cal["sha256"]
        .as_str()
        .ok_or_else(|| err("identity", "Calibration omitted identity"))?;
    if m.model_manifest_sha256
        .as_deref()
        .is_some_and(|h| h != model_hash)
        || m.calibration_sha256
            .as_deref()
            .is_some_and(|h| h != calibration_hash)
    {
        return Err(err(
            "identity",
            "Initialization changed the frozen model/runtime or calibration",
        ));
    }
    m.model_manifest_sha256 = Some(model_hash.into());
    m.calibration_sha256 = Some(calibration_hash.into());
    m.calibration_file_sha256 = Some(core::digest(&encode(cal)?));
    let manifest_bytes = encode(&result["manifest"])?;
    publish(&p.join("model-manifest.json"), &manifest_bytes)?;
    m.model_manifest_file_sha256 = Some(core::digest(&manifest_bytes));
    Ok(())
}

fn save(p: &Path, m: &mut Manifest, r: &Record) -> Result<()> {
    r.verify().map_err(io)?;
    let bytes = encode(r)?;
    let hash = core::digest(&bytes);
    let name = format!("record-{}-{}.json", r.events.len(), &hash[..12]);
    let limit = if r.state.failed.is_some() {
        MAX_BYTES
    } else {
        MAX_BYTES - 32 * 1024 * 1024
    };
    publish_limit(&p.join(&name), &bytes, limit)?;
    m.record_file = name;
    m.record_sha256 = hash;
    m.revision += 1;
    let bytes = encode(m)?;
    publish_limit(
        &p.join(format!("manifest-{:06}.json", m.revision)),
        &bytes,
        limit,
    )?;
    // Immutable manifests are the journal; atomic latest pointer is convenience.
    let temp = p.join(format!(".latest-{}", now()));
    publish_limit(&temp, &bytes, limit)?;
    fs::rename(temp, p.join("latest.json")).map_err(io)?;
    fs::File::open(p).and_then(|f| f.sync_all()).map_err(io)
}
fn load(p: &Path) -> Result<(Manifest, Record)> {
    ordinary_dir(p)?;
    let m: Manifest = decode(&p.join("latest.json"))?;
    if !matches!(
        m.format.as_str(),
        "activation-session-v1" | "activation-cohort-session-v1"
    ) || (m.format == "activation-cohort-session-v1") != m.cohort.is_some()
        || !m.record_file.starts_with("record-")
        || m.record_file.contains('/')
        || m.record_file.contains('\\')
    {
        return Err(err("record", "Invalid activation manifest"));
    }
    let bytes = files::read_bounded(&p.join(&m.record_file), MAX_BYTES, "activation")?;
    if core::digest(&bytes) != m.record_sha256 {
        return Err(err("record", "Activation checkpoint hash differs"));
    }
    let r: Record = serde_json::from_slice(&bytes).map_err(io)?;
    r.verify().map_err(io)?;
    if r.specification != m.config.specification() {
        return Err(err(
            "record",
            "Configuration differs from the recorded mechanism",
        ));
    }
    Ok((m, r))
}
fn snapshot(p: &Path, m: &Manifest, r: &Record) -> Result<Snapshot> {
    let journals = r
        .state
        .journals
        .iter()
        .map(|j| JournalView {
            id: j.id.clone(),
            text: j.text.clone(),
            observed_step: j.observed_step,
            first_applied_step: j.first_applied_step,
            sha256: j.sha256.clone(),
            status: if j.first_applied_step.is_some() {
                "applied"
            } else if j.saved {
                "savedPendingApplication"
            } else {
                "receivedPendingSave"
            }
            .into(),
        })
        .collect();
    let mut replay = Record::new(r.specification.clone()).map_err(io)?;
    let mut events = vec![];
    for (i, e) in r.events.iter().enumerate() {
        replay.append(e.clone()).map_err(io)?;
        let (kind, detail) = match e {
            Event::RequestStarted { request } => ("requestStarted", request.kind.clone()),
            Event::QuietReceived { .. } => (
                "quietReceived",
                "Observation registered without sampled output".into(),
            ),
            Event::JournalReceived { .. } => (
                "journalReceived",
                "Complete writing received; save pending".into(),
            ),
            Event::JournalSaved { .. } => {
                ("journalSaved", "Exact journal saved and read back".into())
            }
            Event::JournalApplied { .. } => (
                "journalApplied",
                "Signature applied at the next numerical step".into(),
            ),
            Event::Failed { reason } => ("failed", reason.clone()),
        };
        events.push(EventView {
            id: format!("event-{}", i + 1),
            kind: kind.into(),
            step: replay.state.step,
            detail,
        });
    }
    let mut annotations = vec![];
    for e in fs::read_dir(p).map_err(io)? {
        let e = e.map_err(io)?;
        if e.file_name().to_string_lossy().starts_with("annotation-") {
            annotations.push(decode(&e.path())?);
        }
    }
    Ok(Snapshot {
        session_id: m.session_id.clone(),
        revision: m.revision,
        status: m.status.clone(),
        config: m.config.clone(),
        step: r.state.step,
        observation_index: r.state.observation_index,
        journal_count: r.state.journals.len(),
        journals,
        events,
        diagnostic: m.diagnostic.clone(),
        active_operation: m.active_operation.clone(),
        directory: p.to_string_lossy().into(),
        can_start: m.cohort.is_none()
            && matches!(m.status.as_str(), "ready" | "paused")
            && !matches!(r.next_kind(), "failed" | "uncertain" | "complete"),
        annotations,
        calibration_sha256: m.calibration_sha256.clone(),
        model_manifest_sha256: m.model_manifest_sha256.clone(),
    })
}
fn request_payload(m: &Manifest, request: &core::Request) -> Value {
    if request.kind == "quiet_capture" {
        json!({"text":request.prompt})
    } else {
        json!({"prompt":request.prompt,"steeringState":request.steering_state,"gain":if m.config.arm==Arm::NoSteering{0.0}else{m.config.gain},"arm":m.config.arm,"maxTokens":m.config.max_journal_tokens,"seed":m.config.seed,"temperature":0.0})
    }
}
fn check_response_identity(m: &Manifest, request: &core::Request, response: &Value) -> Result<()> {
    let receipt = &response["receipt"];
    if receipt["modelManifestSha256"].as_str() != m.model_manifest_sha256.as_deref()
        || receipt["calibrationSha256"].as_str() != m.calibration_sha256.as_deref()
        || receipt["freshCache"] != json!(true)
        || receipt["cacheDiscarded"] != json!(true)
    {
        return Err(err(
            "identity",
            "Worker response changed model, calibration, or cache-isolation identity",
        ));
    }
    if request.kind == "quiet_capture" {
        if receipt["sampledTokenCount"] != json!(0)
            || response["sampledTokenIds"] != json!([])
            || response["generatedTokenIds"] != json!([])
            || receipt["chatTemplateApplied"] != json!(false)
        {
            return Err(err(
                "quiet-output",
                "Quiet capture lacks an explicit isolated zero-sampling receipt",
            ));
        }
    } else {
        let gain = if m.config.arm == Arm::NoSteering {
            0.
        } else {
            m.config.gain
        };
        if receipt["steeringHeld"] != json!(true)
            || receipt["steeringState"] != json!(request.steering_state)
            || receipt["requestedGain"] != json!(gain)
            || receipt["arm"] != json!(m.config.arm)
            || receipt["seed"] != json!(m.config.seed)
            || receipt["temperature"] != json!(0.0)
            || receipt["maxTokens"] != json!(m.config.max_journal_tokens)
        {
            return Err(err(
                "steering",
                "Worker response differs from the frozen steering or generation request",
            ));
        }
        if response["complete"] == json!(true) {
            let tokens = response["generatedTokenIds"]
                .as_array()
                .ok_or_else(|| err("receipt", "Missing generated token identities"))?;
            if tokens.is_empty()
                || tokens.len() > m.config.max_journal_tokens as usize
                || receipt["feedbackEligible"] != json!(true)
                || receipt["capturedTokenId"] != *tokens.last().unwrap()
            {
                return Err(err(
                    "receipt",
                    "Complete journal lacks a matching final-content capture",
                ));
            }
        }
    }
    Ok(())
}
pub fn verify(p: &Path) -> Result<Value> {
    let (m, r) = load(p)?;
    verify_cohort_membership(p, &m, &r)?;
    if let Some(expected) = &m.calibration_file_sha256 {
        let bytes = files::read_bounded(&p.join("calibration.json"), RESPONSE_LIMIT, "activation")?;
        let value: Value = serde_json::from_slice(&bytes).map_err(io)?;
        if core::digest(&bytes) != *expected
            || value["sha256"].as_str() != m.calibration_sha256.as_deref()
            || value["modelManifestSha256"].as_str() != m.model_manifest_sha256.as_deref()
        {
            return Err(err(
                "calibration",
                "Retained calibration differs from the frozen initialization",
            ));
        }
    } else if m.calibration_sha256.is_some() {
        return Err(err(
            "calibration",
            "Calibration identity lacks its file proof",
        ));
    }
    if let Some(expected) = &m.model_manifest_file_sha256 {
        let bytes =
            files::read_bounded(&p.join("model-manifest.json"), RESPONSE_LIMIT, "activation")?;
        let value: Value = serde_json::from_slice(&bytes).map_err(io)?;
        if core::digest(&bytes) != *expected
            || value["sha256"].as_str() != m.model_manifest_sha256.as_deref()
        {
            return Err(err("identity", "Retained model/runtime manifest differs"));
        }
    }
    let mut replay = Record::new(r.specification.clone()).map_err(io)?;
    for e in &r.events {
        match e {
            Event::QuietReceived {
                request_id,
                evidence_sha256,
                projection,
            }
            | Event::JournalReceived {
                request_id,
                evidence_sha256,
                projection,
                ..
            } => {
                let b = files::read_bounded(
                    &p.join(format!("{request_id}-response.json")),
                    RESPONSE_LIMIT,
                    "activation",
                )?;
                if core::digest(&b) != *evidence_sha256 {
                    return Err(err("evidence", "Worker response evidence hash differs"));
                }
                let response: Value = serde_json::from_slice(&b).map_err(io)?;
                if response["projection"] != json!(projection) {
                    return Err(err(
                        "evidence",
                        "Recorded projection differs from its worker response",
                    ));
                }
                let request = replay
                    .state
                    .pending_request
                    .as_ref()
                    .ok_or_else(|| err("evidence", "Response has no preceding request"))?;
                check_response_identity(&m, request, &response)?;
                if let Event::JournalReceived { text, .. } = e {
                    if response["text"] != json!(text) || response["complete"] != json!(true) {
                        return Err(err(
                            "evidence",
                            "Recorded journal differs from its complete worker response",
                        ));
                    }
                }
            }
            _ => {}
        }
        replay.append(e.clone()).map_err(io)?;
    }
    for j in &r.state.journals {
        if j.saved {
            let b = files::read_bounded(&p.join(format!("{}.txt", j.id)), 65536, "activation")?;
            if b != j.text.as_bytes() || core::digest(&b) != j.sha256 {
                return Err(err("evidence", "Journal save/readback proof differs"));
            }
        }
    }
    Ok(
        json!({"status":"passed","modelsContacted":false,"sessionId":m.session_id,"steps":r.state.step,"journals":r.state.journals.len(),"events":r.events.len(),"scope":"Retained projection inputs, numerical replay, exact journals and recorded response hashes; not independent authentication of model activations"}),
    )
}

struct Worker {
    child: Child,
    input: Option<ChildStdin>,
    input_join: Option<JoinHandle<(ChildStdin, std::io::Result<()>)>>,
    output: Receiver<std::result::Result<String, String>>,
    sequence: u64,
    stderr: Arc<Mutex<Vec<u8>>>,
    stderr_join: Option<JoinHandle<()>>,
    evidence_path: Option<PathBuf>,
    protocol_prefix: Option<PathBuf>,
    frozen_envelope: Option<Value>,
}
impl Worker {
    fn spawn(c: &Config) -> Result<Self> {
        let mut child = Command::new(&c.python_path)
            .arg("-B")
            .arg(&c.worker_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .env("PYTHONDONTWRITEBYTECODE", "1")
            .env("HF_HUB_OFFLINE", "1")
            .env("TRANSFORMERS_OFFLINE", "1")
            .spawn()
            .map_err(|e| err("worker-start", e.to_string()))?;
        let input = child.stdin.take().unwrap();
        let stdout = child.stdout.take().unwrap();
        let mut stderr_pipe = child.stderr.take().unwrap();
        let stderr = Arc::new(Mutex::new(Vec::new()));
        let collected = stderr.clone();
        let stderr_join = thread::spawn(move || {
            let mut buffer = [0u8; 4096];
            while let Ok(n) = stderr_pipe.read(&mut buffer) {
                if n == 0 {
                    break;
                }
                let mut bytes = collected.lock().unwrap();
                let remaining = 65536usize.saturating_sub(bytes.len());
                bytes.extend_from_slice(&buffer[..n.min(remaining)]);
            }
        });
        let (tx, output) = mpsc::sync_channel(1);
        thread::spawn(move || {
            let mut reader = BufReader::new(stdout);
            loop {
                let mut bytes = Vec::new();
                let result = std::io::Read::take(&mut reader, RESPONSE_LIMIT + 1)
                    .read_until(b'\n', &mut bytes);
                let item = match result {
                    Ok(0) => break,
                    Ok(_) if bytes.len() as u64 > RESPONSE_LIMIT => {
                        Err("Worker response exceeded eight MiB".into())
                    }
                    Ok(_) => String::from_utf8(bytes).map_err(|e| e.to_string()),
                    Err(e) => Err(e.to_string()),
                };
                let failed = item.is_err();
                if tx.send(item).is_err() || failed {
                    break;
                }
            }
        });
        Ok(Self {
            child,
            input: Some(input),
            input_join: None,
            output,
            sequence: 0,
            stderr,
            stderr_join: Some(stderr_join),
            evidence_path: None,
            protocol_prefix: None,
            frozen_envelope: None,
        })
    }
    fn call(
        &mut self,
        command: &str,
        mut payload: Value,
        cancel: &AtomicBool,
        timeout: Duration,
    ) -> Result<Value> {
        let start = Instant::now();
        self.check_request_budget(cancel, start, timeout)?;
        self.sequence += 1;
        let id = format!("worker-{}", self.sequence);
        payload["id"] = json!(id);
        payload["command"] = json!(command);
        let bytes = serde_json::to_vec(&payload).map_err(io)?;
        if let Some(prefix) = &self.protocol_prefix {
            publish(
                &PathBuf::from(format!(
                    "{}-{}-request.json",
                    prefix.display(),
                    self.sequence
                )),
                &bytes,
            )?;
        }
        let mut input = self
            .input
            .take()
            .ok_or_else(|| err("worker-write", "Owned worker input is closed"))?;
        // A calibration request is larger than a pipe buffer. Keep its write
        // owned but off this control thread so a child that never reads cannot
        // prevent cancellation or consume time outside the request deadline.
        self.input_join = Some(thread::spawn(move || {
            let result = input
                .write_all(&bytes)
                .and_then(|_| input.write_all(b"\n"))
                .and_then(|_| input.flush());
            (input, result)
        }));
        loop {
            self.check_request_budget(cancel, start, timeout)?;
            if self.input_join.as_ref().unwrap().is_finished() {
                let (input, written) = self
                    .input_join
                    .take()
                    .unwrap()
                    .join()
                    .map_err(|_| err("worker-write", "Owned worker input writer panicked"))?;
                self.input = Some(input);
                written.map_err(|e| err("worker-write", e.to_string()))?;
                break;
            }
            thread::sleep(Duration::from_millis(20));
        }
        loop {
            self.check_request_budget(cancel, start, timeout)?;
            match self.output.recv_timeout(Duration::from_millis(20)) {
                Ok(Ok(line)) => {
                    let v: Value =
                        serde_json::from_str(&line).map_err(|e| err("protocol", e.to_string()))?;
                    if v["id"] != id || v["command"] != command {
                        return Err(err("protocol", "Worker response identity differs"));
                    }
                    if v["type"] != "progress" {
                        if let Some(prefix) = &self.protocol_prefix {
                            publish(
                                &PathBuf::from(format!(
                                    "{}-{}-response.json",
                                    prefix.display(),
                                    self.sequence
                                )),
                                line.as_bytes(),
                            )?;
                        }
                        if self.frozen_envelope.as_ref().is_some_and(|expected| {
                            v["workerIdentity"] != expected["workerIdentity"]
                                || v["protocolVersion"] != expected["protocolVersion"]
                        }) {
                            return Err(err(
                                "identity",
                                "Shared worker changed its initialized runtime identity",
                            ));
                        }
                    }
                    // recv_timeout may finish after the deadline. Retain any
                    // terminal wire evidence first, then refuse late results.
                    self.check_request_budget(cancel, start, timeout)?;
                    match v["type"].as_str() {
                        Some("progress") => continue,
                        Some("result") => return Ok(v["result"].clone()),
                        Some("error") => {
                            return Err(err(
                                "worker",
                                v["error"]["message"].as_str().unwrap_or("Worker failed"),
                            ))
                        }
                        _ => return Err(err("protocol", "Unknown worker envelope")),
                    }
                }
                Ok(Err(e)) => return Err(err("protocol", e)),
                Err(mpsc::RecvTimeoutError::Disconnected) => {
                    return Err(err(
                        "worker-exit",
                        "Worker exited without a complete response",
                    ))
                }
                Err(mpsc::RecvTimeoutError::Timeout) => {}
            }
        }
    }
    fn check_request_budget(
        &mut self,
        cancel: &AtomicBool,
        start: Instant,
        timeout: Duration,
    ) -> Result<()> {
        let failure = if cancel.load(Ordering::SeqCst) {
            Some(err(
                "cancelled",
                "Owned activation worker was cancelled; no late result is accepted",
            ))
        } else if start.elapsed() >= timeout {
            Some(err(
                "timeout",
                format!(
                    "Activation operation exceeded its {}-second deadline",
                    timeout.as_secs_f64()
                ),
            ))
        } else {
            None
        };
        if let Some(failure) = failure {
            if let Err(cleanup) = self.terminate_owned() {
                return Err(err(
                    "worker-release",
                    format!(
                        "{}; owned worker reap failed: {}",
                        failure.message, cleanup.message
                    ),
                ));
            }
            return Err(failure);
        }
        Ok(())
    }
    fn terminate_owned(&mut self) -> Result<std::process::ExitStatus> {
        // Killing and reaping the owned reader closes the pipe before joining
        // a writer which may currently be blocked in write_all.
        let _ = self.child.kill();
        let reaped = self.child.wait();
        if let Some(writer) = self.input_join.take() {
            let _ = writer.join();
        }
        self.input.take();
        reaped.map_err(|e| err("worker-release", e.to_string()))
    }
}
impl Drop for Worker {
    fn drop(&mut self) {
        let _ = self.terminate_owned();
        if let Some(h) = self.stderr_join.take() {
            let _ = h.join();
        }
        if let Some(path) = &self.evidence_path {
            let bytes = self.stderr.lock().unwrap();
            let safe = String::from_utf8_lossy(&bytes);
            let _ = publish(path, safe.as_bytes());
        }
    }
}

fn resident_pressure() -> Result<Value> {
    #[cfg(test)]
    {
        Ok(json!({"allowed":true,"pressure":1,"synthetic":true}))
    }
    #[cfg(all(not(test), target_os = "macos"))]
    {
        let output = Command::new("/usr/sbin/sysctl")
            .args(["-n", "kern.memorystatus_vm_pressure_level"])
            .output()
            .map_err(io)?;
        let level = String::from_utf8_lossy(&output.stdout)
            .trim()
            .parse::<u32>()
            .ok();
        if !output.status.success() || !matches!(level, Some(1 | 2)) {
            return Err(err("resident-resource", format!("Resident cohort stopped: pressure={level:?}; critical or unknown pressure does not admit another operation")));
        }
        Ok(
            json!({"allowed":true,"pressure":level,"scope":"already admitted resident worker; no new model load"}),
        )
    }
    #[cfg(all(not(test), not(target_os = "macos")))]
    {
        Err(err(
            "resident-resource",
            "MLX cohort pressure accounting requires macOS",
        ))
    }
}

#[cfg(not(test))]
fn admit() -> Result<Value> {
    #[cfg(target_os = "macos")]
    {
        let pressure = Command::new("/usr/sbin/sysctl")
            .args(["-n", "kern.memorystatus_vm_pressure_level"])
            .output()
            .map_err(io)?;
        let level = String::from_utf8_lossy(&pressure.stdout)
            .trim()
            .parse::<u32>()
            .ok();
        let free = Command::new("/usr/bin/memory_pressure")
            .arg("-Q")
            .output()
            .map_err(io)?;
        let text = String::from_utf8_lossy(&free.stdout);
        let percent = text.lines().find_map(|l| {
            l.strip_prefix("System-wide memory free percentage: ")
                .and_then(|s| s.trim_end_matches('%').trim().parse::<u32>().ok())
        });
        if !pressure.status.success()
            || !free.status.success()
            || level != Some(1)
            || percent.is_none_or(|n| n < 25)
        {
            return Err(err("admission",format!("Model admission refused: pressure={level:?}, freePercent={percent:?}; requires pressure 1 and at least 25%. No model loaded.")));
        }
        Ok(json!({"pressure":level,"freePercent":percent,"admitted":true}))
    }
    #[cfg(not(target_os = "macos"))]
    {
        Err(err(
            "admission",
            "The initial MLX worker requires macOS Apple Silicon",
        ))
    }
}

#[cfg(test)]
mod tests;
