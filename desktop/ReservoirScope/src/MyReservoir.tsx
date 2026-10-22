import { useEffect, useId, useRef, useState, useSyncExternalStore } from 'react';
import MyReservoirConfig from './MyReservoirConfig';
import MyReservoirVisuals from './MyReservoirVisuals';
import MyReservoirJournals from './MyReservoirJournals';
import MyReservoirRecovery, { SustainedVerification } from './MyReservoirRecovery';
import { myReservoirController, type MyReservoirController, type MyReservoirState } from './myReservoirController';
import { DEFAULT_SUSTAINED_CONFIG, validDifferenceControls, validFieldControls, validWritingLimits, type SustainedConfig, type SustainedSummary } from './myReservoirTypes';
import { DEFAULT_CAMERA } from './types';
import { formatSessionDuration } from './sessionDuration';
import ActivationExperiment from './ActivationExperiment';
import './myReservoir.css';

const phase = (value: string) => ({ ready: 'Ready · not started', running: 'Running', awaitingLanguage: 'Waiting for writing', savingJournal: 'Saving journal', paused: 'Paused', stopped: 'Stopped', budgetReached: 'Run limit reached', storageBlocked: 'Storage needs attention', attemptBlocked: 'Writing needs attention', interrupted: 'Interrupted · review needed' })[value] ?? value;
const bytes = (value: number) => `${(value / 1048576).toFixed(2)} MiB`;
const attentionPhases = new Set(['storageBlocked', 'attemptBlocked', 'interrupted', 'budgetReached']);
const settledLimit = (s: SustainedSummary) => s.phase === 'budgetReached'
  && !s.pendingLanguage && !s.pendingSave && !s.pendingApplication
  && !s.canRetrySave && !s.canRetryProvider && !s.canSkipFeedback
  && !s.canPause && s.step === s.durableStep;
const phaseNeedsAttention = (s: SustainedSummary) => attentionPhases.has(s.phase) && !settledLimit(s);
const unsavedSteps = (step: number, durableStep: number) => step > durableStep ? (step === durableStep + 1 ? `step ${step}` : `steps ${durableStep + 1}–${step}`) : null;
export function MyReservoirBoundary({ state, controller }: { state: MyReservoirState; controller: MyReservoirController }) {
  const s = state.summary; if (!s) return null;
  const pending = s.pendingLanguage;
  const needsAttention = phaseNeedsAttention(s) || s.canRetrySave || s.canRetryProvider || pending?.state === 'blocked' || !!s.pendingApplication && !s.canPause;
  const hasActiveFailure = (attentionPhases.has(s.phase) && s.phase !== 'budgetReached') || s.canRetrySave || s.canRetryProvider || pending?.state === 'blocked';
  const hasBoundary = !!pending || !!s.pendingSave || !!s.pendingApplication || s.canRetrySave || s.canRetryProvider || s.canSkipFeedback;
  return <details className={`my-reservoir-boundary${needsAttention ? ' needs-attention' : ''}`} open={needsAttention}>
    <summary>Writing and feedback{needsAttention ? ' · review needed' : ''}</summary>
    {hasBoundary && <h3>{s.pendingSave ? 'Journal save pending' : pending?.state === 'blocked' ? 'Writing needs attention' : pending?.state === 'prepared' ? 'Ready to write' : pending ? s.config.language.backend === 'scripted' ? 'Preparing example writing' : 'Local model writing' : s.pendingApplication ? 'Saved feedback waiting' : s.canRetryProvider || s.canSkipFeedback ? 'Writing needs attention' : 'Storage needs attention'}</h3>}
    {hasActiveFailure && s.diagnostics.length > 0 && <p role="alert" className="my-reservoir-error">{s.diagnostics[s.diagnostics.length - 1]}</p>}
    {!hasBoundary && <p>{needsAttention ? 'The session is not advancing. Review its status and saved history before continuing.' : 'No writing needs attention. Saved entries are below.'}</p>}
    {pending && <><p>Observed step {pending.observedStep}. The numerical clock is held; you can keep reading and inspecting.</p><p>{pending.state === 'blocked' ? 'No network request is active. This opportunity has no accepted journal or feedback; it is not automatically retried.' : s.config.language.backend === 'scripted' ? 'This scripted opportunity makes no model request. Pause holds the clock after the current boundary.' : 'Pause requests a held boundary; an already dispatched request may still finish. Stop cancels outstanding work and retains its outcome.'}</p><details><summary>Request details</summary><dl className="my-reservoir-data"><dt>Turn / attempt</dt><dd>{pending.turnId} / {pending.attemptId}</dd><dt>Operation</dt><dd>{pending.operationId}</dd><dt>Configured source</dt><dd>{s.config.language.backend === 'scripted' ? 'Deterministic script · no model request' : `${pending.endpoint} / ${pending.model}`}</dd></dl></details></>}
    {s.pendingSave && <><p>Writing at step {s.pendingSave.observedStep} is waiting for save confirmation. The save and readback must succeed before its text can enter feedback.</p><details><summary>Pending save details</summary><p className="my-reservoir-hash">{s.pendingSave.entryId}</p></details></>}
    {s.canRetrySave && <button disabled={!!state.busy} onClick={() => void controller.action('retrySave')}>Retry save</button>}
    {s.pendingApplication && <><p>Writing from step {s.pendingApplication.observedStep} is saved and prepared for step {s.pendingApplication.intendedStep}. Pausing preserves it; it has not yet been recorded as applied. Explicitly skipping keeps the text readable and excludes it from feedback and automatic memory.</p><details><summary>Saved journal details</summary><p className="my-reservoir-hash">{s.pendingApplication.entryId}</p></details></>}
    {s.canRetryProvider && <><p>A retry is a new writing attempt with a new identity. The earlier failure remains retained.</p><button disabled={!!state.busy} onClick={() => void controller.action('retryProvider')}>Retry as a new attempt</button></>}
    {s.canSkipFeedback && <button disabled={!!state.busy} onClick={() => void controller.action('skipFeedback')}>{s.pendingApplication ? 'Skip this saved feedback' : 'Skip this writing attempt'}</button>}
  </details>;
}
export function MyReservoirStatus({ state }: { state: MyReservoirState }) {
  const s = state.summary; if (!s) return null;
  const fill = state.frame?.fillPercent;
  const fillAvailable = typeof fill === 'number' && Number.isFinite(fill) && fill >= 0 && fill <= 100;
  return <section className={`my-reservoir-status${phaseNeedsAttention(s) ? ' needs-attention' : ''}`} aria-label="Current reservoir session"><div className="my-reservoir-status-main"><div><strong>{phase(s.phase)}</strong>{settledLimit(s) && <p>Saved entries remain available to read and export.</p>}<p>{s.config.language.backend === 'scripted' ? 'Example writing · offline' : `Local model · ${s.config.language.model}`} · journals save automatically</p><p>Live step {s.step}; saved through step {s.durableStep}.</p></div><dl><div className="my-reservoir-current-fill"><dt>Current sensory fill</dt><dd>{fillAvailable ? `${fill.toFixed(2)}%` : 'Unavailable'}</dd></div><div><dt>Saved journals</dt><dd>{s.journalCount}</dd></div><div><dt>Running time / limit</dt><dd>{formatSessionDuration(s.elapsedSeconds)} / {formatSessionDuration(s.config.maximumDurationSeconds)}</dd></div><div><dt>Storage / budget</dt><dd>{bytes(s.usedBytes)} / {bytes(s.config.storageBudgetBytes)}</dd></div></dl></div><details className="my-reservoir-status-details"><summary>Session measurements and limits</summary><dl><div><dt>Numerical step</dt><dd>{s.step} / {s.config.maximumSteps}</dd></div><div><dt>Saved through step</dt><dd>{s.durableStep}</dd></div><div><dt>Simulated seconds</dt><dd>{s.simulatedTime.toFixed(3)}</dd></div><div><dt>Elapsed / limit seconds</dt><dd>{s.elapsedSeconds.toFixed(1)} / {s.config.maximumDurationSeconds}</dd></div><div><dt>Attempts / limit</dt><dd>{s.turnCount} / {s.config.maximumTurns}</dd></div></dl><p>The first duration, step, attempt or storage bound holds the session. Writing and saving hold numerical time; running time is a separate clock.</p></details></section>;
}
export default function MyReservoir({ active, controller = myReservoirController }: { active: boolean; controller?: MyReservoirController }) {
  const state = useSyncExternalStore(controller.subscribe, controller.snapshot, controller.snapshot);
  const [config, setConfig] = useState<SustainedConfig>({ ...DEFAULT_SUSTAINED_CONFIG, language: { backend: 'scripted' } });
  const [pose, setPose] = useState(DEFAULT_CAMERA), [node, setNode] = useState(0), [tableOnly, setTableOnly] = useState(false);
  const [activationOpen, setActivationOpen] = useState(false);
  useEffect(() => { controller.setActive(active); if (active) void controller.connect(); return () => controller.setActive(false); }, [controller, active]);
  if (!active) return null;
  const s = state.summary, busy = !!state.busy, durationValid = Number.isInteger(config.maximumDurationSeconds) && config.maximumDurationSeconds >= 1 && config.maximumDurationSeconds <= 86400, writingValid = validWritingLimits(config), fieldValid = validFieldControls(config), differenceValid = validDifferenceControls(config), createDisabled = busy || !durationValid || !writingValid || !fieldValid || !differenceValid || !!s && s.phase !== 'stopped';
  const editor = <><MyReservoirConfig config={config} setConfig={setConfig} disabled={busy}/><div className="my-reservoir-actions"><button className="primary-button" disabled={createDisabled} onClick={() => void controller.create(config)}>Create my reservoir</button><p className="my-reservoir-small">{!durationValid ? 'Choose a duration from 1 second to 24 hours in Advanced settings.' : !writingValid ? 'Review the writing limits in Advanced settings.' : !fieldValid ? 'Review the sensory noise and feedback scale in Advanced settings.' : s && s.phase !== 'stopped' ? 'Stop the current session before creating another.' : 'Create prepares the session. Choose Start when you are ready.'}</p></div></>;
  return <section className="my-reservoir"><header className="my-reservoir-heading"><div><h1>My reservoir</h1><p>Run a reservoir with scripted writing or a local model, read its journal, and watch saved text return as input. The session can continue while this app is open or minimized, within your chosen run and storage bounds.</p></div><label className="my-reservoir-graphics-control"><input type="checkbox" checked={tableOnly} onChange={event => setTableOnly(event.target.checked)}/>Replace 3D with exact values</label></header>
    {state.error && <p role="alert" className="my-reservoir-error">{state.error}</p>}{state.message && <p role="status" className="my-reservoir-message">{state.message}</p>}
    {s ? <><MyReservoirStatus state={state}/><div className="my-reservoir-actions"><button className="primary-button" disabled={busy || !s.canStart} onClick={() => void controller.action('start')}>{s.step === 0 ? 'Start' : 'Resume'}</button><button disabled={busy || !s.canPause} onClick={() => void controller.action('pause')}>Pause</button><button disabled={busy || !s.canStop} onClick={() => void controller.action('stop')}>{s.pendingLanguage?.state === 'requesting' && s.config.language.backend === 'ollama' ? 'Cancel request and stop' : 'Stop'}</button><span className="my-reservoir-small">Requested pace: {s.config.paceMs} ms per step · writing every {s.config.turnEvery} steps</span></div>
      <MyReservoirBoundary state={state} controller={controller}/>
      <div className="my-reservoir-reading-layout">
        <MyReservoirJournals state={state} controller={controller}/>
        <MyReservoirVisuals summary={s} frame={state.frame} node={node} onNode={setNode} pose={pose} onPose={setPose} tableOnly={tableOnly}/>
      </div>
      {s.diagnostics.length > 0 && <details className="my-reservoir-details"><summary>Session messages · {s.diagnostics.length}</summary><ul>{s.diagnostics.map((diagnostic, index) => <li key={index}>{diagnostic}</li>)}</ul></details>}
      <div className="my-reservoir-actions"><button disabled={busy || s.canPause || (!!s.pendingLanguage && s.pendingLanguage.state !== 'blocked') || !!s.pendingSave} onClick={() => void controller.export()}>Export saved session…</button><span className="my-reservoir-small">Pause before exporting. To copy earlier saved history while work is unsaved, use Saved sessions and recovery below. Each export creates a separate snapshot.</span></div>
      {state.exported && <details className="my-reservoir-details"><summary>Export details · revision {state.exportRevision}</summary><SustainedVerification report={state.exported}/><p>Later session changes are not included in this export.</p></details>}
      <details className="my-reservoir-details"><summary>Session settings and details</summary><dl className="my-reservoir-data"><dt>Session / generation</dt><dd>{s.sessionId} / {s.generation}</dd><dt>Revision</dt><dd>{s.revision}</dd><dt>Exact simulated seconds</dt><dd>{s.simulatedTime}</dd><dt>Exact storage bytes</dt><dd>{s.usedBytes} / {s.config.storageBudgetBytes}</dd></dl><pre>{JSON.stringify(s.config, null, 2)}</pre><p>These accepted settings belong to this session. Editing the next-session form cannot change an existing run.</p></details><details className="my-reservoir-details"><summary>Prepare another session</summary>{editor}</details>
    </> : editor}<MyReservoirRecovery state={state} controller={controller}/>
    <details className="activation-entry" onToggle={event => setActivationOpen(event.currentTarget.open)}><summary>Activation experiment · optional</summary>{activationOpen && <ActivationExperiment active={active}/>}</details>
  </section>;
}
export function MyReservoirClosePanel({ controller = myReservoirController }: { controller?: MyReservoirController }) {
  const state = useSyncExternalStore(controller.subscribe, controller.snapshot, controller.snapshot), dialog = useRef<HTMLDialogElement>(null), label = useId();
  const s = state.summary, tail = s && unsavedSteps(s.step, s.durableStep);
  useEffect(() => { let disposed = false, stop: (() => void) | undefined; controller.listenClose().then(value => { if (disposed) value(); else stop = value; }).catch(() => {}); return () => { disposed = true; stop?.(); }; }, [controller]);
  useEffect(() => { const element = dialog.current; if (!element) return; if (state.closeRequested && !element.open) element.showModal(); else if (!state.closeRequested && element.open) element.close(); }, [state.closeRequested]);
  return <dialog ref={dialog} className="my-reservoir-close" aria-labelledby={label} onCancel={event => { event.preventDefault(); void controller.returnToApp(); }}><h2 id={label}>Review retained work before quitting</h2><p>Quitting ends execution. Checkpoint and quit requests a final save; a failed save remains visible here. Nothing resumes automatically after relaunch.</p>{state.error && <p role="alert" className="my-reservoir-error">{state.error}</p>}<MyReservoirStatus state={state}/><MyReservoirBoundary state={state} controller={controller}/><MyReservoirRecovery state={state} controller={controller}/>{tail && <p>Discarding may lose unsaved numerical {tail}. The last committed history ends at step {s!.durableStep}.</p>}{(s?.pendingLanguage || s?.pendingSave) && <p>Pending writing may also be lost if it has not been committed. Inspect and export retained history before discarding if you need a copy.</p>}<div className="my-reservoir-actions"><button autoFocus disabled={!!state.busy} onClick={() => void controller.returnToApp()}>Return to app</button><button disabled={!!state.busy} onClick={() => void controller.finishClose(false)}>Checkpoint and quit</button><button disabled={!!state.busy} onClick={() => void controller.finishClose(true)}>Discard unresolved work and quit</button></div><p>Discarding preserves already committed history. It does not confirm a final checkpoint or a saved or applied journal.</p></dialog>;
}
export { MyReservoirClosePanel as SustainedClosePanel };
