import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import RecordedStateInspection, { INITIAL_STATE_INSPECTION, type StateInspectionPreferences } from './RecordedStateInspection';
import type { ObservatoryStateFrame } from './observatoryTypes';
import { DEFAULT_CAMERA } from './types';

const vector = (first: number) => [first, ...Array(127).fill(0)];
const state: ObservatoryStateFrame = {
  activations: vector(-.25), pc: [.12, .23, .34], stateRms: .1, centeredRms: .2, projectedRms: .3, reconstructionRmse: .4, sourceIdentity: 'synthetic-state-identity',
  fields: { magnitude: vector(.25), deviation: vector(2.5), magnitudeOutOfRangeCount: 0, deviationOutOfRangeCount: 1, scores: [.12345678901234567, .2, .3], centeredEnergy: 10,
    selections: [[0], [1], [2], [0, 1, 2]].map((selectedModes, index) => ({ selectedModes, reconstruction: vector(.01 * (index + 1)), residual: vector(.101 + index), reconstructedEnergy: 2 + index, residualEnergy: 8 - index, reconstructionOutOfRangeCount: 0, residualOutOfRangeCount: index > 1 ? 1 : 0 })) },
};
const noAction = () => { throw new Error('Static inspection must not start a request or alter a selection'); };
const html = (preferences: Partial<StateInspectionPreferences> = {}, value = state) => renderToStaticMarkup(<RecordedStateInspection state={value} reference={null} points={[]} total={1024} row={512} node={0} pose={DEFAULT_CAMERA} tableOnly preferences={{ ...INITIAL_STATE_INSPECTION, ...preferences }} onPreferences={noAction} onRow={noAction} onNode={noAction} onPose={noAction}/>);

describe('recorded reference field inspection', () => {
  it('shows signed raw state and unavailable reference/spectrum without inventing data', () => {
    const view = html();
    expect(view).toContain('Same recorded row'); expect(view).toContain('512');
    expect(view).toContain('Raw activation · coordinate 0'); expect(view).toContain('<output>-0.25</output>');
    expect(view).toContain('original signed values'); expect(view).not.toContain('Reference reconstruction modes');
    expect(view).not.toContain('<canvas');
  });
  it('shows backend magnitude on its nonnegative scale without relabeling the signed evidence', () => {
    const view = html({ field: 'magnitude' });
    expect(view).toContain('legend-nonnegative'); expect(view).toContain('<output>0.25</output>');
    expect(view).toContain('<output>-0.25</output>'); expect(view).toContain('exact derived field values');
    expect(view).not.toContain('Reference reconstruction modes');
  });
  it('preserves out-of-range derived coordinates exactly while disclosing fixed display saturation', () => {
    const view = html({ field: 'referenceDeviation' });
    expect(view).toContain('1 coordinates exceed the fixed display range');
    expect(view).toContain('<output>2.5</output>'); expect(view).toContain('<span>−2</span>');
    expect(view).toContain('it does not add the mean back');
  });
  it('uses the chosen backend decomposition and distinguishes row energy from capture variance', () => {
    const first = html({ field: 'reconstruction', modes: 0 });
    const all = html({ field: 'residual', modes: 3 });
    expect(first).toContain('<output>0.01</output>'); expect(first).toContain('20.00%');
    expect(all).toContain('<output>3.101</output>'); expect(all).toContain('50.00%');
    expect(first).toContain('not the whole-capture variance share');
    expect(first).toContain('Recomputed mode scores'); expect(first).toContain('Retained projection coordinates');
    expect(first).not.toMatch(/<details[^>]*\bopen/);
  });
  it('does not turn zero centered energy into an invented reconstruction fraction', () => {
    const view = html({ field: 'residual' }, { ...state, fields: { ...state.fields, centeredEnergy: 0 } });
    expect(view).toContain("squared deviation reconstructed</span><output>Unavailable</output>");
    expect(view).not.toContain('NaN'); expect(view).not.toContain('Infinity');
  });
});
