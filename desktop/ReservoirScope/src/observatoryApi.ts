import { invoke, isTauri } from '@tauri-apps/api/core';
import type { ObservatoryOpenResult, ObservatoryFrameResult, ObservatoryTimelineResult, ObservatoryTrackId, ObservatorySeekMode } from './observatoryTypes';
export interface ObservatoryApi {
  open(requestId:string):Promise<ObservatoryOpenResult>;
  timeline(requestId:string,observatoryId:string,trackId:ObservatoryTrackId,start:number,limit:number,nodeIndex:number|null):Promise<ObservatoryTimelineResult>;
  frame(requestId:string,observatoryId:string,trackId:ObservatoryTrackId,index:number):Promise<ObservatoryFrameResult>;
  seek(requestId:string,observatoryId:string,trackId:ObservatoryTrackId,position:number,mode:ObservatorySeekMode):Promise<ObservatoryFrameResult>;
  close(observatoryId:string):Promise<void>;
}
async function command<T>(name:string,args:Record<string,unknown>):Promise<T>{
  if(!isTauri())throw new Error('Open the desktop app to inspect the bundled Observatory recordings.');
  return invoke<T>(name,args);
}
export const observatoryApi:ObservatoryApi={
  open:requestId=>command('open_observatory',{requestId}),
  timeline:(requestId,observatoryId,trackId,start,limit,nodeIndex)=>command('get_observatory_timeline',{requestId,observatoryId,trackId,start,limit,nodeIndex}),
  frame:(requestId,observatoryId,trackId,index)=>command('get_observatory_frame',{requestId,observatoryId,trackId,index}),
  seek:(requestId,observatoryId,trackId,position,mode)=>command('seek_observatory',{requestId,observatoryId,trackId,position,mode}),
  close:observatoryId=>command('close_observatory',{observatoryId}),
};
