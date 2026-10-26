import { DurationEditor } from './MyReservoirConfig';
import { useState } from 'react';
import type { MyReservoirController, MyReservoirState } from './myReservoirController';
import type { SustainedLimits } from './myReservoirTypes';
import { addHour, extensionError, SESSION_LIMIT_CAPS, sessionLimits, validSessionLimits } from './sustainedLimits';
import { formatSessionDuration } from './sessionDuration';

export default function MyReservoirLimits({ state, controller }: { state: MyReservoirState; controller: MyReservoirController }) {
  const s = state.summary;
  if (!s || s.phase === 'stopped') return null;
  return <details className="my-reservoir-details">
    <summary>Extend session limits</summary>
    <p>Keep this journal going for longer. If running, pause first. Save higher limits, then continue when ready.</p>
    {s.canExtendLimits
      ? <LimitEditor key={`${s.sessionId}:${s.generation}:${s.revision}`} state={state} controller={controller}/>
      : <p>{s.phase === 'storageHeld' || s.phase === 'storageBlocked'
        ? 'A storage hold or unresolved save needs attention before this session can be extended.'
        : 'Pause and resolve any writing or saving in progress before extending the session.'}</p>}
    <p className="my-reservoir-small">Each change is saved with the session. Earlier writing and original settings stay in its history. Storage keeps its existing limit.</p>
  </details>;
}

export function LimitEditor({ state, controller }: { state: MyReservoirState; controller: MyReservoirController }) {
  const s = state.summary!, current = sessionLimits(s);
  const [proposed, setProposed] = useState<SustainedLimits>(current);
  const error = extensionError(current, proposed), busy = !!state.busy;
  return <form onSubmit={event => { event.preventDefault(); if (!error && !busy) void controller.extendLimits(proposed, s.revision); }}>
    <p>Current totals: {formatSessionDuration(current.maximumDurationSeconds)}, {current.maximumTurns.toLocaleString()} writing attempts and {current.maximumSteps.toLocaleString()} steps.</p>
    <fieldset disabled={busy}>
      <legend>New total limits</legend>
      <button type="button" disabled={proposed.maximumDurationSeconds >= 86400} onClick={() => setProposed(addHour(validSessionLimits(proposed) ? proposed : current, s.config))}>{proposed.maximumDurationSeconds > 82800 ? 'Extend to 24 hours' : 'Add 1 hour'}</button>
      <p className="my-reservoir-small">Also adds step and attempt capacity at the requested pace. Review the totals below; the first limit reached still holds the session.</p>
      <DurationEditor label="New total duration" value={proposed.maximumDurationSeconds} onChange={maximumDurationSeconds => setProposed({ ...proposed, maximumDurationSeconds })}/>
      <div className="my-reservoir-config-grid">
        <label>Total writing attempts · including retries<input type="number" min={current.maximumTurns} max={SESSION_LIMIT_CAPS.maximumTurns} value={Number.isFinite(proposed.maximumTurns) ? proposed.maximumTurns : ''} onChange={e => setProposed({ ...proposed, maximumTurns: e.target.value === '' ? NaN : Number(e.target.value) })}/></label>
        <label>Total numerical steps<input type="number" min={current.maximumSteps} max={SESSION_LIMIT_CAPS.maximumSteps} value={Number.isFinite(proposed.maximumSteps) ? proposed.maximumSteps : ''} onChange={e => setProposed({ ...proposed, maximumSteps: e.target.value === '' ? NaN : Number(e.target.value) })}/></label>
      </div>
      <p>{formatSessionDuration(proposed.maximumDurationSeconds)} total · up to 24 hours per session.</p>
      {error && <p className="my-reservoir-small">{error}</p>}
      <button type="submit" disabled={busy || !!error}>Save extended limits</button>
    </fieldset>
  </form>;
}
