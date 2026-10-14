import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import MyReservoir, { MyReservoirBoundary, MyReservoirClosePanel, MyReservoirStatus } from './MyReservoir';
import { reservoirFixture, reservoirSummary, settle } from './myReservoirTestFixtures';
import { DEFAULT_SUSTAINED_CONFIG } from './myReservoirTypes';

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
    expect(failed).toContain('Retry durable save');
    expect(failed).not.toContain('Saved and applied');
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
        expect(html).toContain('Skip this saved feedback explicitly');
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
    expect(close).toContain('Saved feedback awaiting application');
    expect(close).not.toContain('role="alert"');
    const main = renderToStaticMarkup(<MyReservoir active controller={controller}/>);
    expect(main).toContain('Session diagnostics · 1 retained messages');
    expect(main).toContain(`<li>${diagnostic}</li>`);
    expect(main).not.toContain('role="alert"');
    expect(controller.snapshot().summary?.diagnostics).toEqual([diagnostic]);
  });

  it('keeps budget-only attention open without treating historical provider diagnostics as a current failure', () => {
    const { controller } = reservoirFixture();
    const state = { ...controller.snapshot(), summary: reservoirSummary({ phase: 'budgetReached', canStart: false, diagnostics: ['Earlier HTTP 503; retained history.'] }) };
    const html = renderToStaticMarkup(<MyReservoirBoundary state={state} controller={controller}/>);
    expect(html).toMatch(/^<details class="my-reservoir-boundary needs-attention" open="">/);
    expect(html).toContain('The session is held.');
    expect(html).not.toContain('role="alert"');
    expect(html).not.toContain('Earlier HTTP 503');
  });

  it('still exposes a current retry-save failure when a paused session offers a retry', () => {
    const { controller } = reservoirFixture();
    const state = { ...controller.snapshot(), summary: reservoirSummary({ phase: 'paused', canStart: false, canRetrySave: true, pendingSave: { entryId: 'unsaved', attemptId: 3, observedStep: 30 }, diagnostics: ['Journal save failed: permission denied.'] }) };
    const html = renderToStaticMarkup(<MyReservoirBoundary state={state} controller={controller}/>);
    expect(html).toContain('<p role="alert" class="my-reservoir-error">Journal save failed: permission denied.</p>');
    expect(html).toContain('Retry durable save');
    expect(html).not.toContain('Saved feedback awaiting application');
  });

  it('shows human duration and journal count while retaining exact clocks and limits', () => {
    const { controller } = reservoirFixture();
    const html = renderToStaticMarkup(<MyReservoirStatus state={{ ...controller.snapshot(), summary: reservoirSummary({ step: 33, durableStep: 30, simulatedTime: 11, elapsedSeconds: 3661.5, journalCount: 7, turnCount: 9 }) }}/>);
    const [primary, details] = html.split('<details class="my-reservoir-status-details">');
    expect(primary).toContain('Saved journals');
    expect(primary).toContain('>7<');
    expect(primary).toContain('1 hour 1 minute 1 second');
    expect(primary).toContain('Live step 33; retained through step 30.');
    expect(primary).not.toContain('Simulated seconds');
    expect(details).toContain('11.000');
    expect(details).toContain('3661.5 / 21600');
    expect(details).toContain('9 / 360');
    expect(details).toContain('33 / 10800');
  });
});
