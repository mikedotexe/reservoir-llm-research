//! Desktop scheduling and display projection for replayable conversational turns.
use super::*;
use reservoir_core::sustained::SustainedCheckInStatus;

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CheckInSettings {
    pub revision: u64,
    pub prompt: String,
    pub include_telemetry: bool,
    pub elapsed_millis: u64,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CheckInSlot {
    pub ordinal: u64,
    pub scheduled_seconds: u64,
    pub status: String,
    pub admitted_elapsed_millis: Option<u64>,
    pub entry_id: Option<String>,
    pub attempt_id: Option<u64>,
    pub settings_revision: Option<u64>,
    pub prompt: Option<String>,
    pub include_telemetry: Option<bool>,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CheckInSummary {
    pub interval_seconds: u64,
    pub end_after_seconds: u64,
    pub settings: CheckInSettings,
    pub settings_history: Vec<CheckInSettings>,
    pub can_edit: bool,
    pub complete: bool,
    pub slots: Vec<CheckInSlot>,
}

impl SustainedState {
    fn can_edit_check_ins(&self, a: &Active) -> bool {
        a.engine.check_in_state().is_some_and(|state| {
            state.settings_revisions.len() < reservoir_core::sustained::MAX_CHECK_IN_REVISIONS
        }) && !a.engine.check_in_complete()
            && !a.worker_active
            && !a.run_requested
            && !a.dispatch_once
            && a.manifest.phase != "stopped"
            && !sustained_store::storage_held(&a.manifest)
            && a.engine.pending_journal().is_none()
            && !a
                .engine
                .pending_language()
                .is_some_and(|p| p.request_started)
            && a.engine.events().is_empty()
            && a.engine.checkpoint().sha256 == a.committed.sha256
    }
    pub fn update_check_in_settings(
        &self,
        request_id: String,
        id: &str,
        generation: &str,
        expected_revision: &str,
        prompt: String,
        include_telemetry: bool,
    ) -> Result<SustainedUpdate, AppError> {
        let mut g = self.lock()?;
        let a = active(&mut g, id, generation)?;
        if a.manifest.revision != expected_revision {
            return Err(err(
                "stale",
                "Session changed before the conversation settings were saved",
            ));
        }
        if !self.can_edit_check_ins(a) {
            return Err(err(
                "phase",
                "Pause and let writing and saving settle before editing future check-ins",
            ));
        }
        // Publish a clone first: an unsuccessful save must not alter future prompts.
        let mut engine = a.engine.clone();
        engine
            .update_check_in_settings(prompt, include_telemetry, a.engine.schedule_elapsed(a.manifest.elapsed_millis))
            .map_err(ce)?;
        let event_id = engine
            .events()
            .back()
            .ok_or_else(|| err("settings", "No conversation settings change"))?
            .id;
        let mut manifest = a.manifest.clone();
        manifest.revision = next(&manifest.revision);
        let committed = match self.shared.store.persist(
            &mut manifest,
            &a.committed,
            &mut engine,
            sustained_store::Admission::Ordinary,
        ) {
            Ok(cp) => cp,
            Err(error) => {
                let recovered = self.shared.store.verify(id).ok().filter(|saved| {
                    saved.manifest.generation == manifest.generation
                        && saved.manifest.revision == manifest.revision
                        && saved.checkpoint.sha256 == engine.checkpoint().sha256
                });
                let Some(saved) = recovered else {
                    return Err(error);
                };
                manifest = saved.manifest;
                engine.acknowledge_events(event_id).map_err(ce)?;
                saved.checkpoint
            }
        };
        a.engine = engine;
        a.manifest = manifest;
        a.committed = committed;
        a.used_bytes = self.shared.store.used_bytes(id).unwrap_or(a.used_bytes);
        let update = self.update(&g, request_id);
        drop(g);
        self.emit();
        Ok(update)
    }
    pub(super) fn finish_check_ins(&self, a: &mut Active) -> Result<Work, AppError> {
        a.run_requested = false;
        a.dispatch_once = false;
        a.manifest.phase = "scheduleComplete".into();
        a.manifest.revision = next(&a.manifest.revision);
        self.persist(a)?;
        self.shared.busy.store(false, Ordering::SeqCst);
        Ok(Work::Done)
    }
    pub(super) fn check_in_summary(&self, a: &Active) -> Option<CheckInSummary> {
        let schedule = a.manifest.current_config().check_in_schedule.as_ref()?;
        let state = a.engine.check_in_state()?;
        let durable = a.committed.state.check_in_state.as_ref()?;
        let mut history = vec![CheckInSettings {
            revision: 0,
            prompt: state.initial_settings.as_ref().unwrap_or(schedule).prompt.clone(),
            include_telemetry: state.initial_settings.as_ref().unwrap_or(schedule).include_telemetry,
            elapsed_millis: 0,
        }];
        history.extend(state.settings_revisions.iter().map(|r| CheckInSettings {
            revision: r.revision,
            prompt: r.prompt.clone(),
            include_telemetry: r.include_telemetry,
            elapsed_millis: r.elapsed_millis,
        }));
        let slots = (1..=schedule.opportunity_count())
            .map(|ordinal| {
                let outcome = state.outcomes.iter().find(|o| o.ordinal == ordinal);
                let context = outcome.and_then(|o| o.context.as_ref());
                let turn_id = outcome.and_then(|o| o.turn_id);
                let row = a.catalog.iter().rev().find(|j| Some(j.turn_id) == turn_id);
                let pending = a
                    .engine
                    .pending_language()
                    .filter(|p| p.check_in.as_ref().is_some_and(|c| c.ordinal == ordinal));
                let blocked = a.engine.blocked().filter(|p| {
                    p.pending
                        .check_in
                        .as_ref()
                        .is_some_and(|c| c.ordinal == ordinal)
                });
                // Applied/skipped/completed labels describe the durable record,
                // not an in-memory transition whose checkpoint save has failed.
                let status = match durable
                    .outcomes
                    .iter()
                    .find(|o| o.ordinal == ordinal)
                    .map(|o| &o.status)
                {
                    Some(SustainedCheckInStatus::Applied) => "applied",
                    Some(SustainedCheckInStatus::Skipped) => "skipped",
                    Some(SustainedCheckInStatus::Missed) => "missed",
                    _ if blocked.is_some() => {
                        if a.manifest.phase == "stopped" {
                            "cancelled"
                        } else {
                            "failed"
                        }
                    }
                    _ if row.is_some() => "saved",
                    _ if a.manifest.phase == "stopped" => "cancelled",
                    _ if pending.is_some_and(|p| p.request_started) => "requesting",
                    _ if context.is_some() => "prepared",
                    _ => "pending",
                };
                CheckInSlot {
                    ordinal,
                    scheduled_seconds: schedule
                        .deadline_seconds(ordinal)
                        .expect("bounded schedule ordinal"),
                    status: status.into(),
                    admitted_elapsed_millis: context.map(|c| c.admitted_elapsed_millis),
                    entry_id: row
                        .map(|j| j.entry_id.clone())
                        .or_else(|| outcome.and_then(|o| o.journal_id.clone())),
                    attempt_id: pending
                        .map(|p| p.attempt_id)
                        .or_else(|| blocked.map(|b| b.pending.attempt_id))
                        .or_else(|| row.map(|j| j.attempt_id)),
                    settings_revision: context.map(|c| c.settings_revision),
                    prompt: context.map(|c| c.prompt.clone()),
                    include_telemetry: context.map(|c| c.include_telemetry),
                }
            })
            .collect();
        Some(CheckInSummary {
            interval_seconds: schedule.interval_seconds,
            end_after_seconds: schedule.end_after_seconds,
            settings: history.last().expect("initial settings").clone(),
            settings_history: history,
            can_edit: self.can_edit_check_ins(a),
            complete: durable.outcomes.last().is_some_and(|o| {
                o.ordinal == schedule.opportunity_count()
                    && matches!(
                        o.status,
                        SustainedCheckInStatus::Applied | SustainedCheckInStatus::Skipped
                    )
            }),
            slots,
        })
    }
}
