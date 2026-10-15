import { describe, expect, it, vi } from 'vitest';
import { DEFAULT_SUSTAINED_CONFIG } from './myReservoirTypes';
import { journal, reservoirFixture, row, settle } from './myReservoirTestFixtures';

async function history(count = 45) {
  const fixture = reservoirFixture();
  await fixture.controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
  fixture.push({ revision: '100', step: count * 3 + 1, journalCount: count, turnCount: count });
  await fixture.controller.journals();
  await fixture.controller.selectJournal(`journal-${count - 19}`);
  return fixture;
}

describe('journal reading order without moving the numerical clock', () => {
  it('crosses history pages by anchored adjacent entries, then reverses within the accepted page', async () => {
    const { controller, api } = await history();
    const frame = controller.snapshot().frame, action = vi.spyOn(api, 'action'), pages = vi.spyOn(api, 'journals');
    await controller.adjacentJournal('earlier');
    expect(controller.snapshot().journal?.entryId).toBe('journal-25');
    expect(controller.snapshot().page?.offset).toBe(18);
    expect(pages).toHaveBeenCalledWith(expect.any(String), 'personal-1', '1', 18, 20);
    await controller.adjacentJournal('later');
    expect(controller.snapshot().journal?.entryId).toBe('journal-26');
    expect(pages).toHaveBeenCalledOnce();
    expect(controller.snapshot().followLatest).toBe(false);
    expect(controller.snapshot().frame).toBe(frame);
    expect(action).not.toHaveBeenCalled();
  });

  it('uses saved-entry positions rather than attempt IDs and stops at both ends', async () => {
    const { controller, api } = await history(21);
    await controller.selectJournal('journal-21');
    const detail = vi.spyOn(api, 'journal'), pages = vi.spyOn(api, 'journals');
    await controller.adjacentJournal('later');
    expect(detail).not.toHaveBeenCalled(); expect(pages).not.toHaveBeenCalled();
    // A failed attempt may create gaps in turn/attempt IDs without a journal.
    api.journals = async (requestId, sessionId, generation, offset) => ({ requestId, sessionId, generation, revision: '100', offset, total: 21, hasMore: false, entries: [{ ...row(2), turnId: 9, attemptId: 12 }, { ...row(1), turnId: 4, attemptId: 6 }] });
    await controller.journals(19); await controller.selectJournal('journal-2');
    await controller.adjacentJournal('earlier');
    expect(controller.snapshot().journal?.entryId).toBe('journal-1');
    detail.mockClear();
    await controller.adjacentJournal('earlier'); expect(detail).not.toHaveBeenCalled();
  });

  it('finds the same neighbor when new journals shift offsets during the page request', async () => {
    const { controller, api, push } = await history();
    const base = api.journals;
    api.journals = async (...args) => { push({ revision: '102', step: 142, journalCount: 47, turnCount: 47 }); return base(...args); };
    await controller.adjacentJournal('earlier');
    expect(controller.snapshot().journal?.entryId).toBe('journal-25');
    expect(controller.snapshot().page?.total).toBe(47);
    expect(controller.snapshot().summary?.step).toBe(142);
  });

  it('can read the next newly saved entry without jumping straight to the newest', async () => {
    const { controller, push } = await history();
    await controller.selectJournal('journal-45');
    push({ revision: '103', step: 145, journalCount: 48, turnCount: 48 });
    await controller.adjacentJournal('later');
    expect(controller.snapshot().journal?.entryId).toBe('journal-46');
    expect(controller.snapshot().followLatest).toBe(false);
  });

  it('retains the page and prose when the anchor, ordinal or page revision cannot be verified', async () => {
    for (const failure of ['missing-anchor', 'wrong-ordinal', 'stale-revision', 'wrong-hash'] as const) {
      const { controller, api } = await history();
      const accepted = controller.snapshot(), base = api.journals, details = vi.spyOn(api, 'journal');
      api.journals = async (...args) => {
        const result = await base(...args);
        if (failure === 'missing-anchor') result.entries = result.entries.filter(entry => entry.entryId !== 'journal-26');
        if (failure === 'wrong-ordinal') result.total++;
        if (failure === 'stale-revision') result.revision = '99';
        if (failure === 'wrong-hash') result.entries = result.entries.map(entry => entry.entryId === 'journal-26' ? { ...entry, sha256: 'b'.repeat(64) } : entry);
        return result;
      };
      await controller.adjacentJournal('earlier');
      expect(controller.snapshot().journal).toBe(accepted.journal);
      expect(controller.snapshot().page).toBe(accepted.page);
      expect(controller.snapshot().journalError).toContain('unchanged');
      expect(controller.snapshot().readingPage).toBe(false);
      expect(details).not.toHaveBeenCalled();
    }
  });

  it('ignores a late adjacent page after an explicit selection or a replacement generation', async () => {
    for (const replace of [false, true]) {
      const { controller, api } = await history();
      const base = api.journals; let finish!: () => void;
      api.journals = (...args) => new Promise(resolve => { finish = async () => resolve(await base(...args)); });
      const pending = controller.adjacentJournal('earlier');
      if (replace) { await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle(); }
      else await controller.selectJournal('journal-40');
      finish(); await pending;
      expect(controller.snapshot().journal?.entryId ?? null).toBe(replace ? null : 'journal-40');
      expect(controller.snapshot().readingPage).toBe(false);
      expect(controller.snapshot().journalError).toBe('');
    }
  });

  it('retains current prose with a visible error when the adjacent detail fails after a valid page', async () => {
    const { controller, api } = await history(); const accepted = controller.snapshot().journal;
    api.journal = async () => { throw new Error('Adjacent journal failed its hash check.'); };
    await controller.adjacentJournal('earlier');
    expect(controller.snapshot().journal).toBe(accepted);
    expect(controller.snapshot().page?.entries.some(entry => entry.entryId === accepted?.entryId)).toBe(true);
    expect(controller.snapshot().journalError).toContain('hash check');
  });

  it('does not let a late pending-application refresh replace successful cross-page navigation', async () => {
    const { controller, api, push } = await history();
    api.journal = async (requestId, sessionId, generation) => ({ requestId, sessionId, generation, revision: '100', journal: { ...journal(26), firstAppliedStep: null, status: 'savedPendingApplication', application: null } });
    await controller.selectJournal('journal-26');
    controller.setActive(true);
    const basePage = api.journals; let finishPage!: () => void, finishRefresh!: () => void;
    api.journals = (...args) => new Promise(resolve => { finishPage = async () => resolve(await basePage(...args)); });
    api.journal = (requestId, sessionId, generation, entryId) => entryId === 'journal-26'
      ? new Promise(resolve => { finishRefresh = () => resolve({ requestId, sessionId, generation, revision: '101', journal: journal(26) }); })
      : Promise.resolve({ requestId, sessionId, generation, revision: '101', journal: journal(25) });
    const navigation = controller.adjacentJournal('earlier');
    push({ revision: '101', step: 137 });
    expect(controller.snapshot().readingJournal).toBe(true);
    finishPage(); await navigation;
    expect(controller.snapshot().journal?.entryId).toBe('journal-25');
    finishRefresh(); await settle();
    expect(controller.snapshot().journal?.entryId).toBe('journal-25');
    expect(controller.snapshot().frame?.step).toBe('137');
  });

  it('pins the visible journal while an automatic latest detail is still arriving', async () => {
    const { controller, api, push } = await history();
    controller.setActive(true); await controller.followLatest(); await settle();
    expect(controller.snapshot().journal?.entryId).toBe('journal-45');
    let finish!: () => void;
    api.journal = (requestId, sessionId, generation) => new Promise(resolve => { finish = () => resolve({ requestId, sessionId, generation, revision: '101', journal: journal(46) }); });
    push({ revision: '101', step: 139, journalCount: 46, turnCount: 46 }); await settle();
    expect(controller.snapshot().readingJournal).toBe(true);
    const action = vi.spyOn(api, 'action'); controller.pinJournal(); finish(); await settle();
    push({ revision: '102', step: 142, journalCount: 47, turnCount: 47 }); await settle();
    expect(controller.snapshot().journal?.entryId).toBe('journal-45');
    expect(controller.snapshot().followLatest).toBe(false);
    expect(controller.snapshot().readingJournal).toBe(false);
    expect(controller.snapshot().summary!.journalCount - controller.snapshot().seenJournalCount).toBe(1);
    expect(action).not.toHaveBeenCalled();
  });
});
