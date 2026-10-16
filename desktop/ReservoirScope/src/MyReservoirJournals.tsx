import './myReservoirReading.css';
import ProviderPromptEvidence from './ProviderPromptEvidence';
import JournalMeasurements from './JournalMeasurements';
import type { MyReservoirController, MyReservoirState } from './myReservoirController';
import { effectiveOutputTokens, effectiveRequestDeadline, type SustainedConfig, type SustainedJournal } from './myReservoirTypes';

const status = (value: SustainedJournal['status']) => value === 'applied' ? 'Saved · feedback applied' : value === 'skipped' ? 'Saved · feedback skipped' : 'Saved · waiting for first application';
const json = (value: unknown) => value == null ? 'Not retained.' : JSON.stringify(value, null, 2);
export function MyReservoirJournalDetail({ journal, revision, config, onRefreshEvidence, refreshing = false }: { journal: SustainedJournal; revision: string | null; config?: SustainedConfig; onRefreshEvidence?: () => void; refreshing?: boolean }) {
  return <article className="my-reservoir-journal-detail">
    <span className="eyebrow">SAVED ENTRY</span>
    <h3>Entry at step {journal.observedStep}</h3>
    <p className="my-reservoir-journal-status"><strong>{status(journal.status)}</strong>{journal.firstAppliedStep !== null ? ` · first applied at step ${journal.firstAppliedStep}` : ' · no first application recorded'}</p>
    <div className="my-reservoir-journal-prose" style={{ whiteSpace: 'pre-wrap' }}>{journal.text}</div>
    {journal.status !== 'applied' && <p className="my-reservoir-journal-return">
      {journal.status === 'savedPendingApplication' ? 'Saved and checked. This entry is waiting for its first application, so it is not yet eligible to return as memory in a later prompt.' : 'This journal remains readable. Its feedback and automatic prompt-memory exposure were explicitly skipped.'}
    </p>}
    <JournalMeasurements value={journal.measurementReference} observedStep={journal.observedStep} promptVersion={journal.promptVersion}/>
    <details className="my-reservoir-journal-evidence">
      <summary>Evidence</summary>
      <p className="my-reservoir-journal-return">{journal.status === 'applied' && <>This entry’s feedback was first applied at step {journal.firstAppliedStep}. Its full text is eligible for later prompts. </>}Describing a control change does not execute it.</p>
      {onRefreshEvidence && <button disabled={refreshing} onClick={onRefreshEvidence}>Refresh save and feedback details</button>}
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
        {(journal.promptVersion === 'reservoir-journal-v5' || journal.promptVersion === 'reservoir-journal-v6' || journal.promptVersion === 'reservoir-journal-v7' || journal.promptVersion === 'reservoir-journal-v8') && <p>The {journal.promptVersion.replace('reservoir-journal-', '')} prompt uses a compact measurement subset. The full retained observation below also includes coordinates, spectra and other values that were not supplied as part of that readout. The exact prompt records what was supplied, including prior prose.</p>}
        <p>Recurrent coordinates and summaries are separate from sensory measurements. Reading or selecting a coordinate in this app does not edit this retained prompt.</p>
        <h5>Exact prompt</h5><pre tabIndex={0} role="region" aria-label="Exact journal prompt">{journal.prompt}</pre>
        <h5>Versioned numerical observation</h5><pre tabIndex={0} role="region" aria-label="Numerical observation">{json(journal.observation)}</pre>
        <p>Retained prompt context alone does not prove provider receipt. Request-start and response evidence remain separately recorded.</p>
      </section>
      <section>
        <h4>Retained full-text memory</h4>
        {journal.memory ? <>
          <p className="my-reservoir-hash">Entry {journal.memory.entryId} · SHA-256 {journal.memory.sha256}</p>
          <pre tabIndex={0} role="region" aria-label="Previous journal text">{journal.memory.text}</pre>
          <p>Exact memory text retained with this opportunity. This is distinct from the reduced vector applied to the numerical system.</p>
        </> : <p>No prior journal text was retained as memory for this opportunity.</p>}
      </section>
      <section>
        <h4>Save and feedback provenance</h4>
        <dl className="my-reservoir-data">
          <dt>Saved entry</dt><dd>{journal.saveReceipt.entryId}</dd>
          <dt>Readback SHA-256</dt><dd className="my-reservoir-hash">{journal.saveReceipt.sha256}</dd>
          <dt>Saved file path</dt><dd>{journal.saveReceipt.relativePath} · shown for reference</dd>
        </dl>
        <h5>Encoded features</h5><pre tabIndex={0} role="region" aria-label="Encoded text features">{json(journal.encodedFeatures)}</pre>
        <h5>Prepared semantic vector</h5><pre tabIndex={0} role="region" aria-label="Prepared feedback vector">{json(journal.semanticVector)}</pre>
        <h5>Application evidence</h5><pre tabIndex={0} role="region" aria-label="Feedback application evidence">{json(journal.application)}</pre>
        <p>The encoded vector changes input to the reservoir and separate sensory field; it does not train the model or recurrent weights. State differences also depend on the retained forcing, noise and controls.</p>
      </section>
      <section><h4>Raw received reply</h4><pre tabIndex={0} role="region" aria-label="Raw received reply">{journal.rawReply}</pre></section>
    </details>
  </article>;
}
export default function MyReservoirJournals({ state, controller }: { state: MyReservoirState; controller: MyReservoirController }) {
  const summary = state.summary; if (!summary) return null;
  const newCount = Math.max(0, summary.journalCount - state.seenJournalCount), page = state.page;
  const selectedIndex = page?.entries.findIndex(entry => entry.entryId === state.journal?.entryId) ?? -1;
  const position = state.journalPosition ?? (page && selectedIndex >= 0 ? page.total - page.offset - selectedIndex : null);
  const total = Math.max(summary.journalCount, page?.total ?? 0);
  const reading = state.readingPage || state.readingJournal;
  return <section className="my-reservoir-journals" aria-label="Independent journal reading">
    <header className="my-reservoir-journal-header">
      <div>
        <h2>Journal</h2>
        <p className="my-reservoir-small">{summary.journalCount} saved journals · reading never moves the live clock.</p>
        {(summary.pendingSave || summary.pendingLanguage || summary.pendingApplication) && <p className="my-reservoir-journal-progress" role="status">{summary.pendingSave
          ? `Writing at step ${summary.pendingSave.observedStep} · save not yet confirmed.`
          : summary.pendingLanguage
            ? `Writing at step ${summary.pendingLanguage.observedStep} · ${summary.pendingLanguage.state === 'blocked' ? 'needs attention' : summary.pendingLanguage.state === 'prepared' ? 'prepared, not yet dispatched' : summary.config.language.backend === 'scripted' ? 'preparing example writing' : 'waiting for the local model'}.`
            : `Saved writing at step ${summary.pendingApplication!.observedStep} · waiting for application at step ${summary.pendingApplication!.intendedStep}.`}</p>}
      </div>
      <div className="my-reservoir-actions">
        <button aria-pressed={state.followLatest} disabled={!state.followLatest && state.readingPage} onClick={() => state.followLatest ? controller.pinJournal() : void controller.followLatest()}>{state.followLatest ? 'Pause following' : 'Follow latest'}{!state.followLatest && newCount > 0 ? ` · ${newCount} new` : ''}</button>
        <button disabled={state.readingPage} onClick={() => void controller.refreshJournals()}>Refresh this page</button>
      </div>
    </header>
    {state.journalError && <p role="alert" className="my-reservoir-error">{state.journalError}</p>}
    <div className="my-reservoir-journal-grid">
      <div>
        {state.journal && <nav className="my-reservoir-reading-navigation" aria-label="Journal reading position">
          <div>
            <strong aria-live="polite" aria-atomic="true">{position === null ? 'Selected journal' : `Journal ${position} of ${total}`}</strong>
            <p>{position === null ? 'Choose an entry from a history window to establish its reading position.' : state.followLatest ? 'Following latest: new entries open automatically.' : selectedIndex < 0 ? 'Your selected entry is outside this history window. Earlier and Later continue from this entry.' : 'Your selection stays here as new writing arrives.'}</p>
          </div>
          <div className="my-reservoir-actions">
            <button disabled={reading || position === null || position <= 1} onClick={() => void controller.adjacentJournal('earlier')}>Earlier entry</button>
            <button disabled={reading || position === null || position >= total} onClick={() => void controller.adjacentJournal('later')}>Later entry</button>
          </div>
        </nav>}
        {state.readingJournal && <p role="status">Reading selected journal…</p>}
        {state.journal ? <MyReservoirJournalDetail
          key={`${summary.sessionId}:${summary.generation}:${state.journal.entryId}`}
          journal={state.journal} revision={state.journalRevision} config={summary.config}
          onRefreshEvidence={() => void controller.refreshJournal()} refreshing={state.readingJournal}
        /> : <div className="my-reservoir-empty">
          <h3>{summary.journalCount ? 'Choose a journal to read' : 'No saved journal yet'}</h3>
          <p>Entries appear here after they are saved and checked. Pending or failed writing remains available in the session details.</p>
        </div>}
      </div>
      <section className="my-reservoir-history" aria-label="Journal history">
        <p className="my-reservoir-history-order">History window · newest first</p>
        {state.readingPage && <p role="status">Reading journal history…</p>}
        <ul className="my-reservoir-journal-list">{page?.entries.map(entry => <li key={entry.entryId}>
          <button aria-pressed={state.journal?.entryId === entry.entryId} onClick={() => void controller.selectJournal(entry.entryId)}>
            <strong>Step {entry.observedStep}</strong>
            <span className="my-reservoir-history-status">{status(entry.status)} · {entry.firstAppliedStep === null ? 'No first application recorded' : `First applied ${entry.firstAppliedStep}`}</span>
            <span>{entry.textPreview}</span>
          </button>
        </li>)}</ul>
        {page && <div className="my-reservoir-actions">
          <button disabled={state.readingPage || page.total - page.offset >= total} onClick={() => void controller.pageJournals('newer')}>Newer history</button>
          <span className="my-reservoir-small">{page.total === 0 ? '0 journals' : `${page.offset + 1}–${page.offset + page.entries.length} of ${page.total}`}</span>
          <button disabled={state.readingPage || !page.hasMore} onClick={() => void controller.pageJournals('older')}>Older history</button>
        </div>}
      </section>
    </div>
  </section>;
}
