import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoirConfig from './MyReservoirConfig';
import { DEFAULT_SUSTAINED_CONFIG, effectiveDifferenceWatchdogWarmup, effectiveMemoryPolicy, effectiveMemoryRecentExclusion, validDifferenceControls, validMemoryPolicy, validMemoryRecentExclusion, type SustainedConfig } from './myReservoirTypes';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));

const withConfig = (patch: Partial<SustainedConfig>): SustainedConfig => ({ ...DEFAULT_SUSTAINED_CONFIG, ...patch });

describe('earlier-entry policy and watchdog warm-up', () => {
  it('default to the as-built behaviour, treat omitted history as defaults, and bound the warm-up', () => {
    expect(DEFAULT_SUSTAINED_CONFIG.memoryPolicy).toBe('latest');
    expect(DEFAULT_SUSTAINED_CONFIG.differenceWatchdogWarmup).toBe(0);
    const historical = { ...DEFAULT_SUSTAINED_CONFIG } as Record<string, unknown>;
    delete historical.memoryPolicy; delete historical.differenceWatchdogWarmup;
    const h = historical as unknown as SustainedConfig;
    expect(effectiveMemoryPolicy(h)).toBe('latest');
    expect(effectiveDifferenceWatchdogWarmup(h)).toBe(0);
    expect(validMemoryPolicy(h)).toBe(true);
    expect(validDifferenceControls(h)).toBe(true);
    expect(validMemoryPolicy({ ...h, memoryPolicy: 'newest' as unknown as 'latest' })).toBe(false);
    expect(validDifferenceControls(withConfig({ differenceWatchdogWarmup: 120 }))).toBe(true);
    expect(validDifferenceControls(withConfig({ differenceWatchdogWarmup: -1 }))).toBe(false);
    expect(validDifferenceControls(withConfig({ differenceWatchdogWarmup: 1.5 }))).toBe(false);
    // 0.38.0: the recent-return window and the two-entry prompt version.
    expect(DEFAULT_SUSTAINED_CONFIG.memoryRecentExclusion).toBe(0);
    delete historical.memoryRecentExclusion;
    expect(effectiveMemoryRecentExclusion(h)).toBe(0);
    expect(validMemoryRecentExclusion(h)).toBe(true);
    expect(validMemoryRecentExclusion(withConfig({ memoryRecentExclusion: 3 }))).toBe(false);
    expect(validMemoryRecentExclusion(withConfig({ memoryPolicy: 'random-older', memoryRecentExclusion: 3 }))).toBe(true);
    expect(validMemoryRecentExclusion(withConfig({ memoryPolicy: 'state-residual', memoryRecentExclusion: 256 }))).toBe(true);
    expect(validMemoryRecentExclusion(withConfig({ memoryPolicy: 'state-residual', memoryRecentExclusion: 257 }))).toBe(false);
    expect(validMemoryRecentExclusion(withConfig({ memoryPolicy: 'state-residual', memoryRecentExclusion: 1.5 }))).toBe(false);
    expect(validMemoryPolicy(withConfig({ promptVersion: 'reservoir-journal-inert-plain-contract-two-v1' }))).toBe(false);
    expect(validMemoryPolicy(withConfig({ promptVersion: 'reservoir-journal-inert-plain-contract-two-v1', memoryPolicy: 'random' }))).toBe(false);
    expect(validMemoryPolicy(withConfig({ promptVersion: 'reservoir-journal-inert-plain-contract-two-v1', memoryPolicy: 'state-residual' }))).toBe(true);
  });
  it('renders the policy select after the difference signal and the warm-up field with their explanations', () => {
    const setConfig = vi.fn();
    const html = renderToStaticMarkup(<MyReservoirConfig config={withConfig({ memoryPolicy: 'state-aligned', differenceWatchdogWarmup: 120 })} setConfig={setConfig} disabled={false}/>);
    expect(html).toMatch(/Earlier entry returned<select[^>]*><option value="latest">[^<]*<\/option><option value="state-aligned" selected="">/);
    expect(html).toMatch(/Watchdog warm-up · steps<input type="number" min="0" max="10000000" step="1" required="" value="120"/);
    expect(html).toContain('The prompt text is identical under every policy');
    expect(html).toMatch(/<option value="state-residual">[^<]*<\/option><option value="random-older">/);
    expect(html).toContain('projects that push out of the state');
    expect(validMemoryPolicy(withConfig({ memoryPolicy: 'state-residual' }))).toBe(true);
    expect(validMemoryPolicy(withConfig({ memoryPolicy: 'random-older' }))).toBe(true);
    expect(html).toContain('trips the default bound at step 90');
    expect(html.indexOf('Difference gain')).toBeLessThan(html.indexOf('Earlier entry returned'));
    expect(html).toMatch(/Recent-return window · turns<input type="number" min="0" max="256" step="1" required="" value="0"/);
    const windowed = renderToStaticMarkup(<MyReservoirConfig config={withConfig({ memoryPolicy: 'state-residual', memoryRecentExclusion: 3 })} setConfig={setConfig} disabled={false}/>);
    expect(windowed).toMatch(/Recent-return window · turns<input type="number" min="0" max="256" step="1" required="" value="3"/);
    expect(windowed).toContain('keeps an entry returned within the last K turns');
    expect(windowed).toContain('reservoir-journal-inert-plain-contract-two-v1');
    expect(windowed).not.toContain('Use a recent-return window');
    const badWindow = renderToStaticMarkup(<MyReservoirConfig config={withConfig({ memoryRecentExclusion: 3 })} setConfig={setConfig} disabled={false}/>);
    expect(badWindow).toMatch(/Recent-return window · turns<input[^>]*aria-invalid="true"/);
    expect(badWindow).toContain('Use a recent-return window of 0–256 whole turns');
    const invalid = renderToStaticMarkup(<MyReservoirConfig config={withConfig({ differenceWatchdogWarmup: -5 })} setConfig={setConfig} disabled={false}/>);
    expect(invalid).toMatch(/Watchdog warm-up · steps<input[^>]*aria-invalid="true"/);
    expect(invalid).toContain('a warm-up of 0 or more whole steps');
    expect(setConfig).not.toHaveBeenCalled();
  });
});
