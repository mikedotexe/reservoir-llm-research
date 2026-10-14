import { useEffect, useState, useSyncExternalStore } from 'react';
import { PreparationController, type PreparationState } from './preparationController';
import type { PreparationAttempt } from './preparationTypes';
import './preparation.css';

const retained = (value: string | number | null) => value === null ? 'Not retained' : String(value);
function Attempt({ attempt, index }: { attempt: PreparationAttempt; index: number }) {
  return <section className="preparation-attempt" aria-label={`Retained generation attempt ${index + 1}`}>
    <h5>Retained generation attempt {index + 1}</h5>
    <dl className="preparation-fields">
      <div><dt>Recorded run outcome</dt><dd>{retained(attempt.status)}</dd></div>
      <div><dt>Historical record verification</dt><dd>{attempt.verified === null ? 'Not retained' : attempt.verified ? 'Passed · retained receipt' : 'Failed · retained receipt'}</dd></div>
      <div><dt>Recorded steps</dt><dd>{retained(attempt.steps)}</dd></div>
      <div><dt>Recorded requests</dt><dd>{retained(attempt.requestCount)}</dd></div>
      <div><dt>Saved journals by arm</dt><dd>{attempt.journalCounts === null ? 'Not retained' : Object.entries(attempt.journalCounts).map(([arm, count]) => `${arm}: ${count}`).join(' · ') || 'No journal counts recorded'}</dd></div>
      <div><dt>Process exit code</dt><dd>{retained(attempt.exitCode)}</dd></div>
      <div><dt>Started at UTC</dt><dd>{retained(attempt.startedAtUtc)}</dd></div>
      <div><dt>Finished at UTC</dt><dd>{retained(attempt.finishedAtUtc)}</dd></div>
      <div><dt>Historical record name · not followed</dt><dd>{retained(attempt.record)}</dd></div>
      <div><dt>Record SHA-256 retained in report</dt><dd><code>{retained(attempt.sha256)}</code></dd></div>
    </dl>
    {attempt.verification !== null && <p className="preparation-verification"><strong>Retained verification text:</strong> {attempt.verification}</p>}
    <p className="muted">A passed verification receipt describes the saved record. It does not turn a failed or partial run into a completed generation.</p>
  </section>;
}

export function PreparationHistoryView({ state, refresh, select, exportReport, onOpenExample, initiallyOpen = false }: {
  state: PreparationState; refresh: () => void; select: PreparationController['select']; exportReport: () => void;
  onOpenExample?: (id: string) => void; initiallyOpen?: boolean;
}) {
  const [expanded, setExpanded] = useState(initiallyOpen);
  return <details className="preparation-history" open={expanded} onToggle={event => setExpanded(event.currentTarget.open)}>
    <summary>Preparation history · all attempts retained</summary>
    <div className="preparation-content">
      <header><div><h3>Attempts, correction, and later retry</h3><p className="muted">Read-only retained evidence. Viewing and exporting makes no model request.</p></div><button onClick={refresh} disabled={state.busy}>Refresh history</button></header>
      <p>The original unavailable attempt, its protocol correction, and the later retry remain separate. Qualification attempts below retain both failed and completed outcomes.</p>
      {state.busy && <p role="status">Reading bundled preparation history…</p>}
      {state.pendingId && <p role="status">Reading {state.reports.find(r => r.id === state.pendingId)?.title ?? 'report'}…</p>}
      {state.error && <p className="error" role="alert">{state.error}</p>}
      {state.message && <p role="status" className="preparation-message">{state.message}</p>}
      <div className="preparation-reports" aria-label="Retained preparation reports">
        {state.reports.map(report => <button key={report.id} className={state.selected?.summary.id === report.id ? 'selected' : ''} aria-pressed={state.selected?.summary.id === report.id} onClick={() => { void select(report); }}>
          <strong>{report.title}</strong><span>Recorded status: {report.status}</span><span>{report.summary}</span>
        </button>)}
      </div>
      {state.selected && <article className="preparation-detail" aria-label="Selected preparation report">
        <header><div><h4>{state.selected.summary.title}</h4><p><strong>Recorded status: {state.selected.report.status}</strong></p></div><button disabled={state.exporting || state.pendingId !== null} onClick={exportReport}>{state.exporting ? 'Exporting…' : 'Export original report…'}</button></header>
        <p>{state.selected.summary.summary}</p>
        <p className="muted">{state.selected.report.inspectionScope}</p>
        {state.selected.report.scope !== null && <p><strong>Retained scope:</strong> {state.selected.report.scope}</p>}
        <p className="preparation-identity">{state.selected.summary.filename} · {state.selected.summary.sizeBytes.toLocaleString()} bytes<br/><span>Report SHA-256 <code>{state.selected.summary.sha256}</code></span></p>
        {state.selected.report.attempts.length > 0 ? state.selected.report.attempts.map((attempt, index) => <Attempt key={index} attempt={attempt} index={index}/>) : <p className="muted">{state.selected.summary.kind === 'correction' ? 'This is a protocol correction receipt, not a generation attempt.' : 'No generation attempts are retained in this report.'}</p>}
        {state.selected.retainedExampleDiagnostic && <p role="status">{state.selected.retainedExampleDiagnostic}</p>}
        {state.selected.retainedExampleId && onOpenExample && <div><button onClick={() => onOpenExample(state.selected!.retainedExampleId!)}>Open retained retry recording</button><p className="muted">Its packaged bytes match the report’s recorded SHA-256. Opening performs a separate offline verification before displaying the saved partial run.</p></div>}
        <details className="preparation-metadata"><summary>Inspect retained protocol and provenance fields</summary><p className="muted">Historical filenames and endpoints are shown as inert text. They are not opened or contacted.</p>
          {state.selected.report.sections.map((section, index) => <section key={index}><h5>{section.title}</h5><dl className="preparation-fields">{section.fields.map((field, fieldIndex) => <div key={fieldIndex}><dt>{field.label}</dt><dd>{field.value}</dd></div>)}</dl></section>)}
        </details>
      </article>}
      {state.examples.length > 0 && <section className="preparation-examples"><h4>Earlier model qualification attempts</h4><p className="muted">These are separate retained examples. Opening one runs the existing offline verification before accepting it into the reader.</p><ul>{state.examples.map(example => <li key={example.id}><div><strong>{example.title}</strong><p>{example.provenance}</p></div>{onOpenExample && <button onClick={() => onOpenExample(example.id)}>Open retained attempt</button>}</li>)}</ul></section>}
    </div>
  </details>;
}
export default function PreparationHistory({ active, onOpenExample, controller: supplied, initiallyOpen = false }: { active: boolean; onOpenExample?: (id: string) => void; controller?: PreparationController; initiallyOpen?: boolean }) {
  const [owned] = useState(() => new PreparationController());
  const controller = supplied ?? owned;
  const state = useSyncExternalStore(controller.subscribe, controller.snapshot, controller.snapshot);
  useEffect(() => { controller.activate(active); return () => controller.activate(false); }, [active, controller]);
  if (!active) return null;
  return <PreparationHistoryView state={state} refresh={() => { void controller.refresh(); }} select={summary => controller.select(summary)} exportReport={() => { void controller.export(); }} onOpenExample={onOpenExample} initiallyOpen={initiallyOpen}/>;
}
