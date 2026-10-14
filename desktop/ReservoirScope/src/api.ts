import { invoke, isTauri } from '@tauri-apps/api/core';
import type { BuildInfo, FileProof, GuideCatalog, OpenRecordResult, RecordExportResult, RecordFrameResult, RecordTurnResult, ReferenceScene } from './types';

async function command<T>(name: string, args?: Record<string, unknown>): Promise<T> {
  if (!isTauri()) throw new Error('Open the desktop app to connect to the Rust backend. A browser preview cannot load verified resources or use native file dialogs.');
  return invoke<T>(name, args);
}

export const api = {
  buildInfo: () => command<BuildInfo>('get_build_info'),
  scenes: () => command<{ scenes: ReferenceScene[] }>('get_reference_scenes'),
  openProof: () => command<FileProof | null>('open_file_proof'),
  saveProof: () => command<FileProof | null>('save_file_proof'),
  openRecord: (requestId: string, exampleId?: string) => command<OpenRecordResult>('open_record', { requestId, ...(exampleId ? { exampleId } : {}) }),
  recordFrame: (requestId: string, recordId: string, trackId: string, index: number) => command<RecordFrameResult>('get_record_frame', { requestId, recordId, trackId, index }),
  recordTurn: (requestId: string, recordId: string, trackId: string, index: number) => command<RecordTurnResult>('get_record_turn', { requestId, recordId, trackId, index }),
  exportRecord: (requestId: string, recordId: string) => command<RecordExportResult>('export_record', { requestId, recordId }),
  closeRecord: (recordId: string) => command<void>('close_record', { recordId }),
  guideCatalog: () => command<GuideCatalog>('get_guided_catalog'),
};

export function errorText(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  if (error && typeof error === 'object' && 'message' in error && typeof error.message === 'string') return error.message;
  return 'The desktop operation failed.';
}
