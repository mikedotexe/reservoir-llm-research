import { invoke, isTauri } from '@tauri-apps/api/core';
import type { ActivationApi } from './activationTypes';
async function command<T>(name: string, args: Record<string, unknown> = {}): Promise<T> {
  if (!isTauri()) throw new Error('Open the desktop app to use the local activation experiment.');
  return invoke<T>(name, args);
}
export const activationApi: ActivationApi = {
  inspect: config => command('activation_inspect', { config }),
  create: config => command('activation_create', { config }),
  start: sessionId => command('activation_start', { sessionId }),
  stop: sessionId => command('activation_stop', { sessionId }),
  get: sessionId => command('activation_get', { sessionId: sessionId ?? null }),
  list: () => command('activation_list'),
  restore: sessionId => command('activation_restore', { sessionId }),
  export: sessionId => command('activation_export', { sessionId }),
  import: () => command('activation_import'),
  annotate: (sessionId, annotation) => command('activation_annotate', { sessionId, annotation }),
};
