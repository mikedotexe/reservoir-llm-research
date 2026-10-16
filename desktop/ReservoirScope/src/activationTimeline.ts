import type { ActivationEvent, ActivationSnapshot } from './activationTypes';

export const activationEventLabel = (kind: string) => {
  kind = kind.toLowerCase();
  if (/fail|error|reject/.test(kind)) return 'Attempt failed';
  if (/cancel|stop/.test(kind)) return 'Stopped';
  if (/quiet|observation|capture/.test(kind)) return /appl/.test(kind) ? 'Observation applied' : /complete|success|captur|receiv/.test(kind) ? 'Quiet observation received' : 'Quiet observation';
  if (/journal/.test(kind)) return /appl/.test(kind) ? 'Journal feedback applied' : /sav/.test(kind) ? 'Journal saved and read back' : /receiv/.test(kind) ? 'Writing received · save pending' : 'Writing opportunity';
  if (kind === 'requeststarted') return 'Model request started';
  if (/annotat/.test(kind)) return 'Reading note saved';
  if (/creat|ready/.test(kind)) return 'Prepared';
  if (/start|initial/.test(kind)) return 'Started';
  if (/complete/.test(kind)) return 'Run complete';
  return 'Recorded event';
};

interface QuietObservation {
  number: number; text: string; requestedStep: number | null; scheduledStep: number;
  outcome: 'requested' | 'applied' | 'failed' | 'cancelled'; applicationStep: number | null;
}
export interface ActivationTimelineEntry {
  event: ActivationEvent; label: string; observation: QuietObservation | null; failed: boolean;
}

/** Join retained observations to their serial request/outcome events without advancing state. */
export function activationTimeline(session: Pick<ActivationSnapshot, 'config' | 'events'>): ActivationTimelineEntry[] {
  let received = 0, pending: QuietObservation | null = null;
  const observation = (requestedStep: number | null): QuietObservation | null => {
    const text = session.config.observations[received];
    return text === undefined ? null : { number: received + 1, text, requestedStep, scheduledStep: (received + 1) * session.config.stepsBetween, outcome: 'requested', applicationStep: null };
  };
  return session.events.map(event => {
    const kind = event.kind.toLowerCase();
    let quiet: QuietObservation | null = null;
    if (kind === 'requeststarted') {
      pending = event.detail === 'quiet_capture' ? observation(event.step) : null;
      quiet = pending;
    } else if (kind === 'quietreceived') {
      const source = pending ?? observation(null);
      quiet = source ? { ...source, outcome: 'applied', applicationStep: event.step } : null;
      received++; pending = null;
    } else if (kind === 'failed') {
      quiet = pending ? { ...pending, outcome: /\bcancell?ed\b|\bcancellation\b/i.test(event.detail) ? 'cancelled' : 'failed' } : null;
      pending = null;
    }
    return { event, observation: quiet, label: quiet ? `Quiet observation ${quiet.number} ${quiet.outcome}` : activationEventLabel(event.kind), failed: /fail|error|reject|cancel/.test(kind) };
  });
}
