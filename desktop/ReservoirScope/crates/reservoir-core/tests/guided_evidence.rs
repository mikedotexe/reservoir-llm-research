//! Evaluator branches use typed copies of retained examples. Deliberate mutations
//! are not accepted records: they test missing-evidence and cursor boundaries only.
use reservoir_core::{
    actions::{ActionComparisonRecord, ComparisonMode, JournalAction, SaveStatus},
    guided_evidence::{evaluate, unopened, LessonEvidenceState as State, TOLERANCE},
    stage::{LanguageKind, TurnStatus},
};
use std::path::PathBuf;

fn fixture(name: &str) -> ActionComparisonRecord {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../../../essentials/examples/portable")
        .join(name);
    serde_json::from_slice(&std::fs::read(path).unwrap()).unwrap()
}
fn component(stage: usize) -> ActionComparisonRecord {
    fixture(&format!("example-component-{stage}.json"))
}

#[test]
fn canonical_lesson_boundaries_are_verified_and_match_native_claims() {
    let records: Vec<_> = (1..=8).map(component).collect();
    for record in &records {
        record.verify().unwrap();
    }
    let e = |stage: usize, cursor| evaluate(&records[stage - 1], cursor);
    assert!(e(1, 13).observation.contains("quiet"));
    assert!(e(1, 13).observation.contains("lower"));
    assert_eq!(e(2, 1).state, State::NotYetObserved);
    assert_eq!(e(2, 2).evidence_steps, [2]);
    assert!(e(3, 30)
        .observation
        .contains("Reservoir states still match"));
    assert_eq!(e(4, 29).state, State::NotYetObserved);
    assert_eq!(e(4, 30).state, State::Observed);
    assert_eq!(e(5, 30).state, State::NotYetObserved);
    assert_eq!(e(5, 30).evidence_steps, [30]);
    assert_eq!(e(5, 31).evidence_steps, [30, 31]);
    assert!(e(5, 31)
        .observation
        .contains("First state difference: step 31"));
    assert_eq!(e(6, 59).state, State::NotYetObserved);
    assert_eq!(e(6, 60).evidence_steps, [30, 60]);
    assert!(!e(6, 60).observation.contains("submitted model"));
    assert!(!e(7, 89).observation.contains("WAIT was chosen"));
    assert!(e(7, 90).observation.contains("WAIT was chosen"));
    assert!(e(8, 120).observation.contains("retention limit"));
    assert!(e(8, 120).observation.contains("remain matched"));
}

#[test]
fn unopened_zero_empty_and_post_record_cursors_have_no_fabricated_frame() {
    let mut record = component(1);
    assert_eq!(evaluate(&record, 0), unopened());
    assert_eq!(
        evaluate(&record, usize::MAX),
        evaluate(&record, record.right.frames.last().unwrap().step)
    );
    record.right.frames.clear();
    assert_eq!(evaluate(&record, 100), unopened());
    let json = serde_json::to_value(unopened()).unwrap();
    assert_eq!(
        json,
        serde_json::json!({"state":"Not reached yet","observation":"Open an example to inspect recorded evidence.","evidenceSteps":[]})
    );
}

#[test]
fn every_canonical_cursor_equals_its_retained_prefix_and_rewinds() {
    let mut names: Vec<_> = (1..=8)
        .map(|s| format!("example-component-{s}.json"))
        .collect();
    names.extend((4..=8).map(|s| format!("example-model-{s}.json")));
    names.extend(
        [
            "example-observation-scripted.json",
            "example-model-observation-active.json",
        ]
        .map(str::to_string),
    );
    for name in names {
        let full = fixture(&name);
        let end = full.right.frames.last().map_or(0, |f| f.step);
        for cursor in (0..=end).rev() {
            let expected = evaluate(&full, cursor);
            let mut prefix = full.clone();
            prefix.right.frames.retain(|f| f.step <= cursor);
            prefix.right.actions.retain(|a| a.observed_step <= cursor);
            prefix.right.journals.retain(|j| j.observed_step <= cursor);
            if let Some(left) = &mut prefix.left {
                left.frames.retain(|f| f.step <= cursor);
                left.actions.retain(|a| a.observed_step <= cursor);
                left.journals.retain(|j| j.observed_step <= cursor);
            }
            assert_eq!(
                expected,
                evaluate(&prefix, cursor),
                "{name} cursor {cursor}"
            );
            assert!(expected.evidence_steps.iter().all(|step| *step <= cursor));
        }
    }
}

#[test]
fn future_action_journal_frame_and_application_changes_cannot_leak_backwards() {
    for stage in 1..=8 {
        let mut record = component(stage);
        let cursor = if stage < 4 { 12 } else { 29 };
        let expected = evaluate(&record, cursor);
        for frame in &mut record.right.frames {
            if frame.step > cursor {
                frame.state.fill(99.0);
                frame.external_input.fill(99.0);
                frame.control = None;
            }
        }
        for action in &mut record.right.actions {
            if action.observed_step > cursor {
                action.status = TurnStatus::Failed;
                action.prompt = "future text must stay hidden".into();
                action.application_step = None;
                action.memory_entry_id = None;
            }
        }
        for journal in &mut record.right.journals {
            if journal.observed_step > cursor {
                journal.text = "future journal must stay hidden".into();
            }
        }
        assert_eq!(expected, evaluate(&record, cursor), "stage {stage}");
    }
    let mut returned = component(5);
    let at_save = evaluate(&returned, 30);
    returned.right.actions[0].application_step = Some(600);
    assert_eq!(at_save, evaluate(&returned, 30));
    returned.right.actions[0].application_step = None;
    assert_eq!(at_save, evaluate(&returned, 30));
}

#[test]
fn recurrence_requires_matched_prefix_and_uses_fixed_tolerance() {
    let mut record = component(2);
    record.left = None;
    assert_eq!(evaluate(&record, 30).state, State::NotApplicable);
    let mut record = component(2);
    record.left.as_mut().unwrap().frames.remove(0);
    assert_eq!(evaluate(&record, 30).state, State::NotApplicable);
    let mut record = component(2);
    record.right.frames = record.left.as_ref().unwrap().frames.clone();
    assert_eq!(evaluate(&record, 30).state, State::DifferentResult);
    record.right.frames[1].state = record.right.frames[1]
        .state
        .iter()
        .map(|v| v + TOLERANCE * 0.5)
        .collect();
    assert_eq!(evaluate(&record, 30).state, State::DifferentResult);
    record.right.frames[1].state = record.right.frames[1]
        .state
        .iter()
        .map(|v| v + TOLERANCE * 2.0)
        .collect();
    assert_eq!(evaluate(&record, 30).evidence_steps, [2]);
}

#[test]
fn sensory_measurement_is_required_and_does_not_imply_state_difference() {
    let mut record = component(3);
    record.right.frames[29].spectral = None;
    assert_eq!(evaluate(&record, 30).state, State::Incomplete);
    let mut record = component(3);
    record.left = None;
    assert!(evaluate(&record, 30)
        .observation
        .contains("single recorded arm"));
    let mut record = component(3);
    record.right.frames[0].state[0] += 0.1;
    assert!(evaluate(&record, 30).observation.contains("states differ"));
}

#[test]
fn journal_needs_successful_save_and_distinguishes_single_arm() {
    let mut record = component(4);
    record.right.actions[0].status = TurnStatus::Failed;
    record.right.actions[0]
        .save_receipt
        .as_mut()
        .unwrap()
        .status = SaveStatus::Failed;
    let result = evaluate(&record, 30);
    assert_eq!(result.state, State::Incomplete);
    assert!(result.observation.contains("journal save failed"));
    record.right.actions[0].save_receipt = None;
    record.right.actions[0].status = TurnStatus::Cancelled;
    assert!(evaluate(&record, 30).observation.contains("cancelled"));
    let single = fixture("example-model-4.json");
    single.verify().unwrap();
    assert!(evaluate(&single, 30).observation.contains("no control arm"));
}

#[test]
fn return_requires_matching_reached_application_frame() {
    let mut record = component(5);
    record.right.frames[30].semantic_action_id = None;
    assert_eq!(evaluate(&record, 31).state, State::Incomplete);
    assert_eq!(evaluate(&record, 31).evidence_steps, [31]);
    record.right.actions[0].semantic_vector = None;
    assert_eq!(evaluate(&record, 31).state, State::Incomplete);
    let mut record = component(5);
    record.left = None;
    assert!(evaluate(&record, 31).observation.contains("no control arm"));
}

#[test]
fn memory_requires_prior_identity_text_and_prompt_inclusion() {
    for mutation in 0..5 {
        let mut record = component(6);
        match mutation {
            0 => record.right.actions[1].memory_text = Some("altered memory".into()),
            1 => record.right.actions[1].memory_entry_id = Some("missing journal".into()),
            2 => record.right.actions[1].prompt = "No retained memory here".into(),
            3 => record.right.journals[0].observed_step = 60,
            _ => record.right.journals[0].observed_step = 61,
        }
        assert_eq!(
            evaluate(&record, 60).state,
            State::Incomplete,
            "mutation {mutation}"
        );
    }
}

#[test]
fn memory_context_distinguishes_prepared_submitted_and_fixed_replies() {
    let mut record = component(6);
    assert!(evaluate(&record, 60)
        .observation
        .contains("prepared/scripted"));
    assert!(evaluate(&record, 60)
        .observation
        .contains("Replies remain fixed"));
    record.specification.language.backend = LanguageKind::Ollama;
    record.specification.mode = ComparisonMode::IndependentGeneration;
    record.right.actions[1].request_started = false;
    assert!(evaluate(&record, 60)
        .observation
        .contains("prepared, unsubmitted"));
    record.right.actions[1].request_started = true;
    let observation = evaluate(&record, 60).observation;
    assert!(observation.contains("submitted model"));
    assert!(observation.contains("exposure, not improved writing"));
}

#[test]
fn wait_requires_completed_choice_without_journal_or_save_receipt() {
    let mut record = component(7);
    let wait_index = record
        .right
        .actions
        .iter()
        .position(|a| a.chosen_action == Some(JournalAction::Wait))
        .unwrap();
    record.right.actions[wait_index].status = TurnStatus::Failed;
    assert!(!evaluate(&record, 90)
        .observation
        .contains("WAIT was chosen"));
    record.right.actions[wait_index].status = TurnStatus::Completed;
    record.right.actions[wait_index].journal_entry_id = Some("unexpected".into());
    assert_eq!(evaluate(&record, 90).state, State::Incomplete);
    record.right.actions[wait_index].journal_entry_id = None;
    record.right.actions[wait_index].save_receipt = record.right.actions[0].save_receipt.clone();
    assert_eq!(evaluate(&record, 90).state, State::Incomplete);
}

#[test]
fn all_write_model_is_an_observation_not_a_failed_expected_wait() {
    let record = fixture("example-model-7.json");
    record.verify().unwrap();
    let result = evaluate(&record, 90);
    assert_eq!(result.state, State::Observed);
    assert!(result.observation.contains("No WAIT has occurred"));
}

#[test]
fn regulation_requires_all_receipts_and_preserves_bounds_without_benefit_claim() {
    for mutation in 0..3 {
        let mut record = component(8);
        match mutation {
            0 => record.right.frames[119].fill_percent = None,
            1 => record.right.frames[119].retention_used = None,
            _ => record.right.frames[119].control = None,
        }
        assert_eq!(evaluate(&record, 120).state, State::Incomplete);
    }
    let mut record = component(8);
    for bound in [0.82, 0.995] {
        record.right.frames[119]
            .control
            .as_mut()
            .unwrap()
            .applied_retention = bound;
        let result = evaluate(&record, 120);
        assert!(result.observation.contains("retention limit"));
        assert!(!result.observation.contains("target attained"));
    }
    record.right.frames[119]
        .control
        .as_mut()
        .unwrap()
        .applied_retention = 0.95;
    assert!(!evaluate(&record, 120)
        .observation
        .contains("retention limit"));
}

#[test]
fn observation_comparison_requires_both_arms_and_reached_opportunities() {
    let mut record = fixture("example-observation-active-scripted.json");
    record.verify().unwrap();
    assert_eq!(evaluate(&record, 29).state, State::NotYetObserved);
    let result = evaluate(&record, 30);
    assert_eq!(result.state, State::Observed);
    assert!(result
        .observation
        .contains("Different wording is not an improvement score"));
    record.left.as_mut().unwrap().actions[0].status = TurnStatus::Cancelled;
    assert_eq!(evaluate(&record, 30).state, State::Incomplete);
    assert!(evaluate(&record, 30)
        .observation
        .contains("sensory arm cancelled"));
    record.left = None;
    assert_eq!(evaluate(&record, 30).state, State::Incomplete);
}
