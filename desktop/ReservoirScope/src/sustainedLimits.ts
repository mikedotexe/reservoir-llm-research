import type { SustainedConfig, SustainedLimits, SustainedSummary } from './myReservoirTypes';

export const SESSION_LIMIT_CAPS: SustainedLimits = {
  maximumSteps: 1_000_000, maximumTurns: 10_000, maximumDurationSeconds: 86_400,
};
export const sessionLimits = (summary: SustainedSummary): SustainedLimits => summary.effectiveLimits ?? {
  maximumSteps: summary.config.maximumSteps,
  maximumTurns: summary.config.maximumTurns,
  maximumDurationSeconds: summary.config.maximumDurationSeconds,
};
export function validSessionLimits(limits: SustainedLimits): boolean {
  return Object.entries(SESSION_LIMIT_CAPS).every(([key, cap]) => {
    const value = limits[key as keyof SustainedLimits];
    return Number.isSafeInteger(value) && value >= 1 && value <= cap;
  });
}
export function extensionError(current: SustainedLimits, proposed: SustainedLimits): string {
  if (!validSessionLimits(proposed)) return 'Choose whole-number limits up to 24 hours, 10,000 attempts and 1,000,000 steps.';
  const keys = Object.keys(SESSION_LIMIT_CAPS) as (keyof SustainedLimits)[];
  if (keys.some(key => proposed[key] < current[key])) return 'Keep each limit at least as high as its current value.';
  if (!keys.some(key => proposed[key] > current[key])) return 'Increase at least one limit.';
  return '';
}
/** Add capacity at the requested numerical pace; generation time can only slow it. */
export function addHour(limits: SustainedLimits, config: SustainedConfig): SustainedLimits {
  const duration = Math.min(3600, SESSION_LIMIT_CAPS.maximumDurationSeconds - limits.maximumDurationSeconds);
  const steps = Math.ceil(duration * 1000 / Math.max(1, config.paceMs));
  return {
    maximumDurationSeconds: Math.min(SESSION_LIMIT_CAPS.maximumDurationSeconds, limits.maximumDurationSeconds + duration),
    maximumSteps: Math.min(SESSION_LIMIT_CAPS.maximumSteps, limits.maximumSteps + steps),
    maximumTurns: Math.min(SESSION_LIMIT_CAPS.maximumTurns, limits.maximumTurns + Math.ceil(steps / Math.max(1, config.turnEvery))),
  };
}
