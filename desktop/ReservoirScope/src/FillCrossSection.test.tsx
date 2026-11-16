import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import FillCrossSection, { fillDetailWindow } from './FillCrossSection';

describe('fill quadrant and explicitly magnified detail', () => {
  it('keeps missing and invalid measurements distinct from a real zero', () => {
    for (const sample of [null, ...[-1, 101, NaN, Infinity].map(fillPercent => ({ fillPercent, provenance: 'test' }))]) {
      const html = renderToStaticMarkup(<FillCrossSection sample={sample}/>);
      expect(html).toContain('No valid fill measurement');
      expect(html).not.toContain('<svg');
      expect(html).not.toContain('0.00');
    }
    const zero = renderToStaticMarkup(<FillCrossSection sample={{ fillPercent: 0, provenance: 'retained zero' }}/>);
    expect(zero).toContain('0.00');
    expect(zero).toContain('Magnified fill scale, 0 to 10 percent');
  });
  it('retains the exact percentage, provenance and volume encoding beside labelled magnification', () => {
    const html = renderToStaticMarkup(<FillCrossSection sample={{ fillPercent: 12.5, provenance: '<source>', sourceTimeLabel: 'step 42' }}/>);
    expect(html).toContain('<dd>0.5</dd>');
    expect(html).toContain('<dd>12.5%</dd>');
    expect(html).toContain('&lt;source&gt;');
    expect(html).toContain('step 42');
    expect(html).toContain('10× scale');
    expect(html).toContain('not reservoir topology');
  });
  it('keeps every valid percentage inside its declared 10-point detail window', () => {
    for (let n = 0; n <= 1000; n++) {
      const value = n / 10, scale = fillDetailWindow(value);
      expect(scale.start).toBeGreaterThanOrEqual(0);
      expect(scale.end).toBeLessThanOrEqual(100);
      expect(scale.end - scale.start).toBe(10);
      expect(scale.position).toBeGreaterThanOrEqual(0);
      expect(scale.position).toBeLessThanOrEqual(1);
      expect(scale.start + 10 * scale.position).toBeCloseTo(value, 10);
    }
  });
});
