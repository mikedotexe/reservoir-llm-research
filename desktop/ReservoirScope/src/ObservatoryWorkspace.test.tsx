import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import ObservatoryWorkspace, { timelineSegments } from './ObservatoryWorkspace';
import type { ObservatoryTimelinePoint } from './observatoryTypes';

function point(position:number,fillPct:number|null,breakBefore=false):ObservatoryTimelinePoint {
  return {index:position,position,fillPct,breakBefore,tUtc:null,sessionId:null,fillRatePctPerS:null,cascade:null,intervalSeconds:null,stateRms:null,pc:null,nodeValue:null};
}
const fill=(point:ObservatoryTimelinePoint)=>point.fillPct;

describe('retained Observatory timeline segmentation',()=>{
  it('breaks between sessions while retaining the first value in each new session',()=>{
    const points=[point(0,60),point(1.25,63),point(100,72,true),point(102.5,68)];
    expect(timelineSegments(points,fill)).toEqual([[[0,60],[1.25,63]],[[100,72],[102.5,68]]]);
    expect(points.map(item=>item.position)).toEqual([0,1.25,100,102.5]);
  });
  it('does not connect through missing or nonfinite values and retains isolated samples',()=>{
    expect(timelineSegments([point(0,null),point(1,0),point(2,null),point(3,50),point(4,NaN),point(5,70),point(6,Infinity),point(7,null)],fill)).toEqual([[[1,0]],[[3,50]],[[5,70]]]);
  });
  it('preserves signed coordinate values and ordinal positions without smoothing',()=>{
    const points=[point(0,null),point(1,null),point(2,null)];points[0].nodeValue=-0.123456789012345;points[1].nodeValue=0;points[2].nodeValue=1;
    expect(timelineSegments(points,item=>item.nodeValue)).toEqual([[[0,-0.123456789012345],[1,0],[2,1]]]);
    expect(timelineSegments([],fill)).toEqual([]);expect(timelineSegments([point(0,null)],fill)).toEqual([]);
  });
});

describe('Observatory workspace boundaries',()=>{
  it('labels the recordings as independent before opening and renders no invented plot',()=>{
    const html=renderToStaticMarkup(createElement(ObservatoryWorkspace,{active:true}));
    expect(html).toContain('aria-labelledby="observatory-title"');expect(html).toContain('two independent recordings');
    expect(html).toContain('per-row timestamps and paired fill are unavailable');expect(html).toContain('Exact values without 3D');
    expect(html).not.toContain('<svg');expect(html).not.toContain('<canvas');
  });
  it('routes directly to preparation without opening recordings or response graphics',()=>{
    const html=renderToStaticMarkup(createElement(ObservatoryWorkspace,{active:true,view:'preparation'}));
    expect(html).toContain('<button aria-current="page">Preparation history</button>');
    expect(html.match(/class="preparation-history"/g)).toHaveLength(1);
    expect(html).not.toContain('per-row timestamps and paired fill are unavailable');
    expect(html).not.toContain('<canvas'); expect(html).not.toContain('<svg');
  });
  it('renders no hidden workspace graphics',()=>{
    const html=renderToStaticMarkup(createElement(ObservatoryWorkspace,{active:false}));
    expect(html).toContain('hidden');expect(html).not.toContain('<canvas');expect(html).not.toContain('<svg');expect(html).not.toContain('<button');
  });
});
