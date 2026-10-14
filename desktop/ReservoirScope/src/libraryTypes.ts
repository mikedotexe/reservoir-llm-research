import type { OpenRecordResult, VerificationReport } from './types';

export interface LibraryEntry {
  id: string; title: string; filename: string; origin: 'managed' | 'bundled' | 'created';
  family: string; format: string; stage: string | null; backend: string; source: string; model: string;
  seed: string | null; embeddedId: string | null; outcome: string; health: string;
  diagnostic: string | null; sha256: string | null; savedAtMs: number | null;
  lastOpenedAtMs: number | null; catalogOrder: number | null;
}
export interface LibraryQuery {
  text: string; origin: string; family: string; source: string; outcome: string;
  recentOnly: boolean; diagnosticsOnly: boolean; offset: number; limit: number;
}
export interface LibraryCoverage {
  phase: string; complete: boolean; examined: number; indexed: number;
  diagnosticCount: number; message: string; finishedAtMs: number | null;
}
export interface LibraryPage {
  entries: LibraryEntry[]; total: number; offset: number; limit: number; hasMore: boolean;
  coverage: LibraryCoverage; diagnostics: string[]; storagePath: string;
}
export interface LibraryImportResult {
  requestId: string; cancelled: boolean; published: boolean; duplicate: boolean;
  entryId: string | null; report: VerificationReport | null; diagnostics: string[];
}
export interface LibraryApi {
  query(query: LibraryQuery): Promise<LibraryPage>;
  importRecord(requestId: string): Promise<LibraryImportResult>;
  open(requestId: string, entryId: string): Promise<OpenRecordResult>;
  scan(rebuild: boolean): Promise<LibraryCoverage>;
  status(): Promise<LibraryCoverage>;
  cancel(): Promise<LibraryCoverage>;
  release(recordId: string): Promise<void>;
}
export const DEFAULT_LIBRARY_QUERY: LibraryQuery = {
  text: '', origin: 'all', family: 'all', source: 'all', outcome: 'all',
  recentOnly: false, diagnosticsOnly: false, offset: 0, limit: 50,
};
