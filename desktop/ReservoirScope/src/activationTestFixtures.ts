import { vi } from 'vitest';
import { ActivationController } from './activationController';
import { DEFAULT_ACTIVATION_CONFIG, type ActivationApi, type ActivationJournal, type ActivationSnapshot } from './activationTypes';
export const activationJournal = (n = 1): ActivationJournal => ({ id: `journal-${n}`, text: `Complete journal ${n}.\nA question remains open.`, observedStep: n * 20, firstAppliedStep: n * 20 + 1, sha256: 'a'.repeat(64), status: 'applied' });
export const activationSession = (overrides: Partial<ActivationSnapshot> = {}): ActivationSnapshot => ({ sessionId: 'session-1', revision: 1, status: 'ready', config: { ...DEFAULT_ACTIVATION_CONFIG, observations: [...DEFAULT_ACTIVATION_CONFIG.observations] }, step: 0, observationIndex: 0, journalCount: 0, journals: [], events: [{ id: 'event-1', kind: 'created', step: 0, detail: 'Prepared experiment' }], diagnostic: null, activeOperation: null, directory: '/retained/session-1', canStart: true, annotations: [], ...overrides });
export function activationFixture(initial = activationSession()) {
  let current = initial;
  const api: ActivationApi = {
    inspect: vi.fn(async config => ({ ready: true, config })),
    create: vi.fn(async config => { current = activationSession({ config }); return current; }),
    start: vi.fn(async () => { current = { ...current, revision: current.revision + 1, status: 'running', canStart: false }; return current; }),
    stop: vi.fn(async () => { current = { ...current, revision: current.revision + 1, status: 'stopped', activeOperation: null, canStart: false }; return current; }),
    get: vi.fn(async () => current), list: vi.fn(async () => [current]),
    restore: vi.fn(async () => ({ ...current, status: 'paused', activeOperation: null, canStart: false })),
    export: vi.fn(async () => ({ path: '/export.json', verified: true })),
    import: vi.fn(async () => ({ ...current, status: 'paused', activeOperation: null, canStart: false })),
    annotate: vi.fn(async (_id, note) => { current = { ...current, revision: current.revision + 1, annotations: [...current.annotations ?? [], note] }; return current; }),
  };
  const controller = new ActivationController(api, 1000);
  return { api, controller, update: (snapshot: ActivationSnapshot) => { current = snapshot; }, prepare: async () => { await controller.inspect(DEFAULT_ACTIVATION_CONFIG); await controller.create(DEFAULT_ACTIVATION_CONFIG); } };
}
