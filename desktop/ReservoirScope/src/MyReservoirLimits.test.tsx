import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoirLimits from './MyReservoirLimits';
import { MyReservoirStatus } from './MyReservoir';
import { addHour, extensionError, SESSION_LIMIT_CAPS, sessionLimits } from './sustainedLimits';
import { DEFAULT_SUSTAINED_CONFIG, type SustainedLimits, type SustainedUpdate } from './myReservoirTypes';
import { reservoirFixture, reservoirSummary, settle } from './myReservoirTestFixtures';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));
const short: SustainedLimits = { maximumSteps: 10800, maximumTurns: 12, maximumDurationSeconds: 1800 };
const extended = addHour(short, DEFAULT_SUSTAINED_CONFIG);

async function prepared() {
  const fixture = reservoirFixture();
  await fixture.controller.connect();
  await fixture.controller.create({ ...DEFAULT_SUSTAINED_CONFIG, ...short });
  await settle();
  fixture.push({ phase: 'paused', step: 3, durableStep: 3, canExtendLimits: true, effectiveLimits: short, limitExtensionCount: 0 });
  return fixture;
}

describe('same-session limit extension', () => {
  it('adds time plus capacity at the requested pace, within existing ceilings', () => {
    expect(extended).toEqual({ maximumSteps: 14400, maximumTurns: 132, maximumDurationSeconds: 5400 });
    expect(addHour(short, { ...DEFAULT_SUSTAINED_CONFIG, paceMs: 250 })).toEqual({ maximumSteps: 25200, maximumTurns: 492, maximumDurationSeconds: 5400 });
    expect(addHour(SESSION_LIMIT_CAPS, { ...DEFAULT_SUSTAINED_CONFIG, paceMs: 0 })).toEqual(SESSION_LIMIT_CAPS);
    expect(addHour({ ...short, maximumDurationSeconds: 84600 }, DEFAULT_SUSTAINED_CONFIG)).toEqual({ maximumDurationSeconds: 86400, maximumSteps: 12600, maximumTurns: 72 });
    expect(short.maximumTurns).toBe(12);
  });

  it('requires monotonic whole-number totals and allows duration-only changes', () => {
    expect(extensionError(short, short)).toContain('Increase at least one');
    expect(extensionError(short, { ...extended, maximumTurns: 11 })).toContain('at least as high');
    for (const maximumDurationSeconds of [NaN, Infinity, 0, 86401, 5400.5]) {
      expect(extensionError(short, { ...extended, maximumDurationSeconds })).not.toBe('');
    }
    expect(extensionError(short, { ...short, maximumDurationSeconds: 3600 })).toBe('');
  });

  it('saves explicit totals against the current revision without starting or rewriting original settings', async () => {
    const { api, controller } = await prepared();
    const saved = controller.snapshot().summary!;
    const extension = vi.spyOn(api, 'extendLimits'), start = vi.spyOn(api, 'action');
    expect(await controller.extendLimits(extended, saved.revision)).toBe(true);
    expect(extension).toHaveBeenCalledWith(expect.any(String), saved.sessionId, saved.generation, saved.revision, extended);
    const after = controller.snapshot().summary!;
    expect(after.config).toEqual(saved.config);
    expect(after.sessionId).toBe(saved.sessionId);
    expect(sessionLimits(after)).toEqual(extended);
    expect(after.phase).toBe('paused');
    expect(after.limitExtensionCount).toBe(1);
    expect(start).not.toHaveBeenCalled();
    expect(controller.snapshot().message).toContain('Choose Resume');
  });

  it('does not promise Resume when another limit still holds after a valid duration extension', async () => {
    const { api, controller } = await prepared();
    const real = api.extendLimits;
    vi.spyOn(api, 'extendLimits').mockImplementation(async (...args) => {
      const result = await real(...args);
      return { ...result, summary: { ...result.summary!, canStart: false } };
    });
    expect(await controller.extendLimits({ ...short, maximumDurationSeconds: 3600 }, controller.snapshot().summary!.revision)).toBe(true);
    expect(controller.snapshot().message).toContain('Another limit');
    expect(controller.snapshot().message).not.toContain('Choose Resume');
  });

  it('rejects a stale displayed revision, unavailable boundary and invalid totals before dispatch', async () => {
    const { api, controller, push } = await prepared();
    const extension = vi.spyOn(api, 'extendLimits');
    const old = controller.snapshot().summary!.revision;
    push({ revision: '99' });
    expect(await controller.extendLimits(extended, old)).toBe(false);
    expect(controller.snapshot().error).toContain('session changed');
    expect(await controller.extendLimits(short, '99')).toBe(false);
    push({ canExtendLimits: false, phase: 'running' });
    expect(await controller.extendLimits(extended, '99')).toBe(false);
    expect(extension).not.toHaveBeenCalled();
  });

  it('leaves limits unchanged while saving or after a save failure and prevents duplicate submission', async () => {
    const { api, controller } = await prepared();
    const before = controller.snapshot().summary!;
    let reject!: (reason: Error) => void;
    const extension = vi.spyOn(api, 'extendLimits').mockReturnValue(new Promise<SustainedUpdate>((_, fail) => { reject = fail; }));
    const saving = controller.extendLimits(extended, before.revision);
    expect(controller.snapshot().busy).toBe('extendLimits');
    expect(sessionLimits(controller.snapshot().summary!)).toEqual(short);
    expect(await controller.extendLimits(extended, before.revision)).toBe(false);
    reject(new Error('Extension could not be saved'));
    expect(await saving).toBe(false);
    expect(controller.snapshot().summary).toBe(before);
    expect(controller.snapshot().error).toContain('could not be saved');
    expect(controller.snapshot().busy).toBeNull();
    expect(extension).toHaveBeenCalledTimes(1);
  });

  it('shows effective totals and exposes an editor only when the backend permits it', () => {
    const { controller } = reservoirFixture();
    const summary = reservoirSummary({ config: { ...DEFAULT_SUSTAINED_CONFIG, ...short }, effectiveLimits: extended, phase: 'paused', canExtendLimits: true, limitExtensionCount: 1 });
    const state = { ...controller.snapshot(), summary };
    const html = renderToStaticMarkup(<MyReservoirLimits state={state} controller={controller}/>);
    expect(html).toContain('1 hour 30 minutes');
    expect(html).toContain('132 writing attempts');
    expect(html).toContain('Add 1 hour');
    expect(html).toContain('New total duration');
    expect(html).toContain('Save extended limits');
    expect(html).toContain('disabled=""'); // unchanged proposal cannot be saved
    const status = renderToStaticMarkup(<MyReservoirStatus state={state}/>);
    expect(status).toContain('1 hour 30 minutes');
    expect(status).toContain('14400');
    expect(status).not.toContain('10800');
    const running = renderToStaticMarkup(<MyReservoirLimits state={{ ...state, summary: { ...summary, phase: 'running', canExtendLimits: false } }} controller={controller}/>);
    expect(running).toContain('Pause and resolve');
    expect(running).not.toContain('Save extended limits');
  });
});
