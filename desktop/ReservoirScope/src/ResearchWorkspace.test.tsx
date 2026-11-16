import { describe, it, expect, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import ResearchWorkspace, { configurationPatch, loadResearchMeasurements } from './ResearchWorkspace';
import { invoke } from '@tauri-apps/api/core';
import nativeView from './fixtures/experiments/experiment-view.json';
vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));
describe('research workspace', () => {
  it('loads only the selected research run and matches the exact result identity', async () => {
    const report = nativeView.modelExperiments[0], session = {sessionId:nativeView.sessionId,generation:nativeView.generation};
    vi.mocked(invoke).mockResolvedValue(nativeView);
    const result=await loadResearchMeasurements(session,{kind:'experiment',id:report.id,step:report.requestedStep});
    expect(result?.kind).toBe('experiment');
    expect(invoke).toHaveBeenCalledWith('research_request',{method:'GET',path:`/v1/runs/${encodeURIComponent(session.sessionId)}/sonar`,body:null,idempotencyKey:null});
    expect(await loadResearchMeasurements(session,{kind:'experiment',id:'f'.repeat(64),step:report.requestedStep})).toBeNull();
    await expect(loadResearchMeasurements({...session,sessionId:'wrong-run'},{kind:'experiment',id:report.id,step:report.requestedStep})).rejects.toThrow('do not match this run');
  });
  it('patches only explicit changes and clears optional values', () => {
    expect(configurationPatch({ language: { model: 'a', temperature: .7 }, sonar: { version: 'v2' } }, { language: { model: 'b', temperature: .7 } })).toEqual({ language: { model: 'b' }, sonar: null });
  });
  it('keeps run selection independent of execution and exposes recipes', () => {
    const html = renderToStaticMarkup(<ResearchWorkspace active route={null} />);
    expect(html).toContain('Selection does not affect execution');
    expect(html).toContain('Experiment recipes');
    expect(html).toContain('Operations');
    expect(renderToStaticMarkup(<ResearchWorkspace active={false} route={null} />)).toBe('');
  });
  it('opens the section selected by a native settings or experiment route', () => {
    const settings=renderToStaticMarkup(<ResearchWorkspace active route="/v1/settings" />);
    expect(settings).toContain('<details open=""><summary>Model request queue');
    const experiment=renderToStaticMarkup(<ResearchWorkspace active route="/v1/experiments/experiment-1" />);
    expect(experiment).toContain('<details open=""><summary>Experiment recipes');
  });
});
