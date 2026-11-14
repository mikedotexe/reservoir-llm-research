import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoirActions, { JournalActionDetails } from './MyReservoirActions';
import MyReservoirConfig from './MyReservoirConfig';
import MyReservoirJournals, { MyReservoirJournalDetail } from './MyReservoirJournals';
import { ACTION_JOURNAL_PROMPT, ACTION_JOURNAL_PROMPT_V1, validActionSummary, validAuthoredActionConfig, validJournalAction, validReservoirInput, withAuthoredActionMode, withAuthoredActions } from './authoredActions';
import { DEFAULT_CHECK_IN_SCHEDULE } from './checkInSchedule';
import { DEFAULT_SUSTAINED_CONFIG, type SustainedActionDecision, type SustainedActionReceipt, type SustainedActions, type SustainedConfig, type SustainedJournal, type SustainedReservoirInput } from './myReservoirTypes';
import { journal, reservoirFixture, reservoirSummary, row, settle } from './myReservoirTestFixtures';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));

const config: SustainedConfig = { ...DEFAULT_SUSTAINED_CONFIG, actionMode: 'authored-v2', promptVersion: ACTION_JOURNAL_PROMPT };
const input: SustainedReservoirInput = { disposition: 'withhold', rawDirective: 'WITHHOLD_RESERVOIR_INPUT=true', rejection: null };
const controls = { leak: .65, recurrentGain: 1, feedbackScale: .4 };
const decision: SustainedActionDecision = { body: 'I will keep this thought as writing.', rawTail: 'NEXT: PULSE alternating 0.5', request: { kind: 'pulse', direction: 'alternating', strength: .5 }, rejection: null, reservoirInput: input };
const receipt: SustainedActionReceipt = { journalId: 'journal-1', attemptId: 1, observedStep: 3, appliedStep: 4, status: 'applied', request: decision.request, rawTail: decision.rawTail, rejection: null, controlsBefore: controls, controlsAfter: controls, stateDeltaL2: .5, stateDeltaMaxAbs: .09, clippedCoordinates: 0, reservoirInput: input };
const actions = (result = receipt): SustainedActions => ({ state: { controls, latestReceipt: result, recentReceipts: [result], decisionCount: 1, appliedCount: result.status === 'applied' ? 1 : 0, rejectedCount: result.status === 'rejected' ? 1 : 0 }, durableStep: 4 });
const retained = (patch: Partial<SustainedJournal> = {}): SustainedJournal => ({ ...journal(), promptVersion: ACTION_JOURNAL_PROMPT, text: `${decision.body}\n\n${input.rawDirective}\n${decision.rawTail}`, rawReply: `${decision.body}\n\n${input.rawDirective}\n${decision.rawTail}`, action: decision, actionReceipt: receipt, bodySha256: 'b'.repeat(64), semanticVector: Array(48).fill(0), ...patch });

describe('independent numerical text-input choice', () => {
  it('creates v2 shaping sessions while retaining exact v1 capability pairs', () => {
    expect(withAuthoredActionMode(DEFAULT_SUSTAINED_CONFIG, 'authored-v2')).toEqual(config);
    expect(validAuthoredActionConfig(config)).toBe(true);
    expect(validAuthoredActionConfig({ ...config, actionMode: 'authored-v1', promptVersion: ACTION_JOURNAL_PROMPT_V1 })).toBe(true);
    expect(validAuthoredActionConfig({ ...config, actionMode: 'authored-v1' })).toBe(false);
    expect(validAuthoredActionConfig({ ...config, promptVersion: ACTION_JOURNAL_PROMPT_V1 })).toBe(false);
    expect(withAuthoredActions(config, false, ACTION_JOURNAL_PROMPT_V1)).toEqual(DEFAULT_SUSTAINED_CONFIG);
  });

  it('explains retaining memory, clearing the held text input, and passive check-ins in setup', () => {
    const html = renderToStaticMarkup(<MyReservoirConfig config={{ ...config, checkInSchedule: DEFAULT_CHECK_IN_SCHEDULE }} setConfig={() => {}} disabled={false}/>);
    expect(html).toContain('withhold an entry’s numerical text input independently of its action');
    expect(html).toContain('The entry stays in the journal and can return as memory');
    expect(html).toContain('replaces the previous held text input with zero');
    expect(html).toContain('A text-input directive in a check-in is also ordinary writing');
    expect(html).toContain('Text input can be withheld.');
    expect(html).not.toContain('<strong>Feedback is included.</strong>');
  });

  it('distinguishes requested withholding from an already committed send result', () => {
    const sent = { ...receipt, reservoirInput: { disposition: 'send' as const, rawDirective: null, rejection: null } };
    const pending = { attemptId: 2, entryId: 'journal-2', observedStep: 6, intendedStep: 7, phase: 'prepared' as const, durablePrepared: true, decision };
    const summary = reservoirSummary({ config, actions: { ...actions(sent), pending }, step: 6, durableStep: 4 });
    expect(validActionSummary(summary)).toBe(true);
    const html = renderToStaticMarkup(<MyReservoirActions summary={summary}/>);
    expect(html).toContain('Text input selected: withhold');
    expect(html).toContain('On application, zero will replace the previous held text input');
    expect(html).toContain('Text input allowed at step 4');
    expect(html).not.toContain('Text input withheld at step 7');
  });

  it('renders a retained pulse outcome and withholding outcome separately in a paused session', async () => {
    const fixture = reservoirFixture();
    await fixture.controller.create(config); await fixture.controller.connect(); await settle();
    fixture.push({ config, phase: 'paused', step: 4, durableStep: 4, actions: actions() });
    expect(fixture.controller.snapshot().error).toBe('');
    const restored = fixture.controller.snapshot().summary!;
    const html = renderToStaticMarkup(<MyReservoirActions summary={restored}/>);
    expect(html).toContain('Action applied at step 4');
    expect(html).toContain('Text input withheld at step 4');
    expect(html).toContain('The journal body remains eligible for memory');
    expect(html).toContain('Other inputs, ordinary dynamics, and separately chosen actions continue');
  });

  it('shows body-only reading and truthful zero-input evidence without losing the raw directive', () => {
    const saved = retained();
    expect(validJournalAction(saved, config)).toBe(true);
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={saved} revision="8" config={{ ...config, embeddingModel: 'local-embedding' }}/>);
    const prose = html.match(/class="my-reservoir-journal-prose"[^>]*>(.*?)<\/div>/)?.[1];
    expect(prose).toBe(decision.body);
    expect(prose).not.toContain('WITHHOLD_RESERVOIR_INPUT');
    expect(html).toContain('Saved · text input withheld');
    expect(html).not.toContain('Saved · feedback applied');
    expect(html).toContain('Zero text input replaced the previous held input');
    expect(html).toContain('Withheld · zero numerical text input; no embedding request');
    expect(html).toContain('Exact text-input directive');
    expect(html).toContain(input.rawDirective);
    expect(html).toContain('Raw received reply');
    expect(html).toContain('Its journal body is eligible for later prompts');
  });

  it('shows withholding in history rows independently of action status', () => {
    const { controller } = reservoirFixture();
    const state = { ...controller.snapshot(), summary: reservoirSummary({ config, step: 4, durableStep: 4, journalCount: 1, turnCount: 1, actions: actions() }), page: { requestId: 'history', sessionId: 'personal-1', generation: '1', revision: '8', offset: 0, total: 1, hasMore: false, entries: [{ ...row(), actionReceipt: receipt }] } };
    const html = renderToStaticMarkup(<MyReservoirJournals state={state} controller={controller}/>);
    expect(html).toContain('Saved · text input withheld');
    expect(html).toContain('Action applied at step 4');
    expect(html).not.toContain('Saved · feedback applied');
  });

  it('reports malformed input rejection without relabeling an executed pulse as rejected', () => {
    const rejected: SustainedReservoirInput = { disposition: 'rejected', rawDirective: 'WITHHOLD_RESERVOIR_INPUT=<maybe>', rejection: 'Expected true or false, got <maybe>.' };
    const saved = retained({ action: { ...decision, reservoirInput: rejected }, actionReceipt: { ...receipt, reservoirInput: rejected } });
    expect(validJournalAction(saved, config)).toBe(true);
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={saved} revision="8" config={config}/>);
    expect(html).toContain('Input directive rejected; text input withheld at step 4');
    expect(html).toContain('Action applied at step 4');
    expect(html).not.toContain('Action rejected at step');
    expect(html).toContain('&lt;maybe&gt;');
    expect(html).not.toContain('Saved · feedback applied');
  });

  it('allows NONE with either send or withhold without treating withholding as a control action', () => {
    for (const reservoirInput of [input, { disposition: 'send' as const, rawDirective: null, rejection: null }]) {
      const none: SustainedActionReceipt = { ...receipt, status: 'unchanged', request: { kind: 'none' }, rawTail: 'NEXT: NONE', stateDeltaL2: 0, stateDeltaMaxAbs: 0, reservoirInput };
      const summary = reservoirSummary({ config, actions: actions(none), step: 4, durableStep: 4 });
      expect(validActionSummary(summary)).toBe(true);
      const html = renderToStaticMarkup(<MyReservoirActions summary={summary}/>);
      expect(html).toContain('No additional intervention at step 4');
      expect(html).not.toContain('Action applied at step');
      expect(html).toContain(reservoirInput.disposition === 'send' ? 'Text input allowed at step 4' : 'Text input withheld at step 4');
    }
  });

  it('does not promise a zero replacement after a user skipped the saved choice', () => {
    const skipped = retained({ actionReceipt: null, status: 'skipped', firstAppliedStep: null });
    const html = renderToStaticMarkup(<JournalActionDetails journal={skipped}/>);
    expect(html).toContain('Text-input choice skipped · withhold');
    expect(html).toContain('automatic memory exposure was skipped');
    expect(html).not.toContain('On application, zero will replace');
    expect(html).not.toContain('The previous held text input was replaced');
  });

  it('requires the versioned decision, matching receipt, and valid input-rejection shape', () => {
    const missing = { ...decision }; delete missing.reservoirInput;
    expect(validJournalAction(journal(), config)).toBe(false);
    expect(validJournalAction(retained({ action: missing }), config)).toBe(false);
    expect(validJournalAction(retained(), { ...config, actionMode: 'authored-v1', promptVersion: ACTION_JOURNAL_PROMPT_V1 })).toBe(false);
    expect(validJournalAction(retained({ actionReceipt: { ...receipt, reservoirInput: { disposition: 'send', rawDirective: null, rejection: null } } }), config)).toBe(false);
    for (const invalid of [{ ...input, disposition: 'future' }, { ...input, rejection: 'bad' }, { ...input, rawDirective: 1 }, { ...input, disposition: 'rejected', rejection: null }]) expect(validReservoirInput(invalid)).toBe(false);
    expect(validReservoirInput({ ...input, disposition: 'send' })).toBe(false);
    expect(validReservoirInput({ disposition: 'rejected', rawDirective: null, rejection: 'Input directive exceeds 512 bytes; numerical text input was withheld' })).toBe(true);
    expect(validReservoirInput({ disposition: 'rejected', rawDirective: 'é'.repeat(257), rejection: 'Too large.' })).toBe(false);
    const missingReceipt = { ...receipt }; delete missingReceipt.reservoirInput;
    expect(validActionSummary(reservoirSummary({ config, actions: actions(missingReceipt), step: 4, durableStep: 4 }))).toBe(false);
    const mismatchedLatest = actions();
    mismatchedLatest.state.latestReceipt = { ...receipt, reservoirInput: { disposition: 'send', rawDirective: null, rejection: null } };
    expect(validActionSummary(reservoirSummary({ config, actions: mismatchedLatest, step: 4, durableStep: 4 }))).toBe(false);
  });

  it('leaves a check-in directive as ordinary prose with normal saved feedback', () => {
    const saved: SustainedJournal = { ...journal(), promptVersion: ACTION_JOURNAL_PROMPT, text: 'WITHHOLD_RESERVOIR_INPUT=true\nNEXT: NONE', checkIn: { ordinal: 1, scheduledSeconds: 3600, admittedElapsedMillis: 3600000, settingsRevision: 0, prompt: 'Hello.', includeTelemetry: false } };
    expect(validJournalAction(saved, config)).toBe(true);
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={saved} revision="8" config={config}/>);
    expect(html).toContain('Saved · feedback applied');
    expect(html).not.toContain('Saved · text input withheld');
    expect(html.match(/class="my-reservoir-journal-prose"[^>]*>(.*?)<\/div>/s)?.[1]).toContain('WITHHOLD_RESERVOIR_INPUT=true');
  });
});
