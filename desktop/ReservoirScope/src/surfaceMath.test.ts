import { describe, expect, it } from 'vitest';
import { buildSurface, clampPose, fibonacciSites, interpolateField, nearestSite, poseForKey, projectSurface, topographicRadius, validateScene } from './surfaceMath';
import { DEFAULT_CAMERA, type ReferenceScene } from './types';

const scene = (count = 32): ReferenceScene => ({ id: 'test', title: 'Synthetic test', description: 'Unit-test input', provenance: 'Synthetic test', nodeCount: count, values: Array(count).fill(0) });

describe('evidence boundaries', () => {
  it('accepts the two supported dimensions without changing values', () => {
    for (const count of [32, 128]) { const reference = scene(count); const values = [...reference.values]; validateScene(reference); expect(reference.values).toEqual(values); }
  });
  it('rejects mismatched dimensions, non-finite values and out-of-range activations', () => {
    expect(() => validateScene(scene(64))).toThrow();
    expect(() => validateScene({ ...scene(), values: [0] })).toThrow();
    for (const invalid of [NaN, Infinity, 1.01, -1.01]) { const reference = scene(); reference.values[4] = invalid; expect(() => validateScene(reference)).toThrow(); }
  });
});

describe('fixed native-index topography mapping', () => {
  it('preserves the native Fibonacci coordinate order and Float32 sites', () => {
    const sites = fibonacciSites(32);
    expect(sites[0]).toEqual([Math.fround(Math.sqrt(1 - (31 / 32) ** 2)), Math.fround(31 / 32), 0]);
    for (const site of sites) expect(Math.hypot(...site)).toBeCloseTo(1, 6);
    expect(sites[31][1]).toBe(-31 / 32);
  });
  it('preserves a constant field across the entire sphere', () => {
    for (const count of [32, 128]) {
      const sites = fibonacciSites(count);
      for (const direction of [[1, 0, 0], [0, -1, 0], [0.25, 0.5, 0.75]] as [number, number, number][]) {
        expect(interpolateField(direction, sites, Array(count).fill(0.5))).toBeCloseTo(0.5, 6);
      }
    }
  });
  it('has fixed positive, zero and negative radii without per-frame normalization', () => {
    expect(topographicRadius(0)).toBe(0.82);
    expect(topographicRadius(-1)).toBeCloseTo(0.66, 12);
    expect(topographicRadius(1)).toBeCloseTo(0.98, 12);
    expect(topographicRadius(0.25)).toBeCloseTo(0.86, 12);
    expect(() => topographicRadius(0, 0.3)).toThrow();
  });
  it('uses the declared response scale across frames and preserves raw evidence', () => {
    const values = Array(128).fill(0.0005);
    const original = [...values];
    const atlas = buildSurface(values, 32, 64, 0.001);
    expect(atlas.field[100]).toBeCloseTo(0.5, 6);
    expect(projectSurface(atlas, Array(128).fill(0.00025), 0.001).field[100]).toBeCloseTo(0.25, 6);
    expect(values).toEqual(original);
    expect(() => buildSurface(values, 32, 64, 0)).toThrow();
    expect(() => projectSurface(atlas, values, NaN)).toThrow();
  });
  it('interpolates original differences before saturating display relief', () => {
    const atlas = { sites: [[1, 0, 0], [-1, 0, 0]] as [number, number, number][], directions: [[1, 0, 0]] as [number, number, number][], weights: [Float32Array.from([0.5, 0.5])] };
    const projected = projectSurface(atlas, [0.003, -0.001], 0.001);
    expect(projected.field[0]).toBeCloseTo(1, 6);
    expect(projected.positions[0]).toBeCloseTo(0.98, 6);
    // Clipping each input before interpolation would incorrectly produce zero.
    expect(projectSurface(atlas, [0.004, 0], 0.001).field[0]).toBe(2);
  });
  it('constructs a closed outward-oriented mesh for both dimensions', () => {
    for (const count of [32, 128]) {
      const surface = buildSurface(Array(count).fill(0));
      expect(surface.positions.length / 3).toBe(1986);
      expect(surface.indices.length / 3).toBe(3968);
      expect(surface.field.every(value => value === 0)).toBe(true);
      const edges = new Map<string, number>();
      for (let i = 0; i < surface.indices.length; i += 3) {
        const triangle = surface.indices.slice(i, i + 3);
        for (let j = 0; j < 3; j++) {
          const edge = [triangle[j], triangle[(j + 1) % 3]].sort((a, b) => a - b).join(':');
          edges.set(edge, (edges.get(edge) ?? 0) + 1);
        }
        const [a, b, c] = triangle.map(index => surface.positions.slice(index * 3, index * 3 + 3));
        const volume = a[0] * (b[1] * c[2] - b[2] * c[1]) + a[1] * (b[2] * c[0] - b[0] * c[2]) + a[2] * (b[0] * c[1] - b[1] * c[0]);
        expect(volume).toBeGreaterThan(0);
      }
      expect([...edges.values()].every(count => count === 2)).toBe(true);
    }
  });
  it('picks every mapped coordinate without changing the original vector', () => {
    for (const count of [32, 128]) {
      const sites = fibonacciSites(count);
      sites.forEach((site, index) => expect(nearestSite(site, sites)).toBe(index));
    }
  });
  it('reuses a fixed atlas between recorded frames without changing interpolation', () => {
    const surface = buildSurface(Array(32).fill(0));
    const values = Array.from({ length: 32 }, (_, index) => Math.sin(index) * 0.5);
    const projected = projectSurface(surface, values);
    surface.directions.forEach((direction, index) => expect(projected.field[index]).toBe(interpolateField(direction, surface.sites, values)));
    expect(surface.field.every(value => value === 0)).toBe(true);
    expect(() => projectSurface(surface, Array(128).fill(0))).toThrow();
  });
});

describe('linked camera controls', () => {
  it('maps keyboard input predictably and leaves unrelated keys alone', () => {
    expect(poseForKey(DEFAULT_CAMERA, 'ArrowLeft')?.yaw).toBeCloseTo(0.2, 12);
    expect(poseForKey(DEFAULT_CAMERA, '+')?.distance).toBeCloseTo(2.55, 12);
    expect(poseForKey(DEFAULT_CAMERA, 'Tab')).toBeNull();
    expect(DEFAULT_CAMERA).toEqual({ yaw: 0.3, pitch: 0.24, distance: 2.7 });
  });
  it('bounds poles and zoom consistently for keyboard, drag and wheel', () => {
    expect(clampPose({ yaw: 20, pitch: 20, distance: 0 })).toEqual({ yaw: 20, pitch: 1.35, distance: 1.5 });
    expect(clampPose({ yaw: -20, pitch: -20, distance: 20 })).toEqual({ yaw: -20, pitch: -1.35, distance: 5 });
  });
});
