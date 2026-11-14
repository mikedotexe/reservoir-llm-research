import type { SustainedCheckInSchedule, SustainedConfig } from './myReservoirTypes';
import { SESSION_LIMIT_CAPS } from './sustainedLimits';

export const DEFAULT_CHECK_IN_PROMPT = 'tell me, friend, about your idle thoughts or curiosities in a casual, peer conversation without pressure to be correct or helpful';
export const DEFAULT_CHECK_IN_SCHEDULE: SustainedCheckInSchedule = { intervalSeconds: 3600, endAfterSeconds: 21600, prompt: DEFAULT_CHECK_IN_PROMPT, includeTelemetry: true };
export const MAX_CHECK_IN_PROMPT_BYTES = 16_384;

export function validCheckInPrompt(prompt: string): boolean {
  return typeof prompt === 'string' && prompt.trim().length > 0 && new TextEncoder().encode(prompt).length <= MAX_CHECK_IN_PROMPT_BYTES;
}
export function checkInTimes(schedule: SustainedCheckInSchedule): number[] {
  const { intervalSeconds, endAfterSeconds } = schedule;
  if (!Number.isInteger(intervalSeconds) || !Number.isInteger(endAfterSeconds) || intervalSeconds < 1 || intervalSeconds > endAfterSeconds || endAfterSeconds > 86400) return [];
  return Array.from({ length: Math.ceil(endAfterSeconds / intervalSeconds) }, (_, index) => Math.min((index + 1) * intervalSeconds, endAfterSeconds));
}
/** Reserve the fastest possible ordinary cadence plus every scheduled response's application. */
export function checkInCapacity(config: SustainedConfig): { maximumSteps: number; maximumTurns: number } | null {
  const schedule = config.checkInSchedule;
  if (!schedule || !Number.isInteger(config.paceMs) || config.paceMs < 100 || !Number.isInteger(config.turnEvery) || config.turnEvery < 1) return null;
  const count = checkInTimes(schedule).length;
  if (!count) return null;
  const requiredSteps = Math.ceil(schedule.endAfterSeconds * 1000 / config.paceMs) + count + 1;
  return { maximumSteps: Math.max(config.maximumSteps, requiredSteps), maximumTurns: Math.max(config.maximumTurns, Math.ceil(requiredSteps / config.turnEvery) + count) };
}
export function checkInConfigurationError(config: SustainedConfig): string {
  const schedule = config.checkInSchedule;
  if (schedule === undefined) return '';
  if (!schedule || !checkInTimes(schedule).length) return 'Choose a whole-second interval and duration from 1 second to 24 hours; the interval must not exceed the duration.';
  if (!validCheckInPrompt(schedule.prompt) || typeof schedule.includeTelemetry !== 'boolean') return 'Enter a nonempty conversational prompt within the text limit and choose its context mode.';
  if (config.maximumDurationSeconds !== schedule.endAfterSeconds) return 'The session duration must match the final scheduled conversation.';
  const capacity = checkInCapacity(config);
  if (!capacity || !Number.isSafeInteger(capacity.maximumSteps) || !Number.isSafeInteger(capacity.maximumTurns) || capacity.maximumSteps > SESSION_LIMIT_CAPS.maximumSteps || capacity.maximumTurns > SESSION_LIMIT_CAPS.maximumTurns) return 'This schedule needs more than the session’s step or attempt capacity. Increase the interval or pace, or shorten the duration.';
  if (config.maximumSteps < capacity.maximumSteps || config.maximumTurns < capacity.maximumTurns) return 'Increase step and attempt limits to the capacity shown for this schedule.';
  return '';
}
/** Preparing a schedule raises capacity, never lowers a limit or silently clamps a ceiling. */
export function withCheckInCapacity(config: SustainedConfig): SustainedConfig {
  if (!config.checkInSchedule) return config;
  const capacity = checkInCapacity(config);
  return { ...config, maximumDurationSeconds: config.checkInSchedule.endAfterSeconds, ...(capacity ?? {}) };
}

/** A reader-only shuffle. The source records and the session's sampling seed stay untouched. */
export function shuffleCheckInAnswers<T>(answers: readonly T[], random = Math.random): T[] {
  const shuffled = [...answers];
  for (let index = shuffled.length - 1; index > 0; index--) {
    const other = Math.floor(random() * (index + 1));
    [shuffled[index], shuffled[other]] = [shuffled[other], shuffled[index]];
  }
  // Never present chronology as a purportedly shuffled first reading.
  if (shuffled.length > 1 && shuffled.every((answer, index) => answer === answers[index])) shuffled.push(shuffled.shift()!);
  return shuffled;
}
