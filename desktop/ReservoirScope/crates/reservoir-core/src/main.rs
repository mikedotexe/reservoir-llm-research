use reservoir_core::{stage, verify_file, CoreError};
use std::{env, fs::OpenOptions, io::Write, path::Path};

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.len() >= 2
        && args[0] == "verify"
        && (args.len() == 2 || (args.len() == 3 && args[2] == "--json"))
    {
        let report = verify_file(Path::new(&args[1]));
        if args.len() == 3 {
            println!("{}", serde_json::to_string(&report).expect("finite report"));
        } else {
            println!("{:?}: {}", report.status, report.diagnostics.join("; "));
        }
        std::process::exit(report.exit_code());
    }
    if args.len() == 5 && args[0] == "run" && args[1] == "--config" && args[3] == "--output" {
        let result = run(&args[2], &args[4]);
        match result {
            Ok(steps) => {
                println!(
                    "Completed and verified {steps} scripted stage steps. Saved {}",
                    args[4]
                );
                return;
            }
            Err(error) => {
                eprintln!("reservoir-core: {error}");
                std::process::exit(if matches!(error, CoreError::Unsupported(_)) {
                    2
                } else {
                    1
                });
            }
        }
    }
    eprintln!("reservoir-core verify FILE [--json]\nreservoir-core run --config SPEC.json --output NEW_RUN.json\nNo model service is contacted. Verification supports stage/exploration/action numerical records and scoped case/geometry integrity checks; other families and unsupported text return incomplete. Running creates scripted stages only.");
    if !args.is_empty() && args != ["--help"] {
        std::process::exit(1);
    }
}

fn run(config: &str, output: &str) -> reservoir_core::Result<usize> {
    let size = std::fs::metadata(config).map_err(|e| CoreError::Invalid(e.to_string()))?;
    if !size.is_file() || size.len() > 1024 * 1024 {
        return Err(CoreError::Invalid(
            "Recipe must be a regular file no larger than 1 MiB".into(),
        ));
    }
    let bytes = reservoir_core::read_record_bytes(Path::new(config))?;
    if bytes.len() > 1024 * 1024 {
        return Err(CoreError::Invalid("Recipe exceeds 1 MiB".into()));
    }
    let spec: stage::RunSpecification =
        serde_json::from_slice(&bytes).map_err(|e| CoreError::Invalid(e.to_string()))?;
    let record = stage::run_scripted(spec)?;
    let encoded = serde_json::to_vec(&record).map_err(|e| CoreError::Invalid(e.to_string()))?;
    if encoded.len() > reservoir_core::MAX_RECORD_BYTES {
        return Err(CoreError::Invalid(
            "Generated record exceeds 256 MiB".into(),
        ));
    }
    // Do not replace an existing export, fixture or recipe. Write errors are explicit.
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(output)
        .map_err(|e| CoreError::Invalid(format!("Cannot create new output: {e}")))?;
    file.write_all(&encoded)
        .and_then(|_| file.sync_all())
        .map_err(|e| CoreError::Invalid(format!("Output write did not complete: {e}")))?;
    Ok(record.frames.len())
}
