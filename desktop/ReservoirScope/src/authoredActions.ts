import {validExperimentRequest,validExperimentProbeRequest,validExperimentReceipt} from './experiments';
import { sonarQuestion } from './compactSonar';
import { validSonarConfig, validSonarReceipt, sonarDirection, sonarSign } from './sonar';
import { validPeerConfig, validPeerRead } from './peerReading';
import { sameControlDiagnostics, validControlDiagnostics } from './controlFeedback';
import { effectivePromptVersion, type SustainedActionControls, type SustainedActionDecision, type SustainedActionReceipt, type SustainedAuthoredRequest, type SustainedConfig, type SustainedJournal, type SustainedPromptVersion, type SustainedSummary } from './myReservoirTypes';
import { sameInquiryDecision, validContinuityState, validInquiryDecision, validInquiryReceipt, validProbeReceipt, validProbeVector } from './localInquiries';

export const ACTION_JOURNAL_PROMPT_V1 = 'reservoir-journal-actions-v1';
/** Frozen actions/input-choice baseline retained for comparisons and saved sessions. */
export const ACTION_JOURNAL_PROMPT = 'reservoir-journal-actions-v2';
export const CONTINUITY_JOURNAL_PROMPT = 'reservoir-journal-actions-v3';
export const CONTINUITY_CONTEXT_TOKENS = 16_384;
export const isActionPrompt = (version: SustainedPromptVersion | undefined): boolean => version === ACTION_JOURNAL_PROMPT_V1 || version === ACTION_JOURNAL_PROMPT || version === CONTINUITY_JOURNAL_PROMPT;
export const hasAuthoredActions = (config: SustainedConfig): boolean => config.actionMode === 'authored-v1' || config.actionMode === 'authored-v2' || config.actionMode === 'authored-v3';
export const hasReservoirInputChoice = (config: SustainedConfig): boolean => config.actionMode === 'authored-v2' || config.actionMode === 'authored-v3';
export const hasLocalInquiry = (config: SustainedConfig): boolean => config.actionMode === 'authored-v3';

export const validAuthoredActionConfig = (config: SustainedConfig): boolean => validSonarConfig(config) && (config.peerReading === undefined || hasLocalInquiry(config) && config.controlFeedback === 'diagnostic-v1' && validPeerConfig(config.peerReading)) && (config.controlFeedback === undefined || config.controlFeedback === 'diagnostic-v1' && hasLocalInquiry(config)) && (config.actionMode === undefined
  ? !isActionPrompt(effectivePromptVersion(config))
  : config.actionMode === 'authored-v1' && effectivePromptVersion(config) === ACTION_JOURNAL_PROMPT_V1
    || config.actionMode === 'authored-v2' && effectivePromptVersion(config) === ACTION_JOURNAL_PROMPT
    || config.actionMode === 'authored-v3' && effectivePromptVersion(config) === CONTINUITY_JOURNAL_PROMPT);

export function withAuthoredActionMode(config: SustainedConfig, mode: NonNullable<SustainedConfig['actionMode']>): SustainedConfig {
  // Apply a new-session preset only on explicit selection, never during restore or validation.
  const language = mode === 'authored-v3' && config.language.backend === 'ollama'
    ? { ...config.language, contextTokens: Math.max(CONTINUITY_CONTEXT_TOKENS, Number.isFinite(config.language.contextTokens) ? config.language.contextTokens! : 0) }
    : config.language;
  const { controlFeedback: _feedback, peerReading, sonar, ...base } = config;
  return { ...base, language, ...(mode === 'authored-v3' ? { controlFeedback: 'diagnostic-v1' as const, ...(sonar ? { sonar } : {}), ...(peerReading ? { peerReading } : {}) } : {}), actionMode: mode, promptVersion: mode === 'authored-v3' ? CONTINUITY_JOURNAL_PROMPT : mode === 'authored-v2' ? ACTION_JOURNAL_PROMPT : ACTION_JOURNAL_PROMPT_V1 };
}

/** The invitation remembered by the setup form is not serialized into the run. */
export function withAuthoredActions(config: SustainedConfig, enabled: boolean, priorInvitation: SustainedPromptVersion | undefined): SustainedConfig {
  if (enabled) return withAuthoredActionMode(config, 'authored-v3');
  const { actionMode: _mode, promptVersion: _prompt, controlFeedback: _feedback, peerReading: _peers, sonar: _sonar, ...ordinary } = config;
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
  if (value.kind === 'none' || value.kind === 'release' || value.kind === 'readPeers' || value.kind === 'scan') return true;
  if (value.kind === 'experiment') return validExperimentRequest(value.experiment,128);
  if (value.kind === 'probeExperiment') return validExperimentProbeRequest(value.probe);
  if (value.kind === 'scanQuestion') return sonarQuestion(value.question);
  if (value.kind === 'probeScan') return sonarDirection(value.direction) && sonarSign(value.sign);
  if (value.kind === 'probe') return validProbeVector(value.vector);
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
  return hasReservoirInputChoice(config) ? validReservoirInput(value) : value === undefined;
}
function sameInput(left: SustainedActionReceipt['reservoirInput'], right: SustainedActionReceipt['reservoirInput']): boolean {
  return left?.disposition === right?.disposition && left?.rawDirective === right?.rawDirective && left?.rejection === right?.rejection;
}
function validActionChoice(value: unknown): boolean {
  return record(value) && (value.diagnostics === undefined || validControlDiagnostics(value.diagnostics))
    && (value.reservoirInput === undefined || validReservoirInput(value.reservoirInput))
    && (value.inquiry === undefined || validInquiryDecision(value.inquiry))
    && nullableText(value.rejection) && (value.request === null ? typeof value.rejection === 'string' : request(value.request) && value.rejection === null);
}
function validChoiceForMode(value: { request: SustainedAuthoredRequest | null; reservoirInput?: unknown; inquiry?: unknown; diagnostics?: unknown }, config: SustainedConfig): boolean {
  return (config.controlFeedback === 'diagnostic-v1' ? validControlDiagnostics(value.diagnostics) : value.diagnostics === undefined)
    && (value.request?.kind !== 'scanQuestion' && !(value.request?.kind === 'probeScan' && value.request.direction === 'question') || ['compact-scan-v2','experiments-v3','experiments-v4'].includes(config.sonar?.version??''))
    && (!['experiment','probeExperiment'].includes(value.request?.kind??'') || ['experiments-v3','experiments-v4'].includes(config.sonar?.version??''))
    && (value.request?.kind !== 'experiment' || validExperimentRequest(value.request.experiment, config.reservoirNodes ?? 32))
    && (!['scan','probeScan','scanQuestion'].includes(value.request?.kind ?? '') || !!config.sonar)
    && (value.request?.kind !== 'readPeers' || !!config.peerReading)
    && validInputForMode(value.reservoirInput, config) && (hasLocalInquiry(config) || value.inquiry === undefined && value.request?.kind !== 'probe');
}
export function validActionReceipt(value: unknown, durableStep: number, config?: SustainedConfig): value is SustainedActionReceipt {
  if (!record(value) || typeof value.journalId !== 'string' || !value.journalId || !count(value.attemptId, 10000) || !count(value.observedStep) || !count(value.appliedStep) || value.appliedStep <= value.observedStep || value.appliedStep > durableStep
    || !['applied', 'unchanged', 'rejected'].includes(String(value.status)) || !nullableText(value.rawTail) || !nullableText(value.rejection)
    || value.diagnostics !== undefined && !validControlDiagnostics(value.diagnostics)
    || value.reservoirInput !== undefined && !validReservoirInput(value.reservoirInput)
    || config !== undefined && !validInputForMode(value.reservoirInput, config)
    || !controls(value.controlsBefore) || !controls(value.controlsAfter) || !scalar(value.stateDeltaL2, 0, config && (config.reservoirNodes ?? 32) === 32 ? 12 : 24) || !scalar(value.stateDeltaMaxAbs, 0, 2) || !count(value.clippedCoordinates, config?.reservoirNodes ?? 32)
    || value.inquiry !== undefined && (!validInquiryReceipt(value.inquiry, durableStep) || value.inquiry.journalId !== value.journalId || value.inquiry.appliedStep !== value.appliedStep)
    || !validExperimentReceipt(value as unknown as SustainedActionReceipt, config)
    || !validSonarReceipt(value as unknown as SustainedActionReceipt, config)
    || !validProbeReceipt(value as unknown as SustainedActionReceipt)
    || (value.request && record(value.request) && value.request.kind === 'readPeers' ? !validPeerRead(value.peerRead, durableStep, config?.peerReading) || value.peerRead.journalId !== value.journalId || value.peerRead.appliedStep !== value.appliedStep || value.peerRead.snapshot.attemptId !== value.attemptId || value.peerRead.snapshot.observedStep !== value.observedStep : value.peerRead !== undefined)) return false;
  if (config && !validChoiceForMode(value as unknown as SustainedActionReceipt, config)) return false;
  if (value.status === 'rejected') return (value.request === null || record(value.request) && ['probeScan','experiment','probeExperiment'].includes(String(value.request.kind))) && typeof value.rejection === 'string';
  return request(value.request) && value.rejection === null && (value.status === 'unchanged') === (value.request.kind === 'none');
}
export function validActionSummary(summary: SustainedSummary): boolean {
  const actions = summary.actions;
  if (!actions) return true;
  if (!hasAuthoredActions(summary.config) || !record(actions.state) || !count(actions.durableStep) || actions.durableStep > summary.durableStep) return false;
  if (actions.peerRead !== undefined && (!summary.config.peerReading || !validPeerRead(actions.peerRead, actions.durableStep, summary.config.peerReading))) return false;
  const state = actions.state;
  if (!controls(state.controls) || !count(state.decisionCount, 10000) || !count(state.appliedCount, 10000) || !count(state.rejectedCount, 10000) || state.appliedCount + state.rejectedCount > state.decisionCount
    || !Array.isArray(state.recentReceipts) || state.recentReceipts.length > 8 || state.recentReceipts.some(receipt => !validActionReceipt(receipt, actions.durableStep, summary.config))
    || state.latestReceipt !== null && !validActionReceipt(state.latestReceipt, actions.durableStep, summary.config)) return false;
  if (hasLocalInquiry(summary.config)
    ? !validContinuityState(state.continuity, actions.durableStep, (receipt): receipt is SustainedActionReceipt => validActionReceipt(receipt, actions.durableStep, summary.config))
    : state.continuity !== undefined) return false;
  const latest = state.recentReceipts.at(-1);
  if ((state.latestReceipt === null) !== !latest || latest && (latest.journalId !== state.latestReceipt?.journalId || latest.appliedStep !== state.latestReceipt.appliedStep || !sameInput(latest.reservoirInput, state.latestReceipt.reservoirInput))) return false;
  const pending = actions.pending;
  return !pending || typeof pending.entryId === 'string' && !!pending.entryId && count(pending.attemptId, 10000) && count(pending.observedStep) && pending.observedStep <= summary.step
    && ['saving', 'prepared'].includes(pending.phase) && typeof pending.durablePrepared === 'boolean' && (!pending.durablePrepared || pending.phase === 'prepared')
    && (pending.intendedStep == null || count(pending.intendedStep) && pending.intendedStep > pending.observedStep) && validActionChoice(pending.decision) && validChoiceForMode(pending.decision, summary.config);
}
export function validJournalAction(journal: SustainedJournal, config: SustainedConfig): boolean {
  for (const memory of [journal.memory, journal.latestShown]) {
    if (memory && (memory.suppliedText !== undefined || memory.suppliedTextSha256 !== undefined)
      && (!hasAuthoredActions(config) || typeof memory.suppliedText !== 'string' || typeof memory.suppliedTextSha256 !== 'string' || !/^[a-f0-9]{64}$/.test(memory.suppliedTextSha256))) return false;
    if (memory && hasLocalInquiry(config)) {
      if (typeof memory.suppliedText !== 'string' || typeof memory.suppliedTextTruncated !== 'boolean'
        || typeof memory.fullBodySha256 !== 'string' || !/^[a-f0-9]{64}$/.test(memory.fullBodySha256)
        || !count(memory.fullBodyBytes, 1_048_576)) return false;
      const suppliedBytes = new TextEncoder().encode(memory.suppliedText).length;
      if (suppliedBytes > 2048 || suppliedBytes > memory.fullBodyBytes
        || memory.suppliedTextTruncated !== (suppliedBytes < memory.fullBodyBytes)
        || !memory.suppliedTextTruncated && memory.fullBodySha256 !== memory.suppliedTextSha256) return false;
    } else if (memory && (memory.suppliedTextTruncated !== undefined || memory.fullBodyBytes !== undefined || memory.fullBodySha256 !== undefined)) return false;
  }
  if (!journal.action) return journal.actionReceipt == null && journal.bodySha256 == null && (!hasReservoirInputChoice(config) || !!journal.checkIn);
  if (!hasAuthoredActions(config) || journal.checkIn || !validActionDecision(journal.action) || !validChoiceForMode(journal.action, config) || journal.bodySha256 != null && !/^[a-f0-9]{64}$/.test(journal.bodySha256)) return false;
  const receipt = journal.actionReceipt;
  return !receipt || journal.status === 'applied' && journal.firstAppliedStep !== null && validActionReceipt(receipt, journal.firstAppliedStep, config)
    && sameControlDiagnostics(receipt.diagnostics, journal.action.diagnostics)
    && sameInput(receipt.reservoirInput, journal.action.reservoirInput)
    && sameInquiryDecision(receipt.inquiry?.decision, journal.action.inquiry)
    && receipt.journalId === journal.entryId && receipt.attemptId === journal.attemptId && receipt.observedStep === journal.observedStep && receipt.appliedStep === journal.firstAppliedStep;
}
