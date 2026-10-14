import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoir, { MyReservoirClosePanel, MyReservoirStatus } from './MyReservoir';
import MyReservoirRecovery from './MyReservoirRecovery';
import { DEFAULT_SUSTAINED_CONFIG } from './myReservoirTypes';
import { bundle, manifest, reservoirFixture, reservoirSummary, settle } from './myReservoirTestFixtures';

async function blockedFixture() {
  const fixture = reservoirFixture(), { controller, api, push } = fixture;
  await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
  push({ revision: '3246', phase: 'storageBlocked', step: 3240, durableStep: 3210, journalCount: 1, turnCount: 1, canStart: false, canPause: false, canRetrySave: true, pendingSave: { entryId: 'pending-2', observedStep: 3240, attemptId: 2 } });
  api.inspect = async (requestId, sessionId) => ({ requestId, manifest: { ...manifest(sessionId), revision: '3215', phase: 'running', step: 3210, durableStep: 3210, journalCount: 1 }, checkpoint: {}, report: { ...bundle(sessionId), step: 3210, journalCount: 1 } });
  await controller.selectJournal('journal-1');
  return fixture;
}

describe('sustained quota: volatile work and committed-prefix export', () => {
  it('identifies the exact live tail and loss risk without claiming a final checkpoint', async () => {
    const { controller } = await blockedFixture();
    const status = renderToStaticMarkup(<MyReservoirStatus state={controller.snapshot()}/>);
    expect(status).toContain('Live step 3240; retained through step 3210');
    const close = renderToStaticMarkup(<MyReservoirClosePanel controller={controller}/>);
    expect(close).toContain('Discarding may lose unsaved numerical steps 3211–3240');
    expect(close).toContain('Pending writing may also be lost');
    expect(close).toContain('does not confirm a final checkpoint');
    expect(close).not.toContain('The backend pauses at a durable boundary');
  });

  it('keeps the same status structure across ordinary durable flushes', () => {
    const { controller } = reservoirFixture();
    const render = (step: number, durableStep: number) => renderToStaticMarkup(<MyReservoirStatus state={{ ...controller.snapshot(), summary: reservoirSummary({ phase: 'running', canPause: true, step, durableStep }) }}/>);
    const before = render(59, 30), flushed = render(60, 60), next = render(61, 60);
    expect(before).toContain('Live step 59; retained through step 30.');
    expect(flushed).toContain('Live step 60; retained through step 60.');
    expect(next).toContain('Live step 61; retained through step 60.');
    // A checkpoint changes only the values; it must not insert/remove status
    // blocks and move the visualizations under an independent journal reader.
    const tags = (html: string) => html.match(/<\/?[a-z][^>]*>/g);
    expect(tags(before)).toEqual(tags(flushed)); expect(tags(next)).toEqual(tags(flushed));
  });

  it('shows a single unsaved step in close review without inventing a range or a durable-boundary loss', async () => {
    const { controller, push } = await blockedFixture();
    push({ revision: '3247', step: 3211, durableStep: 3210 });
    const single = renderToStaticMarkup(<MyReservoirClosePanel controller={controller}/>);
    expect(single).toContain('may lose unsaved numerical step 3211.'); expect(single).not.toContain('3211–3211');
    push({ revision: '3248', step: 3211, durableStep: 3211 });
    expect(renderToStaticMarkup(<MyReservoirClosePanel controller={controller}/>)).not.toContain('may lose unsaved numerical');
  });

  it('keeps inspected-prefix export available during a pending save and labels its narrower coverage', async () => {
    const { controller } = await blockedFixture(); await controller.inspect('personal-1');
    const recovery = renderToStaticMarkup(<MyReservoirRecovery state={controller.snapshot()} controller={controller}/>);
    expect(recovery).toMatch(/<button>Inspect current committed history<\/button>/);
    expect(recovery).toMatch(/<button>Export inspected bundle…<\/button>/);
    expect(recovery).toContain('This inspected bundle ends at step 3210; the current live step is 3240');
    expect(recovery).toContain('Unsaved numerical steps and writing are excluded');
    expect(recovery).toContain('historical metadata, not current execution status');
    const workspace = renderToStaticMarkup(<MyReservoir active controller={controller}/>);
    expect(workspace).toContain('To export earlier retained history while work is unsaved');
  });

  it('binds prefix export to inspected revision/hash while preserving live state and journal selection', async () => {
    const { controller, api, push } = await blockedFixture(); await controller.inspect('personal-1');
    push({ revision: '3247', diagnostics: ['A retry did not publish another checkpoint.'] });
    const before = controller.snapshot(), action = vi.spyOn(api, 'action');
    api.export = vi.fn(async (requestId, sessionId, generation, revision) => ({ requestId, sessionId, generation, revision: revision!, bundle: { ...bundle(sessionId), step: 3210, journalCount: 1 } }));
    await controller.exportRecovery();
    expect(api.export).toHaveBeenCalledWith(expect.any(String), 'personal-1', '1', '3215');
    expect(controller.snapshot().summary).toBe(before.summary);
    expect(controller.snapshot().frame).toBe(before.frame);
    expect(controller.snapshot().journal).toBe(before.journal);
    expect(controller.snapshot().recoveryMessage).toContain('Committed history through step 3210 exported');
    expect(controller.snapshot().recoveryMessage).toContain('Unsaved work is not included');
    expect(action).not.toHaveBeenCalled();
  });

  it('does not silently substitute an older durable snapshot in the main current-snapshot export', async () => {
    const { controller, api } = await blockedFixture();
    api.export = vi.fn(async (requestId, sessionId, generation) => ({ requestId, sessionId, generation, revision: '3215', bundle: { ...bundle(sessionId), step: 3210 } }));
    await controller.export();
    expect(api.export).toHaveBeenCalledWith(expect.any(String), 'personal-1', '1', '3246');
    expect(controller.snapshot().error).toContain('selected session snapshot');
    expect(controller.snapshot().exported).toBeNull();
  });

  it('cancellation or a changed durable snapshot retains readings and never reports a successful export', async () => {
    const { controller, api } = await blockedFixture(); await controller.inspect('personal-1');
    const before = controller.snapshot();
    api.export = async (requestId, sessionId, generation, revision) => ({ requestId, sessionId, generation, revision: revision!, bundle: null });
    await controller.exportRecovery(); expect(controller.snapshot().recoveryMessage).toContain('cancelled');
    api.export = async () => { throw new Error('The committed snapshot changed before export. Inspect again.'); };
    await controller.exportRecovery();
    expect(controller.snapshot().recoveryError).toContain('committed snapshot changed');
    expect(controller.snapshot().recoveryMessage).toBe('');
    expect(controller.snapshot().recovered).toBe(before.recovered);
    expect(controller.snapshot().journal).toBe(before.journal);
  });

  it('a failed checkpoint-and-quit preserves the unsaved tail and does not automatically discard', async () => {
    const { controller, api } = await blockedFixture(); const before = controller.snapshot();
    api.finishClose = vi.fn(async () => { throw new Error('Storage quota cannot fit this checkpoint.'); });
    await controller.finishClose(false);
    expect(api.finishClose).toHaveBeenCalledExactlyOnceWith(false);
    expect(controller.snapshot().summary).toBe(before.summary);
    expect(controller.snapshot().journal).toBe(before.journal);
    const close = renderToStaticMarkup(<MyReservoirClosePanel controller={controller}/>);
    expect(close).toContain('Storage quota cannot fit this checkpoint');
    expect(close).toContain('a failed save remains visible here');
    expect(close).toContain('steps 3211–3240');
  });
});
