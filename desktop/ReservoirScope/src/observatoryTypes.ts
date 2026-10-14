/** Frozen evidence only. Track clocks are independent; no cross-track joins. */
export type ObservatoryTrackId = 'history' | 'states';
export type ObservatorySeekMode = 'floor' | 'nearest';
export interface ObservatoryIdentity { name: string; sha256: string }
export interface ObservatoryDiagnostic { trackId: ObservatoryTrackId; category: string; message: string }
export interface ObservatoryBands {
  shelfMinPct: number; shelfEntryPct: number | null; targetPct: number;
  shelfMaxPct: number; elevatedReleasePct: number | null; strongRailPct: number;
  forceRailPct: number; status: string | null; note: string | null;
}
export interface ObservatoryTrack {
  id: ObservatoryTrackId; title: string; axis: 'elapsedSeconds' | 'ordinal';
  frameCount: number; nodeCount: number | null; firstPosition: number; lastPosition: number;
  firstUtc: string | null; lastUtc: string | null; capturedAtUtc: string | null;
  identities: ObservatoryIdentity[]; provenance: string[]; missingness: string[];
  definitions: Record<string, string>; bands: ObservatoryBands | null;
}
export interface ObservatorySummary {
  observatoryId: string; tracks: ObservatoryTrack[]; diagnostics: ObservatoryDiagnostic[];
  maxTimelinePage: number;
}
export interface ObservatoryOpenResult { requestId: string; observatory: ObservatorySummary }
export interface ObservatoryHistoryFrame {
  tUtc: string; tSeconds: number; sessionId: string; fillPct: number;
  fillRatePctPerS: number | null; cascade: number[];
  esnCovLambda1: number | null; geomRadius: number | null; geomRel: number | null;
  esnLeak: number | null; esnLambda: number | null; sourceIds: (string | null)[] | null;
  intervalSeconds: number | null; breakBefore: boolean;
}
export interface ObservatoryStateFrame {
  activations: number[]; pc: number[]; stateRms: number; centeredRms: number;
  projectedRms: number; reconstructionRmse: number;
  sourceIdentity: string;
}
export interface ObservatoryFrame {
  trackId: ObservatoryTrackId; index: number; position: number;
  history: ObservatoryHistoryFrame | null; state: ObservatoryStateFrame | null;
}
export interface ObservatoryFrameResult {
  requestId: string; observatoryId: string; frame: ObservatoryFrame;
}
export interface ObservatoryTimelinePoint {
  index: number; position: number; tUtc: string | null; sessionId: string | null;
  fillPct: number | null; fillRatePctPerS: number | null; cascade: number[] | null;
  intervalSeconds: number | null; breakBefore: boolean;
  stateRms: number | null; pc: number[] | null; nodeValue: number | null;
}
export interface ObservatoryTimelineResult {
  requestId: string; observatoryId: string; trackId: ObservatoryTrackId;
  start: number; total: number; hasMore: boolean; nodeIndex: number | null;
  points: ObservatoryTimelinePoint[];
}
