//! Fresh incremental controller fixture for independent unchanged Swift replay.
//! Prefix metadata is an inspection receipt, never a partial portable record.
use reservoir_core::regulation::{RegulationExampleSpecification, RegulationSession};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::{env, error::Error, fs, io::Write, path::Path};

fn write_new(path: &Path, bytes: &[u8]) -> Result<(), Box<dyn Error>> {
    let mut file = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    if fs::read(path)? != bytes {
        return Err("Fixture readback differs".into());
    }
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = env::args().skip(1).collect();
    let [directory] = args.as_slice() else {
        return Err("Use regulation_session_fixtures NEW_OUTPUT_DIRECTORY".into());
    };
    let directory = Path::new(directory);
    fs::create_dir(directory)?;
    let mut session = RegulationSession::new(RegulationExampleSpecification::default())?;
    let mut prefixes = Vec::new();
    for step in 0..=600 {
        if [0, 1, 300, 301, 450, 599, 600].contains(&step) {
            prefixes.push(json!({
                "retainedStep": step,
                "complete": session.is_complete(),
                "portableExportAvailable": session.completed_record().is_ok(),
                "futureCursorEvidence": session.window_evidence(usize::MAX),
                "rewindBeforeWindow": session.window_evidence(300),
                "rewindFirstWindowStep": session.window_evidence(301)
            }));
        }
        if step < 600 {
            session.advance()?;
        }
    }
    let record = session.completed_record()?;
    let bytes = serde_json::to_vec(&record)?;
    let filename = "fresh-controller-600.json";
    write_new(&directory.join(filename), &bytes)?;
    let manifest = json!({
        "kind": "incremental-controller-fixture-generation",
        "scope": "Fixed field-only 600-step synthetic session; generation and byte readback, not an independent verifier or desktop lifecycle result",
        "records": [{"file": filename, "sha256": format!("{:x}", Sha256::digest(&bytes)), "sizeBytes": bytes.len(), "frameCount": record.frames.len()}],
        "prefixInspections": prefixes,
        "advanceAfterCompletionRejected": session.advance().is_err()
    });
    write_new(
        &directory.join("manifest.json"),
        &serde_json::to_vec_pretty(&manifest)?,
    )?;
    println!("{}", directory.join("manifest.json").display());
    Ok(())
}
