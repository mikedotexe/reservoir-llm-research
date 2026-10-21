import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoirConfig from './MyReservoirConfig';
import { DEFAULT_SUSTAINED_CONFIG, DEFAULT_WRITING_TEMPERATURE, effectiveTemperature, validWritingLimits, type SustainedConfig } from './myReservoirTypes';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));

const ollama = (temperature?: number): SustainedConfig => ({ ...DEFAULT_SUSTAINED_CONFIG, language: { backend: 'ollama', endpoint: 'http://127.0.0.1:11434', model: 'chosen:exact', contextTokens: 8192, responseFormat: null, ...(temperature === undefined ? {} : { temperature }) } });

describe('writing temperature', () => {
  it('defaults fresh Ollama selections to 0.7 while omitted history stays greedy and bounds are enforced', () => {
    expect(DEFAULT_WRITING_TEMPERATURE).toBe(0.7);
    expect(effectiveTemperature(ollama())).toBe(0);
    expect(effectiveTemperature(ollama(0.7))).toBe(0.7);
    expect(validWritingLimits(ollama())).toBe(true);
    expect(validWritingLimits(ollama(0))).toBe(true);
    expect(validWritingLimits(ollama(2))).toBe(true);
    for (const bad of [-0.1, 2.5, Number.NaN]) expect(validWritingLimits(ollama(bad))).toBe(false);
    const setConfig = vi.fn();
    const html = renderToStaticMarkup(<MyReservoirConfig config={ollama(0.7)} setConfig={setConfig} disabled={false}/>);
    expect(html).toMatch(/Writing temperature<input type="number" min="0" max="2" step=".05" required="" value="0.7"/);
    expect(html).toContain('each attempt samples with a seed derived from the session seed and attempt number');
    const historical = renderToStaticMarkup(<MyReservoirConfig config={ollama()} setConfig={setConfig} disabled={false}/>);
    expect(historical).toMatch(/Writing temperature<input[^>]*value="0"/);
    const invalid = renderToStaticMarkup(<MyReservoirConfig config={ollama(3)} setConfig={setConfig} disabled={false}/>);
    expect(invalid).toContain('Temperature must be 0–2.');
    expect(invalid).toMatch(/Writing temperature<input[^>]*aria-invalid="true"/);
    expect(setConfig).not.toHaveBeenCalled();
  });
});
