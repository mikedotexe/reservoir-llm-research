import { useCallback, useEffect, useId, useState, useSyncExternalStore } from 'react';
import ActivationRuntimeSetup from './ActivationRuntimeSetup';
import ActivationReadingCollection from './ActivationReadingCollection';
import type { ActivationRuntimePaths } from './activationSetupTypes';
import { activationController, type ActivationController, type ActivationState } from './activationController';
import { ACTIVATION_ARM_NAMES, DEFAULT_ACTIVATION_CONFIG, activationCanStart, activationRunning, type ActivationConfig, type ActivationJournal, type ActivationSnapshot } from './activationTypes';
import { activationTimeline } from './activationTimeline';
import './activation.css';

const statusLabel = (status: string) => ({ ready: 'Ready · not started', running: 'Running', initializing: 'Preparing model', stopped: 'Stopped', completed: 'Complete', complete: 'Complete', failed: 'Held after a failure', held: 'Held for review', interrupted: 'Interrupted · review needed', paused: 'Paused for review' })[status] ?? status;
const seriesLabel = (index: number) => `Reading ${String.fromCharCode(65 + index)}`;
function comparisonStatus(sessions: ActivationSnapshot[]) {
  if (sessions.length < 2) return 'single';
  if (sessions.some(s => !s.modelManifestSha256 || !s.calibrationSha256)) return 'unconfirmed';
  const key = (s: ActivationSnapshot) => JSON.stringify([s.modelManifestSha256, s.calibrationSha256, s.config.seed, s.config.observations, s.config.stepsBetween, s.config.journalEvery, s.config.maxJournalTokens, s.config.gain]);
  return sessions.every(s => key(s) === key(sessions[0])) ? 'matched' : 'different';
}

export function ActivationSetup({ state, config, setConfig, controller }: { state: ActivationState; config: ActivationConfig; setConfig: (c: ActivationConfig) => void; controller: ActivationController }) {
  const busy = !!state.busy || activationRunning(state.current), checked = state.checkedConfig === JSON.stringify(config);
  const id = useId(), [observations, setObservations] = useState(config.observations.join('\n'));
  const update = (patch: Partial<ActivationConfig>) => setConfig({ ...config, ...patch });
  async function inspect() { const result = await controller.inspect(config); if (result?.config) setConfig(result.config); }
  const validObservations = config.observations.length === 12 && config.observations.every(text => text.trim().length > 0 && text.length <= 4096);
  return <section className="activation-setup" aria-labelledby={`${id}-setup`}><h3 id={`${id}-setup`}>Prepare one condition</h3>
    <p>Use the same twelve observations and seed for each condition. Each run has ten controlled steps between observations and six writing opportunities. The model loads only after Start.</p>
    <div className="activation-fields">
      <label>Condition<select disabled={busy} value={config.arm} onChange={e => update({ arm: e.target.value as ActivationConfig['arm'] })}>{Object.entries(ACTIVATION_ARM_NAMES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    </div><details><summary>Advanced local runtime paths</summary><p>Normally the prepared runtime and bundled worker are selected automatically.</p><div className="activation-fields">
      <label>Python interpreter<input disabled={busy} value={config.pythonPath} placeholder="Use the prepared runtime, or enter an absolute path" onChange={e => update({ pythonPath: e.target.value })}/></label>
      <label>Qwen3 model directory<input disabled={busy} value={config.modelPath} placeholder="Local pinned Qwen3-4B model directory" onChange={e => update({ modelPath: e.target.value })}/></label>
      <label>Activation worker<input disabled={busy} value={config.workerPath} placeholder="Use the bundled worker, or enter its absolute path" onChange={e => update({ workerPath: e.target.value })}/></label>
    </div></details>
    <details><summary>Observation sequence and fixed bounds</summary><label htmlFor={`${id}-observations`}>Twelve quiet observations · one per line</label><textarea id={`${id}-observations`} rows={12} disabled={busy} value={observations} onChange={e => { setObservations(e.target.value); update({ observations: e.target.value.split('\n').map(s => s.trim()) }); }}/>
      <dl className="activation-data"><dt>Reservoir</dt><dd>32 coordinates</dd><dt>Seed</dt><dd>{config.seed}</dd><dt>Gap</dt><dd>{config.stepsBetween} controlled steps</dd><dt>Writing cadence</dt><dd>Every {config.journalEvery} observations</dd><dt>Output ceiling</dt><dd>{config.maxJournalTokens.toLocaleString('en-US')} tokens per entry</dd><dt>Steering gain</dt><dd>{config.gain}</dd></dl><p>Controlled steps are experimental time. Waiting for the model does not silently advance that clock.</p>
    </details>
    <div className="activation-actions"><button disabled={busy || !validObservations} onClick={() => void inspect()}>Check activation setup</button><button className="primary-button" disabled={busy || !checked || state.capability?.ready === false || !validObservations} onClick={() => void controller.create(config)}>Create activation experiment</button></div>
    {!validObservations && <p role="alert">Provide exactly twelve nonempty observations, each at most 4,096 characters.</p>}
    <p className="activation-small">Checking inspects the local environment without inference. Create saves a prepared run; Start is a separate action.</p>
    {state.capability && <p role="status">{checked ? state.capability.ready === false ? 'Setup needs attention.' : 'Setup checked for these settings.' : 'Settings changed; check them before creating.'}{state.capability.diagnostic ? ` ${state.capability.diagnostic}` : ''}</p>}
    {state.capability && <details><summary>Setup evidence</summary><pre tabIndex={0}>{JSON.stringify(state.capability, null, 2)}</pre></details>}
  </section>;
}

export function ActivationReadingNote({ session, journal, controller, disabled }: { session: ActivationSnapshot; journal: ActivationJournal; controller: ActivationController; disabled: boolean }) {
  const id = useId(), [excerpt, setExcerpt] = useState(''), [interpretation, setInterpretation] = useState(''), [alternative, setAlternative] = useState(''), [sources, setSources] = useState<string[]>([]);
  async function save() {
    if (await controller.annotate(session.sessionId, { journalId: journal.id, excerpt, interpretation, alternative, sourceEventIds: sources })) { setExcerpt(''); setInterpretation(''); setAlternative(''); setSources([]); }
  }
  return <details className="activation-note"><summary>Add a reading note</summary><p>Keep an interpretation beside its excerpt and another possible reading. These notes stay separate from the model and never determine feedback eligibility.</p>
    <label htmlFor={`${id}-excerpt`}>Exact journal excerpt</label><textarea id={`${id}-excerpt`} value={excerpt} onChange={e => setExcerpt(e.target.value)} rows={3}/>
    <label htmlFor={`${id}-interpretation`}>Interpretation</label><textarea id={`${id}-interpretation`} value={interpretation} onChange={e => setInterpretation(e.target.value)} rows={3}/>
    <label htmlFor={`${id}-alternative`}>Another possible reading</label><textarea id={`${id}-alternative`} value={alternative} onChange={e => setAlternative(e.target.value)} rows={3}/>
    <fieldset><legend>Source events</legend><div className="activation-source-events" role="region" aria-label="Source events for this reading note" tabIndex={0}>{activationTimeline(session).map(({ event, label }, index) => <label key={event.id}><input type="checkbox" checked={sources.includes(event.id)} onChange={e => setSources(e.target.checked ? [...sources, event.id] : sources.filter(id => id !== event.id))}/><span>Event {index + 1} · step {event.step} · {label}</span></label>)}</div></fieldset>
    <button disabled={disabled || !interpretation.trim() || !alternative.trim() || !sources.length} onClick={() => void save()}>Save reading note</button>
    {(session.annotations ?? []).filter(note => note.journalId === journal.id).map((note, index) => <blockquote key={index}><p>{note.excerpt}</p><p><strong>Interpretation:</strong> {note.interpretation}</p><p><strong>Another reading:</strong> {note.alternative}</p><p>{note.sourceEventIds.length} source events linked.</p></blockquote>)}
  </details>;
}

export function ActivationReader({ session, index, state, controller }: { session: ActivationSnapshot; index: number; state: ActivationState; controller: ActivationController }) {
  const selected = state.selected[session.sessionId], position = session.journals.findIndex(j => j.id === selected), journal = session.journals[position] ?? null;
  const label = state.revealed ? ACTIVATION_ARM_NAMES[session.config.arm] : seriesLabel(index), following = state.following[session.sessionId] !== false;
  return <article className="activation-reading" aria-label={`${seriesLabel(index)} journal`}><header><h3>{label}</h3><span>{session.journals.length} journal entries · {statusLabel(session.status)}</span></header>
    <div className="activation-actions"><button disabled={position <= 0} onClick={() => controller.adjacent(session.sessionId, -1)}>Earlier</button><button disabled={position < 0 || position >= session.journals.length - 1} onClick={() => controller.adjacent(session.sessionId, 1)}>Later</button><button aria-pressed={following} onClick={() => controller.follow(session.sessionId)}>Follow latest</button><span>{journal ? `Entry ${position + 1} of ${session.journals.length}` : 'No completed journal yet'}</span></div>
    {!following && position >= 0 && position < session.journals.length - 1 && <p className="activation-new">{session.journals.length - position - 1} later {session.journals.length - position - 1 === 1 ? 'entry' : 'entries'} available. Your selected text stays in place.</p>}
    {journal ? <><div key={journal.id} className="activation-prose" tabIndex={0} aria-label={`${seriesLabel(index)} selected journal`}>{journal.text}</div>{journal.status === 'receivedPendingSave' && <p>Writing received; durable save and readback are pending. This text is not yet eligible for feedback.</p>}<p className="activation-small">Observed at step {journal.observedStep}. {journal.firstAppliedStep === null ? 'No first feedback application is recorded.' : `Feedback first applied at step ${journal.firstAppliedStep}.`} Reading never moves the experiment clock.</p><ActivationReadingNote key={journal.id} session={session} journal={journal} controller={controller} disabled={!!state.busy}/></> : <p>Quiet observations and incomplete attempts remain visible in the timeline even when no journal is saved.</p>}
    {(session.incompleteAttempts ?? []).map(attempt => <details key={attempt.requestId} className="activation-incomplete"><summary>Unfinished writing at step {attempt.observedStep}</summary><p>This retained response is incomplete ({attempt.stopReason}). It is not a saved journal and never entered feedback.</p><div className="activation-prose" tabIndex={0} aria-label="Complete retained unfinished response">{attempt.text}</div>{state.revealed && <p className="activation-small">Response hash: {attempt.responseSha256}</p>}</details>)}
    <details className="activation-timeline"><summary>Observation and feedback timeline · {session.events.length} events</summary><div className="activation-timeline-scroll" role="region" aria-label={`${seriesLabel(index)} observation and feedback timeline`} tabIndex={0}><ol>{activationTimeline(session).map(({ event, label: eventLabel, observation, failed }, i) => <li key={event.id} className={failed ? 'activation-event-failed' : ''}><strong>Event {i + 1} · step {event.step}</strong><span>{eventLabel}</span>{observation && <><blockquote style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', margin: '.5rem 0' }}>{observation.text}</blockquote><p className="activation-small">{observation.outcome === 'applied' ? `Received and applied at step ${observation.applicationStep} without sampled output.` : observation.outcome === 'requested' ? `Requested at step ${observation.requestedStep}. Scheduled application at step ${observation.scheduledStep}.` : `Requested at step ${observation.requestedStep}; held at step ${event.step}. No application is recorded for this observation.`}</p></>}{state.revealed && <><code>{event.id} · {event.kind}</code><p>{event.detail}</p></>}</li>)}</ol></div></details>
    <details className="activation-evidence"><summary>Evidence and condition labels</summary>{!state.revealed ? <><p>Read the prose before revealing which feedback condition produced it.</p><button onClick={() => controller.reveal()}>Reveal condition labels and exact evidence</button></> : <><dl className="activation-data"><dt>Condition</dt><dd>{ACTIVATION_ARM_NAMES[session.config.arm]}</dd><dt>Session</dt><dd>{session.sessionId}</dd><dt>Revision</dt><dd>{session.revision}</dd><dt>Model and runtime hash</dt><dd>{session.modelManifestSha256 ?? 'Unconfirmed · initialization has no retained identity'}</dd><dt>Calibration hash</dt><dd>{session.calibrationSha256 ?? 'Unconfirmed · initialization has no retained identity'}</dd><dt>Journal identity</dt><dd>{journal?.id ?? 'None selected'}</dd><dt>Journal hash</dt><dd>{journal?.sha256 ?? 'Unavailable'}</dd></dl><pre tabIndex={0}>{JSON.stringify({ config: session.config, diagnostic: session.diagnostic, annotations: session.annotations ?? [] }, null, 2)}</pre></>}</details>
    <button disabled={!!state.busy || activationRunning(state.current)} onClick={() => void controller.export(session.sessionId)}>Export this run…</button>
  </article>;
}

export default function ActivationExperiment({ active, controller = activationController }: { active: boolean; controller?: ActivationController }) {
  const state = useSyncExternalStore(controller.subscribe, controller.snapshot, controller.snapshot);
  const [config, setConfig] = useState<ActivationConfig>({ ...DEFAULT_ACTIVATION_CONFIG, observations: [...DEFAULT_ACTIVATION_CONFIG.observations] });
  const prepared = useCallback(({ pythonPath, modelPath }: ActivationRuntimePaths) => setConfig(previous => ({
    ...previous, pythonPath: previous.pythonPath || pythonPath, modelPath: previous.modelPath || modelPath,
  })), []);
  useEffect(() => {
    const visibility = () => controller.setActive(active && !document.hidden);
    visibility(); document.addEventListener('visibilitychange', visibility);
    return () => { document.removeEventListener('visibilitychange', visibility); controller.setActive(false); };
  }, [controller, active]);
  if (!active) return null;
  const current = state.current, busy = !!state.busy, running = activationRunning(current), comparison = comparisonStatus(state.comparisons);
  return <section className="activation-experiment" aria-label="Activation experiment"><header><h2>Activation experiment</h2><p>Let quiet observations shape a small state between pieces of writing. Compare a recurrent reservoir with a fading trace and no steering, using the same observation sequence.</p></header>
    <ActivationReadingCollection active={active}/><ActivationRuntimeSetup busy={busy || running} onReady={prepared}/>
    {state.error && <p role="alert" className="activation-error">{state.error}</p>}{state.message && <p role="status">{state.message}</p>}
    {current && <section className="activation-current" aria-label="Current activation run"><h3>{statusLabel(current.status)}</h3><p>Step {current.step} · {current.observationIndex} of {current.config.observations.length} quiet observations · {current.journalCount} of 6 journals</p><div className="activation-actions"><button className="primary-button" disabled={busy || running || !activationCanStart(current)} onClick={() => void controller.start()}>Start activation run</button><button disabled={busy || !running} onClick={() => void controller.stop()}>Stop and retain results</button><button disabled={busy} onClick={() => void controller.refresh()}>Refresh</button></div><p className="activation-small">Start loads the local model. Stop retains completed records and the outcome of an interrupted attempt. Failed work is never silently retried.</p>{current.diagnostic && <p role="alert">The run has a diagnostic to review in its evidence.</p>}</section>}
    {current ? <details className="activation-next"><summary>Prepare the next condition</summary><ActivationSetup state={state} config={config} setConfig={setConfig} controller={controller}/></details> : <ActivationSetup state={state} config={config} setConfig={setConfig} controller={controller}/>}
    {state.comparisons.length > 0 && <section aria-label="Activation journal comparison"><h3>Read the saved writing</h3><p>Condition labels begin concealed. Each reading keeps its own selected entry while another entry arrives.</p>{comparison === 'unconfirmed' && <p>Calibration or model/runtime identity is unconfirmed for at least one selected run. Matching settings alone do not establish a matched comparison.</p>}{comparison === 'different' && <p className="activation-error">These runs differ in recorded model/runtime identity, calibration, observations or numerical settings. Read them as separate experiments.</p>}{comparison === 'matched' && <p>Recorded model/runtime identity, calibration, observations and numerical settings match across these runs.</p>}<div className="activation-readers">{state.comparisons.map((session, index) => <ActivationReader key={session.sessionId} session={session} index={index} state={state} controller={controller}/>)}</div></section>}
    <details className="activation-saved"><summary>Saved activation runs and paused recovery</summary><p>Choose up to three runs for reading. Restoring or importing a run never starts model work.</p><div className="activation-actions"><button disabled={busy} onClick={() => void controller.list()}>Refresh saved activation runs</button><button disabled={busy || running} onClick={() => void controller.import()}>Import activation run…</button></div><ul>{state.saved.map((session, index) => <li key={session.sessionId}><label><input type="checkbox" checked={state.comparisons.some(s => s.sessionId === session.sessionId)} onChange={e => controller.compare(session, e.target.checked)}/>Saved run {index + 1} · {session.journalCount} entries · {statusLabel(session.status)}</label><button disabled={busy || running} onClick={() => void controller.restore(session.sessionId)}>Restore paused</button>{state.revealed && <small>{session.sessionId} · {ACTIVATION_ARM_NAMES[session.config.arm]}</small>}</li>)}</ul></details>
  </section>;
}
