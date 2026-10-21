import type { FileProof, FrameView, TurnView, RegulationEvidence, StudyNotes } from './types';

export type ActionRecipe = 'actionA' | 'actionB' | 'actionC' | 'actionD' | 'actionE' | 'actionF' | 'actionG' | 'actionH';
export type FreshRecipe = 'regulation' | 'exploration' | 'stage1' | 'stage2' | 'stage3' | 'stage4' | 'journalD' | 'journalE' | ActionRecipe;
export type ActionMode = 'independentGeneration' | 'fixedReplay';
export type SessionTrackId = 'left' | 'right';
export type ActionComparisonKind = 'components' | 'observation';
export interface ExplorationControls {
  leak: number; recurrenceEnabled: boolean; recurrenceStrength: number; repeatInput: boolean; inputStrength: number;
  noiseAmplitude: number; biasEnabled: boolean; sensoryEnabled: boolean; retention: number;
}
export interface LanguageConfiguration {
  backend: 'scripted' | 'ollama'; endpoint?: string | null; model?: string | null; contextTokens?: number | null; responseFormat?: 'json' | null;
  /** Omitted historical values keep greedy decoding (zero). */
  temperature?: number | null;
  /** Omitted sends the request as built; false asks a thinking model for the reply only. */
  thinking?: boolean | null;
}
export interface PendingLanguage {
  operationId: string; arm: SessionTrackId; turnId: number; observedStep: number; endpoint: string; model: string;
  state: 'prepared' | 'requesting' | 'compatibilityBlocked';
}
export interface SessionConfig {
  recipe: FreshRecipe; seed: string; steps: number; turnEvery: number; leak: number; noiseAmplitude: number; retention: number;
  explorationControls?: ExplorationControls; language?: LanguageConfiguration;
  actionMode?: ActionMode; actionInputStrength?: number; actionBiasEnabled?: boolean;
  actionComparePrevious?: boolean; actionComparisonKind?: ActionComparisonKind; actionForcingProfile?: 'pulsedSensoryV1' | 'continuousSensoryV1';
}
export interface ActionSessionSummary {
  stage: number; mode: ActionMode; hasJournal: boolean; hasFeedback: boolean; hasMemory: boolean; hasChoice: boolean; hasController: boolean;
  latestJournalEntryId: string | null; replyTape: { format: string; origin: string; packetCount: number } | null;
}
export type SessionPhase = 'ready' | 'running' | 'paused' | 'awaitingJournalSave' | 'awaitingLanguage' | 'completed' | 'stopped' | 'failed' | 'storageBlocked';
export interface SessionSummary {
  sessionId: string; generation: string; revision: string; config: SessionConfig; phase: SessionPhase;
  step: number; durableStep: number; stepLimit: number; frameCount: number; turnCount: number; journalCount: number;
  unsavedRecord: boolean; pendingWrites: boolean; canStep: boolean; canRun: boolean; canExport: boolean;
  saveError: string | null; libraryEntryId: string | null; diagnostics: string[];
  explorationControls: ExplorationControls | null;
  canRequestJournal: boolean; action: ActionSessionSummary | null;
  tracks: SessionTrackSummary[]; pendingLanguage?: PendingLanguage | null; regulationSpec?: RegulationSpecification | null;
}
export interface SessionTrackSummary {
  id: SessionTrackId; label: string; stage: number | null; frameCount: number; turnCount: number; journalCount: number;
  status: string; failure: string | null; observationChannel: string | null; action: ActionSessionSummary | null;
}
export interface PendingJournalView { arm: SessionTrackId; id: string; actionId: number; observedStep: number; prompt: string; text: string; sha256: string; relativePath: string }
export interface SessionFrame extends FrameView { explorationControls: ExplorationControls | null; control: { error: number; integral: number; requestedRetention: number; appliedRetention: number } | null }
export interface SessionTurn extends TurnView { requestOrder: number | null; memoryText: string | null; memoryEntrySha256: string | null; journalEntryId: string | null; journalSha256: string | null }
export interface RegulationSpecification extends StudyNotes {
  fixture: string; fieldSeed: string; inputSeed: string; steps: number; dt: number; initialRetention: number;
}
export interface RegulationFieldFrame {
  index: number; step: string; time: number; input: number[]; fieldVector: number[]; eigenvalues: number[];
  fillPercent: number; retentionUsed: number; nextRetention: number | null;
  control: SessionFrame['control']; regulationEvidence: RegulationEvidence | null;
}
export interface RegulationDetails {
  requestId: string; sessionId: string; generation: string; revision: string; cursorStep: number;
  projectionWeights: number[];
  timeline: { step: string; baselineFill: number; regulatedFill: number; baselineRetention: number; regulatedRetention: number }[];
}
export interface RegulationFrames { left: RegulationFieldFrame; right: RegulationFieldFrame }
export interface SessionFrames { left: SessionFrame | null; right: SessionFrame }
export interface SessionUpdate { requestId: string; summary: SessionSummary | null; frame: SessionFrame | null; frames: SessionFrames | null; regulationFrames?: RegulationFrames | null; pendingJournal: PendingJournalView | null; closeRequested: boolean }
export interface SessionFrameResult { requestId: string; sessionId: string; generation: string; revision: string; trackId: SessionTrackId; frame: SessionFrame | null; regulationFrame?: RegulationFieldFrame | null }
export interface SessionTurnResult { requestId: string; sessionId: string; generation: string; revision: string; trackId: SessionTrackId; turn: SessionTurn }
export interface SessionExportResult { requestId: string; sessionId: string; generation: string; revision: string; file: FileProof | null }
export interface RecoveryEntry { sessionId: string; phase: string; step: number; durableStep: number; revision: string; recordSha256: string | null; pendingJournal: boolean; pendingLanguage?: boolean; discarded: boolean; diagnostic: string | null }
export interface RecoveryPage { requestId: string; entries: RecoveryEntry[]; incompleteWrites: string[]; examined: number; truncated: boolean }
export interface RecoveryCheckpoint {
  schema: string; sessionId: string; generation: string; revision: string; config: unknown; phase: string; step: number; durableStep: number;
  recordSha256: string | null; pendingJournal: unknown; pendingLanguage?: unknown; rejectedLanguage?: unknown; pairedBoundary?: { step: number; arms: { arm: SessionTrackId; stage: number; receipt: unknown | null; journal: unknown | null }[] } | null;
  attempts: { arm: SessionTrackId; number: number; atMs: string; entryId: string; status: string; diagnostic: string | null }[];
  updatedAtMs: string; discarded: boolean;
}
export type FreshAction = 'step' | 'pulse' | 'run' | 'pause' | 'stop' | 'reset' | 'saveJournal' | 'saveRecord' | 'requestJournal';
export interface FreshApi {
  get(requestId: string, onUpdate: (update: SessionUpdate) => void): Promise<SessionUpdate>;
  create(requestId: string, config: SessionConfig): Promise<SessionUpdate>;
  action(action: FreshAction, requestId: string, sessionId: string, generation: string, onUpdate: (update: SessionUpdate) => void, discard?: boolean, saveCandidate?: { arm: SessionTrackId; entryId: string }): Promise<SessionUpdate>;
  frame(requestId: string, sessionId: string, generation: string, index: number, trackId: SessionTrackId): Promise<SessionFrameResult>;
  turn(requestId: string, sessionId: string, generation: string, index: number, trackId: SessionTrackId): Promise<SessionTurnResult>;
  export(requestId: string, sessionId: string, generation: string): Promise<SessionExportResult>;
  regulationDetails(requestId: string, sessionId: string, generation: string, cursorStep: number): Promise<RegulationDetails>;
  controls(requestId: string, sessionId: string, generation: string, controls: ExplorationControls): Promise<SessionUpdate>;
  listenClose(handler: () => void): Promise<() => void>;
  finishClose(allowDiscard: boolean): Promise<boolean>;
  cancelClose(): Promise<void>;
  recovery(requestId: string): Promise<RecoveryPage>;
  recovered(sessionId: string): Promise<RecoveryCheckpoint>;
  exportRecovery(requestId: string, sessionId: string, kind: 'record' | 'checkpoint', expectedGeneration: string, expectedRevision: string): Promise<SessionExportResult>;
}
export const DEFAULT_EXPLORATION: ExplorationControls = { leak: 0.65, recurrenceEnabled: false, recurrenceStrength: 1, repeatInput: false, inputStrength: 1, noiseAmplitude: 0, biasEnabled: false, sensoryEnabled: false, retention: 0.955 };
export const DEFAULT_FRESH_CONFIG: SessionConfig = { recipe: 'exploration', seed: '20260909', steps: 120, turnEvery: 30, leak: 0.65, noiseAmplitude: 0, retention: 0.955, explorationControls: { ...DEFAULT_EXPLORATION } };
export const FRESH_RECIPES: { id: FreshRecipe; title: string; description: string; group: 'Explore' | 'Original stages' | 'Actions A–H' | 'Field-only study' }[] = [
  { id: 'regulation', group: 'Field-only study', title: 'Controller study · two sensory fields', description: 'A fixed 600-step baseline / regulated sensory-field comparison. No reservoir, language or journal.' },
  { id: 'exploration', group: 'Explore', title: 'Explore', description: 'Start quiet, send a pulse, or change recurrent and synthetic-input controls at the next boundary.' },
  { id: 'stage1', group: 'Original stages', title: '1 · Reservoir', description: 'A finite 32-node reservoir with synthetic input.' },
  { id: 'stage2', group: 'Original stages', title: '2 · Spectral bridge', description: 'A separate sensory field and prepared text context. No journal save receipt.' },
  { id: 'stage3', group: 'Original stages', title: '3 · Language loop', description: 'Explicit scripted or local-model replies encoded into the next-step semantic lane. Stage turns are not journal receipts.' },
  { id: 'stage4', group: 'Original stages', title: '4 · Regulation', description: 'Language turns with reduced fill and control measurements; local requests require explicit configuration.' },
  { id: 'actionA', group: 'Actions A–H', title: 'A · Minimal reservoir', description: 'Leaky state driven by synthetic external input. No recurrence, sensory field or journal.' },
  { id: 'actionB', group: 'Actions A–H', title: 'B · Recurrence', description: 'Adds recurrent connections. No sensory field or journal.' },
  { id: 'actionC', group: 'Actions A–H', title: 'C · Sensory observer', description: 'Adds a separate sensory covariance and reduced fill. No writing or journal exists.' },
  { id: 'actionD', group: 'Actions A–H', title: 'D · Journal output', description: 'Adds journal output and a real local save. Saved text does not return to state.' },
  { id: 'actionE', group: 'Actions A–H', title: 'E · Reservoir return', description: 'Only a durably saved journal prepares encoded feedback for the following numerical step.' },
  { id: 'actionF', group: 'Actions A–H', title: 'F · Journal memory', description: 'Rereads the latest saved local journal and includes its exact text in the next prompt context.' },
  { id: 'actionG', group: 'Actions A–H', title: 'G · Action choice', description: 'Adds WRITE_JOURNAL / WAIT choices from the selected source. WAIT keeps the earlier returned input and creates no journal.' },
  { id: 'actionH', group: 'Actions A–H', title: 'H · Regulation', description: 'Adds measured-fill control of the next sensory retention. Reservoir coordinates are not directly regulated.' },
];

export const actionStage = (recipe: FreshRecipe): number | null => recipe === 'journalD' ? 4 : recipe === 'journalE' ? 5 : /^action[A-H]$/.test(recipe) ? recipe.charCodeAt(6) - 64 : null;
export const freshTitle = (recipe: FreshRecipe): string => recipe === 'journalD' ? 'D · Journal output (0.7 recipe)' : recipe === 'journalE' ? 'E · Reservoir return (0.7 recipe)' : FRESH_RECIPES.find(item => item.id === recipe)?.title ?? recipe;
export const maximumSteps = (recipe: FreshRecipe): number => recipe === 'regulation' ? 600 : recipe === 'exploration' ? 1800 : actionStage(recipe) !== null ? 600 : 3000;
/** A form edit only prepares the next explicit Create. It never mutates an accepted session. */
export function selectFreshRecipe(config: SessionConfig, recipe: FreshRecipe): SessionConfig {
  // This is the backend's fixed creation contract; accepted specification comes from Rust.
  if (recipe === 'regulation') return { recipe, seed: '98', steps: 600, turnEvery: 30, leak: .65, noiseAmplitude: 0, retention: .955, actionMode: 'independentGeneration', actionInputStrength: 1, actionBiasEnabled: false, actionComparePrevious: false, actionComparisonKind: 'components', actionForcingProfile: 'pulsedSensoryV1' };
  return normalizeLanguage({ ...config, recipe, steps: Math.min(config.steps, maximumSteps(recipe)), turnEvery: Math.min(config.turnEvery, maximumSteps(recipe)), actionComparisonKind: 'components', actionForcingProfile: 'pulsedSensoryV1', actionComparePrevious: (actionStage(recipe) ?? 0) > 1 && !!config.actionComparePrevious });
}
export function selectActionComparison(config: SessionConfig, kind: 'standalone' | 'components' | 'observation'): SessionConfig {
  if (kind === 'observation') return normalizeLanguage({ ...selectFreshRecipe(config, 'actionD'), actionComparisonKind: 'observation', actionComparePrevious: true, actionMode: 'independentGeneration' });
  return { ...config, actionComparisonKind: 'components', actionForcingProfile: 'pulsedSensoryV1', actionComparePrevious: kind === 'components' && (actionStage(config.recipe) ?? 0) > 1 };
}

export function supportsLocalModel(config: SessionConfig): boolean {
  return config.recipe === 'stage3' || config.recipe === 'stage4' || (actionStage(config.recipe) ?? 0) >= 4 && config.actionMode !== 'fixedReplay';
}
export function normalizeLanguage(config: SessionConfig): SessionConfig {
  if (!supportsLocalModel(config) || config.language?.backend !== 'ollama') return { ...config, language: { backend: 'scripted' } };
  return { ...config, language: { ...config.language, responseFormat: actionStage(config.recipe) !== null ? 'json' : null } };
}
export function selectActionMode(config: SessionConfig, mode: ActionMode): SessionConfig {
  return normalizeLanguage({ ...config, actionMode: mode });
}
export function selectLanguageBackend(config: SessionConfig, backend: LanguageConfiguration['backend']): SessionConfig {
  return normalizeLanguage({ ...config, language: backend === 'scripted' ? { backend } : { backend, endpoint: '', model: '', contextTokens: 4096 } });
}
