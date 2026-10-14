import { errorText } from './api';
import { casesApi, type CasesApi, type CatalogSummary, type ResearchCase } from './casesApi';
export interface CasesState {
  bundled:CatalogSummary|null; external:CatalogSummary|null;
  selected:{catalog:CatalogSummary;index:number;item:ResearchCase}|null;
  busy:boolean; exporting:boolean; error:string; message:string;
}
export class CasesController {
  private state:CasesState={bundled:null,external:null,selected:null,busy:false,exporting:false,error:'',message:''};
  private listeners=new Set<()=>void>();private generation=0;private selectionGeneration=0;private serial=0;
  constructor(private api:CasesApi=casesApi){}
  snapshot=()=>this.state;
  subscribe=(fn:()=>void)=>{this.listeners.add(fn);return()=>{this.listeners.delete(fn)}};
  private set(patch:Partial<CasesState>){this.state={...this.state,...patch};this.listeners.forEach(fn=>fn())}
  private id(){return `cases-${++this.serial}-${Date.now()}`}
  cancel(){this.generation++;this.selectionGeneration++;this.set({busy:false,message:'Opening cancelled. Previous case retained.'})}
  async open(bundled:boolean){
    if(this.state.busy)return;
    const generation=++this.generation; const selection=++this.selectionGeneration;const requestId=this.id();
    this.set({busy:true,error:'',message:''});let candidate:CatalogSummary|null=null;
    try{
      const result=await this.api.open(requestId,bundled); candidate=result.catalog;
      if(generation!==this.generation||result.requestId!==requestId){if(candidate)await this.api.close(candidate.catalogId);return}
      if(result.cancelled||!candidate){this.set({message:'Dialog cancelled. Previous case retained.'});return}
      // First selection is explicit for the authored catalog; an opened file selects its first case.
      let selected=this.state.selected;
      if(!bundled){const readId=this.id(); const view=await this.api.view(readId,candidate.catalogId,0);
        if(generation!==this.generation||selection!==this.selectionGeneration||view.requestId!==readId||view.catalogId!==candidate.catalogId||view.index!==0){await this.api.close(candidate.catalogId);return}
        selected={catalog:candidate,index:0,item:view.researchCase};
      }
      const old=bundled?this.state.bundled:this.state.external;
      this.set({...bundled?{bundled:candidate}:{external:candidate},selected,message:'Embedded hashes, quotations and references verified by this build.'});
      candidate=null;
      if(old && old.catalogId!==this.state.selected?.catalog.catalogId)await this.api.close(old.catalogId);
    }catch(error){if(candidate)await this.api.close(candidate.catalogId).catch(()=>{});if(generation===this.generation)this.set({error:errorText(error),message:'Previous accepted case retained.'})}
    finally{if(generation===this.generation)this.set({busy:false})}
  }
  async select(catalog:CatalogSummary,index:number){
    const generation=++this.selectionGeneration; const requestId=this.id(); this.set({error:'',message:''});
    try {const view=await this.api.view(requestId,catalog.catalogId,index);
      if(generation!==this.selectionGeneration||view.requestId!==requestId||view.catalogId!==catalog.catalogId||view.index!==index)return;
      this.set({selected:{catalog,index,item:view.researchCase},message:''});
    }catch(error){if(generation===this.selectionGeneration)this.set({error:errorText(error)})}
  }
  async export(kind:'original'|'selected'='original'){
    const selected=this.state.selected;if(!selected||this.state.exporting)return;
    const requestId=this.id();const generation=this.generation;const selection=this.selectionGeneration;
    const current=()=>generation===this.generation&&selection===this.selectionGeneration&&this.state.selected===selected;
    this.set({exporting:true,error:'',message:kind==='selected'?'Preparing this case with all its embedded evidence…':'Preparing the original catalog bytes…'});
    try{
      if(kind==='selected'){
        const result=await this.api.exportSelected(requestId,selected.catalog.catalogId,selected.index,selected.item.id);
        if(!current())return;
        if(result.requestId!==requestId||result.catalogId!==selected.catalog.catalogId||result.index!==selected.index||result.caseId!==selected.item.id||result.sourceCatalogSha256!==selected.catalog.sha256)throw new Error('Export response did not match the selected case.');
        this.set({message:result.file?`Selected case exported as a new one-case catalog: ${result.file.name} · SHA-256 ${result.file.sha256}. Original catalog retained.`:'Selected-case export cancelled. The case remains open.'});
      }else{
        const result=await this.api.export(requestId,selected.catalog.catalogId);
        if(!current())return;
        if(result.requestId!==requestId||result.catalogId!==selected.catalog.catalogId)throw new Error('Export response did not match the original catalog.');
        this.set({message:result.file?`Original catalog exported without rewriting: ${result.file.name} · SHA-256 ${result.file.sha256}`:'Original-catalog export cancelled. The case remains open.'});
      }
    }catch(error){if(current())this.set({error:errorText(error),message:'Export failed. The selected case and original catalog remain open.'})}
    finally{this.set({exporting:false})}
  }
}
