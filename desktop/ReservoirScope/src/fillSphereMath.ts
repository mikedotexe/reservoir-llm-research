/** Native ReservoirScene.swift mapping: a fraction of spherical volume. */
export interface RecordedFillSample {
  fillPercent: number;
  provenance: string;
  /** An explicit retained label only. The renderer never constructs a clock. */
  sourceTimeLabel?: string | null;
}
export interface FillReferences {
  shelfMinPercent: number;
  targetPercent: number;
  shelfMaxPercent: number;
  strongRailPercent: number;
  warningRailPercent: number;
  provenance: string;
}
export interface FillReferenceRing { key: string; title: string; percent: number; radius: number; color: number; dashed: boolean }
export const FILL_REFERENCE_SCOPE = 'Source-defined operating references. Fill alone does not establish historical controller stage, mode, subjective comfort or stability.';

export function fillRadius(fillPercent: number | null | undefined): number | null {
  return typeof fillPercent === 'number' && Number.isFinite(fillPercent) && fillPercent >= 0 && fillPercent <= 100
    ? Math.cbrt(fillPercent / 100) : null;
}
export function referenceRings(references: FillReferences | null | undefined): FillReferenceRing[] {
  if (!references) return [];
  const { shelfMinPercent: min, targetPercent: target, shelfMaxPercent: max, strongRailPercent: strong, warningRailPercent: warning } = references;
  if (![min,target,max,strong,warning].every(value => fillRadius(value) !== null)
    || !(min <= target && target <= max && max <= strong && strong <= warning)) return [];
  return [
    { key: 'shelf-min', title: 'Lower shelf reference', percent: min, color: 0x72e4b5, dashed: false },
    { key: 'target', title: 'Reference target', percent: target, color: 0xf5eedb, dashed: true },
    { key: 'shelf-max', title: 'Upper shelf reference', percent: max, color: 0x72e4b5, dashed: false },
    { key: 'strong', title: 'Strong-drain reference', percent: strong, color: 0xefbd78, dashed: true },
    { key: 'warning', title: 'Warning reference', percent: warning, color: 0xf28482, dashed: true },
  ].map(row => ({ ...row, radius: fillRadius(row.percent)! }));
}
export function fillGeometryKey(fillPercent: number, references: FillReferences | null | undefined): string {
  return [fillPercent, ...referenceRings(references).map(row => row.percent)].join(':');
}
