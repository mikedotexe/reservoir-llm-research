import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import App from './App';
import { myReservoirApi } from './myReservoirApi';

// These readers use browser-only external stores. Their lifecycle has separate tests.
vi.mock('./GuidedTour', () => ({ default: ({ active }: { active: boolean }) => <div data-reader="guide" hidden={!active}/> }));
vi.mock('./CasesWorkspace', () => ({ default: ({ active }: { active: boolean }) => <div data-reader="cases" hidden={!active}/> }));
vi.mock('./RecordedExperiments', () => ({ default: ({ active }: { active: boolean }) => <div data-reader="recording" hidden={!active}/> }));

// Startup route wiring; controller tests separately exercise attachment and navigation.
describe('application entry point', () => {
  it('lands directly in personal setup without creating or starting a session', () => {
    const create = vi.spyOn(myReservoirApi, 'create'), action = vi.spyOn(myReservoirApi, 'action');
    const html = renderToStaticMarkup(<App/>);
    expect(html).toContain('<button aria-current="page">My reservoir</button>');
    expect(html).toContain('Create my reservoir');
    expect(html).not.toContain('aria-label="Experiment views"');
    expect(html).not.toContain('class="preparation-history"');
    expect(html).not.toContain('<canvas');
    for (const reader of ['guide', 'cases', 'recording']) expect(html).toContain(`data-reader="${reader}" hidden=""`);
    expect(create).not.toHaveBeenCalled(); expect(action).not.toHaveBeenCalled();
    vi.restoreAllMocks();
  });
});
