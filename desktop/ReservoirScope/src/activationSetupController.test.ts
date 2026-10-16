import { afterEach, describe, expect, it, vi } from 'vitest';
import { ActivationSetupController } from './activationSetupController';
import { validateActivationSetupStatus, type ActivationSetupApi, type ActivationSetupStatus } from './activationSetupTypes';

const missing: ActivationSetupStatus = { state: 'missing', phase: 'check', message: 'Prepare the runtime to start a new experiment.', canResume: false, requiredBytes: 8 * 1024 ** 3 };
const preparing: ActivationSetupStatus = { ...missing, state: 'preparing', phase: 'model', message: 'Downloading pinned model assets.', downloadedBytes: 1024, totalBytes: 4096, setupId: 'setup-1' };
const interrupted: ActivationSetupStatus = { ...preparing, state: 'interrupted', message: 'The owned preparation process was cancelled.', canResume: true };
const ready: ActivationSetupStatus = { ...missing, state: 'ready', phase: 'complete', message: 'All pinned assets verified.', pythonPath: '/Library/Application Support/Example/runtime/bin/python', modelPath: '/Library/Application Support/Example/model', setupId: 'setup-1' };

function fixture() {
  const api: ActivationSetupApi = { status: vi.fn(async () => missing), prepare: vi.fn(async () => preparing), cancel: vi.fn(async () => interrupted) };
  return { api, controller: new ActivationSetupController(api) };
}

afterEach(() => vi.useRealTimers());

describe('Activation runtime preparation ownership', () => {
  it('checks status on entry without starting preparation and never resumes an interrupted setup automatically', async () => {
    vi.useFakeTimers();
    const { api, controller } = fixture();
    vi.mocked(api.status).mockResolvedValue(interrupted);
    controller.setActive(true); await vi.advanceTimersByTimeAsync(10_000);
    expect(api.status).toHaveBeenCalledTimes(1);
    expect(api.prepare).not.toHaveBeenCalled(); expect(api.cancel).not.toHaveBeenCalled();
    expect(controller.snapshot().status?.state).toBe('interrupted');
    controller.setActive(false);
  });

  it('requires known eligible status and an explicit choice to prepare or resume', async () => {
    const { api, controller } = fixture();
    expect(await controller.prepare()).toBe(false);
    await controller.refresh(); expect(await controller.prepare(true)).toBe(false);
    expect(await controller.prepare(false)).toBe(true);
    expect(api.prepare).toHaveBeenCalledExactlyOnceWith(false);
    await controller.cancel();
    expect(await controller.prepare(false)).toBe(false);
    expect(await controller.prepare(true)).toBe(true);
    expect(api.prepare).toHaveBeenNthCalledWith(2, true);
  });

  it('polls only visible preparation and stops polling after ready', async () => {
    vi.useFakeTimers(); const { api, controller } = fixture();
    controller.setActive(true); await vi.advanceTimersByTimeAsync(0); await controller.prepare();
    vi.mocked(api.status).mockResolvedValue(preparing);
    await vi.advanceTimersByTimeAsync(1000); expect(api.status).toHaveBeenCalledTimes(2);
    controller.setActive(false); await vi.advanceTimersByTimeAsync(5000); expect(api.status).toHaveBeenCalledTimes(2);
    vi.mocked(api.status).mockResolvedValue(ready);
    controller.setActive(true); await vi.advanceTimersByTimeAsync(5000); expect(api.status).toHaveBeenCalledTimes(3);
    expect(controller.snapshot().status?.state).toBe('ready'); expect(api.prepare).toHaveBeenCalledTimes(1);
    controller.setActive(false);
  });

  it('rejects duplicate prepare commands while one is in flight', async () => {
    const { api, controller } = fixture(); await controller.refresh();
    let resolve!: (status: ActivationSetupStatus) => void;
    vi.mocked(api.prepare).mockImplementationOnce(() => new Promise(r => { resolve = r; }));
    const request = controller.prepare();
    expect(await controller.prepare()).toBe(false); expect(await controller.cancel()).toBe(false);
    expect(api.prepare).toHaveBeenCalledTimes(1);
    resolve(preparing); await request; expect(controller.snapshot().pending).toBeNull();
  });

  it('accepts cancellation during a status read and ignores its delayed preparing result', async () => {
    const { api, controller } = fixture(); await controller.refresh(); await controller.prepare();
    let resolve!: (status: ActivationSetupStatus) => void;
    vi.mocked(api.status).mockImplementationOnce(() => new Promise(r => { resolve = r; }));
    const read = controller.refresh(); expect(controller.snapshot().checking).toBe(true);
    expect(await controller.cancel()).toBe(true);
    resolve(preparing); await read;
    expect(controller.snapshot().status).toEqual(interrupted); expect(controller.snapshot().checking).toBe(false);
  });

  it('ignores a delayed failed status read after cancellation succeeded', async () => {
    const { api, controller } = fixture(); await controller.refresh(); await controller.prepare();
    let reject!: (error: Error) => void;
    vi.mocked(api.status).mockImplementationOnce(() => new Promise((_, r) => { reject = r; }));
    const read = controller.refresh(); await controller.cancel(); reject(new Error('Old status read failed')); await read;
    expect(controller.snapshot().status).toEqual(interrupted); expect(controller.snapshot().error).toBe('');
  });

  it('does not overwrite ready with an assumed interrupted state if cancellation raced completion', async () => {
    const { api, controller } = fixture(); await controller.refresh(); await controller.prepare();
    vi.mocked(api.cancel).mockResolvedValueOnce(ready); await controller.cancel();
    expect(controller.snapshot().status).toEqual(ready);
    expect(await controller.prepare()).toBe(false); expect(await controller.prepare(true)).toBe(false);
  });

  it('holds after status failure until an explicit read, retaining the last known status', async () => {
    vi.useFakeTimers(); const { api, controller } = fixture();
    controller.setActive(true); await vi.advanceTimersByTimeAsync(0); await controller.prepare();
    vi.mocked(api.status).mockRejectedValueOnce(new Error('Read unavailable'));
    await vi.advanceTimersByTimeAsync(10_000);
    expect(api.status).toHaveBeenCalledTimes(2); expect(controller.snapshot().status).toEqual(preparing);
    expect(controller.snapshot().error).toContain('Check setup status');
    vi.mocked(api.status).mockResolvedValue(interrupted); await controller.refresh();
    expect(controller.snapshot().error).toBe(''); expect(controller.snapshot().status).toEqual(interrupted);
    expect(api.prepare).toHaveBeenCalledTimes(1); controller.setActive(false);
  });

  it('requires a fresh status read after a preparation transport failure', async () => {
    const { api, controller } = fixture(); await controller.refresh();
    vi.mocked(api.prepare).mockRejectedValueOnce(new Error('Command acknowledgement unavailable'));
    expect(await controller.prepare()).toBe(false); expect(await controller.prepare()).toBe(false);
    expect(api.prepare).toHaveBeenCalledTimes(1);
    vi.mocked(api.status).mockResolvedValue(preparing); await controller.refresh();
    expect(controller.snapshot().status).toEqual(preparing); expect(await controller.prepare()).toBe(false);
  });

  it('does not cancel the app-owned preparation when its view closes', async () => {
    const { api, controller } = fixture(); await controller.refresh(); await controller.prepare();
    controller.setActive(false); expect(api.cancel).not.toHaveBeenCalled();
  });

  it('refuses unsupported or already qualified setups', async () => {
    const { api, controller } = fixture();
    for (const status of [{ ...missing, state: 'unsupported' as const }, ready]) {
      vi.mocked(api.status).mockResolvedValue(status); await controller.refresh();
      expect(await controller.prepare()).toBe(false); expect(await controller.prepare(true)).toBe(false); expect(await controller.cancel()).toBe(false);
    }
    expect(api.prepare).not.toHaveBeenCalled();
  });

  it('rejects invalid readiness, progress, and resume claims without replacing a valid status', async () => {
    const { api, controller } = fixture(); await controller.refresh();
    const bad = [
      { ...ready, pythonPath: null }, { ...ready, modelPath: 'relative/model' },
      { ...preparing, downloadedBytes: -1 }, { ...preparing, totalBytes: Infinity },
      { ...preparing, requiredBytes: 2.5 }, { ...ready, canResume: true },
    ];
    for (const status of bad) {
      expect(() => validateActivationSetupStatus(status)).toThrow('invalid');
      vi.mocked(api.status).mockResolvedValue(status); await controller.refresh();
      expect(controller.snapshot().status).toEqual(missing);
    }
  });
});
