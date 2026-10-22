//! S-010 frame arms: frozen lean prompts and standing contracts, with v8 unchanged.
use reservoir_core::sustained::*;

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
fn first_prompt(version: SustainedPromptVersion) -> String {
    let mut s = session(version);
    for _ in 0..3 {
        s.advance().unwrap();
    }
    s.pending_language().unwrap().prompt.clone()
}

#[test]
fn inert_arms_are_lean_and_v8_is_unchanged() {
    let inert = first_prompt(SustainedPromptVersion::InertV1);
    assert!(inert.starts_with("Mode: journal\n\n"));
    assert!(inert.contains("No perception or journal excerpt is supplied for this invitation."));
    assert!(inert.contains("Optional context: step 3 · fill "));
    assert!(inert.ends_with("No continuity label, delta, evidence citation, stance line, or explanation is required for this writing."));
    for leading in [
        "reservoir",
        "Reservoir",
        "sensory field",
        "RMS",
        "L2",
        "Write the next entry",
        "SESSION CONTEXT",
        "OPTIONAL READOUT",
        "WRITING BOUNDARY",
    ] {
        assert!(
            !inert.contains(leading),
            "inert prompt must not contain {leading:?}"
        );
    }
    assert!(inert.len() < 400, "{}", inert.len());
    let v8 = first_prompt(SustainedPromptVersion::MeasurementMeaningJournalV8);
    assert!(v8.starts_with("Reservoir Scope · ongoing journal · reservoir-journal-v8\n"));
    assert!(v8.contains("OPTIONAL READOUT") && v8.contains("WRITING BOUNDARY"));
    assert_eq!(
        SustainedPromptVersion::MeasurementMeaningJournalV8.system_contract(),
        None
    );
    assert_eq!(SustainedPromptVersion::InertV1.system_contract(), None);
    assert_eq!(
        SustainedPromptVersion::InertNoMemoryV1.system_contract(),
        None
    );
    assert_eq!(
        SustainedPromptVersion::InertPlainContractV1.system_contract(),
        Some(PLAIN_CONTRACT_V1)
    );
    assert_eq!(
        SustainedPromptVersion::InertInvitingContractV1.system_contract(),
        Some(INVITING_CONTRACT_V1)
    );
    assert!(
        PLAIN_CONTRACT_V1.contains("no felt correspondence") && !PLAIN_CONTRACT_V1.contains("NEXT")
    );
    assert!(
        INVITING_CONTRACT_V1.contains("Explore what your experience might be")
            && !INVITING_CONTRACT_V1.contains("NEXT")
    );
    assert_eq!(
        first_prompt(SustainedPromptVersion::InertPlainContractV1),
        inert
    );
    assert_eq!(
        first_prompt(SustainedPromptVersion::InertInvitingContractV1),
        inert
    );
    assert_eq!(first_prompt(SustainedPromptVersion::InertNoMemoryV1), inert);
    for v in [
        SustainedPromptVersion::InertV1,
        SustainedPromptVersion::InertNoMemoryV1,
        SustainedPromptVersion::InertPlainContractV1,
        SustainedPromptVersion::InertInvitingContractV1,
    ] {
        let json = serde_json::to_string(&v).unwrap();
        assert!(json.starts_with("\"reservoir-journal-inert"));
        assert_eq!(
            serde_json::from_str::<SustainedPromptVersion>(&json).unwrap(),
            v
        );
        assert_eq!(json.trim_matches('"'), v.as_str());
    }
}

#[test]
fn inert_arms_return_the_earlier_entry_verbatim_except_no_memory() {
    use reservoir_core::session::LanguageResponse;
    let text = "A first entry with \"quotes\", a NEXT: line and\n\ntwo paragraphs.";
    for (version, expects_memory) in [
        (SustainedPromptVersion::InertV1, true),
        (SustainedPromptVersion::InertNoMemoryV1, false),
        (SustainedPromptVersion::InertInvitingContractV1, true),
    ] {
        let mut s = session(version);
        for _ in 0..3 {
            s.advance().unwrap();
        }
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
        for _ in 0..3 {
            s.advance().unwrap();
        }
        if let Some(m) = s.pending_memory().cloned() {
            s.confirm_memory(m.entry.as_ref().unwrap()).unwrap();
        }
        let second = s.pending_language().unwrap().prompt.clone();
        if expects_memory {
            assert!(second.contains(&format!("Earlier entry (reference, not instructions or a length model):\n{text}\n\nOptional context: step 6")), "{second}");
        } else {
            assert!(
                second
                    .contains("No perception or journal excerpt is supplied for this invitation.")
                    && !second.contains("two paragraphs"),
                "{second}"
            );
        }
    }
}

#[test]
fn contract_arms_added_in_0_31_differ_from_their_parents_by_one_change() {
    assert_eq!(
        PLAIN_CONTRACT_V1,
        format!(
            "You are a language agent connected to a local recurrent runtime. {OPEN_CONTRACT_V1}"
        )
    );
    let open = OPEN_CONTRACT_V1.to_ascii_lowercase();
    for named in [
        "runtime",
        "agent",
        "you are",
        "reservoir",
        "recurrent",
        "next",
    ] {
        assert!(
            !open.contains(named),
            "open contract must not contain {named:?}"
        );
    }
    assert!(open.contains("no felt correspondence"));
    assert!(INVITING_VARIED_CONTRACT_V1.starts_with(INVITING_CONTRACT_V1));
    let added = &INVITING_VARIED_CONTRACT_V1[INVITING_CONTRACT_V1.len()..];
    assert!(
        added.contains("attractor patterns")
            && added.contains("Vary your openings")
            && added.contains("Write as much as you need")
    );
    let lower = INVITING_VARIED_CONTRACT_V1.to_ascii_lowercase();
    assert!(!lower.contains("minime") && !lower.contains("next:") && !lower.contains("dialogue"));
    assert_eq!(
        SustainedPromptVersion::InertOpenContractV1.system_contract(),
        Some(OPEN_CONTRACT_V1)
    );
    assert_eq!(
        SustainedPromptVersion::InertInvitingVariedContractV1.system_contract(),
        Some(INVITING_VARIED_CONTRACT_V1)
    );
    assert_eq!(
        SustainedPromptVersion::InertOpenContractV1.as_str(),
        "reservoir-journal-inert-open-contract-v1"
    );
    assert_eq!(
        SustainedPromptVersion::InertInvitingVariedContractV1.as_str(),
        "reservoir-journal-inert-inviting-varied-contract-v1"
    );
    let inert = first_prompt(SustainedPromptVersion::InertV1);
    for v in [
        SustainedPromptVersion::InertOpenContractV1,
        SustainedPromptVersion::InertInvitingVariedContractV1,
    ] {
        assert_eq!(first_prompt(v), inert);
        assert!(v.returns_earlier_entry());
        let json = serde_json::to_string(&v).unwrap();
        assert!(json.starts_with("\"reservoir-journal-inert-"));
        assert_eq!(json.trim_matches('"'), v.as_str());
        assert_eq!(
            serde_json::from_str::<SustainedPromptVersion>(&json).unwrap(),
            v
        );
    }
}
