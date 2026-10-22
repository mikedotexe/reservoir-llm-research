import { describe, expect, it } from 'vitest';
import { FRAME_ARM_PROMPT_VERSIONS, isSustainedPromptVersion } from './myReservoirTypes';

describe('frame arm prompt versions', () => {
  it('are recognised for reading recovered research sessions but are not the fresh default', () => {
    expect(FRAME_ARM_PROMPT_VERSIONS).toHaveLength(11);
    expect(FRAME_ARM_PROMPT_VERSIONS).toContain('reservoir-journal-inert-plain-contract-scrambled-tag-v1');
    expect(FRAME_ARM_PROMPT_VERSIONS).toContain('reservoir-journal-inert-plain-contract-effect-v1');
    expect(FRAME_ARM_PROMPT_VERSIONS).toContain('reservoir-journal-inert-open-contract-v1');
    expect(FRAME_ARM_PROMPT_VERSIONS).toContain('reservoir-journal-inert-inviting-varied-contract-v1');
    for (const v of FRAME_ARM_PROMPT_VERSIONS) expect(isSustainedPromptVersion(v)).toBe(true);
    expect(isSustainedPromptVersion('reservoir-journal-v8')).toBe(true);
    expect(isSustainedPromptVersion('reservoir-journal-inert-v2')).toBe(false);
  });
});
