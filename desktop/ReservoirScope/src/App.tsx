import ResearchWorkspace from './ResearchWorkspace';
import { invoke, isTauri } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { useEffect, useLayoutEffect, useRef, useState } from 'react';
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
import StudyWalkthrough from './StudyWalkthrough';

const workspaces = ['Study', 'Research runs', 'My reservoir', 'Guided tour', 'Experiments', 'Research cases', 'Geometry bookmarks', 'Observatory'] as const;
type Workspace = typeof workspaces[number];

export default function App() {
  const [researchClosing, setResearchClosing] = useState(false);
  const [researchRoute, setResearchRoute] = useState<string | null>(null);
  const [researchRouteRequest, setResearchRouteRequest] = useState(0);
  useEffect(() => {
    if (!isTauri()) return;
    let disposed = false; const handlers: (() => void)[] = [];
    const route = (value: string) => { if (!disposed) { setResearchRoute(value); setResearchRouteRequest(n => n + 1); setWorkspace('Research runs'); } };
    void listen<string>('research-deep-link', e => route(e.payload)).then(async unlisten => {
      if (disposed) { unlisten(); return; }
      handlers.push(unlisten);
      const value = await invoke<string | null>('research_deep_link');
      if (value) route(value);
    }).catch(error => console.error('Research navigation initialization failed', error));
    void listen('research-close-requested', () => { setResearchClosing(true); route('/v1/runs'); }).then(unlisten => disposed ? unlisten() : handlers.push(unlisten));
    return () => { disposed = true; handlers.forEach(unlisten => unlisten()); };
  }, []);
  const exampleSequence = useRef(0);
  const [openRequest,setOpenRequest]=useState<RecordOpenRequest|null>(null);
  const [experimentView,setExperimentView]=useState<'library'|'recording'|'fresh'>('library');
  const [workspace, setWorkspace] = useState<Workspace>('Study');
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
      <nav className="workspace-nav" aria-label="Workspaces">{workspaces.map(name => <button key={name} aria-current={workspace === name ? 'page' : undefined} onClick={() => navigate(name)}>{name}</button>)}</nav>
    </header>
    <FreshClosePanel /><SustainedClosePanel />
    <main id="workspace-main" ref={main} tabIndex={-1}>
      <ResearchWorkspace active={workspace === 'Research runs'} route={researchRoute} routeRequest={researchRouteRequest} closing={researchClosing} onKeepOpen={() => { void invoke("cancel_sustained_close").then(() => setResearchClosing(false)); }} />
      <StudyWalkthrough active={workspace === 'Study'} />
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
    <details className="app-technical-details" onToggle={event => setDiagnosticsOpen(event.currentTarget.open)}><summary>Technical checks and app details</summary>{diagnosticsOpen && <DesktopDiagnostics/>}</details>
  </div>;
}

