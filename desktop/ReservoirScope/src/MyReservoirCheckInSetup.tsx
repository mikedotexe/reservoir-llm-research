import { DurationEditor } from './MyReservoirConfig';
import { checkInCapacity, checkInConfigurationError, checkInTimes, DEFAULT_CHECK_IN_SCHEDULE, MAX_CHECK_IN_PROMPT_BYTES, withCheckInCapacity } from './checkInSchedule';
import type { SustainedCheckInSchedule, SustainedConfig } from './myReservoirTypes';
import { formatSessionDuration } from './sessionDuration';

export function CheckInPromptFields({ prompt, includeTelemetry, onChange }: { prompt: string; includeTelemetry: boolean; onChange: (prompt: string, includeTelemetry: boolean) => void }) {
  return <>
    <label>Conversational prompt<textarea rows={5} value={prompt} required onChange={event => onChange(event.target.value, includeTelemetry)}/></label>
    <p className="my-reservoir-small">Keep the exact wording you want sent. Up to {MAX_CHECK_IN_PROMPT_BYTES.toLocaleString('en-US')} UTF-8 bytes.</p>
    <label className="my-reservoir-check-in-toggle"><input type="checkbox" checked={includeTelemetry} onChange={event => onChange(prompt, event.target.checked)}/>Include telemetry and session context</label>
    <p>{includeTelemetry
      ? 'Includes the actual current readout, the session’s selected earlier writing and its standing instructions alongside your prompt.'
      : 'Sends only your editable prompt. Earlier writing, reservoir readings and app instructions are not supplied.'} The response still feeds back into the reservoir.</p>
  </>;
}

export default function MyReservoirCheckInSetup({ config, setConfig }: { config: SustainedConfig; setConfig: (config: SustainedConfig) => void }) {
  const schedule = config.checkInSchedule, capacity = checkInCapacity(config), error = checkInConfigurationError(config);
  const update = (value: Partial<SustainedCheckInSchedule>) => setConfig(withCheckInCapacity({ ...config, checkInSchedule: { ...schedule!, ...value } }));
  return <section className="my-reservoir-check-in-setup" aria-label="Scheduled conversations setup">
    <h3>Scheduled conversations</h3>
    <label className="my-reservoir-check-in-toggle"><input type="checkbox" checked={!!schedule} onChange={event => {
      if (event.target.checked) setConfig(withCheckInCapacity({ ...config, checkInSchedule: { ...DEFAULT_CHECK_IN_SCHEDULE } }));
      else { const { checkInSchedule: _schedule, ...ordinary } = config; setConfig(ordinary); }
    }}/>Add conversational check-ins</label>
    {schedule && <>
      <p>Ordinary journaling continues between check-ins. The final answer is saved and its feedback applied before the run finishes.</p>
      <div className="my-reservoir-config-grid">
        <DurationEditor label="Run duration · final check-in" value={schedule.endAfterSeconds} onChange={endAfterSeconds => update({ endAfterSeconds })}/>
        <DurationEditor label="Conversation interval" value={schedule.intervalSeconds} onChange={intervalSeconds => update({ intervalSeconds })}/>
      </div>
      {config.actionMode && <p>Check-ins are conversations, not action turns. No action menu or action receipt is added to a plain prompt, and NEXT text in a check-in never executes a control. With telemetry on, current controls and recent action results are included as context.</p>}
      {config.actionMode === 'authored-v2' && <p>A text-input directive in a check-in is also ordinary writing. Check-in replies continue through the normal feedback path.</p>}
      <CheckInPromptFields prompt={schedule.prompt} includeTelemetry={schedule.includeTelemetry} onChange={(prompt, includeTelemetry) => update({ prompt, includeTelemetry })}/>
      {error ? <p role="alert">{error}</p> : <p>{checkInTimes(schedule).length} scheduled check-ins · every {formatSessionDuration(schedule.intervalSeconds)}, with the final one at {formatSessionDuration(schedule.endAfterSeconds)}. Set interval equal to duration for one final conversation.</p>}
      {capacity && <p className="my-reservoir-small">Capacity: {capacity.maximumSteps.toLocaleString('en-US')} steps and {capacity.maximumTurns.toLocaleString('en-US')} writing attempts, including retries. These limits are raised with the schedule; storage and failed writing can still hold the run.</p>}
      <p className="my-reservoir-small">Hours count running time, including writing, and exclude pauses and sleep. Requests wait for a safe writing boundary. You can change the prompt and context mode while paused; timings stay fixed.</p>
    </>}
  </section>;
}
