import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import MyReservoirJournals, { MyReservoirJournalDetail } from './MyReservoirJournals';
import { DEFAULT_SUSTAINED_CONFIG } from './myReservoirTypes';
import { journal, reservoirFixture, settle } from './myReservoirTestFixtures';

const disclosure = '<details class="my-reservoir-journal-evidence">';

describe('journal prose and optional evidence', () => {
  it('renders the complete journal as whitespace-preserved inert prose outside evidence', () => {
    const text = `  First line\n\n\t<script>not instructions</script> **literal markdown**\n${'A retained sentence.\n'.repeat(2000)}  Final line  `;
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={{ ...journal(), text }} revision="9"/>);
    const reading = html.split(disclosure)[0];
    expect(reading).toContain('<div class="my-reservoir-journal-prose" style="white-space:pre-wrap">  First line\n\n\t');
    expect(reading).toContain('&lt;script&gt;not instructions&lt;/script&gt; **literal markdown**');
    expect(reading).toContain('A retained sentence.\n'.repeat(2000));
    expect(reading).toContain('  Final line  </div>');
    expect(reading).not.toContain('<script>');
    expect(reading).not.toContain('<pre>');
    expect(reading).not.toContain('max-height');
    expect(reading).not.toContain('line-clamp');
  });

  it('keeps identity, source and full evidence in one closed disclosure', () => {
    const entry = {
      ...journal(2), entryId: 'long-entry-identity-unique', configuredModel: 'configured-model-unique', providerModel: 'returned-model-unique', tokenCount: 127,
      timing: { attemptId: 2, dispatchedAtMs: '18446744073709551614', receivedAtMs: '18446744073709551615', transportDurationMs: 987, publishedAtMs: '18446744073709551615' },
    };
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={entry} revision="9007199254740993" config={DEFAULT_SUSTAINED_CONFIG}/>);
    const [reading, evidence] = html.split(disclosure);
    expect(html.match(/<details\b/g)).toHaveLength(2);
    expect(evidence).toMatch(/^<summary>Evidence<\/summary>/);
    expect(html).not.toContain('<details open');
    for (const value of [entry.promptVersion, entry.entryId, entry.sha256, entry.configuredModel, entry.providerModel, '18446744073709551615', '9007199254740993']) {
      expect(reading).not.toContain(value);
      expect(evidence).toContain(value);
    }
    for (const label of ['Journal prompt version', 'Exact prompt', 'Versioned numerical observation', 'Retained full-text memory', 'Host request and save timing', 'Encoded features', 'Prepared semantic vector', 'Application evidence', 'Raw received reply']) expect(evidence).toContain(label);
    expect(evidence).toContain('&lt;script&gt;inert exact prompt&lt;/script&gt;');
    expect(evidence).toContain('Prior applied text');
    expect(evidence).toContain('0.1');
    expect(evidence).toContain('<dd>stop / 127</dd>');
    expect(evidence).toContain('<dd>1024 tokens</dd>');
    expect(evidence).toContain('<dd>180 seconds</dd>');
    expect(reading).not.toContain('Retained output ceiling');
    expect(evidence).toContain('987');
    expect(evidence).not.toContain('<script>');
  });

  it('keeps saved, applied and skipped boundaries visible without opening evidence', () => {
    const applied = renderToStaticMarkup(<MyReservoirJournalDetail journal={journal()} revision="1"/>).split(disclosure)[0];
    expect(applied).toContain('Writing at step 3');
    expect(applied).toContain('Saved and applied');
    expect(applied).toContain('first applied at step 4');
    expect(applied).toContain('does not train the model');
    for (const status of ['savedPendingApplication', 'skipped'] as const) {
      const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={{ ...journal(), status, firstAppliedStep: null, application: null }} revision="2"/>).split(disclosure)[0];
      expect(html).toContain('no first application recorded');
      expect(html).not.toContain('first applied at step 4');
      expect(html).toContain(status === 'skipped' ? 'explicitly skipped' : 'not yet eligible');
    }
  });

  it('removes list identities while preserving reading controls and selected older entry', async () => {
    const { controller, push } = reservoirFixture();
    await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
    push({ revision: '7', step: 7, journalCount: 2, turnCount: 2 });
    await controller.journals();
    await controller.selectJournal('journal-1');
    push({ revision: '10', step: 10, journalCount: 3, turnCount: 3 });
    const html = renderToStaticMarkup(<MyReservoirJournals state={controller.snapshot()} controller={controller}/>);
    const list = html.match(/<ul class="my-reservoir-journal-list">([\s\S]*?)<\/ul>/)?.[1];
    expect(list).toBeDefined();
    expect(list).not.toContain('journal-');
    expect(list).toContain('Step 3');
    expect(list).toContain('First applied 4');
    expect(html).toContain('Follow latest · 1 new');
    expect(html).toContain('Refresh this page');
    expect(html).toContain('Refresh selected application evidence');
    expect(html).toContain('Newer'); expect(html).toContain('Older');
    expect(controller.snapshot().journal?.entryId).toBe('journal-1');
    expect(controller.snapshot().followLatest).toBe(false);
  });
});
