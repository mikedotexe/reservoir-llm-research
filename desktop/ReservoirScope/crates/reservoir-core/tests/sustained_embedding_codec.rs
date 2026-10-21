//! S-010 Part B: the embedding codec option. Surface sessions are unchanged; embedding
//! sessions carry a v3 mechanism identity, require an external projected vector with
//! provenance, record it, and validate it on continuation.
use reservoir_core::{codec, session::LanguageResponse, sustained::*};
use sha2::{Digest, Sha256};

const V3: &str = "essentials32-splitmix64-embedding32-scaled-feedback-field-noise-v3";

fn embedding(seed: u64) -> Vec<f64> {
    (0..768)
        .map(|i| ((i as f64 * 0.37 + seed as f64).sin() * 0.5))
        .collect()
}
fn spec(codec: SustainedCodec) -> SustainedSpecification {
    SustainedSpecification {
        seed: 5,
        turn_every: 3,
        maximum_steps: 100,
        maximum_turns: 30,
        codec,
        ..Default::default()
    }
}
fn embedding_codec() -> SustainedCodec {
    SustainedCodec::Embedding {
        model: "nomic-embed-text".into(),
        projection_seed: 99,
    }
}
fn response(text: &str) -> LanguageResponse {
    LanguageResponse {
        text: text.into(),
        provider_model: None,
        stop_reason: Some("stop".into()),
        token_count: Some(20),
        complete: true,
        provider_prompt_evaluation: None,
    }
}
fn external(vector: Vec<f64>, model: &str, seed: u64) -> ExternalFeedback {
    ExternalFeedback {
        vector,
        provenance: FeedbackProvenance {
            kind: "embedding".into(),
            model: model.into(),
            digest: Some("sha256:abc".into()),
            dimensions: 768,
            embedding_sha256: format!("{:x}", Sha256::digest(b"raw embedding bytes")),
            projection_seed: seed,
        },
    }
}

#[test]
fn projection_is_deterministic_scaled_and_bounded() {
    let a = codec::project_embedding(&embedding(1), 99).unwrap();
    assert_eq!(a, codec::project_embedding(&embedding(1), 99).unwrap());
    assert_eq!(a.len(), 48);
    assert!(a[32..].iter().all(|x| *x == 0.0));
    let rms = (a.iter().take(32).map(|x| x * x).sum::<f64>() / 32.0).sqrt();
    assert!((rms - codec::EMBEDDING_TARGET_RMS).abs() < 1e-9, "{rms}");
    assert!(a.iter().all(|x| x.abs() <= 5.0));
    assert_ne!(a, codec::project_embedding(&embedding(2), 99).unwrap());
    assert_ne!(a, codec::project_embedding(&embedding(1), 100).unwrap());
    let scaled: Vec<f64> = embedding(1).iter().map(|x| x * 3.0).collect();
    let b = codec::project_embedding(&scaled, 99).unwrap();
    assert!(
        a.iter().zip(&b).all(|(x, y)| (x - y).abs() < 1e-9),
        "unit-normalised input"
    );
    assert!(codec::project_embedding(&[], 99).is_err());
    assert!(codec::project_embedding(&[0.0; 16], 99).is_err());
    assert!(codec::project_embedding(&[f64::NAN; 16], 99).is_err());
}

#[test]
fn surface_sessions_are_byte_for_byte_unchanged() {
    let json = serde_json::to_string(&spec(SustainedCodec::Surface)).unwrap();
    assert!(!json.contains("codec"));
    let parsed: SustainedSpecification = serde_json::from_str(&json).unwrap();
    assert_eq!(parsed.codec, SustainedCodec::Surface);
    assert_eq!(
        spec(SustainedCodec::Surface).mechanism(),
        "essentials32-splitmix64-codec48-held-feedback-v1"
    );
    let json = serde_json::to_string(&spec(embedding_codec())).unwrap();
    assert!(json.contains(
        "\"codec\":{\"kind\":\"embedding\",\"model\":\"nomic-embed-text\",\"projectionSeed\":99}"
    ));
    assert_eq!(spec(embedding_codec()).mechanism(), V3);
    assert!(spec(SustainedCodec::Embedding {
        model: " ".into(),
        projection_seed: 1
    })
    .validate()
    .is_err());
    let mut s = SustainedSession::new(spec(SustainedCodec::Surface)).unwrap();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    let p = s.pending_language().unwrap().clone();
    s.start_language(p.attempt_id).unwrap();
    s.confirm_language(
        p.attempt_id,
        &response("A surface entry that is long enough."),
    )
    .unwrap();
    let j = s.pending_journal().unwrap().clone();
    assert!(j.feedback_provenance.is_none());
    assert!(!serde_json::to_string(&j)
        .unwrap()
        .contains("feedbackProvenance"));
    assert_eq!(
        j.encoded_features,
        codec::encode("A surface entry that is long enough.").unwrap()
    );
}

#[test]
fn embedding_sessions_require_matching_external_feedback_and_record_it() {
    let mut s = SustainedSession::new(spec(embedding_codec())).unwrap();
    assert_eq!(
        serde_json::from_slice::<SustainedCheckpoint>(
            &serde_json::to_vec(&s.checkpoint()).unwrap()
        )
        .unwrap()
        .state
        .mechanism,
        V3
    );
    let base = s.checkpoint();
    for _ in 0..3 {
        s.advance().unwrap();
    }
    let p = s.pending_language().unwrap().clone();
    s.start_language(p.attempt_id).unwrap();
    // No external vector: the attempt is retained as blocked, never as feedback.
    s.confirm_language(p.attempt_id, &response("An embedded entry."))
        .unwrap();
    assert!(s.pending_journal().is_none());
    let reason = s.blocked().unwrap().reason.clone();
    assert!(reason.contains("projected embedding"), "{reason}");
    s.retry_language().unwrap();
    let p = s.pending_language().unwrap().clone();
    s.start_language(p.attempt_id).unwrap();
    let vector = codec::project_embedding(&embedding(7), 99).unwrap();
    for bad in [
        external(vector.clone(), "other-model", 99),
        external(vector.clone(), "nomic-embed-text", 98),
        external(vec![0.5; 48], "nomic-embed-text", 99),
        external(
            vector.iter().map(|x| x * 20.0).collect(),
            "nomic-embed-text",
            99,
        ),
    ] {
        let mut probe = s.clone();
        probe
            .confirm_language_with_feedback(
                p.attempt_id,
                &response("An embedded entry."),
                Some(&bad),
            )
            .unwrap();
        assert!(
            probe.pending_journal().is_none(),
            "mismatched provenance must block"
        );
    }
    let good = external(vector.clone(), "nomic-embed-text", 99);
    s.confirm_language_with_feedback(p.attempt_id, &response("An embedded entry."), Some(&good))
        .unwrap();
    let j = s.pending_journal().unwrap().clone();
    assert_eq!(j.encoded_features, vector);
    assert_eq!(j.semantic_vector, vector);
    assert_eq!(
        j.feedback_provenance.as_ref().unwrap().model,
        "nomic-embed-text"
    );
    s.confirm_saved(
        &SustainedSaveReceipt {
            entry_id: j.entry.id.clone(),
            sha256: j.entry.sha256.clone(),
            relative_path: format!("journals/{}.json", j.entry.id),
        },
        &j.entry,
    )
    .unwrap();
    let checkpoint: SustainedCheckpoint =
        serde_json::from_slice(&serde_json::to_vec(&s.checkpoint()).unwrap()).unwrap();
    checkpoint.validate().unwrap();
    let mut altered = checkpoint.clone();
    if let SustainedPhase::Prepared(prepared) = &mut altered.state.phase {
        prepared.semantic_vector[0] += 0.01;
    }
    altered.sha256 = format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&altered.state).unwrap())
    );
    assert!(altered.validate().is_err());
    let id = s.prepared_application().unwrap().entry.attempt_id;
    s.authorize_application(id).unwrap();
    let f = s.advance().unwrap();
    assert!(f.application.is_some());
    assert_eq!(
        f.input[18..],
        vector.iter().map(|x| x * 1.0).collect::<Vec<_>>()[..]
    );
    let segment = SustainedSegment {
        format: FORMAT.into(),
        initial_checkpoint: base,
        events: s.events().iter().cloned().collect(),
        final_checkpoint: serde_json::from_slice(&serde_json::to_vec(&s.checkpoint()).unwrap())
            .unwrap(),
    };
    segment.verify().unwrap();
    let restored = SustainedSession::restore(
        serde_json::from_slice(&serde_json::to_vec(&s.checkpoint()).unwrap()).unwrap(),
    )
    .unwrap();
    assert_eq!(restored.latest_memory().unwrap().entry.id, j.entry.id);
}
