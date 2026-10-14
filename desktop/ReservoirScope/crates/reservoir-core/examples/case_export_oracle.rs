//! Offline conformance harness; never used by the application or live providers.
use reservoir_core::cases::CaseCatalog;
use std::{error::Error, fs, io::Write};

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 5 {
        return Err("usage: case_export_oracle export|verify INPUT INDEX OUTPUT".into());
    }
    let catalog = CaseCatalog::decode(&fs::read(&args[2])?)?;
    if args[1] == "verify" {
        return Ok(());
    }
    if args[1] != "export" {
        return Err("unsupported operation".into());
    }
    let index: usize = args[3].parse()?;
    let item = catalog.cases.get(index).ok_or("invalid selection")?;
    let bytes = catalog.selected_encoded(index, &item.id)?;
    fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&args[4])?
        .write_all(&bytes)?;
    Ok(())
}
