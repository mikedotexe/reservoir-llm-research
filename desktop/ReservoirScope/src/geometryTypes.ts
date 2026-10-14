import type { FileProof } from './types';

export interface GeometryFrame { tMs: string; wallClockUnixMs: string; activations: number[]; rms: number }
export interface GeometrySnapshot {
  sourceSha256: string; capturedAtUnixMs: string; requestedSeconds: number; source: string; scope: string;
  identity: string; durationMs: number; gaps: [string, string][]; frames: GeometryFrame[];
}
export interface GeometryEntry {
  id: string; requestId: string; requestSha256: string; kind: 'capture' | 'prediction' | 'comparison' | 'revision';
  authoredText: string | null; snapshot: GeometrySnapshot | null; baseline: string | null;
  maximumRmsDistance: number | null; prediction: string | null; observation: string | null;
  recipe: string | null; rmsDistance: number | null; thresholdMet: boolean | null; target: string | null;
}
export interface GeometryPacket {
  packetId: string; filename: string; origin: 'syntheticExample' | 'openedFile'; sha256: string;
  bodySha256: string; sizeBytes: number; owner: string; questionId: string; question: string; limits: string;
  verificationScope: string; records: GeometryEntry[];
}
export interface GeometryOpenResult { requestId: string; cancelled: boolean; packet: GeometryPacket | null }
export interface GeometryExportResult { requestId: string; packetId: string; file: FileProof | null }
export interface GeometryApi {
  open(requestId: string, syntheticExample: boolean): Promise<GeometryOpenResult>;
  export(requestId: string, packetId: string): Promise<GeometryExportResult>;
}
