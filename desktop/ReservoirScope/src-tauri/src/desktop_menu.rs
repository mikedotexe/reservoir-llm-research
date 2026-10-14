//! Quit is an application command, not AppKit's direct `terminate:` menu role.
//! The latter bypasses Tauri's ExitRequested callback in the pinned macOS runtime.
use tauri::menu::{AboutMetadata, Menu, MenuItem, PredefinedMenuItem, Submenu};

pub const QUIT: &str = "scope-review-and-quit";

pub fn build(app: &tauri::AppHandle) -> tauri::Result<Menu<tauri::Wry>> {
    let quit = MenuItem::with_id(
        app,
        QUIT,
        "Quit Reservoir Scope Tauri Preview",
        true,
        Some("CmdOrCtrl+Q"),
    )?;
    let about = AboutMetadata {
        name: Some("Reservoir Scope Tauri Preview".into()),
        version: Some(app.package_info().version.to_string()),
        ..Default::default()
    };
    let menu = Menu::new(app)?;
    #[cfg(target_os = "macos")]
    menu.append(&Submenu::with_items(
        app,
        "Reservoir Scope Tauri Preview",
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
        menu.append(&Submenu::with_items(
            app,
            "View",
            true,
            &[&PredefinedMenuItem::fullscreen(app, None)?],
        )?)?;
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
