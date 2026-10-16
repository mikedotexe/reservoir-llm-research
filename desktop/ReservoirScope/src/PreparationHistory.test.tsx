import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import PreparationHistory, { PreparationHistoryView } from './PreparationHistory';
import type { PreparationState } from './preparationController';
import type { PreparationAttempt } from './preparationTypes';

const attempt: PreparationAttempt = { startedAtUtc: null, finishedAtUtc: null, exitCode: 1, record: '../../historical.json', verified: true, verification: 'Verified 60 steps.', sha256: 'b'.repeat(64), status: 'failed', steps: 60, journalCounts: { left: 2, right: 1 }, requestCount: 4 };
const summary = { id: 'retry', kind: 'retry', title: 'Separate retry', status: 'failed', filename: 'retry.json', sha256: 'a'.repeat(64), sizeBytes: 10, summary: 'Partial recording retained.' } as const;
function state(): PreparationState { return { reports: [summary], examples: [{ id: 'example-preparation-1', title: 'Attempt 1', provenance: 'failed · 30 steps', format: 'actions' }], loaded: true, busy: false, pendingId: null, exporting: false, error: '', message: '', selected: { summary, retainedExampleId: 'example-model-observation-active', retainedExampleDiagnostic: null, report: { schema: 'report', status: 'failed', scope: 'Synthetic teaching fixture', inspectionScope: 'Historical metadata, not numerical replay.', sections: [{ title: 'Source', fields: [{ label: 'Historical endpoint', value: '<script>unsafe()</script> http://127.0.0.1:1234' }] }], attempts: [attempt] } } }; }
function render(s = state(), onOpenExample?: (id: string) => void) { return renderToStaticMarkup(<PreparationHistoryView state={s} refresh={() => {}} select={async () => {}} exportReport={() => {}} onOpenExample={onOpenExample}/>); }
describe('preparation history evidence presentation', () => {
  it('keeps failed outcome separate from passed historical verification and exact counts', () => {
    const html = render(); expect(html).toContain('Recorded status: failed'); expect(html).toContain('Passed · retained receipt'); expect(html).toContain('left: 2 · right: 1'); expect(html).toContain('Recorded requests'); expect(html).toContain('Partial recording retained.'); expect(html).toContain('does not turn a failed or partial run into a completed generation'); expect(html).toContain(summary.sha256);
  });
  it('renders missing receipts as unavailable without converting missingness into zero or failed', () => {
    const s = state(); s.selected!.report.attempts = [{ ...attempt, verified: null, steps: null, journalCounts: null, requestCount: null }];
    const html = render(s); expect(html).not.toContain('Passed · retained receipt'); expect(html).not.toContain('Failed · retained receipt'); expect(html).toContain('<dt>Recorded requests</dt><dd>Not retained</dd>'); expect(html).toContain('<dt>Saved journals by arm</dt><dd>Not retained</dd>');
  });
  it('keeps historical text inert, errors visible, and optional record buttons meaningful', () => {
    const s = state(); s.error = 'Package identity changed'; const html = render(s); expect(html).toContain('role="alert"'); expect(html).toContain(s.error); expect(html).toContain('&lt;script&gt;'); expect(html).not.toContain('<script>'); expect(html).not.toContain('href='); expect(html).toContain('../../historical.json'); expect(html).not.toContain('Open retained attempt'); expect(render(s, () => {})).toContain('Open retained attempt'); expect(render(s, () => {})).toContain('Open retained retry recording'); s.selected!.retainedExampleId = null; expect(render(s, () => {})).not.toContain('Open retained retry recording');
  });
  it('emits no UI or fixed DOM ids while inactive', () => {
    expect(renderToStaticMarkup(<PreparationHistory active={false}/>)).toBe(''); expect(render()).not.toMatch(/\sid=/);
  });
  it('allows the canonical Observatory reader to start expanded', () => {
    expect(render()).not.toContain('class="preparation-history" open=""');
    const html = renderToStaticMarkup(<PreparationHistoryView state={state()} refresh={() => {}} select={async () => {}} exportReport={() => {}} initiallyOpen/>);
    expect(html).toContain('class="preparation-history" open=""');
  });
});
