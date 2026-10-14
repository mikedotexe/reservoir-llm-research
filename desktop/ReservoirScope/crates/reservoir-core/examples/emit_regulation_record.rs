//! Offline conformance helper, not a desktop generation command.
use reservoir_core::regulation::{RegulationExampleRecord, RegulationExampleSpecification};
use std::{env, error::Error, fs};
fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = env::args().skip(1).collect();
    match args.as_slice() {
        [command, path] if command == "generate" => {
            let record =
                RegulationExampleRecord::generate(RegulationExampleSpecification::default())?;
            fs::write(path, serde_json::to_vec(&record)?)?;
        }
        [command, path] if command == "windows" => {
            let record: RegulationExampleRecord = serde_json::from_slice(&fs::read(path)?)?;
            record.verify()?;
            let values:Vec<_>=[0,300,301,450,599,600,450,301,300,900].into_iter().map(|cursor|serde_json::json!({"cursor":cursor,"evidence":record.window_evidence(cursor)})).collect();
            println!("{}", serde_json::to_string(&values)?);
        }
        _ => return Err("Use generate FILE or windows FILE".into()),
    }
    Ok(())
}
