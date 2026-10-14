import { Channel, invoke, isTauri } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import type { FreshApi, SessionUpdate } from './freshTypes';

async function command<T>(name: string, args: Record<string, unknown>): Promise<T> {
  if (!isTauri()) throw new Error('Open the desktop app to create and retain an offline experiment.');
  return invoke<T>(name, args);
}
export const freshApi: FreshApi = {
  get: (requestId, onUpdate) => command('get_session', { requestId, onUpdate: new Channel<SessionUpdate>(onUpdate) }),
  create: (requestId, config) => command('create_session', { requestId, config }),
  action: (action, requestId, sessionId, generation, onUpdate, discard = false, saveCandidate) => {
    const args: Record<string, unknown> = { requestId, sessionId, generation };
    const names = { step: 'step_session', pulse: 'step_session', run: 'run_session', pause: 'pause_session', stop: 'stop_session', reset: 'reset_session', saveJournal: 'save_session_journal', saveRecord: 'save_session_record', requestJournal: 'request_session_journal' };
    if (action === 'pulse') args.pulse = true;
    if (action === 'run') args.onUpdate = new Channel<SessionUpdate>(onUpdate);
    if (action === 'reset') args.discard = discard;
    if (action === 'saveJournal') { args.arm = saveCandidate?.arm; args.entryId = saveCandidate?.entryId; }
    return command(names[action], args);
  },
  frame: (requestId, sessionId, generation, index, trackId) => command('get_session_frame', { requestId, sessionId, generation, index, trackId }),
  turn: (requestId, sessionId, generation, index, trackId) => command('get_session_turn', { requestId, sessionId, generation, index, trackId }),
  export: (requestId, sessionId, generation) => command('export_session_record', { requestId, sessionId, generation }),
  regulationDetails: (requestId, sessionId, generation, cursorStep) => command('get_session_regulation_details', { requestId, sessionId, generation, cursorStep }),
  controls: (requestId, sessionId, generation, controls) => command('update_session_controls', { requestId, sessionId, generation, controls }),
  listenClose: async handler => isTauri() ? listen('session-close-requested', handler) : () => {},
  finishClose: allowDiscard => command('finish_session_close', { allowDiscard }),
  cancelClose: () => command('cancel_session_close', {}),
  recovery: requestId => command('list_session_recovery', { requestId }),
  recovered: sessionId => command('get_recovered_session', { sessionId }),
  exportRecovery: (requestId, sessionId, kind, expectedGeneration, expectedRevision) => command('export_recovered_session', { requestId, sessionId, kind, expectedGeneration, expectedRevision }),
};
