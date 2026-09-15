# Bound the flywheel's maintenance pause

This avenue appeared during Mike's authorized provider-observer rollout, rather
than through an authored journal request. On September 8 the controller recorded
pause generation 409 at 17:46:19 UTC. Later status snapshots still reported the
same live lease and `stop_requested=true` while the identified
`felt_contract_graph.py` projection process continued running. Source trees
remained clean, and the observer build proceeded in an isolated checkout.

A guarded operator cancellation was prepared against that exact process and
parent identity. Before it ran, the projection completed and released its lease.
The guard refused because no lease remained; no cancellation signal was sent by
this task. Preserve that correction beside the earlier planned action. This is
an observed delayed pause, not proof of a permanently stuck process.

At source revision `ca87a380b26ef80946b0f99fe3daf8f9bcc4542d`, both
`scripts/steward_control/projection.py::_default_runner` and
`scripts/steward_control/executor.py::run_subprocess` send SIGINT once and then
continue waiting while the child runs. Their configured deadline does not add a
second termination path once `interrupted` is true. A child that ignores or
delays SIGINT can therefore hold the cooperative lease beyond the pause wait.
Whether inherited signal handling explains this particular delay was not tested.

The displayed `child_exited=true` also persisted while the current named child
was independently observed running. `ProjectionRunControl.poll` merges new
progress into the previous dictionary, so a prior step's terminal field can
remain in later progress. This status field should be reset at step boundaries.

Suggested owning follow-up:

1. Give cancellation a finite graceful period for the exact owned maintenance
   child, followed by an explicit cancellation outcome if escalation is needed.
   Preserve completed projection checkpoints and never target Being services.
2. Reset per-step process status and distinguish child execution, cancellation
   requested, process exited and receipt assembly.
3. Test children that finish normally, handle SIGINT slowly, ignore it, spawn
   descendants, and exit just before cancellation. Test that a stale PID is never
   signalled and no new projection step starts after the pause.
4. Measure pause-request to lease-release duration and projector phase time in
   ordinary rounds. Preserve interrupted work for safe resumption rather than
   recomputing every completed projection.

This is a concrete implementation proposal. No scheduler, cancellation policy,
or projection algorithm was changed in the observer rollout. Evidence is retained
with its deployment packet under `rollout/host-evidence/paused-control.json` and
the guarded cancellation script; the final account links the copied packet.

The resume path supplied a second measurement lead: `StewardController.resume`
runs full-chain verification, whereas status uses the indexed tail. A 60-second
operator-wrapper deadline was too short; readback confirmed the pause remained
owned, and the retry completed the existing verification and resumed at 18:15:41
UTC. The retained earlier status counted 1,036,637 evidence events. Measure this
verification cost before considering an anchored incremental path with equivalent
integrity checks. No verification gate was bypassed or weakened. The research
packet retains `control-restoration-retry-before.json` and `control-restoration.json`.
