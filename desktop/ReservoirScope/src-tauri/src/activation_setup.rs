//! Explicit, cancellable preparation of this app's isolated activation runtime.
//! Inspecting this state never spawns a process or starts a download.
use crate::files::{self, AppError};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{
    fs,
    io::{BufRead, BufReader, Read, Write},
    path::{Path, PathBuf},
    process::{Command, Stdio},
    sync::{
        atomic::{AtomicBool, Ordering},
        mpsc, Arc, Mutex,
    },
    thread::{self, JoinHandle},
    time::{Duration, Instant},
};
use tauri::Manager;

type Result<T> = std::result::Result<T, AppError>;
fn error(message: impl std::fmt::Display) -> AppError {
    AppError::new("activation-setup", "preparation", message.to_string())
}
fn prepared_validation_message(detail: impl std::fmt::Display) -> String {
    format!("Prepared installation failed validation: {detail} Prepared files and the readiness receipt are preserved. This is not an interrupted preparation; Resume cannot repair it. Contact the preview maintainer with this diagnostic.")
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SetupStatus {
    pub state: String,
    pub phase: String,
    pub message: String,
    pub downloaded_bytes: Option<u64>,
    pub total_bytes: Option<u64>,
    pub required_bytes: Option<u64>,
    pub python_path: Option<String>,
    pub model_path: Option<String>,
    pub setup_id: Option<String>,
    pub can_resume: bool,
}
impl SetupStatus {
    fn new(state: &str, phase: &str, message: impl Into<String>) -> Self {
        Self {
            state: state.into(),
            phase: phase.into(),
            message: message.into(),
            downloaded_bytes: None,
            total_bytes: None,
            required_bytes: None,
            python_path: None,
            model_path: None,
            setup_id: None,
            can_resume: false,
        }
    }
}
struct Inner {
    root: PathBuf,
    resources: PathBuf,
    driver: PathBuf,
    status: Mutex<SetupStatus>,
    busy: AtomicBool,
    cancel: AtomicBool,
    closing: AtomicBool,
    lifecycle: Mutex<()>,
    join: Mutex<Option<JoinHandle<()>>>,
}
#[derive(Clone)]
pub struct SetupState(Arc<Inner>);

fn json_file(path: &Path) -> Result<Value> {
    serde_json::from_slice(&files::read_bounded(
        path,
        4 * 1024 * 1024,
        "activation-setup",
    )?)
    .map_err(error)
}
fn publish(path: &Path, value: &impl Serialize) -> Result<()> {
    let mut temp =
        tempfile::NamedTempFile::new_in(path.parent().ok_or_else(|| error("Missing parent"))?)
            .map_err(error)?;
    serde_json::to_writer_pretty(&mut temp, value).map_err(error)?;
    temp.write_all(b"\n").map_err(error)?;
    temp.as_file().sync_all().map_err(error)?;
    temp.persist(path).map_err(error)?;
    Ok(())
}
fn child_path(root: &Path, value: &Value, key: &str) -> Result<PathBuf> {
    let relative = value[key]
        .as_str()
        .ok_or_else(|| error(format!("Missing setup field {key}")))?;
    let path = Path::new(relative);
    if path.is_absolute()
        || path
            .components()
            .any(|c| !matches!(c, std::path::Component::Normal(_)))
    {
        return Err(error("Setup asset path must stay within its bundle"));
    }
    Ok(root.join(path))
}
fn hash_file(path: &Path) -> Result<String> {
    let mut file = fs::File::open(path).map_err(error)?;
    let mut h = Sha256::new();
    let mut buffer = [0_u8; 65536];
    loop {
        let n = file.read(&mut buffer).map_err(error)?;
        if n == 0 {
            break;
        }
        h.update(&buffer[..n]);
    }
    Ok(format!("{:x}", h.finalize()))
}
fn ordinary_directory(path: &Path) -> Result<()> {
    if path.exists()
        && !fs::symlink_metadata(path)
            .map_err(error)?
            .file_type()
            .is_dir()
    {
        return Err(error("Setup requires an owned ordinary directory"));
    }
    fs::create_dir_all(path).map_err(error)
}
fn bootstrap_marker_matches(path: &Path, identity: &Value) -> Result<bool> {
    match fs::symlink_metadata(path) {
        Ok(metadata) if metadata.file_type().is_file() => {
            if json_file(path)? != *identity {
                return Err(error("Partial runtime belongs to another manifest"));
            }
            Ok(true)
        }
        Ok(_) => Err(error("Bootstrap ownership requires an ordinary file")),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(false),
        Err(e) => Err(error(e)),
    }
}
fn bootstrap_runtime_directory(root: &Path, runtime_id: &str, identity: &Value) -> Result<PathBuf> {
    if runtime_id.is_empty()
        || matches!(runtime_id, "." | "..")
        || !runtime_id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_.".contains(&b))
    {
        return Err(error("Invalid runtime identity"));
    }
    ordinary_directory(&root.join("runtime"))?;
    let runtime = root.join("runtime").join(runtime_id);
    let runtime_exists = match fs::symlink_metadata(&runtime) {
        Ok(metadata) if metadata.file_type().is_dir() => true,
        Ok(_) => return Err(error("Setup requires an owned ordinary directory")),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => false,
        Err(e) => return Err(error(e)),
    };
    let inner_owner = runtime.join("bootstrap-owner.json");
    let inner_owned = bootstrap_marker_matches(&inner_owner, identity)?;
    let owners = root.join("bootstrap-owners");
    ordinary_directory(&owners)?;
    let sibling_owner = owners.join(format!("{runtime_id}.json"));
    if !bootstrap_marker_matches(&sibling_owner, identity)? {
        // A matching legacy marker can establish ownership without changing a
        // qualified environment. Never adopt an arbitrary existing directory.
        if runtime_exists && !inner_owned {
            return Err(error(
                "Runtime destination contains unowned files; nothing was overwritten",
            ));
        }
        publish(&sibling_owner, identity)?;
    }
    #[cfg(unix)]
    {
        fs::File::open(&owners)
            .map_err(error)?
            .sync_all()
            .map_err(error)?;
        fs::File::open(root)
            .map_err(error)?
            .sync_all()
            .map_err(error)?;
    }
    // The durable sibling marker precedes mkdir. A stopped extraction or an
    // interrupted inner-marker write can therefore resume without deleting data.
    ordinary_directory(&runtime)?;
    if !inner_owned {
        publish(&inner_owner, identity)?;
    }
    Ok(runtime)
}
fn platform_version_supported(is_macos_arm64: bool, version: &str) -> bool {
    is_macos_arm64
        && version
            .trim_end_matches('\0')
            .split('.')
            .next()
            .and_then(|s| s.parse::<u32>().ok())
            .is_some_and(|v| v >= 26)
}
fn platform_supported() -> bool {
    if !cfg!(all(target_os = "macos", target_arch = "aarch64")) {
        return false;
    }
    // sysctl is a read-only platform observation; status does not spawn a child.
    #[cfg(target_os = "macos")]
    unsafe {
        let mut bytes = [0_u8; 64];
        let mut size = bytes.len();
        if libc::sysctlbyname(
            c"kern.osproductversion".as_ptr(),
            bytes.as_mut_ptr().cast(),
            &mut size,
            std::ptr::null_mut(),
            0,
        ) == 0
        {
            return platform_version_supported(
                true,
                &String::from_utf8_lossy(&bytes[..size.min(bytes.len())]),
            );
        }
    }
    false
}
fn require_disk(root: &Path, minimum: u64) -> Result<()> {
    #[cfg(unix)]
    {
        use std::os::unix::ffi::OsStrExt;
        let path = std::ffi::CString::new(root.as_os_str().as_bytes()).map_err(error)?;
        let mut stats: libc::statvfs = unsafe { std::mem::zeroed() };
        if unsafe { libc::statvfs(path.as_ptr(), &mut stats) } != 0 {
            return Err(error(std::io::Error::last_os_error()));
        }
        let available = stats.f_bavail as u128 * stats.f_frsize as u128;
        if available < minimum as u128 {
            return Err(error(format!("Runtime preparation requires at least {minimum} bytes of free storage; {available} are available. Free storage, then try again.")));
        }
    }
    #[cfg(not(unix))]
    {
        let _ = (root, minimum);
    }
    Ok(())
}

fn exited_without_reaping(child: &mut std::process::Child) -> std::io::Result<bool> {
    #[cfg(unix)]
    unsafe {
        let mut info: libc::siginfo_t = std::mem::zeroed();
        if libc::waitid(
            libc::P_PID,
            child.id() as libc::id_t,
            &mut info,
            libc::WEXITED | libc::WNOHANG | libc::WNOWAIT,
        ) != 0
        {
            return Err(std::io::Error::last_os_error());
        }
        Ok(info.si_pid() != 0)
    }
    #[cfg(not(unix))]
    {
        child.try_wait().map(|status| status.is_some())
    }
}
fn terminate(child: &mut std::process::Child) -> std::io::Result<std::process::ExitStatus> {
    #[cfg(unix)]
    unsafe {
        libc::kill(-(child.id() as i32), libc::SIGKILL);
    }
    #[cfg(not(unix))]
    {
        let _ = child.kill();
    }
    child.wait()
}

impl SetupState {
    pub fn new(root: PathBuf, resources: PathBuf, driver: PathBuf) -> Self {
        let mut status = SetupStatus::new("missing", "idle", "Prepare the local runtime to run an activation experiment. Reading examples needs no download.");
        if let Ok(saved) =
            files::read_bounded(&root.join("setup-status.json"), 65536, "activation-setup")
        {
            if let Ok(mut prior) = serde_json::from_slice::<SetupStatus>(&saved) {
                if prior.state == "preparing" {
                    prior.state = "interrupted".into();
                    prior.message =
                        "Preparation was interrupted. Resume explicitly to continue.".into();
                    prior.can_resume = true;
                }
                status = prior;
            }
        }
        Self(Arc::new(Inner {
            root,
            resources,
            driver,
            status: Mutex::new(status),
            busy: AtomicBool::new(false),
            cancel: AtomicBool::new(false),
            closing: AtomicBool::new(false),
            lifecycle: Mutex::new(()),
            join: Mutex::new(None),
        }))
    }
    pub fn is_busy(&self) -> bool {
        self.0.busy.load(Ordering::SeqCst)
    }
    fn manifest(&self) -> Result<Value> {
        let manifest = json_file(&self.0.resources.join("setup-manifest.json"))?;
        if manifest["schema"] != "activation-setup-manifest-v1" {
            return Err(error("Unsupported setup manifest"));
        }
        Ok(manifest)
    }
    pub fn ready_paths(&self) -> Result<Option<(String, String)>> {
        if !self.0.root.join("ready.json").exists() {
            return Ok(None);
        }
        let manifest = self.manifest()?;
        let receipt = json_file(&self.0.root.join("ready.json"))?;
        if receipt["schema"] != "activation-setup-ready-v1"
            || receipt["runtimeId"] != manifest["runtimeId"]
            || receipt["manifestSha256"].as_str()
                != Some(hash_file(&self.0.resources.join("setup-manifest.json"))?.as_str())
        {
            return Err(error(
                "The installed runtime belongs to a different preview.",
            ));
        }
        let root = self.0.root.canonicalize().map_err(error)?;
        let model_spec = json_file(&child_path(
            &self.0.resources,
            &manifest["locks"]["model"],
            "path",
        )?)?;
        let expected_python = root
            .join("runtime")
            .join(
                manifest["runtimeId"]
                    .as_str()
                    .ok_or_else(|| error("Missing runtime identity"))?,
            )
            .join("venv/bin/python");
        let expected_model = root.join("models").join(
            model_spec["revision"]
                .as_str()
                .ok_or_else(|| error("Missing model revision"))?,
        );
        let mut paths = Vec::new();
        for key in ["pythonPath", "modelPath"] {
            let path = PathBuf::from(
                receipt[key]
                    .as_str()
                    .ok_or_else(|| error("Readiness receipt omits a path"))?,
            );
            if path.as_path()
                != if key == "pythonPath" {
                    expected_python.as_path()
                } else {
                    expected_model.as_path()
                }
            {
                return Err(error(
                    "Readiness paths differ from this preview's declared runtime and model",
                ));
            }
            if !path.is_absolute() || !path.canonicalize().map_err(error)?.starts_with(&root) {
                return Err(error(
                    "Installed runtime path leaves this app's setup directory",
                ));
            }
            paths.push(path.to_string_lossy().into_owned());
        }
        if !Path::new(&paths[0]).is_file()
            || !Path::new(&paths[1]).join("model-provenance.json").is_file()
        {
            return Err(error("Installed runtime or model files are missing."));
        }
        Ok(Some((paths.remove(0), paths.remove(0))))
    }
    pub fn status(&self) -> SetupStatus {
        if !platform_supported() {
            return SetupStatus::new("unsupported", "platform", "Activation requires Apple Silicon and macOS 26 or later. Offline examples remain available.");
        }
        let mut status = self.0.status.lock().unwrap().clone();
        if let Ok(manifest) = self.manifest() {
            status.required_bytes = manifest["minimumFreeBytes"].as_u64();
            status.setup_id = manifest["runtimeId"].as_str().map(str::to_owned);
        }
        if !self.is_busy() {
            match self.ready_paths() {
                Ok(Some((python, model))) => {
                    status.state = "ready".into();
                    status.phase = "ready".into();
                    status.message =
                        "Runtime prepared. Check setup, create a session, then choose Start."
                            .into();
                    status.python_path = Some(python);
                    status.model_path = Some(model);
                    status.can_resume = false;
                }
                Err(e) => {
                    status.state = "failed".into();
                    status.message = prepared_validation_message(e.message);
                    status.python_path = None;
                    status.model_path = None;
                    status.can_resume = false;
                }
                Ok(None) => {
                    if status.state == "ready" {
                        status.state = "interrupted".into();
                        status.message =
                            "The readiness receipt is missing. Resume preparation explicitly."
                                .into();
                        status.can_resume = true;
                    }
                }
            }
        }
        status
    }
    fn update(&self, mut status: SetupStatus) -> Result<()> {
        let result = publish(&self.0.root.join("setup-status.json"), &status);
        if let Err(e) = &result {
            status.message = format!(
                "{} Status could not be saved: {}",
                status.message, e.message
            );
        }
        *self.0.status.lock().unwrap() = status;
        result
    }
    pub fn prepare(&self, resume: bool) -> Result<SetupStatus> {
        let _lifecycle = self.0.lifecycle.lock().unwrap();
        if self.0.closing.load(Ordering::SeqCst) || self.is_busy() {
            return Err(error("Preparation is already active or the app is closing"));
        }
        let prior = self.status();
        if prior.state == "unsupported" {
            return Err(error(prior.message));
        }
        if prior.state == "ready" {
            return Ok(prior);
        }
        if self.0.root.join("ready.json").exists() {
            return Err(error(prior.message));
        }
        if prior.can_resume && !resume {
            return Err(error("Choose Resume to continue retained preparation"));
        }
        let manifest = self.manifest()?;
        ordinary_directory(&self.0.root)?;
        require_disk(
            &self.0.root,
            manifest["minimumFreeBytes"]
                .as_u64()
                .ok_or_else(|| error("Missing storage requirement"))?,
        )?;
        let mut status = SetupStatus::new(
            "preparing",
            "bootstrap",
            "Preparing the isolated Python runtime…",
        );
        status.required_bytes = manifest["minimumFreeBytes"].as_u64();
        status.setup_id = manifest["runtimeId"].as_str().map(str::to_owned);
        self.update(status)?;
        if let Some(join) = self.0.join.lock().unwrap().take() {
            let _ = join.join();
        }
        self.0.cancel.store(false, Ordering::SeqCst);
        self.0.busy.store(true, Ordering::SeqCst);
        let owned = self.clone();
        let join = thread::spawn(move || {
            let result = owned.run(&manifest);
            let mut final_status = owned.0.status.lock().unwrap().clone();
            if let Err(e) = result {
                final_status.state = if owned.0.cancel.load(Ordering::SeqCst) {
                    "interrupted"
                } else {
                    "failed"
                }
                .into();
                final_status.message = e.message;
                final_status.can_resume = true;
                let _ = owned.update(final_status);
            }
            owned.0.busy.store(false, Ordering::SeqCst);
        });
        *self.0.join.lock().unwrap() = Some(join);
        Ok(self.status())
    }
    fn run(&self, manifest: &Value) -> Result<()> {
        let deadline = Instant::now() + Duration::from_secs(1800);
        let runtime_id = manifest["runtimeId"]
            .as_str()
            .ok_or_else(|| error("Missing runtime identity"))?;
        let identity = serde_json::json!({"schema":"activation-bootstrap-owner-v1","manifestSha256":hash_file(&self.0.resources.join("setup-manifest.json"))?});
        let runtime = bootstrap_runtime_directory(&self.0.root, runtime_id, &identity)?;
        let archive = child_path(&self.0.resources, &manifest["python"], "archivePath")?;
        if hash_file(&archive)? != manifest["python"]["archiveSha256"].as_str().unwrap_or("") {
            return Err(error("Bundled Python archive hash differs"));
        }
        let python = child_path(&runtime, &manifest["python"], "executableRelativePath")?;
        if !runtime.join("bootstrap-complete.json").exists() {
            let mut command = Command::new("/usr/bin/tar");
            command.args(["-xzf"]).arg(&archive).arg("-C").arg(&runtime);
            self.process(command, deadline, false)?;
            if !python.is_file() {
                return Err(error(
                    "The extracted archive lacks its declared interpreter",
                ));
            }
            publish(&runtime.join("bootstrap-complete.json"), &identity)?;
        } else if json_file(&runtime.join("bootstrap-complete.json"))? != identity {
            return Err(error("Bootstrap completion identity differs"));
        }
        let mut command = Command::new(&python);
        command
            .arg("-I")
            .arg("-B")
            .arg(&self.0.driver)
            .arg("--setup-root")
            .arg(&self.0.root)
            .arg("--resources")
            .arg(&self.0.resources)
            .arg("--parent-pid")
            .arg(std::process::id().to_string())
            .arg("--mode")
            .arg("prepare");
        self.process(command, deadline, true)?;
        let (python, model) = self
            .ready_paths()?
            .ok_or_else(|| error("Preparation ended without a verified readiness receipt"))?;
        let mut status = self.0.status.lock().unwrap().clone();
        status.state = "ready".into();
        status.phase = "ready".into();
        status.message =
            "Runtime preparation completed. Check setup before creating a session.".into();
        status.can_resume = false;
        status.python_path = Some(python);
        status.model_path = Some(model);
        self.update(status)
    }
    fn progress(&self, line: &str) -> Result<Option<String>> {
        let Ok(value) = serde_json::from_str::<Value>(line) else {
            return Ok(None);
        };
        if value["schema"] != "activation-setup-progress-v1" {
            return Ok(None);
        }
        let mut status = self.0.status.lock().unwrap().clone();
        if let Some(phase) = value["phase"].as_str() {
            status.phase = phase.into();
            status.message = match phase {
                "environment" => "Installing the pinned Python dependencies…",
                "model" => "Downloading and checking the pinned Qwen3 model…",
                "verification" => "Verifying the complete runtime and model…",
                "ready" => "Preparation verified; finishing local receipts…",
                _ => "Preparing the isolated activation runtime…",
            }
            .into();
        }
        let diagnostic = value["diagnostic"]
            .as_str()
            .map(|s| s.chars().take(12000).collect::<String>());
        if let Some(message) = diagnostic.as_deref().or_else(|| value["message"].as_str()) {
            status.message = message.into();
        }
        if let Some(file) = value["file"].as_str() {
            status.message = format!("{} Current file: {file}.", status.message);
        }
        status.downloaded_bytes = value["downloadedBytes"].as_u64();
        status.total_bytes = value["totalBytes"].as_u64();
        self.update(status)?;
        Ok(diagnostic)
    }
    fn process(&self, mut command: Command, deadline: Instant, progress: bool) -> Result<()> {
        if self.0.cancel.load(Ordering::SeqCst) {
            return Err(error(
                "Preparation cancelled; retained files can be resumed explicitly",
            ));
        }
        command
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::from(
                fs::OpenOptions::new()
                    .create(true)
                    .append(true)
                    .open(self.0.root.join("setup-stderr.txt"))
                    .map_err(error)?,
            ))
            .env("PYTHONDONTWRITEBYTECODE", "1")
            .env("PYTHONNOUSERSITE", "1");
        #[cfg(unix)]
        {
            use std::os::unix::process::CommandExt;
            command.process_group(0);
        }
        let mut child = command.spawn().map_err(error)?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| error("Missing preparation output"))?;
        let (tx, rx) = mpsc::sync_channel(32);
        let reader = thread::spawn(move || {
            let mut source = BufReader::new(stdout);
            loop {
                let mut line = String::new();
                match source.by_ref().take(65537).read_line(&mut line) {
                    Ok(0) | Err(_) => break,
                    Ok(_) => {}
                }
                if line.len() > 65536 {
                    break;
                }
                if tx.send(line).is_err() {
                    break;
                }
            }
        });
        let mut diagnostic = None;
        let result = 'supervisor: loop {
            let cancelled = self.0.cancel.load(Ordering::SeqCst);
            if cancelled || Instant::now() >= deadline {
                let _ = terminate(&mut child);
                break Err(error(if cancelled {
                    "Preparation cancelled. Retained files require explicit Resume."
                } else {
                    "Preparation reached its 30-minute deadline. Retained files require explicit Resume."
                }));
            }
            while let Ok(line) = rx.try_recv() {
                if progress {
                    match self.progress(&line) {
                        Ok(Some(detail)) => diagnostic = Some(detail),
                        Ok(None) => {}
                        Err(e) => {
                            let _ = terminate(&mut child);
                            break 'supervisor Err(e);
                        }
                    }
                }
            }
            match exited_without_reaping(&mut child) {
                Ok(true) => {
                    // WNOWAIT pins the leader PID until every remaining group member
                    // has been signalled. A crashed driver cannot strand its installer.
                    let status = match terminate(&mut child) {
                        Ok(status) => status,
                        Err(e) => break Err(error(e)),
                    };
                    // Drain through EOF: the final diagnostic can race process exit.
                    while let Ok(line) = rx.recv_timeout(Duration::from_secs(1)) {
                        if progress {
                            match self.progress(&line) {
                                Ok(Some(detail)) => diagnostic = Some(detail),
                                Ok(None) => {}
                                Err(e) => break 'supervisor Err(e),
                            }
                        }
                    }
                    break if status.success() {
                        Ok(())
                    } else {
                        Err(error(diagnostic.unwrap_or_else(|| format!("Preparation stopped ({status}). Resume explicitly or inspect the retained setup diagnostic."))))
                    };
                }
                Ok(false) => thread::sleep(Duration::from_millis(100)),
                Err(e) => {
                    let _ = terminate(&mut child);
                    break Err(error(e));
                }
            }
        };
        drop(rx);
        let _ = reader.join();
        result
    }
    pub fn cancel(&self) -> SetupStatus {
        let _lifecycle = self.0.lifecycle.lock().unwrap();
        self.0.cancel.store(true, Ordering::SeqCst);
        if let Some(join) = self.0.join.lock().unwrap().take() {
            let _ = join.join();
        }
        self.status()
    }
    pub fn request_close(&self) {
        self.0.closing.store(true, Ordering::SeqCst);
        self.cancel();
    }
    pub fn cancel_close(&self) {
        self.0.closing.store(false, Ordering::SeqCst);
    }
}

#[tauri::command]
pub fn activation_setup_status(state: tauri::State<'_, SetupState>) -> SetupStatus {
    state.status()
}
#[tauri::command]
pub async fn activation_setup_prepare(
    app: tauri::AppHandle,
    state: tauri::State<'_, SetupState>,
    resume: bool,
) -> Result<SetupStatus> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        let admission = app.state::<crate::execution_admission::ExecutionAdmission>();
        let _gate = admission.0.lock().map_err(error)?;
        if app.state::<crate::activation::ActivationState>().is_busy()
            || app
                .state::<crate::sessions::SessionState>()
                .execution_busy()
            || app.state::<crate::sustained::SustainedState>().is_busy()
        {
            return Err(error(
                "Stop the running experiment before preparing the runtime",
            ));
        }
        state.prepare(resume)
    })
    .await
    .map_err(error)?
}
#[tauri::command]
pub async fn activation_setup_cancel(state: tauri::State<'_, SetupState>) -> Result<SetupStatus> {
    let state = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || state.cancel())
        .await
        .map_err(error)
}

#[cfg(test)]
mod tests;
