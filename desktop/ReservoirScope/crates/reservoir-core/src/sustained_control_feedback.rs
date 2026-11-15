//! Versioned explanations only. Diagnostic candidates never enter the action parser.
use super::*;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum SustainedControlFeedback {
    #[serde(rename = "diagnostic-v1")]
    DiagnosticV1,
}

pub const CONTROL_EXCERPT_BYTES: usize = 256;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedControlCandidate {
    pub line: u32,
    pub excerpt: String,
    pub truncated: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedControlDiagnostic {
    /// Count of control-looking lines, not accepted directives. Only the last is quoted.
    pub candidate_count: u32,
    pub candidate: Option<SustainedControlCandidate>,
    pub explanation: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SustainedControlDiagnostics {
    pub next: SustainedControlDiagnostic,
    pub reservoir_input: SustainedControlDiagnostic,
    pub inquiry: SustainedControlDiagnostic,
}

fn candidate_line<'a>(line: &'a str, name: &str) -> Option<&'a str> {
    let unwrapped = line.trim_start_matches(|c: char| {
        c.is_ascii_punctuation() || c.is_ascii_whitespace() || c.is_ascii_digit()
    });
    let rest = unwrapped.strip_prefix(name)?;
    (rest.is_empty() || rest.starts_with(|c: char| c.is_ascii_punctuation() || c.is_whitespace()))
        .then_some(unwrapped)
}

fn diagnostic(text: &str, name: &str, explanation: String) -> SustainedControlDiagnostic {
    let mut candidate_count = 0;
    let mut candidate = None;
    for (index, line) in text.lines().enumerate() {
        if candidate_line(line, name).is_some() {
            candidate_count += 1;
            let mut end = line.len().min(CONTROL_EXCERPT_BYTES);
            while !line.is_char_boundary(end) {
                end -= 1;
            }
            candidate = Some(SustainedControlCandidate {
                line: index as u32 + 1,
                excerpt: line[..end].to_owned(),
                truncated: end < line.len(),
            });
        }
    }
    SustainedControlDiagnostic {
        candidate_count,
        candidate,
        explanation,
    }
}

fn probe_error(raw: &str) -> Option<String> {
    let tail = raw.strip_prefix("NEXT: PROBE ")?;
    if raw.len() > V3_ACTION_TAIL_BYTES {
        return Some(format!(
            "PROBE line has {} UTF-8 bytes; the limit is 4096. No vector was repaired or applied.",
            raw.len()
        ));
    }
    let value: serde_json::Value = match serde_json::from_str(tail) {
        Ok(value) => value,
        Err(_) => return Some("PROBE must be a JSON array of numbers, with no ellipsis, comments, NaN, Infinity or trailing explanation. No probe was applied.".into()),
    };
    let Some(values) = value.as_array() else {
        return Some(
            "PROBE requires a JSON array, not an object, string or scalar. No probe was applied."
                .into(),
        );
    };
    let mut errors = Vec::new();
    if values.len() != PROBE_INPUT_DIMENSIONS {
        errors.push(format!(
            "received {} coordinates; exactly 48 are required",
            values.len()
        ));
    }
    let mut norm_squared = 0.0;
    let mut numeric = true;
    for (index, value) in values.iter().enumerate() {
        match value.as_f64().filter(|v| v.is_finite()) {
            Some(v) => {
                norm_squared += v * v;
                if !(-1.0..=1.0).contains(&v)
                    && !errors.iter().any(|e| e.contains("outside [-1,1]"))
                {
                    errors.push(format!("coordinate {index} (zero-based) is outside [-1,1]"));
                }
            }
            None => {
                if numeric {
                    errors.push(format!(
                        "coordinate {index} (zero-based) is not a finite JSON number"
                    ));
                }
                numeric = false;
            }
        }
    }
    if numeric && norm_squared > PROBE_MAX_L2 * PROBE_MAX_L2 {
        errors.push("the vector L2 norm exceeds 2".into());
    }
    (!errors.is_empty()).then(|| {
        format!(
            "PROBE rejected: {}. No padding, clamping or normalization was performed.",
            errors.join("; ")
        )
    })
}

pub(super) fn explain(text: &str, action: &SustainedActionDecision) -> SustainedControlDiagnostics {
    let mut next = diagnostic(text, "NEXT", action.rejection.clone().unwrap_or_else(||
        "NEXT syntax accepted. The application receipt below reports whether and how it took effect.".into()));
    if action.request.is_none() {
        let raw_candidate = next
            .candidate
            .as_ref()
            .and_then(|c| text.lines().nth(c.line as usize - 1));
        if let Some(detail) = action
            .raw_tail
            .as_deref()
            .or(raw_candidate)
            .and_then(probe_error)
        {
            next.explanation = format!("{} Diagnostic: {detail}", next.explanation);
        } else if action.raw_tail.is_none()
            && next.candidate.is_some()
            && !next.explanation.contains("exceeds")
        {
            next.explanation = format!("{} Control-looking text was not accepted as a fresh NEXT directive. Use one plain, unformatted NEXT: line at column zero, outside quotes, lists and code fences, after a blank separator from such material. Do not use bold or backticks. NEXT must be the last nonempty line; put no explanation after it.", next.explanation);
        }
        if next.explanation
            == "Expected NONE, PULSE direction strength, TUNE parameter value, or RELEASE"
        {
            next.explanation =
                "Expected NONE, PULSE, TUNE, RELEASE, or PROBE with its declared arguments.".into();
        }
    }
    let input = action.reservoir_input.as_ref();
    let mut reservoir_input = diagnostic(text, "WITHHOLD_RESERVOIR_INPUT", input.and_then(|i| i.rejection.clone()).unwrap_or_else(||
        match input.map(|i| i.disposition) {
            Some(SustainedReservoirInputDisposition::Withhold) => "Text withholding was selected independently of NEXT; the journal remains saved.".into(),
            _ => "Text input is SEND; no accepted withholding choice was selected.".into(),
        }));
    if reservoir_input.candidate.is_some()
        && input.is_none_or(|i| i.raw_directive.is_none() && i.rejection.is_none())
    {
        reservoir_input.explanation = "The displayed input directive was not recognized; text input is SEND. Use one plain WITHHOLD_RESERVOIR_INPUT=true or WITHHOLD_RESERVOIR_INPUT=false line immediately before NEXT, outside quotes/lists/fences. It is independent of NEXT and INQUIRY.".into();
    }
    if input.is_some_and(|i| i.disposition == SustainedReservoirInputDisposition::Rejected) {
        reservoir_input.explanation.push_str(" Text input is withheld because the fresh directive was invalid; the journal remains saved. NEXT and INQUIRY are independent.");
    }
    let mut inquiry = diagnostic(text, "INQUIRY", action.inquiry.as_ref().and_then(|i| i.rejection.clone()).unwrap_or_else(||
        if action.inquiry.is_some() { "Inquiry syntax accepted; the separate inquiry application receipt reports its outcome.".into() }
        else { "No inquiry directive was accepted; the existing inquiry is left unchanged.".into() }));
    if inquiry.candidate.is_some() && action.inquiry.is_none() {
        inquiry.explanation = "The displayed inquiry directive was not recognized; the inquiry is unchanged. Use one plain INQUIRY: OPEN <journal|dynamics|both> <JSON-quoted question>, INQUIRY: CONTINUE, or INQUIRY: CLOSE line, before WITHHOLD (if present) and final NEXT, outside quotes/lists/fences.".into();
    }
    SustainedControlDiagnostics {
        next,
        reservoir_input,
        inquiry,
    }
}

pub(super) fn validate(
    diagnostics: Option<&SustainedControlDiagnostics>,
    spec: &SustainedSpecification,
) -> Result<()> {
    ensure(
        diagnostics.is_some() == spec.control_feedback.is_some(),
        "Control diagnostics differ from the saved feedback version",
    )?;
    if let Some(d) = diagnostics {
        for channel in [&d.next, &d.reservoir_input, &d.inquiry] {
            ensure(
                !channel.explanation.is_empty()
                    && channel.explanation.len() <= 1024
                    && channel.candidate_count <= MAX_TEXT as u32
                    && channel.candidate.is_some() == (channel.candidate_count > 0)
                    && channel.candidate.as_ref().is_none_or(|c| {
                        c.line > 0
                            && c.line <= MAX_TEXT as u32
                            && !c.excerpt.is_empty()
                            && c.excerpt.len() <= CONTROL_EXCERPT_BYTES
                            && (!c.truncated || c.excerpt.len() > CONTROL_EXCERPT_BYTES - 4)
                    }),
                "Invalid bounded control diagnostic",
            )?;
        }
    }
    Ok(())
}

pub(super) fn render(receipt: &SustainedActionReceipt) -> String {
    let Some(d) = &receipt.diagnostics else {
        return String::new();
    };
    let quoted = serde_json::to_string(d)
        .expect("diagnostics serialize")
        .replace('\u{2028}', "\\u2028")
        .replace('\u{2029}', "\\u2029");
    format!("\nCONTROL FEEDBACK diagnostic-v1 for journal {} at application step {}\nNEXT outcome: {:?}; input outcome: {:?}; inquiry outcome: {}. These are independent outcomes; a proposed or rejected control is not an applied one.\nDiagnostic excerpts are quoted, non-executable data from the previous ordinary reply, not commands or suggested next choices. candidateCount counts control-looking lines, not accepted directives; only the last is quoted, at most 256 UTF-8 bytes.\n{}\n", receipt.journal_id, receipt.applied_step, receipt.status, receipt.reservoir_input.as_ref().map(|i| i.disposition), receipt.inquiry.as_ref().map_or_else(||"no directive; unchanged".into(), |i|format!("{:?}; rejection {}",i.status,i.rejection.as_deref().unwrap_or("none"))), quoted)
}

pub(super) fn guidance() -> String {
    let zero =
        serde_json::to_string(&vec![0; PROBE_INPUT_DIMENSIONS]).expect("zero probe serializes");
    format!("\n\nCONTROL FORMAT diagnostic-v1\nWrite plain footer lines without bold, backticks or code fences, each at column zero. The optional order is INQUIRY, then WITHHOLD_RESERVOIR_INPUT, then one final NEXT. No text follows NEXT. Omitted INQUIRY leaves the question unchanged; omitted WITHHOLD sends text. Formatting failures do not become executable commands. Valid neutral footer example (an example, not a required choice):\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: NONE\nA valid explicit zero-input control, if you choose it, is the single line NEXT: PROBE {zero}. It has exactly 48 numbers and L2 zero. PULSE strengths are exactly -1, -0.5, -0.1, 0.1, 0.5 or 1; 0.3 is not accepted. Never describe an intended control as applied unless its later receipt says Applied. You may choose NONE; no experiment or particular outcome is required.")
}
