import type { FrameView, GuideLesson, RecordSummary, TrackSummary, TurnView } from './types';

export type GuideSource = 'scripted' | 'recordedModel';
export interface GuideResume { stage: number; row: number; source: GuideSource }
export const GUIDE_RESUME_KEY = 'reservoir-scope.guide.v1';

export function sourceForLesson(lesson: GuideLesson, preference: GuideSource) {
  return preference === 'recordedModel' && lesson.modelExample ? lesson.modelExample : lesson.scriptedExample;
}

export function acceptedLessonReplacement(previousId: string | undefined, record: RecordSummary | null, filename: string): record is RecordSummary {
  // The reader retains its accepted handle when an incoming open fails or is cancelled.
  return record !== null && record.recordId !== previousId && record.filename === filename;
}

export interface GuideComparison {
  recordId: string;
  trackId: string;
  step: string;
  frame: FrameView | null;
  message: string;
}
export function comparisonAtCursor(comparison: GuideComparison | null, recordId: string | undefined, trackId: string | null, step: string | undefined): GuideComparison | null {
  return comparison !== null && comparison.recordId === recordId && comparison.trackId === trackId && comparison.step === step ? comparison : null;
}

export type ContinueTarget = { kind: 'checkpoint'; step: number; index: number } | { kind: 'lesson'; stage: number } | { kind: 'complete' };
export function continueTarget(lesson: GuideLesson, track: TrackSummary, currentStep: string): ContinueTarget {
  const current = BigInt(currentStep);
  for (const step of lesson.checkpoints) {
    if (BigInt(step) <= current) continue;
    const point = track.timeline.find(item => item.step === String(step));
    if (point) return { kind: 'checkpoint', step, index: point.index };
  }
  return lesson.stage < 8 ? { kind: 'lesson', stage: lesson.stage + 1 } : { kind: 'complete' };
}

export function turnAtCursor(turn: TurnView, cursorStep?: string): boolean {
  if (cursorStep === undefined) return true;
  return turn.observedStep !== null && BigInt(turn.observedStep) <= BigInt(cursorStep);
}

export function applicationAtCursor(application: string | null, cursorStep?: string): string {
  if (application === null) return 'Not recorded';
  return cursorStep !== undefined && BigInt(application) > BigInt(cursorStep) ? 'Not reached at this cursor' : application;
}

export function readGuideResume(storage: Pick<Storage, 'getItem'>): GuideResume {
  try {
    const value = JSON.parse(storage.getItem(GUIDE_RESUME_KEY) ?? 'null') as Partial<GuideResume> | null;
    if (value && Number.isInteger(value.stage) && value.stage! >= 1 && value.stage! <= 8 && Number.isInteger(value.row) && value.row! >= 0 && value.row! < 600 && ['scripted', 'recordedModel'].includes(value.source ?? '')) return value as GuideResume;
  } catch { /* A missing or unreadable preference never blocks recorded evidence. */ }
  return { stage: 1, row: 0, source: 'scripted' };
}

export function rms(values: number[]): number | null {
  return values.length ? Math.sqrt(values.reduce((sum, value) => sum + value * value, 0) / values.length) : null;
}
export function stateDifference(left: number[], right: number[]): number | null {
  return left.length === right.length && left.length > 0 ? rms(left.map((value, index) => right[index] - value)) : null;
}
