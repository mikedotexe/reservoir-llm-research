import { useSyncExternalStore } from 'react';
import { geometryApi } from './geometryApi';
import { GeometryController } from './geometryController';
import type { GeometryEntry, GeometryPacket, GeometrySnapshot } from './geometryTypes';
import './geometry.css';

// One webview/window; never persisted or automatically reloaded from a path.
const windowReading = new GeometryController(geometryApi);

export default function GeometryWorkspace({ active, controller = windowReading }: { active: boolean; controller?: GeometryController }) {
  const state = useSyncExternalStore(controller.subscribe, controller.snapshot, controller.snapshot);
  if (!active) return null;
  const { packet } = state;
  const entry = packet?.records[state.selected];
  return <section className="geometry-workspace" aria-labelledby="geometry-heading">
    <header className="geometry-heading"><div><h1 id="geometry-heading">Geometry bookmarks</h1><p>{packet ? `${packet.owner} · ${packet.questionId} · ${packet.filename}` : 'Explore recorded state captures, predictions and comparisons.'}</p></div><div className="button-row"><button disabled={state.busy} onClick={() => void controller.open(true)}>Open synthetic example</button><button className="primary-button" disabled={state.busy} onClick={() => void controller.open()}>Open history file…</button></div></header>
    <p>Your reading stays in this window. Reopen the file next launch; opening does not add it to the Library.</p>
    <p className="reader-message" role="status">{state.message || 'Choose a local geometry history file. No live workspace is read automatically.'}</p>
    {packet ? <>
      {packet.origin === 'syntheticExample' && <div className="geometry-synthetic"><strong>Synthetic example · invented coordinates and text</strong><p>The Minime owner and source fields demonstrate the schema. This is not a Being’s observation or producer-interoperability evidence.</p></div>}
      <div className="geometry-heading"><h2>{packet.question || 'No question text recorded.'}</h2><button disabled={state.busy} onClick={() => void controller.export()}>Export original file…</button></div>
      <div className="geometry-layout"><nav aria-label="Geometry history"><ol className="geometry-history">{packet.records.map((item, index) => <li key={item.id}><button aria-current={index === state.selected ? 'step' : undefined} onClick={() => controller.select(index)}><strong>{index + 1}. {item.kind}</strong><span>{item.authoredText ?? (item.thresholdMet ? 'Numerical threshold met' : 'Numerical threshold not met')}</span></button></li>)}</ol>{packet.records.length === 0 && <p>No geometry records are retained.</p>}</nav>
      <div className="geometry-detail">{entry ? <>
        <GeometryAccount entry={entry} />
        {entry.snapshot && <GeometryCapture snapshot={entry.snapshot} frameIndex={state.frame} coordinate={state.coordinate} expanded={state.coordinatesExpanded} onSeek={index => controller.seek(index)} onCoordinate={index => controller.coordinate(index)} onExpand={value => controller.expand(value)} />}
        {entry.kind === 'prediction' && <><p>Predicted maximum mean-state RMS distance: <strong>{entry.maximumRmsDistance?.toString()}</strong></p><GeometryReference label="Baseline" id={entry.baseline} packet={packet} onSelect={index => controller.select(index)} /></>}
        {entry.kind === 'comparison' && <>
          <p className="geometry-distance">{entry.rmsDistance?.toString()}</p><p>{entry.thresholdMet ? 'Numerical threshold met' : 'Numerical threshold not met'}</p>
          <p>Retained RMS distance, independently checked against the two unweighted mean 128-node vectors. Sampling and gaps can affect the result; opposite movements can cancel in a mean.</p>
          <GeometryReference label="Prediction" id={entry.prediction} packet={packet} onSelect={index => controller.select(index)} /><GeometryReference label="Observation" id={entry.observation} packet={packet} onSelect={index => controller.select(index)} />
          <p className="geometry-limits">The prediction record precedes the second capture record. Its source interval can predate the prediction; this is not a prospective trial or proof that the result was previously unseen.</p><p>Recipe: <code>{entry.recipe}</code></p>
        </>}
        {entry.kind === 'revision' && <GeometryReference label="Revises" id={entry.target} packet={packet} onSelect={index => controller.select(index)} />}
        <details><summary>Record identity and request claim</summary><dl><dt>Record ID</dt><dd className="hash">{entry.id}</dd><dt>Request ID</dt><dd>{entry.requestId}</dd><dt>Request SHA-256</dt><dd className="hash">{entry.requestSha256}</dd></dl><p>These hashes bind retained content. They do not establish that an external request was executed.</p></details>
      </> : <p>No geometry record selected.</p>}</div></div>
      <GeometryProvenance packet={packet} />
      {state.exported && <p className="hash">Exported {state.exported.name} · {state.exported.sizeBytes} bytes · SHA-256 {state.exported.sha256}</p>}
    </> : <div className="geometry-empty"><h2>Choose a history to explore</h2><p>The synthetic example follows capture → prediction → capture → comparison → revision. You can also open an exported geometry history. If opening fails or is cancelled, your current reading stays in place.</p></div>}
  </section>;
}

export function GeometryAccount({ entry }: { entry: GeometryEntry }) {
  return <><h3>{entry.kind}</h3>{entry.authoredText !== null && <section aria-label="Authored account"><h4>Recorded account</h4><pre className="geometry-authored">{entry.authoredText}</pre></section>}</>;
}
function GeometryReference({ label, id, packet, onSelect }: { label: string; id: string | null; packet: GeometryPacket; onSelect: (index: number) => void }) {
  if (!id) return null;
  const index = packet.records.findIndex(record => record.id === id);
  return <div className="geometry-reference"><span>{label}</span><button disabled={index < 0} onClick={() => onSelect(index)}>{index >= 0 ? `Read ${index + 1}. ${packet.records[index].kind}` : 'Reference unavailable'}</button><code className="hash">{id}</code></div>;
}
export function GeometryCapture({ snapshot, frameIndex, coordinate, expanded, onSeek, onCoordinate, onExpand }: {
  snapshot: GeometrySnapshot; frameIndex: number; coordinate: number; expanded: boolean;
  onSeek: (index: number) => void; onCoordinate: (index: number) => void; onExpand: (value: boolean) => void;
}) {
  const current = snapshot.frames[frameIndex];
  if (!current) return <p>No retained frame selected.</p>;
  return <section aria-label="Frozen 128-coordinate interval">
    <p>{snapshot.frames.length} states · {snapshot.durationMs} ms observed · {snapshot.requestedSeconds} s requested · {snapshot.gaps.length} recorder gaps greater than 1000 ms</p>
    <p>128 node coordinates × retained frames (ordinal rows)</p>
    <svg className="geometry-map" viewBox={`0 0 128 ${snapshot.frames.length}`} preserveAspectRatio="none" role="img" aria-label={`Activation matrix, ${snapshot.frames.length} retained frames and 128 nodes; fixed minus one to plus one scale; selected values in exact table below`}>
      {snapshot.frames.flatMap((frame, row) => frame.activations.map((value, node) => <rect key={`${row}-${node}`} x={node} y={row} width="1" height="1" fill={value < 0 ? '#5ccee9' : '#ffb366'} opacity={Math.abs(value)} />))}
      <rect x="0" y={frameIndex} width="128" height="1" fill="none" stroke="#fff" strokeWidth=".05" />
    </svg><p className="geometry-scale"><span>−1 cyan · 0 black · +1 orange</span><span>No PCA, interpolation or inferred eigenvectors</span></p>
    <label className="geometry-slider">Recorded frame {frameIndex + 1} / {snapshot.frames.length}<input type="range" min="0" max={Math.max(0, snapshot.frames.length - 1)} step="1" value={frameIndex} disabled={snapshot.frames.length === 1} onChange={event => onSeek(Number(event.target.value))} aria-label="Geometry recorded frame" /></label>
    <dl className="geometry-clock"><dt>Engine clock (ms)</dt><dd>{current.tMs}</dd><dt>Wall clock (Unix ms)</dt><dd>{current.wallClockUnixMs}</dd><dt>UTC display</dt><dd>{geometryUtc(current.wallClockUnixMs)}</dd><dt>State RMS</dt><dd>{current.rms.toString()}</dd></dl>
    {snapshot.gaps.length > 0 && <p className="geometry-gap">Recorder gaps (engine ms): {snapshot.gaps.map(([a, b]) => `${a}…${b}`).join(', ')}. Rows represent retained samples; gaps are not interpolated.</p>}
    <label>Selected coordinate <select value={coordinate} aria-label="Geometry selected coordinate" onChange={event => onCoordinate(Number(event.target.value))}>{current.activations.map((_, index) => <option key={index} value={index}>{index}</option>)}</select></label><output className="geometry-coordinate" aria-live="polite">{current.activations[coordinate]?.toString()}</output>
    <details open={expanded} onToggle={event => onExpand(event.currentTarget.open)}><summary>Exact selected coordinates · 128 signed values</summary><div className="table-scroll"><table><caption>Frame {frameIndex + 1} · original signed coordinates, indexed 0 through 127</caption><thead><tr><th scope="col">Coordinate</th><th scope="col">Value</th></tr></thead><tbody>{current.activations.map((value, index) => <tr key={index} className={index === coordinate ? 'selected-row' : ''}><th scope="row"><button aria-label={`Select geometry coordinate ${index}`} onClick={() => onCoordinate(index)}>{index}</button></th><td>{value.toString()}</td></tr>)}</tbody></table></div></details>
    <details><summary>Capture provenance and exact frame clocks</summary><dl><dt>Source label</dt><dd><code>{snapshot.source}</code></dd><dt>Source SHA-256</dt><dd className="hash">{snapshot.sourceSha256}</dd><dt>Capture wall clock (Unix ms)</dt><dd>{snapshot.capturedAtUnixMs}</dd><dt>Declared scope</dt><dd>{snapshot.scope}</dd><dt>Identity limitation</dt><dd>{snapshot.identity}</dd></dl><p>The source path is a label and is never opened. Boot and node-layout identity remain unverified.</p><div className="table-scroll"><table><caption>All retained frame clocks · missing samples are not fabricated</caption><thead><tr><th>Frame</th><th>Engine ms</th><th>Unix ms</th><th>State RMS</th></tr></thead><tbody>{snapshot.frames.map((f, index) => <tr key={f.tMs}><th scope="row"><button onClick={() => onSeek(index)} aria-label={`Read geometry frame ${index + 1}`}>{index + 1}</button></th><td>{f.tMs}</td><td>{f.wallClockUnixMs}</td><td>{f.rms.toString()}</td></tr>)}</tbody></table></div></details>
  </section>;
}
export function GeometryProvenance({ packet }: { packet: GeometryPacket }) {
  return <footer className="geometry-provenance"><p>Observational coordinates only · boot and node-layout identity unverified · not a causal or felt-state test.</p><p>Integrity checked; producer authenticity and historical novelty are not established.</p><details><summary>File identity, verification and recorded limits</summary><dl><dt>Origin</dt><dd>{packet.origin === 'syntheticExample' ? 'Included synthetic example' : 'Opened local file; producer origin unverified'}</dd><dt>Format</dt><dd>question-geometry-v1</dd><dt>Original file SHA-256</dt><dd className="hash">{packet.sha256}</dd><dt>Nested body SHA-256</dt><dd className="hash">{packet.bodySha256}</dd><dt>Original size</dt><dd>{packet.sizeBytes} bytes</dd></dl><p>{packet.verificationScope}</p><h4>Recorded limits</h4><pre className="geometry-authored">{packet.limits}</pre><p>Export preserves the original file bytes. No model is contacted or source workspace changed.</p></details></footer>;
}
export function geometryUtc(value: string): string {
  try {
    const time = BigInt(value);
    if (time < 0n || time > 8_640_000_000_000_000n) return 'Outside the calendar display range; exact Unix milliseconds are retained above.';
    return new Date(Number(time)).toISOString();
  } catch { return 'Calendar display unavailable; exact clock text is retained above.'; }
}
