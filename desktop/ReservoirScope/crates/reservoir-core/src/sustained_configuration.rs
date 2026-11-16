//! Explicit operator phase transitions. Old checkpoints omit every new field.
use super::*;

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ConfigurationPhase {
    pub revision: u64,
    pub step: u64,
    pub cadence_origin_step: u64,
    pub turn_cursor: u64,
    pub rng_state: u64,
    pub schedule_origin_millis: u64,
    pub operation_id: String,
    pub invalidated: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ConfigurationChange {
    pub version: u32,
    pub operation_id: String,
    pub expected_revision: u64,
    pub predecessor_sha256: String,
    pub specification: SustainedSpecification,
    /// Exact host configuration is replayed as evidence; its schema is checked by the host.
    pub host_configuration: serde_json::Value,
    pub elapsed_millis: u64,
}

pub(super) fn validate_phase(s: &SustainedContinuation) -> Result<()> {
    if let Some(p) = &s.configuration_phase {
        ensure(
            p.revision > 0
                && p.revision <= 256
                && p.cadence_origin_step <= p.step
                && p.step <= s.step
                && p.turn_cursor <= s.turn_cursor
                && !p.operation_id.is_empty()
                && p.operation_id.len() <= 128
                && p.invalidated.len() <= 16,
            "Invalid configuration phase",
        )?;
    }
    Ok(())
}

impl SustainedSession {
    pub fn configuration_revision(&self) -> u64 {
        self.state
            .configuration_phase
            .as_ref()
            .map_or(0, |p| p.revision)
    }
    pub fn configuration_ready(&self) -> bool {
        matches!(self.state.phase, SustainedPhase::Ready)
    }
    pub fn configuration_boundary(&self) -> bool {
        self.configuration_ready() && self.events.is_empty()
    }
    pub fn schedule_elapsed(&self, elapsed: u64) -> u64 {
        elapsed.saturating_sub(
            self.state
                .configuration_phase
                .as_ref()
                .map_or(0, |p| p.schedule_origin_millis),
        )
    }
    pub fn reconfigure(&mut self, change: ConfigurationChange) -> Result<()> {
        self.room()?;
        ensure(
            matches!(self.state.phase, SustainedPhase::Ready),
            "Finish the admitted turn before changing configuration",
        )?;
        ensure(
            change.version == 1
                && !change.operation_id.is_empty()
                && change.operation_id.len() <= 128
                && change.expected_revision == self.configuration_revision()
                && change.expected_revision < 256
                && change.predecessor_sha256 == self.checkpoint().sha256,
            "Configuration transition identity or predecessor differs",
        )?;
        let spec = &change.specification;
        spec.validate()?;
        let old = &self.state.specification;
        ensure(
            spec.seed == old.seed && spec.dt == old.dt,
            "Seed and numerical dimensions require a fresh run",
        )?;
        ensure(
            spec.maximum_steps >= self.state.step
                && spec.maximum_turns >= self.state.attempt_cursor,
            "Configuration budgets are below consumed resources",
        )?;
        let mut next = self.state.clone();
        let mut invalidated = Vec::new();
        let resized = spec.reservoir_nodes != old.reservoir_nodes;
        ensure(
            spec.reservoir_nodes >= old.reservoir_nodes,
            "Resizing preserves existing nodes; shrinking requires a new linked run",
        )?;
        if resized {
            next.reservoir_state.resize(spec.reservoir_nodes, 0.0);
            invalidated.push("reservoir-dimensions-and-derived-context".into());
        }
        let contract = spec.action_mode != old.action_mode
            || spec.prompt_version != old.prompt_version
            || spec.text_admission != old.text_admission
            || spec.control_feedback != old.control_feedback;
        let codec = !same(&spec.codec, &old.codec);
        let memory = (resized && !spec.memory_policy.is_latest())
            || spec.memory_policy != old.memory_policy
            || spec.memory_recent_exclusion != old.memory_recent_exclusion;
        if contract || memory {
            next.latest_memory = None;
            next.held_journal_id = None;
            next.held_vector.fill(0.0);
            next.applied_entries.clear();
            next.chosen_memory = None;
            invalidated.push("incompatible-memory-context".into());
        } else if codec {
            next.held_vector.fill(0.0);
            if !spec.memory_policy.is_latest() {
                next.latest_memory = None;
                next.held_journal_id = None;
                next.applied_entries.clear();
                next.chosen_memory = None;
            }
            invalidated.push("codec-feedback-and-selection-vectors".into());
        }
        // A new baseline must not claim that old authored receipts describe it.
        // Preserve the effective controls unless the operator explicitly changed them.
        let prior_continuity = next
            .action_state
            .as_ref()
            .and_then(|a| a.continuity.clone());
        let controls_changed = spec.leak != old.leak
            || spec.feedback_scale != old.feedback_scale
            || spec.recurrent_gain != old.recurrent_gain;
        if contract || controls_changed || resized {
            next.action_state = spec
                .action_mode
                .map(|_| SustainedActionState::initial(spec));
            if !contract {
                if let Some(actions) = &mut next.action_state {
                    actions.continuity = prior_continuity;
                    if let Some(c) = &mut actions.continuity {
                        c.meaningful_receipts.clear();
                        if resized {
                            c.active_inquiry = None;
                            c.latest_inquiry_receipt = None;
                        }
                    }
                }
            }
            invalidated.push(
                if contract {
                    "action-and-inquiry-context"
                } else {
                    "authored-control-receipts"
                }
                .into(),
            );
        }
        // The host materializes unchanged effective controls into the new baseline.
        if memory || (codec && !spec.memory_policy.is_latest()) {
            if let Some(c) = next
                .action_state
                .as_mut()
                .and_then(|a| a.continuity.as_mut())
            {
                c.journal_window.clear();
            }
        }
        if !same(&spec.peer_reading, &old.peer_reading) {
            next.peer_state = spec
                .peer_reading
                .as_ref()
                .map(|_| SustainedPeerState::default());
            invalidated.push("peer-context".into());
        }
        let numerical = resized
            || controls_changed
            || spec.noise_amplitude != old.noise_amplitude
            || spec.sensory_noise_amplitude != old.sensory_noise_amplitude
            || spec.initial_retention != old.initial_retention
            || spec.regulation_enabled != old.regulation_enabled;
        if numerical || codec || contract || !same(&spec.sonar, &old.sonar) {
            next.sonar_state = spec.sonar.as_ref().map(|_| SustainedSonarState {
                experiments: vec![],
                history: vec![SustainedSonarPoint {
                    step: next.step,
                    state: next.reservoir_state.clone(),
                }],
                latest_scan: None,
                latest_compact_scan: None,
                latest_question: None,
            });
            invalidated.push("scan-predictions".into());
        }
        if spec.initial_retention != old.initial_retention {
            next.retention = spec.initial_retention;
        }
        if spec.initial_retention != old.initial_retention
            || spec.regulation_enabled != old.regulation_enabled
        {
            next.controller_integral = 0.0;
            invalidated.push("regulator-integral".into());
        }
        let difference = spec.difference_gain != old.difference_gain
            || spec.difference_tau != old.difference_tau
            || spec.difference_dead_band != old.difference_dead_band
            || spec.difference_clip != old.difference_clip
            || spec.difference_watchdog != old.difference_watchdog
            || spec.difference_watchdog_fill_std != old.difference_watchdog_fill_std
            || spec.difference_watchdog_warmup != old.difference_watchdog_warmup;
        if difference
            || !next.difference_filtered.is_empty()
            || !next.difference_reference.is_empty()
            || next.difference_gain_dropped.is_some()
        {
            next.difference_filtered.clear();
            next.difference_reference.clear();
            next.difference_reference_step = 0;
            next.difference_fill_window.clear();
            next.difference_out_of_band_steps = 0;
            next.difference_saturated_steps = 0;
            next.difference_gain_dropped = None;
            invalidated.push("difference-channel-accumulators".into());
        }
        let schedule = match (&spec.check_in_schedule, &old.check_in_schedule) {
            (Some(a), Some(b)) => {
                a.interval_seconds != b.interval_seconds
                    || a.end_after_seconds != b.end_after_seconds
            }
            (None, None) => false,
            _ => true,
        };
        if !schedule && !same(&spec.check_in_schedule, &old.check_in_schedule) {
            if let (Some(new), Some(old), Some(progress)) = (
                &spec.check_in_schedule,
                &old.check_in_schedule,
                &mut next.check_in_state,
            ) {
                ensure(
                    progress.settings_revisions.len() < MAX_CHECK_IN_REVISIONS,
                    "Conversation settings revision limit reached",
                )?;
                if progress.initial_settings.is_none() {
                    progress.initial_settings = Some(old.clone());
                }
                progress.settings_revisions.push(SustainedCheckInRevision {
                    revision: progress.settings_revisions.len() as u64 + 1,
                    step: next.step,
                    elapsed_millis: self.schedule_elapsed(change.elapsed_millis),
                    prompt: new.prompt.clone(),
                    include_telemetry: new.include_telemetry,
                });
            }
        }
        if schedule {
            next.check_in_state = spec
                .check_in_schedule
                .as_ref()
                .map(|_| SustainedCheckInState::default());
            invalidated.push("future-conversation-schedule".into());
        }
        next.last_observation = None;
        next.latest_frame = None;
        next.last_entry_effect = None;
        next.last_entry_effect_vector.clear();
        next.configuration_phase = Some(ConfigurationPhase {
            revision: change.expected_revision + 1,
            step: next.step,
            turn_cursor: next.turn_cursor,
            rng_state: next.rng_state,
            cadence_origin_step: if spec.turn_every != old.turn_every {
                next.step
            } else {
                self.state
                    .configuration_phase
                    .as_ref()
                    .map_or(0, |p| p.cadence_origin_step)
            },
            schedule_origin_millis: if schedule {
                change.elapsed_millis
            } else {
                self.state
                    .configuration_phase
                    .as_ref()
                    .map_or(0, |p| p.schedule_origin_millis)
            },
            operation_id: change.operation_id.clone(),
            invalidated,
        });
        next.specification = spec.clone();
        next.mechanism = spec.mechanism().into();
        let model = reservoir_model(spec.seed, spec.reservoir_nodes);
        next.model_sha256 = typed_hash(&model);
        validate_state(&next)?;
        self.model = model;
        self.difference =
            difference_matrix_nodes(spec.seed ^ DIFFERENCE_SEED, spec.reservoir_nodes);
        self.state = next;
        self.event(SustainedEventKind::ConfigurationChanged(change));
        Ok(())
    }
}

/// Prefix-preserving expansion v1. The historical 32×32 block and first 32 input
/// rows remain byte-identical. New coordinates use indexed independent streams;
/// adding more nodes never rescales or redraws existing connections.
pub fn reservoir_model(seed: u64, nodes: usize) -> ReservoirModel {
    let original = ReservoirModel::seeded(seed);
    if nodes == 32 {
        return original;
    }
    let mut model = ReservoirModel {
        node_count: nodes,
        input_count: 66,
        recurrent_weights: vec![0.0; nodes * nodes],
        input_weights: vec![0.0; nodes * 67],
    };
    for row in 0..nodes {
        for column in 0..67 {
            model.input_weights[row * 67 + column] = if row < 32 {
                original.input_weights[row * 67 + column]
            } else {
                let mut rng = SplitMix64::new(
                    seed ^ 0x524553495A45494E ^ ((row as u64) << 32) ^ column as u64,
                );
                let boost = if (18..66).contains(&column) {
                    1.6
                } else if (16..18).contains(&column) {
                    1.2
                } else {
                    1.0
                };
                rng.signed() * 0.5 * boost
            };
        }
        for column in 0..nodes {
            model.recurrent_weights[row * nodes + column] = if row < 32 && column < 32 {
                original.recurrent_weights[row * 32 + column]
            } else {
                let mut rng = SplitMix64::new(
                    seed ^ 0x524553495A455245 ^ ((row as u64) << 32) ^ column as u64,
                );
                if rng.unit() < 0.1 {
                    rng.signed() * 0.9 / 12.8
                } else {
                    0.0
                }
            };
        }
    }
    model
}
pub fn default_reservoir_nodes() -> usize {
    32
}
pub fn is_default_reservoir_nodes(n: &usize) -> bool {
    *n == 32
}
pub(super) fn difference_matrix_nodes(seed: u64, nodes: usize) -> Vec<f64> {
    let original = difference_matrix(seed);
    if nodes == 32 {
        return original;
    }
    (0..48)
        .flat_map(|row| {
            let original = &original;
            (0..nodes).map(move |column| {
                if column < 32 {
                    original[row * 32 + column]
                } else {
                    let mut rng = SplitMix64::new(
                        seed ^ 0x524553495A454449 ^ ((row as u64) << 32) ^ column as u64,
                    );
                    (-2.0 * rng.unit().max(1e-300).ln()).sqrt()
                        * (2.0 * std::f64::consts::PI * rng.unit()).cos()
                        / 32f64.sqrt()
                }
            })
        })
        .collect()
}
