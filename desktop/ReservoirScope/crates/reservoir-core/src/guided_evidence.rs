//! Mechanical guided observations from a verified action-record prefix.
//!
//! This is a port of native `GuidedEvidenceEvaluator`, not a record verifier.
//! Callers must first accept the record with `ActionComparisonRecord::verify`.
//! Historical provider/save receipts are retained claims, not external authentication.
//! No file paths, providers or journal text instructions are executed.
use crate::{
    actions::{
        ActionComparisonRecord, ActionReceipt, ComparisonKind, ComparisonMode, JournalAction,
        SaveStatus,
    },
    stage::{LanguageKind, TurnStatus},
};
use serde::Serialize;

pub const TOLERANCE: f64 = 1e-12;

#[derive(Clone, Copy, Debug, Serialize, PartialEq, Eq)]
pub enum LessonEvidenceState {
    #[serde(rename = "Not reached yet")]
    NotYetObserved,
    #[serde(rename = "Observed")]
    Observed,
    #[serde(rename = "Different outcome")]
    DifferentResult,
    #[serde(rename = "Incomplete evidence")]
    Incomplete,
    #[serde(rename = "No matched comparison")]
    NotApplicable,
}

#[derive(Clone, Debug, Serialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct LessonEvidence {
    pub state: LessonEvidenceState,
    pub observation: String,
    pub evidence_steps: Vec<usize>,
}

fn result(
    state: LessonEvidenceState,
    observation: impl Into<String>,
    steps: &[usize],
) -> LessonEvidence {
    LessonEvidence {
        state,
        observation: observation.into(),
        evidence_steps: steps.to_vec(),
    }
}

pub fn unopened() -> LessonEvidence {
    result(
        LessonEvidenceState::NotYetObserved,
        "Open an example to inspect recorded evidence.",
        &[],
    )
}

fn rms(values: &[f64]) -> f64 {
    if values.is_empty() {
        0.0
    } else {
        (values.iter().fold(0.0, |sum, value| sum + value * value) / values.len() as f64).sqrt()
    }
}
fn delta(a: &[f64], b: &[f64]) -> f64 {
    if a.len() != b.len() {
        f64::INFINITY
    } else {
        rms(&a.iter().zip(b).map(|(a, b)| b - a).collect::<Vec<_>>())
    }
}
fn status(status: &TurnStatus) -> &'static str {
    match status {
        TurnStatus::Completed => "completed",
        TurnStatus::Failed => "failed",
        TurnStatus::Cancelled => "cancelled",
    }
}
fn before_journal(step: usize) -> LessonEvidence {
    result(
        LessonEvidenceState::NotYetObserved,
        format!("No writing opportunity at or before step {step}."),
        &[],
    )
}
fn failed_or_pending(action: &ActionReceipt) -> LessonEvidence {
    let outcome = if action
        .save_receipt
        .as_ref()
        .is_some_and(|r| r.status == SaveStatus::Failed)
    {
        "journal save failed"
    } else {
        status(&action.status)
    };
    result(
        LessonEvidenceState::Incomplete,
        format!(
            "Opportunity at {}: {outcome}. No successful saved journal is established here.",
            action.observed_step
        ),
        &[action.observed_step],
    )
}

/// Evaluate only the retained prefix ending at the last right-arm frame at or
/// before `cursor_step`. Zero or an empty prefix returns the unopened state.
/// This does not rerun verification, score prose, or infer provider authentication.
pub fn evaluate(record: &ActionComparisonRecord, cursor_step: usize) -> LessonEvidence {
    use LessonEvidenceState::*;
    if cursor_step == 0 {
        return unopened();
    }
    let Some(frame) = record.right.frames.iter().rfind(|f| f.step <= cursor_step) else {
        return unopened();
    };
    let step = frame.step;
    let right: Vec<_> = record
        .right
        .frames
        .iter()
        .filter(|f| f.step <= step)
        .collect();
    let left: Vec<_> = record
        .left
        .iter()
        .flat_map(|r| &r.frames)
        .filter(|f| f.step <= step)
        .collect();
    let paired = !left.is_empty()
        && left.len() == right.len()
        && left.iter().zip(&right).all(|(a, b)| a.step == b.step);
    let first_difference = if paired {
        left.iter()
            .zip(&right)
            .find(|(a, b)| delta(&a.state, &b.state) > TOLERANCE)
            .map(|(_, b)| b.step)
    } else {
        None
    };
    let actions: Vec<_> = record
        .right
        .actions
        .iter()
        .filter(|a| a.observed_step <= step)
        .collect();
    let saved: Vec<_> = actions
        .iter()
        .copied()
        .filter(|a| {
            a.status == TurnStatus::Completed
                && a.save_receipt
                    .as_ref()
                    .is_some_and(|r| r.status == SaveStatus::Saved)
        })
        .collect();
    let journals: Vec<_> = record
        .right
        .journals
        .iter()
        .filter(|j| j.observed_step <= step)
        .collect();

    if record.specification.comparison_kind == ComparisonKind::Observation {
        if !paired {
            return result(Incomplete, "Both observation arms are required.", &[]);
        }
        let right_action = actions.last();
        let left_action = record
            .left
            .as_ref()
            .and_then(|r| r.actions.iter().rfind(|a| a.observed_step <= step));
        if let (Some(a), Some(b)) = (right_action, left_action) {
            let complete = a.status == TurnStatus::Completed && b.status == TurnStatus::Completed;
            return result(if complete { Observed } else { Incomplete }, format!("States {} through step {step}. Opportunity {}: sensory arm {}, added-state arm {}. Different wording is not an improvement score.", if first_difference.is_none() { "match" } else { "differ" }, a.observed_step, status(&b.status), status(&a.status)), &[a.observed_step]);
        }
        return result(
            NotYetObserved,
            format!("States match through step {step}; no writing opportunity has been reached."),
            &[],
        );
    }

    match record.specification.stage {
        1 => {
            let quiet = rms(&frame.external_input) <= TOLERANCE;
            let previous = right.iter().rev().nth(1);
            let decaying =
                quiet && previous.is_some_and(|previous| rms(&frame.state) < rms(&previous.state));
            result(
                Observed,
                format!(
                    "Input is {}. State magnitude is {:.3}.{}",
                    if quiet { "quiet" } else { "active" },
                    rms(&frame.state),
                    if decaying {
                        " It is lower than at the preceding step."
                    } else {
                        ""
                    }
                ),
                &[step],
            )
        }
        2 => {
            if !paired {
                return result(NotApplicable, "This recording has one arm; a matched comparison is needed to isolate recurrence.", &[step]);
            }
            if let Some(first) = first_difference {
                return result(Observed, format!("The first state difference is at step {first}; matched inputs are retained."), &[first]);
            }
            result(
                if step < 2 {
                    NotYetObserved
                } else {
                    DifferentResult
                },
                format!("The two recorded states still match through step {step}."),
                &[step],
            )
        }
        3 => {
            if frame.spectral.is_none() {
                return result(Incomplete, "This step has no sensory measurement.", &[step]);
            }
            let comparison = if paired {
                if first_difference.is_none() {
                    "Reservoir states still match."
                } else {
                    "Reservoir states differ; inspect the setup."
                }
            } else {
                "This is a single recorded arm."
            };
            result(
                Observed,
                format!("A separate sensory spectrum is recorded at step {step}. {comparison}"),
                &[step],
            )
        }
        4 => {
            let Some(action) = actions.last() else {
                return before_journal(step);
            };
            if !saved.iter().any(|saved| saved.id == action.id) {
                return failed_or_pending(action);
            }
            let comparison = if paired {
                if first_difference.is_none() {
                    "Writing has left the matched reservoir states unchanged."
                } else {
                    "States differ; this recording does not isolate unchanged state."
                }
            } else {
                "There is no control arm for a state-effect comparison."
            };
            result(
                Observed,
                format!(
                    "A journal was saved at step {}. {comparison}",
                    action.observed_step
                ),
                &[action.observed_step],
            )
        }
        5 => {
            let Some(action) = saved.iter().find(|a| a.semantic_vector.is_some()) else {
                return actions
                    .last()
                    .map_or_else(|| before_journal(step), |a| failed_or_pending(a));
            };
            let Some(applied) = action.application_step.filter(|applied| *applied <= step) else {
                return result(NotYetObserved, format!("Journal saved at {}; its return has not been applied at this cursor. Step forward to inspect the application.", action.observed_step), &[action.observed_step]);
            };
            if !right
                .iter()
                .any(|f| f.step == applied && f.semantic_action_id == Some(action.id))
            {
                return result(
                    Incomplete,
                    "The application receipt has no matching input frame.",
                    &[applied],
                );
            }
            let comparison = if paired {
                first_difference.map_or_else(
                    || "States still match through this cursor.".into(),
                    |first| format!("First state difference: step {first}."),
                )
            } else {
                "The application is recorded; this run has no control arm.".into()
            };
            result(
                Observed,
                format!(
                    "Journal saved at {}, first applied at {applied}. {comparison}",
                    action.observed_step
                ),
                &[action.observed_step, applied],
            )
        }
        6 => {
            let Some(action) = actions.iter().rfind(|a| a.memory_entry_id.is_some()) else {
                if let Some(failed) = actions.last().filter(|a| a.status != TurnStatus::Completed) {
                    return failed_or_pending(failed);
                }
                return result(NotYetObserved, "No earlier journal is present in the prompt at this cursor. Continue to the next writing opportunity.", &[]);
            };
            let prior = journals
                .iter()
                .find(|j| Some(&j.id) == action.memory_entry_id.as_ref());
            let Some(prior) = prior.filter(|prior| {
                prior.observed_step < action.observed_step
                    && action.memory_text.as_ref() == Some(&prior.text)
                    && action.prompt.contains(&prior.text)
            }) else {
                return result(
                    Incomplete,
                    "Memory metadata does not establish exact earlier-journal inclusion.",
                    &[action.observed_step],
                );
            };
            let context = if record.specification.language.backend == LanguageKind::Ollama {
                if action.request_started {
                    "submitted model"
                } else {
                    "prepared, unsubmitted"
                }
            } else {
                "prepared/scripted"
            };
            let limit = if record.specification.mode == ComparisonMode::FixedReplay {
                "Replies remain fixed in this scripted comparison."
            } else {
                "This establishes exposure, not improved writing."
            };
            result(
                Observed,
                format!(
                    "The journal from {} is included in the {context} prompt at {}. {limit}",
                    prior.observed_step, action.observed_step
                ),
                &[prior.observed_step, action.observed_step],
            )
        }
        7 => {
            if let Some(wait) = actions.iter().find(|a| {
                a.chosen_action == Some(JournalAction::Wait) && a.status == TurnStatus::Completed
            }) {
                return result(if wait.journal_entry_id.is_none() && wait.save_receipt.is_none() { Observed } else { Incomplete }, format!("WAIT was chosen at step {}; {}. Earlier returned input remains until a later saved journal replaces it.", wait.observed_step, if wait.journal_entry_id.is_none() { "no journal was written" } else { "unexpected journal evidence is present" }), &[wait.observed_step]);
            }
            if actions.is_empty() {
                return before_journal(step);
            }
            if let Some(action) = actions.last().filter(|a| a.status != TurnStatus::Completed) {
                return failed_or_pending(action);
            }
            result(Observed, format!("{} completed writing choice{} so far. No WAIT has occurred at this cursor; writing is also a valid choice.", actions.len(), if actions.len() == 1 { "" } else { "s" }), &actions.iter().map(|a| a.observed_step).collect::<Vec<_>>())
        }
        8 => {
            let (Some(fill), Some(retention), Some(control)) =
                (frame.fill_percent, frame.retention_used, &frame.control)
            else {
                return result(
                    Incomplete,
                    "Fill, retention and controller evidence are required.",
                    &[step],
                );
            };
            let at_limit = (control.applied_retention - 0.995).abs() < TOLERANCE
                || (control.applied_retention - 0.82).abs() < TOLERANCE;
            let comparison = if paired {
                if first_difference.is_none() {
                    " Reservoir states remain matched."
                } else {
                    " Reservoir states differ."
                }
            } else {
                " This is a single recorded arm."
            };
            result(Observed, format!("Fill {fill:.3}% against 68%; retention {retention:.4}, next {:.4}.{}{comparison}", control.applied_retention, if at_limit { " The controller is at a retention limit." } else { "" }), &[step])
        }
        // An accepted action record cannot reach this branch; keep the public
        // helper total for independently constructed values without a false claim.
        _ => result(Incomplete, "The recorded action stage is unsupported.", &[]),
    }
}
