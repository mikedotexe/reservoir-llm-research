export type ActivationArm = 'no_steering' | 'decaying_trace' | 'recurrent';
export interface ActivationConfig {
  pythonPath: string; workerPath: string; modelPath: string; arm: ActivationArm; seed: number;
  observations: string[]; stepsBetween: number; journalEvery: number; maxJournalTokens: number; gain: number;
}
export interface ActivationJournal {
  id: string; text: string; observedStep: number; firstAppliedStep: number | null; sha256: string; status: string;
}
export interface ActivationEvent { id: string; kind: string; step: number; detail: string }
export interface ActivationAnnotation {
  excerpt: string; interpretation: string; alternative: string; sourceEventIds: string[]; journalId?: string;
}
export interface ActivationSnapshot {
  sessionId: string; revision: number; status: string; config: ActivationConfig; step: number;
  observationIndex: number; journalCount: number; journals: ActivationJournal[]; events: ActivationEvent[];
  diagnostic: string | null; activeOperation: string | null; directory: string;
  modelManifestSha256?: string | null; calibrationSha256?: string | null;
  canStart?: boolean; annotations?: ActivationAnnotation[];
}
export interface ActivationCapability { ready?: boolean; diagnostic?: string; config?: ActivationConfig; [key: string]: unknown }
export interface ActivationExport { path: string | null; verified: boolean }
export interface ActivationApi {
  inspect(config: ActivationConfig): Promise<ActivationCapability>;
  create(config: ActivationConfig): Promise<ActivationSnapshot>;
  start(sessionId: string): Promise<ActivationSnapshot>;
  stop(sessionId: string): Promise<ActivationSnapshot>;
  get(sessionId?: string): Promise<ActivationSnapshot | null>;
  list(): Promise<ActivationSnapshot[]>;
  restore(sessionId: string): Promise<ActivationSnapshot>;
  export(sessionId: string): Promise<ActivationExport>;
  import(): Promise<ActivationSnapshot | null>;
  annotate(sessionId: string, annotation: ActivationAnnotation): Promise<ActivationSnapshot>;
}
export const ACTIVATION_ARM_NAMES: Record<ActivationArm, string> = {
  no_steering: 'No steering', decaying_trace: 'Decaying trace', recurrent: 'Recurrent reservoir',
};
export const DEFAULT_ACTIVATION_CONFIG: ActivationConfig = {
  pythonPath: '', workerPath: '', modelPath: '', arm: 'decaying_trace', seed: pilot.seed,
  observations: [...pilot.observations], stepsBetween: pilot.stepsBetweenObservations,
  journalEvery: pilot.journalEveryObservations, maxJournalTokens: pilot.outputTokens, gain: 0.01,
};
export function activationRunning(session: ActivationSnapshot | null) {
  return !!session && (session.activeOperation !== null || ['running', 'initializing', 'starting'].includes(session.status));
}
export function activationCanStart(session: ActivationSnapshot) {
  return session.canStart ?? session.status === 'ready';
}
import pilot from '../../../shared/reservoir-scope/activation-pilot.json';
