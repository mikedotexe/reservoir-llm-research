import type { FrameView, StudyNotes } from './types';

/** This view only presents the verdict attached by Rust to the accepted frame. */
export function MechanicalEvidence({ frame }: { frame: FrameView }) {
  const evidence = frame.lessonEvidence;
  if (!evidence) return null;
  return <section className="mechanical-evidence" aria-label="Mechanical evidence at the recorded cursor">
    <div><span className="eyebrow">RIGHT-ARM PREFIX · CURSOR {frame.step}</span><strong>{evidence.state}</strong></div>
    <p>{evidence.observation}</p>
    {evidence.evidenceSteps.length > 0 && <small>Evidence steps: {evidence.evidenceSteps.join(', ')}</small>}
  </section>;
}

export function ControllerEvidence({ frame, study }: { frame: Pick<FrameView, 'regulationEvidence'> & Partial<FrameView>; study: StudyNotes }) {
  const evidence = frame.regulationEvidence;
  const total = study.evaluationLastStep - study.evaluationFirstStep + 1;
  return <section className="controller-evidence" aria-label="Controller evaluation at the recorded cursor">
    <span className="eyebrow">SEPARATE SENSORY-FIELD STUDY · TARGET {study.targetFillPercent}%</span>
    <h2>{study.question}</h2>
    {evidence ? <>
      <p><strong>{evidence.isComplete ? 'Complete evaluation window' : 'Partial evaluation window'}</strong> · {evidence.count} / {total} recorded steps · steps {evidence.firstStep}–{evidence.lastStep}</p>
      <div className="controller-errors">{([
        ['Baseline', evidence.baselineMeanAbsoluteError], ['Regulated', evidence.regulatedMeanAbsoluteError],
      ] as const).map(([label, value]) => <div key={label}><strong>{label}</strong><span>{value.toPrecision(8)} percentage points</span><div className="error-scale" aria-hidden="true"><i style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></div><small>Exact mean absolute target error: {value}</small></div>)}</div>
      <p className="record-caption">Fixed 0–100 percentage-point scale. Calculated from the reached prefix only; rewinding removes later observations.</p>
    </> : <p className="notice">Evaluation starts at step {study.evaluationFirstStep}. No target-error result is available at this cursor.</p>}
    <details><summary>Study design and interpretation limits</summary><p>{study.expectedDifference}</p><p>{study.alternativeExplanation}</p><p>{study.stoppingPoint}</p></details>
  </section>;
}
