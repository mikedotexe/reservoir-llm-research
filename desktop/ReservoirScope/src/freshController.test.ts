import { describe, expect, it, vi } from 'vitest';
import { FreshController } from './freshController';
import { DEFAULT_FRESH_CONFIG, DEFAULT_EXPLORATION, type FreshApi, type RecoveryCheckpoint, type SessionSummary, type SessionUpdate, type SessionFrame, type SessionTurn } from './freshTypes';

const frame = (index = 0): SessionFrame => ({ explorationControls: null, control: null, index, step: String(index + 1), time: (index + 1) / 3, state: Array(32).fill(.1), input: Array(66).fill(0), noise: Array(32).fill(0), fillPercent: null, eigenvalues: null, retentionUsed: null, semanticTurnId: null });
const turn: SessionTurn = { requestOrder: null, memoryText: null, memoryEntrySha256: null, journalEntryId: null, journalSha256: null, index: 0, id: '1', observedStep: '1', applicationStep: null, status: 'completed', backend: 'scripted', model: null, prompt: 'Observe only.', reply: 'Fixed text.', encodedFeatures: [1], semanticVector: [0], failure: null, journalSaved: true, rawReply: 'Fixed text.', requestedAction: 'WRITE', chosenAction: 'WRITE', contextKind: 'languageRequest', memoryEntryIds: [], journalRelativePath: 'journals/1.txt', configuredModel: null, providerModel: null, requestStarted: false, tapePacketId: null, failurePhase: null };
const summary = (patch: Partial<SessionSummary> = {}): SessionSummary => {
  const value = { sessionId: 'session-1', generation: '1', revision: '1', config: DEFAULT_FRESH_CONFIG, phase: 'ready' as const, step: 0, durableStep: 0, stepLimit: 120, frameCount: 0, turnCount: 0, journalCount: 0, unsavedRecord: false, pendingWrites: false, canStep: true, canRun: true, canExport: false, saveError: null, libraryEntryId: null, diagnostics: [], explorationControls: null, canRequestJournal: false, action: null, ...patch };
  return { ...value, tracks: patch.tracks ?? [{ id: 'right', label: 'Current', stage: null, frameCount: value.frameCount, turnCount: value.turnCount, journalCount: value.journalCount, status: 'stopped', failure: null, observationChannel: null, action: value.action }] };
};
function update(requestId: string, patch: Partial<SessionSummary> = {}): SessionUpdate {
  const s = summary(patch), f = s.frameCount ? frame(s.frameCount - 1) : null; return { requestId, summary: s, frame: f, frames: f ? { left: null, right: f } : null, pendingJournal: null, closeRequested: false };
}
function fixture() {
  let latest: ((u: SessionUpdate) => void) | null = null; let channelId = ''; let close: (() => void) | null = null; let closeWanted = false;
  const api: FreshApi = {
    get: async (requestId, onUpdate) => { latest = onUpdate; channelId = requestId; return { requestId, summary: null, frame: null, frames: null, pendingJournal: null, closeRequested: closeWanted }; },
    create: async requestId => update(requestId),
    action: async (action, requestId, _sessionId, _generation, onUpdate) => {
      if (action === 'run') { latest = onUpdate; channelId = requestId; return update(requestId, { phase: 'running', revision: '2' }); }
      if (action === 'reset') return update(requestId, { sessionId: 'session-2', generation: '2' });
      return update(requestId, { phase: 'paused', revision: '3', step: 1, frameCount: 1, unsavedRecord: true, canExport: true });
    },
    frame: async (requestId, sessionId, generation, index, trackId) => ({ requestId, sessionId, generation, revision: '3', trackId, frame: frame(index) }),
    turn: async (requestId, sessionId, generation, _index, trackId) => ({ requestId, sessionId, generation, trackId, revision: '3', turn }),
    export: async (requestId, sessionId, generation) => ({ requestId, sessionId, generation, revision: '3', file: null }),
    listenClose: async handler => { close = handler; return () => { close = null; }; }, finishClose: async () => false, regulationDetails: async () => { throw new Error('No regulation details'); }, cancelClose: async () => { closeWanted = false; }, controls: async requestId => update(requestId),
    recovery: async requestId => ({ requestId, entries: [], examined: 0, incompleteWrites: [], truncated: false }), recovered: async () => { throw new Error('No recovery checkpoint'); }, exportRecovery: async () => { throw new Error('No recovery checkpoint'); },
  };
  const controller = new FreshController(api);
  return { api, controller, push: (patch: Partial<SessionSummary>) => latest?.(update(channelId, patch)), oldChannel: () => ({ handler: latest!, id: channelId }), close: () => { closeWanted = true; close?.(); } };
}
describe('fresh session authority and retained lifecycle', () => {
  it('attachment creates no experiment or timer; steps only through explicit commands', async () => {
    const { api, controller } = fixture(); const create = vi.spyOn(api, 'create'), action = vi.spyOn(api, 'action');
    await controller.connect(); expect(create).not.toHaveBeenCalled(); expect(action).not.toHaveBeenCalled(); expect(controller.snapshot().summary).toBeNull();
    await controller.create(DEFAULT_FRESH_CONFIG); expect(controller.snapshot().frame).toBeNull(); expect(action).not.toHaveBeenCalled();
    await controller.action('step'); expect(action).toHaveBeenCalledWith('step', expect.any(String), 'session-1', '1', expect.any(Function), false, undefined); expect(controller.snapshot().frame?.step).toBe('1');
  });
  it('uses backend revisions, ignores older updates, and never advances its own clock', async () => {
    const { controller, push } = fixture(); await controller.create(DEFAULT_FRESH_CONFIG); await controller.action('run');
    push({ phase: 'running', revision: '4', step: 2, frameCount: 2 }); expect(controller.snapshot().frame?.step).toBe('2');
    push({ phase: 'running', revision: '3', step: 1, frameCount: 1 }); expect(controller.snapshot().frame?.step).toBe('2');
    await Promise.resolve(); expect(controller.snapshot().frame?.step).toBe('2');
  });
  it('retains session and channel updates without a mounted renderer or navigation pause command', async () => {
    const { api, controller, push } = fixture(); const action = vi.spyOn(api, 'action'); await controller.create(DEFAULT_FRESH_CONFIG); await controller.action('run');
    // UI subscriptions are independent from the backend channel lifetime.
    const unsubscribe = controller.subscribe(() => {}); unsubscribe(); push({ revision: '5', phase: 'completed', step: 120, frameCount: 120 });
    expect(controller.snapshot().summary?.phase).toBe('completed'); expect(action.mock.calls.map(v => v[0])).toEqual(['run']);
  });
  it('does not replace an accepted frame when its vector has the wrong shape', async () => {
    const { controller, oldChannel } = fixture(); await controller.create(DEFAULT_FRESH_CONFIG); await controller.action('run'); const channel = oldChannel();
    const malformed = update(channel.id, { revision: '3', step: 1, frameCount: 1 }); malformed.frame!.state = [9]; channel.handler(malformed);
    expect(controller.snapshot().frame).toBeNull(); expect(controller.snapshot().summary?.revision).toBe('2'); expect(controller.snapshot().error).toContain('32-node');
  });
  it('reset invalidates old channel and in-flight history callbacks', async () => {
    const { api, controller, oldChannel, push } = fixture(); await controller.create(DEFAULT_FRESH_CONFIG); await controller.action('run');
    push({ phase: 'paused', revision: '4', step: 2, frameCount: 2 }); const old = oldChannel(); let finish!: () => void;
    api.frame = (requestId, sessionId, generation, index, trackId) => new Promise(resolve => { finish = () => resolve({ requestId, sessionId, generation, revision: '4', trackId, frame: frame(index) }); });
    const pending = controller.frame(0); await controller.action('reset', true); finish(); await pending; old.handler(update(old.id, { revision: '999', step: 99, frameCount: 99 }));
    expect(controller.snapshot().summary?.sessionId).toBe('session-2'); expect(controller.snapshot().summary?.generation).toBe('2'); expect(controller.snapshot().frame).toBeNull();
  });
  it('failed journal save retains the identical pending candidate and never invents eligibility', async () => {
    const { api, controller } = fixture(); const candidate = { arm: 'right' as const, id: 'pending-1', actionId: 1, observedStep: 30, prompt: '<script>inert</script>', text: 'Fixed pending text', sha256: 'a'.repeat(64), relativePath: 'journals/1.txt' };
    api.create = async requestId => ({ ...update(requestId, { config: { ...DEFAULT_FRESH_CONFIG, recipe: 'journalE' }, phase: 'awaitingJournalSave', step: 30, frameCount: 30, unsavedRecord: true, canStep: false, canRun: false }), pendingJournal: candidate });
    await controller.create(DEFAULT_FRESH_CONFIG); api.action = async () => { throw new Error('Disk full; no receipt'); }; await controller.action('saveJournal');
    expect(controller.snapshot().pendingJournal).toBe(candidate); expect(controller.snapshot().summary?.canRun).toBe(false); expect(controller.snapshot().summary?.journalCount).toBe(0); expect(controller.snapshot().error).toContain('Disk full');
  });
  it('failed create/reset keeps prior identity and data; save failure is not a replacement', async () => {
    const { api, controller } = fixture(); await controller.create(DEFAULT_FRESH_CONFIG); await controller.action('step'); const accepted = controller.snapshot().frame;
    api.create = async () => { throw new Error('Save the current session first'); }; await controller.create(DEFAULT_FRESH_CONFIG); expect(controller.snapshot().frame).toBe(accepted);
    api.action = async () => { throw new Error('Write failed'); }; await controller.action('reset'); expect(controller.snapshot().frame).toBe(accepted); await controller.action('saveRecord'); expect(controller.snapshot().summary?.unsavedRecord).toBe(true); expect(controller.snapshot().error).toBe('Write failed');
  });
  it('manual frame inspection stays distinct from current running step and can follow latest again', async () => {
    const { controller, push } = fixture(); await controller.create(DEFAULT_FRESH_CONFIG); await controller.action('run'); push({ phase: 'running', revision: '5', step: 3, frameCount: 3 });
    await controller.frame(0); push({ phase: 'running', revision: '6', step: 4, frameCount: 4 }); expect(controller.snapshot().frame?.step).toBe('1'); expect(controller.snapshot().summary?.step).toBe(4); controller.follow(); expect(controller.snapshot().frame?.step).toBe('4');
  });
  it('cancelled export retains the session and saved file receipt is reported without implying Library save', async () => {
    const { api, controller } = fixture(); await controller.create(DEFAULT_FRESH_CONFIG); await controller.action('step'); await controller.export(); expect(controller.snapshot().message).toContain('cancelled'); expect(controller.snapshot().summary?.unsavedRecord).toBe(true);
    api.export = async (requestId, sessionId, generation) => ({ requestId, sessionId, generation, revision: '3', file: { name: 'record.json', sizeBytes: 50, sha256: 'a'.repeat(64) } }); await controller.export(); expect(controller.snapshot().exported?.name).toBe('record.json'); expect(controller.snapshot().summary?.unsavedRecord).toBe(true);
  });
  it('close attempts retain the backend decision and wait for pending writes', async () => {
    const { api, controller, close } = fixture(); await controller.listenClose(); close(); await Promise.resolve(); expect(controller.snapshot().closeRequested).toBe(true);
    const finish = vi.spyOn(api, 'finishClose'); await controller.finishClose(false); expect(controller.snapshot().error).toContain('still unsaved'); await controller.returnToApp(); expect(controller.snapshot().closeRequested).toBe(false);
    api.create = async requestId => update(requestId, { sessionId: 'writing-session', generation: '2', pendingWrites: true }); await controller.create(DEFAULT_FRESH_CONFIG); finish.mockClear(); await controller.finishClose(true); expect(finish).not.toHaveBeenCalled();
  });
  it('a persistent close flag survives listener registration and does not create or resume a session', async () => {
    const { api, controller } = fixture(); api.get = async requestId => ({ ...update(requestId, { phase: 'paused', unsavedRecord: true }), closeRequested: true });
    const action = vi.spyOn(api, 'action'), create = vi.spyOn(api, 'create'); await controller.listenClose(); await Promise.resolve(); expect(controller.snapshot().closeRequested).toBe(true); expect(action).not.toHaveBeenCalled(); expect(create).not.toHaveBeenCalled();
    const cancel = vi.spyOn(api, 'cancelClose'); await controller.returnToApp(); expect(cancel).toHaveBeenCalledOnce(); expect(action).not.toHaveBeenCalled();
  });
  it('applies explicit Explore controls without changing an older inspected frame', async () => {
    const { api, controller } = fixture(); await controller.create(DEFAULT_FRESH_CONFIG); await controller.action('step'); const accepted = controller.snapshot().frame;
    api.controls = async requestId => ({ ...update(requestId, { revision: '4', step: 1, frameCount: 1, explorationControls: { ...DEFAULT_EXPLORATION, recurrenceEnabled: true } }), frame: { ...frame(), explorationControls: DEFAULT_EXPLORATION } });
    await controller.frame(0); const historical = controller.snapshot().frame; await controller.controls({ ...DEFAULT_EXPLORATION, recurrenceEnabled: true });
    expect(controller.snapshot().summary?.explorationControls?.recurrenceEnabled).toBe(true); expect(controller.snapshot().frame).toBe(historical); expect(accepted?.step).toBe('1'); expect(controller.snapshot().message).toContain('next numerical boundary');
  });
  it('refreshes a selected turn after an explicit step applies later feedback', async () => {
    const { api, controller } = fixture(); api.create = async requestId => update(requestId, { step: 1, frameCount: 1, turnCount: 1 }); await controller.create(DEFAULT_FRESH_CONFIG); await controller.turn(0);
    api.action = async (_action, requestId) => update(requestId, { phase: 'paused', revision: '4', step: 2, frameCount: 2, turnCount: 1 });
    api.turn = async (requestId, sessionId, generation, _index, trackId) => ({ requestId, sessionId, generation, trackId, revision: '4', turn: { ...turn, applicationStep: '2' } });
    await controller.action('step'); await Promise.resolve(); expect(controller.snapshot().turn?.applicationStep).toBe('2'); expect(controller.snapshot().turnRevision).toBe('4');
  });
  it('requires new create/reset identity and reattaches an authoritative changed backend session on refresh', async () => {
    const { api, controller } = fixture(); await controller.create(DEFAULT_FRESH_CONFIG); await controller.action('step'); const previous = controller.snapshot().frame;
    await controller.create(DEFAULT_FRESH_CONFIG); expect(controller.snapshot().error).toContain('new session identity'); expect(controller.snapshot().frame).toBe(previous);
    api.action = async (_action, requestId) => update(requestId); await controller.action('reset', true); expect(controller.snapshot().error).toContain('new session and generation'); expect(controller.snapshot().frame).toBe(previous);
    api.get = async requestId => update(requestId, { sessionId: 'backend-current', generation: '9' }); await controller.connect(); expect(controller.snapshot().summary?.sessionId).toBe('backend-current'); expect(controller.snapshot().frame).toBeNull();
  });
  it('sends the explicit action mode and controls only on creation and retains accepted settings across reads', async () => {
    const { api, controller } = fixture();
    const config = { ...DEFAULT_FRESH_CONFIG, recipe: 'actionG' as const, actionMode: 'fixedReplay' as const, actionInputStrength: .4, actionBiasEnabled: true };
    const create = vi.spyOn(api, 'create').mockImplementation(async (id, accepted) => update(id, { config: accepted }));
    await controller.create(config); expect(create).toHaveBeenCalledWith(expect.any(String), config);
    api.get = async id => update(id, { config, revision: '2', step: 1, frameCount: 1 }); await controller.connect();
    expect(controller.snapshot().summary?.config.actionMode).toBe('fixedReplay'); expect(controller.snapshot().summary?.config.actionBiasEnabled).toBe(true); expect(create).toHaveBeenCalledOnce();
  });
  it('discards late saved-memory evidence when reset accepts a new generation', async () => {
    const { api, controller } = fixture(); api.create = async id => update(id, { config: { ...DEFAULT_FRESH_CONFIG, recipe: 'actionF' }, turnCount: 1 });
    await controller.create(DEFAULT_FRESH_CONFIG); let finish!: () => void;
    api.turn = (requestId, sessionId, generation, _index, trackId) => new Promise(resolve => { finish = () => resolve({ requestId, sessionId, generation, revision: '4', trackId, turn: { ...turn, memoryText: 'Old generation memory', memoryEntrySha256: 'a'.repeat(64) } }); });
    const read = controller.turn(0); await controller.action('reset', true); finish(); await read;
    expect(controller.snapshot().summary?.generation).toBe('2'); expect(controller.snapshot().turn).toBeNull(); expect(controller.snapshot().readingTurn).toBe(false);
  });
  it('rejects a nonfinite controller output without replacing the accepted frame', async () => {
    const { controller, oldChannel } = fixture(); await controller.create(DEFAULT_FRESH_CONFIG); await controller.action('run'); const channel = oldChannel();
    const next = update(channel.id, { revision: '3', step: 1, frameCount: 1 }); next.frame!.control = { error: 0, integral: 0, requestedRetention: Infinity, appliedRetention: .9 };
    channel.handler(next); expect(controller.snapshot().frame).toBeNull(); expect(controller.snapshot().summary?.revision).toBe('2'); expect(controller.snapshot().error).toContain('nonfinite retention');
  });
});

const checkpoint = (sessionId: string): RecoveryCheckpoint => ({ schema: 'checkpoint', sessionId, generation: '1', revision: '7', config: { recipe: 'journalE', seed: '20260909' }, phase: 'storageBlocked', step: 30, durableStep: 29, recordSha256: 'b'.repeat(64), pendingJournal: { entry: { text: 'Not yet saved' } }, attempts: [{ arm: 'right', number: 1, atMs: '100', entryId: 'journal-1', status: 'failed', diagnostic: 'Disk full' }], updatedAtMs: '101', discarded: false });

function paired(requestId: string, count = 2): SessionUpdate {
  const result = update(requestId, { revision: String(count + 1), phase: 'paused', step: count, frameCount: count, turnCount: 1, journalCount: 1, config: { ...DEFAULT_FRESH_CONFIG, recipe: 'actionG', actionComparePrevious: true } });
  result.summary!.tracks = ['left', 'right'].map((id, index) => ({ id: id as 'left' | 'right', label: index ? 'G current' : 'F previous', stage: index ? 7 : 6, frameCount: count, turnCount: 1, journalCount: 1, status: 'stopped', failure: null, observationChannel: 'sensory', action: null }));
  result.frames = count ? { left: { ...frame(count - 1), state: Array(32).fill(-.2) }, right: result.frame! } : null;
  return result;
}
describe('fresh comparison track and boundary authority', () => {
  it('selects the matching arm frame and rejects a channel update with misaligned clocks atomically', async () => {
    const { api, controller } = fixture(); api.create = async id => paired(id); await controller.create(DEFAULT_FRESH_CONFIG);
    controller.selectTrack('left'); expect(controller.snapshot().frame?.state[0]).toBe(-.2);
    let push!: () => void;
    api.get = async (id, onUpdate) => { const result = paired(id); const bad = paired(id, 3); bad.frames!.left!.step = '2'; push = () => onUpdate(bad); return result; };
    await controller.connect(); push(); expect(controller.snapshot().frames?.right.step).toBe('2'); expect(controller.snapshot().frames?.left?.step).toBe('2'); expect(controller.snapshot().error).toContain('same numerical boundary');
  });
  it('invalidates old arm turn reads even when indices and entry IDs coincide', async () => {
    const { api, controller } = fixture(); api.create = async id => paired(id); await controller.create(DEFAULT_FRESH_CONFIG); let finish!: () => void;
    api.turn = (requestId, sessionId, generation, _index, trackId) => new Promise(resolve => { finish = () => resolve({ requestId, sessionId, generation, trackId, revision: '3', turn: { ...turn, memoryText: 'right memory' } }); });
    const pending = controller.turn(0); controller.selectTrack('left');
    api.turn = async (requestId, sessionId, generation, _index, trackId) => ({ requestId, sessionId, generation, trackId, revision: '3', turn: { ...turn, memoryText: 'left memory' } });
    await controller.turn(0); finish(); await pending; expect(controller.snapshot().turn?.memoryText).toBe('left memory');
    api.turn = async (requestId, sessionId, generation) => ({ requestId, sessionId, generation, trackId: 'right', revision: '3', turn }); await controller.turn(0);
    expect(controller.snapshot().turn?.memoryText).toBe('left memory'); expect(controller.snapshot().error).toContain('did not match');
  });
  it('retains both prior frames if either historical arm read fails', async () => {
    const { api, controller } = fixture(); api.create = async id => paired(id); await controller.create(DEFAULT_FRESH_CONFIG); const before = controller.snapshot().frames;
    api.frame = async (requestId, sessionId, generation, index, trackId) => { if (trackId === 'left') throw new Error('Left history unavailable'); return { requestId, sessionId, generation, trackId, revision: '3', frame: frame(index) }; };
    await controller.frame(0); expect(controller.snapshot().frames).toBe(before); expect(controller.snapshot().error).toContain('Left history unavailable');
  });
  it('accepts history only after both requested tracks arrive and keeps it separate from following latest', async () => {
    const { api, controller } = fixture(); api.create = async id => paired(id, 3); await controller.create(DEFAULT_FRESH_CONFIG); let left!: () => void;
    api.frame = async (requestId, sessionId, generation, index, trackId) => {
      const result = { requestId, sessionId, generation, trackId, revision: '4', frame: { ...frame(index), state: Array(32).fill(trackId === 'left' ? -.5 : .5) } };
      return trackId === 'left' ? new Promise(resolve => { left = () => resolve(result); }) : result;
    };
    const pending = controller.frame(0); await Promise.resolve(); expect(controller.snapshot().frame?.step).toBe('3'); left(); await pending;
    expect(controller.snapshot().frames?.right.step).toBe('1'); controller.selectTrack('left'); expect(controller.snapshot().frame?.state[0]).toBe(-.5); controller.follow(); expect(controller.snapshot().frame?.step).toBe('3'); expect(controller.snapshot().frame?.state[0]).toBe(-.2);
  });
  it('binds sequential saves to the actual pending arm and entry instead of the inspected arm', async () => {
    const { api, controller } = fixture(); const candidate = { arm: 'left' as const, id: 'same-entry', actionId: 1, observedStep: 2, prompt: 'left context', text: 'same text', sha256: 'a'.repeat(64), relativePath: 'left/same-entry.json' };
    api.create = async id => ({ ...paired(id), pendingJournal: candidate }); await controller.create(DEFAULT_FRESH_CONFIG);
    const saved = vi.spyOn(api, 'action').mockImplementation(async (_action, id) => ({ ...paired(id), pendingJournal: { ...candidate, arm: 'right', relativePath: 'right/same-entry.json' } }));
    await controller.action('saveJournal'); expect(saved).toHaveBeenLastCalledWith('saveJournal', expect.any(String), 'session-1', '1', expect.any(Function), false, { arm: 'left', entryId: 'same-entry' });
    controller.selectTrack('left'); await controller.action('saveJournal'); expect(saved).toHaveBeenLastCalledWith('saveJournal', expect.any(String), 'session-1', '1', expect.any(Function), false, { arm: 'right', entryId: 'same-entry' });
  });
});
describe('fresh recovery inspection remains separate from execution', () => {
  it('lists/inspects a checkpoint without replacing the active session or resuming any steps', async () => {
    const { api, controller } = fixture(); await controller.create(DEFAULT_FRESH_CONFIG); const accepted = controller.snapshot().summary; const action = vi.spyOn(api, 'action');
    api.recovery = async requestId => ({ requestId, entries: [], examined: 3, truncated: true, incompleteWrites: ['unfinished temporary file'] }); api.recovered = async id => checkpoint(id);
    await controller.recovery(); await controller.recovered('old-session'); expect(controller.snapshot().recovered?.durableStep).toBe(29); expect(controller.snapshot().summary).toBe(accepted); expect(controller.snapshot().recovery?.truncated).toBe(true); expect(action).not.toHaveBeenCalled();
  });
  it('ignores an old selection response/failure and keeps prior detail on read failure', async () => {
    const { api, controller } = fixture(); let finish!: () => void;
    api.recovered = () => new Promise(resolve => { finish = () => resolve(checkpoint('old')); }); const pending = controller.recovered('old'); api.recovered = async id => checkpoint(id); await controller.recovered('new'); finish(); await pending; expect(controller.snapshot().recovered?.sessionId).toBe('new');
    api.recovered = async () => { throw new Error('Damaged checkpoint'); }; await controller.recovered('bad'); expect(controller.snapshot().recovered?.sessionId).toBe('new'); expect(controller.snapshot().recoveryError).toBe('Damaged checkpoint');
  });
  it('binds recovery export to the inspected generation/revision and distinguishes a prior portable snapshot', async () => {
    const { api, controller } = fixture(); api.recovered = async id => checkpoint(id); await controller.recovered('old');
    const exported = vi.spyOn(api, 'exportRecovery').mockImplementation(async (requestId, sessionId, _kind, generation, revision) => ({ requestId, sessionId, generation, revision, file: { name: 'snapshot.json', sizeBytes: 100, sha256: 'b'.repeat(64) } }));
    await controller.exportRecovery('record'); expect(exported).toHaveBeenCalledWith(expect.any(String), 'old', 'record', '1', '7'); expect(controller.snapshot().recoveryMessage).toContain('durable step 29');
    exported.mockImplementation(async (requestId, sessionId, _kind, generation, revision) => ({ requestId, sessionId, generation, revision, file: null })); await controller.exportRecovery('checkpoint'); expect(controller.snapshot().recoveryMessage).toContain('cancelled'); expect(controller.snapshot().recovered?.sessionId).toBe('old');
  });
  it('does not claim export success for a changed checkpoint identity or wrong portable bytes', async () => {
    const { api, controller } = fixture(); api.recovered = async id => checkpoint(id); await controller.recovered('old');
    api.exportRecovery = async (requestId, sessionId, _kind, generation, revision) => ({ requestId, sessionId, generation, revision, file: { name: 'changed.json', sizeBytes: 100, sha256: '0'.repeat(64) } }); await controller.exportRecovery('record'); expect(controller.snapshot().recoveryError).toContain('did not match'); expect(controller.snapshot().recoveryMessage).not.toContain('exported');
  });
  it('keeps accepted recovery evidence when a paired boundary duplicates an arm', async () => {
    const { api, controller } = fixture(); api.recovered = async id => checkpoint(id); await controller.recovered('accepted');
    api.recovered = async id => ({ ...checkpoint(id), pairedBoundary: { step: 30, arms: [{ arm: 'left', stage: 5, receipt: null, journal: null }, { arm: 'left', stage: 6, receipt: null, journal: null }] } });
    await controller.recovered('invalid-pair'); expect(controller.snapshot().recovered?.sessionId).toBe('accepted'); expect(controller.snapshot().recoveryError).toContain('invalid paired boundary');
  });
});

describe('asynchronous local language boundaries', () => {
  const config = { ...DEFAULT_FRESH_CONFIG, recipe: 'actionE' as const, language: { backend: 'ollama' as const, endpoint: 'http://127.0.0.1:11435', model: 'owned-test:tag', contextTokens: 4096, responseFormat: 'json' as const } };
  const pendingLanguage = { operationId: 'generation-1', arm: 'right' as const, turnId: 1, observedStep: 1, endpoint: config.language.endpoint, model: config.language.model, state: 'requesting' as const };
  it('reattaches after Create so a manual Step completion arrives without Run or a UI timer', async () => {
    const { api, controller, push } = fixture(); api.create = async id => update(id, { config }); const get = vi.spyOn(api, 'get');
    await controller.create(config); expect(get).toHaveBeenCalledOnce();
    api.action = async (_action, id) => update(id, { config, phase: 'awaitingLanguage', pendingLanguage, step: 1, frameCount: 1, revision: '3', canStep: false, canRun: false, canExport: false });
    await controller.action('step'); expect(controller.snapshot().summary?.pendingLanguage?.operationId).toBe('generation-1');
    const release = controller.subscribe(() => {}); release();
    push({ config, phase: 'paused', pendingLanguage: null, step: 1, frameCount: 1, revision: '4', canStep: true, canRun: true });
    expect(controller.snapshot().summary?.phase).toBe('paused'); expect(controller.snapshot().summary?.pendingLanguage).toBeNull();
  });
  it('held language blocks incompatible commands and Pause does not imply cancellation', async () => {
    const { api, controller } = fixture(); api.create = async id => update(id, { config, phase: 'awaitingLanguage', pendingLanguage, step: 1, frameCount: 1, canStep: false, canRun: false, canExport: false }); await controller.create(config);
    const action = vi.spyOn(api, 'action').mockImplementation(async (_action, id) => update(id, { config, phase: 'awaitingLanguage', pendingLanguage, step: 1, frameCount: 1, revision: '3', canStep: false, canRun: false, canExport: false }));
    for (const name of ['step', 'run', 'reset', 'saveRecord', 'requestJournal'] as const) await controller.action(name);
    expect(action).not.toHaveBeenCalled(); await controller.action('pause'); expect(action.mock.calls[0][0]).toBe('pause'); expect(controller.snapshot().summary?.pendingLanguage).toEqual(pendingLanguage);
  });
  it('stop followed by reset invalidates the old provider callback and attaches the new generation', async () => {
    const { api, controller, oldChannel } = fixture(); api.create = async id => update(id, { config }); await controller.create(config); const old = oldChannel();
    api.action = async (action, id) => action === 'reset' ? update(id, { config, sessionId: 'new-local', generation: '2' }) : update(id, { config, phase: 'stopped', revision: '4', pendingLanguage: null });
    await controller.action('stop'); await controller.action('reset', true);
    old.handler(update(old.id, { config, phase: 'awaitingLanguage', pendingLanguage, step: 1, frameCount: 1, revision: '999', canStep: false, canRun: false, canExport: false }));
    expect(controller.snapshot().summary?.sessionId).toBe('new-local'); expect(controller.snapshot().summary?.pendingLanguage).toBeFalsy();
  });
  it('malformed held requests cannot replace a valid reading or enable portable export', async () => {
    const { api, controller, oldChannel } = fixture(); api.create = async id => update(id, { config }); await controller.create(config); const old = oldChannel();
    old.handler(update(old.id, { config, phase: 'awaitingLanguage', pendingLanguage, step: 1, frameCount: 1, revision: '2', canStep: false, canRun: false, canExport: true }));
    expect(controller.snapshot().summary?.phase).toBe('ready'); expect(controller.snapshot().error).toContain('held local-model boundary');
  });
});
