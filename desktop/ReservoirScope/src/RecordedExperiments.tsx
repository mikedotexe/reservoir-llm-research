import { useEffect, useId, useRef, useState, useSyncExternalStore } from 'react';
import { api } from './api';
import CoordinateInspector from './CoordinateInspector';
import { recordedNumber, scalarSegments } from './recordingChart';
import { RecordingController } from './recordingController';
import { applicationAtCursor, turnAtCursor } from './guideNavigation';
import SurfaceView from './SurfaceView';
import { ControllerEvidence, MechanicalEvidence } from './RecordEvidence';
import { DEFAULT_CAMERA, type CameraPose, type RecordOpenRequest, type ReferenceScene, type TrackSummary, type TurnView, type VerificationReport } from './types';
import './recordings.css';

const examples = [
  { id: 'stage-1', label: '1 · State', description: 'A minimal retained reservoir' },
  { id: 'stage-2', label: '2 · Sensory field', description: 'Prepared text and retained spectra' },
  { id: 'stage-3', label: '3 · Return', description: 'Text returns through encoded input' },
  { id: 'stage-4', label: '4 · Regulation', description: 'Recorded reduced fill and control' },
];

interface RecordedExperimentsProps {
  active: boolean;
  controller?: RecordingController;
  embedded?: boolean;
  hidePlayback?: boolean;
  turnCursorStep?: string;
  openRequest?: RecordOpenRequest | null;
  onOpenResult?: (id: string, accepted: boolean) => void;
}
export default function RecordedExperiments({ active, controller: suppliedController, embedded = false, hidePlayback = false, turnCursorStep, openRequest, onOpenResult }: RecordedExperimentsProps) {
  const [localController] = useState(() => new RecordingController(api));
  const controller = suppliedController ?? localController;
  const lastRequest = useRef<string | null>(null);
  const resultCallback = useRef(onOpenResult);
  resultCallback.current = onOpenResult;
  const state = useSyncExternalStore(controller.subscribe, controller.snapshot);
  const [pose, setPose] = useState<CameraPose>({ ...DEFAULT_CAMERA });
  const [selection, setSelection] = useState<Record<string, number>>({});
  const [tableOnly, setTableOnly] = useState(false);
  const [turnChoice, setTurnChoice] = useState(0);
  const [comparison, setComparison] = useState('component-1');
  const { record, frame, trackId } = state;
  const track = record?.tracks.find(item => item.id === trackId);

  useEffect(() => { if (!active || hidePlayback) controller.pause(); }, [active, hidePlayback, controller]);
  useEffect(() => {
    if (!openRequest || lastRequest.current === openRequest.id) return;
    lastRequest.current = openRequest.id;
    const previous = controller.snapshot().record?.recordId;
    const pending = 'record' in openRequest ? controller.adopt(openRequest.record) : controller.open(openRequest.exampleId);
    void pending.then(() => {
      if (lastRequest.current !== openRequest.id) return;
      const current = controller.snapshot().record;
      const accepted = Boolean(current && ('record' in openRequest ? current.recordId === openRequest.record.recordId : current.recordId !== previous));
      resultCallback.current?.(openRequest.id, accepted);
    });
  }, [openRequest?.id, controller]);
  useEffect(() => {
    const visibility = () => { if (document.hidden) controller.pause(); };
    document.addEventListener('visibilitychange', visibility);
    return () => { document.removeEventListener('visibilitychange', visibility); if (!suppliedController) void controller.close(); };
  }, [controller, suppliedController]);
  useEffect(() => {
    if (!active || hidePlayback || !state.playing || state.loadingFrame || state.opening || !frame) return;
    const timer = window.setTimeout(() => { void controller.seek(frame.index + 1); }, 500);
    return () => window.clearTimeout(timer);
  }, [active, hidePlayback, controller, state.playing, state.loadingFrame, state.opening, frame]);
  useEffect(() => { setTurnChoice(0); }, [record?.recordId, trackId]);
  if (!active) return null;

  const scene: ReferenceScene | null = record && frame && track && frame.state.length > 0 ? {
    id: `${record.recordId}:${track.id}`, title: `${track.label} · recorded state`, nodeCount: frame.state.length,
    description: 'Original reservoir coordinates at the selected recorded frame. The coordinate atlas conveys neither anatomy nor network connectivity.',
    provenance: `${record.filename} · ${record.sha256} · step ${frame.step}`,
    values: frame.state, sourceSha256: record.sha256,
  } : null;
  const selected = scene ? Math.min(selection[scene.id] ?? 0, scene.nodeCount - 1) : 0;
  const chooseCoordinate = (index: number) => { if (scene) setSelection(previous => ({ ...previous, [scene.id]: index })); };
  const seek = (index: number) => { controller.pause(); void controller.seek(index); };

  return <section className={`recorded-workspace${embedded ? ' embedded-reader' : ''}${hidePlayback ? ' playback-collapsed' : ''}`} aria-label={embedded ? 'Guided recorded evidence' : 'Recorded experiments'}>
    {!embedded && <>
    <div className="recorded-heading"><div><span className="eyebrow">EXPERIMENTS · RECORDED EVIDENCE</span><h1 id="recorded-heading">Return to a recording.</h1><p>Read verified experiment files without running a model or changing the original.</p></div><button className="primary-button" disabled={state.opening} onClick={() => void controller.open()}>Open recording…</button></div>
    <div className="recorded-examples" aria-label="Bundled recorded experiments">{examples.map(example => <button key={example.id} disabled={state.opening} onClick={() => void controller.open(example.id)}><strong>{example.label}</strong><span>{example.description}</span></button>)}</div>
    <div className="comparison-picker"><label>More retained examples <select value={comparison} onChange={event => setComparison(event.target.value)}>{Array.from({ length: 8 }, (_, index) => <option key={index} value={`component-${index + 1}`}>Component {String.fromCharCode(65 + index)} · recorded tracks</option>)}<option value="observation-active-scripted">Active observation · scripted recording</option><option value="example-model-observation-active">Active observation · recorded model failure</option><option value="observation-scripted">Quiet observation · scripted recording</option><option value="example-model-observation">Quiet observation · recorded model</option><option value="regulation-controller">Controller mechanism · sensory fields only</option></select></label><button disabled={state.opening} onClick={() => void controller.open(comparison)}>Open selected example</button></div>
    </>}
    {(state.message || state.loadingFrame || !embedded) && <p className="reader-message" role="status">{state.message || (state.loadingFrame ? 'Reading the selected frame…' : 'Bundled examples are retained recordings. Choose Fresh experiments to create an offline run.')}</p>}
    {state.report && (!record || state.report.status !== 'passed' || state.report.sha256 !== record.sha256) && <Verification report={state.report} title="Incoming verification report" />}

    {record ? <>
      <div className="record-title"><div><span className="eyebrow">{record.origin === 'bundled' ? 'BUNDLED RECORDING' : record.origin === 'managed' ? 'MANAGED LIBRARY' : record.origin === 'created' ? 'CREATED EXPERIMENT' : 'OPENED FILE'} · {record.family}</span><h2>{record.title}</h2>{!embedded && <p>{record.filename} · outcome: {record.outcome} · seed: {record.seed ?? 'not recorded'}</p>}</div><div className="button-row"><button disabled={state.exporting} onClick={() => void controller.export()}>{state.exporting ? 'Exporting…' : 'Export original bytes…'}</button><button onClick={() => void controller.close()}>Close recording</button></div></div>
      <div id={embedded ? 'guided-record-playback' : undefined} className="record-controls">
        <label>Track <select value={track?.id ?? ''} disabled={record.tracks.length === 0} onChange={event => void controller.selectTrack(event.target.value)}>{record.tracks.map(item => <option key={item.id} value={item.id}>{item.label} · {item.frameCount} frames</option>)}</select></label>
        {frame && track && <div className="playback-buttons"><button disabled={frame.index === 0 || state.loadingFrame} onClick={() => seek(frame.index - 1)} aria-label="Previous recorded frame">←</button><button disabled={state.loadingFrame || state.opening || (!state.playing && frame.index === track.frameCount - 1)} onClick={() => state.playing ? controller.pause() : controller.play()}>{state.playing ? 'Pause' : 'Play recording'}</button><button disabled={frame.index === track.frameCount - 1 || state.loadingFrame} onClick={() => seek(frame.index + 1)} aria-label="Next recorded frame">→</button></div>}
        <label className="checkbox-label"><input type="checkbox" checked={tableOnly} onChange={event => setTableOnly(event.target.checked)} /> Table fallback</label>
      </div>
      {frame && track ? <>
      <div className="record-cursor"><label htmlFor="recorded-frame">Frame {frame.index + 1} / {track.frameCount}</label><input id="recorded-frame" type="range" min="0" max={Math.max(0, track.frameCount - 1)} value={frame.index} onChange={event => seek(Number(event.target.value))} /><span>Step {frame.step} · time {recordedNumber(frame.time, ' s')}</span></div>
      <p className="record-caption">Playback advances stored frames at up to 2 per second and waits for each read. Recorded time is shown separately. {state.loadingFrame && 'The previous frame remains visible while loading.'}</p>

      {record.study && <ControllerEvidence frame={frame} study={record.study} />}
      <div className="record-visuals">
        {scene ? <div>{[32, 128].includes(scene.nodeCount) ? <SurfaceView reference={scene} selected={selected} pose={pose} onPose={setPose} onSelect={chooseCoordinate} tableOnly={tableOnly} /> : <div className="notice">This state has {scene.nodeCount} coordinates. The 3D atlas currently supports 32 or 128; all recorded coordinates remain in the exact table.</div>}<CoordinateInspector reference={scene} selected={selected} onSelect={chooseCoordinate} /></div> : <div className="field-only-notice"><span className="eyebrow">SENSORY FIELD · NO RESERVOIR STATE</span><h2>Two fields, one shared input.</h2><p>This controller example retains sensory covariance and reduced fill. It has no reservoir activation vector, journal or language model.</p><p>Choose Baseline or Regulated above to inspect its retained fill, spectrum, retention and common 66-coordinate input.</p><p>Current recorded step: {frame.step}</p></div>}
        <div className="record-measures"><FillMeter value={frame.fillPercent} /><ScalarTimeline track={track} selected={frame.index} kind="fill" onSelect={seek} /><ScalarTimeline track={track} selected={frame.index} kind="eigenvalue" onSelect={seek} /><details><summary>Exact recorded spectrum and control</summary><p>Sensory covariance eigenvalues for this reduced experiment; distinct from the signed state and from live-system telemetry.</p><NumericVector title="Eigenvalues" values={frame.eigenvalues} /><dl><dt>Retention used</dt><dd>{recordedNumber(frame.retentionUsed)}</dd><dt>Next applied retention</dt><dd>{recordedNumber(frame.nextRetention ?? null)}</dd><dt>Fill exact</dt><dd>{recordedNumber(frame.fillPercent, '%')}</dd><dt>Semantic turn</dt><dd>{frame.semanticTurnId ?? 'Not recorded'}</dd></dl></details></div>
      </div>
      </> : <div className="record-empty"><h2>No frames retained on this track.</h2><p>The verification result and recorded outcome remain available. No state or fill frame is present.</p></div>}
      <div className="record-evidence">
        {!embedded && frame && <MechanicalEvidence frame={frame} />}
        {frame && <details><summary>Recorded input{record.family !== 'regulation' && ' and noise'} · selected frame</summary><p>These are stored vectors at step {frame.step}; no input is sent or generated by opening them.</p><NumericVector title="Input" values={frame.input} />{record.family === 'regulation' ? <p>No separate noise vector is recorded by this sensory-field study.</p> : <NumericVector title="Noise" values={frame.noise} />}</details>}
        {track && <section className="record-turns"><div className="section-heading"><div><span className="eyebrow">PROMPTS · REPLIES · ENCODING</span><h2>Recorded language turns</h2></div><span>{track.turnCount} retained</span></div>
          {track.turnCount > 0 ? <><div className="turn-picker"><label>Turn number <input type="number" min="1" max={track.turnCount} value={turnChoice + 1} onChange={event => setTurnChoice(Math.max(0, Math.min(track.turnCount - 1, Number(event.target.value) - 1)))} /></label><button disabled={state.loadingTurn} onClick={() => void controller.turn(turnChoice)}>{state.loadingTurn ? 'Reading…' : 'Inspect recorded turn'}</button></div><p className="record-caption">Turn selection is independent of the frame cursor. Observed and application steps show the recorded relationship.</p>
            {state.turn && !turnAtCursor(state.turn, turnCursorStep) && <p className="notice">This turn has not been reached at the current guided cursor. Its text and outcome remain hidden.</p>}{state.turn && turnAtCursor(state.turn, turnCursorStep) && <div className="turn-content"><TurnIdentity turn={state.turn} cursorStep={turnCursorStep} />{state.turn.failure && <p className="status-warning">Recorded failure: {state.turn.failure}</p>}<details open><summary>Exact prompt</summary><pre>{state.turn.prompt}</pre></details><details open><summary>Recorded reply / journal text</summary>{state.turn.reply === null ? <p>Reply text not recorded.</p> : <pre>{state.turn.reply}</pre>}</details><details><summary>Raw recorded reply</summary>{state.turn.rawReply === null ? <p>Raw reply not recorded.</p> : <pre>{state.turn.rawReply}</pre>}</details><details><summary>Encoded features and semantic vector</summary><NumericVector title="Encoded features" values={state.turn.encodedFeatures} /><NumericVector title="Semantic vector" values={state.turn.semanticVector} /></details></div>}</> : <p>No language turns were recorded on this track.</p>}
        </section>}
      </div>
      <Verification report={record.verification} title="Accepted recording verification" />
      <details className="record-identity"><summary>Original file identity</summary><dl><dt>Filename</dt><dd>{record.filename}</dd><dt>Outcome</dt><dd>{record.outcome}</dd><dt>Seed</dt><dd>{record.seed ?? 'Not recorded'}</dd><dt>Format</dt><dd>{record.format}</dd><dt>SHA-256</dt><dd className="hash">{record.sha256}</dd><dt>Export</dt><dd>Exports the original retained bytes, without reconstructing the JSON.</dd></dl>{state.exported && <p className="hash">Exported {state.exported.name} · {state.exported.sizeBytes.toLocaleString()} bytes · {state.exported.sha256}</p>}</details>
    </> : <div className="record-empty"><span aria-hidden="true">◉</span><h2>Choose a recording to begin.</h2><p>Reservoir state, reduced fill, spectra and language evidence appear only when present in an accepted file. A failed or incomplete replacement keeps your current reading.</p></div>}
  </section>;
}

export function Verification({ report, title }: { report: VerificationReport; title: string }) {
  return <details className={`verification-report ${report.status}`} open={report.status !== 'passed'}><summary>{title} · {report.status}</summary><p>{report.scope}</p><dl><dt>Checked steps</dt><dd>{report.checkedSteps}</dd><dt>Checked turns</dt><dd>{report.checkedTurns}</dd><dt>Models contacted</dt><dd>{report.modelsContacted ? 'Yes, according to report' : 'No, according to report'}</dd></dl>{report.diagnostics.length > 0 && <ul>{report.diagnostics.map((message, index) => <li key={index}>{message}</li>)}</ul>}<p className="hash">{report.sha256 ?? 'No source hash reported'}</p></details>;
}

export function TurnIdentity({ turn, cursorStep }: { turn: TurnView; cursorStep?: string }) {
  const recordedFlag = (value: boolean | null) => value === null ? 'Not recorded' : value ? 'Recorded as yes' : 'Recorded as no';
  return <dl>
    <dt>Turn</dt><dd>{turn.index + 1} · {turn.id}</dd>
    <dt>Observed / applied</dt><dd>{turn.observedStep ?? 'Not recorded'} / {applicationAtCursor(turn.applicationStep, cursorStep)}</dd>
    <dt>Status</dt><dd>{turn.status}</dd>
    <dt>Recorded source</dt><dd>{turn.backend ?? 'Not recorded'}</dd>
    <dt>Configured model</dt><dd>{turn.configuredModel ?? 'Not recorded'}</dd>
    <dt>Returned provider model</dt><dd>{turn.providerModel ?? 'Not recorded'}</dd>
    <dt>Request started</dt><dd>{recordedFlag(turn.requestStarted)}</dd>
    <dt>Tape packet ID</dt><dd>{turn.tapePacketId ?? 'Not recorded'}</dd>
    <dt>Failure phase</dt><dd>{turn.failurePhase ?? 'Not recorded'}</dd>
    <dt>Journal saved</dt><dd>{recordedFlag(turn.journalSaved)}</dd>
    <dt>Requested / chosen action</dt><dd>{turn.requestedAction ?? 'Not recorded'} / {turn.chosenAction ?? 'Not recorded'}</dd>
    <dt>Context</dt><dd>{turn.contextKind ?? 'Not recorded'}</dd>
    <dt>Memory entry IDs</dt><dd>{turn.memoryEntryIds.length > 0 ? turn.memoryEntryIds.join(', ') : 'No IDs recorded'}</dd>
    <dt>Journal path</dt><dd>{turn.journalRelativePath ?? 'Not recorded'}</dd>
  </dl>;
}

export function FillMeter({ value }: { value: number | null }) {
  const id = useId().replaceAll(':', '');
  const available = value !== null && Number.isFinite(value);
  const height = available ? Math.max(0, Math.min(100, value)) / 100 * 124 : 0;
  return <section className="record-fill" aria-label="Recorded reduced fill"><div><span className="eyebrow">RECORDED REDUCED FILL</span><h2>{available ? `${value.toFixed(2)}%` : 'Not recorded'}</h2><p>Separate from signed reservoir state.</p>{available && <p className="fill-exact">Exact: {value}%</p>}</div><svg viewBox="0 0 160 160" aria-hidden="true"><defs><clipPath id={id}><circle cx="80" cy="80" r="62" /></clipPath></defs><circle cx="80" cy="80" r="62" fill="#0a151e" stroke="#486671" /><g clipPath={`url(#${id})`}>{available && <rect x="18" y={142 - height} width="124" height={height} fill="#419e92" />}{[25, 50, 75].map(percent => <line key={percent} x1="18" x2="142" y1={142 - percent * 1.24} y2={142 - percent * 1.24} stroke="#bce4d2" opacity=".22" />)}</g><text x="80" y="155" textAnchor="middle" fill="#8ba3ad" fontSize="9">0–100% display scale</text></svg></section>;
}

export function ScalarTimeline({ track, selected, kind, onSelect }: { track: TrackSummary; selected: number; kind: 'fill' | 'eigenvalue'; onSelect: (index: number) => void }) {
  const samples = track.timeline.map(point => ({ index: point.index, value: kind === 'fill' ? point.fillPercent : point.eigenvalues?.[0] ?? null }));
  const present = samples.filter(sample => sample.value !== null && Number.isFinite(sample.value));
  const maximum = kind === 'fill' ? 100 : Math.max(0, ...present.map(sample => sample.value!));
  const segments = scalarSegments(samples, track.frameCount, 0, maximum);
  return <section className="scalar-timeline"><div><h3>{kind === 'fill' ? 'Reduced fill' : 'Sensory covariance λ₁'}</h3><span>{kind === 'fill' ? '0–100%' : `0–${maximum || 0}`}</span></div>{present.length > 0 ? <svg viewBox="-4 -4 608 128" role="img" aria-label={`${kind === 'fill' ? 'Recorded fill' : 'Recorded leading covariance eigenvalue'} across the track; missing samples are gaps.`} onClick={event => { const bounds = event.currentTarget.getBoundingClientRect(); onSelect(Math.round(Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width)) * (track.frameCount - 1))); }}><line x1="0" y1="120" x2="600" y2="120" stroke="#334650" />{segments.map((points, index) => points.includes(' ') ? <polyline key={index} points={points} fill="none" stroke={kind === 'fill' ? '#80d3b3' : '#b7a0e8'} strokeWidth="2" vectorEffect="non-scaling-stroke" /> : <circle key={index} cx={Number(points.split(',')[0])} cy={Number(points.split(',')[1])} r="2" fill="#b7dace" />)}<line x1={track.frameCount <= 1 ? 0 : selected / (track.frameCount - 1) * 600} x2={track.frameCount <= 1 ? 0 : selected / (track.frameCount - 1) * 600} y1="0" y2="120" stroke="#f5d394" strokeWidth="1" /></svg> : <p className="timeline-missing">Not recorded on the retained timeline.</p>}<p>{track.timeline.length} recorded points{track.timelineStride > 1 ? ` · every ${track.timelineStride}th frame plus final; sampled gaps are not connected` : ' · gaps remain missing'}. Use the frame slider for exact navigation.</p></section>;
}

function NumericVector({ title, values }: { title: string; values: number[] | null }) {
  return <div className="numeric-vector"><h3>{title}</h3>{values === null ? <p>Not recorded.</p> : values.length === 0 ? <p>Recorded as an empty vector.</p> : <div className="table-scroll"><table><thead><tr><th scope="col">Index</th><th scope="col">Exact value</th></tr></thead><tbody>{values.map((value, index) => <tr key={index}><th scope="row">{index}</th><td>{value.toString()}</td></tr>)}</tbody></table></div>}</div>;
}
