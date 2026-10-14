import { useLayoutEffect, useRef, useState } from 'react';
import { version as previewVersion } from '../package.json';
import RecordedExperiments from './RecordedExperiments';
import GuidedTour from './GuidedTour';
import CasesWorkspace from './CasesWorkspace';
import GeometryWorkspace from './GeometryWorkspace';
import LibraryView from './LibraryView';
import FreshExperiments, { FreshClosePanel } from './FreshExperiments';
import type { RecordOpenRequest } from './types';
import ObservatoryWorkspace from './ObservatoryWorkspace';
import MyReservoir, { SustainedClosePanel } from './MyReservoir';

const workspaces = ['Guided tour', 'Experiments', 'Research cases', 'Geometry bookmarks', 'Observatory'] as const;
type Workspace = typeof workspaces[number];

export default function App() {
  const exampleSequence = useRef(0);
  const [openRequest,setOpenRequest]=useState<RecordOpenRequest|null>(null);
  const [experimentView,setExperimentView]=useState<'library'|'recording'|'fresh'|'sustained'>('library');
  const [workspace, setWorkspace] = useState<Workspace>('Guided tour');
  const scrollPositions=useRef<Record<string,number>>({});
  const viewKey=workspace==='Experiments'?`${workspace}:${experimentView}`:workspace;
  useLayoutEffect(()=>{window.scrollTo(0,scrollPositions.current[viewKey]??0)},[viewKey]);
  const navigate=(next:Workspace)=>{scrollPositions.current[viewKey]=window.scrollY;setWorkspace(next)};
  const showExperiments=(next:'library'|'recording'|'fresh'|'sustained')=>{scrollPositions.current[viewKey]=window.scrollY;setExperimentView(next)};
  const openExample=(exampleId:string)=>{scrollPositions.current[viewKey]=window.scrollY;scrollPositions.current['Experiments:recording']=0;setOpenRequest({id:`explicit-example-${++exampleSequence.current}`,exampleId});setExperimentView('recording');setWorkspace('Experiments')};
  return <div className="app-shell">
    <a className="skip-link" href="#workspace-main">Skip to workspace</a>
    <header className="app-header">
      <div className="brand"><span className="brand-mark" aria-hidden="true">◉</span><div><strong>Reservoir Scope</strong><span>THE CROSS-PLATFORM LAB</span></div></div>
      <span className="milestone-pill"><span /> {previewVersion} · My reservoir</span>
    </header>
    <nav className="workspace-nav" aria-label="Workspaces">{workspaces.map(name => <button key={name} aria-current={workspace === name ? 'page' : undefined} onClick={() => navigate(name)}>{name}</button>)}</nav>
    <FreshClosePanel /><SustainedClosePanel />
    <main id="workspace-main">
      <GuidedTour active={workspace === 'Guided tour'} onOpenExample={openExample} />
      <CasesWorkspace active={workspace === 'Research cases'} />
      <GeometryWorkspace active={workspace === 'Geometry bookmarks'} />
      <ObservatoryWorkspace active={workspace === 'Observatory'} onOpenExample={openExample} />
      {workspace === 'Experiments' && <nav className="experiment-tabs" aria-label="Experiment views"><button aria-current={experimentView==='library'?'page':undefined} onClick={()=>showExperiments('library')}>Library</button><button aria-current={experimentView==='recording'?'page':undefined} onClick={()=>showExperiments('recording')}>Recording reader</button><button aria-current={experimentView==='sustained'?'page':undefined} onClick={()=>showExperiments('sustained')}>My reservoir</button><button aria-current={experimentView==='fresh'?'page':undefined} onClick={()=>showExperiments('fresh')}>Fresh experiments</button></nav>}
      <LibraryView onOpenExample={openExample} active={workspace === 'Experiments' && experimentView==='library'} onOpen={result=>{if(result.record){setOpenRequest({id:result.requestId,record:result.record});scrollPositions.current['Experiments:recording']=0;showExperiments('recording')}}} />
      <MyReservoir active={workspace === 'Experiments' && experimentView==='sustained'} />
      <FreshExperiments active={workspace === 'Experiments' && experimentView==='fresh'} onViewLibrary={() => showExperiments('library')} />
      <RecordedExperiments active={workspace === 'Experiments' && experimentView==='recording'} openRequest={openRequest} />
    </main>
    <footer><span><i /> Offline evidence · explicit local-model connections</span><span>macOS · Windows · Linux <span className="muted">/ target platforms; qualification tracked separately</span></span></footer>
  </div>;
}

