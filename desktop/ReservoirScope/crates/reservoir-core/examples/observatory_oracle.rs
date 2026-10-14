//! Emits compact digests of every decoded retained value for independent native
//! reader comparison. This is a test helper, not application IPC or a verifier.
use reservoir_core::observatory::{digest, HistoricalEvidence, StateReplay};
use serde_json::json;
use std::path::PathBuf;
fn numbers(values: impl IntoIterator<Item = Option<f64>>) -> Vec<u8> {
    let mut out = Vec::new();
    for value in values {
        match value {
            Some(v) => {
                out.push(1);
                out.extend(v.to_le_bytes());
            }
            None => out.push(0),
        }
    }
    out
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let root = PathBuf::from(
        std::env::args()
            .nth(1)
            .ok_or("usage: observatory_oracle RESOURCE_DIRECTORY")?,
    );
    let h = HistoricalEvidence::from_bytes(&std::fs::read(root.join("data.json"))?)?;
    let m = std::fs::read(root.join("state-replay.json"))?;
    let raw = std::fs::read(root.join("state-replay.bin"))?;
    let geometry = std::fs::read(root.join("state-geometry.json"))?;
    let s = StateReplay::from_bytes(&m, raw, &geometry)?;
    let history: Vec<Option<f64>> = h
        .samples
        .iter()
        .flat_map(|x| {
            vec![
                Some(x.t_s),
                Some(x.fill_pct),
                Some(x.cascade[0]),
                Some(x.cascade[1]),
                Some(x.cascade[2]),
                x.fill_rate_pct_per_s,
                x.esn_cov_lambda1,
                x.geom_radius,
                x.geom_rel,
                x.esn_leak,
                x.esn_lambda,
            ]
        })
        .collect();
    let states: Vec<Option<f64>> = (0..s.manifest.rows)
        .flat_map(|i| s.activations(i).unwrap().into_iter().map(Some))
        .collect();
    let geometry: Vec<Option<f64>> = s
        .geometry
        .samples
        .iter()
        .flat_map(|x| {
            vec![
                x.pc[0],
                x.pc[1],
                x.pc[2],
                x.state_rms,
                x.centered_rms,
                x.projected_rms,
                x.reconstruction_rmse,
                x.centered_norm,
                x.projected_norm,
                x.residual_norm,
            ]
        })
        .map(Some)
        .collect();
    let b = &h.bands;
    let bands = numbers([
        Some(b.shelf_min_pct),
        b.shelf_entry_pct,
        Some(b.target_pct),
        Some(b.shelf_max_pct),
        b.elevated_release_pct,
        Some(b.strong_rail_pct),
        Some(b.force_rail_pct),
    ]);
    let identities:Vec<_>=h.samples.iter().map(|x|json!({"utc":x.t_utc,"session":x.session_id.to_string(),"sourceIds":x.source_ids.as_ref().map(|ids|ids.iter().map(|id|id.map(|v|v.to_string())).collect::<Vec<_>>())})).collect();
    println!(
        "{}",
        json!({"historyCount":h.samples.len(),"stateRows":s.manifest.rows,"dimensions":s.manifest.dimensions,
        "historyNumericSHA256":digest(&numbers(history)),"stateNumericSHA256":digest(&numbers(states)),"geometryNumericSHA256":digest(&numbers(geometry)),"bandsNumericSHA256":digest(&bands),
        "historyIdentities":identities,"sourceSHA256":s.manifest.source_sha256,"geometrySHA256":s.manifest.geometry_sha256,"capturedAtUtc":s.manifest.captured_at_utc})
    );
    Ok(())
}
