import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import RecordedFillSphere, { type RecordedFillSphereProps } from './RecordedFillSphere';
const render=(props:RecordedFillSphereProps)=>renderToStaticMarkup(createElement(RecordedFillSphere,props));
describe('accessible retained fill evidence',()=>{
  it('distinguishes missing data from a real zero-volume measurement',()=>{
    const missing=render({sample:null}); expect(missing).toContain('No retained fill measurement');expect(missing).toContain('Unavailable');expect(missing).not.toContain('0.00');
    const zero=render({sample:{fillPercent:0,provenance:'Retained zero'}});expect(zero).toContain('0.00');expect(zero).toContain('Exact retained fill');expect(zero).toContain('0%');
  });
  it('retains exact values, source and explicit clock label when graphics are disabled',()=>{
    const html=render({sample:{fillPercent:68.1234567890123,provenance:'Frozen observation <data>',sourceTimeLabel:'recorded sample 42'},tableOnly:true});
    expect(html).toContain('68.1234567890123%');expect(html).toContain('recorded sample 42');expect(html).toContain('Frozen observation &lt;data&gt;');expect(html).toContain('Exact values view');expect(html).toContain('cube root');expect(html).not.toContain('Date.now');expect(html).not.toContain('Lose fill graphics context');
  });
  it('withholds invalid geometry and unprovided reference claims',()=>{
    const html=render({sample:{fillPercent:101,provenance:'Invalid display input'}});expect(html).toContain('has not been clamped');expect(html).toContain('No retained reference configuration');expect(html).not.toContain('68%');expect(html).toContain('Not supplied');
  });
  it('exposes supplied reference values and prevents a controller-state inference',()=>{
    const html=render({sample:{fillPercent:62,provenance:'Retained'},references:{shelfMinPercent:58,targetPercent:68,shelfMaxPercent:72,strongRailPercent:74,warningRailPercent:78,provenance:'Snapshot configuration'}});
    for(const value of [58,68,72,74,78])expect(html).toContain(`${value}%`);expect(html).toContain('does not establish historical controller stage');expect(html).toContain('Snapshot configuration');
  });
  it('renders nothing for an inactive workspace',()=>{expect(render({sample:{fillPercent:68,provenance:'Retained'},active:false})).toBe('');});
});
