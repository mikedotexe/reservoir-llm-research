import type { FileProof } from './types';

export type PreparationReportKind = 'original' | 'correction' | 'retry';
export interface PreparationReportSummary {
  id: PreparationReportKind; title: string; kind: PreparationReportKind; status: string;
  filename: string; sha256: string; sizeBytes: number; summary: string;
}
export interface PreparationExample { id: string; title: string; provenance: string; format: string }
export interface PreparationAttempt {
  startedAtUtc: string | null; finishedAtUtc: string | null; exitCode: number | null;
  record: string | null; verified: boolean | null; verification: string | null;
  sha256: string | null; status: string | null; steps: number | null;
  journalCounts: Record<string, number> | null; requestCount: number | null;
}
export interface PreparationReport {
  schema: string; status: string; scope: string | null; inspectionScope: string;
  sections: { title: string; fields: { label: string; value: string }[] }[];
  attempts: PreparationAttempt[];
}
export interface PreparationHistoryResult { requestId: string; reports: PreparationReportSummary[]; examples: PreparationExample[] }
export interface PreparationReportResult { requestId: string; reportId: string; sha256: string; report: PreparationReport; retainedExampleId: string | null; retainedExampleDiagnostic: string | null }
export interface PreparationExportResult { requestId: string; reportId: string; sourceSha256: string; file: FileProof | null }
export interface PreparationApi {
  list(requestId: string): Promise<PreparationHistoryResult>;
  get(requestId: string, reportId: string): Promise<PreparationReportResult>;
  export(requestId: string, reportId: string, expectedSha256: string): Promise<PreparationExportResult>;
}
