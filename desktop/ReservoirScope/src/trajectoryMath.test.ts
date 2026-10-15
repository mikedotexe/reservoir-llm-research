import { describe, expect, it } from 'vitest';
import type { ObservatoryTimelinePoint } from './observatoryTypes';
import { buildTrajectory, exactProjectionValue, MAX_TRAJECTORY_ROWS, nearestTrajectoryRow, TRAJECTORY_PLOT, trajectoryGeometryKey, trajectoryRowForKey } from './trajectoryMath';

function point(index: number, pc: number[] | null, overrides: Partial<ObservatoryTimelinePoint> = {}): ObservatoryTimelinePoint {
  return { index, position: index, pc, tUtc: null, sessionId: null, fillPct: null, fillRatePctPerS: null, cascade: null,
    intervalSeconds: null, breakBefore: false, stateRms: .2, nodeValue: -.1, ...overrides };
}
function ready(points: ObservatoryTimelinePoint[]) {
  const value = buildTrajectory(points, points.length);
  if (value.status !== 'ready') throw new Error(value.reason);
  return value;
}

describe('complete retained PCA geometry', () => {
  it('uses one signed full-capture scale and equal pixel units on every pair', () => {
    const points = [point(0, [-4, 0, 0]), point(1, [0, 2, -1]), point(2, [4, -2, 1])];
    const geometry = ready(points), { left, top, size } = TRAJECTORY_PLOT;
    expect(geometry.extent).toBe(4);
    expect(geometry.projections.map(p => p.axes)).toEqual([[0, 1], [0, 2], [1, 2]]);
    expect(geometry.projections[0].points[0]).toEqual({ index: 0, x: left, y: top + size / 2 });
    expect(geometry.projections[0].points[2].x).toBe(left + size);
    const center = ready([point(0, [0, 0, 0]), point(1, [1, 1, 1]), point(2, [4, 0, 0])]);
    for (const p of center.projections) {
      expect(p.points[1].x - p.points[0].x).toBe(size / 8);
      expect(p.points[0].y - p.points[1].y).toBe(size / 8);
    }
    expect(geometry.rows.map(row => row.pc)).toEqual(points.map(row => row.pc));
    expect(points[0].pc).toEqual([-4, 0, 0]);
  });

  it('retains exact values separately from projection coordinates and does not mutate its inputs', () => {
    const values = [-0, 0.12345678901234566, Number.MIN_VALUE];
    const source = [point(0, values)];
    const geometry = ready(source);
    expect(geometry.rows[0].pc).toEqual(values);
    expect(geometry.rows[0].pc).not.toBe(values);
    expect(exactProjectionValue(geometry.rows[0].pc[0])).toBe('-0');
    expect(exactProjectionValue(geometry.rows[0].pc[1])).toBe('0.12345678901234566');
    expect(exactProjectionValue(geometry.rows[0].pc[2])).toBe('5e-324');
  });

  it('handles one/all-zero rows and very large finite values without nonfinite drawing coordinates', () => {
    const zero = ready([point(0, [0, 0, 0])]);
    expect(zero.allZero).toBe(true); expect(zero.extent).toBe(1);
    expect(zero.projections[0].segments[0]).toHaveLength(1);
    for (const geometry of [zero, ready([point(0, [-Number.MAX_VALUE, Number.MAX_VALUE, 0])]), ready([point(0, [Number.MIN_VALUE, 0, 0])])]) {
      for (const p of geometry.projections.flatMap(p => p.points)) expect(Number.isFinite(p.x) && Number.isFinite(p.y)).toBe(true);
    }
  });

  it('does not connect a declared break and never fabricates an intermediate row', () => {
    const geometry = ready([point(0, [0, 0, 0]), point(1, [1, 1, 1]), point(2, [2, 2, 2], { breakBefore: true })]);
    for (const p of geometry.projections) {
      expect(p.segments.map(s => s.map(row => row.index))).toEqual([[0, 1], [2]]);
      expect(p.points).toHaveLength(3);
    }
  });

  it('requires the whole bounded capture instead of silently truncating or plotting a partial page', () => {
    for (const total of [0, -1, NaN, Infinity, 1.5, MAX_TRAJECTORY_ROWS + 1]) expect(buildTrajectory([], total).status).toBe('unavailable');
    expect(buildTrajectory([point(0, [1, 2, 3])], 2)).toMatchObject({ status: 'unavailable', reason: expect.stringContaining('all 2 recorded rows') });
    expect(buildTrajectory([point(0, [1, 2, 3]), point(1, [2, 3, 4])], 1).status).toBe('unavailable');
    expect(ready(Array.from({ length: MAX_TRAJECTORY_ROWS }, (_, i) => point(i, [i, 0, -i]))).rows).toHaveLength(MAX_TRAJECTORY_ROWS);
  });

  it('rejects wrong/reordered/duplicate index chains, nonordinal positions and clocked/session input', () => {
    const cases = [
      [point(1, [1, 2, 3]), point(0, [0, 0, 0])],
      [point(0, [1, 2, 3]), point(0, [0, 0, 0])],
      [point(0, [1, 2, 3], { position: .1 })],
      [point(0, [1, 2, 3], { tUtc: '2026-10-15T00:00:00Z' })],
      [point(0, [1, 2, 3], { sessionId: 'another recording' })],
      Array<ObservatoryTimelinePoint>(1),
    ];
    for (const points of cases) expect(buildTrajectory(points, points.length).status).toBe('unavailable');
  });

  it('rejects missing, wrong-dimension, sparse or nonfinite PCA without converting them to zero', () => {
    for (const pc of [null, [], [1, 2], [1, 2, 3, 4], [NaN, 0, 0], [0, Infinity, 0], Array<number>(3)]) {
      expect(buildTrajectory([point(0, pc)], 1)).toMatchObject({ status: 'unavailable', reason: expect.stringContaining('three finite') });
    }
  });

  it('memo identity ignores node-history changes but includes every geometry validation input', () => {
    const base = [point(0, [0, 1, 2]), point(1, [3, 4, 5])];
    const key = trajectoryGeometryKey(base, 2);
    expect(trajectoryGeometryKey(base.map(p => ({ ...p, pc: [...p.pc!], nodeValue: .9, stateRms: .7 })), 2)).toBe(key);
    for (const change of [{ pc: [0, 1, 3] }, { index: 1 }, { position: .5 }, { breakBefore: true }, { tUtc: 'x' }, { sessionId: 'y' }]) {
      expect(trajectoryGeometryKey([{ ...base[0], ...change }, base[1]], 2)).not.toBe(key);
    }
    expect(trajectoryGeometryKey([point(0, [-0, 1, 2]), base[1]], 2)).not.toBe(key);
    expect(trajectoryGeometryKey([point(0, [NaN, 1, 2]), base[1]], 2)).not.toBe(trajectoryGeometryKey([point(0, [Infinity, 1, 2]), base[1]], 2));
  });
});

describe('actual retained-row selection', () => {
  const points = [{ index: 8, x: 0, y: 0 }, { index: 2, x: 10, y: 0 }, { index: 4, x: 10, y: 0 }];
  it('selects nearest actual point rather than an interpolated position on the line', () => {
    expect(nearestTrajectoryRow(points, 4, 0, 2)).toBe(8);
    expect(nearestTrajectoryRow(points, 9, 0, null)).toBe(2);
    expect(nearestTrajectoryRow(points, 5, 0, null)).toBe(2);
  });
  it('prefers the current equal-distance row, then the smallest index independent of array order', () => {
    for (const ordered of [points, [...points].reverse()]) {
      expect(nearestTrajectoryRow(ordered, 5, 0, 8)).toBe(8);
      expect(nearestTrajectoryRow(ordered, 10, 0, 4)).toBe(4);
      expect(nearestTrajectoryRow(ordered, 10, 0, 8)).toBe(2);
      expect(nearestTrajectoryRow(ordered, 5, 0, 99)).toBe(2);
    }
  });
  it('has no selection for invalid pointer coordinates or absent geometry', () => {
    expect(nearestTrajectoryRow([], 0, 0, null)).toBeNull();
    expect(nearestTrajectoryRow(points, NaN, 0, null)).toBeNull();
    expect(nearestTrajectoryRow(points, 0, Infinity, null)).toBeNull();
  });
  it('supports adjacent keyboard inspection, endpoints and a first selection without wrapping', () => {
    expect(trajectoryRowForKey(3, null, 'ArrowRight')).toBe(0);
    expect(trajectoryRowForKey(3, 0, 'ArrowLeft')).toBe(0);
    expect(trajectoryRowForKey(3, 2, 'ArrowRight')).toBe(2);
    expect(trajectoryRowForKey(3, 1, 'ArrowUp')).toBe(0);
    expect(trajectoryRowForKey(3, 1, 'ArrowDown')).toBe(2);
    expect(trajectoryRowForKey(3, 1, 'Home')).toBe(0);
    expect(trajectoryRowForKey(3, 1, 'End')).toBe(2);
    expect(trajectoryRowForKey(3, 1, ' ')).toBeNull();
    expect(trajectoryRowForKey(0, null, 'Home')).toBeNull();
  });
});
