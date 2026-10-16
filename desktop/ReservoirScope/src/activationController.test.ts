import { afterEach, describe, expect, it, vi } from 'vitest';
import { DEFAULT_ACTIVATION_CONFIG } from './activationTypes';
import { activationFixture, activationJournal, activationSession } from './activationTestFixtures';
import { validateActivationSnapshot } from './activationController';

afterEach(() => vi.useRealTimers());
describe('Activation experiment ownership and reading', () => {
  it('does not inspect, create, start or poll merely because it becomes visible', async () => {
    vi.useFakeTimers(); const { controller, api } = activationFixture(); controller.setActive(true); await vi.advanceTimersByTimeAsync(5000);
    expect(api.inspect).not.toHaveBeenCalled(); expect(api.create).not.toHaveBeenCalled(); expect(api.start).not.toHaveBeenCalled(); expect(api.get).not.toHaveBeenCalled(); controller.setActive(false);
  });
  it('requires a check for the exact configuration and explicit start after create', async () => {
    const { controller, api } = activationFixture(); expect(await controller.create(DEFAULT_ACTIVATION_CONFIG)).toBe(false);
    await controller.inspect(DEFAULT_ACTIVATION_CONFIG); expect(await controller.create({ ...DEFAULT_ACTIVATION_CONFIG, arm: 'recurrent' })).toBe(false);
    expect(await controller.create(DEFAULT_ACTIVATION_CONFIG)).toBe(true); expect(api.start).not.toHaveBeenCalled(); expect(controller.snapshot().current?.status).toBe('ready');
    await controller.start(); expect(api.start).toHaveBeenCalledExactlyOnceWith('session-1');
  });
  it('does not accept a failed capability check as permission to create', async () => {
    const { api, controller } = activationFixture(); vi.mocked(api.inspect).mockResolvedValue({ ready: false });
    await controller.inspect(DEFAULT_ACTIVATION_CONFIG); expect(await controller.create(DEFAULT_ACTIVATION_CONFIG)).toBe(false); expect(api.create).not.toHaveBeenCalled();
  });
  it('polls only a visible running experiment and stops at a terminal outcome', async () => {
    vi.useFakeTimers(); const { controller, api, update, prepare } = activationFixture(); controller.setActive(true); await prepare(); await vi.advanceTimersByTimeAsync(3000); expect(api.get).not.toHaveBeenCalled();
    await controller.start(); await vi.advanceTimersByTimeAsync(1000); expect(api.get).toHaveBeenCalledTimes(1);
    controller.setActive(false); await vi.advanceTimersByTimeAsync(3000); expect(api.get).toHaveBeenCalledTimes(1);
    update(activationSession({ revision: 3, status: 'completed', canStart: false })); controller.setActive(true); await vi.advanceTimersByTimeAsync(1000); expect(api.get).toHaveBeenCalledTimes(2);
    await vi.advanceTimersByTimeAsync(3000); expect(api.get).toHaveBeenCalledTimes(2); controller.setActive(false);
  });
  it('holds polling after a read error instead of repeatedly retrying', async () => {
    vi.useFakeTimers(); const { controller, api, prepare } = activationFixture(); controller.setActive(true); await prepare(); await controller.start(); vi.mocked(api.get).mockRejectedValue(new Error('read unavailable'));
    await vi.advanceTimersByTimeAsync(5000); expect(api.get).toHaveBeenCalledTimes(1); expect(controller.snapshot().error).toContain('Use Refresh'); controller.setActive(false);
  });
  it('keeps a selected journal stable during later arrivals and supports chronological return', async () => {
    const { controller, update, prepare } = activationFixture(); await prepare();
    update(activationSession({ revision: 2, step: 41, journals: [activationJournal(1), activationJournal(2)], journalCount: 2 })); await controller.refresh();
    expect(controller.snapshot().selected['session-1']).toBe('journal-2'); controller.select('session-1', 'journal-1');
    update(activationSession({ revision: 3, step: 61, journals: [activationJournal(1), activationJournal(2), activationJournal(3)], journalCount: 3 })); await controller.refresh();
    expect(controller.snapshot().selected['session-1']).toBe('journal-1'); controller.adjacent('session-1', 1); expect(controller.snapshot().selected['session-1']).toBe('journal-2');
    controller.follow('session-1'); expect(controller.snapshot().selected['session-1']).toBe('journal-3');
  });
  it('rejects stale or foreign snapshots without replacing retained reading', async () => {
    const { controller, update, prepare } = activationFixture(); await prepare();
    update(activationSession({ revision: 4, step: 21, journals: [activationJournal()], journalCount: 1 })); await controller.refresh();
    update(activationSession({ revision: 2 })); await controller.refresh(); expect(controller.snapshot().current?.revision).toBe(4);
    update(activationSession({ sessionId: 'other', revision: 9 })); await controller.refresh(); expect(controller.snapshot().current?.sessionId).toBe('session-1'); expect(controller.snapshot().current?.journals).toHaveLength(1);
  });
  it('ignores a delayed poll that arrives after Stop', async () => {
    const { controller, api, prepare } = activationFixture(); await prepare(); await controller.start();
    let resolve!: (s: ReturnType<typeof activationSession>) => void;
    vi.mocked(api.get).mockImplementationOnce(() => new Promise(r => { resolve = r; })); const pending = controller.refresh();
    await controller.stop(); resolve(activationSession({ status: 'running', revision: 20 })); await pending;
    expect(controller.snapshot().current?.status).toBe('stopped');
  });
  it('imports and restores for reading without automatically starting', async () => {
    const { controller, api } = activationFixture(); await controller.import(); expect(controller.snapshot().current?.status).toBe('paused'); await controller.restore('session-1'); expect(api.start).not.toHaveBeenCalled();
  });
  it('limits comparison to three sessions and hides labels again when selection changes', () => {
    const { controller } = activationFixture(); for (let i = 1; i <= 3; i++) controller.compare(activationSession({ sessionId: `s${i}` }), true);
    controller.reveal(); expect(controller.snapshot().revealed).toBe(true); controller.compare(activationSession({ sessionId: 's4' }), true); expect(controller.snapshot().comparisons).toHaveLength(3);
    controller.compare(activationSession({ sessionId: 's3' }), false); expect(controller.snapshot().revealed).toBe(false);
  });
  it('stores linked interpretations separately without dispatching model work', async () => {
    const { controller, api, update, prepare } = activationFixture(); await prepare(); update(activationSession({ revision: 2, journals: [activationJournal()], journalCount: 1 })); await controller.refresh();
    const note = { journalId: 'journal-1', excerpt: 'A question remains open.', interpretation: 'It holds the unresolved question.', alternative: 'This could echo the invitation.', sourceEventIds: ['event-1'] };
    expect(await controller.annotate('session-1', note)).toBe(true); expect(api.annotate).toHaveBeenCalledExactlyOnceWith('session-1', note); expect(api.start).not.toHaveBeenCalled();
    expect(await controller.annotate('session-1', { ...note, excerpt: 'Invented quote' })).toBe(false); expect(api.annotate).toHaveBeenCalledTimes(1);
  });
  it('rejects impossible feedback timing and duplicated journal identities', () => {
    expect(() => validateActivationSnapshot(activationSession({ journalCount: 1, journals: [{ ...activationJournal(), firstAppliedStep: 20 }] }))).toThrow('application steps');
    expect(() => validateActivationSnapshot(activationSession({ journalCount: 2, journals: [activationJournal(), activationJournal()] }))).toThrow();
  });
  it('preserves incomplete writing beyond 64 KiB within the existing response bound', () => {
    const { controller } = activationFixture();
    const text = 'Retained unfinished response. '.repeat(3000);
    expect(text.length).toBeGreaterThan(65536);
    const attempt = { requestId: 'request-21', text, observedStep: 60, stopReason: 'max_tokens', responseSha256: 'f'.repeat(64), feedbackEligible: false as const };
    controller.compare(activationSession({ incompleteAttempts: [attempt] }), true);
    expect(controller.snapshot().comparisons[0].incompleteAttempts?.[0].text).toBe(text);
    expect(controller.snapshot().comparisons[0].journalCount).toBe(0);
    expect(() => validateActivationSnapshot(activationSession({ incompleteAttempts: [{ ...attempt, text: 'x'.repeat(8 * 1024 * 1024 + 1) }] }))).toThrow('incomplete writing');
  });
});
