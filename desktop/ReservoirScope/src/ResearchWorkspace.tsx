import { useEffect, useRef, useState } from 'react';
import { invoke, isTauri } from '@tauri-apps/api/core';
import MyReservoirConfig from './MyReservoirConfig';
import type { SustainedConfig, SustainedJournal } from './myReservoirTypes';
import JournalActionStrip from './JournalActionStrip';
import RunIdentity from './RunIdentity';
import { matchingActionResult, type JournalSession, type actionResultReference } from './journalActionResult';
import { validSonarView } from './sonar';
import './research.css';

type Run = { runId: string; generation: string; phase: string; savedPhase: string; step: number; journalCount: number; configurationRevision: number; metadata: { name?: string; experimentId?: string }; configuration: SustainedConfig; summary?: { canSkipFeedback?: boolean; canExtendLimits?: boolean; pendingLanguage?: { attemptId: number }; pendingEmbedding?: { attemptId: number }; pendingSave?: { entryId: string; attemptId: number }; pendingApplication?: { entryId: string; attemptId: number } } };
type ResearchJournal = SustainedJournal & { configuration: SustainedConfig; configurationRevision: number };
type JournalResult = { runId: string; generation: string; journal: ResearchJournal };
type Validation = { valid: boolean; issues?: { path: string; message: string }[]; executionChecks?: string };
export async function loadResearchMeasurements(session: JournalSession, reference: NonNullable<ReturnType<typeof actionResultReference>>) {
  const view = await researchRequest<unknown>('GET', `/v1/runs/${encodeURIComponent(session.sessionId)}/sonar`);
  if (!validSonarView(view, session.sessionId, session.generation)) throw new Error('The saved measurements do not match this run.');
  return matchingActionResult(view, reference);
}
type Operation = { id: string; path?: string; request?: unknown; status: string; result?: unknown; error?: { code: string; message: string } };
type Entry = { entryId: string; textPreview: string; observedStep: number; status: string };
type Page = { entries: Entry[]; total: number; nextCursor: string | null; snapshot: string };
type Settings = { original: SustainedConfig; configured: SustainedConfig; effective: SustainedConfig; configurationRevision: number; history: { revision: number; step: number; operationId: string; invalidated: string[]; config: SustainedConfig }[] };
type Experiment = { id: string; runIds: string[]; status: string };
export async function researchRequest<T>(method: string, path: string, body?: unknown): Promise<T> {
  if (!isTauri()) throw new Error('Open the native Reservoir Scope app to manage research runs.');
  return invoke<T>('research_request', { method, path, body: body ?? null, idempotencyKey: method === 'GET' ? null : crypto.randomUUID() });
}
export function configurationPatch(before: unknown, after: unknown): Record<string, unknown> {
  const a = before as Record<string, unknown>, b = after as Record<string, unknown>, patch: Record<string, unknown> = {};
  for (const key of new Set([...Object.keys(a), ...Object.keys(b)])) {
    if (JSON.stringify(a[key]) === JSON.stringify(b[key])) continue;
    const old = a[key], next = b[key];
    patch[key] = old && next && typeof old === 'object' && typeof next === 'object' && !Array.isArray(next)
      ? configurationPatch(old, next) : next ?? null;
  }
  return patch;
}
const message = (e: unknown) => e instanceof Error ? e.message : typeof e === 'object' && e && 'message' in e ? String(e.message) : String(e);
const initialRecipe = JSON.stringify({ version: 1, baseConfig: { language: { backend: 'scripted' } }, arms: [{ name: 'first', overrides: {} }, { name: 'second', overrides: {} }, { name: 'third', overrides: {} }], peerReading: false }, null, 2);

export default function ResearchWorkspace({ active, route, routeRequest = 0, closing = false, onKeepOpen }: { active: boolean; route: string | null; routeRequest?: number; closing?: boolean; onKeepOpen?: () => void }) {
  const [runs, setRuns] = useState<Run[]>([]), [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState(''), [operations, setOperations] = useState<Operation[]>([]);
  const [draft, setDraft] = useState<SustainedConfig | null>(null), [settings, setSettings] = useState<Settings | null>(null);
  const [edited, setEdited] = useState<SustainedConfig | null>(null), [page, setPage] = useState<Page | null>(null);
  const [journal, setJournal] = useState<JournalResult | null>(null), [recipe, setRecipe] = useState(initialRecipe);
  const [experiments, setExperiments] = useState<Experiment[]>([]), [concurrency, setConcurrency] = useState(1);
  const [busy, setBusy] = useState(false), [entryId, setEntryId] = useState<string | null>(null);
  const [intervention, setIntervention] = useState(JSON.stringify({ at: { step: 3600 }, kind: 'configuration', patch: { reservoirNodes: 48 } }, null, 2));
  const journalElement = useRef<HTMLElement>(null);
  const entryTicket = useRef(0);
  const [entryLoading, setEntryLoading] = useState(false);
  const [validation, setValidation] = useState<Validation | null>(null);
  const [actionText, setActionText] = useState('');
  const selectionEpoch = useRef(0);
  const [configurationJson, setConfigurationJson] = useState<string | null>(null);
  const [concurrencyDraft, setConcurrencyDraft] = useState<number | null>(null);
  const selectedRun = runs.find(r => r.runId === selected);
  const runPath = selected ? `/v1/runs/${encodeURIComponent(selected)}` : '';
  const refresh = async () => {
    try {
      const [catalog, ops, groups] = await Promise.all([
        researchRequest<{ runs: Run[]; scheduler: { maxConcurrentRequests: number } }>('GET', '/v1/runs'),
        researchRequest<Operation[]>('GET', '/v1/operations'),
        researchRequest<{ items: Experiment[] }>('GET', '/v1/experiments'),
      ]);
      setRuns(catalog.runs); setConcurrency(catalog.scheduler.maxConcurrentRequests); setOperations([...ops.filter(o => ["scheduled", "queued", "running", "needsAttention"].includes(o.status)), ...ops.filter(o => !["scheduled", "queued", "running", "needsAttention"].includes(o.status)).slice(0, 12)]); setExperiments(groups.items);
    } catch (e) { setError(message(e)); }
  };
  useEffect(() => {
    if (!active) return;
    void refresh();
    void researchRequest<{ defaultConfiguration: SustainedConfig }>('GET', '/v1/capabilities').then(c => setDraft(previous => previous ?? c.defaultConfiguration)).catch(e => setError(message(e)));
    const timer = setInterval(() => void refresh(), 2000); return () => clearInterval(timer);
  }, [active]);
  useEffect(() => {
    if (!route) return;
    const match = route.match(/^\/v1\/runs\/([^/]+)(?:\/entries\/([^/]+))?$/);
    if (match) { setSelected(match[1]); setEntryId(match[2] ?? null); }
  }, [route, routeRequest]);
  useEffect(() => {
    const epoch = ++selectionEpoch.current;
    setSettings(null); setEdited(null); setConfigurationJson(null); setPage(null); setJournal(null); setValidation(null);
    if (!selected || !active) return;
    void Promise.all([researchRequest<Settings>('GET', runPath + '/settings'), researchRequest<Page>('GET', runPath + '/entries')])
      .then(([s, p]) => { if (epoch !== selectionEpoch.current) return; setSettings(s); setEdited(s.effective); setPage(p); })
      .catch(e => { if (epoch === selectionEpoch.current) setError(message(e)); });
  }, [selected, active]);
  useEffect(() => {
    const ticket = ++entryTicket.current;
    if (!selected || !entryId || !active) { setJournal(null); setEntryLoading(false); return; }
    setEntryLoading(true);
    const epoch = selectionEpoch.current;
    void researchRequest<JournalResult>('GET', runPath + '/entries/' + encodeURIComponent(entryId))
      .then(v => { if (epoch === selectionEpoch.current && ticket === entryTicket.current) { setJournal(v); journalElement.current?.scrollTo({ top: 0 }); } })
      .catch(e => { if (epoch === selectionEpoch.current && ticket === entryTicket.current) setError(message(e)); })
      .finally(() => { if (ticket === entryTicket.current) setEntryLoading(false); });
    return () => { entryTicket.current++; };
  }, [selected, entryId, active]);
  const mutate = async (method: string, path: string, body?: unknown) => {
    setBusy(true); setError('');
    try {
      const operation = await researchRequest<Operation>(method, path, body);
      setOperations(prior => [operation, ...prior.filter(o => o.id !== operation.id)]);
      await refresh();
    } catch (e) { setError(message(e)); }
    finally { setBusy(false); }
  };
  const loadPage = async (cursor?: string) => {
    const epoch = selectionEpoch.current;
    try { const p = await researchRequest<Page>('GET', runPath + '/entries' + (cursor ? '?cursor=' + encodeURIComponent(cursor) : '')); if (epoch === selectionEpoch.current) setPage(p); }
    catch (e) { setError(message(e)); }
  };
  const validate = async (body: unknown) => {
    setValidation(null); setError('');
    try { setValidation(await researchRequest<Validation>('POST', '/v1/validate', body)); }
    catch (e) { setError(message(e)); }
  };
  if (!active) return null;
  return <section className="research-workspace" aria-labelledby="research-title">
    <header><h1 id="research-title">Research runs</h1><p>Prepare experiments, follow their journals, and record changes while they run.</p></header>
    {closing && <aside role="status"><p>Runs are settling before the app closes. Unfinished work stays retained for explicit recovery. Resolve any save failures, then finish closing.</p><button onClick={() => void invoke<boolean>("research_close").then(closed => { if (!closed) setError("A run is still settling or needs recovery. Review its retained status, then try closing again."); }).catch(e => setError(message(e)))}>Finish closing</button><button onClick={onKeepOpen}>Keep open</button></aside>}
    {error && <p role="alert" className="research-error">{error}</p>}
    <div className="research-layout">
      <aside aria-label="Runs"><h2>Runs</h2><button onClick={() => void refresh()}>Refresh</button>
        {!runs.length && <p>No runs yet. Create one below or prepare an experiment.</p>}
        <ul className="research-run-list">{runs.map(r => <li key={r.runId}><button aria-current={selected === r.runId ? 'true' : undefined} onClick={() => { setSelected(r.runId); setEntryId(null); }}><strong>{r.metadata?.name || r.configuration?.language.model || r.runId}</strong><span>{r.phase} · {r.journalCount} entries · step {r.step}</span></button></li>)}</ul>
      </aside>
      <div className="research-detail">{selectedRun ? <>
        <h2>{selectedRun.metadata?.name || selectedRun.configuration.language.model || 'Selected run'}</h2>
        <RunIdentity summary={{ sessionId: selectedRun.runId, generation: selectedRun.generation, config: selectedRun.configuration }}/><p><code>{selectedRun.runId}</code> · {selectedRun.phase} · configuration {selectedRun.configurationRevision}</p>
        <div className="research-actions">{['start', 'pause', 'resume', 'stop'].map(action => <button key={action} disabled={busy} onClick={() => void mutate('POST', runPath + '/actions/' + action)}>{action[0].toUpperCase() + action.slice(1)}</button>)}</div>
        <details><summary>Recovery and export</summary><div className="research-actions">{['retry-save', 'retry-writing', 'retry-encoding'].map(action => <button key={action} disabled={busy} onClick={() => void mutate('POST', runPath + '/actions/' + action)}>{action.replaceAll('-', ' ')}</button>)}{selectedRun.summary?.canSkipFeedback && <button disabled={busy} onClick={() => { const summary=selectedRun.summary!; const pending=summary.pendingSave ?? summary.pendingApplication ?? summary.pendingEmbedding ?? summary.pendingLanguage; void mutate('POST',runPath+'/actions/skip-feedback',{attemptId:pending?.attemptId,entryId:pending && 'entryId' in pending ? pending.entryId : undefined}); }}>Skip retained opportunity</button>}<button disabled={busy} onClick={() => void mutate('POST', runPath + '/exports')}>Save verified export</button></div><p>Results and any required recovery appear in Operations below. The CLI can download exports to your chosen directory.</p></details>
        <details><summary>Schedule an intervention</summary><p>Choose a step or active running time. The current turn settles before the intervention applies. Paused time does not count.</p>
          <div className="research-actions"><button onClick={() => setIntervention(JSON.stringify({ at: { step: selectedRun.step + 3600 }, kind: 'configuration', patch: { reservoirNodes: Math.max(48, selectedRun.configuration.reservoirNodes ?? 32), ...(selectedRun.configuration.sonar?.version === 'experiments-v3' ? { sonar: { ...selectedRun.configuration.sonar, version: 'experiments-v4' } } : {}) } }, null, 2))}>Grow the reservoir</button><button onClick={() => setIntervention(JSON.stringify({ at: { activeSeconds: 3600 }, kind: 'prompt', prompt: 'What have you noticed since our last conversation?', includeTelemetry: true }, null, 2))}>Ask a future question</button></div>
          <textarea aria-label="Scheduled intervention" value={intervention} rows={12} onChange={e => setIntervention(e.target.value)}/><button disabled={busy} onClick={() => { try { void mutate('POST', runPath + '/interventions', JSON.parse(intervention)); } catch(e) { setError(message(e)); } }}>Schedule</button>
        </details>
        <section className="research-reading" aria-label="Run journals">
          <nav aria-label="Journal entries"><h3>Journal</h3><button onClick={() => void loadPage()}>Newest entries</button>
            {page && <><p>{page.total} entries in this saved view</p><ol className="research-entry-list">{page.entries.map(entry => <li key={entry.entryId}><button aria-current={entryId === entry.entryId ? 'true' : undefined} onClick={() => setEntryId(entry.entryId)}><span>Step {entry.observedStep} · {entry.status}</span>{entry.textPreview}</button></li>)}</ol>{page.nextCursor && <button onClick={() => void loadPage(page.nextCursor!)}>Older entries</button>}</>}
          </nav>
          <article ref={journalElement} className="research-journal" aria-label="Selected journal entry" aria-busy={entryLoading}>
            {entryLoading && <p role="status">Loading selected entry…</p>}
            {journal ? <><h3>Step {journal.journal.observedStep} · configuration {journal.journal.configurationRevision}</h3>
              <RunIdentity summary={{ sessionId: journal.runId, generation: journal.generation, config: journal.journal.configuration }}/>
              <JournalActionStrip key={journal.journal.entryId} journal={journal.journal} config={journal.journal.configuration} session={{sessionId:journal.runId,generation:journal.generation}} loadMeasurements={loadResearchMeasurements}/>
              <div className="research-prose">{journal.journal.action?.body ?? journal.journal.text}</div>
              <details><summary>Exact prompt and retained evidence</summary><pre>{JSON.stringify(journal.journal, null, 2)}</pre></details></> : <p>Choose an entry to read. This pane stays on your selection while the run continues.</p>}
          </article>
        </section>
        <details><summary>Check an action before submitting it</summary><p>Validate ordinary-turn syntax against this run’s effective settings. Saved references and application-time bounds are checked only during execution.</p>
          <textarea aria-label="Action to validate" rows={8} value={actionText} onChange={e => setActionText(e.target.value)}/><button onClick={() => void validate({kind:'action',runId:selectedRun.runId,text:actionText})}>Check action</button>
        </details>
        <details><summary>Change this run’s settings</summary><p>The current turn finishes with its saved settings. Your change then applies at a recorded boundary. A running run continues automatically; a paused run stays paused.</p>
          {settings && edited && <><MyReservoirConfig config={edited} setConfig={next => { setEdited(next); setConfigurationJson(null); }} disabled={busy} />
            <button onClick={() => { try { void validate({kind:'configuration',runId:selectedRun.runId,config:configurationPatch(settings.effective,configurationJson===null?edited:JSON.parse(configurationJson))}); } catch(e) {setError(message(e));} }}>Check settings</button>
            <button disabled={busy} onClick={() => { try { void mutate('PATCH', runPath + '/settings', { expectedConfigurationRevision: settings.configurationRevision, patch: configurationPatch(settings.effective, configurationJson === null ? edited : JSON.parse(configurationJson)) }); } catch (e) { setError(message(e)); } }}>Apply at next boundary</button>
            {selectedRun.summary?.canExtendLimits && <button disabled={busy} onClick={() => void mutate('POST',runPath+'/actions/extend-limits',{ maximumSteps:edited.maximumSteps,maximumTurns:edited.maximumTurns,maximumDurationSeconds:edited.maximumDurationSeconds })}>Extend resource limits for the retained turn</button>}
            <button onClick={() => void researchRequest<Settings>('GET', runPath + '/settings').then(s => { setSettings(s); setEdited(s.effective); setConfigurationJson(null); }).catch(e => setError(message(e)))}>Reload effective settings</button>
            <details><summary>All settings as JSON</summary><textarea aria-label="Exact run configuration" rows={16} value={configurationJson ?? JSON.stringify(edited, null, 2)} onChange={e => setConfigurationJson(e.target.value)} /></details>
            <h3>Configuration history</h3>{settings.history.length ? settings.history.map(h => <details key={h.revision}><summary>Configuration {h.revision} · step {h.step}</summary><p>Reset context: {h.invalidated.join(', ') || 'none'}</p><pre>{JSON.stringify(h.config, null, 2)}</pre></details>) : <p>Original configuration; no changes recorded.</p>}</>}
        </details>
      </> : <p>Select a run to inspect its journal and settings. Selection does not affect execution.</p>}</div>
    </div>
    <details><summary>Create a run</summary>{draft && <><MyReservoirConfig config={draft} setConfig={setDraft} disabled={busy} /><button disabled={busy} onClick={() => void mutate('POST', '/v1/runs', { config: draft })}>Prepare run</button></>}</details>
    <details open={route?.startsWith("/v1/experiments/") || undefined}><summary>Experiment recipes</summary><p>A recipe prepares every arm before any model call. Start the prepared experiment when ready.</p><textarea aria-label="Experiment recipe" rows={18} value={recipe} onChange={e => setRecipe(e.target.value)} /><div className="research-actions"><button onClick={() => { try { void validate({kind:'recipe',recipe:JSON.parse(recipe)}); } catch(e) {setError(message(e));} }}>Check recipe</button><button disabled={busy} onClick={() => { try { void mutate('POST', '/v1/recipes', JSON.parse(recipe)); } catch (e) { setError(message(e)); } }}>Save recipe</button><button disabled={busy} onClick={() => { try { void mutate('POST', '/v1/experiments', JSON.parse(recipe)); } catch (e) { setError(message(e)); } }}>Prepare experiment</button></div>
      {experiments.map(e => <article key={e.id} aria-current={route === `/v1/experiments/${e.id}` ? "true" : undefined}><h3>{e.id}</h3><p>{e.runIds.length} runs · {e.status}</p>{e.runIds.map(id => <button key={id} onClick={() => { setSelected(id); setEntryId(null); }}>{runs.find(r => r.runId === id)?.metadata?.name || id}</button>)}<div className="research-actions">{['start', 'pause', 'resume', 'stop'].map(action => <button key={action} disabled={busy} onClick={() => void mutate('POST', `/v1/experiments/${e.id}/actions/${action}`)}>{action}</button>)}</div></article>)}
    </details>
    <details open={route === '/v1/settings'}><summary>Model request queue</summary><p>Reservoirs run independently. Writing and encoding share a fair queue per local endpoint.</p><label>Concurrent requests <input type="number" min={1} max={16} value={concurrencyDraft ?? concurrency} onChange={e => setConcurrencyDraft(Number(e.target.value))} /></label><button disabled={busy} onClick={() => void mutate('PATCH', '/v1/settings', { maxConcurrentRequests: concurrencyDraft ?? concurrency })}>Save concurrency</button></details>
    {validation && <section aria-label="Validation result" role="status"><h2>{validation.valid ? 'Validation passed' : 'Check these fields'}</h2>{validation.issues?.map((issue,i)=><p key={i}><code>{issue.path}</code>: {issue.message}</p>)}<p>{validation.executionChecks}</p></section>}
    <section aria-labelledby="research-operations"><h2 id="research-operations">Operations</h2>{!operations.length && <p>No operations yet.</p>}{operations.map(o => <details key={o.id}><summary>{o.status} · {o.id}</summary><p>{o.path}</p><pre>{JSON.stringify(o.request ?? {}, null, 2)}</pre>{["scheduled", "queued", "running"].includes(o.status) && (o.path?.endsWith("/settings") || o.path?.endsWith("/interventions")) && <button disabled={busy} onClick={() => void mutate("POST", `/v1/operations/${o.id}/cancel`, {})}>Cancel unapplied change</button>}{o.error && <p role="alert">{o.error.code}: {o.error.message}</p>}<pre>{JSON.stringify(o.result ?? {}, null, 2)}</pre></details>)}</section>
  </section>;
}
