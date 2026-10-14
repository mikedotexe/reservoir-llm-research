import { useState, useSyncExternalStore } from 'react';
import { CasesController } from './casesController';
import type { ResearchCase } from './casesApi';
import './cases.css';
const classification={supported:'Supported by the cited evidence',contradicted:'Contradicted by the cited evidence',unresolved:'Unresolved',recalled:'Recalled account'};
export function CaseExportControls({disabled,onExport}:{disabled:boolean;onExport:(kind:'selected'|'original')=>void}){
  return <div className="case-export-controls"><div className="button-row"><button disabled={disabled} onClick={()=>onExport('selected')}>Export selected case…</button><button disabled={disabled} onClick={()=>onExport('original')}>Export original case catalog…</button></div><p>Selected case creates a new one-case catalog with all its embedded evidence and recorded source references. Original catalog preserves every case and its exact file bytes. Neither changes this reading.</p></div>
}
export function CaseReading({item,identity}:{item:ResearchCase;identity:string}){
  const [expanded,setExpanded]=useState<Set<string>>(new Set());
  function show(id:string){const index=item.materials.findIndex(m=>m.id.normalize('NFC')===id.normalize('NFC'));if(index<0)return;
    setExpanded(old=>new Set([...old,item.materials[index].id]));
    requestAnimationFrame(()=>document.getElementById(`${identity}-material-${index}`)?.scrollIntoView({block:'start'}));
  }
  function links(ids:string[]){return <div className="case-evidence-links">{[...new Set(ids.map(v=>v.normalize('NFC')))].map(id=>{
    const material=item.materials.find(m=>m.id.normalize('NFC')===id);return material&&<button key={id} onClick={()=>show(id)}>Show evidence: {material.title}</button>;
  })}</div>}
  return <article className="case-reading">
    <header><span className="eyebrow">REVIEWED ACCOUNT · RETAINED EVIDENCE</span><h2>{item.title}</h2><h3>{item.question}</h3><p>{item.summary}</p><dl><dt>Author</dt><dd>{item.author}</dd><dt>Source owner</dt><dd>{item.sourceOwner}</dd><dt>Interval</dt><dd>{item.interval}</dd></dl></header>
    <section><h3>What happened</h3>{item.sequence.map((event,index)=><div className="case-evidence" key={index}><h4>{event.title}</h4><strong className={event.status==='observed'?'status-ready':'status-warning'}>{event.status==='observed'?'Observed in the retained evidence':'Not observed in this case'}</strong>{event.timestamp&&<p>{event.timestamp}</p>}<p>{event.detail}</p>{links(event.materialIDs)}</div>)}</section>
    <section><h3>What the evidence supports</h3><p>These are reviewed interpretations. Verification checks embedded text, hashes, quotations and references; it does not prove an interpretation.</p>{item.claims.map(claim=><div className="case-evidence" key={claim.id}><h4>{classification[claim.classification]}</h4><blockquote>{claim.quote}</blockquote><p>{claim.explanation}</p>{links([claim.materialID,...claim.evidenceIDs])}</div>)}</section>
    <section><h3>What remains uncertain</h3><ul>{item.limits.map((limit,i)=><li key={i}>{limit}</li>)}</ul></section>
    <section><h3>Exact supplied and recorded material</h3><p>Everything below is embedded in this case. Historical paths identify sources and are never opened.</p>{item.materials.map((m,index)=><details key={m.id} id={`${identity}-material-${index}`} open={expanded.has(m.id)} onToggle={event=>{const open=event.currentTarget.open;setExpanded(old=>{if(old.has(m.id)===open)return old;const next=new Set(old);if(open)next.add(m.id);else next.delete(m.id);return next})}}><summary>{m.title} · {m.kind}</summary>{m.note&&<p>{m.note}</p>}<pre tabIndex={0}>{m.content}</pre><p className="hash">Embedded text SHA-256: {m.sha256}</p>{m.sourcePath&&<p className="hash">Historical source: {m.sourcePath}</p>}{m.sourceSHA256&&<p className="hash">Recorded source artifact SHA-256: {m.sourceSHA256}</p>}</details>)}</section>
  </article>
}
export default function CasesWorkspace({active}:{active:boolean}){
  const [controller]=useState(()=>new CasesController());const state=useSyncExternalStore(controller.subscribe,controller.snapshot);const selected=state.selected;
  return <section className="cases-workspace" hidden={!active}>
    <div className="section-heading"><div><span className="eyebrow">RESEARCH CASES</span><h1>Questions, evidence, limits.</h1><p>Read the authored account alongside its exact embedded material.</p></div><div className="button-row"><button disabled={state.busy||state.exporting||Boolean(state.bundled)} onClick={()=>void controller.open(true)}>Load reviewed cases</button><button disabled={state.busy||state.exporting} onClick={()=>void controller.open(false)}>Open case…</button>{state.busy&&<button onClick={()=>controller.cancel()}>Cancel opening</button>}</div></div>
    {state.error&&<div className="notice warning" role="alert">{state.error}</div>}<p role="status">{state.busy?'Reading and verifying the selected catalog…':state.message}</p>
    <div className="cases-layout"><aside aria-label="Research questions">{[state.bundled,state.external].filter(v=>v!==null).map(catalog=><section key={catalog.catalogId}><h3>{catalog.origin==='bundled'?'Bundled reviewed cases':catalog.filename}</h3>{catalog.cases.map((c,index)=><button key={c.id} aria-current={selected?.catalog.catalogId===catalog.catalogId&&selected.index===index?'true':undefined} onClick={()=>void controller.select(catalog,index)}><strong>{c.title}</strong><span>{c.question}</span></button>)}</section>)}{!state.bundled&&!state.external&&<p>Load the two reviewed cases, or explicitly open a portable case file.</p>}</aside>
      <div>{selected?<><div className="case-identity"><span>Verified embedded evidence · {selected.catalog.origin}</span><p className="hash">{selected.catalog.filename} · SHA-256 {selected.catalog.sha256}</p><p>{selected.catalog.scope}</p><CaseExportControls disabled={state.exporting||state.busy} onExport={kind=>void controller.export(kind)}/></div><CaseReading key={`${selected.catalog.catalogId}-${selected.index}`} identity={`${selected.catalog.catalogId}-${selected.index}`} item={selected.item}/></>:<div className="notice"><h2>Choose a research question</h2><p>Opening a case keeps it here for reading. It does not import it into the Library.</p></div>}</div>
    </div>
  </section>
}
