import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { invoke } from '@tauri-apps/api/core';
import MyReservoir, { MyReservoirBoundary, MyReservoirStatus } from './MyReservoir';
import MyReservoirConfig from './MyReservoirConfig';
import MyReservoirJournals from './MyReservoirJournals';
import MyReservoirRecovery from './MyReservoirRecovery';
import { myReservoirApi } from './myReservoirApi';
import { bundle, manifest, reservoirFixture, reservoirSummary, settle } from './myReservoirTestFixtures';
import { DEFAULT_SUSTAINED_CONFIG, embeddingConfigurationError, type SustainedConfig, type SustainedSummary } from './myReservoirTypes';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true, Channel: class {} }));
const config: SustainedConfig = { ...DEFAULT_SUSTAINED_CONFIG, embeddingModel: 'nomic-embed-text:latest', language: { backend: 'ollama', endpoint: 'http://127.0.0.1:11434', model: 'writer' } };
const text = '<script>inert writing</script>\n\nNEXT: TUNE leak 0.75';
const pending = { attemptId: 3, observedStep: 30, responseText: text, reason: 'Embedding request timed out.', state: 'blocked' as const };
const blocked = (patch: Partial<SustainedSummary> = {}) => reservoirSummary({ config, phase: 'embeddingBlocked', step: 30, durableStep: 30, turnCount: 3, canStart: false, canRetryEmbedding: true, canSkipFeedback: true, pendingEmbedding: pending, ...patch });

describe('completed writing awaiting semantic encoding', () => {
  it('shows the exact retained response separately from a saved journal and offers encoding-only retry', () => {
    const { controller } = reservoirFixture(), state = { ...controller.snapshot(), summary: blocked() };
    const html = renderToStaticMarkup(<MyReservoirBoundary state={state} controller={controller}/>);
    expect(html).toMatch(/^<details class="my-reservoir-boundary needs-attention" open="">/);
    expect(html).toContain('Completed writing awaiting encoding');
    expect(html).toContain('Retry encoding uses this exact response without generating new writing.');
    expect(html).toContain('It has not become a saved journal or entered numerical feedback.');
    expect(html).toContain('&lt;script&gt;inert writing&lt;/script&gt;\n\nNEXT: TUNE leak 0.75');
    expect(html).not.toContain('<script>');
    expect(html).toContain('<button>Retry encoding</button>');
    expect(html).toContain('Skip this retained response');
    expect(html).not.toContain('Retry as a new attempt');
    expect(html).not.toContain('Writing needs attention');
    const journals = renderToStaticMarkup(<MyReservoirJournals state={state} controller={controller}/>);
    expect(journals).toContain('0 saved journals');
    expect(journals).toContain('Completed writing at step 30 · awaiting encoding; response retained.');
    expect(renderToStaticMarkup(<MyReservoirStatus state={state}/>)).toContain('Encoding needs attention');
  });

  it('shows encoding in progress without offering another retry or export', async () => {
    const { controller, push } = reservoirFixture();
    await controller.create(config); await settle();
    push(blocked({ revision: '2', phase: 'waitingForEmbedding', canPause: true, canRetryEmbedding: false, canSkipFeedback: false, pendingEmbedding: { ...pending, reason: null, state: 'requesting' }, diagnostics: ['An earlier encoding failure.'] }));
    const html = renderToStaticMarkup(<MyReservoir active controller={controller}/>);
    expect(html).toContain('The local embedding request is active.');
    expect(html).not.toContain('<button>Retry encoding</button>');
    expect(html).toContain('<button disabled="">Export saved session…</button>');
    expect(html).toContain('Cancel request and stop');
    expect(html).not.toContain('role="alert"');
    expect(html).toContain('encoding in progress');
  });

  it('keeps a paused response visible even when no retry currently fits the budget', () => {
    const { controller } = reservoirFixture(), state = { ...controller.snapshot(), summary: blocked({ phase: 'paused', canRetryEmbedding: false, pendingEmbedding: { ...pending, reason: null, state: 'prepared' } }) };
    const html = renderToStaticMarkup(<MyReservoirBoundary state={state} controller={controller}/>);
    expect(html).toMatch(/^<details class="my-reservoir-boundary needs-attention" open="">/);
    expect(html).toContain('Retained completed response');
    expect(html).toContain('No encoding request is active.');
    expect(html).not.toContain('<button>Retry encoding</button>');
    expect(html).not.toContain('role="alert"');
  });

  it('uses the dedicated retry operation without increasing the writing attempt count', async () => {
    const { api, controller, push } = reservoirFixture();
    await controller.create(config); await settle();
    push(blocked({ revision: '2' }));
    const action = vi.spyOn(api, 'action');
    expect(await controller.action('retryEmbedding')).toBe(true);
    expect(action).toHaveBeenCalledWith('retryEmbedding', expect.any(String), 'personal-1', '1', null, 3);
    expect(controller.snapshot().summary?.turnCount).toBe(3);
    expect(controller.snapshot().summary?.pendingEmbedding?.responseText).toBe(text);
    push({ revision: '4', phase: 'paused', pendingEmbedding: null, canRetryEmbedding: false, pendingApplication: { entryId: 'same-writing', attemptId: 3, observedStep: 30, intendedStep: 31 }, journalCount: 1 });
    const html = renderToStaticMarkup(<MyReservoirBoundary state={controller.snapshot()} controller={controller}/>);
    expect(html).toContain('prepared for step 31');
    expect(html).not.toContain('Retry encoding');
    expect(controller.snapshot().summary?.turnCount).toBe(3);
  });

  it('requires the backend retry capability and binds skip to the retained attempt', async () => {
    const { api, controller, push } = reservoirFixture();
    await controller.create(config); await settle();
    push(blocked({ revision: '2', canRetryEmbedding: false }));
    const action = vi.spyOn(api, 'action');
    expect(await controller.action('retryEmbedding')).toBe(false);
    expect(action).not.toHaveBeenCalled();
    await controller.action('skipFeedback');
    expect(action).toHaveBeenCalledWith('skipFeedback', expect.any(String), 'personal-1', '1', null, 3);
  });

  it('exports a blocked retained response without dispatching a retry', async () => {
    const { api, controller, push } = reservoirFixture();
    await controller.create(config); await settle(); push(blocked({ revision: '2' }));
    const action = vi.spyOn(api, 'action'), exported = vi.spyOn(api, 'export');
    const html = renderToStaticMarkup(<MyReservoir active controller={controller}/>);
    expect(html).toContain('<button>Export saved session…</button>');
    await controller.export();
    expect(exported).toHaveBeenCalledWith(expect.any(String), 'personal-1', '1', '2');
    expect(action).not.toHaveBeenCalled();
    expect(controller.snapshot().summary?.pendingEmbedding?.responseText).toBe(text);
  });

  it('restores retained completed writing without starting encoding or generation', async () => {
    const { api, controller, nextSequence } = reservoirFixture();
    const summary = blocked({ generation: '2', revision: '8', phase: 'paused' });
    api.restore = async requestId => ({ requestId, snapshotSequence: nextSequence(), summary, frame: null, closeRequested: false });
    api.get = async requestId => ({ requestId, snapshotSequence: nextSequence(), summary, frame: null, closeRequested: false });
    const action = vi.spyOn(api, 'action');
    await controller.inspect('personal-1'); await controller.restore(); await settle();
    expect(controller.snapshot().summary?.pendingEmbedding?.responseText).toBe(text);
    expect(controller.snapshot().recoveryMessage).toContain('Retry encoding explicitly');
    expect(action).not.toHaveBeenCalled();
  });

  it('rejects malformed or contradictory encoding snapshots without replacing accepted state', async () => {
    const { controller, channel, nextSequence } = reservoirFixture();
    await controller.create(config); await settle(); const accepted = controller.snapshot().summary, c = channel();
    for (const patch of [
      { pendingEmbedding: null },
      { pendingEmbedding: { ...pending, attemptId: 0 } },
      { pendingEmbedding: { ...pending, observedStep: 29 } },
      { pendingEmbedding: { ...pending, state: 'requesting' as const } },
      { pendingSave: { entryId: 'conflicting', attemptId: 3, observedStep: 30 } },
    ]) {
      c.listener({ requestId: c.id, snapshotSequence: nextSequence(), summary: blocked({ revision: '2', ...patch }), frame: null, closeRequested: false });
      expect(controller.snapshot().summary).toBe(accepted);
      expect(controller.snapshot().error).toContain('retained encoding state');
    }
  });

  it('maps retry encoding to its own IPC command', async () => {
    vi.mocked(invoke).mockResolvedValueOnce({});
    await myReservoirApi.action('retryEmbedding', 'request-1', 'session-1', 'generation-2');
    expect(invoke).toHaveBeenLastCalledWith('retry_sustained_embedding', { requestId: 'request-1', sessionId: 'session-1', generation: 'generation-2' });
  });
});

describe('semantic setup and saved response inspection', () => {
  it('blocks new offline-writing embedding configurations before mutation and explains the remedy', async () => {
    const { api, controller } = reservoirFixture(), create = vi.spyOn(api, 'create');
    const incompatible = { ...DEFAULT_SUSTAINED_CONFIG, embeddingModel: 'nomic-embed-text:latest' };
    expect(await controller.create(incompatible)).toBe(false);
    expect(create).not.toHaveBeenCalled();
    expect(controller.snapshot().error).toContain('requires My local Ollama model');
    const html = renderToStaticMarkup(<MyReservoirConfig config={incompatible} setConfig={() => {}} disabled={false}/>);
    expect(html).toContain('Choose local model writing or Surface statistics.');
    expect(html).toContain('Text reduction<select aria-invalid="true"');
    expect(embeddingConfigurationError(config)).toBeNull();
    expect(embeddingConfigurationError(DEFAULT_SUSTAINED_CONFIG)).toBeNull();
    expect(DEFAULT_SUSTAINED_CONFIG.embeddingModel).toBeUndefined();
  });

  it('renders recovered response previews as inert evidence and marks truncation', () => {
    const { controller } = reservoirFixture();
    const state = { ...controller.snapshot(), recovered: { requestId: 'inspection', manifest: manifest(), report: bundle(), checkpoint: {}, receivedResponses: { total: 1, truncated: false, entries: [{ attemptId: '3', observedStep: '30', complete: true, stopReason: 'stop', stopReasonTruncated: false, tokenCount: '100', responseText: text, responseTextTruncated: true }] } } };
    const html = renderToStaticMarkup(<MyReservoirRecovery state={state} controller={controller}/>);
    expect(html).toContain('Received response text · truncated preview');
    expect(html).toContain('The full response remains in the verified bundle.');
    expect(html).toContain('&lt;script&gt;inert writing&lt;/script&gt;');
    expect(html).not.toContain('<script>');
    expect(html).toContain('A received response is separate from a saved or applied journal.');
  });
});
