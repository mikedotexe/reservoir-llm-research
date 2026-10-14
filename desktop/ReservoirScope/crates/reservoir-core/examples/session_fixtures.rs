//! Generate qualification records only in an explicit new output directory.
//! Successful journal receipts follow real local atomic publication, sync and
//! readback. This is a fixture harness, not the app's storage implementation.
use reservoir_core::{actions::*, exploration::*, session::*, stage::*};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::{
    error::Error,
    fs::{self, File, OpenOptions},
    io::Write,
    path::Path,
};

type AnyResult<T> = Result<T, Box<dyn Error>>;

fn save_journal(root: &Path, session: &mut JournalSession) -> AnyResult<()> {
    let p = session
        .pending_journal()
        .ok_or("No pending journal")?
        .clone();
    let path = root.join(&p.relative_path);
    fs::create_dir_all(path.parent().unwrap())?;
    let bytes = serde_json::to_vec_pretty(&p.entry)?;
    let temporary = path.with_extension("pending");
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&temporary)?;
    file.write_all(&bytes)?;
    file.sync_all()?;
    drop(file);
    // No-clobber publication; output directory is fresh and private to this run.
    fs::hard_link(&temporary, &path)?;
    File::open(path.parent().unwrap())?.sync_all()?;
    fs::remove_file(&temporary)?;
    let readback: JournalEntry = serde_json::from_slice(&fs::read(&path)?)?;
    let receipt = JournalSaveReceipt {
        status: SaveStatus::Saved,
        entry_id: p.entry.id.clone(),
        sha256: p.entry.sha256.clone(),
        relative_path: Some(p.relative_path),
        failure: None,
    };
    session.confirm_saved(&receipt, &readback)?;
    Ok(())
}
fn write_record<T: Serialize>(
    root: &Path,
    name: &str,
    record: &T,
    manifest: &mut Vec<serde_json::Value>,
) -> AnyResult<()> {
    let bytes = serde_json::to_vec_pretty(record)?;
    let result = reservoir_core::verify_bytes(&bytes);
    if result.status != reservoir_core::VerificationStatus::Passed {
        return Err(format!("Generated fixture {name} failed: {:?}", result.diagnostics).into());
    }
    let path = root.join(format!("{name}.json"));
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&path)?;
    file.write_all(&bytes)?;
    file.sync_all()?;
    manifest.push(
        serde_json::json!({"file":path.file_name().unwrap().to_string_lossy(),
        "sha256":format!("{:x}",Sha256::digest(&bytes)),"format":result.format,
        "checkedSteps":result.checked_steps,"checkedTurns":result.checked_turns}),
    );
    Ok(())
}
fn main() -> AnyResult<()> {
    let arg = std::env::args()
        .nth(1)
        .ok_or("Usage: session_fixtures NEW_OUTPUT_DIRECTORY")?;
    let root = Path::new(&arg);
    fs::create_dir(root)?;
    let mut manifest = vec![];
    for stage in 1..=4 {
        let mut session = StageSession::new(RunSpecification {
            stage,
            steps: 32,
            turn_every: 30,
            seed: u64::MAX,
            noise_amplitude: 0.013,
            ..Default::default()
        })?;
        for step in 1..=32 {
            session.advance()?;
            if step == 30 || step == 32 {
                write_record(
                    root,
                    &format!("stage-{stage}-step-{step}"),
                    session.record(),
                    &mut manifest,
                )?;
            }
        }
    }
    let mut explore = ExplorationEngine::new(u64::MAX);
    for step in 1..=32 {
        let controls = ExplorationControls {
            recurrence_enabled: true,
            sensory_enabled: !(13..=17).contains(&step),
            noise_amplitude: 0.013,
            bias_enabled: step > 18,
            repeat_input: step > 20,
            ..Default::default()
        };
        explore.advance(controls, step == 1 || step == 19)?;
        if step == 17 || step == 32 {
            write_record(
                root,
                &format!("explore-step-{step}"),
                &explore.record(),
                &mut manifest,
            )?;
        }
    }
    for stage in [4, 5] {
        for manual in [false, true] {
            let spec: ActionSpecification = serde_json::from_value(serde_json::json!({
                "stage":stage,"steps":65,"turnEvery":30,"seed":18446744073709551615u64,
                "mode":"independentGeneration","comparePrevious":false,"promptVersion":2,
                "noiseAmplitude":0.013
            }))?;
            let mut session = JournalSession::new(spec)?;
            let kind = if manual {
                "manual-and-scheduled"
            } else {
                "scheduled"
            };
            let journal_dir = root.join(format!("journals-{stage}-{kind}"));
            for step in 1..=65 {
                session.advance()?;
                if manual && step == 21 {
                    session.request_journal()?;
                }
                if session.pending_journal().is_some() {
                    save_journal(&journal_dir, &mut session)?;
                }
                if [30, 31, 65].contains(&step) {
                    write_record(
                        root,
                        &format!("journal-{stage}-{kind}-step-{step}"),
                        &session.record()?,
                        &mut manifest,
                    )?;
                }
            }
        }
    }
    let spec: ActionSpecification = serde_json::from_value(serde_json::json!({
        "stage":5,"steps":65,"mode":"independentGeneration","comparePrevious":false
    }))?;
    let mut failed = JournalSession::new(spec)?;
    for _ in 0..30 {
        failed.advance()?;
    }
    // Exercise an actual filesystem error, then explicitly finalize the pending
    // save as a terminal failure; no successful journal path exists for it.
    let missing = root.join("deliberately-absent-parent/journal.json");
    let error = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(missing)
        .unwrap_err();
    failed.fail_pending(&format!(
        "Fixture save failed and was explicitly finalized: {error}"
    ))?;
    write_record(
        root,
        "journal-5-terminal-save-failure",
        &failed.record()?,
        &mut manifest,
    )?;
    let output = serde_json::json!({"schema":"reservoir-session-fixtures-v1","modelsContacted":false,
        "scope":"Core fixture execution; successful journal entries were published and read back in this fixture directory. App storage requires separate qualification.","records":manifest});
    fs::write(
        root.join("manifest.json"),
        serde_json::to_vec_pretty(&output)?,
    )?;
    println!("{}", serde_json::to_string(&output)?);
    Ok(())
}
