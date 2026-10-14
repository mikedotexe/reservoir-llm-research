//! Fresh standalone A–H qualification only. All successful save and memory
//! confirmations follow real reads of this harness's explicit new directory.
//! Canonical resources and prior qualification receipts are never modified.
use reservoir_core::{actions::*, session::*};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::{
    error::Error,
    fs::{self, File, OpenOptions},
    io::Write,
    path::Path,
};
type AnyResult<T> = Result<T, Box<dyn Error>>;

fn spec(stage: u8, mode: ComparisonMode) -> ActionSpecification {
    let mut s: ActionSpecification = serde_json::from_value(serde_json::json!({
        "stage":stage,"steps":11,"turnEvery":3,"seed":18446744073709551615u64,
        "mode":"independentGeneration","comparePrevious":false,"promptVersion":2,
        "noiseAmplitude":0.013,"inputStrength":0.8,"biasEnabled":true
    }))
    .unwrap();
    s.mode = mode;
    s
}
fn resolve_memory(root: &Path, session: &mut ActionSession) -> AnyResult<()> {
    if let Some(p) = session.pending_memory().cloned() {
        let readback: JournalEntry =
            serde_json::from_slice(&fs::read(root.join(&p.relative_path))?)?;
        session.confirm_memory(&readback)?;
    }
    Ok(())
}
fn resolve(root: &Path, session: &mut ActionSession) -> AnyResult<()> {
    resolve_memory(root, session)?;
    if let Some(p) = session.pending_journal().cloned() {
        let path = root.join(&p.relative_path);
        fs::create_dir_all(path.parent().unwrap())?;
        let bytes = serde_json::to_vec_pretty(&p.entry)?;
        let temporary = path.with_extension("pending");
        let mut file = OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(&temporary)?;
        file.write_all(&bytes)?;
        file.sync_all()?;
        drop(file);
        fs::hard_link(&temporary, &path)?;
        File::open(path.parent().unwrap())?.sync_all()?;
        fs::remove_file(temporary)?;
        let readback: JournalEntry = serde_json::from_slice(&fs::read(path)?)?;
        let saved = JournalSaveReceipt {
            status: SaveStatus::Saved,
            entry_id: p.entry.id.clone(),
            sha256: p.entry.sha256.clone(),
            relative_path: Some(p.relative_path),
            failure: None,
        };
        session.confirm_saved(&saved, &readback)?;
    }
    Ok(())
}
fn advance_to(root: &Path, s: &mut ActionSession, step: usize) -> AnyResult<()> {
    while s.frames().len() < step {
        s.advance()?;
        resolve(root, s)?;
    }
    Ok(())
}
fn write_record<T: Serialize>(
    root: &Path,
    name: &str,
    record: &T,
    manifest: &mut Vec<serde_json::Value>,
) -> AnyResult<()> {
    let bytes = serde_json::to_vec_pretty(record)?;
    let report = reservoir_core::verify_bytes(&bytes);
    if report.status != reservoir_core::VerificationStatus::Passed {
        return Err(format!("{name}: {:?}", report.diagnostics).into());
    }
    let path = root.join(format!("{name}.json"));
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(&bytes)?;
    file.sync_all()?;
    manifest.push(serde_json::json!({"file":format!("{name}.json"),"sha256":format!("{:x}",Sha256::digest(&bytes)),
        "format":report.format,"checkedSteps":report.checked_steps,"checkedTurns":report.checked_turns}));
    Ok(())
}
fn main() -> AnyResult<()> {
    let argument = std::env::args()
        .nth(1)
        .ok_or("Usage: action_session_fixtures NEW_OUTPUT_DIRECTORY")?;
    let root = Path::new(&argument);
    fs::create_dir(root)?;
    let mut manifest = vec![];
    for mode in [
        ComparisonMode::IndependentGeneration,
        ComparisonMode::FixedReplay,
    ] {
        let mode_name = if mode == ComparisonMode::FixedReplay {
            "tape"
        } else {
            "scripted"
        };
        for stage in 1..=8 {
            let name = format!("action-{stage}-{mode_name}");
            let journal = root.join(format!("journals-{name}"));
            let mut session = ActionSession::new(spec(stage, mode))?;
            for step in 1..=11 {
                session.advance()?;
                resolve(&journal, &mut session)?;
                if stage >= 6 && (step == 6 || step == 9) {
                    write_record(
                        root,
                        &format!("{name}-stopped-{step}"),
                        &session.record()?,
                        &mut manifest,
                    )?;
                }
            }
            write_record(
                root,
                &format!("{name}-complete"),
                &session.record()?,
                &mut manifest,
            )?;
        }
        let name = format!("action-7-{mode_name}-manual-forced-write");
        let journal = root.join(format!("journals-{name}"));
        let mut manual = ActionSession::new(spec(7, mode))?;
        advance_to(&journal, &mut manual, 8)?;
        // Third independent action would WAIT if scheduled; tape8 also declares
        // WAIT. An explicit manual opportunity forces WRITE in both modes.
        manual.request_action()?;
        resolve(&journal, &mut manual)?;
        write_record(root, &name, &manual.record()?, &mut manifest)?;

        for cancelled in [false, true] {
            let name = format!(
                "action-6-{mode_name}-memory-{}",
                if cancelled { "cancelled" } else { "failed" }
            );
            let journal = root.join(format!("journals-{name}"));
            let mut session = ActionSession::new(spec(6, mode))?;
            advance_to(&journal, &mut session, 5)?;
            session.advance()?;
            if cancelled {
                session.cancel_memory("Fixture explicit stop before the required memory read")?;
            } else {
                let path = journal.join(&session.pending_memory().unwrap().relative_path);
                fs::remove_file(&path)?;
                let failure = fs::read(path).unwrap_err();
                session.fail_memory(&format!(
                    "Fixture actual required journal read failed: {failure}"
                ))?;
            }
            write_record(root, &name, &session.record()?, &mut manifest)?;
        }
        let name = format!("action-8-{mode_name}-save-failed-after-memory");
        let journal = root.join(format!("journals-{name}"));
        let mut failed = ActionSession::new(spec(8, mode))?;
        advance_to(&journal, &mut failed, 5)?;
        failed.advance()?;
        resolve_memory(&journal, &mut failed)?;
        let target = journal.join(&failed.pending_journal().unwrap().relative_path);
        fs::create_dir(&target)?;
        let failure = OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(target)
            .unwrap_err();
        failed.fail_pending(&format!(
            "Fixture actual save failure explicitly finalized: {failure}"
        ))?;
        write_record(root, &name, &failed.record()?, &mut manifest)?;
    }
    let output = serde_json::json!({"schema":"reservoir-action-session-fixtures-v1","modelsContacted":false,
        "scope":"Standalone fresh scripted/tape A–H. Real fixture-directory journal save/readback and memory read; app storage and paired scheduling remain separately qualified.","records":manifest});
    fs::write(
        root.join("manifest.json"),
        serde_json::to_vec_pretty(&output)?,
    )?;
    println!("{}", serde_json::to_string(&output)?);
    Ok(())
}
