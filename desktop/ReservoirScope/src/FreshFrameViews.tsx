import SurfaceView from './SurfaceView';
import CoordinateInspector from './CoordinateInspector';
import RecordedFillSphere from './RecordedFillSphere';
import type { CameraPose, ReferenceScene } from './types';
import type { SessionFrame, SessionFrames, SessionSummary, SessionTrackId, SessionTrackSummary } from './freshTypes';

function scene(summary: SessionSummary, frame: SessionFrame, track: SessionTrackSummary): ReferenceScene {
  return { id: `fresh-${summary.sessionId}-${summary.generation}-${track.id}`, title: `${track.label} · 32-node reservoir`, nodeCount: 32, values: frame.state, description: 'Actual signed reservoir coordinates on the fixed index atlas. Surface shape shows state values, not network connections or fill.', provenance: `Session ${summary.sessionId} · generation ${summary.generation} · ${track.id} track · exact step ${frame.step}`, step: Number(frame.step) };
}

export function FreshTrackStatus({ summary, selected, onSelect }: { summary: SessionSummary; selected: SessionTrackId; onSelect: (id: SessionTrackId) => void }) {
  if (summary.tracks.length < 2) return null;
  return <section className="fresh-track-status" aria-label="Matched track outcomes"><p>Shared clock · {summary.step} retained steps. Journal opportunities resolve in backend order; an unresolved or failed arm does not establish a completed pair.</p><div>{summary.tracks.map(track => <article key={track.id} className={track.id === selected ? 'selected' : ''}><button aria-pressed={track.id === selected} onClick={() => onSelect(track.id)}>Inspect {track.label}</button><p>Retained outcome: <strong>{track.status}</strong> · {track.turnCount} turns · {track.journalCount} journals</p>{track.failure && <p role="alert">{track.failure}</p>}</article>)}</div><p className="fresh-small">Retained outcomes describe portable evidence. The session phase above describes execution now; “stopped” in a partial record does not mean the other arm completed.</p></section>;
}

export default function FreshFrameViews({ summary, frames, selected, node, pose, onPose, onSelectTrack, onSelectNode, tableOnly, active }: {
  summary: SessionSummary; frames: SessionFrames; selected: SessionTrackId; node: number; pose: CameraPose; onPose: (pose: CameraPose) => void;
  onSelectTrack: (id: SessionTrackId) => void; onSelectNode: (node: number) => void; tableOnly: boolean; active: boolean;
}) {
  const track = summary.tracks.find(item => item.id === selected)!;
  const frame = frames[selected];
  if (!track || !frame) return <p>No frame is retained for this selected track.</p>;
  const reference = scene(summary, frame, track), paired = frames.left !== null;
  const fill = <RecordedFillSphere sample={frame.fillPercent === null ? null : { fillPercent: frame.fillPercent, provenance: `${track.label} · fresh reduced sensory active-mode fill`, sourceTimeLabel: `Exact step ${frame.step}` }} active={active} tableOnly={tableOnly}/>;
  const inspector = <CoordinateInspector reference={reference} selected={node} onSelect={onSelectNode} sourceNote={`Values come from the ${track.label} track at step ${frame.step}. No historical source path is read.`}/>;
  if (!paired) return <div className="fresh-primary"><div><SurfaceView reference={reference} selected={node} pose={pose} onPose={onPose} onSelect={onSelectNode} tableOnly={tableOnly} evidenceLabel="Fresh backend state"/>{inspector}</div>{fill}</div>;
  return <><p className="fresh-small">Aligned step {frame.step} · linked cameras · shared fixed −1 to +1 signed scale. Selecting a surface changes only the inspected track and coordinate.</p><div className="fresh-paired-surfaces">{summary.tracks.map(item => {
    const value = frames[item.id];
    return value && <div key={item.id} className={selected === item.id ? 'selected' : ''}><SurfaceView reference={scene(summary, value, item)} selected={node} pose={pose} onPose={onPose} onSelect={index => { onSelectTrack(item.id); onSelectNode(index); }} tableOnly={tableOnly} evidenceLabel={`${item.label} · fresh backend state`}/></div>;
  })}</div><div className="fresh-primary fresh-selected-measurements"><div><span className="eyebrow">EXACT SELECTED TRACK · {track.label}</span>{inspector}</div>{fill}</div></>;
}
