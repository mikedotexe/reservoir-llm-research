import type { SustainedContinuityState, SustainedInquiryDecision, SustainedInquiryReceipt, SustainedInquirySource } from './myReservoirTypes';

const sourceNames: Record<SustainedInquirySource, string> = { journal: 'Recent journal excerpts', dynamics: 'Reservoir observations', both: 'Recent journal excerpts and reservoir observations' };
const number = (value: number) => Number(value.toPrecision(6)).toString();

export function InquiryDecisionView({ decision, skipped = false }: { decision: SustainedInquiryDecision; skipped?: boolean }) {
  const request = decision.request;
  return <div className="my-reservoir-inquiry-decision">
    <p><strong>{skipped ? 'Inquiry choice skipped' : 'Inquiry choice awaiting application'}</strong></p>
    {request?.kind === 'open' && <><p>{request.question}</p><p>{sourceNames[request.source]}</p></>}
    {request?.kind === 'continue' && <p>Continue the existing question.</p>}
    {request?.kind === 'close' && <p>Close the existing question.</p>}
    {decision.rejection && <p className="my-reservoir-action-rejection">{decision.rejection}</p>}
    <p>{skipped ? 'This choice did not change the retained inquiry.' : 'The retained inquiry changes only after this entry is saved, read back and applied.'}</p>
  </div>;
}

export function InquiryReceiptView({ receipt }: { receipt: SustainedInquiryReceipt }) {
  const labels = { opened: 'Inquiry opened', replaced: 'Inquiry replaced', continued: 'Inquiry continued', closed: 'Inquiry closed', rejected: 'Inquiry choice rejected' };
  return <div className="my-reservoir-inquiry-receipt">
    <p><strong>{labels[receipt.status]} at step {receipt.appliedStep}</strong></p>
    {receipt.decision.request?.kind === 'open' && <p>{receipt.decision.request.question}</p>}
    {receipt.rejection && <p className="my-reservoir-action-rejection">{receipt.rejection}</p>}
    {receipt.status === 'closed' && <p>Closing records the model’s choice to leave this question. It does not establish that the question was answered.</p>}
  </div>;
}

export default function MyReservoirInquiry({ continuity }: { continuity: SustainedContinuityState }) {
  const inquiry = continuity.activeInquiry;
  return <section className="my-reservoir-local-inquiry" aria-label="Continuing local inquiry">
    <h3>Continuing local inquiry</h3>
    {inquiry ? <>
      <p className="my-reservoir-inquiry-question">{inquiry.question}</p>
      <p>{sourceNames[inquiry.source]} · opened from the entry at step {inquiry.openedObservedStep}, applied at step {inquiry.openedAppliedStep}.</p>
      <p>The question remains available across ordinary entries until the model closes or replaces it. Retaining a question does not mean it has been resolved.</p>
      <p className="my-reservoir-small">{inquiry.continuationCount} explicit continuation choices · last continued at step {inquiry.lastContinuedStep}.</p>
      <details className="my-reservoir-details"><summary>Retained inquiry evidence</summary>
        {inquiry.source !== 'journal' && <>
          <h4>Opening observation · step {inquiry.baseline.step}</h4>
          <dl className="my-reservoir-data"><dt>Recurrent RMS</dt><dd>{number(inquiry.baseline.rms)}</dd><dt>Separate sensory fill</dt><dd>{number(inquiry.baseline.sensoryFill)}%</dd><dt>Opening leak</dt><dd>{number(inquiry.openingControls.leak)}</dd><dt>Opening recurrent gain</dt><dd>{number(inquiry.openingControls.recurrentGain)}</dd><dt>Opening text feedback scale</dt><dd>{number(inquiry.openingControls.feedbackScale)}</dd></dl>
          <p>Later ordinary prompts can compare this opening observation with their current readout. Their exact supplied evidence remains in each entry’s prompt.</p>
        </>}
        {inquiry.source !== 'dynamics' && <>
          <h4>Selected recent journal excerpts · {inquiry.history.length}</h4>
          <p>Up to four excerpts from the recent applied journal window were retained at opening or the latest explicit continuation, at step {inquiry.lastContinuedStep}. This is a bounded local reading, not a search of the full archive.</p>
          {inquiry.history.length === 0 ? <p>No earlier excerpt was available when this evidence was retained.</p> : <ol>{inquiry.history.map(entry => <li key={entry.journalId}>
            <p>Observed step {entry.observedStep} · applied step {entry.appliedStep}{entry.checkIn ? ' · scheduled conversation' : ' · ordinary journal'}</p>
            <pre className="my-reservoir-inquiry-excerpt">{entry.excerpt}</pre>
            <p className="my-reservoir-small">{entry.excerptTruncated ? `Excerpt truncated to the retained byte limit; complete body is ${entry.bodyBytes} bytes.` : `Complete body · ${entry.bodyBytes} bytes.`}</p>
            <p className="my-reservoir-hash">Entry: {entry.journalId}<br/>Body SHA-256: {entry.bodySha256}</p>
          </li>)}</ol>}
        </>}
      </details>
    </> : <p>No question is currently retained. The model can open one during an ordinary journal turn.</p>}
    {continuity.latestInquiryReceipt && <details className="my-reservoir-details"><summary>Latest inquiry choice</summary><InquiryReceiptView receipt={continuity.latestInquiryReceipt}/></details>}
  </section>;
}
