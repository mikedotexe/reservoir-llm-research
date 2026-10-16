import RecordedObservatory from './RecordedObservatory';
import ResponseWorkspace from './ResponseWorkspace';
import PreparationHistory from './PreparationHistory';
import './observatory.css';

export { timelineSegments } from './RecordedObservatory';
export type ObservatoryView = 'recordings' | 'responses' | 'preparation';
export default function ObservatoryWorkspace({ active, view = 'recordings', onView, onOpenExample, onMyReservoir, onNewExperiment }: {
  active: boolean; view?: ObservatoryView; onView?: (view: ObservatoryView) => void;
  onOpenExample?: (id: string) => void; onMyReservoir?: () => void; onNewExperiment?: () => void;
}) {
  return <section className="observatory-workspace" hidden={!active} aria-labelledby="observatory-title">
    {active&&<><div className="workspace-intro"><h1 id="observatory-title">Observatory</h1><p>Explore two independent recordings of fill and state, and recorded action responses. Each recording keeps its own source, clock and measurement limits.</p></div>
    <nav className="experiment-tabs" aria-label="Observatory views">
      <button aria-current={view==='recordings'?'page':undefined} onClick={()=>onView?.('recordings')}>Fill &amp; state</button>
      <button aria-current={view==='responses'?'page':undefined} onClick={()=>onView?.('responses')}>Action responses</button>
      <button aria-current={view==='preparation'?'page':undefined} onClick={()=>onView?.('preparation')}>Preparation history</button>
    </nav></>}
    <RecordedObservatory active={active&&view==='recordings'}/>
    <ResponseWorkspace active={active&&view==='responses'}/>
    <PreparationHistory initiallyOpen active={active&&view==='preparation'} onOpenExample={onOpenExample}/>
    {active && (onMyReservoir || onNewExperiment) && <section className="observatory-scope"><h2>Try your own reservoir</h2><p>Keep a personal journal or explore a finite experiment.</p><div className="experiment-tabs">{onMyReservoir && <button onClick={onMyReservoir}>Go to My reservoir</button>}{onNewExperiment && <button onClick={onNewExperiment}>Set up a new experiment</button>}</div></section>}
  </section>;
}
