import { useId, useMemo, useState, type KeyboardEvent, type MouseEvent } from 'react';
import type { ObservatoryTimelinePoint } from './observatoryTypes';
import { buildTrajectory, exactProjectionValue, nearestTrajectoryRow, TRAJECTORY_PLOT, trajectoryGeometryKey, trajectoryRowForKey, type TrajectoryProjection } from './trajectoryMath';

interface Props {
  points: ObservatoryTimelinePoint[];
  total: number;
  selectedIndex: number | null;
  onSelect: (index: number) => void;
}

export default function RecordedTrajectory({ points, total, selectedIndex, onSelect }: Props) {
  const id = useId();
  const [pair, setPair] = useState(0);
  const geometryKey = useMemo(() => trajectoryGeometryKey(points, total), [points, total]);
  // The key contains all geometry/validation inputs. Node-history refreshes may
  // replace the point objects without changing this retained PCA geometry.
  const geometry = useMemo(() => buildTrajectory(points, total), [geometryKey, total]);
  if (geometry.status === 'unavailable') return <section className="recorded-trajectory" aria-label="Recorded projection trajectory">
    <h3>Recorded projection trajectory</h3><p role="status">{geometry.reason} Exact selected-row evidence remains available separately.</p>
  </section>;

  const selected = selectedIndex !== null && Number.isInteger(selectedIndex) ? geometry.rows[selectedIndex] : undefined;
  const current = selected?.index ?? null;
  const projection = geometry.projections[pair];
  const [a, b] = projection.axes, name = `PC${a + 1} / PC${b + 1}`;
  const marker = current === null ? null : projection.points[current];
  const { left, top, size, viewSize } = TRAJECTORY_PLOT;
  const centerX = left + size / 2, centerY = top + size / 2;
  const selectKey = (event: KeyboardEvent<SVGSVGElement>) => {
    const row = trajectoryRowForKey(total, current, event.key);
    if (row === null) return;
    event.preventDefault();
    if (row !== current) onSelect(row);
  };
  const selectPoint = (event: MouseEvent<SVGSVGElement>, projection: TrajectoryProjection) => {
    if (event.button !== 0) return;
    const matrix = event.currentTarget.getScreenCTM();
    if (!matrix) return;
    // SVG's actual transform includes responsive sizing and letterboxing.
    const location = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
    if (location.x < left || location.x > left + size || location.y < top || location.y > top + size) return;
    const row = nearestTrajectoryRow(projection.points, location.x, location.y, current);
    if (row !== null && row !== current) onSelect(row);
  };

  return <section className="recorded-trajectory" aria-labelledby={`${id}-heading`}>
    <h3 id={`${id}-heading`}>Recorded projection trajectory</h3>
    <p>Inspect the retained PCA projection in row order. Select a point to inspect its recorded row.</p>
    <div className="trajectory-controls button-row" aria-label="Trajectory row controls">
      <label>Projection <select aria-label="Trajectory projection axes" value={pair} onChange={event => { const value = Number(event.target.value); if (Number.isInteger(value) && value >= 0 && value < 3) setPair(value); }}>
        {geometry.projections.map((p, i) => <option key={i} value={i}>PC{p.axes[0] + 1} / PC{p.axes[1] + 1}</option>)}
      </select></label>
      <button disabled={current === null || current === 0} onClick={() => { if (current !== null && current > 0) onSelect(current - 1); }}>Previous trajectory row</button>
      <output>{current === null ? 'No recorded row selected' : `Selected row ${current} of ${total - 1}`}</output>
      <button disabled={current === total - 1} onClick={() => onSelect(current === null ? 0 : current + 1)}>Next trajectory row</button>
    </div>
    <div className="trajectory-grid">
        <figure className="observatory-plot trajectory-plot" key={name}>
          <figcaption>{name}</figcaption>
          <svg viewBox={`0 0 ${viewSize} ${viewSize}`} preserveAspectRatio="xMidYMid meet" tabIndex={0} role="group"
            aria-label={`${name} retained trajectory. ${current === null ? 'No row selected.' : `Selected row ${current}.`} Arrow keys select adjacent recorded rows; Home and End select the first and last row.`}
            aria-describedby={`${id}-limits`} onKeyDown={selectKey} onClick={event => selectPoint(event, projection)}>
            <title>{name} · ordinal rows only</title>
            <rect x={left} y={top} width={size} height={size} fill="none" className="plot-grid"/>
            <line x1={left} y1={centerY} x2={left + size} y2={centerY} className="plot-zero"/>
            <line x1={centerX} y1={top} x2={centerX} y2={top + size} className="plot-zero"/>
            {projection.segments.map((segment, j) => segment.length === 1
              ? <circle key={j} cx={segment[0].x} cy={segment[0].y} r={2.5} className="plot-dot"/>
              : <polyline key={j} points={projection.segmentPaths[j]} className="plot-trace"/>)}
            <circle cx={projection.points[0].x} cy={projection.points[0].y} r={2.5} className="plot-dot"><title>First retained row 0</title></circle>
            <circle cx={projection.points[total - 1].x} cy={projection.points[total - 1].y} r={2.5} className="plot-dot"><title>Last retained row {total - 1}</title></circle>
            {marker && <g className="trajectory-selection" aria-hidden="true"><circle cx={marker.x} cy={marker.y} r={5} fill="#ffd79a" stroke="#071018" strokeWidth={1.5}/><text x={left} y={top - 10}>Row {marker.index}</text></g>}
            <text x={left} y={top + size + 17}>{(-geometry.extent).toPrecision(3)}</text>
            <text x={left + size} y={top + size + 17} textAnchor="end">+{geometry.extent.toPrecision(3)}</text>
            <text x={centerX} y={viewSize - 12} textAnchor="middle">PC{a + 1}</text>
            <text x={8} y={centerY} transform={`rotate(-90 8 ${centerY})`} textAnchor="middle">PC{b + 1} · same signed scale</text>
            <text x={centerX + 4} y={centerY - 5}>0</text>
          </svg>
        </figure>
    </div>
    <p id={`${id}-limits`}>Ordinal rows only: no per-row timestamps or measured speed. This retained projection is not the full 128-dimensional state or a physical path. Lines connect adjacent recorded rows without smoothing; they do not recover the intervening path.</p>
    <details className="observatory-provenance trajectory-exact">
      <summary>Projection details and exact values</summary>
      <p>All {total} retained rows use the same frozen PCA basis. Every axis uses the complete-capture range −{exactProjectionValue(geometry.extent)} to +{exactProjectionValue(geometry.extent)}. {geometry.allZero ? 'All coordinates are zero; ±1 is a display extent only.' : 'Selection does not rescale the plots.'}</p>
      {selected ? <table><caption>Exact retained projection coordinates · row {selected.index}</caption><thead><tr><th scope="col">PC1</th><th scope="col">PC2</th><th scope="col">PC3</th></tr></thead><tbody><tr>{selected.pc.map((value, i) => <td key={i}><code>{exactProjectionValue(value)}</code></td>)}</tr></tbody></table> : <p>Select a recorded row to inspect its exact projection coordinates.</p>}
      <p>These views share a selected row with the state surface, not a clock with the separate fill recording. Picking chooses the nearest retained point in the selected projection. Equal-distance ties keep the current row when possible, otherwise the lowest row index; use adjacent-row controls to inspect overlaps.</p>
    </details>
  </section>;
}
