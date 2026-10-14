//! Explicit HTTP-only loopback requests. No discovery, service startup, model pull,
//! proxy, redirect, retry, credentials or provider substitution is available here.
use reservoir_core::{
    session::{LanguageResponse, ProviderPromptEvaluation, ProviderPromptEvaluationIssue},
    stage::{LanguageConfiguration, LanguageKind},
};
use serde::Deserialize;
use serde_json::json;
use std::{
    fmt,
    future::{poll_fn, Future},
    net::{IpAddr, Ipv4Addr, Ipv6Addr, SocketAddr},
    pin::pin,
    sync::atomic::{AtomicBool, Ordering},
    task::Poll,
    time::{Duration, Instant},
};

pub const MAXIMUM_BYTES: usize = 1_048_576;
pub const INVENTORY_TIMEOUT: Duration = Duration::from_secs(5);
pub const GENERATION_TIMEOUT: Duration = Duration::from_secs(60);

#[derive(Clone, Debug)]
pub struct TransportError {
    pub category: &'static str,
    pub message: String,
}
impl fmt::Display for TransportError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.message)
    }
}
impl std::error::Error for TransportError {}
fn error(category: &'static str, message: impl Into<String>) -> TransportError {
    TransportError {
        category,
        message: message.into(),
    }
}
type Result<T> = std::result::Result<T, TransportError>;

/// Operational validation is deliberately stricter than inert historical records.
/// Keep the portable reader's Foundation-compatible endpoint interpretation intact.
pub fn validate_configuration(configuration: &LanguageConfiguration) -> Result<()> {
    configuration
        .validate()
        .map_err(|e| error("configuration", e.to_string()))?;
    if configuration.backend != LanguageKind::Ollama {
        return Err(error(
            "configuration",
            "Select an explicit local model configuration.",
        ));
    }
    let endpoint = configuration.endpoint.as_deref().unwrap_or_default();
    let authority = endpoint.strip_prefix("http://").unwrap_or_default();
    let authority = authority.strip_suffix('/').unwrap_or(authority);
    let (host, port) = authority.rsplit_once(':').ok_or_else(|| {
        error(
            "configuration",
            "Use an explicit HTTP loopback address with a port.",
        )
    })?;
    if !matches!(host, "localhost" | "127.0.0.1" | "[::1]")
        || port.is_empty()
        || !port.bytes().all(|b| b.is_ascii_digit())
        || !matches!(port.parse::<u16>(), Ok(1..=65535))
    {
        return Err(error("configuration", "Use http://localhost:PORT, http://127.0.0.1:PORT or http://[::1]:PORT with a port from 1 to 65535 and no path, credentials, query or fragment."));
    }
    Ok(())
}

fn cancelled() -> TransportError {
    error(
        "cancelled",
        "The local model request was cancelled; no late response is accepted.",
    )
}
fn network(e: reqwest::Error) -> TransportError {
    if e.is_timeout() {
        error("timeout", "The local model request exceeded its deadline.")
    } else {
        error(
            "transport",
            format!("The configured local service could not complete the request: {e}"),
        )
    }
}

/// One private runtime per bounded request, called only on an owned backend worker.
/// Cancellation drops the socket future; it never waits for the provider to cooperate.
fn bounded<T>(
    cancel: &AtomicBool,
    timeout: Duration,
    job: impl Future<Output = Result<T>>,
) -> Result<T> {
    if cancel.load(Ordering::Acquire) {
        return Err(cancelled());
    }
    let runtime = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .map_err(|e| error("runtime", e.to_string()))?;
    runtime.block_on(async {
        let until = Instant::now() + timeout;
        let mut work = pin!(job);
        let mut tick = pin!(tokio::time::sleep(Duration::ZERO));
        poll_fn(|cx| {
            if cancel.load(Ordering::Acquire) {
                return Poll::Ready(Err(cancelled()));
            }
            if Instant::now() >= until {
                return Poll::Ready(Err(error(
                    "timeout",
                    "The local model request exceeded its total deadline.",
                )));
            }
            if let Poll::Ready(value) = work.as_mut().poll(cx) {
                return Poll::Ready(if cancel.load(Ordering::Acquire) {
                    Err(cancelled())
                } else if Instant::now() >= until {
                    Err(error(
                        "timeout",
                        "The local model request exceeded its total deadline.",
                    ))
                } else {
                    value
                });
            }
            if tick.as_mut().poll(cx).is_ready() {
                tick.as_mut()
                    .reset(tokio::time::Instant::now() + Duration::from_millis(20));
                cx.waker().wake_by_ref();
            }
            Poll::Pending
        })
        .await
    })
}

async fn request(
    configuration: &LanguageConfiguration,
    body: Option<serde_json::Value>,
    timeout: Duration,
) -> Result<Vec<u8>> {
    let endpoint = configuration
        .endpoint
        .as_deref()
        .unwrap()
        .trim_end_matches('/');
    // Pin localhost resolution to loopback, regardless of host DNS/proxy configuration.
    let client = reqwest::Client::builder()
        .no_proxy()
        .redirect(reqwest::redirect::Policy::none())
        .retry(reqwest::retry::never())
        .timeout(timeout)
        .connect_timeout(timeout)
        .http1_only()
        .pool_max_idle_per_host(0)
        .resolve_to_addrs(
            "localhost",
            &[
                SocketAddr::new(IpAddr::V4(Ipv4Addr::LOCALHOST), 0),
                SocketAddr::new(IpAddr::V6(Ipv6Addr::LOCALHOST), 0),
            ],
        )
        .build()
        .map_err(network)?;
    let builder = if let Some(body) = body {
        client.post(format!("{endpoint}/api/chat")).json(&body)
    } else {
        client
            .get(format!("{endpoint}/api/tags"))
            .header("Accept", "application/json")
    };
    let mut response = builder.send().await.map_err(network)?;
    if response.status().as_u16() != 200 {
        return Err(error(
            "http-status",
            format!(
                "The configured service returned HTTP {}. Redirects are not followed.",
                response.status().as_u16()
            ),
        ));
    }
    if response
        .content_length()
        .is_some_and(|n| n > MAXIMUM_BYTES as u64)
    {
        return Err(error(
            "response-size",
            "The local service response exceeded one MiB.",
        ));
    }
    let mut bytes = Vec::new();
    while let Some(chunk) = response.chunk().await.map_err(network)? {
        if chunk.len() > MAXIMUM_BYTES - bytes.len() {
            return Err(error(
                "response-size",
                "The local service response exceeded one MiB.",
            ));
        }
        bytes.extend_from_slice(&chunk);
    }
    Ok(bytes)
}

#[derive(Clone, Debug)]
pub struct InventoryMatch {
    pub name: String,
    pub digest: Option<String>,
}
fn decode_inventory(bytes: &[u8], model: &str) -> Result<InventoryMatch> {
    #[derive(Deserialize)]
    struct Model {
        name: String,
        model: Option<String>,
        digest: Option<String>,
    }
    #[derive(Deserialize)]
    struct Inventory {
        models: Vec<Model>,
    }
    let inventory: Inventory = serde_json::from_slice(bytes).map_err(|_| {
        error(
            "inventory",
            "The endpoint did not return a valid model inventory.",
        )
    })?;
    let mut matches = inventory.models.into_iter().filter(|row| row.name == model);
    let found = matches.next().ok_or_else(|| {
        error(
            "missing-model",
            "The service responded, but the exact configured model name was not found.",
        )
    })?;
    if matches.next().is_some() {
        return Err(error(
            "duplicate-model",
            "The inventory contains multiple entries for the configured model.",
        ));
    }
    if found.model.as_deref().is_some_and(|name| name != model) {
        return Err(error(
            "inventory",
            "The inventory's model identities disagree.",
        ));
    }
    Ok(InventoryMatch {
        name: found.name,
        digest: found.digest,
    })
}
pub fn inventory(
    configuration: &LanguageConfiguration,
    cancel: &AtomicBool,
) -> Result<InventoryMatch> {
    inventory_with_timeout(configuration, cancel, INVENTORY_TIMEOUT)
}
fn inventory_with_timeout(
    configuration: &LanguageConfiguration,
    cancel: &AtomicBool,
    timeout: Duration,
) -> Result<InventoryMatch> {
    validate_configuration(configuration)?;
    bounded(cancel, timeout, async {
        let bytes = request(configuration, None, timeout).await?;
        decode_inventory(&bytes, configuration.model.as_deref().unwrap())
    })
}
fn generation_body(
    configuration: &LanguageConfiguration,
    prompt: &str,
    output_tokens: u32,
) -> serde_json::Value {
    let mut options = json!({ "num_predict":output_tokens, "temperature":0 });
    if let Some(context) = configuration.context_tokens {
        options["num_ctx"] = json!(context);
    }
    let mut body = json!({ "model":configuration.model, "stream":false,
        "messages":[{"role":"user","content":prompt}], "options":options });
    if let Some(format) = &configuration.response_format {
        body["format"] = json!(format);
    }
    body
}
/// Read this optional provider field from its JSON token, never through f64.
/// Its usability is evidence only; it must not decide whether prose is complete.
fn prompt_evaluation_token(raw: &str) -> Option<ProviderPromptEvaluation> {
    use ProviderPromptEvaluationIssue as Issue;
    let raw = raw.trim();
    let reason = if raw == "null" {
        return None;
    } else if raw.starts_with('-') {
        Issue::Negative
    } else if raw.as_bytes().first().is_some_and(u8::is_ascii_digit) {
        if raw.bytes().all(|b| b.is_ascii_digit()) {
            return Some(match raw.parse::<u64>() {
                Ok(count) => ProviderPromptEvaluation::Reported { count },
                Err(_) => ProviderPromptEvaluation::Unusable {
                    reason: Issue::OutOfRange,
                },
            });
        }
        Issue::NonInteger
    } else {
        Issue::WrongType
    };
    Some(ProviderPromptEvaluation::Unusable { reason })
}

struct PromptEvaluationField(Option<ProviderPromptEvaluation>);
impl<'de> Deserialize<'de> for PromptEvaluationField {
    fn deserialize<D: serde::Deserializer<'de>>(
        deserializer: D,
    ) -> std::result::Result<Self, D::Error> {
        struct Visitor;
        impl<'de> serde::de::Visitor<'de> for Visitor {
            type Value = PromptEvaluationField;
            fn expecting(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
                f.write_str("a provider response object")
            }
            fn visit_map<M: serde::de::MapAccess<'de>>(
                self,
                mut map: M,
            ) -> std::result::Result<Self::Value, M::Error> {
                let mut seen = false;
                let mut duplicate = false;
                let mut value = None;
                while let Some(key) = map.next_key::<String>()? {
                    if key == "prompt_eval_count" {
                        let raw = map.next_value::<Box<serde_json::value::RawValue>>()?;
                        duplicate |= seen;
                        seen = true;
                        value = prompt_evaluation_token(raw.get());
                    } else {
                        map.next_value::<serde::de::IgnoredAny>()?;
                    }
                }
                if duplicate {
                    value = Some(ProviderPromptEvaluation::Unusable {
                        reason: ProviderPromptEvaluationIssue::DuplicateField,
                    });
                }
                Ok(PromptEvaluationField(value))
            }
        }
        deserializer.deserialize_map(Visitor)
    }
}

fn decode_generation(bytes: &[u8], model: &str, output_tokens: u32) -> Result<LanguageResponse> {
    #[derive(Deserialize)]
    struct Message {
        content: String,
    }
    #[derive(Deserialize)]
    struct Response {
        done: bool,
        message: Message,
        model: Option<String>,
        done_reason: Option<String>,
        eval_count: Option<i64>,
    }
    let r: Response = serde_json::from_slice(bytes).map_err(|_| {
        error(
            "response-json",
            "The local model returned an invalid nonstreaming response envelope.",
        )
    })?;
    if r.model.as_deref().is_some_and(|returned| returned != model) {
        return Err(error("model-identity", "The provider returned a different model identity from the explicitly configured model."));
    }
    // Separate parsing keeps malformed optional metadata from becoming a new
    // serde field-type/duplicate-key rejection in the established reply envelope.
    let provider_prompt_evaluation = serde_json::from_slice::<PromptEvaluationField>(bytes)
        .map_err(|_| {
            error(
                "response-json",
                "The local model returned an invalid nonstreaming response envelope.",
            )
        })?
        .0;
    Ok(LanguageResponse {
        text: r.message.content,
        provider_model: r.model,
        complete: r.done
            && r.done_reason.as_deref() != Some("length")
            && r.eval_count
                .is_none_or(|n| (0..=i64::from(output_tokens)).contains(&n)),
        stop_reason: r.done_reason,
        token_count: r.eval_count,
        provider_prompt_evaluation,
    })
}
pub fn generate(
    configuration: &LanguageConfiguration,
    prompt: &str,
    cancel: &AtomicBool,
) -> Result<LanguageResponse> {
    generate_with_timeout(configuration, prompt, cancel, GENERATION_TIMEOUT)
}
/// Sustained-only explicit budgets. Finite stage/action callers keep generate().
pub fn generate_sustained(
    configuration: &LanguageConfiguration,
    prompt: &str,
    cancel: &AtomicBool,
    output_tokens: u32,
    request_deadline_seconds: u64,
) -> Result<LanguageResponse> {
    reservoir_core::sustained::validate_generation_budget(
        output_tokens,
        request_deadline_seconds,
        configuration.context_tokens,
    )
    .map_err(|e| error("configuration", e.to_string()))?;
    generate_with_limits(
        configuration,
        prompt,
        cancel,
        Duration::from_secs(request_deadline_seconds),
        output_tokens,
    )
}
fn generate_with_timeout(
    configuration: &LanguageConfiguration,
    prompt: &str,
    cancel: &AtomicBool,
    timeout: Duration,
) -> Result<LanguageResponse> {
    generate_with_limits(configuration, prompt, cancel, timeout, 256)
}
fn generate_with_limits(
    configuration: &LanguageConfiguration,
    prompt: &str,
    cancel: &AtomicBool,
    timeout: Duration,
    output_tokens: u32,
) -> Result<LanguageResponse> {
    validate_configuration(configuration)?;
    if prompt.len() > MAXIMUM_BYTES {
        return Err(error(
            "prompt-size",
            "The prepared prompt exceeds the bounded local request size.",
        ));
    }
    bounded(cancel, timeout, async {
        let bytes = request(
            configuration,
            Some(generation_body(configuration, prompt, output_tokens)),
            timeout,
        )
        .await?;
        decode_generation(
            &bytes,
            configuration.model.as_deref().unwrap(),
            output_tokens,
        )
    })
}

#[cfg(test)]
#[path = "model_transport_tests.rs"]
mod tests;
