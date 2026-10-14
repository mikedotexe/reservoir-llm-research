import type { CameraPose, ReferenceScene } from './types';

export type Point3 = [number, number, number];
const float = Math.fround;

export function validateScene(scene: ReferenceScene): void {
  if (![32, 128].includes(scene.nodeCount) || scene.values.length !== scene.nodeCount ||
      scene.values.some(value => !Number.isFinite(value) || Math.abs(value) > 1)) {
    throw new Error('Reference scene must contain 32 or 128 finite signed coordinates on the −1…1 scale.');
  }
}

/** Fixed coordinate-index atlas, matching native StateSurfaceAtlas's sites.
 * These directions convey neither network connectivity nor anatomy. */
export function fibonacciSites(count: number): Point3[] {
  if (!Number.isInteger(count) || count < 1 || count > 128) throw new Error('Invalid coordinate count.');
  return Array.from({ length: count }, (_, index) => {
    const y = 1 - 2 * (index + 0.5) / count;
    const radius = Math.sqrt(1 - y * y);
    const angle = Math.PI * (3 - Math.sqrt(5)) * index;
    return [float(radius * Math.cos(angle)), float(y), float(radius * Math.sin(angle))];
  });
}

function normalize(point: Point3): Point3 {
  const norm = Math.hypot(...point);
  return point.map(value => value / norm) as Point3;
}

export function interpolateField(direction: Point3, sites: Point3[], values: number[]): number {
  const weights = interpolationWeights(direction, sites);
  return float(weights.reduce((sum, weight, index) => sum + weight * values[index], 0));
}

function interpolationWeights(direction: Point3, sites: Point3[]): Float32Array {
  const unit = normalize(direction);
  const weights = sites.map(site => {
    const normalized = normalize(site);
    return Math.exp(24 * (unit.reduce((sum, value, axis) => sum + value * normalized[axis], 0) - 1));
  });
  const total = weights.reduce((sum, value) => sum + value, 0);
  return Float32Array.from(weights, weight => weight / total);
}

export function projectSurface(atlas: { directions: Point3[]; weights: Float32Array[]; sites: Point3[] }, values: number[], fixedScale = 1) {
  if (!Number.isFinite(fixedScale) || fixedScale <= 0 || values.length !== atlas.sites.length || values.some(value => !Number.isFinite(value))) throw new Error('Invalid state values.');
  const field = atlas.weights.map(weights => float(weights.reduce((sum, weight, index) => sum + weight * values[index], 0) / fixedScale));
  const positions = atlas.directions.flatMap((direction, index) => direction.map(value => float(value * topographicRadius(field[index]))));
  return { field, positions };
}

export function topographicRadius(value: number, relief = 0.16): number {
  if (!Number.isFinite(value) || !Number.isFinite(relief) || relief < 0 || relief > 0.2) throw new Error('Invalid topography input.');
  return 0.82 + relief * Math.max(-1, Math.min(1, value));
}

export function buildSurface(values: number[], rows = 32, columns = 64, fixedScale = 1) {
  if (!Number.isFinite(fixedScale) || fixedScale <= 0 || ![32, 128].includes(values.length) || values.some(value => !Number.isFinite(value))) throw new Error('Invalid state values.');
  const sites = fibonacciSites(values.length);
  const directions: Point3[] = [[0, 1, 0]];
  for (let row = 1; row < rows; row++) {
    const latitude = row * Math.PI / rows;
    for (let column = 0; column < columns; column++) {
      const longitude = column * 2 * Math.PI / columns;
      directions.push([Math.sin(latitude) * Math.cos(longitude), Math.cos(latitude), Math.sin(latitude) * Math.sin(longitude)]
        .map(value => float(Math.abs(value) < 1e-14 ? 0 : value)) as Point3);
    }
  }
  const bottom = directions.length;
  directions.push([0, -1, 0]);
  const indices: number[] = [];
  const index = (row: number, column: number) => 1 + (row - 1) * columns + column % columns;
  const triangle = (a: number, b: number, c: number) => {
    const pa = directions[a], pb = directions[b], pc = directions[c];
    const volume = pa[0] * (pb[1] * pc[2] - pb[2] * pc[1]) + pa[1] * (pb[2] * pc[0] - pb[0] * pc[2]) + pa[2] * (pb[0] * pc[1] - pb[1] * pc[0]);
    indices.push(...(volume > 0 ? [a, b, c] : [a, c, b]));
  };
  for (let column = 0; column < columns; column++) {
    triangle(0, index(1, column), index(1, column + 1));
    for (let row = 1; row < rows - 1; row++) {
      triangle(index(row, column), index(row + 1, column), index(row + 1, column + 1));
      triangle(index(row, column), index(row + 1, column + 1), index(row, column + 1));
    }
    triangle(index(rows - 1, column), bottom, index(rows - 1, column + 1));
  }
  const weights = directions.map(direction => interpolationWeights(direction, sites));
  return { sites, directions, weights, ...projectSurface({ sites, directions, weights }, values, fixedScale), indices };
}

export function nearestSite(direction: Point3, sites: Point3[]): number {
  const unit = normalize(direction);
  let best = 0, score = -Infinity;
  sites.forEach((site, index) => {
    const current = unit.reduce((sum, value, axis) => sum + value * site[axis], 0);
    if (current > score) { score = current; best = index; }
  });
  return best;
}

export function clampPose(pose: CameraPose): CameraPose {
  return { yaw: pose.yaw, pitch: Math.max(-1.35, Math.min(1.35, pose.pitch)), distance: Math.max(1.5, Math.min(5, pose.distance)) };
}

export function poseForKey(pose: CameraPose, key: string): CameraPose | null {
  switch (key) {
    case 'ArrowLeft': return clampPose({ ...pose, yaw: pose.yaw - 0.1 });
    case 'ArrowRight': return clampPose({ ...pose, yaw: pose.yaw + 0.1 });
    case 'ArrowUp': return clampPose({ ...pose, pitch: pose.pitch + 0.1 });
    case 'ArrowDown': return clampPose({ ...pose, pitch: pose.pitch - 0.1 });
    case '+': case '=': return clampPose({ ...pose, distance: pose.distance - 0.15 });
    case '-': return clampPose({ ...pose, distance: pose.distance + 0.15 });
    default: return null;
  }
}
