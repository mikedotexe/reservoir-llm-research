import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import RecordedTrajectory from './RecordedTrajectory';
import type { ObservatoryTimelinePoint } from './observatoryTypes';

function point(index: number, pc: number[] | null): ObservatoryTimelinePoint {
  return { index, position: index, pc, tUtc: null, sessionId: null, fillPct: null, fillRatePctPerS: null, cascade: null,
    intervalSeconds: null, breakBefore: false, stateRms: .2, nodeValue: -.1 };
}
const rows = [point(0, [-1, 0, .12345678901234566]), point(1, [1, 2, 3]), point(2, [0, -2, 0])];
const html = (points = rows, total = points.length, selectedIndex: number | null = 0) => renderToStaticMarkup(<RecordedTrajectory points={points} total={total} selectedIndex={selectedIndex} onSelect={() => { throw new Error('Rendering must not select a row'); }}/>);

describe('recorded trajectory inspection', () => {
  it('restores the owner-retained projection when this view remounts', () => {
    const view = renderToStaticMarkup(<RecordedTrajectory points={rows} total={3} selectedIndex={1} onSelect={() => {}} projectionIndex={2} onProjectionChange={() => {}}/>);
    expect(view).toContain('PC2 / PC3 retained trajectory');
    expect(view).toContain('value="2" selected=""');
    expect(view).toContain('Selected row 1 of 2');
  });
  it('mounts one large SVG while making all three axis pairs selectable', () => {
    const view = html();
    expect(view.match(/<svg\b/g)).toHaveLength(1);
    for (const label of ['PC1 / PC2', 'PC1 / PC3', 'PC2 / PC3']) expect(view).toContain(label);
    expect(view).toContain('aria-label="Trajectory projection axes"');
    expect(view).toContain('tabindex="0" role="group"');
    expect(view).toContain('Arrow keys select adjacent recorded rows');
    expect(view).toContain('Home and End');
    expect(view).not.toContain('<canvas');
    expect(view).not.toContain('<animate');
  });

  it('keeps exact selected coordinates in a closed disclosure and states projection/clock limits', () => {
    const view = html();
    expect(view).toContain('Exact retained projection coordinates · row 0');
    expect(view).toContain('0.12345678901234566');
    expect(view).toContain('no per-row timestamps or measured speed');
    expect(view).toContain('not the full 128-dimensional state or a physical path');
    expect(view).toContain('do not recover the intervening path');
    expect(view).toContain('not a clock with the separate fill recording');
    expect(view).not.toMatch(/<details[^>]*\bopen/);
    expect(view).toContain('scope="col"');
  });

  it('moves only the selected marker/evidence while full geometry and bounds stay fixed', () => {
    const first = html(rows, 3, 0), last = html(rows, 3, 2);
    expect(first.match(/<polyline[^>]*>/g)).toEqual(last.match(/<polyline[^>]*>/g));
    expect(first).toContain('range −3 to +3'); expect(last).toContain('range −3 to +3');
    expect(first).toContain('Selected row 0 of 2'); expect(last).toContain('Selected row 2 of 2');
    expect(first).toContain('disabled="">Previous trajectory row');
    expect(last).toContain('disabled="">Next trajectory row');
    expect(last).toContain('Exact retained projection coordinates · row 2');
  });

  it('does not fabricate a marker or exact values when selection is absent or out of range', () => {
    for (const index of [null, -1, 3, 1.5]) {
      const view = html(rows, 3, index);
      expect(view).toContain('No recorded row selected');
      expect(view).not.toContain('<g class="trajectory-selection"');
      expect(view).not.toContain('<table');
      expect(view).toContain('Select a recorded row to inspect its exact');
    }
  });

  it('hides all geometry and explains incomplete or invalid coverage', () => {
    for (const [points, total] of [[rows.slice(0, 2), 3], [[point(0, [NaN, 0, 0])], 1], [[point(1, [1, 2, 3])], 1]] as const) {
      const view = html([...points], total);
      expect(view).not.toContain('<svg'); expect(view).not.toContain('<table');
      expect(view).toContain('role="status"'); expect(view).toContain('Trajectory unavailable');
      expect(view).toContain('Exact selected-row evidence remains available separately');
    }
  });

  it('discloses the zero-only display scale and retains the zero point', () => {
    const view = html([point(0, [0, 0, -0])]);
    expect(view).toContain('All coordinates are zero; ±1 is a display extent only');
    expect(view).toContain('<code>-0</code>');
    expect(view).toContain('Row 0');
    expect(view).not.toContain('NaN'); expect(view).not.toContain('Infinity');
  });
});
