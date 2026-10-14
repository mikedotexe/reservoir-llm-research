import { describe, expect, it } from 'vitest';
import { applicationAtCursor, comparisonAtCursor, continueTarget, readGuideResume, sourceForLesson, stateDifference, turnAtCursor, type GuideComparison } from './guideNavigation';
import type { GuideLesson, TrackSummary, TurnView } from './types';

const lesson = (stage = 5): GuideLesson => ({ stage, title: 'Test lesson', question: 'Test question', suggestedAction: 'Inspect', expected: 'Scripted expectation', modelExpected: 'Model expectation', limitation: 'Test limit', focus: 'feedback', checkpoints: [30, 31, 60, 61], scriptedFile: 'scripted.json', modelFile: stage >= 4 ? 'model.json' : null,
  scriptedExample: { id: 'scripted', title: 'Scripted', file: 'scripted.json', format: 'test', provenance: 'Test fixture', group: 'guided', order: stage, lessonId: 'E' },
  modelExample: stage >= 4 ? { id: 'model', title: 'Recorded', file: 'model.json', format: 'test', provenance: 'Test fixture', group: 'model', order: stage, lessonId: 'E' } : null });
const track: TrackSummary = { id: 'right', label: 'Right', frameCount: 120, turnCount: 4, backend: null, model: null, timelineStride: 1,
  timeline: Array.from({ length: 120 }, (_, index) => ({ index, step: String(index + 1), time: null, fillPercent: null, eigenvalues: null })) };

describe('authored recorded guide navigation', () => {
  it('continues from saving to its exact next-step application, then next authored checkpoint', () => {
    expect(continueTarget(lesson(), track, '30')).toEqual({ kind: 'checkpoint', step: 31, index: 30 });
    expect(continueTarget(lesson(), track, '31')).toEqual({ kind: 'checkpoint', step: 60, index: 59 });
    expect(continueTarget(lesson(), track, '61')).toEqual({ kind: 'lesson', stage: 6 });
  });
  it('ends H without automatic playback and cannot invent an unavailable checkpoint', () => {
    expect(continueTarget({ ...lesson(8), checkpoints: [30, 60, 90, 120] }, track, '120')).toEqual({ kind: 'complete' });
    expect(continueTarget(lesson(), { ...track, frameCount: 30, timeline: track.timeline.slice(0, 30) }, '30')).toEqual({ kind: 'lesson', stage: 6 });
  });
  it('uses numerical examples for A–C while preserving recorded-model preference for D–H', () => {
    expect(sourceForLesson(lesson(2), 'recordedModel').id).toBe('scripted');
    expect(sourceForLesson(lesson(4), 'recordedModel').id).toBe('model');
    expect(sourceForLesson(lesson(4), 'scripted').id).toBe('scripted');
  });
  it('hides future turns and applications, including cursor rewinds', () => {
    const turn = { observedStep: '30' } as TurnView;
    expect(turnAtCursor(turn, '29')).toBe(false);
    expect(turnAtCursor(turn, '30')).toBe(true);
    expect(turnAtCursor({ observedStep: null } as TurnView, '30')).toBe(false);
    expect(applicationAtCursor('31', '30')).toBe('Not reached at this cursor');
    expect(applicationAtCursor('31', '31')).toBe('31');
    expect(applicationAtCursor(null, '31')).toBe('Not recorded');
  });
  it('restores bounded guide preferences and recovers from invalid saved preferences', () => {
    expect(readGuideResume({ getItem: () => JSON.stringify({ stage: 6, row: 59, source: 'recordedModel' }) })).toEqual({ stage: 6, row: 59, source: 'recordedModel' });
    for (const data of ['bad json', JSON.stringify({ stage: 9, row: 0, source: 'scripted' }), JSON.stringify({ stage: 1, row: -1, source: 'scripted' })]) {
      expect(readGuideResume({ getItem: () => data })).toEqual({ stage: 1, row: 0, source: 'scripted' });
    }
  });
  it('computes only current matched-vector difference and preserves absent comparisons', () => {
    expect(stateDifference([0, 1], [0, 1])).toBe(0);
    expect(stateDifference([0, 1], [1, 0])).toBe(1);
    expect(stateDifference([0], [0, 1])).toBeNull();
    expect(stateDifference([], [])).toBeNull();
  });
  it('does not reuse the previous opposite arm after a same-step track switch', () => {
    const comparison: GuideComparison = { recordId: 'fixture', trackId: 'right', step: '30', frame: null, message: 'Left compared with right' };
    expect(comparisonAtCursor(comparison, 'fixture', 'right', '30')).toBe(comparison);
    expect(comparisonAtCursor(comparison, 'fixture', 'left', '30')).toBeNull();
    expect(comparisonAtCursor(comparison, 'next-record', 'right', '30')).toBeNull();
    expect(comparisonAtCursor(comparison, 'fixture', 'right', '31')).toBeNull();
    expect(comparisonAtCursor(null, undefined, null, undefined)).toBeNull();
  });
});
