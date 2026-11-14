//! Display only committed control/receipt state; pending decisions never imply execution.
use super::*;
use reservoir_core::sustained::{
    SustainedActionDecision, SustainedActionRequest, SustainedActionState,
};

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PendingActionDecision {
    pub request: Option<SustainedActionRequest>,
    pub rejection: Option<String>,
}
impl From<&SustainedActionDecision> for PendingActionDecision {
    fn from(value: &SustainedActionDecision) -> Self {
        Self {
            request: value.request.clone(),
            rejection: value.rejection.clone(),
        }
    }
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PendingAction {
    pub attempt_id: u64,
    pub entry_id: String,
    pub observed_step: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub intended_step: Option<u64>,
    pub phase: &'static str,
    pub durable_prepared: bool,
    pub decision: PendingActionDecision,
}
#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ActionsSummary {
    pub state: SustainedActionState,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pending: Option<PendingAction>,
    pub durable_step: u64,
}

impl SustainedState {
    pub(super) fn actions_summary(&self, a: &Active) -> Option<ActionsSummary> {
        let state = a.committed.state.action_state.clone()?;
        let pending = if let Some(p) = a.engine.pending_journal() {
            p.action.as_deref().map(|decision| PendingAction {
                attempt_id: p.entry.attempt_id,
                entry_id: p.entry.id.clone(),
                observed_step: p.entry.observed_step,
                intended_step: None,
                phase: "saving",
                durable_prepared: false,
                decision: decision.into(),
            })
        } else {
            a.engine.prepared_application().and_then(|p| {
                p.action.as_deref().map(|decision| PendingAction {
                    attempt_id: p.entry.attempt_id,
                    entry_id: p.entry.id.clone(),
                    observed_step: p.entry.observed_step,
                    intended_step: Some(p.application_step),
                    phase: "prepared",
                    durable_prepared: matches!(
                        &a.committed.state.phase,
                        SustainedPhase::Prepared(saved) if saved.entry.id == p.entry.id
                    ),
                    decision: decision.into(),
                })
            })
        };
        Some(ActionsSummary {
            state,
            pending,
            durable_step: a.committed.state.step,
        })
    }

    /// Offline examples exercise actual actions only in an explicitly enabled,
    /// ordinary turn. Scheduled probes retain their passive, historical replies.
    pub(super) fn scripted_reply_for(
        &self,
        epoch: u64,
        pending: &reservoir_core::sustained::SustainedPendingLanguage,
    ) -> String {
        let enabled = pending.check_in.is_none()
            && self
                .lock()
                .ok()
                .and_then(|g| {
                    g.active
                        .as_ref()
                        .map(|a| a.epoch == epoch && a.engine.specification().action_mode.is_some())
                })
                .unwrap_or(false);
        if !enabled {
            return SCRIPTED_REPLIES[((pending.attempt_id - 1) as usize) % SCRIPTED_REPLIES.len()]
                .into();
        }
        match (pending.attempt_id - 1) % 4 {
            0 => "Example writing: I will apply an alternating state pulse and inspect its recorded consequence.\nNEXT: PULSE alternating 0.5",
            1 => "Example writing: I will change recurrent leak to 0.35 for subsequent steps. The receipt will show whether it was applied.\nNEXT: TUNE leak 0.35",
            2 => "Example writing: I will leave the current controls in place and let ordinary evolution continue.\nNEXT: NONE",
            _ => "Example writing: I will release the authored control adjustments while retaining the state that has developed.\nNEXT: RELEASE",
        }.into()
    }

    /// Compute the exact text the core will encode while retaining the raw provider
    /// response for its existing save, hash and replay contract. The state lock is
    /// released before the potentially slow embedding call.
    #[cfg(test)]
    pub(super) fn feedback_text_for(
        &self,
        epoch: u64,
        attempt: u64,
        text: &str,
    ) -> Result<String, String> {
        self.feedback_text_and_action_for(epoch, attempt, text)
            .map(|(body, _)| body)
    }

    fn feedback_text_and_action_for(
        &self,
        epoch: u64,
        attempt: u64,
        text: &str,
    ) -> Result<(String, bool), String> {
        let g = self.lock().map_err(|e| e.message)?;
        let a = g.active.as_ref().ok_or("No active writing attempt")?;
        let pending = a
            .engine
            .pending_language()
            .ok_or("No pending writing attempt")?;
        if a.epoch != epoch || pending.attempt_id != attempt {
            return Err("The writing attempt changed before feedback encoding".into());
        }
        let authored = a.engine.specification().action_mode.is_some() && pending.check_in.is_none();
        a.engine
            .feedback_text_for_response(text)
            .map(|body| (body, authored))
            .map_err(|e| e.to_string())
    }

    pub(super) fn external_feedback_for(
        &self,
        epoch: u64,
        pending: &reservoir_core::sustained::SustainedPendingLanguage,
        text: &str,
        model: &str,
        projection_seed: u64,
    ) -> Result<Option<reservoir_core::sustained::ExternalFeedback>, String> {
        let (body, authored) =
            self.feedback_text_and_action_for(epoch, pending.attempt_id, text)?;
        // An explicitly authored action may stand alone. It still saves and applies,
        // but its empty body contributes zero text feedback and needs no embedding.
        if authored && body.trim().is_empty() {
            return Ok(None);
        }
        let receipt = (self.shared.embedder)(
            &pending.configuration,
            model,
            &body,
            &self.shared.cancel,
            pending.request_deadline_seconds,
        )?;
        let vector = reservoir_core::codec::project_embedding(&receipt.vector, projection_seed)
            .map_err(|e| e.to_string())?;
        let raw = serde_json::to_vec(&receipt.vector).unwrap_or_default();
        Ok(Some(reservoir_core::sustained::ExternalFeedback {
            vector,
            provenance: reservoir_core::sustained::FeedbackProvenance {
                kind: "embedding".into(),
                model: receipt.model,
                digest: receipt.digest,
                dimensions: receipt.vector.len(),
                embedding_sha256: format!("{:x}", <sha2::Sha256 as sha2::Digest>::digest(&raw)),
                projection_seed,
            },
        }))
    }
}

/// Preserve original journal identity and identify the exact body supplied back to
/// the model separately. An action entry's raw-text hash never labels body-only text.
pub(super) fn memory_evidence(
    memory: &reservoir_core::sustained::SustainedMemory,
) -> serde_json::Value {
    let mut value = serde_json::json!({
        "entryId": memory.entry.id,
        "text": memory.entry.text,
        "sha256": memory.entry.sha256,
    });
    if let Some(body) = &memory.entry.body {
        value["suppliedText"] = body.clone().into();
        value["suppliedTextSha256"] = crate::files::digest(body.as_bytes()).into();
    }
    value
}
