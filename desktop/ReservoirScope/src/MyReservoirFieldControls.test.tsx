import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoirConfig from './MyReservoirConfig';
import { DEFAULT_SUSTAINED_CONFIG, effectiveFeedbackScale, effectiveSensoryNoise, validFieldControls, type SustainedConfig } from './myReservoirTypes';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));

describe('sensory field noise and feedback scale controls', () => {
  it('fresh defaults select field noise 0.5 and feedback ×0.4 while omitted history keeps mechanism v1 values', () => {
    expect(DEFAULT_SUSTAINED_CONFIG.sensoryNoiseAmplitude).toBe(0.5);
    expect(DEFAULT_SUSTAINED_CONFIG.feedbackScale).toBe(0.4);
    const { sensoryNoiseAmplitude, feedbackScale, ...historical } = DEFAULT_SUSTAINED_CONFIG;
    void sensoryNoiseAmplitude; void feedbackScale;
    expect(effectiveSensoryNoise(historical)).toBe(0);
    expect(effectiveFeedbackScale(historical)).toBe(1);
    expect(validFieldControls(historical)).toBe(true);
    expect(validFieldControls(DEFAULT_SUSTAINED_CONFIG)).toBe(true);
    for (const bad of [{ sensoryNoiseAmplitude: -0.1 }, { sensoryNoiseAmplitude: 1.5 }, { feedbackScale: -1 }, { feedbackScale: 2.5 }, { feedbackScale: Number.NaN }]) {
      expect(validFieldControls({ ...DEFAULT_SUSTAINED_CONFIG, ...bad } as SustainedConfig)).toBe(false);
    }
  });
  it('renders both controls under Advanced settings with their effective values and patches on change', () => {
    const setConfig = vi.fn();
    const html = renderToStaticMarkup(<MyReservoirConfig config={DEFAULT_SUSTAINED_CONFIG} setConfig={setConfig} disabled={false}/>);
    const advanced = html.indexOf('<details class="my-reservoir-advanced">');
    expect(html.indexOf('Sensory input noise amplitude')).toBeGreaterThan(advanced);
    expect(html.indexOf('Text feedback scale')).toBeGreaterThan(advanced);
    expect(html).toMatch(/Sensory input noise amplitude<input type="number" min="0" max="1" step=".05" required="" value="0.5"/);
    expect(html).toMatch(/Text feedback scale<input type="number" min="0" max="2" step=".05" required="" value="0.4"/);
    expect(html).toContain('Noise 0 with scale 1 reproduces the earlier mechanism exactly');
    expect(html).not.toContain('role="alert">Use a sensory input noise amplitude');
    const { sensoryNoiseAmplitude, feedbackScale, ...historical } = DEFAULT_SUSTAINED_CONFIG;
    void sensoryNoiseAmplitude; void feedbackScale;
    const old = renderToStaticMarkup(<MyReservoirConfig config={historical} setConfig={setConfig} disabled={false}/>);
    expect(old).toMatch(/Sensory input noise amplitude<input type="number" min="0" max="1" step=".05" required="" value="0"/);
    expect(old).toMatch(/Text feedback scale<input type="number" min="0" max="2" step=".05" required="" value="1"/);
    const invalid = renderToStaticMarkup(<MyReservoirConfig config={{ ...DEFAULT_SUSTAINED_CONFIG, feedbackScale: 3 }} setConfig={setConfig} disabled={false}/>);
    expect(invalid).toContain('Use a sensory input noise amplitude of 0–1 and a text feedback scale of 0–2.');
    expect(invalid).toMatch(/Text feedback scale<input[^>]*aria-invalid="true"[^>]*>/);
    expect(invalid).toMatch(/Text feedback scale<input[^>]*value="3"[^>]*>/);
    expect(setConfig).not.toHaveBeenCalled();
  });
});
