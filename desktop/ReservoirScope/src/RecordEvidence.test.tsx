import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { ControllerEvidence, MechanicalEvidence } from './RecordEvidence';
import type { FrameView, StudyNotes } from './types';

const frame: FrameView = { index: 299, step: '300', time: 100, state: [], input: [], noise: [], fillPercent: 70, eigenvalues: [], retentionUsed: .955, semanticTurnId: null };
const study: StudyNotes = { question: 'Synthetic test question', expectedDifference: 'Authored expectation only', alternativeExplanation: 'No universal target attainment', stoppingPoint: '600 steps', evaluationFirstStep: 301, evaluationLastStep: 600, targetFillPercent: 68 };
describe('backend-owned prefix evidence presentation', () => {
  it('does not manufacture a mechanical verdict for an unsupported family', () => {
    expect(renderToStaticMarkup(<MechanicalEvidence frame={frame} />)).toBe('');
  });
  it('preserves distinct incomplete and observed states instead of inferring success', () => {
    const html = renderToStaticMarkup(<MechanicalEvidence frame={{...frame, lessonEvidence:{state:'Incomplete evidence',observation:'Save failed <untrusted>',evidenceSteps:[30]}}} />);
    expect(html).toContain('Incomplete evidence');
    expect(html).toContain('Save failed &lt;untrusted&gt;');
    expect(html).toContain('Evidence steps: 30');
    expect(html).not.toContain('<untrusted>');
  });
  it('withholds target-error numbers before the evaluation window', () => {
    const html = renderToStaticMarkup(<ControllerEvidence frame={frame} study={study} />);
    expect(html).toContain('Evaluation starts at step 301');
    expect(html).not.toContain('Exact mean absolute target error:');
    expect(html).not.toContain('Complete evaluation window');
  });
  it('labels a one-step prefix as partial while retaining exact paired errors', () => {
    const html = renderToStaticMarkup(<ControllerEvidence frame={{...frame,step:'301',regulationEvidence:{count:1,firstStep:301,lastStep:301,isComplete:false,baselineMeanAbsoluteError:17.125,regulatedMeanAbsoluteError:2.75}}} study={study} />);
    expect(html).toContain('Partial evaluation window');
    expect(html).toContain('1 / 300 recorded steps');
    expect(html).toContain('Exact mean absolute target error: 17.125');
    expect(html).toContain('Exact mean absolute target error: 2.75');
    expect(html).not.toContain('Complete evaluation window');
  });
  it('only labels the returned complete window complete and clears on rewind', () => {
    const complete={...frame,step:'600',regulationEvidence:{count:300,firstStep:301,lastStep:600,isComplete:true,baselineMeanAbsoluteError:17,regulatedMeanAbsoluteError:2}};
    expect(renderToStaticMarkup(<ControllerEvidence frame={complete} study={study} />)).toContain('Complete evaluation window');
    const rewound=renderToStaticMarkup(<ControllerEvidence frame={frame} study={study} />);
    expect(rewound).not.toContain('Complete evaluation window');
    expect(rewound).not.toContain('Exact mean absolute target error:');
  });
});
