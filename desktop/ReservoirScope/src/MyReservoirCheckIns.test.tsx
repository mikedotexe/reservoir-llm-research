import { Children, isValidElement, type ReactElement, type ReactNode } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { MyReservoirStatus } from './MyReservoir';
import MyReservoirConfig from './MyReservoirConfig';
import MyReservoirCheckIns, { CheckInReading } from './MyReservoirCheckIns';
import MyReservoirCheckInSetup from './MyReservoirCheckInSetup';
import { MyReservoirJournalDetail } from './MyReservoirJournals';
import { checkInCapacity, checkInConfigurationError, checkInTimes, DEFAULT_CHECK_IN_PROMPT, DEFAULT_CHECK_IN_SCHEDULE, MAX_CHECK_IN_PROMPT_BYTES, shuffleCheckInAnswers, validCheckInPrompt, withCheckInCapacity } from './checkInSchedule';
import { DEFAULT_SUSTAINED_CONFIG, type SustainedCheckIns, type SustainedConfig, type SustainedJournal, type SustainedUpdate } from './myReservoirTypes';
import { journal, reservoirFixture, reservoirSummary, settle } from './myReservoirTestFixtures';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));
const config = (): SustainedConfig => withCheckInCapacity({ ...DEFAULT_SUSTAINED_CONFIG, checkInSchedule: { ...DEFAULT_CHECK_IN_SCHEDULE } });
const checkIns = (): SustainedCheckIns => ({ intervalSeconds: 3600, endAfterSeconds: 21600, settings: { revision: 0, prompt: DEFAULT_CHECK_IN_PROMPT, includeTelemetry: true }, canEdit: true, complete: false, slots: checkInTimes(DEFAULT_CHECK_IN_SCHEDULE).map((scheduledSeconds, index) => ({ ordinal: index + 1, scheduledSeconds, status: 'pending' })), settingsHistory: [{ revision: 0, prompt: DEFAULT_CHECK_IN_PROMPT, includeTelemetry: true, elapsedMillis: 0 }] });
const answer = (n: number): SustainedJournal => ({ ...journal(n), text: `Private answer ${n}`, checkIn: { ordinal: n, scheduledSeconds: n * 3600, admittedElapsedMillis: n * 3600000 + 42, settingsRevision: 0, prompt: DEFAULT_CHECK_IN_PROMPT, includeTelemetry: n !== 2 }, observationSupplied: n !== 2, systemContract: n !== 2 ? 'Standing instructions retained exactly.' : null });
function answeredSchedule(): SustainedCheckIns {
  const c = checkIns();
  c.slots = c.slots.map((slot, index) => index < 2 ? { ...slot, ...answer(index + 1).checkIn, status: 'applied', entryId: `journal-${index + 1}`, attemptId: index + 1 } : { ...slot, status: index === 2 ? 'failed' : index === 3 ? 'missed' : index === 4 ? 'skipped' : 'pending' });
  return c;
}
function elements(node: ReactNode): ReactElement<Record<string, unknown>>[] {
  if (!isValidElement<Record<string, unknown>>(node)) return [];
  const result = [node]; Children.forEach(node.props.children as ReactNode, child => result.push(...elements(child))); return result;
}
async function prepared() {
  const fixture = reservoirFixture(); await fixture.controller.connect(); await fixture.controller.create(config()); await settle();
  fixture.push({ checkIns: checkIns(), phase: 'paused', canPause: false });
  return fixture;
}

describe('scheduled conversation setup', () => {
  it('keeps existing sessions unscheduled and explicitly enables the six-hour preset', () => {
    expect(DEFAULT_SUSTAINED_CONFIG.checkInSchedule).toBeUndefined();
    const setConfig = vi.fn(), tree = MyReservoirCheckInSetup({ config: DEFAULT_SUSTAINED_CONFIG, setConfig });
    const checkbox = elements(tree).find(node => node.type === 'input')!;
    (checkbox.props.onChange as (event: { target: { checked: boolean } }) => void)({ target: { checked: true } });
    expect(setConfig).toHaveBeenCalledExactlyOnceWith(config());
    expect(config().checkInSchedule?.prompt).toBe(DEFAULT_CHECK_IN_PROMPT);
    const html = renderToStaticMarkup(<MyReservoirConfig config={config()} setConfig={setConfig} disabled={false}/>);
    expect(html).toContain('6 scheduled check-ins'); expect(html).toContain('Include telemetry and session context');
    expect(html).toContain('The final answer is saved and its feedback applied');
    expect(html.indexOf('Scheduled conversations')).toBeLessThan(html.indexOf('Advanced settings'));
  });
  it('reserves both ordinary-loop and check-in capacity without lowering existing limits', () => {
    expect(checkInCapacity(config())).toEqual({ maximumSteps: 21607, maximumTurns: 727 });
    expect(checkInConfigurationError(config())).toBe('');
    const generous = withCheckInCapacity({ ...config(), maximumSteps: 50000, maximumTurns: 5000 });
    expect(generous.maximumSteps).toBe(50000); expect(generous.maximumTurns).toBe(5000);
    const largeStepCeiling = withCheckInCapacity({ ...config(), maximumSteps: 1_000_000 });
    expect(largeStepCeiling.maximumTurns).toBe(727); expect(checkInConfigurationError(largeStepCeiling)).toBe('');
    const insufficient = { ...config(), maximumTurns: 360 };
    expect(checkInConfigurationError(insufficient)).toContain('Increase step and attempt');
    expect(checkInConfigurationError(withCheckInCapacity({ ...config(), turnEvery: 1 }))).toContain('capacity');
  });
  it('includes the final nonmultiple deadline exactly once and supports a single final conversation', () => {
    expect(checkInTimes({ ...DEFAULT_CHECK_IN_SCHEDULE, endAfterSeconds: 9000 })).toEqual([3600, 7200, 9000]);
    expect(checkInTimes({ ...DEFAULT_CHECK_IN_SCHEDULE, intervalSeconds: 21600 })).toEqual([21600]);
    expect(checkInTimes(DEFAULT_CHECK_IN_SCHEDULE)).toEqual([3600, 7200, 10800, 14400, 18000, 21600]);
    for (const intervalSeconds of [0, NaN, Infinity, 3600.5, 21601]) expect(checkInTimes({ ...DEFAULT_CHECK_IN_SCHEDULE, intervalSeconds })).toEqual([]);
  });
  it('validates exact UTF-8 bytes and preserves valid prompt whitespace', () => {
    expect(validCheckInPrompt('   \n')).toBe(false);
    expect(validCheckInPrompt('x'.repeat(MAX_CHECK_IN_PROMPT_BYTES))).toBe(true);
    expect(validCheckInPrompt('é'.repeat(MAX_CHECK_IN_PROMPT_BYTES / 2 + 1))).toBe(false);
    const exact = '  tell me\nfriend  ';
    expect(withCheckInCapacity({ ...config(), checkInSchedule: { ...DEFAULT_CHECK_IN_SCHEDULE, prompt: exact } }).checkInSchedule?.prompt).toBe(exact);
  });
  it('explains plain mode without promising implicit history', () => {
    const html = renderToStaticMarkup(<MyReservoirCheckInSetup config={{ ...config(), checkInSchedule: { ...DEFAULT_CHECK_IN_SCHEDULE, includeTelemetry: false } }} setConfig={vi.fn()}/>);
    expect(html).toContain('Sends only your editable prompt'); expect(html).toContain('The response still feeds back');
  });
  it('rejects invalid schedules before session creation', async () => {
    const { controller, api } = reservoirFixture(); const create = vi.spyOn(api, 'create');
    expect(await controller.create({ ...config(), maximumDurationSeconds: 1 })).toBe(false);
    expect(await controller.create({ ...config(), checkInSchedule: { ...DEFAULT_CHECK_IN_SCHEDULE, prompt: ' ' } })).toBe(false);
    expect(create).not.toHaveBeenCalled();
  });
});

describe('paused conversational prompt editing', () => {
  it('saves against the displayed revision without starting, rewriting original settings, or changing slots', async () => {
    const { controller, api } = await prepared(); const before = controller.snapshot().summary!;
    const edit = vi.spyOn(api, 'updateCheckInSettings'), start = vi.spyOn(api, 'action');
    expect(await controller.updateCheckInSettings('  what interests you?\n', false, before.revision)).toBe(true);
    expect(edit).toHaveBeenCalledWith(expect.any(String), before.sessionId, before.generation, before.revision, '  what interests you?\n', false);
    const after = controller.snapshot().summary!;
    expect(after.config).toEqual(before.config); expect(after.checkIns?.slots).toEqual(before.checkIns?.slots);
    expect(after.checkIns?.settings).toEqual({ revision: 1, prompt: '  what interests you?\n', includeTelemetry: false });
    expect(after.phase).toBe('paused'); expect(start).not.toHaveBeenCalled();
  });
  it('rejects stale edits, running boundaries and empty prompts without dispatch', async () => {
    const { controller, api, push } = await prepared(), edit = vi.spyOn(api, 'updateCheckInSettings');
    expect(await controller.updateCheckInSettings('new', false, '0')).toBe(false);
    expect(await controller.updateCheckInSettings(' ', false, controller.snapshot().summary!.revision)).toBe(false);
    push({ checkIns: { ...checkIns(), canEdit: false }, phase: 'running' });
    expect(await controller.updateCheckInSettings('new', false, controller.snapshot().summary!.revision)).toBe(false);
    expect(edit).not.toHaveBeenCalled();
  });
  it('keeps saved settings unchanged after a persistence failure and prevents duplicate submission', async () => {
    const { controller, api } = await prepared(); const before = controller.snapshot().summary!;
    let reject!: (reason: Error) => void;
    const edit = vi.spyOn(api, 'updateCheckInSettings').mockReturnValue(new Promise<SustainedUpdate>((_, fail) => { reject = fail; }));
    const operation = controller.updateCheckInSettings('new', false, before.revision);
    expect(await controller.updateCheckInSettings('new', false, before.revision)).toBe(false);
    expect(controller.snapshot().summary).toBe(before);
    reject(new Error('Could not save prompt revision')); expect(await operation).toBe(false);
    expect(controller.snapshot().summary).toBe(before); expect(controller.snapshot().error).toContain('Could not save'); expect(edit).toHaveBeenCalledTimes(1);
  });
  it('exposes the editor only when permitted and retains settings history in the reading surface', () => {
    const { controller } = reservoirFixture(); const state = { ...controller.snapshot(), summary: reservoirSummary({ config: config(), checkIns: checkIns(), phase: 'paused' }) };
    const html = renderToStaticMarkup(<MyReservoirCheckIns state={state} controller={controller}/>);
    expect(html).toContain('Save future check-in settings'); expect(html).toContain('revision 0'); expect(html).toContain('prepared, failed or retried');
    const running = renderToStaticMarkup(<MyReservoirCheckIns state={{ ...state, summary: { ...state.summary, checkIns: { ...checkIns(), canEdit: false } } }} controller={controller}/>);
    expect(running).not.toContain('Save future check-in settings'); expect(running).toContain('Pause and let any writing');
  });
});

describe('check-in outcomes and reading', () => {
  it('keeps all six outcomes visible and gives a calm completed status', () => {
    const { controller } = reservoirFixture(); const state = { ...controller.snapshot(), summary: reservoirSummary({ config: config(), checkIns: answeredSchedule(), phase: 'scheduleComplete', canStart: false }) };
    const html = renderToStaticMarkup(<MyReservoirCheckIns state={state} controller={controller}/>);
    expect(html).toContain('2 saved answers from 6 scheduled check-ins'); expect(html).toContain('Needs attention'); expect(html).toContain('Missed'); expect(html).toContain('Skipped'); expect(html).toContain('Check-in 6');
    const status = renderToStaticMarkup(<MyReservoirStatus state={state}/>);
    expect(status).toContain('Scheduled conversations complete'); expect(status).not.toContain('needs-attention');
  });
  it('loads saved answers without changing journal selection or starting work', async () => {
    const { controller, api, push } = await prepared(); push({ checkIns: answeredSchedule(), journalCount: 2, turnCount: 2 });
    vi.spyOn(api, 'journal').mockImplementation(async (requestId, sessionId, generation, entryId) => ({ requestId, sessionId, generation, revision: controller.snapshot().summary!.revision, journal: answer(Number(entryId.split('-')[1])) }));
    const action = vi.spyOn(api, 'action'), selected = controller.snapshot().journal;
    expect((await controller.loadCheckInAnswers()).map(j => j.entryId)).toEqual(['journal-1', 'journal-2']);
    expect(controller.snapshot().journal).toBe(selected); expect(action).not.toHaveBeenCalled();
  });
  it('rejects mismatched saved contexts instead of quietly substituting an answer', async () => {
    const { controller, api, push } = await prepared(); push({ checkIns: answeredSchedule(), journalCount: 2, turnCount: 2 });
    vi.spyOn(api, 'journal').mockImplementation(async (requestId, sessionId, generation) => ({ requestId, sessionId, generation, revision: controller.snapshot().summary!.revision, journal: answer(6) }));
    await expect(controller.loadCheckInAnswers()).rejects.toThrow('saved identity and context');
  });
  it('shuffles a stable copy and reveals time and context only after the reader requests it', () => {
    const original = [answer(1), answer(2)], shuffled = shuffleCheckInAnswers(original, () => .999);
    expect(shuffled).toEqual([original[1], original[0]]); expect(original.map(j => j.entryId)).toEqual(['journal-1', 'journal-2']);
    const props = { answers: shuffled, onReveal: vi.fn(), onClose: vi.fn(), onOpen: vi.fn() };
    const blind = renderToStaticMarkup(<CheckInReading {...props} revealed={false}/>);
    expect(blind).toContain('Private answer 2'); expect(blind).toContain('Reveal timeline and context');
    expect(blind).not.toContain('Check-in 2'); expect(blind).not.toContain('prompt revision'); expect(blind).not.toContain('Plain prompt'); expect(blind).not.toContain('Open answer and evidence');
    const revealed = renderToStaticMarkup(<CheckInReading {...props} revealed/>);
    expect(revealed).toContain('Check-in 2'); expect(revealed).toContain('Plain prompt'); expect(revealed).toContain('2 hours');
  });
  it('distinguishes internal observations from text supplied in a plain check-in', () => {
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={answer(2)} revision="3" config={config()}/>);
    expect(html).toContain('retained internally, not sent to the model'); expect(html).toContain('No app-supplied system message');
    expect(html).not.toContain('v8 prompt supplies'); expect(html).not.toContain('The v8 prompt uses a compact');
    const telemetry = renderToStaticMarkup(<MyReservoirJournalDetail journal={answer(1)} revision="3" config={config()}/>);
    expect(telemetry).toContain('Standing instructions retained exactly.');
  });
});
