import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { ControlFeedback, sameControlDiagnostics, validControlDiagnostics } from './controlFeedback';
import { validAuthoredActionConfig, withAuthoredActionMode } from './authoredActions';
import { DEFAULT_SUSTAINED_CONFIG, validFieldControls, type SustainedControlDiagnostics } from './myReservoirTypes';
import { reservoirFixture, settle } from './myReservoirTestFixtures';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn(), isTauri: () => true }));
const diagnostics = (): SustainedControlDiagnostics => ({
  next: { candidateCount: 1, candidate: { line: 4, excerpt: '**NEXT: <script>inert</script>**', truncated: false }, explanation: 'Use a plain NEXT: line.' },
  reservoirInput: { candidateCount: 0, candidate: null, explanation: 'Text is sent.' },
  inquiry: { candidateCount: 0, candidate: null, explanation: 'Inquiry unchanged.' },
});
describe('versioned feedback and Unicode admission', () => {
  it('renders all independent channels with inert escaped excerpts', () => {
    const html = renderToStaticMarkup(<ControlFeedback diagnostics={diagnostics()}/>);
    expect(html).toContain('Control feedback'); expect(html).toContain('Text is sent.'); expect(html).toContain('Inquiry unchanged.');
    expect(html).toContain('&lt;script&gt;inert&lt;/script&gt;'); expect(html).not.toContain('<script>');
  });
  it('bounds Unicode excerpts by bytes and compares every retained diagnostic', () => {
    const d = diagnostics(); expect(validControlDiagnostics(d)).toBe(true);
    expect(sameControlDiagnostics(d, structuredClone(d))).toBe(true);
    const other = structuredClone(d); other.inquiry.explanation = 'invented'; expect(sameControlDiagnostics(d, other)).toBe(false);
    d.next.candidate!.excerpt = '🪨'.repeat(65); expect(validControlDiagnostics(d)).toBe(false);
    d.next.candidate!.excerpt = '🪨'.repeat(64); d.next.candidate!.truncated = true; expect(validControlDiagnostics(d)).toBe(true);
    d.next.candidateCount = 0; expect(validControlDiagnostics(d)).toBe(false);
    expect(validControlDiagnostics({ ...diagnostics(), inquiry: { ...diagnostics().inquiry, explanation: 'a'.repeat(1025) } })).toBe(false);
  });
  it('selects the new policy explicitly and rejects invalid policy/codec pairs', () => {
    const config = withAuthoredActionMode(DEFAULT_SUSTAINED_CONFIG, 'authored-v3');
    expect(config.controlFeedback).toBe('diagnostic-v1'); expect(validAuthoredActionConfig(config)).toBe(true);
    expect(withAuthoredActionMode(config, 'authored-v2').controlFeedback).toBeUndefined();
    expect(validAuthoredActionConfig({ ...DEFAULT_SUSTAINED_CONFIG, controlFeedback: 'diagnostic-v1' })).toBe(false);
    expect(validFieldControls({ ...config, textAdmission: 'utf8-v1' })).toBe(false);
    expect(validFieldControls({ ...config, embeddingModel: 'fixture', textAdmission: 'utf8-v1' })).toBe(true);
  });
  it('rejects attempts to change an existing session policy', async () => {
    const { controller, push } = reservoirFixture();
    await controller.create(DEFAULT_SUSTAINED_CONFIG); await controller.connect(); await settle();
    const original = controller.snapshot().summary;
    push({ revision: '2', config: { ...DEFAULT_SUSTAINED_CONFIG, embeddingModel: 'fixture', textAdmission: 'utf8-v1' } });
    expect(controller.snapshot().summary).toBe(original);
    expect(controller.snapshot().error).toContain('saved text admission or control feedback policy');
  });
});
