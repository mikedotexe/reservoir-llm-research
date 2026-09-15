//! Finite reference run from the qualified pre-action ESN source.
//! The runner copies only native numerical modules; no runtime or live I/O.
mod buffer_pool;
mod esn;
mod gpu;

use anyhow::{ensure, Result};
use esn::{EsnSnapshotV2, ESN};
use gpu::Gpu;
use serde_json::json;
use std::{fs, path::PathBuf};

fn input(t: usize) -> Vec<f32> {
    (0..66)
        .map(|i| 0.15_f32 * (((t * 7 + i * 3) as f32) * 0.071_f32).sin())
        .collect()
}

fn main() -> Result<()> {
    let output = PathBuf::from(std::env::args().nth(1).expect("new output directory"));
    ensure!(!output.exists(), "output must be new");
    fs::create_dir_all(&output)?;
    let gpu = Gpu::new()?;
    let mut cases = Vec::new();
    for start in [24_usize, 96, 192] {
        let mut rng = fastrand::Rng::with_seed(3517018368);
        let mut parent = ESN::new(128, 66, 0.25, 0.15, 0.95, 0.35, 0.999, &gpu, &mut rng)?;
        parent.set_profiling_enabled(false);
        for tick in 0..start { parent.step(&input(tick))?; }
        let checkpoint = parent.snapshot_v2()?;
        for alternating in [false, true] {
            let mut copy = ESN::from_snapshot_v2(&checkpoint, &gpu)?;
            let mut path = vec![copy.x.clone()];
            let mut traces = Vec::new();
            let mut inputs = Vec::new();
            let mut rhos = Vec::new();
            for offset in 0..100 {
                let rho = if alternating && offset % 2 == 0 { 0.82_f32 } else { 0.999_f32 };
                copy.set_rho_direct(rho);
                let u = input(start + offset);
                copy.step(&u)?;
                inputs.push(u);
                rhos.push(rho);
                path.push(copy.x.clone());
                traces.push(copy.last_step_trace().clone());
            }
            let final_snapshot: EsnSnapshotV2 = copy.snapshot_v2()?;
            cases.push(json!({"start":start,"alternating_rho":alternating,
                "checkpoint":checkpoint,"inputs":inputs,"rhos":rhos,
                "path":path,"traces":traces,"final_snapshot":final_snapshot}));
        }
    }
    fs::write(output.join("baseline.json"), serde_json::to_vec(&json!({
        "schema":"research.native_state_action_baseline.v1",
        "source_revision":env!("RESEARCH_BASE_REVISION"),
        "source_sha256":env!("RESEARCH_BASE_ESN_SHA256"),
        "cases":cases
    }))?)?;
    println!("Saved six complete reference continuations (three checkpoints, two rho schedules).");
    Ok(())
}
