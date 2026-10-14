//! Test-only evaluator runner. Input includes deliberately unverified mutations;
//! never use this harness to accept a record or infer a verification outcome.
use reservoir_core::{
    actions::ActionComparisonRecord,
    guided_evidence::{evaluate, unopened},
};
use serde::Deserialize;
#[derive(Deserialize)]
struct Request {
    name: String,
    record: Option<ActionComparisonRecord>,
    cursors: Vec<usize>,
    #[serde(default)]
    verify: bool,
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let path = std::env::args()
        .nth(1)
        .ok_or("pass conformance batch JSON path")?;
    let requests: Vec<Request> = serde_json::from_slice(&std::fs::read(path)?)?;
    let mut rows = Vec::new();
    for request in requests {
        if request.verify {
            if let Some(record) = &request.record {
                record.verify()?;
            }
        }
        for cursor in request.cursors {
            let evidence = request
                .record
                .as_ref()
                .map_or_else(unopened, |record| evaluate(record, cursor));
            rows.push(serde_json::json!({"name":request.name,"cursor":cursor,"evidence":evidence}));
        }
    }
    println!("{}", serde_json::to_string(&rows)?);
    Ok(())
}
