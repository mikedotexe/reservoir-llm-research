import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import ActivationReadingCollection, { ActivationCollectionReader } from './ActivationReadingCollection';
import type { ActivationReadingApi, CollectionReading } from './activationReadingTypes';

function fixture(): CollectionReading {
  return {
    id: 'reading-a', entries: [{ id: 'journal-1', status: 'complete', text: '<script>inert writing</script>\nFinal paragraph.', sha256: 'a'.repeat(64), observedStep: 20, savedStep: 20, appliedStep: 21, requestId: 'request-5', prompt: 'Exact invitation with earlier prose.', promptSha256: 'b'.repeat(64), stopReason: 'eos', contentTokens: 10, sourceResponseSha256: 'c'.repeat(64), eventIds: ['event-1'] }],
    events: [{ id: 'event-1', kind: 'quietReceived', step: 10, observation: '<script>inert quiet observation</script>' }],
    disclosure: { arm: 'recurrent', sourceAttempt: 'Distinct historical attempt', sourceSession: 'source-private-identity', sourceFormat: 'activation-session-v1', recordSha256: 'd'.repeat(64), modelManifestSha256: 'e'.repeat(64), calibrationSha256: 'f'.repeat(64), modelId: 'test-model', modelRevision: 'test-revision', protocol: { seed: 1, stepsBetween: 10, journalEvery: 2, maxJournalTokens: 1024, gain: 0.01 }, notes: [{ title: 'Earlier reading', text: 'Interpretation and another possible reading.', sha256: '0'.repeat(64), sourceSha256: '1'.repeat(64), attribution: 'Selected source note' }] },
  };
}

describe('Portable activation reading collection', () => {
  it('offers explicit offline opening without invoking model or file operations', () => {
    const api: ActivationReadingApi = { open: vi.fn(), export: vi.fn(), close: vi.fn() };
    const html = renderToStaticMarkup(<ActivationReadingCollection api={api}/>);
    expect(html).toContain('Read the included examples');
    expect(html).toContain('Open a reading collection');
    expect(api.open).not.toHaveBeenCalled(); expect(api.export).not.toHaveBeenCalled();
    expect(html).not.toContain('Start activation run');
    expect(renderToStaticMarkup(<ActivationReadingCollection api={api} active={false}/>)).toBe('');
  });
  it('starts at complete prose and keeps allocation, prompt and interpretations concealed', () => {
    const reading = fixture();
    const html = renderToStaticMarkup(<ActivationCollectionReader reading={reading} index={0} position={0} revealed={false} select={() => {}}/>);
    expect(html).toContain('Reading A'); expect(html).toContain('Final paragraph.');
    expect(html).toContain('&lt;script&gt;inert writing&lt;/script&gt;');
    expect(html).toContain('&lt;script&gt;inert quiet observation&lt;/script&gt;');
    expect(html).not.toContain('<script>'); expect(html).not.toContain('Recurrent reservoir');
    expect(html).not.toContain(reading.entries[0].prompt); expect(html).not.toContain(reading.disclosure.sourceSession);
    expect(html).not.toContain(reading.disclosure.notes[0].text); expect(html).not.toContain(reading.disclosure.modelManifestSha256);
  });
  it('reveals exact prompt, attributed notes and source identities only after disclosure', () => {
    const reading = fixture();
    const html = renderToStaticMarkup(<ActivationCollectionReader reading={reading} index={1} position={0} revealed select={() => {}}/>);
    expect(html).toContain('Reading B'); expect(html).toContain('Recurrent reservoir');
    expect(html).toContain(reading.entries[0].prompt); expect(html).toContain(reading.disclosure.sourceSession);
    expect(html).toContain(reading.disclosure.notes[0].text); expect(html).toContain(reading.disclosure.modelManifestSha256);
    expect(html).toContain('do not establish an intervention effect');
  });
  it('makes the complete event timeline a named keyboard-focusable scrolling region', () => {
    const reading = fixture();
    reading.events.push({ id: 'event-final', kind: 'journalApplied', step: 21, observation: null });
    const html = renderToStaticMarkup(<ActivationCollectionReader reading={reading} index={1} position={0} revealed={false} select={() => {}}/>);
    expect(html).toContain('class="activation-collection-timeline" role="region" aria-label="Reading B quiet observations and writing boundaries" tabindex="0"><ol>');
    expect(html).toContain('Step 21 · Journal feedback applied');
    expect(html).toContain('&lt;script&gt;inert quiet observation&lt;/script&gt;');
  });
  it('retains the entire unfinished response separately from completed journals', () => {
    const reading = fixture();
    const repeated = 'A deliberately repeated synthetic sentence.\n'.repeat(150) + 'Unfinished final fragment';
    reading.entries.push({ ...reading.entries[0], id: 'unfinished', status: 'incomplete', text: repeated, savedStep: null, appliedStep: null, observedStep: 40, contentTokens: 1024, stopReason: 'max_tokens' });
    const html = renderToStaticMarkup(<ActivationCollectionReader reading={reading} index={0} position={1} revealed={false} select={() => {}}/>);
    expect(html).toContain('1 completed journal'); expect(html).toContain('1 unfinished response');
    expect(html).toContain(repeated); expect(html).toContain('not saved as a journal or applied as feedback');
    expect(html).toContain('output ceiling'); expect(html).not.toContain('feedback first applied at step null');
  });
});
