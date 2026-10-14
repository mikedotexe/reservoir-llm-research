import { describe,it,expect,vi } from 'vitest';
import { CasesController } from './casesController';
import type { CasesApi,CatalogSummary,ResearchCase,CaseOpenResult,SelectedCaseExportResult } from './casesApi';
const catalog=(id:string):CatalogSummary=>({catalogId:id,filename:'case.json',origin:'external',sha256:'a'.repeat(64),scope:'Embedded integrity',cases:[{id:'q',title:'Question',question:'What was supplied?'}]});
const item:ResearchCase={id:'q',title:'Question',question:'What was supplied?',summary:'Bounded',author:'Reader',sourceOwner:'Source',interval:'Past',limits:['No runtime claim'],materials:[],claims:[],sequence:[]};
function fixture(){const closed:string[]=[];const api:CasesApi={open:async(requestId)=>({requestId,cancelled:false,catalog:catalog('one')}),view:async(requestId,catalogId,index)=>({requestId,catalogId,index,researchCase:item}),close:async(id)=>{closed.push(id)},export:async(requestId,catalogId)=>({requestId,catalogId,file:null}),exportSelected:async(requestId,catalogId,index,caseId)=>({requestId,catalogId,index,caseId,sourceCatalogSha256:catalog('one').sha256,file:null})};return {api,closed,controller:new CasesController(api)}}
describe('reviewed case reading lifecycle',()=>{
  it('selects external first case, preserves it on a rejected replacement and cancelled dialog',async()=>{
    const {controller,api}=fixture();await controller.open(false);expect(controller.snapshot().selected?.item.title).toBe('Question');
    api.open=async()=>{throw new Error('Changed embedded hash')};await controller.open(false);expect(controller.snapshot().error).toBe('Changed embedded hash');expect(controller.snapshot().selected?.catalog.catalogId).toBe('one');
    api.open=async requestId=>({requestId,cancelled:true,catalog:null});await controller.open(false);expect(controller.snapshot().selected?.catalog.catalogId).toBe('one');
  });
  it('closes a late cancelled candidate without changing accepted reading',async()=>{
    const {controller,api,closed}=fixture();await controller.open(false);let release!:(result:CaseOpenResult)=>void;let pendingId='';api.open=requestId=>{pendingId=requestId;return new Promise(resolve=>{release=resolve})};
    const pending=controller.open(false);controller.cancel();release({requestId:pendingId,cancelled:false,catalog:catalog('late')});await pending;expect(closed).toContain('late');expect(controller.snapshot().selected?.catalog.catalogId).toBe('one');
  });
  it('requires explicit question selection for bundled authored order',async()=>{
    const {controller}=fixture();await controller.open(true);expect(controller.snapshot().bundled?.cases[0].id).toBe('q');expect(controller.snapshot().selected).toBeNull();await controller.select(controller.snapshot().bundled!,0);expect(controller.snapshot().selected?.index).toBe(0);
  });
  it('rejects mismatched request identity and retains original on failed first-frame view',async()=>{
    const {controller,api,closed}=fixture();await controller.open(false);api.open=async()=>({requestId:'wrong',cancelled:false,catalog:catalog('wrong')});await controller.open(false);expect(closed).toContain('wrong');
    api.open=async requestId=>({requestId,cancelled:false,catalog:catalog('two')});api.view=async()=>{throw new Error('unavailable')};await controller.open(false);expect(closed).toContain('two');expect(controller.snapshot().selected?.catalog.catalogId).toBe('one');
  });
});
describe('selected-case derivative export',()=>{
  const proof={name:'selected.json',sizeBytes:321,sha256:'b'.repeat(64)};
  it('sends only accepted selection identity and keeps original catalog and selected reading',async()=>{
    const {controller,api}=fixture();await controller.open(false);const selected=controller.snapshot().selected;
    const original=vi.spyOn(api,'export');const derivative=vi.spyOn(api,'exportSelected').mockImplementation(async(requestId,catalogId,index,caseId)=>({requestId,catalogId,index,caseId,sourceCatalogSha256:'a'.repeat(64),file:proof}));
    await controller.export('selected');expect(derivative).toHaveBeenCalledWith(expect.any(String),'one',0,'q');expect(original).not.toHaveBeenCalled();expect(controller.snapshot().selected).toBe(selected);expect(controller.snapshot().message).toContain('new one-case catalog');expect(controller.snapshot().message).toContain(proof.sha256);
    await controller.export('original');expect(original).toHaveBeenCalledTimes(1);expect(controller.snapshot().message).toContain('Original-catalog export cancelled');
  });
  it('retains reading on selected export cancellation or write rejection',async()=>{
    const {controller,api}=fixture();await controller.open(false);const selected=controller.snapshot().selected;
    await controller.export('selected');expect(controller.snapshot().selected).toBe(selected);expect(controller.snapshot().message).toContain('Selected-case export cancelled');
    api.exportSelected=async()=>{throw new Error('Destination is read-only')};await controller.export('selected');expect(controller.snapshot().selected).toBe(selected);expect(controller.snapshot().error).toBe('Destination is read-only');expect(controller.snapshot().exporting).toBe(false);
  });
  it('does nothing without a selection and prevents overlapping original/derivative dialogs',async()=>{
    const {controller,api}=fixture();const derivative=vi.spyOn(api,'exportSelected');await controller.export('selected');expect(derivative).not.toHaveBeenCalled();
    await controller.open(false);let release!:(v:SelectedCaseExportResult)=>void;let result!:SelectedCaseExportResult;
    derivative.mockImplementation((requestId,catalogId,index,caseId)=>{result={requestId,catalogId,index,caseId,sourceCatalogSha256:'a'.repeat(64),file:null};return new Promise(resolve=>{release=resolve})});
    const original=vi.spyOn(api,'export');const pending=controller.export('selected');await controller.export('original');await controller.export('selected');expect(original).not.toHaveBeenCalled();expect(derivative).toHaveBeenCalledTimes(1);release(result);await pending;
  });
  it.each(['catalogId','caseId','requestId','sourceCatalogSha256','index'] as const)('rejects a mismatched %s response without changing the reading',async(field)=>{
    const {controller,api}=fixture();await controller.open(false);const selected=controller.snapshot().selected;
    api.exportSelected=async(requestId,catalogId,index,caseId)=>({...{requestId,catalogId,index,caseId,sourceCatalogSha256:'a'.repeat(64),file:proof},[field]:field==='index'?9:'wrong'} as SelectedCaseExportResult);
    await controller.export('selected');expect(controller.snapshot().selected).toBe(selected);expect(controller.snapshot().error).toContain('did not match');expect(controller.snapshot().message).not.toContain('exported');
  });
  it.each([false,true])('ignores old export success/failure after a different selection (failure=%s)',async(failure)=>{
    const {controller,api}=fixture();await controller.open(false);let finish!:()=>void;
    api.exportSelected=(requestId,catalogId,index,caseId)=>new Promise((resolve,reject)=>{finish=()=>failure?reject(new Error('late failure')):resolve({requestId,catalogId,index,caseId,sourceCatalogSha256:'a'.repeat(64),file:proof})});
    const pending=controller.export('selected');await controller.select(catalog('new'),0);finish();await pending;expect(controller.snapshot().selected?.catalog.catalogId).toBe('new');expect(controller.snapshot().error).toBe('');expect(controller.snapshot().message).toBe('');
  });
});
