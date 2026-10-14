import { it,expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { CaseReading,CaseExportControls } from './CasesWorkspace';
import type { ResearchCase } from './casesApi';
it('renders supplied text inertly and preserves authored uncertainty and ownership',()=>{
  const item:ResearchCase={id:'q',title:'Case',question:'Question?',summary:'Summary',author:'Author',sourceOwner:'Owner',interval:'Past',limits:['Unknown runtime'],materials:[{id:'m',title:'Source',kind:'text',content:'<script>danger()</script>',sha256:'a'.repeat(64),sourcePath:'Z:\\missing',sourceSHA256:null,note:null}],claims:[{id:'c',classification:'recalled',materialID:'m',quote:'danger()',evidenceIDs:['m'],explanation:'Authored account'}],sequence:[{title:'Later outcome',detail:'Not checked',materialIDs:[],status:'notObserved',timestamp:null}]};
  const html=renderToStaticMarkup(<CaseReading identity="one" item={item}/>);expect(html).toContain('&lt;script&gt;danger()&lt;/script&gt;');expect(html).not.toContain('<script>');expect(html).toContain('Not observed in this case');expect(html).toContain('Recalled account');expect(html).toContain('does not prove an interpretation');expect(html).toContain('Source owner');expect(html).toContain('Unknown runtime');
});
it('distinguishes the selected derivative from exact original export and disables both during an operation',()=>{
  const html=renderToStaticMarkup(<CaseExportControls disabled onExport={()=>{}}/>);
  expect(html).toContain('Export selected case…');expect(html).toContain('Export original case catalog…');
  expect(html).toContain('all its embedded evidence and recorded source references');expect(html).toContain('exact file bytes');
  expect(html.match(/disabled=""/g)).toHaveLength(2);
});
