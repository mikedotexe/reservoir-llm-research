import { useEffect, useRef, useState } from 'react';
import { errorText } from './api';
import { activationReadingApi } from './activationReadingApi';
import type { ActivationReadingApi, CollectionReading, OpenedReadingCollection } from './activationReadingTypes';
import './activationReading.css';

const armNames = { no_steering: 'No steering', decaying_trace: 'Decaying trace', recurrent: 'Recurrent reservoir' };
function eventName(kind: string, observation: string | null) {
  return ({ requestStarted: observation === null ? 'Writing requested' : 'Quiet observation requested', quietReceived: 'Quiet observation applied · zero sampled tokens', journalReceived: 'Complete writing received', journalSaved: 'Journal saved and read back', journalApplied: 'Journal feedback applied', failed: 'Attempt held' })[kind] ?? 'Recorded event';
}

export function ActivationCollectionReader({ reading, index, position, revealed, select }: {
  reading: CollectionReading; index: number; position: number; revealed: boolean; select: (position: number) => void;
}) {
  const label = `Reading ${String.fromCharCode(65 + index)}`;
  const entry = reading.entries[position];
  if (!entry) return <p role="alert">This selected writing is unavailable.</p>;
  const complete = reading.entries.filter(e => e.status === 'complete').length;
  const unfinished = reading.entries.length - complete;
  return <article className="activation-collection-reading" aria-label={label}>
    <header><h4>{label}{revealed ? ` · ${armNames[reading.disclosure.arm]}` : ''}</h4><p>{complete} completed {complete === 1 ? 'journal' : 'journals'}{unfinished ? ` · ${unfinished} unfinished response` : ''}</p></header>
    <nav className="activation-collection-actions" aria-label={`${label} chronology`}>
      <button disabled={position === 0} onClick={() => select(position - 1)}>Earlier</button>
      <button disabled={position === reading.entries.length - 1} onClick={() => select(position + 1)}>Later</button>
      <span>{entry.status === 'incomplete' ? 'Unfinished response' : 'Entry'} {position + 1} of {reading.entries.length}</span>
    </nav>
    {entry.status === 'incomplete' && <p className="activation-collection-incomplete">Unfinished response · retained in full. It was not saved as a journal or applied as feedback.{entry.stopReason === 'max_tokens' ? ' The attempt ended at its output ceiling.' : ''}</p>}
    <div key={`${reading.id}:${entry.id}`} className="activation-collection-prose" tabIndex={0} aria-label={`${label} selected writing`}>{entry.text}</div>
    <p className="activation-collection-small">Observed at step {entry.observedStep}. {entry.status === 'complete' ? `Saved and read back at step ${entry.savedStep}; feedback first applied at step ${entry.appliedStep}.` : 'No save or feedback application.'} Reading does not advance numerical time.</p>
    <details><summary>Quiet observations and writing boundaries</summary><ol className="activation-collection-timeline">{reading.events.map(event => <li key={event.id}><strong>Step {event.step} · {eventName(event.kind, event.observation)}</strong>{event.observation !== null && <blockquote>{event.observation}</blockquote>}{entry.eventIds.includes(event.id) && <span className="activation-collection-small">Boundary linked to the selected writing</span>}</li>)}</ol></details>
    {revealed && <>
      <details><summary>Exact invitation and retained evidence</summary><p>This is the complete submitted prompt for the selected writing. Quiet observations were processed separately; earlier saved prose is a separate memory path.</p><pre tabIndex={0}>{entry.prompt}</pre>
        <dl><dt>Attempt</dt><dd>{reading.disclosure.sourceAttempt}</dd><dt>Model</dt><dd>{reading.disclosure.modelId}</dd><dt>Revision</dt><dd>{reading.disclosure.modelRevision}</dd><dt>Text SHA-256</dt><dd>{entry.sha256}</dd><dt>Prompt SHA-256</dt><dd>{entry.promptSha256}</dd><dt>Source response SHA-256</dt><dd>{entry.sourceResponseSha256}</dd><dt>Source record SHA-256</dt><dd>{reading.disclosure.recordSha256}</dd><dt>Model/runtime SHA-256</dt><dd>{reading.disclosure.modelManifestSha256}</dd><dt>Calibration SHA-256</dt><dd>{reading.disclosure.calibrationSha256}</dd><dt>Content tokens</dt><dd>{entry.contentTokens}</dd><dt>Stop reason</dt><dd>{entry.stopReason}</dd></dl>
        <pre tabIndex={0}>{JSON.stringify({ sourceSession: reading.disclosure.sourceSession, sourceFormat: reading.disclosure.sourceFormat, protocol: reading.disclosure.protocol, eventIds: entry.eventIds }, null, 2)}</pre>
      </details>
      <details><summary>Earlier interpretations and alternatives</summary><p>These attributed passages are readings of the text. They do not establish an intervention effect or internal experience.</p>{reading.disclosure.notes.map((note, i) => <section key={`${note.sha256}-${i}`}><h5>{note.title}</h5><div className="activation-collection-note">{note.text}</div><p className="activation-collection-small">{note.attribution}</p><details><summary>Note identity</summary><p>Selected text SHA-256: {note.sha256}</p><p>Original account SHA-256: {note.sourceSha256}</p></details></section>)}</details>
    </>}
  </article>;
}

/** A reading-only path: this module has no activation worker/session API. */
export default function ActivationReadingCollection({ api = activationReadingApi, active = true }: { api?: ActivationReadingApi; active?: boolean }) {
  const [opened, setOpened] = useState<OpenedReadingCollection | null>(null);
  const [positions, setPositions] = useState<Record<string, number>>({});
  const [revealed, setRevealed] = useState(false), [busy, setBusy] = useState(false);
  const [error, setError] = useState(''), [message, setMessage] = useState('');
  const owned = useRef<string | null>(null), alive = useRef(true);
  useEffect(() => { alive.current = true; return () => { alive.current = false; if (owned.current) { void api.close(owned.current).catch(() => {}); owned.current = null; } }; }, [api]);
  async function open(bundled: boolean) {
    if (busy) return;
    setBusy(true); setError(''); setMessage('');
    try {
      const result = await api.open(bundled);
      if (!alive.current) { if (result) await api.close(result.collectionId); return; }
      if (!result) { setMessage('Open cancelled. The current reading is unchanged.'); return; }
      const prior = owned.current;
      owned.current = result.collectionId; setOpened(result); setPositions({}); setRevealed(false);
      setMessage('Opened for offline reading. No model request was made.');
      if (prior) await api.close(prior);
    } catch (e) { if (alive.current) setError(errorText(e)); }
    finally { if (alive.current) setBusy(false); }
  }
  async function exportReading() {
    if (!opened || busy) return;
    setBusy(true); setError(''); setMessage('');
    try { const proof = await api.export(opened.collectionId); if (alive.current) setMessage(proof ? `Verified portable collection saved: ${proof.name}` : 'Export cancelled.'); }
    catch (e) { if (alive.current) setError(errorText(e)); }
    finally { if (alive.current) setBusy(false); }
  }
  if (!active) return null;
  return <section className="activation-collection" aria-label="Offline activation reading collection"><h3>Begin with the writing</h3>
    <p>Read two retained historical sequences before preparing a model. The examples open offline and keep every completed entry and the entire unfinished response.</p>
    <div className="activation-collection-actions"><button disabled={busy} onClick={() => void open(true)}>Read the included examples</button><button disabled={busy} onClick={() => void open(false)}>Open a reading collection…</button>{opened && <button disabled={busy} onClick={() => void exportReading()}>Export this reading collection…</button>}</div>
    {error && <p role="alert">{error}</p>}{message && <p role="status">{message}</p>}
    {opened && <><h3>{opened.collection.title}</h3><p>{opened.collection.scope}</p>
      <details><summary>Questions to keep beside the writing</summary><ol>{opened.collection.questions.map((question, index) => <li key={index}>{question}</li>)}</ol></details>
      <p>Condition labels and earlier interpretations begin concealed. Read each sequence chronologically; these historical attempts do not form a matched comparison.</p>
      {!revealed ? <button onClick={() => setRevealed(true)}>Reveal conditions, invitations and interpretations</button> : <p className="activation-collection-small">Allocation is revealed for both readings. Reopening a collection conceals it again.</p>}
      <div className="activation-collection-readers">{opened.collection.readings.map((reading, index) => <ActivationCollectionReader key={reading.id} reading={reading} index={index} position={positions[reading.id] ?? 0} revealed={revealed} select={position => setPositions(previous => ({ ...previous, [reading.id]: position }))}/>)}</div>
      <details><summary>About this portable collection</summary><p>This is a reading derivative with checked text, prompt and note hashes. It does not contain the complete numerical evidence and cannot start or resume an experiment. Source-file hashes identify the retained originals; this file alone cannot authenticate those unavailable originals.</p><p>Collection SHA-256: <code>{opened.sha256}</code></p><p>Export preserves the exact opened bytes. Condition concealment is a reading aid; the file contains its allocation for reproducibility.</p></details>
    </>}
  </section>;
}
