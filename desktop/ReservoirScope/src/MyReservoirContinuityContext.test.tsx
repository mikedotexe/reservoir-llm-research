import { Children, isValidElement, type ReactElement, type ReactNode } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoirActionSetup from './MyReservoirActionSetup';
import MyReservoirConfig from './MyReservoirConfig';
import { CONTINUITY_CONTEXT_TOKENS, validAuthoredActionConfig, withAuthoredActionMode } from './authoredActions';
import { DEFAULT_SUSTAINED_CONFIG, validWritingLimits, type SustainedConfig } from './myReservoirTypes';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));

function elements(node: ReactNode): ReactElement<Record<string, unknown>>[] {
  if (!isValidElement<Record<string, unknown>>(node)) return [];
  const result = [node];
  Children.forEach(node.props.children as ReactNode, child => result.push(...elements(child)));
  return result;
}
const change = (element: ReactElement<Record<string, unknown>>, target: { value?: string; checked?: boolean }) =>
  (element.props.onChange as (event: { target: typeof target }) => void)({ target });
const local = (contextTokens = 8192): SustainedConfig => ({ ...DEFAULT_SUSTAINED_CONFIG, language: { backend: 'ollama', endpoint: 'http://127.0.0.1:11435', model: 'chosen:exact', contextTokens, temperature: .6, thinking: false, responseFormat: null } });

function actionSetup(config: SustainedConfig, setConfig: (config: SustainedConfig) => void): ReactNode {
  let tree: ReactNode;
  function Capture() { tree = MyReservoirActionSetup({ config, setConfig }); return tree; }
  renderToStaticMarkup(<Capture/>);
  return tree;
}

describe('context room for continuing inquiry', () => {
  it('raises context when actions are enabled after choosing a local model, preserving the other settings', () => {
    const original = local(), setConfig = vi.fn();
    const checkbox = elements(actionSetup(original, setConfig)).find(element => element.type === 'input' && element.props.type === 'checkbox')!;
    change(checkbox, { checked: true });
    const selected = setConfig.mock.calls[0][0] as SustainedConfig;
    expect(selected.actionMode).toBe('authored-v3');
    expect(selected.language).toEqual({ ...original.language, contextTokens: CONTINUITY_CONTEXT_TOKENS });
    expect(original.language.contextTokens).toBe(8192);
    expect(validWritingLimits(selected)).toBe(true);
  });

  it('uses the same context when the model source is chosen after enabling inquiry with offline writing', () => {
    const setConfig = vi.fn();
    const checkbox = elements(actionSetup(DEFAULT_SUSTAINED_CONFIG, setConfig)).find(element => element.type === 'input' && element.props.type === 'checkbox')!;
    change(checkbox, { checked: true });
    const scripted = setConfig.mock.calls[0][0] as SustainedConfig;
    expect(scripted.language).toEqual({ backend: 'scripted' });
    setConfig.mockClear();
    const source = elements(MyReservoirConfig({ config: scripted, setConfig, disabled: false })).find(element => element.type === 'select' && element.props.value === 'scripted')!;
    change(source, { value: 'ollama' });
    expect(setConfig.mock.calls[0][0]).toEqual({ ...scripted, language: { backend: 'ollama', endpoint: '', model: '', contextTokens: CONTINUITY_CONTEXT_TOKENS, responseFormat: null, temperature: .7 } });
  });

  it('applies the new preset on explicit v3 selection, preserving larger custom contexts and older mode defaults', () => {
    for (const context of [4096, 8192, 16384, 32768]) {
      const previous = withAuthoredActionMode(local(context), 'authored-v2'), setConfig = vi.fn();
      const selector = elements(actionSetup(previous, setConfig)).find(element => element.type === 'select' && element.props.value === 'authored-v2')!;
      change(selector, { value: 'authored-v3' });
      expect(setConfig.mock.calls[0][0].language.contextTokens).toBe(Math.max(context, CONTINUITY_CONTEXT_TOKENS));
      expect(previous.language.contextTokens).toBe(context);
    }
    for (const mode of ['authored-v1', 'authored-v2'] as const) {
      const previous = withAuthoredActionMode(local(), mode);
      expect(previous.language).toEqual(local().language);
      const scripted = withAuthoredActionMode(DEFAULT_SUSTAINED_CONFIG, mode), setConfig = vi.fn();
      const source = elements(MyReservoirConfig({ config: scripted, setConfig, disabled: false })).find(element => element.type === 'select' && element.props.value === 'scripted')!;
      change(source, { value: 'ollama' });
      expect(setConfig.mock.calls[0][0].language.contextTokens).toBe(8192);
    }
  });

  it('allows an explicit smaller research context and displays its limit without rewriting saved settings', () => {
    const configured = withAuthoredActionMode(local(), 'authored-v3'), setConfig = vi.fn();
    const contextInput = elements(MyReservoirConfig({ config: configured, setConfig, disabled: false })).find(element => element.type === 'input' && element.props.max === '32768')!;
    change(contextInput, { value: '4096' });
    const smaller = setConfig.mock.calls[0][0] as SustainedConfig;
    expect(smaller.language.contextTokens).toBe(4096);
    expect(validWritingLimits(smaller)).toBe(true);
    expect(validAuthoredActionConfig(smaller)).toBe(true);
    setConfig.mockClear();
    const html = renderToStaticMarkup(<MyReservoirConfig config={smaller} setConfig={setConfig} disabled/>);
    expect(html).toContain('Continuing inquiry uses 16,384 context tokens by default to make room for retained evidence. Smaller contexts may omit supplied material.');
    expect(html).toContain('max="32768" step="1" required="" value="4096"');
    expect(setConfig).not.toHaveBeenCalled();
    for (const mode of ['authored-v1', 'authored-v2', 'authored-v3'] as const) {
      const saved = { ...withAuthoredActionMode(local(), mode), language: local().language };
      const before = structuredClone(saved);
      renderToStaticMarkup(<MyReservoirConfig config={saved} setConfig={setConfig} disabled/>);
      expect(saved).toEqual(before);
      expect(saved.language.contextTokens).toBe(8192);
    }
    expect(setConfig).not.toHaveBeenCalled();
  });
});
