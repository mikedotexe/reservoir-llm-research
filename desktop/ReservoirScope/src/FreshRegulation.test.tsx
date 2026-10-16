import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import FreshExperiments, { ConfigEditor, FreshJournal, FreshRecovery, FreshSaveStatus } from './FreshExperiments';
import FreshRegulation, { RegulationFields, RegulationTrends } from './FreshRegulation';
import { FreshController } from './freshController';
import { DEFAULT_FRESH_CONFIG, selectFreshRecipe, type FreshApi, type RegulationDetails, type RegulationFieldFrame, type RegulationSpecification, type SessionSummary, type SessionUpdate, type SessionTurn, type RecoveryCheckpoint } from './freshTypes';

const config = selectFreshRecipe(DEFAULT_FRESH_CONFIG, 'regulation');
const spec: RegulationSpecification = { fixture: 'uniform66-seed42-field98-v1', fieldSeed: '98', inputSeed: '42', steps: 600, dt: 1 / 3, initialRetention: .955, targetFillPercent: 68, evaluationFirstStep: 301, evaluationLastStep: 600, question: 'Fixed study question', expectedDifference: 'Expected difference', alternativeExplanation: 'Bounded synthetic input only', stoppingPoint: '600 steps' };
const field = (step: number, baseline = false): RegulationFieldFrame => ({ index: step - 1, step: String(step), time: step / 3, input: Array(66).fill(.1), fieldVector: Array(32).fill(.2), eigenvalues: Array(32).fill(.3), fillPercent: baseline ? 70 : 65, retentionUsed: baseline ? .955 : .91, nextRetention: baseline ? null : .92, control: baseline ? null : { error: .03, integral: .1, requestedRetention: .92, appliedRetention: .92 }, regulationEvidence: step < 301 ? null : { count: step - 300, firstStep: 301, lastStep: step, isComplete: step === 600, baselineMeanAbsoluteError: 2, regulatedMeanAbsoluteError: 3 } });
const pair = (step: number) => ({ left: field(step, true), right: field(step) });
function summary(step = 0, patch: Partial<SessionSummary> = {}): SessionSummary {
  return { sessionId: 'fields-1', generation: '1', revision: String(step + 1), config, phase: step === 600 ? 'completed' : 'paused', step, durableStep: step === 600 ? 600 : 0, stepLimit: 600, frameCount: step, turnCount: 0, journalCount: 0, unsavedRecord: true, pendingWrites: false, canStep: step < 600, canRun: step < 600, canExport: step === 600, canRequestJournal: false, action: null, regulationSpec: spec, explorationControls: null, saveError: null, libraryEntryId: null, diagnostics: [], tracks: (['left', 'right'] as const).map(id => ({ id, label: id === 'left' ? 'Baseline field' : 'Regulated field', stage: null, frameCount: step, turnCount: 0, journalCount: 0, status: step === 600 ? 'completed' : 'stopped', failure: null, observationChannel: null, action: null })), ...patch };
}
const update = (requestId: string, step = 0, patch: Partial<SessionSummary> = {}): SessionUpdate => ({ requestId, summary: summary(step, patch), frame: null, frames: null, regulationFrames: step ? pair(step) : null, pendingJournal: null, closeRequested: false });
const checkpoint = (): RecoveryCheckpoint => ({ schema: 'reservoir-scope-finite-session-v1', sessionId: 'fields-1', generation: '1', revision: '4', config, phase: 'paused', step: 3, durableStep: 0, recordSha256: null, pendingJournal: null, attempts: [], updatedAtMs: '100', discarded: false });
const details = (requestId: string, step: number): RegulationDetails => ({ requestId, sessionId: 'fields-1', generation: '1', revision: '601', cursorStep: step, projectionWeights: Array(2112).fill(.123), timeline: Array.from({ length: step }, (_, index) => ({ step: String(index + 1), baselineFill: 70, regulatedFill: 65, baselineRetention: .955, regulatedRetention: .91 })) });
function fixture(step = 0) {
  let receive: (u: SessionUpdate) => void = () => {}, request = '';
  const api: FreshApi = {
    get: async (id, callback) => { request = id; receive = callback; return update(id, step); },
    create: async id => update(id, step),
    action: async (action, id, _session, _generation, callback) => { if (action === 'reset') return update(id, 0, { sessionId: 'fields-2', generation: '2' }); if (action === 'run') { request = id; receive = callback; } return update(id, step, { phase: action === 'run' ? 'running' : 'paused' }); },
    frame: async (id, sessionId, generation, index, trackId) => ({ requestId: id, sessionId, generation, revision: '601', trackId, frame: null, regulationFrame: field(index + 1, trackId === 'left') }),
    turn: async () => { throw Error('No turns in this field study'); },
    export: async (id, sessionId, generation) => ({ requestId: id, sessionId, generation, revision: '601', file: null }),
    controls: async id => update(id, step), regulationDetails: async (id, _session, _generation, cursor) => details(id, cursor),
    listenClose: async () => () => {}, finishClose: async () => false, cancelClose: async () => {},
    recovery: async id => ({ requestId: id, entries: [], incompleteWrites: [], examined: 0, truncated: false }), recovered: async () => checkpoint(),
    exportRecovery: async (id, sessionId, _kind, generation, revision) => ({ requestId: id, sessionId, generation, revision, file: null }),
  };
  const controller = new FreshController(api);
  return { api, controller, push: (step: number, patch: Partial<SessionSummary> = {}) => receive(update(request, step, patch)), send: (value: SessionUpdate) => receive({ ...value, requestId: request }) };
}

describe('fixed fresh field-only study', () => {
  it('selecting the study removes all mutable reservoir/action settings and never offers those controls', () => {
    const chosen = selectFreshRecipe({ ...DEFAULT_FRESH_CONFIG, seed: '77', steps: 9, noiseAmplitude: .2, actionComparePrevious: true, actionMode: 'fixedReplay', actionComparisonKind: 'observation' }, 'regulation');
    expect(chosen).toEqual(config); expect(chosen.explorationControls).toBeUndefined();
    const html = renderToStaticMarkup(<ConfigEditor config={chosen} setConfig={() => {}} disabled={false}/>);
    expect(html).toContain('600 steps'); expect(html).not.toContain('<input'); expect(html).not.toContain('Reply mode'); expect(html).not.toContain('Turn opportunity every');
    expect(selectFreshRecipe(chosen, 'actionH').recipe).toBe('actionH');
  });
  it('renders two fields and exact sensory values, with no reservoir surface or invented target bands', () => {
    const html = renderToStaticMarkup(<RegulationFields frames={pair(301)} spec={spec} active tableOnly/>);
    expect(html).toContain('Baseline field'); expect(html).toContain('Regulated field'); expect(html).toContain('1 / 300 recorded steps'); expect(html).toContain('Projected sensory field coordinates'); expect(html).toContain('RMS normalization'); expect(html).not.toContain('scene-canvas'); expect(html).not.toContain('Recurrent'); expect(html).toContain('No retained reference configuration');
    const before = renderToStaticMarkup(<RegulationFields frames={pair(300)} spec={spec} active tableOnly/>);
    expect(before).toContain('Evaluation starts at step 301'); expect(before).not.toContain('percentage points');
    const complete = renderToStaticMarkup(<RegulationFields frames={pair(600)} spec={spec} active tableOnly/>); expect(complete).toContain('Complete evaluation window'); expect(complete).toContain('300 / 300');
  });
  it('keeps fixed trend scales and non-color arm distinctions with a blank future extent', () => {
    const html = renderToStaticMarkup(<RegulationTrends details={details('d', 1)}/>);
    expect(html).toContain('dashed blue'); expect(html).toContain('solid green'); expect(html).toContain('fixed 0–100%'); expect(html).toContain('fixed 0–1'); expect(html).toContain('blank remainder'); expect(html).toContain('<circle'); expect(html).not.toContain('L 570');
  });
  it('attaches without creating or fetching trends and renders only field data from the backend', async () => {
    const { api, controller } = fixture(3), create = vi.spyOn(api, 'create'), read = vi.spyOn(api, 'regulationDetails');
    await controller.connect(); expect(create).not.toHaveBeenCalled(); expect(read).not.toHaveBeenCalled(); expect(controller.snapshot().frame).toBeNull(); expect(controller.snapshot().frames).toBeNull();
    const html = renderToStaticMarkup(<FreshExperiments controller={controller} active/>);
    expect(html).toContain('Fresh field-only controller study'); expect(html).not.toContain('scene-canvas'); expect(html).not.toContain('Writing and outcomes');
    expect(renderToStaticMarkup(<FreshExperiments controller={controller} active={false}/>)).toBe('');
  });
  it('rejects misaligned field pairs and future evaluation evidence without replacing accepted data', async () => {
    const { controller, send } = fixture(301); await controller.connect(); const accepted = controller.snapshot().regulationFrames;
    const bad = update('x', 302); bad.regulationFrames!.left = field(301, true); send(bad);
    expect(controller.snapshot().regulationFrames).toBe(accepted); expect(controller.snapshot().error).toContain('numerical boundary');
    const future = update('x', 302); future.regulationFrames!.right.regulationEvidence = field(600).regulationEvidence; send(future);
    expect(controller.snapshot().regulationFrames).toBe(accepted); expect(controller.snapshot().error).toContain('evaluation prefix');
  });
  it('accepts historical fields atomically, retains both on peer failure, and ignores reset-stale reads', async () => {
    const { api, controller } = fixture(600); await controller.connect(); const accepted = controller.snapshot().regulationFrames;
    api.frame = async (id, sessionId, generation, index, trackId) => { if (trackId === 'left') throw Error('left unavailable'); return { requestId: id, sessionId, generation, revision: '601', trackId, frame: null, regulationFrame: field(index + 1) }; };
    await controller.frame(0); expect(controller.snapshot().regulationFrames).toBe(accepted);
    const finish: (() => void)[] = []; api.frame = (id, sessionId, generation, index, trackId) => new Promise(resolve => finish.push(() => resolve({ requestId: id, sessionId, generation, revision: '601', trackId, frame: null, regulationFrame: field(index + 1, trackId === 'left') })));
    const pending = controller.frame(0); finish[0](); await Promise.resolve(); expect(controller.snapshot().regulationFrames).toBe(accepted);
    api.get = async id => update(id, 0, { sessionId: 'fields-2', generation: '2' });
    await controller.action('reset', true); finish[1](); await pending; expect(controller.snapshot().summary?.sessionId).toBe('fields-2'); expect(controller.snapshot().regulationFrames).toBeNull();
  });
  it('rewinding removes later aggregate and ignores an in-flight details read for a different cursor', async () => {
    const { api, controller } = fixture(600); await controller.connect(); await controller.regulationDetails(); expect(controller.snapshot().regulationDetails?.timeline).toHaveLength(600);
    await controller.frame(299); expect(controller.snapshot().regulationFrames?.right.regulationEvidence).toBeNull();
    const html = renderToStaticMarkup(<FreshRegulation state={controller.snapshot()} controller={controller} active tableOnly/>); expect(html).not.toContain('Retained controller prefix trends'); expect(html).not.toContain('Complete evaluation window');
    let finish!: () => void; api.regulationDetails = (id, _s, _g, cursor) => new Promise(resolve => { finish = () => resolve(details(id, cursor)); });
    const pending = controller.regulationDetails(); await controller.frame(0); finish(); await pending;
    expect(controller.snapshot().regulationDetails?.cursorStep).toBe(600); expect(controller.snapshot().readingRegulationDetails).toBe(false);
    expect(renderToStaticMarkup(<FreshRegulation state={controller.snapshot()} controller={controller} active tableOnly/>)).not.toContain('Retained controller prefix trends');
  });
  it('rejects details containing future timeline rows and keeps the accepted bounded prefix', async () => {
    const { api, controller } = fixture(301); await controller.connect(); await controller.regulationDetails(); const accepted = controller.snapshot().regulationDetails;
    api.regulationDetails = async id => ({ ...details(id, 302), cursorStep: 301 }); await controller.regulationDetails(); expect(controller.snapshot().regulationDetails).toBe(accepted); expect(controller.snapshot().error).toContain('bounded selected prefix');
  });
  it('prevents partial portable saves/exports and explicitly exports only the captured progress checkpoint', async () => {
    const { api, controller } = fixture(3); await controller.connect(); const action = vi.spyOn(api, 'action'), exp = vi.spyOn(api, 'export'), progress = vi.spyOn(api, 'exportRecovery');
    await controller.action('saveRecord'); await controller.export(); expect(action).not.toHaveBeenCalled(); expect(exp).not.toHaveBeenCalled();
    await controller.exportProgress(); expect(progress).toHaveBeenCalledWith(expect.any(String), 'fields-1', 'checkpoint', '1', '4'); expect(controller.snapshot().message).toContain('cancelled');
    const html = renderToStaticMarkup(<FreshSaveStatus state={controller.snapshot()} controller={controller}/>); expect(html).toContain('progress checkpoint only'); expect(html).toContain('without numerical frames'); expect(html).toContain('Export progress checkpoint');
    api.recovered = async () => ({ ...checkpoint(), sessionId: 'different' }); progress.mockClear(); await controller.exportProgress(); expect(progress).not.toHaveBeenCalled();
    const recovery = renderToStaticMarkup(<FreshRecovery state={{ ...controller.snapshot(), recovered: checkpoint() }} controller={controller}/>); expect(recovery).toContain('no numerical frames, complete portable record or resumable state');
  });
  it('does not export an older progress checkpoint when current persistence fails', async () => {
    const { api, controller } = fixture(3); await controller.connect();
    api.action = async (_action, id) => update(id, 3, { phase: 'storageBlocked', saveError: 'Checkpoint disk full' });
    const read = vi.spyOn(api, 'recovered'), exp = vi.spyOn(api, 'exportRecovery'); await controller.exportProgress();
    expect(read).not.toHaveBeenCalled(); expect(exp).not.toHaveBeenCalled(); expect(controller.snapshot().summary?.phase).toBe('storageBlocked'); expect(controller.snapshot().error).toContain('disk full');
  });
  it('makes actual request order visible and leaves absent order explicit for fixed tape or unstarted turns', () => {
    const c = new FreshController(), turn: SessionTurn = { requestOrder: 2, index: 0, id: '1', prompt: 'exact', reply: null, memoryEntryIds: [], requestStarted: true, observedStep: '1', applicationStep: null, status: 'completed', backend: 'scripted', model: null, encodedFeatures: null, semanticVector: null, failure: null, journalSaved: false, rawReply: null, requestedAction: null, chosenAction: null, contextKind: 'languageRequest', journalRelativePath: null, configuredModel: null, providerModel: null, tapePacketId: null, failurePhase: null, memoryText: null, memoryEntrySha256: null, journalEntryId: null, journalSha256: null };
    const state = { ...c.snapshot(), summary: summary(1, { config: { ...DEFAULT_FRESH_CONFIG, recipe: 'actionD' }, tracks: [{ ...summary(1).tracks[1], turnCount: 1, label: 'Right D' }] }), turn, turnRevision: '3' };
    const html = renderToStaticMarkup(<FreshJournal state={state} controller={c}/>); expect(html).toContain('Actual request order</dt><dd>2');
    const absent = renderToStaticMarkup(<FreshJournal state={{ ...state, turn: { ...turn, requestOrder: null, requestStarted: false } }} controller={c}/>); expect(absent).toContain('Absent · no request order retained'); expect(absent).toContain('fixed tape and unstarted opportunities');
  });
});
