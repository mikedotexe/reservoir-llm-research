import { describe, expect, it } from 'vitest';
import { errorText } from './api';

describe('backend error presentation', () => {
  it('preserves concrete typed backend errors without dumping the payload', () => {
    expect(errorText({ operation: 'open-file', code: 'too-large', message: 'File exceeds the 16 MiB limit.' })).toBe('File exceeds the 16 MiB limit.');
    expect(errorText(new Error('Missing resource'))).toBe('Missing resource');
    expect(errorText('Dialog unavailable')).toBe('Dialog unavailable');
    expect(errorText(null)).toBe('The desktop operation failed.');
  });
});
