import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import ActivationExperiment, { ActivationReader, ActivationSetup } from './ActivationExperiment';
import { DEFAULT_ACTIVATION_CONFIG } from './activationTypes';
import { activationFixture, activationJournal, activationSession } from './activationTestFixtures';
import pilot from '../../../shared/reservoir-scope/activation-pilot.json';

describe('Activation experiment interface', () => {
  it('renders an opt-in setup without invoking model work', () => {
    const { controller, api } = activationFixture(); const html = renderToStaticMarkup(<ActivationExperiment active controller={controller}/>);
    expect(html).toContain('Check activation setup'); expect(html).toContain('Create activation experiment'); expect(html).toContain('model loads only after Start');
    expect(api.inspect).not.toHaveBeenCalled(); expect(api.start).not.toHaveBeenCalled(); expect(api.list).not.toHaveBeenCalled();
    expect(renderToStaticMarkup(<ActivationExperiment active={false} controller={controller}/>)).toBe('');
  });
  it('uses the canonical twelve-observation pilot rather than an independently edited sequence', () => {
    expect(DEFAULT_ACTIVATION_CONFIG.observations).toEqual(pilot.observations); expect(DEFAULT_ACTIVATION_CONFIG.seed).toBe(pilot.seed); expect(DEFAULT_ACTIVATION_CONFIG.stepsBetween).toBe(10); expect(DEFAULT_ACTIVATION_CONFIG.journalEvery).toBe(2);
  });
  it('keeps setup check, prepared creation and start distinct', async () => {
    const { controller, prepare } = activationFixture(); await prepare();
    const html = renderToStaticMarkup(<ActivationExperiment active controller={controller}/>); expect(html).toContain('Ready · not started'); expect(html).toContain('Start activation run'); expect(html).toContain('Stop and retain results');
    const setup = renderToStaticMarkup(<ActivationSetup state={controller.snapshot()} config={DEFAULT_ACTIVATION_CONFIG} setConfig={() => {}} controller={controller}/>); expect(setup).toContain('without inference'); expect(setup).toContain('1,024');
  });
  it('conceals condition and raw event details until explicitly revealed', () => {
    const { controller } = activationFixture(); const s = activationSession({ modelManifestSha256: 'b'.repeat(64), calibrationSha256: 'c'.repeat(64), config: { ...DEFAULT_ACTIVATION_CONFIG, arm: 'recurrent' }, journalCount: 1, journals: [activationJournal()], events: [{ id: 'event-1', kind: 'quiet_capture', step: 10, detail: 'recurrent secret condition' }] }); controller.compare(s, true);
    const html = renderToStaticMarkup(<ActivationReader session={s} index={0} state={controller.snapshot()} controller={controller}/>);
    expect(html).toContain('Reading A'); expect(html).toContain('Complete journal 1'); expect(html).not.toContain('Recurrent reservoir'); expect(html).not.toContain('recurrent secret condition'); expect(html).toContain('Reveal condition labels and exact evidence');
    expect(html).not.toContain(s.modelManifestSha256); expect(html).not.toContain(s.calibrationSha256);
    controller.reveal(); const revealed = renderToStaticMarkup(<ActivationReader session={s} index={0} state={controller.snapshot()} controller={controller}/>); expect(revealed).toContain('Recurrent reservoir'); expect(revealed).toContain('recurrent secret condition'); expect(revealed).toContain(s.modelManifestSha256); expect(revealed).toContain(s.calibrationSha256);
  });
  it('does not suggest a matched comparison from paths and settings without initialized identities', () => {
    const { controller } = activationFixture(); controller.compare(activationSession(), true); controller.compare(activationSession({ sessionId: 'session-2' }), true);
    const html = renderToStaticMarkup(<ActivationExperiment active controller={controller}/>);
    expect(html).toContain('Calibration or model/runtime identity is unconfirmed'); expect(html).not.toContain('settings match across these runs');
  });
  it.each(['calibrationSha256', 'modelManifestSha256'] as const)('rejects a comparison with different %s even at the same local paths', field => {
    const { controller } = activationFixture(); const identity = { modelManifestSha256: 'b'.repeat(64), calibrationSha256: 'c'.repeat(64) };
    controller.compare(activationSession(identity), true); controller.compare(activationSession({ ...identity, sessionId: 'session-2', [field]: 'd'.repeat(64) }), true);
    const html = renderToStaticMarkup(<ActivationExperiment active controller={controller}/>); expect(html).toContain('Read them as separate experiments'); expect(html).not.toContain('settings match across these runs');
  });
  it('matches retained identities and settings even when local asset paths differ', () => {
    const { controller } = activationFixture(); const identity = { modelManifestSha256: 'b'.repeat(64), calibrationSha256: 'c'.repeat(64) };
    controller.compare(activationSession(identity), true); controller.compare(activationSession({ ...identity, sessionId: 'session-2', config: { ...DEFAULT_ACTIVATION_CONFIG, arm: 'recurrent', modelPath: '/another/local/model' } }), true);
    const html = renderToStaticMarkup(<ActivationExperiment active controller={controller}/>); expect(html).toContain('settings match across these runs'); expect(html).not.toContain('Read them as separate experiments');
  });
  it('renders full inert text, incomplete application and failed observations honestly', () => {
    const { controller } = activationFixture(); const s = activationSession({ journalCount: 1, journals: [{ ...activationJournal(), text: '<script>inert full journal</script>\nFinal paragraph.', firstAppliedStep: null }], events: [{ id: 'event-1', kind: 'quiet_failed', step: 10, detail: 'worker error' }] }); controller.compare(s, true);
    const html = renderToStaticMarkup(<ActivationReader session={s} index={0} state={controller.snapshot()} controller={controller}/>); expect(html).toContain('&lt;script&gt;inert full journal&lt;/script&gt;'); expect(html).toContain('Final paragraph.'); expect(html).not.toContain('<script>'); expect(html).toContain('No first feedback application is recorded'); expect(html).toContain('Attempt failed'); expect(html).toContain('never determine feedback eligibility'); expect(html).toContain('Another possible reading');
  });
  it('shows exact quiet input, request and application boundaries, and cancellation before revealing condition evidence', () => {
    const { controller } = activationFixture();
    const s = activationSession({ config: { ...DEFAULT_ACTIVATION_CONFIG, arm: 'recurrent', observations: ['<script>inert observation</script>\nSecond line.', 'The next observation never applies.'] }, events: [
      { id: 'event-1', kind: 'requestStarted', step: 9, detail: 'quiet_capture' }, { id: 'event-2', kind: 'quietReceived', step: 10, detail: 'Observation registered without sampled output' },
      { id: 'event-3', kind: 'requestStarted', step: 19, detail: 'quiet_capture' }, { id: 'event-4', kind: 'failed', step: 19, detail: 'Cancelled recurrent secret condition' },
    ] }); controller.compare(s, true);
    const html = renderToStaticMarkup(<ActivationReader session={s} index={0} state={controller.snapshot()} controller={controller}/>);
    expect(html).toContain('&lt;script&gt;inert observation&lt;/script&gt;\nSecond line.'); expect(html).not.toContain('<script>');
    expect(html).toContain('Quiet observation 1 requested'); expect(html).toContain('Scheduled application at step 10'); expect(html).toContain('Quiet observation 1 applied'); expect(html).toContain('Received and applied at step 10 without sampled output');
    expect(html).toContain('The next observation never applies.'); expect(html).toContain('Quiet observation 2 cancelled'); expect(html).toContain('Requested at step 19; held at step 19. No application is recorded');
    expect(html).not.toContain('Recurrent reservoir'); expect(html).not.toContain('recurrent secret condition');
  });
});
