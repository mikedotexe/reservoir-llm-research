export interface BuildInfo {
  appName: string;
  version: string;
  milestone: string;
  platform: string;
  arch: string;
  sourceIdentity: string;
  appDataDir?: string;
  resourceStatus: string;
  resources: { name: string; sha256: string; status: string }[];
}

export interface ReferenceScene {
  id: string;
  title: string;
  nodeCount: number;
  description: string;
  provenance: string;
  values: number[];
  sourcePath?: string;
  sourceSha256?: string;
  step?: number;
}

export interface FileProof { name: string; sizeBytes: number; sha256: string }
export interface CameraPose { yaw: number; pitch: number; distance: number }
export const DEFAULT_CAMERA: CameraPose = { yaw: 0.3, pitch: 0.24, distance: 2.7 };

export interface VerificationReport {
  schema: string; status: 'passed' | 'failed' | 'incomplete'; format: string | null; scope: string;
  checkedSteps: number; checkedTurns: number; sha256: string | null; modelsContacted: boolean; diagnostics: string[];
}
export interface TimelinePoint {
  index: number; step: string; time: number | null; fillPercent: number | null; eigenvalues: number[] | null;
}
export interface TrackSummary {
  id: string; label: string; frameCount: number; turnCount: number; backend: string | null; model: string | null;
  timeline: TimelinePoint[]; timelineStride: number;
}
export interface RecordSummary {
  recordId: string; title: string; family: string; format: string; origin: 'bundled' | 'external' | 'managed' | 'created'; filename: string;
  sha256: string; seed: string | null; outcome: string; tracks: TrackSummary[]; verification: VerificationReport; study?: StudyNotes | null;
}
export interface FrameView {
  index: number; step: string; time: number | null; state: number[]; input: number[]; noise: number[];
  fillPercent: number | null; eigenvalues: number[] | null; retentionUsed: number | null; semanticTurnId: string | null;
  nextRetention?: number | null; lessonEvidence?: LessonEvidence | null; regulationEvidence?: RegulationEvidence | null;
}
export interface TurnView {
  index: number; id: string; observedStep: string | null; applicationStep: string | null; status: string;
  backend: string | null; model: string | null; prompt: string; reply: string | null; encodedFeatures: number[] | null;
  semanticVector: number[] | null; failure: string | null; journalSaved: boolean | null;
  rawReply: string | null; requestedAction: string | null; chosenAction: string | null; contextKind: string | null;
  memoryEntryIds: string[]; journalRelativePath: string | null;
  configuredModel: string | null; providerModel: string | null; requestStarted: boolean | null;
  tapePacketId: string | null; failurePhase: string | null;
}
export interface OpenRecordResult { requestId: string; cancelled: boolean; report: VerificationReport | null; record: RecordSummary | null }
export interface RecordFrameResult { requestId: string; recordId: string; trackId: string; frame: FrameView }
export interface RecordTurnResult { requestId: string; recordId: string; trackId: string; turn: TurnView }
export interface RecordExportResult { requestId: string; recordId: string; file: FileProof | null }

export type RecordOpenRequest = { id: string; record: RecordSummary } | { id: string; exampleId: string };
export interface GuideExample { id: string; title: string; file: string; format: string; provenance: string; group: string; order: number; lessonId: string | null }
export interface GuideLesson {
  stage: number; title: string; question: string; suggestedAction: string; expected: string; modelExpected: string;
  limitation: string; focus: string; checkpoints: number[]; scriptedFile: string; modelFile: string | null;
  scriptedExample: GuideExample; modelExample: GuideExample | null;
}
export interface GuideCatalog { format: string; lessons: GuideLesson[]; comparisons: GuideExample[]; lessonsSha256: string; examplesSha256: string }

export interface LessonEvidence {
  state: 'Not reached yet' | 'Observed' | 'Different outcome' | 'Incomplete evidence' | 'No matched comparison';
  observation: string; evidenceSteps: number[];
}
export interface RegulationEvidence {
  count: number; firstStep: number; lastStep: number; isComplete: boolean;
  baselineMeanAbsoluteError: number; regulatedMeanAbsoluteError: number;
}
export interface StudyNotes {
  question: string; expectedDifference: string; alternativeExplanation: string; stoppingPoint: string;
  evaluationFirstStep: number; evaluationLastStep: number; targetFillPercent: number;
}
