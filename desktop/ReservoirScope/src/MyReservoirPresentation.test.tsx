import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoir, { MyReservoirBoundary, MyReservoirClosePanel, MyReservoirStatus } from './MyReservoir';
import MyReservoirVisuals from './MyReservoirVisuals';
import { reservoirFixture, reservoirFrame, reservoirSummary, settle } from './myReservoirTestFixtures';
import { DEFAULT_SUSTAINED_CONFIG } from './myReservoirTypes';
import { DEFAULT_CAMERA } from './types';

describe('calm running view and visible recovery actions', () => {
  it('keeps ordinary writing inside a closed panel, then exposes a failed-save remedy', () => {
    const { controller } = reservoirFixture();
    const state = controller.snapshot();
    const pending = { operationId: 'owned-operation', turnId: 1, attemptId: 1, observedStep: 30, endpoint: '', model: '', state: 'requesting' as const };
    const normal = renderToStaticMarkup(<MyReservoirBoundary controller={controller} state={{ ...state, summary: reservoirSummary({ phase: 'awaitingLanguage', canPause: true, pendingLanguage: pending }) }}/>);
    expect(normal).toMatch(/^<details class="my-reservoir-boundary"><summary>Writing and feedback<\/summary>/);
    expect(normal).not.toContain('role="alert"');
    const failed = renderToStaticMarkup(<MyReservoirBoundary controller={controller} state={{ ...state, summary: reservoirSummary({ phase: 'storageBlocked', canStart: false, canRetrySave: true, pendingSave: { entryId: 'pending-entry', attemptId: 1, observedStep: 30 }, diagnostics: ['The journal could not be saved.'] }) }}/>);
    expect(failed).toMatch(/^<details class="my-reservoir-boundary needs-attention" open="">/);
    expect(failed).toContain('role="alert"');
    expect(failed).toContain('The journal could not be saved.');
    expect(failed).toContain('Retry save');
    expect(failed).not.toContain('Saved · feedback applied');
  });

  it('exposes paused prepared feedback and interruption even without a provider retry', () => {
    const { controller } = reservoirFixture(), state = controller.snapshot();
    for (const summary of [
      reservoirSummary({ phase: 'paused', pendingApplication: { entryId: 'saved-journal', attemptId: 1, observedStep: 30, intendedStep: 31 }, canSkipFeedback: true }),
      reservoirSummary({ phase: 'interrupted', canStart: false, diagnostics: ['Execution was interrupted. Review before restarting.'] }),
    ]) {
      const html = renderToStaticMarkup(<MyReservoirBoundary state={{ ...state, summary }} controller={controller}/>);
      expect(html).toMatch(/^<details class="my-reservoir-boundary needs-attention" open="">/);
      if (summary.pendingApplication) {
        expect(html).toContain('prepared for step 31');
        expect(html).toContain('not yet been recorded as applied');
        expect(html).toContain('Skip this saved feedback');
      } else expect(html).toContain('Execution was interrupted. Review before restarting.');
    }
  });

  it('keeps a retried provider failure in history after saved feedback is prepared, without a current failure alert', async () => {
    const { controller, push } = reservoirFixture();
    await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
    const diagnostic = 'The local model returned HTTP 503.';
    const pendingLanguage = { operationId: 'failed-attempt', turnId: 1, attemptId: 1, observedStep: 10, endpoint: 'http://127.0.0.1:54321', model: 'fixture', state: 'blocked' as const };
    push({ revision: '2', phase: 'attemptBlocked', step: 10, durableStep: 10, turnCount: 1, canStart: false, canRetryProvider: true, pendingLanguage, diagnostics: [diagnostic] });
    expect(renderToStaticMarkup(<MyReservoirClosePanel controller={controller}/>)).toContain(`<p role="alert" class="my-reservoir-error">${diagnostic}</p>`);
    push({ revision: '3', phase: 'paused', turnCount: 2, canStart: true, canRetryProvider: false, pendingLanguage: null, pendingApplication: { entryId: 'saved-after-retry', attemptId: 2, observedStep: 10, intendedStep: 11 }, canSkipFeedback: true, journalCount: 1 });
    const state = controller.snapshot();
    const boundary = renderToStaticMarkup(<MyReservoirBoundary state={state} controller={controller}/>);
    expect(boundary).toMatch(/^<details class="my-reservoir-boundary needs-attention" open="">/);
    expect(boundary).toContain('prepared for step 11');
    expect(boundary).not.toContain(diagnostic);
    expect(boundary).not.toContain('role="alert"');
    const close = renderToStaticMarkup(<MyReservoirClosePanel controller={controller}/>);
    expect(close).toContain('Saved feedback waiting');
    expect(close).not.toContain('role="alert"');
    const main = renderToStaticMarkup(<MyReservoir active controller={controller}/>);
    expect(main).toContain('Session messages · 1');
    expect(main).toContain(`<li>${diagnostic}</li>`);
    expect(main).not.toContain('role="alert"');
    expect(controller.snapshot().summary?.diagnostics).toEqual([diagnostic]);
  });

  it('shows a settled run limit calmly without treating historical provider diagnostics as a current failure', () => {
    const { controller } = reservoirFixture();
    const state = { ...controller.snapshot(), summary: reservoirSummary({ phase: 'budgetReached', canStart: false, diagnostics: ['Earlier HTTP 503; retained history.'] }) };
    const html = renderToStaticMarkup(<MyReservoirBoundary state={state} controller={controller}/>);
    expect(html).toMatch(/^<details class="my-reservoir-boundary"><summary>Writing and feedback<\/summary>/);
    expect(html).not.toContain('review needed');
    expect(html).not.toContain('role="alert"');
    expect(html).not.toContain('Earlier HTTP 503');
    const status = renderToStaticMarkup(<MyReservoirStatus state={state}/>);
    expect(status).toContain('Run limit reached');
    expect(status).toContain('Saved entries remain available to read and export.');
    expect(status).not.toContain('needs-attention');
    expect(status).not.toContain('all writing complete');
  });

  it.each([
    { pendingLanguage: { operationId: 'prepared', turnId: 1, attemptId: 1, observedStep: 30, endpoint: '', model: '', state: 'prepared' as const } },
    { pendingSave: { entryId: 'unsaved', attemptId: 1, observedStep: 30 } },
    { pendingApplication: { entryId: 'saved', attemptId: 1, observedStep: 30, intendedStep: 31 } },
    { canRetrySave: true }, { canRetryProvider: true }, { canSkipFeedback: true },
    { step: 31, durableStep: 30 }, { canPause: true },
  ])('keeps an unresolved limit visible: %j', unresolved => {
    const { controller } = reservoirFixture();
    const state = { ...controller.snapshot(), summary: reservoirSummary({ phase: 'budgetReached', canStart: false, ...unresolved }) };
    const boundary = renderToStaticMarkup(<MyReservoirBoundary state={state} controller={controller}/>);
    expect(boundary).toMatch(/^<details class="my-reservoir-boundary needs-attention" open="">/);
    expect(boundary).toContain('review needed');
    const status = renderToStaticMarkup(<MyReservoirStatus state={state}/>);
    expect(status).toContain('needs-attention');
    expect(status).not.toContain('Saved entries remain available to read and export.');
  });

  it('still exposes a current retry-save failure when a paused session offers a retry', () => {
    const { controller } = reservoirFixture();
    const state = { ...controller.snapshot(), summary: reservoirSummary({ phase: 'paused', canStart: false, canRetrySave: true, pendingSave: { entryId: 'unsaved', attemptId: 3, observedStep: 30 }, diagnostics: ['Journal save failed: permission denied.'] }) };
    const html = renderToStaticMarkup(<MyReservoirBoundary state={state} controller={controller}/>);
    expect(html).toContain('<p role="alert" class="my-reservoir-error">Journal save failed: permission denied.</p>');
    expect(html).toContain('Retry save');
    expect(html).not.toContain('Saved feedback waiting');
  });

  it('shows human duration and journal count while retaining exact clocks and limits', () => {
    const { controller } = reservoirFixture();
    const html = renderToStaticMarkup(<MyReservoirStatus state={{ ...controller.snapshot(), summary: reservoirSummary({ step: 33, durableStep: 30, simulatedTime: 11, elapsedSeconds: 3661.5, journalCount: 7, turnCount: 9 }) }}/>);
    const [primary, details] = html.split('<details class="my-reservoir-status-details">');
    expect(primary).toContain('Saved journals');
    expect(primary).toContain('>7<');
    expect(primary).toContain('1 hour 1 minute 1 second');
    expect(primary).toContain('Live step 33; saved through step 30.');
    expect(primary).not.toContain('Simulated seconds');
    expect(details).toContain('11.000');
    expect(details).toContain('3661.5 / 21600');
    expect(details).toContain('9 / 360');
    expect(details).toContain('33 / 10800');
  });

  it('puts the complete selected journal before history and live graphics without moving the reading or clock', async () => {
    const { controller, push, api } = reservoirFixture();
    await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
    push({ revision: '7', step: 7, journalCount: 2, turnCount: 2 });
    await controller.journals(); await controller.selectJournal('journal-1');
    push({ revision: '10', step: 10, journalCount: 3, turnCount: 3 });
    const before = controller.snapshot(), action = vi.spyOn(api, 'action');
    const html = renderToStaticMarkup(<MyReservoir active controller={controller}/>);
    const navigation = html.indexOf('aria-label="Journal reading position"');
    const prose = html.indexOf('class="my-reservoir-journal-prose"');
    const history = html.indexOf('aria-label="Journal history"');
    const visuals = html.indexOf('aria-label="Current reservoir visuals"');
    expect(navigation).toBeGreaterThan(0);
    expect(prose).toBeGreaterThan(navigation);
    expect(history).toBeGreaterThan(prose);
    expect(visuals).toBeGreaterThan(history);
    expect(html).toContain('Entry at step 3');
    expect(html).toContain('Live frame at step 10, separate from the selected journal.');
    expect(html).toContain('Current sensory fill</dt><dd>62.00%');
    expect(html).toContain('Follow latest · 1 new');
    expect(html).toContain('Saved sessions and recovery');
    expect(controller.snapshot()).toBe(before);
    expect(action).not.toHaveBeenCalled();
  });

  it('shows actual zero fill while preserving unavailable or invalid current values', () => {
    const base = { ...reservoirFixture().controller.snapshot(), summary: reservoirSummary({ step: 33 }) };
    for (const [fill, expected] of [[0, '0.00%'], [17.23456, '17.23%'], [null, 'Unavailable'], [NaN, 'Unavailable'], [101, 'Unavailable']] as const) {
      const html = renderToStaticMarkup(<MyReservoirStatus state={{ ...base, frame: { ...reservoirFrame(33), fillPercent: fill } }}/>);
      expect(html).toContain(`Current sensory fill</dt><dd>${expected}</dd>`);
      expect(html).not.toContain('fill rate');
    }
    const missing = renderToStaticMarkup(<MyReservoirStatus state={{ ...base, frame: null }}/>);
    expect(missing).toContain('Current sensory fill</dt><dd>Unavailable</dd>');
  });

  it('keeps the controller reference optional and current exact coordinates inside a closed disclosure', () => {
    const props = { frame: reservoirFrame(33), node: 0, onNode: () => {}, pose: DEFAULT_CAMERA, onPose: () => {}, tableOnly: true };
    const html = renderToStaticMarkup(<MyReservoirVisuals {...props} summary={reservoirSummary({ step: 33 })}/>);
    const [visible, exact] = html.split('<details class="my-reservoir-details"><summary>Current numerical measurements and exact inputs</summary>');
    expect(visible).not.toContain('68%');
    expect(visible).not.toContain('class="coordinate-inspector"');
    expect(exact).toContain('class="coordinate-inspector"');
    expect(exact).toContain('68% target with an error deadband from 64% to 72%');
    expect(exact).toContain('not a guaranteed outcome');
    expect(exact).toContain('0.125');
    const unregulated = renderToStaticMarkup(<MyReservoirVisuals {...props} summary={reservoirSummary({ config: { ...DEFAULT_SUSTAINED_CONFIG, regulationEnabled: false } })}/>);
    expect(unregulated).not.toContain('68%');
    expect(unregulated).not.toContain('deadband');
  });
});
