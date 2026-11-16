use std::sync::Mutex;
use tauri::{Emitter, Manager};
use tauri_plugin_deep_link::DeepLinkExt;

#[derive(Default)]
pub struct LinkState(Mutex<Option<String>>);
pub fn parse(raw: &str) -> Option<String> {
    if raw.len() > 2048 {
        return None;
    }
    let u = tauri::Url::parse(raw).ok()?;
    if !matches!(u.scheme(), "reservoirscope" | "reservoirscope-dev")
        || u.host_str() != Some("v1")
        || !u.username().is_empty()
        || u.password().is_some()
        || u.port().is_some()
        || u.query().is_some()
        || u.fragment().is_some()
    {
        return None;
    }
    let p: Vec<_> = u.path().trim_matches('/').split('/').collect();
    let valid = |s: &str| crate::sustained_store::valid_id(s);
    match p.as_slice() {
        ["runs", run] if valid(run) => Some(format!("/v1/runs/{run}")),
        ["runs", run, "entries", entry] if valid(run) && valid(entry) => {
            Some(format!("/v1/runs/{run}/entries/{entry}"))
        }
        ["experiments", experiment] if valid(experiment) => {
            Some(format!("/v1/experiments/{experiment}"))
        }
        ["settings"] => Some("/v1/settings".into()),
        _ => None,
    }
}
pub fn install(app: &tauri::AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    app.manage(LinkState::default());
    let receive = |app: &tauri::AppHandle, urls: Vec<tauri::Url>| {
        for url in urls {
            if let Some(route) = parse(url.as_str()) {
                *app.state::<LinkState>().0.lock().unwrap() = Some(route.clone());
                let _ = app.emit("research-deep-link", route);
                if let Some(w) = app.get_webview_window("main") {
                    let _ = w.show();
                    let _ = w.set_focus();
                }
            }
        }
    };
    let handle = app.clone();
    app.deep_link()
        .on_open_url(move |e| receive(&handle, e.urls()));
    if let Some(urls) = app.deep_link().get_current()? {
        receive(app, urls);
    }
    Ok(())
}
#[tauri::command]
pub fn research_deep_link(state: tauri::State<'_, LinkState>) -> Option<String> {
    state.0.lock().ok()?.take()
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn navigation_only() {
        assert_eq!(
            parse("reservoirscope://v1/runs/run-1/entries/journal-2"),
            Some("/v1/runs/run-1/entries/journal-2".into())
        );
        for s in [
            "reservoirscope://v1/runs/run-1/actions/start",
            "reservoirscope://v1/settings?token=secret",
            "reservoirscope://v1/runs/a%2Fb",
            "https://v1/settings",
            "reservoirscope://evil/v1/settings",
        ] {
            assert_eq!(parse(s), None);
        }
    }
}
