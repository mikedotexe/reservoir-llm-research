import { useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import { ObservatoryController } from './observatoryController';
import { observatoryApi } from './observatoryApi';
import RecordedFillSphere from './RecordedFillSphere';
import SurfaceView from './SurfaceView';
import CoordinateInspector from './CoordinateInspector';
import { DEFAULT_CAMERA, type ReferenceScene } from './types';
import type { ObservatoryTimelinePoint } from './observatoryTypes';
import './observatory.css';

export function timelineSegments(points:ObservatoryTimelinePoint[],value:(point:ObservatoryTimelinePoint)=>number|null):[number,number][][]{
  const segments:[number,number][][]=[];let current:[number,number][]=[];
  for(const point of points){const y=value(point);if(point.breakBefore||y===null||!Number.isFinite(y)){if(current.length)segments.push(current);current=[]}if(y!==null&&Number.isFinite(y))current.push([point.position,y]);}
  if(current.length)segments.push(current);return segments;
}
function TimelinePlot({points,value,range,title,position,axis}:{points:ObservatoryTimelinePoint[];value:(point:ObservatoryTimelinePoint)=>number|null;range:[number,number];title:string;position:number;axis:string}){
  const first=points[0]?.position??0,last=points.at(-1)?.position??1;
  const x=(v:number)=>48+((v-first)/Math.max(1e-12,last-first))*688;
  const y=(v:number)=>142-((v-range[0])/Math.max(1e-12,range[1]-range[0]))*116;
  const segments=timelineSegments(points,value);
  return <figure className="observatory-plot"><figcaption>{title}</figcaption><svg viewBox="0 0 760 184" role="img" aria-label={`${title}. Fixed vertical range ${range[0]} to ${range[1]}. Horizontal axis: ${axis}. Missing values and session boundaries break the line.`}>
    <line x1="48" y1="142" x2="736" y2="142" className="plot-grid"/><line x1="48" y1="26" x2="736" y2="26" className="plot-grid"/>
    {range[0]<0&&range[1]>0&&<line x1="48" y1={y(0)} x2="736" y2={y(0)} className="plot-zero"/>}
    <text x="3" y="31">{range[1].toPrecision(3)}</text><text x="3" y="147">{range[0].toPrecision(3)}</text>
    {segments.map((segment,i)=>segment.length===1?<circle key={i} cx={x(segment[0][0])} cy={y(segment[0][1])} r="2" className="plot-dot"/>:<polyline key={i} points={segment.map(([a,b])=>`${x(a)},${y(b)}`).join(' ')} className="plot-trace"/>)}
    <line x1={x(position)} y1="22" x2={x(position)} y2="146" className="plot-cursor"/>
    <text x="48" y="170">{first.toFixed(2)}</text><text x="736" y="170" textAnchor="end">{last.toFixed(2)} · {axis}</text>
  </svg><p>All {points.length} retained rows · gaps between sessions are not connected. Exact selected values appear below.</p></figure>;
}
const shown=(value:number|null|undefined)=>value===null||value===undefined?'Unavailable':String(value);
export default function RecordedObservatory({active}:{active:boolean}){
  const [controller]=useState(()=>new ObservatoryController(observatoryApi));
  const state=useSyncExternalStore(controller.subscribe,controller.snapshot,controller.snapshot);
  const [tableOnly,setTableOnly]=useState(false),[pose,setPose]=useState({...DEFAULT_CAMERA});
  useEffect(()=>()=>{void controller.close()},[controller]);
  useEffect(()=>{if(!active)controller.pause()},[active,controller]);
  useEffect(()=>{const hide=()=>{if(document.hidden)controller.pause()};document.addEventListener('visibilitychange',hide);return()=>document.removeEventListener('visibilitychange',hide)},[controller]);
  useEffect(()=>{
    if(!active||!state.playing)return;
    let stopped=false,timer:ReturnType<typeof setTimeout>;
    const tick=async()=>{await controller.tick(performance.now());if(!stopped)timer=setTimeout(()=>{void tick()},100)};
    timer=setTimeout(()=>{void tick()},100);return()=>{stopped=true;clearTimeout(timer)};
  },[active,controller,state.playing]);
  const track=state.summary?.tracks.find(item=>item.id===state.trackId),frame=state.frame,history=frame?.history,recordedState=frame?.state;
  const reference=useMemo<ReferenceScene|null>(()=>recordedState?{id:'observatory-state-replay',title:'Recorded reservoir state',nodeCount:128,values:recordedState.activations,description:'Fixed coordinate-index atlas. These positions do not represent measured physical or neural locations.',provenance:recordedState.sourceIdentity}:null,[recordedState]);
  const fillSample=useMemo(()=>history?{fillPercent:history.fillPct,provenance:'Bundled data.json · historical Minime reservoir telemetry',sourceTimeLabel:`${history.tUtc} · elapsed ${history.tSeconds} s · session ${history.sessionId}`}:null,[history]);
  const bands=track?.bands;
  const references=useMemo(()=>bands?{shelfMinPercent:bands.shelfMinPct,targetPercent:bands.targetPct,shelfMaxPercent:bands.shelfMaxPct,strongRailPercent:bands.strongRailPct,warningRailPercent:bands.forceRailPct,provenance:[bands.status,bands.note].filter(Boolean).join(' ')}:null,[bands]);
  const cascadeMax=state.points.reduce((max,point)=>(point.cascade??[]).reduce((m,v)=>Math.max(m,v),max),1);
  const rateExtent=state.points.reduce((max,point)=>Math.max(max,Math.abs(point.fillRatePctPerS??0)),0.001);
  if(!active)return null;
  return <section className="observatory-recordings" aria-label="Fill and state recordings">
    <div className="button-row"><button className="primary" disabled={state.opening} onClick={()=>void controller.open()}>{state.opening?'Opening recordings…':state.summary?'Reload bundled recordings':'Open bundled recordings'}</button>{state.summary&&<button onClick={()=>void controller.close()}>Close recordings</button>}<label className="observatory-checkbox"><input type="checkbox" checked={tableOnly} onChange={event=>setTableOnly(event.target.checked)}/>Exact values without 3D</label></div>
    {state.message&&<p className="reader-message" role="status">{state.message}</p>}
    {state.summary?.diagnostics.map((item,i)=><p role="alert" className="observatory-warning" key={i}>{item.trackId}: {item.category} — {item.message}</p>)}
    {!state.summary&&<div className="observatory-welcome"><h2>Two windows into recorded dynamics</h2><div><article><span>01 / FILL HISTORY</span><h3>A volume that breathes with the recorded fill</h3><p>507 clocked samples, reference zones, retained fill-rate differences and three sensory direction estimates.</p></article><article><span>02 / STATE REPLAY</span><h3>A surface with 128 exact coordinates</h3><p>1,024 activation rows, coordinate inspection and retained projection metrics. Row order is known; per-row timestamps and paired fill are unavailable.</p></article></div><p>Opening checks bundled hashes and record structure locally. It does not contact a Being, start an experiment or connect a model.</p></div>}
    {state.summary&&<nav className="experiment-tabs" aria-label="Independent Observatory recordings">{state.summary.tracks.map(item=><button key={item.id} aria-current={item.id===state.trackId?'page':undefined} onClick={()=>void controller.selectTrack(item.id)}>{item.id==='history'?'Fill history · recorded time':'128-node replay · row order'}</button>)}</nav>}
    {track&&<>
      <div className="observatory-track-heading"><div><span className="eyebrow">{track.axis==='elapsedSeconds'?'RECORDED CLOCK':'ORDINAL PLAYBACK · NO ROW TIMESTAMPS'}</span><h2>{track.title}</h2></div><span className="subtle-tag">{track.frameCount} retained rows</span></div>
      <p className="observatory-warning">{track.id==='history'?'The clocked fill history has no retained 128-coordinate state vectors. The separate state replay is not synchronized with this recording.':'The state replay has no paired fill measurements or per-row timestamps. Playback speed is an inspection choice, not a measured rate.'}</p>
      <div className="observatory-transport" aria-label="Recorded playback controls"><button disabled={!frame||frame.index===0} onClick={()=>void controller.frame((frame?.index??0)-1)}>Previous row</button><button disabled={!frame||(!state.playing&&frame.index>=track.frameCount-1)} onClick={()=>state.playing?controller.pause():controller.play(performance.now())}>{state.playing?'Pause':'Play'}</button><button disabled={!frame||frame.index>=track.frameCount-1} onClick={()=>void controller.frame((frame?.index??0)+1)}>Next row</button><label>Row <input aria-label="Recorded row index" type="number" min="0" max={track.frameCount-1} value={frame?.index??0} onChange={event=>void controller.frame(event.target.valueAsNumber)}/></label><label>{track.id==='history'?'Clock speed':'Rows / second'} <select aria-label="Playback speed" value={state.rate} onChange={event=>controller.setRate(Number(event.target.value))}>{[0.5,1,2,4,8,16,32].map(rate=><option key={rate} value={rate}>{rate}{track.id==='history'?'×':''}</option>)}</select></label><output>{state.loading?'Reading…':frame?`Row ${frame.index} of ${track.frameCount-1}`:'No selected row'}</output></div>
      <label className="observatory-scrubber">{track.axis==='elapsedSeconds'?'Elapsed recorded seconds · nearest retained sample':'Recorded ordinal · no interpolation'}<input aria-label="Recorded position" type="range" min={track.firstPosition} max={track.lastPosition} step={track.axis==='elapsedSeconds'?0.001:1} value={frame?.position??track.firstPosition} onChange={event=>void controller.seek(event.target.valueAsNumber)}/></label>
      {history&&<div className="observatory-evidence-grid"><RecordedFillSphere sample={fillSample} references={references} tableOnly={tableOnly}/><section className="observatory-measurements"><h3>At this recorded boundary</h3><dl><div><dt>UTC label · approximate</dt><dd>{history.tUtc}</dd></div><div><dt>Elapsed recorded seconds</dt><dd>{shown(history.tSeconds)}</dd></div><div><dt>Session identity</dt><dd>{history.sessionId}</dd></div><div><dt>Interval from previous row</dt><dd>{shown(history.intervalSeconds)}{history.intervalSeconds===null?'':' s'}</dd></div><div><dt>Retained backward fill difference</dt><dd>{shown(history.fillRatePctPerS)}{history.fillRatePctPerS===null?'':' percentage points / s'}</dd></div><div><dt>ESN-state covariance λ1 · separate quantity</dt><dd>{shown(history.esnCovLambda1)}</dd></div><div><dt>State RMS radius</dt><dd>{shown(history.geomRadius)}</dd></div><div><dt>Relative geometry radius</dt><dd>{shown(history.geomRel)}</dd></div><div><dt>ESN leak</dt><dd>{shown(history.esnLeak)}</dd></div><div><dt>RLS forgetting coefficient</dt><dd>{shown(history.esnLambda)}</dd></div></dl><h3>Retained sensory directions</h3><p>Three Rayleigh estimates in stored order. These are not certified leading eigenvalues or a complete spectrum; no eigenvectors are retained.</p><ol className="observatory-directions">{history.cascade.map((value,index)=><li key={index}><span>Direction slot {index+1}</span>{state.points.length===track.frameCount&&<meter min="0" max={cascadeMax} value={value}/>}<code>{String(value)}</code></li>)}</ol><p>{state.points.length===track.frameCount?`Direction bars use a shared zero-based scale across the whole retained history: 0 to ${cascadeMax}.`:"Direction bars await complete timeline coverage; exact selected values remain available."} Fill is a rank-derived statistic, not a fraction of occupied neurons or memory.</p></section></div>}
      {reference&&recordedState&&<><div className="observatory-state-note"><p>The surface is a fixed coordinate-index atlas of signed reservoir activations. Its shape is a display projection, not measured anatomy, a covariance ellipsoid or the full phase space.</p><dl><div><dt>State RMS</dt><dd>{shown(recordedState.stateRms)}</dd></div><div><dt>Centered RMS</dt><dd>{shown(recordedState.centeredRms)}</dd></div><div><dt>Projected RMS</dt><dd>{shown(recordedState.projectedRms)}</dd></div><div><dt>Reconstruction RMSE</dt><dd>{shown(recordedState.reconstructionRmse)}</dd></div></dl><p>Retained projection coordinates: {recordedState.pc.map(shown).join(' · ')}. These summarize the captured trajectory; they do not supply a clock or fill measurement.</p></div><SurfaceView evidenceLabel="Retained state row" reference={reference} selected={state.node} onSelect={node=>void controller.selectNode(node)} pose={pose} onPose={setPose} tableOnly={tableOnly}/><CoordinateInspector reference={reference} selected={state.node} onSelect={node=>void controller.selectNode(node)}/></>}
      {state.loadingTimeline?<p role="status">Reading bounded timeline pages…</p>:state.points.length>0&&<div className="observatory-plots">{track.id==='history'?<><TimelinePlot title="Retained fill percentage" points={state.points} value={point=>point.fillPct} range={[0,100]} position={frame?.position??0} axis="elapsed seconds"/><TimelinePlot title="Backward fill difference · percentage points / second" points={state.points} value={point=>point.fillRatePctPerS} range={[-rateExtent,rateExtent]} position={frame?.position??0} axis="elapsed seconds"/></>:<TimelinePlot title={`Coordinate ${state.node} · signed activation`} points={state.points} value={point=>point.nodeValue} range={[-1,1]} position={frame?.position??0} axis="row order"/>}</div>}
      <details className="observatory-provenance"><summary>Recording provenance, limits and definitions</summary><p>Bundled hashes and format structure are checked when opened. No historical dynamics are rerun here.</p>{track.provenance.map((text,i)=><p key={`p${i}`}>{text}</p>)}{track.missingness.map((text,i)=><p key={`m${i}`}>{text}</p>)}{track.capturedAtUtc&&<p>Capture metadata: {track.capturedAtUtc}. This is not a timestamp for each state row.</p>}<dl>{Object.entries(track.definitions).map(([key,value])=><div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl><h3>Original resource identities</h3>{track.identities.map(item=><p key={item.name}><strong>{item.name}</strong><br/><code>{item.sha256}</code></p>)}</details>
    </>}

  </section>;
}
