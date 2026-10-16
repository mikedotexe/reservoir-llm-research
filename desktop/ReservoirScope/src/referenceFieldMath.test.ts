import { describe, expect, it } from 'vitest';
import { REFERENCE_FIELDS, referenceFieldDefinition, selectReferenceField, type BackendReferenceVectors, type ReferenceField } from './referenceFieldMath';

const vectors: BackendReferenceVectors = {
  activations: [-.25, .5, -0], magnitude: [.25, .5, 0], deviation: [-.125, .25, .5],
  reconstruction: [.01, -.02, .03], residual: [-.135, .27, .47],
};

describe('backend reference-field display selection', () => {
  it('selects each exact backend vector without recomputing a decomposition', () => {
    const expected = [vectors.activations, vectors.magnitude, vectors.deviation, vectors.reconstruction, vectors.residual];
    REFERENCE_FIELDS.forEach((field, index) => {
      const result = selectReferenceField(field, vectors, 3);
      expect(result.status).toBe('ready');
      if (result.status !== 'ready') throw new Error(result.reason);
      expect(result.values).toEqual(expected[index]);
      expect(result.values).not.toBe(expected[index]);
    });
  });

  it('retains fixed signed, nonnegative magnitude and reference ranges across values', () => {
    expect(referenceFieldDefinition('signedActivation')).toMatchObject({ range: [-1, 1], fixedScale: 1, palette: 'signed', requiresReference: false });
    expect(referenceFieldDefinition('magnitude')).toMatchObject({ range: [0, 1], fixedScale: 1, palette: 'magnitude', requiresReference: false });
    for (const field of ['referenceDeviation', 'reconstruction', 'residual'] as const) {
      expect(referenceFieldDefinition(field)).toMatchObject({ range: [-2, 2], fixedScale: 2, requiresReference: true });
      expect(selectReferenceField(field, { ...vectors, deviation: [0, 0, 0], reconstruction: [0, 0, 0], residual: [0, 0, 0] }, 3)).toMatchObject({ status: 'ready', definition: { range: [-2, 2] } });
    }
  });

  it('reports display overflow without clipping or normalizing exact coordinates', () => {
    const values = [-2.25, 2, 3.125];
    const result = selectReferenceField('residual', { activations: null, residual: values }, 3);
    expect(result).toMatchObject({ status: 'ready', values, outOfRangeCount: 2, definition: { range: [-2, 2] } });
    expect(values).toEqual([-2.25, 2, 3.125]);
  });

  it('preserves negative zero and binary64 precision without changing source arrays', () => {
    const values = Object.freeze([-0, .12345678901234566]);
    const result = selectReferenceField('signedActivation', { activations: values }, 2);
    expect(result.status).toBe('ready');
    if (result.status !== 'ready') throw new Error(result.reason);
    expect(Object.is(result.values[0], -0)).toBe(true);
    expect(result.values[1]).toBe(.12345678901234566);
    result.values[1] = 0;
    expect(values[1]).toBe(.12345678901234566);
  });

  it('does not substitute raw activations or compute missing magnitude/reference vectors', () => {
    for (const field of REFERENCE_FIELDS.filter(field => field !== 'signedActivation')) {
      expect(selectReferenceField(field, { activations: [-1, .5, 0] }, 3).status).toBe('unavailable');
    }
    expect(selectReferenceField('signedActivation', { activations: null }, 3).status).toBe('unavailable');
  });

  it('rejects mismatched, sparse, nonfinite and Float32-overflow vectors before drawing', () => {
    const sparse = [0, , 1] as number[];
    for (const values of [[1, 2], sparse, [0, NaN, 1], [0, Infinity, 1], [0, 1e40, 1]]) {
      expect(selectReferenceField('residual', { activations: null, residual: values }, 3).status).toBe('unavailable');
    }
  });

  it('rejects unknown fields and ambiguous coordinate counts without accepting prototype keys', () => {
    for (const field of ['unknown', '__proto__', 'constructor']) {
      expect(selectReferenceField(field as ReferenceField, vectors, 3).status).toBe('unavailable');
    }
    for (const count of [0, -1, 129, NaN, 1.5]) {
      expect(selectReferenceField('signedActivation', vectors, count).status).toBe('unavailable');
    }
    expect(selectReferenceField('signedActivation', vectors).status).toBe('unavailable');
  });
});
