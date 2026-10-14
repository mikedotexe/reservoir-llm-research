import { describe, expect, it } from 'vitest';
import { recordedNumber, scalarSegments } from './recordingChart';

describe('recorded scalar evidence', () => {
  it('keeps zero distinct from missing values and does not invent precision', () => {
    expect(recordedNumber(0, '%')).toBe('0%');
    expect(recordedNumber(null)).toBe('Not recorded');
    expect(recordedNumber(undefined)).toBe('Not recorded');
    expect(recordedNumber(12.3456789)).toBe('12.3456789');
  });
  it('breaks lines at missing samples and gaps in frame indices', () => {
    const lines = scalarSegments([{ index: 0, value: 20 }, { index: 1, value: 30 }, { index: 2, value: null }, { index: 3, value: 40 }, { index: 5, value: 0 }], 6, 0, 100, 500, 100);
    expect(lines).toEqual(['0.000,80.000 100.000,70.000', '300.000,60.000', '500.000,100.000']);
  });
  it('leaves an absent scalar series empty and handles a single recorded sample', () => {
    expect(scalarSegments([{ index: 0, value: null }], 1, 0, 100)).toEqual([]);
    expect(scalarSegments([{ index: 0, value: 2 }], 1, 2, 2)).toEqual(['0.000,60.000']);
  });
});
