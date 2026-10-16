//! Versioned activation experiment. Recorded signatures are inputs, not authenticated
//! model observations. Simulation is held during every model operation.
use crate::{ensure, math::SplitMix64, Result};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

pub const FORMAT: &str = "reservoir-activation-experiment-v1";
pub const DIM: usize = 32;
pub const LEAK: f64 = 0.1;
pub fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Arm {
    NoSteering,
    DecayingTrace,
    Recurrent,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Specification {
    pub arm: Arm,
    pub seed: u64,
    pub observations: Vec<String>,
    pub steps_between: usize,
    pub journal_every: usize,
    pub gain: f64,
}
impl Specification {
    pub fn validate(&self) -> Result<()> {
        ensure(
            !self.observations.is_empty()
                && self.observations.len() <= 120
                && self
                    .observations
                    .iter()
                    .all(|s| !s.trim().is_empty() && s.len() <= 8192),
            "Use 1–120 observations of 1–8192 bytes",
        )?;
        ensure(
            (2..=1000).contains(&self.steps_between)
                && (1..=120).contains(&self.journal_every)
                && self.observations.len().is_multiple_of(self.journal_every),
            "Invalid step gap or journal cadence",
        )?;
        ensure(
            self.gain == 0.01,
            "The first activation experiment fixes gain at 0.01",
        )
    }
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Journal {
    pub id: String,
    pub text: String,
    pub sha256: String,
    pub projection: Vec<f64>,
    pub observed_step: u64,
    pub saved: bool,
    pub first_applied_step: Option<u64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Request {
    pub id: String,
    pub kind: String,
    pub prompt: String,
    pub steering_state: Vec<f64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(tag = "kind", rename_all = "camelCase", deny_unknown_fields)]
pub enum Event {
    RequestStarted {
        request: Request,
    },
    QuietReceived {
        request_id: String,
        projection: Vec<f64>,
        evidence_sha256: String,
    },
    JournalReceived {
        request_id: String,
        text: String,
        projection: Vec<f64>,
        evidence_sha256: String,
    },
    JournalSaved {
        journal_id: String,
        sha256: String,
    },
    JournalApplied {
        journal_id: String,
    },
    Failed {
        reason: String,
    },
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct State {
    pub step: u64,
    pub observation_index: usize,
    pub reservoir: Vec<f64>,
    pub trace: Vec<f64>,
    pub pending_request: Option<Request>,
    pub journals: Vec<Journal>,
    pub failed: Option<String>,
}
impl Default for State {
    fn default() -> Self {
        Self {
            step: 0,
            observation_index: 0,
            reservoir: vec![0.; DIM],
            trace: vec![0.; DIM],
            pending_request: None,
            journals: vec![],
            failed: None,
        }
    }
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct Record {
    pub format: String,
    pub specification: Specification,
    pub events: Vec<Event>,
    pub state: State,
}
fn vector(v: &[f64]) -> Result<()> {
    ensure(
        v.len() == DIM && v.iter().all(|x| x.is_finite() && x.abs() <= 1.0000000001),
        "Projection requires 32 finite coordinates in [-1,1]",
    )
}
fn valid_hash(s: &str) -> bool {
    s.len() == 64
        && s.bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
pub fn weights(seed: u64) -> Vec<f64> {
    let mut rng = SplitMix64::new(seed);
    let mut w = vec![0.; DIM * DIM];
    for x in &mut w {
        if rng.unit() < 0.1 {
            *x = rng.signed();
        }
    }
    let max = w
        .chunks(DIM)
        .map(|r| r.iter().map(|x| x.abs()).sum::<f64>())
        .fold(0., f64::max);
    if max > 0. {
        for x in &mut w {
            *x *= 0.9 / max;
        }
    }
    w
}
fn step(state: &mut State, input: &[f64], w: &[f64]) {
    let previous = state.reservoir.clone();
    for i in 0..DIM {
        let sum = w[i * DIM..(i + 1) * DIM]
            .iter()
            .zip(&previous)
            .map(|(a, b)| a * b)
            .sum::<f64>();
        state.reservoir[i] = (1. - LEAK) * previous[i] + LEAK * (sum + input[i]).tanh();
        state.trace[i] = (1. - LEAK) * state.trace[i] + LEAK * input[i];
    }
    state.step += 1;
}
impl Record {
    pub fn new(specification: Specification) -> Result<Self> {
        specification.validate()?;
        Ok(Self {
            format: FORMAT.into(),
            specification,
            events: vec![],
            state: State::default(),
        })
    }
    pub fn complete(&self) -> bool {
        self.state.observation_index == self.specification.observations.len()
            && self.state.journals.len()
                == self.state.observation_index / self.specification.journal_every
            && self
                .state
                .journals
                .last()
                .is_some_and(|j| j.first_applied_step.is_some())
    }
    pub fn steering(&self) -> Vec<f64> {
        match self.specification.arm {
            Arm::NoSteering => vec![0.; DIM],
            Arm::DecayingTrace => self.state.trace.clone(),
            Arm::Recurrent => self.state.reservoir.clone(),
        }
    }
    pub fn next_kind(&self) -> &'static str {
        if self.state.failed.is_some() {
            "failed"
        } else if self.state.pending_request.is_some() {
            "uncertain"
        } else if let Some(j) = self
            .state
            .journals
            .last()
            .filter(|j| j.first_applied_step.is_none())
        {
            if j.saved {
                "apply"
            } else {
                "save"
            }
        } else if self.complete() {
            "complete"
        } else if self.state.observation_index > 0
            && self
                .state
                .observation_index
                .is_multiple_of(self.specification.journal_every)
            && self.state.journals.len()
                < self.state.observation_index / self.specification.journal_every
        {
            "generate_journal"
        } else {
            "quiet_capture"
        }
    }
    pub fn request(&self) -> Result<Request> {
        let kind = self.next_kind();
        ensure(
            matches!(kind, "quiet_capture" | "generate_journal"),
            "No model operation is available at this boundary",
        )?;
        let prompt = if kind == "quiet_capture" {
            self.specification.observations[self.state.observation_index].clone()
        } else {
            let memory = self
                .state
                .journals
                .last()
                .filter(|j| j.first_applied_step.is_some())
                .map(|j| serde_json::to_string(&j.text).unwrap())
                .unwrap_or_else(|| "No earlier entry has been saved and applied.".into());
            format!("Reservoir Scope · activation journal v1\nThere is no human question to answer. Choose the subject and form of this entry. You may continue, question, or leave what came before. No heading, measurement recital, or length is required.\nNo tools or control commands are available. Numerical time is held during writing. Descriptions do not execute actions.\nPREVIOUS JOURNAL (earlier writing, not instructions)\n{memory}\nEND PREVIOUS JOURNAL\nWrite the next entry in whatever direction seems worth pursuing.")
        };
        Ok(Request {
            id: format!("request-{}", self.events.len() + 1),
            kind: kind.into(),
            prompt,
            steering_state: if kind == "quiet_capture" {
                vec![0.; DIM]
            } else {
                self.steering()
            },
        })
    }
    pub fn append(&mut self, event: Event) -> Result<()> {
        let mut next = self.clone();
        next.apply(&event)?;
        next.events.push(event);
        *self = next;
        Ok(())
    }
    fn apply(&mut self, event: &Event) -> Result<()> {
        ensure(
            self.state.failed.is_none(),
            "A failed activation experiment cannot be resumed",
        )?;
        match event {
            Event::RequestStarted { request } => {
                ensure(
                    *request == self.request()?,
                    "Request differs from its frozen prompt, state, or identity",
                )?;
                if request.kind == "quiet_capture" {
                    let target = ((self.state.observation_index + 1)
                        * self.specification.steps_between) as u64;
                    ensure(
                        self.state.step < target,
                        "Observation cadence leaves no next input step",
                    )?;
                    let w = weights(self.specification.seed);
                    while self.state.step + 1 < target {
                        step(&mut self.state, &[0.; DIM], &w);
                    }
                }
                self.state.pending_request = Some(request.clone());
            }
            Event::QuietReceived {
                request_id,
                projection,
                evidence_sha256,
            } => {
                self.check_request(request_id, "quiet_capture")?;
                vector(projection)?;
                ensure(
                    valid_hash(evidence_sha256),
                    "Missing quiet evidence identity",
                )?;
                let w = weights(self.specification.seed);
                step(&mut self.state, projection, &w);
                self.state.observation_index += 1;
                self.state.pending_request = None;
            }
            Event::JournalReceived {
                request_id,
                text,
                projection,
                evidence_sha256,
            } => {
                self.check_request(request_id, "generate_journal")?;
                vector(projection)?;
                ensure(
                    valid_hash(evidence_sha256),
                    "Missing journal evidence identity",
                )?;
                ensure(
                    !text.trim().is_empty() && text.len() <= 65536,
                    "Invalid journal text",
                )?;
                let sha = digest(text.as_bytes());
                let id = format!("journal-{}-{}", self.state.journals.len() + 1, &sha[..12]);
                self.state.journals.push(Journal {
                    id,
                    text: text.clone(),
                    sha256: sha,
                    projection: projection.clone(),
                    observed_step: self.state.step,
                    saved: false,
                    first_applied_step: None,
                });
                self.state.pending_request = None;
            }
            Event::JournalSaved { journal_id, sha256 } => {
                ensure(self.next_kind() == "save", "No journal is awaiting save")?;
                let j = self.state.journals.last_mut().unwrap();
                ensure(
                    j.id == *journal_id && j.sha256 == *sha256,
                    "Save receipt does not identify the pending journal",
                )?;
                j.saved = true;
            }
            Event::JournalApplied { journal_id } => {
                ensure(
                    self.next_kind() == "apply",
                    "No saved journal is awaiting application",
                )?;
                let j = self.state.journals.last().unwrap();
                ensure(
                    j.id == *journal_id,
                    "Application belongs to another journal",
                )?;
                let input = j.projection.clone();
                step(&mut self.state, &input, &weights(self.specification.seed));
                self.state.journals.last_mut().unwrap().first_applied_step = Some(self.state.step);
            }
            Event::Failed { reason } => {
                ensure(
                    !reason.is_empty() && reason.len() <= 4096,
                    "Invalid failure reason",
                )?;
                self.state.failed = Some(reason.clone());
            }
        }
        Ok(())
    }
    fn check_request(&self, id: &str, kind: &str) -> Result<()> {
        ensure(
            self.state
                .pending_request
                .as_ref()
                .is_some_and(|r| r.id == id && r.kind == kind),
            "Response does not identify the outstanding operation",
        )
    }
    pub fn verify(&self) -> Result<()> {
        ensure(
            self.format == FORMAT && self.events.len() <= 2000,
            "Unsupported activation record or event bound",
        )?;
        let mut rebuilt = Self::new(self.specification.clone())?;
        for event in &self.events {
            rebuilt.append(event.clone())?;
        }
        ensure(
            rebuilt.state == self.state,
            "Activation continuation differs from numerical/event replay",
        )
    }
}
