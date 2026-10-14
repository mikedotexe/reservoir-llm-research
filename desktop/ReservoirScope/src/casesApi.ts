import { invoke, isTauri } from '@tauri-apps/api/core';
import type { FileProof } from './types';
export interface CaseSummary { id:string; title:string; question:string }
export interface CatalogSummary { catalogId:string; filename:string; origin:string; sha256:string; scope:string; cases:CaseSummary[] }
export interface ResearchCase extends CaseSummary {
  summary:string; author:string; sourceOwner:string; interval:string; limits:string[];
  sequence:{title:string;detail:string;materialIDs:string[];status:'observed'|'notObserved';timestamp:string|null}[];
  claims:{id:string;classification:'supported'|'contradicted'|'unresolved'|'recalled';materialID:string;quote:string;evidenceIDs:string[];explanation:string}[];
  materials:{id:string;title:string;kind:string;content:string;sha256:string;sourcePath:string|null;sourceSHA256:string|null;note:string|null}[];
}
export interface CaseOpenResult {requestId:string;cancelled:boolean;catalog:CatalogSummary|null}
export interface CaseViewResult {requestId:string;catalogId:string;index:number;researchCase:ResearchCase}
export interface SelectedCaseExportResult {requestId:string;catalogId:string;index:number;caseId:string;sourceCatalogSha256:string;file:FileProof|null}
export interface CasesApi {
  open(requestId:string,bundled:boolean):Promise<CaseOpenResult>;
  view(requestId:string,catalogId:string,index:number):Promise<CaseViewResult>;
  close(catalogId:string):Promise<void>;
  export(requestId:string,catalogId:string):Promise<{requestId:string;catalogId:string;file:FileProof|null}>;
  exportSelected(requestId:string,catalogId:string,index:number,caseId:string):Promise<SelectedCaseExportResult>;
}
async function command<T>(name:string,args:Record<string,unknown>):Promise<T>{
  if(!isTauri())throw new Error('Open the desktop app to verify case evidence and use native dialogs.');
  return invoke<T>(name,args);
}
export const casesApi:CasesApi={
  open:(requestId,bundled)=>command('open_cases',{requestId,bundled}),
  view:(requestId,catalogId,index)=>command('get_case',{requestId,catalogId,index}),
  close:catalogId=>command('close_cases',{catalogId}),
  export:(requestId,catalogId)=>command('export_cases',{requestId,catalogId}),
  exportSelected:(requestId,catalogId,index,caseId)=>command('export_selected_case',{requestId,catalogId,index,caseId}),
};
