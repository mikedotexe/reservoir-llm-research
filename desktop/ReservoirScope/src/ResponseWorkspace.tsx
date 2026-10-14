import { useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import { responseApi } from './responseApi';
import { ResponseController } from './responseController';
import type { ResponseEventDetail, ResponseField, ResponseFrame, ResponseSummary } from './responseTypes';
import SurfaceView from './SurfaceView';
import CoordinateInspector from './CoordinateInspector';
import { DEFAULT_CAMERA, type ReferenceScene } from './types';
import './response.css';

const exact = (value: number | null | undefined) => value === null || value === undefined ? 'Unavailable' : String(value);
function Metadata({ values }: { values: Record<string, string> }) {
  return <dl className="response-metadata">{Object.entries(values).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl>;
}

/** Subtract integer identities before conversion so adjacent large u64 IDs stay distinct. */
export function responsePlotPositions(summary: ResponseSummary): number[] {
  if (summary.kind === 'simulation') return summary.timeline.map((_, index) => index / Math.max(1, summary.frameCount - 1));
  const positions = summary.timeline.map(point => BigInt(point.position));
  const first = positions[0] ?? 0n, span = (positions.at(-1) ?? first) - first;
  return positions.map(position => span > 0n ? Number(position - first) / Number(span) : 0);
}
export function ResponseTimelinePlot({ summary, selected }: { summary: ResponseSummary; selected: number }) {
  if (!summary.timeline.length) return null;
  const native = summary.kind === 'native', positions = responsePlotPositions(summary);
  const maximum = summary.timeline.reduce((max, point) => Math.max(max, point.l2), Math.max(1e-12, summary.returnThreshold ?? 0));
  const x = (index: number) => 48 + positions[index] * 680, y = (value: number) => 128 - value / maximum * 104;
  const title = native ? 'Immediate action size at each applied boundary · L2' : 'Retained full-state separation · L2';
  const current = summary.timeline[selected];
  return <figure className="response-plot"><figcaption>{title}</figcaption><svg viewBox="0 0 760 172" role="img" aria-label={`${title}. ${native ? 'Successful native step IDs; bars are immediate action boundaries, not recovery.' : 'Simulation boundary indices, not measured seconds.'} Selected ${native ? 'step' : 'sample'} ${native ? current.position : selected}: ${String(current.l2)}. Vertical range 0 to ${String(maximum)}.${summary.returnThreshold !== null ? ` Return threshold ${String(summary.returnThreshold)}.` : ''}`}>
    <line x1="48" y1="128" x2="728" y2="128" className="response-plot-grid"/><text x="2" y="130">0</text><text x="2" y="20">{maximum.toPrecision(4)}</text>
    {native ? summary.timeline.map((point, index) => <line key={index} x1={x(index)} x2={x(index)} y1="128" y2={y(point.l2)} className="response-plot-bar"/>) : <polyline className="response-plot-line" points={summary.timeline.map((point, index) => `${x(index)},${y(point.l2)}`).join(' ')}/>}
    {summary.returnThreshold !== null && <line x1="48" x2="728" y1={y(summary.returnThreshold)} y2={y(summary.returnThreshold)} className="response-plot-threshold"/>}
    <line x1={x(selected)} x2={x(selected)} y1="20" y2="132" className="response-plot-cursor"/><circle cx={x(selected)} cy={y(current.l2)} r="3" className="response-plot-point"/>
    <text x="48" y="158">{native ? summary.timeline[0].position : '0 · displacement applied'}</text><text x="728" y="158" textAnchor="end">{native ? `${summary.timeline.at(-1)!.position} · successful step` : `${summary.frameCount - 1} · boundaries`}</text>
  </svg><p>{native ? 'One bar per applied or no-op receipt. The ordinary state is the result of that same step; this is not a no-action counterfactual or later response.' : `Raw retained boundaries, with no easing. The dashed threshold is ${exact(summary.returnThreshold)}; the declared dwell and return result are listed below. Playback seconds do not measure reservoir time.`}</p></figure>;
}

export function ResponseExactCoordinates({ summary, frame, node, onSelect }: { summary: ResponseSummary; frame: ResponseFrame; node: number; onSelect: (node: number) => void }) {
  return <section className="response-exact" aria-label="Exact paired coordinates"><h3>Exact coordinate {node}</h3><dl className="response-coordinate-values">
    <div><dt>{summary.firstLabel}</dt><dd>{exact(frame.first[node])}</dd></div><div><dt>{summary.secondLabel}</dt><dd>{exact(frame.second[node])}</dd></div><div><dt>{summary.kind === 'native' ? 'Retained Float32 action difference' : 'Retained paired difference'}</dt><dd>{exact(frame.delta[node])}</dd></div>
    {frame.direction && <div><dt>Requested direction weight</dt><dd>{exact(frame.direction[node])}</dd></div>}{frame.realizedNoise && <div><dt>Actual step noise</dt><dd>{exact(frame.realizedNoise[node])}</dd></div>}
  </dl><details><summary>All 128 exact paired coordinates</summary><div className="table-scroll"><table><caption>Original accepted values; no display normalization or smoothing</caption><thead><tr><th scope="col">Coordinate</th><th scope="col">{summary.firstLabel}</th><th scope="col">{summary.secondLabel}</th><th scope="col">Difference</th>{frame.direction && <th scope="col">Direction</th>}{frame.realizedNoise && <th scope="col">Step noise</th>}</tr></thead><tbody>{frame.delta.map((value, index) => <tr key={index} className={index === node ? 'selected-row' : ''}><th scope="row"><button aria-label={`Inspect response coordinate ${index}`} onClick={() => onSelect(index)}>{index}</button></th><td>{exact(frame.first[index])}</td><td>{exact(frame.second[index])}</td><td>{exact(value)}</td>{frame.direction && <td>{exact(frame.direction[index])}</td>}{frame.realizedNoise && <td>{exact(frame.realizedNoise[index])}</td>}</tr>)}</tbody></table></div></details></section>;
}

export function ResponseReceiptDetail({ event, node }: { event: ResponseEventDetail; node: number }) {
  return <section className="response-event-detail" aria-label={`Receipt ${event.index} detail`}><h3>Receipt {event.index} · {event.status}</h3><p>{event.hasState ? 'This receipt has an applied or no-op state boundary. Receipt inspection does not move the replay selection.' : event.isBoundary ? 'This boundary was rejected. Its retained before/after values do not establish an applied action.' : 'Admission, terminal or failed event. This event does not establish an applied state change.'}</p><Metadata values={event.metadata}/><h4>Receipt coordinate {node}</h4><dl className="response-coordinate-values"><div><dt>Requested direction</dt><dd>{exact(event.direction[node])}</dd></div>{event.realizedNoise && <div><dt>Actual step noise</dt><dd>{exact(event.realizedNoise[node])}</dd></div>}{event.first && <div><dt>Ordinary step</dt><dd>{exact(event.first[node])}</dd></div>}{event.second && <div><dt>Boundary result</dt><dd>{exact(event.second[node])}</dd></div>}{event.delta && <div><dt>Retained Float32 difference</dt><dd>{exact(event.delta[node])}</dd></div>}</dl></section>;
}

export default function ResponseWorkspace({ active }: { active: boolean }) {
  const [controller] = useState(() => new ResponseController(responseApi));
  const state = useSyncExternalStore(controller.subscribe, controller.snapshot, controller.snapshot);
  const [tableOnly, setTableOnly] = useState(false), [pose, setPose] = useState({ ...DEFAULT_CAMERA });
  useEffect(() => () => { void controller.close(); }, [controller]);
  useEffect(() => { if (!active) controller.pause(); }, [active, controller]);
  useEffect(() => { const hide = () => { if (document.hidden) controller.pause(); }; document.addEventListener('visibilitychange', hide); return () => document.removeEventListener('visibilitychange', hide); }, [controller]);
  useEffect(() => {
    if (!active || !state.playing) return;
    let stopped = false, timer: ReturnType<typeof setTimeout>;
    const tick = async () => { await controller.tick(performance.now()); if (!stopped) timer = setTimeout(() => { void tick(); }, 100); };
    timer = setTimeout(() => { void tick(); }, 100); return () => { stopped = true; clearTimeout(timer); };
  }, [active, controller, state.playing]);
  const { summary, frame } = state, native = summary?.kind === 'native';
  const references = useMemo(() => {
    if (!summary || !frame) return null;
    const make = (field: 'first' | 'second' | 'delta', title: string): ReferenceScene => ({ id: `response:${summary.responseId}:${field}`, title, nodeCount: 128, values: frame[field], sourceSha256: summary.sha256, description: 'Fixed coordinate-index drawing atlas; patches do not imply network connections or physical locations. No fill measurement, measured playback time or native PCA join.', provenance: `${summary.kind === 'native' ? 'Isolated native action rehearsal' : 'Separate esn-divide simulation'} · ${summary.filename} · boundary ${frame.position}` });
    return { first: make('first', summary.firstLabel), second: make('second', summary.secondLabel), delta: make('delta', native ? 'Immediate action difference' : 'Paired state difference') };
  }, [summary, frame, native]);
  if (!active) return null;
  const selectedField = state.field === 'comparison' ? 'delta' : state.field;
  const selectedReference = references?.[selectedField];
  return <section className="response-workspace" aria-labelledby="response-heading"><div className="response-heading"><div><h2 id="response-heading">Action boundaries and retained responses</h2><p>Inspect an immediate native action or the separate esn-divide simulation. Their states, clocks and meanings remain distinct.</p></div></div>
    <div className="response-open-controls"><button disabled={state.opening || state.exporting} onClick={() => void controller.open('native-example')}>Load bundled native receipts</button><button disabled={state.opening || state.exporting} onClick={() => void controller.open('native-file')}>Open native receipt file…</button><button disabled={state.opening || state.exporting} onClick={() => void controller.open('simulation-example')}>Load bundled simulation</button>{summary && <><button disabled={state.opening || state.exporting} onClick={() => void controller.export()}>{state.exporting ? 'Exporting…' : 'Export original bytes…'}</button><button onClick={() => void controller.close()}>Close response</button></>}</div>
    {state.message && <p className="response-message" role="status">{state.message}</p>}
    {!summary && <p className="response-empty">Choose evidence explicitly. Native receipts describe ordinary-step → applied-result boundaries in an isolated rehearsal. The simulation retains paired control and perturbed states across 65 boundaries; it is not native checkpoint replay.</p>}
    {summary && <><div className="response-source"><span className="eyebrow">{native ? 'MINIME NATIVE ESN · ISOLATED REHEARSAL' : 'ESN-DIVIDE SIMULATION · SEPARATE PARENT'}</span><h3>{summary.filename}</h3><p>{native ? 'Immediate observed differences, not a no-action counterfactual or recovery trajectory.' : 'One recorded direct state displacement followed by identical recorded controls; no adaptive-controller replica.'} No measured fill, synchronized wall-clock time or native PCA basis is supplied.</p></div>
      <div className="response-preferences"><label><input type="checkbox" checked={tableOnly} onChange={event => setTableOnly(event.target.checked)}/>Exact values without 3D</label><label>Coordinate <input type="number" aria-label="Response coordinate index" min="0" max="127" value={state.node} onChange={event => controller.selectNode(event.target.valueAsNumber)}/></label></div>
      {frame && references && selectedReference ? <>
        <nav className="response-fields" aria-label="Response comparison field">{([['delta', native ? 'Action difference' : 'Paired difference'], ['first', summary.firstLabel], ['second', summary.secondLabel], ['comparison', 'Compare states']] as [ResponseField, string][]).map(([field, label]) => <button key={field} aria-pressed={state.field === field} onClick={() => controller.selectField(field)}>{label}</button>)}</nav>
        <div className="response-transport" aria-label="Response playback controls"><button disabled={frame.index === 0} onClick={() => void controller.frame(frame.index - 1)}>Previous</button><button disabled={!state.playing && (state.loading || state.opening || frame.index >= summary.frameCount - 1)} onClick={() => state.playing ? controller.pause() : controller.play(performance.now())}>{state.playing ? 'Pause' : 'Inspect sequence'}</button><button disabled={frame.index >= summary.frameCount - 1} onClick={() => void controller.frame(frame.index + 1)}>Next</button><button onClick={() => void controller.frame(0)}>{native ? 'First applied boundary' : 'Injected boundary'}</button><label>Boundary index <input type="number" aria-label="Response boundary index" min="0" max={summary.frameCount - 1} value={frame.index} onChange={event => void controller.frame(event.target.valueAsNumber)}/></label><label>Playback rate <select aria-label="Response playback rate" value={state.rate} onChange={event => controller.setRate(Number(event.target.value))}>{[0.5, 1, 2, 3, 4, 8].map(rate => <option key={rate} value={rate}>{rate} {native ? 'receipts' : 'boundaries'} / playback s</option>)}</select></label><output>{state.loading ? 'Reading…' : `${native ? 'Applied receipt' : 'Sample boundary'} ${frame.index} / ${summary.frameCount - 1}`}</output></div>
        <label className="response-scrubber">{native ? 'Applied receipt order · raw boundaries' : 'Simulation boundary · 0 already includes the displacement'}<input aria-label="Response retained boundary" type="range" min="0" max={summary.frameCount - 1} step="1" value={frame.index} onChange={event => void controller.frame(event.target.valueAsNumber)}/></label>
        <div className={state.field === 'comparison' ? 'response-surfaces paired' : 'response-surfaces'}>{(state.field === 'comparison' ? [references.first, references.second] : [selectedReference]).map(reference => <SurfaceView key={reference.id} reference={reference} selected={state.node} onSelect={node => controller.selectNode(node)} pose={pose} onPose={setPose} tableOnly={tableOnly} fixedScale={state.field === 'delta' ? summary.fixedDeltaScale : 1} evidenceLabel={native ? 'Native immediate boundary' : 'Retained simulation'}/>)}</div>
        <p className="response-scale">{state.field === 'comparison' ? 'Both cameras and coordinate selection are linked. Both states use the same fixed −1…+1 signed scale.' : state.field === 'delta' ? `Difference scale fixed at −${summary.fixedDeltaScale}…+${summary.fixedDeltaScale} for ${native ? 'the complete accepted native bundle' : 'the declared simulation displacement'}; never normalized per frame.` : 'Signed state scale is fixed at −1…+1.'} Exact values below remain unscaled. The sphere is only an index drawing map.</p>
        <ResponseExactCoordinates summary={summary} frame={frame} node={state.node} onSelect={node => controller.selectNode(node)}/>
        <CoordinateInspector reference={selectedReference} selected={state.node} onSelect={node => controller.selectNode(node)} fixedScale={selectedField === 'delta' ? summary.fixedDeltaScale : 1}/>
        <div className="response-boundary"><h3>{native ? 'Successful native step' : 'Original simulation boundary'} {frame.position}</h3><p>{native ? 'Immediate full-state action size' : 'Current paired full-state separation'} · L2 <strong>{exact(frame.l2)}</strong></p><Metadata values={frame.metadata}/></div>
        <ResponseTimelinePlot summary={summary} selected={frame.index}/>
        <details className="response-timeline-table"><summary>Exact {native ? 'applied-boundary sizes' : 'retained separation path'} · {summary.frameCount} rows</summary><div className="table-scroll"><table><caption>{native ? 'Successful step identities and immediate action sizes' : 'Simulation samples and original boundary indices; no measured seconds'}</caption><thead><tr><th scope="col">Index</th><th scope="col">{native ? 'Successful step' : 'Original boundary'}</th><th scope="col">L2</th></tr></thead><tbody>{summary.timeline.map(point => <tr key={point.index} className={point.index === frame.index ? 'selected-row' : ''}><th scope="row"><button onClick={() => void controller.frame(point.index)} aria-label={`Select response boundary ${point.index}`}>{point.index}</button></th><td>{point.position}</td><td>{exact(point.l2)}</td></tr>)}</tbody></table></div></details>
      </> : <p className="response-empty">No applied state boundary. This accepted bundle contains {summary.events.length} receipts; inspect the events below.</p>}
      {summary.events.length > 0 && <section className="response-events"><h3>Native receipt events · {summary.events.length}</h3><p>Event inspection is independent of playback. Rejections, admission, terminal and failed events cannot create an applied state frame.</p><div className="response-event-list" aria-label="Native receipt events">{summary.events.map(event => <button key={event.index} aria-pressed={state.event?.index === event.index} onClick={() => void controller.selectEvent(event.index)}><span>Receipt {event.index} · {event.status}</span><small>{event.frameIndex !== null ? `Applied frame ${event.frameIndex}` : event.isBoundary ? 'Rejected boundary' : 'No applied state'}</small></button>)}</div>{state.loadingEvent && <p role="status">Reading selected receipt…</p>}{state.event && <ResponseReceiptDetail event={state.event} node={state.node}/>}</section>}
      <section className="response-result"><h3>{native ? 'Accepted bundle metadata' : 'Retained simulation result and selection'}</h3><Metadata values={summary.metadata}/></section>
      <details className="response-provenance"><summary>Evidence identity, provenance and limits</summary><p>Accepted {summary.origin === 'bundled' ? 'bundled resource' : 'explicitly opened file'} · {summary.sizeBytes} bytes</p><code>{summary.sha256}</code>{summary.provenance.map((text, index) => <p key={`p${index}`}>{text}</p>)}{summary.missingness.map((text, index) => <p key={`m${index}`}>{text}</p>)}<p>Source and model hashes supplied inside a receipt are producer declarations; they do not authenticate deployment. This reader does not follow historical paths, run a simulation, contact a model or change a live system.</p></details>
      {state.exported && <p className="response-export">Exported original bytes · {state.exported.name} · {state.exported.sizeBytes} bytes · <code>{state.exported.sha256}</code></p>}
    </>}
  </section>;
}
