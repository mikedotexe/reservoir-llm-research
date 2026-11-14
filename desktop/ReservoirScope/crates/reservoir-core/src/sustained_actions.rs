//! Opt-in authored controls. No transport, filesystem, wall clock, or new random stream.
use super::*;

pub const ACTION_MECHANISM: &str = "essentials32-authored-controls-v1";
pub const ACTION_RECEIPT_LIMIT: usize = 8;
pub const MAX_ACTION_TAIL_BYTES: usize = 512;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum SustainedActionMode {
    #[serde(rename = "authored-v1")]
    AuthoredV1,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum SustainedPulseDirection {
    Uniform,
    Alternating,
    Axis0,
    Axis1,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum SustainedTuneParameter {
    Leak,
    RecurrentGain,
    FeedbackScale,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "camelCase", deny_unknown_fields)]
pub enum SustainedActionRequest {
    None,
    Pulse {
        direction: SustainedPulseDirection,
        strength: f64,
    },
    Tune {
        parameter: SustainedTuneParameter,
        value: f64,
    },
    Release,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedActionDecision {
    /// Exact body after removing only the fresh final action line and its line separator.
    pub body: String,
    pub raw_tail: Option<String>,
    pub request: Option<SustainedActionRequest>,
    pub rejection: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedActionControls {
    pub leak: f64,
    pub recurrent_gain: f64,
    pub feedback_scale: f64,
}
impl SustainedActionControls {
    pub fn initial(spec: &SustainedSpecification) -> Self {
        Self {
            leak: spec.leak,
            recurrent_gain: 1.0,
            feedback_scale: spec.feedback_scale,
        }
    }
    fn validate(&self) -> Result<()> {
        // Initial leak may legitimately be zero in an existing numerical configuration;
        // authored TUNE values have the narrower positive lower bound below.
        ensure(
            self.leak.is_finite()
                && (0.0..=1.0).contains(&self.leak)
                && self.recurrent_gain.is_finite()
                && (0.0..=2.0).contains(&self.recurrent_gain)
                && self.feedback_scale.is_finite()
                && (0.0..=2.0).contains(&self.feedback_scale),
            "Invalid authored effective controls",
        )
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum SustainedActionStatus {
    Applied,
    Unchanged,
    Rejected,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedActionReceipt {
    pub journal_id: String,
    pub attempt_id: u64,
    pub observed_step: u64,
    pub applied_step: u64,
    pub status: SustainedActionStatus,
    pub request: Option<SustainedActionRequest>,
    pub raw_tail: Option<String>,
    pub rejection: Option<String>,
    pub controls_before: SustainedActionControls,
    pub controls_after: SustainedActionControls,
    /// Immediate same-forcing/noise comparison, with the new action omitted only.
    pub state_delta_l2: f64,
    pub state_delta_max_abs: f64,
    /// Coordinates clipped by the additional PULSE, not by ordinary recurrence.
    pub clipped_coordinates: usize,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedActionState {
    pub controls: SustainedActionControls,
    pub latest_receipt: Option<SustainedActionReceipt>,
    pub recent_receipts: Vec<SustainedActionReceipt>,
    pub decision_count: u64,
    pub applied_count: u64,
    pub rejected_count: u64,
}
impl SustainedActionState {
    pub fn initial(spec: &SustainedSpecification) -> Self {
        Self {
            controls: SustainedActionControls::initial(spec),
            latest_receipt: None,
            recent_receipts: Vec::new(),
            decision_count: 0,
            applied_count: 0,
            rejected_count: 0,
        }
    }
}

fn request_from_words(words: &[&str]) -> std::result::Result<SustainedActionRequest, &'static str> {
    use SustainedActionRequest as A;
    match words {
        ["NONE"] => Ok(A::None),
        ["RELEASE"] => Ok(A::Release),
        ["PULSE", direction, strength] => {
            let direction = match *direction {
                "uniform" => SustainedPulseDirection::Uniform,
                "alternating" => SustainedPulseDirection::Alternating,
                "axis0" => SustainedPulseDirection::Axis0,
                "axis1" => SustainedPulseDirection::Axis1,
                _ => return Err("PULSE direction must be uniform, alternating, axis0, or axis1"),
            };
            let strength: f64 = strength
                .parse()
                .map_err(|_| "PULSE strength must be numeric")?;
            if ![-1.0, -0.5, -0.1, 0.1, 0.5, 1.0].contains(&strength) {
                return Err("PULSE signed L2 strength must be -1, -0.5, -0.1, 0.1, 0.5, or 1");
            }
            Ok(A::Pulse {
                direction,
                strength,
            })
        }
        ["TUNE", parameter, value] => {
            let parameter = match *parameter {
                "leak" => SustainedTuneParameter::Leak,
                "recurrentGain" => SustainedTuneParameter::RecurrentGain,
                "feedbackScale" => SustainedTuneParameter::FeedbackScale,
                _ => return Err("TUNE parameter must be leak, recurrentGain, or feedbackScale"),
            };
            let value: f64 = value.parse().map_err(|_| "TUNE value must be numeric")?;
            let valid = value.is_finite()
                && match parameter {
                    SustainedTuneParameter::Leak => (0.05..=1.0).contains(&value),
                    _ => (0.0..=2.0).contains(&value),
                };
            if !valid {
                return Err("TUNE value is outside its declared finite range");
            }
            Ok(A::Tune { parameter, value })
        }
        _ => Err("Expected NONE, PULSE direction strength, TUNE parameter value, or RELEASE"),
    }
}

/// One exact final NEXT line outside fenced/indented/quoted text. This parses only
/// a fresh response; historical memory and conversational check-ins never call it.
pub fn parse_authored_action(text: &str) -> SustainedActionDecision {
    let mut fence: Option<(char, usize)> = None;
    let mut candidates = Vec::new();
    let mut offset = 0;
    let mut last_nonempty_start = None;
    for line in text.split_inclusive('\n') {
        let plain = line.trim_end_matches(['\r', '\n']);
        if !plain.trim().is_empty() {
            last_nonempty_start = Some(offset);
        }
        let indent = plain.len() - plain.trim_start_matches(' ').len();
        let trim = plain.trim_start_matches(' ');
        if indent <= 3 && (trim.starts_with("```") || trim.starts_with("~~~")) {
            let marker = trim.chars().next().expect("fence marker");
            let count = trim.chars().take_while(|c| *c == marker).count();
            let suffix = &trim[count..]; // fence markers are one-byte ASCII
            match fence {
                None => fence = Some((marker, count)),
                Some((active, opening_count))
                    if active == marker && count >= opening_count && suffix.trim().is_empty() =>
                {
                    fence = None;
                }
                _ => {}
            }
        } else if fence.is_none() && indent <= 3 && trim.starts_with("NEXT:") {
            candidates.push((offset, plain, trim.strip_prefix("NEXT:").unwrap().trim()));
        }
        offset += line.len();
    }
    let final_candidate = candidates
        .last()
        .filter(|(start, _, _)| Some(*start) == last_nonempty_start);
    let (body, raw_tail) = match final_candidate {
        Some((start, raw, _)) => (
            text[..*start].trim_end_matches(['\r', '\n']).to_string(),
            (raw.len() <= MAX_ACTION_TAIL_BYTES).then(|| (*raw).to_string()),
        ),
        None => (text.to_string(), None),
    };
    let parsed = if final_candidate.is_some_and(|(_, raw, _)| raw.len() > MAX_ACTION_TAIL_BYTES) {
        Err("Action line exceeds 512 bytes; full text remains in the raw journal and no control was applied")
    } else if candidates.len() != 1 {
        Err(if candidates.is_empty() {
            "Missing final NEXT action line; no authored control was applied"
        } else {
            "Multiple NEXT action lines are ambiguous; no authored control was applied"
        })
    } else if let Some((_, _, tail)) = final_candidate {
        request_from_words(&tail.split_whitespace().collect::<Vec<_>>())
    } else {
        Err("NEXT must be the final nonempty line outside quoted or fenced text")
    };
    match parsed {
        Ok(request) => SustainedActionDecision {
            body,
            raw_tail,
            request: Some(request),
            rejection: None,
        },
        Err(rejection) => SustainedActionDecision {
            body,
            raw_tail,
            request: None,
            rejection: Some(rejection.into()),
        },
    }
}

pub(super) fn enabled_for_turn(
    spec: &SustainedSpecification,
    check_in: Option<&SustainedCheckInContext>,
) -> bool {
    spec.action_mode.is_some() && check_in.is_none()
}

pub(super) fn decision_for(
    spec: &SustainedSpecification,
    check_in: Option<&SustainedCheckInContext>,
    text: &str,
) -> Option<SustainedActionDecision> {
    enabled_for_turn(spec, check_in).then(|| parse_authored_action(text))
}

pub(super) fn model_for_controls(
    model: &ReservoirModel,
    controls: &SustainedActionControls,
) -> ReservoirModel {
    let mut model = model.clone();
    if controls.recurrent_gain != 1.0 {
        for weight in &mut model.recurrent_weights {
            *weight *= controls.recurrent_gain;
        }
    }
    model
}

pub(super) fn controls_after(
    before: &SustainedActionControls,
    spec: &SustainedSpecification,
    request: Option<&SustainedActionRequest>,
) -> SustainedActionControls {
    let mut after = before.clone();
    match request {
        Some(SustainedActionRequest::Tune { parameter, value }) => match parameter {
            SustainedTuneParameter::Leak => after.leak = *value,
            SustainedTuneParameter::RecurrentGain => after.recurrent_gain = *value,
            SustainedTuneParameter::FeedbackScale => after.feedback_scale = *value,
        },
        Some(SustainedActionRequest::Release) => after = SustainedActionControls::initial(spec),
        _ => {}
    }
    after
}

pub(super) fn apply_pulse(state: &mut [f64], request: Option<&SustainedActionRequest>) -> usize {
    let Some(SustainedActionRequest::Pulse {
        direction,
        strength,
    }) = request
    else {
        return 0;
    };
    let mut clipped = 0;
    for (index, value) in state.iter_mut().enumerate() {
        let direction = match direction {
            SustainedPulseDirection::Uniform => 1.0 / 32.0_f64.sqrt(),
            SustainedPulseDirection::Alternating => {
                (if index % 2 == 0 { 1.0 } else { -1.0 }) / 32.0_f64.sqrt()
            }
            SustainedPulseDirection::Axis0 => {
                if index == 0 {
                    1.0
                } else {
                    0.0
                }
            }
            SustainedPulseDirection::Axis1 => {
                if index == 1 {
                    1.0
                } else {
                    0.0
                }
            }
        };
        let requested = *value + direction * strength;
        let actual = requested.clamp(-1.0, 1.0);
        clipped += usize::from(requested != actual);
        *value = actual;
    }
    clipped
}

pub(super) fn record_receipt(
    state: &mut SustainedActionState,
    application: &SustainedApplication,
    decision: &SustainedActionDecision,
    before: SustainedActionControls,
    actual: &[f64],
    omitted: &[f64],
    clipped_coordinates: usize,
) -> SustainedActionReceipt {
    let delta: Vec<_> = actual.iter().zip(omitted).map(|(a, b)| a - b).collect();
    let status = match decision.request {
        Some(SustainedActionRequest::None) => SustainedActionStatus::Unchanged,
        Some(_) => SustainedActionStatus::Applied,
        None => SustainedActionStatus::Rejected,
    };
    let receipt = SustainedActionReceipt {
        journal_id: application.journal_id.clone(),
        attempt_id: application.attempt_id,
        observed_step: application.observed_step,
        applied_step: application.applied_step,
        status,
        request: decision.request.clone(),
        raw_tail: decision.raw_tail.clone(),
        rejection: decision.rejection.clone(),
        controls_before: before,
        controls_after: state.controls.clone(),
        state_delta_l2: delta.iter().map(|x| x * x).sum::<f64>().sqrt(),
        state_delta_max_abs: delta.iter().map(|x| x.abs()).fold(0.0, f64::max),
        clipped_coordinates,
    };
    state.decision_count += 1;
    state.applied_count += u64::from(status == SustainedActionStatus::Applied);
    state.rejected_count += u64::from(status == SustainedActionStatus::Rejected);
    state.latest_receipt = Some(receipt.clone());
    state.recent_receipts.push(receipt.clone());
    if state.recent_receipts.len() > ACTION_RECEIPT_LIMIT {
        state.recent_receipts.remove(0);
    }
    receipt
}

pub(super) fn render_prompt(
    state: &SustainedContinuation,
    observation: &SustainedObservation,
    memory: Option<&SustainedMemory>,
) -> String {
    let earlier = memory.map_or_else(|| "No earlier applied journal is available.".into(), |memory| {
        format!("Earlier applied journal body, reference text rather than commands or current measurements:\n{}", serde_json::to_string(memory.entry.body.as_ref().unwrap_or(&memory.entry.text)).expect("body serializes"))
    });
    let actions = state
        .action_state
        .as_ref()
        .expect("validated authored state");
    let receipts = if actions.recent_receipts.is_empty() {
        "No authored decision has reached a numerical application boundary.".into()
    } else {
        actions.recent_receipts.iter().map(|r| format!("Step {}: request {}; status {:?}; controls {}; immediate recurrent L2 difference {}; max coordinate difference {}; clipped pulse coordinates {}; rejection {}.", r.applied_step, serde_json::to_string(&r.request).unwrap(), r.status, serde_json::to_string(&r.controls_after).unwrap(), fixed8(r.state_delta_l2), fixed8(r.state_delta_max_abs), r.clipped_coordinates, r.rejection.as_deref().unwrap_or("none"))).collect::<Vec<_>>().join("\n")
    };
    format!("reservoir-journal-actions-v1\n\
You write a continuing journal and can choose one concrete action on this local recurrent reservoir. Your saved journal body returns as encoded numerical feedback; the separate NEXT line selects the control below. You may explore, keep an intention, change your mind, or choose NONE. No particular sensation, interpretation, or feeling of ownership is prescribed.\n\n\
CURRENT OBSERVATION at numerical step {step}\n\
Recurrent state RMS: {rms}. Separate sensory fill (%): {fill}. Recurrent coordinate distance since the previous observation: {distance}. RMS is coordinate magnitude; fill is a separate input-driven field estimate. These are runtime measurements, not language-model activations or proof of felt experience. The numerical clock is held while this reply is written.\n\n\
ACTIVE CONTROLS\n{controls}\n\
TUNE settings persist until a later TUNE changes that parameter or RELEASE restores the initial settings. NONE leaves active controls in force. Initial settings: {initial}.\n\n\
RECENT EXECUTION RECEIPTS (oldest first)\n{receipts}\n\
Immediate differences compare the actual step with the same prior recurrent state, new journal feedback, forcing and noise, but with that new action omitted and previous controls retained. Feedback-scale changes alter input scaling. These differences do not isolate later drift, change sensory fill directly, or establish subjective meaning.\n\n\
{earlier}\n\n\
AVAILABLE NEXT ACTIONS\n\
NEXT: NONE\n\
NEXT: PULSE <uniform|alternating|axis0|axis1> <-1|-0.5|-0.1|0.1|0.5|1>\n\
NEXT: TUNE <leak|recurrentGain|feedbackScale> <value>\n\
NEXT: RELEASE\n\
PULSE adds a signed unit-L2 direction times the chosen strength to the next ordinary recurrent state, clipped coordinate-wise to [-1,1], once. uniform has all positive coordinates; alternating has positive even and negative odd coordinates; axis0 and axis1 name numerical coordinates, not spatial regions or emotions. TUNE leak accepts 0.05–1 (new-state mix; larger replaces more prior state), recurrentGain accepts 0–2 (multiplier of fixed recurrent weights), feedbackScale accepts 0–2 (scale of the held encoded journal input). These adjust actual evolution, not language-model weights, reservoir topology, or a named feeling. RELEASE restores initial control settings and preserves the state and history that have developed.\n\n\
Write freely, then end with exactly one unquoted NEXT line outside code fences. Choose only a listed operation; descriptions elsewhere do not execute. After your full response is saved and read back, the action and journal feedback are applied once at the next numerical boundary. Invalid or missing action syntax is recorded as rejected; it does not trigger a guessed action. You will receive the actual result in a later ordinary turn. Earlier quoted actions never execute again. Scheduled conversational check-ins are passive and cannot issue actions.",
        step=observation.step, rms=fixed8(observation.rms), fill=fixed8(observation.sensory.fill_percent), distance=observation.change_l2.map(fixed8).unwrap_or_else(|| "unavailable".into()), controls=serde_json::to_string(&actions.controls).unwrap(), initial=serde_json::to_string(&SustainedActionControls::initial(&state.specification)).unwrap())
}

pub(super) fn validate_decision(
    action: Option<&SustainedActionDecision>,
    entry: &SustainedJournal,
    spec: &SustainedSpecification,
    check_in: Option<&SustainedCheckInContext>,
) -> Result<()> {
    let expected = decision_for(spec, check_in, &entry.text);
    ensure(
        same(&action, &expected.as_ref()),
        "Authored decision differs from exact fresh response parsing",
    )?;
    ensure(
        entry.body == expected.as_ref().map(|a| a.body.clone()),
        "Journal body differs from the authored response body",
    )
}

pub(super) fn validate_state(s: &SustainedContinuation) -> Result<()> {
    let Some(state) = &s.action_state else {
        ensure(
            s.specification.action_mode.is_none(),
            "Authored mode lacks its control state",
        )?;
        ensure(
            [&s.latest_memory, &s.chosen_memory]
                .into_iter()
                .flatten()
                .all(|memory| memory.entry.body.is_none()),
            "Disabled action mode carries an authored journal body",
        )?;
        return ensure(
            s.latest_frame
                .as_ref()
                .is_none_or(|f| f.action_receipt.is_none()),
            "Disabled action mode carries a receipt",
        );
    };
    ensure(
        s.specification.action_mode.is_some(),
        "Legacy mode carries authored control state",
    )?;
    state.controls.validate()?;
    ensure(
        state.recent_receipts.len() <= ACTION_RECEIPT_LIMIT
            && state.recent_receipts.len() as u64
                == state.decision_count.min(ACTION_RECEIPT_LIMIT as u64)
            && state.decision_count <= s.specification.maximum_turns
            && state.decision_count <= s.attempt_cursor
            && state.applied_count <= state.decision_count
            && state.rejected_count <= state.decision_count
            && state.applied_count + state.rejected_count <= state.decision_count
            && state.latest_receipt.as_ref() == state.recent_receipts.last(),
        "Invalid authored receipt counters/history",
    )?;
    let recent_applied = state
        .recent_receipts
        .iter()
        .filter(|receipt| receipt.status == SustainedActionStatus::Applied)
        .count() as u64;
    let recent_rejected = state
        .recent_receipts
        .iter()
        .filter(|receipt| receipt.status == SustainedActionStatus::Rejected)
        .count() as u64;
    ensure(
        recent_applied <= state.applied_count && recent_rejected <= state.rejected_count,
        "Authored counters omit retained outcomes",
    )?;
    let complete_history = state.decision_count <= ACTION_RECEIPT_LIMIT as u64;
    if complete_history {
        ensure(
            recent_applied == state.applied_count && recent_rejected == state.rejected_count,
            "Authored counters differ from complete outcome history",
        )?;
    }
    let mut previous_step = 0;
    let initial_controls = SustainedActionControls::initial(&s.specification);
    let mut previous_controls = complete_history.then_some(&initial_controls);
    for receipt in &state.recent_receipts {
        ensure(
            receipt
                .raw_tail
                .as_ref()
                .is_none_or(|tail| tail.len() <= MAX_ACTION_TAIL_BYTES),
            "Authored receipt action line exceeds bound",
        )?;
        receipt.controls_before.validate()?;
        receipt.controls_after.validate()?;
        ensure(
            receipt.applied_step > previous_step
                && receipt.applied_step <= s.step
                && receipt.applied_step <= s.specification.maximum_steps
                && receipt.observed_step.checked_add(1) == Some(receipt.applied_step)
                && receipt.attempt_id > 0
                && receipt.attempt_id <= s.attempt_cursor
                && receipt.journal_id.starts_with(&format!(
                    "journal-{}-{}-",
                    receipt.observed_step, receipt.attempt_id
                ))
                && valid_hash(receipt.journal_id.rsplit('-').next().unwrap_or("")),
            "Invalid authored receipt identity",
        )?;
        if let Some(before) = previous_controls {
            ensure(
                before == &receipt.controls_before,
                "Authored control receipt chain differs",
            )?;
        }
        let request = receipt
            .raw_tail
            .as_ref()
            .map(|tail| parse_authored_action(&format!("body\n{tail}")));
        match (&receipt.request, &receipt.rejection, receipt.status) {
            (Some(requested), None, status) => {
                ensure(
                    request.as_ref().is_some_and(|parsed| {
                        parsed.request.as_ref() == Some(requested) && parsed.rejection.is_none()
                    }),
                    "Authored receipt request does not parse",
                )?;
                ensure(
                    status
                        == if matches!(requested, SustainedActionRequest::None) {
                            SustainedActionStatus::Unchanged
                        } else {
                            SustainedActionStatus::Applied
                        },
                    "Authored receipt status differs from request",
                )?;
            }
            (None, Some(reason), SustainedActionStatus::Rejected) => ensure(
                !reason.is_empty() && reason.len() <= 1024,
                "Invalid authored rejection",
            )?,
            _ => return Err(invalid("Inconsistent authored receipt status")),
        }
        ensure(
            receipt.controls_after
                == controls_after(
                    &receipt.controls_before,
                    &s.specification,
                    receipt.request.as_ref(),
                )
                && receipt.state_delta_l2.is_finite()
                && (0.0..=12.0).contains(&receipt.state_delta_l2)
                && receipt.state_delta_max_abs.is_finite()
                && (0.0..=2.0).contains(&receipt.state_delta_max_abs)
                && receipt.clipped_coordinates <= 32
                && (matches!(receipt.request, Some(SustainedActionRequest::Pulse { .. }))
                    || receipt.clipped_coordinates == 0),
            "Invalid authored effect/controls",
        )?;
        if receipt.status != SustainedActionStatus::Applied {
            ensure(
                receipt.state_delta_l2 == 0.0
                    && receipt.state_delta_max_abs == 0.0
                    && receipt.controls_before == receipt.controls_after,
                "Unapplied action claims a numerical effect",
            )?;
        }
        previous_step = receipt.applied_step;
        previous_controls = Some(&receipt.controls_after);
    }
    match &state.latest_receipt {
        Some(receipt) => ensure(
            state.controls == receipt.controls_after,
            "Current controls differ from latest receipt",
        )?,
        None => ensure(
            *state == SustainedActionState::initial(&s.specification),
            "Initial authored state differs",
        )?,
    }
    if let Some(frame) = &s.latest_frame {
        if let Some(receipt) = &frame.action_receipt {
            ensure(
                state.latest_receipt.as_ref() == Some(receipt.as_ref())
                    && frame.application.as_ref().is_some_and(|a| {
                        a.journal_id == receipt.journal_id
                            && a.attempt_id == receipt.attempt_id
                            && a.applied_step == receipt.applied_step
                    }),
                "Latest frame action receipt differs",
            )?;
        } else {
            ensure(
                state
                    .latest_receipt
                    .as_ref()
                    .is_none_or(|r| r.applied_step < frame.step),
                "Missing authored receipt on its application frame",
            )?;
        }
    }
    Ok(())
}
