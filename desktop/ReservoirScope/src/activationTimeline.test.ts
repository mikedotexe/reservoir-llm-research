import { describe, expect, it } from 'vitest';
import { activationTimeline } from './activationTimeline';
import { activationSession } from './activationTestFixtures';
import type { ActivationEvent } from './activationTypes';

const event = (n: number, kind: string, step: number, detail = ''): ActivationEvent => ({ id: `event-${n}`, kind, step, detail });

describe('Activation observation timeline', () => {
  it('joins all twelve observations across intervening journal events to their real application boundaries', () => {
    const session = activationSession(), events: ActivationEvent[] = [];
    const add = (kind: string, step: number, detail = '') => events.push(event(events.length + 1, kind, step, detail));
    for (let n = 1; n <= 12; n++) {
      add('requestStarted', n * 10 - 1, 'quiet_capture'); add('quietReceived', n * 10);
      if (n % 2 === 0) { add('requestStarted', n * 10, 'generate_journal'); add('journalReceived', n * 10); add('journalSaved', n * 10); add('journalApplied', n * 10 + 1); }
    }
    const rows = activationTimeline({ ...session, events }), applied = rows.flatMap(row => row.observation?.outcome === 'applied' ? [row.observation] : []);
    expect(applied.map(o => o.text)).toEqual(session.config.observations);
    expect(applied.map(o => o.applicationStep)).toEqual(Array.from({ length: 12 }, (_, i) => (i + 1) * 10));
    expect(applied.map(o => o.requestedStep)).toEqual(Array.from({ length: 12 }, (_, i) => (i + 1) * 10 - 1));
    expect(rows.filter(row => row.event.kind.startsWith('journal')).every(row => row.observation === null)).toBe(true);
  });
  it.each([['worker exited', 'failed'], ['Owned activation worker was cancelled; no late result is accepted', 'cancelled']])('keeps an unsuccessful quiet request attached to its own observation: %s', (reason, outcome) => {
    const session = activationSession({ events: [event(1, 'requestStarted', 9, 'quiet_capture'), event(2, 'quietReceived', 10), event(3, 'requestStarted', 19, 'quiet_capture'), event(4, 'failed', 19, reason)] });
    const rows = activationTimeline(session), last = rows.at(-1)!;
    expect(last.observation).toMatchObject({ number: 2, text: session.config.observations[1], outcome, requestedStep: 19, scheduledStep: 20, applicationStep: null });
    expect(last.failed).toBe(true); expect(rows.filter(row => row.observation?.outcome === 'applied')).toHaveLength(1);
  });
  it('does not attribute a later journal failure or initialization refusal to a quiet observation', () => {
    const events = [event(1, 'requestStarted', 9, 'quiet_capture'), event(2, 'quietReceived', 10), event(3, 'requestStarted', 10, 'generate_journal'), event(4, 'failed', 10, 'journal failed')];
    expect(activationTimeline(activationSession({ events })).at(-1)?.observation).toBeNull();
    expect(activationTimeline(activationSession({ events: [event(1, 'failed', 0, 'Resource admission refused')] }))[0].observation).toBeNull();
  });
  it('keeps a request distinct from an application and uses the receipt step as the actual application boundary', () => {
    const session = activationSession({ events: [event(1, 'requestStarted', 9, 'quiet_capture')] });
    expect(activationTimeline(session)[0].observation).toMatchObject({ outcome: 'requested', scheduledStep: 10, applicationStep: null });
    const received = activationTimeline({ ...session, events: [...session.events, event(2, 'quietReceived', 11)] })[1].observation;
    expect(received).toMatchObject({ outcome: 'applied', scheduledStep: 10, applicationStep: 11 });
  });
});
