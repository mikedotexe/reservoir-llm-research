import { describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { invoke } from '@tauri-apps/api/core';
import JournalActionStrip from './JournalActionStrip';
import RunIdentity, { runIdentity } from './RunIdentity';
import { journalActionSummary } from './journalActionSummary';
import { actionResultReference, matchingActionResult, loadJournalActionResult } from './journalActionResult';
import { journal, reservoirSummary } from './myReservoirTestFixtures';
import type { SustainedActionReceipt, SustainedJournal } from './myReservoirTypes';
import type { SonarView } from './sonar';
import nativeView from './fixtures/experiments/experiment-view.json';
import nativeActions from './fixtures/experiments/experiment-actions.json';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));
const receipt = nativeActions.state.recentReceipts[1] as SustainedActionReceipt;
const view = nativeView as SonarView;
const entry = (patch: Partial<SustainedJournal> = {}): SustainedJournal => ({ ...journal(2), entryId: receipt.journalId,
  action: { body: 'I will investigate this difference.', rawTail: receipt.rawTail, request: receipt.request, rejection: null },
  actionReceipt: receipt, ...patch });

describe('entry action summary', () => {
  it('never treats prose or a scheduled conversation as an executed action', () => {
    expect(journalActionSummary({ ...journal(), text: 'I scanned and found a result. NEXT: SCAN' }).status).toBe('No action record');
    expect(journalActionSummary(entry({ checkIn: { ordinal: 1, scheduledSeconds: 3600, admittedElapsedMillis: 3600000, settingsRevision: 0, prompt: 'Hello', includeTelemetry: true } })).status).toBe('Actions off');
  });
  it('distinguishes pending, skipped, rejected and missing outcomes', () => {
    expect(journalActionSummary(entry({ actionReceipt: null, status: 'savedPendingApplication' })).status).toBe('Awaiting execution');
    expect(journalActionSummary(entry({ actionReceipt: null, status: 'skipped' })).status).toBe('Skipped');
    expect(journalActionSummary(entry({ actionReceipt: null })).status).toBe('Outcome unavailable');
    const rejected = entry({ actionReceipt: { ...receipt, status: 'rejected', rejection: '<script>invalid direction</script>', experiment: { reportId: null, outcome: null, explanation: 'Rejected direction' } } });
    expect(journalActionSummary(rejected).status).toBe('Rejected');
    const html = renderToStaticMarkup(<JournalActionStrip journal={rejected}/>);
    expect(html).toContain('View reason'); expect(html).toContain('&lt;script&gt;invalid direction&lt;/script&gt;');
    expect(html).not.toContain('<script>'); expect(html).not.toContain('Load matching measurements');
  });
  it('keeps measured, no-contrast, zero-stimulus and unresolved experiment results distinct', () => {
    const statuses = ['Measurements completed', 'No distinguishing contrast', 'No probe stimulus', 'Response unresolved'];
    (['measured', 'noContrast', 'noExcitation', 'unresolved'] as const).forEach((outcome, index) => {
      const summary = journalActionSummary(entry({ actionReceipt: { ...receipt, experiment: { ...receipt.experiment!, outcome } } }));
      expect(summary.status).toBe(statuses[index]); expect(summary.scope).toBe('On copies');
    });
  });
  it('labels NONE and missing peers without claiming an intervention or a successful reading', () => {
    const none = nativeActions.state.recentReceipts[0] as SustainedActionReceipt;
    expect(journalActionSummary(entry({ action: { ...entry().action!, request: none.request }, actionReceipt: none })).status).toBe('No additional intervention');
    const peers: SustainedActionReceipt = { ...receipt, request: { kind: 'readPeers' }, experiment: undefined, peerRead: { journalId: receipt.journalId, appliedStep: 7, snapshot: { attemptId: 2, observedStep: 6, capturedAtMs: '10', peers: [{ participant: 'glm', entry: null, unavailable: 'No applied entry' }] } } };
    expect(journalActionSummary(entry({ action: { ...entry().action!, request: peers.request }, actionReceipt: peers })).status).toBe('No peer entries available');
  });
  it('keeps real probe evidence separate from copied experiments and exposes original parameters', () => {
    const probe = nativeActions.state.recentReceipts[2] as SustainedActionReceipt;
    const current = entry({ action: { ...entry().action!, request: probe.request }, actionReceipt: probe });
    expect(journalActionSummary(current).scope).toBe('Live input');
    expect(journalActionSummary(current).status).toBe('Applied · step 10');
    const html = renderToStaticMarkup(<JournalActionStrip journal={current}/>);
    expect(html).toContain('Requested parameters'); expect(html).toContain('only the immediate paired effect is observed');
  });
});

describe('linked saved result', () => {
  it('matches identity and originating request instead of taking the newest result', () => {
    const reference = actionResultReference(receipt)!;
    expect(matchingActionResult(view, reference)).toEqual({ kind: 'experiment', report: view.modelExperiments![0] });
    expect(matchingActionResult(view, { ...reference, id: '0'.repeat(64) })).toBeNull();
    expect(matchingActionResult(view, { ...reference, step: reference.step + 1 })).toBeNull();
    expect(matchingActionResult({ ...view, modelExperiments: view.modelExperiments!.slice(1) }, reference)).toBeNull();
    expect(actionResultReference({ ...receipt, status: 'rejected' })).toBeNull();
  });
  it('loads passively and rejects a different session or generation', async () => {
    vi.mocked(invoke).mockResolvedValue(view);
    const session = { sessionId: view.sessionId, generation: view.generation };
    expect((await loadJournalActionResult(session, actionResultReference(receipt)!))?.kind).toBe('experiment');
    expect(invoke).toHaveBeenLastCalledWith('observe_sustained_sonar', { ...session, scan: false, question: null });
    await expect(loadJournalActionResult({ ...session, generation: 'another' }, actionResultReference(receipt)!)).rejects.toThrow('do not match');
    await expect(loadJournalActionResult({ ...session, sessionId: 'another' }, actionResultReference(receipt)!)).rejects.toThrow('do not match');
  });
});

describe('run identity', () => {
  it('keeps identity stable through restore, distinguishes runs, and retains exact model text', () => {
    const base = reservoirSummary(), config = { ...base.config, language: { backend: 'ollama' as const, model: 'gemma4:12b' } };
    const first = reservoirSummary({ config, sessionId: 'run-a' });
    expect(runIdentity(first).accent).toBe('gemma');
    expect(runIdentity({ ...first, generation: '2' } as typeof first)).toEqual(runIdentity(first));
    expect(runIdentity({ ...first, sessionId: 'run-b' }).label).not.toBe(runIdentity(first).label);
    for (const [model, accent] of [['glm-4.7-flash:latest', 'glm'], ['ministral-3:14b', 'mistral'], ['unknown-model', 'other']]) {
      expect(runIdentity({ ...first, config: { ...config, language: { ...config.language, model } } })).toMatchObject({ model, accent });
    }
    const html = renderToStaticMarkup(<RunIdentity summary={first}/>);
    expect(html).toContain('gemma4:12b'); expect(html).toContain('Session run-a · generation 1');
    expect(runIdentity(base).model).toBe('Scripted writing');
  });
});
