//! Scripted local fixture only: no provider, network, or existing session access.
//! Writes prompts, real journal save/read-backs, frames and replayable segments into
//! an explicitly new output directory. It is numerical qualification, not a model study.
use reservoir_core::{session::LanguageResponse, sustained::*};
use serde::Serialize;
use std::{error::Error, fs, io::Write, path::Path};
type Result<T> = std::result::Result<T, Box<dyn Error>>;

fn write<T: Serialize>(path: &Path, value: &T) -> Result<()> {
    let mut file = fs::OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)?;
    file.write_all(&serde_json::to_vec_pretty(value)?)?;
    file.sync_all()?;
    Ok(())
}
fn main() -> Result<()> {
    let argument = std::env::args()
        .nth(1)
        .ok_or("Usage: continuity_probe_fixture NEW_OUTPUT_DIRECTORY")?;
    let root = Path::new(&argument);
    fs::create_dir(root)?;
    fs::create_dir(root.join("journals"))?;
    let specification = SustainedSpecification {
        action_mode: Some(SustainedActionMode::AuthoredV3),
        prompt_version: SustainedPromptVersion::ActionJournalV3,
        turn_every: 3,
        maximum_steps: 100,
        maximum_turns: 20,
        sensory_noise_amplitude: 0.5,
        feedback_scale: 0.4,
        ..Default::default()
    };
    let mut session = SustainedSession::new(specification)?;
    let mut base = session.checkpoint();
    write(&root.join("initial-checkpoint.json"), &base)?;
    let mut probe = vec![0.0; 48];
    probe[0] = 0.5;
    probe[47] = -0.25;
    let replies = [
        "Earlier writing supplies a real local reference.\nNEXT: TUNE leak 0.8".to_owned(),
        format!("I will compare the response to these numerical input coordinates.\nINQUIRY: OPEN both \"What changes after this input, and what was I writing earlier?\"\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: PROBE {}", serde_json::to_string(&probe)?),
        "The earlier question may remain open while I write about something else.\nNEXT: NONE".to_owned(),
        "I can now revisit a newer window of saved writing.\nINQUIRY: CONTINUE\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: NONE".to_owned(),
        "Restore the initial controls while retaining the accumulated state.\nNEXT: RELEASE".to_owned(),
        "Leave this question for now.\nINQUIRY: CLOSE\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE".to_owned(),
    ];
    let mut prompt_bytes = Vec::new();
    for (index, text) in replies.into_iter().enumerate() {
        while matches!(session.phase(), SustainedPhase::Ready) {
            session.advance()?;
        }
        if let Some(memory) = session.pending_memory().cloned() {
            let entry: SustainedJournal =
                serde_json::from_slice(&fs::read(root.join(memory.relative_path))?)?;
            session.confirm_memory(&entry)?;
        }
        let pending = session
            .pending_language()
            .ok_or("missing writing opportunity")?
            .clone();
        prompt_bytes.push(pending.prompt.len());
        write(&root.join(format!("prompt-{}.json", index + 1)), &pending)?;
        session.start_language(pending.attempt_id)?;
        session.confirm_language(
            pending.attempt_id,
            &LanguageResponse {
                text,
                provider_model: Some("scripted-local-fixture".into()),
                stop_reason: Some("stop".into()),
                token_count: None,
                complete: true,
                provider_prompt_evaluation: None,
            },
        )?;
        let journal = session.pending_journal().ok_or("missing journal")?.clone();
        let relative_path = format!("journals/{}.json", journal.entry.id);
        write(&root.join(&relative_path), &journal.entry)?;
        fs::File::open(root.join("journals"))?.sync_all()?;
        let readback: SustainedJournal =
            serde_json::from_slice(&fs::read(root.join(&relative_path))?)?;
        session.confirm_saved(
            &SustainedSaveReceipt {
                entry_id: readback.id.clone(),
                sha256: readback.sha256.clone(),
                relative_path,
            },
            &readback,
        )?;
        // Exercise a real serialized restoration while the OPEN+PROBE awaits authorization.
        if index == 1 {
            let prepared_segment = SustainedSegment {
                format: FORMAT.into(),
                initial_checkpoint: base.clone(),
                events: session.events().iter().cloned().collect(),
                final_checkpoint: session.checkpoint(),
            };
            prepared_segment.verify()?;
            write(
                &root.join("segment-2-before-restore.json"),
                &prepared_segment,
            )?;
            if let Some(event) = prepared_segment.events.last() {
                session.acknowledge_events(event.id)?;
            }
            base = prepared_segment.final_checkpoint;
            write(
                &root.join("prepared-checkpoint.json"),
                &session.checkpoint(),
            )?;
            session = SustainedSession::restore(serde_json::from_slice(&fs::read(
                root.join("prepared-checkpoint.json"),
            )?)?)?;
        }
        session.authorize_application(pending.attempt_id)?;
        let frame = session.advance()?;
        write(&root.join(format!("frame-{}.json", index + 1)), &frame)?;
        let segment = SustainedSegment {
            format: FORMAT.into(),
            initial_checkpoint: base,
            events: session.events().iter().cloned().collect(),
            final_checkpoint: session.checkpoint(),
        };
        segment.verify()?;
        let segment_path = root.join(format!("segment-{}.json", index + 1));
        write(&segment_path, &segment)?;
        let restored_segment: SustainedSegment = serde_json::from_slice(&fs::read(&segment_path)?)?;
        restored_segment.verify()?;
        if let Some(event) = segment.events.last() {
            session.acknowledge_events(event.id)?;
        }
        base = segment.final_checkpoint;
    }
    write(&root.join("final-checkpoint.json"), &session.checkpoint())?;
    println!(
        "{}",
        serde_json::json!({"fixture":"scripted-local-continuity-v3","turns":6,"promptBytes":prompt_bytes,"finalStep":session.step(),"inquiryClosed":session.action_state().unwrap().continuity.as_ref().unwrap().active_inquiry.is_none()})
    );
    Ok(())
}
