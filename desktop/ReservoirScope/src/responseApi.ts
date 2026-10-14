import { invoke, isTauri } from '@tauri-apps/api/core';
import type { ResponseApi } from './responseTypes';

async function command<T>(name: string, args: Record<string, unknown>): Promise<T> {
  if (!isTauri()) throw new Error('Open the desktop app to inspect retained response evidence and use native file dialogs.');
  return invoke<T>(name, args);
}
export const responseApi: ResponseApi = {
  open: (requestId, source, previousResponseId) => command('open_response', { requestId, source, previousResponseId }),
  frame: (requestId, responseId, index) => command('get_response_frame', { requestId, responseId, index }),
  event: (requestId, responseId, index) => command('get_response_event', { requestId, responseId, index }),
  export: (requestId, responseId) => command('export_response', { requestId, responseId }),
  close: responseId => command('close_response', { responseId }),
};
