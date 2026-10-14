//! Mark only the lifetime of an explicitly started run as user-requested work.
//! This lets a minimized Mac app avoid App Nap while preserving system sleep.
use crate::files::AppError;

#[cfg(target_os = "macos")]
mod platform {
    use super::AppError;
    use objc2::{
        msg_send,
        rc::Retained,
        runtime::{AnyClass, AnyObject},
    };

    // NSActivityOptions is uint64_t. Foundation's public constant is
    // NSActivityUserInitiated & ~NSActivityIdleSystemSleepDisabled.
    const OPTIONS: u64 = 0x00ff_ffff & !(1 << 20);
    pub struct RunActivity {
        process: Retained<AnyObject>,
        token: Retained<AnyObject>,
    }
    impl RunActivity {
        pub fn begin() -> Result<Self, AppError> {
            objc2::rc::autoreleasepool(|_| {
                let error = || {
                    AppError::new(
                        "start-sustained",
                        "activity",
                        "Could not register this user-requested run with macOS.",
                    )
                };
                let process_class = AnyClass::get(c"NSProcessInfo").ok_or_else(error)?;
                let string_class = AnyClass::get(c"NSString").ok_or_else(error)?;
                // SAFETY: Foundation provides these documented thread-safe object
                // accessors/activity methods. Retain non-owned results; the reason
                // uses a static NUL-terminated UTF-8 string and an owned NSString.
                unsafe {
                    let process: *mut AnyObject = msg_send![process_class, processInfo];
                    let process = Retained::retain(process).ok_or_else(error)?;
                    let reason: *mut AnyObject = msg_send![string_class, alloc];
                    let reason: *mut AnyObject = msg_send![reason, initWithUTF8String: c"Running the explicitly started reservoir and saving its journals".as_ptr()];
                    let reason = Retained::from_raw(reason).ok_or_else(error)?;
                    let token: *mut AnyObject =
                        msg_send![&*process, beginActivityWithOptions: OPTIONS, reason: &*reason];
                    let token = Retained::retain(token).ok_or_else(error)?;
                    Ok(Self { process, token })
                }
            })
        }
    }
    impl Drop for RunActivity {
        fn drop(&mut self) {
            // SAFETY: End exactly the activity started above while both its
            // process object and token remain retained. Never alter other apps.
            unsafe {
                let _: () = msg_send![&*self.process, endActivity: &*self.token];
            }
        }
    }
    #[cfg(test)]
    mod tests {
        use super::*;
        #[test]
        fn user_activity_preserves_system_and_display_sleep() {
            assert_eq!(OPTIONS & ((1 << 20) | (1 << 40)), 0);
            objc2::rc::autoreleasepool(|_| {
                drop(RunActivity::begin().unwrap());
            });
        }
    }
}
#[cfg(target_os = "macos")]
pub use platform::RunActivity;

#[cfg(not(target_os = "macos"))]
pub struct RunActivity;
#[cfg(not(target_os = "macos"))]
impl RunActivity {
    pub fn begin() -> Result<Self, AppError> {
        Ok(Self)
    }
}
