import { useEffect, useId, useRef, useState, useSyncExternalStore } from 'react';
import { ActivationSetupController } from './activationSetupController';
import { activationSetupCanPrepare, activationSetupCanResume, type ActivationRuntimePaths, type ActivationSetupState } from './activationSetupTypes';
import './activationRuntimeSetup.css';

const stateLabels: Record<ActivationSetupState, string> = {
  missing: 'Runtime not prepared', preparing: 'Preparing activation runtime', interrupted: 'Preparation interrupted',
  ready: 'Activation runtime ready', failed: 'Preparation needs attention', unsupported: 'Activation unavailable on this computer',
};

export function setupBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes.toLocaleString('en-US')} bytes`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KiB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MiB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GiB`;
}

interface Props {
  busy?: boolean;
  onReady?: (paths: ActivationRuntimePaths) => void;
  controller?: ActivationSetupController;
}

export default function ActivationRuntimeSetup({ busy = false, onReady, controller: suppliedController }: Props) {
  const [ownedController] = useState(() => new ActivationSetupController());
  const controller = suppliedController ?? ownedController;
  const state = useSyncExternalStore(controller.subscribe, controller.snapshot, controller.snapshot);
  const id = useId(), notified = useRef('');
  const { status, pending, checking, error } = state;
  const preparing = status?.state === 'preparing';
  const hasTotal = status?.totalBytes !== null && status?.totalBytes !== undefined && status.totalBytes > 0;
  const hasReceived = status?.downloadedBytes !== null && status?.downloadedBytes !== undefined;

  useEffect(() => {
    controller.setActive(true);
    return () => controller.setActive(false);
  }, [controller]);

  useEffect(() => {
    if (status?.state !== 'ready' || !status.pythonPath || !status.modelPath) { notified.current = ''; return; }
    const key = JSON.stringify([status.setupId, status.pythonPath, status.modelPath]);
    if (notified.current === key || !onReady) return;
    notified.current = key;
    onReady({ pythonPath: status.pythonPath, modelPath: status.modelPath });
  }, [status, onReady]);

  return <section className="activation-runtime-setup" aria-labelledby={`${id}-title`}>
    <h3 id={`${id}-title`}>Prepare activation runtime</h3>
    <p>Read examples immediately, or prepare this Mac for new writing. Preparation installs a private Python runtime, its pinned dependencies, and the pinned Qwen3 4B model. Downloads begin only when you choose Prepare.</p>
    <p className="activation-runtime-requirements">Activation requires Apple Silicon and macOS 26 or later. This preview was tested on macOS 27.0.1. First preparation downloads approximately 2.23 GiB of model and dependency files and requires 8 GiB of free storage. Preparation does not run the model; Create and Start follow separately.</p>
    <div className="activation-runtime-status" role="status" aria-live="polite" aria-atomic="true">
      <strong>{pending === 'cancel' ? 'Cancelling preparation…' : pending === 'prepare' || pending === 'resume' ? 'Starting preparation…' : status ? stateLabels[status.state] : checking ? 'Checking local setup…' : 'Setup status has not been checked'}</strong>
      {status?.message && <p>{status.message}</p>}
    </div>
    {error && <p className="activation-runtime-error" role="alert">{error}</p>}
    {preparing && <div className="activation-runtime-progress">
      <label htmlFor={`${id}-progress`}>{status.phase ? `Current phase: ${status.phase.replaceAll('_', ' ').replaceAll('-', ' ')}` : 'Preparation in progress'}</label>
      <progress id={`${id}-progress`} aria-label="Current preparation phase progress" {...(hasTotal && hasReceived ? { value: Math.min(status.downloadedBytes!, status.totalBytes!), max: status.totalBytes! } : {})}/>
      {hasReceived && <span>{setupBytes(status.downloadedBytes!)} received{hasTotal ? ` of ${setupBytes(status.totalBytes!)}` : ''}</span>}
    </div>}
    {status && status.state !== 'ready' && status.state !== 'unsupported' && <dl className="activation-runtime-sizes">
      <dt>Current file download size</dt><dd>{hasTotal ? setupBytes(status.totalBytes!) : 'Not yet reported'}</dd>
      <dt>Storage required</dt><dd>{status.requiredBytes !== undefined && status.requiredBytes !== null ? setupBytes(status.requiredBytes) : 'Not yet reported'}</dd>
    </dl>}
    <div className="activation-runtime-actions">
      {activationSetupCanPrepare(status) && <button className="primary-button" disabled={busy || checking || !!pending || !!error} onClick={() => void controller.prepare(false)}>Prepare activation runtime</button>}
      {activationSetupCanResume(status) && <button className="primary-button" disabled={busy || checking || !!pending || !!error} onClick={() => void controller.prepare(true)}>Resume preparation</button>}
      {preparing && <button disabled={!!pending} onClick={() => void controller.cancel()}>Cancel preparation</button>}
      <button disabled={!!pending || checking} onClick={() => void controller.refresh()}>{checking ? 'Checking setup status…' : 'Check setup status'}</button>
    </div>
    {busy && !preparing && status?.state !== 'ready' && status?.state !== 'unsupported' && <p>Finish or stop the current experiment before preparing its runtime.</p>}
    {(status?.state === 'interrupted' || status?.state === 'failed') && <p>{activationSetupCanResume(status) ? 'Preparation remains paused until you choose Resume preparation.' : activationSetupCanPrepare(status) ? 'Resolve the reported issue before choosing Prepare activation runtime again.' : 'Resolve the reported issue and check setup status before continuing.'} Recognized partial downloads are retained.</p>}
    {preparing && <p>Keep the app open during preparation. Each attempt has a 30-minute deadline. Cancel retains recognized partial downloads; returning later never resumes them automatically.</p>}
    {status?.state === 'ready' && <p>Local assets and dependencies have been verified. Check the experiment settings below before creating a run. Start performs a separate memory check before loading the model.</p>}
    {status?.state === 'unsupported' && <p>The offline examples remain available. Activation preparation will not start on this computer.</p>}
    <details className="activation-runtime-help"><summary>Preparation and recovery</summary>
      <p>No Terminal is needed. Choose Prepare, leave the app open, and wait for “Activation runtime ready.” The app stores its own versioned runtime and model under Application Support.</p>
      <p>If preparation stops, read the message above, resolve the reported issue, and use Check setup status. Resume preparation is offered only for a recognized interrupted installation. Creating an experiment and starting its model work always remain explicit choices.</p>
    </details>
    {status && <details className="activation-runtime-evidence"><summary>Local setup evidence</summary>
      <p>This is a local setup receipt. It does not establish that a model request will finish or that steering improves the writing.</p>
      <pre tabIndex={0} aria-label="Local activation setup status">{JSON.stringify(status, null, 2)}</pre>
    </details>}
  </section>;
}
