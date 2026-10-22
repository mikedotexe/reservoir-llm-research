//! Quit is an application command, not AppKit's direct `terminate:` menu role.
//! The latter bypasses Tauri's ExitRequested callback in the pinned macOS runtime.
use tauri::menu::{AboutMetadata, Menu, MenuItem, PredefinedMenuItem, Submenu};
use tauri::Manager;
use tauri_plugin_dialog::{DialogExt, MessageDialogKind};

pub const QUIT: &str = "scope-review-and-quit";
const ZOOM_IN: &str = "scope-zoom-in";
const ZOOM_OUT: &str = "scope-zoom-out";
const ACTUAL_SIZE: &str = "scope-actual-size";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum ZoomCommand {
    In,
    Out,
    ActualSize,
}

impl ZoomCommand {
    fn from_id(id: &str) -> Option<Self> {
        match id {
            ZOOM_IN => Some(Self::In),
            ZOOM_OUT => Some(Self::Out),
            ACTUAL_SIZE => Some(Self::ActualSize),
            _ => None,
        }
    }
}

// Only the main webview uses this process-local state. It is not a preference or
// recording field. Tauri reports dispatch errors; lower-level platform errors are
// logged by its runtime, so this tracks the last accepted request, not a readback.
#[derive(Default)]
pub struct MainWindowZoom(std::sync::Mutex<ZoomLevel>);

struct ZoomLevel(u16);

impl Default for ZoomLevel {
    fn default() -> Self {
        Self(100)
    }
}

impl ZoomLevel {
    fn request<E>(
        &mut self,
        command: ZoomCommand,
        apply: impl FnOnce(f64) -> Result<(), E>,
    ) -> Result<(), E> {
        let next = match command {
            ZoomCommand::In => self.0.saturating_add(25).min(200),
            ZoomCommand::Out => self.0.saturating_sub(25).max(75),
            ZoomCommand::ActualSize => 100,
        };
        if next == self.0 && command != ZoomCommand::ActualSize {
            return Ok(());
        }
        apply(f64::from(next) / 100.0)?;
        self.0 = next;
        Ok(())
    }
}

pub fn handle_zoom(app: &tauri::AppHandle, id: &str) {
    let Some(command) = ZoomCommand::from_id(id) else {
        return;
    };
    let result = (|| {
        let window = app
            .get_webview_window("main")
            .ok_or_else(|| "The main window is unavailable.".to_string())?;
        let state = app.state::<MainWindowZoom>();
        let mut level = state
            .0
            .lock()
            .map_err(|_| "The zoom controls are unavailable.".to_string())?;
        level
            .request(command, |factor| window.set_zoom(factor))
            .map_err(|error| error.to_string())
    })();
    if let Err(error) = result {
        eprintln!("Could not change main-window zoom: {error}");
        let dialog = app
            .dialog()
            .message(format!("The zoom request could not be applied.\n\n{error}"))
            .title("Could not change zoom")
            .kind(MessageDialogKind::Error);
        let dialog = if let Some(window) = app.get_webview_window("main") {
            dialog.parent(&window)
        } else {
            dialog
        };
        dialog.show(|_| {});
    }
}

pub fn build(app: &tauri::AppHandle) -> tauri::Result<Menu<tauri::Wry>> {
    let quit = MenuItem::with_id(
        app,
        QUIT,
        "Quit Reservoir Scope Tauri",
        true,
        Some("CmdOrCtrl+Q"),
    )?;
    let about = AboutMetadata {
        name: Some("Reservoir Scope Tauri".into()),
        version: Some(app.package_info().version.to_string()),
        ..Default::default()
    };
    let menu = Menu::new(app)?;
    #[cfg(target_os = "macos")]
    menu.append(&Submenu::with_items(
        app,
        "Reservoir Scope Tauri",
        true,
        &[
            &PredefinedMenuItem::about(app, None, Some(about))?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::services(app, None)?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::hide(app, None)?,
            &PredefinedMenuItem::hide_others(app, None)?,
            &PredefinedMenuItem::show_all(app, None)?,
            &PredefinedMenuItem::separator(app)?,
            &quit,
        ],
    )?)?;
    let file = Submenu::with_items(
        app,
        "File",
        true,
        &[&PredefinedMenuItem::close_window(app, None)?],
    )?;
    #[cfg(not(target_os = "macos"))]
    file.append(&quit)?;
    menu.append(&file)?;
    menu.append(&Submenu::with_items(
        app,
        "Edit",
        true,
        &[
            &PredefinedMenuItem::undo(app, None)?,
            &PredefinedMenuItem::redo(app, None)?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::cut(app, None)?,
            &PredefinedMenuItem::copy(app, None)?,
            &PredefinedMenuItem::paste(app, None)?,
            &PredefinedMenuItem::select_all(app, None)?,
        ],
    )?)?;
    let view = Submenu::with_items(
        app,
        "View",
        true,
        &[
            &MenuItem::with_id(app, ZOOM_IN, "Zoom In", true, Some("CmdOrCtrl+Shift+Equal"))?,
            &MenuItem::with_id(app, ZOOM_OUT, "Zoom Out", true, Some("CmdOrCtrl+Minus"))?,
            &MenuItem::with_id(app, ACTUAL_SIZE, "Actual Size", true, Some("CmdOrCtrl+0"))?,
        ],
    )?;
    #[cfg(target_os = "macos")]
    {
        view.append(&PredefinedMenuItem::separator(app)?)?;
        view.append(&PredefinedMenuItem::fullscreen(app, None)?)?;
    }
    menu.append(&view)?;
    let window = Submenu::with_items(
        app,
        "Window",
        true,
        &[
            &PredefinedMenuItem::minimize(app, None)?,
            &PredefinedMenuItem::maximize(app, None)?,
            &PredefinedMenuItem::close_window(app, None)?,
        ],
    )?;
    #[cfg(target_os = "macos")]
    {
        window.set_as_windows_menu_for_nsapp()?;
    }
    menu.append(&window)?;
    let help = Submenu::new(app, "Help", true)?;
    #[cfg(not(target_os = "macos"))]
    help.append(&PredefinedMenuItem::about(app, None, Some(about))?)?;
    #[cfg(target_os = "macos")]
    help.set_as_help_menu_for_nsapp()?;
    menu.append(&help)?;
    Ok(menu)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zoom_is_bounded_and_repeated_limits_do_not_dispatch() {
        let mut level = ZoomLevel::default();
        let mut requested = Vec::new();
        for command in [ZoomCommand::In; 20]
            .into_iter()
            .chain([ZoomCommand::Out; 20])
        {
            level
                .request(command, |factor| {
                    requested.push(factor);
                    Ok::<_, ()>(())
                })
                .unwrap();
        }
        assert_eq!(
            requested,
            [1.25, 1.5, 1.75, 2.0, 1.75, 1.5, 1.25, 1.0, 0.75]
        );
        assert_eq!(level.0, 75);
    }

    #[test]
    fn failed_request_preserves_previous_level_for_next_command() {
        let mut level = ZoomLevel::default();
        assert_eq!(
            level.request(ZoomCommand::In, |_| Err("dispatch")),
            Err("dispatch")
        );
        assert_eq!(level.0, 100);
        level
            .request(ZoomCommand::In, |factor| {
                assert_eq!(factor, 1.25);
                Ok::<_, ()>(())
            })
            .unwrap();
        assert_eq!(level.0, 125);
        assert_eq!(
            level.request(ZoomCommand::ActualSize, |_| Err("reset")),
            Err("reset")
        );
        assert_eq!(level.0, 125);
    }

    #[test]
    fn actual_size_always_requests_one_and_other_state_is_independent() {
        let mut first = ZoomLevel::default();
        let second = ZoomLevel::default();
        first.request(ZoomCommand::In, |_| Ok::<_, ()>(())).unwrap();
        assert_eq!(second.0, 100);
        for _ in 0..2 {
            let mut called = false;
            first
                .request(ZoomCommand::ActualSize, |factor| {
                    called = true;
                    assert_eq!(factor, 1.0);
                    Ok::<_, ()>(())
                })
                .unwrap();
            assert!(called);
            assert_eq!(first.0, 100);
        }
    }

    #[test]
    fn quit_and_other_menu_actions_are_not_zoom_commands() {
        assert_eq!(ZoomCommand::from_id(QUIT), None);
        assert_eq!(ZoomCommand::from_id("unknown"), None);
        assert_eq!(ZoomCommand::from_id(ZOOM_IN), Some(ZoomCommand::In));
        assert_eq!(ZoomCommand::from_id(ZOOM_OUT), Some(ZoomCommand::Out));
        assert_eq!(
            ZoomCommand::from_id(ACTUAL_SIZE),
            Some(ZoomCommand::ActualSize)
        );
    }
}
