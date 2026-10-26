import { Children, isValidElement, type ReactElement, type ReactNode } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoirConfig from './MyReservoirConfig';
import { DEFAULT_SUSTAINED_CONFIG, FRAME_ARM_PROMPT_VERSIONS, type SustainedConfig } from './myReservoirTypes';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));

const plainJournal = 'reservoir-journal-inert-plain-contract-no-tag-v1';
const render = (config: SustainedConfig, disabled = false, setConfig = vi.fn()) => renderToStaticMarkup(<MyReservoirConfig config={config} setConfig={setConfig} disabled={disabled}/>);
const invitationOptions = (html: string) => html.match(/Writing invitation<select[^>]*>(.*?)<\/select>/)?.[1] ?? '';

function elements(node: ReactNode): ReactElement<Record<string, unknown>>[] {
  if (!isValidElement<Record<string, unknown>>(node)) return [];
  const result = [node];
  Children.forEach(node.props.children as ReactNode, child => result.push(...elements(child)));
  return result;
}

describe('writing invitation choice', () => {
  it('offers the readout and plain journal in Advanced settings without changing the fresh default', () => {
    const setConfig = vi.fn(), html = render(DEFAULT_SUSTAINED_CONFIG, false, setConfig);
    expect(html.indexOf('Writing invitation')).toBeGreaterThan(html.indexOf('<details class="my-reservoir-advanced">'));
    const options = invitationOptions(html);
    expect(options).toContain('<option value="reservoir-journal-v8" selected="">Current readout (as built)</option>');
    expect(options).toContain(`<option value="${plainJournal}">Plain journal · prior text, no numerical readout</option>`);
    expect(options.match(/<option /g)).toHaveLength(2);
    expect(DEFAULT_SUSTAINED_CONFIG.promptVersion).toBe('reservoir-journal-v8');
    expect(setConfig).not.toHaveBeenCalled();
  });

  it('selects the plain invitation explicitly without changing model, memory or run settings', () => {
    const config: SustainedConfig = { ...DEFAULT_SUSTAINED_CONFIG, memoryPolicy: 'random-older', memoryRecentExclusion: 3, language: { backend: 'ollama', model: 'chosen:exact', endpoint: 'http://127.0.0.1:11434', contextTokens: 8192, temperature: 0.7, thinking: false } };
    const setConfig = vi.fn(), tree = MyReservoirConfig({ config, setConfig, disabled: false });
    const choice = elements(tree).find(element => element.type === 'select' && element.props.value === 'reservoir-journal-v8')!;
    (choice.props.onChange as (event: { target: { value: string } }) => void)({ target: { value: plainJournal } });
    expect(setConfig).toHaveBeenCalledExactlyOnceWith({ ...config, promptVersion: plainJournal });
    expect(config.promptVersion).toBe('reservoir-journal-v8');
    const html = render(setConfig.mock.calls[0][0]);
    expect(invitationOptions(html)).toContain(`<option value="${plainJournal}" selected="">`);
    expect(html).toContain('a standing plain contract and, when available, one saved entry; no numerical readout or context tag is sent');
    expect(html).toContain('The Earlier entry returned setting chooses the text (latest applied entry by default)');
    expect(html).not.toContain('Each writing opportunity includes all 32 reservoir coordinates');
  });

  it('preserves other research invitations and historical missing versions when displaying settings', () => {
    const setConfig = vi.fn();
    for (const promptVersion of [...FRAME_ARM_PROMPT_VERSIONS.filter(version => version !== plainJournal), 'reservoir-journal-v4'] as const) {
      const html = render({ ...DEFAULT_SUSTAINED_CONFIG, promptVersion }, false, setConfig);
      expect(invitationOptions(html)).toContain(`<option value="${promptVersion}" selected="">Research invitation · ${promptVersion}</option>`);
    }
    const { promptVersion: _version, ...legacy } = DEFAULT_SUSTAINED_CONFIG;
    expect(invitationOptions(render(legacy, false, setConfig))).toContain('<option value="reservoir-journal-v1" selected="">');
    expect(legacy).not.toHaveProperty('promptVersion');
    expect(setConfig).not.toHaveBeenCalled();
  });

  it('keeps the invitation within disabled session controls', () => {
    const html = render({ ...DEFAULT_SUSTAINED_CONFIG, promptVersion: plainJournal }, true);
    expect(html).toMatch(/<fieldset disabled=""><legend>Prepare your reservoir<\/legend>[\s\S]*Writing invitation<select/);
    expect(invitationOptions(html)).toContain(`<option value="${plainJournal}" selected="">`);
    expect(html).toContain('Saved sessions keep the prompt they were created with.');
  });
});
