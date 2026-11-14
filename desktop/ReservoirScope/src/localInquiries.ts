import type { SustainedActionReceipt, SustainedContinuityState, SustainedInquiryDecision, SustainedInquiryJournal, SustainedInquiryReceipt } from './myReservoirTypes';

const record = (value: unknown): value is Record<string, unknown> => value !== null && typeof value === 'object' && !Array.isArray(value);
const count = (value: unknown, maximum = 1_000_000): value is number => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 && value <= maximum;
const scalar = (value: unknown, minimum: number, maximum: number): value is number => typeof value === 'number' && Number.isFinite(value) && value >= minimum && value <= maximum;
const bytes = (value: string) => new TextEncoder().encode(value).length;
const text = (value: unknown, maximum = 4096): value is string => typeof value === 'string' && value.length > 0 && bytes(value) <= maximum;
const optionalText = (value: unknown, maximum = 4096): boolean => value === null || text(value, maximum);
const source = (value: unknown): boolean => value === 'journal' || value === 'dynamics' || value === 'both';
const question = (value: unknown): value is string => text(value, 512) && value.trim().length > 0 && !/[\u0000-\u001f\u007f-\u009f]/u.test(value);
const controls = (value: unknown): boolean => record(value) && scalar(value.leak, 0, 1) && scalar(value.recurrentGain, 0, 2) && scalar(value.feedbackScale, 0, 2);
const vector = (value: unknown, length: number, limit: number): value is number[] => Array.isArray(value) && value.length === length && value.every(x => scalar(x, -limit, limit));

export const validProbeVector = (value: unknown): value is number[] => vector(value, 48, 1) && value.reduce((sum, x) => sum + x * x, 0) <= 4;

export function validInquiryDecision(value: unknown): value is SustainedInquiryDecision {
  if (!record(value) || !optionalText(value.rawDirective) || !optionalText(value.rejection, 1024)) return false;
  if (value.request === null) return text(value.rejection, 1024);
  if (!record(value.request) || value.rejection !== null || !text(value.rawDirective)) return false;
  if (value.request.kind === 'continue' || value.request.kind === 'close') return true;
  return value.request.kind === 'open' && source(value.request.source) && question(value.request.question);
}

export function validInquiryReceipt(value: unknown, durableStep: number): value is SustainedInquiryReceipt {
  if (!record(value) || !text(value.journalId) || !count(value.appliedStep, durableStep) || value.appliedStep === 0
    || !['opened', 'replaced', 'continued', 'closed', 'rejected'].includes(String(value.status))
    || !optionalText(value.inquiryId) || !optionalText(value.previousInquiryId) || !optionalText(value.rejection, 1024)
    || !validInquiryDecision(value.decision)) return false;
  if (value.status === 'rejected') return text(value.rejection, 1024) && value.inquiryId === value.previousInquiryId
    && (value.decision.request === null ? value.rejection === value.decision.rejection
      : (value.decision.request.kind === 'continue' || value.decision.request.kind === 'close') && value.inquiryId === null);
  if (value.rejection !== null || value.decision.rejection !== null || value.decision.request === null) return false;
  if (value.status === 'opened' || value.status === 'replaced') return value.decision.request.kind === 'open' && text(value.inquiryId)
    && (value.status === 'replaced') === (value.previousInquiryId !== null);
  if (value.status === 'continued') return value.decision.request.kind === 'continue' && text(value.inquiryId) && value.inquiryId === value.previousInquiryId;
  return value.decision.request.kind === 'close' && value.inquiryId === null && text(value.previousInquiryId);
}

function validInquiryJournal(value: unknown, durableStep: number): value is SustainedInquiryJournal {
  return record(value) && text(value.journalId) && count(value.observedStep, durableStep) && count(value.appliedStep, durableStep)
    && value.appliedStep > value.observedStep && typeof value.bodySha256 === 'string' && /^[a-f0-9]{64}$/.test(value.bodySha256)
    && count(value.bodyBytes, 1_048_576) && typeof value.excerpt === 'string' && bytes(value.excerpt) <= 512 && bytes(value.excerpt) <= value.bodyBytes
    && typeof value.excerptTruncated === 'boolean' && value.excerptTruncated === (bytes(value.excerpt) < value.bodyBytes) && typeof value.checkIn === 'boolean';
}

function journals(value: unknown, limit: number, durableStep: number): value is SustainedInquiryJournal[] {
  return Array.isArray(value) && value.length <= limit && value.every(v => validInquiryJournal(v, durableStep))
    && value.every((v, i) => i === 0 || v.appliedStep > value[i - 1].appliedStep)
    && new Set(value.map(v => v.journalId)).size === value.length;
}

export function validContinuityState(value: unknown, durableStep: number, validReceipt: (receipt: unknown) => receipt is SustainedActionReceipt): value is SustainedContinuityState {
  if (!record(value)) return false;
  const receipts = value.meaningfulReceipts, transitions = value.inputTransitions;
  if (!Array.isArray(receipts) || receipts.length > 8
    || receipts.some(r => !validReceipt(r) || r.status !== 'applied')
    || !receipts.every((r, i) => i === 0 || r.appliedStep > receipts[i - 1].appliedStep)
    || !Array.isArray(transitions) || transitions.length > 8
    || transitions.some(r => !record(r) || !text(r.journalId) || !count(r.appliedStep, durableStep) || r.appliedStep === 0 || !['send', 'withhold', 'rejected'].includes(String(r.disposition)))
    || !transitions.every((r, i) => i === 0 || r.appliedStep > transitions[i - 1].appliedStep)
    || !journals(value.journalWindow, 8, durableStep)
    || value.latestInquiryReceipt !== null && !validInquiryReceipt(value.latestInquiryReceipt, durableStep)) return false;
  const inquiry = value.activeInquiry;
  const latest = value.latestInquiryReceipt as SustainedInquiryReceipt | null;
  if (inquiry === null) return latest === null || latest.inquiryId === null;
  if (!record(inquiry) || latest === null || latest.inquiryId !== inquiry.id) return false;
  if (latest.decision.request?.kind === 'open' && (latest.decision.request.question !== inquiry.question || latest.decision.request.source !== inquiry.source
    || latest.journalId !== inquiry.openedJournalId || latest.appliedStep !== inquiry.openedAppliedStep)) return false;
  if (latest.status === 'continued' && latest.appliedStep !== inquiry.lastContinuedStep) return false;
  return record(inquiry) && text(inquiry.id) && question(inquiry.question) && source(inquiry.source)
    && text(inquiry.openedJournalId) && count(inquiry.openedObservedStep, durableStep) && count(inquiry.openedAppliedStep, durableStep)
    && inquiry.openedAppliedStep > inquiry.openedObservedStep && count(inquiry.lastContinuedStep, durableStep) && inquiry.lastContinuedStep >= inquiry.openedAppliedStep
    && count(inquiry.continuationCount, 10000) && controls(inquiry.openingControls) && record(inquiry.baseline)
    && inquiry.baseline.step === inquiry.openedObservedStep && scalar(inquiry.baseline.rms, 0, 1) && scalar(inquiry.baseline.sensoryFill, 0, 100)
    && vector(inquiry.baseline.state, 32, 1) && journals(inquiry.history, 4, inquiry.lastContinuedStep - 1);
}

export function sameInquiryDecision(left: SustainedInquiryDecision | undefined, right: SustainedInquiryDecision | undefined): boolean {
  return left?.rawDirective === right?.rawDirective && left?.rejection === right?.rejection
    && left?.request?.kind === right?.request?.kind
    && (left?.request?.kind !== 'open' || right?.request?.kind === 'open' && left.request.source === right.request.source && left.request.question === right.request.question);
}

export function validProbeReceipt(receipt: SustainedActionReceipt): boolean {
  const probe = receipt.probe, request = receipt.request;
  if (request?.kind !== 'probe') return probe === undefined;
  if (!probe || !validProbeVector(probe.requestedVector) || !validProbeVector(probe.appliedVector)
    || !vector(probe.stateDeltaVector, 32, 2) || !validProbeVector(request.vector)) return false;
  return probe.requestedVector.every((x, i) => x === request.vector[i] && x === probe.appliedVector[i])
    && Math.abs(Math.hypot(...probe.stateDeltaVector) - receipt.stateDeltaL2) <= 1e-8
    && Math.abs(Math.max(...probe.stateDeltaVector.map(Math.abs)) - receipt.stateDeltaMaxAbs) <= 1e-8;
}
