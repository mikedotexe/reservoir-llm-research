import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoirConfig from './MyReservoirConfig';
import { DEFAULT_SUSTAINED_CONFIG, type SustainedConfig } from './myReservoirTypes';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));

const ollama = (thinking?: boolean | null): SustainedConfig => ({ ...DEFAULT_SUSTAINED_CONFIG, language: { backend: 'ollama', endpoint: 'http://127.0.0.1:11434', model: 'gemma4:12b', contextTokens: 8192, responseFormat: null, temperature: 0.7, ...(thinking === undefined ? {} : { thinking }) } });

describe('model thinking', () => {
  it('is omitted unless chosen and renders the recorded choice', () => {
    const setConfig = vi.fn();
    expect(DEFAULT_SUSTAINED_CONFIG.language.thinking).toBeUndefined();
    expect(renderToStaticMarkup(<MyReservoirConfig config={ollama()} setConfig={setConfig} disabled={false}/>)).toMatch(/Model thinking<select[^>]*><option value="omit" selected="">/);
    expect(renderToStaticMarkup(<MyReservoirConfig config={ollama(false)} setConfig={setConfig} disabled={false}/>)).toMatch(/<option value="false" selected="">Off/);
    expect(renderToStaticMarkup(<MyReservoirConfig config={ollama(true)} setConfig={setConfig} disabled={false}/>)).toMatch(/<option value="true" selected="">On/);
    expect(setConfig).not.toHaveBeenCalled();
  });
});
