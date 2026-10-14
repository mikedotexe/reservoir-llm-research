//! Actual workspace sleep/wake notifications, independent of window visibility.
//! A minimized window is allowed to run; a system interruption requires resume.
use objc2::{
    msg_send,
    rc::Retained,
    runtime::{AnyClass, AnyObject, ClassBuilder, Sel},
    sel, MainThreadMarker,
};
use std::{cell::RefCell, io, panic::AssertUnwindSafe, sync::OnceLock};

type Callback = Box<dyn Fn(&str) + Send + Sync>;
static CALLBACK: OnceLock<Callback> = OnceLock::new();
thread_local! {
    // Notification-center selector observers do not own their observer. Retain
    // this one for the main thread's lifetime, matching application lifetime.
    static OBSERVER: RefCell<Option<Retained<AnyObject>>> = const { RefCell::new(None) };
}

#[link(name = "AppKit", kind = "framework")]
unsafe extern "C" {
    static NSWorkspaceWillSleepNotification: *const AnyObject;
    static NSWorkspaceDidWakeNotification: *const AnyObject;
}

fn deliver(reason: &str) {
    // Never unwind through AppKit's Objective-C callback boundary.
    let _ = std::panic::catch_unwind(AssertUnwindSafe(|| {
        if let Some(callback) = CALLBACK.get() {
            callback(reason);
        }
    }));
}
extern "C" fn will_sleep(_: &AnyObject, _: Sel, _: *mut AnyObject) {
    deliver("macOS reported system sleep. Resume explicitly after waking; no missed steps are simulated.");
}
extern "C" fn did_wake(_: &AnyObject, _: Sel, _: *mut AnyObject) {
    deliver("macOS reported system wake. Inspect the retained boundary and resume explicitly.");
}

/// Install once during main-thread setup. The callback must cancel scheduling
/// promptly; persistence belongs to the session owner, never a WebView timer.
pub fn install(callback: impl Fn(&str) + Send + Sync + 'static) -> io::Result<()> {
    let _main = MainThreadMarker::new()
        .ok_or_else(|| io::Error::other("Sleep notifications require main-thread setup."))?;
    if CALLBACK.get().is_some() {
        return Err(io::Error::other(
            "Sleep notification adapter already installed.",
        ));
    }
    let base =
        AnyClass::get(c"NSObject").ok_or_else(|| io::Error::other("NSObject is unavailable."))?;
    let workspace_class = AnyClass::get(c"NSWorkspace")
        .ok_or_else(|| io::Error::other("NSWorkspace is unavailable."))?;
    let mut builder = ClassBuilder::new(c"ReservoirScopeSleepObserverV1", base)
        .ok_or_else(|| io::Error::other("Could not allocate sleep observer."))?;
    // SAFETY: Both methods have NotificationCenter's required void method ABI
    // with one nullable object argument; the new NSObject subclass has no ivars.
    unsafe {
        builder.add_method(sel!(scopeWillSleep:), will_sleep as extern "C" fn(_, _, _));
        builder.add_method(sel!(scopeDidWake:), did_wake as extern "C" fn(_, _, _));
    }
    let observer_class = builder.register();
    // SAFETY: AppKit is already initialized on its main thread. `new` returns
    // an owned NSObject, and sharedWorkspace/notificationCenter are documented
    // non-owning object accessors. Use NSWorkspace's center, not defaultCenter.
    let (observer, center) = unsafe {
        let observer: *mut AnyObject = msg_send![observer_class, new];
        let observer = Retained::from_raw(observer)
            .ok_or_else(|| io::Error::other("Could not create sleep observer."))?;
        let workspace: *mut AnyObject = msg_send![workspace_class, sharedWorkspace];
        if workspace.is_null() {
            return Err(io::Error::other("NSWorkspace singleton is unavailable."));
        }
        let center: *mut AnyObject = msg_send![workspace, notificationCenter];
        if center.is_null() {
            return Err(io::Error::other(
                "Workspace notification center is unavailable.",
            ));
        }
        (observer, center)
    };
    CALLBACK
        .set(Box::new(callback))
        .map_err(|_| io::Error::other("Concurrent sleep notification adapter installation."))?;
    // SAFETY: Constants are AppKit-owned NSString notification names. The live
    // retained observer implements both selectors; nil accepts this workspace's
    // notifications regardless of sender. No remote notification is registered.
    unsafe {
        let _: () = msg_send![center, addObserver: &*observer, selector: sel!(scopeWillSleep:), name: NSWorkspaceWillSleepNotification, object: std::ptr::null::<AnyObject>()];
        let _: () = msg_send![center, addObserver: &*observer, selector: sel!(scopeDidWake:), name: NSWorkspaceDidWakeNotification, object: std::ptr::null::<AnyObject>()];
    }
    OBSERVER.with(|slot| *slot.borrow_mut() = Some(observer));
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn callbacks_are_safe_before_installation() {
        let object = objc2::runtime::NSObject::new();
        will_sleep(&object, sel!(scopeWillSleep:), std::ptr::null_mut());
        did_wake(&object, sel!(scopeDidWake:), std::ptr::null_mut());
    }
}
