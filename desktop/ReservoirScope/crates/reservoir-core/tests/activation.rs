use reservoir_core::activation::*;
fn record(arm: Arm) -> Record {
    Record::new(Specification {
        arm,
        seed: 42,
        observations: vec!["rain".into(), "quiet".into()],
        steps_between: 10,
        journal_every: 2,
        gain: 0.01,
    })
    .unwrap()
}
fn quiet(r: &mut Record) {
    let request = r.request().unwrap();
    r.append(Event::RequestStarted {
        request: request.clone(),
    })
    .unwrap();
    r.append(Event::QuietReceived {
        request_id: request.id,
        projection: vec![0.2; 32],
        evidence_sha256: "a".repeat(64),
    })
    .unwrap();
}
#[test]
fn numerical_replay_and_arm_snapshot_hold() {
    for arm in [Arm::NoSteering, Arm::DecayingTrace, Arm::Recurrent] {
        let mut r = record(arm);
        quiet(&mut r);
        quiet(&mut r);
        assert_eq!(r.state.step, 20);
        let request = r.request().unwrap();
        let old = r.state.reservoir.clone();
        r.append(Event::RequestStarted { request }).unwrap();
        assert_eq!(old, r.state.reservoir);
        r.verify().unwrap();
        if arm == Arm::NoSteering {
            assert_eq!(r.steering(), vec![0.; 32]);
        }
    }
}
#[test]
fn save_readback_receipt_and_next_step_application_are_distinct() {
    let mut r = record(Arm::Recurrent);
    quiet(&mut r);
    quiet(&mut r);
    let q = r.request().unwrap();
    r.append(Event::RequestStarted { request: q.clone() })
        .unwrap();
    r.append(Event::JournalReceived {
        request_id: q.id,
        text: "An unresolved question.".into(),
        projection: vec![0.1; 32],
        evidence_sha256: "b".repeat(64),
    })
    .unwrap();
    let j = r.state.journals[0].clone();
    assert!(r
        .append(Event::JournalApplied {
            journal_id: j.id.clone()
        })
        .is_err());
    r.append(Event::JournalSaved {
        journal_id: j.id.clone(),
        sha256: j.sha256,
    })
    .unwrap();
    assert_eq!(r.state.step, 20);
    r.append(Event::JournalApplied {
        journal_id: j.id.clone(),
    })
    .unwrap();
    assert_eq!(r.state.step, 21);
    assert!(r
        .append(Event::JournalApplied { journal_id: j.id })
        .is_err());
    assert!(r.complete());
    r.verify().unwrap();
}
#[test]
fn uncertain_and_failed_requests_never_resend_or_forge_wait() {
    let mut r = record(Arm::Recurrent);
    let q = r.request().unwrap();
    r.append(Event::RequestStarted { request: q }).unwrap();
    assert!(r.request().is_err());
    r.append(Event::Failed {
        reason: "cancelled".into(),
    })
    .unwrap();
    assert_eq!(r.next_kind(), "failed");
    r.verify().unwrap();
}
#[test]
fn tampering_and_bad_projection_rejected() {
    let mut r = record(Arm::Recurrent);
    quiet(&mut r);
    r.state.reservoir[0] += 0.01;
    assert!(r.verify().is_err());
    let mut r = record(Arm::Recurrent);
    let q = r.request().unwrap();
    r.append(Event::RequestStarted { request: q.clone() })
        .unwrap();
    assert!(r
        .append(Event::QuietReceived {
            request_id: q.id,
            projection: vec![2.; 32],
            evidence_sha256: "a".repeat(64)
        })
        .is_err());
}
#[test]
fn observations_keep_exact_ten_step_spacing_across_journal_feedback() {
    let mut r = record(Arm::Recurrent);
    r.specification.observations = vec!["signal".into(); 12];
    for index in 1..=12 {
        quiet(&mut r);
        assert_eq!(r.state.step, index * 10);
        if index % 2 == 0 {
            let q = r.request().unwrap();
            r.append(Event::RequestStarted { request: q.clone() })
                .unwrap();
            r.append(Event::JournalReceived {
                request_id: q.id,
                text: format!("entry{index}"),
                projection: vec![0.1; 32],
                evidence_sha256: "b".repeat(64),
            })
            .unwrap();
            let j = r.state.journals.last().unwrap().clone();
            r.append(Event::JournalSaved {
                journal_id: j.id.clone(),
                sha256: j.sha256,
            })
            .unwrap();
            r.append(Event::JournalApplied { journal_id: j.id })
                .unwrap();
            assert_eq!(r.state.step, index * 10 + 1);
        }
    }
    assert_eq!(r.state.step, 121);
    assert_eq!(r.state.journals.len(), 6);
    r.verify().unwrap();
}
