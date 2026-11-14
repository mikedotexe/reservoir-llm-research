import { effectivePromptVersion, type SustainedActionControls, type SustainedActionDecision, type SustainedActionReceipt, type SustainedAuthoredRequest, type SustainedConfig, type SustainedJournal, type SustainedPromptVersion, type SustainedSummary } from './myReservoirTypes';

export const ACTION_JOURNAL_PROMPT_V1 = 'reservoir-journal-actions-v1';
export const ACTION_JOURNAL_PROMPT = 'reservoir-journal-actions-v2';
export const isActionPrompt = (version: SustainedPromptVersion | undefined): boolean => version === ACTION_JOURNAL_PROMPT_V1 || version === ACTION_JOURNAL_PROMPT;
export const hasAuthoredActions = (config: SustainedConfig): boolean => config.actionMode === 'authored-v1' || config.actionMode === 'authored-v2';

export const validAuthoredActionConfig = (config: SustainedConfig): boolean => config.actionMode === undefined
  ? !isActionPrompt(effectivePromptVersion(config))
  : config.actionMode === 'authored-v1' && effectivePromptVersion(config) === ACTION_JOURNAL_PROMPT_V1
    || config.actionMode === 'authored-v2' && effectivePromptVersion(config) === ACTION_JOURNAL_PROMPT;

/** The invitation remembered by the setup form is not serialized into the run. */
export function withAuthoredActions(config: SustainedConfig, enabled: boolean, priorInvitation: SustainedPromptVersion | undefined): SustainedConfig {
  if (enabled) return { ...config, actionMode: 'authored-v2', promptVersion: ACTION_JOURNAL_PROMPT };
  const { actionMode: _mode, promptVersion: _prompt, ...ordinary } = config;
  const restored = isActionPrompt(priorInvitation) ? 'reservoir-journal-v8' : priorInvitation;
  return restored === undefined ? ordinary : { ...ordinary, promptVersion: restored };
}

const record = (value: unknown): value is Record<string, unknown> => value !== null && typeof value === 'object' && !Array.isArray(value);
const count = (value: unknown, maximum = 1_000_000): value is number => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 && value <= maximum;
const scalar = (value: unknown, minimum: number, maximum: number): value is number => typeof value === 'number' && Number.isFinite(value) && value >= minimum && value <= maximum;
const nullableText = (value: unknown): value is string | null => value === null || typeof value === 'string';
const controls = (value: unknown): value is SustainedActionControls => record(value) && scalar(value.leak, 0, 1) && scalar(value.recurrentGain, 0, 2) && scalar(value.feedbackScale, 0, 2);
function request(value: unknown): value is SustainedAuthoredRequest {
  if (!record(value)) return false;
  if (value.kind === 'none' || value.kind === 'release') return true;
  if (value.kind === 'pulse') return ['uniform', 'alternating', 'axis0', 'axis1'].includes(String(value.direction)) && typeof value.strength === 'number' && [.1, .5, 1].includes(Math.abs(value.strength));
  return value.kind === 'tune' && ['leak', 'recurrentGain', 'feedbackScale'].includes(String(value.parameter))
    && scalar(value.value, value.parameter === 'leak' ? .05 : 0, value.parameter === 'leak' ? 1 : 2);
}
export function validActionDecision(value: unknown): value is SustainedActionDecision {
  return record(value) && typeof value.body === 'string' && nullableText(value.rawTail) && validActionChoice(value);
}
export function validReservoirInput(value: unknown): boolean {
  if (!record(value) || !nullableText(value.rawDirective) || !nullableText(value.rejection)
    || value.rawDirective !== null && new TextEncoder().encode(value.rawDirective).length > 512) return false;
  if (value.disposition === 'send') return value.rejection === null && (value.rawDirective === null || value.rawDirective === 'WITHHOLD_RESERVOIR_INPUT=false');
  if (value.disposition === 'withhold') return value.rejection === null && value.rawDirective === 'WITHHOLD_RESERVOIR_INPUT=true';
  return value.disposition === 'rejected' && typeof value.rejection === 'string' && value.rejection.length > 0 && new TextEncoder().encode(value.rejection).length <= 1024;
}
function validInputForMode(value: unknown, config: SustainedConfig): boolean {
  return config.actionMode === 'authored-v2' ? validReservoirInput(value) : value === undefined;
}
function sameInput(left: SustainedActionReceipt['reservoirInput'], right: SustainedActionReceipt['reservoirInput']): boolean {
  return left?.disposition === right?.disposition && left?.rawDirective === right?.rawDirective && left?.rejection === right?.rejection;
}
function validActionChoice(value: unknown): boolean {
  return record(value) && (value.reservoirInput === undefined || validReservoirInput(value.reservoirInput))
    && nullableText(value.rejection) && (value.request === null ? typeof value.rejection === 'string' : request(value.request) && value.rejection === null);
}
export function validActionReceipt(value: unknown, durableStep: number, config?: SustainedConfig): value is SustainedActionReceipt {
  if (!record(value) || typeof value.journalId !== 'string' || !value.journalId || !count(value.attemptId, 10000) || !count(value.observedStep) || !count(value.appliedStep) || value.appliedStep <= value.observedStep || value.appliedStep > durableStep
    || !['applied', 'unchanged', 'rejected'].includes(String(value.status)) || !nullableText(value.rawTail) || !nullableText(value.rejection)
    || value.reservoirInput !== undefined && !validReservoirInput(value.reservoirInput)
    || config !== undefined && !validInputForMode(value.reservoirInput, config)
    || !controls(value.controlsBefore) || !controls(value.controlsAfter) || !scalar(value.stateDeltaL2, 0, 12) || !scalar(value.stateDeltaMaxAbs, 0, 2) || !count(value.clippedCoordinates, 32)) return false;
  if (value.status === 'rejected') return value.request === null && typeof value.rejection === 'string';
  return request(value.request) && value.rejection === null && (value.status === 'unchanged') === (value.request.kind === 'none');
}
export function validActionSummary(summary: SustainedSummary): boolean {
  const actions = summary.actions;
  if (!actions) return true;
  if (!hasAuthoredActions(summary.config) || !record(actions.state) || !count(actions.durableStep) || actions.durableStep > summary.durableStep) return false;
  const state = actions.state;
  if (!controls(state.controls) || !count(state.decisionCount, 10000) || !count(state.appliedCount, 10000) || !count(state.rejectedCount, 10000) || state.appliedCount + state.rejectedCount > state.decisionCount
    || !Array.isArray(state.recentReceipts) || state.recentReceipts.length > 8 || state.recentReceipts.some(receipt => !validActionReceipt(receipt, actions.durableStep) || !validInputForMode(receipt.reservoirInput, summary.config))
    || state.latestReceipt !== null && (!validActionReceipt(state.latestReceipt, actions.durableStep) || !validInputForMode(state.latestReceipt.reservoirInput, summary.config))) return false;
  const latest = state.recentReceipts.at(-1);
  if ((state.latestReceipt === null) !== !latest || latest && (latest.journalId !== state.latestReceipt?.journalId || latest.appliedStep !== state.latestReceipt.appliedStep || !sameInput(latest.reservoirInput, state.latestReceipt.reservoirInput))) return false;
  const pending = actions.pending;
  return !pending || typeof pending.entryId === 'string' && !!pending.entryId && count(pending.attemptId, 10000) && count(pending.observedStep) && pending.observedStep <= summary.step
    && ['saving', 'prepared'].includes(pending.phase) && typeof pending.durablePrepared === 'boolean' && (!pending.durablePrepared || pending.phase === 'prepared')
    && (pending.intendedStep == null || count(pending.intendedStep) && pending.intendedStep > pending.observedStep) && validActionChoice(pending.decision) && validInputForMode(pending.decision.reservoirInput, summary.config);
}
export function validJournalAction(journal: SustainedJournal, config: SustainedConfig): boolean {
  for (const memory of [journal.memory, journal.latestShown]) {
    if (memory && (memory.suppliedText !== undefined || memory.suppliedTextSha256 !== undefined)
      && (!hasAuthoredActions(config) || typeof memory.suppliedText !== 'string' || typeof memory.suppliedTextSha256 !== 'string' || !/^[a-f0-9]{64}$/.test(memory.suppliedTextSha256))) return false;
  }
  if (!journal.action) return journal.actionReceipt == null && journal.bodySha256 == null && (config.actionMode !== 'authored-v2' || !!journal.checkIn);
  if (!hasAuthoredActions(config) || journal.checkIn || !validActionDecision(journal.action) || !validInputForMode(journal.action.reservoirInput, config) || journal.bodySha256 != null && !/^[a-f0-9]{64}$/.test(journal.bodySha256)) return false;
  const receipt = journal.actionReceipt;
  return !receipt || journal.status === 'applied' && journal.firstAppliedStep !== null && validActionReceipt(receipt, journal.firstAppliedStep)
    && validInputForMode(receipt.reservoirInput, config)
    && sameInput(receipt.reservoirInput, journal.action.reservoirInput)
    && receipt.journalId === journal.entryId && receipt.attemptId === journal.attemptId && receipt.observedStep === journal.observedStep && receipt.appliedStep === journal.firstAppliedStep;
}
