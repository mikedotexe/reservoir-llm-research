import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoirConfig from './MyReservoirConfig';
import { DEFAULT_EMBEDDING_MODEL, DEFAULT_SUSTAINED_CONFIG, effectiveCodec, validFieldControls } from './myReservoirTypes';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));

describe('text reduction choice', () => {
  it('defaults to the surface codec, offers the embedding codec with a model name, and validates it', () => {
    expect(effectiveCodec(DEFAULT_SUSTAINED_CONFIG)).toBe('surface');
    expect(DEFAULT_EMBEDDING_MODEL).toBe('nomic-embed-text');
    expect(validFieldControls({ ...DEFAULT_SUSTAINED_CONFIG, embeddingModel: 'nomic-embed-text' })).toBe(true);
    expect(validFieldControls({ ...DEFAULT_SUSTAINED_CONFIG, embeddingModel: ' ' })).toBe(false);
    expect(validFieldControls({ ...DEFAULT_SUSTAINED_CONFIG, embeddingModel: 'x', embeddingProjectionSeed: '007' })).toBe(false);
    expect(validFieldControls({ ...DEFAULT_SUSTAINED_CONFIG, embeddingModel: 'x', embeddingProjectionSeed: '42' })).toBe(true);
    const setConfig = vi.fn();
    const surface = renderToStaticMarkup(<MyReservoirConfig config={DEFAULT_SUSTAINED_CONFIG} setConfig={setConfig} disabled={false}/>);
    expect(surface).toContain('Surface statistics (as built)');
    expect(surface).not.toContain('Embedding model · exact local name');
    const embedding = renderToStaticMarkup(<MyReservoirConfig config={{ ...DEFAULT_SUSTAINED_CONFIG, embeddingModel: 'nomic-embed-text' }} setConfig={setConfig} disabled={false}/>);
    expect(embedding).toMatch(/Embedding model · exact local name<input[^>]*value="nomic-embed-text"/);
    expect(embedding).toContain('projects it to 32 coordinates with a fixed seeded matrix');
    expect(setConfig).not.toHaveBeenCalled();
  });
});
