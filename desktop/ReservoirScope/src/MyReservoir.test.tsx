import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoir, { MyReservoirBoundary, MyReservoirStatus } from './MyReservoir';
import MyReservoirConfig from './MyReservoirConfig';
import MyReservoirVisuals from './MyReservoirVisuals';
import MyReservoirJournals, { MyReservoirJournalDetail } from './MyReservoirJournals';
import MyReservoirRecovery from './MyReservoirRecovery';
import { DEFAULT_SUSTAINED_CONFIG } from './myReservoirTypes';
import { DEFAULT_CAMERA } from './types';
import { reservoirFixture, reservoirSummary, reservoirFrame, journal, settle } from './myReservoirTestFixtures';

describe('My reservoir explicit operation and evidence', () => {
  it('starts no session on rendering and does not mount graphics when inactive', () => {
    const { api, controller } = reservoirFixture(); const create = vi.spyOn(api, 'create'), action = vi.spyOn(api, 'action');
    const html = renderToStaticMarkup(<MyReservoir active controller={controller}/>); expect(html).toContain('Create my reservoir'); expect(html).toContain('No experiment starts from navigation'); expect(html).not.toContain('Recorded value · no smoothing'); expect(create).not.toHaveBeenCalled(); expect(action).not.toHaveBeenCalled();
    expect(renderToStaticMarkup(<MyReservoir active={false} controller={controller}/>)).toBe('');
  });
  it('shows explicit run/storage bounds and uses plain-text local readiness without a finite Step instruction', () => {
    const html = renderToStaticMarkup(<MyReservoirConfig disabled={false} setConfig={() => {}} config={{ ...DEFAULT_SUSTAINED_CONFIG, language: { backend: 'ollama', endpoint: '', model: '', contextTokens: 4096, responseFormat: null } }}/>);
    expect(html).toContain('value="10800"'); expect(html).toContain('value="360"'); expect(html).toContain('exactly 21600 seconds'); expect(html).toContain('value="256"'); expect(html).toContain('including retries'); expect(html).toContain('Check local model'); expect(html).toContain('Room for up to 1,024 output tokens per entry'); expect(html).toContain('Start explicitly begins'); expect(html).not.toContain('Step, Run or a manual opportunity');
    expect(html).toContain('Some storage is reserved for saving, stopping and closing safely'); expect(html).toContain('can stop before the selected storage limit is full');
  });
  it('distinguishes live simulated time, durable cursor and host budgets', () => {
    const state = { ...reservoirFixture().controller.snapshot(), summary: reservoirSummary({ step: 33, durableStep: 30, simulatedTime: 11, elapsedSeconds: 64, usedBytes: 1048576 }) };
    const html = renderToStaticMarkup(<MyReservoirStatus state={state}/>); expect(html).toContain('Numerical step'); expect(html).toContain('Durable step'); expect(html).toContain('>30<'); expect(html).toContain('Simulated seconds'); expect(html).toContain('11.000'); expect(html).toContain('Elapsed / limit seconds'); expect(html).toContain('1.00 MiB');
  });
  it('keeps surface state separate from compact sensory fill and preserves exact disclosures', () => {
    const html = renderToStaticMarkup(<MyReservoirVisuals summary={reservoirSummary({ step: 3 })} frame={reservoirFrame(3)} node={0} onNode={() => {}} pose={DEFAULT_CAMERA} onPose={() => {}} tableOnly/>);
    expect(html).toContain('My reservoir · 32 coordinates'); expect(html).toContain('Separate reduced sensory'); expect(html).toContain('Exact fill values, interpretation and graphics recovery'); expect(html).toContain('Exact retained fill'); expect(html).toContain('Sensory eigenvalues'); expect(html).toContain('0.125'); expect(html).not.toContain('evidence of learned');
  });
  it('does not turn unavailable fill into a zero value or spherical measurement', () => {
    const html = renderToStaticMarkup(<MyReservoirVisuals summary={reservoirSummary({ step: 3 })} frame={{ ...reservoirFrame(3), fillPercent: null }} node={0} onNode={() => {}} pose={DEFAULT_CAMERA} onPose={() => {}} tableOnly/>);
    expect(html).toContain('No retained fill measurement'); expect(html).not.toContain('Retained fill 0 percent');
    const restored = renderToStaticMarkup(<MyReservoirVisuals summary={reservoirSummary({ step: 30 })} frame={null} node={0} onNode={() => {}} pose={DEFAULT_CAMERA} onPose={() => {}} tableOnly/>);
    expect(restored).toContain('global step 30'); expect(restored).toContain('Current frame unavailable'); expect(restored).not.toContain('Ready for the first observation');
  });
  it('shows saved-but-unapplied and skipped entries without granting memory/application', () => {
    const pending = renderToStaticMarkup(<MyReservoirJournalDetail journal={{ ...journal(), status: 'savedPendingApplication', firstAppliedStep: null, application: null }} revision="3"/>);
    expect(pending).toContain('waiting for first application'); expect(pending).toContain('not yet eligible'); expect(pending).toContain('no first application recorded');
    const skipped = renderToStaticMarkup(<MyReservoirJournalDetail journal={{ ...journal(), status: 'skipped', firstAppliedStep: null, application: null }} revision="4"/>);
    expect(skipped).toContain('automatic prompt-memory exposure were explicitly skipped'); expect(skipped).not.toContain('first applied at step 4');
  });
  it('renders exact journal/prompt/memory and source safely, with host timing separate', () => {
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={{ ...journal(2), text: '<script>reply</script>', timing: { attemptId: 2, dispatchedAtMs: '12345678901234567890', receivedAtMs: '12345678901234567891', transportDurationMs: 1, publishedAtMs: null } }} revision="7"/>);
    expect(html).toContain('&lt;script&gt;reply&lt;/script&gt;'); expect(html).toContain('&lt;script&gt;inert exact prompt&lt;/script&gt;'); expect(html).not.toContain('<script>'); expect(html).toContain('Prior applied text'); expect(html).toContain('12345678901234567890'); expect(html).toContain('separate from simulated time'); expect(html).toContain('not proof of provider receipt'); expect(html).toContain('not train the model');
  });
  it('keeps independent reading and labels new journals without moving current selection', async () => {
    const { controller, push } = reservoirFixture(); await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle(); push({ revision: '7', step: 7, journalCount: 2, turnCount: 2 }); await controller.selectJournal('journal-1'); push({ revision: '10', step: 10, journalCount: 3, turnCount: 3 });
    const html = renderToStaticMarkup(<MyReservoirJournals state={controller.snapshot()} controller={controller}/>); expect(html).toContain('1 new'); expect(html).toContain('Writing at step 3'); expect(html).toContain('reading position never moves the live clock');
  });
  it('labels pending save, explicit retry and skip without inventing successful durability', () => {
    const { controller } = reservoirFixture(), state = { ...controller.snapshot(), summary: reservoirSummary({ phase: 'storageBlocked', canStart: false, canRetrySave: true, canSkipFeedback: true, pendingSave: { entryId: 'pending-j', observedStep: 30, attemptId: 4 } }) };
    const html = renderToStaticMarkup(<MyReservoirBoundary state={state} controller={controller}/>); expect(html).toContain('Retry durable save'); expect(html).toContain('storage failure never becomes an applied journal'); expect(html).toContain('Skip this unresolved writing opportunity');
  });
  it('separates blocked outcomes and scripted opportunities from live model requests', () => {
    const { controller } = reservoirFixture(), pending = { operationId: 'op', turnId: 2, attemptId: 4, observedStep: 30, endpoint: '', model: '', state: 'requesting' as const };
    const scripted = renderToStaticMarkup(<MyReservoirBoundary controller={controller} state={{ ...controller.snapshot(), summary: reservoirSummary({ pendingLanguage: pending }) }}/>); expect(scripted).toContain('Scripted writing boundary'); expect(scripted).toContain('no model request'); expect(scripted).not.toContain('Local writing request in progress');
    const blocked = renderToStaticMarkup(<MyReservoirBoundary controller={controller} state={{ ...controller.snapshot(), summary: reservoirSummary({ pendingLanguage: { ...pending, state: 'blocked' }, canRetryProvider: true }) }}/>); expect(blocked).toContain('No network request is active'); expect(blocked).toContain('Retry as a new attempt'); expect(blocked).not.toContain('response was not accepted');
    const memoryBlocked = renderToStaticMarkup(<MyReservoirBoundary controller={controller} state={{ ...controller.snapshot(), summary: reservoirSummary({ phase: 'attemptBlocked', config: { ...DEFAULT_SUSTAINED_CONFIG, language: { backend: 'ollama', endpoint: 'http://127.0.0.1:11434', model: 'configured' } }, pendingLanguage: { ...pending, attemptId: 0, state: 'blocked' }, diagnostics: ['The prior journal could not be read.'] }) }}/>); expect(memoryBlocked).toContain('Writing attempt blocked'); expect(memoryBlocked).not.toContain('Local writing request in progress'); expect(memoryBlocked).not.toContain('Response acceptance blocked'); expect(memoryBlocked).not.toContain('Provider attempt failed');
  });
  it('allows committed blocked-attempt export without forcing retry or skip, while a request is unsettled it stays disabled', async () => {
    const { controller, push } = reservoirFixture(); await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
    const pending = { operationId: 'held-op', turnId: 1, attemptId: 1, observedStep: 30, endpoint: '', model: '', state: 'blocked' as const };
    push({ revision: '3', phase: 'attemptBlocked', canPause: false, pendingLanguage: pending });
    const blocked = renderToStaticMarkup(<MyReservoir active controller={controller}/>);
    expect(blocked).toMatch(/<button>Export committed session bundle…<\/button>/);
    push({ revision: '4', phase: 'awaitingLanguage', pendingLanguage: { ...pending, state: 'requesting' } });
    const requesting = renderToStaticMarkup(<MyReservoir active controller={controller}/>);
    expect(requesting).toMatch(/<button disabled="">Export committed session bundle…<\/button>/);
  });
  it('recovery preserves wide integer strings and shows verification without claiming automatic resume or whole-directory hash', async () => {
    const { controller } = reservoirFixture(); await controller.recovery(); await controller.inspect('personal-1'); const html = renderToStaticMarkup(<MyReservoirRecovery state={controller.snapshot()} controller={controller}/>);
    expect(html).toContain('18446744073709551615'); expect(html).toContain('12345678901234567890'); expect(html).toContain('&lt;script&gt;inert&lt;/script&gt;'); expect(html).toContain('not yet a replay verification'); expect(html).toContain('Restore paused for review'); expect(html).toContain('not a fabricated whole-directory digest'); expect(html).toContain('does not start numerical scheduling');
  });
});
