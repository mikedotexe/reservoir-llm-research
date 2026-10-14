import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import ResponseWorkspace, { ResponseExactCoordinates, ResponseReceiptDetail, ResponseTimelinePlot, responsePlotPositions } from './ResponseWorkspace';
import type { ResponseEventDetail, ResponseFrame, ResponseSummary } from './responseTypes';

function summary(kind: 'native' | 'simulation' = 'native'): ResponseSummary {
  return { responseId: 'test', kind, origin: 'bundled', filename: 'fixture.json', sha256: 'a'.repeat(64), sizeBytes: 1234, frameCount: 3, nodeCount: 128, fixedDeltaScale: 0.001, firstLabel: kind === 'native' ? 'Ordinary step' : 'Control', secondLabel: kind === 'native' ? 'Applied result' : 'Perturbed', returnThreshold: kind === 'native' ? null : 0.0001, provenance: [], missingness: [], metadata: {}, events: [], timeline: ['18446744073709551610', '18446744073709551611', '18446744073709551615'].map((position, index) => ({ index, position, l2: [0.001, 0.00005, 0.00002][index], receiptIndex: kind === 'native' ? index : null })) };
}
function frame(): ResponseFrame {
  const delta = [0.00012345678901234567, ...Array<number>(127).fill(0)];
  return { index: 0, position: '18446744073709551610', l2: delta[0], first: Array(128).fill(0), second: delta, delta, direction: [1, ...Array<number>(127).fill(0)], realizedNoise: Array(128).fill(0), metadata: {} };
}
describe('response timeline identity and meaning', () => {
  it('spaces adjacent u64 successful-step IDs without first rounding them to JS numbers', () => {
    expect(responsePlotPositions(summary())).toEqual([0, 0.2, 1]);
    const one = summary(); one.timeline = one.timeline.slice(0, 1); one.frameCount = 1;
    expect(responsePlotPositions(one)).toEqual([0]);
  });
  it('draws native immediate sizes as separate bars with exact IDs and no recovery line', () => {
    const html = renderToStaticMarkup(createElement(ResponseTimelinePlot, { summary: summary(), selected: 1 }));
    expect(html.match(/class="response-plot-bar"/g)).toHaveLength(3); expect(html).not.toContain('<polyline');
    expect(html).toContain('18446744073709551611'); expect(html).toContain('18446744073709551615'); expect(html).toContain('not recovery'); expect(html).toContain('role="img"'); expect(html).not.toContain('response-plot-threshold');
  });
  it('keeps simulation samples ordinal and labels the fixed return threshold without inventing measured time', () => {
    const simulated = summary('simulation'); simulated.timeline = simulated.timeline.map((point, index) => ({ ...point, position: String(200 + index) }));
    expect(responsePlotPositions(simulated)).toEqual([0, 0.5, 1]);
    const html = renderToStaticMarkup(createElement(ResponseTimelinePlot, { summary: simulated, selected: 1 }));
    expect(html).toContain('<polyline'); expect(html).toContain('response-plot-threshold'); expect(html).toContain('Return threshold 0.0001'); expect(html).toContain('not measured seconds'); expect(html).toContain('0 · displacement applied'); expect(html).not.toContain('response-plot-bar');
  });
  it('does not draw an event-only bundle as a zero-valued measurement', () => {
    const events = summary(); events.timeline = []; events.frameCount = 0;
    expect(renderToStaticMarkup(createElement(ResponseTimelinePlot, { summary: events, selected: 0 }))).toBe('');
  });
});
describe('exact response evidence', () => {
  it('exposes all original paired coordinates, noise and direction without scaling exact numbers', () => {
    const html = renderToStaticMarkup(createElement(ResponseExactCoordinates, { summary: summary(), frame: frame(), node: 0, onSelect: () => {} }));
    expect(html).toContain('0.00012345678901234567'); expect(html).toContain('Ordinary step'); expect(html).toContain('Applied result'); expect(html).toContain('Retained Float32 action difference');
    expect(html).toContain('Actual step noise'); expect(html).toContain('Requested direction weight'); expect(html.match(/Inspect response coordinate /g)).toHaveLength(128); expect(html).toContain('scope="col"'); expect(html).toContain('no display normalization or smoothing');
  });
  it('keeps simulation terminology independent of native receipt claims', () => {
    const f = frame(); f.direction = null; f.realizedNoise = null;
    const html = renderToStaticMarkup(createElement(ResponseExactCoordinates, { summary: summary('simulation'), frame: f, node: 127, onSelect: () => {} }));
    expect(html).toContain('Control'); expect(html).toContain('Perturbed'); expect(html).toContain('Retained paired difference'); expect(html).not.toContain('Float32 action'); expect(html).not.toContain('Actual step noise');
  });
  it('discloses rejected boundary values without calling them an applied state', () => {
    const detail: ResponseEventDetail = { index: 3, status: 'headroom_rejected', hasState: false, isBoundary: true, metadata: { Reason: '<not an instruction>' }, direction: Array(128).fill(0), realizedNoise: Array(128).fill(0), first: Array(128).fill(0), second: Array(128).fill(0), delta: Array(128).fill(0) };
    const html = renderToStaticMarkup(createElement(ResponseReceiptDetail, { event: detail, node: 0 }));
    expect(html).toContain('This boundary was rejected'); expect(html).toContain('do not establish an applied action'); expect(html).toContain('&lt;not an instruction&gt;');
    detail.status = 'accepted'; detail.isBoundary = false; detail.first = null; detail.second = null; detail.delta = null; detail.realizedNoise = null;
    const admission = renderToStaticMarkup(createElement(ResponseReceiptDetail, { event: detail, node: 0 }));
    expect(admission).toContain('does not establish an applied state change'); expect(admission).not.toContain('Boundary result');
  });
  it('requires explicit source opening and removes all graphics while inactive', () => {
    const html = renderToStaticMarkup(createElement(ResponseWorkspace, { active: true }));
    expect(html).toContain('Load bundled native receipts'); expect(html).toContain('Open native receipt file'); expect(html).toContain('Load bundled simulation'); expect(html).not.toContain('<canvas'); expect(html).not.toContain('<svg');
    expect(renderToStaticMarkup(createElement(ResponseWorkspace, { active: false }))).toBe('');
  });
});
