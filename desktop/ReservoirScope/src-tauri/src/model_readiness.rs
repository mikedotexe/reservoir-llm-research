//! Explicit inventory checks have their own owner, independent of experiment sessions.
use crate::{
    files::AppError,
    model_transport::{self, InventoryMatch, TransportError},
};
use reservoir_core::stage::LanguageConfiguration;
use serde::Serialize;
use std::{
    collections::VecDeque,
    sync::{
        atomic::{AtomicBool, AtomicU64, Ordering},
        Arc, Mutex,
    },
    time::{SystemTime, UNIX_EPOCH},
};

static NEXT_OPERATION: AtomicU64 = AtomicU64::new(1);
#[derive(Clone)]
struct Check {
    request_id: String,
    operation_id: String,
    cancel: Arc<AtomicBool>,
}
#[derive(Default)]
struct Owner {
    active: Option<Check>,
    cancelled: VecDeque<String>,
}
#[derive(Clone, Default)]
pub struct ModelReadinessState(Arc<Mutex<Owner>>);

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ModelReadinessResult {
    request_id: String,
    operation_id: String,
    endpoint: String,
    requested_model: String,
    status: &'static str,
    matched_model: Option<String>,
    digest: Option<String>,
    checked_at_ms: String,
    diagnostic: Option<String>,
}
fn validate_id(id: &str) -> Result<(), AppError> {
    if id.is_empty() || id.len() > 256 {
        Err(AppError::new(
            "check-local-model",
            "request-id",
            "Use a nonempty bounded readiness request identifier.",
        ))
    } else {
        Ok(())
    }
}
impl ModelReadinessState {
    fn begin(&self, request_id: String) -> Result<Check, AppError> {
        validate_id(&request_id)?;
        let mut owner = self.0.lock().map_err(|_| {
            AppError::new(
                "check-local-model",
                "state",
                "Readiness state is unavailable.",
            )
        })?;
        if owner
            .active
            .as_ref()
            .is_some_and(|old| old.request_id == request_id)
        {
            return Err(AppError::new(
                "check-local-model",
                "request-id",
                "This readiness check is already in progress.",
            ));
        }
        let check = Check {
            cancel: Arc::new(AtomicBool::new(owner.cancelled.contains(&request_id))),
            request_id,
            operation_id: format!(
                "model-check-{}-{}",
                std::process::id(),
                NEXT_OPERATION.fetch_add(1, Ordering::Relaxed)
            ),
        };
        // A cancellation received before registration must not supersede a newer check.
        if !check.cancel.load(Ordering::Acquire) {
            if let Some(old) = owner.active.replace(check.clone()) {
                old.cancel.store(true, Ordering::Release);
            }
        }
        Ok(check)
    }
    fn cancel(&self, request_id: String) -> Result<(), AppError> {
        validate_id(&request_id)?;
        let mut owner = self.0.lock().map_err(|_| {
            AppError::new(
                "cancel-local-model-check",
                "state",
                "Readiness state is unavailable.",
            )
        })?;
        if let Some(check) = &owner.active {
            if check.request_id == request_id {
                check.cancel.store(true, Ordering::Release);
            }
        }
        if !owner.cancelled.contains(&request_id) {
            owner.cancelled.push_back(request_id);
        }
        while owner.cancelled.len() > 64 {
            owner.cancelled.pop_front();
        }
        Ok(())
    }
    fn finish(&self, check: &Check) -> Result<bool, AppError> {
        let mut owner = self.0.lock().map_err(|_| {
            AppError::new(
                "check-local-model",
                "state",
                "Readiness state is unavailable.",
            )
        })?;
        let current = owner
            .active
            .as_ref()
            .is_some_and(|active| active.operation_id == check.operation_id);
        if current {
            owner.active = None;
        }
        Ok(current && !check.cancel.load(Ordering::Acquire))
    }
    fn result(
        &self,
        check: Check,
        config: LanguageConfiguration,
        result: Result<InventoryMatch, TransportError>,
    ) -> Result<ModelReadinessResult, AppError> {
        let current = self.finish(&check)?;
        let (status, matched_model, digest, diagnostic) = if !current {
            (
                "cancelled",
                None,
                None,
                Some("This check was cancelled or superseded.".into()),
            )
        } else {
            match result {
                Ok(found) => ("found", Some(found.name), found.digest, None),
                Err(e) => (
                    if e.category == "cancelled" {
                        "cancelled"
                    } else {
                        "unavailable"
                    },
                    None,
                    None,
                    Some(e.message),
                ),
            }
        };
        Ok(ModelReadinessResult {
            request_id: check.request_id,
            operation_id: check.operation_id,
            endpoint: config.endpoint.unwrap_or_default(),
            requested_model: config.model.unwrap_or_default(),
            status,
            matched_model,
            digest,
            diagnostic,
            checked_at_ms: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap_or_default()
                .as_millis()
                .to_string(),
        })
    }
}

#[tauri::command]
pub async fn check_local_model(
    state: tauri::State<'_, ModelReadinessState>,
    request_id: String,
    configuration: LanguageConfiguration,
) -> Result<ModelReadinessResult, AppError> {
    model_transport::validate_configuration(&configuration)
        .map_err(|e| AppError::new("check-local-model", e.category, e.message))?;
    let state = state.inner().clone();
    let check = state.begin(request_id)?;
    let worker_check = check.clone();
    let worker_config = configuration.clone();
    let result = tauri::async_runtime::spawn_blocking(move || {
        model_transport::inventory(&worker_config, &worker_check.cancel)
    })
    .await;
    match result {
        Ok(result) => state.result(check, configuration, result),
        Err(e) => {
            state.finish(&check)?;
            Err(AppError::new("check-local-model", "worker", e.to_string()))
        }
    }
}
#[tauri::command]
pub fn cancel_local_model_check(
    state: tauri::State<'_, ModelReadinessState>,
    request_id: String,
) -> Result<(), AppError> {
    state.cancel(request_id)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn supersession_and_late_completion_do_not_clear_new_owner() {
        let state = ModelReadinessState::default();
        let a = state.begin("a".into()).unwrap();
        let b = state.begin("b".into()).unwrap();
        assert!(a.cancel.load(Ordering::Acquire));
        assert!(!state.finish(&a).unwrap());
        assert!(!b.cancel.load(Ordering::Acquire));
        assert!(state.finish(&b).unwrap());
        assert!(!state.finish(&b).unwrap());
    }
    #[test]
    fn cancellation_before_registration_and_old_cancellation_preserve_new_owner() {
        let state = ModelReadinessState::default();
        state.cancel("a".into()).unwrap();
        let b = state.begin("b".into()).unwrap();
        let a = state.begin("a".into()).unwrap();
        assert!(a.cancel.load(Ordering::Acquire));
        assert!(!state.finish(&a).unwrap());
        state.cancel("a".into()).unwrap();
        assert!(state.finish(&b).unwrap());
    }
    #[test]
    fn explicit_cancellation_and_duplicate_request_ids() {
        let state = ModelReadinessState::default();
        let a = state.begin("a".into()).unwrap();
        assert!(state.begin("a".into()).is_err());
        state.cancel("a".into()).unwrap();
        assert!(a.cancel.load(Ordering::Acquire));
        assert!(!state.finish(&a).unwrap());
        assert!(state.begin(String::new()).is_err());
        assert!(state.cancel("x".repeat(257)).is_err());
    }
}
