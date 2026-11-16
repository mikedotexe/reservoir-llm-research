//! Authenticated loopback transport. No URL carries credentials or mutation authority.
use crate::{
    files::AppError,
    research_service::{self, ResearchService},
};
use axum::{
    body::{to_bytes, Body},
    extract::{Request, State},
    http::{HeaderMap, StatusCode},
    response::{
        sse::{Event, KeepAlive, Sse},
        IntoResponse, Response,
    },
    Json, Router,
};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap, convert::Infallible, fs, io::Write, path::PathBuf, sync::Arc,
    time::Duration,
};
use tokio_stream::{wrappers::IntervalStream, StreamExt};

#[derive(Clone)]
struct Server {
    service: ResearchService,
    token: Arc<String>,
    host: String,
    instance: String,
}
pub struct ApiServer {
    shutdown: Option<tokio::sync::oneshot::Sender<()>>,
    descriptor: PathBuf,
    pub address: String,
    pub instance: String,
}
impl Drop for ApiServer {
    fn drop(&mut self) {
        if let Some(tx) = self.shutdown.take() {
            let _ = tx.send(());
        }
        if let Ok(bytes) = fs::read(&self.descriptor) {
            if serde_json::from_slice::<Value>(&bytes)
                .ok()
                .is_some_and(|v| v["instanceId"] == self.instance)
            {
                let _ = fs::remove_file(&self.descriptor);
            }
        }
    }
}
fn response_error(e: AppError) -> Response {
    let status = match e.category.as_str() {
        "unauthorized" => StatusCode::UNAUTHORIZED,
        "origin" | "host" => StatusCode::FORBIDDEN,
        "not-found" | "missing" => StatusCode::NOT_FOUND,
        "cursor-expired" => StatusCode::GONE,
        "conflict" | "stale" | "idempotency-conflict" | "closing" => StatusCode::CONFLICT,
        "busy" => StatusCode::TOO_MANY_REQUESTS,
        "storage" | "worker" => StatusCode::INTERNAL_SERVER_ERROR,
        _ => StatusCode::UNPROCESSABLE_ENTITY,
    };
    (
        status,
        Json(json!({"error":{"code":e.category,"message":e.message,"operation":e.operation}})),
    )
        .into_response()
}
fn authorized(headers: &HeaderMap, server: &Server) -> Result<(), AppError> {
    if headers.contains_key("origin") {
        return Err(research_service::error(
            "origin",
            "Browser-origin API requests are not accepted",
        ));
    }
    if headers.get("host").and_then(|h| h.to_str().ok()) != Some(server.host.as_str()) {
        return Err(research_service::error(
            "host",
            "Host does not identify this loopback instance",
        ));
    }
    let expected = format!("Bearer {}", server.token);
    let received = headers
        .get("authorization")
        .map(|h| h.as_bytes())
        .unwrap_or_default();
    let different = received
        .iter()
        .zip(expected.as_bytes())
        .fold(0u8, |d, (a, b)| d | (a ^ b));
    if received.len() != expected.len() || different != 0 {
        return Err(research_service::error(
            "unauthorized",
            "A same-user discovery token is required",
        ));
    }
    Ok(())
}
pub fn start(service: ResearchService, identity: &str) -> Result<ApiServer, AppError> {
    let listener = std::net::TcpListener::bind((std::net::Ipv4Addr::LOCALHOST, 0))
        .map_err(|e| research_service::error("listen", e.to_string()))?;
    listener
        .set_nonblocking(true)
        .map_err(|e| research_service::error("listen", e.to_string()))?;
    let host = listener.local_addr().unwrap().to_string();
    let address = format!("http://{host}");
    let instance = research_service::id("instance");
    let token = format!(
        "{}{}",
        uuid::Uuid::new_v4().simple(),
        uuid::Uuid::new_v4().simple()
    );
    let descriptor = service.discovery_directory().join("endpoint.json");
    let mut temp = tempfile::NamedTempFile::new_in(service.discovery_directory())
        .map_err(|e| research_service::error("discovery", e.to_string()))?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        temp.as_file()
            .set_permissions(fs::Permissions::from_mode(0o600))
            .map_err(|e| research_service::error("discovery", e.to_string()))?;
    }
    temp.write_all(json!({"version":1,"instanceId":instance,"applicationId":identity,"pid":std::process::id(),"url":address,"token":token}).to_string().as_bytes()).map_err(|e|research_service::error("discovery",e.to_string()))?;
    temp.as_file()
        .sync_all()
        .map_err(|e| research_service::error("discovery", e.to_string()))?;
    temp.persist(&descriptor)
        .map_err(|e| research_service::error("discovery", e.to_string()))?;
    let state = Server {
        service,
        token: Arc::new(token),
        host,
        instance: instance.clone(),
    };
    let app = Router::new().fallback(handle).with_state(state);
    let (tx, rx) = tokio::sync::oneshot::channel();
    tauri::async_runtime::spawn(async move {
        let listener =
            tokio::net::TcpListener::from_std(listener).expect("nonblocking loopback listener");
        if let Err(e) = axum::serve(listener, app)
            .with_graceful_shutdown(async {
                let _ = rx.await;
            })
            .await
        {
            eprintln!("Research API stopped: {e}");
        }
    });
    Ok(ApiServer {
        shutdown: Some(tx),
        descriptor,
        address,
        instance,
    })
}
async fn handle(State(server): State<Server>, request: Request) -> Response {
    if let Err(e) = authorized(request.headers(), &server) {
        return response_error(e);
    }
    let method = request.method().as_str().to_owned();
    let path = request.uri().path().to_owned();
    let query: BTreeMap<String, String> = request
        .uri()
        .query()
        .map(|q| {
            tauri::Url::parse(&format!("http://localhost/?{q}"))
                .map(|u| u.query_pairs().into_owned().collect())
                .unwrap_or_default()
        })
        .unwrap_or_default();
    if method == "GET" && path == "/v1/events" {
        // Full replacement snapshots provide explicit resynchronization after reconnect.
        // The pull-driven stream has no unbounded producer queue and never owns a run clock.
        let stream=IntervalStream::new(tokio::time::interval(Duration::from_secs(1))).map(move |_|{
            let runs=server.service.list_runs().unwrap_or_else(|e|json!({"error":e}));
            let ops=server.service.operations().unwrap_or_default().into_iter().take(64).map(|o|json!({"id":o.id,"status":o.status})).collect::<Vec<_>>();
            Ok::<_,Infallible>(Event::default().event("snapshot").data(json!({"instanceId":server.instance,"resync":true,"runs":runs,"operations":ops}).to_string()))
        });
        return Sse::new(stream)
            .keep_alive(KeepAlive::new().interval(Duration::from_secs(5)))
            .into_response();
    }
    let key = request
        .headers()
        .get("idempotency-key")
        .and_then(|s| s.to_str().ok())
        .unwrap_or("")
        .to_owned();
    if method == "GET" && path.starts_with("/v1/exports/") && path.ends_with("/content") {
        let export = path
            .trim_start_matches("/v1/exports/")
            .trim_end_matches("/content")
            .to_owned();
        let relative = query.get("path").cloned().unwrap_or_default();
        let s = server.service.clone();
        return match tauri::async_runtime::spawn_blocking(move || s.export_file(&export, &relative))
            .await
        {
            Ok(Ok(bytes)) => (
                [("content-type", "application/octet-stream")],
                Body::from(bytes),
            )
                .into_response(),
            Ok(Err(e)) => response_error(e),
            Err(e) => response_error(research_service::error("worker", e.to_string())),
        };
    }
    let body = match to_bytes(request.into_body(), 1024 * 1024).await {
        Ok(b) => b,
        Err(_) => return response_error(research_service::error("body", "Request exceeds 1 MiB")),
    };
    let body = if body.is_empty() {
        json!({})
    } else {
        match serde_json::from_slice(&body) {
            Ok(v) => v,
            Err(e) => return response_error(research_service::error("json", e.to_string())),
        }
    };
    let s = server.service;
    let is_get = method == "GET";
    let is_validation = method == "POST" && path == "/v1/validate";
    let result = tauri::async_runtime::spawn_blocking(move || {
        if is_get {
            read(&s, &path, &query)
        } else if is_validation {
            s.validate_request(&body)
        } else {
            s.submit(&method, &path, &key, body)
                .and_then(research_service::value)
        }
    })
    .await;
    match result {
        Ok(Ok(v)) => (
            if is_get || is_validation {
                StatusCode::OK
            } else {
                StatusCode::ACCEPTED
            },
            Json(v),
        )
            .into_response(),
        Ok(Err(e)) => response_error(e),
        Err(e) => response_error(research_service::error("worker", e.to_string())),
    }
}

pub fn read(
    s: &ResearchService,
    path: &str,
    q: &BTreeMap<String, String>,
) -> Result<Value, AppError> {
    let parts: Vec<_> = path.trim_matches('/').split('/').collect();
    let number = |key: &str, default: u64| -> Result<u64, AppError> {
        q.get(key).map_or(Ok(default), |v| {
            v.parse().map_err(|_| {
                research_service::error("query", format!("{key} must be an unsigned integer"))
            })
        })
    };
    match parts.as_slice() {
        ["v1", "capabilities"] => Ok(
            json!({"apiVersion":1,"appVersion":env!("CARGO_PKG_VERSION"),"multiRun":true,"validation":{"path":"/v1/validate","kinds":["configuration","recipe","action"],"mutates":false},"experimentContracts":["experiments-v3","experiments-v4"],"experimentCommandExample":reservoir_core::sustained::experiment_command_example(),"configurationPhases":true,"automaticBoundaryChanges":true,"scheduledInterventions":true,"reservoirNodes":{"minimum":32,"maximum":128,"resize":"prefix-preserving-growth-v1","newNodeState":0,"sensoryDimensions":32,"textInputDimensions":48},
            "maximumPageSize":50,"cursorLifetime":"bounded-to-128-snapshots-and-process-lifetime","restartPolicy":"retain-without-automatic-dispatch","creationOnly":["seed"],"defaultConfiguration":crate::sustained::SustainedConfig::default(),"actions":["start","pause","resume","stop","retry-save","retry-writing","retry-encoding","skip-feedback","extend-limits"]}),
        ),
        ["v1", "schema"] => Ok(schema()),
        ["v1", "openapi.json"] => Ok(openapi()),
        ["v1", "runs"] => s.list_runs(),
        ["v1", "runs", run] => s.run(run),
        ["v1", "runs", run, "settings"] => s.settings(run),
        ["v1", "runs", run, "entries"] => s.entries(
            run,
            q.get("cursor").map(String::as_str),
            number("limit", 25)? as usize,
        ),
        ["v1", "runs", run, "entries", entry] => s.entry(run, entry),
        ["v1", "runs", run, "events"] => {
            s.events(run, number("after", 0)?, number("limit", 50)? as usize)
        }
        ["v1", "runs", run, "sonar"] => s.sonar(run),
        ["v1", "runs", run, "interventions"] => s.interventions(run),
        ["v1", "operations"] => research_service::value(s.operations()?),
        ["v1", "operations", op] => research_service::value(s.operation(op)?),
        ["v1", "recipes"] => s.documents("recipes"),
        ["v1", "recipes", doc] => s.document("recipes", doc),
        ["v1", "experiments"] => s.documents("experiments"),
        ["v1", "experiments", doc] => s.document("experiments", doc),
        ["v1", "settings"] => Ok(s.scheduler()),
        ["v1", "exports", export, "files"] => s.export_files(export),
        _ => Err(research_service::error("not-found", "Unknown read route")),
    }
}
pub fn schema() -> Value {
    let mut schema = serde_json::to_value(schemars::schema_for!(crate::sustained::SustainedConfig))
        .expect("schema");
    if let Some(properties) = schema["properties"].as_object_mut() {
        for (key, p) in properties {
            p["x-changePolicy"] = json!(if key == "seed" {
                "fresh-run"
            } else {
                "automatic-boundary"
            });
        }
    }
    schema["properties"]["reservoirNodes"]["minimum"] = json!(32);
    schema["properties"]["reservoirNodes"]["maximum"] = json!(128);
    schema["properties"]["reservoirNodes"]["x-changePolicy"] =
        json!("prefix-preserving-growth-at-boundary");
    schema["description"]=json!("Exact accepted configuration types. Capabilities supplies creation defaults; Rust validates cross-field constraints. Changes apply at durable turn boundaries.");
    schema
}

pub fn openapi() -> Value {
    fn reference(name: &str) -> Value {
        json!({"$ref":format!("#/components/schemas/{name}")})
    }
    fn rebase(v: &mut Value) {
        match v {
            Value::Object(m) => {
                if let Some(Value::String(r)) = m.get_mut("$ref") {
                    if let Some(name) = r.strip_prefix("#/$defs/") {
                        *r = format!("#/components/schemas/{name}");
                    }
                }
                for child in m.values_mut() {
                    rebase(child);
                }
            }
            Value::Array(a) => {
                for child in a {
                    rebase(child)
                }
            }
            _ => {}
        }
    }
    let mut config = schema();
    rebase(&mut config);
    let definitions = config
        .as_object_mut()
        .unwrap()
        .remove("$defs")
        .unwrap_or(json!({}));
    config.as_object_mut().unwrap().remove("$schema");
    let mut schemas = definitions.as_object().cloned().unwrap_or_default();
    schemas.insert("RunConfiguration".into(), config.clone());
    // Merge patches permit partial nested objects, not just partial root fields.
    fn partial(v: &mut Value) {
        match v {
            Value::Object(m) => {
                m.remove("required");
                if let Some(Value::String(r)) = m.get_mut("$ref") {
                    r.push_str("Patch");
                }
                for child in m.values_mut() {
                    partial(child);
                }
            }
            Value::Array(a) => {
                for child in a {
                    partial(child);
                }
            }
            _ => {}
        }
    }
    for (name, definition) in definitions.as_object().unwrap() {
        let mut patch = definition.clone();
        partial(&mut patch);
        schemas.insert(format!("{name}Patch"), patch);
    }
    partial(&mut config);
    schemas.insert("ConfigurationPatch".into(), config);
    schemas.insert("Operation".into(),json!({"type":"object","required":["id","status","method","path","request"],"properties":{
        "id":{"type":"string"},"status":{"enum":["queued","running","scheduled","completed","failed","cancelled","needsAttention"]},"method":{"type":"string"},"path":{"type":"string"},"request":{},"result":{},"error":{"type":["object","null"]}}}));
    schemas.insert("Error".into(),json!({"type":"object","required":["error"],"properties":{"error":{"type":"object","required":["code","message"],"properties":{"code":{"type":"string"},"message":{"type":"string"}}}}}));
    schemas.insert("SettingsChange".into(),json!({"type":"object","required":["expectedConfigurationRevision","patch"],"properties":{"expectedConfigurationRevision":{"type":"integer","minimum":0,"maximum":255},"patch":reference("ConfigurationPatch")}}));
    schemas.insert("Intervention".into(),json!({"type":"object","required":["at","kind"],"properties":{
        "at":{"oneOf":[{"type":"object","required":["step"],"additionalProperties":false,"properties":{"step":{"type":"integer","minimum":1,"maximum":10000000}}},{"type":"object","required":["activeSeconds"],"additionalProperties":false,"properties":{"activeSeconds":{"type":"integer","minimum":1,"maximum":604800}}}]},
        "kind":{"enum":["configuration","prompt"]},"patch":reference("ConfigurationPatch"),"prompt":{"type":"string","minLength":1,"maxLength":16384},"includeTelemetry":{"type":"boolean"},"expectedConfigurationRevision":{"type":"integer","minimum":0}},
        "allOf":[{"if":{"properties":{"kind":{"const":"configuration"}}},"then":{"required":["patch"]}},{"if":{"properties":{"kind":{"const":"prompt"}}},"then":{"required":["prompt","includeTelemetry"]}}],
        "description":"Executes at the first settled turn boundary at or after the requested step or active running time. Paused time does not advance activeSeconds. Restart never dispatches automatically."}));
    schemas.insert("Recipe".into(),json!({"type":"object","required":["version","arms"],"properties":{"version":{"const":1},"name":{"type":"string"},"baseConfig":reference("ConfigurationPatch"),"peerReading":{"type":"boolean","default":false},"maxConcurrentRequests":{"type":"integer","minimum":1,"maximum":16,"description":"Sets the application's shared queue limit on experiment start/resume."},"interventions":{"type":"array","items":reference("Intervention")},"arms":{"type":"array","minItems":1,"maxItems":32,"items":{"type":"object","required":["name"],"properties":{"name":{"type":"string","pattern":"^[A-Za-z0-9-]+$","maxLength":128},"overrides":reference("ConfigurationPatch"),"interventions":{"type":"array","items":reference("Intervention")}}}}}}));
    schemas.insert("Run".into(),json!({"type":"object","required":["runId","phase","step","configurationRevision","configuration"],"properties":{"runId":{"type":"string"},"generation":{"type":"string"},"revision":{"type":"string"},"phase":{"type":"string"},"savedPhase":{"type":"string"},"step":{"type":"integer"},"journalCount":{"type":"integer"},"configurationRevision":{"type":"integer"},"configuration":reference("RunConfiguration"),"snapshot":{"type":"string"},"summary":{"type":["object","null"]},"metadata":{"type":"object"}}}));
    schemas.insert("RunSettings".into(),json!({"type":"object","required":["original","configured","effective","configurationRevision","history"],"properties":{
        "original":reference("RunConfiguration"),"configured":reference("RunConfiguration"),"effective":reference("RunConfiguration"),
        "configurationRevision":{"type":"integer"},"history":{"type":"array","items":{"type":"object","properties":{
            "revision":{"type":"integer"},"step":{"type":"integer"},"operationId":{"type":"string"},"elapsedMillis":{"type":"integer"},
            "invalidated":{"type":"array","items":{"type":"string"}},"config":reference("RunConfiguration")}}}}}));
    schemas.insert("EntryIndex".into(),json!({"type":"object","required":["entryId","turnId","attemptId","observedStep","firstAppliedStep","status","textPreview","sha256","objectSha256"],"properties":{
        "entryId":{"type":"string"},"turnId":{"type":"integer"},"attemptId":{"type":"integer"},"observedStep":{"type":"integer"},
        "firstAppliedStep":{"type":["integer","null"]},"status":{"enum":["savedPendingApplication","applied","skipped"]},
        "textPreview":{"type":"string"},"sha256":{"type":"string"},"objectSha256":{"type":"string"},"actionReceipt":{"type":["object","null"]}}}));
    schemas.insert("EntryPage".into(),json!({"type":"object","required":["runId","snapshot","total","entries","nextCursor"],"properties":{
        "runId":{"type":"string"},"snapshot":{"type":"string"},"total":{"type":"integer"},"entries":{"type":"array","items":reference("EntryIndex")},
        "nextCursor":{"type":["string","null"]}}}));
    schemas.insert("JournalResult".into(),json!({"type":"object","required":["runId","snapshot","generation","revision","journal"],"properties":{
        "runId":{"type":"string"},"snapshot":{"type":"string"},"generation":{"type":"string"},"revision":{"type":"string"},
        "journal":{"type":"object","required":["entryId","text","prompt","rawReply","configurationRevision","configuration","evidence","objectSha256"],"properties":{
            "entryId":{"type":"string"},"turnId":{"type":"integer"},"attemptId":{"type":"integer"},"observedStep":{"type":"integer"},
            "firstAppliedStep":{"type":["integer","null"]},"status":{"type":"string"},"text":{"type":"string"},"prompt":{"type":"string"},
            "rawReply":{"type":"string"},"configurationRevision":{"type":"integer"},"configuration":reference("RunConfiguration"),
            "actionReceipt":{"type":["object","null"]},"evidence":{"type":"object","description":"Exact verified journal object, including the pending turn and provider outcome."},"objectSha256":{"type":"string"}}}}}));
    let mut paths = serde_json::Map::new();
    for (path, methods) in [
        ("/v1/capabilities", vec!["get"]),
        ("/v1/validate", vec!["post"]),
        ("/v1/schema", vec!["get"]),
        ("/v1/openapi.json", vec!["get"]),
        ("/v1/runs", vec!["get", "post"]),
        ("/v1/runs/{runId}", vec!["get"]),
        ("/v1/runs/{runId}/clone", vec!["post"]),
        ("/v1/runs/{runId}/settings", vec!["get", "patch"]),
        ("/v1/runs/{runId}/interventions", vec!["get", "post"]),
        ("/v1/runs/{runId}/entries", vec!["get"]),
        ("/v1/runs/{runId}/entries/{entryId}", vec!["get"]),
        ("/v1/runs/{runId}/actions/{action}", vec!["post"]),
        ("/v1/runs/{runId}/exports", vec!["post"]),
        ("/v1/runs/{runId}/events", vec!["get"]),
        ("/v1/runs/{runId}/sonar", vec!["get"]),
        ("/v1/recipes", vec!["get", "post"]),
        ("/v1/recipes/{recipeId}", vec!["get"]),
        ("/v1/experiments", vec!["get", "post"]),
        ("/v1/experiments/{experimentId}", vec!["get"]),
        (
            "/v1/experiments/{experimentId}/actions/{action}",
            vec!["post"],
        ),
        ("/v1/operations", vec!["get"]),
        ("/v1/operations/{operationId}", vec!["get"]),
        ("/v1/operations/{operationId}/cancel", vec!["post"]),
        ("/v1/settings", vec!["get", "patch"]),
        ("/v1/models/check", vec!["post"]),
        ("/v1/events", vec!["get"]),
        ("/v1/exports/{exportId}/files", vec!["get"]),
        ("/v1/exports/{exportId}/content", vec!["get"]),
    ] {
        let mut ops = serde_json::Map::new();
        for method in methods {
            let mut params = Vec::new();
            for segment in path.split('/') {
                if let Some(name) = segment.strip_prefix('{').and_then(|s| s.strip_suffix('}')) {
                    let mut parameter =
                        json!({"in":"path","name":name,"required":true,"schema":{"type":"string"}});
                    if name == "action" {
                        parameter["schema"]["enum"] = if path.contains("experiments") {
                            json!(["start", "pause", "resume", "stop"])
                        } else {
                            json!([
                                "start",
                                "pause",
                                "resume",
                                "stop",
                                "retry-save",
                                "retry-writing",
                                "retry-encoding",
                                "skip-feedback",
                                "extend-limits"
                            ])
                        };
                    }
                    params.push(parameter);
                }
            }
            if path.ends_with("/entries") {
                params.push(json!({"in":"query","name":"limit","schema":{"type":"integer","minimum":1,"maximum":50,"default":25}}));
                params.push(json!({"in":"query","name":"cursor","schema":{"type":"string"}}));
            }
            if path.ends_with("/{runId}/events") {
                params.push(json!({"in":"query","name":"after","schema":{"type":"integer","minimum":0,"default":0}}));
                params.push(json!({"in":"query","name":"limit","schema":{"type":"integer","minimum":1,"maximum":200,"default":50}}));
            }
            if path.ends_with("/content") {
                params.push(json!({"in":"query","name":"path","required":true,"schema":{"type":"string"},"description":"Exact relative path returned by the export files endpoint."}));
            }
            let result = if path == "/v1/validate" {
                json!({"type":"object","required":["valid"],"properties":{"valid":{"type":"boolean"},"issues":{"type":"array","items":{"type":"object","properties":{"path":{"type":"string"},"message":{"type":"string"}}}},"executionChecks":{"type":"string"}}})
            } else if method != "get" {
                reference("Operation")
            } else {
                match path {
                    "/v1/runs/{runId}" => reference("Run"),
                    "/v1/runs" => {
                        json!({"type":"object","properties":{"runs":{"type":"array","items":{"anyOf":[reference("Run"),{"type":"object","required":["runId","error"]}]}},"scheduler":{"type":"object"}}})
                    }
                    "/v1/runs/{runId}/settings" => reference("RunSettings"),
                    "/v1/runs/{runId}/entries" => reference("EntryPage"),
                    "/v1/runs/{runId}/entries/{entryId}" => reference("JournalResult"),
                    "/v1/operations/{operationId}" => reference("Operation"),
                    "/v1/operations" => json!({"type":"array","items":reference("Operation")}),
                    "/v1/runs/{runId}/interventions" => {
                        json!({"type":"object","properties":{"operations":{"type":"array","items":reference("Operation")}}})
                    }
                    _ => json!({"type":"object"}),
                }
            };
            let status = if method == "get" || path == "/v1/validate" {
                "200"
            } else {
                "202"
            };
            let mut responses = serde_json::Map::new();
            responses.insert(status.into(),json!({"description":if path=="/v1/validate"{"Read-only validation result"}else if method=="get"{"Saved read result"}else{"Durable operation; poll by id for completion"},"content":{"application/json":{"schema":result}}}));
            for code in ["401", "403", "404", "409", "410", "422", "429", "500"] {
                responses.insert(code.into(),json!({"description":"Structured error","content":{"application/json":{"schema":reference("Error")}}}));
            }
            if path == "/v1/events" {
                responses.insert("200".into(),json!({"description":"Pull-driven full replacement snapshots; reconnect starts with resync:true","content":{"text/event-stream":{"schema":{"type":"string"}}}}));
            }
            if path.ends_with("/content") {
                responses.insert("200".into(),json!({"description":"Exact verified export file","content":{"application/octet-stream":{"schema":{"type":"string","format":"binary"}}}}));
            }
            let mut op = json!({"parameters":params,"responses":responses});
            if method != "get" {
                if path != "/v1/validate" {
                    op["parameters"].as_array_mut().unwrap().push(json!({"in":"header","name":"Idempotency-Key","required":true,"schema":{"type":"string","minLength":1,"maxLength":128}}));
                }
                let body = match path {
                    "/v1/validate" => {
                        json!({"type":"object","required":["kind"],"properties":{"kind":{"enum":["configuration","recipe","action"]},"runId":{"type":"string"},"config":reference("ConfigurationPatch"),"recipe":reference("Recipe"),"text":{"type":"string","maxLength":65536}},"description":"Read-only preflight; returns valid:false with issues for invalid input. Never creates operations or calls models."})
                    }
                    "/v1/runs" => {
                        json!({"type":"object","properties":{"config":reference("ConfigurationPatch"),"metadata":{"type":"object"}}})
                    }
                    "/v1/runs/{runId}/clone" => {
                        json!({"type":"object","properties":{"overrides":reference("ConfigurationPatch")}})
                    }
                    "/v1/runs/{runId}/settings" => reference("SettingsChange"),
                    "/v1/runs/{runId}/interventions" => reference("Intervention"),
                    "/v1/recipes" => reference("Recipe"),
                    "/v1/experiments" => {
                        json!({"anyOf":[reference("Recipe"),{"type":"object","required":["recipeId"],"properties":{"recipeId":{"type":"string"}}}]})
                    }
                    "/v1/settings" => {
                        json!({"type":"object","required":["maxConcurrentRequests"],"properties":{"maxConcurrentRequests":{"type":"integer","minimum":1,"maximum":16}}})
                    }
                    "/v1/models/check" => reference("LanguageConfiguration"),
                    _ => {
                        json!({"type":"object","properties":{"generation":{"type":"string"},"entryId":{"type":"string"},"attemptId":{"type":"integer"},"maximumSteps":{"type":"integer"},"maximumTurns":{"type":"integer"},"maximumDurationSeconds":{"type":"integer"}},"description":"extend-limits requires all three maximum fields; skip-feedback identifies the retained entryId or attemptId."})
                    }
                };
                op["requestBody"] =
                    json!({"required":false,"content":{"application/json":{"schema":body}}});
            }
            ops.insert(method.into(), op);
        }
        paths.insert(path.into(), Value::Object(ops));
    }
    json!({"openapi":"3.1.0","info":{"title":"Reservoir Scope Research API","version":"1.0.0"},"security":[{"localToken":[]}],"components":{"securitySchemes":{"localToken":{"type":"http","scheme":"bearer"}},"schemas":schemas},"paths":paths})
}

#[tauri::command]
pub async fn research_request(
    service: tauri::State<'_, ResearchService>,
    method: String,
    path: String,
    body: Option<Value>,
    idempotency_key: Option<String>,
) -> Result<Value, AppError> {
    let s = service.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        if method == "GET" {
            let url = tauri::Url::parse(&format!("http://localhost{path}"))
                .map_err(|e| research_service::error("path", e.to_string()))?;
            read(&s, url.path(), &url.query_pairs().into_owned().collect())
        } else if method == "POST" && path == "/v1/validate" {
            s.validate_request(&body.unwrap_or(json!({})))
        } else {
            s.submit(
                &method,
                &path,
                idempotency_key.as_deref().unwrap_or(""),
                body.unwrap_or(json!({})),
            )
            .and_then(research_service::value)
        }
    })
    .await
    .map_err(|e| research_service::error("worker", e.to_string()))?
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn authenticated_http_contract_and_schema_references() {
        let dir = tempfile::tempdir().unwrap();
        let service = ResearchService::new(
            dir.path().into(),
            crate::sustained::SustainedState::new(dir.path().join("sustained-v1")),
        )
        .unwrap();
        let server = start(service.clone(), "test").unwrap();
        let descriptor: Value = serde_json::from_slice(
            &fs::read(service.discovery_directory().join("endpoint.json")).unwrap(),
        )
        .unwrap();
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            assert_eq!(
                fs::metadata(service.discovery_directory().join("endpoint.json"))
                    .unwrap()
                    .permissions()
                    .mode()
                    & 0o777,
                0o600
            );
        }
        let token = descriptor["token"].as_str().unwrap().to_owned();
        tauri::async_runtime::block_on(async {
            let c = reqwest::Client::builder().no_proxy().build().unwrap();
            let url = format!("{}/v1/capabilities", server.address);
            assert_eq!(c.get(&url).send().await.unwrap().status(), 401);
            assert_eq!(
                c.get(&url)
                    .bearer_auth(&token)
                    .header("Origin", "https://example.org")
                    .send()
                    .await
                    .unwrap()
                    .status(),
                403
            );
            assert_eq!(
                c.get(&url)
                    .bearer_auth(&token)
                    .header("Host", "example.org")
                    .send()
                    .await
                    .unwrap()
                    .status(),
                403
            );
            let cap: Value = c
                .get(&url)
                .bearer_auth(&token)
                .send()
                .await
                .unwrap()
                .json()
                .await
                .unwrap();
            assert_eq!(cap["scheduledInterventions"], true);
            let validation = c
                .post(format!("{}/v1/validate", server.address))
                .bearer_auth(&token)
                .json(&json!({"kind":"configuration","config":{"reservoirNodes":129}}))
                .send()
                .await
                .unwrap();
            assert_eq!(validation.status(), 200);
            assert_eq!(validation.json::<Value>().await.unwrap()["valid"], false);
            assert!(service.operations().unwrap().is_empty());
            let url = format!("{}/v1/runs", server.address);
            assert_eq!(
                c.post(&url)
                    .bearer_auth(&token)
                    .json(&json!({}))
                    .send()
                    .await
                    .unwrap()
                    .status(),
                422
            );
            let a: Value = c
                .post(&url)
                .bearer_auth(&token)
                .header("Idempotency-Key", "create-once")
                .json(&json!({}))
                .send()
                .await
                .unwrap()
                .json()
                .await
                .unwrap();
            let b: Value = c
                .post(&url)
                .bearer_auth(&token)
                .header("Idempotency-Key", "create-once")
                .json(&json!({}))
                .send()
                .await
                .unwrap()
                .json()
                .await
                .unwrap();
            assert_eq!(a["id"], b["id"]);
            assert_eq!(
                c.post(&url)
                    .bearer_auth(&token)
                    .header("Idempotency-Key", "create-once")
                    .json(&json!({"config":{"leak":0.2}}))
                    .send()
                    .await
                    .unwrap()
                    .status(),
                409
            );
            assert_eq!(
                c.post(&url)
                    .bearer_auth(&token)
                    .header("Idempotency-Key", "too-large")
                    .body(vec![b'a'; 1024 * 1024 + 1])
                    .send()
                    .await
                    .unwrap()
                    .status(),
                422
            );
        });
        let spec = openapi();
        fn refs(root: &Value, v: &Value) {
            match v {
                Value::Object(m) => {
                    if let Some(Value::String(r)) = m.get("$ref") {
                        assert!(
                            root.pointer(r.trim_start_matches('#')).is_some(),
                            "unresolved {r}"
                        );
                    }
                    for v in m.values() {
                        refs(root, v);
                    }
                }
                Value::Array(a) => {
                    for v in a {
                        refs(root, v)
                    }
                }
                _ => {}
            }
        }
        refs(&spec, &spec);
        let schedule_patch = &spec["components"]["schemas"]["SustainedCheckInSchedulePatch"];
        assert!(schedule_patch.is_object());
        assert!(
            schedule_patch.get("required").is_none(),
            "A prompt-only schedule patch is valid"
        );
        assert_eq!(
            spec["paths"]["/v1/runs/{runId}/entries/{entryId}"]["get"]["responses"]["200"]
                ["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/JournalResult"
        );
        assert!(spec["paths"]["/v1/runs/{runId}/interventions"]["post"]["requestBody"].is_object());
        drop(server);
        assert!(!service.discovery_directory().join("endpoint.json").exists());
    }
}

#[tauri::command]
pub fn research_close(app: tauri::AppHandle) -> bool {
    if !crate::request_session_close(&app) {
        app.exit(0);
        true
    } else {
        false
    }
}
