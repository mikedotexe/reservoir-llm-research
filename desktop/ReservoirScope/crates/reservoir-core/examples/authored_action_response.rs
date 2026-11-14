//! Numerical action qualification with scripted prose and matched exogenous
//! forcing. No provider, app store, historical data, or live being is contacted.
//! Save receipts are simulated in memory here; host durability has separate tests.
use reservoir_core::{session::LanguageResponse, sustained::*};
use serde_json::{json, Value};
use std::{error::Error, fs, path::Path};

type Result<T> = std::result::Result<T, Box<dyn Error>>;
const STEPS: u64 = 300;
const ACTION_STEP: u64 = 31;
const RELEASE_STEP: u64 = 151;
const BODY: &str = "I am keeping a record of this step and its consequences.";

struct Run {
    frames: Vec<SustainedFrame>,
    evidence: Value,
}

fn run(seed: u64, action: &str) -> Result<Run> {
    let mut config = serde_json::to_value(SustainedSpecification::default())?;
    config["seed"] = json!(seed);
    config["turnEvery"] = json!(10);
    config["maximumSteps"] = json!(STEPS);
    config["maximumTurns"] = json!(40);
    config["sensoryNoiseAmplitude"] = json!(0.5);
    config["feedbackScale"] = json!(0.4);
    config["promptVersion"] = json!("reservoir-journal-actions-v1");
    config["actionMode"] = json!("authored-v1");
    let mut session = SustainedSession::new(serde_json::from_value(config.clone())?)?;
    let mut frames = Vec::new();
    let mut journals = Vec::new();
    while session.step() < STEPS {
        if let Some(memory) = session.pending_memory().cloned() {
            session.confirm_memory(memory.entry.as_ref().ok_or("expected latest memory")?)?;
        }
        if let Some(pending) = session.pending_language().cloned() {
            let choice = match pending.turn_id {
                3 => action,
                15 => "RELEASE",
                _ => "NONE",
            };
            session.start_language(pending.attempt_id)?;
            session.confirm_language(
                pending.attempt_id,
                &LanguageResponse {
                    text: format!("{BODY}\n\nNEXT: {choice}"),
                    provider_model: None,
                    stop_reason: Some("stop".into()),
                    token_count: None,
                    complete: true,
                    provider_prompt_evaluation: None,
                },
            )?;
        }
        if let Some(pending) = session.pending_journal().cloned() {
            journals.push(serde_json::to_value(&pending)?);
            session.confirm_saved(
                &SustainedSaveReceipt {
                    entry_id: pending.entry.id.clone(),
                    sha256: pending.entry.sha256.clone(),
                    relative_path: format!("journals/{}.json", pending.entry.id),
                },
                &pending.entry,
            )?;
        }
        if let Some(pending) = session.prepared_application() {
            session.authorize_application(pending.entry.attempt_id)?;
        }
        let frame = session.advance()?;
        if frame.state.iter().any(|x| !x.is_finite() || x.abs() > 1.0)
            || !frame.sensory.fill_percent.is_finite()
        {
            return Err(format!("nonfinite/out-of-range state at step {}", frame.step).into());
        }
        frames.push(frame);
        if let Some(last) = session.events().back() {
            let id = last.id;
            session.acknowledge_events(id)?;
        }
    }
    let evidence = json!({
        "config": config,
        "intervention": action,
        "actionStep": ACTION_STEP,
        "releaseStep": RELEASE_STEP,
        "journalBody": BODY,
        "journals": journals,
        "frames": frames,
        "finalCheckpoint": session.checkpoint(),
    });
    Ok(Run { frames, evidence })
}

fn distance(left: &[f64], right: &[f64]) -> f64 {
    left.iter()
        .zip(right)
        .map(|(a, b)| (a - b).powi(2))
        .sum::<f64>()
        .sqrt()
}

fn compare(control: &Run, actual: &Run, action: &str) -> Result<Value> {
    let deltas: Vec<Value> = control
        .frames
        .iter()
        .zip(&actual.frames)
        .map(|(c, a)| {
            json!({
                "step": a.step,
                "recurrentL2": distance(&c.state, &a.state),
                "sensoryFillDifferencePoints": a.sensory.fill_percent - c.sensory.fill_percent,
                "matchedRecurrenceNoise": c.noise == a.noise,
                "matchedSensoryNoise": c.sensory_noise == a.sensory_noise,
                "nearSaturatedCoordinates": a.state.iter().filter(|x| x.abs() >= 0.999).count(),
            })
        })
        .collect();
    for row in &deltas {
        if row["matchedRecurrenceNoise"] != true || row["matchedSensoryNoise"] != true {
            return Err("action consumed or changed an exogenous noise stream".into());
        }
        if row["step"].as_u64().unwrap() < ACTION_STEP && row["recurrentL2"] != 0.0 {
            return Err("paired paths diverged before intervention".into());
        }
    }
    let first = deltas[(ACTION_STEP - 1) as usize]["recurrentL2"]
        .as_f64()
        .unwrap();
    if action == "NONE" && deltas.iter().any(|d| d["recurrentL2"] != 0.0) {
        return Err("NONE comparison changed recurrent state".into());
    }
    if action != "NONE" && first <= 1e-12 {
        return Err("declared intervention had no measurable immediate effect".into());
    }
    let receipt = actual.frames[(ACTION_STEP - 1) as usize]
        .action_receipt
        .as_ref()
        .ok_or("missing intervention receipt")?;
    if (receipt.state_delta_l2 - first).abs() > 1e-12 {
        return Err("reported immediate action effect differs from independent paired path".into());
    }
    let release = actual.frames[(RELEASE_STEP - 1) as usize]
        .action_receipt
        .as_ref()
        .ok_or("missing RELEASE receipt")?;
    if !matches!(release.request, Some(SustainedActionRequest::Release))
        || release.controls_after
            != (SustainedActionControls {
                leak: 0.65,
                recurrent_gain: 1.0,
                feedback_scale: 0.4,
            })
    {
        return Err("RELEASE did not restore configured controls".into());
    }
    let maximum = deltas
        .iter()
        .map(|d| d["recurrentL2"].as_f64().unwrap())
        .fold(0.0_f64, f64::max);
    let saturated = deltas
        .iter()
        .map(|d| d["nearSaturatedCoordinates"].as_u64().unwrap())
        .max()
        .unwrap();
    let samples: Vec<_> = [
        ACTION_STEP,
        ACTION_STEP + 10,
        ACTION_STEP + 60,
        RELEASE_STEP - 1,
        RELEASE_STEP,
        RELEASE_STEP + 10,
        STEPS,
    ]
    .into_iter()
    .map(|step| deltas[(step - 1) as usize].clone())
    .collect();
    Ok(
        json!({"firstRecurrentL2":first,"maximumRecurrentL2":maximum,
        "maximumNearSaturatedCoordinates":saturated,"samples":samples,"trajectory":deltas}),
    )
}

fn write(path: &Path, value: &Value) -> Result<()> {
    fs::write(path, serde_json::to_vec_pretty(value)?)?;
    Ok(())
}

fn main() -> Result<()> {
    let arguments: Vec<_> = std::env::args().skip(1).collect();
    let [directory] = arguments.as_slice() else {
        return Err("Usage: authored_action_response NEW_OUTPUT_DIRECTORY".into());
    };
    let directory = Path::new(directory);
    fs::create_dir(directory)?;
    let cases = [
        ("none", "NONE"),
        ("pulse-uniform-small", "PULSE uniform 0.1"),
        ("pulse-uniform-positive", "PULSE uniform 1"),
        ("pulse-uniform-negative", "PULSE uniform -1"),
        ("pulse-alternating", "PULSE alternating 0.5"),
        ("pulse-axis0", "PULSE axis0 1"),
        ("pulse-axis1", "PULSE axis1 -1"),
        ("leak-low", "TUNE leak 0.05"),
        ("leak-high", "TUNE leak 1"),
        ("recurrent-off", "TUNE recurrentGain 0"),
        ("recurrent-high", "TUNE recurrentGain 2"),
        ("feedback-off", "TUNE feedbackScale 0"),
        ("feedback-high", "TUNE feedbackScale 2"),
    ];
    let mut outcomes = Vec::new();
    for seed in [20260909, 20260910] {
        let control = run(seed, "NONE")?;
        write(
            &directory.join(format!("{seed}-control.json")),
            &control.evidence,
        )?;
        for (name, action) in cases {
            let result = run(seed, action).and_then(|actual| {
                let comparison = compare(&control, &actual, action)?;
                write(
                    &directory.join(format!("{seed}-{name}.json")),
                    &json!({"run":actual.evidence,"comparison":comparison}),
                )?;
                Ok(comparison)
            });
            match result {
                Ok(mut summary) => {
                    summary.as_object_mut().unwrap().remove("trajectory");
                    outcomes.push(json!({"seed":seed,"case":name,"action":action,
                        "status":"passed","result":summary}));
                }
                Err(error) => outcomes.push(json!({"seed":seed,"case":name,
                    "action":action,"status":"failed","error":error.to_string()})),
            }
        }
    }
    let passed = outcomes.iter().all(|o| o["status"] == "passed");
    let report = json!({
        "format":"authored-action-response-v1",
        "modelsContacted":false,
        "status":if passed {"passed"} else {"failed"},
        "scope":"Paired scripted 300-step paths with identical prose and exogenous noise. Text encoding may respond to the resulting sensory state. In-memory save receipts, not host durability or model behavior. No subjective-effect inference.",
        "seeds":[20260909,20260910],"caseCount":outcomes.len(),"nearSaturationThreshold":0.999,
        "actionStep":ACTION_STEP,"releaseStep":RELEASE_STEP,"outcomes":outcomes,
    });
    write(&directory.join("report.json"), &report)?;
    println!("{}", directory.join("report.json").display());
    if !passed {
        return Err("one or more action comparisons failed".into());
    }
    Ok(())
}
