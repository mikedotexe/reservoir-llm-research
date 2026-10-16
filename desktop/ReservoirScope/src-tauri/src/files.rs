use serde::Serialize;
use sha2::{Digest, Sha256};
use std::{
    fs,
    io::{Read, Seek, SeekFrom, Write},
    path::{Path, PathBuf},
};

pub const MAX_PROOF_BYTES: u64 = 256 * 1024 * 1024;

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AppError {
    pub operation: String,
    pub category: String,
    pub message: String,
}

impl AppError {
    pub fn new(operation: &str, category: &str, message: impl Into<String>) -> Self {
        Self {
            operation: operation.into(),
            category: category.into(),
            message: message.into(),
        }
    }
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct FileProof {
    pub name: String,
    pub size_bytes: u64,
    pub sha256: String,
}

pub fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

pub fn app_data_path(default: PathBuf) -> Result<PathBuf, AppError> {
    match std::env::var_os("RESERVOIR_SCOPE_TAURI_LIBRARY") {
        None => Ok(default),
        Some(value) => isolated_path(PathBuf::from(value)),
    }
}

fn isolated_path(path: PathBuf) -> Result<PathBuf, AppError> {
    if !path.is_absolute() {
        return Err(AppError::new(
            "app-data",
            "invalid-override",
            "RESERVOIR_SCOPE_TAURI_LIBRARY must be an absolute local path.",
        ));
    }
    Ok(path)
}

pub fn read_bounded(path: &Path, limit: u64, operation: &str) -> Result<Vec<u8>, AppError> {
    let error = |e: std::io::Error| AppError::new(operation, "file-io", e.to_string());
    let entry = fs::symlink_metadata(path).map_err(error)?;
    if !entry.file_type().is_file() || entry.len() > limit {
        return Err(AppError::new(
            operation,
            "file-bound",
            format!("Choose a regular file no larger than {limit} bytes. Symlinks are not read."),
        ));
    }
    let mut options = fs::OpenOptions::new();
    options.read(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        // Refuse a link introduced after lstat; a replaced FIFO must not block.
        options.custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK);
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt;
        // FILE_FLAG_OPEN_REPARSE_POINT: inspect the link itself rather than following it.
        options.custom_flags(0x0020_0000);
    }
    let file = options.open(path).map_err(error)?;
    let before = file.metadata().map_err(error)?;
    if !before.is_file() || before.file_type().is_symlink() || before.len() > limit {
        return Err(AppError::new(
            operation,
            "file-bound",
            "The selected file is not within the size bound.",
        ));
    }
    let mut bytes = Vec::new();
    (&file)
        .take(limit + 1)
        .read_to_end(&mut bytes)
        .map_err(error)?;
    let after = file.metadata().map_err(error)?;
    if bytes.len() as u64 > limit
        || before.len() != bytes.len() as u64
        || before.len() != after.len()
        || before.modified().ok() != after.modified().ok()
    {
        return Err(AppError::new(
            operation,
            "changed-file",
            "The file changed during its bounded read. Choose a stable snapshot.",
        ));
    }
    Ok(bytes)
}

fn proof(path: &Path, bytes: &[u8]) -> FileProof {
    FileProof {
        name: path
            .file_name()
            .unwrap_or_default()
            .to_string_lossy()
            .into(),
        size_bytes: bytes.len() as u64,
        sha256: digest(bytes),
    }
}

pub fn inspect_file(path: &Path) -> Result<FileProof, AppError> {
    let bytes = read_bounded(path, MAX_PROOF_BYTES, "open-file")?;
    Ok(proof(path, &bytes))
}

fn verify_export_handle(file: &mut fs::File, expected: &[u8]) -> Result<(), AppError> {
    let error = |e: std::io::Error| AppError::new("save-file", "verify", e.to_string());
    file.seek(SeekFrom::Start(0)).map_err(error)?;
    let mut buffer = [0u8; 65536];
    for chunk in expected.chunks(buffer.len()) {
        file.read_exact(&mut buffer[..chunk.len()]).map_err(error)?;
        if &buffer[..chunk.len()] != chunk {
            return Err(AppError::new(
                "save-file",
                "verify",
                "The selected export differs from its source bytes. The file was retained for inspection.",
            ));
        }
    }
    if file.read(&mut buffer[..1]).map_err(error)? != 0 {
        return Err(AppError::new(
            "save-file",
            "verify",
            "The selected export has unexpected trailing bytes. The file was retained for inspection.",
        ));
    }
    Ok(())
}

fn write_selected_export(file: &mut fs::File, bytes: &[u8]) -> Result<(), AppError> {
    file.write_all(bytes)
        .and_then(|_| file.sync_all())
        .map_err(|e| AppError::new("save-file", "write", e.to_string()))?;
    verify_export_handle(file, bytes)
}

/// Publish immutable external evidence using only the file selected in the save
/// panel. Opening its parent directory can request a broader macOS permission and
/// block after the chosen file was saved. Internal evidence publication retains
/// its separate directory-sync contract.
pub fn selected_file_export(path: &Path, bytes: &[u8]) -> Result<FileProof, AppError> {
    if !path.is_absolute() || path.file_name().is_none() {
        return Err(AppError::new(
            "save-file",
            "destination",
            "Choose an absolute local destination with a filename.",
        ));
    }
    if bytes.len() as u64 > MAX_PROOF_BYTES {
        return Err(AppError::new(
            "save-file",
            "file-bound",
            "The activation export exceeds its 256 MiB file bound.",
        ));
    }
    let mut options = fs::OpenOptions::new();
    options.read(true).write(true).create_new(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK);
    }
    match options.open(path) {
        Ok(mut file) => write_selected_export(&mut file, bytes)?,
        Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => {
            // Keep the existing immutable-export behavior: identical bytes are
            // idempotent; a different file is never truncated or replaced.
            if read_bounded(path, MAX_PROOF_BYTES, "save-file")? != bytes {
                return Err(AppError::new(
                    "save-file",
                    "collision",
                    "The selected file already contains different bytes. Choose a new export filename.",
                ));
            }
        }
        Err(e) => return Err(AppError::new("save-file", "create", e.to_string())),
    }
    Ok(proof(path, bytes))
}

pub fn atomic_export(
    path: &Path,
    bytes: &[u8],
    resource_root: &Path,
) -> Result<FileProof, AppError> {
    let parent = path.parent().filter(|p| p.is_absolute()).ok_or_else(|| {
        AppError::new(
            "save-file",
            "destination",
            "Choose an absolute local destination.",
        )
    })?;
    let parent = parent
        .canonicalize()
        .map_err(|e| AppError::new("save-file", "destination", e.to_string()))?;
    if let Ok(resources) = resource_root.canonicalize() {
        if parent.starts_with(resources) {
            return Err(AppError::new(
                "save-file",
                "destination",
                "Bundled reference resources are read-only. Choose a different destination.",
            ));
        }
    }
    let name = path
        .file_name()
        .ok_or_else(|| AppError::new("save-file", "destination", "Choose a filename."))?;
    let destination = parent.join(name);
    if let Ok(metadata) = fs::symlink_metadata(&destination) {
        if !metadata.file_type().is_file() {
            return Err(AppError::new(
                "save-file",
                "destination",
                "The destination must be a regular file, not a link or directory.",
            ));
        }
    }
    let mut temporary = tempfile::NamedTempFile::new_in(&parent)
        .map_err(|e| AppError::new("save-file", "create", e.to_string()))?;
    temporary
        .write_all(bytes)
        .and_then(|_| temporary.as_file().sync_all())
        .map_err(|e| AppError::new("save-file", "write", e.to_string()))?;
    temporary
        .persist(&destination)
        .map_err(|e| AppError::new("save-file", "publish", e.to_string()))?;
    Ok(proof(&destination, bytes))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bounded_snapshot_and_exact_export() {
        let dir = tempfile::tempdir().unwrap();
        let source = dir.path().join("source.json");
        let original = b"{\"seed\":18446744073709551615,\"text\":\"unchanged\"}\n";
        fs::write(&source, original).unwrap();
        assert!(read_bounded(&source, 2, "test").is_err());
        let bytes = read_bounded(&source, 1024, "test").unwrap();
        let target = dir.path().join("copy.json");
        let result = atomic_export(&target, &bytes, &dir.path().join("resources")).unwrap();
        assert_eq!(fs::read(target).unwrap(), original);
        assert_eq!(result.sha256, digest(original));
    }

    #[test]
    fn selected_export_verifies_exact_bytes_and_preserves_existing_files() {
        let dir = tempfile::tempdir().unwrap();
        let target = dir.path().join("activation.json");
        let bytes = b"{\"text\":\"Complete retained writing.\\n\"}\n";
        let proof = selected_file_export(&target, bytes).unwrap();
        assert_eq!(proof.sha256, digest(bytes));
        assert_eq!(proof.size_bytes, bytes.len() as u64);
        assert_eq!(fs::read(&target).unwrap(), bytes);
        assert!(selected_file_export(&target, bytes).is_ok());
        assert_eq!(
            selected_file_export(&target, b"different")
                .unwrap_err()
                .category,
            "collision"
        );
        assert_eq!(fs::read(&target).unwrap(), bytes);
        assert!(selected_file_export(Path::new("relative.json"), bytes).is_err());
        assert!(selected_file_export(dir.path(), bytes).is_err());
    }

    #[test]
    fn export_readback_rejects_changed_truncated_and_extended_bytes() {
        let dir = tempfile::tempdir().unwrap();
        let target = dir.path().join("readback.json");
        for actual in [b"wrong".as_slice(), b"ex", b"exact plus extra"] {
            fs::write(&target, actual).unwrap();
            let mut file = fs::File::open(&target).unwrap();
            assert_eq!(
                verify_export_handle(&mut file, b"exact")
                    .unwrap_err()
                    .category,
                "verify"
            );
            assert_eq!(fs::read(&target).unwrap(), actual);
        }
    }

    #[cfg(unix)]
    #[test]
    fn selected_export_write_and_readback_need_no_parent_path_access() {
        let dir = tempfile::tempdir().unwrap();
        let parent = dir.path().join("chosen-parent");
        fs::create_dir(&parent).unwrap();
        let path = parent.join("selected.json");
        let mut file = fs::OpenOptions::new()
            .read(true)
            .write(true)
            .create_new(true)
            .open(&path)
            .unwrap();
        let moved = dir.path().join("moved-parent");
        fs::rename(&parent, &moved).unwrap();
        assert!(!parent.exists());
        let bytes = b"Selected file remains usable after its parent pathname disappears.\n";
        // This helper receives only the selected handle, so it cannot reopen the
        // original file or parent path for sync or readback.
        write_selected_export(&mut file, bytes).unwrap();
        assert_eq!(fs::read(moved.join("selected.json")).unwrap(), bytes);
    }

    #[test]
    fn cannot_overwrite_resources_or_accept_relative_override() {
        let dir = tempfile::tempdir().unwrap();
        assert!(atomic_export(&dir.path().join("scene.json"), b"[]", dir.path()).is_err());
        assert!(isolated_path(PathBuf::from("relative-library")).is_err());
        assert_eq!(isolated_path(dir.path().to_owned()).unwrap(), dir.path());
        assert!(read_bounded(dir.path(), 1024, "test").is_err());
    }

    #[cfg(unix)]
    #[test]
    fn refuses_symbolic_links() {
        let dir = tempfile::tempdir().unwrap();
        let source = dir.path().join("source");
        let link = dir.path().join("link");
        fs::write(&source, b"original").unwrap();
        std::os::unix::fs::symlink(&source, &link).unwrap();
        assert!(inspect_file(&link).is_err());
        assert!(atomic_export(&link, b"replacement", &dir.path().join("resources")).is_err());
        assert!(selected_file_export(&link, b"original").is_err());
        assert_eq!(fs::read(source).unwrap(), b"original");
    }
}
