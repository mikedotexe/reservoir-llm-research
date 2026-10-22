import type { LanguageConfiguration, SessionFrame } from './freshTypes';

export type SustainedPromptVersion = 'reservoir-journal-v1' | 'reservoir-journal-v2' | 'reservoir-journal-v3' | 'reservoir-journal-v4' | 'reservoir-journal-v5' | 'reservoir-journal-v6' | 'reservoir-journal-v7' | 'reservoir-journal-v8'
  | 'reservoir-journal-inert-v1' | 'reservoir-journal-inert-no-memory-v1' | 'reservoir-journal-inert-plain-contract-v1' | 'reservoir-journal-inert-inviting-contract-v1'
  | 'reservoir-journal-inert-open-contract-v1' | 'reservoir-journal-inert-inviting-varied-contract-v1'
  | 'reservoir-journal-inert-effect-v1' | 'reservoir-journal-inert-plain-contract-effect-v1'
  | 'reservoir-journal-inert-no-tag-v1' | 'reservoir-journal-inert-plain-contract-no-tag-v1' | 'reservoir-journal-inert-plain-contract-scrambled-tag-v1';
/** S-010 frame arms: lean per-turn input modeled on the beings' own, with or without the earlier entry or a standing contract. Research sessions; not offered as a fresh default. */
export const FRAME_ARM_PROMPT_VERSIONS: SustainedPromptVersion[] = ['reservoir-journal-inert-v1', 'reservoir-journal-inert-no-memory-v1', 'reservoir-journal-inert-plain-contract-v1', 'reservoir-journal-inert-inviting-contract-v1', 'reservoir-journal-inert-open-contract-v1', 'reservoir-journal-inert-inviting-varied-contract-v1', 'reservoir-journal-inert-effect-v1', 'reservoir-journal-inert-plain-contract-effect-v1', 'reservoir-journal-inert-no-tag-v1', 'reservoir-journal-inert-plain-contract-no-tag-v1', 'reservoir-journal-inert-plain-contract-scrambled-tag-v1'];
export const isSustainedPromptVersion = (value: unknown): value is SustainedPromptVersion => value === 'reservoir-journal-v1' || value === 'reservoir-journal-v2' || value === 'reservoir-journal-v3' || value === 'reservoir-journal-v4' || value === 'reservoir-journal-v5' || value === 'reservoir-journal-v6' || value === 'reservoir-journal-v7' || value === 'reservoir-journal-v8' || (FRAME_ARM_PROMPT_VERSIONS as unknown[]).includes(value);
export const effectivePromptVersion = (config: SustainedConfig): SustainedPromptVersion => config.promptVersion === undefined ? 'reservoir-journal-v1' : config.promptVersion;
export const effectiveOutputTokens = (config: SustainedConfig): number => config.outputTokens === undefined ? 256 : config.outputTokens;
export const effectiveRequestDeadline = (config: SustainedConfig): number => config.requestDeadlineSeconds === undefined ? 60 : config.requestDeadlineSeconds;
/** Fresh Ollama sessions sample at 0.7; omitted historical values keep greedy decoding. */
export const DEFAULT_WRITING_TEMPERATURE = 0.7;
export const effectiveTemperature = (config: SustainedConfig): number => config.language?.temperature == null ? 0 : config.language.temperature;
/** Omitted historical values keep mechanism v1: no field noise and feedback ×1. */
export const effectiveSensoryNoise = (config: SustainedConfig): number => config.sensoryNoiseAmplitude === undefined ? 0 : config.sensoryNoiseAmplitude;
export const effectiveFeedbackScale = (config: SustainedConfig): number => config.feedbackScale === undefined ? 1 : config.feedbackScale;
/** Difference-signal channel (0.35.0): omitted values are the as-built defaults (gain 0 keeps the earlier mechanism exactly). */
export const effectiveDifferenceGain = (config: SustainedConfig): number => config.differenceGain === undefined ? 0 : config.differenceGain;
export const effectiveDifferenceTau = (config: SustainedConfig): number => config.differenceTau === undefined ? 3 : config.differenceTau;
export const effectiveDifferenceDeadBand = (config: SustainedConfig): number => config.differenceDeadBand === undefined ? 0.02 : config.differenceDeadBand;
export const effectiveDifferenceClip = (config: SustainedConfig): number => config.differenceClip === undefined ? 0.2 : config.differenceClip;
export const effectiveDifferenceWatchdog = (config: SustainedConfig): boolean => config.differenceWatchdog === undefined ? true : config.differenceWatchdog;
export const effectiveDifferenceWatchdogFillStd = (config: SustainedConfig): number => config.differenceWatchdogFillStd === undefined ? 10 : config.differenceWatchdogFillStd;
/** Watchdog warm-up (0.36.0): steps before the fill ring counts; omitted is 0, as built. */
export const effectiveDifferenceWatchdogWarmup = (config: SustainedConfig): number => config.differenceWatchdogWarmup === undefined ? 0 : config.differenceWatchdogWarmup;
export const validDifferenceControls = (config: SustainedConfig): boolean => {
  const gain = effectiveDifferenceGain(config), tau = effectiveDifferenceTau(config), band = effectiveDifferenceDeadBand(config), clip = effectiveDifferenceClip(config), std = effectiveDifferenceWatchdogFillStd(config), warmup = effectiveDifferenceWatchdogWarmup(config);
  return Number.isFinite(gain) && gain >= -1 && gain <= 1 && Number.isFinite(tau) && tau >= 0 && tau <= 1000 && Number.isFinite(band) && band >= 0 && band <= 1 && Number.isFinite(clip) && clip > 0 && clip <= 5 && Number.isFinite(std) && std >= 0 && std <= 100 && Number.isInteger(warmup) && warmup >= 0 && warmup <= 10000000;
};
/** Which earlier entry a turn returns (0.36.0): omitted keeps the latest applied entry, as built. */
export type SustainedMemoryPolicy = 'latest' | 'state-aligned' | 'random' | 'state-residual' | 'random-older';
export const MEMORY_POLICIES: SustainedMemoryPolicy[] = ['latest', 'state-aligned', 'random', 'state-residual', 'random-older'];
export const effectiveMemoryPolicy = (config: SustainedConfig): SustainedMemoryPolicy => config.memoryPolicy === undefined ? 'latest' : config.memoryPolicy;
export const validMemoryPolicy = (config: SustainedConfig): boolean => config.memoryPolicy === undefined || (MEMORY_POLICIES as unknown[]).includes(config.memoryPolicy);
export function validFieldControls(config: SustainedConfig): boolean {
  const noise = effectiveSensoryNoise(config), scale = effectiveFeedbackScale(config);
  const model = config.embeddingModel;
  const seed = config.embeddingProjectionSeed;
  return Number.isFinite(noise) && noise >= 0 && noise <= 1 && Number.isFinite(scale) && scale >= 0 && scale <= 2
    && (model == null || model.trim().length > 0 && model === model.trim() && model.length <= 256)
    && (seed == null || seed === '' || /^(0|[1-9][0-9]*)$/.test(seed));
}
export function validWritingLimits(config: SustainedConfig): boolean {
  const output = effectiveOutputTokens(config), deadline = effectiveRequestDeadline(config);
  const context = config.language?.contextTokens, temperature = config.language?.temperature;
  return Number.isInteger(output) && output >= 256 && output <= 2048
    && Number.isInteger(deadline) && deadline >= 60 && deadline <= 180
    && (context == null || Number.isInteger(context) && context >= 512 && context <= 32768 && context > output)
    && (temperature == null || Number.isFinite(temperature) && temperature >= 0 && temperature <= 2);
}

export interface SustainedConfig {
  /** Omitted historical configuration retains v1; only fresh defaults select v8. */
  promptVersion?: SustainedPromptVersion;
  /** Omitted historical budgets retain 256 tokens / 60 seconds. */
  outputTokens?: number; requestDeadlineSeconds?: number;
  seed: string; turnEvery: number; maximumSteps: number; maximumTurns: number; maximumDurationSeconds: number;
  storageBudgetBytes: number; paceMs: number; leak: number; noiseAmplitude: number; initialRetention: number;
  regulationEnabled: boolean; language: LanguageConfiguration;
  /** Omitted historical configuration keeps mechanism v1; fresh defaults select field noise 0.5 and feedback ×0.4. */
  sensoryNoiseAmplitude?: number; feedbackScale?: number;
  differenceGain?: number; differenceTau?: number; differenceDeadBand?: number; differenceClip?: number; differenceWatchdog?: boolean; differenceWatchdogFillStd?: number;
  /** 0.36.0: watchdog warm-up steps (omitted is 0) and the earlier-entry policy (omitted is latest). */
  differenceWatchdogWarmup?: number; memoryPolicy?: SustainedMemoryPolicy;
  /** Text reduction (S-010 Part B): an embedding model name selects the embedding codec; omitted keeps the surface codec. */
  embeddingModel?: string | null; embeddingProjectionSeed?: string | null;
}
export const DEFAULT_EMBEDDING_MODEL = 'nomic-embed-text';
export const effectiveCodec = (config: SustainedConfig): 'surface' | 'embedding' => config.embeddingModel ? 'embedding' : 'surface';
export const DEFAULT_SUSTAINED_CONFIG: SustainedConfig = {
  promptVersion: 'reservoir-journal-v8', seed: '20260909', turnEvery: 30, maximumSteps: 10800, maximumTurns: 360, maximumDurationSeconds: 21600,
  storageBudgetBytes: 268435456, paceMs: 1000, leak: .65, noiseAmplitude: .02, initialRetention: .955,
  regulationEnabled: true, language: { backend: 'scripted' },
  outputTokens: 1024, requestDeadlineSeconds: 180,
  sensoryNoiseAmplitude: .5, feedbackScale: .4, differenceGain: 0, differenceTau: 3, differenceDeadBand: .02, differenceClip: .2, differenceWatchdog: true, differenceWatchdogFillStd: 10,
  differenceWatchdogWarmup: 0, memoryPolicy: 'latest',
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
  /** Sampling evidence; both absent for historical greedy journals. */
  temperature?: number | null; samplingSeed?: string | null; thinking?: boolean | null;
  /** Present only under the embedding codec. */
  feedbackProvenance?: { kind: string; model: string; digest?: string | null; dimensions: number; embeddingSha256: string; projectionSeed: number } | null;
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
