//! Read-only peer observations from explicitly joined, local Reservoir Scope stores.
//! A manifest names one immutable checkpoint; no peer process is contacted or mutated.
use super::*;
use crate::files;
use reservoir_core::sustained::*;
use std::{collections::BTreeMap, fs, path::Path};

const MAX_APPS: usize = 32;
const MAX_SESSIONS: usize = 256;
fn unavailable(name: &str, reason: &str) -> SustainedPeerResult {
    SustainedPeerResult {
        participant: name.into(),
        entry: None,
        unavailable: Some(reason.into()),
    }
}
fn directories(path: &Path, limit: usize) -> Result<Vec<std::path::PathBuf>, AppError> {
    sustained_store::ordinary(path)?;
    let mut paths = Vec::new();
    for entry in fs::read_dir(path).map_err(|_| err("peers", "Cannot list peer directory"))? {
        let entry = entry.map_err(|_| err("peers", "Cannot inspect peer directory"))?;
        if entry
            .file_type()
            .map_err(|_| err("peers", "Cannot inspect peer type"))?
            .is_dir()
        {
            paths.push(entry.path());
            if paths.len() > limit {
                return Err(err("peers", "Peer discovery bound exceeded"));
            }
        }
    }
    paths.sort();
    Ok(paths)
}
fn stores(root: &Path) -> Result<Vec<SustainedStore>, AppError> {
    let app = root
        .parent()
        .ok_or_else(|| err("peers", "Missing app directory"))?;
    let base = app
        .parent()
        .ok_or_else(|| err("peers", "Missing local app-data directory"))?;
    sustained_store::ordinary(base)?;
    let mut result = Vec::new();
    // Filter names before counting; unrelated application data is neither opened nor read.
    for item in fs::read_dir(base).map_err(|_| err("peers", "Cannot list local app stores"))? {
        let item = item.map_err(|_| err("peers", "Cannot inspect local app store"))?;
        let app_name = item.file_name();
        let app_name = app_name.to_string_lossy();
        if app_name != "research.reservoir.scope"
            && !app_name.starts_with("research.reservoir.scope.")
        {
            continue;
        }
        if !item
            .file_type()
            .map_err(|_| err("peers", "Cannot inspect app directory"))?
            .is_dir()
        {
            continue;
        }
        let path = item.path().join("sustained-v1");
        if path.exists() {
            sustained_store::ordinary(&item.path())?;
            sustained_store::ordinary(&path)?;
            result.push(SustainedStore::new(path));
            if result.len() > MAX_APPS {
                return Err(err("peers", "Too many Reservoir Scope stores"));
            }
        }
    }
    // Also supports an isolated test/CLI store, but never broadens discovery beyond its siblings.
    if !result.iter().any(|s| s.root == root) {
        result.push(SustainedStore::new(root.to_owned()));
    }
    Ok(result)
}

fn entry(
    store: &SustainedStore,
    manifest: &Manifest,
    manifest_bytes: &[u8],
) -> Result<SustainedPeerEntry, AppError> {
    let path = store.root.join(&manifest.session_id);
    sustained_store::ordinary(&path)?;
    sustained_store::ordinary(&path.join("checkpoints"))?;
    let sha = &manifest.checkpoint_sha256;
    if sha.len() != 64
        || !sha
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    {
        return Err(err("peers", "Invalid peer checkpoint identity"));
    }
    let bytes = files::read_bounded(
        &path.join("checkpoints").join(format!("{sha}.json")),
        sustained_store::OBJECT_LIMIT,
        "peer-checkpoint",
    )?;
    if files::digest(&bytes) != *sha {
        return Err(err("peers", "Peer checkpoint bytes differ"));
    }
    let checkpoint: SustainedCheckpoint = serde_json::from_slice(&bytes).map_err(ce)?;
    checkpoint.validate().map_err(ce)?;
    if checkpoint.state.step != manifest.durable_step
        || manifest.step != manifest.durable_step
        || checkpoint.state.specification.peer_reading != manifest.config.peer_reading
        || serde_json::to_value(&checkpoint.state.specification.language).map_err(ce)?
            != serde_json::to_value(&manifest.config.language).map_err(ce)?
    {
        return Err(err("peers", "Peer manifest and checkpoint differ"));
    }
    let memory = checkpoint
        .state
        .latest_memory
        .as_ref()
        .ok_or_else(|| err("peers", "Peer has no applied journal yet"))?;
    let (journal, object_sha) = store.read_journal_proof(&manifest.session_id, &memory.entry.id)?;
    if serde_json::to_vec(&journal.pending.entry).map_err(ce)?
        != serde_json::to_vec(&memory.entry).map_err(ce)?
        || journal.configured_model != manifest.config.language.model
        || journal
            .pending
            .response
            .provider_model
            .as_ref()
            .is_some_and(|m| m.is_empty() || m.len() > 256)
    {
        return Err(err("peers", "Peer journal differs from committed memory"));
    }
    let body = memory.entry.body.as_deref().unwrap_or(&memory.entry.text);
    let excerpt = peer_excerpt(body).to_owned();
    Ok(SustainedPeerEntry {
        session_id: manifest.session_id.clone(),
        journal_id: memory.entry.id.clone(),
        configured_model: journal.configured_model,
        provider_model: journal.pending.response.provider_model,
        observed_step: memory.entry.observed_step,
        applied_step: memory.applied_step,
        check_in: journal.pending.check_in.is_some(),
        manifest_sha256: files::digest(manifest_bytes),
        checkpoint_sha256: sha.clone(),
        journal_object_sha256: object_sha,
        raw_reply_sha256: memory.entry.sha256.clone(),
        body_sha256: files::digest(body.as_bytes()),
        body_bytes: body.len(),
        excerpt_sha256: files::digest(excerpt.as_bytes()),
        truncated: excerpt.len() < body.len(),
        excerpt,
    })
}

pub(super) fn capture(
    store: &SustainedStore,
    own: &Manifest,
    pending: &SustainedPendingLanguage,
) -> SustainedPeerSnapshot {
    let config = own
        .config
        .peer_reading
        .as_ref()
        .expect("enabled peer reading");
    let mut snapshot = SustainedPeerSnapshot {
        attempt_id: pending.attempt_id,
        observed_step: pending.observed_step,
        captured_at_ms: crate::session_store::now_ms().to_string(),
        peers: config
            .peers
            .iter()
            .map(|name| unavailable(name, "No matching peer session is available in this group"))
            .collect(),
    };
    let collect = || -> Result<BTreeMap<String, Vec<SustainedPeerResult>>, AppError> {
        let mut found: BTreeMap<String, Vec<SustainedPeerResult>> = BTreeMap::new();
        let mut inspected = 0;
        let mut manifest_bytes = 0;
        for peer_store in stores(&store.root)? {
            for path in directories(&peer_store.root, MAX_SESSIONS)? {
                let Some(id) = path
                    .file_name()
                    .and_then(|s| s.to_str())
                    .filter(|id| sustained_store::valid_id(id))
                else {
                    continue;
                };
                if peer_store.root == store.root && id == own.session_id {
                    continue;
                }
                let bytes = match files::read_bounded(
                    &path.join("manifest.json"),
                    128 * 1024,
                    "peer-manifest",
                ) {
                    Ok(v) => v,
                    Err(_) => continue,
                };
                inspected += 1;
                manifest_bytes += bytes.len();
                if inspected > 512 || manifest_bytes > 16 * 1024 * 1024 {
                    return Err(err("peers", "Peer manifest scan bound exceeded"));
                }
                let manifest: Manifest = match serde_json::from_slice(&bytes) {
                    Ok(m) => m,
                    Err(_) => continue,
                };
                let Some(peer) = &manifest.config.peer_reading else {
                    continue;
                };
                if peer.group != config.group || !config.peers.contains(&peer.participant) {
                    continue;
                }
                let name = peer.participant.clone();
                let result = if manifest.session_id != id
                    || peer.validate().is_err()
                    || !peer.peers.contains(&config.participant)
                {
                    unavailable(
                        &name,
                        "Peer membership is invalid or does not include this participant",
                    )
                } else {
                    match entry(&peer_store, &manifest, &bytes) {
                        Ok(entry) => SustainedPeerResult {
                            participant: name.clone(),
                            entry: Some(entry),
                            unavailable: None,
                        },
                        Err(_) => unavailable(
                            &name,
                            "Peer has no readable, verified applied journal at this snapshot",
                        ),
                    }
                };
                found.entry(name).or_default().push(result);
            }
        }
        Ok(found)
    };
    match collect() {
        Ok(mut found) => {
            for result in &mut snapshot.peers {
                if let Some(mut candidates) = found.remove(&result.participant) {
                    *result = if candidates.len() == 1 {
                        candidates.remove(0)
                    } else {
                        unavailable(&result.participant, "Multiple sessions claim this participant in the group; use a new group or distinct participant names")
                    };
                }
            }
        }
        Err(_) => {
            for result in &mut snapshot.peers {
                *result = unavailable(
                    &result.participant,
                    "Local peer discovery was unavailable or exceeded its bounded scope",
                );
            }
        }
    }
    snapshot
}
