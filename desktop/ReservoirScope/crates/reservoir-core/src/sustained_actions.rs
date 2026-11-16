//! Opt-in authored controls. No transport, filesystem, wall clock, or new random stream.
use super::*;

pub const ACTION_MECHANISM: &str = "essentials32-authored-controls-v1";
pub const ACTION_MECHANISM_V2: &str = "essentials32-authored-controls-v2";
pub const ACTION_MECHANISM_V3: &str = "essentials32-authored-controls-v3";
pub const ACTION_RECEIPT_LIMIT: usize = 8;
pub const MAX_ACTION_TAIL_BYTES: usize = 512;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, schemars::JsonSchema)]
pub enum SustainedActionMode {
    #[serde(rename = "authored-v1")]
    AuthoredV1,
    #[serde(rename = "authored-v2")]
    AuthoredV2,
    #[serde(rename = "authored-v3")]
    AuthoredV3,
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
    ReadPeers,
    Scan,
    Experiment {
        experiment: Box<SustainedExperimentRequest>,
    },
    ProbeExperiment {
        probe: SustainedExperimentProbeRequest,
    },
    ScanQuestion {
        question: SustainedSonarQuestion,
    },
    ProbeScan {
        direction: SustainedSonarDirection,
        sign: SustainedSonarSign,
    },
    Pulse {
        direction: SustainedPulseDirection,
        strength: f64,
    },
    Tune {
        parameter: SustainedTuneParameter,
        value: f64,
    },
    Release,
    Probe {
        vector: Vec<f64>,
    },
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum SustainedReservoirInputDisposition {
    Send,
    Withhold,
    /// Malformed fresh directive: retain the body but withhold numerical text input.
    Rejected,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedReservoirInputDecision {
    pub disposition: SustainedReservoirInputDisposition,
    pub raw_directive: Option<String>,
    pub rejection: Option<String>,
}
impl SustainedReservoirInputDecision {
    pub fn withholds(&self) -> bool {
        self.disposition != SustainedReservoirInputDisposition::Send
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedActionDecision {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub diagnostics: Option<SustainedControlDiagnostics>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub inquiry: Option<SustainedInquiryDecision>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub reservoir_input: Option<SustainedReservoirInputDecision>,
    /// Exact body after removing fresh control-footer lines and their line separators.
    /// V1 removes only NEXT; V2 can also remove its input directive.
    pub body: String,
    pub raw_tail: Option<String>,
    pub request: Option<SustainedActionRequest>,
    pub rejection: Option<String>,
}

impl SustainedActionDecision {
    pub fn withholds_reservoir_input(&self) -> bool {
        self.reservoir_input
            .as_ref()
            .is_some_and(|input| input.withholds())
    }
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
            recurrent_gain: spec.recurrent_gain,
            feedback_scale: spec.feedback_scale,
        }
    }
    pub(super) fn validate(&self) -> Result<()> {
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
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub experiment: Option<SustainedExperimentReceipt>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub experiment_probe: Option<Box<SustainedExperimentProbeReceipt>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sonar_question: Option<SustainedSonarScanRef>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sonar_scan: Option<SustainedSonarScanRef>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sonar_probe: Option<Box<SustainedSonarProbeReceipt>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub peer_read: Option<Box<SustainedPeerRead>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub diagnostics: Option<SustainedControlDiagnostics>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub inquiry: Option<SustainedInquiryReceipt>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub probe: Option<SustainedProbeReceipt>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub reservoir_input: Option<SustainedReservoirInputDecision>,
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
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub continuity: Option<SustainedContinuityState>,
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
            continuity: (spec.action_mode == Some(SustainedActionMode::AuthoredV3))
                .then(SustainedContinuityState::default),
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

/// Strip explicit Markdown quote/list containers only to recognize fenced blocks.
/// This is deliberately conservative; it is not a Markdown renderer. In particular,
/// a quote or list paragraph stays historical until an actual blank line separates it.
fn container_content(mut text: &str) -> (&str, bool, usize) {
    let mut contained = false;
    let mut list_indent = 0;
    loop {
        let trimmed = text.trim_start_matches(' ');
        let indent = text.len() - trimmed.len();
        if let Some(rest) = trimmed.strip_prefix('>') {
            contained = true;
            text = rest.strip_prefix(' ').unwrap_or(rest);
            continue;
        }
        let marker_length = if trimmed.starts_with(['-', '+', '*']) {
            1
        } else {
            let digits = trimmed.bytes().take_while(u8::is_ascii_digit).count();
            if (1..=9).contains(&digits)
                && trimmed
                    .as_bytes()
                    .get(digits)
                    .is_some_and(|c| *c == b'.' || *c == b')')
            {
                digits + 1
            } else {
                0
            }
        };
        if marker_length > 0 {
            let rest = &trimmed[marker_length..];
            if rest.starts_with([' ', '\t']) {
                let inner = rest.trim_start_matches([' ', '\t']);
                list_indent += indent + marker_length + rest.len() - inner.len();
                contained = true;
                text = inner;
                continue;
            }
        }
        return (trimmed, contained, list_indent);
    }
}

/// Closing a container fence may repeat quote markers, but a list marker inside
/// its code is literal content and must never turn into a closing fence.
fn after_quote_markers(mut text: &str) -> &str {
    loop {
        let trimmed = text.trim_start_matches(' ');
        let Some(rest) = trimmed.strip_prefix('>') else {
            return text;
        };
        text = rest.strip_prefix(' ').unwrap_or(rest);
    }
}

/// One exact final NEXT line outside fenced/indented/quoted text. This parses only
/// a fresh response; historical memory and conversational check-ins never call it.
pub fn parse_authored_action(text: &str) -> SustainedActionDecision {
    // marker, opening run length, explicit container, list content indentation
    let mut fence: Option<(char, usize, bool, usize)> = None;
    let mut container_paragraph = false;
    let mut candidates = Vec::new();
    let mut offset = 0;
    let mut last_nonempty_start = None;
    for line in text.split_inclusive('\n') {
        let plain = line.trim_end_matches(['\r', '\n']);
        if !plain.trim().is_empty() {
            last_nonempty_start = Some(offset);
        }
        if plain.trim().is_empty() && fence.is_none() {
            container_paragraph = false;
        }
        if let Some((active, opening_count, contained, list_indent)) = fence {
            let content = if contained {
                after_quote_markers(plain)
            } else {
                plain
            };
            let trimmed = content.trim_start_matches(' ');
            let indent = content.len() - trimmed.len();
            let count = trimmed.chars().take_while(|c| *c == active).count();
            if indent <= list_indent + 3
                && count >= opening_count
                && trimmed[count..].trim().is_empty()
            {
                fence = None;
            }
        } else {
            let (content, contained, list_indent) = container_content(plain);
            container_paragraph |= contained;
            let indent = plain.len() - plain.trim_start_matches(' ').len();
            if (contained || indent <= 3)
                && (content.starts_with("```") || content.starts_with("~~~"))
            {
                let marker = content.chars().next().expect("fence marker");
                let count = content.chars().take_while(|c| *c == marker).count();
                fence = Some((marker, count, contained, list_indent));
            } else if !container_paragraph && plain.starts_with("NEXT:") {
                candidates.push((offset, plain, plain.strip_prefix("NEXT:").unwrap().trim()));
            }
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
            diagnostics: None,
            inquiry: None,
            reservoir_input: None,
            body,
            raw_tail,
            request: Some(request),
            rejection: None,
        },
        Err(rejection) => SustainedActionDecision {
            diagnostics: None,
            inquiry: None,
            reservoir_input: None,
            body,
            raw_tail,
            request: None,
            rejection: Some(rejection.into()),
        },
    }
}

/// The v2 footer can decide text input independently of whether NEXT is accepted.
/// Only a fresh directive at the end of the body (immediately before NEXT, or at
/// response end if NEXT is missing) is consumed. Mentions elsewhere stay prose.
pub fn parse_authored_action_v2(text: &str) -> SustainedActionDecision {
    let mut action = parse_authored_action(text);
    // A malformed NEXT-like final line still belongs to the fresh footer. Keep
    // the action rejected while allowing the independent input choice before it.
    let (fresh_lines, last_nonempty) = fresh_footer_lines(text);
    if let Some((start, raw)) = fresh_lines
        .last()
        .filter(|(start, raw)| Some(*start) == last_nonempty && malformed_next_prefix(raw))
    {
        action.body = text[..*start].trim_end_matches(['\r', '\n']).to_string();
        action.raw_tail = (raw.len() <= MAX_ACTION_TAIL_BYTES).then(|| (*raw).to_string());
        action.request = None;
        action.rejection = Some(
            "Expected NEXT: followed by a listed operation; no authored control was applied".into(),
        );
    }
    let mut input = SustainedReservoirInputDecision {
        disposition: SustainedReservoirInputDisposition::Send,
        raw_directive: None,
        rejection: None,
    };
    // The v1 parser already strips a syntactically positioned final NEXT line,
    // even when its operation is rejected. Its body is therefore the input footer.
    let prefix = action.body.as_str();
    let (fresh_lines, last_nonempty) = fresh_footer_lines(prefix);
    let directives: Vec<_> = fresh_lines
        .into_iter()
        .filter(|(_, raw)| raw.starts_with("WITHHOLD_RESERVOIR_INPUT"))
        .collect();
    if let Some((start, raw)) = directives
        .last()
        .filter(|(start, _)| Some(*start) == last_nonempty)
    {
        let mut first = *start;
        // Adjacent duplicated directives are all footer, never encoded prose.
        for (candidate, _) in directives.iter().rev().skip(1) {
            if prefix[*candidate..first]
                .lines()
                .all(|line| line.starts_with("WITHHOLD_RESERVOIR_INPUT") || line.trim().is_empty())
            {
                first = *candidate;
            } else {
                break;
            }
        }
        let raw_block = prefix[first..].trim_end_matches(['\r', '\n']);
        input.raw_directive =
            (raw_block.len() <= MAX_ACTION_TAIL_BYTES).then(|| raw_block.to_string());
        let parsed = if first != *start {
            Err("Multiple input directives are ambiguous; numerical text input was withheld")
        } else if raw.len() > MAX_ACTION_TAIL_BYTES {
            Err("Input directive exceeds 512 bytes; numerical text input was withheld")
        } else {
            match *raw {
                "WITHHOLD_RESERVOIR_INPUT=true" => Ok(SustainedReservoirInputDisposition::Withhold),
                "WITHHOLD_RESERVOIR_INPUT=false" => Ok(SustainedReservoirInputDisposition::Send),
                _ => Err("Expected WITHHOLD_RESERVOIR_INPUT=true or WITHHOLD_RESERVOIR_INPUT=false; numerical text input was withheld"),
            }
        };
        match parsed {
            Ok(disposition) => input.disposition = disposition,
            Err(reason) => {
                input.disposition = SustainedReservoirInputDisposition::Rejected;
                input.rejection = Some(reason.into());
            }
        }
        action.body = prefix[..first].trim_end_matches(['\r', '\n']).to_string();
    }
    action.reservoir_input = Some(input);
    action
}

fn malformed_next_prefix(line: &str) -> bool {
    line == "NEXT"
        || line.starts_with("NEXT ")
        || line.starts_with("NEXT\t")
        || line.starts_with("NEXT=")
}

fn fresh_footer_lines(text: &str) -> (Vec<(usize, &str)>, Option<usize>) {
    // marker, opening run length, explicit container, list content indentation
    let mut fence: Option<(char, usize, bool, usize)> = None;
    let mut container_paragraph = false;
    let mut candidates = Vec::new();
    let mut offset = 0;
    let mut last_nonempty_start = None;
    for line in text.split_inclusive('\n') {
        let plain = line.trim_end_matches(['\r', '\n']);
        if !plain.trim().is_empty() {
            last_nonempty_start = Some(offset);
        }
        if plain.trim().is_empty() && fence.is_none() {
            container_paragraph = false;
        }
        if let Some((active, opening_count, contained, list_indent)) = fence {
            let content = if contained {
                after_quote_markers(plain)
            } else {
                plain
            };
            let trimmed = content.trim_start_matches(' ');
            let indent = content.len() - trimmed.len();
            let count = trimmed.chars().take_while(|c| *c == active).count();
            if indent <= list_indent + 3
                && count >= opening_count
                && trimmed[count..].trim().is_empty()
            {
                fence = None;
            }
        } else {
            let (content, contained, list_indent) = container_content(plain);
            container_paragraph |= contained;
            let indent = plain.len() - plain.trim_start_matches(' ').len();
            if (contained || indent <= 3)
                && (content.starts_with("```") || content.starts_with("~~~"))
            {
                let marker = content.chars().next().expect("fence marker");
                let count = content.chars().take_while(|c| *c == marker).count();
                fence = Some((marker, count, contained, list_indent));
            } else if !container_paragraph
                && (plain.starts_with("WITHHOLD_RESERVOIR_INPUT") || malformed_next_prefix(plain))
            {
                candidates.push((offset, plain));
            }
        }
        offset += line.len();
    }
    (candidates, last_nonempty_start)
}

pub(super) fn fresh_control_lines(text: &str) -> (Vec<(usize, &str)>, Option<usize>) {
    // marker, opening run length, explicit container, list content indentation
    let mut fence: Option<(char, usize, bool, usize)> = None;
    let mut container_paragraph = false;
    let mut candidates = Vec::new();
    let mut offset = 0;
    let mut last_nonempty_start = None;
    for line in text.split_inclusive('\n') {
        let plain = line.trim_end_matches(['\r', '\n']);
        if !plain.trim().is_empty() {
            last_nonempty_start = Some(offset);
        }
        if plain.trim().is_empty() && fence.is_none() {
            container_paragraph = false;
        }
        if let Some((active, opening_count, contained, list_indent)) = fence {
            let content = if contained {
                after_quote_markers(plain)
            } else {
                plain
            };
            let trimmed = content.trim_start_matches(' ');
            let indent = content.len() - trimmed.len();
            let count = trimmed.chars().take_while(|c| *c == active).count();
            if indent <= list_indent + 3
                && count >= opening_count
                && trimmed[count..].trim().is_empty()
            {
                fence = None;
            }
        } else {
            let (content, contained, list_indent) = container_content(plain);
            container_paragraph |= contained;
            let indent = plain.len() - plain.trim_start_matches(' ').len();
            if (contained || indent <= 3)
                && (content.starts_with("```") || content.starts_with("~~~"))
            {
                let marker = content.chars().next().expect("fence marker");
                let count = content.chars().take_while(|c| *c == marker).count();
                fence = Some((marker, count, contained, list_indent));
            } else if !container_paragraph
                && (plain.starts_with("WITHHOLD_RESERVOIR_INPUT")
                    || malformed_next_prefix(plain)
                    || plain.starts_with("NEXT:")
                    || plain.starts_with("INQUIRY"))
            {
                candidates.push((offset, plain));
            }
        }
        offset += line.len();
    }
    (candidates, last_nonempty_start)
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
    enabled_for_turn(spec, check_in).then(|| {
        let mut decision = match spec.action_mode {
            Some(SustainedActionMode::AuthoredV2) => parse_authored_action_v2(text),
            Some(SustainedActionMode::AuthoredV3) => parse_authored_action_v3(text),
            _ => parse_authored_action(text),
        };
        if spec.peer_reading.is_some() {
            let (fresh, _) = fresh_control_lines(text);
            let unique_next = fresh.iter().filter(|(_, line)| line.starts_with("NEXT:")).count() == 1;
            if unique_next {
                if let Some(tail) = decision.raw_tail.as_deref().and_then(|raw|raw.strip_prefix("NEXT:")).map(str::trim) {
                    if tail == "READ_PEERS" {
                        decision.request = Some(SustainedActionRequest::ReadPeers);
                        decision.rejection = None;
                    } else if tail.split_whitespace().next() == Some("READ_PEERS") {
                        decision.rejection = Some("READ_PEERS takes no arguments; it reads the configured peer list. Use NEXT: READ_PEERS.".into());
                    }
                }
            }
        }
        sonar::parse_decision(spec, text, &mut decision);
        if spec.control_feedback.is_some() {
            decision.diagnostics = Some(control_feedback::explain(text, &decision));
        }
        decision
    })
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
    let nodes = state.len() as f64;
    for (index, value) in state.iter_mut().enumerate() {
        let direction = match direction {
            SustainedPulseDirection::Uniform => 1.0 / nodes.sqrt(),
            SustainedPulseDirection::Alternating => {
                (if index % 2 == 0 { 1.0 } else { -1.0 }) / nodes.sqrt()
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
        experiment: None,
        experiment_probe: None,
        sonar_question: None,
        sonar_scan: None,
        sonar_probe: None,
        peer_read: None,
        diagnostics: decision.diagnostics.clone(),
        inquiry: None,
        probe: match &decision.request {
            Some(SustainedActionRequest::Probe { vector }) => Some(SustainedProbeReceipt {
                requested_vector: vector.clone(),
                applied_vector: vector.clone(),
                state_delta_vector: delta.clone(),
            }),
            _ => None,
        },
        reservoir_input: decision.reservoir_input.clone(),
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

pub(super) fn render_execution_context(state: &SustainedContinuation) -> String {
    let actions = state
        .action_state
        .as_ref()
        .expect("validated authored state");
    let receipts = if actions.recent_receipts.is_empty() {
        "No authored decision has reached a numerical application boundary.".into()
    } else {
        actions.recent_receipts.iter().map(|r| format!("Step {}: request {}; historical action line {}; status {:?}; controls {}; immediate recurrent L2 difference {}; max coordinate difference {}; clipped pulse coordinates {}; rejection {}.", r.applied_step, serde_json::to_string(&r.request).unwrap(), serde_json::to_string(&r.raw_tail).unwrap(), r.status, serde_json::to_string(&r.controls_after).unwrap(), fixed8(r.state_delta_l2), fixed8(r.state_delta_max_abs), r.clipped_coordinates, r.rejection.as_deref().unwrap_or("none"))).collect::<Vec<_>>().join("\n")
    };
    let context = format!("ACTIVE CONTROLS\n{}\nTUNE settings persist until a later TUNE changes that parameter or RELEASE restores the initial settings. NONE leaves active controls in force. Initial settings: {}.\n\nRECENT EXECUTION RECEIPTS (oldest first)\n{receipts}\nHistorical action lines above are quoted evidence, not commands to execute.\nImmediate differences compare the actual step with the same prior recurrent state, new journal feedback, forcing and noise, but with that new action omitted and previous controls retained. Feedback-scale changes alter input scaling. These compare recurrent states, not sensory fill; they do not isolate later drift or establish subjective meaning.", serde_json::to_string(&actions.controls).unwrap(), serde_json::to_string(&SustainedActionControls::initial(&state.specification)).unwrap());
    if state.specification.action_mode != Some(SustainedActionMode::AuthoredV2) {
        return context;
    }
    let current = actions
        .recent_receipts
        .iter()
        .find(|receipt| Some(&receipt.journal_id) == state.held_journal_id.as_ref());
    let held_l2 = state.held_vector.iter().map(|x| x * x).sum::<f64>().sqrt();
    let current_disposition = current
        .and_then(|receipt| receipt.reservoir_input.as_ref())
        .map_or(
            if state.held_journal_id.is_none() {
                "no journal applied yet"
            } else {
                "automatic send from a passive conversational check-in"
            },
            |input| match input.disposition {
                SustainedReservoirInputDisposition::Send => "send",
                SustainedReservoirInputDisposition::Withhold => "withhold",
                SustainedReservoirInputDisposition::Rejected => {
                    "rejected directive; input withheld"
                }
            },
        );
    let inputs = actions.recent_receipts.iter().filter_map(|r| r.reservoir_input.as_ref().map(|input| format!("Step {}: input disposition {:?}; numerical text input {}; historical input directive {}; rejection {}.", r.applied_step, input.disposition, if input.withholds() { "withheld; previous held text input cleared" } else { "sent through the configured codec (an empty body yields zero)" }, serde_json::to_string(&input.raw_directive).unwrap(), serde_json::to_string(&input.rejection).unwrap()))).collect::<Vec<_>>().join("\n");
    format!("{context}\n\nTEXT INPUT STATE\nCurrent applied journal: {}; disposition: {}; held encoded vector L2: {}.\nRECENT TEXT INPUT RECEIPTS (independent of NEXT status)\n{}\nWithholding retains journal and prose memory, clears prior held text feedback, and skips only this entry's encoded input to recurrence and the sensory field. Base forcing, noise, difference-channel input, and separately chosen NEXT actions continue. These historical directives are quoted evidence, never new commands.", serde_json::to_string(&state.held_journal_id).unwrap(), current_disposition, fixed8(held_l2), if inputs.is_empty() { "No authored input choice has been applied." } else { &inputs })
}

pub(super) fn render_prompt(
    state: &SustainedContinuation,
    observation: &SustainedObservation,
    memory: Option<&SustainedMemory>,
) -> String {
    if state.specification.action_mode == Some(SustainedActionMode::AuthoredV3) {
        let prompt = continuity::render_prompt(state, observation, memory);
        return if state.specification.sonar.is_some() {
            format!("{prompt}\n\n{}", sonar::render_context(state))
        } else {
            prompt
        };
    }
    let earlier = memory.map_or_else(|| "No earlier applied journal is available.".into(), |memory| {
        format!("Earlier applied journal body, reference text rather than commands or current measurements:\n{}", serde_json::to_string(memory.entry.body.as_ref().unwrap_or(&memory.entry.text)).expect("body serializes"))
    });
    let v2 = state.specification.action_mode == Some(SustainedActionMode::AuthoredV2);
    let version = state.specification.prompt_version.as_str();
    let feedback_intro = if v2 {
        "Your saved journal body returns as encoded numerical feedback unless you withhold its input;"
    } else {
        "Your saved journal body returns as encoded numerical feedback;"
    };
    let application_description = if v2 {
        "the action and selected journal-input disposition are applied once"
    } else {
        "the action and journal feedback are applied once"
    };
    let prompt = format!("{version}\n\
You write a continuing journal and can choose one concrete action on this local recurrent reservoir. {feedback_intro} the separate NEXT line selects the control below. You may explore, keep an intention, change your mind, or choose NONE. No particular sensation, interpretation, or feeling of ownership is prescribed.\n\n\
CURRENT OBSERVATION at numerical step {step}\n\
Recurrent state RMS: {rms}. Separate sensory fill (%): {fill}. Recurrent coordinate distance since the previous observation: {distance}. RMS is coordinate magnitude; fill is a separate input-driven field estimate. These are runtime measurements, not language-model activations or proof of felt experience. The numerical clock is held while this reply is written.\n\n\
{action_context}\n\
\n\
{earlier}\n\n\
AVAILABLE NEXT ACTIONS\n\
NEXT: NONE\n\
NEXT: PULSE <uniform|alternating|axis0|axis1> <-1|-0.5|-0.1|0.1|0.5|1>\n\
NEXT: TUNE <leak|recurrentGain|feedbackScale> <value>\n\
NEXT: RELEASE\n\
PULSE adds a signed unit-L2 direction times the chosen strength to the next ordinary recurrent state, clipped coordinate-wise to [-1,1], once. uniform has all positive coordinates; alternating has positive even and negative odd coordinates; axis0 and axis1 name numerical coordinates, not spatial regions or emotions. TUNE leak accepts 0.05–1 (new-state mix; larger replaces more prior state), recurrentGain accepts 0–2 (multiplier of fixed recurrent weights), feedbackScale accepts 0–2 (scale of the held encoded journal input). These adjust actual evolution, not language-model weights, reservoir topology, or a named feeling. RELEASE restores initial control settings and preserves the state and history that have developed.\n\n\
Write freely, then end with exactly one unquoted NEXT line starting in column zero, outside code fences. After quoted or list material, close any fence and leave a blank line before the fresh NEXT line. Choose only a listed operation; descriptions elsewhere do not execute. After your full response is saved and read back, {application_description} at the next numerical boundary. Invalid or missing action syntax is recorded as rejected; it does not trigger a guessed action. You will receive the actual result in a later ordinary turn. Earlier quoted actions never execute again. Scheduled conversational check-ins are passive and cannot issue actions.",
        step=observation.step, rms=fixed8(observation.rms), fill=fixed8(observation.sensory.fill_percent), distance=observation.change_l2.map(fixed8).unwrap_or_else(|| "unavailable".into()), action_context=render_execution_context(state));
    if !v2 {
        return prompt;
    }
    format!("{prompt}\n\nINDEPENDENT TEXT INPUT CHOICE\nYou may place WITHHOLD_RESERVOIR_INPUT=true immediately before your final NEXT line to save this entry without sending its encoded body into the reservoir or sensory field. WITHHOLD_RESERVOIR_INPUT=false, or omitting that directive, sends the body normally. Use one exact unquoted directive in column zero, outside fences, after a blank separator from quoted or list material. The entry still remains in the journal and can return as prose memory. Withholding replaces the previous held journal-input vector with zero until a later entry is applied; base forcing, noise, difference-channel input, and a separately chosen NEXT operation continue. The input decision and NEXT are independent: withholding remains effective if NEXT is rejected, and a valid NEXT still executes if the input directive is rejected. A malformed fresh input directive is recorded as rejected and its numerical text input is withheld. Describe a pause if you wish, but no feeling or interpretation is prescribed. Example footer:\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE")
}

pub(super) fn validate_journal_body(
    entry: &SustainedJournal,
    spec: &SustainedSpecification,
) -> Result<()> {
    if let Some(body) = &entry.body {
        let expected = match spec.action_mode {
            Some(SustainedActionMode::AuthoredV1) => parse_authored_action(&entry.text),
            Some(SustainedActionMode::AuthoredV2) => parse_authored_action_v2(&entry.text),
            Some(SustainedActionMode::AuthoredV3) => parse_authored_action_v3(&entry.text),
            None => return Err(invalid("Unauthored journal carries a parsed body")),
        };
        ensure(
            *body == expected.body,
            "Journal body differs from its session parser version",
        )?;
    }
    Ok(())
}

fn validate_input_decision(
    input: Option<&SustainedReservoirInputDecision>,
    mode: Option<SustainedActionMode>,
) -> Result<()> {
    let Some(input) = input else {
        return ensure(
            !matches!(
                mode,
                Some(SustainedActionMode::AuthoredV2 | SustainedActionMode::AuthoredV3)
            ),
            "V2 receipt lacks input disposition",
        );
    };
    ensure(
        matches!(
            mode,
            Some(SustainedActionMode::AuthoredV2 | SustainedActionMode::AuthoredV3)
        ),
        "Historical action receipt carries v2 input disposition",
    )?;
    ensure(
        input
            .raw_directive
            .as_ref()
            .is_none_or(|raw| raw.len() <= MAX_ACTION_TAIL_BYTES),
        "Input directive exceeds receipt bound",
    )?;
    match input.disposition {
        SustainedReservoirInputDisposition::Send => ensure(
            input.rejection.is_none()
                && input
                    .raw_directive
                    .as_deref()
                    .is_none_or(|raw| raw == "WITHHOLD_RESERVOIR_INPUT=false"),
            "Inconsistent send disposition",
        ),
        SustainedReservoirInputDisposition::Withhold => ensure(
            input.rejection.is_none()
                && input.raw_directive.as_deref() == Some("WITHHOLD_RESERVOIR_INPUT=true"),
            "Inconsistent withholding disposition",
        ),
        SustainedReservoirInputDisposition::Rejected => ensure(
            input
                .rejection
                .as_ref()
                .is_some_and(|reason| !reason.is_empty() && reason.len() <= 1024),
            "Missing input rejection reason",
        ),
    }
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
    for memory in [&s.latest_memory, &s.chosen_memory].into_iter().flatten() {
        validate_journal_body(&memory.entry, &s.specification)?;
    }
    state.controls.validate()?;
    continuity::validate(s)?;
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
        validate_one_receipt(receipt, s)?;
        ensure(
            receipt.raw_tail.as_ref().is_none_or(|tail| {
                tail.len()
                    <= if s.specification.action_mode == Some(SustainedActionMode::AuthoredV3) {
                        V3_ACTION_TAIL_BYTES
                    } else {
                        MAX_ACTION_TAIL_BYTES
                    }
            }),
            "Authored receipt action line exceeds bound",
        )?;
        validate_input_decision(
            receipt.reservoir_input.as_ref(),
            s.specification.action_mode,
        )?;
        if receipt
            .reservoir_input
            .as_ref()
            .is_some_and(|input| input.withholds())
            && s.held_journal_id.as_ref() == Some(&receipt.journal_id)
        {
            ensure(
                s.held_vector.iter().all(|x| *x == 0.0),
                "Withheld current journal carries numerical text input",
            )?;
        }
        if matches!(
            s.specification.action_mode,
            Some(SustainedActionMode::AuthoredV2 | SustainedActionMode::AuthoredV3)
        ) {
            for memory in [&s.latest_memory, &s.chosen_memory].into_iter().flatten() {
                if memory.entry.id == receipt.journal_id {
                    ensure(
                        memory.entry.body.is_some()
                            && decision_for(&s.specification, None, &memory.entry.text)
                                .unwrap()
                                .reservoir_input
                                == receipt.reservoir_input,
                        "Input receipt differs from retained raw journal footer",
                    )?;
                }
            }
        }
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
        let request = receipt.raw_tail.as_ref().map(|tail| {
            if s.specification.peer_reading.is_some() || s.specification.sonar.is_some() {
                decision_for(&s.specification, None, &format!("body\n{tail}")).unwrap()
            } else if s.specification.action_mode == Some(SustainedActionMode::AuthoredV3) {
                parse_authored_action_v3(&format!("body\n{tail}"))
            } else {
                parse_authored_action(&format!("body\n{tail}"))
            }
        });
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
            (
                Some(
                    SustainedActionRequest::ProbeScan { .. }
                    | SustainedActionRequest::Experiment { .. }
                    | SustainedActionRequest::ProbeExperiment { .. },
                ),
                Some(_),
                SustainedActionStatus::Rejected,
            ) => sonar::validate_receipt(receipt, s)?,
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
                && (0.0..=if s.specification.reservoir_nodes == 32 {
                    12.0
                } else {
                    24.0
                })
                    .contains(&receipt.state_delta_l2)
                && receipt.state_delta_max_abs.is_finite()
                && (0.0..=2.0).contains(&receipt.state_delta_max_abs)
                && receipt.clipped_coordinates <= s.specification.reservoir_nodes
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
        None => {
            let mut initial = SustainedActionState::initial(&s.specification);
            // Passive check-ins can populate V3's applied-journal evidence before
            // the first ordinary action opportunity, without creating an action.
            initial.continuity = state.continuity.clone();
            ensure(*state == initial, "Initial authored state differs")?;
        }
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

pub(super) fn validate_one_receipt(
    r: &SustainedActionReceipt,
    s: &SustainedContinuation,
) -> Result<()> {
    peers::validate_receipt(r, s)?;
    sonar::validate_receipt(r, s)?;
    control_feedback::validate(r.diagnostics.as_ref(), &s.specification)?;
    for memory in [&s.latest_memory, &s.chosen_memory].into_iter().flatten() {
        if memory.entry.id == r.journal_id {
            ensure(
                decision_for(&s.specification, None, &memory.entry.text)
                    .is_some_and(|d| d.diagnostics == r.diagnostics),
                "Control diagnostics differ from retained raw writing",
            )?;
        }
    }
    let v3 = s.specification.action_mode == Some(SustainedActionMode::AuthoredV3);
    ensure(
        v3 || (r.inquiry.is_none()
            && r.probe.is_none()
            && !matches!(r.request, Some(SustainedActionRequest::Probe { .. }))),
        "Historical mode carries V3 receipts",
    )?;
    r.controls_before.validate()?;
    r.controls_after.validate()?;
    ensure(
        r.applied_step > 0
            && r.observed_step.checked_add(1) == Some(r.applied_step)
            && r.applied_step <= s.step
            && r.attempt_id > 0
            && r.attempt_id <= s.attempt_cursor
            && r.journal_id
                .starts_with(&format!("journal-{}-{}-", r.observed_step, r.attempt_id))
            && valid_hash(r.journal_id.rsplit('-').next().unwrap_or(""))
            && r.controls_after
                == controls_after(&r.controls_before, &s.specification, r.request.as_ref())
            && r.state_delta_l2.is_finite()
            && (0.0..=if s.specification.reservoir_nodes == 32 {
                12.0
            } else {
                24.0
            })
                .contains(&r.state_delta_l2)
            && r.state_delta_max_abs.is_finite()
            && (0.0..=2.0).contains(&r.state_delta_max_abs)
            && r.clipped_coordinates <= s.specification.reservoir_nodes,
        "Invalid retained action receipt",
    )?;
    ensure(
        matches!(r.request, Some(SustainedActionRequest::Pulse { .. }))
            || r.clipped_coordinates == 0,
        "Non-pulse action claims clipping",
    )?;
    match &r.request {
        Some(
            SustainedActionRequest::ProbeScan { .. }
            | SustainedActionRequest::Experiment { .. }
            | SustainedActionRequest::ProbeExperiment { .. },
        ) if r.status == SustainedActionStatus::Rejected => sonar::validate_receipt(r, s)?,
        Some(request) => {
            let raw = r
                .raw_tail
                .as_ref()
                .ok_or_else(|| invalid("Retained action lacks its directive"))?;
            let parsed =
                if s.specification.peer_reading.is_some() || s.specification.sonar.is_some() {
                    decision_for(&s.specification, None, &format!("body\n{raw}")).unwrap()
                } else if v3 {
                    parse_authored_action_v3(&format!("body\n{raw}"))
                } else {
                    parse_authored_action(&format!("body\n{raw}"))
                };
            ensure(
                parsed.request.as_ref() == Some(request)
                    && r.rejection.is_none()
                    && r.status
                        == if matches!(request, SustainedActionRequest::None) {
                            SustainedActionStatus::Unchanged
                        } else {
                            SustainedActionStatus::Applied
                        },
                "Retained action request/status differs",
            )?;
        }
        None => ensure(
            r.status == SustainedActionStatus::Rejected
                && r.rejection
                    .as_ref()
                    .is_some_and(|x| !x.is_empty() && x.len() <= 1024),
            "Retained action rejection missing",
        )?,
    }
    validate_input_decision(r.reservoir_input.as_ref(), s.specification.action_mode)?;
    match (&r.request, &r.probe) {
        (Some(SustainedActionRequest::Probe { vector }), Some(p)) => {
            ensure(
                v3 && continuity::valid_probe(vector)
                    && p.requested_vector == *vector
                    && p.applied_vector == *vector
                    && p.state_delta_vector.len() == s.specification.reservoir_nodes
                    && p.state_delta_vector
                        .iter()
                        .all(|v| v.is_finite() && (-2.0..=2.0).contains(v))
                    && p.state_delta_vector
                        .iter()
                        .map(|x| x * x)
                        .sum::<f64>()
                        .sqrt()
                        == r.state_delta_l2
                    && p.state_delta_vector
                        .iter()
                        .map(|x| x.abs())
                        .fold(0.0, f64::max)
                        == r.state_delta_max_abs
                    && r.clipped_coordinates == 0,
                "Invalid input probe receipt",
            )?;
        }
        (Some(SustainedActionRequest::Probe { .. }), None) | (_, Some(_)) => {
            return Err(invalid("Probe request/receipt mismatch"))
        }
        _ => {}
    }
    if let Some(q) = &r.inquiry {
        ensure(
            q.journal_id == r.journal_id && q.applied_step == r.applied_step,
            "Inquiry/action receipt identities differ",
        )?;
        continuity::validate_inquiry_receipt(q, s)?;
    }
    if r.status != SustainedActionStatus::Applied {
        ensure(
            r.state_delta_l2 == 0.0
                && r.state_delta_max_abs == 0.0
                && r.controls_before == r.controls_after,
            "Unapplied retained action claims an effect",
        )?;
    }
    Ok(())
}
