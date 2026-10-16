import { invoke, isTauri } from '@tauri-apps/api/core';
import type { ActivationReadingApi } from './activationReadingTypes';
async function command<T>(name: string, args: Record<string, unknown>): Promise<T> {
  if (!isTauri()) throw new Error('Open the desktop app to read the bundled collection and use local file dialogs.');
  return invoke<T>(name, args);
}
export const activationReadingApi: ActivationReadingApi = {
  open: bundled => command('activation_reading_open', { bundled }),
  export: collectionId => command('activation_reading_export', { collectionId }),
  close: collectionId => command('activation_reading_close', { collectionId }),
};
