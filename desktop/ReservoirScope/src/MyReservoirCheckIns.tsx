import { useState } from 'react';
import type { MyReservoirController, MyReservoirState } from './myReservoirController';
import type { SustainedCheckInSlot, SustainedJournal } from './myReservoirTypes';
import { shuffleCheckInAnswers, validCheckInPrompt } from './checkInSchedule';
import { CheckInPromptFields } from './MyReservoirCheckInSetup';
import { formatSessionDuration } from './sessionDuration';
import { errorText } from './api';

const contextLabel = (telemetry: boolean) => telemetry ? 'Telemetry + session context' : 'Plain prompt';
const outcome = (status: string) => ({ pending: 'Not yet due', prepared: 'Prepared', requesting: 'Waiting for reply', failed: 'Needs attention', saved: 'Saved · feedback pending', applied: 'Saved · feedback applied', skipped: 'Skipped', missed: 'Missed', cancelled: 'Cancelled' })[status] ?? status;
function CheckInSlot({ slot, controller, reading }: { slot: SustainedCheckInSlot; controller: MyReservoirController; reading: boolean }) {
  return <li>
    <div><strong>Check-in {slot.ordinal} · {formatSessionDuration(slot.scheduledSeconds)}</strong><p>{outcome(slot.status)}{slot.settingsRevision != null && <> · prompt revision {slot.settingsRevision} · {contextLabel(!!slot.includeTelemetry)}</>}</p>
      {slot.admittedElapsedMillis != null && <p>Prepared at {formatSessionDuration(slot.admittedElapsedMillis / 1000)} running time · {Math.max(0, slot.admittedElapsedMillis - slot.scheduledSeconds * 1000) / 1000} seconds after due.</p>}
    </div>
    {slot.entryId && <button disabled={reading} onClick={() => void controller.selectJournal(slot.entryId!)}>Open answer and evidence</button>}
  </li>;
}
export function CheckInEditor({ state, controller }: { state: MyReservoirState; controller: MyReservoirController }) {
  const summary = state.summary!, settings = summary.checkIns!.settings;
  const [prompt, setPrompt] = useState(settings.prompt), [includeTelemetry, setIncludeTelemetry] = useState(settings.includeTelemetry);
  const changed = prompt !== settings.prompt || includeTelemetry !== settings.includeTelemetry;
  const invalid = !validCheckInPrompt(prompt), busy = !!state.busy;
  return <form onSubmit={event => { event.preventDefault(); if (changed && !invalid && !busy) void controller.updateCheckInSettings(prompt, includeTelemetry, summary.revision); }}>
    <fieldset disabled={busy}><legend>Future check-in settings · revision {settings.revision}</legend>
      <CheckInPromptFields prompt={prompt} includeTelemetry={includeTelemetry} onChange={(text, telemetry) => { setPrompt(text); setIncludeTelemetry(telemetry); }}/>
      {invalid && <p role="alert">Enter a nonempty prompt within the text limit.</p>}
      <button type="submit" disabled={!changed || invalid || busy}>Save future check-in settings</button>
    </fieldset>
    <p className="my-reservoir-small">Changes apply to check-ins not yet prepared. A prepared, failed or retried check-in keeps its original prompt and mode. Saving does not resume the run.</p>
  </form>;
}
export function CheckInReading({ answers, revealed, onReveal, onClose, onOpen }: { answers: SustainedJournal[]; revealed: boolean; onReveal: () => void; onClose: () => void; onOpen: (id: string) => void }) {
  return <section className="my-reservoir-check-in-reading" aria-label="Check-in answer reading">
    <div className="my-reservoir-actions">{!revealed && <button onClick={onReveal}>Reveal timeline and context</button>}<button onClick={onClose}>Close reading</button></div>
    <p>{revealed ? 'The same shuffled answers now show their recorded times and context. Changes in wording or mode provide another possible explanation for differences.' : 'Answers are shuffled. Note recurring curiosities, new distinctions, repetition and descriptions of experience before revealing the timeline. The writing itself may mention time or measurements.'}</p>
    {answers.map((answer, index) => <article className="my-reservoir-journal-detail" key={answer.entryId}>
      <h3>Response {index + 1}</h3>
      {revealed && answer.checkIn && <><p>Check-in {answer.checkIn.ordinal} · {formatSessionDuration(answer.checkIn.scheduledSeconds)} · prompt revision {answer.checkIn.settingsRevision} · {contextLabel(answer.checkIn.includeTelemetry)}</p><p>{outcome(answer.status === 'savedPendingApplication' ? 'saved' : answer.status)}</p><details><summary>Wording used</summary><pre>{answer.checkIn.prompt}</pre></details></>}
      <div className="my-reservoir-journal-prose" style={{ whiteSpace: 'pre-wrap' }}>{answer.text}</div>
      {revealed && <button onClick={() => onOpen(answer.entryId)}>Open answer and evidence</button>}
    </article>)}
  </section>;
}
export default function MyReservoirCheckIns({ state, controller, onBlindReadingChange }: { state: MyReservoirState; controller: MyReservoirController; onBlindReadingChange?: (blind: boolean) => void }) {
  const [answers, setAnswers] = useState<SustainedJournal[] | null>(null), [revealed, setRevealed] = useState(false), [loading, setLoading] = useState(false), [error, setError] = useState('');
  const summary = state.summary, checkIns = summary?.checkIns;
  if (!summary || !checkIns) return null;
  const savedCount = checkIns.slots.filter(slot => slot.entryId).length, next = checkIns.slots.find(slot => slot.status === 'pending'), blind = (loading || answers !== null) && !revealed;
  const read = async () => { setLoading(true); setRevealed(false); onBlindReadingChange?.(true); setError(''); try { const result = await controller.loadCheckInAnswers(); setAnswers(shuffleCheckInAnswers(result)); setRevealed(false); } catch (reason) { setError(errorText(reason)); onBlindReadingChange?.(false); } finally { setLoading(false); } };
  return <section className="my-reservoir-check-ins" aria-label="Scheduled conversations">
    <header><h2>Scheduled conversations</h2><p>{savedCount} saved answers from {checkIns.slots.length} scheduled check-ins · {checkIns.slots.length - savedCount} without a saved answer.</p>
      {!blind && <p>{checkIns.complete ? 'The schedule is complete. Every opportunity remains listed below, including those without an applied answer.' : next ? <>Next scheduled at {formatSessionDuration(next.scheduledSeconds)} running time{summary.elapsedSeconds >= next.scheduledSeconds ? ' · waiting for a safe writing boundary' : ` · in ${formatSessionDuration(next.scheduledSeconds - summary.elapsedSeconds)}`}.</> : 'Finishing the final check-in and its feedback.'}</p>}
    </header>
    {!answers && <button disabled={loading || savedCount === 0} onClick={() => void read()}>{loading ? 'Loading saved answers…' : 'Read answers without hour labels'}</button>}
    {error && <p role="alert">{error}</p>}
    {answers && <><p className="my-reservoir-small">This reading holds {answers.length} saved answers from when it was opened. Close and reopen to include later answers.</p><CheckInReading answers={answers} revealed={revealed} onReveal={() => { setRevealed(true); onBlindReadingChange?.(false); }} onClose={() => { setAnswers(null); onBlindReadingChange?.(false); }} onOpen={id => void controller.selectJournal(id)}/></>}
    {!blind && <>
      <details className="my-reservoir-details"><summary>Schedule and outcomes · {checkIns.slots.length} opportunities</summary><ul className="my-reservoir-check-in-slots">{checkIns.slots.map(slot => <CheckInSlot key={slot.ordinal} slot={slot} controller={controller} reading={state.readingJournal}/>)}</ul></details>
      <details className="my-reservoir-details"><summary>Edit future check-ins</summary>
        {checkIns.canEdit ? <CheckInEditor key={`${summary.sessionId}:${summary.generation}:${summary.revision}`} state={state} controller={controller}/> : <p>{checkIns.complete ? 'This schedule has finished.' : 'Pause and let any writing or saving settle before editing future check-ins.'}</p>}
        <p className="my-reservoir-small">The interval and final time stay fixed. Original settings and each accepted change remain in the saved history.</p>
      </details>
      <details className="my-reservoir-details"><summary>Prompt and context history · current revision {checkIns.settings.revision}</summary>{(checkIns.settingsHistory ?? [checkIns.settings]).map(settings => <section key={settings.revision}><h3>Revision {settings.revision} · {contextLabel(settings.includeTelemetry)}</h3>{'elapsedMillis' in settings && typeof settings.elapsedMillis === 'number' && <p>Saved at {formatSessionDuration(settings.elapsedMillis / 1000)} running time.</p>}<pre>{settings.prompt}</pre></section>)}</details>
    </>}
    <p className="my-reservoir-small">This is one developing sequence: earlier replies can affect later writing. Plain prompts receive no session history. Read descriptions of experience with curiosity; these answers alone do not establish subjective experience.</p>
  </section>;
}
