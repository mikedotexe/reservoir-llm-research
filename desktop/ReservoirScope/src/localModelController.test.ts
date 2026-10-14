import { describe, expect, it, vi } from 'vitest';
import { LocalModelController, localModelError, type ModelReadinessApi, type ModelReadinessResult } from './localModelController';
import { DEFAULT_FRESH_CONFIG, normalizeLanguage, selectActionComparison, selectActionMode, selectFreshRecipe, selectLanguageBackend, supportsLocalModel, type LanguageConfiguration } from './freshTypes';

const configuration: LanguageConfiguration = { backend: 'ollama', endpoint: 'http://127.0.0.1:11435', model: 'exact-model:tag', contextTokens: 4096, responseFormat: 'json' };
const result = (requestId: string, c = configuration): ModelReadinessResult => ({ requestId, operationId: 'readiness-operation', endpoint: c.endpoint!, requestedModel: c.model!, status: 'found', matchedModel: c.model!, digest: 'sha256:retained', checkedAtMs: '100', diagnostic: null });
function fixture() { const api: ModelReadinessApi = { check: vi.fn(async (id, c) => result(id, c)), cancel: vi.fn(async () => {}) }; return { api, controller: new LocalModelController(api) }; }

describe('explicit local model selection and readiness', () => {
  it('defaults to scripted/blank fields and clears model settings on ineligible recipes or fixed tape', () => {
    expect(DEFAULT_FRESH_CONFIG.language?.backend ?? 'scripted').toBe('scripted');
    const action = selectLanguageBackend({ ...DEFAULT_FRESH_CONFIG, recipe: 'actionH' }, 'ollama');
    expect(action.language).toEqual({ backend: 'ollama', endpoint: '', model: '', contextTokens: 4096, responseFormat: 'json' });
    const accepted = { ...action, language: configuration };
    for (const recipe of ['exploration', 'stage1', 'stage2', 'actionA', 'actionB', 'actionC', 'regulation'] as const) expect(selectFreshRecipe(accepted, recipe).language?.backend ?? 'scripted').toBe('scripted');
    const tape = selectActionMode(accepted, 'fixedReplay'); expect(tape.language).toEqual({ backend: 'scripted' }); expect(selectActionMode(tape, 'independentGeneration').language).toEqual({ backend: 'scripted' });
    expect(supportsLocalModel(tape)).toBe(false); expect(selectFreshRecipe(accepted, 'stage3').language?.responseFormat).toBeNull();
    expect(selectActionComparison(accepted, 'observation').language?.responseFormat).toBe('json');
    expect(normalizeLanguage({ ...accepted, recipe: 'stage4' }).language?.endpoint).toBe(configuration.endpoint);
  });
  it('selecting configuration creates no service operation; only explicit check calls the backend', async () => {
    const { api, controller } = fixture(); controller.select(configuration); expect(api.check).not.toHaveBeenCalled(); expect(controller.snapshot().result).toBeNull();
    await controller.check(configuration); expect(api.check).toHaveBeenCalledOnce(); expect(controller.snapshot().result?.digest).toBe('sha256:retained');
  });
  it('rejects nonloopback, credential, implicit-port and invalid context/model configurations without contact', async () => {
    const { api, controller } = fixture();
    for (const endpoint of ['http://127.1:11435', 'http://remote.example:11435', 'http://user@localhost:11435', 'http://localhost', 'https://localhost:11435', 'http://localhost:11435/api', 'http://localhost:11435?x', 'http://localhost:0', 'http://localhost:65536']) { await controller.check({ ...configuration, endpoint }); expect(controller.snapshot().error).toContain('loopback'); }
    for (const c of [{ ...configuration, model: '' }, { ...configuration, model: ' padded ' }, { ...configuration, contextTokens: 511 }, { ...configuration, contextTokens: 4096.5 }]) expect(localModelError(c)).not.toBeNull();
    expect(api.check).not.toHaveBeenCalled(); expect(localModelError({ ...configuration, endpoint: 'http://[::1]:11435/' })).toBeNull();
  });
  it('changing endpoint/model/context invalidates the pending check and discards late results', async () => {
    const { api, controller } = fixture(); let finish!: () => void;
    api.check = (id, c) => new Promise(resolve => { finish = () => resolve(result(id, c)); }); const pending = controller.check(configuration);
    controller.select({ ...configuration, contextTokens: 8192 }); expect(api.cancel).toHaveBeenCalledOnce(); finish(); await pending; expect(controller.snapshot().result).toBeNull(); expect(controller.snapshot().checking).toBe(false);
  });
  it('cancel clears the receipt immediately and late completion cannot promote availability', async () => {
    const { api, controller } = fixture(); let finish!: () => void;
    api.check = (id, c) => new Promise(resolve => { finish = () => resolve(result(id, c)); }); const pending = controller.check(configuration); await controller.cancel();
    expect(controller.snapshot().result).toBeNull(); finish(); await pending; expect(controller.snapshot().result).toBeNull(); expect(controller.snapshot().message).toContain('discarded');
  });
  it('a cancelled earlier request cannot erase or replace a newer exact-configuration receipt', async () => {
    const { api, controller } = fixture(); const finish: (() => void)[] = [];
    api.check = (id, c) => new Promise(resolve => finish.push(() => resolve(result(id, c))));
    const a = controller.check(configuration), b = controller.check({ ...configuration, model: 'other:tag' }); finish[1](); await b; finish[0](); await a;
    expect(controller.snapshot().result?.requestedModel).toBe('other:tag'); expect(controller.snapshot().checking).toBe(false);
  });
  it('rejects mismatched identity and retains HTTP unavailable separately from validation errors', async () => {
    const { api, controller } = fixture(); api.check = async id => ({ ...result(id), requestedModel: 'different' }); await controller.check(configuration); expect(controller.snapshot().error).toContain('does not match'); expect(controller.snapshot().result).toBeNull();
    api.check = async id => ({ ...result(id), status: 'unavailable', matchedModel: null, digest: null, diagnostic: 'Service unavailable' }); await controller.check(configuration); expect(controller.snapshot().result?.status).toBe('unavailable'); expect(controller.snapshot().error).toBe('');
  });
  it('disposal cancels an in-flight check and never accepts its subsequent response', async () => {
    const { api, controller } = fixture(); let finish!: () => void; api.check = (id, c) => new Promise(resolve => { finish = () => resolve(result(id, c)); });
    const pending = controller.check(configuration); controller.dispose(); finish(); await pending; expect(api.cancel).toHaveBeenCalledOnce(); expect(controller.snapshot().result).toBeNull();
  });
});
