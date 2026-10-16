/** Display selection only. Rust owns the reference decomposition and metrics. */
export type ReferenceField = 'signedActivation' | 'magnitude' | 'referenceDeviation' | 'reconstruction' | 'residual';

export interface BackendReferenceVectors {
  activations: readonly number[] | null;
  magnitude?: readonly number[] | null;
  deviation?: readonly number[] | null;
  reconstruction?: readonly number[] | null;
  residual?: readonly number[] | null;
}

export interface ReferenceFieldDefinition {
  title: string;
  range: readonly [number, number];
  fixedScale: number;
  palette: 'signed' | 'magnitude';
  requiresReference: boolean;
}

const definitions: Record<ReferenceField, ReferenceFieldDefinition> = {
  signedActivation: { title: 'Signed activation', range: [-1, 1], fixedScale: 1, palette: 'signed', requiresReference: false },
  magnitude: { title: 'Activation magnitude', range: [0, 1], fixedScale: 1, palette: 'magnitude', requiresReference: false },
  referenceDeviation: { title: 'Deviation from capture mean', range: [-2, 2], fixedScale: 2, palette: 'signed', requiresReference: true },
  reconstruction: { title: 'Selected-mode reconstruction', range: [-2, 2], fixedScale: 2, palette: 'signed', requiresReference: true },
  residual: { title: 'Residual after selected modes', range: [-2, 2], fixedScale: 2, palette: 'signed', requiresReference: true },
};

export const REFERENCE_FIELDS = Object.keys(definitions) as ReferenceField[];

export function referenceFieldDefinition(field: ReferenceField): ReferenceFieldDefinition | null {
  return Object.hasOwn(definitions, field) ? definitions[field] : null;
}

export type SelectedReferenceField = { status: 'unavailable'; reason: string } | {
  status: 'ready'; field: ReferenceField; definition: ReferenceFieldDefinition;
  /** Exact backend values, copied without normalization or clipping. */
  values: number[]; outOfRangeCount: number;
};

/** Never substitutes activations for a missing reference field, or reconstructs
 * a missing vector in JavaScript. Fixed ranges are drawing limits, not bounds on
 * the exact evidence returned here. */
export function selectReferenceField(
  field: ReferenceField, vectors: BackendReferenceVectors, expectedCount = 128,
): SelectedReferenceField {
  const definition = referenceFieldDefinition(field);
  if (!definition) return { status: 'unavailable', reason: 'Unknown reference field.' };
  if (!Number.isInteger(expectedCount) || expectedCount < 1 || expectedCount > 128) {
    return { status: 'unavailable', reason: 'Reference field requires a known coordinate count from 1 to 128.' };
  }
  const vector = field === 'signedActivation' ? vectors.activations
    : field === 'magnitude' ? vectors.magnitude
      : field === 'referenceDeviation' ? vectors.deviation
        : field === 'reconstruction' ? vectors.reconstruction : vectors.residual;
  if (!Array.isArray(vector) || vector.length !== expectedCount) {
    return { status: 'unavailable', reason: `${definition.title} is unavailable: expected ${expectedCount} backend coordinates.` };
  }
  // Indexed validation detects sparse arrays. Float32 safety matches the display
  // buffer; this does not round the exact values retained in the inspector.
  for (let index = 0; index < vector.length; index++) {
    if (typeof vector[index] !== 'number' || !Number.isFinite(vector[index]) || !Number.isFinite(Math.fround(vector[index]))) {
      return { status: 'unavailable', reason: `${definition.title} contains an unavailable or non-renderable coordinate.` };
    }
  }
  const [lower, upper] = definition.range;
  return { status: 'ready', field, definition, values: [...vector],
    outOfRangeCount: vector.filter(value => value < lower || value > upper).length };
}
