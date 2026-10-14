export interface ScalarSample { index: number; value: number | null }

/** Missing values and omitted frame indices break a line, never bridge a gap. */
export function scalarSegments(samples: ScalarSample[], frameCount: number, minimum: number, maximum: number, width = 600, height = 120): string[] {
  const lines: string[] = [];
  let points: string[] = [];
  let previous = -2;
  const finish = () => { if (points.length) lines.push(points.join(' ')); points = []; };
  for (const sample of samples) {
    if (sample.value === null || !Number.isFinite(sample.value)) { finish(); previous = sample.index; continue; }
    if (sample.index !== previous + 1) finish();
    const x = frameCount <= 1 ? 0 : sample.index / (frameCount - 1) * width;
    const y = maximum <= minimum ? height / 2 : height - (sample.value - minimum) / (maximum - minimum) * height;
    points.push(`${x.toFixed(3)},${y.toFixed(3)}`);
    previous = sample.index;
  }
  finish();
  return lines;
}

export function recordedNumber(value: number | null | undefined, unit = ''): string {
  return value === null || value === undefined || !Number.isFinite(value) ? 'Not recorded' : `${value}${unit}`;
}
