import { useEffect, useRef, useState } from 'react';
import { invoke, isTauri } from '@tauri-apps/api/core';
import type { SustainedConfig, SustainedSummary, SustainedActionReceipt } from './myReservoirTypes';
import { withSonar, validSonarView, type SonarView, type SonarMirror, type SonarReport } from './sonar';
import './sonar.css';
const num=(v:number)=>v===0?'0':Number(v.toPrecision(4)).toString();
export function SonarSetup({config,setConfig}:{config:SustainedConfig;setConfig:(c:SustainedConfig)=>void}) {
  return <section className="sonar-setup" aria-label="Response scanning setup">
    <label><input type="checkbox" checked={!!config.sonar} disabled={(config.differenceGain??0)!==0} onChange={e=>{
      setConfig(withSonar(config,e.target.checked));
    }}/>Allow the model to scan copies of its reservoir</label>
    <p>Scans measure signed responses across all 48 authored input coordinates. The saved result returns to later ordinary writing. The scan itself adds no numerical input. Selecting it sets a 512 MiB storage budget and, for local models, at least 32,768 context tokens; both remain editable in Advanced settings. Detailed scan checkpoints consume more storage, so the storage limit may end a run before its time limit.</p>
    {(config.differenceGain??0)!==0&&<p>Response scanning v1 requires the difference channel off.</p>}
    {config.sonar&&<><label><input type="checkbox" checked={config.sonar.allowLiveProbe} onChange={e=>setConfig({...config,sonar:{...config.sonar!,allowLiveProbe:e.target.checked}})}/>Also allow real probes along measured scan directions</label>
      <p>Real probes affect recurrence and the sensory field. Input L2 is at most 0.01; the additional immediate recurrent displacement is bounded by 0.05. This permission is fixed at creation. Ordinary PULSE, TUNE and authored PROBE retain their own existing bounds.</p></>}
  </section>;
}
export function MirrorView({mirror}:{mirror:SonarMirror}) {
  const pts=mirror.projectedHistory;const extent=Math.max(.000001,...pts.flatMap(p=>p.slice(0,2).map(Math.abs)));
  return <div className="sonar-mirror"><h4>Passive recurrent mirror</h4>
    <p>{mirror.sampleCount} saved state samples · steps {mirror.firstStep}–{mirror.lastStep}. Current RMS {num(mirror.currentRms)} · {mirror.currentBoundaryCoordinates} coordinates at ±1.</p>
    {mirror.principalAxes.length?<><svg viewBox="0 0 440 220" role="img" aria-label="Recent recurrent states projected onto their first two principal axes">
      <line x1="35" y1="100" x2="420" y2="100" stroke="#657186"/><line x1="225" y1="10" x2="225" y2="190" stroke="#657186"/>
      {pts.map((p,i)=><circle key={i} cx={225+p[0]/extent*180} cy={100-p[1]/extent*85} r={i===pts.length-1?4:2} fill={i===pts.length-1?'#ffba69':'#67d9d2'} opacity={.2+.8*(i+1)/pts.length}/>)}
      <text x="35" y="212">PC1 → · PC2 ↑ · shared extent ±{num(extent)}</text></svg>
      <p>These two axes explain {num((mirror.explainedShares[0]+mirror.explainedShares[1])*100)}% of this window’s variance. The axes change with the window; this projection is not a global topology map.</p></>:<p>No variance axes are available from this snapshot. Earlier sessions retain no scanner history; a single state does not define a trajectory.</p>}
    <p>The sensory field’s spectrum is a separate measurement. This view uses the recurrent states themselves.</p>
  </div>;
}
function Curves({positive,negative}:{positive:number[];negative:number[]}) {
  const top=Math.max(0,Math.ceil(Math.log10(Math.max(1,...positive,...negative))));
  const y=(v:number)=>15+(top-Math.log10(Math.max(1e-12,v)))/(top+12)*150;
  return <svg viewBox="0 0 440 205" role="img" aria-label="Signed copied response curves, recurrent L2 on a logarithmic scale, over 64 steps">
    {[top,-3,-6,-9,-12].map(e=><g key={e}><line x1="55" y1={y(10**e)} x2="425" y2={y(10**e)} stroke="#344153"/><text x="3" y={y(10**e)+4}>10^{e}</text></g>)}
    <polyline points={positive.map((v,i)=>`${55+i/63*370},${y(v)}`).join(' ')} stroke="#67d9d2" fill="none" strokeWidth="2"/>
    <polyline points={negative.map((v,i)=>`${55+i/63*370},${y(v)}`).join(' ')} stroke="#ffba69" fill="none" strokeWidth="2" strokeDasharray="5 3"/>
    <text x="55" y="191">1</text><text x="200" y="191">Steps after impulse</text><text x="410" y="191">64</text>
  </svg>;
}
export function ScanView({report,label}:{report:SonarReport;label:string}) {
  const max=Math.max(1e-12,...report.immediateResponseMatrix.flat().map(Math.abs));
  return <section className="sonar-report"><h4>{label} · origin step {report.origin.step}</h4>
    <p>96 signed coordinate experiments on copies · input L2 {report.epsilon} · 64 steps. Held text, controls, forcing and copied noise are shared. Future writing, actions and sensory evolution are not simulated.</p>
    <p className="sonar-id">Scan {report.id}</p>
    <h5>Immediate input response · 32 states × 48 input slots</h5>
    <svg viewBox="0 0 530 365" role="img" aria-label="Signed central-difference response matrix, rows recurrent coordinates and columns input coordinates">
      {report.immediateResponseMatrix.map((row,r)=>row.map((v,c)=><rect key={`${r}-${c}`} x={40+c*10} y={15+r*10} width="9" height="9" fill={v>=0?'#ffba69':'#67d9d2'} opacity={.06+.94*Math.abs(v)/max}><title>{`State ${r}, input ${c}: ${num(v)}`}</title></rect>))}
      <text x="3" y="25">0</text><text x="3" y="332">31</text><text x="40" y="355">Input 0 → 47 · orange positive / teal negative</text>
    </svg>
    <p>Central finite difference per unit input; color maximum ±{num(max)}. Coordinate indices are numerical channels, not spatial regions.</p>
    <div className="sonar-candidates">{report.candidates.map(c=><article key={c.direction}><h5>{c.direction}</h5><Curves positive={c.positiveResponseL2} negative={c.negativeResponseL2}/>
      <p>Teal + / dashed orange −. First response {num(c.positiveResponseL2[0])} / {num(c.negativeResponseL2[0])}. Return step {c.positiveReturnStep??'unresolved'} / {c.negativeReturnStep??'unresolved'}.</p></article>)}</div>
    <p>Curves show recurrent L2 differences from the paired baseline. Values below 10⁻¹² are drawn at the floor. Return requires five consecutive boundaries below 10% of the first response. “Persistent” selects the strongest resolved response at step 16; it does not establish enduring memory.</p>
    <p>At these controls, real probe input cap {num(report.maximumLiveInputL2)}; immediate additional recurrent bound {report.maximumLiveStateL2}. A later real probe recalculates its dose and forecast.</p>
  </section>;
}
export function SonarReceiptView({receipt}:{receipt:SustainedActionReceipt}) {
  return <>{receipt.sonarScan&&<p>Copied scan saved at step {receipt.sonarScan.step}. Its own additional numerical effect is zero; the entry’s text-input choice still applies. Scan <span className="sonar-id">{receipt.sonarScan.id}</span>.</p>}
    {receipt.sonarProbe&&<><p>Measured direction from scan step {receipt.sonarProbe.sourceScan?.step??'unavailable'}. {receipt.sonarProbe.rejection?'No probe applied.':`Fresh first-step forecast ${num(receipt.sonarProbe.forecastResponseL2[0])}; observed paired effect ${num(receipt.stateDeltaL2)}; bound ${receipt.sonarProbe.maximumStateL2}.`}</p>
    {!receipt.sonarProbe.rejection&&<p>Later forecast points assume held text and controls remain fixed; they are not observed live consequences. The real impulse also enters the sensory field.</p>}
    <details><summary>Exact scan probe receipt</summary><pre>{JSON.stringify(receipt.sonarProbe,null,2)}</pre></details></>}
  </>;
}
export default function MyReservoirSonar({summary}:{summary:SustainedSummary}) {
  const [view,setView]=useState<SonarView|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const ticket=useRef(0);
  useEffect(()=>{ticket.current++;setView(null);setBusy(false);setError('');return()=>{ticket.current++;};},[summary.sessionId,summary.generation]);
  async function observe(scan:boolean) {
    const current=++ticket.current;setBusy(true);setError('');
    try {if(!isTauri())throw new Error('Open the native app to inspect a saved numerical state.');
      const next=await invoke<unknown>('observe_sustained_sonar',{sessionId:summary.sessionId,generation:summary.generation,scan});
      if(!validSonarView(next,summary.sessionId,summary.generation))throw new Error('The scanner returned an invalid or mismatched observation.');
      if(current===ticket.current)setView(next);
    }catch(e){if(current===ticket.current)setError(e instanceof Error?e.message:String(e));}
    finally{if(current===ticket.current)setBusy(false);}
  }
  return <details className="my-reservoir-details sonar-panel"><summary>Reservoir response scanner</summary>
    <p>Inspect the committed numerical state or experiment on a copy. Operator observations stay outside model prompts and do not replace the model’s cached scan.</p>
    <div className="sonar-buttons"><button disabled={busy} onClick={()=>void observe(false)}>Observe saved state</button><button disabled={busy||(summary.config.differenceGain??0)!==0} onClick={()=>void observe(true)}>Scan a copy</button></div>
    {busy&&<p role="status">Computing from a copied committed checkpoint…</p>}{error&&<p role="alert">{error}</p>}
    {(summary.config.differenceGain??0)!==0&&<p>Copied response scans require the difference channel off; passive observation remains available.</p>}
    {view&&<><p>Snapshot at step {view.step}; current committed step {summary.durableStep}. Refresh explicitly for a newer observation.</p><MirrorView mirror={view.mirror}/>
      {view.operatorScan&&<ScanView report={view.operatorScan} label="Operator scan · not supplied to the model"/>}
      {view.modelScan&&<ScanView report={view.modelScan} label="Model-selected cached scan"/>}
      <details><summary>Exact observation and provenance</summary><pre>{JSON.stringify(view,null,2)}</pre></details></>}
  </details>;
}
