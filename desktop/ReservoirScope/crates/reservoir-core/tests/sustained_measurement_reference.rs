use reservoir_core::{session::LanguageResponse, sustained::*};
use sha2::{Digest, Sha256};
fn spec(version: SustainedPromptVersion) -> SustainedSpecification {
    SustainedSpecification {
        seed: u64::MAX,
        turn_every: 3,
        maximum_steps: 30,
        maximum_turns: 10,
        prompt_version: version,
        ..Default::default()
    }
}
fn engine() -> SustainedSession {
    SustainedSession::new(spec(SustainedPromptVersion::OpenJournalV4)).unwrap()
}
fn steps(s: &mut SustainedSession, n: usize) {
    for _ in 0..n {
        s.advance().unwrap();
    }
}
fn response(text: &str) -> LanguageResponse {
    LanguageResponse {
        text: text.into(),
        provider_model: None,
        stop_reason: Some("stop".into()),
        token_count: Some(40),
        complete: true,
        provider_prompt_evaluation: None,
    }
}
fn save(s: &mut SustainedSession, text: &str) -> SustainedPendingJournal {
    let id = s.pending_language().unwrap().attempt_id;
    s.start_language(id).unwrap();
    s.confirm_language(id, &response(text)).unwrap();
    let p = s.pending_journal().unwrap().clone();
    s.confirm_saved(
        &SustainedSaveReceipt {
            entry_id: p.entry.id.clone(),
            sha256: p.entry.sha256.clone(),
            relative_path: format!("journals/{}.json", p.entry.id),
        },
        &p.entry,
    )
    .unwrap();
    p
}
fn memory(s: &mut SustainedSession) {
    let e = s.pending_memory().unwrap().entry.clone().unwrap();
    s.confirm_memory(&e).unwrap();
}
fn rehash(c: &mut SustainedCheckpoint) {
    c.sha256 = format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&c.state).unwrap())
    );
}
fn segment(s: &SustainedSession, initial: SustainedCheckpoint) -> SustainedSegment {
    SustainedSegment {
        format: FORMAT.into(),
        initial_checkpoint: initial,
        events: s.events().iter().cloned().collect(),
        final_checkpoint: s.checkpoint(),
    }
}
#[test]
fn v4_first_reference_has_current_values_and_unavailable_comparison_without_assigning_prose() {
    let mut s = engine();
    steps(&mut s, 3);
    let p = s.pending_language().unwrap();
    assert_eq!(p.observation.version, PAIRED_OBSERVATION_VERSION);
    assert!(p.observation.previous_measurements.is_none());
    assert!(!serde_json::to_value(&p.observation)
        .unwrap()
        .as_object()
        .unwrap()
        .contains_key("previousMeasurements"));
    let r = measurement_reference(&p.observation).unwrap();
    assert_eq!(r.current_step, 3);
    assert_eq!(r.previous_step, None);
    assert!(!r.comparison_available);
    assert_eq!(r.rows.len(), 8);
    assert!(r
        .rows
        .iter()
        .all(|r| r.previous.is_none() && r.delta.is_none()));
    assert_eq!(r.rows[0].current, p.observation.rms);
    assert_eq!(r.rows[2].current, p.observation.sensory.eigenvalues[0]);
    for text in [
        "Choose what draws your attention, the topic and the form.",
        "no metric, step heading, word count or format is required",
        "unavailable, not zero",
        "Creative and subjective prose is welcome",
    ] {
        assert!(p.prompt.contains(text));
    }
    assert!(!p.prompt.contains("Cite the current RMS"));
    assert!(!p.prompt.contains("60–100 words"));
}
#[test]
fn v4_frozen_prompts_retry_and_exact_memory_reproduce() {
    let mut s = SustainedSession::new(SustainedSpecification {
        seed: u64::MAX,
        turn_every: 10,
        maximum_steps: 180,
        maximum_turns: 30,
        prompt_version: SustainedPromptVersion::OpenJournalV4,
        ..Default::default()
    })
    .unwrap();
    steps(&mut s, 10);
    let first = include_str!("fixtures/sustained-prompts/v4-observation-10.txt");
    assert_eq!(s.pending_language().unwrap().prompt, first);
    s = SustainedSession::restore(s.checkpoint()).unwrap();
    s.retry_language().unwrap();
    assert_eq!(s.pending_language().unwrap().prompt, first);
    save(
        &mut s,
        "I notice the retained pattern at observation 1 and will watch how the next state changes.",
    );
    s.authorize_application(2).unwrap();
    steps(&mut s, 10);
    memory(&mut s);
    assert_eq!(
        s.pending_language().unwrap().prompt,
        include_str!("fixtures/sustained-prompts/v4-memory-20.txt")
    );
    let o = &s.pending_language().unwrap().observation;
    let r = measurement_reference(o).unwrap();
    let prior = o.previous_measurements.as_ref().unwrap();
    assert_eq!(
        (r.current_step, r.previous_step, r.comparison_available),
        (20, Some(10), true)
    );
    assert_eq!(r.rows[2].previous, Some(prior.leading_sensory_eigenvalue));
    assert_eq!(
        r.rows[2].delta,
        Some(o.sensory.eigenvalues[0] - prior.leading_sensory_eigenvalue)
    );
    assert_eq!(r.rows[5].previous, Some(prior.shoulder_share * 100.0));
    assert_eq!(
        r.rows[5].delta,
        Some(o.sensory.shoulder_share * 100.0 - prior.shoulder_share * 100.0)
    );
    assert_eq!(r.rows[5].unit, "percent");
}
#[test]
fn failed_skipped_observation_remains_the_previous_measurement_but_not_memory() {
    let mut s = engine();
    let genesis = s.checkpoint();
    steps(&mut s, 3);
    let first = save(
        &mut s,
        "A room of rain. The fictional star is 999; no factual test decides whether I may write.",
    );
    s.authorize_application(1).unwrap();
    steps(&mut s, 3);
    memory(&mut s);
    let six = s.pending_language().unwrap().observation.clone();
    s.start_language(2).unwrap();
    s.fail_language(2, "Owned supplied failure").unwrap();
    s.skip_pending("Explicit skip").unwrap();
    steps(&mut s, 3);
    memory(&mut s);
    let p = s.pending_language().unwrap();
    assert_eq!(p.memory.as_ref().unwrap().entry.observed_step, 3);
    assert_eq!(p.memory.as_ref().unwrap().entry.text, first.entry.text);
    let previous = p.observation.previous_measurements.as_ref().unwrap();
    assert_eq!(previous.step, 6);
    assert_eq!(previous.rms, six.rms);
    assert_eq!(
        previous.leading_sensory_eigenvalue,
        six.sensory.eigenvalues[0]
    );
    assert!(p.prompt.contains("Previous observation step 6"));
    assert!(p.prompt.contains("Prior observed step: 3."));
    segment(&s, genesis).verify().unwrap();
    let expected = p.prompt.clone();
    s = SustainedSession::restore(s.checkpoint()).unwrap();
    s.retry_language().unwrap();
    memory(&mut s);
    assert_eq!(s.pending_language().unwrap().prompt, expected);
}
#[test]
fn v4_pair_metadata_prompt_and_version_mutations_are_rejected() {
    let mut s = engine();
    steps(&mut s, 3);
    save(&mut s, "A passing image.");
    s.authorize_application(1).unwrap();
    steps(&mut s, 3);
    memory(&mut s);
    for mutation in 0..5 {
        let mut c = s.checkpoint();
        match mutation {
            0 => {
                c.state
                    .last_observation
                    .as_mut()
                    .unwrap()
                    .previous_measurements = None
            }
            1 => {
                c.state
                    .last_observation
                    .as_mut()
                    .unwrap()
                    .previous_measurements
                    .as_mut()
                    .unwrap()
                    .step = 5
            }
            2 => c.state.last_observation.as_mut().unwrap().version = OBSERVATION_VERSION.into(),
            3 => c.state.specification.prompt_version = SustainedPromptVersion::OpenJournalV3,
            _ => {
                if let SustainedPhase::Language(p) = &mut c.state.phase {
                    p.prompt = p
                        .prompt
                        .replace("Current minus previous", "Previous minus current");
                }
            }
        }
        rehash(&mut c);
        assert!(c.validate().is_err(), "mutation{mutation}");
    }
}
#[test]
fn full_replay_rejects_self_consistent_rehashed_prior_scalars() {
    let mut s = engine();
    let initial = s.checkpoint();
    steps(&mut s, 3);
    save(&mut s, "First supplied image.");
    s.authorize_application(1).unwrap();
    steps(&mut s, 3);
    memory(&mut s);
    save(&mut s, "Second supplied image.");
    s.authorize_application(2).unwrap();
    steps(&mut s, 1);
    let mut record = segment(&s, initial);
    record.verify().unwrap();
    record
        .final_checkpoint
        .state
        .last_observation
        .as_mut()
        .unwrap()
        .previous_measurements
        .as_mut()
        .unwrap()
        .rms = 0.5;
    rehash(&mut record.final_checkpoint);
    record.final_checkpoint.validate().unwrap();
    assert!(record.verify().is_err());
}
#[test]
fn legacy_second_observation_is_not_misreported_as_first_or_as_retained_pair() {
    let mut s = SustainedSession::new(spec(SustainedPromptVersion::OpenJournalV3)).unwrap();
    steps(&mut s, 3);
    save(&mut s, "A prior thread.");
    s.authorize_application(1).unwrap();
    steps(&mut s, 3);
    memory(&mut s);
    let o = &s.pending_language().unwrap().observation;
    let r = measurement_reference(o).unwrap();
    assert_eq!(r.previous_step, Some(3));
    assert!(!r.comparison_available);
    assert!(r
        .rows
        .iter()
        .all(|r| r.previous.is_none() && r.delta.is_none()));
    assert!(!serde_json::to_value(o)
        .unwrap()
        .as_object()
        .unwrap()
        .contains_key("previousMeasurements"));
}
#[test]
fn v4_changes_context_only_not_recurrence_or_save_gate() {
    let mut old = SustainedSession::new(spec(SustainedPromptVersion::OpenJournalV3)).unwrap();
    let mut new = engine();
    for _ in 0..3 {
        steps(&mut old, 3);
        steps(&mut new, 3);
        assert_eq!(
            serde_json::to_vec(old.latest_frame().unwrap()).unwrap(),
            serde_json::to_vec(new.latest_frame().unwrap()).unwrap()
        );
        for s in [&mut old, &mut new] {
            if s.pending_memory().is_some() {
                memory(s);
            }
            let p = save(
                s,
                "No metrics or assigned form. A cloud, a threshold, an unfinished question.",
            );
            assert!(s.advance().is_err());
            s.authorize_application(p.entry.attempt_id).unwrap();
        }
    }
}
