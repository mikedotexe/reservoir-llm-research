import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import MyReservoirJournals, { MyReservoirJournalDetail } from './MyReservoirJournals';
import { DEFAULT_SUSTAINED_CONFIG } from './myReservoirTypes';
import { journal, reservoirFixture, reservoirSummary, settle } from './myReservoirTestFixtures';

const disclosure = '<details class="my-reservoir-journal-evidence">';

describe('journal prose and optional evidence', () => {
  it('renders the complete journal as whitespace-preserved inert prose outside evidence', () => {
    const text = `  First line\n\n\t<script>not instructions</script> **literal markdown**\nRMS: 0.8123; sensory fill: 19.7%\n${'A retained sentence.\n'.repeat(2000)}  Final line  `;
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={{ ...journal(), text }} revision="9"/>);
    const reading = html.split(disclosure)[0];
    expect(reading).toContain('<div class="my-reservoir-journal-prose" style="white-space:pre-wrap">  First line\n\n\t');
    expect(reading).toContain('&lt;script&gt;not instructions&lt;/script&gt; **literal markdown**');
    expect(reading).toContain('RMS: 0.8123; sensory fill: 19.7%');
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

  it('makes every scrollable evidence block keyboard reachable with a distinct accessible name', () => {
    const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={journal(2)} revision="9"/>);
    const evidence = html.split(disclosure)[1];
    const blocks = [...evidence.matchAll(/<pre tabindex="0" role="region" aria-label="([^"]+)">/g)];
    expect(blocks).toHaveLength(7);
    expect(new Set(blocks.map(block => block[1])).size).toBe(7);
    expect(evidence.match(/<pre\b/g)).toHaveLength(7);
    expect(html).not.toMatch(/<details[^>]*\bopen/);
    expect(evidence).toContain('&lt;script&gt;inert exact prompt&lt;/script&gt;');
  });

  it('keeps saved, applied and skipped boundaries visible without opening evidence', () => {
    const applied = renderToStaticMarkup(<MyReservoirJournalDetail journal={journal()} revision="1"/>).split(disclosure)[0];
    expect(applied).toContain('Entry at step 3');
    expect(applied).toContain('Saved · feedback applied');
    expect(applied).toContain('first applied at step 4');
    expect(applied).not.toContain('Its full text is eligible for later prompts');
    expect(renderToStaticMarkup(<MyReservoirJournalDetail journal={journal()} revision="1"/>).split(disclosure)[1]).toContain('Its full text is eligible for later prompts');
    expect(applied).not.toContain('Describing a control change does not execute it');
    expect(applied).not.toContain('saved at step');
    expect(applied).not.toContain('Encoded features');
    for (const status of ['savedPendingApplication', 'skipped'] as const) {
      const html = renderToStaticMarkup(<MyReservoirJournalDetail journal={{ ...journal(), status, firstAppliedStep: null, application: null }} revision="2"/>).split(disclosure)[0];
      expect(html).toContain('Entry at step 3');
      expect(html).toContain('no first application recorded');
      expect(html).not.toContain('first applied at step 4');
      expect(html).not.toContain('Its full text is eligible');
      expect(html).not.toContain('Saved · feedback applied');
      expect(html).not.toContain('saved at step');
      expect(html).not.toContain('Describing a control change does not execute it');
      expect(html).toContain(status === 'skipped' ? 'explicitly skipped' : 'not yet eligible');
    }
  });

  it('keeps claimed operations as inert writing rather than changing controls or application evidence', async () => {
    const { api, controller, push } = reservoirFixture();
    await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
    push({ revision: '7', step: 7, journalCount: 2, turnCount: 2 });
    const text = 'I set noise to 0.01 and applied feedback at step 999.\n<button>Start</button>';
    api.journal = async (requestId, sessionId, generation) => ({ requestId, sessionId, generation, revision: '7', journal: { ...journal(), text } });
    const action = vi.spyOn(api, 'action');
    await controller.selectJournal('journal-1');
    const before = controller.snapshot(), html = renderToStaticMarkup(<MyReservoirJournals state={before} controller={controller}/>);
    const prose = html.match(/<div class="my-reservoir-journal-prose"[^>]*>([\s\S]*?)<\/div>/)![1];
    expect(prose).toBe('I set noise to 0.01 and applied feedback at step 999.\n&lt;button&gt;Start&lt;/button&gt;');
    expect(html).toContain('Entry at step 3'); expect(html).toContain('first applied at step 4');
    expect(html).not.toMatch(/<button[^>]*>Start<\/button>/);
    expect(html).not.toContain('model-authored'); // The same reader also presents deterministic scripted writing.
    expect(action).not.toHaveBeenCalled();
    expect(controller.snapshot()).toBe(before);
    expect(before.summary?.config.noiseAmplitude).toBe(DEFAULT_SUSTAINED_CONFIG.noiseAmplitude);
    expect(before.journal?.firstAppliedStep).toBe(4);
    expect(html).not.toMatch(/<details[^>]*\bopen/);
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
    expect(html).toContain('Journal 1 of 3');
    expect(html).toContain('<strong aria-live="polite" aria-atomic="true">Journal 1 of 3</strong>');
    expect(html).toContain('Your selection stays here as new writing arrives.');
    expect(html).toContain('<button disabled="">Earlier entry</button>');
    expect(html).toContain('<button>Later entry</button>');
    expect(html).toContain('Refresh this page');
    expect(html).toContain('Refresh save and feedback details');
    expect(html).toContain('Newer'); expect(html).toContain('Older');
    expect(html).toContain('Entry at step 3'); expect(html).not.toContain('Entry at step 10');
    expect(html).toContain('first applied at step 4'); expect(html).not.toContain('first applied at step 11');
    expect(controller.snapshot().summary?.step).toBe(10);
    expect(controller.snapshot().journal?.entryId).toBe('journal-1');
    expect(controller.snapshot().followLatest).toBe(false);
  });

  it('makes automatic following explicitly pausable without moving the current reading', async () => {
    const { controller, push } = reservoirFixture();
    await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
    push({ revision: '7', step: 7, journalCount: 2, turnCount: 2 });
    await controller.followLatest();
    const following = renderToStaticMarkup(<MyReservoirJournals state={controller.snapshot()} controller={controller}/>);
    expect(following).toContain('<button aria-pressed="true">Pause following</button>');
    expect(following).toContain('Following latest: new entries open automatically.');
    expect(following).toContain('Journal 2 of 2');
    const entry = controller.snapshot().journal;
    controller.pinJournal();
    const pinned = renderToStaticMarkup(<MyReservoirJournals state={controller.snapshot()} controller={controller}/>);
    expect(pinned).toContain('<button aria-pressed="false">Follow latest</button>');
    expect(pinned).toContain('Your selection stays here as new writing arrives.');
    expect(controller.snapshot().journal).toBe(entry);
  });

  it('keeps reading errors visible with retained prose and puts routine refresh inside closed evidence', async () => {
    const { controller, push, api } = reservoirFixture();
    await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
    push({ revision: '7', step: 7, journalCount: 2, turnCount: 2 });
    await controller.journals(); await controller.selectJournal('journal-1');
    const accepted = controller.snapshot().journal;
    api.journal = async () => { throw new Error('Retained entry could not be verified.'); };
    await controller.refreshJournal();
    const html = renderToStaticMarkup(<MyReservoirJournals state={controller.snapshot()} controller={controller}/>);
    const [reading, evidence] = html.split(disclosure);
    expect(reading).toContain('role="alert"');
    expect(reading).toContain('Retained entry could not be verified.');
    expect(reading).toContain('Entry at step 3');
    expect(reading).not.toContain('Refresh save and feedback details');
    expect(evidence).toContain('Refresh save and feedback details');
    expect(html).not.toMatch(/<details[^>]*\bopen/);
    expect(controller.snapshot().journal).toBe(accepted);
  });
  it('labels the history window separately while a pinned entry outside it keeps adjacent reading controls', async () => {
    const { controller, push, api } = reservoirFixture();
    await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
    push({ revision: '100', step: 136, journalCount: 45, turnCount: 45 });
    await controller.journals(); await controller.selectJournal('journal-26');
    await controller.pageJournals('older'); await controller.pageJournals('older');
    const action = vi.spyOn(api, 'action');
    const html = renderToStaticMarkup(<MyReservoirJournals state={controller.snapshot()} controller={controller}/>);
    expect(html).toContain('History window · newest first');
    expect(html).toContain('Journal 26 of 45');
    expect(html).toContain('Your selected entry is outside this history window');
    expect(html).toContain('<button>Earlier entry</button>');
    expect(html).toContain('<button>Later entry</button>');
    expect(html).toContain('Entry at step 78');
    expect(controller.snapshot().journal?.entryId).toBe('journal-26');
    expect(action).not.toHaveBeenCalled();
  });

  it('shows pending save and pending application separately from the complete selected entry', () => {
    const { controller } = reservoirFixture();
    const base = { ...controller.snapshot(), journal: journal(), journalPosition: 1 };
    for (const [pending, expected] of [
      [{ pendingSave: { entryId: 'waiting', observedStep: 30, attemptId: 2 } }, 'Writing at step 30 · save not yet confirmed.'],
      [{ pendingApplication: { entryId: 'saved', observedStep: 30, intendedStep: 31, attemptId: 2 } }, 'Saved writing at step 30 · waiting for application at step 31.'],
    ] as const) {
      const html = renderToStaticMarkup(<MyReservoirJournals controller={controller} state={{ ...base, summary: reservoirSummary({ step: 30, journalCount: 1, turnCount: 2, ...pending }) }}/>);
      expect(html).toContain(`<p class="my-reservoir-journal-progress" role="status">${expected}</p>`);
      expect(html).toContain('Entry at step 3');
      expect(html).toContain('first applied at step 4');
      expect(html).not.toContain('first applied at step 31');
      expect(html.indexOf('class="my-reservoir-journal-prose"')).toBeLessThan(html.indexOf('aria-label="Journal history"'));
    }
  });

});
