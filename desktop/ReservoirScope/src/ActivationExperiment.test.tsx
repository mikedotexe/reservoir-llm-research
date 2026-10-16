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
    const { controller } = activationFixture(); const s = activationSession({ config: { ...DEFAULT_ACTIVATION_CONFIG, arm: 'recurrent' }, journalCount: 1, journals: [activationJournal()], events: [{ id: 'event-1', kind: 'quiet_capture', step: 10, detail: 'recurrent secret condition' }] }); controller.compare(s, true);
    const html = renderToStaticMarkup(<ActivationReader session={s} index={0} state={controller.snapshot()} controller={controller}/>);
    expect(html).toContain('Reading A'); expect(html).toContain('Complete journal 1'); expect(html).not.toContain('Recurrent reservoir'); expect(html).not.toContain('recurrent secret condition'); expect(html).toContain('Reveal condition labels and exact evidence');
    controller.reveal(); const revealed = renderToStaticMarkup(<ActivationReader session={s} index={0} state={controller.snapshot()} controller={controller}/>); expect(revealed).toContain('Recurrent reservoir'); expect(revealed).toContain('recurrent secret condition');
  });
  it('renders full inert text, incomplete application and failed observations honestly', () => {
    const { controller } = activationFixture(); const s = activationSession({ journalCount: 1, journals: [{ ...activationJournal(), text: '<script>inert full journal</script>\nFinal paragraph.', firstAppliedStep: null }], events: [{ id: 'event-1', kind: 'quiet_failed', step: 10, detail: 'worker error' }] }); controller.compare(s, true);
    const html = renderToStaticMarkup(<ActivationReader session={s} index={0} state={controller.snapshot()} controller={controller}/>); expect(html).toContain('&lt;script&gt;inert full journal&lt;/script&gt;'); expect(html).toContain('Final paragraph.'); expect(html).not.toContain('<script>'); expect(html).toContain('No first feedback application is recorded'); expect(html).toContain('Attempt failed'); expect(html).toContain('never determine feedback eligibility'); expect(html).toContain('Another possible reading');
  });
});
