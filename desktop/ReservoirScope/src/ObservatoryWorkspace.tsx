import { useState } from 'react';
import RecordedObservatory from './RecordedObservatory';
import ResponseWorkspace from './ResponseWorkspace';
import PreparationHistory from './PreparationHistory';
import DesktopDiagnostics from './DesktopDiagnostics';
import './observatory.css';

export { timelineSegments } from './RecordedObservatory';
type View = 'recordings' | 'responses' | 'preparation';
export default function ObservatoryWorkspace({active,onOpenExample}:{active:boolean;onOpenExample?:(id:string)=>void}) {
  const [view,setView]=useState<View>('recordings');
  const [diagnostics,setDiagnostics]=useState(false);
  return <section className="observatory-workspace" hidden={!active} aria-labelledby="observatory-title">
    {active&&<><div className="workspace-intro"><span className="eyebrow">OBSERVATORY / RECORDED EVIDENCE</span><h1 id="observatory-title">Watch the reservoir change.</h1><p>Explore two independent recordings of fill and state, inspect an action’s immediate effect, and follow a separate simulation’s response. Each keeps its own source, clock and measurement limits.</p></div>
    <nav className="experiment-tabs" aria-label="Observatory views">
      <button aria-current={view==='recordings'?'page':undefined} onClick={()=>setView('recordings')}>Fill &amp; state</button>
      <button aria-current={view==='responses'?'page':undefined} onClick={()=>setView('responses')}>Action responses</button>
      <button aria-current={view==='preparation'?'page':undefined} onClick={()=>setView('preparation')}>Preparation history</button>
    </nav></>}
    <RecordedObservatory active={active&&view==='recordings'}/>
    <ResponseWorkspace active={active&&view==='responses'}/>
    <PreparationHistory initiallyOpen active={active&&view==='preparation'} onOpenExample={onOpenExample}/>
    {active&&<section className="observatory-scope"><h2>Run your own reservoir</h2><p>These views inspect retained evidence. Open Experiments → My reservoir to create a bounded session with scripted writing or an explicitly selected local model. It can keep writing and applying saved journals while the app is open or minimized. Fresh experiments offers separate finite recipes.</p><button onClick={()=>setDiagnostics(!diagnostics)}>{diagnostics?'Hide':'Show'} desktop diagnostics and reference scenes</button>{diagnostics&&<DesktopDiagnostics/>}</section>}
  </section>;
}
