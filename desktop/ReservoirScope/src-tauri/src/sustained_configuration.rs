use super::*;

#[derive(Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ConfigurationRecord {
    pub event_id: u64,
    pub step: u64,
    pub elapsed_millis: u64,
    pub operation_id: String,
    pub revision: u64,
    pub invalidated: Vec<String>,
    pub config: SustainedConfig,
}

impl SustainedState {
    pub fn retain_shutdown(&self) -> Result<bool, AppError> {
        self.shared
            .configuration_pause
            .store(true, Ordering::SeqCst);
        if self.requires_reload() {
            return Ok(true);
        }
        if self.shared.closing.load(Ordering::SeqCst) {
            return Ok(true);
        }
        let mut g = self.shared.inner.lock().map_err(ce)?;
        if let Some(a) = g.active.as_mut() {
            if a.worker_active {
                return Ok(false);
            }
            if a.engine.pending_journal().is_some() || !a.engine.events().is_empty() {
                return Ok(false); // A save failure needs explicit recovery, never discard.
            }
            if a.engine.pending_language().is_some() || a.engine.pending_feedback().is_some() {
                a.engine.interrupt("Application shutdown retained this opportunity; explicit recovery is required").map_err(ce)?;
                a.manifest.phase = "interrupted".into();
                a.manifest.revision = next(&a.manifest.revision);
                a.run_requested = false;
                self.persist_mode(a, sustained_store::Admission::Close)?;
            }
        }
        self.shared.closing.store(true, Ordering::SeqCst);
        Ok(true)
    }
    pub fn request_boundary_pause(&self) {
        self.shared
            .configuration_pause
            .store(true, Ordering::SeqCst);
    }
    pub fn cancel_boundary_pause(&self) {
        self.shared
            .configuration_pause
            .store(false, Ordering::SeqCst);
    }
    pub fn settled_boundary(&self) -> bool {
        self.shared.inner.lock().ok().is_some_and(|g| {
            g.active
                .as_ref()
                .is_some_and(|a| !a.worker_active && a.engine.configuration_boundary())
        })
    }
    pub fn settings(&self) -> Result<serde_json::Value, AppError> {
        let g = self.lock()?;
        let a = g.active.as_ref().ok_or_else(|| err("missing", "No run"))?;
        let mut effective = serde_json::to_value(a.manifest.current_config()).map_err(ce)?;
        let limits = a.manifest.effective_limits();
        effective["maximumSteps"] = serde_json::json!(limits.maximum_steps);
        effective["maximumTurns"] = serde_json::json!(limits.maximum_turns);
        effective["maximumDurationSeconds"] = serde_json::json!(limits.maximum_duration_seconds);
        if let Some(settings) = a
            .committed
            .state
            .check_in_state
            .as_ref()
            .and_then(|c| c.settings_revisions.last())
        {
            effective["checkInSchedule"]["prompt"] = serde_json::json!(settings.prompt);
            effective["checkInSchedule"]["includeTelemetry"] =
                serde_json::json!(settings.include_telemetry);
        }
        if let Some(actions) = &a.committed.state.action_state {
            effective["leak"] = serde_json::json!(actions.controls.leak);
            effective["feedbackScale"] = serde_json::json!(actions.controls.feedback_scale);
            effective["recurrentGain"] = serde_json::json!(actions.controls.recurrent_gain);
        }
        Ok(
            serde_json::json!({"original":a.manifest.config,"configured":a.manifest.current_config(),
            "effective":effective,"configurationRevision":a.engine.configuration_revision(),
            "history":a.manifest.configuration_changes,"checkpointSha256":a.committed.sha256}),
        )
    }
    pub fn apply_configuration(
        &self,
        operation_id: &str,
        expected_revision: u64,
        config: SustainedConfig,
    ) -> Result<serde_json::Value, AppError> {
        config.validate()?;
        let mut g = self.lock()?;
        let a = g.active.as_mut().ok_or_else(|| err("missing", "No run"))?;
        if a.manifest.phase == "stopped" {
            return Err(err("phase", "A stopped run requires a fresh linked run"));
        }
        if !a.engine.configuration_boundary() || a.worker_active {
            return Err(err("needs-boundary", "The admitted turn has not settled"));
        }
        if config.maximum_duration_seconds.saturating_mul(1000) < a.manifest.elapsed_millis
            || config.storage_budget_bytes < a.used_bytes.saturating_add(2 * 1024 * 1024)
        {
            return Err(err(
                "configuration",
                "Limits are below consumed resources plus persistence reserve",
            ));
        }
        let change = reservoir_core::sustained::ConfigurationChange {
            version: 1,
            operation_id: operation_id.into(),
            expected_revision,
            predecessor_sha256: a.engine.checkpoint().sha256,
            specification: config.specification()?,
            host_configuration: serde_json::to_value(&config).map_err(ce)?,
            elapsed_millis: a.manifest.elapsed_millis,
        };
        let mut engine = a.engine.clone();
        engine.reconfigure(change).map_err(ce)?;
        let phase = engine.checkpoint().state.configuration_phase.unwrap();
        let record = ConfigurationRecord {
            event_id: engine.events().back().unwrap().id,
            step: a.manifest.step,
            elapsed_millis: a.manifest.elapsed_millis,
            operation_id: operation_id.into(),
            revision: phase.revision,
            invalidated: phase.invalidated,
            config,
        };
        let mut manifest = a.manifest.clone();
        manifest.configuration_changes.push(record.clone());
        manifest.revision = next(&manifest.revision);
        manifest.phase = "paused".into();
        let committed = match self.shared.store.persist(
            &mut manifest,
            &a.committed,
            &mut engine,
            sustained_store::Admission::Ordinary,
        ) {
            Ok(cp) => cp,
            Err(error) => {
                let recovered =
                    self.shared
                        .store
                        .verify(&manifest.session_id)
                        .ok()
                        .filter(|saved| {
                            saved.manifest.generation == manifest.generation
                                && saved.manifest.revision == manifest.revision
                                && saved.checkpoint.sha256 == engine.checkpoint().sha256
                        });
                let Some(saved) = recovered else {
                    if !self
                        .shared
                        .store
                        .verify(&manifest.session_id)
                        .is_ok_and(|saved| saved.checkpoint.sha256 == a.committed.sha256)
                    {
                        self.shared
                            .configuration_uncertain
                            .store(true, Ordering::SeqCst);
                        return Err(err("needs-attention", "Could not establish configuration publication; the next explicit mutation must reload verified storage"));
                    }
                    return Err(error);
                };
                manifest = saved.manifest;
                engine.acknowledge_events(record.event_id).map_err(ce)?;
                saved.checkpoint
            }
        };
        a.engine = engine;
        a.manifest = manifest;
        a.committed = committed;
        a.used_bytes = self.shared.store.used_bytes(&a.manifest.session_id)?;
        self.shared
            .configuration_pause
            .store(false, Ordering::SeqCst);
        drop(g);
        self.emit();
        serde_json::to_value(record).map_err(ce)
    }
    pub fn stored_manifest(&self) -> Result<Manifest, AppError> {
        self.lock()?
            .active
            .as_ref()
            .map(|a| a.manifest.clone())
            .ok_or_else(|| err("missing", "No run"))
    }
    pub fn catalog_snapshot(&self) -> Result<(Manifest, Vec<JournalIndex>), AppError> {
        let g = self.lock()?;
        let a = g.active.as_ref().ok_or_else(|| err("missing", "No run"))?;
        Ok((a.manifest.clone(), a.catalog.clone()))
    }
}

#[derive(Clone)]
pub struct BoundaryTarget {
    pub step: Option<u64>,
    pub active_millis: Option<u64>,
    pub reached: Option<bool>,
}
impl BoundaryTarget {
    fn due(&self, step: u64, elapsed: u64) -> bool {
        self.step.is_some_and(|s| step >= s) || self.active_millis.is_some_and(|t| elapsed >= t)
    }
}
impl SustainedState {
    pub fn arm_boundary(
        &self,
        id: &str,
        step: Option<u64>,
        active_millis: Option<u64>,
    ) -> Result<(), AppError> {
        let g = self.lock()?;
        let a = g.active.as_ref().ok_or_else(|| err("missing", "No run"))?;
        let mut targets = self.shared.boundary_targets.lock().map_err(ce)?;
        if targets.len() >= 32
            || targets
                .values()
                .any(|t| t.step == step && t.active_millis == active_millis)
        {
            return Err(err(
                "conflict",
                "At most 32 distinct intervention boundaries may be scheduled per run",
            ));
        }
        let mut target = BoundaryTarget {
            step,
            active_millis,
            reached: None,
        };
        if !a.worker_active && target.due(a.engine.step(), a.manifest.elapsed_millis) {
            target.reached = Some(false);
        }
        targets.insert(id.into(), target);
        Ok(())
    }
    pub(super) fn target_due(&self, a: &Active) -> bool {
        let mut targets = self.shared.boundary_targets.lock().unwrap();
        for t in targets.values_mut() {
            if t.reached.is_none() && t.due(a.engine.step(), a.manifest.elapsed_millis) {
                t.reached = Some(a.run_requested);
            }
        }
        targets.values().any(|t| t.reached.is_some())
    }
    pub fn boundary_reached(&self, id: &str) -> Option<bool> {
        self.shared.boundary_targets.lock().ok()?.get(id)?.reached
    }
    pub fn disable_target_resume(&self) {
        if let Ok(mut targets) = self.shared.boundary_targets.lock() {
            for t in targets.values_mut() {
                if t.reached.is_some() {
                    t.reached = Some(false);
                }
            }
        }
    }
    pub fn disarm_boundary(&self, id: &str) {
        if let Ok(mut t) = self.shared.boundary_targets.lock() {
            t.remove(id);
        }
    }
    pub fn custom_prompt(
        &self,
        operation_id: &str,
        prompt: String,
        telemetry: bool,
        resume: bool,
    ) -> Result<serde_json::Value, AppError> {
        let mut g = self.lock()?;
        let a = g.active.as_mut().ok_or_else(|| err("missing", "No run"))?;
        if !a.engine.configuration_boundary() || a.worker_active {
            return Err(err("needs-boundary", "The current turn must settle"));
        }
        let mut engine = a.engine.clone();
        if engine.checkpoint().state.latest_frame.is_none() {
            engine.advance().map_err(ce)?;
        }
        engine
            .admit_custom_prompt(
                operation_id.into(),
                prompt,
                telemetry,
                a.manifest.elapsed_millis,
            )
            .map_err(ce)?;
        a.engine = engine;
        a.manifest.revision = next(&a.manifest.revision);
        self.persist(a)?;
        self.shared
            .configuration_pause
            .store(!resume, Ordering::SeqCst);
        self.shared.pause.store(false, Ordering::SeqCst);
        self.shared.cancel.store(false, Ordering::SeqCst);
        self.shared.interrupted.store(false, Ordering::SeqCst);
        a.run_requested = true;
        a.manifest.phase = "running".into();
        a.last_accounted = Instant::now();
        let result = serde_json::json!({"runId":a.manifest.session_id,"operationId":operation_id,"observedStep":a.engine.step(),"attemptId":a.engine.pending_language().map(|p|p.attempt_id),"status":"admitted"});
        self.disarm_boundary(operation_id);
        self.launch(a);
        drop(g);
        self.emit();
        Ok(result)
    }
}
