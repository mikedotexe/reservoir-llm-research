import { describe, expect, it, vi } from 'vitest';
import { ObservatoryController } from './observatoryController';
import type { ObservatoryApi } from './observatoryApi';
import type { ObservatoryFrame, ObservatoryFrameResult, ObservatoryOpenResult, ObservatorySummary, ObservatoryTimelinePoint, ObservatoryTimelineResult, ObservatoryTrackId } from './observatoryTypes';

const historyPositions = [10,12,20,35,50];
function summary(id: string, maxTimelinePage = 2): ObservatorySummary {
  return { observatoryId:id,maxTimelinePage,diagnostics:[],tracks:(['history','states'] as const).map(track=>({
    id:track,title:track,axis:track==='history'?'elapsedSeconds':'ordinal',frameCount:5,nodeCount:track==='states'?128:null,
    firstPosition:track==='history'?10:0,lastPosition:track==='history'?50:4,firstUtc:null,lastUtc:null,capturedAtUtc:null,
    identities:[{name:`${track}.json`,sha256:'retained-test-identity'}],provenance:['Synthetic protocol fixture'],missingness:[],definitions:{},bands:null,stateReference:null,
  })) };
}
function frame(trackId: ObservatoryTrackId,index:number): ObservatoryFrame {
  return {trackId,index,position:trackId==='history'?historyPositions[index]:index,
    history:trackId==='history'?{tUtc:`retained-utc-${index}`,tSeconds:historyPositions[index],sessionId:'original-session',fillPct:60+index,fillRatePctPerS:null,cascade:[4,2,1],esnCovLambda1:null,geomRadius:null,geomRel:null,esnLeak:null,esnLambda:null,sourceIds:null,intervalSeconds:index?historyPositions[index]-historyPositions[index-1]:null,breakBefore:index===3}:null,
    state:trackId==='states'?{activations:Array(128).fill(0),pc:[0,0,0],stateRms:0,centeredRms:0,projectedRms:0,reconstructionRmse:0,sourceIdentity:'original-state-capture',fields:{magnitude:Array(128).fill(0),deviation:Array(128).fill(0),magnitudeOutOfRangeCount:0,deviationOutOfRangeCount:0,scores:[0,0,0],centeredEnergy:0,selections:[]}}:null};
}
function point(trackId:ObservatoryTrackId,index:number,nodeIndex:number|null):ObservatoryTimelinePoint {
  return {index,position:frame(trackId,index).position,tUtc:trackId==='history'?`retained-utc-${index}`:null,sessionId:trackId==='history'?'original-session':null,
    fillPct:trackId==='history'?60+index:null,fillRatePctPerS:null,cascade:trackId==='history'?[4,2,1]:null,intervalSeconds:trackId==='history'&&index?historyPositions[index]-historyPositions[index-1]:null,breakBefore:trackId==='history'&&index===3,
    stateRms:trackId==='states'?0:null,pc:trackId==='states'?[0,0,0]:null,nodeValue:trackId==='states'&&nodeIndex!==null?nodeIndex/256+index/1000:null};
}
function page(requestId:string,observatoryId:string,trackId:ObservatoryTrackId,start:number,limit:number,nodeIndex:number|null):ObservatoryTimelineResult {
  const end=Math.min(5,start+limit);return {requestId,observatoryId,trackId,start,total:5,hasMore:end<5,nodeIndex,points:Array.from({length:end-start},(_,i)=>point(trackId,start+i,nodeIndex))};
}
function deferred<T>() {let resolve!:(value:T)=>void;let reject!:(error:Error)=>void;const promise=new Promise<T>((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};}
function harness() {
  let handles=0;
  const api:ObservatoryApi={
    open:vi.fn(async requestId=>({requestId,observatory:summary(`handle-${++handles}`)})),
    close:vi.fn(async()=>{}),
    frame:vi.fn(async(requestId,observatoryId,trackId,index)=>({requestId,observatoryId,frame:frame(trackId,index)})),
    timeline:vi.fn(async(...args:Parameters<ObservatoryApi['timeline']>)=>page(...args)),
    seek:vi.fn(async(requestId,observatoryId,trackId,position,mode)=>{
      const positions=trackId==='history'?historyPositions:[0,1,2,3,4];let index=0;
      positions.forEach((p,i)=>{if(mode==='floor'?p<=position:Math.abs(p-position)<Math.abs(positions[index]-position))index=i;});
      return {requestId,observatoryId,frame:frame(trackId,index)};
    }),
  };
  return {api,controller:new ObservatoryController(api)};
}

describe('Observatory accepted handle and selection generations',()=>{
  it('assembles every bounded page in order without publishing a partial successful timeline',async()=>{
    const {api,controller}=harness();const snapshots:number[]=[];controller.subscribe(()=>snapshots.push(controller.snapshot().points.length));
    await controller.open();
    expect(vi.mocked(api.timeline).mock.calls.map(call=>[call[3],call[4],call[5]])).toEqual([[0,2,null],[2,2,null],[4,2,null]]);
    expect(controller.snapshot().points.map(p=>p.index)).toEqual([0,1,2,3,4]);
    expect(snapshots.every(length=>length===0||length===5)).toBe(true);
    expect(controller.snapshot().points[3].breakBefore).toBe(true);expect(controller.snapshot().frame?.history?.tUtc).toBe('retained-utc-0');
  });
  it('releases obsolete opens and cannot resurrect an explicitly closed workspace',async()=>{
    const {api,controller}=harness();const slow=deferred<ObservatoryOpenResult>();let id='';
    vi.mocked(api.open).mockImplementationOnce(requestId=>{id=requestId;return slow.promise;});
    const pending=controller.open();await controller.open();const accepted=controller.snapshot().summary!.observatoryId;
    slow.resolve({requestId:id,observatory:summary('obsolete')});await pending;
    expect(controller.snapshot().summary?.observatoryId).toBe(accepted);expect(api.close).toHaveBeenCalledWith('obsolete');
    const afterClose=deferred<ObservatoryOpenResult>();let lateId='';vi.mocked(api.open).mockImplementationOnce(requestId=>{lateId=requestId;return afterClose.promise;});
    const late=controller.open();await controller.close();afterClose.resolve({requestId:lateId,observatory:summary('late')});await late;
    expect(controller.snapshot().summary).toBeNull();expect(controller.snapshot().frame).toBeNull();expect(api.close).toHaveBeenCalledWith('late');expect(api.close).toHaveBeenCalledWith(accepted);
  });
  it('retains the accepted reading on failed or mismatched open and releases only the candidate',async()=>{
    const {api,controller}=harness();await controller.open();await controller.frame(2);const accepted=controller.snapshot().summary;
    vi.mocked(api.open).mockRejectedValueOnce(new Error('identity check failed'));await controller.open();
    expect(controller.snapshot().summary).toBe(accepted);expect(controller.snapshot().frame?.index).toBe(2);
    vi.mocked(api.open).mockResolvedValueOnce({requestId:'wrong',observatory:summary('wrong-candidate')});await controller.open();
    expect(controller.snapshot().summary).toBe(accepted);expect(controller.snapshot().message).toContain('did not match');expect(api.close).toHaveBeenCalledWith('wrong-candidate');expect(api.close).not.toHaveBeenCalledWith(accepted!.observatoryId);
  });
  it('ignores stale frame replies across manual reads, track replacement and close',async()=>{
    const {api,controller}=harness();await controller.open();
    const slow=deferred<ObservatoryFrameResult>();let result!:ObservatoryFrameResult;
    vi.mocked(api.frame).mockImplementationOnce((requestId,observatoryId,trackId,index)=>{result={requestId,observatoryId,frame:frame(trackId,index)};return slow.promise;});
    const pending=controller.frame(3);await controller.frame(2);slow.resolve(result);await pending;expect(controller.snapshot().frame?.index).toBe(2);
    const old=deferred<ObservatoryFrameResult>();vi.mocked(api.frame).mockImplementationOnce((requestId,observatoryId,trackId,index)=>{result={requestId,observatoryId,frame:frame(trackId,index)};return old.promise;});
    const obsolete=controller.frame(4);await controller.selectTrack('states');old.resolve(result);await obsolete;expect(controller.snapshot().frame?.trackId).toBe('states');expect(controller.snapshot().frame?.index).toBe(0);
    const closing=deferred<ObservatoryFrameResult>();vi.mocked(api.frame).mockImplementationOnce((requestId,observatoryId,trackId,index)=>{result={requestId,observatoryId,frame:frame(trackId,index)};return closing.promise;});
    const closed=controller.frame(3);await controller.close();closing.resolve(result);await closed;expect(controller.snapshot().frame).toBeNull();expect(controller.snapshot().loading).toBe(false);
  });
  it('cancels old track/node paging and accepts only the latest selected coordinate',async()=>{
    const {api,controller}=harness();await controller.open();await controller.selectTrack('states');
    const slow=deferred<ObservatoryTimelineResult>();let stale!:ObservatoryTimelineResult;
    vi.mocked(api.timeline).mockImplementationOnce((...args)=>{stale=page(...args);return slow.promise;});
    const oldNode=controller.selectNode(1);await controller.selectNode(127);slow.resolve(stale);await oldNode;
    expect(controller.snapshot().node).toBe(127);expect(controller.snapshot().points[0].nodeValue).toBe(127/256);
    const trackPage=deferred<ObservatoryTimelineResult>();vi.mocked(api.timeline).mockImplementationOnce((...args)=>{stale=page(...args);return trackPage.promise;});
    const oldTrack=controller.timeline();await controller.selectTrack('history');trackPage.resolve(stale);await oldTrack;
    expect(controller.snapshot().trackId).toBe('history');expect(controller.snapshot().points.every(p=>p.nodeValue===null)).toBe(true);
    const count=vi.mocked(api.timeline).mock.calls.length;await controller.selectNode(-1);await controller.selectNode(128);await controller.selectNode(0.5);expect(api.timeline).toHaveBeenCalledTimes(count);
  });
  it('retains the last selected frame on failed/mismatched reads',async()=>{
    const {api,controller}=harness();await controller.open();await controller.frame(2);
    vi.mocked(api.frame).mockRejectedValueOnce(new Error('frame transport failed'));await controller.frame(4);
    expect(controller.snapshot().frame?.index).toBe(2);expect(controller.snapshot().loading).toBe(false);expect(controller.snapshot().message).toContain('last readable frame');
    vi.mocked(api.frame).mockImplementationOnce(async(requestId,observatoryId)=>({requestId,observatoryId,frame:frame('states',4)}));await controller.frame(4);expect(controller.snapshot().frame?.index).toBe(2);
  });
  it('does not reset a newer track selection when old-handle cleanup finishes',async()=>{
    const {api,controller}=harness();await controller.open();const cleanup=deferred<void>();
    vi.mocked(api.close).mockImplementationOnce(()=>cleanup.promise);
    const reload=controller.open();await vi.waitFor(()=>expect(controller.snapshot().summary?.observatoryId).toBe('handle-2'));
    await controller.selectTrack('states');await controller.frame(3);cleanup.resolve();await reload;
    expect(controller.snapshot().trackId).toBe('states');expect(controller.snapshot().frame?.index).toBe(3);expect(api.close).toHaveBeenCalledWith('handle-1');
  });
});

describe('Observatory complete timeline coverage',()=>{
  it('does not expose a successful prefix after a later page fails',async()=>{
    const {api,controller}=harness();vi.mocked(api.timeline).mockImplementation(async(...args)=>{if(args[3]===2)throw new Error('second page failed');return page(...args);});
    await controller.open();expect(controller.snapshot().points).toEqual([]);expect(controller.snapshot().loadingTimeline).toBe(false);expect(controller.snapshot().message).toContain('coverage is incomplete');expect(controller.snapshot().frame?.index).toBe(0);
  });
  it.each(['request','handle','track','start','total','node','empty','oversized','index','hasMore'] as const)('rejects malformed %s page without publishing coverage',async flaw=>{
    const {api,controller}=harness();vi.mocked(api.timeline).mockImplementationOnce(async(...args)=>{
      const result=page(...args);
      switch(flaw){case'request':result.requestId='stale';break;case'handle':result.observatoryId='other';break;case'track':result.trackId='states';break;case'start':result.start=1;break;case'total':result.total=6;break;case'node':result.nodeIndex=1;break;case'empty':result.points=[];break;case'oversized':result.points.push(point('history',2,null));break;case'index':result.points[1].index=3;break;case'hasMore':result.hasMore=false;break;}
      return result;
    });await controller.open();expect(controller.snapshot().points).toEqual([]);expect(controller.snapshot().message).toContain('coverage is incomplete');expect(api.timeline).toHaveBeenCalledTimes(1);
  });
  it('invalidates a pending page and its eventual failure when closing',async()=>{
    const {api,controller}=harness();await controller.open();const slow=deferred<ObservatoryTimelineResult>();vi.mocked(api.timeline).mockImplementationOnce(()=>slow.promise);
    const pending=controller.timeline();await controller.close();slow.reject(new Error('obsolete failure'));await pending;
    expect(controller.snapshot().points).toEqual([]);expect(controller.snapshot().message).toBe('');expect(controller.snapshot().loadingTimeline).toBe(false);
  });
});

describe('Observatory monotonic recorded clocks',()=>{
  it('uses floor/hold while playing, nearest for deliberate seeking, and never fabricates an in-between frame',async()=>{
    const {api,controller}=harness();await controller.open();controller.play(1000);await controller.tick(6000);
    expect(api.seek).toHaveBeenLastCalledWith(expect.any(String),'handle-1','history',15,'floor');expect(controller.snapshot().frame?.position).toBe(12);expect(controller.snapshot().frame?.index).toBe(1);
    await controller.seek(18);expect(api.seek).toHaveBeenLastCalledWith(expect.any(String),'handle-1','history',18,'nearest');expect(controller.snapshot().frame?.position).toBe(20);expect(controller.snapshot().playing).toBe(false);
  });
  it('ignores backward wall-clock inputs and accumulates elapsed time during one in-flight frame',async()=>{
    const {api,controller}=harness();await controller.open();const slow=deferred<ObservatoryFrameResult>();let result!:ObservatoryFrameResult;
    vi.mocked(api.seek).mockImplementationOnce((requestId,observatoryId,trackId)=>{result={requestId,observatoryId,frame:frame(trackId,1)};return slow.promise;});
    controller.play(1000);const pending=controller.tick(4000);await controller.tick(3000);await controller.tick(8000);expect(api.seek).toHaveBeenCalledTimes(1);
    slow.resolve(result);await pending;await controller.tick(8000);expect(api.seek).toHaveBeenLastCalledWith(expect.any(String),'handle-1','history',17,'floor');expect(controller.snapshot().frame?.position).toBe(12);
  });
  it('pauses at the final retained position and applies rate changes only to a new clock',async()=>{
    const {api,controller}=harness();await controller.open();controller.setRate(8);controller.play(0);await controller.tick(10000);
    expect(api.seek).toHaveBeenLastCalledWith(expect.any(String),'handle-1','history',50,'floor');expect(controller.snapshot().frame?.index).toBe(4);expect(controller.snapshot().playing).toBe(false);
    controller.play(10001);expect(controller.snapshot().playing).toBe(false);await controller.frame(0);controller.play(11000);controller.setRate(2);expect(controller.snapshot().playing).toBe(false);controller.setRate(3);expect(controller.snapshot().rate).toBe(2);
    controller.play(12000);await controller.tick(13000);expect(api.seek).toHaveBeenLastCalledWith(expect.any(String),'handle-1','history',12,'floor');
  });
  it('does not advance after pause/navigation even if an earlier playback request completes',async()=>{
    const {api,controller}=harness();await controller.open();const slow=deferred<ObservatoryFrameResult>();let result!:ObservatoryFrameResult;
    vi.mocked(api.seek).mockImplementationOnce((requestId,observatoryId,trackId)=>{result={requestId,observatoryId,frame:frame(trackId,2)};return slow.promise;});
    controller.play(0);const pending=controller.tick(10000);controller.pause();slow.resolve(result);await pending;
    expect(controller.snapshot().frame?.index).toBe(0);expect(controller.snapshot().playing).toBe(false);expect(controller.snapshot().loading).toBe(false);
  });
  it('a manual seek supersedes an in-flight playback reply',async()=>{
    const {api,controller}=harness();await controller.open();const slow=deferred<ObservatoryFrameResult>();let result!:ObservatoryFrameResult;
    vi.mocked(api.seek).mockImplementationOnce((requestId,observatoryId,trackId)=>{result={requestId,observatoryId,frame:frame(trackId,1)};return slow.promise;});
    controller.play(0);const pending=controller.tick(2000);await controller.seek(35);slow.resolve(result);await pending;
    expect(controller.snapshot().frame?.index).toBe(3);expect(controller.snapshot().playing).toBe(false);
  });
  it('cannot start a playback clock while a manual frame is still loading',async()=>{
    const {api,controller}=harness();await controller.open();const slow=deferred<ObservatoryFrameResult>();let result!:ObservatoryFrameResult;
    vi.mocked(api.frame).mockImplementationOnce((requestId,observatoryId,trackId,index)=>{result={requestId,observatoryId,frame:frame(trackId,index)};return slow.promise;});
    const pending=controller.frame(2);controller.play(1000);await controller.tick(9000);
    expect(controller.snapshot().playing).toBe(false);expect(api.seek).not.toHaveBeenCalled();slow.resolve(result);await pending;
    expect(controller.snapshot().frame?.index).toBe(2);controller.play(10000);await controller.tick(11000);
    expect(api.seek).toHaveBeenLastCalledWith(expect.any(String),'handle-1','history',21,'floor');
  });
  it('retains the accepted frame object during floor holds to avoid redundant GPU updates',async()=>{
    const {controller}=harness();await controller.open();const accepted=controller.snapshot().frame;
    controller.play(0);await controller.tick(500);expect(controller.snapshot().frame).toBe(accepted);
    await controller.tick(1900);expect(controller.snapshot().frame).toBe(accepted);
    await controller.tick(2000);expect(controller.snapshot().frame).not.toBe(accepted);expect(controller.snapshot().frame?.index).toBe(1);
  });
});

describe('Observatory source failure disclosure',()=>{
  it('does not call an empty failed catalog successfully checked evidence',async()=>{
    const {api,controller}=harness();
    vi.mocked(api.open).mockImplementationOnce(async requestId=>({requestId,observatory:{...summary('failed'),tracks:[],diagnostics:[{trackId:'history',category:'hash',message:'Resource changed'},{trackId:'states',category:'missing',message:'Resource absent'}]}}));
    await controller.open();expect(controller.snapshot().message).toContain('No recording was accepted');expect(controller.snapshot().summary?.diagnostics).toHaveLength(2);expect(api.frame).not.toHaveBeenCalled();expect(api.timeline).not.toHaveBeenCalled();
  });
});
