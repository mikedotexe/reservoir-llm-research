import { invoke, isTauri } from '@tauri-apps/api/core';
import type { LibraryApi } from './libraryTypes';

async function command<T>(name: string, args?: Record<string, unknown>): Promise<T> {
  if (!isTauri()) throw new Error('Open the desktop app to use its local Library. A browser preview cannot read or import your recordings.');
  return invoke<T>(name, args);
}
export const libraryApi: LibraryApi = {
  query: query => command('library_query', { query }),
  importRecord: requestId => command('library_import', { requestId }),
  open: (requestId, entryId) => command('library_open', { requestId, entryId }),
  scan: rebuild => command('library_scan', { rebuild }),
  status: () => command('library_scan_status'),
  cancel: () => command('library_cancel_scan'),
  release: recordId => command('close_record', { recordId }),
};
