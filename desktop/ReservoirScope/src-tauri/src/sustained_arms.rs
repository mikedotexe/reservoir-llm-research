//! Research-only headless arm runner for S-010. Ignored by default; driven by environment
//! variables, it creates one sustained session in a private store with the real local
//! transport, lets it run until a journal count, a terminal phase or a wall-clock bound,
//! then pauses and stops it. A reply the core refuses (token-limited, incomplete,
//! whitespace) is retained as a blocked attempt; arm policy skips it explicitly, counts
//! it and continues. It touches no live system and adds no product surface.
//!
//! ARM_STORE=<dir> ARM_CONFIG=<SustainedConfig json file> ARM_ENTRIES=<n> ARM_MINUTES=<m>
//! cargo test --locked -p reservoir-scope-desktop run_arm_from_env -- --ignored --nocapture
use super::*;
use std::time::{Duration, Instant};

#[test]
#[ignore]
fn run_arm_from_env() {
    let store = std::env::var("ARM_STORE").expect("ARM_STORE");
    let config_path = std::env::var("ARM_CONFIG").expect("ARM_CONFIG");
    let entries: u64 = std::env::var("ARM_ENTRIES")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(12);
    let minutes: u64 = std::env::var("ARM_MINUTES")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(40);
    let config: SustainedConfig =
        serde_json::from_slice(&fs::read(&config_path).expect("config file")).expect("config json");
    let s = SustainedState::new(PathBuf::from(&store));
    let created = s.create("arm-create".into(), config).expect("create");
    let m = created.summary.expect("summary");
    eprintln!("arm session {} created in {store}", m.session_id);
    s.start("arm-start".into(), &m.session_id, &m.generation)
        .expect("start");
    let started = Instant::now();
    let mut last_report = 0u64;
    let mut skipped = 0u64;
    loop {
        std::thread::sleep(Duration::from_secs(2));
        let (phase, count, step, worker, blocked_attempt) = {
            let g = s.lock().expect("lock");
            let a = g.active.as_ref().expect("active");
            (
                a.manifest.phase.clone(),
                a.manifest.journal_count,
                a.manifest.step,
                a.worker_active,
                a.engine.blocked().map(|b| b.pending.attempt_id),
            )
        };
        if count != last_report {
            eprintln!(
                "arm {} · step {step} · journals {count} · phase {phase} · {:.0}s",
                m.session_id,
                started.elapsed().as_secs_f64()
            );
            last_report = count;
        }
        if phase == "attemptBlocked" && !worker {
            if let Some(attempt) = blocked_attempt {
                match s.skip(
                    "arm-skip".into(),
                    &m.session_id,
                    &m.generation,
                    None,
                    Some(attempt),
                ) {
                    Ok(_) => {
                        skipped += 1;
                        eprintln!(
                            "arm {} · skipped blocked attempt {attempt} at step {step}",
                            m.session_id
                        );
                        if let Err(e) = s.start("arm-resume".into(), &m.session_id, &m.generation) {
                            eprintln!("arm {} · resume failed: {}", m.session_id, e.message);
                        }
                        continue;
                    }
                    Err(e) => eprintln!("arm {} · skip failed: {}", m.session_id, e.message),
                }
            }
        }
        let terminal = matches!(
            phase.as_str(),
            "stopped" | "providerFailed" | "storageBlocked" | "budgetReached" | "interrupted"
        );
        if count >= entries || terminal || started.elapsed() > Duration::from_secs(minutes * 60) {
            if !terminal {
                let _ = s.pause("arm-pause".into(), &m.session_id, &m.generation);
                let settle = Instant::now();
                while settle.elapsed() < Duration::from_secs(240) {
                    std::thread::sleep(Duration::from_secs(1));
                    let g = s.lock().expect("lock");
                    let a = g.active.as_ref().expect("active");
                    if !a.worker_active {
                        break;
                    }
                }
                let _ = s.stop("arm-stop".into(), &m.session_id, &m.generation);
            }
            let g = s.lock().expect("lock");
            let a = g.active.as_ref().expect("active");
            println!(
                "{{\"sessionId\":\"{}\",\"phase\":\"{}\",\"journals\":{},\"step\":{},\"seconds\":{:.0},\"skipped\":{skipped}}}",
                m.session_id,
                a.manifest.phase,
                a.manifest.journal_count,
                a.manifest.step,
                started.elapsed().as_secs_f64()
            );
            break;
        }
    }
}
