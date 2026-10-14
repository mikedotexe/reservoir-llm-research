//! Supplied-response qualification, never an HTTP/provider-authentication claim.
//! Fixture journals use actual no-clobber publication and fresh readback. No live
//! system, canonical fixture, earlier release receipt or app store is accessed.
use reservoir_core::{actions::*, comparison::ActionComparisonSession, session::*, stage::*};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::{
    error::Error,
    fs::{self, OpenOptions},
    io::Write,
    path::Path,
};
type AnyResult<T> = Result<T, Box<dyn Error>>;

fn language(json: bool) -> LanguageConfiguration {
    LanguageConfiguration {
        backend: LanguageKind::Ollama,
        endpoint: Some("http://127.0.0.1:11499".into()),
        model: Some("fixture-provider-not-contacted".into()),
        context_tokens: Some(2048),
        response_format: json.then(|| "json".into()),
    }
}
fn response(text: String) -> LanguageResponse {
    LanguageResponse {
        text,
        provider_model: Some("fixture-provider-not-contacted".into()),
        stop_reason: Some("stop".into()),
        token_count: Some(20),
        complete: true,
        provider_prompt_evaluation: None,
    }
}
fn write_new(path: &Path, bytes: &[u8]) -> AnyResult<()> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    drop(file);
    #[cfg(unix)]
    {
        std::fs::File::open(path.parent().unwrap())?.sync_all()?;
    }
    if fs::read(path)? != bytes {
        return Err("Fixture readback differs".into());
    }
    Ok(())
}
fn saved(root: &Path, pending: &PendingJournal) -> AnyResult<(JournalSaveReceipt, JournalEntry)> {
    let path = root.join(&pending.relative_path);
    fs::create_dir_all(path.parent().unwrap())?;
    write_new(&path, &serde_json::to_vec(&pending.entry)?)?;
    let readback = serde_json::from_slice(&fs::read(path)?)?;
    Ok((
        JournalSaveReceipt {
            status: SaveStatus::Saved,
            entry_id: pending.entry.id.clone(),
            sha256: pending.entry.sha256.clone(),
            relative_path: Some(pending.relative_path.clone()),
            failure: None,
        },
        readback,
    ))
}
fn write_record<T: Serialize>(
    root: &Path,
    name: &str,
    record: &T,
    records: &mut Vec<serde_json::Value>,
) -> AnyResult<()> {
    let bytes = serde_json::to_vec(record)?;
    let file = format!("{name}.json");
    write_new(&root.join(&file), &bytes)?;
    records.push(serde_json::json!({"file":file,"sha256":format!("{:x}",Sha256::digest(&bytes)),"bytes":bytes.len()}));
    Ok(())
}

fn stage_fixture(
    root: &Path,
    stage: u8,
    outcome: &str,
    records: &mut Vec<serde_json::Value>,
) -> AnyResult<()> {
    let mut s = StageSession::new(RunSpecification {
        stage,
        steps: 32,
        turn_every: 30,
        seed: u64::MAX,
        noise_amplitude: 0.013,
        language: language(false),
        ..Default::default()
    })?;
    for _ in 0..30 {
        s.advance()?;
    }
    if outcome == "cancel-prepared" {
        s.cancel_language(1, 30, "Fixture explicit stop before dispatch")?;
    } else {
        s.start_language(1, 30)?;
        match outcome {
            "transport" => {
                s.fail_language(1, 30, "Fixture provider operation failed without response")?
            }
            "cancel-started" => s.cancel_language(1, 30, "Fixture explicit stop after dispatch")?,
            _ => {
                let mut r = response(
                    "I notice the retained sensory pattern and will watch its next change.".into(),
                );
                match outcome {
                    "incomplete" => r.complete = false,
                    "length" => r.stop_reason = Some("length".into()),
                    "negative-tokens" => r.token_count = Some(-1),
                    "empty" => r.text = " \n\t".into(),
                    "oversized" => r.text = "x".repeat(65_537),
                    "unsupported" => r.text = "\u{10ffff}".into(),
                    _ => {}
                }
                if outcome == "unsupported" {
                    if s.confirm_language(1, 30, &r).is_ok() {
                        return Err("Unqualified Unicode unexpectedly accepted".into());
                    }
                    s.cancel_language(
                        1,
                        30,
                        "Explicit cancellation after unsupported codec response",
                    )?;
                } else {
                    s.confirm_language(1, 30, &r)?;
                }
                if outcome == "complete" {
                    s.advance()?;
                    s.advance()?;
                }
                if outcome == "stopped-prefix" {
                    s.stop();
                }
            }
        }
    }
    write_record(
        root,
        &format!("stage-{stage}-{outcome}"),
        s.portable_record()?,
        records,
    )
}

enum ActionEngine {
    Single(Box<JournalSession>),
    Pair(Box<ActionComparisonSession>),
}
impl ActionEngine {
    fn new(spec: ActionSpecification) -> AnyResult<Self> {
        Ok(if spec.compare_previous {
            Self::Pair(Box::new(ActionComparisonSession::new(spec)?))
        } else {
            Self::Single(Box::new(JournalSession::new(spec)?))
        })
    }
    fn advance(&mut self) -> AnyResult<()> {
        match self {
            Self::Single(s) => {
                s.advance()?;
            }
            Self::Pair(s) => {
                s.advance()?;
            }
        };
        Ok(())
    }
    fn language(&self) -> Option<(Arm, PendingLanguage)> {
        match self {
            Self::Single(s) => s.pending_language().map(|p| (Arm::Right, p.clone())),
            Self::Pair(s) => s.pending_language().map(|(a, p)| (a, p.clone())),
        }
    }
    fn memory(&self) -> Option<(Arm, PendingMemory)> {
        match self {
            Self::Single(s) => s.pending_memory().map(|p| (Arm::Right, p.clone())),
            Self::Pair(s) => s.pending_memory().map(|(a, p)| (a, p.clone())),
        }
    }
    fn journal(&self) -> Option<(Arm, PendingJournal)> {
        match self {
            Self::Single(s) => s.pending_journal().map(|p| (Arm::Right, p.clone())),
            Self::Pair(s) => s.pending_journal().map(|(a, p)| (a, p.clone())),
        }
    }
    fn start(&mut self, a: Arm, p: &PendingLanguage) -> AnyResult<()> {
        match self {
            Self::Single(s) => s.start_language(p.turn_id, p.observed_step)?,
            Self::Pair(s) => s.start_language(a, p.turn_id, p.observed_step)?,
        };
        Ok(())
    }
    fn confirm(&mut self, a: Arm, p: &PendingLanguage, r: &LanguageResponse) -> AnyResult<()> {
        match self {
            Self::Single(s) => s.confirm_language(p.turn_id, p.observed_step, r)?,
            Self::Pair(s) => s.confirm_language(a, p.turn_id, p.observed_step, r)?,
        };
        Ok(())
    }
    fn fail(&mut self, a: Arm, p: &PendingLanguage) -> AnyResult<()> {
        match self {
            Self::Single(s) => s.fail_language(
                p.turn_id,
                p.observed_step,
                "Fixture provider operation failed",
            )?,
            Self::Pair(s) => s.fail_language(
                a,
                p.turn_id,
                p.observed_step,
                "Fixture provider operation failed",
            )?,
        };
        Ok(())
    }
    fn cancel(&mut self, a: Arm, p: &PendingLanguage) -> AnyResult<()> {
        match self {
            Self::Single(s) => {
                s.cancel_language(p.turn_id, p.observed_step, "Fixture explicit cancellation")?
            }
            Self::Pair(s) => s.cancel_language(
                a,
                p.turn_id,
                p.observed_step,
                "Fixture explicit cancellation",
            )?,
        };
        Ok(())
    }
    fn read(&mut self, root: &Path, a: Arm, p: &PendingMemory) -> AnyResult<()> {
        let readback = serde_json::from_slice(&fs::read(root.join(&p.relative_path))?)?;
        match self {
            Self::Single(s) => s.confirm_memory(&readback)?,
            Self::Pair(s) => s.confirm_memory(a, &readback)?,
        };
        Ok(())
    }
    fn save(&mut self, root: &Path, a: Arm, p: &PendingJournal) -> AnyResult<()> {
        let (receipt, readback) = saved(root, p)?;
        match self {
            Self::Single(s) => s.confirm_saved(&receipt, &readback)?,
            Self::Pair(s) => s.confirm_saved(a, &receipt, &readback)?,
        };
        Ok(())
    }
    fn record(&self) -> AnyResult<ActionComparisonRecord> {
        Ok(match self {
            Self::Single(s) => s.record()?,
            Self::Pair(s) => s.record()?,
        })
    }
    fn done(&self) -> bool {
        match self {
            Self::Single(s) => s.is_complete() || s.is_failed(),
            Self::Pair(s) => s.is_complete() || s.is_failed(),
        }
    }
    fn stop(&mut self) -> AnyResult<()> {
        match self {
            Self::Single(s) => s.stop()?,
            Self::Pair(s) => s.stop("Fixture stopped prefix")?,
        };
        Ok(())
    }
    fn manual(&mut self) -> AnyResult<()> {
        match self {
            Self::Single(s) => s.request_action()?,
            Self::Pair(s) => s.request_action()?,
        };
        Ok(())
    }
}
fn action_spec(stage: u8, paired: bool, observation: bool, quiet: bool) -> ActionSpecification {
    let mut s:ActionSpecification=serde_json::from_value(serde_json::json!({"stage":stage,"steps":11,"turnEvery":3,"seed":18446744073709551615u64,"comparePrevious":paired,"mode":"independentGeneration","promptVersion":2,"noiseAmplitude":0.013})).unwrap();
    s.language = language(true);
    if observation {
        s.comparison_kind = ComparisonKind::Observation;
        s.forcing_profile = ForcingProfile::ContinuousSensoryV1;
    }
    if quiet {
        s.input_strength = 0.0;
        s.noise_amplitude = 0.0;
        s.bias_enabled = false;
    }
    s
}
fn resolve(
    s: &mut ActionEngine,
    root: &Path,
    outcome: &str,
    target: Arm,
    attempted: &mut bool,
) -> AnyResult<bool> {
    loop {
        if let Some((a, p)) = s.memory() {
            s.read(root, a, &p)?;
        } else if let Some((a, p)) = s.language() {
            let changed = !*attempted
                && a == target
                && !matches!(outcome, "complete" | "stopped-prefix" | "manual");
            if changed {
                *attempted = true;
            }
            if changed && outcome == "cancel-prepared" {
                s.cancel(a, &p)?;
                return Ok(true);
            }
            s.start(a, &p)?;
            if changed && outcome == "transport" {
                s.fail(a, &p)?;
                continue;
            }
            if changed && outcome == "cancel-started" {
                s.cancel(a, &p)?;
                return Ok(true);
            }
            let wait =
                p.prompt.contains("Choose WRITE_JOURNAL or WAIT.") && p.turn_id.is_multiple_of(3);
            let mut r = response(if wait {
                r#"{"action":"WAIT","text":""}"#.into()
            } else {
                r#"{"action":"WRITE_JOURNAL","text":"I notice a retained pattern and remember a quiet change."}"#.into()
            });
            if changed {
                match outcome {
                    "incomplete" => r.complete = false,
                    "length" => r.stop_reason = Some("length".into()),
                    "negative-tokens" => r.token_count = Some(-1),
                    "malformed" => r.text = "not JSON".into(),
                    "forced-wait" => r.text = r#"{"action":"WAIT","text":""}"#.into(),
                    "empty-write" => r.text = r#"{"action":"WRITE_JOURNAL","text":""}"#.into(),
                    "oversized" => r.text = "x".repeat(65_537),
                    "unsupported" => r.text = r#"{"action":"WAIT","text":"",}"#.into(),
                    _ => {}
                }
            }
            if changed && outcome == "unsupported" {
                if s.confirm(a, &p, &r).is_ok() {
                    return Err("Ambiguous JSON unexpectedly settled".into());
                }
                s.cancel(a, &p)?;
                return Ok(true);
            }
            s.confirm(a, &p, &r)?;
        } else if let Some((a, p)) = s.journal() {
            s.save(root, a, &p)?;
        } else {
            return Ok(false);
        }
    }
}
fn action_fixture(
    root: &Path,
    name: &str,
    spec: ActionSpecification,
    outcome: &str,
    target: Arm,
    records: &mut Vec<serde_json::Value>,
) -> AnyResult<()> {
    let journal_root = root.join(format!("{name}.journals"));
    fs::create_dir(&journal_root)?;
    let mut s = ActionEngine::new(spec)?;
    let mut attempted = false;
    for step in 1..=11 {
        s.advance()?;
        if resolve(&mut s, &journal_root, outcome, target, &mut attempted)? || s.done() {
            break;
        }
        if outcome == "stopped-prefix" && step == 6 {
            s.stop()?;
            break;
        }
        if outcome == "manual" && step == 7 {
            s.manual()?;
            resolve(&mut s, &journal_root, "complete", target, &mut attempted)?;
        }
    }
    write_record(root, name, &s.record()?, records)
}
fn main() -> AnyResult<()> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let [directory] = args.as_slice() else {
        return Err("Use language_session_fixtures NEW_OUTPUT_DIRECTORY".into());
    };
    let root = Path::new(directory);
    fs::create_dir(root)?;
    let mut records = vec![];
    for stage in [3, 4] {
        for outcome in [
            "complete",
            "stopped-prefix",
            "incomplete",
            "length",
            "negative-tokens",
            "empty",
            "oversized",
            "transport",
            "cancel-prepared",
            "cancel-started",
            "unsupported",
        ] {
            stage_fixture(root, stage, outcome, &mut records)?;
        }
    }
    for stage in 4..=8 {
        for paired in [false, true] {
            let prefix = if paired { "pair" } else { "single" };
            action_fixture(
                root,
                &format!("{prefix}-{stage}-complete"),
                action_spec(stage, paired, false, false),
                "complete",
                Arm::Right,
                &mut records,
            )?;
        }
    }
    for quiet in [false, true] {
        action_fixture(
            root,
            &format!(
                "observation-{}-complete",
                if quiet { "quiet" } else { "active" }
            ),
            action_spec(4, true, true, quiet),
            "complete",
            Arm::Right,
            &mut records,
        )?;
    }
    for outcome in [
        "stopped-prefix",
        "manual",
        "incomplete",
        "length",
        "negative-tokens",
        "malformed",
        "forced-wait",
        "empty-write",
        "oversized",
        "transport",
        "cancel-prepared",
        "cancel-started",
        "unsupported",
    ] {
        let stage = if outcome == "manual" { 8 } else { 5 };
        action_fixture(
            root,
            &format!("single-{stage}-{outcome}"),
            action_spec(stage, false, false, false),
            outcome,
            Arm::Right,
            &mut records,
        )?;
    }
    for observation in [false, true] {
        for target in [Arm::Left, Arm::Right] {
            for outcome in [
                "transport",
                "incomplete",
                "cancel-prepared",
                "cancel-started",
            ] {
                let name = format!(
                    "{}-{:?}-{outcome}",
                    if observation { "observation" } else { "pair" },
                    target
                )
                .to_lowercase();
                action_fixture(
                    root,
                    &name,
                    action_spec(if observation { 4 } else { 6 }, true, observation, false),
                    outcome,
                    target,
                    &mut records,
                )?;
            }
        }
    }
    let manifest = serde_json::json!({"schema":"reservoir-core.supplied-language-fixtures.v1","scope":"Typed injected provider responses and actual fixture-directory save/readback; no HTTP requests, model execution, app-store or provider authentication","records":records,"modelsContacted":false,"liveSourcesRead":false});
    write_new(
        &root.join("manifest.json"),
        &serde_json::to_vec_pretty(&manifest)?,
    )?;
    println!("{}", root.join("manifest.json").display());
    Ok(())
}
