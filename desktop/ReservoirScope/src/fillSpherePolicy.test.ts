import { describe, expect, it, vi } from 'vitest';
import { createFillScheduler, fillDrawingBufferSize } from './fillSpherePolicy';
function harness() {
  let id=0, current=0; const queue = new Map<number,()=>void>(); const values: number[]=[];
  const request=vi.fn((callback:()=>void)=>{queue.set(++id,callback);return id;});
  const scheduler=createFillScheduler({request,cancel:frame=>{queue.delete(frame);},draw:()=>{values.push(current);}}, {active:true,documentVisible:true,inViewport:true,contextAvailable:true});
  return { scheduler, queue, values, request, update:(value:number)=>{current=value;scheduler.invalidate();}, flush:()=>{const callbacks=[...queue.values()];queue.clear();callbacks.forEach(callback=>callback());} };
}
describe('fill renderer suspension and raster bounds', () => {
  it('coalesces recorded updates without smoothing or an idle animation loop', () => {
    const h=harness();h.update(58);h.update(68);h.update(78);expect(h.queue.size).toBe(1);h.flush();expect(h.values).toEqual([78]);expect(h.queue.size).toBe(0);h.flush();expect(h.values).toEqual([78]);
  });
  it('requires active workspace, visible document, viewport intersection and recovered context', () => {
    const h=harness();h.update(58);h.scheduler.setVisibility({active:false,documentVisible:false,inViewport:false,contextAvailable:false});h.update(74);h.flush();expect(h.values).toEqual([]);
    h.scheduler.setVisibility({documentVisible:true,inViewport:true,contextAvailable:true});h.flush();expect(h.values).toEqual([]);
    h.scheduler.setVisibility({active:true});h.flush();expect(h.values).toEqual([74]);expect(h.queue.size).toBe(0);
  });
  it('disposes a pending frame permanently, including after attempted restoration', () => {
    const h=harness();h.update(68);h.scheduler.dispose();h.update(70);h.scheduler.setVisibility({active:true,contextAvailable:true});h.flush();expect(h.values).toEqual([]);expect(h.queue.size).toBe(0);
  });
  it('caps DPR, physical pixels and hardware dimensions without modifying fill', () => {
    for (const [w,h,dpr,limit] of [[512,512,4,4096],[8000,4000,4,4096],[600,1200,3,256],[0.5,0.25,1,4096]]) {
      const size=fillDrawingBufferSize(w,h,dpr,limit)!;expect(size.width*size.height).toBeLessThanOrEqual(1_000_000);expect(Math.max(size.width,size.height)).toBeLessThanOrEqual(limit);
      expect(size.width).toBeGreaterThanOrEqual(1);expect(size.height).toBeGreaterThanOrEqual(1);
    }
    expect(fillDrawingBufferSize(400,300,4)).toEqual({width:800,height:600});
    expect(fillDrawingBufferSize(0,300,1)).toBeNull();
  });
});
