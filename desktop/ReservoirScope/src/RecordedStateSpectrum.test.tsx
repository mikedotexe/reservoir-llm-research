import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import RecordedStateSpectrum from './RecordedStateSpectrum';
import type { ObservatoryStateReference } from './observatoryTypes';

function reference(): ObservatoryStateReference {
  const eigenvalues = Array.from({ length: 128 }, (_, index) => (128 - index) / 1000);
  const totalSampleVariance = eigenvalues.reduce((sum, value) => sum + value, 0);
  const explainedVarianceRatio = eigenvalues.map(value => value / totalSampleVariance);
  const retainedFraction = explainedVarianceRatio.slice(0, 3).reduce((sum, value) => sum + value, 0);
  return { rows: 1024, dimensions: 128, retainedModeCount: 3, covarianceDenominator: 1023,
    eigenvalues, explainedVarianceRatio, retainedFraction, omittedFraction: 1 - retainedFraction,
    totalSampleVariance, fitScope: 'entire_captured_window_retrospective', frozen: true, sourceIdentity: 'retained-geometry-sha256' };
}
const html = (value: ObservatoryStateReference | null = reference()) => renderToStaticMarkup(<RecordedStateSpectrum reference={value}/>);

describe('whole-capture state spectrum', () => {
  it('renders all 128 modes once on a zero-based linear scale and distinguishes the three retained basis vectors', () => {
    const view = html();
    expect(view.match(/<svg\b/g)).toHaveLength(1);
    expect(view.match(/<rect\b/g)).toHaveLength(128);
    expect(view.match(/class="state-spectrum-retained"/g)).toHaveLength(3);
    expect(view.match(/class="state-spectrum-other"/g)).toHaveLength(125);
    expect(view).toContain('Zero to 0.128 squared activation units');
    expect(view).toContain('PC1–PC3 are left of the dashed divider');
    expect(view).not.toContain('<canvas'); expect(view).not.toContain('<animate');
  });

  it('keeps the full exact table and provenance closed without rounding backend evidence', () => {
    const data = reference(); data.eigenvalues[127] = .00012345678901234567;
    const view = html(data);
    expect(view).not.toMatch(/<details[^>]*\bopen/);
    expect(view.match(/<tr>/g)).toHaveLength(129);
    expect(view).toContain('<code>0.00012345678901234567</code>');
    expect(view).toContain(String(data.explainedVarianceRatio[127]));
    expect(view).toContain('retained-geometry-sha256');
    expect(view).toContain('Sample covariance denominator'); expect(view).toContain('1023');
    expect(view).toContain('without clipping or reordering');
  });

  it('explains retrospective state covariance without implying per-row or sensory measurements', () => {
    const view = html();
    expect(view).toContain('all 1,024 recorded rows');
    expect(view).toContain('stays fixed when the selected row changes');
    expect(view).toContain('separate from the sensory history');
    expect(view).toContain('recurrent-weight eigenvalues');
    expect(view).toContain('not a neuron location');
    expect(view).toContain('not a covariance estimate at the selected row');
    expect(view).toContain('not'); expect(view).toContain('stability or capacity boundary');
  });

  it('has no selected-row dependency and never mutates the supplied reference', () => {
    const data = reference(); const before = JSON.stringify(data);
    const first = html(data), next = html(data);
    expect(first.match(/<rect[^>]+>/g)).toEqual(next.match(/<rect[^>]+>/g));
    expect(JSON.stringify(data)).toBe(before);
  });

  it('refuses partial, sparse, negative, unordered or nonfinite spectra without showing partial bars', () => {
    const invalid: ObservatoryStateReference[] = [];
    let data = reference(); data.eigenvalues.pop(); invalid.push(data);
    data = reference(); delete data.eigenvalues[70]; invalid.push(data);
    data = reference(); data.eigenvalues[127] = -1e-15; invalid.push(data);
    data = reference(); data.eigenvalues[10] = NaN; invalid.push(data);
    data = reference(); data.eigenvalues[10] = Infinity; invalid.push(data);
    data = reference(); data.eigenvalues[2] = .9; invalid.push(data);
    data = reference(); data.explainedVarianceRatio[10] = 1.2; invalid.push(data);
    data = reference(); data.explainedVarianceRatio.pop(); invalid.push(data);
    for (const item of invalid) {
      const view = html(item); expect(view).toContain('role="status"');
      expect(view).not.toContain('<svg'); expect(view).not.toContain('<table');
    }
  });

  it('requires the correct complete-capture definition instead of treating unknown metadata as qualified', () => {
    const invalid = [null, ...[
      { dimensions: 127 }, { rows: 1 }, { rows: 1025 }, { retainedModeCount: 128 },
      { covarianceDenominator: 1024 }, { frozen: null }, { frozen: false },
      { fitScope: null }, { fitScope: 'online' }, { sourceIdentity: '' },
      { retainedFraction: NaN }, { omittedFraction: -1 }, { totalSampleVariance: Infinity },
    ].map(change => ({ ...reference(), ...change }))];
    for (const item of invalid) {
      const view = html(item); expect(view).toContain('role="status"'); expect(view).not.toContain('<svg');
    }
  });

  it('discloses a display-only extent for zero eigenvalues without fabricating variance', () => {
    const data = reference(); data.eigenvalues.fill(0); data.explainedVarianceRatio.fill(0);
    data.retainedFraction = 0; data.omittedFraction = 0; data.totalSampleVariance = 0;
    const view = html(data);
    expect(view).toContain('All eigenvalues are zero; 0–1 is a display extent only');
    expect(view.match(/height="0"/g)).toHaveLength(128);
    expect(view).not.toContain('NaN'); expect(view).not.toContain('Infinity');
  });
});
