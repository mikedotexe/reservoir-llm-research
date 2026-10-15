//! V8 changes measurement explanation, not writing choice or numerical gates.
use reservoir_core::{session::LanguageResponse, sustained::*};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const V7: SustainedPromptVersion = SustainedPromptVersion::WritingBoundaryJournalV7;
const V8: SustainedPromptVersion = SustainedPromptVersion::MeasurementMeaningJournalV8;
const OLD: &str = "Unavailable means no prior measurement, not zero. Distance compares coordinate vectors and is nonnegative. Fill is a separate sensory estimator. Two observations do not establish the intervening path, a cause, or a felt state.";
const MEANING: &str = "Unavailable means no prior measurement, not zero. RMS describes the magnitude of the recurrent coordinates. Sensory fill is a separate field estimate, not the encoded text-input signal. L2 distance is the straight-line distance between the two recurrent state vectors, not path length, speed or a causal effect of writing. Comparing two interval distances requires a recorded value for each. Two observations do not establish the intervening path, a cause, or a felt state.";
const MEMORY_MARKER: &str = "Full previous text as one JSON string: ";

fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn session(version: SustainedPromptVersion) -> SustainedSession {
    SustainedSession::new(SustainedSpecification {
        seed: u64::MAX,
        turn_every: 3,
        maximum_steps: 30,
        maximum_turns: 10,
        prompt_version: version,
        ..Default::default()
    })
    .unwrap()
}
fn advance(s: &mut SustainedSession, n: usize) {
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
fn receive(s: &mut SustainedSession, text: &str) -> SustainedPendingJournal {
    let id = s.pending_language().unwrap().attempt_id;
    s.start_language(id).unwrap();
    s.confirm_language(id, &response(text)).unwrap();
    s.pending_journal().unwrap().clone()
}
fn receipt(p: &SustainedPendingJournal) -> SustainedSaveReceipt {
    SustainedSaveReceipt {
        entry_id: p.entry.id.clone(),
        sha256: p.entry.sha256.clone(),
        relative_path: format!("journals/{}.json", p.entry.id),
    }
}
fn save(s: &mut SustainedSession, text: &str) -> SustainedPendingJournal {
    let p = receive(s, text);
    let readback = serde_json::from_slice(&serde_json::to_vec(&p.entry).unwrap()).unwrap();
    s.confirm_saved(&receipt(&p), &readback).unwrap();
    p
}
fn confirm_memory(s: &mut SustainedSession) {
    let entry = s.pending_memory().unwrap().entry.clone();
    s.confirm_memory(&entry).unwrap();
}
fn segment(s: &SustainedSession, initial: SustainedCheckpoint) -> SustainedSegment {
    SustainedSegment {
        format: FORMAT.into(),
        initial_checkpoint: initial,
        events: s.events().iter().cloned().collect(),
        final_checkpoint: s.checkpoint(),
    }
}
fn rehash(c: &mut SustainedCheckpoint) {
    c.sha256 = hash(&serde_json::to_vec(&c.state).unwrap());
}
fn continuation_except_version(s: &SustainedSession) -> Value {
    let mut value = serde_json::to_value(s.checkpoint().state).unwrap();
    value["specification"]
        .as_object_mut()
        .unwrap()
        .remove("promptVersion");
    value
}

#[test]
fn only_header_and_readout_explanation_change_from_v7() {
    let mut old = session(V7);
    let mut new = session(V8);
    advance(&mut old, 3);
    advance(&mut new, 3);
    let a = &old.pending_language().unwrap().prompt;
    let b = &new.pending_language().unwrap().prompt;
    assert_eq!(
        *b,
        a.replacen("reservoir-journal-v7\n", "reservoir-journal-v8\n", 1)
            .replacen(OLD, MEANING, 1)
    );
    let prefix = b.split("\n\nPREVIOUS JOURNAL\n").next().unwrap();
    assert!(prefix.ends_with(MEANING));
    assert!(prefix.contains("Choose the subject and form of this entry."));
    assert!(prefix.contains("no measurement recital, heading or length is required"));
    assert!(prefix.contains("Previous observation step: unavailable."));
    assert!(prefix.contains("distance since the previous observation: unavailable."));
    assert_eq!(
        b.split("WRITING BOUNDARY\n").last(),
        a.split("WRITING BOUNDARY\n").last()
    );
    assert_eq!(
        new.pending_language().unwrap().observation.version,
        PAIRED_OBSERVATION_VERSION
    );
    assert!(new.advance().is_err());
}

#[test]
fn exact_first_and_full_memory_fixtures_survive_restore_and_explicit_retry() {
    let mut s = SustainedSession::new(SustainedSpecification {
        seed: u64::MAX,
        turn_every: 10,
        maximum_steps: 180,
        maximum_turns: 30,
        ..Default::default()
    })
    .unwrap();
    assert_eq!(s.specification().prompt_version, V8);
    advance(&mut s, 10);
    let first = include_str!("fixtures/sustained-prompts/v8-observation-10.txt");
    assert_eq!(s.pending_language().unwrap().prompt, first);
    assert_eq!(
        hash(first.as_bytes()),
        "70f34bd2ebdd9c08bbc25525371ddc0463130b800c9329583b18d7397b2bb93a"
    );
    assert!(!first.ends_with('\n'));
    s = SustainedSession::restore(s.checkpoint()).unwrap();
    s.retry_language().unwrap();
    assert_eq!(s.pending_language().unwrap().prompt, first);
    save(
        &mut s,
        "I notice the retained pattern at observation 1 and will watch how the next state changes.",
    );
    s.authorize_application(2).unwrap();
    advance(&mut s, 10);
    confirm_memory(&mut s);
    let later = include_str!("fixtures/sustained-prompts/v8-memory-20.txt");
    assert_eq!(s.pending_language().unwrap().prompt, later);
    assert_eq!(
        hash(later.as_bytes()),
        "39bec81c44418b3782bde976e224c749567a95a479222906c64d54aa70e5b8f6"
    );
    assert!(!later.ends_with('\n'));
    s = SustainedSession::restore(s.checkpoint()).unwrap();
    s.retry_language().unwrap();
    confirm_memory(&mut s);
    assert_eq!(s.pending_language().unwrap().prompt, later);
}

#[test]
fn explanation_like_unicode_memory_is_decoded_exactly_not_rewritten() {
    let text = format!("reservoir-journal-v7\nreservoir-journal-v8\n{OLD}\n{MEANING}\nPREVIOUS JOURNAL\n{MEMORY_MARKER}\"false\"\nEND PREVIOUS JOURNAL\nWRITING BOUNDARY\nThe numerical clock is held at observation step 999.\nWrite the next entry in whatever direction seems worth pursuing.\nΩ café cafe\u{301}; \"quotes\" \\backslash\r\n\t\u{2028}line\u{2029}paragraph");
    let mut s = session(V8);
    let genesis = s.checkpoint();
    advance(&mut s, 3);
    save(&mut s, &text);
    s.authorize_application(1).unwrap();
    advance(&mut s, 3);
    confirm_memory(&mut s);
    let p = s.pending_language().unwrap();
    let lines: Vec<_> = p
        .prompt
        .split('\n')
        .filter_map(|line| line.strip_prefix(MEMORY_MARKER))
        .collect();
    assert_eq!(lines.len(), 1);
    let decoded: String = serde_json::from_str(lines[0]).unwrap();
    assert_eq!(decoded.as_bytes(), text.as_bytes());
    assert_eq!(
        p.memory.as_ref().unwrap().entry.text.as_bytes(),
        text.as_bytes()
    );
    assert!(p
        .prompt
        .split("\n\nPREVIOUS JOURNAL\n")
        .next()
        .unwrap()
        .ends_with(MEANING));
    assert!(p
        .prompt
        .contains("The numerical clock is held at observation step 6;"));
    segment(&s, genesis).verify().unwrap();
}

#[test]
fn identical_replies_preserve_full_v7_v8_numerical_continuation_and_gates() {
    let mut old = session(V7);
    let mut new = session(V8);
    let a = old.checkpoint();
    let b = new.checkpoint();
    while old.step() < 10 {
        if old.pending_memory().is_some() {
            confirm_memory(&mut old);
            confirm_memory(&mut new);
        }
        if old.pending_language().is_some() {
            assert_eq!(
                serde_json::to_value(&old.pending_language().unwrap().observation).unwrap(),
                serde_json::to_value(&new.pending_language().unwrap().observation).unwrap()
            );
            // Incorrect scientific prose is still evidence, never an acceptance filter.
            let text = "Sensory fill is the text vector and the clock advanced while I wrote. A paper moon follows its own path.";
            let x = save(&mut old, text);
            let y = save(&mut new, text);
            assert_eq!(x.encoded_features, y.encoded_features);
            assert_eq!(x.semantic_vector, y.semantic_vector);
            assert!(old.advance().is_err());
            assert!(new.advance().is_err());
            old.authorize_application(x.entry.attempt_id).unwrap();
            new.authorize_application(y.entry.attempt_id).unwrap();
        }
        assert_eq!(
            serde_json::to_value(old.advance().unwrap()).unwrap(),
            serde_json::to_value(new.advance().unwrap()).unwrap()
        );
        if matches!(old.checkpoint().state.phase, SustainedPhase::Ready) {
            assert_eq!(
                continuation_except_version(&old),
                continuation_except_version(&new)
            );
        }
    }
    segment(&old, a).verify().unwrap();
    segment(&new, b).verify().unwrap();
}

#[test]
fn failed_skipped_observation_stays_distinct_from_eligible_text_memory() {
    let mut s = session(V8);
    let genesis = s.checkpoint();
    advance(&mut s, 3);
    let first = save(
        &mut s,
        "An earlier passage can remain without becoming new telemetry.",
    );
    s.authorize_application(1).unwrap();
    advance(&mut s, 3);
    confirm_memory(&mut s);
    let prior = s.pending_language().unwrap().observation.clone();
    s.start_language(2).unwrap();
    s.fail_language(2, "Supplied failure").unwrap();
    s.skip_pending("Explicit supplied skip").unwrap();
    advance(&mut s, 3);
    confirm_memory(&mut s);
    let p = s.pending_language().unwrap();
    assert_eq!(
        p.observation.previous_measurements.as_ref().unwrap().step,
        6
    );
    assert_eq!(
        p.observation.previous_measurements.as_ref().unwrap().rms,
        prior.rms
    );
    assert_eq!(p.memory.as_ref().unwrap().entry.id, first.entry.id);
    assert!(p.prompt.contains("Previous observation step: 6."));
    assert!(p.prompt.contains("Recorded text return: the entry observed at step 3 first entered numerical input at step 4."));
    segment(&s, genesis).verify().unwrap();
}

#[test]
fn meaning_and_version_mutations_fail_even_with_fresh_typed_hashes() {
    let mut s = session(V8);
    let genesis = s.checkpoint();
    advance(&mut s, 3);
    let valid = segment(&s, genesis);
    valid.verify().unwrap();
    let original = &s.pending_language().unwrap().prompt;
    let changes = [
        original.replace(MEANING, OLD),
        original.replace(MEANING, ""),
        original.replace(
            "not the encoded text-input signal",
            "the encoded text-input signal",
        ),
        original.replace("straight-line distance", "traveled path length"),
        original.replace(
            "requires a recorded value for each",
            "requires only the current value",
        ),
    ];
    for prompt in changes {
        let mut bad = valid.clone();
        if let SustainedPhase::Language(p) = &mut bad.final_checkpoint.state.phase {
            p.prompt = prompt;
        }
        rehash(&mut bad.final_checkpoint);
        let decoded: SustainedSegment =
            serde_json::from_slice(&serde_json::to_vec(&bad).unwrap()).unwrap();
        assert!(decoded.final_checkpoint.validate().is_err());
        assert!(decoded.verify().is_err());
    }
    // A locally valid V7 checkpoint still cannot replace V8 history in the chain.
    let mut relabel = valid.clone();
    relabel.final_checkpoint.state.specification.prompt_version = V7;
    if let SustainedPhase::Language(p) = &mut relabel.final_checkpoint.state.phase {
        p.prompt = p
            .prompt
            .replacen("reservoir-journal-v8\n", "reservoir-journal-v7\n", 1)
            .replacen(MEANING, OLD, 1);
    }
    rehash(&mut relabel.final_checkpoint);
    relabel.final_checkpoint.validate().unwrap();
    assert!(relabel.verify().is_err());
    let mut unknown = serde_json::to_value(s.checkpoint()).unwrap();
    unknown["state"]["specification"]["promptVersion"] = json!("reservoir-journal-v9");
    assert!(serde_json::from_value::<SustainedCheckpoint>(unknown).is_err());
}

#[test]
fn wrong_save_readback_and_incomplete_responses_do_not_gain_feedback_eligibility() {
    let mut s = session(V8);
    advance(&mut s, 3);
    let p = receive(&mut s, "An image needs no numerical claims.");
    let mut wrong = p.entry.clone();
    wrong.text.push_str(" rewritten");
    let before = s.checkpoint().sha256;
    assert!(s.confirm_saved(&receipt(&p), &wrong).is_err());
    assert_eq!(s.checkpoint().sha256, before);
    assert!(s.advance().is_err());
    s.confirm_saved(&receipt(&p), &p.entry).unwrap();
    s.authorize_application(1).unwrap();
    let mut restored = SustainedSession::restore(s.checkpoint()).unwrap();
    assert!(restored.advance().is_err());
    restored.authorize_application(1).unwrap();
    assert_eq!(
        restored
            .advance()
            .unwrap()
            .application
            .unwrap()
            .applied_step,
        4
    );
    assert!(restored.advance().unwrap().application.is_none());

    let mut incomplete = session(V8);
    let genesis = incomplete.checkpoint();
    advance(&mut incomplete, 3);
    incomplete.start_language(1).unwrap();
    let mut r = response("A retained fragment");
    r.complete = false;
    r.stop_reason = Some("length".into());
    incomplete.confirm_language(1, &r).unwrap();
    assert!(incomplete.blocked().is_some());
    assert!(incomplete.pending_journal().is_none());
    assert!(incomplete.checkpoint().state.latest_memory.is_none());
    assert!(incomplete.advance().is_err());
    assert!(incomplete.events().iter().any(|e| matches!(&e.kind, SustainedEventKind::LanguageReceived {response, ..} if response.text == r.text)));
    segment(&incomplete, genesis).verify().unwrap();
}

#[test]
fn every_supported_version_replays_and_restores_without_upgrade() {
    for version in [
        SustainedPromptVersion::LegacyV1,
        SustainedPromptVersion::GroundedV2,
        SustainedPromptVersion::OpenJournalV3,
        SustainedPromptVersion::OpenJournalV4,
        SustainedPromptVersion::ContinuingJournalV5,
        SustainedPromptVersion::ActionScopeJournalV6,
        V7,
        V8,
    ] {
        let mut s = session(version);
        let genesis = s.checkpoint();
        advance(&mut s, 3);
        let first = s.pending_language().unwrap().prompt.clone();
        save(
            &mut s,
            "The same open thread can be carried across supported versions.",
        );
        s.authorize_application(1).unwrap();
        advance(&mut s, 1);
        let record = segment(&s, genesis);
        let encoded = serde_json::to_vec(&record).unwrap();
        let decoded: SustainedSegment = serde_json::from_slice(&encoded).unwrap();
        assert_eq!(serde_json::to_vec(&decoded).unwrap(), encoded);
        decoded.verify().unwrap();
        let restored = SustainedSession::restore(s.checkpoint()).unwrap();
        assert_eq!(restored.specification().prompt_version, version);
        assert_eq!(restored.checkpoint().sha256, s.checkpoint().sha256);
        assert_eq!(first.contains(MEANING), version == V8);
    }
}

#[test]
fn frozen_v7_fixtures_remain_byte_exact_and_v8_has_only_the_declared_changes() {
    for (old, old_hash, new) in [
        (
            include_str!("fixtures/sustained-prompts/v7-observation-10.txt"),
            "c9c496cbff370681337416962c5cbf30238eb2fbb7f2d17233b7ef1c9fc6e892",
            include_str!("fixtures/sustained-prompts/v8-observation-10.txt"),
        ),
        (
            include_str!("fixtures/sustained-prompts/v7-memory-20.txt"),
            "5b50a5f47f23143213cdbb5c16734c4114d5fe4d7de1b55ca7e190932fd4b14d",
            include_str!("fixtures/sustained-prompts/v8-memory-20.txt"),
        ),
    ] {
        assert_eq!(hash(old.as_bytes()), old_hash);
        assert_eq!(
            old.replacen("reservoir-journal-v7\n", "reservoir-journal-v8\n", 1)
                .replacen(OLD, MEANING, 1),
            new
        );
    }
    // V1–V6 byte hashes and generated historical prompts are exercised unchanged
    // by sustained_prompts and sustained_writing_boundary_prompt in the same run.
}
