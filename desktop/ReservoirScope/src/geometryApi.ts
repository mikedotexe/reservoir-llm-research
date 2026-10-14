import { invoke, isTauri } from '@tauri-apps/api/core';
import type { GeometryApi, GeometryExportResult, GeometryOpenResult } from './geometryTypes';

async function command<T>(name: string, args: Record<string, unknown>): Promise<T> {
  if (!isTauri()) throw new Error('Open the desktop app to read a verified geometry packet or use native file dialogs.');
  return invoke<T>(name, args);
}
export const geometryApi: GeometryApi = {
  open: (requestId, syntheticExample) => command<GeometryOpenResult>('open_geometry', { requestId, syntheticExample }),
  export: (requestId, packetId) => command<GeometryExportResult>('export_geometry', { requestId, packetId }),
};
