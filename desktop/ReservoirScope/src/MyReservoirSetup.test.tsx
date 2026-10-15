import { Children, isValidElement, type ReactElement, type ReactNode } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { invoke } from '@tauri-apps/api/core';
import MyReservoirConfig from './MyReservoirConfig';
import { LocalModelController } from './localModelController';
import { DEFAULT_SUSTAINED_CONFIG } from './myReservoirTypes';
import { formatSessionDuration, parseSessionDuration, splitSessionDuration } from './sessionDuration';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));

function elements(node: ReactNode): ReactElement<Record<string, unknown>>[] {
  if (!isValidElement<Record<string, unknown>>(node)) return [];
  const result = [node];
  Children.forEach(node.props.children as ReactNode, child => result.push(...elements(child)));
  return result;
}

describe('exact session duration editing', () => {
  it('round-trips every accepted integer second without truncation or unit-switch rounding', () => {
    for (let seconds = 1; seconds <= 86400; seconds++) {
      expect(parseSessionDuration(splitSessionDuration(seconds))).toBe(seconds);
    }
  });
  it('rejects incomplete, fractional, negative and out-of-range drafts rather than changing their meaning', () => {
    for (const parts of [
      { hours: '', minutes: '1', seconds: '0' },
      { hours: '1.5', minutes: '0', seconds: '0' },
      { hours: '-1', minutes: '0', seconds: '0' },
      { hours: '0', minutes: '60', seconds: '0' },
      { hours: '0', minutes: '0', seconds: '60' },
      { hours: '24', minutes: '0', seconds: '1' },
      { hours: '0', minutes: '0', seconds: '0' },
      { hours: '1e1', minutes: '0', seconds: '0' },
    ]) expect(parseSessionDuration(parts)).toBeNull();
    expect(parseSessionDuration({ hours: '00', minutes: '00', seconds: '01' })).toBe(1);
    expect(parseSessionDuration({ hours: '24', minutes: '00', seconds: '00' })).toBe(86400);
    expect(splitSessionDuration(3601.5)).toEqual({ hours: '', minutes: '', seconds: '' });
  });
  it('formats human-readable elapsed time separately from exact editor conversion', () => {
    expect(formatSessionDuration(21600)).toBe('6 hours');
    expect(formatSessionDuration(3601)).toBe('1 hour 1 second');
    expect(formatSessionDuration(61)).toBe('1 minute 1 second');
    expect(formatSessionDuration(0)).toBe('0 seconds');
    expect(formatSessionDuration(61.999)).toBe('1 minute 1 second');
    expect(formatSessionDuration(Number.NaN)).toBe('Unavailable');
    expect(formatSessionDuration(-1)).toBe('Unavailable');
  });
});

describe('calmer sustained setup without automatic execution', () => {
  it('keeps source and defaults visible while seed, numerical controls and detailed limits start collapsed', () => {
    const setConfig = vi.fn();
    const html = renderToStaticMarkup(<MyReservoirConfig config={DEFAULT_SUSTAINED_CONFIG} setConfig={setConfig} disabled={false}/>);
    const advanced = html.indexOf('<details class="my-reservoir-advanced">');
    expect(advanced).toBeGreaterThan(0);
    expect(html.indexOf('Reply source')).toBeLessThan(advanced);
    expect(html.indexOf('Selected session limits')).toBeLessThan(advanced);
    expect(html.indexOf('Seed · unsigned integer')).toBeGreaterThan(advanced);
    expect(html.indexOf('Maximum numerical steps')).toBeGreaterThan(advanced);
    expect(html.indexOf('Leak · new-state mix')).toBeGreaterThan(advanced);
    expect(html).not.toMatch(/<details[^>]*\bopen/);
    expect(html).toContain('Every 30 steps'); expect(html).toContain('1 second per step');
    expect(html).toContain('6 hours'); expect(html).toContain('256 MiB');
    expect(html.indexOf('Up to 10800 numerical steps or 360 writing attempts, including retries')).toBeLessThan(advanced);
    expect(html).toContain('first run or storage limit reached holds execution');
    expect(html).toContain('Synthetic writing from a deterministic script');
    expect(html).not.toContain('Check local model');
    expect(setConfig).not.toHaveBeenCalled(); expect(invoke).not.toHaveBeenCalled();
  });
  it('retains arbitrary accepted seconds in an exact hours/minutes/seconds editor', () => {
    const html = renderToStaticMarkup(<MyReservoirConfig config={{ ...DEFAULT_SUSTAINED_CONFIG, maximumDurationSeconds: 3661 }} setConfig={() => {}} disabled={false}/>);
    expect(html).toContain('1 hour 1 minute 1 second'); expect(html).toContain('exactly 3661 seconds');
    expect(html).toContain('Hours<input'); expect(html).toContain('Minutes<input'); expect(html).toContain('Seconds<input');
    const invalid = renderToStaticMarkup(<MyReservoirConfig config={{ ...DEFAULT_SUSTAINED_CONFIG, maximumDurationSeconds: Number.NaN }} setConfig={() => {}} disabled={false}/>);
    expect(invalid).toContain('role="alert"'); expect(invalid).toContain('from 1 second to 24 hours');
    expect(invalid).not.toContain('exactly NaN seconds');
  });
  it('describes fresh v8 measurement meanings separately from every retained earlier contract', () => {
    const render = (config: typeof DEFAULT_SUSTAINED_CONFIG) => renderToStaticMarkup(<MyReservoirConfig config={config} setConfig={() => {}} disabled={false}/>);
    expect(render(DEFAULT_SUSTAINED_CONFIG)).toContain('clearer measurement meanings and the held writing boundary');
    const v7 = render({ ...DEFAULT_SUSTAINED_CONFIG, promptVersion: 'reservoir-journal-v7' });
    expect(v7).toContain('held writing boundary and the recorded prior feedback application');
    expect(v7).not.toContain('clearer measurement meanings');
    const v6 = render({ ...DEFAULT_SUSTAINED_CONFIG, promptVersion: 'reservoir-journal-v6' });
    expect(v6).toContain('compact optional readout and explicit limits on what writing can change');
    expect(v6).not.toContain('held writing boundary');
    const v5 = render({ ...DEFAULT_SUSTAINED_CONFIG, promptVersion: 'reservoir-journal-v5' });
    expect(v5).toContain('compact optional readout and the complete previous journal near the invitation');
    expect(v5).toContain('prompt supplies only current and prior recurrent RMS');
    expect(v5).not.toContain('explicit limits on what writing can change');
    expect(render(DEFAULT_SUSTAINED_CONFIG)).toContain('retains the full numerical observation for Evidence');
    expect(render(DEFAULT_SUSTAINED_CONFIG)).toContain('prompt supplies only current and prior recurrent RMS');
    expect(render(DEFAULT_SUSTAINED_CONFIG)).not.toContain('Each writing opportunity includes all 32 reservoir coordinates');
    expect(render({ ...DEFAULT_SUSTAINED_CONFIG, promptVersion: 'reservoir-journal-v4' })).toContain('current and previous observed measurements kept separate from prior prose');
    expect(render({ ...DEFAULT_SUSTAINED_CONFIG, promptVersion: 'reservoir-journal-v4' })).toContain('Each writing opportunity includes all 32 reservoir coordinates');
    expect(render({ ...DEFAULT_SUSTAINED_CONFIG, promptVersion: 'reservoir-journal-v3' })).toContain('current readings and prior writing as context');
    expect(render({ ...DEFAULT_SUSTAINED_CONFIG, promptVersion: 'reservoir-journal-v2' })).toContain('structured grounded observations');
    const { promptVersion: _version, ...legacy } = DEFAULT_SUSTAINED_CONFIG;
    expect(render(legacy)).toContain('original observation and memory contract');
  });
  it('explains actual text feedback without prescribing prose or implying that setup executes it', () => {
    const setConfig = vi.fn(), html = renderToStaticMarkup(<MyReservoirConfig config={DEFAULT_SUSTAINED_CONFIG} setConfig={setConfig} disabled={false}/>);
    const visibleAfterAdvanced = html.split('</details>')[1];
    expect(visibleAfterAdvanced).toContain('The topic and form stay open');
    expect(visibleAfterAdvanced).toContain('Once saved and checked, writing can contribute a numerical signal at the next step');
    expect(visibleAfterAdvanced).toContain('Only after application can its full text return in a later prompt');
    expect(visibleAfterAdvanced).toContain('Describing a control change does not execute it');
    expect(visibleAfterAdvanced).toContain('Create prepares local state; Start is a separate action');
    expect(visibleAfterAdvanced).not.toContain('Seed · unsigned integer');
    expect(html).not.toMatch(/<details[^>]*\bopen/);
    expect(setConfig).not.toHaveBeenCalled(); expect(invoke).not.toHaveBeenCalled();
  });
  it('changing source prepares explicit blank local settings without changing numerical defaults or contacting anything', () => {
    const setConfig = vi.fn();
    const tree = MyReservoirConfig({ config: DEFAULT_SUSTAINED_CONFIG, setConfig, disabled: false });
    const source = elements(tree).find(element => element.type === 'select' && element.props.value === 'scripted')!;
    (source.props.onChange as (event: { target: { value: string } }) => void)({ target: { value: 'ollama' } });
    const configured = setConfig.mock.calls[0][0];
    expect(configured).toEqual({ ...DEFAULT_SUSTAINED_CONFIG, language: { backend: 'ollama', endpoint: '', model: '', contextTokens: 8192, responseFormat: null } });
    new LocalModelController().select(configured.language);
    expect(invoke).not.toHaveBeenCalled();
  });
  it('keeps exact endpoint/model/readiness outside Advanced settings and respects disabled editing', () => {
    const config = { ...DEFAULT_SUSTAINED_CONFIG, language: { backend: 'ollama' as const, endpoint: 'http://127.0.0.1:11435', model: 'chosen:exact', contextTokens: 4096, responseFormat: null } };
    const setConfig = vi.fn(), html = renderToStaticMarkup(<MyReservoirConfig config={config} setConfig={setConfig} disabled/>);
    const advanced = html.indexOf('<details class="my-reservoir-advanced">');
    expect(html).toContain('<fieldset disabled="">');
    expect(html.indexOf('HTTP loopback endpoint')).toBeLessThan(advanced);
    expect(html.indexOf('chosen:exact')).toBeLessThan(advanced);
    expect(html.indexOf('Check local model')).toBeLessThan(advanced);
    expect(html.indexOf('Maximum output tokens per entry')).toBeGreaterThan(advanced);
    expect(html.indexOf('Request deadline · seconds')).toBeGreaterThan(advanced);
    expect(html.indexOf('Context tokens')).toBeGreaterThan(advanced);
    expect(html).toContain('1,024 output tokens per entry, within 3 minutes');
    expect(html).toContain('ceilings, not a requested length');
    expect(html).toMatch(/<button type="button" disabled="">Check local model<\/button>/);
    expect(html).toContain('Create saves local configuration only');
    expect(html).toContain('Start explicitly begins the session');
    expect(setConfig).not.toHaveBeenCalled(); expect(invoke).not.toHaveBeenCalled();
  });
  it('keeps a cleared output limit invalid and displays historical ceilings without upgrading them', () => {
    const config = { ...DEFAULT_SUSTAINED_CONFIG, language: { backend: 'ollama' as const, endpoint: '', model: '', contextTokens: 8192 } };
    const setConfig = vi.fn(), tree = MyReservoirConfig({ config, setConfig, disabled: false });
    const limit = elements(tree).find(element => element.type === 'input' && element.props.max === '2048')!;
    (limit.props.onChange as (event: { target: { value: string } }) => void)({ target: { value: '' } });
    expect(setConfig.mock.calls[0][0].outputTokens).toBeNaN();
    const invalid = renderToStaticMarkup(<MyReservoirConfig config={setConfig.mock.calls[0][0]} setConfig={setConfig} disabled={false}/>);
    expect(invalid).toContain('Use 256–2,048 whole output tokens'); expect(invalid).not.toContain('NaN output tokens');
    const { outputTokens: _output, requestDeadlineSeconds: _deadline, ...legacy } = config;
    const html = renderToStaticMarkup(<MyReservoirConfig config={legacy} setConfig={setConfig} disabled={false}/>);
    expect(html).toContain('256 output tokens per entry, within 1 minute');
    expect(legacy).not.toHaveProperty('outputTokens');
  });
});
