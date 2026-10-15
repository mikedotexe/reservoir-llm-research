import type { SustainedPromptVersion } from './myReservoirTypes';
import { formatRecordedMeasurement, readMeasurementReference } from './journalMeasurementReference';

export default function JournalMeasurements({ value, observedStep, promptVersion }: { value: unknown; observedStep: number; promptVersion?: SustainedPromptVersion }) {
  const { reference, reason } = readMeasurementReference(value, observedStep);
  return <details className="my-reservoir-journal-measurements">
    <summary>Recorded measurements</summary>
    {(promptVersion === 'reservoir-journal-v5' || promptVersion === 'reservoir-journal-v6' || promptVersion === 'reservoir-journal-v7' || promptVersion === 'reservoir-journal-v8') && <p>This table shows retained measurements for your inspection. The {promptVersion.replace('reservoir-journal-', '')} prompt supplies only current and prior recurrent RMS and separate sensory fill with their differences, plus state-coordinate L2 distance since the previous observation; it does not supply this full table.</p>}
    {reference ? <>
      <p>Observed at this entry’s writing step {reference.currentStep}. These are retained numerical readings, separate from the prose and the current live state.</p>
      {!reference.comparisonAvailable && <p>{reference.previousStep === null
        ? 'No previous observation is recorded for this entry.'
        : `The previous observation was at step ${reference.previousStep}, but its scalar measurements are not retained in this reference. Differences are unavailable.`}</p>}
      <div className="my-reservoir-measurement-scroll" tabIndex={0} role="region" aria-label={`Recorded measurements at writing step ${reference.currentStep}`}>
        <table className="my-reservoir-measurement-table">
          <caption>Current and prior refer to observation steps, not prior journal prose. Values are shown to eight significant digits; the retained observation in Evidence contains the full values.</caption>
          <thead><tr><th scope="col">Measurement</th><th scope="col">Current · step {reference.currentStep}</th><th scope="col">{reference.previousStep === null ? 'Prior · unavailable' : `Prior · step ${reference.previousStep}`}</th><th scope="col">Difference · current − prior</th></tr></thead>
          <tbody>{reference.rows.map(row => <tr key={row.key}>
            <th scope="row">{row.label}{row.unit === 'percent' ? ' (%)' : ''}</th>
            <td title={String(row.current)}>{formatRecordedMeasurement(row.current)}</td>
            <td title={row.previous === null ? undefined : String(row.previous)}>{row.previous === null ? 'Unavailable' : formatRecordedMeasurement(row.previous)}</td>
            <td title={row.delta === null ? undefined : String(row.delta)}>{row.delta === null ? 'Unavailable' : <>{formatRecordedMeasurement(row.delta, true)}{row.unit === 'percent' ? ' pp' : ''}</>}</td>
          </tr>)}</tbody>
        </table>
      </div>
      <p>“pp” means percentage points. Head, shoulder and tail are shares of the top eight sensory eigenvalues, not spatial regions. A difference between two observations does not establish a trend or explain its cause. This view does not assess or change the writing.</p>
    </> : <p>{reason} The exact retained observation remains available in Evidence.</p>}
  </details>;
}
