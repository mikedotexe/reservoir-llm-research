import { Channel, invoke, isTauri } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import type { MyReservoirApi, SustainedUpdate } from './myReservoirTypes';

async function command<T>(name: string, args: Record<string, unknown>): Promise<T> {
  if (!isTauri()) throw new Error('Open the desktop app to create and retain your reservoir.');
  return invoke<T>(name, args);
}
export const myReservoirApi: MyReservoirApi = {
  get: (requestId, onUpdate) => command('get_sustained', { requestId, onUpdate: new Channel<SustainedUpdate>(onUpdate) }),
  create: (requestId, config) => command('create_sustained', { requestId, config }),
  action: (action, requestId, sessionId, generation, expectedEntryId = null, expectedAttemptId = null) => command(({ start: 'start_sustained', pause: 'pause_sustained', stop: 'stop_sustained', retrySave: 'retry_sustained_save', retryProvider: 'retry_sustained_language', skipFeedback: 'skip_sustained_feedback' })[action], { requestId, sessionId, generation, ...(action === 'skipFeedback' ? { expectedEntryId, expectedAttemptId } : {}) }),
  journals: (requestId, sessionId, generation, offset, limit) => command('list_sustained_journals', { requestId, sessionId, generation, offset, limit }),
  journal: (requestId, sessionId, generation, entryId) => command('get_sustained_journal', { requestId, sessionId, generation, entryId }),
  listenClose: async handler => isTauri() ? listen('sustained-close-requested', handler) : () => {},
  finishClose: allowDiscard => command('finish_sustained_close', { allowDiscard }),
  cancelClose: () => command('cancel_sustained_close', {}),
  export: (requestId, sessionId, generation, expectedRevision) => command('export_sustained', { requestId, sessionId, generation, expectedRevision }),
  recovery: requestId => command('list_sustained_recovery', { requestId }),
  inspect: (requestId, sessionId) => command('inspect_sustained_recovery', { requestId, sessionId }),
  restore: (requestId, sessionId, expectedGeneration, expectedRevision) => command('resume_sustained', { requestId, sessionId, expectedGeneration, expectedRevision }),
};
