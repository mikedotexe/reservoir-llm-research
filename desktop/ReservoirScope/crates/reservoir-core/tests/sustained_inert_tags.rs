//! S-011 controls: the inert input with no telemetry tag, and with a scrambled tag whose
//! fill number is seeded and unrelated to the field.
use reservoir_core::sustained::*;

fn session(version: SustainedPromptVersion, seed: u64) -> SustainedSession {
    SustainedSession::new(SustainedSpecification {
        seed,
        turn_every: 3,
        maximum_steps: 100,
        maximum_turns: 30,
        prompt_version: version,
        ..Default::default()
    })
    .unwrap()
}
fn first(version: SustainedPromptVersion, seed: u64) -> (String, f64) {
    let mut s = session(version, seed);
    for _ in 0..3 {
        s.advance().unwrap();
    }
    let p = s.pending_language().unwrap().clone();
    (p.prompt, p.observation.sensory.fill_percent)
}

#[test]
fn no_tag_versions_omit_the_context_line_and_keep_the_rest() {
    let (inert, _) = first(SustainedPromptVersion::InertV1, 11);
    let expected: String = inert
        .lines()
        .filter(|l| !l.starts_with("Optional context"))
        .collect::<Vec<_>>()
        .join("\n");
    for v in [
        SustainedPromptVersion::InertNoTagV1,
        SustainedPromptVersion::InertPlainContractNoTagV1,
    ] {
        let (p, _) = first(v, 11);
        assert!(
            !p.contains("Optional context") && !p.contains("fill"),
            "{p}"
        );
        assert_eq!(
            p, expected,
            "the no-tag prompt is the inert prompt minus its tag line"
        );
        assert!(v.returns_earlier_entry() && !v.reports_entry_effect());
        let json = serde_json::to_string(&v).unwrap();
        assert_eq!(json.trim_matches('"'), v.as_str());
        assert_eq!(
            serde_json::from_str::<SustainedPromptVersion>(&json).unwrap(),
            v
        );
    }
    assert_eq!(SustainedPromptVersion::InertNoTagV1.system_contract(), None);
    assert_eq!(
        SustainedPromptVersion::InertPlainContractNoTagV1.system_contract(),
        Some(PLAIN_CONTRACT_V1)
    );
}

#[test]
fn the_scrambled_tag_is_seeded_bounded_and_unrelated_to_the_field() {
    let v = SustainedPromptVersion::InertPlainContractScrambledTagV1;
    assert_eq!(v.system_contract(), Some(PLAIN_CONTRACT_V1));
    let (a, live) = first(v, 11);
    let (b, _) = first(v, 11);
    let (c, _) = first(v, 12);
    assert_eq!(a, b, "deterministic for a seed");
    assert_ne!(a, c, "differs across seeds");
    let shown = scrambled_fill(11, 3);
    assert!((40.0..95.0).contains(&shown));
    assert!(
        a.contains(&format!("Optional context: step 3 · fill {shown:.1}%")),
        "{a}"
    );
    assert!((shown - live).abs() > 0.05, "shown {shown} vs live {live}");
    let values: Vec<f64> = (1..=200).map(|step| scrambled_fill(11, step)).collect();
    assert!(values.iter().all(|x| (40.0..95.0).contains(x)));
    let mean = values.iter().sum::<f64>() / values.len() as f64;
    assert!((55.0..80.0).contains(&mean), "{mean}");
    let json = serde_json::to_string(&v).unwrap();
    assert_eq!(
        json.trim_matches('"'),
        "reservoir-journal-inert-plain-contract-scrambled-tag-v1"
    );
}

#[test]
fn the_two_entry_no_tag_version_is_the_no_tag_frame_around_two_entries() {
    let v = SustainedPromptVersion::InertPlainContractTwoNoTagV1;
    assert_eq!(v.system_contract(), Some(PLAIN_CONTRACT_V1));
    assert!(v.returns_two_entries() && v.returns_earlier_entry() && !v.reports_entry_effect());
    let mut s = SustainedSession::new(SustainedSpecification {
        seed: 11,
        turn_every: 3,
        maximum_steps: 100,
        maximum_turns: 30,
        prompt_version: v,
        memory_policy: SustainedMemoryPolicy::RandomOlder,
        ..Default::default()
    })
    .unwrap();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    let p = s.pending_language().unwrap().clone();
    let (single, _) = first(SustainedPromptVersion::InertPlainContractNoTagV1, 11);
    assert_eq!(
        p.prompt, single,
        "the first turn is the no-tag plain contract's"
    );
    assert!(!p.prompt.contains("Optional context") && !p.prompt.contains("fill"));
    let json = serde_json::to_string(&v).unwrap();
    assert_eq!(
        json.trim_matches('"'),
        "reservoir-journal-inert-plain-contract-two-no-tag-v1"
    );
}
