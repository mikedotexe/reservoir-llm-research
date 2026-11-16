//! Read-only preflight: no operation record, owner restoration, or provider calls.
use super::*;

impl ResearchService {
    pub fn validate_request(&self, body: &Value) -> Result<Value, AppError> {
        let kind = body["kind"].as_str().unwrap_or("");
        if kind == "recipe" {
            return Ok(
                match self.expand_recipe(&body["recipe"], "validation-preview") {
                    Ok(arms) => {
                        json!({"valid":true,"scope":"recipe-configuration","arms":arms.into_iter().map(|(name,config)|json!({"name":name,"config":config})).collect::<Vec<_>>(),"executionChecks":"No runs prepared, no models checked, no operations submitted."})
                    }
                    Err(e) => invalid("recipe", e.message),
                },
            );
        }
        if !matches!(kind, "configuration" | "action") {
            return Ok(invalid("kind", "Choose configuration, recipe, or action"));
        }
        if body
            .get("runId")
            .is_some_and(|v| v.as_str().is_none_or(str::is_empty))
        {
            return Ok(invalid(
                "runId",
                "Supply an opaque run identifier or omit runId for creation defaults",
            ));
        }
        let settings = body
            .get("runId")
            .and_then(Value::as_str)
            .map(|run| self.settings(run))
            .transpose()?;
        let mut config = settings
            .as_ref()
            .map(|s| s["effective"].clone())
            .unwrap_or(value(SustainedConfig::default())?);
        if let Some(patch) = body.get("config") {
            if !patch.is_object() {
                return Ok(invalid(
                    "config",
                    "Supply a configuration object or partial patch",
                ));
            }
            merge(&mut config, patch);
        }
        let config = match configuration(&config) {
            Ok(c) => c,
            Err(e) => return Ok(invalid("config", e.message)),
        };
        let mut result = if kind == "action" {
            let Some(text) = body["text"].as_str() else {
                return Ok(invalid(
                    "text",
                    "Supply the complete ordinary-turn reply text",
                ));
            };
            match reservoir_core::sustained::validate_authored_action_text(
                &config.specification()?,
                text,
            ) {
                Ok(result) => result,
                Err(e) => invalid("text", e.to_string()),
            }
        } else {
            json!({"valid":true,"scope":"configuration-shape-and-ranges","config":config,"issues":[],
                "executionChecks":"Consumed budgets, revision, phase boundary and state migration are checked when applying. Validation does not apply changes."})
        };
        if let Some(settings) = settings {
            result["configurationRevision"] = settings["configurationRevision"].clone();
        }
        Ok(result)
    }
}
fn invalid(path: &str, message: impl Into<String>) -> Value {
    json!({"valid":false,"issues":[{"path":path,"message":message.into()}]})
}
