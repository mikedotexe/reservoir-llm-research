import { errorText } from './api';
import type { ObservatoryApi } from './observatoryApi';
import type { ObservatoryFrame, ObservatoryFrameResult, ObservatorySummary, ObservatoryTimelinePoint, ObservatoryTrackId } from './observatoryTypes';
export interface ObservatoryReading {
  summary:ObservatorySummary|null; trackId:ObservatoryTrackId|null; frame:ObservatoryFrame|null;
  points:ObservatoryTimelinePoint[]; node:number; opening:boolean; loading:boolean; loadingTimeline:boolean;
  playing:boolean; rate:number; message:string;
}
const empty=():ObservatoryReading=>({summary:null,trackId:null,frame:null,points:[],node:0,opening:false,loading:false,loadingTimeline:false,playing:false,rate:1,message:''});
let sequence=0;
const request=()=>`observatory-${++sequence}`;
/** Backend handles own evidence; this controller owns only bounded views and selection. */
export class ObservatoryController {
  private state=empty(); private listeners=new Set<()=>void>();
  private openGeneration=0; private frameGeneration=0; private timelineGeneration=0;
  private clock:{time:number;position:number}|null=null;
  constructor(private api:ObservatoryApi){}
  snapshot=()=>this.state;
  subscribe=(listener:()=>void)=>{this.listeners.add(listener);return()=>{this.listeners.delete(listener)}};
  private update(next:Partial<ObservatoryReading>){this.state={...this.state,...next};this.listeners.forEach(listener=>listener())}
  private async release(id:string){try{await this.api.close(id)}catch{/* A cleanup failure cannot replace a newer reading. */}}
  async open(){
    const generation=++this.openGeneration;this.pause();this.update({opening:true,message:'Checking bundled recording identities and structure…'});
    let candidate:ObservatorySummary|null=null;
    try{
      const id=request(),result=await this.api.open(id);candidate=result.observatory;
      if(generation!==this.openGeneration){await this.release(candidate.observatoryId);return}
      if(result.requestId!==id)throw new Error('Recording response did not match its request.');
      const old=this.state.summary;this.frameGeneration++;this.timelineGeneration++;
      this.update({...empty(),summary:candidate,message:candidate.tracks.length?'Available bundled recordings passed identity and structure checks.':'No recording was accepted. See the source diagnostics below.'});
      const selected=generation===this.openGeneration&&candidate.tracks[0]?this.selectTrack(candidate.tracks[0].id):Promise.resolve();
      if(old)await this.release(old.observatoryId);
      await selected;
    }catch(error){if(candidate)await this.release(candidate.observatoryId);if(generation===this.openGeneration)this.update({opening:false,message:errorText(error)})}
  }
  async selectTrack(trackId:ObservatoryTrackId){
    const track=this.state.summary?.tracks.find(item=>item.id===trackId);if(!track)return;
    this.pause();this.frameGeneration++;this.timelineGeneration++;
    this.update({trackId,frame:null,points:[],loading:false,loadingTimeline:false,rate:trackId==='history'?1:4,message:''});
    await Promise.all([this.frame(0),this.timeline()]);
  }
  async selectNode(node:number){
    const track=this.state.summary?.tracks.find(item=>item.id===this.state.trackId);
    if(!Number.isInteger(node)||node<0||node>=(track?.nodeCount??0))return;
    this.update({node});await this.timeline();
  }
  async timeline(){
    const {summary,trackId,node}=this.state,track=summary?.tracks.find(item=>item.id===trackId);if(!summary||!trackId||!track)return;
    const generation=++this.timelineGeneration,nodeIndex=trackId==='states'?node:null;
    this.update({loadingTimeline:true,points:[]});
    try{
      const points:ObservatoryTimelinePoint[]=[];
      const limit=Math.min(256,summary.maxTimelinePage);
      if(!Number.isInteger(limit)||limit<1||track.frameCount>100_000)throw new Error('Unsupported timeline bounds.');
      while(points.length<track.frameCount){
        const id=request(),start=points.length,result=await this.api.timeline(id,summary.observatoryId,trackId,start,limit,nodeIndex);
        if(generation!==this.timelineGeneration)return;
        if(result.requestId!==id||result.observatoryId!==summary.observatoryId||result.trackId!==trackId||result.start!==start||result.total!==track.frameCount||result.nodeIndex!==nodeIndex||!result.points.length||result.points.length>limit||start+result.points.length>track.frameCount||result.points.some((point,i)=>point.index!==start+i)||result.hasMore!==(start+result.points.length<track.frameCount))throw new Error('Timeline page did not match the selected recording.');
        points.push(...result.points);
      }
      this.update({points,loadingTimeline:false});
    }catch(error){if(generation===this.timelineGeneration)this.update({loadingTimeline:false,points:[],message:`${errorText(error)} Timeline coverage is incomplete; exact selected frames remain available.`})}
  }
  async frame(index:number){
    this.pause();const track=this.state.summary?.tracks.find(item=>item.id===this.state.trackId);
    if(!track||!Number.isFinite(index))return;
    const target=Math.max(0,Math.min(track.frameCount-1,Math.round(index)));
    return this.read((id,handle,trackId)=>this.api.frame(id,handle,trackId,target),target);
  }
  async seek(position:number){
    this.pause();if(!Number.isFinite(position))return;
    return this.read((id,handle,trackId)=>this.api.seek(id,handle,trackId,position,'nearest'));
  }
  private async read(load:(id:string,handle:string,trackId:ObservatoryTrackId)=>Promise<ObservatoryFrameResult>,index?:number){
    const {summary,trackId}=this.state;if(!summary||!trackId)return;
    const generation=++this.frameGeneration,id=request();this.update({loading:true});
    try{
      const result=await load(id,summary.observatoryId,trackId);
      if(generation!==this.frameGeneration)return;
      if(result.requestId!==id||result.observatoryId!==summary.observatoryId||result.frame.trackId!==trackId||(index!==undefined&&result.frame.index!==index))throw new Error('Frame did not match the selected recording.');
      this.update({frame:this.state.frame?.index===result.frame.index&&this.state.frame.trackId===result.frame.trackId?this.state.frame:result.frame,loading:false});
    }catch(error){if(generation===this.frameGeneration){this.pause();this.update({loading:false,message:`${errorText(error)} The last readable frame is retained.`})}}
  }
  setRate(rate:number){if([0.5,1,2,4,8,16,32].includes(rate)){this.pause();this.update({rate})}}
  play(now:number){const track=this.state.summary?.tracks.find(item=>item.id===this.state.trackId);if(!track||!this.state.frame||this.state.loading||this.state.frame.index>=track.frameCount-1||!Number.isFinite(now))return;this.clock={time:now,position:this.state.frame.position};this.update({playing:true})}
  pause(){if(this.clock){this.frameGeneration++;this.update({loading:false})}this.clock=null;if(this.state.playing)this.update({playing:false})}
  async tick(now:number){
    const track=this.state.summary?.tracks.find(item=>item.id===this.state.trackId),clock=this.clock;
    if(!this.state.playing||!track||!clock||!Number.isFinite(now))return;
    clock.position=Math.min(track.lastPosition,clock.position+Math.max(0,now-clock.time)/1000*this.state.rate);clock.time=Math.max(now,clock.time);
    if(this.state.loading)return;
    const position=clock.position;
    await this.read((id,handle,trackId)=>this.api.seek(id,handle,trackId,position,'floor'));
    if(this.clock===clock&&position>=track.lastPosition)this.pause();
  }
  async close(){this.openGeneration++;this.frameGeneration++;this.timelineGeneration++;this.pause();const old=this.state.summary;this.update(empty());if(old)await this.release(old.observatoryId)}
}
