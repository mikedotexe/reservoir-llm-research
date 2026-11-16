import { useId } from 'react';
import { fillRadius, type RecordedFillSample } from './fillSphereMath';

// The quadrant retains the sphere's volume encoding. The separate linear ruler
// explicitly magnifies percentage, rather than silently exaggerating geometry.
export function fillDetailWindow(value: number) {
  const start = Math.min(90, Math.max(0, Math.floor(value / 5) * 5 - 5));
  return { start, end: start + 10, position: (value - start) / 10 };
}
const quadrant = (r: number) => `M 20 150 L 20 ${150 - r} A ${r} ${r} 0 0 1 ${20 + r} 150 Z`;
export default function FillCrossSection({ sample }: { sample: RecordedFillSample | null }) {
  const id = useId(), radius = fillRadius(sample?.fillPercent), available = radius !== null && sample !== null;
  const detail = available ? fillDetailWindow(sample.fillPercent) : null;
  return <section className="fill-cross-section" aria-label="Sensory fill cross-section">
    <header><div><span className="eyebrow">LIVE MEASUREMENT</span><h2>Sensory fill</h2></div><strong className="fill-cross-value">{available ? sample.fillPercent.toFixed(2) : '—'}<small>{available ? '%' : ''}</small></strong></header>
    {available ? <>
      <div className="fill-cross-graphic">
        <svg viewBox="0 0 180 170" role="img" aria-labelledby={`${id}-title ${id}-description`}>
          <title id={`${id}-title`}>{`Quadrant cross-section · ${sample.fillPercent.toFixed(2)}% fill`}</title>
          <desc id={`${id}-description`}>One quarter of the spherical volume display. Radius is the cube root of fill divided by 100; this is a measurement diagram, not reservoir topology.</desc>
          <defs><linearGradient id={`${id}-fill`} x1="0" y1="1" x2="1" y2="0"><stop stopColor="#264b4a"/><stop offset="1" stopColor="#9de4ce"/></linearGradient></defs>
          <path d={quadrant(124)} fill="#15272b" stroke="#4c6569"/>
          {radius > 0 && <path d={quadrant(radius * 124)} fill={`url(#${id}-fill)`} fillOpacity=".65" stroke="#b4f2d9" strokeWidth="1.5"/>}
          {[20, 40, 60, 80].map(percent => <path key={percent} d={quadrant(Math.cbrt(percent / 100) * 124)} fill="none" stroke="#86b1ae" strokeOpacity=".25" strokeDasharray="2 4"/>)}
          <text x="24" y="17">100%</text><text x="155" y="154">0</text>
        </svg>
        <p>Quadrant slice<span>Volume ∝ fill<br/>Radius ∝ ∛fill</span></p>
      </div>
      <div className="fill-detail-label"><span>Detail · 10 percentage points</span><span>10× scale</span></div>
      <div className="fill-detail-track" role="img" aria-label={`Magnified fill scale, ${detail!.start} to ${detail!.end} percent. Current value ${sample.fillPercent} percent.`}><span style={{ left: `${detail!.position * 100}%` }}/></div>
      <div className="fill-detail-ticks">{[detail!.start, detail!.start + 5, detail!.end].map(value => <span key={value}>{value}%</span>)}</div>
    </> : <p className="fill-unavailable">No valid fill measurement.</p>}
    <details><summary>Measurement details</summary><p>Sensory fill is a percentage, not a rate. The quadrant keeps the spherical volume scale; the ruler magnifies a labelled 10-point window and recentres in 5-point increments.</p><dl><dt>Exact fill</dt><dd>{available ? `${sample.fillPercent}%` : 'Unavailable'}</dd><dt>Radius / full radius</dt><dd>{radius ?? 'Unavailable'}</dd><dt>Source</dt><dd>{sample?.provenance ?? 'No source supplied'}</dd><dt>Observation</dt><dd>{sample?.sourceTimeLabel ?? 'Unavailable'}</dd></dl><p>The display adds no smoothing and does not map internal topology.</p></details>
  </section>;
}
