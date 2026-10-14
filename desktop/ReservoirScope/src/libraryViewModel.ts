import type { LibraryEntry } from './libraryTypes';

export const LIBRARY_ROW_HEIGHT = 142;
export function visibleLibraryRows(count: number, scrollTop: number, height: number) {
  const first = Math.min(count, Math.max(0, Math.floor(Math.max(0, scrollTop) / LIBRARY_ROW_HEIGHT) - 3));
  const last = Math.min(count, Math.ceil((Math.max(0, scrollTop) + height) / LIBRARY_ROW_HEIGHT) + 3);
  return { first: Math.min(count, first), last, top: first * LIBRARY_ROW_HEIGHT };
}
export function libraryDate(value: number | null): string {
  return value === null ? 'Unknown' : new Date(value).toLocaleString();
}
export function entryCanOpen(entry: LibraryEntry): boolean {
  return ['ready', 'unverified', 'metadataIssue'].includes(entry.health);
}
export function libraryHealth(entry: LibraryEntry): string {
  if (entry.health === 'notBundled') return 'Authored example not included in this build';
  if (entry.health === 'ready') return 'Record verification passed; opening verifies again';
  if (entry.health === 'unverified') return 'Metadata indexed; opening verifies the recording';
  if (entry.health === 'metadataIssue') return 'Local metadata needs attention; opening verifies the recording';
  return entry.health[0]?.toUpperCase() + entry.health.slice(1);
}
