//! New-directory paired qualification fixtures. Save confirmations and memory
//! confirmations follow actual filesystem writes/reads in separate arm paths.
//! No canonical resource, earlier receipt, model or live system is accessed.
use reservoir_core::{actions::*, comparison::ActionComparisonSession};
use sha2::{Digest, Sha256};
use std::{
    error::Error,
    fs::{self, File, OpenOptions},
    io::Write,
    path::Path,
};
type AnyResult<T> = Result<T, Box<dyn Error>>;

fn spec(stage: u8, mode: ComparisonMode) -> ActionSpecification {
    let mut s:ActionSpecification=serde_json::from_value(serde_json::json!({
        "stage":stage,"steps":11,"turnEvery":3,"seed":18446744073709551615u64,
        "comparePrevious":true,"promptVersion":2,"inputStrength":0.8,"noiseAmplitude":0.013,"biasEnabled":true
    })).unwrap();
    s.mode = mode;
    s
}
fn observation(quiet: bool, profile: ForcingProfile) -> ActionSpecification {
    let mut s = spec(4, ComparisonMode::IndependentGeneration);
    s.comparison_kind = ComparisonKind::Observation;
    s.forcing_profile = profile;
    if quiet {
        s.input_strength = 0.0;
        s.noise_amplitude = 0.0;
        s.bias_enabled = false;
    }
    s
}
fn read_one(root: &Path, s: &mut ActionComparisonSession) -> AnyResult<()> {
    let (arm, p) = s
        .pending_memory()
        .map(|(a, p)| (a, p.clone()))
        .ok_or("No pending memory")?;
    let entry: JournalEntry = serde_json::from_slice(&fs::read(root.join(p.relative_path))?)?;
    s.confirm_memory(arm, &entry)?;
    Ok(())
}
fn save_one(root: &Path, s: &mut ActionComparisonSession) -> AnyResult<()> {
    let (arm, p) = s
        .pending_journal()
        .map(|(a, p)| (a, p.clone()))
        .ok_or("No pending journal")?;
    let target = root.join(&p.relative_path);
    fs::create_dir_all(target.parent().unwrap())?;
    let temporary = target.with_extension("pending");
    let bytes = serde_json::to_vec_pretty(&p.entry)?;
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&temporary)?;
    file.write_all(&bytes)?;
    file.sync_all()?;
    drop(file);
    fs::hard_link(&temporary, &target)?;
    File::open(target.parent().unwrap())?.sync_all()?;
    fs::remove_file(temporary)?;
    let readback: JournalEntry = serde_json::from_slice(&fs::read(target)?)?;
    let receipt = JournalSaveReceipt {
        status: SaveStatus::Saved,
        entry_id: p.entry.id,
        sha256: p.entry.sha256,
        relative_path: Some(p.relative_path),
        failure: None,
    };
    s.confirm_saved(arm, &receipt, &readback)?;
    Ok(())
}
fn resolve(root: &Path, s: &mut ActionComparisonSession) -> AnyResult<()> {
    loop {
        if s.pending_memory().is_some() {
            read_one(root, s)?;
        } else if s.pending_journal().is_some() {
            save_one(root, s)?;
        } else {
            break;
        }
    }
    Ok(())
}
fn to(root: &Path, s: &mut ActionComparisonSession, step: usize) -> AnyResult<()> {
    while s.frames(Arm::Right).len() < step {
        s.advance()?;
        resolve(root, s)?;
    }
    Ok(())
}
fn failed_save(root: &Path, s: &mut ActionComparisonSession) -> AnyResult<()> {
    let (arm, p) = s
        .pending_journal()
        .map(|(a, p)| (a, p.clone()))
        .ok_or("No pending journal")?;
    let path = root.join(p.relative_path);
    fs::create_dir_all(&path)?;
    let failure = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .unwrap_err();
    s.fail_pending(
        arm,
        &format!("Fixture actual journal publication failure: {failure}"),
    )?;
    Ok(())
}
fn write(
    root: &Path,
    name: &str,
    s: &ActionComparisonSession,
    manifest: &mut Vec<serde_json::Value>,
) -> AnyResult<()> {
    let r = s.record()?;
    r.verify()?;
    let bytes = serde_json::to_vec_pretty(&r)?;
    let report = reservoir_core::verify_bytes(&bytes);
    if report.status != reservoir_core::VerificationStatus::Passed {
        return Err(format!("{name}: {:?}", report.diagnostics).into());
    }
    let filename = format!("{name}.json");
    let mut f = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(root.join(&filename))?;
    f.write_all(&bytes)?;
    f.sync_all()?;
    manifest.push(serde_json::json!({"file":filename,"sha256":format!("{:x}",Sha256::digest(&bytes)),"format":r.format,"stage":r.specification.stage,"comparisonKind":r.specification.comparison_kind,"mode":r.specification.mode,"checkedSteps":report.checked_steps,"checkedTurns":report.checked_turns}));
    Ok(())
}
fn main() -> AnyResult<()> {
    let argument = std::env::args()
        .nth(1)
        .ok_or("Usage: comparison_session_fixtures NEW_OUTPUT_DIRECTORY")?;
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
        for stage in 2..=8 {
            let name = format!("pair-{stage}-{mode_name}");
            let journal = root.join(format!("journals-{name}"));
            let mut s = ActionComparisonSession::new(spec(stage, mode))?;
            for step in 1..=11 {
                s.advance()?;
                resolve(&journal, &mut s)?;
                if stage >= 5 && [3, 6].contains(&step) {
                    write(root, &format!("{name}-stopped-{step}"), &s, &mut manifest)?;
                }
            }
            write(root, &format!("{name}-complete"), &s, &mut manifest)?;
        }
        let name = format!("pair-8-{mode_name}-manual-forced-write");
        let journal = root.join(format!("journals-{name}"));
        let mut s = ActionComparisonSession::new(spec(8, mode))?;
        to(&journal, &mut s, 8)?;
        s.request_action()?;
        resolve(&journal, &mut s)?;
        to(&journal, &mut s, 11)?;
        write(root, &name, &s, &mut manifest)?;

        for arm in [Arm::Left, Arm::Right] {
            let label = if arm == Arm::Left { "left" } else { "right" };
            let name = format!("pair-6-{mode_name}-{label}-save-failed");
            let journal = root.join(format!("journals-{name}"));
            let mut s = ActionComparisonSession::new(spec(6, mode))?;
            to(&journal, &mut s, 2)?;
            s.advance()?;
            if arm == Arm::Right {
                save_one(&journal, &mut s)?;
            }
            failed_save(&journal, &mut s)?;
            write(root, &name, &s, &mut manifest)?;

            let name = format!("pair-7-{mode_name}-{label}-memory-failed");
            let journal = root.join(format!("journals-{name}"));
            let mut s = ActionComparisonSession::new(spec(7, mode))?;
            to(&journal, &mut s, 5)?;
            s.advance()?;
            if arm == Arm::Right {
                read_one(&journal, &mut s)?;
                save_one(&journal, &mut s)?;
            }
            let (pending_arm, p) = s
                .pending_memory()
                .map(|(a, p)| (a, p.clone()))
                .ok_or("Missing expected memory boundary")?;
            if pending_arm != arm {
                return Err("Unexpected memory ordering".into());
            }
            let path = journal.join(p.relative_path);
            fs::remove_file(&path)?;
            let failure = fs::read(path).unwrap_err();
            s.fail_memory(
                arm,
                &format!("Fixture actual journal read failed: {failure}"),
            )?;
            write(root, &name, &s, &mut manifest)?;
        }
        let name = format!("pair-7-{mode_name}-cancel-before-memory");
        let journal = root.join(format!("journals-{name}"));
        let mut s = ActionComparisonSession::new(spec(7, mode))?;
        to(&journal, &mut s, 5)?;
        s.advance()?;
        s.stop("Fixture explicit stop before left memory exposure and before peer request")?;
        write(root, &name, &s, &mut manifest)?;

        let name = format!("pair-6-{mode_name}-stop-after-first-save");
        let journal = root.join(format!("journals-{name}"));
        let mut s = ActionComparisonSession::new(spec(6, mode))?;
        to(&journal, &mut s, 2)?;
        s.advance()?;
        save_one(&journal, &mut s)?;
        s.stop("Fixture explicit stop retaining pending right save failure")?;
        write(root, &name, &s, &mut manifest)?;
    }
    for profile in [
        ForcingProfile::PulsedSensoryV1,
        ForcingProfile::ContinuousSensoryV1,
    ] {
        let profile_name = if profile == ForcingProfile::PulsedSensoryV1 {
            "pulsed"
        } else {
            "continuous"
        };
        for quiet in [false, true] {
            let name = format!(
                "observation-{profile_name}-{}",
                if quiet { "quiet" } else { "active" }
            );
            let journal = root.join(format!("journals-{name}"));
            let mut s = ActionComparisonSession::new(observation(quiet, profile))?;
            for step in 1..=11 {
                s.advance()?;
                resolve(&journal, &mut s)?;
                if [3, 6].contains(&step) {
                    write(root, &format!("{name}-stopped-{step}"), &s, &mut manifest)?;
                }
            }
            write(root, &format!("{name}-complete"), &s, &mut manifest)?;
        }
    }
    for step in [3, 6] {
        let name = format!("observation-first-save-failed-step-{step}");
        let journal = root.join(format!("journals-{name}"));
        let mut s =
            ActionComparisonSession::new(observation(false, ForcingProfile::ContinuousSensoryV1))?;
        to(&journal, &mut s, step - 1)?;
        s.advance()?;
        failed_save(&journal, &mut s)?;
        // Native observation policy still attempts the partner after failure.
        resolve(&journal, &mut s)?;
        write(root, &name, &s, &mut manifest)?;
    }
    let value = serde_json::json!({"schema":"reservoir-comparison-session-fixtures-v1","modelsContacted":false,"scope":"Fresh standalone paired component/observation records; per-arm actual fixture-directory saves/readbacks and memory reads. App storage/lifecycle and scientific usefulness are separately qualified.","records":manifest});
    let mut f = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(root.join("manifest.json"))?;
    f.write_all(&serde_json::to_vec_pretty(&value)?)?;
    f.sync_all()?;
    println!("{}", serde_json::to_string(&value)?);
    Ok(())
}
