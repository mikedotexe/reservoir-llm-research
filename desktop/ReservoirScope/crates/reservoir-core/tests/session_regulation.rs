use reservoir_core::{math::SplitMix64, regulation::*};

#[test]
fn fixed_session_exposes_only_retained_prefix_and_exports_only_at_600() {
    let spec = RegulationExampleSpecification::default();
    let mut session = RegulationSession::new(spec.clone()).unwrap();
    assert_eq!(session.specification(), &spec);
    assert!(session.frames().is_empty());
    assert!(!session.is_complete());
    assert!(session.completed_record().is_err());
    assert!(session.window_evidence(usize::MAX).is_none());
    let mut projection_rng = SplitMix64::new(98);
    assert_eq!(
        session.projection_weights(),
        (0..2112)
            .map(|_| projection_rng.signed())
            .collect::<Vec<_>>()
    );
    let mut input_rng = SplitMix64::new(42);
    let mut next_retention = 0.955;

    for step in 1..=600 {
        let frame = session.advance().unwrap();
        assert_eq!(frame.step, step);
        assert_eq!(frame.time, step as f64 * spec.dt);
        // Both fields consume this one exact sequence, rather than advancing
        // separate RNGs or silently dropping its last semantic-lane coordinates.
        assert_eq!(
            frame.input,
            (0..66).map(|_| input_rng.signed()).collect::<Vec<_>>()
        );
        assert_eq!(frame.baseline.retention_used, 0.955);
        assert!(frame.baseline.control.is_none());
        assert_eq!(frame.regulated.retention_used, next_retention);
        next_retention = frame.regulated.control.as_ref().unwrap().applied_retention;
        assert_eq!(session.frames().len(), step);
        assert_eq!(
            frame.baseline.spectral.field_vector,
            frame.regulated.spectral.field_vector
        );

        if [1, 300, 301, 450, 599].contains(&step) {
            assert!(!session.is_complete());
            assert!(
                session.completed_record().is_err(),
                "prefix {step} must not become a portable record"
            );
        }
        if step <= 300 {
            assert!(session.window_evidence(usize::MAX).is_none());
        } else {
            let current = session.window_evidence(usize::MAX).unwrap();
            assert_eq!(
                (current.first_step, current.last_step, current.count),
                (301, step, step - 300)
            );
            assert_eq!(current.is_complete, step == 600);
            assert!(session.window_evidence(300).is_none());
            let rewind = session.window_evidence(301).unwrap();
            assert_eq!(
                (rewind.count, rewind.last_step, rewind.is_complete),
                (1, 301, false)
            );
            assert_eq!(
                rewind.baseline_mean_absolute_error,
                (session.frames()[300].baseline.fill_percent - 68.0).abs()
            );
        }
    }
    assert!(session.is_complete());
    let completed = session.completed_record().unwrap();
    completed.verify().unwrap();
    assert_eq!(completed.checked_steps(), 1200);
    assert_eq!(completed.window_evidence(600), session.window_evidence(600));
    assert_eq!(completed.summary.evaluation_count, 300);
    let before = serde_json::to_vec(&completed.frames[599]).unwrap();
    assert!(session.advance().is_err());
    assert_eq!(session.frames().len(), 600);
    assert_eq!(serde_json::to_vec(&session.frames()[599]).unwrap(), before);
    // The explicit snapshot owns its data; a caller editing it cannot alter the
    // live session's retained frames or future completed snapshots.
    let mut edited = completed;
    edited.frames[599].input[0] = 0.0;
    assert_ne!(edited.frames[599].input, session.frames()[599].input);
}

#[test]
fn reading_between_step_chunks_never_advances_or_changes_the_sequence() {
    let mut uninterrupted =
        RegulationSession::new(RegulationExampleSpecification::default()).unwrap();
    let mut chunked = RegulationSession::new(RegulationExampleSpecification::default()).unwrap();
    for _ in 0..34 {
        uninterrupted.advance().unwrap();
    }
    for chunk in [1, 3, 9, 21] {
        for _ in 0..chunk {
            chunked.advance().unwrap();
        }
        let length = chunked.frames().len();
        for cursor in [0, 300, 600, usize::MAX] {
            assert!(chunked.window_evidence(cursor).is_none());
            assert!(chunked.completed_record().is_err());
        }
        assert_eq!(chunked.frames().len(), length);
    }
    assert_eq!(
        serde_json::to_vec(uninterrupted.frames()).unwrap(),
        serde_json::to_vec(chunked.frames()).unwrap()
    );
    assert_eq!(
        serde_json::to_vec(&uninterrupted.advance().unwrap()).unwrap(),
        serde_json::to_vec(&chunked.advance().unwrap()).unwrap()
    );
}

#[test]
fn fresh_creation_rejects_alternate_fixed_recipe_but_preserves_study_notes() {
    for key in [
        "fieldSeed",
        "inputSeed",
        "steps",
        "dt",
        "initialRetention",
        "targetFillPercent",
        "evaluationFirstStep",
        "evaluationLastStep",
    ] {
        let mut value = serde_json::to_value(RegulationExampleSpecification::default()).unwrap();
        value[key] = serde_json::json!(0);
        let spec = serde_json::from_value(value).unwrap();
        assert!(RegulationSession::new(spec).is_err(), "{key}");
    }
    let spec = RegulationExampleSpecification {
        question: "A bounded offline controller comparison".into(),
        ..Default::default()
    };
    let session = RegulationSession::new(spec.clone()).unwrap();
    assert_eq!(session.specification(), &spec);
}
