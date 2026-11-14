import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoirConfig from './MyReservoirConfig';
import MyReservoirActions, { JournalActionDetails } from './MyReservoirActions';
import { MyReservoirJournalDetail } from './MyReservoirJournals';
import { ACTION_JOURNAL_PROMPT, validActionSummary, validAuthoredActionConfig, validJournalAction, withAuthoredActions } from './authoredActions';
import { DEFAULT_CHECK_IN_SCHEDULE } from './checkInSchedule';
import { DEFAULT_SUSTAINED_CONFIG, type SustainedActionControls, type SustainedActionDecision, type SustainedActionReceipt, type SustainedActions, type SustainedConfig, type SustainedJournal } from './myReservoirTypes';
import { journal, reservoirFixture, reservoirSummary, settle } from './myReservoirTestFixtures';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));

const enabled: SustainedConfig = { ...DEFAULT_SUSTAINED_CONFIG, actionMode: 'authored-v1', promptVersion: ACTION_JOURNAL_PROMPT };
const controls: SustainedActionControls = { leak: .65, recurrentGain: 1, feedbackScale: .4 };
const decision: SustainedActionDecision = { body: 'I would like to follow this change.', rawTail: 'NEXT: TUNE leak 0.2', request: { kind: 'tune', parameter: 'leak', value: .2 }, rejection: null };
const receipt: SustainedActionReceipt = { journalId: 'journal-1', attemptId: 1, observedStep: 3, appliedStep: 4, status: 'applied', request: decision.request, rawTail: decision.rawTail, rejection: null, controlsBefore: controls, controlsAfter: { ...controls, leak: .2 }, stateDeltaL2: .14, stateDeltaMaxAbs: .04, clippedCoordinates: 0 };
const actionState = (patch: Partial<SustainedActions> = {}): SustainedActions => ({ state: { controls: receipt.controlsAfter, latestReceipt: receipt, recentReceipts: [receipt], decisionCount: 1, appliedCount: 1, rejectedCount: 0 }, durableStep: 4, ...patch });
const actionJournal = (patch: Partial<SustainedJournal> = {}): SustainedJournal => ({ ...journal(), promptVersion: ACTION_JOURNAL_PROMPT, text: `${decision.body}\n${decision.rawTail}`, rawReply: `${decision.body}\n${decision.rawTail}`, action: decision, actionReceipt: receipt, bodySha256: 'b'.repeat(64), ...patch });
const renderSetup = (config: SustainedConfig) => renderToStaticMarkup(<MyReservoirConfig config={config} setConfig={() => {}} disabled={false}/>);

describe('new-session reservoir action capability', () => {
  it('starts off, enables a matching invitation and restores the chosen ordinary invitation', () => {
    const plain = 'reservoir-journal-inert-plain-contract-no-tag-v1';
    const config: SustainedConfig = { ...DEFAULT_SUSTAINED_CONFIG, promptVersion: plain, checkInSchedule: { ...DEFAULT_CHECK_IN_SCHEDULE, includeTelemetry: false } };
    const active = withAuthoredActions(config, true, plain);
    expect(active).toEqual({ ...config, actionMode: 'authored-v1', promptVersion: ACTION_JOURNAL_PROMPT });
    expect(validAuthoredActionConfig(active)).toBe(true);
    expect(withAuthoredActions(active, false, plain)).toEqual(config);
    expect(JSON.stringify(withAuthoredActions(active, false, plain))).not.toContain('actionMode');
    const { promptVersion: _prompt, ...legacy } = DEFAULT_SUSTAINED_CONFIG;
    expect(withAuthoredActions(withAuthoredActions(legacy, true, undefined), false, undefined)).toEqual(legacy);
    expect(DEFAULT_SUSTAINED_CONFIG).not.toHaveProperty('actionMode');
    expect(renderSetup(DEFAULT_SUSTAINED_CONFIG)).toContain('type="checkbox"/>Let the model shape the reservoir');
  });

  it('explains persistent choices, locks the action invitation and keeps check-ins passive', () => {
    const html = renderSetup({ ...enabled, checkInSchedule: { ...DEFAULT_CHECK_IN_SCHEDULE, includeTelemetry: false } });
    expect(html).toContain('checked=""/>Let the model shape the reservoir');
    expect(html).toContain('Adjustments persist until the model changes or releases them');
    expect(html).toContain('Writing invitation<select disabled=""');
    expect(html).toContain(`value="${ACTION_JOURNAL_PROMPT}" selected="">Journal with reservoir actions`);
    expect(html).toContain('This choice is fixed when you create the session');
    expect(html).toContain('No action menu or action receipt is added to a plain prompt');
    expect(html).toContain('NEXT text in a check-in never executes a control');
    expect(html).toContain('Sends only your editable prompt');
    expect(html).not.toContain('Research invitation · reservoir-journal-actions-v1');
  });

  it('serializes an explicit capability and rejects mismatched or unknown versions before creation', async () => {
    const { controller, api } = reservoirFixture();
    const create = vi.spyOn(api, 'create');
    for (const invalid of [{ ...DEFAULT_SUSTAINED_CONFIG, actionMode: 'authored-v1' }, { ...DEFAULT_SUSTAINED_CONFIG, promptVersion: ACTION_JOURNAL_PROMPT }, { ...enabled, actionMode: 'future' }]) {
      expect(await controller.create(invalid as SustainedConfig)).toBe(false);
    }
    expect(create).not.toHaveBeenCalled();
    expect(await controller.create(enabled)).toBe(true);
    expect(create.mock.calls[0][1]).toEqual(enabled);
    expect(controller.snapshot().summary?.config.actionMode).toBe('authored-v1');
  });

  it('cannot acquire action capability from a later session update', async () => {
    const { controller, push } = reservoirFixture();
    await controller.create(DEFAULT_SUSTAINED_CONFIG); await controller.connect(); await settle();
    const original = controller.snapshot().summary;
    push({ revision: '2', config: enabled });
    expect(controller.snapshot().summary).toBe(original);
    expect(controller.snapshot().error).toContain('changed its reservoir action capability');
  });
});

describe('recorded actions and pending choices', () => {
  it('shows current saved controls and separates a queued choice from an earlier applied result', () => {
    const actions = actionState({ pending: { attemptId: 2, entryId: 'journal-2', observedStep: 6, intendedStep: 7, phase: 'prepared', durablePrepared: false, decision: { rejection: null, request: { kind: 'pulse', direction: 'uniform', strength: .5 } } } });
    const summary = reservoirSummary({ config: enabled, actions, step: 6, durableStep: 4 });
    expect(validActionSummary(summary)).toBe(true);
    const html = renderToStaticMarkup(<MyReservoirActions summary={summary}/>);
    expect(html).toContain('Saved controls · through step 4');
    expect(html).toContain('Action waiting for save confirmation');
    expect(html).toContain('No application has been recorded for this choice');
    expect(html).toContain('Action applied at step 4');
    expect(html).not.toContain('Action applied at step 7');
    const durable = renderToStaticMarkup(<MyReservoirActions summary={{ ...summary, actions: { ...actions, pending: { ...actions.pending!, durablePrepared: true } } }}/>);
    expect(durable).toContain('Saved action waiting for application');
  });

  it('retains NONE and rejected results without calling either an applied action', () => {
    const unchanged = { ...receipt, status: 'unchanged' as const, request: { kind: 'none' as const }, rawTail: 'NEXT: NONE', controlsAfter: controls, stateDeltaL2: 0, stateDeltaMaxAbs: 0 };
    const rejected = { ...receipt, status: 'rejected' as const, request: null, rawTail: 'NEXT: TELEPORT', rejection: 'Unknown action <TELEPORT>.', controlsAfter: controls, stateDeltaL2: 0, stateDeltaMaxAbs: 0 };
    for (const result of [unchanged, rejected]) {
      const actions = actionState({ state: { controls, latestReceipt: result, recentReceipts: [result], decisionCount: 1, appliedCount: 0, rejectedCount: result.status === 'rejected' ? 1 : 0 } });
      const summary = reservoirSummary({ config: enabled, actions, step: 4, durableStep: 4 });
      expect(validActionSummary(summary)).toBe(true);
      const html = renderToStaticMarkup(<MyReservoirActions summary={summary}/>);
      expect(html).not.toContain('Action applied at step');
      expect(html).toContain(result.status === 'rejected' ? 'Action rejected at step 4' : 'No additional intervention at step 4');
      if (result.status === 'rejected') expect(html).toContain('&lt;TELEPORT&gt;');
    }
  });

  it('does not accept receipts beyond the saved boundary or attach capability to legacy sessions', () => {
    expect(validActionSummary(reservoirSummary({ config: enabled, actions: actionState(), step: 6, durableStep: 3 }))).toBe(false);
    expect(validActionSummary(reservoirSummary({ actions: actionState(), step: 4, durableStep: 4 }))).toBe(false);
    expect(renderToStaticMarkup(<MyReservoirActions summary={reservoirSummary()}/>)).toBe('');
  });
});

describe('journal body and authored action evidence', () => {
  it('reads the body while preserving the complete reply, exact action line and durable receipt', () => {
    const retained = actionJournal();
    expect(validJournalAction(retained, enabled)).toBe(true);
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={retained} revision="8" config={enabled}/>);
    const prose = html.match(/class="my-reservoir-journal-prose"[^>]*>(.*?)<\/div>/)?.[1];
    expect(prose).toBe(decision.body);
    expect(prose).not.toContain('NEXT:');
    expect(html).toContain('Exact action line');
    expect(html).toContain('Raw received reply');
    expect(html).toContain('Action applied at step 4');
    expect(html).toContain('Immediate action difference · L2');
    expect(html).toContain('omitting this action');
    expect(html).toContain('Journal body SHA-256:');
  });

  it('distinguishes the body supplied as memory from its complete saved source', () => {
    const retained = actionJournal({ memory: { entryId: 'older', text: 'Earlier body.\nNEXT: NONE', sha256: 'a'.repeat(64), suppliedText: 'Earlier body.', suppliedTextSha256: 'c'.repeat(64) } });
    expect(validJournalAction(retained, enabled)).toBe(true);
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={retained} revision="8" config={enabled}/>);
    expect(html).toContain('Supplied body SHA-256:');
    expect(html).toMatch(/aria-label="Previous journal text">Earlier body\.<\/pre>/);
    expect(html).toContain('Original earlier journal · full response');
    expect(html).toContain('Earlier body.\nNEXT: NONE');
    expect(validJournalAction({ ...retained, memory: { ...retained.memory!, suppliedTextSha256: 'invalid' } }, enabled)).toBe(false);
  });

  it('shows an action-only entry without substituting its raw NEXT line for prose', () => {
    const retained = actionJournal({ text: decision.rawTail!, rawReply: decision.rawTail!, action: { ...decision, body: '' } });
    expect(validJournalAction(retained, enabled)).toBe(true);
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={retained} revision="8" config={enabled}/>);
    const prose = html.match(/class="my-reservoir-journal-prose"[^>]*>(.*?)<\/div>/)?.[1];
    expect(prose).toContain('No journal text in this entry.');
    expect(prose).not.toContain('NEXT:');
    expect(html).toContain('Action applied at step 4');
    expect(html).toContain('Raw received reply');
  });

  it('keeps a skipped action unapplied and rejects unrelated or check-in action receipts', () => {
    const skipped = actionJournal({ status: 'skipped', firstAppliedStep: null, actionReceipt: null });
    expect(validJournalAction(skipped, enabled)).toBe(true);
    const html = renderToStaticMarkup(<JournalActionDetails journal={skipped}/>);
    expect(html).toContain('The saved action was skipped');
    expect(html).not.toContain('Action applied');
    expect(validJournalAction(actionJournal({ actionReceipt: { ...receipt, journalId: 'another-entry' } }), enabled)).toBe(false);
    expect(validJournalAction(actionJournal({ checkIn: { ordinal: 1, scheduledSeconds: 3600, admittedElapsedMillis: 3600000, settingsRevision: 0, prompt: 'Hello.', includeTelemetry: false } }), enabled)).toBe(false);
    expect(validJournalAction(journal(), DEFAULT_SUSTAINED_CONFIG)).toBe(true);
  });
});
