import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { FillMeter, ScalarTimeline, TurnIdentity, Verification } from './RecordedExperiments';
import type { TrackSummary, TurnView, VerificationReport } from './types';

describe('recorded evidence views', () => {
  const turn: TurnView = { index: 0, id: 'synthetic-test-turn', observedStep: '0', applicationStep: null,
    status: 'completed', backend: 'fixedTape', model: 'legacy-merged-label', configuredModel: 'configured-test-model',
    providerModel: null, requestStarted: null, tapePacketId: 'synthetic-packet', failurePhase: null,
    prompt: '', reply: null, rawReply: null, encodedFeatures: null, semanticVector: null, failure: null,
    journalSaved: null, requestedAction: null, chosenAction: null, contextKind: 'preparedExampleContext',
    memoryEntryIds: [], journalRelativePath: null };
  it('separates configured identity from unknown returned identity and tape provenance', () => {
    const html = renderToStaticMarkup(createElement(TurnIdentity, { turn }));
    expect(html).toContain('<dt>Recorded source</dt><dd>fixedTape</dd>');
    expect(html).toContain('<dt>Configured model</dt><dd>configured-test-model</dd>');
    expect(html).toContain('<dt>Returned provider model</dt><dd>Not recorded</dd>');
    expect(html).toContain('<dt>Request started</dt><dd>Not recorded</dd>');
    expect(html).toContain('<dt>Tape packet ID</dt><dd>synthetic-packet</dd>');
    expect(html).toContain('<dt>Journal saved</dt><dd>Not recorded</dd>');
    expect(html).not.toContain('legacy-merged-label');
  });
  it('preserves explicit false request flags and separately returned provider identity', () => {
    const html = renderToStaticMarkup(createElement(TurnIdentity, { turn: { ...turn, providerModel: 'returned-test-model', requestStarted: false, tapePacketId: null, failurePhase: 'before-request' } }));
    expect(html).toContain('<dt>Returned provider model</dt><dd>returned-test-model</dd>');
    expect(html).toContain('<dt>Request started</dt><dd>Recorded as no</dd>');
    expect(html).toContain('<dt>Tape packet ID</dt><dd>Not recorded</dd>');
    expect(html).toContain('<dt>Failure phase</dt><dd>before-request</dd>');
  });
  it('does not expose a future application receipt in the guided turn inspector', () => {
    const html = renderToStaticMarkup(createElement(TurnIdentity, { turn: { ...turn, observedStep: '30', applicationStep: '31' }, cursorStep: '30' }));
    expect(html).toContain('30 / Not reached at this cursor');
    expect(html).not.toContain('30 / 31');
  });
  it('renders missing fill as unavailable and real zero as a measured zero', () => {
    const missing = renderToStaticMarkup(createElement(FillMeter, { value: null }));
    const zero = renderToStaticMarkup(createElement(FillMeter, { value: 0 }));
    expect(missing).toContain('Not recorded');
    expect(missing).not.toContain('Exact:');
    expect(zero).toContain('0.00%');
    expect(zero).toContain('Exact: 0%');
  });
  it('shows only the backend verification scope and preserves escaped diagnostics', () => {
    const report: VerificationReport = { schema: 'test', status: 'incomplete', format: null, scope: 'Synthetic structural check only', checkedSteps: 0, checkedTurns: 0, sha256: null, modelsContacted: false, diagnostics: ['<script>untrusted record text</script>'] };
    const html = renderToStaticMarkup(createElement(Verification, { report, title: 'Incoming report' }));
    expect(html).toContain('Synthetic structural check only');
    expect(html).toContain('incomplete');
    expect(html).toContain('&lt;script&gt;untrusted record text&lt;/script&gt;');
    expect(html).not.toContain('<script>');
  });
  it('shows unavailable spectra without drawing a fabricated zero series', () => {
    const track: TrackSummary = { id: 'test', label: 'Synthetic unit test', frameCount: 2, turnCount: 0, backend: null, model: null, timelineStride: 1,
      timeline: [0, 1].map(index => ({ index, step: String(index), time: index, fillPercent: null, eigenvalues: null })) };
    const html = renderToStaticMarkup(createElement(ScalarTimeline, { track, selected: 0, kind: 'eigenvalue', onSelect: () => {} }));
    expect(html).toContain('Not recorded on the retained timeline');
    expect(html).not.toContain('<polyline');
    expect(html).not.toContain('<svg');
  });
});
