import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import ResearchWorkspace, { configurationPatch } from './ResearchWorkspace';
describe('research workspace', () => {
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
