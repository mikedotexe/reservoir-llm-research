import { beforeEach, describe, expect, it, vi } from 'vitest';
import { invoke, isTauri } from '@tauri-apps/api/core';
import { activationSetupApi } from './activationSetupApi';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: vi.fn(() => true) }));

beforeEach(() => { vi.mocked(invoke).mockReset(); vi.mocked(isTauri).mockReturnValue(true); });

describe('Activation setup command boundary', () => {
  it('uses the lifecycle commands with an explicit resume argument', async () => {
    await activationSetupApi.status(); await activationSetupApi.prepare(false); await activationSetupApi.prepare(true); await activationSetupApi.cancel();
    expect(invoke).toHaveBeenNthCalledWith(1, 'activation_setup_status', {});
    expect(invoke).toHaveBeenNthCalledWith(2, 'activation_setup_prepare', { resume: false });
    expect(invoke).toHaveBeenNthCalledWith(3, 'activation_setup_prepare', { resume: true });
    expect(invoke).toHaveBeenNthCalledWith(4, 'activation_setup_cancel', {});
  });

  it('never pretends a browser preview can prepare a native runtime', async () => {
    vi.mocked(isTauri).mockReturnValue(false);
    await expect(activationSetupApi.status()).rejects.toThrow('Open the desktop app');
    await expect(activationSetupApi.prepare(false)).rejects.toThrow('Reading examples does not need this runtime');
    expect(invoke).not.toHaveBeenCalled();
  });
});
