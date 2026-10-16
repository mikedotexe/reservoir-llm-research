import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import FreshExperiments, { FreshJournal, FreshRecovery, FreshSaveStatus } from './FreshExperiments';
import { FreshController, type FreshState } from './freshController';
import { DEFAULT_FRESH_CONFIG } from './freshTypes';

function state(): FreshState {
  return { ...new FreshController().snapshot(), summary: { sessionId: 'new-1', generation: '1', revision: '3', config: { ...DEFAULT_FRESH_CONFIG, recipe: 'journalE' }, phase: 'awaitingJournalSave', step: 30, durableStep: 29, stepLimit: 120, frameCount: 30, turnCount: 0, journalCount: 0, unsavedRecord: true, pendingWrites: false, canStep: false, canRun: false, canExport: false, explorationControls: null, canRequestJournal: false, action: null, tracks: [{ id: 'right', label: 'Current', stage: 5, frameCount: 30, turnCount: 0, journalCount: 0, status: 'stopped', failure: null, observationChannel: 'sensory', action: null }], saveError: 'Disk full', libraryEntryId: null, diagnostics: [] }, pendingJournal: { arm: 'right', id: 'entry1', actionId: 1, observedStep: 30, prompt: '<script>do not execute</script>', text: 'Fixed candidate', sha256: 'a'.repeat(64), relativePath: '../../inert-label.txt' } };
}
const controller = new FreshController();
describe('fresh experiment scientific presentation', () => {
  it('does not render inactive graphics or imply a run exists before explicit creation', () => {
    expect(renderToStaticMarkup(<FreshExperiments active={false}/>)).toBe(''); const html = renderToStaticMarkup(<FreshExperiments active/>); expect(html).toContain('Choose an experiment, then create it.'); expect(html).toContain('After creating it, choose Step once or Run to begin'); expect(html).not.toContain('scene-canvas');
  });
  it('keeps failed candidate text ineligible and exposes explicit retry or terminal failure choice', () => {
    const html = renderToStaticMarkup(<FreshJournal state={state()} controller={controller}/>);
    expect(html).toContain('Retry right journal save'); expect(html).toContain('Stop and retain failed save'); expect(html).toContain('Save not yet confirmed'); expect(html).toContain('clock is paused'); expect(html).toContain('&lt;script&gt;'); expect(html).not.toContain('<script>'); expect(html).not.toContain('href='); expect(html).toContain('../../inert-label.txt');
  });
  it('separates stage prepared/scripted turns from journal save receipts', () => {
    const s = state(); s.summary!.config.recipe = 'stage2'; s.pendingJournal = null; const html = renderToStaticMarkup(<FreshJournal state={s} controller={controller}/>);
    expect(html).toContain('not durable journal save receipts'); expect(html).not.toContain('Save right journal'); expect(html).not.toContain('Request manual WRITE at this boundary');
  });
  it('shows durable checkpoint step separately from current step and preserves a save error', () => {
    const html = renderToStaticMarkup(<FreshSaveStatus state={state()} controller={controller}/>); expect(html).toContain('Current step 30 · checkpoint saved through step 29'); expect(html).toContain('Current record has unsaved changes'); expect(html).toContain('No pending write'); expect(html).toContain('role="alert"'); expect(html).toContain('Disk full'); expect(html).toContain('disabled=""');
  });
  it('recovery inspection states partial coverage and prior portable boundary without offering resume', () => {
    const s = state(); s.recovery = { requestId: 'r', entries: [], incompleteWrites: ['incomplete'], examined: 5, truncated: true }; s.recovered = { schema: 'checkpoint', sessionId: 'old', generation: '1', revision: '4', config: {}, phase: 'storageBlocked', step: 30, durableStep: 29, recordSha256: 'a'.repeat(64), pendingJournal: { observedStep: 30, entry: { text: '<img src=x onerror=unsafe()>' } }, attempts: [], updatedAtMs: '100', discarded: false };
    const html = renderToStaticMarkup(<FreshRecovery state={s} controller={controller}/>); expect(html).toContain('coverage truncated'); expect(html).toContain('portable snapshot ends at durable step 29'); expect(html).toContain('Export recovery checkpoint'); expect(html).toContain('Export portable snapshot through step 29'); expect(html).toContain('&lt;img'); expect(html).not.toContain('<img'); expect(html).not.toContain('Resume experiment');
  });
});
