import { memo, useId, useMemo } from 'react';
import type { ObservatoryStateReference } from './observatoryTypes';

interface Props { reference: ObservatoryStateReference | null }

function unavailable(reference: ObservatoryStateReference | null): string | null {
  if (!reference) return 'The full-capture state covariance reference is unavailable.';
  const { rows, dimensions, retainedModeCount, covarianceDenominator, eigenvalues, explainedVarianceRatio,
    retainedFraction, omittedFraction, totalSampleVariance, frozen, fitScope, sourceIdentity } = reference;
  if (!Number.isInteger(rows) || rows < 2 || rows > 1024 || dimensions !== 128 || retainedModeCount !== 3 || covarianceDenominator !== rows - 1) {
    return 'State spectrum unavailable: capture dimensions or covariance definition are inconsistent.';
  }
  if (frozen !== true || fitScope !== 'entire_captured_window_retrospective' || typeof sourceIdentity !== 'string' || !sourceIdentity.trim()) {
    return 'State spectrum unavailable: the frozen full-capture reference is not identified.';
  }
  if (!Array.isArray(eigenvalues) || !Array.isArray(explainedVarianceRatio) || eigenvalues.length !== dimensions || explainedVarianceRatio.length !== dimensions) {
    return 'State spectrum unavailable: all 128 eigenvalues and variance fractions are required.';
  }
  for (let index = 0; index < dimensions; index++) {
    const value = eigenvalues[index], fraction = explainedVarianceRatio[index];
    if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 ||
      typeof fraction !== 'number' || !Number.isFinite(fraction) || fraction < 0 || fraction > 1 ||
      (index > 0 && value > eigenvalues[index - 1])) {
      return 'State spectrum unavailable: retained values must be finite, nonnegative and in descending mode order.';
    }
  }
  if (![retainedFraction, omittedFraction].every(value => Number.isFinite(value) && value >= 0 && value <= 1) ||
    !Number.isFinite(totalSampleVariance) || totalSampleVariance < 0) {
    return 'State spectrum unavailable: retained variance metadata are invalid.';
  }
  return null;
}

function RecordedStateSpectrum({ reference }: Props) {
  const id = useId();
  const issue = useMemo(() => unavailable(reference), [reference]);
  if (issue || !reference) return <section className="recorded-state-spectrum" aria-label="State capture spectrum"><h3>State capture spectrum</h3><p role="status">{issue}</p></section>;
  const { rows, dimensions, eigenvalues, explainedVarianceRatio, retainedModeCount } = reference;
  const maximum = eigenvalues[0], extent = maximum || 1;
  const left = 48, top = 26, width = 688, height = 120, bottom = top + height;
  const barWidth = width / dimensions;
  return <section className="recorded-state-spectrum" aria-labelledby={`${id}-heading`}>
    <h3 id={`${id}-heading`}>State capture spectrum</h3>
    <p>One centered sample-covariance spectrum for all {rows.toLocaleString('en-US')} recorded rows. It stays fixed when the selected row changes.</p>
    <figure className="observatory-plot state-spectrum-plot">
      <figcaption>All {dimensions} state-covariance eigenvalues · zero-based linear scale</figcaption>
      <svg viewBox="0 0 760 200" role="img" aria-label={`Whole-capture state covariance spectrum, all ${dimensions} modes. Zero to ${String(extent)} squared activation units. First ${retainedModeCount} modes have retained basis vectors; the other eigenvalues do not.`} aria-describedby={`${id}-limits`}>
        <line x1={left} y1={bottom} x2={left + width} y2={bottom} className="plot-grid"/>
        <line x1={left} y1={top} x2={left + width} y2={top} className="plot-grid"/>
        {eigenvalues.map((value, index) => {
          const barHeight = value / extent * height;
          return <rect key={index} x={left + index * barWidth + .35} y={bottom - barHeight} width={barWidth - .7} height={barHeight}
            className={index < retainedModeCount ? 'state-spectrum-retained' : 'state-spectrum-other'}
            fill={index < retainedModeCount ? '#64ddc8' : '#8196b7'}>
            <title>Mode {index + 1}: {String(value)}; variance fraction {String(explainedVarianceRatio[index])}{index < retainedModeCount ? '; retained basis vector' : '; eigenvalue only'}</title>
          </rect>;
        })}
        <line x1={left + retainedModeCount * barWidth} y1={top} x2={left + retainedModeCount * barWidth} y2={bottom} className="plot-zero"/>
        <text x="3" y={top + 4}>{extent.toPrecision(4)}</text><text x="32" y={bottom + 4}>0</text>
        <text x={left} y={bottom + 18}>1</text><text x={left + width} y={bottom + 18} textAnchor="end">{dimensions}</text>
        <text x={left + width / 2} y="184" textAnchor="middle">Covariance mode rank · squared activation units</text>
      </svg>
      <p>PC1–PC3 are left of the dashed divider; only those three basis vectors are retained. They account for {(reference.retainedFraction * 100).toFixed(2)}% of this capture’s variance.</p>
      {maximum === 0 && <p>All eigenvalues are zero; 0–1 is a display extent only.</p>}
    </figure>
    <p id={`${id}-limits`}>This is separate from the sensory history’s three direction estimates, fill, live covariance and recurrent-weight eigenvalues. A mode rank is not a neuron location.</p>
    <details className="observatory-provenance state-spectrum-exact">
      <summary>Exact spectrum and reference provenance</summary>
      <dl>
        <div><dt>Capture rows / coordinates</dt><dd>{rows} / {dimensions}</dd></div>
        <div><dt>Sample covariance denominator</dt><dd>{reference.covarianceDenominator}</dd></div>
        <div><dt>First-three variance fraction</dt><dd>{String(reference.retainedFraction)}</dd></div>
        <div><dt>Other-mode variance fraction</dt><dd>{String(reference.omittedFraction)}</dd></div>
        <div><dt>Total sample variance</dt><dd>{String(reference.totalSampleVariance)}</dd></div>
        <div><dt>Fit scope</dt><dd>{reference.fitScope}</dd></div>
        <div><dt>Geometry source identity</dt><dd><code>{reference.sourceIdentity}</code></dd></div>
      </dl>
      <p>The reference was fitted retrospectively to the complete capture. These values are not a covariance estimate at the selected row, an online observation, or evidence of a stability or capacity boundary. Values below are the backend’s retained numbers, without clipping or reordering.</p>
      <table><caption>All {dimensions} retained covariance modes</caption>
        <thead><tr><th scope="col">Mode</th><th scope="col">Eigenvalue</th><th scope="col">Variance fraction</th><th scope="col">Basis vector retained</th></tr></thead>
        <tbody>{eigenvalues.map((value, index) => <tr key={index}><th scope="row">{index + 1}</th><td><code>{String(value)}</code></td><td><code>{String(explainedVarianceRatio[index])}</code></td><td>{index < retainedModeCount ? `PC${index + 1}` : 'No'}</td></tr>)}</tbody>
      </table>
    </details>
  </section>;
}

export default memo(RecordedStateSpectrum);
