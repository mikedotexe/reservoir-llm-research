//! Serialize user admission across the finite lab and the sustained lab. Each
//! owner still owns its worker; this gate prevents simultaneous independent runs.
use crate::{files::AppError, sessions::SessionState, sustained::SustainedState};
use std::sync::Mutex;
use tauri::Manager;

#[derive(Default)]
pub struct ExecutionAdmission(pub Mutex<()>, pub CloseCoordinator);

/// This separate, short gate never covers persistence, provider calls or waiting
/// for execution admission. Return and the final exit decision linearize here.
#[derive(Default)]
pub struct CloseCoordinator(Mutex<CloseState>);

#[derive(Default)]
pub struct CloseState {
    epoch: u64,
    pub committed: bool,
    pub deferred: bool,
}

impl CloseCoordinator {
    pub fn epoch(&self) -> u64 {
        self.0.lock().unwrap_or_else(|e| e.into_inner()).epoch
    }

    pub fn current<T>(
        &self,
        expected: u64,
        action: impl FnOnce(&mut CloseState) -> T,
    ) -> Option<T> {
        let mut state = self.0.lock().unwrap_or_else(|e| e.into_inner());
        (state.epoch == expected).then(|| action(&mut state))
    }

    pub fn cancel(&self, reopen: impl FnOnce()) -> bool {
        let mut state = self.0.lock().unwrap_or_else(|e| e.into_inner());
        if state.committed {
            // Exit has already been atomically authorized. A later command must
            // not reopen either owner between that decision and process exit.
            return false;
        }
        state.epoch = state.epoch.wrapping_add(1);
        state.deferred = false;
        reopen();
        true
    }

    /// A slow owner finish can complete after Return. It may retain a stopped
    /// checkpoint, but its provisional command gates must not strand the app or
    /// authorize an exit in a later epoch. Run immediately after the slow work.
    pub fn settled(&self, expected: u64, reopen: impl FnOnce()) -> bool {
        let state = self.0.lock().unwrap_or_else(|e| e.into_inner());
        if state.epoch == expected {
            return !state.committed;
        }
        if !state.committed {
            reopen();
        }
        false
    }
}

pub fn start_finite<T>(
    app: &tauri::AppHandle,
    start: impl FnOnce() -> Result<T, AppError>,
) -> Result<T, AppError> {
    let admission = app.state::<ExecutionAdmission>();
    let _guard = admission
        .0
        .lock()
        .map_err(|_| blocked("Execution admission is unavailable."))?;
    if app.state::<crate::activation::ActivationState>().is_busy() {
        return Err(blocked(
            "Stop the activation experiment before starting another experiment.",
        ));
    }
    if app.state::<SustainedState>().is_busy() {
        return Err(blocked(
            "Stop or settle My reservoir before starting a finite experiment.",
        ));
    }
    start()
}

pub fn start_sustained<T>(
    app: &tauri::AppHandle,
    start: impl FnOnce() -> Result<T, AppError>,
) -> Result<T, AppError> {
    let admission = app.state::<ExecutionAdmission>();
    let _guard = admission
        .0
        .lock()
        .map_err(|_| blocked("Execution admission is unavailable."))?;
    if app.state::<crate::activation::ActivationState>().is_busy() {
        return Err(blocked(
            "Stop the activation experiment before starting another experiment.",
        ));
    }
    if app.state::<SessionState>().execution_busy() {
        return Err(blocked("Pause and retain or explicitly reset the finite experiment before starting My reservoir."));
    }
    start()
}

fn blocked(message: &str) -> AppError {
    AppError::new("start-session", "other-session", message)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Barrier,
    };

    #[test]
    fn return_after_deferred_wait_invalidates_final_authorization() {
        let close = Arc::new(CloseCoordinator::default());
        let epoch = close.epoch();
        let ready = Arc::new(Barrier::new(2));
        let proceed = Arc::new(Barrier::new(2));
        let waiter = {
            let (close, ready, proceed) = (close.clone(), ready.clone(), proceed.clone());
            std::thread::spawn(move || {
                // Admission has become available, but its guard was released.
                ready.wait();
                proceed.wait();
                close.current(epoch, |s| s.committed = true).is_some()
            })
        };
        ready.wait();
        assert!(close.cancel(|| {}));
        proceed.wait();
        assert!(!waiter.join().unwrap());
        assert!(!close.current(close.epoch(), |s| s.committed).unwrap());
    }

    #[test]
    fn return_during_slow_finish_reopens_late_gate_without_exit() {
        let close = Arc::new(CloseCoordinator::default());
        let gate = Arc::new(AtomicBool::new(false));
        let epoch = close.epoch();
        let started = Arc::new(Barrier::new(2));
        let finish = Arc::new(Barrier::new(2));
        let worker = {
            let (close, gate, started, finish) =
                (close.clone(), gate.clone(), started.clone(), finish.clone());
            std::thread::spawn(move || {
                assert!(close.current(epoch, |_| ()).is_some());
                started.wait();
                finish.wait();
                // The owner finishes persistence and sets its provisional gate.
                gate.store(true, Ordering::SeqCst);
                close.settled(epoch, || gate.store(false, Ordering::SeqCst))
            })
        };
        started.wait();
        assert!(close.cancel(|| gate.store(false, Ordering::SeqCst)));
        finish.wait();
        assert!(!worker.join().unwrap());
        assert!(!gate.load(Ordering::SeqCst));
        assert!(close.current(epoch, |s| s.committed = true).is_none());
    }

    #[test]
    fn return_between_finish_settlement_and_exit_check_still_wins() {
        let close = CloseCoordinator::default();
        let epoch = close.epoch();
        assert!(close.settled(epoch, || panic!("current finish reopened")));
        assert!(close.cancel(|| {}));
        assert!(close.current(epoch, |s| s.committed = true).is_none());
    }

    #[test]
    fn committed_exit_cannot_reopen_between_authorization_and_process_exit() {
        let close = CloseCoordinator::default();
        let epoch = close.epoch();
        close.current(epoch, |s| s.committed = true).unwrap();
        assert!(!close.cancel(|| panic!("committed owner reopened")));
        assert_eq!(close.epoch(), epoch);
        assert!(!close.settled(epoch, || panic!("committed owner reopened")));
    }

    #[test]
    fn stale_finish_preserves_newer_review_and_committed_exit() {
        let close = CloseCoordinator::default();
        let old = close.epoch();
        close.cancel(|| {});
        let current = close.epoch();
        close.current(current, |s| s.deferred = true).unwrap();
        let reopened = AtomicBool::new(false);
        assert!(!close.settled(old, || reopened.store(true, Ordering::SeqCst)));
        assert!(reopened.load(Ordering::SeqCst));
        assert!(close.current(current, |s| s.deferred).unwrap());
        close.current(current, |s| s.committed = true).unwrap();
        assert!(!close.settled(old, || panic!("new exit reopened")));
    }
}
