import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoirConfig from './MyReservoirConfig';
import { DEFAULT_SUSTAINED_CONFIG, effectiveDifferenceClip, effectiveDifferenceGain, effectiveDifferenceWatchdog, validDifferenceControls, type SustainedConfig } from './myReservoirTypes';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));

const withDifference = (patch: Partial<SustainedConfig>): SustainedConfig => ({ ...DEFAULT_SUSTAINED_CONFIG, ...patch });

describe('difference-signal controls', () => {
  it('default to the as-built channel (gain 0), treat omitted history as defaults, and bound every field', () => {
    expect(DEFAULT_SUSTAINED_CONFIG.differenceGain).toBe(0);
    expect(DEFAULT_SUSTAINED_CONFIG.differenceTau).toBe(3);
    expect(DEFAULT_SUSTAINED_CONFIG.differenceClip).toBe(0.2);
    expect(DEFAULT_SUSTAINED_CONFIG.differenceWatchdog).toBe(true);
    const historical = { ...DEFAULT_SUSTAINED_CONFIG } as Record<string, unknown>;
    for (const key of ['differenceGain', 'differenceTau', 'differenceDeadBand', 'differenceClip', 'differenceWatchdog', 'differenceWatchdogFillStd']) delete historical[key];
    const h = historical as unknown as SustainedConfig;
    expect(effectiveDifferenceGain(h)).toBe(0);
    expect(effectiveDifferenceClip(h)).toBe(0.2);
    expect(effectiveDifferenceWatchdog(h)).toBe(true);
    expect(validDifferenceControls(h)).toBe(true);
    expect(validDifferenceControls(withDifference({ differenceGain: -1 }))).toBe(true);
    expect(validDifferenceControls(withDifference({ differenceGain: 1.5 }))).toBe(false);
    expect(validDifferenceControls(withDifference({ differenceClip: 0 }))).toBe(false);
    expect(validDifferenceControls(withDifference({ differenceTau: Number.NaN }))).toBe(false);
    expect(validDifferenceControls(withDifference({ differenceWatchdogFillStd: 101 }))).toBe(false);
  });
  it('renders the six controls after the text reduction with their values and flags invalid values', () => {
    const setConfig = vi.fn();
    const html = renderToStaticMarkup(<MyReservoirConfig config={withDifference({ differenceGain: 0.05 })} setConfig={setConfig} disabled={false}/>);
    expect(html).toMatch(/Difference gain<input type="number" min="-1" max="1" step=".01" required="" value="0.05"/);
    expect(html).toMatch(/Watchdog<select[^>]*><option value="true" selected="">/);
    expect(html).toContain('Gain 0 reproduces the earlier mechanism exactly');
    expect(html.indexOf('Text reduction')).toBeLessThan(html.indexOf('Difference gain'));
    const invalid = renderToStaticMarkup(<MyReservoirConfig config={withDifference({ differenceGain: 1.5 })} setConfig={setConfig} disabled={false}/>);
    expect(invalid).toMatch(/Difference gain<input[^>]*aria-invalid="true"/);
    expect(invalid).toContain('Use a difference gain of −1 to 1');
    expect(setConfig).not.toHaveBeenCalled();
  });
});
