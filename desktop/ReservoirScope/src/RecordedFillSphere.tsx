import { useEffect, useId, useRef, useState } from 'react';
import { FILL_REFERENCE_SCOPE, fillRadius, referenceRings, type FillReferences, type RecordedFillSample } from './fillSphereMath';
import { mountFillSphere, type FillGraphicsStatus, type FillSphereRenderer } from './fillSphereRenderer';
import './fillSphere.css';

export type { FillReferences, RecordedFillSample } from './fillSphereMath';
export interface RecordedFillSphereProps {
  sample: RecordedFillSample | null;
  references?: FillReferences | null;
  active?: boolean;
  tableOnly?: boolean;
  compact?: boolean;
}
export default function RecordedFillSphere({ sample, references, active = true, tableOnly = false, compact = false }: RecordedFillSphereProps) {
  const titleId = useId();
  const host = useRef<HTMLDivElement>(null);
  const runtime = useRef<FillSphereRenderer | null>(null);
  const current = useRef({ sample, references }); current.current = { sample, references };
  const [graphics, setGraphics] = useState<FillGraphicsStatus | null>(null);
  const radius = fillRadius(sample?.fillPercent);
  const available = sample !== null && radius !== null;
  const rings = referenceRings(references);
  useEffect(() => {
    if (!active || tableOnly || !available || !host.current) { setGraphics(null); return; }
    let alive = true;
    setGraphics(null);
    let mounted: FillSphereRenderer | null = null;
    try {
      mounted = mountFillSphere(host.current, status => { if (alive) setGraphics(status); });
      runtime.current = mounted;
      mounted.update(current.current.sample!.fillPercent, current.current.references);
    } catch (error) {
      setGraphics({ state: 'unavailable', detail: error instanceof Error ? error.message : 'Graphics unavailable. Exact retained values remain available.', frames: 0, supportsRecovery: false });
    }
    return () => { alive = false; mounted?.dispose(); if (runtime.current === mounted) runtime.current = null; };
  }, [active, tableOnly, available]);
  useEffect(() => { if (available) runtime.current?.update(sample!.fillPercent,references); }, [available,sample,references]);
  if (!active) return null;
  const fallback = !available ? 'No retained fill measurement' : tableOnly ? 'Exact values view' : graphics?.state === 'lost' ? 'Graphics context lost' : graphics?.state === 'unavailable' ? 'Graphics unavailable' : 'Preparing the fill sphere';
  const exactDetails = <>
    <dl className="recorded-fill-values">
      <div><dt>Exact retained fill</dt><dd>{available ? `${String(sample!.fillPercent)}%` : 'Unavailable'}</dd></div>
      <div><dt>Sphere radius / full radius</dt><dd>{radius === null ? 'Unavailable' : String(radius)}</dd></div>
      <div><dt>Source</dt><dd>{sample?.provenance || 'No source supplied'}</dd></div>
      <div><dt>Retained time or position</dt><dd>{sample?.sourceTimeLabel || 'Not supplied'}</dd></div>
    </dl>
    {sample !== null && !available && <p className="recorded-fill-warning">The supplied fill is outside the finite 0–100% display contract; it has not been clamped. Supplied value: {String(sample.fillPercent)}.</p>}
    <p className="recorded-fill-explanation">The percentage controls sphere volume. Its radius is the cube root of the volume fraction; 12.5% fill has half the full radius. The large readout is rounded to two decimals; the exact retained percentage is listed above.</p>
    {rings.length > 0 ? <details className="recorded-fill-references" open><summary>Retained reference zones</summary>
      <p>{FILL_REFERENCE_SCOPE}</p><table><caption>{references!.provenance}</caption><thead><tr><th scope="col">Reference</th><th scope="col">Fill volume</th></tr></thead><tbody>{rings.map(ring => <tr key={ring.key}><th scope="row"><span className="recorded-fill-swatch" aria-hidden="true" style={{ backgroundColor: `#${ring.color.toString(16).padStart(6,'0')}` }} />{ring.title}</th><td>{String(ring.percent)}%</td></tr>)}</tbody></table>
    </details> : <p className="recorded-fill-explanation">{references ? 'Reference metadata is outside the supported ordered 0–100% contract; no reference rings are drawn.' : 'No retained reference configuration was supplied; no target or operating-zone rings are inferred.'}</p>}
    {available && !tableOnly && <details className="recorded-fill-qualification"><summary>Graphics diagnostics</summary><p>WebGL2 · {graphics?.frames ?? 0} frames drawn</p><p>This explicit test removes the graphics context temporarily. The retained percentage, provenance and reference values stay available.</p><div><button disabled={!graphics?.supportsRecovery || graphics.state !== 'ready'} onClick={() => runtime.current?.loseContext()}>Lose fill graphics context</button><button disabled={graphics?.state !== 'lost' || !graphics.supportsRecovery} onClick={() => runtime.current?.restoreContext()}>Restore fill context</button></div>{graphics && !graphics.supportsRecovery && <p>The context-loss testing extension is unavailable.</p>}</details>}
  </>;
  return <section className="recorded-fill-card" aria-labelledby={titleId}>
    <header className="recorded-fill-heading"><div><span className="eyebrow">RECORDED FILL</span><h2 id={titleId}>Spherical volume</h2><p>A cutaway view of the retained fill percentage.</p></div>
      <div className="recorded-fill-number" aria-label={available ? `Retained fill ${String(sample!.fillPercent)} percent` : 'No retained fill measurement'}>{available ? <>{sample!.fillPercent.toFixed(2)}<small>%</small></> : '—'}</div>
    </header>
    <div className="recorded-fill-canvas" data-show-graphics={available && !tableOnly && graphics?.state === 'ready' ? 'true' : 'false'} ref={host}>
      {(!available || tableOnly || graphics?.state !== 'ready') && <div className="recorded-fill-fallback" role="status"><span aria-hidden="true">◯</span><strong>{fallback}</strong><p>{!available ? 'A missing or invalid value is not shown as an empty sphere.' : tableOnly ? 'The graphics context is released. The retained value and reference table remain available below.' : graphics?.detail ?? 'Preparing a bounded WebGL2 scene.'}</p></div>}
      {available && !tableOnly && graphics?.state === 'ready' && <div className="recorded-fill-caption">100% reference shell<br /><span>Radius ∝ ∛(fill / 100)</span></div>}
    </div>
    <div className="recorded-fill-status"><span>{available && !tableOnly && graphics?.state === 'ready' ? '● Recorded value · no smoothing' : fallback}</span></div>
    {compact && sample && <p className="recorded-fill-explanation">{sample.provenance} · {sample.sourceTimeLabel ?? 'Time not supplied'}</p>}
    {compact ? <details className="recorded-fill-qualification"><summary>Exact fill values, interpretation and graphics recovery</summary>{exactDetails}</details> : exactDetails}
  </section>;
}
