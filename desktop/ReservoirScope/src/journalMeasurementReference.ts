import type { JournalMeasurementReference } from './myReservoirTypes';

const rows = [
  ['rms', 'Recurrent reservoir RMS', 'dimensionless'],
  ['l2', 'Recurrent reservoir L2 norm', 'dimensionless'],
  ['leadingSensoryEigenvalue', 'Largest sensory covariance eigenvalue', 'dimensionless'],
  ['fillPercent', 'Reduced sensory active-mode fill', 'percent'],
  ['headSharePercent', 'Top-eight sensory head share', 'percent'],
  ['shoulderSharePercent', 'Top-eight sensory shoulder share', 'percent'],
  ['tailSharePercent', 'Top-eight sensory tail share', 'percent'],
  ['entropy', 'Top-eight sensory normalized entropy', 'dimensionless'],
] as const;

const object = (value: unknown): value is Record<string, unknown> => value !== null && typeof value === 'object' && !Array.isArray(value);
const step = (value: unknown): value is number => Number.isSafeInteger(value) && (value as number) > 0 && (value as number) <= 1_000_000;
const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value);

/** Validate the bounded Rust read model, without deriving measurements from prose or recomputing deltas. */
export function readMeasurementReference(value: unknown, observedStep: number): { reference: JournalMeasurementReference | null; reason: string } {
  if (value == null) return { reference: null, reason: 'Structured measurements were not supplied for this entry.' };
  if (!object(value) || !step(value.currentStep) || value.currentStep !== observedStep
    || value.previousStep !== null && (!step(value.previousStep) || value.previousStep >= value.currentStep)
    || typeof value.comparisonAvailable !== 'boolean' || value.comparisonAvailable && value.previousStep === null
    || !Array.isArray(value.rows) || value.rows.length !== rows.length) {
    return { reference: null, reason: 'The measurement reference does not match this entry’s writing step and comparison boundaries.' };
  }
  for (let i = 0; i < rows.length; i++) {
    const row = value.rows[i], [key, label, unit] = rows[i];
    if (!object(row) || row.key !== key || row.label !== label || row.unit !== unit || !finite(row.current)
      || (value.comparisonAvailable ? !finite(row.previous) || !finite(row.delta) : row.previous !== null || row.delta !== null)) {
      return { reference: null, reason: 'The measurement reference has incomplete or unsupported rows. No comparison is displayed.' };
    }
  }
  return { reference: value as unknown as JournalMeasurementReference, reason: '' };
}

export function formatRecordedMeasurement(value: number, delta = false): string {
  const rounded = Number(value.toPrecision(8)).toString();
  return delta && value > 0 ? `+${rounded}` : rounded;
}
