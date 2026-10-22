import { useLayoutEffect, useRef, useState } from 'react';
import { version as appVersion } from '../package.json';
import RecordedExperiments from './RecordedExperiments';
import GuidedTour from './GuidedTour';
import CasesWorkspace from './CasesWorkspace';
import GeometryWorkspace from './GeometryWorkspace';
import LibraryView from './LibraryView';
import FreshExperiments, { FreshClosePanel } from './FreshExperiments';
import type { RecordOpenRequest } from './types';
import ObservatoryWorkspace, { type ObservatoryView } from './ObservatoryWorkspace';
import MyReservoir, { SustainedClosePanel } from './MyReservoir';
import DesktopDiagnostics from './DesktopDiagnostics';

const workspaces = ['My reservoir', 'Guided tour', 'Experiments', 'Research cases', 'Geometry bookmarks', 'Observatory'] as const;
type Workspace = typeof workspaces[number];

export default function App() {
  const exampleSequence = useRef(0);
  const [openRequest,setOpenRequest]=useState<RecordOpenRequest|null>(null);
  const [experimentView,setExperimentView]=useState<'library'|'recording'|'fresh'>('library');
  const [workspace, setWorkspace] = useState<Workspace>('My reservoir');
  const [aboutOpen, setAboutOpen] = useState(false);
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);
  const [observatoryView, setObservatoryView] = useState<ObservatoryView>('recordings');
  const main = useRef<HTMLElement>(null);
  const focusOnArrival = useRef(false);
  const scrollPositions = useRef<Record<string, number>>({});
  const viewKey = workspace === 'Experiments' ? `${workspace}:${experimentView}`
    : workspace === 'Observatory' ? `${workspace}:${observatoryView}` : workspace;
  useLayoutEffect(() => {
    window.scrollTo(0, scrollPositions.current[viewKey] ?? 0);
    if (focusOnArrival.current) { main.current?.focus({ preventScroll: true }); focusOnArrival.current = false; }
  }, [viewKey, openRequest]);
  const rememberPosition = () => { scrollPositions.current[viewKey] = window.scrollY; };
  const navigate = (next: Workspace, focus = false) => {
    rememberPosition(); focusOnArrival.current = focus; setWorkspace(next);
  };
  const showExperiments = (next: 'library' | 'recording' | 'fresh', focus = false) => {
    rememberPosition(); focusOnArrival.current = focus; setExperimentView(next); setWorkspace('Experiments');
  };
  const showObservatory = (next: ObservatoryView, focus = false) => {
    rememberPosition(); focusOnArrival.current = focus; setObservatoryView(next); setWorkspace('Observatory');
  };
  const openRecording = (request: RecordOpenRequest) => {
    rememberPosition(); scrollPositions.current['Experiments:recording'] = 0;
    focusOnArrival.current = true; setOpenRequest(request); setExperimentView('recording'); setWorkspace('Experiments');
  };
  const openExample = (exampleId: string) => openRecording({ id: `explicit-example-${++exampleSequence.current}`, exampleId });
  return <div className="app-shell">
    <a className="skip-link" href="#workspace-main">Skip to workspace</a>
    <header className="app-header">
      <div className="brand"><span className="brand-mark" aria-hidden="true">◉</span><div><strong>Reservoir Scope</strong></div></div>
      <button aria-expanded={aboutOpen} aria-controls="app-information" onClick={()=>{setAboutOpen(!aboutOpen);setDiagnosticsOpen(false)}}>About this app</button>
    </header>
    {aboutOpen&&<section id="app-information" className="app-information" aria-labelledby="app-information-title">
      <h2 id="app-information-title">About Reservoir Scope</h2>
      <p>Version {appVersion} · Explore recordings, run experiments and keep a personal reservoir journal.</p>
      <p>This app has its own storage, separate from the earlier native macOS app. Windows and Linux remain qualification targets; checks on one platform do not qualify another.</p>
      <details onToggle={event=>setDiagnosticsOpen(event.currentTarget.open)}><summary>Technical checks and app details</summary>{diagnosticsOpen&&<DesktopDiagnostics/>}</details>
    </section>}
    <nav className="workspace-nav" aria-label="Workspaces">{workspaces.map(name => <button key={name} aria-current={workspace === name ? 'page' : undefined} onClick={() => navigate(name)}>{name}</button>)}</nav>
    <FreshClosePanel /><SustainedClosePanel />
    <main id="workspace-main" ref={main} tabIndex={-1}>
      <GuidedTour active={workspace === 'Guided tour'} onOpenExample={openExample} />
      <CasesWorkspace active={workspace === 'Research cases'} />
      <GeometryWorkspace active={workspace === 'Geometry bookmarks'} />
      <ObservatoryWorkspace active={workspace === 'Observatory'} view={observatoryView} onView={showObservatory} onOpenExample={openExample} onMyReservoir={() => navigate('My reservoir', true)} onNewExperiment={() => showExperiments('fresh', true)} />
      {workspace === 'Experiments' && <nav className="experiment-tabs" aria-label="Experiment views"><button aria-current={experimentView==='library'?'page':undefined} onClick={()=>showExperiments('library')}>Library</button><button aria-current={experimentView==='recording'?'page':undefined} onClick={()=>showExperiments('recording')}>Recording</button><button aria-current={experimentView==='fresh'?'page':undefined} onClick={()=>showExperiments('fresh')}>New experiment</button></nav>}
      <LibraryView onPreparationHistory={() => showObservatory('preparation', true)} active={workspace === 'Experiments' && experimentView==='library'} onOpen={result => { if (result.record) openRecording({ id: result.requestId, record: result.record }); }} />
      <MyReservoir active={workspace === 'My reservoir'} />
      <FreshExperiments active={workspace === 'Experiments' && experimentView==='fresh'} onViewLibrary={() => showExperiments('library')} />
      <RecordedExperiments active={workspace === 'Experiments' && experimentView==='recording'} openRequest={openRequest} />
    </main>
  </div>;
}

