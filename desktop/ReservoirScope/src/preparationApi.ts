import { invoke, isTauri } from '@tauri-apps/api/core';
import type { PreparationApi, PreparationExportResult, PreparationHistoryResult, PreparationReportResult } from './preparationTypes';

async function command<T>(name: string, args: Record<string, unknown>): Promise<T> {
  if (!isTauri()) throw new Error('Open the desktop app to inspect bundled preparation history and export original reports.');
  return invoke<T>(name, args);
}
export const preparationApi: PreparationApi = {
  list: requestId => command<PreparationHistoryResult>('list_preparation_history', { requestId }),
  get: (requestId, reportId) => command<PreparationReportResult>('get_preparation_report', { requestId, reportId }),
  export: (requestId, reportId, expectedSha256) => command<PreparationExportResult>('export_preparation_report', { requestId, reportId, expectedSha256 }),
};
