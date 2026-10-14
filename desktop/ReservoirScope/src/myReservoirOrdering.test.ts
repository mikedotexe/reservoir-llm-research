import { describe, expect, it, vi } from 'vitest';
import { DEFAULT_SUSTAINED_CONFIG, type SustainedUpdate } from './myReservoirTypes';
import { reservoirFixture, reservoirSummary, reservoirFrame, settle } from './myReservoirTestFixtures';

describe('sustained process-local snapshot ordering', () => {
  it('keeps a newer settled Stop update when the same-revision command response arrives last', async () => {
    const { controller, api, channel, nextSequence } = reservoirFixture();
    await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
    let finish!: () => void;
    const stopped = reservoirSummary({ revision: '2', phase: 'stopped', canStart: false, canPause: true, canStop: false });
    api.action = (_action, requestId) => {
      const response: SustainedUpdate = { requestId, snapshotSequence: nextSequence(), summary: stopped, frame: null, closeRequested: false };
      return new Promise(resolve => { finish = () => resolve(response); });
    };
    const command = controller.action('stop'), c = channel();
    c.listener({ requestId: c.id, snapshotSequence: nextSequence(), summary: { ...stopped, canPause: false }, frame: null, closeRequested: false });
    const settled = controller.snapshot().summary;
    finish(); expect(await command).toBe(true);
    expect(controller.snapshot().summary).toBe(settled); expect(controller.snapshot().summary?.canPause).toBe(false); expect(controller.snapshot().busy).toBeNull();
    const exportCall = vi.spyOn(api, 'export'); await controller.export();
    expect(exportCall).toHaveBeenCalledWith(expect.any(String), 'personal-1', '1', '2'); // persisted revision, not the snapshot sequence
  });

  it('uses exact integers above JavaScript number precision and ignores duplicate/older snapshots', async () => {
    const { controller, channel } = reservoirFixture(); await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
    const c = channel(), publish = (snapshotSequence: string, canPause: boolean) => c.listener({ requestId: c.id, snapshotSequence, summary: reservoirSummary({ revision: '2', canPause }), frame: null, closeRequested: false });
    publish('9007199254740993', false); const accepted = controller.snapshot().summary;
    publish('9007199254740992', true); expect(controller.snapshot().summary).toBe(accepted);
    publish('9007199254740993', true); expect(controller.snapshot().summary).toBe(accepted);
    publish('9007199254740994', true); expect(controller.snapshot().summary?.canPause).toBe(true); expect(controller.snapshot().summary).not.toBe(accepted);
  });

  it('invalid or unrelated envelopes cannot consume the accepted sequence', async () => {
    const { controller, channel, nextSequence } = reservoirFixture(); await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
    const c = channel(), accepted = controller.snapshot().summary;
    for (const snapshotSequence of ['0', '01', '-1', '1.5', '18446744073709551616', 'not-a-number']) {
      c.listener({ requestId: c.id, snapshotSequence, summary: reservoirSummary({ revision: '2' }), frame: null, closeRequested: false });
      expect(controller.snapshot().summary).toBe(accepted); expect(controller.snapshot().error).toContain('canonical snapshot sequence');
    }
    c.listener({ requestId: 'another-request', snapshotSequence: '18446744073709551615', summary: reservoirSummary({ revision: '2' }), frame: null, closeRequested: false });
    c.listener({ requestId: c.id, snapshotSequence: '18446744073709551615', summary: reservoirSummary({ generation: '99', revision: '2' }), frame: null, closeRequested: false });
    c.listener({ requestId: c.id, snapshotSequence: '18446744073709551615', summary: reservoirSummary({ revision: '2', step: 1 }), frame: { ...reservoirFrame(1), state: [1] }, closeRequested: false });
    expect(controller.snapshot().summary).toBe(accepted);
    c.listener({ requestId: c.id, snapshotSequence: nextSequence(), summary: reservoirSummary({ revision: '2', canPause: true }), frame: null, closeRequested: false });
    expect(controller.snapshot().summary?.canPause).toBe(true);
  });

  it('preserves process ordering across new owners even when their persisted revisions restart', async () => {
    const { controller, api, push, channel, nextSequence } = reservoirFixture(); await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
    push({ revision: '8', step: 7 }); const oldChannel = channel();
    await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle();
    expect(controller.snapshot().summary?.sessionId).toBe('personal-2'); expect(controller.snapshot().summary?.revision).toBe('1');
    oldChannel.listener({ requestId: oldChannel.id, snapshotSequence: '18446744073709551615', summary: reservoirSummary({ revision: '99' }), frame: null, closeRequested: true });
    push({ revision: '2', step: 1 }); expect(controller.snapshot().summary?.sessionId).toBe('personal-2'); expect(controller.snapshot().frame?.step).toBe('1'); expect(controller.snapshot().closeRequested).toBe(false);
    const current = controller.snapshot().summary;
    api.create = async requestId => ({ requestId, snapshotSequence: '1', summary: reservoirSummary({ sessionId: 'personal-3', generation: '3' }), frame: null, closeRequested: false });
    expect(await controller.create(DEFAULT_SUSTAINED_CONFIG)).toBe(false); expect(controller.snapshot().summary).toBe(current);
    const c = channel(); c.listener({ requestId: c.id, snapshotSequence: nextSequence(), summary: { ...current!, revision: '3' }, frame: reservoirFrame(1), closeRequested: false });
    expect(controller.snapshot().summary?.revision).toBe('3');
  });

  it('orders null initial-session snapshots without inventing an owner', async () => {
    const { controller, channel, nextSequence } = reservoirFixture(); await controller.connect(); const c = channel();
    const sequence = nextSequence();
    c.listener({ requestId: c.id, snapshotSequence: sequence, summary: null, frame: null, closeRequested: true });
    c.listener({ requestId: c.id, snapshotSequence: sequence, summary: null, frame: null, closeRequested: false });
    expect(controller.snapshot().summary).toBeNull(); expect(controller.snapshot().closeRequested).toBe(true);
    c.listener({ requestId: c.id, snapshotSequence: nextSequence(), summary: null, frame: null, closeRequested: false });
    expect(controller.snapshot().closeRequested).toBe(false);
  });

  it('cancelling close reattaches after the decision and invalidates old pending close callbacks', async () => {
    const { controller, channel, close, nextSequence, api } = reservoirFixture(); await controller.create(DEFAULT_SUSTAINED_CONFIG); await settle(); await controller.listenClose(); close(); await settle();
    expect(controller.snapshot().closeRequested).toBe(true); const old = channel();
    const late: SustainedUpdate = { requestId: old.id, snapshotSequence: nextSequence(), summary: controller.snapshot().summary, frame: controller.snapshot().frame, closeRequested: true };
    const action = vi.spyOn(api, 'action'); await controller.returnToApp(); old.listener(late);
    expect(controller.snapshot().closeRequested).toBe(false); expect(action).not.toHaveBeenCalled();
    // A later real request remains admissible; cancellation is not permanent muting.
    close(); await settle(); expect(controller.snapshot().closeRequested).toBe(true);
  });
});
