//! Incremental offline matched comparisons. Numerical boundaries are paired;
//! each arm's real storage evidence is supplied separately by the caller.
use crate::{
    actions::*,
    ensure,
    session::{
        ensure_action_language, JournalSession, LanguageResponse, PendingJournal, PendingLanguage,
        PendingMemory,
    },
    stage::RunStatus,
    Result,
};
use serde::Serialize;
use std::sync::Arc;

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ComparisonFrame {
    pub left: ActionFrame,
    pub right: ActionFrame,
}

struct Boundary {
    trigger: Trigger,
    order: [Arm; 2],
    next: usize,
    request_order: usize,
    prior_failed: bool,
}

pub struct ActionComparisonSession {
    specification: ActionSpecification,
    left: JournalSession,
    right: JournalSession,
    tape: Option<Arc<ActionReplyTape>>,
    boundary: Option<Boundary>,
    active_arm: Option<Arm>,
    stopped: bool,
}

impl ActionComparisonSession {
    pub fn new(specification: ActionSpecification) -> Result<Self> {
        specification.validate()?;
        ensure(specification.compare_previous && specification.stage > 1,
            "A matched comparison requires an available left arm (components B–H or observation D/D)")?;
        ensure_action_language(&specification)?;
        let tape = if specification.mode == ComparisonMode::FixedReplay {
            Some(Arc::new(ActionReplyTape::make(&specification)?))
        } else {
            None
        };
        let left_stage = if specification.comparison_kind == ComparisonKind::Observation {
            4
        } else {
            specification.stage - 1
        };
        let left =
            JournalSession::new_arm(specification.clone(), left_stage, Arm::Left, tape.clone())?;
        let right = JournalSession::new_arm(
            specification.clone(),
            specification.stage,
            Arm::Right,
            tape.clone(),
        )?;
        Ok(Self {
            specification,
            left,
            right,
            tape,
            boundary: None,
            active_arm: None,
            stopped: false,
        })
    }
    pub fn specification(&self) -> &ActionSpecification {
        &self.specification
    }
    pub fn tape(&self) -> Option<&ActionReplyTape> {
        self.tape.as_deref()
    }
    fn engine(&self, arm: Arm) -> &JournalSession {
        match arm {
            Arm::Left => &self.left,
            Arm::Right => &self.right,
        }
    }
    fn engine_mut(&mut self, arm: Arm) -> &mut JournalSession {
        match arm {
            Arm::Left => &mut self.left,
            Arm::Right => &mut self.right,
        }
    }
    pub fn run(&self, arm: Arm) -> &ActionRunRecord {
        self.engine(arm).run()
    }
    pub fn frames(&self, arm: Arm) -> &[ActionFrame] {
        self.engine(arm).frames()
    }
    pub fn actions(&self, arm: Arm) -> &[ActionReceipt] {
        self.engine(arm).actions()
    }
    pub fn journals(&self, arm: Arm) -> &[JournalEntry] {
        self.engine(arm).journals()
    }
    pub fn is_complete(&self) -> bool {
        self.left.is_complete() && self.right.is_complete()
    }
    /// A failed first observation arm can coexist with an unresolved partner.
    /// The caller must resolve pending storage before taking a portable record.
    pub fn is_failed(&self) -> bool {
        self.left.is_failed() || self.right.is_failed()
    }
    pub fn pending_journal(&self) -> Option<(Arm, &PendingJournal)> {
        let arm = self.active_arm?;
        self.engine(arm)
            .pending_journal()
            .map(|pending| (arm, pending))
    }
    pub fn pending_memory(&self) -> Option<(Arm, &PendingMemory)> {
        let arm = self.active_arm?;
        self.engine(arm)
            .pending_memory()
            .map(|pending| (arm, pending))
    }
    pub fn pending_language(&self) -> Option<(Arm, &PendingLanguage)> {
        let arm = self.active_arm?;
        self.engine(arm)
            .pending_language()
            .map(|pending| (arm, pending))
    }
    pub fn record(&self) -> Result<ActionComparisonRecord> {
        ensure(self.boundary.is_none(), "Paired boundary has unresolved journal save or memory read; finish it, explicitly stop, or discard before snapshot")?;
        let status = if self.is_failed() {
            RunStatus::Failed
        } else if self.is_complete() {
            RunStatus::Completed
        } else {
            RunStatus::Stopped
        };
        Ok(ActionComparisonRecord {
            format: FORMATS[2].into(),
            specification: self.specification.clone(),
            tape: self.tape.as_deref().cloned(),
            left: Some(self.run(Arm::Left).clone()),
            right: self.run(Arm::Right).clone(),
            status,
            failure: if self.is_failed() {
                self.run(Arm::Left)
                    .failure
                    .clone()
                    .or_else(|| self.run(Arm::Right).failure.clone())
            } else {
                None
            },
        })
    }
    fn ready(&self) -> Result<()> {
        ensure(
            !self.stopped && !self.is_failed() && !self.is_complete() && self.boundary.is_none(),
            "Comparison is stopped, failed, complete, or has an unresolved paired boundary",
        )
    }
    /// Both numerical preparations finish before either arm mutates. No growing
    /// history is cloned during this transaction; only current numerical state.
    pub fn advance(&mut self) -> Result<ComparisonFrame> {
        self.ready()?;
        let left = self.left.prepare_frame()?;
        let right = self.right.prepare_frame()?;
        let pair = ComparisonFrame {
            left: self.left.commit_frame(left),
            right: self.right.commit_frame(right),
        };
        let step = pair.right.step;
        if self.specification.stage >= 4
            && step < self.specification.steps
            && step.is_multiple_of(self.specification.turn_every)
        {
            self.begin_boundary(Trigger::Scheduled)?;
        }
        Ok(pair)
    }
    pub fn can_request_action(&self) -> bool {
        self.ready().is_ok()
            && self.right.can_request_action()
            && (self.run(Arm::Left).stage < 4 || self.left.can_request_action())
    }
    pub fn request_action(&mut self) -> Result<()> {
        ensure(self.can_request_action(), "Manual comparison action needs an unused nonfinal nonscheduled boundary and remaining capacity in both arms")?;
        self.begin_boundary(Trigger::Manual)
    }
    fn begin_boundary(&mut self, trigger: Trigger) -> Result<()> {
        let number = self.right.actions().len() + 1;
        let right_first = self.specification.comparison_kind == ComparisonKind::Observation
            && number.is_multiple_of(2);
        self.boundary = Some(Boundary {
            trigger,
            order: if right_first {
                [Arm::Right, Arm::Left]
            } else {
                [Arm::Left, Arm::Right]
            },
            next: 0,
            request_order: 0,
            prior_failed: false,
        });
        self.pump()
    }
    fn pump(&mut self) -> Result<()> {
        while self.active_arm.is_none() {
            let Some(boundary) = &mut self.boundary else {
                return Ok(());
            };
            if boundary.next == 2 {
                self.boundary = None;
                return Ok(());
            }
            let arm = boundary.order[boundary.next];
            boundary.next += 1;
            let trigger = boundary.trigger;
            let cancel = self.stopped
                || (boundary.prior_failed
                    && self.specification.comparison_kind == ComparisonKind::Components);
            if self.engine(arm).run().stage < 4 {
                continue;
            }
            if cancel {
                self.engine_mut(arm).cancel_before_action(
                    trigger,
                    "Paired action stopped before this request started.",
                )?;
                continue;
            }
            let boundary = self.boundary.as_mut().unwrap();
            boundary.request_order += 1;
            let order = boundary.request_order;
            self.engine_mut(arm).begin_opportunity(trigger, order)?;
            if self.engine(arm).pending_memory().is_some()
                || self.engine(arm).pending_journal().is_some()
                || self.engine(arm).pending_language().is_some()
            {
                self.active_arm = Some(arm);
            }
            // A WAIT is already committed; continue to the next eligible arm.
        }
        Ok(())
    }
    fn current(&self, arm: Arm) -> Result<()> {
        ensure(
            self.active_arm == Some(arm),
            "Receipt arm differs from the active ordered opportunity",
        )
    }
    fn resolved(&mut self, arm: Arm) -> Result<()> {
        if self.engine(arm).pending_memory().is_none()
            && self.engine(arm).pending_journal().is_none()
            && self.engine(arm).pending_language().is_none()
        {
            self.boundary.as_mut().unwrap().prior_failed |= self.engine(arm).is_failed();
            self.active_arm = None;
            self.pump()?;
        }
        Ok(())
    }
    pub fn confirm_memory(&mut self, arm: Arm, readback: &JournalEntry) -> Result<()> {
        self.current(arm)?;
        self.engine_mut(arm).confirm_memory(readback)?;
        self.resolved(arm)
    }
    pub fn start_language(&mut self, arm: Arm, id: usize, step: usize) -> Result<()> {
        self.current(arm)?;
        self.engine_mut(arm).start_language(id, step)
    }
    pub fn confirm_language(
        &mut self,
        arm: Arm,
        id: usize,
        step: usize,
        response: &LanguageResponse,
    ) -> Result<()> {
        self.current(arm)?;
        self.engine_mut(arm).confirm_language(id, step, response)?;
        self.resolved(arm)
    }
    pub fn fail_language(&mut self, arm: Arm, id: usize, step: usize, reason: &str) -> Result<()> {
        self.current(arm)?;
        self.engine_mut(arm).fail_language(id, step, reason)?;
        self.resolved(arm)
    }
    /// Cancelling one in-flight operation explicitly stops the entire paired
    /// boundary; an unstarted peer is cancelled instead of silently dispatched.
    pub fn cancel_language(
        &mut self,
        arm: Arm,
        id: usize,
        step: usize,
        reason: &str,
    ) -> Result<()> {
        self.current(arm)?;
        let pending = self
            .engine(arm)
            .pending_language()
            .ok_or_else(|| crate::CoreError::Invalid("No pending language opportunity".into()))?;
        ensure(
            pending.turn_id == id && pending.observed_step == step,
            "Language cancellation belongs to a different opportunity",
        )?;
        self.stop(reason)
    }
    pub fn confirm_saved(
        &mut self,
        arm: Arm,
        receipt: &JournalSaveReceipt,
        readback: &JournalEntry,
    ) -> Result<()> {
        self.current(arm)?;
        self.engine_mut(arm).confirm_saved(receipt, readback)?;
        self.resolved(arm)
    }
    pub fn fail_memory(&mut self, arm: Arm, reason: &str) -> Result<()> {
        self.current(arm)?;
        self.engine_mut(arm).fail_memory(reason)?;
        self.resolved(arm)
    }
    pub fn fail_pending(&mut self, arm: Arm, reason: &str) -> Result<()> {
        self.current(arm)?;
        self.engine_mut(arm).fail_pending(reason)?;
        self.resolved(arm)
    }
    /// Explicit stop is terminal. A prepared WRITE becomes retained save failure;
    /// a pending read and unstarted peer become cancellations before exposure.
    pub fn stop(&mut self, reason: &str) -> Result<()> {
        ensure(
            !reason.is_empty() && reason.len() <= 4096,
            "Stop diagnostic must contain 1–4096 UTF-8 bytes",
        )?;
        self.stopped = true;
        if let Some(arm) = self.active_arm {
            if self.engine(arm).pending_journal().is_some() {
                self.engine_mut(arm).fail_pending(reason)?;
            } else if let Some(pending) = self.engine(arm).pending_language() {
                let (id, step) = (pending.turn_id, pending.observed_step);
                self.engine_mut(arm).cancel_language(id, step, reason)?;
            } else {
                self.engine_mut(arm).cancel_memory(reason)?;
            }
            self.resolved(arm)?;
        }
        self.left.stop()?;
        self.right.stop()?;
        Ok(())
    }
}
