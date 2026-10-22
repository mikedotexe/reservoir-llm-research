use crate::files::{self, AppError};
use serde::{Deserialize, Serialize};
use std::path::Path;

// Expected identities are compiled into the application, not trusted from a mutable sidecar.
const INDEX: &[u8] = include_bytes!("../resources/resource-index.json");

pub fn index_identity() -> String {
    files::digest(INDEX)
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct Index {
    schema: String,
    baseline_commit: String,
    reference_manifest_sha256: String,
    reference_scenes_sha256: String,
    resources: Vec<Resource>,
}

#[derive(Deserialize)]
struct Resource {
    name: String,
    sha256: String,
    bytes: u64,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BuildInfo {
    app_name: &'static str,
    version: &'static str,
    milestone: &'static str,
    platform: &'static str,
    arch: &'static str,
    resource_status: &'static str,
    source_identity: String,
    app_data_dir: String,
    resources: Vec<ResourceStatus>,
}

#[derive(Serialize)]
pub struct ResourceStatus {
    name: String,
    sha256: String,
    status: String,
}

#[derive(Serialize, Deserialize)]
pub struct ReferenceScenes {
    pub scenes: Vec<ReferenceScene>,
}

#[derive(Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ReferenceScene {
    id: String,
    title: String,
    node_count: usize,
    description: String,
    provenance: String,
    values: Vec<f64>,
    source_path: String,
    source_sha256: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    step: Option<u64>,
}

fn index() -> Result<Index, AppError> {
    let index: Index = serde_json::from_slice(INDEX)
        .map_err(|e| AppError::new("resources", "manifest", e.to_string()))?;
    if index.schema != "reservoir-scope.resource-index.v1" {
        return Err(AppError::new(
            "resources",
            "manifest",
            "Unsupported resource-index format.",
        ));
    }
    for entry in &index.resources {
        if Path::new(&entry.name).file_name().and_then(|n| n.to_str()) != Some(&entry.name)
            || entry.name.contains(['/', '\\'])
            || entry.name == ".."
        {
            return Err(AppError::new(
                "resources",
                "manifest",
                "Resource names must be plain filenames.",
            ));
        }
    }
    Ok(index)
}

fn checked(root: &Path, name: &str, expected: &str, limit: u64) -> Result<Vec<u8>, AppError> {
    let bytes = files::read_bounded(&root.join(name), limit, "resources")?;
    if files::digest(&bytes) != expected {
        return Err(AppError::new(
            "resources",
            "hash-mismatch",
            format!("Bundled {name} does not match this executable’s resource identity."),
        ));
    }
    Ok(bytes)
}

fn statuses(root: &Path, index: &Index) -> Vec<ResourceStatus> {
    let mut resources: Vec<(&str, &str, u64)> = index
        .resources
        .iter()
        .map(|r| (r.name.as_str(), r.sha256.as_str(), r.bytes))
        .collect();
    resources.push((
        "reference-manifest.json",
        &index.reference_manifest_sha256,
        4 * 1024 * 1024,
    ));
    resources.push((
        "reference-scenes.json",
        &index.reference_scenes_sha256,
        1024 * 1024,
    ));
    resources
        .iter()
        .map(|(name, hash, limit)| ResourceStatus {
            name: (*name).into(),
            sha256: (*hash).into(),
            status: match checked(root, name, hash, *limit) {
                Ok(_) => "hash matched".into(),
                Err(e) => e.message,
            },
        })
        .collect()
}

pub fn build_info(root: &Path, data: &Path) -> Result<BuildInfo, AppError> {
    let index = index()?;
    let resources = statuses(root, &index);
    let valid = resources.iter().all(|r| r.status == "hash matched");
    Ok(BuildInfo {
        app_name: "Reservoir Scope",
        version: env!("CARGO_PKG_VERSION"),
        milestone:
            "Offline research and finite experiments · partial M1–M4; desktop parity is not yet qualified",
        platform: std::env::consts::OS,
        arch: std::env::consts::ARCH,
        resource_status: if valid {
            "Bundled reference hashes match. Numerical replay is a separate check."
        } else {
            "Some bundled resources are unavailable or changed. Reference viewing is disabled."
        },
        source_identity: index.baseline_commit,
        app_data_dir: data.to_string_lossy().into(),
        resources,
    })
}

/// Only explicit catalog identities can resolve into bundled paths.
pub fn record_example(root: &Path, id: &str) -> Result<(String, Vec<u8>), AppError> {
    let name = match id {
        "stage-1" => "essentials-stage-1.json",
        "stage-2" => "essentials-stage-2.json",
        "stage-3" => "essentials-stage-3.json",
        "stage-4" => "essentials-stage-4.json",
        "component-1" => "example-component-1.json",
        "component-2" => "example-component-2.json",
        "component-3" => "example-component-3.json",
        "component-4" => "example-component-4.json",
        "component-5" => "example-component-5.json",
        "component-6" => "example-component-6.json",
        "component-7" => "example-component-7.json",
        "component-8" => "example-component-8.json",
        "observation-active-scripted" => "example-observation-active-scripted.json",
        "observation-scripted" => "example-observation-scripted.json",
        "regulation-controller" => "example-regulation-controller.json",
        "example-model-observation-active" => "example-model-observation-active.json",
        "example-model-observation" => "example-model-observation.json",
        "example-preparation-1" => "example-preparation-1.json",
        "example-preparation-2" => "example-preparation-2.json",
        "example-preparation-3" => "example-preparation-3.json",
        "example-preparation-4" => "example-preparation-4.json",
        "example-model-4" => "example-model-4.json",
        "example-model-5" => "example-model-5.json",
        "example-model-6" => "example-model-6.json",
        "example-model-7" => "example-model-7.json",
        "example-model-8" => "example-model-8.json",
        _ => {
            return Err(AppError::new(
                "open-record",
                "example",
                "Unknown bundled example.",
            ))
        }
    };
    Ok((name.into(), catalog_bytes(root, name)?))
}

/// Resolve only a name compiled into this build's resource index; no input path
/// or historical source reference can escape the immutable bundle catalog.
pub fn catalog_bytes(root: &Path, name: &str) -> Result<Vec<u8>, AppError> {
    let index = index()?;
    let resource = index
        .resources
        .iter()
        .find(|r| r.name == name)
        .ok_or_else(|| {
            AppError::new(
                "open-record",
                "resource",
                "Example is absent from this build.",
            )
        })?;
    checked(root, name, &resource.sha256, resource.bytes)
}

pub fn reference_scene_bytes(root: &Path) -> Result<Vec<u8>, AppError> {
    let index = index()?;
    if statuses(root, &index)
        .iter()
        .any(|r| r.status != "hash matched")
    {
        return Err(AppError::new("reference-scenes", "resource-integrity", "Bundled reference verification failed. Inspect resource status; no substitute scene will be shown."));
    }
    checked(
        root,
        "reference-scenes.json",
        &index.reference_scenes_sha256,
        1024 * 1024,
    )
}

pub fn reference_scenes(root: &Path) -> Result<ReferenceScenes, AppError> {
    let bytes = reference_scene_bytes(root)?;
    let scenes: ReferenceScenes = serde_json::from_slice(&bytes)
        .map_err(|e| AppError::new("reference-scenes", "decode", e.to_string()))?;
    if scenes.scenes.len() != 2
        || scenes.scenes.iter().any(|s| {
            ![32, 128].contains(&s.node_count)
                || s.values.len() != s.node_count
                || s.values.iter().any(|v| !v.is_finite())
        })
    {
        return Err(AppError::new(
            "reference-scenes",
            "dimensions",
            "Expected finite 32-coordinate and 128-coordinate reference scenes.",
        ));
    }
    Ok(scenes)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn root() -> std::path::PathBuf {
        Path::new(env!("CARGO_MANIFEST_DIR")).join("resources")
    }

    #[test]
    fn packaged_reference_values_have_declared_identity() {
        let scenes = reference_scenes(&root()).unwrap();
        assert_eq!(
            scenes
                .scenes
                .iter()
                .map(|s| s.node_count)
                .collect::<Vec<_>>(),
            vec![32, 128]
        );
        assert_eq!(scenes.scenes[0].values[0], 0.028602939487182236);
        // This value rounds by one ULP without serde_json's float_roundtrip feature.
        // Test this package alone too: workspace feature unification can mask the bug.
        assert_eq!(
            scenes.scenes[0].values[1].to_bits(),
            0.027976834027714854_f64.to_bits()
        );
        assert_eq!(scenes.scenes[0].step, Some(1));
        assert!(build_info(&root(), Path::new("/unused"))
            .unwrap()
            .resources
            .iter()
            .all(|r| r.status == "hash matched"));
    }

    #[test]
    fn missing_and_tampered_resources_are_not_qualified() {
        let dir = tempfile::tempdir().unwrap();
        let index = index().unwrap();
        for entry in std::fs::read_dir(root()).unwrap() {
            let path = entry.unwrap().path();
            if path.is_file() {
                std::fs::copy(&path, dir.path().join(path.file_name().unwrap())).unwrap();
            }
        }
        std::fs::write(dir.path().join("reference-scenes.json"), b"{\"scenes\":[]}").unwrap();
        assert!(reference_scenes(dir.path()).is_err());
        assert!(statuses(dir.path(), &index)
            .iter()
            .any(|r| r.status != "hash matched"));
        std::fs::remove_file(dir.path().join("state-replay.bin")).unwrap();
        assert!(reference_scenes(dir.path()).is_err());
    }
}
