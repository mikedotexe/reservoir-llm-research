import { useMemo } from 'react';
import SurfaceView from './SurfaceView';
import CoordinateInspector from './CoordinateInspector';
import RecordedFillSphere from './RecordedFillSphere';
import type { SessionFrame } from './freshTypes';
import type { CameraPose, ReferenceScene } from './types';
import type { SustainedSummary } from './myReservoirTypes';

function Vector({ label, values }: { label: string; values: number[] | null }) {
  return values === null ? <p>{label}: unavailable.</p> : <div className="table-scroll"><table><caption>{label} · exact retained values</caption><thead><tr><th scope="col">Coordinate</th><th scope="col">Value</th></tr></thead><tbody>{values.map((value, index) => <tr key={index}><th scope="row">{index}</th><td>{String(value)}</td></tr>)}</tbody></table></div>;
}
export default function MyReservoirVisuals({ summary, frame, node, onNode, pose, onPose, tableOnly }: { summary: SustainedSummary; frame: SessionFrame | null; node: number; onNode: (node: number) => void; pose: CameraPose; onPose: (pose: CameraPose) => void; tableOnly: boolean }) {
  // Stable frame identity keeps status/watchdog updates out of both renderers.
  const reference = useMemo<ReferenceScene | null>(() => frame ? { id: `personal-${summary.sessionId}-${summary.generation}`, title: 'My reservoir · 32 coordinates', nodeCount: 32, values: frame.state, step: Number(frame.step), description: 'Signed reservoir state on a fixed coordinate-index atlas. Shape is neither network connectivity nor sensory fill.', provenance: `Session ${summary.sessionId} · generation ${summary.generation} · global step ${frame.step}` } : null, [summary.sessionId, summary.generation, frame]);
  const fillSample = useMemo(() => frame && frame.fillPercent !== null ? { fillPercent: frame.fillPercent, provenance: 'Separate reduced sensory active-mode fill · sustained session', sourceTimeLabel: `Global step ${frame.step} · simulated time ${frame.time ?? 'unavailable'}` } : null, [frame]);
  if (!frame || !reference) return <section className="my-reservoir-live-view my-reservoir-empty" aria-label="Current reservoir visuals"><h2>{summary.step === 0 ? 'Waiting for the first observation' : 'Current frame unavailable'}</h2><p>{summary.step === 0 ? 'Measurements appear after the first numerical step.' : `The session is at global step ${summary.step}; its current frame is unavailable.`}</p></section>;
  return <section className="my-reservoir-live-view" aria-label="Current reservoir visuals">
    <h2>Current state and sensory fill</h2>
    <p className="my-reservoir-small">Live frame at step {frame.step}, separate from the selected journal.</p>
    <div className="my-reservoir-primary">
      <RecordedFillSphere sample={fillSample} tableOnly={tableOnly} compact/>
      <SurfaceView reference={reference} selected={node} onSelect={onNode} pose={pose} onPose={onPose} tableOnly={tableOnly} evidenceLabel="Current backend state"/>
    </div>
    <details className="my-reservoir-details"><summary>Current numerical measurements and exact inputs</summary>
      <p>Sensory fill is a smoothed estimate of active sensory modes, separate from recurrent state and the encoded text-input signal. It is a percentage, not a rate.</p>
      {summary.config.regulationEnabled && <p>Regulation uses a 68% target with an error deadband from 64% to 72%. These are controller reference settings, not a guaranteed outcome or a proven special state.</p>}
      <CoordinateInspector reference={reference} selected={node} onSelect={onNode} sourceNote="Exact current backend coordinates. Selecting a node does not change the next prompt or the independently selected journal."/>
      <dl className="my-reservoir-data"><dt>Global step</dt><dd>{frame.step}</dd><dt>Simulated time · seconds</dt><dd>{frame.time ?? 'Unavailable'}</dd><dt>Sensory retention used</dt><dd>{frame.retentionUsed ?? 'Unavailable'}</dd><dt>Next sensory retention</dt><dd>{frame.nextRetention ?? 'Unavailable'}</dd><dt>Held semantic source</dt><dd>{frame.semanticTurnId ?? 'No source supplied'}</dd></dl><p>Sensory eigenvalues describe a separate covariance field. They are not the reservoir-state spectrum, and fill is not a measurement of learned content.</p><div className="my-reservoir-vector-grid"><Vector label="Applied input" values={frame.input}/><Vector label="Seeded noise" values={frame.noise}/><Vector label="Sensory eigenvalues" values={frame.eigenvalues}/></div></details>
  </section>;
}
