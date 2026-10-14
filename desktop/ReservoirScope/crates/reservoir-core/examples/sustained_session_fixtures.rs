//! Fresh private-directory segment/journal qualification. Supplied prose only;
//! no provider or app-store access and no historical/canonical source mutation.
use reservoir_core::{session::LanguageResponse, sustained::*};
use sha2::{Digest, Sha256};
use std::{
    error::Error,
    fs::{self, OpenOptions},
    io::Write,
    path::Path,
};
type R<T> = Result<T, Box<dyn Error>>;
fn digest(b: &[u8]) -> String {
    format!("{:x}", Sha256::digest(b))
}
fn publish(path: &Path, bytes: &[u8]) -> R<()> {
    let temp = path.with_extension("staging");
    let mut f = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&temp)?;
    f.write_all(bytes)?;
    f.sync_all()?;
    drop(f);
    if fs::read(&temp)? != bytes {
        return Err("staged byte mismatch".into());
    }
    // A hard link publishes without replacing a prior destination in this fresh
    // fixture directory. Platform/app storage support is a separate qualification.
    fs::hard_link(&temp, path)?;
    fs::remove_file(&temp)?;
    #[cfg(unix)]
    fs::File::open(path.parent().unwrap())?.sync_all()?;
    if fs::read(path)? != bytes {
        return Err("published byte mismatch".into());
    }
    Ok(())
}
fn flush(
    root: &Path,
    s: &mut SustainedSession,
    base: &mut SustainedCheckpoint,
    manifest: &mut Vec<serde_json::Value>,
) -> R<()> {
    if s.events().is_empty() {
        return Ok(());
    }
    let segment = SustainedSegment {
        format: FORMAT.into(),
        initial_checkpoint: base.clone(),
        events: s.events().iter().cloned().collect(),
        final_checkpoint: s.checkpoint(),
    };
    segment.verify()?;
    let filename = format!("segment-{:05}.json", manifest.len() + 1);
    let bytes = serde_json::to_vec(&segment)?;
    publish(&root.join(&filename), &bytes)?;
    manifest.push(serde_json::json!({"file":filename,"sha256":digest(&bytes),"bytes":bytes.len(),"startStep":segment.initial_checkpoint.state.step,"endStep":segment.final_checkpoint.state.step,"startCheckpoint":segment.initial_checkpoint.sha256,"endCheckpoint":segment.final_checkpoint.sha256,"events":segment.events.len()}));
    s.acknowledge_events(segment.events.last().unwrap().id)?;
    *base = segment.final_checkpoint;
    Ok(())
}
#[derive(Default)]
struct Measurements {
    maximum_outbox: usize,
    maximum_checkpoint_bytes: usize,
}
impl Measurements {
    fn observe(&mut self, s: &SustainedSession) -> R<()> {
        self.maximum_outbox = self.maximum_outbox.max(s.events().len());
        self.maximum_checkpoint_bytes = self
            .maximum_checkpoint_bytes
            .max(serde_json::to_vec(&s.checkpoint())?.len());
        Ok(())
    }
}
fn main() -> R<()> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let [directory] = args.as_slice() else {
        return Err("Use sustained_session_fixtures NEW_OUTPUT_DIRECTORY".into());
    };
    let root = Path::new(directory);
    fs::create_dir(root)?;
    fs::create_dir(root.join("journals"))?;
    let spec = SustainedSpecification {
        seed: u64::MAX,
        turn_every: 10,
        maximum_steps: 180,
        maximum_turns: 30,
        ..Default::default()
    };
    let mut s = SustainedSession::new(spec)?;
    let mut base = s.checkpoint();
    let genesis = base.clone();
    let mut manifest = vec![];
    let mut interrupted = false;
    let mut measurements = Measurements::default();
    measurements.observe(&s)?;
    while s.step() < 180 {
        if let Some(memory) = s.pending_memory().cloned() {
            let pending: SustainedPendingJournal =
                serde_json::from_slice(&fs::read(root.join(memory.relative_path))?)?;
            s.confirm_memory(&pending.entry)?;
            measurements.observe(&s)?;
        }
        if let Some(p) = s.pending_language().cloned() {
            if !interrupted {
                flush(root, &mut s, &mut base, &mut manifest)?;
                s = SustainedSession::restore(serde_json::from_slice(&serde_json::to_vec(
                    &s.checkpoint(),
                )?)?)?;
                measurements.observe(&s)?;
                s.retry_language()?;
                measurements.observe(&s)?;
                interrupted = true;
                continue;
            }
            s.start_language(p.attempt_id)?;
            measurements.observe(&s)?;
            s.confirm_language(p.attempt_id,&LanguageResponse{text:format!("I notice the retained pattern at observation {} and will watch how the next state changes.",p.turn_id),provider_model:None,stop_reason:Some("stop".into()),token_count:Some(22),complete:true,provider_prompt_evaluation:None})?;
            measurements.observe(&s)?;
        }
        if let Some(p) = s.pending_journal().cloned() {
            // Persist the accepted-response boundary before publishing the journal.
            flush(root, &mut s, &mut base, &mut manifest)?;
            let relative = format!("journals/{}.json", p.entry.id);
            let bytes = serde_json::to_vec(&p)?;
            publish(&root.join(&relative), &bytes)?;
            let readback: SustainedPendingJournal =
                serde_json::from_slice(&fs::read(root.join(&relative))?)?;
            s.confirm_saved(
                &SustainedSaveReceipt {
                    entry_id: p.entry.id.clone(),
                    sha256: p.entry.sha256.clone(),
                    relative_path: relative,
                },
                &readback.entry,
            )?;
            measurements.observe(&s)?;
            // Persist prepared feedback before granting permission to use it.
            flush(root, &mut s, &mut base, &mut manifest)?;
        }
        if let Some(p) = s.prepared_application() {
            let id = p.entry.attempt_id;
            s.authorize_application(id)?;
        }
        s.advance()?;
        measurements.observe(&s)?;
        if s.events().len() >= 32 {
            flush(root, &mut s, &mut base, &mut manifest)?;
        }
    }
    flush(root, &mut s, &mut base, &mut manifest)?;
    let result = serde_json::json!({"schema":"reservoir-sustained-fixture-manifest-v1","scope":"180 numerical steps with injected replies, real private-directory journal publication/readback, explicit interrupted preparation retry, immutable bounded segments; not wall-time soak or model execution","modelsContacted":false,"genesis":genesis,"segments":manifest,"finalCheckpoint":s.checkpoint(),"maximumRetainedEvents":measurements.maximum_outbox,"maximumCheckpointBytes":measurements.maximum_checkpoint_bytes});
    publish(
        &root.join("manifest.json"),
        &serde_json::to_vec_pretty(&result)?,
    )?;
    println!("{}", root.join("manifest.json").display());
    Ok(())
}
