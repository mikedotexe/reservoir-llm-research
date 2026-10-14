//! Cooperative AppKit termination must consult the same session guard as Tauri.
//!
//! Tao 0.37.1 implements `applicationWillTerminate:` but not the earlier veto.
//! `NSApplication.terminate:` can therefore bypass Tauri's `ExitRequested` event.
//! Install one method on a no-ivar subclass of the *actual* application delegate,
//! preserving Tao's delegate object, state, inherited methods, and ownership.
//! This does not intercept force quit, signals, crashes, or power loss.

use objc2::{
    msg_send,
    rc::Retained,
    runtime::{AnyClass, AnyObject, ClassBuilder, Sel},
    sel, MainThreadMarker,
};
use std::{ffi::CStr, io, panic::AssertUnwindSafe, sync::OnceLock};

static APP: OnceLock<tauri::AppHandle> = OnceLock::new();

// NSApplicationTerminateReply is NSUInteger: Cancel=0, Now=1. Keep the exact
// unsigned pointer-sized ABI; a Rust bool would have the wrong method encoding.
extern "C" fn application_should_terminate(
    _delegate: &AnyObject,
    _selector: Sel,
    _application: *mut AnyObject,
) -> usize {
    // No Rust panic may unwind through Objective-C. Missing setup or an unexpected
    // callback thread also refuses termination rather than losing unsaved work.
    let review = std::panic::catch_unwind(AssertUnwindSafe(|| {
        if MainThreadMarker::new().is_none() {
            return true;
        }
        APP.get().is_none_or(super::request_session_close)
    }))
    .unwrap_or(true);
    usize::from(!review)
}

fn delegate_subclass(original: &AnyClass, name: &CStr) -> io::Result<&'static AnyClass> {
    if original
        .instance_method(sel!(applicationShouldTerminate:))
        .is_some()
    {
        return Err(io::Error::other(
            "Application delegate already implements a termination policy; review the macOS session guard before starting.",
        ));
    }
    let mut builder = ClassBuilder::new(name, original).ok_or_else(|| {
        io::Error::other("Could not allocate the macOS session termination delegate subclass.")
    })?;
    // SAFETY: This exactly matches AppKit's optional delegate method:
    // -(NSUInteger)applicationShouldTerminate:(NSApplication *)sender.
    // We add no ivars and override no existing method. Inherited Tao callbacks
    // continue receiving the original object and its unchanged ivar layout.
    unsafe {
        builder.add_method(
            sel!(applicationShouldTerminate:),
            application_should_terminate as extern "C" fn(_, _, _) -> _,
        );
    }
    let subclass = builder.register();
    if subclass.superclass() != Some(original)
        || subclass.instance_size() != original.instance_size()
    {
        return Err(io::Error::other(
            "Incompatible macOS termination delegate layout; refusing unguarded startup.",
        ));
    }
    Ok(subclass)
}

/// Call once from Tauri's main-thread setup, after managing SessionState.
pub fn install(app: &tauri::AppHandle) -> io::Result<()> {
    let _main = MainThreadMarker::new()
        .ok_or_else(|| io::Error::other("macOS termination guard requires main-thread setup."))?;
    if APP.get().is_some() {
        return Err(io::Error::other(
            "macOS termination guard was already installed.",
        ));
    }
    let application_class = AnyClass::get(c"NSApplication")
        .ok_or_else(|| io::Error::other("NSApplication is unavailable."))?;
    // SAFETY: AppKit is linked by Tauri. These are the documented NSApplication
    // singleton/delegate accessors, called only on the main thread. Retain the
    // delegate across its temporary removal below; NSApplication's delegate
    // property does not transfer ownership to us.
    let (application, delegate) = unsafe {
        let application: *mut AnyObject = msg_send![application_class, sharedApplication];
        if application.is_null() {
            return Err(io::Error::other("NSApplication singleton is unavailable."));
        }
        let delegate: *mut AnyObject = msg_send![application, delegate];
        let delegate = Retained::retain(delegate)
            .ok_or_else(|| io::Error::other("NSApplication has no delegate to guard."))?;
        (application, delegate)
    };
    let original = delegate.class();
    // The currently pinned Tao delegate must retain these inherited lifecycle
    // methods. Do not depend on Tao's private runtime class name.
    if original
        .instance_method(sel!(applicationWillTerminate:))
        .is_none()
        || original
            .instance_method(sel!(applicationDidFinishLaunching:))
            .is_none()
    {
        return Err(io::Error::other(
            "Unexpected application delegate lifecycle; refusing unguarded startup.",
        ));
    }
    let subclass = delegate_subclass(original, c"ReservoirScopeSessionTerminationDelegateV1")?;
    APP.set(app.clone())
        .map_err(|_| io::Error::other("Concurrent macOS termination guard installation."))?;
    // SAFETY: Installation occurs once on the main thread before user commands.
    // This is an immediate subclass of the object's current class, with exactly
    // the same instance size and no new ivars, as checked above. No method is
    // overridden. The delegate remains retained throughout and Tao keeps its
    // existing ownership. No other code in this app mutates the delegate class.
    let previous = unsafe { AnyObject::set_class(&delegate, subclass) };
    assert_eq!(
        previous, original,
        "Application delegate class changed during installation"
    );
    // Refresh AppKit's optional-delegate-method bookkeeping after changing the
    // object's class. Restore the exact same retained delegate immediately.
    // SAFETY: Both messages use the documented nullable object argument ABI,
    // on the main thread, while the delegate is strongly retained locally.
    unsafe {
        let _: () = msg_send![application, setDelegate: std::ptr::null::<AnyObject>()];
        let _: () = msg_send![application, setDelegate: &*delegate];
        let installed: *mut AnyObject = msg_send![application, delegate];
        if installed != (&*delegate as *const AnyObject).cast_mut() || delegate.class() != subclass
        {
            return Err(io::Error::other(
                "macOS termination guard did not remain installed; refusing startup.",
            ));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use objc2::{runtime::NSObject, ClassType};

    #[test]
    fn subclass_preserves_layout_and_inherited_methods() {
        let base = NSObject::class();
        let subclass = delegate_subclass(base, c"ReservoirScopeTerminationLayoutTest").unwrap();
        assert_eq!(subclass.superclass(), Some(base));
        assert_eq!(subclass.instance_size(), base.instance_size());
        assert_eq!(
            subclass.instance_method(sel!(description)),
            base.instance_method(sel!(description))
        );
        assert!(subclass
            .instance_method(sel!(applicationShouldTerminate:))
            .is_some());
        assert!(
            delegate_subclass(subclass, c"ReservoirScopeTerminationPolicyClobberTest").is_err()
        );
    }

    #[test]
    fn uninitialized_callback_refuses_termination() {
        let object = NSObject::new();
        assert_eq!(
            application_should_terminate(
                &object,
                sel!(applicationShouldTerminate:),
                std::ptr::null_mut()
            ),
            0
        );
    }
}
