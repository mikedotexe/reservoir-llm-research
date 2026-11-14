//! Offline held-input/leak diagnostic using the actual sustained numerical loop.
//! Synthetic projected vectors, scripted writing and in-memory save authorization;
//! no provider, app store, live being or six-hour-run record is contacted.
//! Input-switch intervals here are numerical steps, not end-to-end LLM cadence.
use reservoir_core::{codec, session::LanguageResponse, sustained::*};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{error::Error, fs, path::Path};

type Result<T> = std::result::Result<T, Box<dyn Error>>;
const STEPS: u64 = 300;
const CHANGE: u64 = 121;
const RESTORE: u64 = 151;
const SCALE: f64 = 0.4;
const PROJECTION_SEED: u64 = 99;
const SYNTHETIC_MODEL: &str = "synthetic-vector-fixture-no-model-called";
const BODY: &str = "This scripted entry carries a controlled numerical test input.";

#[derive(Clone, Copy, PartialEq)]
enum Input {
    Zero,
    A,
    B,
}
#[derive(Clone, Copy)]
enum Condition {
    Hold,
    Zero,
    Withdraw,
    Switch,
    QuietRestore,
    Alternate(u64),
}
impl Condition {
    fn name(self) -> String {
        match self {
            Self::Hold => "hold-a".into(),
            Self::Zero => "always-zero".into(),
            Self::Withdraw => "withdraw".into(),
            Self::Switch => "switch-a-to-b".into(),
            Self::QuietRestore => "quiet-30-restore".into(),
            Self::Alternate(cadence) => format!("alternate-{cadence}"),
        }
    }
    fn input(self, step: u64) -> Input {
        if step == 1 || matches!(self, Self::Zero) {
            return Input::Zero;
        }
        if step < CHANGE {
            return Input::A;
        }
        match self {
            Self::Hold => Input::A,
            Self::Zero | Self::Withdraw => Input::Zero,
            Self::Switch => Input::B,
            Self::QuietRestore if step < RESTORE => Input::Zero,
            Self::QuietRestore => Input::A,
            Self::Alternate(cadence) if ((step - CHANGE) / cadence).is_multiple_of(2) => Input::B,
            Self::Alternate(_) => Input::A,
        }
    }
}
struct Inputs {
    raw_a: Vec<f64>,
    raw_b: Vec<f64>,
    a: ExternalFeedback,
    b: ExternalFeedback,
}
impl Inputs {
    fn new() -> Result<Self> {
        let raw_a: Vec<f64> = (0..64).map(|i| (i as f64 * 0.37 + 0.4).sin()).collect();
        let raw_b: Vec<f64> = raw_a.iter().map(|x| -x).collect();
        let external = |raw: &[f64]| -> Result<ExternalFeedback> {
            Ok(ExternalFeedback {
                vector: codec::project_embedding(raw, PROJECTION_SEED)?,
                provenance: FeedbackProvenance {
                    kind: "embedding".into(),
                    model: SYNTHETIC_MODEL.into(),
                    digest: None,
                    dimensions: raw.len(),
                    embedding_sha256: format!("{:x}", Sha256::digest(serde_json::to_vec(raw)?)),
                    projection_seed: PROJECTION_SEED,
                },
            })
        };
        let a = external(&raw_a)?;
        let b = external(&raw_b)?;
        if a.vector.iter().zip(&b.vector).any(|(a, b)| a != &-b) {
            return Err("opposite synthetic cues failed projection symmetry".into());
        }
        Ok(Self { raw_a, raw_b, a, b })
    }
    fn get(&self, input: Input) -> Option<&ExternalFeedback> {
        match input {
            Input::Zero => None,
            Input::A => Some(&self.a),
            Input::B => Some(&self.b),
        }
    }
}
struct Run {
    frames: Vec<SustainedFrame>,
    evidence: Value,
}
fn norm(values: &[f64]) -> f64 {
    values.iter().map(|x| x * x).sum::<f64>().sqrt()
}
fn distance(a: &[f64], b: &[f64]) -> f64 {
    a.iter()
        .zip(b)
        .map(|(a, b)| (a - b).powi(2))
        .sum::<f64>()
        .sqrt()
}
fn run(seed: u64, leak: f64, condition: Condition, inputs: &Inputs) -> Result<Run> {
    let spec = SustainedSpecification {
        seed,
        leak,
        turn_every: 1,
        maximum_steps: STEPS,
        maximum_turns: STEPS + 1,
        noise_amplitude: 0.02,
        sensory_noise_amplitude: 0.5,
        feedback_scale: SCALE,
        action_mode: Some(SustainedActionMode::AuthoredV2),
        prompt_version: SustainedPromptVersion::ActionJournalV2,
        codec: SustainedCodec::Embedding {
            model: SYNTHETIC_MODEL.into(),
            projection_seed: PROJECTION_SEED,
        },
        ..Default::default()
    };
    let mut session = SustainedSession::new(spec.clone())?;
    let mut frames = Vec::new();
    let mut applications = Vec::new();
    while session.step() < STEPS {
        if let Some(memory) = session.pending_memory().cloned() {
            session.confirm_memory(memory.entry.as_ref().ok_or("expected latest memory")?)?;
        }
        if let Some(pending) = session.pending_language().cloned() {
            let input = condition.input(pending.observed_step + 1);
            let withhold = input == Input::Zero;
            session.start_language(pending.attempt_id)?;
            session.confirm_language_with_feedback(
                pending.attempt_id,
                &LanguageResponse {
                    text: format!("{BODY}\n\nWITHHOLD_RESERVOIR_INPUT={withhold}\nNEXT: NONE"),
                    provider_model: None,
                    stop_reason: Some("stop".into()),
                    token_count: None,
                    complete: true,
                    provider_prompt_evaluation: None,
                },
                inputs.get(input),
            )?;
        }
        if let Some(pending) = session.pending_journal().cloned() {
            applications.push(json!({
                "entry":pending.entry,"action":pending.action,
                "semanticVector":pending.semantic_vector,
                "feedbackProvenance":pending.feedback_provenance,
            }));
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
            return Err("nonfinite or unbounded state".into());
        }
        let expected = inputs.get(condition.input(frame.step));
        let zero = vec![0.0; 48];
        let vector = expected.map_or(zero.as_slice(), |x| x.vector.as_slice());
        if frame.input[18..]
            .iter()
            .zip(vector)
            .any(|(actual, unscaled)| *actual != unscaled * SCALE)
        {
            return Err(format!("held input mismatch at step {}", frame.step).into());
        }
        if frame.step > 1 {
            let receipt = frame
                .action_receipt
                .as_ref()
                .ok_or("missing application receipt")?;
            if receipt.status != SustainedActionStatus::Unchanged || receipt.state_delta_l2 != 0.0 {
                return Err("NEXT NONE changed controls or claimed an action effect".into());
            }
            if frame
                .application
                .as_ref()
                .is_none_or(|a| a.applied_step != frame.step)
            {
                return Err(
                    "expected one saved application per step after initial observation".into(),
                );
            }
        }
        frames.push(frame);
        if let Some(last) = session.events().back() {
            let id = last.id;
            session.acknowledge_events(id)?;
        }
    }
    let evidence = json!({
        "condition":condition.name(),"specification":spec,"frames":frames,
        "applications":applications,"finalCheckpoint":session.checkpoint(),
    });
    Ok(Run { frames, evidence })
}
fn row(a: &SustainedFrame, b: &SustainedFrame) -> Value {
    json!({"step":a.step,"recurrentL2":distance(&a.state,&b.state),
        "sensoryFillDifferencePoints":a.sensory.fill_percent-b.sensory.fill_percent,
        "retentionDifference":a.next_retention-b.next_retention})
}
fn sample(a: &Run, b: &Run, start: u64) -> Vec<Value> {
    [1,5,10,30,60,120,180].into_iter().filter_map(|lag| {
        let step = start + lag - 1;
        (step<=STEPS).then(|| json!({"lag":lag,"comparison":row(&a.frames[(step-1) as usize],&b.frames[(step-1) as usize])}))
    }).collect()
}
fn compare(actual: &Run, control: &Run, condition: Condition) -> Result<Value> {
    for (a, c) in actual.frames.iter().zip(&control.frames) {
        if a.noise != c.noise
            || a.sensory_noise != c.sensory_noise
            || a.input[..18] != c.input[..18]
        {
            return Err("exogenous forcing or noise differs in paired comparison".into());
        }
        if !matches!(condition, Condition::Zero)
            && a.step < CHANGE
            && (a.state != c.state || a.sensory.fill_percent != c.sensory.fill_percent)
        {
            return Err("paths diverged before prescribed manipulation".into());
        }
    }
    let after: Vec<_> = actual.frames.iter().filter(|f| f.step >= CHANGE).collect();
    let motion: Vec<_> = actual
        .frames
        .windows(2)
        .filter(|w| w[1].step >= CHANGE)
        .map(|w| distance(&w[0].state, &w[1].state))
        .collect();
    let mut result = json!({
        "samplesFromHoldA":sample(actual,control,CHANGE),
        "meanRecurrentStepMotionAfterChange":motion.iter().sum::<f64>()/motion.len() as f64,
        "maximumNearSaturatedCoordinates":after.iter().map(|f| f.state.iter().filter(|x| x.abs()>=0.999).count()).max().unwrap(),
        "meanNearSaturatedCoordinateFraction":after.iter().map(|f| f.state.iter().filter(|x| x.abs()>=0.999).count() as f64/32.0).sum::<f64>()/after.len() as f64,
        "maximumRecurrentDifferenceFromHoldA":actual.frames.iter().zip(&control.frames).map(|(a,c)|distance(&a.state,&c.state)).fold(0.0_f64,f64::max),
        "meanSensoryFillAfterChange":after.iter().map(|f|f.sensory.fill_percent).sum::<f64>()/after.len() as f64,
        "finalScaledTextInputL2":norm(&actual.frames.last().unwrap().input[18..]),
    });
    if matches!(condition, Condition::QuietRestore) {
        result["postRestoreResidualFromHoldA"] = json!(sample(actual, control, RESTORE));
    }
    if let Condition::Alternate(cadence) = condition {
        let switches: Vec<_> = (CHANGE..=STEPS)
            .step_by(cadence as usize)
            .map(|step| {
                let i = (step - 1) as usize;
                let end = (step + cadence - 1).min(STEPS);
                json!({"switchStep":step,"basePhase":(step-1)%30+1,
                "oneStepMotion":distance(&actual.frames[i-1].state,&actual.frames[i].state),
                "differenceFromHoldAAtSwitch":row(&actual.frames[i],&control.frames[i]),
                "endOfHold":row(&actual.frames[(end-1)as usize],&control.frames[(end-1)as usize])})
            })
            .collect();
        result["switches"] = json!(switches);
    }
    Ok(result)
}
fn write(path: &Path, value: &Value) -> Result<()> {
    fs::write(path, serde_json::to_vec_pretty(value)?)?;
    Ok(())
}
fn main() -> Result<()> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let [directory] = args.as_slice() else {
        return Err("Usage: leak_cadence_response NEW_OUTPUT_DIRECTORY".into());
    };
    let directory = Path::new(directory);
    fs::create_dir(directory)?;
    let inputs = Inputs::new()?;
    write(
        &directory.join("synthetic-inputs.json"),
        &json!({
            "provenance":"Scripted synthetic vectors passed through the external-feedback contract; no embedding provider called.",
            "rawA":inputs.raw_a,"rawB":inputs.raw_b,"a":inputs.a,"b":inputs.b,
            "scaledInputL2":norm(&inputs.a.vector)*SCALE,
        }),
    )?;
    let conditions = [
        Condition::Hold,
        Condition::Zero,
        Condition::Withdraw,
        Condition::Switch,
        Condition::QuietRestore,
        Condition::Alternate(5),
        Condition::Alternate(15),
        Condition::Alternate(30),
        Condition::Alternate(60),
    ];
    let mut summaries = Vec::new();
    for seed in [20260909, 20260910] {
        for leak in [0.05, 0.2, 0.35, 0.65, 0.9] {
            let hold = run(seed, leak, Condition::Hold, &inputs)?;
            let zero = run(seed, leak, Condition::Zero, &inputs)?;
            for condition in conditions {
                let produced;
                let actual = match condition {
                    Condition::Hold => &hold,
                    Condition::Zero => &zero,
                    _ => {
                        produced = run(seed, leak, condition, &inputs)?;
                        &produced
                    }
                };
                let mut result = compare(actual, &hold, condition)?;
                if matches!(condition, Condition::Withdraw) {
                    result["priorInputResidualFromAlwaysZero"] =
                        json!(sample(actual, &zero, CHANGE));
                }
                let file = format!("{seed}-leak-{leak}-{}.json", condition.name());
                write(
                    &directory.join(&file),
                    &json!({"run":actual.evidence,"result":result}),
                )?;
                summaries.push(json!({"seed":seed,"leak":leak,"condition":condition.name(),"file":file,"result":result}));
            }
            println!("finished seed {seed}, leak {leak}");
        }
    }
    write(
        &directory.join("report.json"),
        &json!({
            "format":"leak-cadence-response-v1","status":"passed","modelsContacted":false,
            "sourceBase":"b4f94ab","stepsPerPath":STEPS,"pathCount":summaries.len(),
            "manipulationStep":CHANGE,"restoreStep":RESTORE,"nearSaturationThreshold":0.999,
            "scope":"Synthetic numerical input, not language behavior or a replay of six-hour writing. In-memory save authorization. Input cadence and fixed base-forcing phase interact; additive noise is not leak-scaled. No optimal leak or subjective effect inferred.",
            "outcomes":summaries,
        }),
    )?;
    println!("{}", directory.join("report.json").display());
    Ok(())
}
