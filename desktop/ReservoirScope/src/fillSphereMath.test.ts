import { describe, expect, it } from 'vitest';
import { fillGeometryKey, fillRadius, referenceRings, type FillReferences } from './fillSphereMath';
const references: FillReferences = { shelfMinPercent:58,targetPercent:68,shelfMaxPercent:72,strongRailPercent:74,warningRailPercent:78,provenance:'Retained fixture configuration' };
describe('recorded spherical volume contract', () => {
  it('preserves volume at endpoints, native references and a half-radius example', () => {
    expect(fillRadius(0)).toBe(0); expect(fillRadius(100)).toBe(1); expect(fillRadius(12.5)).toBe(0.5);
    for (let p=0;p<=100;p+=0.25) expect(fillRadius(p)! ** 3 * 100).toBeCloseTo(p,12);
    for (const p of [58,68,72,74,78]) expect(fillRadius(p)).toBeCloseTo(Math.pow(p/100,1/3),15);
    expect(fillRadius(68)).not.toBe(0.68);
  });
  it('preserves no data and rejects invalid values instead of clamping', () => {
    for (const value of [null,undefined,NaN,Infinity,-Infinity,-0.1,100.1]) expect(fillRadius(value)).toBeNull();
  });
  it('maps supplied references exactly, without default or reconstructed thresholds', () => {
    expect(referenceRings(null)).toEqual([]);
    expect(referenceRings(references).map(ring=>ring.percent)).toEqual([58,68,72,74,78]);
    const custom={...references,shelfMinPercent:45,targetPercent:57,shelfMaxPercent:62,strongRailPercent:83,warningRailPercent:91};
    expect(referenceRings(custom).map(ring=>ring.radius ** 3 *100)).toEqual(expect.arrayContaining([expect.closeTo(45,12),expect.closeTo(57,12),expect.closeTo(91,12)]));
    expect(referenceRings({...references,targetPercent:80})).toEqual([]);
    expect(referenceRings({...references,warningRailPercent:NaN})).toEqual([]);
  });
  it('invalidates geometry for retained values and thresholds, not descriptive metadata', () => {
    expect(fillGeometryKey(68,references)).toBe(fillGeometryKey(68,{...references,provenance:'New description'}));
    expect(fillGeometryKey(68,references)).not.toBe(fillGeometryKey(68.01,references));
    expect(fillGeometryKey(68,references)).not.toBe(fillGeometryKey(68,{...references,targetPercent:69}));
    expect(fillGeometryKey(68,null)).not.toBe(fillGeometryKey(68,references));
  });
});
