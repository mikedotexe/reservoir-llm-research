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

describe('pinned reading across growing history windows', () => {
  it('refreshes the same anchored window after repeated arrivals, then crosses the 20-entry boundary without losing entries', async () => {
    const { controller, push, api } = await history(21);
    const accepted = controller.snapshot(), ids = accepted.page!.entries.map(entry => entry.entryId);
    const action = vi.spyOn(api, 'action');
    for (const count of [24, 29, 36]) push({ revision: String(100 + count), step: count * 3 + 1, journalCount: count, turnCount: count });
    await controller.refreshJournals();
    expect(controller.snapshot().page?.entries.map(entry => entry.entryId)).toEqual(ids);
    expect(controller.snapshot().page?.offset).toBe(15);
    expect(controller.snapshot().journal).toBe(accepted.journal);
    expect(controller.snapshot().journalPosition).toBe(2);
    await controller.pageJournals('older');
    expect(controller.snapshot().page?.entries.map(entry => entry.entryId)).toEqual(['journal-2', 'journal-1']);
    await controller.pageJournals('newer');
    expect(controller.snapshot().page?.entries.map(entry => entry.entryId)).toEqual(ids);
    expect(controller.snapshot().journal).toBe(accepted.journal);
    expect(controller.snapshot().followLatest).toBe(false);
    expect(controller.snapshot().summary?.journalCount).toBe(36);
    expect(action).not.toHaveBeenCalled();
  });

  it('keeps a stable selected ordinal when the list moves away, and Earlier/Later continue from the selected text', async () => {
    const { controller, push } = await history();
    const accepted = controller.snapshot().journal;
    await controller.pageJournals('older'); await controller.pageJournals('older');
    expect(controller.snapshot().page?.entries.some(entry => entry.entryId === accepted?.entryId)).toBe(false);
    expect(controller.snapshot().journal).toBe(accepted);
    expect(controller.snapshot().journalPosition).toBe(26);
    push({ revision: '160', step: 151, journalCount: 50, turnCount: 50 });
    await controller.adjacentJournal('earlier');
    expect(controller.snapshot().journal?.entryId).toBe('journal-25');
    expect(controller.snapshot().journalPosition).toBe(25);
    await controller.adjacentJournal('later');
    expect(controller.snapshot().journal?.entryId).toBe('journal-26');
    expect(controller.snapshot().journalPosition).toBe(26);
  });

  it('manual history intent cancels a late latest detail while preserving the visible journal', async () => {
    for (const operation of ['refresh', 'older'] as const) {
      const { controller, api } = await history(21);
      const accepted = controller.snapshot().journal;
      let finish!: () => void;
      api.journal = (requestId, sessionId, generation) => new Promise(resolve => { finish = () => resolve({ requestId, sessionId, generation, revision: '100', journal: journal(21) }); });
      await controller.followLatest(); await settle();
      expect(controller.snapshot().readingJournal).toBe(true);
      if (operation === 'refresh') await controller.refreshJournals(); else await controller.pageJournals('older');
      finish(); await settle();
      expect(controller.snapshot().journal).toBe(accepted);
      expect(controller.snapshot().journalPosition).toBe(2);
      expect(controller.snapshot().followLatest).toBe(false);
      expect(controller.snapshot().readingJournal).toBe(false);
    }
  });

  it('corrects one arrival-shifted window but retains accepted history when repeated races exhaust the bound', async () => {
    for (const continuous of [false, true]) {
      const { controller, api, push } = await history(21);
      const accepted = controller.snapshot(), base = api.journals;
      let calls = 0;
      api.journals = async (...args) => {
        calls++;
        if (continuous || calls === 1) push({ revision: String(100 + calls), step: (21 + calls) * 3 + 1, journalCount: 21 + calls, turnCount: 21 + calls });
        return base(...args);
      };
      await controller.refreshJournals();
      expect(calls).toBe(2);
      expect(controller.snapshot().journal).toBe(accepted.journal);
      expect(controller.snapshot().readingPage).toBe(false);
      if (continuous) {
        expect(controller.snapshot().page).toBe(accepted.page);
        expect(controller.snapshot().journalError).toContain('try again');
      } else {
        expect(controller.snapshot().page?.entries.map(entry => entry.entryId)).toEqual(accepted.page?.entries.map(entry => entry.entryId));
        expect(controller.snapshot().page?.offset).toBe(1);
        expect(controller.snapshot().journalError).toBe('');
      }
    }
  });

  it('rejects a substituted anchor without replacing history or text, then Follow latest deliberately opens the newest', async () => {
    const { controller, api, push } = await history(21);
    const accepted = controller.snapshot(), base = api.journals;
    api.journals = async (...args) => {
      const result = await base(...args);
      result.entries = result.entries.map(entry => entry.entryId === 'journal-21' ? { ...entry, sha256: 'b'.repeat(64) } : entry);
      return result;
    };
    await controller.refreshJournals();
    expect(controller.snapshot().page).toBe(accepted.page);
    expect(controller.snapshot().journal).toBe(accepted.journal);
    expect(controller.snapshot().journalError).toContain('anchor');
    api.journals = base; push({ revision: '150', step: 109, journalCount: 36, turnCount: 36 });
    await controller.followLatest(); await settle();
    expect(controller.snapshot().journal?.entryId).toBe('journal-36');
    expect(controller.snapshot().journalPosition).toBe(36);
    expect(controller.snapshot().page?.offset).toBe(0);
    expect(controller.snapshot().followLatest).toBe(true);
  });
  it('keeps the accepted page and ordinal when an adjacent detail has a different saved hash', async () => {
    const { controller, api } = await history();
    const accepted = controller.snapshot(), base = api.journal;
    api.journal = async (...args) => {
      const result = await base(...args);
      return { ...result, journal: { ...result.journal, sha256: 'b'.repeat(64), saveReceipt: { ...result.journal.saveReceipt, sha256: 'b'.repeat(64) } } };
    };
    await controller.adjacentJournal('earlier');
    expect(controller.snapshot().page).toBe(accepted.page);
    expect(controller.snapshot().journal).toBe(accepted.journal);
    expect(controller.snapshot().journalPosition).toBe(26);
    expect(controller.snapshot().journalError).toContain('saved evidence');
  });

  it('Follow latest retries a failed detail read without treating its requested identity as displayed prose', async () => {
    const { controller, api } = await history(21);
    const accepted = controller.snapshot().journal, base = api.journal;
    api.journal = async () => { throw new Error('Temporary journal read failure'); };
    await controller.followLatest(); await settle();
    expect(controller.snapshot().journal).toBe(accepted);
    api.journal = base;
    await controller.followLatest(); await settle();
    expect(controller.snapshot().journal?.entryId).toBe('journal-21');
    expect(controller.snapshot().journalPosition).toBe(21);
    expect(controller.snapshot().journalError).toBe('');
  });

  it('Follow latest cancels an earlier manual detail even when the newest journal is already displayed', async () => {
    const { controller, api } = await history(21);
    await controller.selectJournal('journal-21');
    let finish!: () => void;
    api.journal = (requestId, sessionId, generation) => new Promise(resolve => { finish = () => resolve({ requestId, sessionId, generation, revision: '100', journal: journal(20) }); });
    const pending = controller.selectJournal('journal-20');
    await controller.followLatest(); await settle();
    finish(); await pending;
    expect(controller.snapshot().journal?.entryId).toBe('journal-21');
    expect(controller.snapshot().journalPosition).toBe(21);
    expect(controller.snapshot().followLatest).toBe(true);
    expect(controller.snapshot().readingJournal).toBe(false);
  });

});
