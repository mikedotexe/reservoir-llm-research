//! Offline test helper: Rust-generated exploration histories for independent
//! Swift verification. Accepts one owned output directory, never live sources.
use reservoir_core::exploration::{ExplorationControls, ExplorationEngine, ExplorationRecord};
use std::{env, fs, path::PathBuf};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut arguments = env::args().skip(1);
    let output = PathBuf::from(arguments.next().ok_or("expected OUTPUT_DIRECTORY")?);
    if arguments.next().is_some() {
        return Err("expected exactly one argument".into());
    }
    fs::create_dir_all(&output)?;
    let fixtures = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/exploration");
    for name in [
        "empty-u64-max",
        "quiet-defaults",
        "pulsed-forcing",
        "control-transitions-u64-max",
        "sensory-restarts-u64-large",
    ] {
        let source: ExplorationRecord =
            serde_json::from_slice(&fs::read(fixtures.join(format!("{name}.json")))?)?;
        source.verify()?;
        let mut engine = ExplorationEngine::new(source.seed);
        for frame in &source.frames {
            engine.advance(frame.controls.clone(), frame.pulse)?;
        }
        let generated = engine.record();
        generated.verify()?;
        fs::write(
            output.join(format!("{name}.json")),
            serde_json::to_vec(&generated)?,
        )?;
    }
    // Independent Swift must also accept Rust continuation after importing Swift
    // state/covariance, including exact RNG position and a retained alternative basis.
    let mut source: ExplorationRecord =
        serde_json::from_slice(&fs::read(fixtures.join("sensory-restarts-u64-large.json"))?)?;
    for value in &mut source.frames[0].spectral.as_mut().unwrap().eigenvectors[..32] {
        *value = -*value;
    }
    let mut resumed = ExplorationEngine::from_record(&source)?;
    for step in 0..8 {
        resumed.advance(
            ExplorationControls {
                recurrence_enabled: true,
                repeat_input: true,
                noise_amplitude: 0.04,
                bias_enabled: step % 2 == 0,
                sensory_enabled: step != 3,
                retention: 0.94,
                ..Default::default()
            },
            step == 2,
        )?;
    }
    let record = resumed.record();
    record.verify()?;
    fs::write(
        output.join("swift-import-rust-continuation.json"),
        serde_json::to_vec(&record)?,
    )?;
    println!("Generated six bounded exploration records; no model calls");
    Ok(())
}
