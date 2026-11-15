//! Display only committed control/receipt state; pending decisions never imply execution.
use super::*;
use reservoir_core::sustained::{
    SustainedActionDecision, SustainedActionMode, SustainedActionRequest, SustainedActionState,
    SustainedInquiryDecision, SustainedReservoirInputDecision,
};

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PendingActionDecision {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub diagnostics: Option<reservoir_core::sustained::SustainedControlDiagnostics>,
    pub request: Option<SustainedActionRequest>,
    pub rejection: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reservoir_input: Option<SustainedReservoirInputDecision>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub inquiry: Option<SustainedInquiryDecision>,
}
impl From<&SustainedActionDecision> for PendingActionDecision {
    fn from(value: &SustainedActionDecision) -> Self {
        Self {
            diagnostics: value.diagnostics.clone(),
            request: value.request.clone(),
            rejection: value.rejection.clone(),
            reservoir_input: value.reservoir_input.clone(),
            inquiry: value.inquiry.clone(),
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
    #[serde(skip_serializing_if = "Option::is_none")]
    pub peer_read: Option<Box<reservoir_core::sustained::SustainedPeerRead>>,
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
            peer_read: a
                .committed
                .state
                .peer_state
                .as_ref()
                .and_then(|p| p.latest_read.clone()),
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
        let mode = pending
            .check_in
            .is_none()
            .then(|| {
                self.lock().ok().and_then(|g| {
                    g.active
                        .as_ref()
                        .filter(|a| a.epoch == epoch)
                        .and_then(|a| a.engine.specification().action_mode)
                })
            })
            .flatten();
        let Some(mode) = mode else {
            return SCRIPTED_REPLIES[((pending.attempt_id - 1) as usize) % SCRIPTED_REPLIES.len()]
                .into();
        };
        let peer_reading = self.lock().ok().is_some_and(|g| {
            g.active.as_ref().is_some_and(|a| {
                a.epoch == epoch && a.engine.specification().peer_reading.is_some()
            })
        });
        let sonar = self.lock().ok().is_some_and(|g| {
            g.active
                .as_ref()
                .is_some_and(|a| a.epoch == epoch && a.engine.specification().sonar.is_some())
        });
        if sonar {
            return match (pending.attempt_id-1)%4 {
                0=>"Scripted scanner check: request a measured direction; if no scan is cached, expect an explicit rejection.\nNEXT: PROBE_SCAN strongest positive",
                1=>"Scripted scanner check: measure signed coordinate responses on copies.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: SCAN",
                2=>"Scripted scanner check: apply the measured strongest direction if saved live-probe authority permits.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: PROBE_SCAN strongest positive",
                _=>"Scripted scanner check: retain the receipt and let ordinary dynamics continue.\nNEXT: NONE",
            }.into();
        }
        if peer_reading {
            return if pending.attempt_id % 2 == 1 {
                "Example writing: I will read the already-applied entries available from the configured peers.\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: READ_PEERS"
            } else {
                "Example writing: The saved peer reading remains available as attributed context. This scripted example does not interpret its contents.\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: NONE"
            }.into();
        }
        if mode == SustainedActionMode::AuthoredV3 {
            return match (pending.attempt_id - 1) % 4 {
                0 => "Example writing: I will retain a question and inspect the recorded consequence of an alternating pulse.\nINQUIRY: OPEN both \"What changes after this pulse, and what does the recent journal record?\"\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: PULSE alternating 0.5",
                1 => "Example writing: I will keep the question available while withholding this entry's numerical input and changing leak.\nINQUIRY: CONTINUE\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: TUNE leak 0.35",
                2 => "Example writing: I will leave the question open and let ordinary dynamics continue.\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: NONE",
                _ => "Example writing: I will close this question and restore the initial controls while retaining the accumulated state and journal.\nINQUIRY: CLOSE\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: RELEASE",
            }.into();
        }
        if mode == SustainedActionMode::AuthoredV2 {
            return match (pending.attempt_id - 1) % 4 {
                0 => "Example writing: I will send this entry as numerical input and apply an alternating state pulse.\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: PULSE alternating 0.5",
                1 => "Example writing: I will retain these words in memory while withholding their numerical input, and change recurrent leak to 0.35.\nWITHHOLD_RESERVOIR_INPUT=true\nNEXT: TUNE leak 0.35",
                2 => "Example writing: I will send this entry as numerical input again while leaving the current controls in place.\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: NONE",
                _ => "Example writing: I will release the authored control adjustments while retaining the state that has developed.\nWITHHOLD_RESERVOIR_INPUT=false\nNEXT: RELEASE",
            }.into();
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
            .or_else(|| a.engine.pending_feedback().map(|p| &p.pending))
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
        // The core returns no text to encode for an empty authored body or a v2/v3
        // withheld/rejected input decision. The saved body and raw reply remain
        // intact, but there is no embedding request or claimed embedding receipt.
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
    version: SustainedPromptVersion,
) -> serde_json::Value {
    let mut value = serde_json::json!({
        "entryId": memory.entry.id,
        "text": memory.entry.text,
        "sha256": memory.entry.sha256,
    });
    if version == SustainedPromptVersion::ActionJournalV3 {
        let body = memory.entry.body.as_deref().unwrap_or(&memory.entry.text);
        let supplied = reservoir_core::sustained::sustained_v3_memory_excerpt(body);
        value["suppliedText"] = supplied.into();
        value["suppliedTextSha256"] = crate::files::digest(supplied.as_bytes()).into();
        value["suppliedTextTruncated"] = (supplied.len() < body.len()).into();
        value["fullBodyBytes"] = body.len().into();
        value["fullBodySha256"] = crate::files::digest(body.as_bytes()).into();
    } else if let Some(body) = &memory.entry.body {
        value["suppliedText"] = body.clone().into();
        value["suppliedTextSha256"] = crate::files::digest(body.as_bytes()).into();
    }
    value
}
