import { useRef } from 'react';
import UiIcon from './UiIcon';
import { formatSessionDuration } from './sessionDuration';
import './myReservoirReading.css';
import ProviderPromptEvidence from './ProviderPromptEvidence';
import JournalMeasurements from './JournalMeasurements';
import { JournalActionDetails, actionReceiptStatus } from './MyReservoirActions';
import type { MyReservoirController, MyReservoirState } from './myReservoirController';
import { effectiveOutputTokens, effectiveRequestDeadline, type SustainedConfig, type SustainedJournal, type SustainedJournalRow } from './myReservoirTypes';

const withheld = (journal: Pick<SustainedJournal, 'actionReceipt'>) => journal.actionReceipt?.reservoirInput !== undefined && journal.actionReceipt.reservoirInput.disposition !== 'send';
const status = (journal: Pick<SustainedJournalRow, 'status' | 'actionReceipt'>) => journal.status === 'applied'
  ? withheld(journal) ? journal.actionReceipt?.reservoirInput?.disposition === 'rejected' ? 'Saved · input directive rejected; text input withheld' : 'Saved · text input withheld' : 'Saved · feedback applied'
  : journal.status === 'skipped' ? 'Saved · feedback skipped' : 'Saved · waiting for first application';
const json = (value: unknown) => value == null ? 'Not retained.' : JSON.stringify(value, null, 2);
export function MyReservoirJournalDetail({ journal, revision, config, onRefreshEvidence, refreshing = false }: { journal: SustainedJournal; revision: string | null; config?: SustainedConfig; onRefreshEvidence?: () => void; refreshing?: boolean }) {
  const body = journal.action?.body ?? journal.text;
  return <article className="my-reservoir-journal-detail">
    <span className="eyebrow">{journal.checkIn ? `SCHEDULED CHECK-IN ${journal.checkIn.ordinal}` : 'SAVED ENTRY'}</span>
    <h3>Entry at step {journal.observedStep}</h3>
    <p className="my-reservoir-journal-status"><strong>{status(journal)}</strong>{journal.firstAppliedStep !== null ? ` · first applied at step ${journal.firstAppliedStep}` : ' · no first application recorded'}</p>
    <div className="my-reservoir-journal-prose" style={{ whiteSpace: 'pre-wrap' }}>{body.trim() ? body : <span className="my-reservoir-small">No journal text in this entry.</span>}</div>
    {journal.status !== 'applied' && <p className="my-reservoir-journal-return">
      {journal.status === 'savedPendingApplication' ? 'Saved and checked. This entry is waiting for its first application, so it is not yet eligible to return as memory in a later prompt.' : 'This journal remains readable. Its feedback and automatic prompt-memory exposure were explicitly skipped.'}
    </p>}
    {journal.checkIn && <p>{journal.checkIn.includeTelemetry ? 'Telemetry and session context were supplied with the conversational prompt.' : 'Only the conversational prompt was supplied. Numerical observations below were retained internally, not sent to the model.'} {config?.actionMode && 'No action was requested or executed by this check-in.'}</p>}
    <JournalMeasurements value={journal.measurementReference} observedStep={journal.observedStep} promptVersion={journal.checkIn ? undefined : journal.promptVersion}/>
    <details className="my-reservoir-journal-evidence">
      <summary>Evidence</summary>
      <p className="my-reservoir-journal-return">{journal.status === 'applied' && <>{withheld(journal) ? 'Zero text input replaced the previous held input' : 'This entry’s feedback was first applied'} at step {journal.firstAppliedStep}. {journal.action ? 'Its journal body is eligible for later prompts. ' : 'Its full text is eligible for later prompts. '}</>}{journal.action ? 'Only the separate parsed action can change controls; prose is retained as writing.' : 'Describing a control change does not execute it.'}</p>
      {onRefreshEvidence && <button disabled={refreshing} onClick={onRefreshEvidence}>Refresh save and feedback details</button>}
      {journal.checkIn && <section><h4>Scheduled conversation</h4><dl className="my-reservoir-data">
        <dt>Check-in</dt><dd>{journal.checkIn.ordinal} · due at {formatSessionDuration(journal.checkIn.scheduledSeconds)}</dd>
        <dt>Prepared running time</dt><dd>{journal.checkIn.admittedElapsedMillis / 1000} seconds</dd>
        <dt>Prompt revision</dt><dd>{journal.checkIn.settingsRevision}</dd>
        <dt>Context mode</dt><dd>{journal.checkIn.includeTelemetry ? 'Telemetry + session context' : 'Plain prompt only'}</dd>
        <dt>Numerical observation supplied</dt><dd>{journal.observationSupplied ? 'Compact readout supplied; full observation retained internally' : 'Not supplied'}</dd>
      </dl><h5>Editable prompt used</h5><pre>{journal.checkIn.prompt}</pre><h5>Exact app-supplied system message</h5>{journal.systemContract ? <pre>{journal.systemContract}</pre> : <p>No app-supplied system message.</p>}</section>}
      <JournalActionDetails journal={journal}/>
      <h4>Journal and request identity</h4>
      <dl className="my-reservoir-data">
        <dt>{journal.checkIn ? 'Ordinary invitation version' : 'Journal prompt version'}</dt><dd>{journal.promptVersion}{journal.checkIn && ' · this check-in used the scheduled-conversation renderer'}</dd>
        {config && <><dt>Retained output ceiling</dt><dd>{effectiveOutputTokens(config)} tokens</dd><dt>Retained request deadline</dt><dd>{effectiveRequestDeadline(config)} seconds</dd></>}
        <dt>Entry identity</dt><dd className="my-reservoir-hash">{journal.entryId}</dd>
        <dt>Turn / attempt</dt><dd>{journal.turnId} / {journal.attemptId}</dd>
        <dt>Journal SHA-256</dt><dd className="my-reservoir-hash">{journal.sha256}</dd>
        <dt>Configured model</dt><dd>{journal.configuredModel ?? 'No model configured'}</dd>
        <dt>Returned model identity</dt><dd>{journal.providerModel ?? 'Not retained'}</dd>
        <dt>Request recorded started</dt><dd>{String(journal.requestStarted)}</dd>
        <dt>Provider completeness</dt><dd>{String(journal.providerComplete)}</dd>
        <dt>Stop reason / tokens</dt><dd>{journal.stopReason ?? 'Not retained'} / {journal.tokenCount ?? 'Not retained'}</dd>
        <dt>Text reduction</dt><dd>{journal.action?.reservoirInput && journal.action.reservoirInput.disposition !== 'send' ? 'Withheld · zero numerical text input; no embedding request' : journal.feedbackProvenance ? `Embedding · ${journal.feedbackProvenance.model} · ${journal.feedbackProvenance.dimensions} dims · sha256 ${journal.feedbackProvenance.embeddingSha256.slice(0, 12)}… · projection seed ${journal.feedbackProvenance.projectionSeed}` : 'Surface statistics'}</dd>
        <dt>Sampling</dt><dd>{journal.temperature == null ? 'Greedy · temperature 0 (historical or unset)' : journal.temperature === 0 ? 'Greedy · temperature 0' : `Temperature ${journal.temperature} · seed ${journal.samplingSeed ?? 'not retained'}`}</dd>
        <dt>Model thinking</dt><dd>{journal.thinking == null ? 'As built (field omitted)' : journal.thinking ? 'On' : 'Off · reply only'}</dd>
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
        {(!journal.checkIn && (journal.promptVersion === 'reservoir-journal-v5' || journal.promptVersion === 'reservoir-journal-v6' || journal.promptVersion === 'reservoir-journal-v7' || journal.promptVersion === 'reservoir-journal-v8')) && <p>The {journal.promptVersion.replace('reservoir-journal-', '')} prompt uses a compact measurement subset. The full retained observation below also includes coordinates, spectra and other values that were not supplied as part of that readout. The exact prompt records what was supplied, including prior prose.</p>}
        {journal.action && <p>{journal.promptVersion === 'reservoir-journal-actions-v3' ? 'The continuing inquiry prompt supplies a compact readout, controls, retained interventions, local inquiry evidence and a bounded prefix of any earlier journal body.' : 'The action prompt supplies a compact current readout, active controls, recent action results and any earlier journal body.'} The full observation below contains additional values retained for inspection.</p>}
        <p>Recurrent coordinates and summaries are separate from sensory measurements. Reading or selecting a coordinate in this app does not edit this retained prompt.</p>
        <h5>Exact prompt</h5><pre tabIndex={0} role="region" aria-label="Exact journal prompt">{journal.prompt}</pre>
        <h5>Versioned numerical observation</h5><pre tabIndex={0} role="region" aria-label="Numerical observation">{json(journal.observation)}</pre>
        <p>Retained prompt context alone does not prove provider receipt. Request-start and response evidence remain separately recorded.</p>
      </section>
      <section>
        <h4>{journal.promptVersion === 'reservoir-journal-actions-v3' ? 'Earlier writing supplied' : 'Retained full-text memory'}</h4>
        {journal.memory ? <>
          <p className="my-reservoir-hash">Entry {journal.memory.entryId} · SHA-256 {journal.memory.sha256}</p>
          {journal.memory.suppliedTextSha256 && <p className="my-reservoir-hash">{journal.memory.suppliedTextTruncated ? 'Supplied prefix SHA-256' : 'Supplied body SHA-256'}: {journal.memory.suppliedTextSha256}</p>}
          <pre tabIndex={0} role="region" aria-label="Previous journal text">{journal.memory.suppliedText ?? journal.memory.text}</pre>
          <p>{journal.memory.suppliedTextTruncated ? 'Only the bounded prefix above was supplied in this earlier-writing slot; the remaining body was not included in that slot. The entry identity and original SHA-256 refer to the complete saved response.' : journal.memory.suppliedText !== undefined ? 'The journal body above was supplied as earlier writing. The entry identity and original SHA-256 refer to the complete saved response.' : 'Exact memory text retained with this opportunity.'} This is distinct from the reduced vector applied to the numerical system.</p>
          {journal.memory.fullBodySha256 && <p className="my-reservoir-hash">Complete body · {journal.memory.fullBodyBytes} bytes · SHA-256 {journal.memory.fullBodySha256}{journal.memory.suppliedTextTruncated ? ' · supplied prefix limited to 2048 UTF-8 bytes' : ''}</p>}
          {journal.memory.suppliedText !== undefined && <details><summary>Original earlier journal · full response</summary><pre tabIndex={0} role="region" aria-label="Original earlier journal">{journal.memory.text}</pre></details>}
        </> : <p>No prior journal text was retained as memory for this opportunity.</p>}
      </section>
      {journal.latestShown && <section>
        <h4>Latest entry also shown</h4>
        <p className="my-reservoir-hash">Entry {journal.latestShown.entryId} · SHA-256 {journal.latestShown.sha256}</p>
        {journal.latestShown.suppliedTextSha256 && <p className="my-reservoir-hash">{journal.latestShown.suppliedTextTruncated ? 'Supplied prefix SHA-256' : 'Supplied body SHA-256'}: {journal.latestShown.suppliedTextSha256}</p>}
        <pre tabIndex={0} role="region" aria-label="Latest entry text">{journal.latestShown.suppliedText ?? journal.latestShown.text}</pre>
        {journal.latestShown.fullBodySha256 && <p className="my-reservoir-hash">Complete body · {journal.latestShown.fullBodyBytes} bytes · SHA-256 {journal.latestShown.fullBodySha256}{journal.latestShown.suppliedTextTruncated ? ' · only a prefix of at most 2048 UTF-8 bytes was supplied in this slot' : ''}</p>}
        {journal.latestShown.suppliedText !== undefined && <details><summary>Original latest journal · full response</summary><pre>{journal.latestShown.text}</pre></details>}
        <p>Under the two-entry prompt version the latest applied entry was shown after the chosen older entry above, marked only by order.</p>
      </section>}
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
  const reader = useRef<HTMLDivElement>(null);
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
        <p className="my-reservoir-small reader-update-status" role="status">{state.readingJournal ? 'Updating entry…' : `${summary.journalCount} saved entries`}</p>
      </div>
      <div className="my-reservoir-actions">
        <button className="icon-button" title="Open journal folder" aria-label={state.openingJournalFolder ? 'Opening folder…' : 'Open journal folder'} disabled={state.openingJournalFolder} onClick={() => void controller.openJournalFolder()}><UiIcon name="folder"/></button>
        <button aria-pressed={state.followLatest} disabled={!state.followLatest && state.readingPage} onClick={() => { if (state.followLatest) controller.pinJournal(); else { if (reader.current) reader.current.scrollTop = 0; void controller.followLatest(); } }}>{state.followLatest ? 'Pause following' : 'Follow latest'}{!state.followLatest && newCount > 0 ? ` · ${newCount} new` : ''}</button>
        <button className="icon-button" title="Refresh this page" aria-label="Refresh this page" disabled={state.readingPage} onClick={() => void controller.refreshJournals()}><UiIcon name="refresh"/></button>
      </div>
    </header>
    {state.journalError && <p role="alert" className="my-reservoir-error">{state.journalError}</p>}
    <div className="my-reservoir-journal-grid">
      <div>
        <nav className="my-reservoir-reading-navigation" aria-label="Journal reading position">
          <div>
            <strong aria-live="polite" aria-atomic="true">{position === null ? state.journal ? 'Selected journal' : 'Waiting for the first entry' : `Journal ${position} of ${total}`}</strong>
            <p>{position === null ? 'Choose an entry from a history window to establish its reading position.' : state.followLatest ? 'Following latest · scroll to hold this entry.' : selectedIndex < 0 ? 'Held entry · outside this history window.' : 'Held here as new writing arrives.'}</p>
          </div>
          <div className="my-reservoir-actions">
            <button disabled={reading || position === null || position <= 1} onClick={() => void controller.adjacentJournal('earlier')} title="Earlier entry" aria-label="Earlier entry"><UiIcon name="previous"/></button>
            <button disabled={reading || position === null || position >= total} onClick={() => void controller.adjacentJournal('later')} title="Later entry" aria-label="Later entry"><UiIcon name="next"/></button>
          </div>
        </nav>
        <div ref={reader} className="journal-reader-pane" tabIndex={0} role="region" aria-label="Journal entry" aria-busy={state.readingJournal} onScroll={event => { if (state.followLatest && event.currentTarget.scrollTop > 8) controller.pinJournal(); }} onPointerDown={() => { if (state.followLatest && state.journal) controller.pinJournal(); }}>
        {state.journal ? <MyReservoirJournalDetail
          journal={state.journal} revision={state.journalRevision} config={summary.config}
          onRefreshEvidence={() => void controller.refreshJournal()} refreshing={state.readingJournal}
        /> : <div className="my-reservoir-empty">
          <h3>{summary.journalCount ? 'Choose a journal to read' : 'No saved journal yet'}</h3>
          <p>Entries appear here after they are saved and checked. Pending or failed writing remains available in the session details.</p>
        </div>}
        </div>
      </div>
      <details className="journal-history-disclosure"><summary>Journal history</summary><section className="my-reservoir-history" aria-label="Journal history">
        <p className="my-reservoir-history-order" role="status">{state.readingPage ? 'Updating history…' : 'History · newest first'}</p>
        <ul className="my-reservoir-journal-list">{page?.entries.map(entry => <li key={entry.entryId}>
          <button aria-pressed={state.journal?.entryId === entry.entryId} onClick={() => void controller.selectJournal(entry.entryId)}>
            <strong>Step {entry.observedStep}</strong>
            <span className="my-reservoir-history-status">{status(entry)} · {entry.firstAppliedStep === null ? 'No first application recorded' : `First applied ${entry.firstAppliedStep}`}</span>
            {entry.actionReceipt && <span className="my-reservoir-history-status">{actionReceiptStatus(entry.actionReceipt)}</span>}
            <span>{entry.textPreview.trim() ? entry.textPreview : 'No journal text in this entry.'}</span>
          </button>
        </li>)}</ul>
        {page && <div className="my-reservoir-actions">
          <button disabled={state.readingPage || page.total - page.offset >= total} onClick={() => void controller.pageJournals('newer')}>Newer history</button>
          <span className="my-reservoir-small">{page.total === 0 ? '0 journals' : `${page.offset + 1}–${page.offset + page.entries.length} of ${page.total}`}</span>
          <button disabled={state.readingPage || !page.hasMore} onClick={() => void controller.pageJournals('older')}>Older history</button>
        </div>}
      </section></details>
    </div>
  </section>;
}
