import type { LanguageConfiguration, SessionFrame } from './freshTypes';

export type SustainedPromptVersion = 'reservoir-journal-v1' | 'reservoir-journal-v2' | 'reservoir-journal-v3' | 'reservoir-journal-v4' | 'reservoir-journal-v5';
export const isSustainedPromptVersion = (value: unknown): value is SustainedPromptVersion => value === 'reservoir-journal-v1' || value === 'reservoir-journal-v2' || value === 'reservoir-journal-v3' || value === 'reservoir-journal-v4' || value === 'reservoir-journal-v5';
export const effectivePromptVersion = (config: SustainedConfig): SustainedPromptVersion => config.promptVersion === undefined ? 'reservoir-journal-v1' : config.promptVersion;
export const effectiveOutputTokens = (config: SustainedConfig): number => config.outputTokens === undefined ? 256 : config.outputTokens;
export const effectiveRequestDeadline = (config: SustainedConfig): number => config.requestDeadlineSeconds === undefined ? 60 : config.requestDeadlineSeconds;
export function validWritingLimits(config: SustainedConfig): boolean {
  const output = effectiveOutputTokens(config), deadline = effectiveRequestDeadline(config);
  const context = config.language?.contextTokens;
  return Number.isInteger(output) && output >= 256 && output <= 2048
    && Number.isInteger(deadline) && deadline >= 60 && deadline <= 180
    && (context == null || Number.isInteger(context) && context >= 512 && context <= 32768 && context > output);
}

export interface SustainedConfig {
  /** Omitted historical configuration retains v1; only fresh defaults select v5. */
  promptVersion?: SustainedPromptVersion;
  /** Omitted historical budgets retain 256 tokens / 60 seconds. */
  outputTokens?: number; requestDeadlineSeconds?: number;
  seed: string; turnEvery: number; maximumSteps: number; maximumTurns: number; maximumDurationSeconds: number;
  storageBudgetBytes: number; paceMs: number; leak: number; noiseAmplitude: number; initialRetention: number;
  regulationEnabled: boolean; language: LanguageConfiguration;
}
export const DEFAULT_SUSTAINED_CONFIG: SustainedConfig = {
  promptVersion: 'reservoir-journal-v5', seed: '20260909', turnEvery: 30, maximumSteps: 10800, maximumTurns: 360, maximumDurationSeconds: 21600,
  storageBudgetBytes: 268435456, paceMs: 1000, leak: .65, noiseAmplitude: .02, initialRetention: .955,
  regulationEnabled: true, language: { backend: 'scripted' },
  outputTokens: 1024, requestDeadlineSeconds: 180,
};
export interface SustainedSummary {
  sessionId: string; generation: string; revision: string; config: SustainedConfig; phase: string;
  step: number; durableStep: number; simulatedTime: number; elapsedSeconds: number; usedBytes: number;
  journalCount: number; turnCount: number; canStart: boolean; canPause: boolean; canStop: boolean; canRetrySave: boolean;
  canRetryProvider: boolean; canSkipFeedback: boolean;
  pendingLanguage: { operationId: string; turnId: number; attemptId: number; observedStep: number; endpoint: string; model: string; state: 'prepared' | 'requesting' | 'blocked' } | null;
  pendingSave: { entryId: string; attemptId: number; observedStep: number } | null; diagnostics: string[];
  pendingApplication: { entryId: string; attemptId: number; observedStep: number; intendedStep: number } | null;
}
export interface SustainedUpdate { requestId: string; snapshotSequence: string; summary: SustainedSummary | null; frame: SessionFrame | null; closeRequested: boolean }
export type SustainedAction = 'start' | 'pause' | 'stop' | 'retrySave' | 'retryProvider' | 'skipFeedback';
export interface SustainedBundleReport { format: string; sessionId: string; manifestSha256: string; checkpointSha256: string; segmentCount: number; step: number; journalCount: number; sizeBytes: number; verification: string; diagnostics: string[] }
export interface SustainedExport { requestId: string; sessionId: string; generation: string; revision: string; bundle: SustainedBundleReport | null }
export interface SustainedManifest { format: string; sessionId: string; generation: string; revision: string; config: SustainedConfig; phase: string; step: number; durableStep: number; elapsedMillis: number; journalCount: number; segmentCount: number; lastSegmentSha256: string | null; checkpointSha256: string; previousCheckpointSha256: string | null; diagnostics: string[] }
export interface SustainedRecoveryEntry { sessionId: string; generation: string | null; revision: string | null; phase: string | null; step: number | null; durableStep: number | null; journalCount: number | null; diagnostic: string | null }
export interface SustainedRecoveryPage { requestId: string; entries: SustainedRecoveryEntry[]; complete: boolean }
export type ProviderPromptEvaluation = { status: 'reported'; count: string } | { status: 'unusable'; reason: 'wrongType' | 'negative' | 'nonInteger' | 'outOfRange' | 'duplicateField' };
export interface RetainedProviderResponses { total: number; truncated: boolean; entries: { attemptId: string; observedStep: string; complete: boolean; stopReason: string | null; stopReasonTruncated: boolean; tokenCount: string | null; providerPromptEvaluation?: ProviderPromptEvaluation | null }[] }
export interface SustainedRecoveryDetail { requestId: string; manifest: SustainedManifest; checkpoint: unknown; report: SustainedBundleReport; receivedResponses?: RetainedProviderResponses }
export interface SustainedJournalRow {
  entryId: string; turnId: number; attemptId: number; observedStep: number; firstAppliedStep: number | null;
  status: 'savedPendingApplication' | 'applied' | 'skipped'; textPreview: string; sha256: string;
}
export interface JournalMeasurementReference {
  currentStep: number; previousStep: number | null; comparisonAvailable: boolean;
  rows: { key: string; label: string; unit: 'dimensionless' | 'percent'; current: number; previous: number | null; delta: number | null }[];
}
export interface SustainedJournal extends Omit<SustainedJournalRow, 'textPreview'> {
  providerPromptEvaluation?: ProviderPromptEvaluation | null;
  text: string; prompt: string; promptVersion: SustainedPromptVersion; rawReply: string; observation: unknown; measurementReference?: JournalMeasurementReference | null;
  memory: { entryId: string; text: string; sha256: string } | null;
  encodedFeatures: number[]; semanticVector: number[]; saveReceipt: { entryId: string; sha256: string; relativePath: string };
  providerModel: string | null; stopReason: string | null; tokenCount: number | null; providerComplete: boolean;
  configuredModel: string | null; requestStarted: boolean; application: unknown | null;
  timing?: { attemptId: number; dispatchedAtMs: string | null; receivedAtMs: string | null; transportDurationMs: number | null; publishedAtMs: string | null };
}
export interface SustainedJournalPage { requestId: string; sessionId: string; generation: string; revision: string; total: number; offset: number; hasMore: boolean; entries: SustainedJournalRow[] }
export interface SustainedJournalResult { requestId: string; sessionId: string; generation: string; revision: string; journal: SustainedJournal }
export interface MyReservoirApi {
  get(requestId: string, onUpdate: (update: SustainedUpdate) => void): Promise<SustainedUpdate>;
  create(requestId: string, config: SustainedConfig): Promise<SustainedUpdate>;
  action(action: SustainedAction, requestId: string, sessionId: string, generation: string, expectedEntryId?: string | null, expectedAttemptId?: number | null): Promise<SustainedUpdate>;
  journals(requestId: string, sessionId: string, generation: string, offset: number, limit: number): Promise<SustainedJournalPage>;
  journal(requestId: string, sessionId: string, generation: string, entryId: string): Promise<SustainedJournalResult>;
  listenClose(handler: () => void): Promise<() => void>;
  finishClose(allowDiscard: boolean): Promise<boolean>;
  cancelClose(): Promise<void>;
  export(requestId: string, sessionId: string, generation: string, expectedRevision?: string): Promise<SustainedExport>;
  recovery(requestId: string): Promise<SustainedRecoveryPage>;
  inspect(requestId: string, sessionId: string): Promise<SustainedRecoveryDetail>;
  restore(requestId: string, sessionId: string, expectedGeneration: string, expectedRevision: string): Promise<SustainedUpdate>;
}
