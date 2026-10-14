import { renderToStaticMarkup } from 'react-dom/server';
import { expect, it } from 'vitest';
import MyReservoirRecovery from './MyReservoirRecovery';
import { bundle, manifest, reservoirFixture } from './myReservoirTestFixtures';

it('keeps bounded received-response evidence distinct from saved journals, including incomplete attempts', () => {
  const { controller } = reservoirFixture();
  const state = { ...controller.snapshot(), recovered: {
    requestId: 'inspection', manifest: manifest(), report: bundle(), checkpoint: {},
    receivedResponses: { total: 75, truncated: true, entries: [
      { attemptId: '9007199254740993', observedStep: '50', complete: false, stopReason: 'length', stopReasonTruncated: true, tokenCount: '9223372036854775807', providerPromptEvaluation: { status: 'reported' as const, count: '18446744073709551615' } },
    ] },
  } };
  const html = renderToStaticMarkup(<MyReservoirRecovery state={state} controller={controller}/>);
  expect(html).toContain('<details><summary>Retained responses</summary>');
  expect(html).toContain('1 of 75 received responses shown · newest responses only');
  expect(html).toContain('A received response is separate from a saved or applied journal.');
  expect(html).toContain('Attempt 9007199254740993 · step 50');
  expect(html).toContain('Provider completeness: false · stop reason: length');
  expect(html).toContain('(truncated preview; full value retained in bundle)');
  expect(html).toContain('18446744073709551615 tokens');
  expect(html).toContain('output tokens: 9223372036854775807');
  expect(html).not.toContain('<details open');
});
