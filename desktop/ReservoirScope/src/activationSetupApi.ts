import { invoke, isTauri } from '@tauri-apps/api/core';
import type { ActivationSetupApi, ActivationSetupStatus } from './activationSetupTypes';

async function command(name: string, args: Record<string, unknown> = {}): Promise<ActivationSetupStatus> {
  if (!isTauri()) throw new Error('Open the desktop app to prepare or check the activation runtime. Reading examples does not need this runtime.');
  return invoke<ActivationSetupStatus>(name, args);
}

export const activationSetupApi: ActivationSetupApi = {
  status: () => command('activation_setup_status'),
  prepare: resume => command('activation_setup_prepare', { resume }),
  cancel: () => command('activation_setup_cancel'),
};
