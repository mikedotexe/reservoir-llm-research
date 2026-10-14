//! Exact retained-response comparison output for the unchanged native oracle.
use reservoir_core::response::{NativeResponse, SimulationResponse};
use serde_json::json;
use sha2::{Digest, Sha256};
fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn array(bytes: &mut Vec<u8>, values: Option<Vec<f64>>) {
    if let Some(values) = values {
        bytes.push(1);
        bytes.extend((values.len() as u64).to_le_bytes());
        for v in values {
            bytes.extend(v.to_le_bytes());
        }
    } else {
        bytes.push(0);
    }
}
fn scalar(bytes: &mut Vec<u8>, value: Option<f64>) {
    if let Some(v) = value {
        bytes.push(1);
        bytes.extend(v.to_le_bytes());
    } else {
        bytes.push(0);
    }
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    if !(3..=4).contains(&args.len()) {
        return Err(
            "usage: response_oracle native|simulation FILE [PREVIOUS_FILE|EXPECTED_SHA256]".into(),
        );
    }
    let bytes = std::fs::read(&args[2])?;
    let out = match args[1].as_str() {
        "native" => {
            let n = NativeResponse::decode(&bytes)?;
            if let Some(path) = args.get(3) {
                n.validate_replacement(&NativeResponse::decode(&std::fs::read(path)?)?)?;
            }
            let receipts:Vec<_>=n.receipts.iter().map(|r|{
                let mut b=vec![];
                for v in [Some(&r.direction),r.before.as_ref(),r.after.as_ref(),r.delta.as_ref(),r.realized_noise.as_ref()]{array(&mut b,v.map(|v|v.iter().copied().map(f64::from).collect()));}
                for v in [r.requested_amount.map(f64::from),r.attenuation.map(f64::from),r.max_abs_delta.map(f64::from),r.effective_leak.map(f64::from),r.actual_l2]{scalar(&mut b,v);}
                json!({"status":r.status,"frameId":r.frame_id(),"successfulStepId":r.successful_step_id.map(|v|v.to_string()),"observedAtUnixMs":r.observed_at_unix_ms.to_string(),"boundaryWaitUs":r.boundary_wait_us.map(|v|v.to_string()),"numericSha256":hash(&b)})
            }).collect();
            json!({"kind":"native","fileSha256":n.file_sha256,"receiptCount":n.receipts.len(),"frameCount":n.frame_indices.len(),"boundaryCount":n.boundary_indices.len(),"deltaScale":n.delta_scale(),"receipts":receipts})
        }
        "simulation" => {
            let s = if let Some(expected) = args.get(3) {
                SimulationResponse::decode_with_hash(&bytes, expected)?
            } else {
                SimulationResponse::decode(&bytes)?
            };
            let frames:Vec<_>=s.frames.iter().map(|f|{let mut b=vec![];for v in [&f.control,&f.intervention,&f.delta]{array(&mut b,Some(v.clone()));}scalar(&mut b,Some(f.separation_l2));
                json!({"index":f.sample_index,"position":f.original_boundary_step.to_string(),"numericSha256":hash(&b)})}).collect();
            json!({"kind":"simulation","fileSha256":hash(&bytes),"frameCount":s.frames.len(),"nodeCount":s.node_count,"fixedDeltaScale":s.fixed_delta_scale(),"returnBoundary":s.result_summary.return_boundary,"returnStatus":s.result_summary.return_status,"peakGainOverInitial":s.result_summary.peak_gain_over_initial,"frames":frames})
        }
        _ => return Err("unknown response mode".into()),
    };
    println!("{out}");
    Ok(())
}
