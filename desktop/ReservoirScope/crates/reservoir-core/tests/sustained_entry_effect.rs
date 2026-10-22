//! S-010 idea 3: the entry-effect readout. What an applied entry did to the recurrent
//! state at its application step, computed as a counterfactual against the same step
//! with no held feedback, carried on the application frame and the next observation, and
//! reported in one clause of the inert prompt by the two versions that ask for it.
use reservoir_core::{
    math::{forcing, ReservoirEngine, ReservoirModel},
    session::LanguageResponse,
    sustained::*,
};

fn session(version: SustainedPromptVersion) -> SustainedSession {
    SustainedSession::new(SustainedSpecification {
        seed: 11,
        turn_every: 3,
        maximum_steps: 100,
        maximum_turns: 30,
        prompt_version: version,
        ..Default::default()
    })
    .unwrap()
}
fn advance_to_language(s: &mut SustainedSession) -> Vec<SustainedFrame> {
    let mut frames = Vec::new();
    while s.pending_language().is_none() && s.pending_memory().is_none() {
        frames.push(s.advance().unwrap());
    }
    frames
}
fn write_and_apply(s: &mut SustainedSession, text: &str) {
    let p = s.pending_language().unwrap().clone();
    s.start_language(p.attempt_id).unwrap();
    s.confirm_language(
        p.attempt_id,
        &LanguageResponse {
            text: text.into(),
            provider_model: None,
            stop_reason: Some("stop".into()),
            token_count: Some(20),
            complete: true,
            provider_prompt_evaluation: None,
        },
    )
    .unwrap();
    let j = s.pending_journal().unwrap().clone();
    s.confirm_saved(
        &SustainedSaveReceipt {
            entry_id: j.entry.id.clone(),
            sha256: j.entry.sha256.clone(),
            relative_path: format!("journals/{}.json", j.entry.id),
        },
        &j.entry,
    )
    .unwrap();
    let id = s.prepared_application().unwrap().entry.attempt_id;
    s.authorize_application(id).unwrap();
}
fn next_prompt(s: &mut SustainedSession) -> (String, Vec<SustainedFrame>) {
    let frames = advance_to_language(s);
    if let Some(m) = s.pending_memory().cloned() {
        s.confirm_memory(m.entry.as_ref().unwrap()).unwrap();
    }
    (s.pending_language().unwrap().prompt.clone(), frames)
}

#[test]
fn effect_versions_report_a_counterfactual_shift_from_the_second_entry_on() {
    for version in [
        SustainedPromptVersion::InertEffectV1,
        SustainedPromptVersion::InertPlainContractEffectV1,
    ] {
        let mut s = session(version);
        let first_frames = advance_to_language(&mut s);
        assert!(first_frames.iter().all(|f| f.entry_effect.is_none()));
        let first = s.pending_language().unwrap().clone();
        assert!(first.observation.entry_effect.is_none());
        assert!(
            !first.prompt.contains("previous entry's effect"),
            "{}",
            first.prompt
        );
        assert!(first.prompt.contains("Optional context: step 3 · fill "));

        write_and_apply(
            &mut s,
            "I notice a wide quiet and I wonder what the number means? Perhaps nothing.",
        );
        let (second, frames) = next_prompt(&mut s);
        let application = frames
            .iter()
            .find(|f| f.application.is_some())
            .expect("an application frame");
        let effect = application
            .entry_effect
            .clone()
            .expect("effect on the application frame");
        assert!(effect.shift > 0.0 && effect.shift.is_finite());
        assert_eq!(effect.applied_step, application.step);
        assert_eq!(
            effect.alignment, None,
            "no previous application to align with"
        );
        assert!(frames
            .iter()
            .filter(|f| f.application.is_none())
            .all(|f| f.entry_effect.is_none()));
        let shown = s
            .pending_language()
            .unwrap()
            .observation
            .entry_effect
            .clone()
            .unwrap();
        assert_eq!(shown, effect);
        assert!(
            second.contains(&format!(
                " · previous entry's effect: shift {:.2}",
                effect.shift
            )),
            "{second}"
        );
        assert!(!second.contains("alignment"), "{second}");

        // The counterfactual definition, recomputed from the recorded frame: the same step
        // with the entry's scaled vector minus the same step with no held feedback, from the
        // same prior state and noise draws.
        let prior = frames
            .iter()
            .find(|f| f.step + 1 == application.step)
            .map(|f| f.state.clone())
            .unwrap_or_else(|| first_frames.last().unwrap().state.clone());
        let spec = s.specification().clone();
        let model = ReservoirModel::seeded(spec.seed);
        let mut with = ReservoirEngine::new(model.clone(), spec.leak, Some(prior.clone())).unwrap();
        let mut without = ReservoirEngine::new(model, spec.leak, Some(prior)).unwrap();
        let with_state = with.step(&application.input, &application.noise).unwrap();
        let silent_input = forcing(application.step as usize, spec.dt);
        let without_state = without.step(&silent_input, &application.noise).unwrap();
        let shift: f64 = with_state
            .iter()
            .zip(&without_state)
            .map(|(a, b)| (a - b) * (a - b))
            .sum::<f64>()
            .sqrt();
        assert_eq!(effect.shift, shift);
        assert_eq!(with_state, application.state);

        write_and_apply(
            &mut s,
            "A second entry, shorter, with digits 12 and 34 and no questions.",
        );
        let (third, frames) = next_prompt(&mut s);
        let effect2 = frames
            .iter()
            .find_map(|f| f.entry_effect.clone())
            .expect("second application effect");
        let alignment = effect2
            .alignment
            .expect("alignment with the first application");
        assert!((-1.0..=1.0).contains(&alignment));
        assert!(
            third.contains(&format!(
                " · previous entry's effect: shift {:.2} · alignment with the one before {:+.2}",
                effect2.shift, alignment
            )),
            "{third}"
        );
        if version == SustainedPromptVersion::InertPlainContractEffectV1 {
            assert_eq!(version.system_contract(), Some(PLAIN_CONTRACT_V1));
        } else {
            assert_eq!(version.system_contract(), None);
        }
        assert!(version.reports_entry_effect() && version.returns_earlier_entry());
        let json = serde_json::to_string(&version).unwrap();
        assert_eq!(json.trim_matches('"'), version.as_str());
        assert_eq!(
            serde_json::from_str::<SustainedPromptVersion>(&json).unwrap(),
            version
        );
    }
}

#[test]
fn earlier_versions_carry_no_effect_and_their_prompts_are_unchanged() {
    for version in [
        SustainedPromptVersion::InertV1,
        SustainedPromptVersion::InertPlainContractV1,
        SustainedPromptVersion::MeasurementMeaningJournalV8,
    ] {
        let mut s = session(version);
        advance_to_language(&mut s);
        write_and_apply(&mut s, "An entry that is applied.");
        let (second, frames) = next_prompt(&mut s);
        assert!(frames.iter().all(|f| f.entry_effect.is_none()));
        assert!(s
            .pending_language()
            .unwrap()
            .observation
            .entry_effect
            .is_none());
        assert!(!second.contains("previous entry's effect"));
        assert!(!version.reports_entry_effect());
        let frame_json =
            serde_json::to_string(frames.iter().find(|f| f.application.is_some()).unwrap())
                .unwrap();
        assert!(!frame_json.contains("entryEffect"));
        let checkpoint = serde_json::to_string(&s.checkpoint()).unwrap();
        assert!(!checkpoint.contains("lastEntryEffect"));
    }
    // An inert-effect session's first prompt equals the inert prompt.
    let a = {
        let mut s = session(SustainedPromptVersion::InertEffectV1);
        advance_to_language(&mut s);
        s.pending_language().unwrap().prompt.clone()
    };
    let b = {
        let mut s = session(SustainedPromptVersion::InertV1);
        advance_to_language(&mut s);
        s.pending_language().unwrap().prompt.clone()
    };
    assert_eq!(a, b);
}
