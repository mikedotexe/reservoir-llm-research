use reservoir_core::{session::LanguageResponse, sustained::*};
use sha2::{Digest, Sha256};

fn base_spec() -> SustainedSpecification {
    SustainedSpecification {
        action_mode: Some(SustainedActionMode::AuthoredV3),
        prompt_version: SustainedPromptVersion::ActionJournalV3,
        turn_every: 3,
        maximum_steps: 1000,
        maximum_turns: 200,
        sensory_noise_amplitude: 0.5,
        feedback_scale: 0.4,
        ..Default::default()
    }
}
fn reply(text: &str) -> LanguageResponse {
    LanguageResponse {
        text: text.into(),
        provider_model: None,
        stop_reason: Some("stop".into()),
        token_count: Some(30),
        complete: true,
        provider_prompt_evaluation: None,
    }
}
fn rehash(c: &mut SustainedCheckpoint) {
    c.sha256 = format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&c.state).unwrap())
    );
}
struct Run {
    session: SustainedSession,
    base: SustainedCheckpoint,
    entries: Vec<SustainedJournal>,
}
impl Run {
    fn new(spec: SustainedSpecification) -> Self {
        let session = SustainedSession::new(spec).unwrap();
        let base = session.checkpoint();
        Self {
            session,
            base,
            entries: Vec::new(),
        }
    }
    fn reach(&mut self) {
        while matches!(self.session.phase(), SustainedPhase::Ready) {
            self.session.advance().unwrap();
        }
        if let Some(m) = self.session.pending_memory().cloned() {
            self.session
                .confirm_memory(
                    m.entry
                        .as_ref()
                        .or_else(|| {
                            self.entries
                                .iter()
                                .find(|e| Some(e.id.as_str()) == m.entry_id())
                        })
                        .expect("saved memory"),
                )
                .unwrap();
        }
    }
    fn save(&mut self, text: &str) -> SustainedPendingJournal {
        self.reach();
        let id = self.session.pending_language().unwrap().attempt_id;
        self.session.start_language(id).unwrap();
        self.session.confirm_language(id, &reply(text)).unwrap();
        let p = self.session.pending_journal().unwrap().clone();
        self.session
            .confirm_saved(
                &SustainedSaveReceipt {
                    entry_id: p.entry.id.clone(),
                    sha256: p.entry.sha256.clone(),
                    relative_path: format!("journals/{}.json", p.entry.id),
                },
                &p.entry,
            )
            .unwrap();
        self.entries.push(p.entry.clone());
        p
    }
    fn apply(&mut self) -> SustainedFrame {
        let id = self
            .session
            .prepared_application()
            .unwrap()
            .entry
            .attempt_id;
        self.session.authorize_application(id).unwrap();
        self.session.advance().unwrap()
    }
    fn turn(&mut self, text: &str) -> SustainedFrame {
        self.save(text);
        self.apply()
    }
    fn verify(&mut self) -> SustainedSegment {
        let segment = SustainedSegment {
            format: FORMAT.into(),
            initial_checkpoint: self.base.clone(),
            events: self.session.events().iter().cloned().collect(),
            final_checkpoint: self.session.checkpoint(),
        };
        segment.verify().unwrap();
        if let Some(e) = segment.events.last() {
            self.session.acknowledge_events(e.id).unwrap();
        }
        self.base = segment.final_checkpoint.clone();
        segment
    }
}
fn distance(a: &[f64], b: &[f64]) -> f64 {
    a.iter()
        .zip(b)
        .map(|(a, b)| (a - b) * (a - b))
        .sum::<f64>()
        .sqrt()
}

fn spec(live: bool) -> SustainedSpecification {
    SustainedSpecification {
        sonar: Some(SustainedSonarConfig {
            version: SustainedSonarVersion::ExperimentsV3,
            allow_live_probe: live,
        }),
        control_feedback: Some(SustainedControlFeedback::DiagnosticV1),
        ..base_spec()
    }
}
fn request() -> SustainedExperimentRequest {
    let mut v = vec![0.; 48];
    v[0] = 1.;
    serde_json::from_value(serde_json::json!({"name":"amplitude-test","question":"Does doubling amplitude double the response?","conditions":[{"label":"current"}],"probe":{"direction":{"kind":"vector","values":v},"amplitudes":[0.001,0.002]},"observe":{"steps":[1,2,4,8,16,32,64],"coordinates":[0,1,31]}})).unwrap()
}
fn command(r: &SustainedExperimentRequest, withhold: bool) -> String {
    format!(
        "A copied test.\nWITHHOLD_RESERVOIR_INPUT={withhold}\nNEXT: EXPERIMENT {}",
        serde_json::to_string(r).unwrap()
    )
}
fn reports(run: &Run) -> Vec<SustainedExperimentReport> {
    run.session
        .checkpoint()
        .state
        .sonar_state
        .unwrap()
        .experiments
}
#[test]
fn direct_impulse_measurement_matches_native_signed_curves_without_mutating_checkpoint() {
    let s = SustainedSession::new(spec(false)).unwrap();
    let cp = s.checkpoint();
    let bytes = serde_json::to_vec(&cp).unwrap();
    let r = experiment_sustained_checkpoint(&cp, request()).unwrap();
    assert_eq!(r, experiment_sustained_checkpoint(&cp, request()).unwrap());
    assert_eq!(bytes, serde_json::to_vec(&cp).unwrap());
    validate_experiment_report(&r).unwrap();
    let baseline = sustained_sonar_continuation(&r.origin, &[0.; 48]).unwrap();
    for row in &r.responses {
        let sign = if row.sign == SustainedSonarSign::Positive {
            1.
        } else {
            -1.
        };
        let vector: Vec<_> = r
            .unit_input
            .iter()
            .map(|v| v * row.amplitude * sign)
            .collect();
        let path = sustained_sonar_continuation(&r.origin, &vector).unwrap();
        for (i, t) in r.request.observe.steps.iter().enumerate() {
            assert_eq!(
                row.response_l2[i],
                distance(&path[t - 1].state, &baseline[t - 1].state)
            );
            for (j, c) in r.request.observe.coordinates.iter().enumerate() {
                assert_eq!(
                    row.coordinates[i][j],
                    path[t - 1].state[*c] - baseline[t - 1].state[*c]
                );
            }
        }
    }
    assert!(r
        .responses
        .iter()
        .filter(|r| r.amplitude == 0.002)
        .all(|r| r.amplitude_scaling_error[0].unwrap() < 0.01));
}
#[test]
fn explicit_degenerate_conditions_zero_amplitude_and_parameter_contrast() {
    let cp = SustainedSession::new(spec(false)).unwrap().checkpoint();
    let mut req = request();
    let mut alt = req.conditions[0].clone();
    alt.label = "without-held-text".into();
    alt.held_input_scale = 0.;
    req.conditions.push(alt);
    let r = experiment_sustained_checkpoint(&cp, req.clone()).unwrap();
    assert_eq!(r.outcome, ExperimentOutcome::NoContrast);
    assert!(r.explanation.contains("identical"));
    assert!(r
        .contrasts
        .iter()
        .flat_map(|r| &r.response_gap_l2)
        .all(|v| *v == 0.));
    req.conditions[1].leak = Some(0.2);
    let r = experiment_sustained_checkpoint(&cp, req.clone()).unwrap();
    assert_eq!(r.outcome, ExperimentOutcome::Measured);
    assert!(r.contrasts[0].response_gap_l2[0] > 1e-6);
    req.probe.amplitudes = vec![0.];
    let r = experiment_sustained_checkpoint(&cp, req).unwrap();
    assert_eq!(r.outcome, ExperimentOutcome::NoExcitation);
    assert!(r.responses.iter().all(|r| r.return_step.is_none()));
}
#[test]
fn train_is_identical_before_second_pulse_and_oscillation_changes_signed_response() {
    let cp = SustainedSession::new(spec(false)).unwrap().checkpoint();
    let mut req = request();
    let a = experiment_sustained_checkpoint(&cp, req.clone()).unwrap();
    req.probe.waveform = ExperimentWaveform::PulseTrain {
        spacing: 3,
        count: 3,
    };
    let train = experiment_sustained_checkpoint(&cp, req.clone()).unwrap();
    assert_eq!(
        &a.responses[0].response_l2[..2],
        &train.responses[0].response_l2[..2]
    );
    assert!(train.responses[0].response_l2[2] > a.responses[0].response_l2[2]);
    assert!(train
        .responses
        .iter()
        .all(|r| r.return_step.is_none_or(|n| n > 7)));
    req.probe.waveform = ExperimentWaveform::Oscillation {
        period: 2,
        duration: 8,
    };
    let osc = experiment_sustained_checkpoint(&cp, req).unwrap();
    assert_eq!(
        a.responses[0].response_l2[0],
        osc.responses[0].response_l2[0]
    );
    assert_ne!(
        a.responses[0].coordinates[1],
        osc.responses[0].coordinates[1]
    );
}
#[test]
fn origin_precedes_this_entries_withhold_result_reaches_next_prompt_and_replays() {
    let mut run = Run::new(spec(true));
    run.turn("A first input.\nNEXT: NONE");
    run.reach();
    let origin = run.session.checkpoint().state;
    assert!(origin.held_vector.iter().any(|v| *v != 0.));
    run.save(&command(&request(), true));
    assert!(reports(&run).is_empty());
    assert!(run.session.advance().is_err());
    let frame = run.apply();
    let r = reports(&run).pop().unwrap();
    assert_eq!(r.origin.step, 6);
    assert_eq!(r.origin.held_vector, origin.held_vector);
    assert_eq!(r.origin.state, origin.reservoir_state);
    assert_eq!(r.origin.rng_state, origin.rng_state.to_string());
    assert_eq!(frame.action_receipt.unwrap().state_delta_l2, 0.);
    assert!(run
        .session
        .checkpoint()
        .state
        .held_vector
        .iter()
        .all(|v| *v == 0.));
    run.verify();
    run.reach();
    let p = &run.session.pending_language().unwrap().prompt;
    assert!(p.contains(&r.id) && p.contains("EXPERIMENT RESULTS") && p.contains("amplitude-test"));
}
#[test]
fn retained_followups_resolve_immutable_references_and_evicted_ids_reject() {
    let mut run = Run::new(spec(false));
    run.turn(&command(&request(), true));
    let first = reports(&run)[0].clone();
    let mut req = request();
    req.follow_up_of = Some(first.id.clone());
    req.origin = ExperimentOrigin::Experiment {
        id: first.id.clone(),
    };
    req.probe.direction = ExperimentDirection::Experiment {
        id: "latest".into(),
    };
    req.probe.amplitudes = vec![0.0015];
    run.turn(&command(&req, false));
    let next = reports(&run).pop().unwrap();
    assert_eq!(next.origin, first.origin);
    assert_eq!(next.unit_input, first.unit_input);
    assert_eq!(next.resolved_references, vec![first.id.clone()]);
    for _ in 0..4 {
        run.turn(&command(&request(), true));
        run.verify();
    }
    assert_eq!(reports(&run).len(), 4);
    let f = run.turn(&command(&req, true));
    assert_eq!(
        f.action_receipt.as_ref().unwrap().status,
        SustainedActionStatus::Rejected
    );
    assert!(f
        .action_receipt
        .unwrap()
        .rejection
        .unwrap()
        .contains("unavailable or evicted"));
    run.verify();
}
#[test]
fn measured_live_impulse_refreshes_forecast_and_requires_authority_and_measured_dose() {
    for live in [false, true] {
        let mut run = Run::new(spec(live));
        run.turn(&command(&request(), false));
        let id = reports(&run)[0].id.clone();
        run.turn("Change current leak.\nNEXT: TUNE leak 0.75");
        let text=format!("Apply a measured impulse.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: PROBE_EXPERIMENT {{\"id\":\"{id}\",\"amplitude\":0.001,\"sign\":\"positive\"}}");
        let f = run.turn(&text);
        let r = f.action_receipt.unwrap();
        let p = r.experiment_probe.unwrap();
        if live {
            assert_eq!(r.status, SustainedActionStatus::Applied);
            assert_eq!(p.forecast_response_l2[0], r.state_delta_l2);
            assert_eq!(p.forecast_origin.unwrap().controls.leak, 0.75);
            assert!(r.state_delta_l2 > 0. && r.state_delta_l2 <= 0.05);
        } else {
            assert_eq!(r.status, SustainedActionStatus::Rejected);
            assert_eq!(r.state_delta_l2, 0.);
        }
        run.verify();
        let f = run.turn(&text.replace("0.001,", "0.003,"));
        assert_eq!(
            f.action_receipt.unwrap().status,
            SustainedActionStatus::Rejected
        );
        run.verify();
    }
}
#[test]
fn malformed_and_legacy_requests_are_not_executed_and_report_tampering_fails() {
    let mut req = request();
    req.observe.steps = vec![65];
    assert!(validate_experiment_request(&req).is_err());
    req = request();
    req.probe.amplitudes = vec![0.001, 0.001];
    assert!(validate_experiment_request(&req).is_err());
    let mut old = spec(false);
    old.sonar.as_mut().unwrap().version = SustainedSonarVersion::CompactScanV2;
    let mut run = Run::new(old);
    let f = run.turn(&command(&request(), true));
    assert_eq!(
        f.action_receipt.unwrap().status,
        SustainedActionStatus::Rejected
    );
    assert!(reports(&run).is_empty());
    run.verify();
    let mut run = Run::new(spec(false));
    run.turn(&command(&request(), true));
    let mut cp = run.session.checkpoint();
    cp.state.sonar_state.as_mut().unwrap().experiments[0].responses[0].response_l2[0] += 0.1;
    rehash(&mut cp);
    assert!(cp.validate().is_err());
    run.verify();
}

#[test]
fn weighted_directions_saved_state_and_boundaries_remain_explicit() {
    let mut run = Run::new(spec(false));
    run.turn("Establish a state.\nNEXT: NONE");
    run.turn(&command(&request(), true));
    let first = reports(&run)[0].clone();
    let mut req = request();
    let mut other = vec![0.; 48];
    other[1] = 1.;
    req.probe.direction = ExperimentDirection::Mixture {
        terms: vec![
            ExperimentDirectionTerm {
                source: ExperimentDirectionSource::Experiment {
                    id: "latest".into(),
                },
                weight: 2.,
            },
            ExperimentDirectionTerm {
                source: ExperimentDirectionSource::Vector { values: other },
                weight: -1.,
            },
        ],
    };
    req.conditions[0].starting_state = ExperimentStartingState::Experiment {
        id: "latest".into(),
    };
    run.turn(&command(&req, true));
    let report = reports(&run).pop().unwrap();
    assert_eq!(report.condition_origins[0].state, first.origin.state);
    assert_eq!(report.condition_origins[0].step, report.origin.step);
    assert_ne!(report.origin.step, first.origin.step);
    assert!((report.unit_input[0] - 2. / 5f64.sqrt()).abs() < 1e-12);
    assert!((report.unit_input[1] + 1. / 5f64.sqrt()).abs() < 1e-12);
    assert!(!serde_json::to_string(&report.request)
        .unwrap()
        .contains("latest"));
    run.verify();
    req.probe.direction = ExperimentDirection::Mixture {
        terms: vec![ExperimentDirectionTerm {
            source: ExperimentDirectionSource::Experiment {
                id: "latest".into(),
            },
            weight: 0.,
        }],
    };
    let f = run.turn(&command(&req, true));
    assert_eq!(
        f.action_receipt.unwrap().status,
        SustainedActionStatus::Rejected
    );
    run.verify();
    req = request();
    req.probe.waveform = ExperimentWaveform::PulseTrain {
        spacing: 64,
        count: 16,
    };
    assert!(validate_experiment_request(&req).is_err());
    req = request();
    req.probe.amplitudes = vec![0., 0.005, 0.01];
    let mut alt = req.conditions[0].clone();
    alt.label = "other".into();
    alt.leak = Some(0.1);
    req.conditions.push(alt);
    let r = experiment_sustained_checkpoint(&run.session.checkpoint(), req).unwrap();
    assert_eq!(r.numerical_steps, 896);
}

#[test]
fn v4_preflight_explains_screenshot_errors_and_example_is_executable() {
    let mut current = spec(true);
    current.sonar.as_mut().unwrap().version = SustainedSonarVersion::ExperimentsV4;
    let good = experiment_command_example();
    let validation = validate_authored_action_text(&current, &good).unwrap();
    assert_eq!(validation["valid"], true, "{validation}");
    let mut value = serde_json::to_value(request()).unwrap();
    value["conditions"][0]["feedbackScale"] = serde_json::json!(0.4);
    value["probe"].as_object_mut().unwrap().remove("amplitudes");
    value["probe"]["observe"] = value["observe"].take();
    let bad = format!("INQUIRY: OPEN dynamics {{\"question\"}}\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: EXPERIMENT {value}");
    let result = validate_authored_action_text(&current, &bad).unwrap();
    assert_eq!(result["valid"], false);
    let issues = result["issues"].as_array().unwrap();
    for expected in [
        "INQUIRY",
        "NEXT.experiment.conditions[0].feedbackScale",
        "NEXT.experiment.probe.amplitudes",
        "NEXT.experiment.probe.observe",
    ] {
        assert!(
            issues.iter().any(|i| i["path"] == expected),
            "missing {expected}: {result}"
        );
    }
    let malformed =
        validate_authored_action_text(&current, "NEXT: EXPERIMENT {\"name\":\"unfinished\"")
            .unwrap();
    assert!(malformed.to_string().contains("complete JSON object"));
    let mut run = Run::new(current);
    let pending = run.save(&bad);
    assert_eq!(pending.entry.text, bad);
    assert!(pending.action.unwrap().request.is_none());
    run.apply();
    run.verify();
    run.turn(&good);
    assert_eq!(reports(&run).last().unwrap().version, "parameterized-v2");
    run.verify();
    // Historical v3 continues to emit its original serde rejection, without new guidance.
    let historical = validate_authored_action_text(&spec(true), &bad).unwrap();
    assert!(historical["decision"]["rejection"]
        .as_str()
        .unwrap()
        .contains("unknown field `feedbackScale`"));
    let mut old = Run::new(spec(true));
    old.reach();
    let prompt = &old.session.pending_language().unwrap().prompt;
    assert!(prompt.contains("PARAMETERIZED EXPERIMENTS parameterized-v1"));
    assert!(!prompt.contains("EXPERIMENT COMMAND EXAMPLE"));
}

#[test]
fn v4_growth_resets_old_references_and_replays_copied_experiments_and_live_probe() {
    let mut current = spec(true);
    current.sonar.as_mut().unwrap().version = SustainedSonarVersion::ExperimentsV4;
    let mut run = Run::new(current);
    run.turn(&command(&request(), true));
    let old_id = reports(&run)[0].id.clone();
    run.verify();
    let before = run.session.checkpoint();
    let mut enlarged = run.session.specification().clone();
    enlarged.reservoir_nodes = 48;
    run.session
        .reconfigure(ConfigurationChange {
            version: 1,
            operation_id: "grow-experiments".into(),
            expected_revision: 0,
            predecessor_sha256: before.sha256.clone(),
            specification: enlarged,
            host_configuration: serde_json::json!({}),
            elapsed_millis: 1000,
        })
        .unwrap();
    let grown = run.session.checkpoint();
    assert_eq!(
        grown.state.reservoir_state[..32],
        before.state.reservoir_state
    );
    assert!(grown.state.reservoir_state[32..].iter().all(|x| *x == 0.));
    assert!(reports(&run).is_empty());
    run.verify();
    let rejected = run.turn(&format!("WITHHOLD_RESERVOIR_INPUT=true\nNEXT: PROBE_EXPERIMENT {{\"id\":\"{old_id}\",\"amplitude\":0.001,\"sign\":\"positive\"}}"));
    assert_eq!(
        rejected.action_receipt.unwrap().status,
        SustainedActionStatus::Rejected
    );
    run.verify();
    let mut requested = request();
    requested.observe.coordinates = vec![0, 31, 47];
    run.turn(&command(&requested, true));
    let report = reports(&run).pop().unwrap();
    assert_eq!(report.origin.state.len(), 48);
    assert_eq!(report.version, "parameterized-v2");
    validate_experiment_report(&report).unwrap();
    let baseline = sustained_sonar_continuation(&report.origin, &[0.; 48]).unwrap();
    let impulse: Vec<_> = report.unit_input.iter().map(|v| v * 0.001).collect();
    let stimulated = sustained_sonar_continuation(&report.origin, &impulse).unwrap();
    for (i, step) in report.request.observe.steps.iter().enumerate() {
        assert_eq!(
            report.responses[0].response_l2[i],
            distance(&baseline[step - 1].state, &stimulated[step - 1].state)
        );
    }
    run.verify();
    let applied = run.turn(&format!("WITHHOLD_RESERVOIR_INPUT=true\nNEXT: PROBE_EXPERIMENT {{\"id\":\"{}\",\"amplitude\":0.001,\"sign\":\"positive\"}}",report.id));
    assert_eq!(
        applied.action_receipt.as_ref().unwrap().status,
        SustainedActionStatus::Applied
    );
    if let Ok(folder) = std::env::var("GROWTH_EXPERIMENT_FIXTURE_OUT") {
        std::fs::create_dir_all(&folder).unwrap();
        std::fs::write(
            std::path::Path::new(&folder).join("experiment-growth.json"),
            serde_json::to_vec_pretty(
                &serde_json::json!({"report":report,"receipt":applied.action_receipt}),
            )
            .unwrap(),
        )
        .unwrap();
    }
    run.verify();
    SustainedSession::restore(run.session.checkpoint()).unwrap();
}

#[test]
fn historical_experiments_require_explicit_contract_change_for_growth() {
    let mut old = spec(false);
    old.reservoir_nodes = 48;
    assert!(SustainedSession::new(old.clone()).is_err());
    old.sonar.as_mut().unwrap().version = SustainedSonarVersion::ExperimentsV4;
    for nodes in [32, 48, 64, 128] {
        old.reservoir_nodes = nodes;
        let cp = SustainedSession::new(old.clone()).unwrap().checkpoint();
        let mut req = request();
        req.observe.coordinates = vec![nodes - 1];
        let report = experiment_sustained_checkpoint(&cp, req.clone()).unwrap();
        validate_experiment_report(&report).unwrap();
        assert_eq!(report.origin.state.len(), nodes);
        req.observe.coordinates = vec![nodes];
        assert!(experiment_sustained_checkpoint(&cp, req).is_err());
    }
}
