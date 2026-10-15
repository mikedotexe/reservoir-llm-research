import type { ObservatoryTimelinePoint } from './observatoryTypes';

/** The bundled recording contains at most 1,024 rows. Larger captures need a
 * separate presentation budget; never silently truncate one to fit this view. */
export const MAX_TRAJECTORY_ROWS = 1024;
export const TRAJECTORY_PLOT = { left: 44, top: 28, size: 232, viewSize: 320 } as const;
export const TRAJECTORY_AXES = [[0, 1], [0, 2], [1, 2]] as const;

export interface TrajectoryRow { index: number; pc: [number, number, number] }
export interface ProjectedRow { index: number; x: number; y: number }
export interface TrajectoryProjection {
  axes: readonly [number, number];
  points: ProjectedRow[];
  segments: ProjectedRow[][];
  segmentPaths: string[];
}
export type TrajectoryGeometry = { status: 'unavailable'; reason: string } | {
  status: 'ready'; rows: TrajectoryRow[]; extent: number; allZero: boolean;
  projections: TrajectoryProjection[];
};

/** Include every geometry/validation input, excluding selected-node history and
 * other unrelated measurements. Preserve invalid-number distinctions and -0. */
export function trajectoryGeometryKey(points: ObservatoryTimelinePoint[], total: number): string {
  if (!Number.isInteger(total) || total < 1 || total > MAX_TRAJECTORY_ROWS || points.length !== total) {
    return `coverage:${String(total)}:${points.length}`;
  }
  return JSON.stringify(points.map(p => p ? [p.index, p.position, p.pc, p.breakBefore, p.tUtc, p.sessionId] : null), (_key, value: unknown) => {
    if (typeof value === 'number' && (!Number.isFinite(value) || Object.is(value, -0))) return { number: Object.is(value, -0) ? '-0' : String(value) };
    return value;
  });
}

export function buildTrajectory(points: ObservatoryTimelinePoint[], total: number): TrajectoryGeometry {
  if (!Number.isInteger(total) || total < 1 || total > MAX_TRAJECTORY_ROWS) {
    return { status: 'unavailable', reason: `Trajectory unavailable: expected a complete recording of 1–${MAX_TRAJECTORY_ROWS} rows.` };
  }
  if (points.length !== total) {
    return { status: 'unavailable', reason: `Trajectory unavailable until all ${total} recorded rows are available (${points.length} received).` };
  }
  const rows: TrajectoryRow[] = [];
  let magnitude = 0;
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    if (!p || p.index !== i || p.position !== i || p.tUtc !== null || p.sessionId !== null || typeof p.breakBefore !== 'boolean') {
      return { status: 'unavailable', reason: 'Trajectory unavailable: rows must form one complete ordinal recording in exact index order.' };
    }
    if (!Array.isArray(p.pc) || p.pc.length !== 3 || [0, 1, 2].some(axis => typeof p.pc![axis] !== 'number' || !Number.isFinite(p.pc![axis]))) {
      return { status: 'unavailable', reason: 'Trajectory unavailable: every row must retain three finite projection coordinates.' };
    }
    const pc: [number, number, number] = [p.pc[0], p.pc[1], p.pc[2]];
    rows.push({ index: i, pc });
    for (const value of pc) magnitude = Math.max(magnitude, Math.abs(value));
  }
  // One equal signed scale for every axis and projection, independent of cursor.
  // For an entirely zero capture, ±1 is a disclosed display extent only.
  const extent = magnitude || 1;
  const { left, top, size } = TRAJECTORY_PLOT;
  const projections = TRAJECTORY_AXES.map(axes => {
    const projected = rows.map(row => ({ index: row.index,
      x: left + (row.pc[axes[0]] / extent + 1) * size / 2,
      y: top + (1 - row.pc[axes[1]] / extent) * size / 2 }));
    const segments: ProjectedRow[][] = [];
    for (const point of projected) {
      if (!segments.length || points[point.index].breakBefore) segments.push([]);
      segments[segments.length - 1].push(point);
    }
    return { axes, points: projected, segments, segmentPaths: segments.map(segment => segment.map(point => `${point.x},${point.y}`).join(' ')) };
  });
  return { status: 'ready', rows, extent, allZero: magnitude === 0, projections };
}

/** Pick a retained row, never an interpolated point on a connecting line.
 * Exact distance ties prefer the current row, then the smallest row index. */
export function nearestTrajectoryRow(points: ProjectedRow[], x: number, y: number, selectedIndex: number | null): number | null {
  if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
  let best: number | null = null, distance = Infinity;
  for (const point of points) {
    const next = (point.x - x) ** 2 + (point.y - y) ** 2;
    if (!Number.isFinite(next)) continue;
    if (next < distance || (next === distance && (point.index === selectedIndex || (best !== selectedIndex && (best === null || point.index < best))))) {
      distance = next; best = point.index;
    }
  }
  return best;
}

export function trajectoryRowForKey(total: number, selectedIndex: number | null, key: string): number | null {
  if (!Number.isInteger(total) || total < 1 || total > MAX_TRAJECTORY_ROWS) return null;
  if (key === 'Home') return 0;
  if (key === 'End') return total - 1;
  const direction = key === 'ArrowLeft' || key === 'ArrowUp' ? -1 : key === 'ArrowRight' || key === 'ArrowDown' ? 1 : 0;
  if (!direction) return null;
  if (selectedIndex === null || !Number.isInteger(selectedIndex) || selectedIndex < 0 || selectedIndex >= total) return 0;
  return Math.max(0, Math.min(total - 1, selectedIndex + direction));
}

export function exactProjectionValue(value: number): string {
  return Object.is(value, -0) ? '-0' : String(value);
}
