import type { FileProof } from './types';

export type ResponseKind = 'native' | 'simulation';
export type ResponseSource = 'native-example' | 'native-file' | 'simulation-example';
export type ResponseField = 'delta' | 'first' | 'second' | 'comparison';
export interface ResponseTimelinePoint { index: number; position: string; l2: number; receiptIndex: number | null }
export interface ResponseEvent { index: number; status: string; frameIndex: number | null; isBoundary: boolean }
export interface ResponseSummary {
  responseId: string; kind: ResponseKind; origin: 'bundled' | 'openedFile'; filename: string;
  sha256: string; sizeBytes: number; frameCount: number; nodeCount: number; fixedDeltaScale: number;
  firstLabel: string; secondLabel: string; returnThreshold: number | null; provenance: string[]; missingness: string[];
  metadata: Record<string, string>; timeline: ResponseTimelinePoint[]; events: ResponseEvent[];
}
export interface ResponseFrame {
  index: number; position: string; first: number[]; second: number[]; delta: number[]; l2: number;
  direction: number[] | null; realizedNoise: number[] | null; metadata: Record<string, string>;
}
export interface ResponseEventDetail {
  index: number; status: string; hasState: boolean; isBoundary: boolean; metadata: Record<string, string>;
  direction: number[]; realizedNoise: number[] | null; first: number[] | null; second: number[] | null; delta: number[] | null;
}
export interface ResponseOpenResult { requestId: string; cancelled: boolean; response: ResponseSummary | null }
export interface ResponseFrameResult { requestId: string; responseId: string; frame: ResponseFrame }
export interface ResponseEventResult { requestId: string; responseId: string; event: ResponseEventDetail }
export interface ResponseExportResult { requestId: string; responseId: string; file: FileProof | null }
export interface ResponseApi {
  open(requestId: string, source: ResponseSource, previousResponseId: string | null): Promise<ResponseOpenResult>;
  frame(requestId: string, responseId: string, index: number): Promise<ResponseFrameResult>;
  event(requestId: string, responseId: string, index: number): Promise<ResponseEventResult>;
  export(requestId: string, responseId: string): Promise<ResponseExportResult>;
  close(responseId: string): Promise<void>;
}
