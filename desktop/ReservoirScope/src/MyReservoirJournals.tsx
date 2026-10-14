import ProviderPromptEvidence from './ProviderPromptEvidence';
import JournalMeasurements from './JournalMeasurements';
import type { MyReservoirController, MyReservoirState } from './myReservoirController';
import { effectiveOutputTokens, effectiveRequestDeadline, type SustainedConfig, type SustainedJournal } from './myReservoirTypes';

const status = (value: SustainedJournal['status']) => value === 'applied' ? 'Saved and applied' : value === 'skipped' ? 'Saved · feedback explicitly skipped' : 'Saved · waiting for first application';
const json = (value: unknown) => value == null ? 'Not retained.' : JSON.stringify(value, null, 2);
export function MyReservoirJournalDetail({ journal, revision, config }: { journal: SustainedJournal; revision: string | null; config?: SustainedConfig }) {
  return <article className="my-reservoir-journal-detail">
    <span className="eyebrow">RETAINED JOURNAL</span>
    <h3>Writing at step {journal.observedStep}</h3>
    <p className="my-reservoir-journal-status"><strong>{status(journal.status)}</strong>{journal.firstAppliedStep !== null ? ` · first applied at step ${journal.firstAppliedStep}` : ' · no first application recorded'}</p>
    <div className="my-reservoir-journal-prose" style={{ whiteSpace: 'pre-wrap' }}>{journal.text}</div>
    {journal.status === 'savedPendingApplication' && <p className="my-reservoir-journal-return">Saved safely. This entry is waiting for its first application, so it is not yet eligible to return as memory in a later prompt.</p>}
    {journal.status === 'skipped' && <p className="my-reservoir-journal-return">This journal remains readable. Its feedback and automatic prompt-memory exposure were explicitly skipped.</p>}
    {journal.status === 'applied' && <p className="my-reservoir-journal-return">After a saved entry is applied, its text can enter later prompts and its encoded vector contributes to numerical input. This does not train the model.</p>}
    <JournalMeasurements value={journal.measurementReference} observedStep={journal.observedStep} promptVersion={journal.promptVersion}/>
    <details className="my-reservoir-journal-evidence">
      <summary>Evidence</summary>
      <h4>Journal and request identity</h4>
      <dl className="my-reservoir-data">
        <dt>Journal prompt version</dt><dd>{journal.promptVersion}</dd>
        {config && <><dt>Retained output ceiling</dt><dd>{effectiveOutputTokens(config)} tokens</dd><dt>Retained request deadline</dt><dd>{effectiveRequestDeadline(config)} seconds</dd></>}
        <dt>Entry identity</dt><dd className="my-reservoir-hash">{journal.entryId}</dd>
        <dt>Turn / attempt</dt><dd>{journal.turnId} / {journal.attemptId}</dd>
        <dt>Journal SHA-256</dt><dd className="my-reservoir-hash">{journal.sha256}</dd>
        <dt>Configured model</dt><dd>{journal.configuredModel ?? 'No model configured'}</dd>
        <dt>Returned model identity</dt><dd>{journal.providerModel ?? 'Not retained'}</dd>
        <dt>Request recorded started</dt><dd>{String(journal.requestStarted)}</dd>
        <dt>Provider completeness</dt><dd>{String(journal.providerComplete)}</dd>
        <dt>Stop reason / tokens</dt><dd>{journal.stopReason ?? 'Not retained'} / {journal.tokenCount ?? 'Not retained'}</dd>
        <dt>Captured session revision</dt><dd>{revision ?? 'Unavailable'}</dd>
      </dl>
      <ProviderPromptEvidence value={journal.providerPromptEvaluation} contextTokens={config?.language.contextTokens}/>
      {journal.timing && <section>
        <h4>Host request and save timing</h4>
        <p>Local host bookkeeping, separate from simulated time. A dispatch timestamp records transport handoff, not proof of provider receipt.</p>
        <dl className="my-reservoir-data">
          <dt>Attempt identity</dt><dd>{journal.timing.attemptId}</dd>
          <dt>Dispatch · epoch milliseconds</dt><dd>{journal.timing.dispatchedAtMs ?? 'Not retained / no model dispatch'}</dd>
          <dt>Response received · epoch milliseconds</dt><dd>{journal.timing.receivedAtMs ?? 'Not retained'}</dd>
          <dt>Transport duration · monotonic milliseconds</dt><dd>{journal.timing.transportDurationMs ?? 'Not retained'}</dd>
          <dt>Journal publication · epoch milliseconds</dt><dd>{journal.timing.publishedAtMs ?? 'Not retained'}</dd>
        </dl>
      </section>}
      <section>
        <h4>Exact prompt and observation</h4>
        {journal.promptVersion === 'reservoir-journal-v5' && <p>The v5 prompt uses a compact measurement subset. The full retained observation below also includes coordinates, spectra and other values that were not supplied as part of that readout. The exact prompt records what was supplied, including prior prose.</p>}
        <p>Recurrent coordinates and summaries are separate from sensory measurements. Reading or selecting a coordinate in this app does not edit this retained prompt.</p>
        <h5>Exact prompt</h5><pre>{journal.prompt}</pre>
        <h5>Versioned numerical observation</h5><pre>{json(journal.observation)}</pre>
        <p>Retained prompt context alone does not prove provider receipt. Request-start and response evidence remain separately recorded.</p>
      </section>
      <section>
        <h4>Retained full-text memory</h4>
        {journal.memory ? <>
          <p className="my-reservoir-hash">Entry {journal.memory.entryId} · SHA-256 {journal.memory.sha256}</p>
          <pre>{journal.memory.text}</pre>
          <p>Exact memory text retained with this opportunity. This is distinct from the reduced vector applied to the numerical system.</p>
        </> : <p>No prior journal text was retained as memory for this opportunity.</p>}
      </section>
      <section>
        <h4>Save and feedback provenance</h4>
        <dl className="my-reservoir-data">
          <dt>Saved entry</dt><dd>{journal.saveReceipt.entryId}</dd>
          <dt>Readback SHA-256</dt><dd className="my-reservoir-hash">{journal.saveReceipt.sha256}</dd>
          <dt>Owned path label</dt><dd>{journal.saveReceipt.relativePath} · never followed from this view</dd>
        </dl>
        <h5>Encoded features</h5><pre>{json(journal.encodedFeatures)}</pre>
        <h5>Prepared semantic vector</h5><pre>{json(journal.semanticVector)}</pre>
        <h5>Application evidence</h5><pre>{json(journal.application)}</pre>
        <p>The encoded vector changes input to the reservoir and separate sensory field; it does not train the model or recurrent weights. State differences also depend on the retained forcing, noise and controls.</p>
      </section>
      <section><h4>Raw received reply</h4><pre>{journal.rawReply}</pre></section>
    </details>
  </article>;
}
export default function MyReservoirJournals({ state, controller }: { state: MyReservoirState; controller: MyReservoirController }) {
  const summary = state.summary; if (!summary) return null;
  const newCount = Math.max(0, summary.journalCount - state.seenJournalCount), page = state.page;
  return <section className="my-reservoir-journals" aria-label="Independent journal reading"><header className="my-reservoir-journal-header"><div><span className="eyebrow">YOUR WRITING HISTORY</span><h2>Journals and their return</h2><p className="my-reservoir-small">{summary.journalCount} saved journals · {summary.turnCount} retained attempts. Your reading position never moves the live clock.</p></div><div className="my-reservoir-actions"><button aria-pressed={state.followLatest} disabled={state.readingPage} onClick={() => void controller.followLatest()}>Follow latest{!state.followLatest && newCount > 0 ? ` · ${newCount} new` : ''}</button><button disabled={state.readingPage} onClick={() => void controller.journals(page?.offset ?? 0)}>Refresh this page</button></div></header>
    {state.journalError && <p role="alert" className="my-reservoir-error">{state.journalError}</p>}
    <div className="my-reservoir-journal-grid"><div>{state.readingPage && <p role="status">Reading journal history…</p>}<ul className="my-reservoir-journal-list">{page?.entries.map(entry => <li key={entry.entryId}><button aria-pressed={state.journal?.entryId === entry.entryId} onClick={() => void controller.selectJournal(entry.entryId)}><strong>Step {entry.observedStep} · {status(entry.status)}</strong><span>{entry.textPreview}</span><span>{entry.firstAppliedStep === null ? 'No first application recorded' : `First applied ${entry.firstAppliedStep}`}</span></button></li>)}</ul>{page && <div className="my-reservoir-actions"><button disabled={state.readingPage || page.offset === 0} onClick={() => void controller.journals(Math.max(0, page.offset - 20))}>Newer</button><span className="my-reservoir-small">{page.total === 0 ? '0 journals' : `${page.offset + 1}–${page.offset + page.entries.length} of ${page.total}`}</span><button disabled={state.readingPage || !page.hasMore} onClick={() => void controller.journals(page.offset + 20)}>Older</button></div>}</div><div>{state.readingJournal && <p role="status">Reading selected journal…</p>}{state.journal ? <><MyReservoirJournalDetail journal={state.journal} revision={state.journalRevision} config={summary.config}/><button disabled={state.readingJournal} onClick={() => void controller.refreshJournal()}>Refresh selected application evidence</button></> : <div className="my-reservoir-empty"><h3>{summary.journalCount ? 'Choose a journal to read' : 'No saved journal yet'}</h3><p>Writing appears here after actual durable save and readback. Failed and pending outcomes remain distinct in session diagnostics.</p></div>}</div></div>
  </section>;
}
